"""Unit tests for Phase 6 Dynamic Reflection Controller."""

from backend.confidence.confidence_gate import ConfidenceDecision, NextAction, RoutingResult
from backend.confidence.schemas import (
    AnswerConsistencyResult,
    ConfidenceResult,
    EvidenceAgreementResult,
    EvidenceSupportResult,
    FactCoverageResult,
    RetrievalConfidenceResult,
)
from backend.config import Settings
from backend.controller.controller_service import ControllerService
from backend.controller.decision_engine import DecisionEngine
from backend.controller.schemas import AnswerType, ControllerDecision
from backend.drift.schemas import SemanticDriftReport
from backend.models.schemas import FactEvidence, FactStatus, PlanOutput, RequiredFact
from backend.reflection.schemas import ReflectionReport
from backend.verification.schemas import VerificationReport, VerifiedClaimItem, ClaimStatus


def _make_confidence(score: float) -> ConfidenceResult:
    return ConfidenceResult(
        retrieval_confidence=score,
        evidence_support=score,
        fact_coverage=score,
        answer_consistency=score,
        evidence_agreement=score,
        overall_confidence=score,
        component_scores={},
        retrieval_details=RetrievalConfidenceResult(
            retrieval_confidence=score,
            top_document_raw_score=score,
            top_document_normalized_score=score,
            average_top_k_raw_score=score,
            average_top_k_normalized_score=score,
        ),
        support_details=EvidenceSupportResult(evidence_support=score, claim_scores=[]),
        coverage_details=FactCoverageResult(fact_coverage=score, covered_facts=[], missing_facts=[]),
        consistency_details=AnswerConsistencyResult(answer_consistency=score, contradictions=[]),
        agreement_details=EvidenceAgreementResult(
            evidence_agreement=score, conflicting_chunk_ids=[], conflicting_facts=[]
        ),
    )


def _make_routing(next_action: NextAction, threshold: float = 0.70, score: float = 0.4) -> RoutingResult:
    decision = ConfidenceDecision.HIGH_CONFIDENCE if next_action == NextAction.RETURN_INITIAL_ANSWER else ConfidenceDecision.LOW_CONFIDENCE
    return RoutingResult(
        decision=decision,
        next_action=next_action,
        overall_confidence=score,
        threshold=threshold,
        reason="Test routing",
        major_contributors=[],
    )


def _make_plan(missing_facts: list[str] | None = None, all_missing: bool = False) -> PlanOutput:
    facts = [
        RequiredFact(
            fact_id="f1",
            requirement="Creator of Python",
            status=FactStatus.FOUND,
            evidence=[FactEvidence(chunk_id="c1", document_id="d1", supported_fact="Guido")],
        )
    ]
    return PlanOutput(
        question_intent="Creator of Python",
        required_facts=facts if not all_missing else [],
        missing_facts=missing_facts or [],
        conflicting_facts=[],
        answer_instruction="State creator",
    )


def _make_reflection(candidate: str | None = None) -> ReflectionReport:
    return ReflectionReport(
        reflection_required=candidate is not None,
        reflection_reason="test",
        identified_problems=[],
        missing_facts=[],
        unsupported_claims=[],
        candidate_answer=candidate,
        reflection_summary="Test reflection",
    )


def _make_verification(score: float, claims: list[ClaimStatus] | None = None) -> VerificationReport:
    items = []
    if claims:
        for i, status in enumerate(claims):
            items.append(VerifiedClaimItem(
                claim_id=f"c{i}",
                claim_text=f"Claim {i}",
                status=status,
            ))
    return VerificationReport(
        verified_claims=items,
        supported_claims=[c.claim_text for c in items if c.status == ClaimStatus.SUPPORTED],
        unsupported_claims=[c.claim_text for c in items if c.status == ClaimStatus.UNSUPPORTED],
        contradicted_claims=[c.claim_text for c in items if c.status == ClaimStatus.CONTRADICTED],
        verification_score=score,
    )


def _make_drift(score: float, detected: bool) -> SemanticDriftReport:
    return SemanticDriftReport(
        drift_detected=detected,
        drift_score=score,
        drift_reason="Test drift reason",
        changed_intent=None,
        added_information=[],
        removed_information=[],
    )


# ============================================================
# Rule 1: High Confidence → Return Initial
# ============================================================
def test_high_confidence_returns_initial():
    engine = DecisionEngine(verification_threshold=0.80, drift_threshold=0.20)
    result = engine.evaluate(
        confidence=_make_confidence(0.92),
        routing=_make_routing(NextAction.RETURN_INITIAL_ANSWER, score=0.92),
        plan=_make_plan(),
        reflection=_make_reflection(None),
        verification=_make_verification(1.0),
        drift=_make_drift(0.0, False),
        initial_answer="Initial answer.",
        candidate_answer=None,
        latency_ms=1.0,
    )
    assert result.decision == ControllerDecision.RETURN_INITIAL
    assert result.selected_answer_type == AnswerType.INITIAL
    assert result.selected_answer == "Initial answer."
    assert result.final_status == "SUCCESS_INITIAL"


# ============================================================
# Rule 2: Reflection verified, low drift → Return Reflected
# ============================================================
def test_reflection_verified_low_drift_returns_reflected():
    engine = DecisionEngine(verification_threshold=0.80, drift_threshold=0.20)
    result = engine.evaluate(
        confidence=_make_confidence(0.45),
        routing=_make_routing(NextAction.REFLECTION_REQUIRED, score=0.45),
        plan=_make_plan(),
        reflection=_make_reflection("Improved candidate answer."),
        verification=_make_verification(0.90, [ClaimStatus.SUPPORTED]),
        drift=_make_drift(0.10, False),
        initial_answer="Initial answer.",
        candidate_answer="Improved candidate answer.",
        latency_ms=1.0,
    )
    assert result.decision == ControllerDecision.RETURN_REFLECTED
    assert result.selected_answer_type == AnswerType.REFLECTED
    assert result.selected_answer == "Improved candidate answer."
    assert result.final_status == "SUCCESS_REFLECTED"


# ============================================================
# Rule 3a: Reflection rejected – low verification
# ============================================================
def test_reflection_rejected_low_verification():
    engine = DecisionEngine(verification_threshold=0.80, drift_threshold=0.20)
    result = engine.evaluate(
        confidence=_make_confidence(0.45),
        routing=_make_routing(NextAction.REFLECTION_REQUIRED, score=0.45),
        plan=_make_plan(),
        reflection=_make_reflection("Problematic candidate."),
        verification=_make_verification(0.50, [ClaimStatus.UNSUPPORTED]),
        drift=_make_drift(0.10, False),
        initial_answer="Initial answer.",
        candidate_answer="Problematic candidate.",
        latency_ms=1.0,
    )
    assert result.decision == ControllerDecision.RETURN_INITIAL
    assert result.selected_answer_type == AnswerType.INITIAL
    assert result.selected_answer == "Initial answer."
    assert result.final_status == "REJECTED_REFLECTED_FALLBACK"
    assert "verification score" in result.reason


# ============================================================
# Rule 3b: Drift too high → Reject Reflection
# ============================================================
def test_reflection_rejected_high_drift():
    engine = DecisionEngine(verification_threshold=0.80, drift_threshold=0.20)
    result = engine.evaluate(
        confidence=_make_confidence(0.45),
        routing=_make_routing(NextAction.REFLECTION_REQUIRED, score=0.45),
        plan=_make_plan(),
        reflection=_make_reflection("Drifted candidate."),
        verification=_make_verification(0.90, [ClaimStatus.SUPPORTED]),
        drift=_make_drift(0.75, True),
        initial_answer="Initial answer.",
        candidate_answer="Drifted candidate.",
        latency_ms=1.0,
    )
    assert result.decision == ControllerDecision.RETURN_INITIAL
    assert result.selected_answer_type == AnswerType.INITIAL
    assert result.final_status == "REJECTED_REFLECTED_FALLBACK"
    assert "drift" in result.reason


# ============================================================
# Rule 4: Insufficient evidence
# ============================================================
def test_insufficient_information():
    plan = PlanOutput(
        question_intent="Creator",
        required_facts=[],
        missing_facts=["missing1"],
        conflicting_facts=[],
        answer_instruction="Use evidence",
    )
    engine = DecisionEngine(verification_threshold=0.80, drift_threshold=0.20)
    result = engine.evaluate(
        confidence=_make_confidence(0.45),
        routing=_make_routing(NextAction.REFLECTION_REQUIRED, score=0.45),
        plan=plan,
        reflection=_make_reflection(None),
        verification=_make_verification(0.0),
        drift=_make_drift(1.0, True),
        initial_answer="Initial.",
        candidate_answer=None,
        latency_ms=1.0,
    )
    assert result.decision == ControllerDecision.INSUFFICIENT_INFORMATION
    assert result.selected_answer_type == AnswerType.NONE
    assert result.final_status == "INSUFFICIENT_EVIDENCE"


# ============================================================
# Fallback: ControllerService exception safety
# ============================================================
def test_controller_service_safe_fallback():
    settings = Settings(LLM_PROVIDER="mock")
    service = ControllerService(settings)

    class _BrokenDrift:
        drift_detected = True
        drift_score = float("nan")
        drift_reason = "broken"
        changed_intent = None
        added_information = []
        removed_information = []

    result = service.process_decision(
        confidence=_make_confidence(0.92),
        routing=_make_routing(NextAction.RETURN_INITIAL_ANSWER, score=0.92),
        plan=_make_plan(),
        reflection=_make_reflection(None),
        verification=_make_verification(1.0),
        drift=_make_drift(0.0, False),
        initial_answer="Safe fallback answer.",
        candidate_answer=None,
    )
    assert result.selected_answer == "Safe fallback answer."
