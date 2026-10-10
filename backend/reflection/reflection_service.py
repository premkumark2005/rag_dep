"""Service wrapper for Ultra-Lightweight Reflection orchestration."""

import time
from backend.confidence.confidence_gate import NextAction, RoutingResult
from backend.confidence.schemas import ConfidenceResult
from backend.generation.llm_client import LLMClient
from backend.models.schemas import PlanOutput, RerankedChunk
from backend.reflection.reflection_agent import ReflectionAgent
from backend.reflection.schemas import ReflectionReport
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ReflectionService:
    """Orchestrates single-pass reflection if next_action is REFLECTION_REQUIRED."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.agent = ReflectionAgent(llm_client)

    def reflect_if_needed(
        self,
        question: str,
        plan: PlanOutput,
        evidence: list[RerankedChunk],
        initial_answer: str,
        confidence: ConfidenceResult,
        routing: RoutingResult,
    ) -> tuple[ReflectionReport, float, str | None]:
        """Evaluates routing next_action and executes reflection exactly once if REFLECTION_REQUIRED.
        
        Returns:
            (ReflectionReport, reflection_latency_ms, reflection_prompt)
        """
        if routing.next_action != NextAction.REFLECTION_REQUIRED:
            logger.info("Reflection skipped (NextAction is %s)", routing.next_action.value)
            return (
                ReflectionReport(
                    reflection_required=False,
                    reflection_reason="Confidence gate approved initial answer. Reflection not required.",
                    identified_problems=[],
                    missing_facts=[],
                    unsupported_claims=[],
                    candidate_answer=None,
                    reflection_summary="Skipped reflection since overall confidence met threshold.",
                ),
                0.0,
                None,
            )

        logger.info("Reflection Started | reason=%s", routing.reason)
        start_time = time.perf_counter()

        report, prompt = self.agent.reflect(
            question=question,
            plan=plan,
            evidence=evidence,
            initial_answer=initial_answer,
            confidence=confidence,
            reason=routing.reason,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "Reflection Finished | latency_ms=%.3f | problem_count=%d | missing_facts_count=%d | unsupported_claims_count=%d",
            latency_ms,
            len(report.identified_problems),
            len(report.missing_facts),
            len(report.unsupported_claims),
        )

        return report, round(latency_ms, 3), prompt
