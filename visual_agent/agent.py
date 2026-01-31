from __future__ import annotations

import time
from dataclasses import dataclass

from .capture import capture_primary_monitor, maybe_save_debug_frame, redact_rects
from .config import AppConfig
from .llm import LLMClient, LLMRequest
from .ocr import ocr_image
from .overlay import Overlay, OverlayMessage
from .rules.base import Observation, Suggestion
from .rules.registry import build_rules
from .window_context import get_window_context


@dataclass(frozen=True)
class AgentOutput:
    suggestion: Suggestion | None


class VisualAgent:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.llm = LLMClient(
            provider=cfg.llm.provider,
            base_url=cfg.llm.base_url,
            model=cfg.llm.model,
            api_key_env=cfg.llm.api_key_env,
        )
        # Pass LLM client to rules so LLM-powered rules can use it
        self.rules = build_rules(cfg.rules.enabled, llm_client=self.llm)
        
        # Debug: Print LLM and rule status
        if cfg.agent.debug_ocr:
            import os
            print("\n" + "=" * 72)
            print("LLM Configuration Status:")
            print(f"  Provider: {cfg.llm.provider}")
            print(f"  Model: {cfg.llm.model}")
            print(f"  Base URL: {cfg.llm.base_url}")
            print(f"  API Key Env Var Name: {cfg.llm.api_key_env}")
            api_key = os.environ.get(cfg.llm.api_key_env)
            if api_key:
                print(f"  API Key: Found ({len(api_key)} chars)")
                print(f"  LLM Enabled: {self.llm.enabled()}")
            else:
                print(f"  API Key: NOT FOUND in environment variable '{cfg.llm.api_key_env}'")
                print(f"  LLM Enabled: {self.llm.enabled()}")
                print(f"  → Set it with: setx {cfg.llm.api_key_env} \"your-api-key\"")
            print(f"  Rules loaded: {[r.name for r in self.rules]}")
            print("=" * 72 + "\n")
        
        self.overlay = Overlay()
        self._last_window_sig: tuple[str | None, str | None] | None = None
        self._last_suggestion_key: str | None = None

    def start(self) -> None:
        if self.cfg.assist.overlay_enabled:
            self.overlay.start()

        while True:
            win = get_window_context()
            win_sig = (win.active_app, win.active_title)

            if self.cfg.agent.analyze_on_window_change_only and self._last_window_sig == win_sig:
                time.sleep(self.cfg.agent.interval_s)
                continue
            self._last_window_sig = win_sig

            frame = capture_primary_monitor()
            img = redact_rects(frame.image, self.cfg.privacy.redact_rects or [])
            maybe_save_debug_frame(img, self.cfg.agent.debug_save_frames, self.cfg.agent.debug_frames_dir)

            ocr = ocr_image(img, lang=self.cfg.vision.ocr_lang)
            obs = Observation(active_app=win.active_app, active_title=win.active_title, ocr_text=ocr.text)

            if self.cfg.agent.debug_ocr:
                self._print_debug_info(obs)

            out = self._analyze(obs)
            self._emit(out, obs)

            time.sleep(self.cfg.agent.interval_s)

    def _analyze(self, obs: Observation) -> AgentOutput:
        best: Suggestion | None = None
        for r in self.rules:
            conf = r.match(obs)
            if self.cfg.agent.debug_ocr:
                print(f"  Rule '{r.name}': confidence = {conf:.2f}")
            if conf <= 0:
                continue
            s = r.suggest(obs)
            if (best is None) or (s.confidence > best.confidence):
                best = s

        # Note: LLM-powered rules handle their own LLM calls internally.
        # Traditional rules can still be refined by LLM if needed, but excel_llm rule
        # already uses LLM for both matching and suggestions.

        return AgentOutput(suggestion=best)

    def _emit(self, out: AgentOutput, obs: Observation) -> None:
        if not out.suggestion:
            self._post_overlay("Visual Agent", "Watching screen… (no suggestion)")
            return

        # Deduplicate spam: only re-post if content changed meaningfully.
        key = f"{out.suggestion.title}|{'|'.join(out.suggestion.steps)}"
        if key == self._last_suggestion_key:
            return
        self._last_suggestion_key = key

        body = "\n".join([f"{i+1}. {s}" for i, s in enumerate(out.suggestion.steps)])
        title = f"{out.suggestion.title} ({out.suggestion.source}, {out.suggestion.confidence:.2f})"
        self._post_overlay(title, body)

        if self.cfg.assist.terminal_output:
            print("\n" + "=" * 72)
            print(title)
            print(body)
            if obs.active_title:
                print(f"\nWindow: {obs.active_title}")

    def _print_debug_info(self, obs: Observation) -> None:
        """Print debug information about OCR and window context."""
        print("\n" + "-" * 72)
        print("DEBUG: Observation")
        print("-" * 72)
        print(f"Active App: {obs.active_app}")
        print(f"Active Title: {obs.active_title}")
        print(f"OCR Text ({len(obs.ocr_text)} chars):")
        if obs.ocr_text:
            # Show first 500 chars, or full text if shorter
            ocr_preview = obs.ocr_text[:500] + ("..." if len(obs.ocr_text) > 500 else "")
            print(f"  {ocr_preview!r}")
        else:
            print("  (empty)")
        print("-" * 72)
        print("Rule Matching:")

    def _post_overlay(self, title: str, body: str) -> None:
        if not self.cfg.assist.overlay_enabled:
            return
        self.overlay.post(OverlayMessage(title=title, body=body))

