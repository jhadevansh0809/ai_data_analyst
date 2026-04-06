"""LangGraph workflow builder."""
from langgraph.graph import StateGraph, END
from app.graph.state import AnalystState
from app.nodes.intent_parser import parse_intent
from app.nodes.sql_generator import generate_sql
from app.nodes.sql_validator import validate_sql
from app.nodes.execute_query import execute_query
from app.nodes.result_analyzer import analyze_results
from app.nodes.formatter import format_response


def should_retry(state: AnalystState) -> str:
    """Conditional edge: decide if we should retry SQL execution."""
    error = state.get("error")
    retry_count = state.get("retry_count", 0)
    validated_sql = state.get("validated_sql")
    
    # Retry if there's an error, we have SQL, and retry count < 2
    if error and validated_sql and retry_count < 2:
        return "retry"
    return "continue"


def should_validate(state: AnalystState) -> str:
    """Conditional edge: check if SQL validation passed."""
    error = state.get("error")
    validated_sql = state.get("validated_sql")
    
    if error:
        return "error"
    if validated_sql:
        return "execute"
    return "error"


def build_graph() -> StateGraph:
    """Build the LangGraph workflow."""
    workflow = StateGraph(AnalystState)
    
    # Add nodes
    workflow.add_node("parse_intent", parse_intent)
    workflow.add_node("generate_sql", generate_sql)
    workflow.add_node("validate_sql", validate_sql)
    workflow.add_node("execute_query", execute_query)
    workflow.add_node("analyze_results", analyze_results)
    workflow.add_node("format_response", format_response)
    
    # Define edges
    workflow.set_entry_point("parse_intent")
    
    workflow.add_edge("parse_intent", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")
    
    # Conditional edge: validate SQL
    workflow.add_conditional_edges(
        "validate_sql",
        should_validate,
        {
            "execute": "execute_query",
            "error": "format_response"
        }
    )
    
    # Conditional edge: retry logic
    workflow.add_conditional_edges(
        "execute_query",
        should_retry,
        {
            "retry": "execute_query",
            "continue": "analyze_results"
        }
    )
    
    workflow.add_edge("analyze_results", "format_response")
    workflow.add_edge("format_response", END)
    
    return workflow.compile()


