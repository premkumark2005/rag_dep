"""Answer consistency scoring against evidence facts."""

from backend.confidence.schemas import AnswerConsistencyResult, ContradictionItem
from backend.confidence.utils import extract_creator_names, extract_years
from backend.models.schemas import PlanOutput


class AnswerConsistencyScorer:
    """Detects contradictions between the answer and retrieved evidence."""

    def score(self, answer: str, plan: PlanOutput) -> AnswerConsistencyResult:
        if not plan.required_facts:
            return AnswerConsistencyResult(answer_consistency=1.0, contradictions=[])

        answer_years = extract_years(answer)
        answer_creators = extract_creator_names(answer)
        contradictions: list[ContradictionItem] = []
        checks = 0

        for fact in plan.required_facts:
            evidence_years = set()
            evidence_creators = set()
            for item in fact.evidence:
                evidence_years.update(extract_years(item.supported_fact))
                evidence_creators.update(extract_creator_names(item.supported_fact))

            requirement_lower = fact.requirement.lower()
            if "when" in requirement_lower or "year" in requirement_lower or "date" in requirement_lower:
                checks += 1
                if answer_years and evidence_years and answer_years.isdisjoint(evidence_years):
                    contradictions.append(
                        ContradictionItem(
                            fact_id=fact.fact_id,
                            reason="Answer year does not match evidence year.",
                            evidence_chunk_ids=[entry.chunk_id for entry in fact.evidence],
                        )
                    )
            if "creator" in requirement_lower or "who" in requirement_lower or "inventor" in requirement_lower:
                checks += 1
                if answer_creators and evidence_creators and answer_creators.isdisjoint(evidence_creators):
                    contradictions.append(
                        ContradictionItem(
                            fact_id=fact.fact_id,
                            reason="Answer entity does not match evidence entity.",
                            evidence_chunk_ids=[entry.chunk_id for entry in fact.evidence],
                        )
                    )

        if checks == 0:
            consistency = 1.0
        else:
            consistency = 1.0 - (len(contradictions) / checks)
        return AnswerConsistencyResult(answer_consistency=round(max(0.0, consistency), 6), contradictions=contradictions)

