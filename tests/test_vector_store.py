import uuid

import chromadb
import pytest

from src.db import vector_store


@pytest.fixture
def collection():
    client = chromadb.EphemeralClient()
    unique_name = f"test_docs_{uuid.uuid4().hex}"
    return vector_store.get_collection(client=client, collection_name=unique_name)


def test_add_and_query_returns_most_relevant_document_first(collection):
    vector_store.add_documents(
        collection,
        documents=[
            "Our refund policy allows returns within 30 days of purchase.",
            "The onboarding process takes approximately two weeks for new hires.",
            "Vacation requests must be submitted at least two weeks in advance.",
        ],
        ids=["refund_policy", "onboarding", "vacation_policy"],
        metadatas=[
            {"source": "policies/refunds.md"},
            {"source": "hr/onboarding.md"},
            {"source": "hr/vacation.md"},
        ],
    )

    hits = vector_store.query_collection(collection, "how do I return a product I bought?", n_results=1)

    assert len(hits) == 1
    assert hits[0]["id"] == "refund_policy"


def test_query_includes_source_metadata_for_attribution(collection):
    vector_store.add_documents(
        collection,
        documents=["Employees receive 15 paid vacation days per year."],
        ids=["vacation_days"],
        metadatas=[{"source": "hr/vacation.md"}],
    )

    hits = vector_store.query_collection(collection, "how many vacation days do I get?", n_results=1)

    assert hits[0]["metadata"]["source"] == "hr/vacation.md"
    assert hits[0]["text"] == "Employees receive 15 paid vacation days per year."


def test_n_results_limits_number_of_hits(collection):
    vector_store.add_documents(
        collection,
        documents=["doc one", "doc two", "doc three"],
        ids=["one", "two", "three"],
    )

    hits = vector_store.query_collection(collection, "doc", n_results=2)

    assert len(hits) == 2


def test_query_on_empty_collection_returns_no_hits(collection):
    hits = vector_store.query_collection(collection, "anything", n_results=5)

    assert hits == []
