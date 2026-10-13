from __future__ import annotations

from typing import Any


def build_markdown_report(question: str, profile: dict[str, Any], answer: str, dataset_name: str = "uploaded_dataset") -> str:
    lines = [
        "# Data Analysis Report",
        "",
        f"- Dataset: {dataset_name}",
        f"- Question: {question}",
        "",
        "## Dataset Summary",
        f"- Rows: {profile.get('row_count', 0)}",
        f"- Columns: {profile.get('column_count', 0)}",
        f"- Columns: {', '.join(profile.get('columns', [])) or 'None'}",
        "",
        "## Findings",
        answer.strip() if answer.strip() else "No narrative answer was provided.",
    ]
    return "\n".join(lines)
