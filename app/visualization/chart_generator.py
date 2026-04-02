"""Plotly chart generator.

Takes a pandas DataFrame and a selected chart type and returns a Plotly
figure as a JSON-serializable dict suitable for sending to the frontend.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import plotly.express as px

from app.visualization.chart_selector import ChartType


def prepare_dataframe_for_charts(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce SQL/driver types so numeric and date columns are usable for charts.

    Database drivers often return numbers as ``Decimal`` or strings, which pandas
    stores as ``object``. Without coercion, chart selection sees no numeric
    columns and falls back to a plain table (values only in the UI).
    """
    if df.empty:
        return df
    out = df.copy()

    # Parse obvious date/time columns first (before numeric coercion).
    for col in list(out.columns):
        col_lower = str(col).lower()
        if not any(k in col_lower for k in ("date", "time", "month", "year")):
            continue
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            continue
        parsed = pd.to_datetime(out[col], errors="coerce")
        if parsed.notna().sum() >= max(1, int(len(out) * 0.5)):
            out[col] = parsed

    # Coerce int/float/Decimal/numeric strings to numeric dtypes.
    for col in list(out.columns):
        if pd.api.types.is_numeric_dtype(out[col]):
            continue
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            continue
        converted = pd.to_numeric(out[col], errors="coerce")
        if converted.notna().sum() >= max(1, int(len(out) * 0.5)):
            out[col] = converted

    return out


class ChartGenerator:
    """Generate Plotly charts from dataframes."""

    @staticmethod
    def _pick_time_and_metric(df: pd.DataFrame) -> tuple[Optional[str], Optional[str]]:
        datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        # Fallback: use name heuristics for datetime-like
        if not datetime_cols:
            for col in df.columns:
                col_lower = col.lower()
                if any(k in col_lower for k in ["date", "time", "month", "year"]):
                    datetime_cols.append(col)

        time_col = datetime_cols[0] if datetime_cols else None
        metric_col = numeric_cols[0] if numeric_cols else None
        return time_col, metric_col

    @staticmethod
    def _pick_category_and_metric(df: pd.DataFrame) -> tuple[Optional[str], Optional[str]]:
        object_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        category_col = object_cols[0] if object_cols else None
        metric_col = numeric_cols[0] if numeric_cols else None
        return category_col, metric_col

    @staticmethod
    def _pick_two_numeric(df: pd.DataFrame) -> tuple[Optional[str], Optional[str]]:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if len(numeric_cols) < 2:
            return None, None
        return numeric_cols[0], numeric_cols[1]

    @staticmethod
    def generate_chart(df: pd.DataFrame, chart_type: ChartType, title: str | None = None) -> Dict[str, Any]:
        """Generate a Plotly figure dict for the given chart type.

        The returned dict is safe to JSON-serialize on the FastAPI side.
        """
        if df.empty:
            # Frontend can render its own "no data" state
            return {
                "data": [],
                "layout": {"title": title or "No data", "xaxis": {}, "yaxis": {}},
            }

        fig = None

        if chart_type == "line":
            x, y = ChartGenerator._pick_time_and_metric(df)
            if x and y:
                fig = px.line(df, x=x, y=y, title=title or f"{y} over {x}")

        elif chart_type in ("bar", "bar_horizontal"):
            cat, metric = ChartGenerator._pick_category_and_metric(df)
            if cat and metric:
                if chart_type == "bar_horizontal":
                    fig = px.bar(df, x=metric, y=cat, orientation="h", title=title or f"{metric} by {cat}")
                else:
                    fig = px.bar(df, x=cat, y=metric, title=title or f"{metric} by {cat}")
            elif chart_type == "bar" and metric and not cat and len(df) > 1:
                # One numeric column only (no category): bar against row index
                fig = px.bar(
                    df.assign(_row=df.index.astype(str)),
                    x="_row",
                    y=metric,
                    title=title or str(metric),
                )
                fig.update_layout(xaxis_title="")

        elif chart_type == "scatter":
            x, y = ChartGenerator._pick_two_numeric(df)
            if x and y:
                fig = px.scatter(df, x=x, y=y, title=title or f"{y} vs {x}")

        # Fallback: simple table-like representation (frontend can render pretty)
        if fig is None:
            # Represent as a generic JSON with rows/columns, not a Plotly figure
            return {
                "type": "table",
                "columns": list(df.columns),
                "rows": df.to_dict(orient="records"),
                "title": title or "Table",
            }

        # Return Plotly JSON (dict form)
        return fig.to_dict()


# Convenience function
def generate_chart(df: pd.DataFrame, chart_type: ChartType, title: Optional[str] = None) -> Dict[str, Any]:
    return ChartGenerator.generate_chart(df, chart_type, title=title)


