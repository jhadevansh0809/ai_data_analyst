"""Node for formatting final response."""
import logging
from typing import Dict, Any
from app.graph.state import AnalystState

logger = logging.getLogger(__name__)


def format_response(state: AnalystState) -> Dict[str, Any]:
    """Format the final response for the user."""
    insights = state.get("insights")
    error = state.get("error")
    query_result = state.get("query_result")
    
    logger.info(f"[format_response] Formatting response")
    logger.info(f"[format_response] Has insights: {insights is not None}")
    logger.info(f"[format_response] Has error: {error is not None}")
    logger.info(f"[format_response] Has query_result: {query_result is not None}")
    
    if error:
        logger.warning(f"[format_response] Returning error response: {error}")
        return {
            "messages": [{
                "role": "assistant",
                "content": f"I encountered an error: {error}. Please try rephrasing your question."
            }]
        }
    
    if insights:
        logger.info(f"[format_response] Returning insights response")
        return {
            "messages": [{
                "role": "assistant",
                "content": insights
            }]
        }
    
    # Fallback: return raw results if no insights
    if query_result:
        logger.info(f"[format_response] Returning fallback response with query results")
        return {
            "messages": [{
                "role": "assistant",
                "content": f"Query executed successfully. Found {len(query_result)} results."
            }]
        }
    
    logger.warning("[format_response] No response content available")
    return {
        "messages": [{
            "role": "assistant",
            "content": "I couldn't generate a response. Please try again."
        }]
    }

