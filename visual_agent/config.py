from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

@dataclass(frozen=True)
class LLMConfig:
    provider: str = "none"
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    api_key_env: str = "OPENAI_API_KEY"


@dataclass(frozen=True)
class AssistConfig:
    overlay_enabled: bool = True
    terminal_output: bool = True


@dataclass(frozen=True)
class VisionConfig:
    ocr_lang: str = "eng"


@dataclass(frozen=True)
class PrivacyConfig:
    redact_rects: list[list[int]] | None = None


@dataclass(frozen=True)
class AgentConfig:
    interval_s: float = 1.0
    analyze_on_window_change_only: bool = False
    debug_save_frames: bool = False
    debug_frames_dir: str = ".agent_frames"
    debug_ocr: bool = False  # Show OCR text and rule matching details


@dataclass(frozen=True)
class RulesConfig:
    enabled: list[str]


@dataclass(frozen=True)
class AppConfig:
    agent: AgentConfig
    privacy: PrivacyConfig
    vision: VisionConfig
    assist: AssistConfig
    llm: LLMConfig
    rules: RulesConfig


def _get(d: dict[str, Any], path: str, default: Any) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def load_config(path: str | Path) -> AppConfig:
    p = Path(path)
    raw: dict[str, Any] = {}
    if p.exists():
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    agent = AgentConfig(
        interval_s=float(_get(raw, "agent.interval_s", 1.0)),
        analyze_on_window_change_only=bool(_get(raw, "agent.analyze_on_window_change_only", False)),
        debug_save_frames=bool(_get(raw, "agent.debug_save_frames", False)),
        debug_frames_dir=str(_get(raw, "agent.debug_frames_dir", ".agent_frames")),
        debug_ocr=bool(_get(raw, "agent.debug_ocr", False)),
    )
    privacy = PrivacyConfig(
        redact_rects=_get(raw, "privacy.redact_rects", []) or [],
    )
    vision = VisionConfig(
        ocr_lang=str(_get(raw, "vision.ocr_lang", "eng")),
    )
    assist = AssistConfig(
        overlay_enabled=bool(_get(raw, "assist.overlay_enabled", True)),
        terminal_output=bool(_get(raw, "assist.terminal_output", True)),
    )
    llm = LLMConfig(
        provider=str(_get(raw, "llm.provider", "none")),
        base_url=str(_get(raw, "llm.base_url", "https://api.openai.com/v1")),
        model=str(_get(raw, "llm.model", "gpt-4o-mini")),
        api_key_env=str(_get(raw, "llm.api_key_env", "OPENAI_API_KEY")),
    )
    rules = RulesConfig(
        enabled=list(_get(raw, "rules.enabled", ["excel_llm"])),
    )
    return AppConfig(agent=agent, privacy=privacy, vision=vision, assist=assist, llm=llm, rules=rules)
