"""Claim Extractor module to break down answers into factual claims."""

import re
from backend.verification.schemas import ExtractedClaim

# Phrases whose presence in an answer indicates an abstention / insufficient-evidence response.
# Matching is case-insensitive and substring-based.
_ABSTENTION_PHRASES: tuple[str, ...] = (
    "insufficient information",
    "not enough information",
    "no relevant information",
    "no information available",
    "cannot answer from the provided",
    "cannot answer based on the provided",
    "cannot answer using the provided",
    "knowledge base does not contain",
    "knowledge base does not have",
    "evidence does not support an answer",
    "evidence does not contain",
    "unable to determine from",
    "not contained in the provided",
    "not available in the provided",
    "provided documents do not",
    "provided knowledge base does not",
    "no sufficient information",
    "not present in the provided",
)


class ClaimExtractor:
    """Extracts factual claims from a candidate answer into independent units."""

    @staticmethod
    def is_abstention(text: str) -> bool:
        """Return True when *text* is a system-level abstention / insufficient-evidence response.

        Abstention responses should NOT be decomposed into factual claims for verification.
        """
        if not text:
            return False
        lower = text.lower()
        return any(phrase in lower for phrase in _ABSTENTION_PHRASES)

    def extract_claims(self, text: str) -> list[ExtractedClaim]:
        if not text or not text.strip():
            return []

        # Abstention answers are not factual claims — return empty to avoid penalisation.
        if self.is_abstention(text):
            return []

        # Normalize unicode whitespace (e.g. narrow no-break space \u202f, non-breaking space \xa0)
        cleaned_text = text.replace("\u202f", " ").replace("\xa0", " ")

        # Remove citation and evidence references
        cleaned_text = re.sub(r"\[Evidence\s+\d+\]", " ", cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r"Source:\s*[^\n]+", " ", cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r"\[\d+\]\([^)]+\)", " ", cleaned_text)  # [1](chunk_id=...)
        cleaned_text = re.sub(r"\[\d+\]", " ", cleaned_text)  # [1]
        cleaned_text = re.sub(r"\[chunk_id=[^\]]+\]", " ", cleaned_text)  # [chunk_id=...]
        cleaned_text = re.sub(r"\?\d+\?chunk_id=[^?]+\?", " ", cleaned_text)  # ?1?chunk_id=...?
        cleaned_text = re.sub(r"[*_`#]", " ", cleaned_text)  # Markdown formatting

        # Split sentences by punctuation or conjunctions
        sentences = re.split(r"(?<=[.!?])\s+", cleaned_text.replace("\n", " "))

        claims: list[ExtractedClaim] = []
        claim_idx = 1

        for sentence in sentences:
            clean_s = sentence.strip()
            if not clean_s or len(clean_s) < 5:
                continue

            # Split compound sentences on ' and ' or ';' if long enough
            sub_parts = re.split(r"\b(and|but|while)\b", clean_s, flags=re.IGNORECASE)

            # Reconstruct meaningful clauses if splitting yields valid pieces
            built_claims = []
            curr = ""
            for part in sub_parts:
                if part.lower() in {"and", "but", "while"}:
                    if curr.strip():
                        built_claims.append(curr.strip())
                    curr = ""
                else:
                    curr += (" " if curr else "") + part
            if curr.strip():
                built_claims.append(curr.strip())

            # Fallback to full sentence if sub-parts are too short or incomplete
            if len(built_claims) <= 1 or any(len(c.split()) < 3 for c in built_claims):
                claims.append(ExtractedClaim(claim_id=f"claim_{claim_idx}", claim_text=clean_s))
                claim_idx += 1
            else:
                for sub in built_claims:
                    sub_clean = sub.strip().rstrip(".,;")
                    if len(sub_clean.split()) >= 3:
                        claims.append(ExtractedClaim(claim_id=f"claim_{claim_idx}", claim_text=sub_clean))
                        claim_idx += 1

        return claims
