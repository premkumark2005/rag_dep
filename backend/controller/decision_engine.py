"""Decision Engine evaluating confidence, verification, drift, and planner output."""

from backend.confidence.confidence_gate import NextAction, RoutingResult
from backend.confidence.schemas import ConfidenceResult
from backend.controller.schemas import AnswerType, ControllerDecision, ControllerMetrics, ControllerResult
from backend.drift.schemas import SemanticDriftReport
from backend.models.schemas import PlanOutput
from backend.reflection.schemas import ReflectionReport
from backend.verification.schemas import VerificationReport


class DecisionEngine:
    """Core decision logic for Phase 6 Dynamic Reflection Controller."""

    def __init__(
        self,
        verification_threshold: float = 0.80,
        drift_threshold: float = 0.20,
        max_reflection_attempts: int = 1,
    ) -> None:
        self.verification_threshold = verification_threshold
        self.drift_threshold = drift_threshold
        self.max_reflection_attempts = max_reflection_attempts

    def evaluate(
        self,
        confidence: ConfidenceResult,
        routing: RoutingResult,
        plan: PlanOutput,
        reflection: ReflectionReport,
        verification: VerificationReport,
        drift: SemanticDriftReport,
        initial_answer: str,
        candidate_answer: str | None,
        latency_ms: float,
    ) -> ControllerResult:
        metrics = ControllerMetrics(
            confidence=confidence.overall_confidence,
            verification=verification.verification_score,
            drift=drift.drift_score,
            verification_threshold=self.verification_threshold,
            drift_threshold=self.drift_threshold,
            decision_latency_ms=round(latency_ms, 3),
        )

        # Rule 4: Critical Missing Evidence in Planner
        # Triggers when missing_facts exist AND there is no (or zero) required facts coverage
        if plan.missing_facts and (len(plan.required_facts) == 0 or len(plan.missing_facts) >= len(plan.required_facts)):
            return ControllerResult(
                decision=ControllerDecision.INSUFFICIENT_INFORMATION,
                reason="Insufficient information: evidence lacks all required facts specified by planning module.",
                selected_answer="I am sorry, but the provided documents do not contain sufficient evidence to answer your question.",
                selected_answer_type=AnswerType.NONE,
                metrics=metrics,
                reflection_retry=False,
                retrieval_retry=True,
                final_status="INSUFFICIENT_EVIDENCE",
            )

        # Rule 1: High Confidence Gate Pass
        if routing.next_action == NextAction.RETURN_INITIAL_ANSWER:
            return ControllerResult(
                decision=ControllerDecision.RETURN_INITIAL,
                reason=f"Confidence gate passed (overall_confidence {confidence.overall_confidence:.2f} >= threshold {routing.threshold:.2f}). Returning initial answer.",
                selected_answer=initial_answer,
                selected_answer_type=AnswerType.INITIAL,
                metrics=metrics,
                reflection_retry=False,
                retrieval_retry=False,
                final_status="SUCCESS_INITIAL",
            )

        # Reflection was performed
        cand = candidate_answer or initial_answer
        v_score = verification.verification_score
        d_score = drift.drift_score

        # Rule 2: Reflection Verified & Low Drift
        if v_score >= self.verification_threshold and d_score <= self.drift_threshold:
            return ControllerResult(
                decision=ControllerDecision.RETURN_REFLECTED,
                reason=(
                    f"Reflection accepted: verification score ({v_score:.2f}) >= threshold ({self.verification_threshold:.2f}) "
                    f"and semantic drift score ({d_score:.2f}) <= threshold ({self.drift_threshold:.2f})."
                ),
                selected_answer=cand,
                selected_answer_type=AnswerType.REFLECTED,
                metrics=metrics,
                reflection_retry=False,
                retrieval_retry=False,
                final_status="SUCCESS_REFLECTED",
            )

        # Rule 3: Reflection Rejected due to low verification or high drift
        reasons = []
        if v_score < self.verification_threshold:
            reasons.append(f"verification score ({v_score:.2f}) < threshold ({self.verification_threshold:.2f})")
        if d_score > self.drift_threshold:
            reasons.append(f"semantic drift score ({d_score:.2f}) > threshold ({self.drift_threshold:.2f})")

        rejection_reason = "Reflection rejected because " + " and ".join(reasons) + ". Falling back to initial answer."

        return ControllerResult(
            decision=ControllerDecision.RETURN_INITIAL,
            reason=rejection_reason,
            selected_answer=initial_answer,
            selected_answer_type=AnswerType.INITIAL,
            metrics=metrics,
            reflection_retry=False,
            retrieval_retry=False,
            final_status="REJECTED_REFLECTED_FALLBACK",
        )
