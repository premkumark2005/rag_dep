"""Confidence Gate module for gating decisions based on multi-signal confidence."""

from enum import Enum
from pydantic import BaseModel
from backend.confidence.schemas import ConfidenceResult


class ConfidenceDecision(str, Enum):
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"


class NextAction(str, Enum):
    RETURN_INITIAL_ANSWER = "RETURN_INITIAL_ANSWER"
    REFLECTION_REQUIRED = "REFLECTION_REQUIRED"


class RoutingResult(BaseModel):
    decision: ConfidenceDecision
    next_action: NextAction
    overall_confidence: float
    threshold: float
    reason: str
    major_contributors: list[str]


class ConfidenceGate:
    """Evaluates confidence score against threshold to decide downstream routing."""

    def __init__(self, threshold: float = 0.70) -> None:
        self.threshold = threshold

    def evaluate(self, confidence: ConfidenceResult) -> RoutingResult:
        overall = confidence.overall_confidence
        decision = ConfidenceDecision.HIGH_CONFIDENCE if overall >= self.threshold else ConfidenceDecision.LOW_CONFIDENCE
        next_action = NextAction.RETURN_INITIAL_ANSWER if decision == ConfidenceDecision.HIGH_CONFIDENCE else NextAction.REFLECTION_REQUIRED

        # Identify major negative or positive contributors
        component_scores = {
            "retrieval_confidence": confidence.retrieval_confidence,
            "evidence_support": confidence.evidence_support,
            "fact_coverage": confidence.fact_coverage,
            "answer_consistency": confidence.answer_consistency,
            "evidence_agreement": confidence.evidence_agreement,
        }

        # Sort component scores by score ascending to identify lowest contributors for low confidence, or all for high confidence
        sorted_components = sorted(component_scores.items(), key=lambda item: item[1])

        if decision == ConfidenceDecision.HIGH_CONFIDENCE:
            reason = f"Overall confidence ({overall:.2f}) meets or exceeds configured threshold ({self.threshold:.2f})."
            major_contributors = [comp[0] for comp in sorted_components if comp[1] >= self.threshold]
            if not major_contributors:
                major_contributors = [sorted_components[-1][0]]
        else:
            # Low confidence: identify key weak areas (e.g. below threshold or lowest 2)
            weak_components = [comp[0] for comp in sorted_components if comp[1] < self.threshold]
            if not weak_components:
                weak_components = [sorted_components[0][0]]
            
            readable_weak = [c.replace("_", " ") for c in weak_components[:2]]
            reason = f"Overall confidence ({overall:.2f}) is below threshold ({self.threshold:.2f}) due to low " + " and ".join(readable_weak) + "."
            major_contributors = weak_components

        return RoutingResult(
            decision=decision,
            next_action=next_action,
            overall_confidence=round(overall, 4),
            threshold=round(self.threshold, 4),
            reason=reason,
            major_contributors=major_contributors,
        )
