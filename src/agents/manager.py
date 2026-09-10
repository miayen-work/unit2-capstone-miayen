import json

from src.agents import qualitative_agent, quantitative_agent
from src.llm import gemini_client

VALID_QUERY_TYPES = {"qualitative", "quantitative", "complex"}

CLASSIFICATION_PROMPT = """Classify the following user question into exactly one category:
- "qualitative": asks about policies, documentation, processes, or explanations
- "quantitative": asks about numbers, counts, totals, aggregates, or data lookups
- "complex": asks about both qualitative and quantitative information, or has multiple distinct parts

Respond with only a JSON object of the form {{"type": "<category>"}}.

Question: {query}
"""


def classify_query(query: str) -> str:
    prompt = CLASSIFICATION_PROMPT.format(query=query)
    response = gemini_client.generate(prompt)
    query_type = _parse_type(response["text"])
    if query_type not in VALID_QUERY_TYPES:
        raise ValueError(f"Unrecognized query type returned by classifier: {query_type!r}")
    return query_type


def _parse_type(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned.strip())["type"]


def handle_query(query: str) -> dict:
    query_type = classify_query(query)

    if query_type == "qualitative":
        return {"type": query_type, **qualitative_agent.answer(query)}

    if query_type == "quantitative":
        return {"type": query_type, **quantitative_agent.answer(query)}

    return {
        "type": query_type,
        "qualitative": qualitative_agent.answer(query),
        "quantitative": quantitative_agent.answer(query),
    }
