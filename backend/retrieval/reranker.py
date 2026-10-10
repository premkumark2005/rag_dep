"""Cross-encoder reranking for hybrid candidates."""

from __future__ import annotations

import os
from typing import Any, Protocol

from backend.models.schemas import HybridRetrievedChunk, RerankedChunk
from backend.utils.exceptions import RetrievalError

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")


class CrossEncoderPredictor(Protocol):
    """Inference interface used for reranking."""

    def predict(self, pairs: list[list[str]] | list[tuple[str, str]]) -> Any: ...


class CrossEncoderReranker:
    """Reranks hybrid candidates with a configurable cross-encoder model."""

    def __init__(self, model_name: str, predictor: CrossEncoderPredictor | None = None) -> None:
        self.model_name = model_name
        self._predictor = predictor

    @property
    def predictor(self) -> CrossEncoderPredictor:
        if self._predictor is None:
            self._predictor = self._load_predictor()
        return self._predictor

    def _load_predictor(self) -> CrossEncoderPredictor:
        try:
            from sentence_transformers import CrossEncoder

            return CrossEncoder(self.model_name)
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError(f"Failed to load reranker model '{self.model_name}': {exc}") from exc

    def rerank(
        self,
        query: str,
        candidates: list[HybridRetrievedChunk],
        top_k: int,
    ) -> list[RerankedChunk]:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")
        if not candidates:
            return []

        pairs = [(query, item.text) for item in candidates]
        raw_scores = self.predictor.predict(pairs)
        if len(raw_scores) != len(candidates):
            raise RetrievalError("Cross-encoder returned score count different from candidate count.")

        scored_items: list[tuple[HybridRetrievedChunk, float]] = []
        for item, raw_score in zip(candidates, raw_scores, strict=False):
            scored_items.append((item, float(raw_score)))

        scored_items.sort(key=lambda item: item[1], reverse=True)

        reranked: list[RerankedChunk] = []
        for rank, (item, raw_score) in enumerate(scored_items[:top_k], start=1):
            reranked.append(
                RerankedChunk(
                    rerank_rank=rank,
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    title=item.title,
                    text=item.text,
                    source=item.source,
                    chunk_index=item.chunk_index,
                    reranker_raw_score=raw_score,
                    bm25_rank=item.bm25_rank,
                    bm25_score=item.bm25_score,
                    dense_rank=item.dense_rank,
                    dense_score=item.dense_score,
                    rrf_score=item.rrf_score,
                )
            )
        return reranked

