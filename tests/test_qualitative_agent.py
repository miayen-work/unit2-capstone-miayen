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


def test_answer_only_cites_sources_the_model_says_it_used():
    hits = [
        {"id": "refund_policy", "text": "Refunds within 30 days.", "metadata": {"source": "refund_policy.md"}},
        {"id": "vacation_policy", "text": "15 paid vacation days.", "metadata": {"source": "vacation_policy.md"}},
    ]
    with patch("src.agents.qualitative_agent.search", return_value=hits), patch(
        "src.agents.qualitative_agent.gemini_client"
    ) as mock_client, patch("src.agents.qualitative_agent.tokenomics") as mock_tokenomics:
        mock_client.generate.return_value = _mock_llm_response(
            '{"answer": "You can get a refund within 30 days.", "sources": ["refund_policy.md"]}'
        )

        result = qualitative_agent.answer("What is the refund policy?")

    assert result == {
        "answer": "You can get a refund within 30 days.",
        "sources": ["refund_policy.md"],
    }
    mock_tokenomics.log_usage.assert_called_once_with(qualitative_agent.AGENT_NAME, 15, 25)


def test_answer_ignores_hallucinated_source_names_not_actually_retrieved():
    hits = [{"id": "refund_policy", "text": "Refunds within 30 days.", "metadata": {"source": "refund_policy.md"}}]
    with patch("src.agents.qualitative_agent.search", return_value=hits), patch(
        "src.agents.qualitative_agent.gemini_client"
    ) as mock_client, patch("src.agents.qualitative_agent.tokenomics"):
        mock_client.generate.return_value = _mock_llm_response(
            '{"answer": "Refunds within 30 days.", "sources": ["refund_policy.md", "made_up_file.md"]}'
        )

        result = qualitative_agent.answer("What is the refund policy?")

    assert result["sources"] == ["refund_policy.md"]


def test_answer_handles_markdown_fenced_json_response():
    hits = [{"id": "refund_policy", "text": "Refunds within 30 days.", "metadata": {"source": "refund_policy.md"}}]
    with patch("src.agents.qualitative_agent.search", return_value=hits), patch(
        "src.agents.qualitative_agent.gemini_client"
    ) as mock_client, patch("src.agents.qualitative_agent.tokenomics"):
        mock_client.generate.return_value = _mock_llm_response(
            '```json\n{"answer": "Refunds within 30 days.", "sources": ["refund_policy.md"]}\n```'
        )

        result = qualitative_agent.answer("What is the refund policy?")

    assert result == {"answer": "Refunds within 30 days.", "sources": ["refund_policy.md"]}


def test_answer_falls_back_to_all_retrieved_sources_when_response_is_not_json():
    hits = [
        {"id": "refund_policy", "text": "Refunds within 30 days.", "metadata": {"source": "refund_policy.md"}},
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
