from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.models.schemas import IngestResponse, Phase2QueryRequest, Phase2QueryResponse, QueryRequest, QueryResponse
from backend.services.rag_service import RAGService
from backend.services.trace_store import get_trace, list_traces
from backend.utils.exceptions import (
    IngestionError,
    LLMConfigurationError,
    LLMGenerationError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    RetrievalError,
    VectorStoreError,
    VectorStoreNotReadyError,
)

app = FastAPI(
    title="Confidence-Gated Ultra-Lightweight Reflection RAG",
    description="RAG verification, reflection, and decision controller API.",
    version="7.0.0-phase7",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service = RAGService(settings)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "project": "Confidence-Gated Ultra-Lightweight Reflection RAG",
        "phase": "Phase 7 Evaluator Dashboard",
        "status": "running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    try:
        return rag_service.ingest_documents()
    except IngestionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (VectorStoreError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    try:
        return rag_service.query(payload.question, payload.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except VectorStoreNotReadyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except LLMGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc


@app.post("/query/phase2", response_model=Phase2QueryResponse)
def query_phase2(payload: Phase2QueryRequest) -> Phase2QueryResponse:
    try:
        return rag_service.query_phase2(payload.question, payload.final_context_k, payload.system)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except VectorStoreNotReadyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM configuration error: {exc}. Check LLM_PROVIDER and LLM_API_KEY in your .env file.",
        ) from exc
    except LLMServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except (RetrievalError, LLMGenerationError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Phase 2 query failed: {exc}") from exc


@app.get("/trace/{request_id}", response_model=Phase2QueryResponse)
def get_request_trace(request_id: str) -> Phase2QueryResponse:
    """Retrieve full pipeline trace for evaluator dashboard."""
    trace = get_trace(request_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace for request_id '{request_id}' not found.")
    return trace


@app.get("/traces")
def list_request_traces() -> list[dict[str, str]]:
    """List recent query traces."""
    return list_traces()


@app.get("/system/config")
def get_system_config() -> dict[str, str | float | int]:
    """Return read-only system configurations and thresholds for dashboard display."""
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "reranker_model": settings.reranker_model,
        "confidence_threshold": settings.confidence_threshold,
        "verification_threshold": settings.verification_threshold,
        "drift_threshold": settings.drift_threshold,
        "max_reflection_attempts": settings.max_reflection_attempts,
        "bm25_top_k": settings.bm25_top_k,
        "dense_top_k": settings.dense_top_k,
        "rerank_top_k": settings.rerank_top_k,
    }
