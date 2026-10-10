import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Tooltip,
  Paper,
} from "@mui/material";
import {
  HelpOutlined,
  CompareArrows,
  FormatListBulleted,
  Create,
  VerifiedUser,
  AltRoute,
  AutoFixHigh,
  FactCheck,
  TrendingFlat,
  Gavel,
  CheckCircleOutlined,
} from "@mui/icons-material";
import type { Phase2QueryResponse } from "../types/trace";

interface PipelineVisualizerProps {
  trace: Phase2QueryResponse;
  onSelectStage?: (stageId: string) => void;
}

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({
  trace,
  onSelectStage,
}) => {
  const isTraditional = trace.system === "traditional_rag";
  const isAlwaysRefl = trace.system === "always_reflection";

  const isHighConfidence = trace.routing && (trace.routing as any).next_action === "RETURN_INITIAL_ANSWER";
  const reflectionExecuted = trace.reflection && (trace.reflection as any).reflection_required;
  const decision = trace.controller && (trace.controller as any).decision ? (trace.controller as any).decision : "N/A";
  const answerType = trace.controller && (trace.controller as any).selected_answer_type ? (trace.controller as any).selected_answer_type : "INITIAL";

  const overallConf = trace.confidence && typeof (trace.confidence as any).overall_confidence === "number"
    ? (trace.confidence as any).overall_confidence
    : null;
  const verifScore = trace.verification && typeof (trace.verification as any).verification_score === "number"
    ? (trace.verification as any).verification_score
    : null;
  const driftScore = trace.semantic_drift && typeof (trace.semantic_drift as any).drift_score === "number"
    ? (trace.semantic_drift as any).drift_score
    : null;

  const planFactsCount = trace.plan && Array.isArray((trace.plan as any).required_facts) ? (trace.plan as any).required_facts.length : 0;
  const planMissingCount = trace.plan && Array.isArray((trace.plan as any).missing_facts) ? (trace.plan as any).missing_facts.length : 0;

  const stages = [
    {
      id: "question",
      title: "User Question",
      icon: <HelpOutlined fontSize="small" />,
      time: null,
      badge: "Input Query ✓",
      color: "#38bdf8",
    },
    {
      id: "retrieval",
      title: isTraditional ? "Dense Retrieval" : "Hybrid Retrieval",
      icon: <CompareArrows fontSize="small" />,
      time: isTraditional
        ? trace.metadata.dense_time_ms
        : trace.metadata.bm25_time_ms + trace.metadata.dense_time_ms + trace.metadata.fusion_time_ms,
      badge: isTraditional
        ? `${trace.retrieval.dense_results.length} Chunks ✓`
        : `${trace.retrieval.hybrid_results.length} Candidates ✓`,
      color: "#818cf8",
    },
    {
      id: "reranking",
      title: "Cross Encoder",
      icon: <CompareArrows fontSize="small" />,
      time: isTraditional || isAlwaysRefl ? 0 : trace.metadata.reranking_time_ms,
      badge: isTraditional || isAlwaysRefl ? "N/A" : `Top-${trace.retrieval.reranked_results.length} Reranked ✓`,
      color: isTraditional || isAlwaysRefl ? "#64748b" : "#a78bfa",
    },
    {
      id: "planning",
      title: "Planning Module",
      icon: <FormatListBulleted fontSize="small" />,
      time: isTraditional || isAlwaysRefl ? 0 : trace.metadata.planning_time_ms,
      badge: isTraditional || isAlwaysRefl ? "N/A" : `${planFactsCount} Facts (${planMissingCount} Missing) ✓`,
      color: isTraditional || isAlwaysRefl ? "#64748b" : "#f472b6",
    },
    {
      id: "initial_answer",
      title: isTraditional ? "Answer Generation" : "Initial Answer",
      icon: <Create fontSize="small" />,
      time: trace.metadata.generation_time_ms,
      badge: isTraditional ? "Direct Gen ✓" : "Initial Gen ✓",
      color: "#fb7185",
    },
    {
      id: "confidence",
      title: "Confidence Est.",
      icon: <VerifiedUser fontSize="small" />,
      time: isTraditional || isAlwaysRefl ? 0 : trace.metadata.confidence_time_ms,
      badge: isTraditional || isAlwaysRefl || overallConf === null ? "N/A" : `${(overallConf * 100).toFixed(1)}% Score ✓`,
      color: isTraditional || isAlwaysRefl || overallConf === null ? "#64748b" : overallConf >= 0.7 ? "#4ade80" : "#facc15",
    },
    {
      id: "confidence_gate",
      title: "Confidence Gate",
      icon: <AltRoute fontSize="small" />,
      time: isTraditional || isAlwaysRefl ? 0 : 0.1,
      badge: isTraditional || isAlwaysRefl ? "N/A" : `${(trace.routing as any)?.decision || "N/A"} ✓`,
      color: isTraditional || isAlwaysRefl ? "#64748b" : isHighConfidence ? "#4ade80" : "#fbbf24",
    },
    {
      id: "reflection",
      title: "Reflection",
      icon: <AutoFixHigh fontSize="small" />,
      time: isTraditional ? 0 : trace.metadata.reflection_time_ms,
      badge: isTraditional ? "N/A" : isAlwaysRefl ? "Mandatory Reflected ✓" : reflectionExecuted ? "Reflected (1 Pass) ✓" : "Bypassed",
      color: isTraditional ? "#64748b" : "#c084fc",
    },
    {
      id: "verification",
      title: "Verification",
      icon: <FactCheck fontSize="small" />,
      time: isTraditional || isAlwaysRefl ? 0 : trace.metadata.verification_time_ms,
      badge: isTraditional || isAlwaysRefl || verifScore === null ? "N/A" : `${(verifScore * 100).toFixed(0)}% Grounded ✓`,
      color: isTraditional || isAlwaysRefl || verifScore === null ? "#64748b" : verifScore >= 0.8 ? "#4ade80" : "#f87171",
    },
    {
      id: "semantic_drift",
      title: "Drift Detector",
      icon: <TrendingFlat fontSize="small" />,
      time: isTraditional || isAlwaysRefl ? 0 : trace.metadata.drift_time_ms,
      badge: isTraditional || isAlwaysRefl || driftScore === null ? "N/A" : `Drift ${driftScore.toFixed(2)} ✓`,
      color: isTraditional || isAlwaysRefl || driftScore === null ? "#64748b" : (trace.semantic_drift as any)?.drift_detected ? "#f87171" : "#4ade80",
    },
    {
      id: "controller",
      title: "Controller",
      icon: <Gavel fontSize="small" />,
      time: isTraditional || isAlwaysRefl ? 0 : trace.metadata.controller_time_ms,
      badge: isTraditional || isAlwaysRefl ? "N/A" : `${decision} ✓`,
      color: isTraditional || isAlwaysRefl ? "#64748b" : decision === "RETURN_REFLECTED" ? "#c084fc" : "#38bdf8",
    },
    {
      id: "final_answer",
      title: "Final Answer",
      icon: <CheckCircleOutlined fontSize="small" />,
      time: trace.metadata.total_time_ms,
      badge: `From ${isTraditional ? "INITIAL" : isAlwaysRefl ? "REFLECTED" : answerType} ✓`,
      color: "#22c55e",
    },
  ];

  return (
    <Card
      elevation={2}
      sx={{
        bgcolor: "#1e293b",
        color: "#f8fafc",
        borderRadius: 3,
        border: "1px solid #334155",
        mb: 3,
      }}
    >
      <CardContent sx={{ pb: 2 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Typography variant="h6" sx={{ color: "#38bdf8", fontWeight: "bold" }}>
            End-to-End Pipeline Execution Trace
          </Typography>
          <Typography variant="caption" sx={{ color: "#94a3b8" }}>
            Total: <strong style={{ color: "#38bdf8" }}>{trace.metadata.total_time_ms.toFixed(1)} ms</strong>
          </Typography>
        </Box>

        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            overflowX: "auto",
            py: 1,
            px: 0.5,
            "::-webkit-scrollbar": { height: 6 },
            "::-webkit-scrollbar-thumb": { bgcolor: "#334155", borderRadius: 3 },
          }}
        >
          {stages.map((stage, idx) => (
            <React.Fragment key={stage.id}>
              <Tooltip title={`Click to view ${stage.title} details`}>
                <Paper
                  elevation={0}
                  onClick={() => onSelectStage && onSelectStage(stage.id)}
                  sx={{
                    minWidth: 130,
                    p: 1.2,
                    bgcolor: "#0f172a",
                    border: `1px solid ${stage.color}`,
                    borderRadius: 2,
                    cursor: "pointer",
                    transition: "transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out",
                    "&:hover": {
                      transform: "translateY(-3px)",
                      boxShadow: `0 4px 12px ${stage.color}40`,
                    },
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 0.5 }}>
                    <Box sx={{ color: stage.color, display: "flex", alignItems: "center" }}>
                      {stage.icon}
                    </Box>
                    <Typography variant="caption" sx={{ color: "#94a3b8", ml: "auto", fontSize: "0.7rem" }}>
                      {stage.time !== null ? `${stage.time.toFixed(0)} ms` : "0 ms"}
                    </Typography>
                  </Box>

                  <Typography
                    variant="body2"
                    noWrap
                    sx={{ color: "#f8fafc", fontSize: "0.8rem", mb: 0.5, fontWeight: "bold" }}
                  >
                    {stage.title}
                  </Typography>

                  <Chip
                    label={stage.badge}
                    size="small"
                    sx={{
                      height: 18,
                      fontSize: "0.65rem",
                      fontWeight: "bold",
                      bgcolor: `${stage.color}20`,
                      color: stage.color,
                      border: `1px solid ${stage.color}40`,
                    }}
                  />
                </Paper>
              </Tooltip>

              {idx < stages.length - 1 && (
                <Typography variant="body2" sx={{ color: "#475569", fontWeight: "bold", flexShrink: 0 }}>
                  →
                </Typography>
              )}
            </React.Fragment>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};
