"""Service orchestrating Phase 6 Dynamic Reflection Controller execution."""

import time
from backend.confidence.confidence_gate import RoutingResult
from backend.confidence.schemas import ConfidenceResult
from backend.config import Settings
from backend.controller.decision_engine import DecisionEngine
from backend.controller.schemas import AnswerType, ControllerDecision, ControllerMetrics, ControllerResult
from backend.drift.schemas import SemanticDriftReport
from backend.models.schemas import PlanOutput
from backend.reflection.schemas import ReflectionReport
from backend.utils.logger import get_logger
from backend.verification.schemas import VerificationReport

logger = get_logger(__name__)


class ControllerService:
"""Service wrapper for Dynamic Reflection Controller with safe fallback handling."""

def __init__(self, settings: Settings) -> None:
self.settings = settings
self.engine = DecisionEngine(
verification_threshold=settings.verification_threshold,
drift_threshold=settings.drift_threshold,
max_reflection_attempts=settings.max_reflection_attempts,
)

def process_decision(
self,
confidence: ConfidenceResult,
routing: RoutingResult,
plan: PlanOutput,
reflection: ReflectionReport,
verification: VerificationReport,
drift: SemanticDriftReport,
initial_answer: str,
candidate_answer: str | None,
) -> ControllerResult:
start_time = time.perf_counter()
logger.info("Controller Started | threshold_verification=%.2f | threshold_drift=%.2f", self.settings.verification_threshold, self.settings.drift_threshold)

try:
latency_ms = (time.perf_counter() - start_time) * 1000
result = self.engine.evaluate(
confidence=confidence,
routing=routing,
plan=plan,
reflection=reflection,
verification=verification,
drift=drift,
initial_answer=initial_answer,
candidate_answer=candidate_answer,
latency_ms=latency_ms,
)
except Exception as exc:
logger.error("Controller decision failed unexpectedly; using safe initial answer fallback: %s", exc)
latency_ms = (time.perf_counter() - start_time) * 1000
result = ControllerResult(
decision=ControllerDecision.RETURN_INITIAL,
reason=f"Safe fallback triggered due to exception: {exc}",
selected_answer=initial_answer,
selected_answer_type=AnswerType.INITIAL,
metrics=ControllerMetrics(
confidence=confidence.overall_confidence,
verification=verification.verification_score,
drift=drift.drift_score,
verification_threshold=self.settings.verification_threshold,
drift_threshold=self.settings.drift_threshold,
decision_latency_ms=round(latency_ms, 3),
),
reflection_retry=False,
retrieval_retry=False,
final_status="SAFE_FALLBACK",
)

logger.info(
"Controller Completed | decision=%s | selected_type=%s | verification_score=%.4f | drift_score=%.4f | latency_ms=%.3f | reason=%s",
result.decision.value,
result.selected_answer_type.value,
result.metrics.verification,
result.metrics.drift,
result.metrics.decision_latency_ms,
result.reason,
)

return result
