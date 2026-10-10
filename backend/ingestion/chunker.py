"""Configurable text chunking utilities."""

from backend.models.schemas import Chunk, Document


def chunk_document(document: Document, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    """Split a document into overlapping chunks while preserving metadata."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must satisfy 0 <= chunk_overlap < chunk_size.")

    text = document.text.strip()
    if not text:
        return []

    step = chunk_size - chunk_overlap
    chunks: list[Chunk] = []
    chunk_index = 0

    for start in range(0, len(text), step):
        piece = text[start : start + chunk_size].strip()
        if not piece:
            continue
        chunks.append(
            Chunk(
                chunk_id=f"{document.document_id}_chunk_{chunk_index:04d}",
                document_id=document.document_id,
                title=document.title,
                text=piece,
                source=document.source,
                chunk_index=chunk_index,
            )
        )
        chunk_index += 1
        if start + chunk_size >= len(text):
            break

    return chunks

