from src.db import vector_store
from src.llm import gemini_client
from src.utils import tokenomics

AGENT_NAME = "qualitative_agent"

ANSWER_PROMPT = """Answer the question using only the context below. If the context does not
contain the answer, say you don't know.

Context:
{context}

Question: {question}
"""


def search(query: str, n_results: int = 3, collection=None) -> list[dict]:
    collection = collection or vector_store.get_collection()
    return vector_store.query_collection(collection, query, n_results=n_results)


def answer(query: str, n_results: int = 3, collection=None) -> dict:
    hits = search(query, n_results=n_results, collection=collection)
    context = "\n\n".join(hit["text"] for hit in hits)
    prompt = ANSWER_PROMPT.format(context=context, question=query)

    response = gemini_client.generate(prompt)
    tokenomics.log_usage(AGENT_NAME, response["input_tokens"], response["output_tokens"])

    sources = sorted({hit["metadata"]["source"] for hit in hits if hit.get("metadata")})
    return {"answer": response["text"], "sources": sources}
