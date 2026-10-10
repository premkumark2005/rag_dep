"""Fact coverage confidence from planner-required facts."""

from backend.confidence.schemas import FactCoverageResult
from backend.confidence.utils import tokenize
from backend.models.schemas import PlanOutput


class FactCoverageScorer:
    """Scores how many required planner facts are present in the generated answer."""

    def score(self, answer: str, plan: PlanOutput) -> FactCoverageResult:
        if not plan.required_facts:
            return FactCoverageResult(fact_coverage=1.0, covered_facts=[], missing_facts=[])

        answer_terms = tokenize(answer)
        covered: list[str] = []
        missing: list[str] = []

        for fact in plan.required_facts:
            evidence_text = " ".join(item.supported_fact for item in fact.evidence)
            reference_terms = tokenize(f"{fact.requirement} {evidence_text}")
            if not reference_terms:
                missing.append(fact.fact_id)
                continue
            overlap = len(answer_terms & reference_terms) / len(reference_terms)
            if overlap >= 0.20:
                covered.append(fact.fact_id)
            else:
                missing.append(fact.fact_id)

        coverage = len(covered) / len(plan.required_facts)
        return FactCoverageResult(
            fact_coverage=round(coverage, 6),
            covered_facts=covered,
            missing_facts=missing,
        )

