"""Application configuration."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    data_directory: Path = Field(default=PROJECT_ROOT / "data" / "sample_documents", alias="DATA_DIRECTORY")
    faiss_storage_directory: Path = Field(default=PROJECT_ROOT / "storage" / "faiss", alias="FAISS_STORAGE_DIRECTORY")

    chunk_size: int = Field(default=500, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP")

    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )
    default_top_k: int = Field(default=5, alias="DEFAULT_TOP_K")
    bm25_top_k: int = Field(default=10, alias="BM25_TOP_K")
    dense_top_k: int = Field(default=10, alias="DENSE_TOP_K")
    rrf_k: int = Field(default=60, alias="RRF_K")
    rerank_top_k: int = Field(default=5, alias="RERANK_TOP_K")
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        alias="RERANKER_MODEL",
    )
    confidence_threshold: float = Field(default=0.70, alias="CONFIDENCE_THRESHOLD")
    verification_threshold: float = Field(default=0.80, alias="VERIFICATION_THRESHOLD")
    drift_threshold: float = Field(default=0.20, alias="DRIFT_THRESHOLD")
    max_reflection_attempts: int = Field(default=1, alias="MAX_REFLECTION_ATTEMPTS")
    retrieval_weight: float = Field(default=0.20, alias="RETRIEVAL_WEIGHT")

    support_weight: float = Field(default=0.35, alias="SUPPORT_WEIGHT")
    fact_weight: float = Field(default=0.20, alias="FACT_WEIGHT")
    consistency_weight: float = Field(default=0.15, alias="CONSISTENCY_WEIGHT")
    agreement_weight: float = Field(default=0.10, alias="AGREEMENT_WEIGHT")

    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_model: str = Field(default="mock-rag-baseline", alias="LLM_MODEL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")

    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("CHUNK_SIZE must be greater than 0.")
        return value

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, value: int, info) -> int:
        chunk_size = info.data.get("chunk_size")
        if value < 0:
            raise ValueError("CHUNK_OVERLAP must be >= 0.")
        if isinstance(chunk_size, int) and value >= chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")
        return value

    @field_validator("default_top_k")
    @classmethod
    def validate_top_k(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("DEFAULT_TOP_K must be greater than 0.")
        return value

    @field_validator("bm25_top_k", "dense_top_k", "rrf_k", "rerank_top_k")
    @classmethod
    def validate_positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Phase 2 retrieval/reranking settings must be greater than 0.")
        return value

    @field_validator(
        "confidence_threshold",
        "retrieval_weight",
        "support_weight",
        "fact_weight",
        "consistency_weight",
        "agreement_weight",
    )
    @classmethod
    def validate_confidence_fraction(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("Confidence thresholds and weights must be within [0, 1].")
        return value


settings = Settings()
