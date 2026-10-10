"""Custom domain exceptions."""


class RAGError(Exception):
    """Base error for the RAG application."""


class IngestionError(RAGError):
    """Raised when ingestion fails."""


class RetrievalError(RAGError):
    """Raised when retrieval fails."""


class VectorStoreError(RAGError):
    """Raised for FAISS/index persistence issues."""


class VectorStoreNotReadyError(VectorStoreError):
    """Raised when vector store is missing or not initialized."""


class EmbeddingModelError(RAGError):
    """Raised when embedding model cannot be loaded or used."""


class LLMConfigurationError(RAGError):
    """Raised when LLM configuration is missing/invalid."""


class LLMGenerationError(RAGError):
    """Raised when LLM generation fails."""


class LLMServiceUnavailableError(LLMGenerationError):
    """Raised when the LLM service is temporarily unavailable (e.g. 503)."""


class LLMRateLimitError(LLMGenerationError):
    """Raised when the LLM service rate limit is exceeded (e.g. 429)."""


class PlanningError(RAGError):
    """Raised when planning stage fails."""

