"""Chart selection logic for automatic visualization.

Given a pandas DataFrame and (optionally) the original user query,
this module decides which high-level chart type to use.
"""

from __future__ import annotations

from typing import Literal, Optional

import pandas as pd

ChartType = Literal["line", "bar", "bar_horizontal", "scatter", "table"]


class ChartSelector:
    """Heuristic chart selector based on dataframe schema and user query."""

    @staticmethod
    def select_chart_type(df: pd.DataFrame, user_query: str | None = None) -> ChartType:
        """Decide the best chart type based on dataframe columns and query text.

        Heuristics:
        - Time-like column + numeric metric(s) -> line chart
        - Categorical + numeric metric -> vertical bar chart
        - Ranking / "top" queries -> horizontal bar chart
        - Two numeric columns -> scatter
        - Fallback -> table (no strong signal)
        """
        if df.empty or df.shape[1] == 0:
            return "table"

        user_query_lower = (user_query or "").lower()

        # Basic column type grouping
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
        object_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        # Also treat obvious date-like column names as datetime proxies
        for col in df.columns:
            col_lower = col.lower()
            if any(k in col_lower for k in ["date", "time", "month", "year"]) and col not in datetime_cols:
                datetime_cols.append(col)

        # 1) Time-series style -> line chart
        if datetime_cols and numeric_cols:
            return "line"

        # 2) Ranking / "top" / "highest" -> horizontal bar
        if any(kw in user_query_lower for kw in ["top ", "rank", "highest", "lowest", "most", "least"]):
            if object_cols and numeric_cols:
                return "bar_horizontal"

        # 3) Generic category + metric -> bar
        if object_cols and numeric_cols:
            return "bar"

        # 4) Two numeric columns -> scatter
        if len(numeric_cols) >= 2:
            return "scatter"

        # 5) One numeric column, multiple rows -> bar (e.g. single aggregate broken out by row)
        if len(numeric_cols) == 1 and len(df) > 1:
            return "bar"

        # 6) Fallback -> table
        return "table"


# Convenience function
def select_chart_type(df: pd.DataFrame, user_query: Optional[str] = None) -> ChartType:
    return ChartSelector.select_chart_type(df, user_query=user_query)


