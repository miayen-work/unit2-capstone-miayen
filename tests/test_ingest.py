from src.ingest import read_documents


def test_reads_all_markdown_files_in_directory(tmp_path):
    (tmp_path / "refund_policy.md").write_text("Refunds within 30 days.", encoding="utf-8")
    (tmp_path / "vacation_policy.md").write_text("15 paid vacation days.", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("should be ignored", encoding="utf-8")

    docs = read_documents(str(tmp_path))

    assert len(docs) == 2
    ids = {doc["id"] for doc in docs}
    assert ids == {"refund_policy", "vacation_policy"}


def test_document_includes_text_and_source_metadata(tmp_path):
    (tmp_path / "refund_policy.md").write_text("Refunds within 30 days.", encoding="utf-8")

    docs = read_documents(str(tmp_path))

    assert docs[0]["text"] == "Refunds within 30 days."
    assert docs[0]["metadata"]["source"] == "refund_policy.md"


def test_reads_real_project_documents():
    docs = read_documents()

    ids = {doc["id"] for doc in docs}
    assert ids == {
        "refund_policy",
        "onboarding",
        "vacation_policy",
        "security_policy",
        "support_sla",
        "code_review_policy",
        "customer_complaints_policy",
        "expense_policy",
        "employee_satisfaction_benchmark",
        "customer_success_strategies",
    }
    assert all(doc["text"].strip() for doc in docs)
