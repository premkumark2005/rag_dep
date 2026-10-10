import pytest

from backend.models.schemas import BM25RetrievedChunk, RetrievedChunk
from backend.retrieval.hybrid_retriever import HybridRetriever


def test_rrf_fusion_merges_duplicates_and_preserves_scores() -> None:
    bm25_results = [
        BM25RetrievedChunk(
            rank=1,
            chunk_id="chunk_a",
            document_id="doc_1",
            title="doc1",
            text="A",
            source="a.txt",
            chunk_index=0,
            bm25_score=8.2,
        ),
        BM25RetrievedChunk(
            rank=2,
            chunk_id="chunk_b",
            document_id="doc_2",
            title="doc2",
            text="B",
            source="b.txt",
            chunk_index=0,
            bm25_score=7.1,
        ),
        BM25RetrievedChunk(
            rank=3,
            chunk_id="chunk_c",
            document_id="doc_3",
            title="doc3",
            text="C",
            source="c.txt",
            chunk_index=0,
            bm25_score=6.0,
        ),
    ]
    dense_results = [
        RetrievedChunk(
            rank=1,
            chunk_id="chunk_c",
            document_id="doc_3",
            title="doc3",
            text="C",
            source="c.txt",
            chunk_index=0,
            score=0.91,
        ),
        RetrievedChunk(
            rank=2,
            chunk_id="chunk_a",
            document_id="doc_1",
            title="doc1",
            text="A",
            source="a.txt",
            chunk_index=0,
            score=0.88,
        ),
        RetrievedChunk(
            rank=3,
            chunk_id="chunk_d",
            document_id="doc_4",
            title="doc4",
            text="D",
            source="d.txt",
            chunk_index=0,
            score=0.75,
        ),
    ]

    retriever = HybridRetriever(rrf_k=60)
    fused = retriever.fuse(bm25_results=bm25_results, dense_results=dense_results, top_k=4)

    assert len(fused) == 4
    assert len({item.chunk_id for item in fused}) == 4

    chunk_a = next(item for item in fused if item.chunk_id == "chunk_a")
    expected_rrf = (1.0 / (60 + 1)) + (1.0 / (60 + 2))
    assert chunk_a.bm25_rank == 1
    assert chunk_a.dense_rank == 2
    assert chunk_a.bm25_score == pytest.approx(8.2)
    assert chunk_a.dense_score == pytest.approx(0.88)
    assert chunk_a.rrf_score == pytest.approx(expected_rrf)

    assert fused[0].chunk_id == "chunk_a"

