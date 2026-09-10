from unittest.mock import MagicMock, patch

import pytest

from src.llm import gemini_client


@pytest.fixture(autouse=True)
def reset_client():
    gemini_client._client = None
    yield
    gemini_client._client = None


def test_configure_uses_explicit_api_key():
    with patch("src.llm.gemini_client.genai") as mock_genai:
        gemini_client.configure(api_key="explicit-key")
        mock_genai.Client.assert_called_once_with(api_key="explicit-key")


def test_configure_falls_back_to_env_var(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    with patch("src.llm.gemini_client.genai") as mock_genai:
        gemini_client.configure()
        mock_genai.Client.assert_called_once_with(api_key="env-key")


def test_configure_raises_without_any_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        gemini_client.configure()


def test_generate_auto_configures_when_not_yet_configured(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    fake_response = MagicMock()
    fake_response.text = "hello from gemini"
    fake_response.usage_metadata.prompt_token_count = 10
    fake_response.usage_metadata.candidates_token_count = 20

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("src.llm.gemini_client.genai") as mock_genai:
        mock_genai.Client.return_value = fake_client
        result = gemini_client.generate("what is our refund policy?")

    mock_genai.Client.assert_called_once_with(api_key="env-key")
    fake_client.models.generate_content.assert_called_once_with(
        model=gemini_client.DEFAULT_MODEL, contents="what is our refund policy?"
    )
    assert result == {"text": "hello from gemini", "input_tokens": 10, "output_tokens": 20}


def test_generate_reuses_existing_client():
    fake_response = MagicMock()
    fake_response.text = "ok"
    fake_response.usage_metadata.prompt_token_count = 1
    fake_response.usage_metadata.candidates_token_count = 1

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response
    gemini_client._client = fake_client

    with patch("src.llm.gemini_client.genai") as mock_genai:
        gemini_client.generate("hi", model_name="gemini-1.5-pro")

    mock_genai.Client.assert_not_called()
    fake_client.models.generate_content.assert_called_once_with(
        model="gemini-1.5-pro", contents="hi"
    )
