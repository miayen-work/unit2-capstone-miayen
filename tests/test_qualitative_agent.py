from unittest.mock import MagicMock, patch

from src.agents import qualitative_agent


def _mock_llm_response(text: str) -> dict:
    return {"text": text, "input_tokens": 15, "output_tokens": 25}


def test_search_queries_the_provided_collection():
    fake_collection = MagicMock()
    with patch("src.agents.qualitative_agent.vector_store") as mock_store:
        mock_store.query_collection.return_value = [{"id": "refund_policy", "text": "...", "metadata": {}}]
        results = qualitative_agent.search("refund question", n_results=2, collection=fake_collection)

    mock_store.query_collection.assert_called_once_with(fake_collection, "refund question", n_results=2)
    mock_store.get_collection.assert_not_called()
    assert results == [{"id": "refund_policy", "text": "...", "metadata": {}}]


def test_search_creates_default_collection_when_none_given():
    with patch("src.agents.qualitative_agent.vector_store") as mock_store:
        default_collection = MagicMock()
        mock_store.get_collection.return_value = default_collection
        mock_store.query_collection.return_value = []
        qualitative_agent.search("refund question")

    mock_store.get_collection.assert_called_once()
    mock_store.query_collection.assert_called_once_with(default_collection, "refund question", n_results=3)


def test_answer_returns_llm_text_and_sorted_unique_sources():
    hits = [
        {"id": "refund_policy", "text": "Refunds within 30 days.", "metadata": {"source": "refund_policy.md"}},
        {"id": "refund_policy_2", "text": "Prorated for annual plans.", "metadata": {"source": "refund_policy.md"}},
        {"id": "support_sla", "text": "Support SLAs by plan.", "metadata": {"source": "support_sla.md"}},
    ]
    with patch("src.agents.qualitative_agent.search", return_value=hits), patch(
        "src.agents.qualitative_agent.gemini_client"
    ) as mock_client, patch("src.agents.qualitative_agent.tokenomics") as mock_tokenomics:
        mock_client.generate.return_value = _mock_llm_response("You can get a refund within 30 days.")

        result = qualitative_agent.answer("What is the refund policy?")

    assert result == {
        "answer": "You can get a refund within 30 days.",
        "sources": ["refund_policy.md", "support_sla.md"],
    }
    mock_tokenomics.log_usage.assert_called_once_with(qualitative_agent.AGENT_NAME, 15, 25)


def test_answer_includes_hit_text_in_prompt_context():
    hits = [{"id": "refund_policy", "text": "Refunds within 30 days.", "metadata": {"source": "refund_policy.md"}}]
    with patch("src.agents.qualitative_agent.search", return_value=hits), patch(
        "src.agents.qualitative_agent.gemini_client"
    ) as mock_client, patch("src.agents.qualitative_agent.tokenomics"):
        mock_client.generate.return_value = _mock_llm_response("Answer text")

        qualitative_agent.answer("What is the refund policy?")

    sent_prompt = mock_client.generate.call_args[0][0]
    assert "Refunds within 30 days." in sent_prompt
    assert "What is the refund policy?" in sent_prompt
