"""Baseline 1: Traditional RAG Service Implementation.

Pipeline:
Question -> Dense Retrieval (FAISS) -> Top-K Chunks -> Direct LLM Generation -> Final Answer

Excludes:
BM25, Hybrid Retrieval, RRF, Cross Encoder Reranking, Planning, Confidence Estimator,
Confidence Gate, Reflection, Verification, Semantic Drift, Dynamic Controller.
"""

import time
import uuid

from backend.config import Settings
from backend.generation.generator import AnswerGenerator
from backend.generation.llm_client import LLMClient
from backend.models.schemas import Phase2Metadata, Phase2QueryResponse, Phase2RetrievalTrace
from backend.retrieval.dense_retriever import DenseRetriever
from backend.services.trace_store import save_trace
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class TraditionalRAGService:
    """Runs Baseline 1: Traditional RAG."""

    def __init__(
        self,
        settings: Settings,
        dense_retriever: DenseRetriever,
        llm_client: LLMClient,
    ) -> None:
        self.settings = settings
        self.dense_retriever = dense_retriever
        self.generator = AnswerGenerator(llm_client)

    def query(self, question: str, top_k: int | None = None) -> Phase2QueryResponse:
        selected_top_k = top_k or self.settings.dense_top_k
        total_start = time.perf_counter()

        # Step 1: Dense Retrieval
        dense_start = time.perf_counter()
        dense_results = self.dense_retriever.retrieve(question, selected_top_k)
        dense_time_ms = (time.perf_counter() - dense_start) * 1000

        # Step 2: Direct Answer Generation
        gen_start = time.perf_counter()
        answer = self.generator.generate(question, dense_results)
        generation_time_ms = (time.perf_counter() - gen_start) * 1000

        total_time_ms = (time.perf_counter() - total_start) * 1000

        request_id = f"req_{uuid.uuid4().hex[:12]}"

        metadata = Phase2Metadata(
            bm25_time_ms=0.0,
            dense_time_ms=round(dense_time_ms, 3),
            fusion_time_ms=0.0,
            reranking_time_ms=0.0,
            planning_time_ms=0.0,
            generation_time_ms=round(generation_time_ms, 3),
            confidence_time_ms=0.0,
            reflection_time_ms=0.0,
            verification_time_ms=0.0,
            drift_time_ms=0.0,
            controller_time_ms=0.0,
            total_time_ms=round(total_time_ms, 3),
            bm25_top_k=0,
            dense_top_k=selected_top_k,
            rerank_top_k=0,
        )

        retrieval_trace = Phase2RetrievalTrace(
            bm25_results=[],
            dense_results=dense_results,
            hybrid_results=[],
            reranked_results=[],
        )

        response = Phase2QueryResponse(
            request_id=request_id,
            question_id=request_id,
            system="traditional_rag",
            llm_calls=1,
            latency_ms=round(total_time_ms, 3),
            question=question,
            retrieval=retrieval_trace,
            plan={"applicable": False},
            initial_answer=answer,
            candidate_answer=None,
            confidence={"applicable": False},
            routing={"applicable": False},
            reflection={
                "applicable": False,
                "triggered": False,
                "reflection_required": False,
                "reflection_reason": "Not applicable",
                "identified_problems": [],
                "missing_facts": [],
                "unsupported_claims": [],
                "candidate_answer": None,
                "reflection_summary": "Not applicable",
            },
            verification={
                "applicable": False,
                "verified_claims": [],
                "supported_claims": [],
                "unsupported_claims": [],
                "contradicted_claims": [],
                "verification_score": 0.0,
            },
            semantic_drift={
                "applicable": False,
                "drift_detected": False,
                "drift_score": 0.0,
                "drift_reason": "Not applicable",
            },
            controller={
                "applicable": False,
                "decision": "RETURN_INITIAL",
                "reason": "Not applicable",
                "selected_answer": answer,
                "selected_answer_type": "INITIAL",
                "metrics": {
                    "confidence": 0.0,
                    "verification": 0.0,
                    "drift": 0.0,
                    "verification_threshold": 0.0,
                    "drift_threshold": 0.0,
                    "decision_latency_ms": 0.0,
                },
                "final_status": "Not applicable",
            },
            final_answer=answer,
            metadata=metadata,
        )

        save_trace(response)
        logger.info("Traditional RAG query completed | request_id=%s | latency_ms=%.3f", request_id, total_time_ms)
        return response
