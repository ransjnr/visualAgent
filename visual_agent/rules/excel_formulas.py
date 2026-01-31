from __future__ import annotations

import re

from .base import Observation, Rule, Suggestion


class ExcelFormulasRule(Rule):
    name = "excel_formulas"

    def match(self, obs: Observation) -> float:
        t = (obs.ocr_text or "").lower()
        title = (obs.active_title or "").lower()
        app = (obs.active_app or "").lower()

        excelish = any(k in title for k in ["excel", "workbook", ".xlsx"]) or "excel" in app
        if not excelish:
            return 0.0

        # Common Excel formulas and functions
        formula_keywords = [
            "sum", "average", "count", "min", "max", "if", "vlookup", "hlookup",
            "index", "match", "sumif", "countif", "sumifs", "countifs",
            "concatenate", "text", "date", "today", "now", "year", "month", "day",
            "left", "right", "mid", "len", "find", "search", "substitute", "replace",
            "round", "roundup", "rounddown", "abs", "sqrt", "power",
            "and", "or", "not", "iserror", "isblank", "isnumber", "istext",
            "lookup", "xlookup", "filter", "sort", "unique",
            "formula", "function", "fx", "=", "=sum", "=if", "=vlookup"
        ]

        # Check for formula-related UI elements
        formula_ui = any(k in t for k in ["formula bar", "fx button", "insert function", "function library"])
        
        # Check for actual formula keywords
        formula_detected = any(re.search(rf"\b{kw}\b", t) for kw in formula_keywords)
        
        # Check for formula syntax patterns
        formula_syntax = bool(re.search(r"=\s*\w+\s*\(", t)) or "=" in t

        if formula_ui:
            return 0.95
        if formula_detected and formula_syntax:
            return 0.85
        if formula_detected:
            return 0.70
        if formula_syntax:
            return 0.60
        return 0.0

    def suggest(self, obs: Observation) -> Suggestion:
        t = (obs.ocr_text or "").lower()
        
        # Detect specific formula types for tailored suggestions
        if any(k in t for k in ["vlookup", "hlookup", "lookup", "xlookup"]):
            return Suggestion(
                title="Working with lookup formulas in Excel",
                steps=[
                    "Click the cell where you want the result.",
                    "Type **=VLOOKUP(** (or **=XLOOKUP(** for newer Excel).",
                    "Enter the lookup value (what you're searching for).",
                    "Select the table array (the data range to search in).",
                    "Enter the column number (VLOOKUP) or return array (XLOOKUP).",
                    "For VLOOKUP: add **FALSE** for exact match or **TRUE** for approximate.",
                    "Press **Enter** to complete the formula.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["sumif", "countif", "sumifs", "countifs"]):
            return Suggestion(
                title="Using conditional sum/count formulas in Excel",
                steps=[
                    "Click the cell where you want the result.",
                    "Type **=SUMIF(** or **=COUNTIF(** for single condition.",
                    "For multiple conditions, use **=SUMIFS(** or **=COUNTIFS(**.",
                    "Select the range to evaluate (criteria range).",
                    "Enter the condition (e.g., \">100\", \"=\"\"text\"\"\", or a cell reference).",
                    "For SUMIF/SUMIFS: select the sum range (the values to add).",
                    "Press **Enter** to complete the formula.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["if", "nested if", "if statement"]):
            return Suggestion(
                title="Creating IF formulas in Excel",
                steps=[
                    "Click the cell where you want the result.",
                    "Type **=IF(** to start the formula.",
                    "Enter the logical test (e.g., **A1>10**, **B2=\"Yes\"**).",
                    "Add a comma, then the value if TRUE (e.g., **\"Pass\"**, **100**).",
                    "Add a comma, then the value if FALSE (e.g., **\"Fail\"**, **0**).",
                    "For multiple conditions, nest IF functions: **=IF(condition1, value1, IF(condition2, value2, value3))**.",
                    "Press **Enter** to complete the formula.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["index", "match"]):
            return Suggestion(
                title="Using INDEX and MATCH in Excel",
                steps=[
                    "Click the cell where you want the result.",
                    "Type **=INDEX(** to start the formula.",
                    "Select the array/range where you want to return a value from.",
                    "Type **,MATCH(** to find the position.",
                    "Enter the lookup value (what you're searching for).",
                    "Select the lookup array (where to search).",
                    "Add **,0)** for exact match, then close with **)**.",
                    "Press **Enter** to complete the formula.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        # Generic formula suggestion
        return Suggestion(
            title="Working with formulas in Excel",
            steps=[
                "Click the cell where you want the result.",
                "Type **=** to start a formula, or click the **fx** button to use Function Wizard.",
                "Type the function name (e.g., **SUM**, **AVERAGE**, **IF**) followed by **(**.",
                "Select the cells or ranges you want to include (click and drag, or type cell references).",
                "Use **:** for ranges (e.g., **A1:A10**), **,** to separate arguments.",
                "Close with **)** and press **Enter** to complete.",
                "To edit: click the cell and modify in the formula bar, or press **F2**.",
            ],
            confidence=self.match(obs),
            source=self.name,
        )

