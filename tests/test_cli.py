from unittest.mock import patch

from src import cli


def test_format_result_qualitative_includes_sources():
    result = {"type": "qualitative", "answer": "Refunds within 30 days.", "sources": ["refund_policy.md"]}
    text = cli.format_result(result)
    assert "Refunds within 30 days." in text
    assert "refund_policy.md" in text


def test_format_result_qualitative_with_no_sources():
    result = {"type": "qualitative", "answer": "I don't know.", "sources": []}
    text = cli.format_result(result)
    assert "no sources found" in text


def test_format_result_quantitative_success():
    result = {
        "type": "quantitative",
        "sql": "SELECT COUNT(*) FROM customers",
        "rows": [{"count": 10}],
        "answer": "We have 10 customers.",
        "error": None,
    }
    text = cli.format_result(result)
    assert "We have 10 customers." in text
    assert "SELECT COUNT(*) FROM customers" in text


def test_format_result_quantitative_error():
    result = {"type": "quantitative", "sql": "DROP TABLE customers", "rows": [], "error": "Blocked: DROP not permitted"}
    text = cli.format_result(result)
    assert "Could not run that query" in text
    assert "Blocked: DROP not permitted" in text


def test_format_result_quantitative_no_data_available():
    result = {
        "type": "quantitative",
        "sql": None,
        "rows": [],
        "error": "The available data does not include information needed to answer this question.",
    }
    text = cli.format_result(result)
    assert text == "The available data does not include information needed to answer this question."
    assert "Could not run that query" not in text


def test_format_result_complex_combines_both_sections():
    result = {
        "type": "complex",
        "qualitative": {"answer": "Refunds within 30 days.", "sources": ["refund_policy.md"]},
        "quantitative": {
            "sql": "SELECT COUNT(*) FROM subscriptions",
            "rows": [{"count": 12}],
            "answer": "We have 12 subscriptions.",
            "error": None,
        },
    }
    text = cli.format_result(result)
    assert "Refunds within 30 days." in text
    assert "We have 12 subscriptions." in text


def test_run_processes_queries_until_exit():
    inputs = iter(["What is our refund policy?", "exit"])
    outputs = []

    with patch("src.cli.manager") as mock_manager:
        mock_manager.handle_query.return_value = {
            "type": "qualitative",
            "answer": "Refunds within 30 days.",
            "sources": ["refund_policy.md"],
        }
        cli.run(input_fn=lambda _: next(inputs), print_fn=outputs.append)

    mock_manager.handle_query.assert_called_once_with("What is our refund policy?")
    assert any("Refunds within 30 days." in line for line in outputs)


def test_run_skips_blank_input_without_calling_handle_query():
    inputs = iter(["", "  ", "exit"])

    with patch("src.cli.manager") as mock_manager:
        cli.run(input_fn=lambda _: next(inputs), print_fn=lambda _: None)

    mock_manager.handle_query.assert_not_called()


def test_run_accepts_quit_as_well_as_exit():
    inputs = iter(["quit"])

    with patch("src.cli.manager") as mock_manager:
        cli.run(input_fn=lambda _: next(inputs), print_fn=lambda _: None)

    mock_manager.handle_query.assert_not_called()


def test_run_recovers_after_handle_query_raises_and_keeps_going():
    inputs = iter(["first query", "second query", "exit"])
    outputs = []

    with patch("src.cli.manager") as mock_manager:
        mock_manager.handle_query.side_effect = [
            RuntimeError("429 RESOURCE_EXHAUSTED"),
            {"type": "qualitative", "answer": "ok", "sources": []},
        ]
        cli.run(input_fn=lambda _: next(inputs), print_fn=outputs.append)

    assert mock_manager.handle_query.call_count == 2
    assert any("429 RESOURCE_EXHAUSTED" in line for line in outputs)
    assert any("ok" in line for line in outputs)


def test_run_prints_cost_summary_after_every_ten_queries():
    inputs = iter([f"query {i}" for i in range(10)] + ["exit"])
    outputs = []

    with patch("src.cli.manager") as mock_manager, patch("src.cli.tokenomics") as mock_tokenomics:
        mock_manager.handle_query.return_value = {"type": "qualitative", "answer": "ok", "sources": []}
        mock_tokenomics.format_summary.return_value = "SUMMARY"
        cli.run(input_fn=lambda _: next(inputs), print_fn=outputs.append)

    assert mock_tokenomics.format_summary.call_count == 1
    assert "SUMMARY" in outputs


def test_run_prints_final_summary_on_exit_with_leftover_queries():
    inputs = iter(["only one query", "exit"])
    outputs = []

    with patch("src.cli.manager") as mock_manager, patch("src.cli.tokenomics") as mock_tokenomics:
        mock_manager.handle_query.return_value = {"type": "qualitative", "answer": "ok", "sources": []}
        mock_tokenomics.format_summary.return_value = "SUMMARY"
        cli.run(input_fn=lambda _: next(inputs), print_fn=outputs.append)

    assert mock_tokenomics.format_summary.call_count == 1
    assert "SUMMARY" in outputs


def test_run_does_not_print_summary_when_no_queries_were_processed():
    inputs = iter(["exit"])

    with patch("src.cli.manager"), patch("src.cli.tokenomics") as mock_tokenomics:
        cli.run(input_fn=lambda _: next(inputs), print_fn=lambda _: None)

    mock_tokenomics.format_summary.assert_not_called()
