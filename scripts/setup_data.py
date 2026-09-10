"""One-time setup: initialize the SQLite database and ingest documents into Chroma."""

from src.db import sql_store, vector_store
from src.ingest import read_documents


def setup_sql() -> None:
    conn = sql_store.get_connection()
    sql_store.initialize_database(conn)
    conn.close()
    print("SQLite database initialized at", sql_store.DEFAULT_DB_PATH)


def setup_vector_store() -> None:
    collection = vector_store.get_collection()
    docs = read_documents()
    vector_store.add_documents(
        collection,
        documents=[doc["text"] for doc in docs],
        ids=[doc["id"] for doc in docs],
        metadatas=[doc["metadata"] for doc in docs],
    )
    print(f"Ingested {len(docs)} documents into Chroma collection '{collection.name}'")


if __name__ == "__main__":
    setup_sql()
    setup_vector_store()
