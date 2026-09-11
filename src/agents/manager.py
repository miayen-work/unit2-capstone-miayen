import json

from src.agents import qualitative_agent, quantitative_agent
from src.llm import gemini_client
from src.utils import tokenomics

AGENT_NAME = "manager"

VALID_QUERY_TYPES = {"qualitative", "quantitative", "complex"}

CLASSIFICATION_PROMPT = """Classify the following user question into exactly one category:
- "qualitative": can be fully answered from written documentation (policies, processes,
  explanations) with no computation over records needed
- "quantitative": can be fully answered by computing something over structured records
  (counts, sums, rates, comparisons, lookups) with no policy/process explanation needed
- "complex": needs both - e.g. it asks to explain or reference a policy/process AND also
  asks for a computed number, count, or comparison over records

Classify based on what the question actually requires to answer it in full, not by
surface keywords. A question can mention the word "policy" while still needing a real
computed number (which makes it "complex", not just "qualitative") - and a question about
numbers can still need a documented policy to interpret them correctly. Read the whole
question and decide what it would actually take to answer it completely.

Respond with only a JSON object of the form {{"type": "<category>"}}.

Question: {query}
"""


def classify_query(query: str) -> str:
    prompt = CLASSIFICATION_PROMPT.format(query=query)
    response = gemini_client.generate(prompt)
    tokenomics.log_usage(AGENT_NAME, response["input_tokens"], response["output_tokens"])
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


def _qualitative_is_incomplete(result: dict) -> bool:
    answer = (result.get("answer") or "").lower()
    return not result.get("sources") or "don't know" in answer or "do not know" in answer


def _quantitative_is_incomplete(result: dict) -> bool:
    return result.get("error") is not None


def handle_query(query: str) -> dict:
    query_type = classify_query(query)

    if query_type == "qualitative":
        return {"type": query_type, **qualitative_agent.answer(query)}

    if query_type == "quantitative":
        return {"type": query_type, **quantitative_agent.answer(query)}

    qualitative_result = qualitative_agent.answer(query)
    quantitative_result = quantitative_agent.answer(query)

    # Complex queries need real coordination: if one side came back incomplete but the
    # other succeeded, follow up on the incomplete side using the other side's answer as
    # extra context, rather than just returning the partial result as-is.
    if _quantitative_is_incomplete(quantitative_result) and not _qualitative_is_incomplete(qualitative_result):
        follow_up = (
            f"{query}\n\nRelevant policy context already found: {qualitative_result['answer']}"
        )
        quantitative_result = quantitative_agent.answer(follow_up)

    if _qualitative_is_incomplete(qualitative_result) and not _quantitative_is_incomplete(quantitative_result):
        follow_up = f"{query}\n\nRelevant data already found: {quantitative_result['answer']}"
        qualitative_result = qualitative_agent.answer(follow_up)

    return {
        "type": query_type,
        "qualitative": qualitative_result,
        "quantitative": quantitative_result,
    }
