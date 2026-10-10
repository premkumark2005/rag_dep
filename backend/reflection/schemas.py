"""Schemas for Phase 4 Ultra-Lightweight Reflection module."""

from enum import Enum
from pydantic import BaseModel


class ReflectionProblemType(str, Enum):
    MISSING_FACT = "MISSING_FACT"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    WEAK_EVIDENCE = "WEAK_EVIDENCE"
    CONTRADICTION = "CONTRADICTION"
    INCOMPLETE_ANSWER = "INCOMPLETE_ANSWER"
    LOW_RETRIEVAL_CONFIDENCE = "LOW_RETRIEVAL_CONFIDENCE"
    OTHER = "OTHER"


class IdentifiedProblem(BaseModel):
    type: ReflectionProblemType
    description: str


class ReflectionReport(BaseModel):
    reflection_required: bool
    reflection_reason: str
    identified_problems: list[IdentifiedProblem]
    missing_facts: list[str]
    unsupported_claims: list[str]
    candidate_answer: str | None = None
    reflection_summary: str
