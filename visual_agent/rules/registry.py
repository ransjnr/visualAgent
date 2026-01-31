from __future__ import annotations

from .base import Rule
from .excel_charts import ExcelChartsRule
from .excel_data_analysis import ExcelDataAnalysisRule
from .excel_formatting import ExcelFormattingRule
from .excel_formulas import ExcelFormulasRule
from .excel_import_export import ExcelImportExportRule
from .excel_llm import ExcelLLMRule
from .excel_pivottables import ExcelPivotTablesRule


def build_rules(enabled: list[str], llm_client=None) -> list[Rule]:
    """
    Build rules from enabled list. LLM-powered rules will receive the llm_client.
    """
    # Rules that need LLM client
    llm_rules: dict[str, type] = {
        "excel_llm": ExcelLLMRule,
    }
    
    # Traditional hardcoded rules (kept for fallback or specific use cases)
    traditional_rules: dict[str, Rule] = {
        "excel_charts": ExcelChartsRule(),
        "excel_formulas": ExcelFormulasRule(),
        "excel_pivottables": ExcelPivotTablesRule(),
        "excel_data_analysis": ExcelDataAnalysisRule(),
        "excel_formatting": ExcelFormattingRule(),
        "excel_import_export": ExcelImportExportRule(),
    }
    
    out: list[Rule] = []
    for name in enabled:
        # Check if it's an LLM-powered rule
        if name in llm_rules:
            rule_class = llm_rules[name]
            out.append(rule_class(llm_client))
        # Otherwise use traditional rule
        elif name in traditional_rules:
            out.append(traditional_rules[name])
    return out

