from __future__ import annotations

import re

from .base import Observation, Rule, Suggestion


class ExcelImportExportRule(Rule):
    name = "excel_import_export"

    def match(self, obs: Observation) -> float:
        t = (obs.ocr_text or "").lower()
        title = (obs.active_title or "").lower()
        app = (obs.active_app or "").lower()

        excelish = any(k in title for k in ["excel", "workbook", ".xlsx"]) or "excel" in app
        if not excelish:
            return 0.0

        # Import/Export keywords
        import_export_keywords = [
            "import", "export", "save as", "export data", "import data",
            "get external data", "from text", "from csv", "from web",
            "from database", "from access", "from sql", "power query",
            "csv", "text file", "delimited", "fixed width",
            "export to pdf", "save as pdf", "print to pdf"
        ]

        import_export_detected = any(k in t for k in import_export_keywords)
        
        # Check for Data/File tab UI elements
        import_export_ui = any(k in t for k in [
            "get data", "from file", "from text/csv", "from web", "from database",
            "save as", "export", "print"
        ])

        if import_export_ui:
            return 0.90
        if import_export_detected:
            return 0.75
        return 0.0

    def suggest(self, obs: Observation) -> Suggestion:
        t = (obs.ocr_text or "").lower()
        
        if any(k in t for k in ["import", "get data", "from text", "from csv", "from file"]):
            return Suggestion(
                title="Importing data into Excel",
                steps=[
                    "Go to **Data** tab → **Get Data** (or **From Text/CSV** for text files).",
                    "For text/CSV: select your file → **Import**. Preview the data and adjust delimiter/encoding if needed.",
                    "For web data: **Get Data** → **From Other Sources** → **From Web**. Enter the URL.",
                    "For database: **Get Data** → **From Database** → choose your database type.",
                    "In the preview: adjust data types, remove columns, or transform data as needed.",
                    "Click **Load** to import to a new worksheet, or **Load To** to choose destination.",
                    "Use **Power Query Editor** for advanced transformations before loading.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        if any(k in t for k in ["export", "save as", "csv", "pdf", "print"]):
            return Suggestion(
                title="Exporting data from Excel",
                steps=[
                    "For CSV: **File** → **Save As** → choose **CSV (Comma delimited) (*.csv)** → **Save**.",
                    "For PDF: **File** → **Save As** → choose **PDF (*.pdf)** → **Save**.",
                    "For printing: **File** → **Print** (or **Ctrl+P**). Adjust settings, then **Print**.",
                    "To export specific range: select it → **File** → **Save As** → choose format.",
                    "For other formats: **File** → **Save As** → choose from the file type dropdown.",
                    "Note: CSV only saves the active sheet and may lose formatting.",
                ],
                confidence=self.match(obs),
                source=self.name,
            )
        
        # Generic import/export suggestion
        return Suggestion(
            title="Importing or exporting data in Excel",
            steps=[
                "To import: **Data** tab → **Get Data** → choose source (File, Database, Web, etc.).",
                "To export to CSV: **File** → **Save As** → **CSV (Comma delimited)**.",
                "To export to PDF: **File** → **Save As** → **PDF**.",
                "Use **Power Query** (Get & Transform Data) for advanced data import and transformation.",
                "For printing: **File** → **Print** to preview and print your worksheet.",
            ],
            confidence=self.match(obs),
            source=self.name,
        )


