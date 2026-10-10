export interface BM25Chunk {
  rank: number;
  chunk_id: string;
  document_id: string;
  title: string;
  text: string;
  source: string;
  chunk_index: number;
  bm25_score: number;
}

export interface DenseChunk {
  rank: number;
  chunk_id: string;
  document_id: string;
  title: string;
  text: string;
  source: string;
  chunk_index: number;
  score: number;
}

export interface HybridChunk {
  rank: number;
  chunk_id: string;
  document_id: string;
  title: string;
  text: string;
  source: string;
  chunk_index: number;
  bm25_rank?: number | null;
  bm25_score?: number | null;
  dense_rank?: number | null;
  dense_score?: number | null;
  rrf_score: number;
}

export interface RerankedChunk {
  rerank_rank: number;
  chunk_id: string;
  document_id: string;
  title: string;
  text: string;
  source: string;
  chunk_index: number;
  reranker_raw_score: number;
  bm25_rank?: number | null;
  bm25_score?: number | null;
  dense_rank?: number | null;
  dense_score?: number | null;
  rrf_score: number;
}

export interface FactEvidence {
  chunk_id: string;
  document_id: string;
  supported_fact: string;
}

export interface RequiredFact {
  fact_id: string;
  requirement: string;
  status: "FOUND" | "MISSING" | "CONFLICTING";
  evidence: FactEvidence[];
}

export interface PlanOutput {
  applicable?: boolean;
  question_intent: string;
  required_facts: RequiredFact[];
  missing_facts: string[];
  conflicting_facts: string[];
  answer_instruction: string;
}

export interface RetrievalConfidenceResult {
  retrieval_confidence: number;
  top_document_raw_score: number;
  top_document_normalized_score: number;
  average_top_k_raw_score: number;
  average_top_k_normalized_score: number;
}

export interface ClaimSupportScore {
  claim: string;
  best_chunk_id: string;
  similarity_score: number;
}

export interface EvidenceSupportResult {
  evidence_support: number;
  claim_scores: ClaimSupportScore[];
}

export interface FactCoverageResult {
  fact_coverage: number;
  covered_facts: string[];
  missing_facts: string[];
}

export interface Contradiction {
  claim_1: string;
  claim_2: string;
  reason: string;
}

export interface AnswerConsistencyResult {
  answer_consistency: number;
  contradictions: Contradiction[];
}

export interface EvidenceAgreementResult {
  evidence_agreement: number;
  conflicting_chunk_ids: string[];
  conflicting_facts: string[];
}

export interface ConfidenceResult {
  applicable?: boolean;
  retrieval_confidence: number;
  evidence_support: number;
  fact_coverage: number;
  answer_consistency: number;
  evidence_agreement: number;
  overall_confidence: number;
  component_scores: Record<string, number>;
  retrieval_details: RetrievalConfidenceResult;
  support_details: EvidenceSupportResult;
  coverage_details: FactCoverageResult;
  consistency_details: AnswerConsistencyResult;
  agreement_details: EvidenceAgreementResult;
}

export interface RoutingResult {
  applicable?: boolean;
  decision: "HIGH_CONFIDENCE" | "LOW_CONFIDENCE";
  next_action: "RETURN_INITIAL_ANSWER" | "REFLECTION_REQUIRED";
  overall_confidence: number;
  threshold: number;
  reason: string;
  major_contributors: string[];
}

export interface ProblemItem {
  problem_type: string;
  description: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
}

export interface ReflectionReport {
  applicable?: boolean;
  triggered?: boolean;
  reflection_required: boolean;
  reflection_reason: string;
  identified_problems: ProblemItem[];
  missing_facts: string[];
  unsupported_claims: string[];
  candidate_answer: string | null;
  reflection_summary: string;
}

export interface VerifiedClaimItem {
  claim_id: string;
  claim_text: string;
  status: "SUPPORTED" | "UNSUPPORTED" | "CONTRADICTED";
  supporting_chunks?: string[];
  contradicting_chunks?: string[];
  confidence?: number;
}

export interface VerificationReport {
  applicable?: boolean;
  verified_claims: VerifiedClaimItem[];
  supported_claims: string[];
  unsupported_claims: string[];
  contradicted_claims: string[];
  verification_score: number;
}

export interface SemanticDriftReport {
  applicable?: boolean;
  drift_detected: boolean;
  drift_score: number;
  drift_reason: string;
  changed_intent?: string | null;
  added_information?: string[];
  removed_information?: string[];
}

export interface ControllerMetrics {
  confidence: number;
  verification: number;
  drift: number;
  verification_threshold: number;
  drift_threshold: number;
  decision_latency_ms: number;
}

export interface ControllerResult {
  applicable?: boolean;
  decision: "RETURN_INITIAL" | "RETURN_REFLECTED" | "REFLECT_AGAIN" | "RETRIEVE_MORE" | "INSUFFICIENT_INFORMATION";
  reason: string;
  selected_answer: string;
  selected_answer_type: "INITIAL" | "REFLECTED" | "NONE";
  metrics: ControllerMetrics;
  reflection_retry: boolean;
  retrieval_retry: boolean;
  final_status: string;
}

export interface Phase2Metadata {
  bm25_time_ms: number;
  dense_time_ms: number;
  fusion_time_ms: number;
  reranking_time_ms: number;
  planning_time_ms: number;
  generation_time_ms: number;
  confidence_time_ms: number;
  reflection_time_ms: number;
  verification_time_ms: number;
  drift_time_ms: number;
  controller_time_ms: number;
  total_time_ms: number;
  bm25_top_k: number;
  dense_top_k: number;
  rerank_top_k: number;
}

export interface Phase2RetrievalTrace {
  bm25_results: BM25Chunk[];
  dense_results: DenseChunk[];
  hybrid_results: HybridChunk[];
  reranked_results: RerankedChunk[];
}

export interface Phase2QueryResponse {
  request_id: string;
  question_id?: string;
  system?: "traditional_rag" | "always_reflection" | "proposed_rag" | string;
  llm_calls?: number;
  latency_ms?: number;
  question: string;
  retrieval: Phase2RetrievalTrace;
  plan: PlanOutput;
  initial_answer: string;
  candidate_answer?: string | null;
  confidence: ConfidenceResult;
  routing: RoutingResult;
  reflection: ReflectionReport;
  verification: VerificationReport;
  semantic_drift: SemanticDriftReport;
  controller: ControllerResult;
  final_answer: string;
  metadata: Phase2Metadata;
}

export interface SystemConfig {
  llm_provider: string;
  llm_model: string;
  embedding_model: string;
  reranker_model: string;
  confidence_threshold: number;
  verification_threshold: number;
  drift_threshold: number;
  max_reflection_attempts: number;
  bm25_top_k: number;
  dense_top_k: number;
  rerank_top_k: number;
}

export interface TraceSummary {
  request_id: string;
  question: string;
  system?: string;
  final_answer: string;
  decision: string;
}
