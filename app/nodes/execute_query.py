"""Node for executing SQL queries."""
import logging
from typing import Dict, Any
from app.graph.state import AnalystState
from app.database.connection import get_db_manager
from app.database.result_enrichment import enrich_rows_with_entity_names

logger = logging.getLogger(__name__)


def execute_query(state: AnalystState) -> Dict[str, Any]:
    """Execute validated SQL query."""
    validated_sql = state.get("validated_sql")
    retry_count = state.get("retry_count", 0)
    
    logger.info(f"[execute_query] Starting query execution (retry: {retry_count})")
    logger.info(f"[execute_query] SQL: {validated_sql}")
    
    if not validated_sql:
        error_msg = "No validated SQL query to execute"
        logger.error(f"[execute_query] {error_msg}")
        return {
            "query_result": None,
            "error": error_msg
        }
    
    try:
        db_manager = get_db_manager()
        logger.info("[execute_query] Executing query...")
        result = db_manager.execute_query(validated_sql)
        result = enrich_rows_with_entity_names(db_manager, result)
        logger.info(f"[execute_query] Query executed successfully. Rows returned: {len(result)}")
        return {
            "query_result": result,
            "error": None
        }
    except ValueError as e:
        error_msg = f"Database configuration error: {str(e)}"
        logger.error(f"[execute_query] {error_msg}")
        return {
            "query_result": None,
            "error": error_msg
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[execute_query] Query execution failed: {error_msg}", exc_info=True)
        return {
            "query_result": None,
            "error": error_msg,
            "retry_count": retry_count + 1
        }

