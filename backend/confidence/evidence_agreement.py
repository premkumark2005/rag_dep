"""Evidence agreement scoring across retrieved chunks."""

from backend.confidence.schemas import EvidenceAgreementResult
from backend.confidence.utils import extract_creator_names, extract_years
from backend.models.schemas import PlanOutput


class EvidenceAgreementScorer:
    """Scores agreement between evidence chunks for planner-required facts."""

    def score(self, plan: PlanOutput) -> EvidenceAgreementResult:
        if not plan.required_facts:
            return EvidenceAgreementResult(evidence_agreement=1.0, conflicting_chunk_ids=[], conflicting_facts=[])

        conflicting_facts: list[str] = []
        conflicting_chunk_ids: set[str] = set()

        for fact in plan.required_facts:
            evidence_texts = [item.supported_fact for item in fact.evidence]
            if not evidence_texts:
                continue

            years = set()
            creators = set()
            for entry in fact.evidence:
                years.update(extract_years(entry.supported_fact))
                creators.update(extract_creator_names(entry.supported_fact))

            has_conflict = False
            requirement_lower = fact.requirement.lower()
            if ("when" in requirement_lower or "year" in requirement_lower or "date" in requirement_lower) and len(years) > 1:
                has_conflict = True
            if ("creator" in requirement_lower or "who" in requirement_lower or "inventor" in requirement_lower) and len(creators) > 1:
                has_conflict = True

            if has_conflict:
                conflicting_facts.append(fact.fact_id)
                conflicting_chunk_ids.update(item.chunk_id for item in fact.evidence)

        agreement = 1.0 - (len(conflicting_facts) / len(plan.required_facts))
        return EvidenceAgreementResult(
            evidence_agreement=round(max(0.0, agreement), 6),
            conflicting_chunk_ids=sorted(conflicting_chunk_ids),
            conflicting_facts=conflicting_facts,
        )

