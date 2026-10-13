from __future__ import annotations

import warnings
from typing import Any

import pandas as pd


def _looks_like_datetime(series: pd.Series) -> bool:
    if series.empty:
        return False
    sample = series.dropna().head(10)
    if sample.empty:
        return False
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Could not infer format.*")
            parsed = pd.to_datetime(sample, errors="raise")
        return parsed.notna().all()
    except (TypeError, ValueError):
        return False


def summarize_dataset(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        raise ValueError("Dataset cannot be summarized because it is empty.")

    datetime_columns = [col for col in df.columns if _looks_like_datetime(df[col])]
    numeric_columns = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    categorical_columns = [
        col for col in df.columns if col not in datetime_columns and not pd.api.types.is_numeric_dtype(df[col])
    ]

    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": {col: int(val) for col, val in df.isna().sum().items()},
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "datetime_columns": datetime_columns,
        "preview": df.head(5).to_dict(orient="records"),
        "summary_stats": {
            col: df[col].describe().to_dict() for col in numeric_columns
        },
    }
