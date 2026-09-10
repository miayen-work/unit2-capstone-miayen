import sqlite3

from src.db import sql_store
from src.llm import gemini_client
from src.utils import tokenomics
from src.validation.sql_validator import validate_sql

AGENT_NAME = "quantitative_agent"

NO_DATA_RESPONSE = "NO_DATA"
NO_DATA_MESSAGE = "The available data does not include information needed to answer this question."

SCHEMA_DESCRIPTION = """Tables:
customers(id, name, company, signup_date)
subscriptions(id, customer_id, plan, monthly_amount, start_date, status)

plan is one of 'Basic', 'Pro', 'Enterprise'. status is one of 'active', 'cancelled'.
"""

SQL_PROMPT = f"""Given the SQLite schema below, write a single read-only SQL SELECT query that
answers the question. Respond with only the SQL query - no explanation, no markdown formatting.

If the schema does not contain the data needed to answer the question, do not guess or invent a
query - respond with exactly the single word: {NO_DATA_RESPONSE}

{{schema}}
Question: {{question}}
"""

SUMMARY_PROMPT = """Question: {question}

SQL query used: {sql}

Query result rows (as JSON): {rows}

Write a short, direct, plain-language answer to the question using only this data. Do not
mention SQL, queries, or column names - just answer naturally, the way a person would.
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
    cleaned = cleaned.strip().rstrip(";")
    if cleaned.upper() == NO_DATA_RESPONSE:
        return NO_DATA_RESPONSE
    return cleaned


def summarize_results(question: str, sql: str, rows: list[dict]) -> str:
    prompt = SUMMARY_PROMPT.format(question=question, sql=sql, rows=rows)
    response = gemini_client.generate(prompt)
    tokenomics.log_usage(AGENT_NAME, response["input_tokens"], response["output_tokens"])
    return response["text"].strip()


def answer(question: str, conn=None) -> dict:
    sql = generate_sql(question)

    if sql == NO_DATA_RESPONSE:
        return {"sql": None, "rows": [], "answer": NO_DATA_MESSAGE, "error": NO_DATA_MESSAGE}

    validation = validate_sql(sql)
    if not validation["valid"]:
        return {"sql": sql, "rows": [], "answer": None, "error": validation["reason"]}

    conn = conn or sql_store.get_connection()
    try:
        rows = sql_store.run_query(conn, sql)
    except sqlite3.OperationalError as exc:
        return {"sql": sql, "rows": [], "answer": None, "error": f"Query failed: {exc}"}

    answer_text = summarize_results(question, sql, rows)
    return {"sql": sql, "rows": rows, "answer": answer_text, "error": None}
