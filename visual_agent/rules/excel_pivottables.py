from __future__ import annotations

import re

from .base import Observation, Rule, Suggestion


class ExcelPivotTablesRule(Rule):
    name = "excel_pivottables"

    def match(self, obs: Observation) -> float:
        t = (obs.ocr_text or "").lower()
        title = (obs.active_title or "").lower()
        app = (obs.active_app or "").lower()

        excelish = any(k in title for k in ["excel", "workbook", ".xlsx"]) or "excel" in app
        if not excelish:
            return 0.0

        # PivotTable keywords
        pivot_keywords = [
            "pivot", "pivottable", "pivot table", "pivotchart", "pivot chart",
            "pivot field", "pivot fields", "rows", "columns", "values", "filters",
            "pivot table tools", "analyze", "design", "refresh pivot"
        ]

        pivot_detected = any(k in t for k in pivot_keywords)
        
        # Check for PivotTable UI elements
        pivot_ui = any(k in t for k in [
            "pivot table fields", "field list", "pivot table analyze",
            "pivot table design", "refresh all", "change data source"
        ])

        if pivot_ui:
            return 0.95
        if pivot_detected:
            return 0.85
        return 0.0

    def suggest(self, obs: Observation) -> Suggestion:
        t = (obs.ocr_text or "").lower()
        
        # Check if user is creating or modifying a PivotTable
        if any(k in t for k in ["create", "insert", "new pivot", "pivot table wizard"]):
            return Suggestion(
                title="Creating a PivotTable in Excel",
                steps=[
                    "Select your data range (include headers). Make sure there are no blank rows or columns.",
                    "Go to **Insert** tab → click **PivotTable** (or **Recommended PivotTables** for suggestions).",
                    "In the dialog: verify the data range, choose **New Worksheet** or **Existing Worksheet**.",
                    "Click **OK** to create the PivotTable.",
                    "In the **PivotTable Fields** pane: drag fields to **Rows**, **Columns**, **Values**, or **Filters**.",
                    "For Values: right-click a field → **Value Field Settings** to change calculation (Sum, Count, Average, etc.).",
                    "Use **PivotTable Analyze** and **Design** tabs to format and customize your PivotTable.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["refresh", "update", "change data source"]):
            return Suggestion(
                title="Refreshing or updating a PivotTable in Excel",
                steps=[
                    "Click anywhere inside the PivotTable to activate it.",
                    "Go to **PivotTable Analyze** tab (or **Analyze** in older Excel).",
                    "Click **Refresh** to update with latest data, or **Refresh All** to update all PivotTables.",
                    "To change the data source: **PivotTable Analyze** → **Change Data Source** → select new range.",
                    "To update automatically: **PivotTable Analyze** → **Options** → check **Refresh data when opening the file**.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        # Generic PivotTable suggestion
        return Suggestion(
            title="Working with PivotTables in Excel",
            steps=[
                "Click inside your PivotTable to activate it.",
                "Use the **PivotTable Fields** pane to add/remove fields from Rows, Columns, Values, or Filters.",
                "Right-click any field in the Values area → **Value Field Settings** to change calculations.",
                "Use **PivotTable Analyze** tab to refresh data, change data source, or insert slicers/timelines.",
                "Use **Design** tab to change layout, style, and formatting options.",
                "To create a chart: **PivotTable Analyze** → **PivotChart**.",
            ],
            confidence=self.match(obs),
            source=self.name,
        )


