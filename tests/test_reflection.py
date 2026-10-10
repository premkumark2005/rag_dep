"""Unit tests for Phase 4 Ultra-Lightweight Reflection Module."""

import pytest
from backend.confidence.confidence_gate import ConfidenceDecision, RoutingResult, NextAction
from backend.confidence.schemas import (
    AnswerConsistencyResult,
    ConfidenceResult,
    EvidenceAgreementResult,
    EvidenceSupportResult,
    FactCoverageResult,
    RetrievalConfidenceResult,
)
from backend.models.schemas import FactEvidence, FactStatus, PlanOutput, RequiredFact, RerankedChunk
from backend.reflection.reflection_agent import ReflectionAgent
from backend.reflection.reflection_service import ReflectionService
from backend.reflection.schemas import ReflectionProblemType, ReflectionReport


class DummyLLMClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.call_count = 0

    def generate(self, prompt: str) -> str:
        self.call_count += 1
        return self.response_text


def _make_dummy_context():
    plan = PlanOutput(
        question_intent="Test intent",
        required_facts=[
            RequiredFact(
                fact_id="fact_1",
                requirement="Creator",
                status=FactStatus.FOUND,
                evidence=[FactEvidence(chunk_id="c1", document_id="d1", supported_fact="Python created by Guido.")],
            )
        ],
        missing_facts=["Release year"],
        conflicting_facts=[],
        answer_instruction="Test instruction",
    )
    evidence = [
        RerankedChunk(
            rerank_rank=1,
            chunk_id="c1",
            document_id="d1",
            title="t1",
            text="Python was created by Guido.",
            source="s1",
            chunk_index=0,
            reranker_raw_score=0.9,
            rrf_score=0.1,
        )
    ]
    confidence = ConfidenceResult(
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
        coverage_details=FactCoverageResult(fact_coverage=0.5, covered_facts=[], missing_facts=["Release year"]),
        consistency_details=AnswerConsistencyResult(answer_consistency=0.5, contradictions=[]),
        agreement_details=EvidenceAgreementResult(
            evidence_agreement=0.5, conflicting_chunk_ids=[], conflicting_facts=[]
        ),
    )
    return plan, evidence, confidence


def test_reflection_does_not_execute_for_high_confidence():
    client = DummyLLMClient("{}")
    service = ReflectionService(client)
    plan, evidence, confidence = _make_dummy_context()

    routing = RoutingResult(
        decision=ConfidenceDecision.HIGH_CONFIDENCE,
        next_action=NextAction.RETURN_INITIAL_ANSWER,
        overall_confidence=0.95,
        threshold=0.70,
        reason="High confidence",
        major_contributors=["evidence_support"],
    )

    report, latency_ms, prompt = service.reflect_if_needed(
        question="Who created Python?",
        plan=plan,
        evidence=evidence,
        initial_answer="Guido van Rossum created Python.",
        confidence=confidence,
        routing=routing,
    )

    assert report.reflection_required is False
    assert report.candidate_answer is None
    assert client.call_count == 0
    assert latency_ms == 0.0


def test_reflection_executes_once_for_low_confidence():
    json_response = """
    {
      "reflection_summary": "Added missing facts.",
      "identified_problems": [
        {"type": "MISSING_FACT", "description": "Release year missing"}
      ],
      "missing_facts": ["Release year"],
      "unsupported_claims": [],
      "candidate_answer": "Python was created by Guido van Rossum in 1991."
    }
    """
    client = DummyLLMClient(json_response)
    service = ReflectionService(client)
    plan, evidence, confidence = _make_dummy_context()

    routing = RoutingResult(
        decision=ConfidenceDecision.LOW_CONFIDENCE,
        next_action=NextAction.REFLECTION_REQUIRED,
        overall_confidence=0.45,
        threshold=0.70,
        reason="Low confidence due to missing facts",
        major_contributors=["fact_coverage"],
    )

    report, latency_ms, prompt = service.reflect_if_needed(
        question="Who created Python?",
        plan=plan,
        evidence=evidence,
        initial_answer="Guido van Rossum created Python.",
        confidence=confidence,
        routing=routing,
    )

    assert report.reflection_required is True
    assert client.call_count == 1
    assert report.candidate_answer == "Python was created by Guido van Rossum in 1991."
    assert len(report.identified_problems) == 1
    assert report.identified_problems[0].type == ReflectionProblemType.MISSING_FACT


def test_reflection_malformed_json_recovery():
    malformed_llm = DummyLLMClient("Here is your output: {\"reflection_summary\": \"Recovered\", \"identified_problems\": [], \"missing_facts\": [], \"unsupported_claims\": [], \"candidate_answer\": \"Fixed answer\"} end of text")
    agent = ReflectionAgent(malformed_llm)
    plan, evidence, confidence = _make_dummy_context()

    report, _ = agent.reflect(
        question="Q",
        plan=plan,
        evidence=evidence,
        initial_answer="Initial",
        confidence=confidence,
        reason="Low confidence",
    )

    assert report.reflection_summary == "Recovered"
    assert report.candidate_answer == "Fixed answer"
