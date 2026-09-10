import json

from src.db import vector_store
from src.llm import gemini_client
from src.utils import tokenomics

AGENT_NAME = "qualitative_agent"

ANSWER_PROMPT = """Answer the question using only the context below. Each excerpt is labeled with
its source file. If the context does not contain the answer, say you don't know.

Respond with only a JSON object of the form:
{{"answer": "<your answer>", "sources": ["<source file>", ...]}}

Only list a source if its content was actually used to answer the question.

Context:
{context}

Question: {question}
"""


def search(query: str, n_results: int = 3, collection=None) -> list[dict]:
    collection = collection or vector_store.get_collection()
    return vector_store.query_collection(collection, query, n_results=n_results)


def answer(query: str, n_results: int = 3, collection=None) -> dict:
    hits = search(query, n_results=n_results, collection=collection)
    context = "\n\n".join(
        f"[Source: {(hit.get('metadata') or {}).get('source', hit['id'])}]\n{hit['text']}" for hit in hits
    )
    prompt = ANSWER_PROMPT.format(context=context, question=query)

    response = gemini_client.generate(prompt)
    tokenomics.log_usage(AGENT_NAME, response["input_tokens"], response["output_tokens"])

    retrieved_sources = {hit["metadata"]["source"] for hit in hits if hit.get("metadata")}
    answer_text, sources = _parse_response(response["text"], retrieved_sources)
    return {"answer": answer_text, "sources": sources}


def _parse_response(text: str, retrieved_sources: set) -> tuple[str, list[str]]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        cited_sources = sorted(source for source in data["sources"] if source in retrieved_sources)
        return data["answer"], cited_sources
    except (json.JSONDecodeError, KeyError, TypeError):
        return text.strip(), sorted(retrieved_sources)
