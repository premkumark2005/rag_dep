"""Evidence-grounded planner producing structured answer plans."""

from __future__ import annotations

import json
import re

from backend.generation.llm_client import LLMClient
from backend.models.schemas import FactEvidence, FactStatus, PlanOutput, RerankedChunk, RequiredFact
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class PlanningModule:
    """Generates structured plans from question + evidence."""

    def __init__(self, llm_client: LLMClient, max_retries: int = 1) -> None:
        self.llm_client = llm_client
        self.max_retries = max_retries

    def create_plan(self, question: str, evidence_chunks: list[RerankedChunk]) -> PlanOutput:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        prompt = self._build_planner_prompt(question, evidence_chunks)
        attempts = 0
        llm_output = ""
        while attempts <= self.max_retries:
            llm_output = self.llm_client.generate(prompt)
            parsed = self._parse_and_validate_plan(llm_output, evidence_chunks)
            if parsed is not None:
                return parsed

            attempts += 1
            if attempts <= self.max_retries:
                prompt = self._build_repair_prompt(question, evidence_chunks, llm_output)

        logger.warning("Planner JSON invalid after retries; using deterministic fallback plan.")
        return self._fallback_plan(question, evidence_chunks)

    def _build_planner_prompt(self, question: str, evidence_chunks: list[RerankedChunk]) -> str:
        evidence_lines: list[str] = []
        for item in evidence_chunks:
            evidence_lines.append(
                f"- chunk_id: {item.chunk_id}\n"
                f"  document_id: {item.document_id}\n"
                f"  source: {item.source}\n"
                f"  text: {item.text}"
            )

        evidence_block = "\n".join(evidence_lines) if evidence_lines else "(No evidence provided)"
        return (
            "You are an evidence-grounded planning module for RAG.\n"
            "Use ONLY the supplied evidence.\n"
            "Do not use internal knowledge, do not invent evidence, and do not generate the final answer.\n"
            "Every supported_fact must cite a valid chunk_id from the evidence list.\n"
            "If evidence is missing, mark status MISSING.\n"
            "If evidence contains incompatible claims for same fact, mark status CONFLICTING.\n"
            "Return strict JSON only with this schema keys exactly:\n"
            "{"
            '"question_intent": string,'
            '"required_facts": [{"fact_id": string, "requirement": string, "status": "FOUND|MISSING|CONFLICTING", '
            '"evidence": [{"chunk_id": string, "document_id": string, "supported_fact": string}]}],'
            '"missing_facts": [string],'
            '"conflicting_facts": [string],'
            '"answer_instruction": string'
            "}\n\n"
            f"QUESTION:\n{question}\n\n"
            f"EVIDENCE:\n{evidence_block}"
        )

    def _build_repair_prompt(self, question: str, evidence_chunks: list[RerankedChunk], bad_output: str) -> str:
        return (
            self._build_planner_prompt(question, evidence_chunks)
            + "\n\nPrevious output was invalid JSON. Return only corrected strict JSON.\n"
            + f"INVALID_OUTPUT:\n{bad_output}"
        )

    def _parse_and_validate_plan(
        self,
        llm_output: str,
        evidence_chunks: list[RerankedChunk],
    ) -> PlanOutput | None:
        json_text = self._extract_json_block(llm_output)
        if not json_text:
            return None

        try:
            payload = json.loads(json_text)
            plan = PlanOutput.model_validate(payload)
        except Exception:  # noqa: BLE001
            return None

        valid_chunk_ids = {chunk.chunk_id for chunk in evidence_chunks}
        for fact in plan.required_facts:
            for evidence in fact.evidence:
                if evidence.chunk_id not in valid_chunk_ids:
                    return None
        return plan

    def _extract_json_block(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            return stripped

        fenced = re.search(r"```json\s*(\{.*\})\s*```", text, flags=re.DOTALL)
        if fenced:
            return fenced.group(1).strip()

        braces = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        if braces:
            return braces.group(1).strip()
        return ""

    def _fallback_plan(self, question: str, evidence_chunks: list[RerankedChunk]) -> PlanOutput:
        requirements = self._infer_requirements(question)
        required_facts: list[RequiredFact] = []
        missing_facts: list[str] = []
        conflicting_facts: list[str] = []

        for index, requirement in enumerate(requirements, start=1):
            status, evidence = self._evaluate_requirement(requirement, evidence_chunks)
            required_facts.append(
                RequiredFact(
                    fact_id=f"fact_{index}",
                    requirement=requirement,
                    status=status,
                    evidence=evidence,
                )
            )
            if status == FactStatus.MISSING:
                missing_facts.append(requirement)
            elif status == FactStatus.CONFLICTING:
                conflicting_facts.append(requirement)

        if missing_facts or conflicting_facts:
            instruction = (
                "Answer only using FOUND facts. Clearly state missing/conflicting information and avoid unsupported claims."
            )
        else:
            instruction = "Answer using only the cited evidence for each required fact."

        return PlanOutput(
            question_intent=f"Answer the question using evidence-grounded facts: {question}",
            required_facts=required_facts,
            missing_facts=missing_facts,
            conflicting_facts=conflicting_facts,
            answer_instruction=instruction,
        )

    def _infer_requirements(self, question: str) -> list[str]:
        normalized = question.strip().rstrip("?")
        clauses = [part.strip() for part in re.split(r"\band\b", normalized, flags=re.IGNORECASE) if part.strip()]
        if not clauses:
            return [normalized]
        requirements: list[str] = []
        for clause in clauses:
            lower = clause.lower()
            if lower.startswith("who "):
                requirements.append(f"Identify: {clause}")
            elif lower.startswith("when "):
                requirements.append(f"Determine time/date: {clause}")
            elif "when" in lower or "year" in lower or "date" in lower:
                requirements.append(f"Determine time/date: {clause}")
            else:
                requirements.append(f"Determine: {clause}")
        return requirements

    def _evaluate_requirement(
        self,
        requirement: str,
        chunks: list[RerankedChunk],
    ) -> tuple[FactStatus, list[FactEvidence]]:
        req_terms = self._tokens(requirement)
        matched_sentences: list[FactEvidence] = []

        for chunk in chunks:
            sentences = re.split(r"(?<=[.!?])\s+", chunk.text)
            for sentence in sentences:
                clean = sentence.strip()
                if not clean:
                    continue
                sentence_terms = self._tokens(clean)
                if len(req_terms & sentence_terms) == 0:
                    continue
                matched_sentences.append(
                    FactEvidence(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        supported_fact=clean,
                    )
                )

        if not matched_sentences:
            return FactStatus.MISSING, []

        lower_req = requirement.lower()
        if "time/date" in lower_req or "when" in lower_req or "year" in lower_req:
            years = self._extract_years([item.supported_fact for item in matched_sentences])
            if len(years) > 1:
                return FactStatus.CONFLICTING, matched_sentences
            if len(years) == 0:
                return FactStatus.MISSING, []

        if "who" in lower_req or "identify" in lower_req or "creator" in lower_req:
            creators = self._extract_creator_names([item.supported_fact for item in matched_sentences])
            if len(creators) > 1:
                return FactStatus.CONFLICTING, matched_sentences

        return FactStatus.FOUND, matched_sentences

    def _tokens(self, text: str) -> set[str]:
        return set(re.findall(r"[A-Za-z0-9]+", text.lower()))

    def _extract_years(self, sentences: list[str]) -> set[str]:
        years: set[str] = set()
        for sentence in sentences:
            years.update(re.findall(r"\b(?:1[0-9]{3}|20[0-9]{2})\b", sentence))
        return years

    def _extract_creator_names(self, sentences: list[str]) -> set[str]:
        names: set[str] = set()
        for sentence in sentences:
            match = re.search(r"created by ([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})", sentence)
            if match:
                names.add(match.group(1).strip())
        return names

