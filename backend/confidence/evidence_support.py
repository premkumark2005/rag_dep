"""Claim-level evidence support scoring for generated answers."""

from __future__ import annotations

import re

from backend.confidence.schemas import ClaimSupportScore, EvidenceSupportResult
from backend.confidence.utils import extract_creator_names, extract_years, jaccard_similarity
from backend.models.schemas import PlanOutput, RerankedChunk


class EvidenceSupportScorer:
    """Scores how strongly answer claims are supported by retrieved evidence."""

    def score(self, answer: str, plan: PlanOutput, reranked_chunks: list[RerankedChunk]) -> EvidenceSupportResult:
        if not plan.required_facts:
            return EvidenceSupportResult(evidence_support=0.0, claim_scores=[])

        answer_sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", answer) if part.strip()]
        claim_scores: list[ClaimSupportScore] = []

        for fact in plan.required_facts:
            claim_text = self._best_claim_sentence(fact.requirement, answer_sentences, answer)
            support_values = []
            supporting_ids: list[str] = []
            contradiction_ids: list[str] = []
            contradiction_penalty = 0.0

            for evidence in fact.evidence:
                similarity = jaccard_similarity(claim_text, evidence.supported_fact)
                support_values.append(similarity)
                if similarity >= 0.20:
                    supporting_ids.append(evidence.chunk_id)

            support_score = max(support_values) if support_values else 0.0

            evidence_years = set()
            evidence_creators = set()
            for evidence in fact.evidence:
                evidence_years.update(extract_years(evidence.supported_fact))
                evidence_creators.update(extract_creator_names(evidence.supported_fact))

            answer_years = extract_years(claim_text)
            answer_creators = extract_creator_names(claim_text)
            requirement_lower = fact.requirement.lower()

            if ("when" in requirement_lower or "year" in requirement_lower or "date" in requirement_lower) and answer_years and evidence_years:
                if answer_years.isdisjoint(evidence_years):
                    contradiction_penalty = max(contradiction_penalty, 0.5)
                    contradiction_ids = [entry.chunk_id for entry in fact.evidence]

            if ("creator" in requirement_lower or "who" in requirement_lower or "inventor" in requirement_lower) and answer_creators and evidence_creators:
                if answer_creators.isdisjoint(evidence_creators):
                    contradiction_penalty = max(contradiction_penalty, 0.5)
                    contradiction_ids = [entry.chunk_id for entry in fact.evidence]

            final_score = max(0.0, support_score - contradiction_penalty)
            claim_scores.append(
                ClaimSupportScore(
                    fact_id=fact.fact_id,
                    claim_text=claim_text,
                    support_score=round(support_score, 6),
                    contradiction_penalty=round(contradiction_penalty, 6),
                    final_score=round(final_score, 6),
                    supporting_chunk_ids=sorted(set(supporting_ids)),
                    contradicting_chunk_ids=sorted(set(contradiction_ids)),
                )
            )

        overall = sum(item.final_score for item in claim_scores) / len(claim_scores) if claim_scores else 0.0
        return EvidenceSupportResult(evidence_support=round(overall, 6), claim_scores=claim_scores)

    def _best_claim_sentence(self, requirement: str, sentences: list[str], fallback: str) -> str:
        if not sentences:
            return fallback
        best_sentence = sentences[0]
        best_score = -1.0
        for sentence in sentences:
            score = jaccard_similarity(requirement, sentence)
            if score > best_score:
                best_score = score
                best_sentence = sentence
        return best_sentence

