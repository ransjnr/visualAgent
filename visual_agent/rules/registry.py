from __future__ import annotations

from .base import Rule
from .excel_charts import ExcelChartsRule


def build_rules(enabled: list[str]) -> list[Rule]:
    all_rules: dict[str, Rule] = {
        "excel_charts": ExcelChartsRule(),
    }
    out: list[Rule] = []
    for name in enabled:
        r = all_rules.get(name)
        if r:
            out.append(r)
    return out

