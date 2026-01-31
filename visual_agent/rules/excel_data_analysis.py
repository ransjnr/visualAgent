from __future__ import annotations

import re

from .base import Observation, Rule, Suggestion


class ExcelDataAnalysisRule(Rule):
    name = "excel_data_analysis"

    def match(self, obs: Observation) -> float:
        t = (obs.ocr_text or "").lower()
        title = (obs.active_title or "").lower()
        app = (obs.active_app or "").lower()

        excelish = any(k in title for k in ["excel", "workbook", ".xlsx"]) or "excel" in app
        if not excelish:
            return 0.0

        # Data analysis keywords
        analysis_keywords = [
            "sort", "filter", "autofilter", "advanced filter", "sort & filter",
            "data validation", "validation", "drop down", "dropdown", "list",
            "remove duplicates", "duplicates", "unique values",
            "text to columns", "text to columns", "split", "delimiter",
            "group", "ungroup", "subtotal", "outline",
            "what-if analysis", "goal seek", "scenario", "data table",
            "solver", "analysis toolpak"
        ]

        analysis_detected = any(k in t for k in analysis_keywords)
        
        # Check for Data tab UI elements
        data_ui = any(k in t for k in [
            "data tab", "sort & filter", "data tools", "data validation",
            "text to columns", "remove duplicates", "consolidate"
        ])

        if data_ui:
            return 0.90
        if analysis_detected:
            return 0.75
        return 0.0

    def suggest(self, obs: Observation) -> Suggestion:
        t = (obs.ocr_text or "").lower()
        
        if any(k in t for k in ["sort", "sorting"]):
            return Suggestion(
                title="Sorting data in Excel",
                steps=[
                    "Select the data range you want to sort (include headers).",
                    "Go to **Data** tab → click **Sort** (or use **Sort A to Z** / **Sort Z to A** for simple sorts).",
                    "In the Sort dialog: choose the column to sort by, sort order (A-Z, Z-A, or custom).",
                    "For multiple levels: click **Add Level** to sort by additional columns.",
                    "Check **My data has headers** if your first row contains headers.",
                    "Click **OK** to apply the sort.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["filter", "autofilter", "advanced filter"]):
            return Suggestion(
                title="Filtering data in Excel",
                steps=[
                    "Select your data range (include headers).",
                    "Go to **Data** tab → click **Filter** (or **Advanced** for complex criteria).",
                    "Click the dropdown arrow in any column header to see filter options.",
                    "Use checkboxes to show/hide specific values, or use **Text Filters** / **Number Filters** for conditions.",
                    "To filter by multiple columns: apply filters to each column as needed.",
                    "To clear filters: **Data** tab → **Clear** (or click the filter icon again).",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["data validation", "validation", "drop down", "dropdown", "list"]):
            return Suggestion(
                title="Creating data validation in Excel",
                steps=[
                    "Select the cell(s) where you want validation.",
                    "Go to **Data** tab → **Data Validation** (or **Data Tools** → **Data Validation**).",
                    "In the **Settings** tab: choose **Allow** type (List, Whole Number, Date, etc.).",
                    "For dropdown lists: choose **List**, then enter values separated by commas or select a range.",
                    "Use **Input Message** tab to show a hint when the cell is selected.",
                    "Use **Error Alert** tab to customize the error message for invalid entries.",
                    "Click **OK** to apply validation.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["remove duplicates", "duplicates", "unique"]):
            return Suggestion(
                title="Removing duplicates in Excel",
                steps=[
                    "Select the data range (include headers if present).",
                    "Go to **Data** tab → **Remove Duplicates**.",
                    "In the dialog: check **My data has headers** if applicable.",
                    "Select which columns to check for duplicates (or leave all checked to find rows that are identical across all columns).",
                    "Click **OK** to remove duplicates. Excel will show how many duplicates were found and removed.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["text to columns", "split", "delimiter"]):
            return Suggestion(
                title="Splitting text into columns in Excel",
                steps=[
                    "Select the column(s) containing the text you want to split.",
                    "Go to **Data** tab → **Text to Columns**.",
                    "Choose **Delimited** (if separated by commas, tabs, etc.) or **Fixed Width** (if aligned in columns).",
                    "For Delimited: select the delimiter (comma, tab, space, semicolon, or custom).",
                    "Preview the results in the dialog, adjust column breaks if needed.",
                    "Choose the destination (new columns or overwrite existing).",
                    "Click **Finish** to split the text.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        # Generic data analysis suggestion
        return Suggestion(
            title="Data analysis tools in Excel",
            steps=[
                "Go to the **Data** tab for sorting, filtering, and data tools.",
                "Use **Sort & Filter** for organizing your data.",
                "Use **Data Validation** to create dropdown lists and restrict input.",
                "Use **Text to Columns** to split data in a column.",
                "Use **Remove Duplicates** to clean your data.",
                "Use **What-If Analysis** (Goal Seek, Scenario Manager, Data Tables) for advanced analysis.",
            ],
            confidence=self.match(obs),
            source=self.name,
        )


