from unittest.mock import patch

import pytest

from src.agents import quantitative_agent
from src.db import sql_store


def _mock_llm_response(text: str) -> dict:
    return {"text": text, "input_tokens": 30, "output_tokens": 10}


@pytest.fixture
def conn():
    connection = sql_store.get_connection(db_path=":memory:")
    sql_store.initialize_database(connection)
    yield connection
    connection.close()


def test_generate_sql_strips_markdown_fences_and_semicolon():
    with patch("src.agents.quantitative_agent.gemini_client") as mock_client, patch(
        "src.agents.quantitative_agent.tokenomics"
    ):
        mock_client.generate.return_value = _mock_llm_response(
            "```sql\nSELECT COUNT(*) FROM customers;\n```"
        )
        sql = quantitative_agent.generate_sql("how many customers do we have?")

    assert sql == "SELECT COUNT(*) FROM customers"


def test_generate_sql_logs_tokenomics():
    with patch("src.agents.quantitative_agent.gemini_client") as mock_client, patch(
        "src.agents.quantitative_agent.tokenomics"
    ) as mock_tokenomics:
        mock_client.generate.return_value = _mock_llm_response("SELECT COUNT(*) FROM customers")
        quantitative_agent.generate_sql("how many customers do we have?")

    mock_tokenomics.log_usage.assert_called_once_with(quantitative_agent.AGENT_NAME, 30, 10)


def test_answer_executes_valid_generated_sql(conn):
    with patch("src.agents.quantitative_agent.generate_sql", return_value="SELECT COUNT(*) AS count FROM customers"):
        result = quantitative_agent.answer("how many customers do we have?", conn=conn)

    assert result["error"] is None
    assert result["rows"] == [{"count": 10}]


def test_answer_blocks_disallowed_sql_without_executing_it(conn):
    with patch("src.agents.quantitative_agent.generate_sql", return_value="DROP TABLE customers"), patch(
        "src.agents.quantitative_agent.sql_store"
    ) as mock_sql_store:
        result = quantitative_agent.answer("delete all customers", conn=conn)

    assert result["rows"] == []
    assert "DROP" in result["error"]
    mock_sql_store.run_query.assert_not_called()
