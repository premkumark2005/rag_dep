import json

from backend.models.schemas import FactStatus, RerankedChunk
from backend.planning.planner import PlanningModule


class _LLMStub:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.call_count = 0

    def generate(self, prompt: str) -> str:
        _ = prompt
        if self.call_count < len(self.outputs):
            value = self.outputs[self.call_count]
        else:
            value = self.outputs[-1]
        self.call_count += 1
        return value


def _evidence_chunks() -> list[RerankedChunk]:
    return [
        RerankedChunk(
            rerank_rank=1,
            chunk_id="chunk_001",
            document_id="doc_001",
            title="python",
            text="Python was created by Guido van Rossum.",
            source="python.txt",
            chunk_index=0,
            reranker_raw_score=0.9,
            bm25_rank=1,
            bm25_score=10.0,
            dense_rank=1,
            dense_score=0.95,
            rrf_score=0.03,
        ),
        RerankedChunk(
            rerank_rank=2,
            chunk_id="chunk_002",
            document_id="doc_001",
            title="python",
            text="Python was first publicly released in 1991.",
            source="python.txt",
            chunk_index=1,
            reranker_raw_score=0.85,
            bm25_rank=2,
            bm25_score=9.0,
            dense_rank=2,
            dense_score=0.9,
            rrf_score=0.029,
        ),
    ]


def test_planner_parses_all_facts_found_json() -> None:
    payload = {
        "question_intent": "Identify Python creator and first public release year.",
        "required_facts": [
            {
                "fact_id": "fact_1",
                "requirement": "Creator of Python",
                "status": "FOUND",
                "evidence": [
                    {
                        "chunk_id": "chunk_001",
                        "document_id": "doc_001",
                        "supported_fact": "Python was created by Guido van Rossum.",
                    }
                ],
            },
            {
                "fact_id": "fact_2",
                "requirement": "First release year of Python",
                "status": "FOUND",
                "evidence": [
                    {
                        "chunk_id": "chunk_002",
                        "document_id": "doc_001",
                        "supported_fact": "Python was first publicly released in 1991.",
                    }
                ],
            },
        ],
        "missing_facts": [],
        "conflicting_facts": [],
        "answer_instruction": "Use only cited evidence.",
    }
    planner = PlanningModule(_LLMStub([json.dumps(payload)]), max_retries=0)
    plan = planner.create_plan("Who created Python and when was it first released?", _evidence_chunks())

    assert len(plan.required_facts) == 2
    assert all(item.status == FactStatus.FOUND for item in plan.required_facts)
    assert not plan.missing_facts


def test_planner_parses_missing_fact_json() -> None:
    payload = {
        "question_intent": "Identify creator and release year.",
        "required_facts": [
            {
                "fact_id": "fact_1",
                "requirement": "Creator of Python",
                "status": "FOUND",
                "evidence": [
                    {
                        "chunk_id": "chunk_001",
                        "document_id": "doc_001",
                        "supported_fact": "Python was created by Guido van Rossum.",
                    }
                ],
            },
            {
                "fact_id": "fact_2",
                "requirement": "First release year of Python",
                "status": "MISSING",
                "evidence": [],
            },
        ],
        "missing_facts": ["First release year of Python"],
        "conflicting_facts": [],
        "answer_instruction": "State creator and mention missing year evidence.",
    }
    planner = PlanningModule(_LLMStub([json.dumps(payload)]), max_retries=0)
    plan = planner.create_plan("Who created Python and when was it first released?", _evidence_chunks())

    assert any(item.status == FactStatus.MISSING for item in plan.required_facts)
    assert "First release year of Python" in plan.missing_facts


def test_planner_parses_conflicting_fact_json() -> None:
    payload = {
        "question_intent": "Identify championship year for Team X.",
        "required_facts": [
            {
                "fact_id": "fact_1",
                "requirement": "Year Team X won Championship Y",
                "status": "CONFLICTING",
                "evidence": [
                    {
                        "chunk_id": "chunk_001",
                        "document_id": "doc_001",
                        "supported_fact": "Team X won Championship Y in 1973.",
                    },
                    {
                        "chunk_id": "chunk_002",
                        "document_id": "doc_001",
                        "supported_fact": "Team X won Championship Y in 1999.",
                    },
                ],
            }
        ],
        "missing_facts": [],
        "conflicting_facts": ["Year Team X won Championship Y"],
        "answer_instruction": "Report evidence conflict.",
    }
    planner = PlanningModule(_LLMStub([json.dumps(payload)]), max_retries=0)
    plan = planner.create_plan("When did Team X win Championship Y?", _evidence_chunks())

    assert len(plan.required_facts) == 1
    assert plan.required_facts[0].status == FactStatus.CONFLICTING
    assert plan.conflicting_facts


def test_planner_handles_malformed_json_with_fallback() -> None:
    planner = PlanningModule(_LLMStub(["not-json", "still-not-json"]), max_retries=1)
    plan = planner.create_plan("Who created Python and when was it first released?", _evidence_chunks())

    assert len(plan.required_facts) >= 1
    assert isinstance(plan.missing_facts, list)
    assert isinstance(plan.conflicting_facts, list)

