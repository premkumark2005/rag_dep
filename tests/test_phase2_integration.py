import json
from pathlib import Path

import numpy as np

from backend.confidence.confidence_estimator import ConfidenceEstimator
from backend.config import Settings
from backend.generation.generator import PlannedAnswerGenerator
from backend.generation.llm_client import MockLLMClient
from backend.models.schemas import Chunk, RetrievedChunk
from backend.planning.planner import PlanningModule
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.reranker import CrossEncoderReranker
from backend.retrieval.vector_store import FAISSVectorStore
from backend.services.phase2_service import Phase2PipelineService


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
                },
                {
                    "fact_id": "fact_2",
                    "requirement": "First public release year of Python",
                    "status": "FOUND",
                    "evidence": [
                        {
                            "chunk_id": "doc_001_chunk_0001",
                            "document_id": "doc_001",
                            "supported_fact": "Python was first publicly released in 1991.",
                        }
                    ],
                },
            ],
            "missing_facts": [],
            "conflicting_facts": [],
            "answer_instruction": "State creator and release year from evidence only.",
        }
        return json.dumps(payload)


def _build_phase2_service(tmp_path: Path) -> Phase2PipelineService:
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
        Chunk(
            chunk_id="doc_002_chunk_0000",
            document_id="doc_002",
            title="java",
            text="Java was created by James Gosling.",
            source="java.txt",
            chunk_index=0,
        ),
    ]

    embedder = _RuleBasedEmbedder()
    store = FAISSVectorStore(tmp_path / "faiss")
    store.build_index(chunks, embedder.embed_documents([chunk.text for chunk in chunks]))
    dense_retriever = DenseRetriever(embedder=embedder, vector_store=store)

    bm25_retriever = BM25Retriever()
    bm25_retriever.build_index(chunks)

    settings = Settings(
        BM25_TOP_K=3,
        DENSE_TOP_K=3,
        RRF_K=60,
        RERANK_TOP_K=2,
        RERANKER_MODEL="stub",
        LLM_PROVIDER="mock",
    )

    return Phase2PipelineService(
        settings=settings,
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        hybrid_retriever=HybridRetriever(rrf_k=settings.rrf_k),
        reranker=CrossEncoderReranker(model_name="stub", predictor=_PredictorStub()),
        planner=PlanningModule(_PlannerLLMStub()),
        planned_generator=PlannedAnswerGenerator(MockLLMClient()),
        confidence_estimator=ConfidenceEstimator(settings),
    )


def test_phase2_pipeline_returns_trace_plan_and_initial_answer(tmp_path: Path) -> None:
    service = _build_phase2_service(tmp_path)
    response = service.query("Who created Python and when was it first released?", final_context_k=2)

    assert response.question
    assert len(response.retrieval.bm25_results) > 0
    assert len(response.retrieval.dense_results) > 0
    assert len(response.retrieval.hybrid_results) > 0
    assert len(response.retrieval.reranked_results) == 2
    assert response.retrieval.reranked_results[0].chunk_id == "doc_001_chunk_0000"
    assert response.plan.required_facts
    assert response.plan.missing_facts == []
    assert response.initial_answer
    assert response.confidence.overall_confidence >= 0
    assert response.confidence.retrieval_confidence >= 0
    assert response.confidence.component_scores
    assert response.routing.decision is not None
    assert response.routing.next_action is not None
    assert response.routing.threshold == service.settings.confidence_threshold
    assert response.reflection is not None
    assert response.reflection.reflection_required in (True, False)
    assert response.verification is not None
    assert 0.0 <= response.verification.verification_score <= 1.0
    assert response.semantic_drift is not None
    assert 0.0 <= response.semantic_drift.drift_score <= 1.0
    assert response.controller is not None
    assert response.controller.decision is not None
    assert response.controller.selected_answer_type is not None
    assert response.final_answer
    assert response.metadata.total_time_ms >= 0




