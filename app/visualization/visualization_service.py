"""High-level visualization service combining selector + generator."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import pandas as pd

from app.visualization.chart_selector import ChartType, select_chart_type
from app.visualization.chart_generator import generate_chart, prepare_dataframe_for_charts


class VisualizationService:
    """Service that turns raw query results into chart JSON."""

    @staticmethod
    def create_visualization(
        query_result: list[dict],
        user_query: str,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Create a chart JSON object from query results.

        Returns (chart_json, chart_type).
        """
        if not query_result:
            return None, None

        # Use pandas as the intermediate format
        df = prepare_dataframe_for_charts(pd.DataFrame(query_result))

        chart_type: ChartType = select_chart_type(df, user_query=user_query)
        chart_json = generate_chart(df, chart_type, title=user_query)

        return chart_json, chart_type


# Singleton-style instance
visualization_service = VisualizationService()


