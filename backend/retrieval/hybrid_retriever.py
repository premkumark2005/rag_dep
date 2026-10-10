"""Hybrid retrieval using Reciprocal Rank Fusion (RRF)."""

from dataclasses import dataclass

from backend.models.schemas import BM25RetrievedChunk, HybridRetrievedChunk, RetrievedChunk


@dataclass
class HybridRetrievalOutput:
    """Container for independent and fused retrieval outputs."""

    bm25_results: list[BM25RetrievedChunk]
    dense_results: list[RetrievedChunk]
    hybrid_results: list[HybridRetrievedChunk]


class HybridRetriever:
    """Fuses BM25 and dense rankings using RRF without score mixing."""

    def __init__(self, rrf_k: int) -> None:
        if rrf_k <= 0:
            raise ValueError("rrf_k must be greater than 0.")
        self.rrf_k = rrf_k

    def fuse(
        self,
        bm25_results: list[BM25RetrievedChunk],
        dense_results: list[RetrievedChunk],
        top_k: int,
    ) -> list[HybridRetrievedChunk]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        merged: dict[str, HybridRetrievedChunk] = {}

        for item in bm25_results:
            merged[item.chunk_id] = HybridRetrievedChunk(
                rank=0,
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                title=item.title,
                text=item.text,
                source=item.source,
                chunk_index=item.chunk_index,
                bm25_rank=item.rank,
                bm25_score=item.bm25_score,
                dense_rank=None,
                dense_score=None,
                rrf_score=1.0 / (self.rrf_k + item.rank),
            )

        for item in dense_results:
            existing = merged.get(item.chunk_id)
            if existing is None:
                merged[item.chunk_id] = HybridRetrievedChunk(
                    rank=0,
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    title=item.title,
                    text=item.text,
                    source=item.source,
                    chunk_index=item.chunk_index,
                    bm25_rank=None,
                    bm25_score=None,
                    dense_rank=item.rank,
                    dense_score=item.score,
                    rrf_score=1.0 / (self.rrf_k + item.rank),
                )
                continue

            existing.dense_rank = item.rank
            existing.dense_score = item.score
            existing.rrf_score += 1.0 / (self.rrf_k + item.rank)

        ranked = sorted(
            merged.values(),
            key=lambda item: item.rrf_score,
            reverse=True,
        )
        for rank, item in enumerate(ranked[:top_k], start=1):
            item.rank = rank
        return ranked[:top_k]

