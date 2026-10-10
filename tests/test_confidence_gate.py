"""Unit tests for ConfidenceGate decisions and routing."""

import pytest
from backend.confidence.confidence_gate import ConfidenceDecision, ConfidenceGate, NextAction
from backend.confidence.schemas import (
    AnswerConsistencyResult,
    ConfidenceResult,
    EvidenceAgreementResult,
    EvidenceSupportResult,
    FactCoverageResult,
    RetrievalConfidenceResult,
)


def make_dummy_confidence_result(overall_confidence: float) -> ConfidenceResult:
    return ConfidenceResult(
        retrieval_confidence=overall_confidence,
        evidence_support=overall_confidence,
        fact_coverage=overall_confidence,
        answer_consistency=overall_confidence,
        evidence_agreement=overall_confidence,
        overall_confidence=overall_confidence,
        component_scores={},
        retrieval_details=RetrievalConfidenceResult(
            retrieval_confidence=overall_confidence,
            top_document_raw_score=0.9,
            top_document_normalized_score=0.9,
            average_top_k_raw_score=0.8,
            average_top_k_normalized_score=0.8,
        ),
        support_details=EvidenceSupportResult(evidence_support=overall_confidence, claim_scores=[]),
        coverage_details=FactCoverageResult(
            fact_coverage=overall_confidence, covered_facts=[], missing_facts=[]
        ),
        consistency_details=AnswerConsistencyResult(
            answer_consistency=overall_confidence, contradictions=[]
        ),
        agreement_details=EvidenceAgreementResult(
            evidence_agreement=overall_confidence, conflicting_chunk_ids=[], conflicting_facts=[]
        ),
    )


def test_confidence_gate_high_confidence():
    """Case 1: Confidence 0.92, Threshold 0.70 -> HIGH_CONFIDENCE, RETURN_INITIAL_ANSWER."""
    gate = ConfidenceGate(threshold=0.70)
    conf = make_dummy_confidence_result(0.92)
    routing = gate.evaluate(conf)

    assert routing.decision == ConfidenceDecision.HIGH_CONFIDENCE
    assert routing.next_action == NextAction.RETURN_INITIAL_ANSWER
    assert routing.threshold == 0.70
    assert routing.overall_confidence == 0.92


def test_confidence_gate_low_confidence():
    """Case 2: Confidence 0.41, Threshold 0.70 -> LOW_CONFIDENCE, REFLECTION_REQUIRED."""
    gate = ConfidenceGate(threshold=0.70)
    conf = make_dummy_confidence_result(0.41)
    routing = gate.evaluate(conf)

    assert routing.decision == ConfidenceDecision.LOW_CONFIDENCE
    assert routing.next_action == NextAction.REFLECTION_REQUIRED
    assert routing.threshold == 0.70
    assert routing.overall_confidence == 0.41


def test_confidence_gate_exact_threshold():
    """Case 3: Confidence exactly equal to threshold (0.70) -> HIGH_CONFIDENCE."""
    gate = ConfidenceGate(threshold=0.70)
    conf = make_dummy_confidence_result(0.70)
    routing = gate.evaluate(conf)

    assert routing.decision == ConfidenceDecision.HIGH_CONFIDENCE
    assert routing.next_action == NextAction.RETURN_INITIAL_ANSWER
    assert routing.threshold == 0.70
    assert routing.overall_confidence == 0.70
