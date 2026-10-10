"""Evidence Verifier comparing extracted claims strictly against retrieved evidence.

Contradiction policy (CRITICAL):
    Absence of supporting evidence is NOT contradiction.
    A claim is CONTRADICTED only when retrieved evidence explicitly states a fact
    that is INCOMPATIBLE with the claim:
      - Conflicting year for the same dateable event (year-conflict rule).
      - Explicit incompatible substitution (e.g. "instead of X", "rather than X", "X, not Y").
      - Direct negation of the claim's core predicate/entity (e.g. "was not created by X", "not X").
    
    Absence of mention, incomplete information, unrelated topics, or meta-statements
    (such as "does not provide information", "does not establish") are NOT contradictions.
"""

import re
from backend.models.schemas import RerankedChunk
from backend.verification.schemas import ClaimStatus, ExtractedClaim, VerifiedClaimItem
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Stopwords to filter out when tokenizing
_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is", "it",
    "its", "of", "on", "that", "the", "to", "was", "were", "will", "with", "this", "these", "those"
})

# Meta-negation patterns that represent absence of information or general commentary,
# NOT factual contradiction of a claim.
_META_NEGATION_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b(?:does|do|did)\s+not\s+(?:provide|establish|contain|include|state|mention|have|specify)\b", re.IGNORECASE),
    re.compile(r"\bnot\s+(?:available|provided|contained|found|included|known|clear|established)\b", re.IGNORECASE),
    re.compile(r"\bnot\s+(?:fully|entirely|completely)\s+\w+", re.IGNORECASE),
    re.compile(r"\bgenerally\s+do\s+not\b", re.IGNORECASE),
)


class EvidenceVerifier:
    """Verifies factual claims against retrieved evidence chunks ONLY (no external memory)."""

    def verify_claims(
        self,
        claims: list[ExtractedClaim],
        evidence: list[RerankedChunk],
    ) -> list[VerifiedClaimItem]:
        verified_items: list[VerifiedClaimItem] = []

        for claim in claims:
            status, supporting, contradicting = self._verify_single_claim(claim.claim_text, evidence)
            verified_items.append(
                VerifiedClaimItem(
                    claim_id=claim.claim_id,
                    claim_text=claim.claim_text,
                    status=status,
                    supporting_chunks=supporting,
                    contradicting_chunks=contradicting,
                    confidence=1.0 if status == ClaimStatus.SUPPORTED else 0.8,
                )
            )

        return verified_items

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _verify_single_claim(
        self,
        claim_text: str,
        evidence: list[RerankedChunk],
    ) -> tuple[ClaimStatus, list[str], list[str]]:
        claim_tokens = self._tokenize(claim_text)
        if not claim_tokens:
            return ClaimStatus.UNSUPPORTED, [], []

        supporting_chunks: list[str] = []
        contradicting_chunks: list[str] = []

        # Years mentioned explicitly IN THE CLAIM (prerequisite for year-conflict rule)
        claim_years = set(re.findall(r"\b(?:1[0-9]{3}|20[0-9]{2})\b", claim_text))

        for chunk in evidence:
            chunk_text = chunk.text
            chunk_tokens = self._tokenize(chunk_text)

            overlap_ratio = (
                len(claim_tokens & chunk_tokens) / len(claim_tokens)
                if claim_tokens else 0.0
            )

            # ── Check 1: Explicit contradiction ──────────────────────────────
            is_contra = self._is_explicit_contradiction(
                claim_text=claim_text,
                claim_tokens=claim_tokens,
                claim_years=claim_years,
                chunk_text=chunk_text,
                chunk_tokens=chunk_tokens,
                overlap_ratio=overlap_ratio,
            )
            if is_contra:
                contradicting_chunks.append(chunk.chunk_id)
                continue

            # ── Check 2: Direct supporting evidence ──────────────────────────
            # A chunk supports the claim when:
            # - High token overlap (>= 0.5)
            # - If claim has years, chunk must contain at least one of those years
            if overlap_ratio >= 0.5:
                if claim_years:
                    chunk_years = set(re.findall(r"\b(?:1[0-9]{3}|20[0-9]{2})\b", chunk_text))
                    if claim_years & chunk_years:
                        supporting_chunks.append(chunk.chunk_id)
                else:
                    supporting_chunks.append(chunk.chunk_id)

        if contradicting_chunks:
            return ClaimStatus.CONTRADICTED, supporting_chunks, contradicting_chunks
        if supporting_chunks:
            return ClaimStatus.SUPPORTED, supporting_chunks, []

        return ClaimStatus.UNSUPPORTED, [], []

    def _is_explicit_contradiction(
        self,
        claim_text: str,
        claim_tokens: set[str],
        claim_years: set[str],
        chunk_text: str,
        chunk_tokens: set[str],
        overlap_ratio: float,
    ) -> bool:
        """Return True ONLY when chunk_text explicitly states an incompatible fact."""
        # Clean out meta-negations ("does not provide", "not available", etc.) before checking
        cleaned_chunk = chunk_text
        for pattern in _META_NEGATION_PATTERNS:
            cleaned_chunk = pattern.sub(" ", cleaned_chunk)

        # ── Case A: Year-conflict contradiction ──────────────────────────────
        # Applies when:
        # 1. The claim asserts an explicit year for an event.
        # 2. The chunk is about the same entity/event (overlap >= 0.4).
        # 3. The chunk provides dates, but NONE of the claim's years appear in the chunk.
        # 4. The chunk shares event predicates (e.g. "created", "released", "appeared", "began").
        if claim_years and overlap_ratio >= 0.4:
            chunk_years = set(re.findall(r"\b(?:1[0-9]{3}|20[0-9]{2})\b", chunk_text))
            if chunk_years and not (claim_years & chunk_years):
                event_keywords = {"created", "released", "published", "began", "started", "founded", "appeared", "developed"}
                if (claim_tokens & chunk_tokens & event_keywords) or len(claim_tokens & chunk_tokens) >= 3:
                    return True

        # ── Case B: Explicit alternative substitution ("instead of X", "rather than X")
        # e.g., "created using module X instead of venv"
        # Extract distinctive tokens from claim (tokens with len > 2, excluding generic words)
        generic_words = {"python", "language", "module", "used", "create", "creating", "tools", "tool", "program"}
        distinctive_claim_tokens = (claim_tokens - generic_words)

        for token in distinctive_claim_tokens:
            token_pattern = re.escape(token)
            # Pattern: "instead of <token>", "rather than <token>", "not <token>", "unlike <token>"
            subst_regex = rf"\b(?:instead\s+of|rather\s+than|unlike|not)\s+{token_pattern}\b"
            if re.search(subst_regex, cleaned_chunk, flags=re.IGNORECASE):
                # Ensure the claim itself didn't assert this negation
                if not re.search(subst_regex, claim_text, flags=re.IGNORECASE):
                    return True

        # ── Case C: Direct predicate negation of core claim action ───────────
        # e.g. "was not created by Guido", "is not used to create"
        for token in distinctive_claim_tokens:
            token_pattern = re.escape(token)
            direct_neg_regex = rf"\b(?:was\s+not|is\s+not|were\s+not|cannot\s+be|never)\s+(?:\w+\s+)?{token_pattern}\b"
            if re.search(direct_neg_regex, cleaned_chunk, flags=re.IGNORECASE):
                if not re.search(direct_neg_regex, claim_text, flags=re.IGNORECASE):
                    return True

        return False

    def _tokenize(self, text: str) -> set[str]:
        tokens = set(re.findall(r"[A-Za-z0-9]+", text.lower()))
        return tokens - _STOP_WORDS
