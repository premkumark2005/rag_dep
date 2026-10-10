"""Phase 2 pipeline orchestration: hybrid retrieval, reranking, and planning."""

import time
import uuid

from backend.confidence.confidence_estimator import ConfidenceEstimator
from backend.confidence.confidence_gate import ConfidenceGate
from backend.config import Settings
from backend.controller.controller_service import ControllerService
from backend.drift.semantic_drift_detector import SemanticDriftDetector
from backend.generation.generator import PlannedAnswerGenerator
from backend.generation.llm_client import create_llm_client
from backend.models.schemas import Phase2Metadata, Phase2QueryResponse, Phase2RetrievalTrace
from backend.planning.planner import PlanningModule
from backend.reflection.reflection_service import ReflectionService
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.reranker import CrossEncoderReranker
from backend.services.trace_store import save_trace
from backend.utils.logger import get_logger
from backend.verification.verification_service import VerificationService

logger = get_logger(__name__)



class Phase2PipelineService:
    """Runs the Phase 2-6 pipeline with full trace and controller decision."""

    def __init__(
        self,
        settings: Settings,
        dense_retriever: DenseRetriever,
        bm25_retriever: BM25Retriever,
        hybrid_retriever: HybridRetriever,
        reranker: CrossEncoderReranker,
        planner: PlanningModule,
        planned_generator: PlannedAnswerGenerator,
        confidence_estimator: ConfidenceEstimator,
        reflection_service: ReflectionService | None = None,
        verification_service: VerificationService | None = None,
        drift_detector: SemanticDriftDetector | None = None,
        controller_service: ControllerService | None = None,
    ) -> None:
        self.settings = settings
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker
        self.planner = planner
        self.planned_generator = planned_generator
        self.confidence_estimator = confidence_estimator
        self.confidence_gate = ConfidenceGate(threshold=self.settings.confidence_threshold)
        self.reflection_service = reflection_service or ReflectionService(create_llm_client(self.settings))
        self.verification_service = verification_service or VerificationService()
        self.drift_detector = drift_detector or SemanticDriftDetector()
        self.controller_service = controller_service or ControllerService(self.settings)

    def query(
        self,
        question: str,
        final_context_k: int | None = None,
        system: str = "proposed_rag",
    ) -> Phase2QueryResponse:
        system = (system or "proposed_rag").strip().lower()

        if system == "traditional_rag":
            from backend.services.traditional_rag_service import TraditionalRAGService
            traditional_service = TraditionalRAGService(
                settings=self.settings,
                dense_retriever=self.dense_retriever,
                llm_client=create_llm_client(self.settings),
            )
            return traditional_service.query(question, final_context_k)

        if system == "always_reflection":
            from backend.services.always_reflection_service import AlwaysReflectionService
            always_reflection_service = AlwaysReflectionService(
                settings=self.settings,
                dense_retriever=self.dense_retriever,
                llm_client=create_llm_client(self.settings),
            )
            return always_reflection_service.query(question, final_context_k)

        rerank_top_k = final_context_k or self.settings.rerank_top_k
        if rerank_top_k <= 0:
            raise ValueError("final_context_k must be greater than 0.")

        total_start = time.perf_counter()

        bm25_start = time.perf_counter()
        bm25_results = self.bm25_retriever.retrieve(question, self.settings.bm25_top_k)
        bm25_time_ms = (time.perf_counter() - bm25_start) * 1000

        dense_start = time.perf_counter()
        dense_results = self.dense_retriever.retrieve(question, self.settings.dense_top_k)
        dense_time_ms = (time.perf_counter() - dense_start) * 1000

        fusion_start = time.perf_counter()
        hybrid_results = self.hybrid_retriever.fuse(
            bm25_results=bm25_results,
            dense_results=dense_results,
            top_k=max(self.settings.bm25_top_k, self.settings.dense_top_k),
        )
        fusion_time_ms = (time.perf_counter() - fusion_start) * 1000

        rerank_start = time.perf_counter()
        reranked_results = self.reranker.rerank(
            query=question,
            candidates=hybrid_results,
            top_k=rerank_top_k,
        )
        reranking_time_ms = (time.perf_counter() - rerank_start) * 1000

        planning_start = time.perf_counter()
        plan = self.planner.create_plan(question, reranked_results)
        planning_time_ms = (time.perf_counter() - planning_start) * 1000

        generation_start = time.perf_counter()
        initial_answer = self.planned_generator.generate(question, plan, reranked_results)
        generation_time_ms = (time.perf_counter() - generation_start) * 1000

        confidence_start = time.perf_counter()
        confidence = self.confidence_estimator.estimate(
            question=question,
            plan=plan,
            reranked_chunks=reranked_results,
            initial_answer=initial_answer,
        )
        confidence_time_ms = (time.perf_counter() - confidence_start) * 1000

        routing = self.confidence_gate.evaluate(confidence)

        reflection_report, reflection_time_ms, _ = self.reflection_service.reflect_if_needed(
            question=question,
            plan=plan,
            evidence=reranked_results,
            initial_answer=initial_answer,
            confidence=confidence,
            routing=routing,
        )

        verification_report, verification_time_ms = self.verification_service.verify(
            candidate_answer=reflection_report.candidate_answer,
            initial_answer=initial_answer,
            evidence=reranked_results,
            plan=plan,
        )

        drift_report, drift_time_ms = self.drift_detector.detect_drift(
            question=question,
            plan=plan,
            candidate_answer=reflection_report.candidate_answer,
            initial_answer=initial_answer,
        )

        controller_start = time.perf_counter()
        controller_result = self.controller_service.process_decision(
            confidence=confidence,
            routing=routing,
            plan=plan,
            reflection=reflection_report,
            verification=verification_report,
            drift=drift_report,
            initial_answer=initial_answer,
            candidate_answer=reflection_report.candidate_answer,
        )
        controller_time_ms = (time.perf_counter() - controller_start) * 1000

        total_time_ms = (time.perf_counter() - total_start) * 1000
        metadata = Phase2Metadata(
            bm25_time_ms=round(bm25_time_ms, 3),
            dense_time_ms=round(dense_time_ms, 3),
            fusion_time_ms=round(fusion_time_ms, 3),
            reranking_time_ms=round(reranking_time_ms, 3),
            planning_time_ms=round(planning_time_ms, 3),
            generation_time_ms=round(generation_time_ms, 3),
            confidence_time_ms=round(confidence_time_ms, 3),
            reflection_time_ms=round(reflection_time_ms, 3),
            verification_time_ms=round(verification_time_ms, 3),
            drift_time_ms=round(drift_time_ms, 3),
            controller_time_ms=round(controller_time_ms, 3),
            total_time_ms=round(total_time_ms, 3),
            bm25_top_k=self.settings.bm25_top_k,
            dense_top_k=self.settings.dense_top_k,
            rerank_top_k=rerank_top_k,
        )
        retrieval_trace = Phase2RetrievalTrace(
            bm25_results=bm25_results,
            dense_results=dense_results,
            hybrid_results=hybrid_results,
            reranked_results=reranked_results,
        )

        # Dynamic LLM Call Count for Proposed RAG: Planner (1) + Generator (1) + Reflection (1 if executed else 0)
        llm_calls_count = 3 if reflection_report.reflection_required else 2

        logger.info(
            "Phase2 query completed | provider=%s | model=%s | confidence=%.4f | "
            "decision=%s | answer_type=%s | final_status=%s | total_ms=%.3f",
            self.settings.llm_provider,
            self.settings.llm_model,
            confidence.overall_confidence,
            controller_result.decision.value,
            controller_result.selected_answer_type.value,
            controller_result.final_status,
            total_time_ms,
        )

        request_id = f"req_{uuid.uuid4().hex[:12]}"
        response = Phase2QueryResponse(
            request_id=request_id,
            question_id=request_id,
            system="proposed_rag",
            llm_calls=llm_calls_count,
            latency_ms=round(total_time_ms, 3),
            question=question,
            retrieval=retrieval_trace,
            plan=plan,
            initial_answer=initial_answer,
            candidate_answer=reflection_report.candidate_answer,
            confidence=confidence,
            routing=routing,
            reflection=reflection_report,
            verification=verification_report,
            semantic_drift=drift_report,
            controller=controller_result,
            final_answer=controller_result.selected_answer,
            metadata=metadata,
        )
        save_trace(response)
        return response







