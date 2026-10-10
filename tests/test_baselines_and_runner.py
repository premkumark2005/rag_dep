"""Tests for STEP 4: Three Experimental Systems, Common Result Schema, and Evaluation Runner."""

import json
from pathlib import Path
import numpy as np
import pytest

from backend.confidence.confidence_estimator import ConfidenceEstimator
from backend.config import Settings
from backend.generation.generator import PlannedAnswerGenerator
from backend.generation.llm_client import MockLLMClient
from backend.models.schemas import Chunk
from backend.planning.planner import PlanningModule
from backend.reflection.reflection_service import ReflectionService
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.reranker import CrossEncoderReranker
from backend.retrieval.vector_store import FAISSVectorStore
from backend.services.phase2_service import Phase2PipelineService
from backend.services.trace_store import list_traces


class _RuleBasedEmbedder:
    def _to_vector(self, text: str) -> np.ndarray:
        lower = text.lower()
        vector = np.array(
            [
                lower.count("python"),
                lower.count("guido"),
                lower.count("1991"),
                lower.count("java"),
            ],
            dtype=np.float32,
        )
        norm = np.linalg.norm(vector)
        return vector / norm if norm > 0 else vector

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return np.array([self._to_vector(text) for text in texts], dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        return self._to_vector(query)


class _PredictorStub:
    def predict(self, pairs):
        scores = []
        for _, passage in pairs:
            lower = passage.lower()
            if "guido" in lower:
                scores.append(1.0)
            elif "1991" in lower:
                scores.append(0.95)
            elif "python" in lower:
                scores.append(0.8)
            else:
                scores.append(0.0)
        return scores


class _PlannerLLMStub:
    def generate(self, prompt: str) -> str:
        _ = prompt
        payload = {
            "question_intent": "Identify Python creator and first release year.",
            "required_facts": [
                {
                    "fact_id": "fact_1",
                    "requirement": "Creator of Python",
                    "status": "FOUND",
                    "evidence": [
                        {
                            "chunk_id": "doc_001_chunk_0000",
                            "document_id": "doc_001",
                            "supported_fact": "Python was created by Guido van Rossum.",
                        }
                    ],
                }
            ],
            "missing_facts": [],
            "conflicting_facts": [],
            "answer_instruction": "State creator and release year from evidence only.",
        }
        return json.dumps(payload)


@pytest.fixture
def phase2_service(tmp_path: Path) -> Phase2PipelineService:
    chunks = [
        Chunk(
            chunk_id="doc_001_chunk_0000",
            document_id="doc_001",
            title="python",
            text="Python was created by Guido van Rossum.",
            source="python.txt",
            chunk_index=0,
        ),
        Chunk(
            chunk_id="doc_001_chunk_0001",
            document_id="doc_001",
            title="python",
            text="Python was first publicly released in 1991.",
            source="python.txt",
            chunk_index=1,
        ),
    ]

    embedder = _RuleBasedEmbedder()
    store = FAISSVectorStore(tmp_path / "faiss")
    store.build_index(chunks, embedder.embed_documents([chunk.text for chunk in chunks]))
    dense_retriever = DenseRetriever(embedder=embedder, vector_store=store)

    bm25_retriever = BM25Retriever()
    bm25_retriever.build_index(chunks)

    settings = Settings(
        BM25_TOP_K=2,
        DENSE_TOP_K=2,
        RRF_K=60,
        RERANK_TOP_K=2,
        RERANKER_MODEL="stub",
        LLM_PROVIDER="mock",
    )

    mock_client = MockLLMClient()
    return Phase2PipelineService(
        settings=settings,
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        hybrid_retriever=HybridRetriever(rrf_k=settings.rrf_k),
        reranker=CrossEncoderReranker(model_name="stub", predictor=_PredictorStub()),
        planner=PlanningModule(_PlannerLLMStub()),
        planned_generator=PlannedAnswerGenerator(mock_client),
        confidence_estimator=ConfidenceEstimator(settings),
        reflection_service=ReflectionService(mock_client),
    )


def test_traditional_rag_does_not_call_reflection(phase2_service: Phase2PipelineService) -> None:
    """Test 1: Traditional RAG does not call reflection and has llm_calls == 1."""
    res = phase2_service.query("Who created Python?", system="traditional_rag")
    assert res.system == "traditional_rag"
    assert res.llm_calls == 1
    assert res.reflection["applicable"] is False
    assert res.confidence["applicable"] is False
    assert res.verification["applicable"] is False
    assert res.semantic_drift["applicable"] is False
    assert res.controller["applicable"] is False


def test_always_reflection_always_calls_reflection(phase2_service: Phase2PipelineService) -> None:
    """Test 2: Always-Reflection RAG always calls reflection and has llm_calls == 2."""
    res = phase2_service.query("Who created Python?", system="always_reflection")
    assert res.system == "always_reflection"
    assert res.llm_calls == 2
    assert res.reflection["applicable"] is True
    assert res.reflection["triggered"] is True
    assert res.reflection["reflection_required"] is True
    assert res.confidence["applicable"] is False
    assert res.verification["applicable"] is False
    assert res.semantic_drift["applicable"] is False


def test_proposed_rag_uses_confidence_gate(phase2_service: Phase2PipelineService) -> None:
    """Test 3: Proposed RAG still uses the confidence gate."""
    res = phase2_service.query("Who created Python?", system="proposed_rag")
    assert res.system == "proposed_rag"
    assert res.confidence is not None
    assert hasattr(res.confidence, "overall_confidence")
    assert res.routing is not None
    assert hasattr(res.routing, "decision")


def test_system_selection(phase2_service: Phase2PipelineService) -> None:
    """Test 4: Correct system selection routes to correct service."""
    t_res = phase2_service.query("Who created Python?", system="traditional_rag")
    a_res = phase2_service.query("Who created Python?", system="always_reflection")
    p_res = phase2_service.query("Who created Python?", system="proposed_rag")

    assert t_res.system == "traditional_rag"
    assert a_res.system == "always_reflection"
    assert p_res.system == "proposed_rag"


def test_common_result_schema(phase2_service: Phase2PipelineService) -> None:
    """Test 5: All 3 systems conform to common result schema."""
    for sys_name in ["traditional_rag", "always_reflection", "proposed_rag"]:
        res = phase2_service.query("Who created Python?", system=sys_name)
        d = res.model_dump()
        assert "request_id" in d
        assert "system" in d
        assert "question" in d
        assert "final_answer" in d
        assert "llm_calls" in d
        assert "retrieval" in d
        assert "metadata" in d


def test_non_applicable_fields(phase2_service: Phase2PipelineService) -> None:
    """Test 9: Non-applicable fields display applicable: false in Traditional RAG."""
    res = phase2_service.query("Who created Python?", system="traditional_rag")
    assert res.confidence["applicable"] is False
    assert res.plan["applicable"] is False
    assert res.verification["applicable"] is False
    assert res.semantic_drift["applicable"] is False
    assert res.controller["applicable"] is False


def test_query_history_records_selected_system(phase2_service: Phase2PipelineService) -> None:
    """Test 11: Query history records selected system."""
    phase2_service.query("Who created Python?", system="traditional_rag")
    phase2_service.query("What is FAISS?", system="always_reflection")

    traces = list_traces()
    systems = [t["system"] for t in traces]
    assert "traditional_rag" in systems
    assert "always_reflection" in systems
