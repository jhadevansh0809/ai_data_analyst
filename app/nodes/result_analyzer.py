"""Node for analyzing query results and generating insights."""
import logging
from typing import Dict, Any
from app.graph.state import AnalystState
from app.llm.client import LLMClient
from app.llm.prompts import get_result_analyzer_prompt

logger = logging.getLogger(__name__)


def analyze_results(state: AnalystState) -> Dict[str, Any]:
    """Analyze query results and generate insights."""
    query_result = state.get("query_result")
    user_question = state.get("user_question", "")
    validated_sql = state.get("validated_sql", "")
    
    logger.info(f"[analyze_results] Starting result analysis")
    logger.info(f"[analyze_results] Query result count: {len(query_result) if query_result else 0}")
    
    if not query_result:
        original_error = state.get("error")
        error_msg = original_error or "No query results to analyze"
        logger.error(f"[analyze_results] {error_msg}")
        return {
            "insights": None,
            "error": error_msg
        }
    
    try:
        llm_client = LLMClient()
        prompt = get_result_analyzer_prompt(user_question, query_result, validated_sql)
        logger.debug(f"[analyze_results] Prompt: {prompt}")
        
        insights = llm_client.chat_completion(prompt)
        logger.info(f"[analyze_results] Insights generated: {insights[:200]}...")
        
        return {
            "insights": insights,
            "error": None
        }
    except Exception as e:
        error_msg = f"Result analysis error: {str(e)}"
        logger.error(f"[analyze_results] Exception: {error_msg}", exc_info=True)
        return {
            "insights": None,
            "error": error_msg
        }

