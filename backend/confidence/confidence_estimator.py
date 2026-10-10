"""Confidence estimator orchestration for Phase 3A."""

from backend.confidence.answer_consistency import AnswerConsistencyScorer
from backend.confidence.evidence_agreement import EvidenceAgreementScorer
from backend.confidence.evidence_support import EvidenceSupportScorer
from backend.confidence.fact_coverage import FactCoverageScorer
from backend.confidence.retrieval_confidence import RetrievalConfidenceScorer
from backend.confidence.schemas import ConfidenceResult
from backend.config import Settings
from backend.models.schemas import PlanOutput, RerankedChunk


class ConfidenceEstimator:
    """Combines independent confidence signals into an overall confidence score."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.retrieval_scorer = RetrievalConfidenceScorer()
        self.support_scorer = EvidenceSupportScorer()
        self.coverage_scorer = FactCoverageScorer()
        self.consistency_scorer = AnswerConsistencyScorer()
        self.agreement_scorer = EvidenceAgreementScorer()

    def estimate(
        self,
        question: str,
        plan: PlanOutput,
        reranked_chunks: list[RerankedChunk],
        initial_answer: str,
    ) -> ConfidenceResult:
        _ = question
        retrieval = self.retrieval_scorer.score(reranked_chunks)
        support = self.support_scorer.score(initial_answer, plan, reranked_chunks)
        coverage = self.coverage_scorer.score(initial_answer, plan)
        consistency = self.consistency_scorer.score(initial_answer, plan)
        agreement = self.agreement_scorer.score(plan)

        weighted = {
            "retrieval_confidence": retrieval.retrieval_confidence * self.settings.retrieval_weight,
            "evidence_support": support.evidence_support * self.settings.support_weight,
            "fact_coverage": coverage.fact_coverage * self.settings.fact_weight,
            "answer_consistency": consistency.answer_consistency * self.settings.consistency_weight,
            "evidence_agreement": agreement.evidence_agreement * self.settings.agreement_weight,
        }
        weight_total = (
            self.settings.retrieval_weight
            + self.settings.support_weight
            + self.settings.fact_weight
            + self.settings.consistency_weight
            + self.settings.agreement_weight
        )
        overall = (sum(weighted.values()) / weight_total) if weight_total > 0 else 0.0

        return ConfidenceResult(
            retrieval_confidence=round(retrieval.retrieval_confidence, 6),
            evidence_support=round(support.evidence_support, 6),
            fact_coverage=round(coverage.fact_coverage, 6),
            answer_consistency=round(consistency.answer_consistency, 6),
            evidence_agreement=round(agreement.evidence_agreement, 6),
            overall_confidence=round(overall, 6),
            component_scores={key: round(value, 6) for key, value in weighted.items()},
            retrieval_details=retrieval,
            support_details=support,
            coverage_details=coverage,
            consistency_details=consistency,
            agreement_details=agreement,
        )

