"""Prompt templates and utilities for Ultra-Lightweight Reflection."""

from backend.confidence.schemas import ConfidenceResult
from backend.models.schemas import PlanOutput, RerankedChunk


def build_reflection_prompt(
    question: str,
    plan: PlanOutput,
    evidence: list[RerankedChunk],
    initial_answer: str,
    confidence: ConfidenceResult,
) -> str:
    """Build structured prompt instructing LLM to reflect on low-confidence answer."""
    evidence_text = "\n".join(
        [
            f"- chunk_id: {c.chunk_id}\n  document_id: {c.document_id}\n  source: {c.source}\n  text: {c.text}"
            for c in evidence
        ]
    )

    plan_json = plan.model_dump_json(indent=2)
    
    confidence_summary = (
        f"Overall Confidence: {confidence.overall_confidence:.4f}\n"
        f"- Retrieval Confidence: {confidence.retrieval_confidence:.4f}\n"
        f"- Evidence Support: {confidence.evidence_support:.4f}\n"
        f"- Fact Coverage: {confidence.fact_coverage:.4f}\n"
        f"- Answer Consistency: {confidence.answer_consistency:.4f}\n"
        f"- Evidence Agreement: {confidence.evidence_agreement:.4f}"
    )

    return f"""You are an evidence-grounded reflection assistant.
Your job is NOT to generate a new answer from scratch.

Review the existing answer against the question, planner instructions, retrieved evidence, and confidence analysis.

QUESTION:
{question}

PLANNER OUTPUT:
{plan_json}

RETRIEVED EVIDENCE:
{evidence_text}

INITIAL ANSWER:
{initial_answer}

CONFIDENCE ANALYSIS:
{confidence_summary}

INSTRUCTIONS:
1. Identify problems in the initial answer (e.g. MISSING_FACT, UNSUPPORTED_CLAIM, WEAK_EVIDENCE, CONTRADICTION, INCOMPLETE_ANSWER, LOW_RETRIEVAL_CONFIDENCE, OTHER).
2. List any missing facts or unsupported claims explicitly.
3. Suggest corrections and generate ONE improved candidate answer grounded strictly in the provided evidence.
4. Do NOT introduce any external knowledge not found in the evidence.

Return strict JSON only with this schema:
{{
  "reflection_summary": "High level explanation of why confidence was low and how it was corrected",
  "identified_problems": [
    {{
      "type": "MISSING_FACT | UNSUPPORTED_CLAIM | WEAK_EVIDENCE | CONTRADICTION | INCOMPLETE_ANSWER | LOW_RETRIEVAL_CONFIDENCE | OTHER",
      "description": "Specific problem description"
    }}
  ],
  "missing_facts": ["List of missing facts"],
  "unsupported_claims": ["List of unsupported claims"],
  "candidate_answer": "The revised improved answer strictly using provided evidence."
}}
"""
