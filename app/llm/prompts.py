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
    """Prompt for analyzing query results and generating insights."""
    return [
        {
            "role": "system",
            "content": """You are a data analyst. Analyze the query results and provide 
insights in natural language. Be concise, accurate, and actionable.

Format your response as:
1. Summary of findings
2. Key insights
3. Any notable patterns or anomalies"""
        },
        {
            "role": "user",
            "content": f"""Original question: {user_question}

SQL Query executed:
{sql_query}

Query Results:
{query_result}

Provide insights based on these results."""
        }
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

