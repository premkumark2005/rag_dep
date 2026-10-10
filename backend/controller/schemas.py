"""Schemas for Phase 6 Dynamic Reflection Controller."""

from enum import Enum
from pydantic import BaseModel


class ControllerDecision(str, Enum):
    RETURN_INITIAL = "RETURN_INITIAL"
    RETURN_REFLECTED = "RETURN_REFLECTED"
    REFLECT_AGAIN = "REFLECT_AGAIN"
    RETRIEVE_MORE = "RETRIEVE_MORE"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class AnswerType(str, Enum):
    INITIAL = "INITIAL"
    REFLECTED = "REFLECTED"
    NONE = "NONE"


class ControllerMetrics(BaseModel):
    confidence: float
    verification: float
    drift: float
    verification_threshold: float
    drift_threshold: float
    decision_latency_ms: float


class ControllerResult(BaseModel):
    decision: ControllerDecision
    reason: str
    selected_answer: str
    selected_answer_type: AnswerType
    metrics: ControllerMetrics
    reflection_retry: bool = False
    retrieval_retry: bool = False
    final_status: str
