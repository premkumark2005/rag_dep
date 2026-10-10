"""SentenceTransformer embedding wrapper."""

import os
from typing import Any, Protocol

import numpy as np

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

from backend.utils.exceptions import EmbeddingModelError


class Embedder(Protocol):
    """Common interface for embedders used by retrievers."""

    def embed_documents(self, texts: list[str]) -> np.ndarray: ...

    def embed_query(self, query: str) -> np.ndarray: ...


class EmbeddingModel:
    """Encapsulates a sentence-transformers embedding model."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = self._load_model()

    def _load_model(self) -> Any:
        try:
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(self.model_name)
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingModelError(f"Failed to load embedding model '{self.model_name}': {exc}") from exc

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return np.asarray(embeddings, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        if not query.strip():
            raise EmbeddingModelError("Query for embedding cannot be empty.")
        embedding = self._model.encode([query], normalize_embeddings=True)
        return np.asarray(embedding[0], dtype=np.float32)
