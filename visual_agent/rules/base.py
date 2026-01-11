from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Observation:
    active_app: str | None
    active_title: str | None
    ocr_text: str


@dataclass(frozen=True)
class Suggestion:
    title: str
    steps: list[str]
    confidence: float  # 0..1
    source: str  # rule name / llm / etc.


class Rule:
    name: str

    def match(self, obs: Observation) -> float:
        """Return confidence 0..1 that this rule applies."""
        raise NotImplementedError

    def suggest(self, obs: Observation) -> Suggestion:
        raise NotImplementedError

