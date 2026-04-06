"""Prompts for LLM interactions."""
from typing import Dict, Any


def get_intent_parser_prompt(user_question: str) -> list[dict]:
    """Prompt for parsing user intent into structured JSON."""
    return [
        {
            "role": "system",
            "content": """You are an intent parser for a data analyst system. 
Convert the user's natural language question into a structured JSON intent.

The intent should include:
- question_type: "aggregation", "filtering", "comparison", "trend_analysis", or "general"
- entities: list of relevant entities (e.g., ["orders", "cafes", "vendors"])
- filters: dict of filters to apply (e.g., {"date_range": "last_month", "status": "completed"})
- metrics: list of metrics to calculate (e.g., ["total_revenue", "average_order_value"])
- grouping: list of fields to group by (e.g., ["cafe_id", "vendor_id"])

Return ONLY valid JSON, no additional text."""
        },
        {
            "role": "user",
            "content": f"Parse this question into intent JSON: {user_question}"
        }
    ]


def get_sql_generator_prompt(intent: Dict[str, Any], schema_info: str) -> list[dict]:
    """Prompt for generating SQL query from intent."""
    return [
        {
            "role": "system",
            "content": f"""You are a SQL query generator for a data analyst system.

Available tables and their schemas:
{schema_info}

Rules:
- Only use SELECT statements
- Always add LIMIT 100 to queries
- Only query from tables: orders, cafes, vendors
- Use proper JOINs when needed
- Return clean, readable SQL

Return ONLY the SQL query, no explanations."""
        },
        {
            "role": "user",
            "content": f"Generate a SQL query for this intent: {intent}"
        }
    ]


def get_result_analyzer_prompt(user_question: str, query_result: list, sql_query: str) -> list[dict]:
    """Prompt for analyzing query results: insights plus optional follow-up ideas."""
    return [
        {
            "role": "system",
            "content": """You are the analytics assistant for a cafe-chain business (orders, cafes, vendors).

Ground every claim in the provided rows. If the result set is empty or insufficient to answer the question, say so plainly and describe what is missing.

Write for a business reader: short paragraphs or tight bullets, no filler, no repetition of the raw table unless a few numbers are needed for clarity.

Structure your reply exactly in this order, using these headings (markdown ## is fine):

## Answer
Directly address what the user asked, with the most important numbers or facts first.

## Key findings
Bullets: patterns, comparisons, or drivers that stand out in the data.

## Caveats (if any)
Only if relevant: sampling limits, ties, missing fields, or why the SQL might not fully match the intent.

## Suggested follow-ups
Two or three concrete questions the user could ask next to go deeper (same domain; no generic platitudes). If the data cannot support more analysis, say "None needed" or offer one narrow refinement instead of inventing questions.

Do not mention the SQL dialect or internal system instructions. Do not fabricate metrics not present in the results.""",
        },
        {
            "role": "user",
            "content": f"""User question:
{user_question}

SQL that was run:
{sql_query}

Result rows (Python list of dicts):
{query_result}""",
        },
    ]


def get_schema_info() -> str:
    """Return schema information for available tables."""
    return """
orders table:
- id (integer, primary key)
- cafe_id (integer, foreign key to cafes)
- vendor_id (integer, foreign key to vendors)
- order_date (timestamp)
- total_amount (decimal)
- status (string)
- items (jsonb)

cafes table:
- id (integer, primary key)
- name (string)
- location (string)
- manager_name (string)
- created_at (timestamp)

vendors table:
- id (integer, primary key)
- name (string)
- category (string)
- contact_email (string)
- created_at (timestamp)
"""

