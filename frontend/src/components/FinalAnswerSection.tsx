import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  Chip,
} from "@mui/material";
import { CheckCircleOutlined, AutoAwesome } from "@mui/icons-material";
import type { Phase2QueryResponse } from "../types/trace";

interface FinalAnswerSectionProps {
  trace: Phase2QueryResponse;
}

export const FinalAnswerSection: React.FC<FinalAnswerSectionProps> = ({
  trace,
}) => {
  const selectedType = trace.controller && (trace.controller as any).selected_answer_type ? (trace.controller as any).selected_answer_type : "INITIAL";
  const isReflected = selectedType === "REFLECTED";
  const isInitial = selectedType === "INITIAL";

  const systemName = trace.system === "traditional_rag"
    ? "Traditional RAG"
    : trace.system === "always_reflection"
    ? "Always-Reflection RAG"
    : "Proposed RAG";

  return (
    <Card
      id="final_answer"
      elevation={4}
      sx={{
        bgcolor: "#0f172a",
        color: "#f8fafc",
        borderRadius: 3,
        border: "2px solid #22c55e",
        mb: 3,
        boxShadow: "0 8px 24px rgba(34, 197, 94, 0.15)",
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2, flexWrap: "wrap", gap: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <CheckCircleOutlined sx={{ fontSize: 32, color: "#22c55e" }} />
            <Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Typography variant="h6" sx={{ color: "#f8fafc", fontWeight: "bold" }}>
                  Section 10: Final Selected Output Answer
                </Typography>
                <Chip
                  label={systemName}
                  size="small"
                  sx={{ bgcolor: "#38bdf8", color: "#0f172a", fontWeight: "bold", fontSize: "0.75rem" }}
                />
              </Box>
              <Typography variant="caption" sx={{ color: "#94a3b8" }}>
                Verified answer selected for user presentation.
              </Typography>
            </Box>
          </Box>

          <Chip
            icon={<AutoAwesome style={{ color: "#ffffff" }} />}
            label={`Source: ${isReflected ? "Reflected Answer" : isInitial ? "Initial Answer" : "Insufficient Info Fallback"}`}
            sx={{
              bgcolor: isReflected ? "#c084fc" : isInitial ? "#0284c7" : "#ef4444",
              color: "#ffffff",
              fontWeight: "bold",
              fontSize: "0.85rem",
              py: 0.5,
            }}
          />
        </Box>

        <Paper sx={{ p: 3, bgcolor: "#1e293b", borderRadius: 2, border: "1px solid #334155" }}>
          <Typography
            variant="body1"
            sx={{ color: "#f8fafc", fontSize: "1.05rem", lineHeight: 1.7, whiteSpace: "pre-wrap" }}
          >
            {trace.final_answer}
          </Typography>
        </Paper>

        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mt: 2 }}>
          <Typography variant="caption" sx={{ color: "#64748b" }}>
            Request ID: <strong style={{ color: "#38bdf8" }}>{trace.request_id}</strong> | System: <strong style={{ color: "#38bdf8" }}>{systemName}</strong> | LLM Calls: <strong style={{ color: "#c084fc" }}>{trace.llm_calls ?? 1}</strong>
          </Typography>
          <Typography variant="caption" sx={{ color: "#64748b" }}>
            Total Pipeline Latency: <strong style={{ color: "#22c55e" }}>{(trace.latency_ms ?? trace.metadata.total_time_ms).toFixed(1)} ms</strong>
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};
