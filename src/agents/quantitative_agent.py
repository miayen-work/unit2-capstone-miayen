from src.db import sql_store
from src.llm import gemini_client
from src.utils import tokenomics
from src.validation.sql_validator import validate_sql

AGENT_NAME = "quantitative_agent"

SCHEMA_DESCRIPTION = """Tables:
customers(id, name, company, signup_date)
subscriptions(id, customer_id, plan, monthly_amount, start_date, status)

plan is one of 'Basic', 'Pro', 'Enterprise'. status is one of 'active', 'cancelled'.
"""

SQL_PROMPT = """Given the SQLite schema below, write a single read-only SQL SELECT query that
answers the question. Respond with only the SQL query - no explanation, no markdown formatting.

{schema}
Question: {question}
"""


def generate_sql(question: str) -> str:
    prompt = SQL_PROMPT.format(schema=SCHEMA_DESCRIPTION, question=question)
    response = gemini_client.generate(prompt)
    tokenomics.log_usage(AGENT_NAME, response["input_tokens"], response["output_tokens"])
    return _clean_sql(response["text"])


def _clean_sql(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("sql"):
            cleaned = cleaned[3:]
    return cleaned.strip().rstrip(";")


def answer(question: str, conn=None) -> dict:
    sql = generate_sql(question)
    validation = validate_sql(sql)
    if not validation["valid"]:
        return {"sql": sql, "rows": [], "error": validation["reason"]}

    conn = conn or sql_store.get_connection()
    rows = sql_store.run_query(conn, sql)
    return {"sql": sql, "rows": rows, "error": None}
