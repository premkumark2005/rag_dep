"""RAG orchestration service for Phase 1 baseline."""

import time

from backend.confidence.confidence_estimator import ConfidenceEstimator
from backend.config import Settings
from backend.generation.generator import AnswerGenerator, PlannedAnswerGenerator
from backend.generation.llm_client import create_llm_client
from backend.ingestion.chunker import chunk_document
from backend.ingestion.document_loader import load_txt_documents
from backend.models.schemas import IngestResponse, Phase2QueryResponse, QueryMetadata, QueryResponse, QueryTrace
from backend.planning.planner import PlanningModule
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.embedding_model import EmbeddingModel
from backend.retrieval.reranker import CrossEncoderReranker
from backend.retrieval.vector_store import FAISSVectorStore
from backend.services.phase2_service import Phase2PipelineService
from backend.utils.logger import get_logger


logger = get_logger(__name__)


class RAGService:
    """Coordinates ingestion, retrieval, and generation."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.vector_store = FAISSVectorStore(settings.faiss_storage_directory)
        self.bm25_retriever = BM25Retriever()
        self._embedder: EmbeddingModel | None = None
        self._retriever: DenseRetriever | None = None
        self._generator: AnswerGenerator | None = None
        self._planned_generator: PlannedAnswerGenerator | None = None
        self._reranker: CrossEncoderReranker | None = None
        self._planner: PlanningModule | None = None
        self._confidence_estimator: ConfidenceEstimator | None = None
        self._phase2_pipeline: Phase2PipelineService | None = None

    @property
    def embedder(self) -> EmbeddingModel:
        if self._embedder is None:
            self._embedder = EmbeddingModel(self.settings.embedding_model)
        return self._embedder

    @property
    def retriever(self) -> DenseRetriever:
        if self._retriever is None:
            self._retriever = DenseRetriever(self.embedder, self.vector_store)
        return self._retriever

    @property
    def generator(self) -> AnswerGenerator:
        if self._generator is None:
            self._generator = AnswerGenerator(create_llm_client(self.settings))
        return self._generator

    @property
    def planned_generator(self) -> PlannedAnswerGenerator:
        if self._planned_generator is None:
            self._planned_generator = PlannedAnswerGenerator(create_llm_client(self.settings))
        return self._planned_generator

    @property
    def reranker(self) -> CrossEncoderReranker:
        if self._reranker is None:
            self._reranker = CrossEncoderReranker(self.settings.reranker_model)
        return self._reranker

    @property
    def planner(self) -> PlanningModule:
        if self._planner is None:
            self._planner = PlanningModule(create_llm_client(self.settings))
        return self._planner

    @property
    def phase2_pipeline(self) -> Phase2PipelineService:
        if self._phase2_pipeline is None:
            self._phase2_pipeline = Phase2PipelineService(
                settings=self.settings,
                dense_retriever=self.retriever,
                bm25_retriever=self.bm25_retriever,
                hybrid_retriever=HybridRetriever(rrf_k=self.settings.rrf_k),
                reranker=self.reranker,
                planner=self.planner,
                planned_generator=self.planned_generator,
                confidence_estimator=self.confidence_estimator,
            )
        return self._phase2_pipeline

    @property
    def confidence_estimator(self) -> ConfidenceEstimator:
        if self._confidence_estimator is None:
            self._confidence_estimator = ConfidenceEstimator(self.settings)
        return self._confidence_estimator

    def ingest_documents(self) -> IngestResponse:
        """Load .txt docs, chunk, embed, build FAISS index, and persist it."""
        documents = load_txt_documents(self.settings.data_directory)
        all_chunks = []
        for doc in documents:
            all_chunks.extend(
                chunk_document(
                    document=doc,
                    chunk_size=self.settings.chunk_size,
                    chunk_overlap=self.settings.chunk_overlap,
                )
            )

        if not all_chunks:
            raise ValueError("No chunks were created from the loaded documents.")

        embeddings = self.embedder.embed_documents([chunk.text for chunk in all_chunks])
        self.vector_store.build_index(all_chunks, embeddings)
        self.vector_store.save_index()
        self.bm25_retriever.build_index(all_chunks)

        return IngestResponse(
            documents_processed=len(documents),
            chunks_created=len(all_chunks),
            index_status="created",
        )

    def ensure_index_loaded(self) -> None:
        """Load persisted index into memory if not already loaded."""
        if self.vector_store.index is None or not self.vector_store.chunks:
            self.vector_store.load_index()
        self.ensure_bm25_loaded()

    def ensure_bm25_loaded(self) -> None:
        """Build BM25 index from loaded chunks if needed."""
        if not self.vector_store.chunks:
            return
        if not self.bm25_retriever.is_ready:
            self.bm25_retriever.build_index(self.vector_store.chunks)

    def query(self, question: str, top_k: int | None = None) -> QueryResponse:
        """Run the full Phase 1 RAG pipeline and preserve intermediate trace."""
        selected_top_k = top_k or self.settings.default_top_k
        if selected_top_k <= 0:
            raise ValueError("top_k must be greater than 0.")
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        self.ensure_index_loaded()

        total_start = time.perf_counter()

        retrieval_start = time.perf_counter()
        retrieved_chunks = self.retriever.retrieve(question, selected_top_k)
        retrieval_time_ms = (time.perf_counter() - retrieval_start) * 1000

        generation_start = time.perf_counter()
        answer = self.generator.generate(question, retrieved_chunks)
        generation_time_ms = (time.perf_counter() - generation_start) * 1000

        total_time_ms = (time.perf_counter() - total_start) * 1000

        metadata = QueryMetadata(
            retrieval_time_ms=round(retrieval_time_ms, 3),
            generation_time_ms=round(generation_time_ms, 3),
            total_time_ms=round(total_time_ms, 3),
            top_k=selected_top_k,
        )
        trace = QueryTrace(
            question=question,
            retrieved_chunks=retrieved_chunks,
            initial_generated_answer=answer,
            metadata=metadata,
        )

        logger.info(
            "Query processed | question=%s | top_k=%d | retrieved=%d | retrieval_ms=%.3f | generation_ms=%.3f | total_ms=%.3f",
            question,
            selected_top_k,
            len(retrieved_chunks),
            metadata.retrieval_time_ms,
            metadata.generation_time_ms,
            metadata.total_time_ms,
        )

        return QueryResponse(
            question=question,
            answer=answer,
            retrieved_chunks=retrieved_chunks,
            metadata=metadata,
            trace=trace,
        )

    def query_phase2(
        self,
        question: str,
        final_context_k: int | None = None,
        system: str = "proposed_rag",
    ) -> Phase2QueryResponse:
        """Run the Phase 2 pipeline while preserving baseline path separately."""
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")
        self.ensure_index_loaded()
        return self.phase2_pipeline.query(question=question, final_context_k=final_context_k, system=system)
