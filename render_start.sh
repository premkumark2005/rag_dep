#!/bin/bash
# Auto-ingest documents on startup then launch the API
echo "Starting document ingestion..."
python -c "
from backend.config import settings
from backend.services.rag_service import RAGService
svc = RAGService(settings)
result = svc.ingest_documents()
print(f'Ingested: {result}')
"
echo "Starting FastAPI..."
uvicorn backend.main:app --host 0.0.0.0 --port $PORT