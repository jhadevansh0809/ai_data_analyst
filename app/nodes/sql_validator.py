"""Node for validating SQL queries."""
import re
import logging
from typing import Dict, Any
from app.graph.state import AnalystState

logger = logging.getLogger(__name__)

ALLOWED_TABLES = {"orders", "cafes", "vendors"}
FORBIDDEN_KEYWORDS = {
    "delete", "drop", "truncate", "alter", "create", "insert", 
    "update", "grant", "revoke", "exec", "execute"
}


def validate_sql(state: AnalystState) -> Dict[str, Any]:
    """Validate SQL query for safety."""
    sql_query = state.get("sql_query")
    error = state.get("error")
    
    logger.info(f"[validate_sql] Starting SQL validation")
    logger.info(f"[validate_sql] SQL query: {sql_query}")
    logger.info(f"[validate_sql] Previous error: {error}")
    logger.info(f"[validate_sql] State keys: {list(state.keys())}")
    
    if not sql_query:
        error_msg = "No SQL query to validate"
        logger.error(f"[validate_sql] {error_msg}")
        logger.error(f"[validate_sql] Full state: {state}")
        return {
            "validated_sql": None,
            "error": error_msg
        }
    
    sql_upper = sql_query.upper().strip()
    
    # Check for forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword.upper()}\b", sql_upper):
            return {
                "validated_sql": None,
                "error": f"Forbidden keyword detected: {keyword}"
            }
    
    # Must start with SELECT
    if not sql_upper.startswith("SELECT"):
        return {
            "validated_sql": None,
            "error": "Only SELECT statements are allowed"
        }
    
    # Check for allowed tables only
    sql_lower = sql_query.lower()
    table_pattern = r'\b(from|join)\s+(\w+)'
    matches = re.findall(table_pattern, sql_lower, re.IGNORECASE)
    
    for _, table in matches:
        table_clean = table.strip().lower()
        if table_clean not in ALLOWED_TABLES:
            return {
                "validated_sql": None,
                "error": f"Table '{table_clean}' is not allowed. Allowed tables: {', '.join(ALLOWED_TABLES)}"
            }
    
    # Ensure LIMIT 100 is present
    validated_sql = sql_query.strip()
    if "LIMIT" not in sql_upper:
        # Add LIMIT 100 if not present
        if validated_sql.endswith(";"):
            validated_sql = validated_sql[:-1].strip()
        validated_sql = f"{validated_sql} LIMIT 100"
    else:
        # Replace existing LIMIT with 100
        limit_pattern = r'\bLIMIT\s+\d+'
        if re.search(limit_pattern, sql_upper):
            validated_sql = re.sub(
                limit_pattern,
                "LIMIT 100",
                validated_sql,
                flags=re.IGNORECASE
            )
    
    logger.info(f"[validate_sql] Validation passed. Validated SQL: {validated_sql}")
    return {
        "validated_sql": validated_sql,
        "error": None
    }

