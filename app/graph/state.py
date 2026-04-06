"""State definition for LangGraph workflow."""
from typing import Annotated, TypedDict
from operator import add


class AnalystState(TypedDict):
    """State for the AI Data Analyst workflow."""
    messages: Annotated[list, add]  # Accumulated conversation / trace messages across nodes
    user_question: str  # Raw user question coming into the workflow
    intent: dict | None  # Structured intent JSON derived from the question (filters/metrics/grouping)
    sql_query: str | None  # Candidate SQL generated from the intent (pre-validation)
    validated_sql: str | None  # Safety-checked SQL that is allowed to execute (SELECT-only, LIMIT enforced)
    query_result: list | None  # Query results (list of row dicts) returned from the database
    insights: str | None  # Natural-language analysis/insights derived from query_result
    error: str | None  # Error message from any step (parsing/generation/validation/execution/analysis)
    retry_count: int  # Number of SQL execution retries attempted so far (max 2)

