from backend.models.schemas import Chunk
from backend.retrieval.bm25_retriever import BM25Retriever


def test_bm25_lexical_match_ranks_java_highest() -> None:
    chunks = [
        Chunk(
            chunk_id="chunk_java",
            document_id="doc_java",
            title="java",
            text="Java was developed by James Gosling.",
            source="java.txt",
            chunk_index=0,
        ),
        Chunk(
            chunk_id="chunk_python",
            document_id="doc_python",
            title="python",
            text="Python was created by Guido van Rossum.",
            source="python.txt",
            chunk_index=0,
        ),
    ]

    retriever = BM25Retriever()
    retriever.build_index(chunks)
    results = retriever.retrieve("James Gosling Java", top_k=2)

    assert results
    assert results[0].chunk_id == "chunk_java"
    assert results[0].bm25_score >= results[1].bm25_score

