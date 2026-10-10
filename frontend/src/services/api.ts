import axios from "axios";
import type { Phase2QueryResponse, SystemConfig, TraceSummary } from "../types/trace";

const API_BASE_URL = "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const queryPipeline = async (
  question: string,
  final_context_k?: number,
  system: string = "proposed_rag"
): Promise<Phase2QueryResponse> => {
  const response = await api.post<Phase2QueryResponse>("/query/phase2", {
    question,
    final_context_k: final_context_k || undefined,
    system,
  });
  return response.data;
};

export const fetchTrace = async (request_id: string): Promise<Phase2QueryResponse> => {
  const response = await api.get<Phase2QueryResponse>(`/trace/${request_id}`);
  return response.data;
};

export const fetchTraceList = async (): Promise<TraceSummary[]> => {
  const response = await api.get<TraceSummary[]>("/traces");
  return response.data;
};

export const fetchSystemConfig = async (): Promise<SystemConfig> => {
  const response = await api.get<SystemConfig>("/system/config");
  return response.data;
};

export const ingestDocuments = async (): Promise<{ documents_processed: number; chunks_created: number; index_status: string }> => {
  const response = await api.post("/ingest");
  return response.data;
};
