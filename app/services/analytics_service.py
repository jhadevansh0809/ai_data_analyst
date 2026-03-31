"""High-level analytics service orchestrating the existing LangGraph
pipeline with conversation memory, visualization, and PDF reports.

IMPORTANT: This module does NOT modify the existing SQL generation
pipeline. It simply calls the compiled graph the same way the /ask
endpoint does, then adds visualization + reporting on top.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np
from app.chat.conversation_manager import conversation_manager
from app.graph.state import AnalystState
from app.reports.report_generator import report_generator
from app.visualization.visualization_service import visualization_service


class AnalyticsService:
    """Main entry point for chat-based analytics."""

    def __init__(self, graph) -> None:  # graph: compiled LangGraph
        self.graph = graph

    def _build_user_question_with_context(self, conversation_id: str, user_query: str) -> str:
        """Augment the raw user query with brief conversation context.

        This preserves the internal graph nodes while giving the LLM
        extra context for follow-up questions.
        """
        context = conversation_manager.get_context_summary(conversation_id)
        if not context:
            return user_query.strip()

        return (
            "You are continuing a conversation with the user. "
            "Here is the recent context:\n"
            f"{context}\n\n"
            f"Current user question: {user_query.strip()}"
        )

    def run_chat_analysis(
        self,
        conversation_id: str,
        user_query: str,
    ) -> Dict[str, Any]:
        """Run the full analytics pipeline for a chat request.

        Returns a dict matching the desired chat response format:
        {
            "message": "...",
            "sql_query": "...",
            "chart": {...},
            "report_id": "...",
        }
        """
        # 0) Lightweight small-talk / greeting handling to avoid
        # unnecessary SQL generation when the user is not asking
        # a data-related question.
        normalized = user_query.strip().lower()
        small_talk_phrases = {"hi", "hello", "hey", "hi!", "hello!", "hey!", "hi there", "hello there"}
        if any(normalized.startswith(p) for p in small_talk_phrases) or normalized in {"thanks", "thank you"}:
            message = (
                "Hi! I'm your AI data analyst. I can help you explore your data with SQL, charts, "
                "and PDF reports. Try asking something like 'Show monthly revenue for this year'."
            )
            # We still record the turn so the conversation history is consistent,
            # but we skip the heavy LangGraph / SQL pipeline.
            conversation_manager.add_turn(
                conversation_id=conversation_id,
                user_query=user_query,
                sql_query=None,
                insights=message,
                chart_type=None,
                report_id=None,
            )
            return {
                "message": message,
                "sql_query": "",
                "chart": None,
                "report_id": None,
            }

        # 1) Build state for the existing graph
        augmented_question = self._build_user_question_with_context(conversation_id, user_query)
        initial_state: AnalystState = {
            "messages": [],
            "user_question": augmented_question,
            "intent": None,
            "sql_query": None,
            "validated_sql": None,
            "query_result": None,
            "insights": None,
            "error": None,
            "retry_count": 0,
        }

        # 2) Run the compiled graph (existing pipeline)
        final_state = self.graph.invoke(initial_state)

        insights: Optional[str] = final_state.get("insights")
        validated_sql: Optional[str] = final_state.get("validated_sql")
        sql_query: Optional[str] = final_state.get("sql_query")
        query_result: Optional[list[dict]] = final_state.get("query_result")
        error: Optional[str] = final_state.get("error")
        intent: Optional[dict] = final_state.get("intent")

        # 2a) If we couldn't derive a usable intent / SQL / result, fail fast
        if not intent or (not validated_sql and not sql_query) or (not query_result and not insights):
            message = (
                "I couldn't process that message as a data question. "
                "Please try asking something specific about your data, e.g. "
                "\"Show monthly revenue for this year\"."
            )
            conversation_manager.add_turn(
                conversation_id=conversation_id,
                user_query=user_query,
                sql_query=None,
                insights=message,
                chart_type=None,
                report_id=None,
            )
            return {
                "message": message,
                "sql_query": "",
                "chart": None,
                "report_id": None,
            }

        # The user-facing message is the insights (or error message)
        if error and not insights:
            message = f"An error occurred: {error}"
        else:
            message = insights or "No insights were generated."

        # Prefer validated SQL if available
        final_sql = validated_sql or sql_query or ""

        # 3) Visualization from query_result
        chart_json: Optional[Dict[str, Any]] = None
        chart_type: Optional[str] = None
        if query_result:
            raw_chart_json, chart_type = visualization_service.create_visualization(
                query_result=query_result,
                user_query=user_query,
            )
            # Ensure the chart is fully JSON-serializable (no numpy types or other objects)
            def make_json_safe(value: Any) -> Any:
                if isinstance(value, dict):
                    return {str(k): make_json_safe(v) for k, v in value.items()}
                if isinstance(value, (list, tuple)):
                    return [make_json_safe(v) for v in value]
                if isinstance(value, np.ndarray):
                    return value.tolist()
                if isinstance(value, np.generic):
                    return value.item()
                return value

            chart_json = make_json_safe(raw_chart_json) if raw_chart_json is not None else None

        # 4) PDF report generation
        chart_description = None
        if chart_type:
            chart_description = f"Automatically generated {chart_type} chart for the query result."

        report_id = report_generator.generate_report(
            user_query=user_query,
            sql_query=final_sql,
            insights=insights or message,
            chart_description=chart_description,
            chart_json=chart_json,
        )

        # 5) Update conversation memory
        conversation_manager.add_turn(
            conversation_id=conversation_id,
            user_query=user_query,
            sql_query=final_sql,
            insights=insights or message,
            chart_type=chart_type,
            report_id=report_id,
        )

        return {
            "message": message,
            "sql_query": final_sql,
            "chart": chart_json,
            "report_id": report_id,
        }


def create_analytics_service(graph) -> AnalyticsService:
    """Factory used from FastAPI startup to inject the compiled graph."""
    return AnalyticsService(graph)


