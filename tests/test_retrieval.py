from pathlib import Path

import numpy as np

from backend.models.schemas import Chunk
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.embedding_model import EmbeddingModel
from backend.retrieval.vector_store import FAISSVectorStore


class _DummySentenceTransformer:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def encode(self, texts, normalize_embeddings: bool = True):
        vectors = []
        for text in texts:
            lower = text.lower()
            vector = np.array(
                [
                    lower.count("python"),
                    lower.count("guido"),
                    lower.count("java"),
                    lower.count("learning"),
                ],
                dtype=np.float32,
            )
            if normalize_embeddings:
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
            vectors.append(vector)
        return np.array(vectors, dtype=np.float32)


class _RuleBasedEmbedder:
    def _to_vector(self, text: str) -> np.ndarray:
        lower = text.lower()
        vector = np.array(
            [
                lower.count("python"),
                lower.count("guido"),
                lower.count("java"),
                lower.count("james"),
                lower.count("learning"),
            ],
            dtype=np.float32,
        )
        norm = np.linalg.norm(vector)
        return vector / norm if norm > 0 else vector

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return np.array([self._to_vector(text) for text in texts], dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        return self._to_vector(query)


def test_embedding_dimensions_consistent(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.retrieval.embedding_model.EmbeddingModel._load_model",
        lambda self: _DummySentenceTransformer("dummy-model"),
    )
    model = EmbeddingModel("dummy-model")

    doc_vectors = model.embed_documents(["Python", "Java"])
    query_vector = model.embed_query("Who created Python?")

    assert doc_vectors.shape == (2, 4)
    assert query_vector.shape == (4,)


def test_faiss_build_save_load_and_search(tmp_path: Path) -> None:
    store = FAISSVectorStore(tmp_path / "faiss")
    chunks = [
        Chunk(
            chunk_id="chunk_001",
            document_id="doc_python",
            title="python",
            text="Python was created by Guido van Rossum.",
            source="python.txt",
            chunk_index=0,
        ),
        Chunk(
            chunk_id="chunk_002",
            document_id="doc_java",
            title="java",
            text="Java was created by James Gosling.",
            source="java.txt",
            chunk_index=0,
        ),
    ]
    embedder = _RuleBasedEmbedder()
    embeddings = embedder.embed_documents([chunk.text for chunk in chunks])

    store.build_index(chunks, embeddings)
    store.save_index()

    reloaded_store = FAISSVectorStore(tmp_path / "faiss")
    reloaded_store.load_index()
    results = reloaded_store.search(embedder.embed_query("Who created Python?"), top_k=2)

    assert len(results) == 2
    assert results[0][0].document_id == "doc_python"


def test_dense_retrieval_returns_python_for_creator_query(tmp_path: Path) -> None:
    chunks = [
        Chunk(
            chunk_id="chunk_python",
            document_id="doc_python",
            title="python",
            text="Python was created by Guido van Rossum.",
            source="python.txt",
            chunk_index=0,
        ),
        Chunk(
            chunk_id="chunk_java",
            document_id="doc_java",
            title="java",
            text="Java was created by James Gosling.",
            source="java.txt",
            chunk_index=0,
        ),
        Chunk(
            chunk_id="chunk_ml",
            document_id="doc_ml",
            title="machine_learning",
            text="Machine learning is a subset of AI.",
            source="machine_learning.txt",
            chunk_index=0,
        ),
    ]
    embedder = _RuleBasedEmbedder()
    embeddings = embedder.embed_documents([chunk.text for chunk in chunks])

    store = FAISSVectorStore(tmp_path / "faiss")
    store.build_index(chunks, embeddings)
    retriever = DenseRetriever(embedder=embedder, vector_store=store)
    results = retriever.retrieve("Who created Python?", top_k=2)

    assert results
    assert any(item.document_id == "doc_python" for item in results)
