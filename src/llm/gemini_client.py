import os

from google import genai

DEFAULT_MODEL = "gemini-flash-lite-latest"

_client: genai.Client | None = None


def configure(api_key: str | None = None) -> None:
    global _client
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    _client = genai.Client(api_key=api_key)


def generate(prompt: str, model_name: str = DEFAULT_MODEL) -> dict:
    if _client is None:
        configure()
    response = _client.models.generate_content(model=model_name, contents=prompt)
    usage = response.usage_metadata
    return {
        "text": response.text,
        "input_tokens": usage.prompt_token_count,
        "output_tokens": usage.candidates_token_count,
    }
