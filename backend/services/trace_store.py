"""In-memory trace store for retrieving execution traces by request_id."""

from backend.models.schemas import Phase2QueryResponse

_TRACE_STORE: dict[str, Phase2QueryResponse] = {}


def save_trace(response: Phase2QueryResponse) -> None:
    """Save execution trace in store."""
    _TRACE_STORE[response.request_id] = response


def get_trace(request_id: str) -> Phase2QueryResponse | None:
    """Retrieve execution trace by request_id."""
    return _TRACE_STORE.get(request_id)


def list_traces() -> list[dict[str, str]]:
    """List recent saved request_ids and questions."""
    result = []
    for req_id, resp in _TRACE_STORE.items():
        system = getattr(resp, "system", "proposed_rag")
        decision_val = "N/A"
        ctrl = resp.controller
        if isinstance(ctrl, dict):
            decision_val = str(ctrl.get("decision", "N/A"))
        elif ctrl is not None and hasattr(ctrl, "decision"):
            decision_val = str(getattr(ctrl.decision, "value", ctrl.decision))
            
        result.append(
            {
                "request_id": req_id,
                "question": resp.question,
                "system": system,
                "final_answer": resp.final_answer,
                "decision": decision_val,
            }
        )
    return result
