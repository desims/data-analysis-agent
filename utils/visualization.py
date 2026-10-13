from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px


def choose_chart(df: pd.DataFrame, x_col: str | None, y_col: str | None = None) -> str:
    if df.empty or x_col is None or x_col not in df.columns:
        return "invalid"

    if y_col is not None and y_col not in df.columns:
        return "invalid"

    x_series = df[x_col]
    y_series = df[y_col] if y_col else None

    if y_col is not None and pd.api.types.is_numeric_dtype(y_series):
        if pd.api.types.is_numeric_dtype(x_series):
            return "scatter"
        if pd.api.types.is_datetime64_any_dtype(x_series) or pd.api.types.is_datetime64tz_dtype(x_series):
            return "line"
        return "bar"

    if pd.api.types.is_datetime64_any_dtype(x_series) or pd.api.types.is_datetime64tz_dtype(x_series):
        return "line"

    if y_col is None:
        return "histogram"

    return "bar"


def make_chart_figure(df: pd.DataFrame, chart_type: str, x_col: str | None, y_col: str | None = None, title: str | None = None) -> Any | None:
    if chart_type == "invalid" or not x_col or x_col not in df.columns:
        return None

    if chart_type == "line":
        if y_col is None or y_col not in df.columns:
            return None
        fig = px.line(df, x=x_col, y=y_col, title=title or f"{y_col} over {x_col}", template="plotly_white")
        return fig

    if chart_type == "bar":
        if y_col is None or y_col not in df.columns:
            return None
        fig = px.bar(df, x=x_col, y=y_col, title=title or f"{y_col} by {x_col}", template="plotly_white")
        return fig

    if chart_type == "scatter":
        if y_col is None or y_col not in df.columns:
            return None
        fig = px.scatter(df, x=x_col, y=y_col, title=title or f"{y_col} vs {x_col}", template="plotly_white")
        return fig

    if chart_type == "histogram":
        fig = px.histogram(df, x=x_col, title=title or f"Distribution of {x_col}", template="plotly_white")
        return fig

    return None
