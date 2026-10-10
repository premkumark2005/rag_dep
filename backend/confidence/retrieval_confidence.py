"""Retrieval confidence from reranker scores."""

from backend.confidence.schemas import RetrievalConfidenceResult
from backend.confidence.utils import clamp
from backend.models.schemas import RerankedChunk


class RetrievalConfidenceScorer:
    """Computes retrieval confidence from reranked evidence."""

    def score(self, reranked_chunks: list[RerankedChunk]) -> RetrievalConfidenceResult:
        if not reranked_chunks:
            return RetrievalConfidenceResult(
                retrieval_confidence=0.0,
                top_document_raw_score=0.0,
                top_document_normalized_score=0.0,
                average_top_k_raw_score=0.0,
                average_top_k_normalized_score=0.0,
            )

        raw_scores = [item.reranker_raw_score for item in reranked_chunks]
        min_raw = min(raw_scores)
        max_raw = max(raw_scores)
        if max_raw == min_raw:
            normalized = [0.5 for _ in raw_scores]
        else:
            normalized = [(value - min_raw) / (max_raw - min_raw) for value in raw_scores]

        weighted_sum = 0.0
        weight_total = 0.0
        for index, value in enumerate(normalized, start=1):
            weight = 1.0 / index
            weighted_sum += value * weight
            weight_total += weight
        retrieval_confidence = clamp(weighted_sum / weight_total if weight_total else 0.0)

        top_raw = raw_scores[0]
        top_normalized = normalized[0]
        avg_raw = sum(raw_scores) / len(raw_scores)
        avg_normalized = sum(normalized) / len(normalized)

        return RetrievalConfidenceResult(
            retrieval_confidence=round(retrieval_confidence, 6),
            top_document_raw_score=round(float(top_raw), 6),
            top_document_normalized_score=round(float(top_normalized), 6),
            average_top_k_raw_score=round(float(avg_raw), 6),
            average_top_k_normalized_score=round(float(avg_normalized), 6),
        )

