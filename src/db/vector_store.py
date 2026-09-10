import chromadb
from chromadb.utils import embedding_functions

DEFAULT_COLLECTION_NAME = "enterprise_docs"
DEFAULT_PERSIST_DIR = "data/database/chroma"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_client(persist_dir: str = DEFAULT_PERSIST_DIR):
    return chromadb.PersistentClient(path=persist_dir)


def get_collection(
    client=None,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
):
    client = client or get_client()
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
    return client.get_or_create_collection(name=collection_name, embedding_function=embedding_fn)


def add_documents(collection, documents: list[str], ids: list[str], metadatas: list[dict] | None = None) -> None:
    # upsert (not add) so re-ingesting the same doc ids - e.g. re-running setup after
    # editing a doc - overwrites instead of raising on duplicate ids
    collection.upsert(documents=documents, ids=ids, metadatas=metadatas)


def query_collection(collection, query: str, n_results: int = 5) -> list[dict]:
    results = collection.query(query_texts=[query], n_results=n_results)
    hits = []
    for doc_id, doc, meta, dist in zip(
        results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        hits.append({"id": doc_id, "text": doc, "metadata": meta, "distance": dist})
    return hits
