"""Schemas for Phase 5 Semantic Drift Detection."""

from pydantic import BaseModel


class SemanticDriftReport(BaseModel):
    drift_detected: bool
    drift_score: float
    drift_reason: str
    changed_intent: str | None = None
    added_information: list[str] = []
    removed_information: list[str] = []
