from pathlib import Path

DEFAULT_DOCUMENTS_DIR = "data/documents"


def read_documents(directory: str = DEFAULT_DOCUMENTS_DIR) -> list[dict]:
    docs = []
    for path in sorted(Path(directory).glob("*.md")):
        docs.append(
            {
                "id": path.stem,
                "text": path.read_text(encoding="utf-8"),
                "metadata": {"source": path.name},
            }
        )
    return docs
