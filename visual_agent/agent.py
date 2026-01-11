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
        self.rules = build_rules(cfg.rules.enabled)
        self.overlay = Overlay()
        self.llm = LLMClient(
            provider=cfg.llm.provider,
            base_url=cfg.llm.base_url,
            model=cfg.llm.model,
            api_key_env=cfg.llm.api_key_env,
        )
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

            out = self._analyze(obs)
            self._emit(out, obs)

            time.sleep(self.cfg.agent.interval_s)

    def _analyze(self, obs: Observation) -> AgentOutput:
        best: Suggestion | None = None
        for r in self.rules:
            conf = r.match(obs)
            if conf <= 0:
                continue
            s = r.suggest(obs)
            if (best is None) or (s.confidence > best.confidence):
                best = s

        # Optional LLM refinement: turn OCR/window context into more tailored steps
        if best and self.llm.enabled():
            system = (
                "You are an on-screen assistant. Output a concise step-by-step checklist (max 6 steps). "
                "Do not ask questions. Avoid disclaimers. Be specific about UI clicks/tabs when possible."
            )
            user = (
                f"Active window title: {obs.active_title!r}\n"
                f"Active app: {obs.active_app!r}\n"
                f"On-screen text (OCR, noisy): {obs.ocr_text!r}\n\n"
                f"User likely task: {best.title}\n"
                "Produce steps."
            )
            steps = self.llm.suggest_steps(LLMRequest(system=system, user=user))
            if steps:
                best = Suggestion(
                    title=best.title,
                    steps=steps,
                    confidence=min(1.0, best.confidence + 0.05),
                    source=f"{best.source}+llm",
                )

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

    def _post_overlay(self, title: str, body: str) -> None:
        if not self.cfg.assist.overlay_enabled:
            return
        self.overlay.post(OverlayMessage(title=title, body=body))

