import pytest

from backend.confidence.answer_consistency import AnswerConsistencyScorer
from backend.confidence.confidence_estimator import ConfidenceEstimator
from backend.confidence.evidence_agreement import EvidenceAgreementScorer
from backend.confidence.evidence_support import EvidenceSupportScorer
from backend.confidence.fact_coverage import FactCoverageScorer
from backend.confidence.retrieval_confidence import RetrievalConfidenceScorer
from backend.config import Settings
from backend.models.schemas import FactEvidence, FactStatus, PlanOutput, RequiredFact, RerankedChunk


def _reranked_chunks() -> list[RerankedChunk]:
    return [
        RerankedChunk(
            rerank_rank=1,
            chunk_id="chunk_python_creator",
            document_id="doc_python",
            title="python",
            text="Python was created by Guido van Rossum.",
            source="python.txt",
            chunk_index=0,
            reranker_raw_score=6.0,
            bm25_rank=1,
            bm25_score=8.0,
            dense_rank=1,
            dense_score=0.9,
            rrf_score=0.03,
        ),
        RerankedChunk(
            rerank_rank=2,
            chunk_id="chunk_python_year",
            document_id="doc_python",
            title="python",
            text="Python was first publicly released in 1991.",
            source="python.txt",
            chunk_index=1,
            reranker_raw_score=3.0,
            bm25_rank=2,
            bm25_score=7.2,
            dense_rank=2,
            dense_score=0.8,
            rrf_score=0.028,
        ),
    ]


def _plan() -> PlanOutput:
    return PlanOutput(
        question_intent="Identify creator and first release year.",
        required_facts=[
            RequiredFact(
                fact_id="fact_1",
                requirement="Creator of Python",
                status=FactStatus.FOUND,
                evidence=[
                    FactEvidence(
                        chunk_id="chunk_python_creator",
                        document_id="doc_python",
                        supported_fact="Python was created by Guido van Rossum.",
                    )
                ],
            ),
            RequiredFact(
                fact_id="fact_2",
                requirement="First release year of Python",
                status=FactStatus.FOUND,
                evidence=[
                    FactEvidence(
                        chunk_id="chunk_python_year",
                        document_id="doc_python",
                        supported_fact="Python was first publicly released in 1991.",
                    )
                ],
            ),
        ],
        missing_facts=[],
        conflicting_facts=[],
        answer_instruction="Use supported evidence only.",
    )


def test_retrieval_confidence_rewards_top_ranked_scores() -> None:
    result = RetrievalConfidenceScorer().score(_reranked_chunks())
    assert result.retrieval_confidence > 0.5
    assert result.top_document_normalized_score >= result.average_top_k_normalized_score


def test_fact_coverage_detects_partial_coverage() -> None:
    answer = "Python was created by Guido van Rossum."
    result = FactCoverageScorer().score(answer, _plan())
    assert result.fact_coverage == pytest.approx(0.5)
    assert "fact_1" in result.covered_facts
    assert "fact_2" in result.missing_facts


def test_evidence_agreement_detects_conflicting_years() -> None:
    conflict_plan = _plan()
    conflict_plan.required_facts[1].evidence.append(
        FactEvidence(
            chunk_id="chunk_python_year_conflict",
            document_id="doc_python",
            supported_fact="Python was first publicly released in 1995.",
        )
    )
    result = EvidenceAgreementScorer().score(conflict_plan)
    assert result.evidence_agreement < 1.0
    assert "fact_2" in result.conflicting_facts
    assert "chunk_python_year_conflict" in result.conflicting_chunk_ids


def test_answer_consistency_detects_year_contradiction() -> None:
    answer = "Python was created by Guido van Rossum and first released in 1995."
    result = AnswerConsistencyScorer().score(answer, _plan())
    assert result.answer_consistency < 1.0
    assert result.contradictions


def test_evidence_support_scores_claims_and_penalizes_contradiction() -> None:
    answer = "Python was created by Guido van Rossum and first released in 1995."
    result = EvidenceSupportScorer().score(answer, _plan(), _reranked_chunks())
    assert len(result.claim_scores) == 2
    year_claim = next(item for item in result.claim_scores if item.fact_id == "fact_2")
    assert year_claim.contradiction_penalty > 0
    assert result.evidence_support < 1.0


def test_confidence_estimator_returns_weighted_overall_score() -> None:
    settings = Settings(
        RETRIEVAL_WEIGHT=0.20,
        SUPPORT_WEIGHT=0.35,
        FACT_WEIGHT=0.20,
        CONSISTENCY_WEIGHT=0.15,
        AGREEMENT_WEIGHT=0.10,
    )
    answer = "Python was created by Guido van Rossum and first released in 1991."
    result = ConfidenceEstimator(settings).estimate(
        question="Who created Python and when was it first released?",
        plan=_plan(),
        reranked_chunks=_reranked_chunks(),
        initial_answer=answer,
    )
    assert result.overall_confidence > 0.0
    assert set(result.component_scores) == {
        "retrieval_confidence",
        "evidence_support",
        "fact_coverage",
        "answer_consistency",
        "evidence_agreement",
    }

