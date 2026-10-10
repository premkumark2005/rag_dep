"""Reflection Agent for executing single-pass LLM reflection with fallback handling."""

import json
import re
from backend.confidence.schemas import ConfidenceResult
from backend.generation.llm_client import LLMClient
from backend.models.schemas import PlanOutput, RerankedChunk
from backend.reflection.reflection_prompt import build_reflection_prompt
from backend.reflection.schemas import IdentifiedProblem, ReflectionProblemType, ReflectionReport
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ReflectionAgent:
    """Performs single-pass lightweight reflection over low-confidence answers."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def reflect(
        self,
        question: str,
        plan: PlanOutput,
        evidence: list[RerankedChunk],
        initial_answer: str,
        confidence: ConfidenceResult,
        reason: str,
    ) -> tuple[ReflectionReport, str]:
        """Runs reflection once and returns (ReflectionReport, prompt_text)."""
        prompt = build_reflection_prompt(
            question=question,
            plan=plan,
            evidence=evidence,
            initial_answer=initial_answer,
            confidence=confidence,
        )

        try:
            raw_response = self.llm_client.generate(prompt)
            report = self._parse_reflection_response(raw_response, reason, initial_answer)
        except Exception as exc:
            logger.warning("Reflection generation/parsing failed, falling back to default report: %s", exc)
            report = ReflectionReport(
                reflection_required=True,
                reflection_reason=reason,
                identified_problems=[
                    IdentifiedProblem(
                        type=ReflectionProblemType.OTHER,
                        description=f"Reflection parsing error: {exc}",
                    )
                ],
                missing_facts=plan.missing_facts,
                unsupported_claims=[],
                candidate_answer=initial_answer,
                reflection_summary="Reflection attempted but failed to produce structured output. Retained initial answer.",
            )

        return report, prompt

    def _parse_reflection_response(
        self,
        raw_response: str,
        reason: str,
        initial_answer: str,
    ) -> ReflectionReport:
        clean_text = raw_response.strip()
        # Remove markdown code fences if present
        if clean_text.startswith("```"):
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r"\s*```$", "", clean_text)

        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError:
            # Malformed JSON recovery
            json_match = re.search(r"\{.*\}", clean_text, flags=re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {}

        if not data or not isinstance(data, dict):
            return ReflectionReport(
                reflection_required=True,
                reflection_reason=reason,
                identified_problems=[
                    IdentifiedProblem(
                        type=ReflectionProblemType.OTHER,
                        description="Malformed JSON response from reflection model.",
                    )
                ],
                missing_facts=[],
                unsupported_claims=[],
                candidate_answer=initial_answer,
                reflection_summary="Fallback report generated due to malformed LLM response.",
            )

        summary = data.get("reflection_summary") or "Single-pass reflection completed."
        missing_facts = [str(f) for f in data.get("missing_facts", [])]
        unsupported_claims = [str(c) for c in data.get("unsupported_claims", [])]
        candidate = data.get("candidate_answer") or initial_answer

        raw_problems = data.get("identified_problems", [])
        problems: list[IdentifiedProblem] = []

        valid_types = {t.value for t in ReflectionProblemType}
        if isinstance(raw_problems, list):
            for item in raw_problems:
                if isinstance(item, dict):
                    p_type = str(item.get("type", "OTHER")).upper()
                    if p_type not in valid_types:
                        p_type = ReflectionProblemType.OTHER.value
                    desc = str(item.get("description", "Unspecified problem"))
                    problems.append(IdentifiedProblem(type=ReflectionProblemType(p_type), description=desc))

        if not problems:
            problems.append(
                IdentifiedProblem(
                    type=ReflectionProblemType.OTHER,
                    description="Low confidence detected by confidence gate.",
                )
            )

        return ReflectionReport(
            reflection_required=True,
            reflection_reason=reason,
            identified_problems=problems,
            missing_facts=missing_facts,
            unsupported_claims=unsupported_claims,
            candidate_answer=candidate,
            reflection_summary=summary,
        )
