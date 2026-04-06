"""Node for generating SQL query from intent."""
import logging
from typing import Dict, Any
from app.graph.state import AnalystState
from app.llm.client import LLMClient
from app.llm.prompts import get_sql_generator_prompt, get_schema_info

logger = logging.getLogger(__name__)


def generate_sql(state: AnalystState) -> Dict[str, Any]:
    """Generate SQL query from intent."""
    intent = state.get("intent")
    error = state.get("error")
    
    logger.info(f"[generate_sql] Starting SQL generation")
    logger.info(f"[generate_sql] Intent: {intent}")
    logger.info(f"[generate_sql] Previous error: {error}")
    
    if intent is None:
        error_msg = "No intent available for SQL generation"
        logger.error(f"[generate_sql] {error_msg}")
        return {
            "sql_query": None,
            "error": error_msg
        }
    
    try:
        llm_client = LLMClient()
        schema_info = get_schema_info()
        prompt = get_sql_generator_prompt(intent, schema_info)
        logger.debug(f"[generate_sql] Prompt: {prompt}")
        
        response = llm_client.chat_completion(prompt)
        logger.info(f"[generate_sql] LLM response received: {response[:200]}...")
        
        # Clean up SQL query (remove markdown code blocks if present)
        original_response = response
        sql_query = response.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        elif sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        logger.info(f"[generate_sql] Generated SQL: {sql_query}")
        
        return {
            "sql_query": sql_query,
            "error": None
        }
    except Exception as e:
        error_msg = f"SQL generation error: {str(e)}"
        logger.error(f"[generate_sql] Exception: {error_msg}", exc_info=True)
        return {
            "sql_query": None,
            "error": error_msg
        }

