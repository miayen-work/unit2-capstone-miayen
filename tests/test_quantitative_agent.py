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


def test_answer_executes_valid_generated_sql_and_summarizes_in_plain_language(conn):
    with patch(
        "src.agents.quantitative_agent.generate_sql", return_value="SELECT COUNT(*) AS count FROM customers"
    ), patch("src.agents.quantitative_agent.summarize_results", return_value="We have 10 customers.") as mock_summarize:
        result = quantitative_agent.answer("how many customers do we have?", conn=conn)

    assert result["error"] is None
    assert result["rows"] == [{"count": 10}]
    assert result["answer"] == "We have 10 customers."
    mock_summarize.assert_called_once_with(
        "how many customers do we have?", "SELECT COUNT(*) AS count FROM customers", [{"count": 10}]
    )


def test_summarize_results_logs_tokenomics_and_returns_model_text():
    with patch("src.agents.quantitative_agent.gemini_client") as mock_client, patch(
        "src.agents.quantitative_agent.tokenomics"
    ) as mock_tokenomics:
        mock_client.generate.return_value = _mock_llm_response("We have 10 customers.")
        text = quantitative_agent.summarize_results(
            "how many customers do we have?", "SELECT COUNT(*) FROM customers", [{"count": 10}]
        )

    assert text == "We have 10 customers."
    mock_tokenomics.log_usage.assert_called_once_with(quantitative_agent.AGENT_NAME, 30, 10)


def test_answer_blocks_disallowed_sql_without_executing_it(conn):
    with patch("src.agents.quantitative_agent.generate_sql", return_value="DROP TABLE customers"), patch(
        "src.agents.quantitative_agent.sql_store"
    ) as mock_sql_store:
        result = quantitative_agent.answer("delete all customers", conn=conn)

    assert result["rows"] == []
    assert "DROP" in result["error"]
    mock_sql_store.run_query.assert_not_called()


def test_answer_returns_error_for_sql_against_a_nonexistent_table(conn):
    with patch(
        "src.agents.quantitative_agent.generate_sql", return_value="SELECT COUNT(*) FROM employees"
    ):
        result = quantitative_agent.answer("how many employees do we have?", conn=conn)

    assert result["rows"] == []
    assert result["error"] is not None
    assert "employees" in result["error"]


def test_generate_sql_returns_no_data_sentinel_when_model_says_so():
    with patch("src.agents.quantitative_agent.gemini_client") as mock_client, patch(
        "src.agents.quantitative_agent.tokenomics"
    ):
        mock_client.generate.return_value = _mock_llm_response("NO_DATA")
        sql = quantitative_agent.generate_sql("how many employees do we have?")

    assert sql == quantitative_agent.NO_DATA_RESPONSE


def test_answer_returns_graceful_message_without_running_a_query_when_no_data(conn):
    with patch(
        "src.agents.quantitative_agent.generate_sql", return_value=quantitative_agent.NO_DATA_RESPONSE
    ), patch("src.agents.quantitative_agent.sql_store") as mock_sql_store:
        result = quantitative_agent.answer("how many employees do we have?", conn=conn)

    assert result["sql"] is None
    assert result["rows"] == []
    assert result["answer"] == quantitative_agent.NO_DATA_MESSAGE
    assert result["error"] == quantitative_agent.NO_DATA_MESSAGE
    mock_sql_store.run_query.assert_not_called()
