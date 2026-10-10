"""Schemas for Phase 5 Evidence Verification and Claim Extraction."""

from enum import Enum
from pydantic import BaseModel


class ClaimStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


class ExtractedClaim(BaseModel):
    claim_id: str
    claim_text: str


class VerifiedClaimItem(BaseModel):
    claim_id: str
    claim_text: str
    status: ClaimStatus
    supporting_chunks: list[str] = []
    contradicting_chunks: list[str] = []
    confidence: float = 1.0


class VerificationReport(BaseModel):
    verified_claims: list[VerifiedClaimItem]
    supported_claims: list[str]
    unsupported_claims: list[str]
    contradicted_claims: list[str]
    verification_score: float
    # Abstention-awareness fields (backward-compatible, default False)
    abstention_detected: bool = False
    abstention_valid: bool = False

