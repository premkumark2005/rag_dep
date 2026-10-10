"""Schemas for ingestion, retrieval, and query responses."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from backend.confidence.confidence_gate import RoutingResult
from backend.confidence.schemas import ConfidenceResult
from backend.controller.schemas import ControllerResult
from backend.drift.schemas import SemanticDriftReport
from backend.reflection.schemas import ReflectionReport
from backend.verification.schemas import VerificationReport



class Document(BaseModel):



    """Represents a source document before chunking."""

    document_id: str
    title: str
    text: str
    source: str


class Chunk(BaseModel):
    """Represents a structured chunk for retrieval."""

    chunk_id: str
    document_id: str
    title: str
    text: str
    source: str
    chunk_index: int


class RetrievedChunk(BaseModel):
    """Retrieved chunk with ranking and relevance score."""

    rank: int
    chunk_id: str
    document_id: str
    title: str
    text: str
    source: str
    chunk_index: int
    score: float


class QueryRequest(BaseModel):
    """Request body for a RAG query."""

    question: str
    top_k: int | None = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Question cannot be empty.")
        return value.strip()

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("top_k must be greater than 0.")
        return value


class QueryMetadata(BaseModel):
    """Timing and configuration metadata for a query run."""

    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    top_k: int


class QueryTrace(BaseModel):
    """Intermediate pipeline values preserved for extension in future phases."""

    question: str
    retrieved_chunks: list[RetrievedChunk]
    initial_generated_answer: str
    metadata: QueryMetadata


class QueryResponse(BaseModel):
    """Response body for a RAG query."""

    question: str
    answer: str
    retrieved_chunks: list[RetrievedChunk]
    metadata: QueryMetadata
    trace: QueryTrace


class BM25RetrievedChunk(BaseModel):
    """Sparse retrieval result containing BM25 score."""

    rank: int
    chunk_id: str
    document_id: str
    title: str
    text: str
    source: str
    chunk_index: int
    bm25_score: float


class HybridRetrievedChunk(BaseModel):
    """Merged hybrid retrieval entry with full stage trace fields."""

    rank: int
    chunk_id: str
    document_id: str
    title: str
    text: str
    source: str
    chunk_index: int
    bm25_rank: int | None = None
    bm25_score: float | None = None
    dense_rank: int | None = None
    dense_score: float | None = None
    rrf_score: float


class RerankedChunk(BaseModel):
    """Cross-encoder reranked evidence with preserved retrieval trace."""

    rerank_rank: int
    chunk_id: str
    document_id: str
    title: str
    text: str
    source: str
    chunk_index: int
    reranker_raw_score: float
    bm25_rank: int | None = None
    bm25_score: float | None = None
    dense_rank: int | None = None
    dense_score: float | None = None
    rrf_score: float


class FactStatus(str, Enum):
    """Planner status of an individual required fact."""

    FOUND = "FOUND"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"


class FactEvidence(BaseModel):
    """Evidence entry linked to a required fact."""

    chunk_id: str
    document_id: str
    supported_fact: str


class RequiredFact(BaseModel):
    """A required answer fact and its evidence coverage status."""

    fact_id: str
    requirement: str
    status: FactStatus
    evidence: list[FactEvidence]


class PlanOutput(BaseModel):
    """Structured planner output for evidence-grounded generation."""

    question_intent: str
    required_facts: list[RequiredFact]
    missing_facts: list[str]
    conflicting_facts: list[str]
    answer_instruction: str


class Phase2QueryRequest(BaseModel):
    """Request body for the Phase 2 pipeline endpoint."""

    question: str
    final_context_k: int | None = None
    system: str = "proposed_rag"

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Question cannot be empty.")
        return value.strip()

    @field_validator("final_context_k")
    @classmethod
    def validate_final_context_k(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("final_context_k must be greater than 0.")
        return value


class Phase2RetrievalTrace(BaseModel):
    """Phase 2 retrieval trace for evaluator visibility."""

    bm25_results: list[BM25RetrievedChunk]
    dense_results: list[RetrievedChunk]
    hybrid_results: list[HybridRetrievedChunk]
    reranked_results: list[RerankedChunk]


class Phase2Metadata(BaseModel):
    """Latency metadata for each Phase 2 stage."""

    bm25_time_ms: float
    dense_time_ms: float
    fusion_time_ms: float
    reranking_time_ms: float
    planning_time_ms: float
    generation_time_ms: float
    confidence_time_ms: float
    reflection_time_ms: float = 0.0
    verification_time_ms: float = 0.0
    drift_time_ms: float = 0.0
    controller_time_ms: float = 0.0
    total_time_ms: float
    bm25_top_k: int
    dense_top_k: int
    rerank_top_k: int


class Phase2QueryResponse(BaseModel):
    """Response for the Phase 2 hybrid planned pipeline and baseline systems."""

    request_id: str
    question_id: str | None = None
    system: str = "proposed_rag"
    llm_calls: int = 1
    latency_ms: float | None = None
    question: str
    retrieval: Phase2RetrievalTrace
    plan: dict | PlanOutput | None = None
    initial_answer: str
    candidate_answer: str | None = None
    confidence: dict | ConfidenceResult | None = None
    routing: dict | RoutingResult | None = None
    reflection: dict | ReflectionReport | None = None
    verification: dict | VerificationReport | None = None
    semantic_drift: dict | SemanticDriftReport | None = None
    controller: dict | ControllerResult | None = None
    final_answer: str
    metadata: Phase2Metadata







class IngestResponse(BaseModel):
    """Response body after ingesting documents into FAISS."""

    documents_processed: int
    chunks_created: int
    index_status: str = Field(description="Status of FAISS index creation.")
