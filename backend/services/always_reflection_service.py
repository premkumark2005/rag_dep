"""Baseline 2: Always-Reflection RAG Service Implementation.

Pipeline:
Question -> Retrieval (Dense/Hybrid) -> Initial Answer -> Mandatory Reflection -> Revised Answer

Reflection MUST always execute.

Excludes:
Confidence Gate, Dynamic Reflection Controller, Semantic Drift Detection,
Evidence Verification, Controller decision logic.
"""

import time
import uuid

from backend.confidence.schemas import ConfidenceResult
from backend.config import Settings
from backend.generation.generator import AnswerGenerator
from backend.generation.llm_client import LLMClient
from backend.models.schemas import Phase2Metadata, Phase2QueryResponse, Phase2RetrievalTrace, PlanOutput, RerankedChunk
from backend.reflection.reflection_agent import ReflectionAgent
from backend.reflection.schemas import ReflectionReport
from backend.retrieval.dense_retriever import DenseRetriever
from backend.services.trace_store import save_trace
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AlwaysReflectionService:
    """Runs Baseline 2: Always-Reflection RAG."""

    def __init__(
        self,
        settings: Settings,
        dense_retriever: DenseRetriever,
        llm_client: LLMClient,
    ) -> None:
        self.settings = settings
        self.dense_retriever = dense_retriever
        self.generator = AnswerGenerator(llm_client)
        self.reflection_agent = ReflectionAgent(llm_client)

    def query(self, question: str, top_k: int | None = None) -> Phase2QueryResponse:
        selected_top_k = top_k or self.settings.dense_top_k
        total_start = time.perf_counter()

        # Step 1: Retrieval
        dense_start = time.perf_counter()
        dense_results = self.dense_retriever.retrieve(question, selected_top_k)
        dense_time_ms = (time.perf_counter() - dense_start) * 1000

        # Step 2: Initial Answer Generation
        gen_start = time.perf_counter()
        initial_answer = self.generator.generate(question, dense_results)
        generation_time_ms = (time.perf_counter() - gen_start) * 1000

        # Convert DenseRetrievedChunks to RerankedChunks for reflection format
        evidence_chunks = [
            RerankedChunk(
                rerank_rank=chunk.rank,
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                title=chunk.title,
                text=chunk.text,
                source=chunk.source,
                chunk_index=chunk.chunk_index,
                reranker_raw_score=chunk.score,
                rrf_score=chunk.score,
            )
            for chunk in dense_results
        ]

        dummy_plan = PlanOutput(
            question_intent=f"Answer the question: {question}",
            required_facts=[],
            missing_facts=[],
            conflicting_facts=[],
            answer_instruction="Reflect on the initial answer using provided evidence.",
        )

        from backend.confidence.schemas import (
            AnswerConsistencyResult,
            EvidenceAgreementResult,
            EvidenceSupportResult,
            FactCoverageResult,
            RetrievalConfidenceResult,
        )

        dummy_confidence = ConfidenceResult(
            retrieval_confidence=0.5,
            evidence_support=0.5,
            fact_coverage=0.5,
            answer_consistency=0.5,
            evidence_agreement=0.5,
            overall_confidence=0.5,
            component_scores={},
            retrieval_details=RetrievalConfidenceResult(
                retrieval_confidence=0.5,
                top_document_raw_score=0.5,
                top_document_normalized_score=0.5,
                average_top_k_raw_score=0.5,
                average_top_k_normalized_score=0.5,
            ),
            support_details=EvidenceSupportResult(evidence_support=0.5, claim_scores=[]),
            coverage_details=FactCoverageResult(fact_coverage=0.5, covered_facts=[], missing_facts=[]),
            consistency_details=AnswerConsistencyResult(answer_consistency=0.5, contradictions=[]),
            agreement_details=EvidenceAgreementResult(evidence_agreement=0.5, conflicting_chunk_ids=[], conflicting_facts=[]),
        )

        # Step 3: Mandatory Reflection
        refl_start = time.perf_counter()
        reflection_report, _ = self.reflection_agent.reflect(
            question=question,
            plan=dummy_plan,
            evidence=evidence_chunks,
            initial_answer=initial_answer,
            confidence=dummy_confidence,
            reason="Always-Reflection Baseline Policy: Mandatory single-pass reflection pass.",
        )
        reflection_time_ms = (time.perf_counter() - refl_start) * 1000

        final_answer = reflection_report.candidate_answer or initial_answer
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
            reflection_time_ms=round(reflection_time_ms, 3),
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
            reranked_results=evidence_chunks,
        )

        # Ensure reflection dict/model carries applicable and triggered flags
        reflection_dict = reflection_report.model_dump()
        reflection_dict["applicable"] = True
        reflection_dict["triggered"] = True
        reflection_dict["reflection_required"] = True

        response = Phase2QueryResponse(
            request_id=request_id,
            question_id=request_id,
            system="always_reflection",
            llm_calls=2,
            latency_ms=round(total_time_ms, 3),
            question=question,
            retrieval=retrieval_trace,
            plan={"applicable": False},
            initial_answer=initial_answer,
            candidate_answer=final_answer,
            confidence={"applicable": False},
            routing={"applicable": False},
            reflection=reflection_dict,
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
                "decision": "RETURN_REFLECTED",
                "reason": "Always-Reflection Policy",
                "selected_answer": final_answer,
                "selected_answer_type": "REFLECTED",
                "metrics": {
                    "confidence": 0.0,
                    "verification": 0.0,
                    "drift": 0.0,
                    "verification_threshold": 0.0,
                    "drift_threshold": 0.0,
                    "decision_latency_ms": 0.0,
                },
                "final_status": "Always Reflected",
            },
            final_answer=final_answer,
            metadata=metadata,
        )

        save_trace(response)
        logger.info("Always-Reflection RAG query completed | request_id=%s | latency_ms=%.3f", request_id, total_time_ms)
        return response
