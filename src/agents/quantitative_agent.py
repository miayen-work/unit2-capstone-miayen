import sqlite3
from datetime import date

from src.db import sql_store
from src.llm import gemini_client
from src.utils import tokenomics
from src.validation.sql_validator import validate_sql

AGENT_NAME = "quantitative_agent"

NO_DATA_RESPONSE = "NO_DATA"
NO_DATA_MESSAGE = "The available data does not include information needed to answer this question."

SCHEMA_DESCRIPTION = """Tables:
customers(id, name, company, region, signup_date)
subscriptions(id, customer_id, plan, monthly_amount, start_date, status)
revenue_by_month(id, month, region, revenue)
employees(id, name, department, satisfaction_score, survey_date)
code_review_tickets(id, opened_at, reviewed_at, turnaround_hours)
expense_requests(id, employee_name, amount, request_date)

plan is one of 'Basic', 'Pro', 'Enterprise'. status is one of 'active', 'cancelled'.
region is one of 'NA', 'EMEA', 'APAC'. month is formatted 'YYYY-MM'.
satisfaction_score is on a 0-10 scale. turnaround_hours is the time from a code review
ticket being opened to its first review. dates are formatted 'YYYY-MM-DD' (or with a time
of day for code_review_tickets).

Business term mappings (the schema has no column with these exact names - compute them):
- "churn" / "churn rate" = count of subscriptions with status = 'cancelled' divided by the
  total count of subscriptions (optionally scoped to a plan or time period if asked).
- "manager sign-off" / "requires approval" for expense_requests = amount >= 500.
- "meeting the SLA" / "on time" for code_review_tickets = turnaround_hours <= 48.
Only respond with the NO_DATA sentinel below when the underlying facts truly are not present
in any table above - not merely because the question uses different wording than a column
name.
"""

SQL_PROMPT = """Today's date is {today}.

Given the SQLite schema below, write a single read-only SQL SELECT query that answers the
question. Respond with only the SQL query - no explanation, no markdown formatting.

The question may be a compound question that also asks about things outside this database
(industry benchmarks, policy explanations, recommendations, opinions). Ignore those parts and
write a query for whatever data-driven portion of the question these tables CAN answer. For
example, "how does our score compare to industry averages" - just query our own score; do not
try to represent the industry average or the comparison itself in SQL.

Only respond with the single word """ + NO_DATA_RESPONSE + """ if none of the tables below
contain any data relevant to any part of the question.

{schema}
Question: {question}
"""

SUMMARY_PROMPT = """Question: {question}

SQL query used: {sql}

Query result rows (as JSON): {rows}

Write a short, direct, plain-language answer to the question using only this data. Do not
mention SQL, queries, or column names - just answer naturally, the way a person would.
"""


def generate_sql(question: str) -> str:
    prompt = SQL_PROMPT.format(schema=SCHEMA_DESCRIPTION, question=question, today=date.today().isoformat())
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
