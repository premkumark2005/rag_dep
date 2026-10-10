from backend.models.schemas import HybridRetrievedChunk
from backend.retrieval.reranker import CrossEncoderReranker


class _PredictorStub:
    def predict(self, pairs):
        scores = []
        for _, passage in pairs:
            lower = passage.lower()
            if "guido" in lower and "python" in lower:
                scores.append(1.0)
            elif "james gosling" in lower and "java" in lower:
                scores.append(0.2)
            else:
                scores.append(0.0)
        return scores


def test_cross_encoder_reranker_orders_more_relevant_candidate_first() -> None:
    candidates = [
        HybridRetrievedChunk(
            rank=1,
            chunk_id="chunk_java",
            document_id="doc_java",
            title="java",
            text="Java was created by James Gosling.",
            source="java.txt",
            chunk_index=0,
            bm25_rank=1,
            bm25_score=9.0,
            dense_rank=2,
            dense_score=0.6,
            rrf_score=0.03,
        ),
        HybridRetrievedChunk(
            rank=2,
            chunk_id="chunk_python",
            document_id="doc_python",
            title="python",
            text="Python was created by Guido van Rossum.",
            source="python.txt",
            chunk_index=0,
            bm25_rank=2,
            bm25_score=8.5,
            dense_rank=1,
            dense_score=0.9,
            rrf_score=0.032,
        ),
    ]

    reranker = CrossEncoderReranker(model_name="stub-model", predictor=_PredictorStub())
    reranked = reranker.rerank("Who created Python?", candidates, top_k=2)

    assert len(reranked) == 2
    assert reranked[0].chunk_id == "chunk_python"
    assert reranked[0].rerank_rank == 1
    assert reranked[0].reranker_raw_score > reranked[1].reranker_raw_score
    assert reranked[0].bm25_rank == 2
    assert reranked[0].dense_rank == 1

