from __future__ import annotations

import re

from .base import Observation, Rule, Suggestion


class ExcelChartsRule(Rule):
    name = "excel_charts"

    def match(self, obs: Observation) -> float:
        t = (obs.ocr_text or "").lower()
        title = (obs.active_title or "").lower()
        app = (obs.active_app or "").lower()

        # Heuristics: we can't "see tabs" reliably everywhere, so combine OCR + window hints.
        excelish = any(k in title for k in ["excel", "workbook", ".xlsx"]) or "excel" in app
        chartish = any(k in t for k in ["chart", "charts", "pivotchart", "graph"]) or "chart" in title

        # Also match when user is in data/table context and likely wants to visualize.
        dataish = bool(re.search(r"\b(sum|average|count|min|max)\b", t)) or "table" in t or "pivot" in t

        if excelish and chartish:
            return 0.9
        if excelish and dataish:
            return 0.6
        if chartish:
            return 0.4
        return 0.0

    def suggest(self, obs: Observation) -> Suggestion:
        # Generic Excel chart flow that applies to desktop + web variants.
        steps = [
            "Select the data range you want to plot (include headers).",
            "Go to the **Insert** tab (or **Insert** menu in Excel for web).",
            "Pick a chart type (Start with **Recommended Charts** if you’re unsure).",
            "If the chart looks wrong: use **Switch Row/Column** and verify headers are recognized.",
            "Use **Chart Design / Format** to add axis titles, legend, and data labels.",
        ]
        # If OCR indicates pivot context, suggest pivot chart path.
        t = (obs.ocr_text or "").lower()
        if "pivot" in t:
            steps.insert(2, "If you’re using a PivotTable: click inside it → **Insert** → **PivotChart**.")

        return Suggestion(
            title="Looks like you're making a chart in Excel",
            steps=steps,
            confidence=self.match(obs),
            source=self.name,
        )

