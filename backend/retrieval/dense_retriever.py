"""Dense retriever using sentence embeddings + FAISS."""

from backend.models.schemas import RetrievedChunk
from backend.retrieval.embedding_model import Embedder
from backend.retrieval.vector_store import FAISSVectorStore


class DenseRetriever:
    """Runs dense retrieval over a FAISS index."""

    def __init__(self, embedder: Embedder, vector_store: FAISSVectorStore) -> None:
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        query_embedding = self.embedder.embed_query(query.strip())
        matches = self.vector_store.search(query_embedding, top_k)

        results: list[RetrievedChunk] = []
        for rank, (chunk, score) in enumerate(matches, start=1):
            results.append(
                RetrievedChunk(
                    rank=rank,
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    title=chunk.title,
                    text=chunk.text,
                    source=chunk.source,
                    chunk_index=chunk.chunk_index,
                    score=score,
                )
            )
        return results

