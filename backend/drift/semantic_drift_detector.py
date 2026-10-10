"""Semantic Drift Detector evaluating candidate answer against original question and planner intent.

Drift detection policy:
    Lexical and structural rewording is NOT drift.
    Drift is only declared when the candidate answer fundamentally changes
    the question intent — i.e. it answers a different question.

    A required fact is considered "missing" from the candidate only when there
    is ZERO bidirectional token overlap between the requirement and the candidate.
    Bidirectional overlap means we check both directions:
        - Requirement tokens covered by candidate  (forward coverage)
        - Candidate tokens that cover requirement  (reverse coverage)
    The requirement is treated as present when EITHER direction reaches >= 0.4.

    Drift is declared ONLY when ALL of the following hold:
        1. The missing-fact ratio is >= 0.5   (majority of facts missing)
        2. At least 2 facts are actually missing (single-token facts are noisy)
        3. The question-level token overlap between candidate and question is < 0.3
           (the candidate talks about a completely different topic)
"""

import re
import time
from backend.drift.schemas import SemanticDriftReport
from backend.models.schemas import PlanOutput
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Minimum bidirectional overlap to consider a required fact "covered" in the candidate.
_COVERAGE_THRESHOLD = 0.4

# Minimum missing-fact ratio to consider drift at all.
_MISSING_RATIO_THRESHOLD = 0.5

# Minimum number of actually-missing facts (guards against single-token noise).
_MIN_MISSING_COUNT = 2

# Minimum question-level overlap; if the candidate still mentions most question
# terms we do NOT declare drift even if plan facts seem missing.
_QUESTION_OVERLAP_FLOOR = 0.3


class SemanticDriftDetector:
    """Detects intent shift, added facts, and missing key intent requirements in reflected candidate answers."""

    def detect_drift(
        self,
        question: str,
        plan: PlanOutput,
        candidate_answer: str | None,
        initial_answer: str,
    ) -> tuple[SemanticDriftReport, float]:
        start_time = time.perf_counter()
        target_text = candidate_answer or initial_answer

        q_terms = self._tokenize(question)
        target_terms = self._tokenize(target_text)
        initial_terms = self._tokenize(initial_answer)

        # ── Step 1: check which required facts are MISSING from the candidate ──
        required_reqs = [r.requirement for r in plan.required_facts]
        missing_reqs: list[str] = []

        for req in required_reqs:
            req_terms = self._tokenize(req)
            if not req_terms:
                continue
            # Skip single-token requirements — too noisy to be meaningful on their own.
            if len(req_terms) == 1:
                continue
            if not self._is_covered(req_terms, target_terms):
                missing_reqs.append(req)

        # ── Step 2: identify genuinely added information ───────────────────────
        added_terms = target_terms - (q_terms | initial_terms)
        added_information = [term for term in added_terms if len(term) > 3]

        # ── Step 3: compute drift score ────────────────────────────────────────
        total_reqs = len([r for r in required_reqs if len(self._tokenize(r)) >= 2])
        if total_reqs > 0:
            missing_ratio = len(missing_reqs) / total_reqs
            drift_score = round(missing_ratio, 4)
        else:
            # No multi-token requirements — fall back to question-level overlap.
            overlap = len(q_terms & target_terms) / len(q_terms) if q_terms else 1.0
            drift_score = round(max(0.0, 1.0 - overlap), 4)
            missing_ratio = drift_score

        # ── Step 4: question-level safety net ─────────────────────────────────
        # Even if plan facts appear missing, if the candidate still addresses the
        # same question topic we do NOT call it drift.
        question_overlap = len(q_terms & target_terms) / len(q_terms) if q_terms else 1.0

        # ── Step 5: final drift decision ──────────────────────────────────────
        # When ALL multi-token requirements are missing (ratio == 1.0) that is
        # unambiguous drift — the candidate addresses none of the required facts.
        # The question-overlap floor is bypassed in this case to avoid suppressing
        # obvious drift just because a common query term (e.g. "pip") appears in
        # both the question and an off-topic candidate.
        all_facts_missing = total_reqs > 0 and len(missing_reqs) == total_reqs
        drift_detected = (
            missing_ratio >= _MISSING_RATIO_THRESHOLD
            and len(missing_reqs) >= _MIN_MISSING_COUNT
            and (all_facts_missing or question_overlap < _QUESTION_OVERLAP_FLOOR)
        )

        if drift_detected:
            reason = (
                f"High semantic drift: candidate answer omitted key required "
                f"fact(s): {', '.join(missing_reqs)}."
            )
        elif missing_reqs:
            reason = (
                f"Minor wording difference; required fact(s) not lexically matched "
                f"but question intent appears preserved: {', '.join(missing_reqs)}."
            )
        else:
            reason = "No significant semantic drift detected. Candidate answer retains original question intent."

        changed_intent = f"Omitted facts: {', '.join(missing_reqs)}" if drift_detected and missing_reqs else None

        report = SemanticDriftReport(
            drift_detected=drift_detected,
            drift_score=drift_score,
            drift_reason=reason,
            changed_intent=changed_intent,
            added_information=added_information[:5],
            removed_information=missing_reqs if drift_detected else [],
        )

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Semantic Drift Detection Completed | latency_ms=%.3f | drift_detected=%s | "
            "drift_score=%.4f | question_overlap=%.4f | missing=%d/%d | reason=%s",
            latency_ms, drift_detected, drift_score, question_overlap,
            len(missing_reqs), total_reqs, reason,
        )

        return report, round(latency_ms, 3)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_covered(self, req_terms: set[str], candidate_terms: set[str]) -> bool:
        """Return True when req_terms and candidate_terms overlap sufficiently
        in EITHER direction (bidirectional coverage check).
        """
        if not req_terms or not candidate_terms:
            return False
        shared = req_terms & candidate_terms
        forward = len(shared) / len(req_terms)          # how much of req is in candidate
        reverse = len(shared) / len(candidate_terms)    # how much of candidate matches req
        return forward >= _COVERAGE_THRESHOLD or reverse >= _COVERAGE_THRESHOLD

    def _tokenize(self, text: str) -> set[str]:
        stop_words = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it",
            "of", "on", "that", "the", "to", "was", "were", "what", "when", "where", "who", "why", "with"
        }
        tokens = set(re.findall(r"[A-Za-z0-9]+", text.lower()))
        return tokens - stop_words
