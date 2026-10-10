from backend.ingestion.chunker import chunk_document
from backend.models.schemas import Document


def test_chunking_creates_overlapping_non_empty_unique_chunks() -> None:
    document = Document(
        document_id="doc_001",
        title="sample",
        text="ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 30,
        source="memory://sample",
    )

    chunk_size = 100
    chunk_overlap = 20
    chunks = chunk_document(document, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    assert chunks
    assert all(chunk.text.strip() for chunk in chunks)
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)

    if len(chunks) > 1:
        expected_overlap = chunks[0].text[-chunk_overlap:]
        assert chunks[1].text.startswith(expected_overlap)


def test_chunking_rejects_invalid_overlap() -> None:
    document = Document(
        document_id="doc_001",
        title="sample",
        text="hello world",
        source="memory://sample",
    )
    try:
        chunk_document(document, chunk_size=100, chunk_overlap=100)
    except ValueError as exc:
        assert "0 <= chunk_overlap < chunk_size" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid overlap.")

