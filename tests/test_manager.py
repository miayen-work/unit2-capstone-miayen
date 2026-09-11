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


def test_handle_query_follows_up_quantitative_when_it_was_incomplete():
    with patch("src.agents.manager.classify_query", return_value="complex"), patch(
        "src.agents.manager.qualitative_agent"
    ) as mock_qual, patch("src.agents.manager.quantitative_agent") as mock_quant:
        mock_qual.answer.return_value = {"answer": "Reviews must happen within 48 hours.", "sources": ["code_review_policy.md"]}
        mock_quant.answer.side_effect = [
            {"sql": None, "rows": [], "answer": None, "error": "The available data does not include information needed to answer this question."},
            {"sql": "SELECT COUNT(*) FROM code_review_tickets WHERE turnaround_hours <= 48", "rows": [{"count": 10}], "error": None},
        ]

        result = manager.handle_query("Are our code review turnaround times meeting our documented standard?")

    assert mock_quant.answer.call_count == 2
    follow_up_prompt = mock_quant.answer.call_args_list[1][0][0]
    assert "Reviews must happen within 48 hours." in follow_up_prompt
    assert result["quantitative"]["rows"] == [{"count": 10}]


def test_handle_query_follows_up_qualitative_when_it_was_incomplete():
    with patch("src.agents.manager.classify_query", return_value="complex"), patch(
        "src.agents.manager.qualitative_agent"
    ) as mock_qual, patch("src.agents.manager.quantitative_agent") as mock_quant:
        mock_qual.answer.side_effect = [
            {"answer": "I don't know.", "sources": []},
            {"answer": "Given our score of 7.16, we are slightly below the 7.4 industry benchmark.", "sources": ["employee_satisfaction_benchmark.md"]},
        ]
        mock_quant.answer.return_value = {
            "sql": "SELECT AVG(satisfaction_score) FROM employees",
            "rows": [{"avg": 7.16}],
            "answer": "Our average employee satisfaction score is 7.16.",
            "error": None,
        }

        result = manager.handle_query("How does our employee satisfaction compare to industry standards?")

    assert mock_qual.answer.call_count == 2
    follow_up_prompt = mock_qual.answer.call_args_list[1][0][0]
    assert "7.16" in follow_up_prompt
    assert "industry benchmark" in result["qualitative"]["answer"]


def test_handle_query_does_not_follow_up_when_both_sides_are_incomplete():
    with patch("src.agents.manager.classify_query", return_value="complex"), patch(
        "src.agents.manager.qualitative_agent"
    ) as mock_qual, patch("src.agents.manager.quantitative_agent") as mock_quant:
        mock_qual.answer.return_value = {"answer": "I don't know.", "sources": []}
        mock_quant.answer.return_value = {"sql": None, "rows": [], "answer": None, "error": "NO_DATA"}

        manager.handle_query("some unanswerable compound question")

    mock_qual.answer.assert_called_once()
    mock_quant.answer.assert_called_once()
