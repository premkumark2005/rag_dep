"""Verification Service orchestrating claim extraction, evidence verification, and scoring."""

import time
from backend.models.schemas import PlanOutput, RerankedChunk
from backend.verification.claim_extractor import ClaimExtractor
from backend.verification.evidence_verifier import EvidenceVerifier
from backend.verification.schemas import ClaimStatus, VerificationReport
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class VerificationService:
    """Orchestrates claim extraction and evidence verification over candidate answers."""

    def __init__(self) -> None:
        self.claim_extractor = ClaimExtractor()
        self.evidence_verifier = EvidenceVerifier()

    def verify(
        self,
        candidate_answer: str | None,
        initial_answer: str,
        evidence: list[RerankedChunk],
        plan: PlanOutput | None = None,
    ) -> tuple[VerificationReport, float]:
        start_time = time.perf_counter()
        target_text = candidate_answer or initial_answer

        logger.info("Verification Started")

        # ── Abstention detection ──────────────────────────────────────────────
        # If the answer is a system-level "I don't know" / "insufficient info"
        # response, we must NOT treat the abstention sentence as an unsupported
        # claim.  Instead we check whether the planner agrees that information
        # is missing and mark the abstention as valid if so.
        if self.claim_extractor.is_abstention(target_text):
            has_missing_facts = bool(plan and plan.missing_facts)
            latency_ms = (time.perf_counter() - start_time) * 1000
            # Score: 1.0 when abstention is valid (planner confirms missing facts),
            #        0.5 when no planner evidence of missing facts (unusual path).
            score = 1.0 if has_missing_facts else 0.5
            report = VerificationReport(
                verified_claims=[],
                supported_claims=[],
                unsupported_claims=[],
                contradicted_claims=[],
                verification_score=score,
                abstention_detected=True,
                abstention_valid=has_missing_facts,
            )
            logger.info(
                "Verification Completed (abstention) | latency_ms=%.3f | "
                "abstention_valid=%s | score=%.2f",
                latency_ms, has_missing_facts, score,
            )
            return report, round(latency_ms, 3)

        # ── Normal claim-based verification ──────────────────────────────────
        claims = self.claim_extractor.extract_claims(target_text)

        if not claims:
            report = VerificationReport(
                verified_claims=[],
                supported_claims=[],
                unsupported_claims=[],
                contradicted_claims=[],
                verification_score=1.0,
            )
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.info("Verification Completed | latency_ms=%.3f | total_claims=0 | score=1.00", latency_ms)
            return report, round(latency_ms, 3)

        verified_items = self.evidence_verifier.verify_claims(claims, evidence)

        supported = [item.claim_text for item in verified_items if item.status == ClaimStatus.SUPPORTED]
        unsupported = [item.claim_text for item in verified_items if item.status == ClaimStatus.UNSUPPORTED]
        contradicted = [item.claim_text for item in verified_items if item.status == ClaimStatus.CONTRADICTED]

        total_claims = len(verified_items)
        score = len(supported) / total_claims if total_claims > 0 else 1.0

        report = VerificationReport(
            verified_claims=verified_items,
            supported_claims=supported,
            unsupported_claims=unsupported,
            contradicted_claims=contradicted,
            verification_score=round(score, 4),
        )

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Verification Completed | latency_ms=%.3f | total_claims=%d | "
            "supported=%d | unsupported=%d | contradicted=%d | score=%.4f",
            latency_ms, total_claims, len(supported), len(unsupported), len(contradicted), score,
        )

        return report, round(latency_ms, 3)
