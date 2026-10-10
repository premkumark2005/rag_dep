from pathlib import Path

from backend.ingestion.document_loader import load_txt_documents


def test_documents_load_with_metadata(tmp_path: Path) -> None:
    docs_dir = tmp_path / "sample_documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "python.txt").write_text("Python was created by Guido van Rossum.", encoding="utf-8")
    (docs_dir / "java.txt").write_text("Java was created at Sun Microsystems.", encoding="utf-8")

    documents = load_txt_documents(docs_dir)

    assert len(documents) == 2
    assert documents[0].document_id == "doc_001"
    assert {doc.title for doc in documents} == {"python", "java"}
    for doc in documents:
        assert doc.source.endswith(f"{doc.title}.txt")
        assert doc.text
