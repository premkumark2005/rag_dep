"""Grounded answer generation from retrieved evidence."""

from backend.generation.llm_client import LLMClient
from backend.models.schemas import PlanOutput, RerankedChunk, RetrievedChunk


class AnswerGenerator:
    """Builds grounded prompts and generates final answers."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def generate(self, query: str, retrieved_chunks: list[RetrievedChunk]) -> str:
        prompt = self._build_prompt(query, retrieved_chunks)
        return self.llm_client.generate(prompt)

    def _build_prompt(self, question: str, retrieved_chunks: list[RetrievedChunk]) -> str:
        context_parts: list[str] = []
        for item in retrieved_chunks:
            context_parts.append(
                f"[Evidence {item.rank}]\n"
                f"Source: {item.source}\n"
                f"{item.text}\n"
            )

        context_block = "\n".join(context_parts) if context_parts else "(No evidence retrieved.)"
        return (
            "You are a retrieval-augmented question answering system.\n\n"
            "Answer the user's question using ONLY the information contained in the provided context.\n\n"
            "Do not introduce factual claims that are unsupported by the context.\n\n"
            "If the provided context is insufficient to answer the question, clearly state:\n"
            "'Insufficient information in the provided knowledge base.'\n\n"
            "Do not use unsupported external knowledge.\n\n"
            f"QUESTION:\n{question}\n\n"
            f"CONTEXT:\n\n{context_block}\n\n"
            "ANSWER:"
        )


class PlannedAnswerGenerator:
    """Generates an initial answer from planner output + reranked evidence."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def generate(self, query: str, plan: PlanOutput, reranked_chunks: list[RerankedChunk]) -> str:
        prompt = self._build_prompt(query, plan, reranked_chunks)
        return self.llm_client.generate(prompt)

    def _build_prompt(self, query: str, plan: PlanOutput, reranked_chunks: list[RerankedChunk]) -> str:
        context_lines: list[str] = []
        for chunk in reranked_chunks:
            context_lines.append(
                f"[Evidence {chunk.rerank_rank}] chunk_id={chunk.chunk_id}\n"
                f"Source: {chunk.source}\n"
                f"{chunk.text}\n"
            )

        required_facts_lines: list[str] = []
        for fact in plan.required_facts:
            evidence_ids = ", ".join(item.chunk_id for item in fact.evidence) if fact.evidence else "None"
            required_facts_lines.append(
                f"- {fact.fact_id}: {fact.requirement} | status={fact.status.value} | evidence={evidence_ids}"
            )

        required_facts_block = "\n".join(required_facts_lines) if required_facts_lines else "- None"
        context_block = "\n".join(context_lines) if context_lines else "(No evidence retrieved.)"

        return (
            "You are an evidence-grounded question answering system.\n\n"
            "Generate the answer using ONLY the supplied evidence and structured plan.\n"
            "Do not introduce facts that are not supported by the evidence.\n"
            "Do not silently fill facts marked MISSING.\n"
            "Do not silently resolve facts marked CONFLICTING.\n"
            "If critical information required to answer the question is missing or conflicting, clearly indicate "
            "that the available evidence is insufficient or conflicting.\n"
            "Follow the answer instruction produced by the planning module.\n\n"
            f"QUESTION:\n{query}\n\n"
            f"PLANNED_INTENT:\n{plan.question_intent}\n\n"
            f"REQUIRED_FACTS:\n{required_facts_block}\n\n"
            f"MISSING_FACTS:\n{plan.missing_facts}\n\n"
            f"CONFLICTING_FACTS:\n{plan.conflicting_facts}\n\n"
            f"ANSWER_INSTRUCTION:\n{plan.answer_instruction}\n\n"
            f"CONTEXT:\n{context_block}\n\n"
            "INITIAL ANSWER:"
        )
