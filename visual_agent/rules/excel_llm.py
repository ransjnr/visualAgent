from __future__ import annotations

import json
import os
import re
import urllib.request

from .base import Observation, Rule, Suggestion


class ExcelLLMRule(Rule):
    """
    LLM-powered Excel rule that dynamically analyzes context and generates suggestions.
    Replaces hardcoded rules with intelligent, context-aware assistance.
    """
    name = "excel_llm"

    def __init__(self, llm_client) -> None:
        self.llm_client = llm_client

    def match(self, obs: Observation) -> float:
        """Use LLM to determine if this is an Excel task and return confidence."""
        if not self.llm_client:
            print("DEBUG: LLM client is None, using fallback")
            # Fallback: basic Excel detection without LLM
            title = (obs.active_title or "").lower()
            app = (obs.active_app or "").lower()
            excelish = any(k in title for k in ["excel", "workbook", ".xlsx"]) or "excel" in app
            return 0.5 if excelish else 0.0
        
        if not self.llm_client.enabled():
            print("DEBUG: LLM not enabled, using fallback detection")
            # LLM not enabled - use fallback detection
            title = (obs.active_title or "").lower()
            app = (obs.active_app or "").lower()
            excelish = any(k in title for k in ["excel", "workbook", ".xlsx"]) or "excel" in app
            return 0.5 if excelish else 0.0

        # Use LLM to analyze context and determine confidence
        system = (
            "You are a context analyzer for an Excel assistant. "
            "Analyze the user's screen context and determine if they are working on an Excel task. "
            "Respond with ONLY a JSON object: {\"confidence\": 0.0-1.0, \"task\": \"brief task description\"}. "
            "confidence: 0.0 = not Excel-related, 0.3-0.6 = possibly Excel-related, 0.7-1.0 = definitely Excel task. "
            "task: a brief description of what the user is likely doing (e.g., 'creating a formula', 'making a chart')."
        )
        user = (
            f"Active window title: {obs.active_title or 'Unknown'}\n"
            f"Active app: {obs.active_app or 'Unknown'}\n"
            f"On-screen text (OCR): {obs.ocr_text[:500] if obs.ocr_text else '(empty)'}\n\n"
            "Is this an Excel-related task? What is the user likely trying to do?"
        )

        print("DEBUG: Calling LLM for analysis...")
        result = self._call_llm_for_analysis(system, user)
        if result:
            conf = result.get("confidence", 0.0)
            print(f"DEBUG: LLM analysis returned confidence: {conf}")
            return conf
        
        # Fallback if LLM fails
        print("DEBUG: LLM analysis failed, using fallback")
        title = (obs.active_title or "").lower()
        app = (obs.active_app or "").lower()
        excelish = any(k in title for k in ["excel", "workbook", ".xlsx"]) or "excel" in app
        return 0.5 if excelish else 0.0

    def suggest(self, obs: Observation) -> Suggestion:
        """Use LLM to generate step-by-step suggestions based on context."""
        if not self.llm_client or not self.llm_client.enabled():
            # Fallback suggestion
            return Suggestion(
                title="Working in Excel",
                steps=[
                    "The LLM assistant is not enabled. Enable it in config.yaml to get intelligent suggestions.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )

        # Use LLM to generate contextual suggestions
        system = (
            "You are an Excel expert assistant. Analyze the user's screen and provide helpful step-by-step guidance. "
            "Output a JSON object with: {\"title\": \"task title\", \"steps\": [\"step1\", \"step2\", ...]}. "
            "Be specific about Excel UI elements (tabs, buttons, menus). "
            "Keep steps concise and actionable (4-8 steps). "
            "Focus on what the user is likely trying to accomplish based on the screen context."
        )
        user = (
            f"Active window title: {obs.active_title or 'Unknown'}\n"
            f"Active app: {obs.active_app or 'Unknown'}\n"
            f"On-screen text (OCR, may be noisy): {obs.ocr_text[:1000] if obs.ocr_text else '(empty)'}\n\n"
            "What Excel task is the user working on? Provide step-by-step instructions to help them."
        )

        result = self._call_llm_for_suggestion(system, user)
        if result:
            return Suggestion(
                title=result.get("title", "Excel assistance"),
                steps=result.get("steps", []),
                confidence=self.match(obs),
                source=self.name,
            )

        # Fallback if LLM fails
        return Suggestion(
            title="Excel assistance",
            steps=[
                "Unable to generate suggestions. Check LLM configuration.",
            ],
            confidence=self.match(obs),
            source=self.name,
        )

    def _call_llm_for_analysis(self, system: str, user: str) -> dict | None:
        """Call LLM to analyze context and return confidence/task."""
        api_key = os.environ.get(self.llm_client.api_key_env)
        if not api_key:
            return None

        url = f"{self.llm_client.base_url}/chat/completions"
        payload = {
            "model": self.llm_client.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,  # Lower temperature for more consistent analysis
        }
        # Add JSON mode for supported models (GPT-4o-mini supports JSON mode)
        model_lower = self.llm_client.model.lower()
        if "gpt-4" in model_lower and "o1" not in model_lower:
            payload["response_format"] = {"type": "json_object"}

        try:
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
            with urllib.request.urlopen(http_req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
            obj = json.loads(raw)
            content = obj["choices"][0]["message"]["content"]
            
            # Try to parse JSON from response
            try:
                result = json.loads(content)
                print(f"DEBUG: LLM analysis successful: {result}")
                return result
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON parse error in analysis: {e}")
                print(f"DEBUG: Response content: {content[:200]}")
                # Fallback: try to extract JSON from text
                json_match = re.search(r'\{[^}]+\}', content)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        pass
                return None
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if hasattr(e, 'read') else str(e)
            print(f"DEBUG: HTTP error in LLM analysis: {e.code} {e.reason}")
            print(f"DEBUG: Error body: {error_body[:500]}")
            return None
        except Exception as e:
            print(f"DEBUG: Exception in LLM analysis: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _call_llm_for_suggestion(self, system: str, user: str) -> dict | None:
        """Call LLM to generate suggestions and return title/steps."""
        api_key = os.environ.get(self.llm_client.api_key_env)
        if not api_key:
            return None

        url = f"{self.llm_client.base_url}/chat/completions"
        payload = {
            "model": self.llm_client.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.3,
        }
        # Add JSON mode for supported models (GPT-4o-mini supports JSON mode)
        model_lower = self.llm_client.model.lower()
        if "gpt-4" in model_lower and "o1" not in model_lower:
            payload["response_format"] = {"type": "json_object"}

        try:
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
            with urllib.request.urlopen(http_req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
            obj = json.loads(raw)
            content = obj["choices"][0]["message"]["content"]
            print(f"DEBUG: LLM suggestion response received ({len(content)} chars)")
            
            # Try to parse JSON from response
            try:
                result = json.loads(content)
                # Ensure steps is a list
                if "steps" in result and isinstance(result["steps"], str):
                    # If steps is a string, try to split it
                    result["steps"] = [s.strip() for s in result["steps"].split("\n") if s.strip()]
                elif "steps" not in result:
                    result["steps"] = []
                print(f"DEBUG: LLM suggestion parsed successfully: {result.get('title', 'N/A')} with {len(result.get('steps', []))} steps")
                return result
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON parse error in suggestion: {e}")
                print(f"DEBUG: Response content preview: {content[:300]}")
                # Fallback: try to extract JSON from text
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        if "steps" in result and isinstance(result["steps"], str):
                            result["steps"] = [s.strip() for s in result["steps"].split("\n") if s.strip()]
                        print(f"DEBUG: Extracted JSON from text: {result.get('title', 'N/A')}")
                        return result
                    except json.JSONDecodeError:
                        pass
                
                # Last resort: try to parse as plain text with title and steps
                lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
                if lines:
                    title = lines[0].replace("Title:", "").replace("title:", "").strip()
                    steps = []
                    for line in lines[1:]:
                        line = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                        if line and not line.lower().startswith("title"):
                            steps.append(line)
                    result = {"title": title or "Excel assistance", "steps": steps[:8]}
                    print(f"DEBUG: Parsed as plain text: {result.get('title', 'N/A')} with {len(result.get('steps', []))} steps")
                    return result
                return None
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if hasattr(e, 'read') else str(e)
            print(f"DEBUG: HTTP error in LLM suggestion: {e.code} {e.reason}")
            print(f"DEBUG: Error body: {error_body[:500]}")
            return None
        except Exception as e:
            print(f"DEBUG: Exception in LLM suggestion: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None

