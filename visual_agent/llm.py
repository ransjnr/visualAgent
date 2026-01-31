from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMRequest:
    system: str
    user: str


class LLMClient:
    def __init__(self, provider: str, base_url: str, model: str, api_key_env: str) -> None:
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env

    def enabled(self) -> bool:
        if self.provider == "none" or self.provider == "rules_only":
            return False
        return bool(os.environ.get(self.api_key_env))

    def suggest_steps(self, req: LLMRequest) -> list[str] | None:
        """
        Minimal "OpenAI-compatible" client without adding heavy deps.
        Returns list of steps or None on failure / disabled.
        """
        if self.provider != "openai_compatible":
            return None
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            return None

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": req.system},
                {"role": "user", "content": req.user},
            ],
            "temperature": 0.2,
        }
        data = json.dumps(payload).encode("utf-8")
        http_req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
            obj = json.loads(raw)
            content = obj["choices"][0]["message"]["content"]
            # Expect a simple numbered list; parse naively.
            lines = [ln.strip() for ln in (content or "").splitlines() if ln.strip()]
            steps: list[str] = []
            for ln in lines:
                ln2 = ln
                ln2 = ln2.lstrip("-•").strip()
                ln2 = ln2.replace("1) ", "1. ")
                ln2 = ln2.replace("2) ", "2. ")
                # Strip leading "N. "
                ln2 = ln2.split(". ", 1)[1] if ln2[:2].isdigit() and ". " in ln2[:4] else ln2
                if ln2:
                    steps.append(ln2)
            return steps[:8] if steps else None
        except Exception:
            return None

