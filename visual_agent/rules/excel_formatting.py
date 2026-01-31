from __future__ import annotations

import re

from .base import Observation, Rule, Suggestion


class ExcelFormattingRule(Rule):
    name = "excel_formatting"

    def match(self, obs: Observation) -> float:
        t = (obs.ocr_text or "").lower()
        title = (obs.active_title or "").lower()
        app = (obs.active_app or "").lower()

        excelish = any(k in title for k in ["excel", "workbook", ".xlsx"]) or "excel" in app
        if not excelish:
            return 0.0

        # Formatting keywords
        formatting_keywords = [
            "format", "formatting", "conditional format", "conditional formatting",
            "cell format", "number format", "currency", "percentage", "date format",
            "format cells", "format painter", "styles", "cell styles",
            "border", "borders", "fill", "background", "font", "font size",
            "merge", "merge cells", "wrap text", "text alignment",
            "format as table", "table style", "autoformat"
        ]

        formatting_detected = any(k in t for k in formatting_keywords)
        
        # Check for Format/Home tab UI elements
        format_ui = any(k in t for k in [
            "home tab", "format cells", "conditional formatting", "format painter",
            "number format", "cell styles", "format as table"
        ])

        if format_ui:
            return 0.90
        if formatting_detected:
            return 0.75
        return 0.0

    def suggest(self, obs: Observation) -> Suggestion:
        t = (obs.ocr_text or "").lower()
        
        if any(k in t for k in ["conditional format", "conditional formatting"]):
            return Suggestion(
                title="Applying conditional formatting in Excel",
                steps=[
                    "Select the cells you want to format conditionally.",
                    "Go to **Home** tab → **Conditional Formatting**.",
                    "Choose a rule type: **Highlight Cells Rules**, **Top/Bottom Rules**, **Data Bars**, **Color Scales**, or **Icon Sets**.",
                    "Select a specific rule (e.g., **Greater Than**, **Color Scales**) and set the criteria.",
                    "Choose a format style or customize colors/fonts.",
                    "Click **OK** to apply. Use **Manage Rules** to edit or delete existing rules.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["format cells", "number format", "currency", "percentage", "date format"]):
            return Suggestion(
                title="Formatting cells in Excel",
                steps=[
                    "Select the cell(s) you want to format.",
                    "Right-click → **Format Cells**, or press **Ctrl+1**, or go to **Home** tab → click the dialog launcher in Number group.",
                    "Choose a category: **Number**, **Currency**, **Accounting**, **Date**, **Time**, **Percentage**, **Text**, etc.",
                    "Set specific options (decimal places, date format, currency symbol, etc.).",
                    "Use other tabs: **Alignment** (text alignment, wrap text, merge), **Font** (font, size, color), **Border**, **Fill** (background).",
                    "Click **OK** to apply formatting.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["format as table", "table style", "table"]):
            return Suggestion(
                title="Formatting data as a table in Excel",
                steps=[
                    "Select your data range (include headers).",
                    "Go to **Home** tab → **Format as Table** (or **Insert** tab → **Table**).",
                    "Choose a table style from the gallery.",
                    "In the dialog: verify the range and check **My table has headers** if applicable.",
                    "Click **OK** to create the table.",
                    "Use **Table Design** tab to change style, add total row, or convert back to range.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["merge", "merge cells", "wrap text", "alignment"]):
            return Suggestion(
                title="Cell alignment and merging in Excel",
                steps=[
                    "Select the cell(s) you want to format.",
                    "For alignment: **Home** tab → use **Align Left**, **Center**, **Align Right**, **Top**, **Middle**, **Bottom**.",
                    "For wrap text: **Home** tab → **Wrap Text** (or **Format Cells** → **Alignment** → check **Wrap text**).",
                    "To merge cells: select the range → **Home** tab → **Merge & Center** (or choose merge option from dropdown).",
                    "Use **Format Cells** → **Alignment** tab for more options (indent, orientation, etc.).",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        # Generic formatting suggestion
        return Suggestion(
            title="Formatting in Excel",
            steps=[
                "Select the cell(s) you want to format.",
                "Use **Home** tab for quick formatting: font, size, color, borders, fill, number format.",
                "For advanced options: right-click → **Format Cells** (or **Ctrl+1**).",
                "Use **Format Painter** (paintbrush icon) to copy formatting from one cell to another.",
                "Use **Conditional Formatting** to format cells based on their values.",
                "Use **Format as Table** to quickly apply professional table styles.",
            ],
            confidence=self.match(obs),
            source=self.name,
        )


