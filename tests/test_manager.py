from unittest.mock import patch

import pytest

from src.agents import manager


def _mock_response(text: str) -> dict:
    return {"text": text, "input_tokens": 5, "output_tokens": 5}


def test_classifies_qualitative_query():
    with patch("src.agents.manager.gemini_client") as mock_client:
        mock_client.generate.return_value = _mock_response('{"type": "qualitative"}')
        result = manager.classify_query("What is our refund policy?")
    assert result == "qualitative"


def test_classifies_quantitative_query():
    with patch("src.agents.manager.gemini_client") as mock_client:
        mock_client.generate.return_value = _mock_response('{"type": "quantitative"}')
        result = manager.classify_query("How many units did we sell last quarter?")
    assert result == "quantitative"


def test_classifies_complex_query():
    with patch("src.agents.manager.gemini_client") as mock_client:
        mock_client.generate.return_value = _mock_response('{"type": "complex"}')
        result = manager.classify_query("What is our refund policy and how many refunds were issued last month?")
    assert result == "complex"


def test_handles_markdown_fenced_json_response():
    with patch("src.agents.manager.gemini_client") as mock_client:
        mock_client.generate.return_value = _mock_response('```json\n{"type": "qualitative"}\n```')
        result = manager.classify_query("What is our onboarding process?")
    assert result == "qualitative"


def test_raises_on_unrecognized_query_type():
    with patch("src.agents.manager.gemini_client") as mock_client:
        mock_client.generate.return_value = _mock_response('{"type": "unknown"}')
        with pytest.raises(ValueError):
            manager.classify_query("some ambiguous question")


def test_prompt_includes_the_question():
    with patch("src.agents.manager.gemini_client") as mock_client:
        mock_client.generate.return_value = _mock_response('{"type": "qualitative"}')
        manager.classify_query("What is our refund policy?")
    sent_prompt = mock_client.generate.call_args[0][0]
    assert "What is our refund policy?" in sent_prompt


def test_handle_query_routes_qualitative_to_qualitative_agent():
    with patch("src.agents.manager.classify_query", return_value="qualitative"), patch(
        "src.agents.manager.qualitative_agent"
    ) as mock_qual, patch("src.agents.manager.quantitative_agent") as mock_quant:
        mock_qual.answer.return_value = {"answer": "30 days", "sources": ["refund_policy.md"]}

        result = manager.handle_query("What is our refund policy?")

    mock_qual.answer.assert_called_once_with("What is our refund policy?")
    mock_quant.answer.assert_not_called()
    assert result == {"type": "qualitative", "answer": "30 days", "sources": ["refund_policy.md"]}


def test_handle_query_routes_quantitative_to_quantitative_agent():
    with patch("src.agents.manager.classify_query", return_value="quantitative"), patch(
        "src.agents.manager.qualitative_agent"
    ) as mock_qual, patch("src.agents.manager.quantitative_agent") as mock_quant:
        mock_quant.answer.return_value = {"sql": "SELECT COUNT(*) FROM customers", "rows": [{"count": 10}], "error": None}

        result = manager.handle_query("How many customers do we have?")

    mock_quant.answer.assert_called_once_with("How many customers do we have?")
    mock_qual.answer.assert_not_called()
    assert result == {
        "type": "quantitative",
        "sql": "SELECT COUNT(*) FROM customers",
        "rows": [{"count": 10}],
        "error": None,
    }


def test_handle_query_calls_both_agents_for_complex_query():
    with patch("src.agents.manager.classify_query", return_value="complex"), patch(
        "src.agents.manager.qualitative_agent"
    ) as mock_qual, patch("src.agents.manager.quantitative_agent") as mock_quant:
        mock_qual.answer.return_value = {"answer": "30 days", "sources": ["refund_policy.md"]}
        mock_quant.answer.return_value = {"sql": "SELECT 1", "rows": [{"1": 1}], "error": None}

        result = manager.handle_query("What is our refund policy and how many refunds happened?")

    mock_qual.answer.assert_called_once()
    mock_quant.answer.assert_called_once()
    assert result["type"] == "complex"
    assert result["qualitative"]["answer"] == "30 days"
    assert result["quantitative"]["rows"] == [{"1": 1}]
