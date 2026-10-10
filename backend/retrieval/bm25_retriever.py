"""BM25 sparse retrieval over ingested chunks."""

import re

from rank_bm25 import BM25Okapi

from backend.models.schemas import BM25RetrievedChunk, Chunk
from backend.utils.exceptions import RetrievalError, VectorStoreNotReadyError

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


def tokenize_for_bm25(text: str) -> list[str]:
    """Lowercase deterministic tokenization for BM25 indexing/querying."""
    return _TOKEN_PATTERN.findall(text.lower())


class BM25Retriever:
    """Sparse lexical retriever sharing the same chunk metadata as dense retrieval."""

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._tokenized_corpus: list[list[str]] = []
        self._bm25: BM25Okapi | None = None

    @property
    def is_ready(self) -> bool:
        return self._bm25 is not None and bool(self._chunks)

    def build_index(self, chunks: list[Chunk]) -> None:
        if not chunks:
            raise RetrievalError("Cannot build BM25 index with empty chunks.")
        tokenized = [tokenize_for_bm25(chunk.text) for chunk in chunks]
        if not any(tokenized):
            raise RetrievalError("BM25 tokenized corpus is empty.")

        self._chunks = list(chunks)
        self._tokenized_corpus = tokenized
        self._bm25 = BM25Okapi(self._tokenized_corpus)

    def retrieve(self, query: str, top_k: int) -> list[BM25RetrievedChunk]:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")
        if self._bm25 is None or not self._chunks:
            raise VectorStoreNotReadyError("BM25 index is not built. Ingest or load chunks first.")

        query_tokens = tokenize_for_bm25(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda idx: float(scores[idx]),
            reverse=True,
        )

        results: list[BM25RetrievedChunk] = []
        for rank, idx in enumerate(ranked_indices[: min(top_k, len(ranked_indices))], start=1):
            chunk = self._chunks[idx]
            results.append(
                BM25RetrievedChunk(
                    rank=rank,
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    title=chunk.title,
                    text=chunk.text,
                    source=chunk.source,
                    chunk_index=chunk.chunk_index,
                    bm25_score=float(scores[idx]),
                )
            )
        return results
