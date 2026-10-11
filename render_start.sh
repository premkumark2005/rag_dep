
#!/usr/bin/env bash
set -e

echo "Starting document ingestion..."

python -c "
from backend.config import settings
from backend.services.rag_service import RAGService

svc = RAGService(settings)
result = svc.ingest_documents()
print(f'Ingested: {result}')
"

echo "Starting FastAPI..."

exec uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-10000}"
