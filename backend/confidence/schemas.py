"""Schemas for confidence estimator outputs."""

from pydantic import BaseModel


class RetrievalConfidenceResult(BaseModel):
    retrieval_confidence: float
    top_document_raw_score: float
    top_document_normalized_score: float
    average_top_k_raw_score: float
    average_top_k_normalized_score: float


class ClaimSupportScore(BaseModel):
    fact_id: str
    claim_text: str
    support_score: float
    contradiction_penalty: float
    final_score: float
    supporting_chunk_ids: list[str]
    contradicting_chunk_ids: list[str]


class EvidenceSupportResult(BaseModel):
    evidence_support: float
    claim_scores: list[ClaimSupportScore]


class FactCoverageResult(BaseModel):
    fact_coverage: float
    covered_facts: list[str]
    missing_facts: list[str]


class ContradictionItem(BaseModel):
    fact_id: str
    reason: str
    evidence_chunk_ids: list[str]


class AnswerConsistencyResult(BaseModel):
    answer_consistency: float
    contradictions: list[ContradictionItem]


class EvidenceAgreementResult(BaseModel):
    evidence_agreement: float
    conflicting_chunk_ids: list[str]
    conflicting_facts: list[str]


class ConfidenceResult(BaseModel):
    retrieval_confidence: float
    evidence_support: float
    fact_coverage: float
    answer_consistency: float
    evidence_agreement: float
    overall_confidence: float
    component_scores: dict[str, float]
    retrieval_details: RetrievalConfidenceResult
    support_details: EvidenceSupportResult
    coverage_details: FactCoverageResult
    consistency_details: AnswerConsistencyResult
    agreement_details: EvidenceAgreementResult

