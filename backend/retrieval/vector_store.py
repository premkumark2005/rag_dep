"""FAISS vector store with metadata persistence."""

import json
from pathlib import Path

import faiss
import numpy as np

from backend.models.schemas import Chunk
from backend.utils.exceptions import VectorStoreError, VectorStoreNotReadyError


class FAISSVectorStore:
    """Persists dense vectors in FAISS and chunk metadata in JSON."""

    INDEX_FILENAME = "index.faiss"
    METADATA_FILENAME = "metadata.json"

    def __init__(self, storage_directory: Path) -> None:
        self.storage_directory = storage_directory
        self.index_path = self.storage_directory / self.INDEX_FILENAME
        self.metadata_path = self.storage_directory / self.METADATA_FILENAME
        self.index: faiss.IndexFlatIP | None = None
        self.chunks: list[Chunk] = []

    def build_index(self, chunks: list[Chunk], embeddings: np.ndarray) -> None:
        """Build a new in-memory FAISS index from chunks and embeddings."""
        if not chunks:
            raise VectorStoreError("Cannot build index with empty chunks.")
        if embeddings.size == 0:
            raise VectorStoreError("Cannot build index with empty embeddings.")
        if embeddings.shape[0] != len(chunks):
            raise VectorStoreError("Embeddings count must match chunk count.")
        if embeddings.ndim != 2:
            raise VectorStoreError("Embeddings must be a 2D array.")

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(np.asarray(embeddings, dtype=np.float32))
        self.chunks = list(chunks)

    def save_index(self) -> None:
        """Persist FAISS index and chunk metadata to disk."""
        if self.index is None:
            raise VectorStoreNotReadyError("No in-memory index exists to save.")
        self.storage_directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        metadata = [chunk.model_dump() for chunk in self.chunks]
        self.metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    def load_index(self) -> None:
        """Load FAISS index and metadata from disk into memory."""
        if not self.index_path.exists() or not self.metadata_path.exists():
            raise VectorStoreNotReadyError(
                "FAISS index not found. Run /ingest first to build and save the index."
            )
        self.index = faiss.read_index(str(self.index_path))
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        self.chunks = [Chunk(**item) for item in metadata]

    def search(self, query_embedding: np.ndarray, top_k: int) -> list[tuple[Chunk, float]]:
        """Search top-k chunks using a query embedding."""
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")
        if self.index is None or not self.chunks:
            raise VectorStoreNotReadyError("Vector store is not loaded.")
        if query_embedding.ndim != 1:
            raise VectorStoreError("query_embedding must be a 1D vector.")

        if self.index.ntotal == 0:
            return []

        k = min(top_k, self.index.ntotal)
        query = np.asarray([query_embedding], dtype=np.float32)
        scores, indices = self.index.search(query, k)

        results: list[tuple[Chunk, float]] = []
        for idx, score in zip(indices[0], scores[0], strict=False):
            if idx < 0:
                continue
            results.append((self.chunks[int(idx)], float(score)))
        return results

