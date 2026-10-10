import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Paper,
} from "@mui/material";
import { Settings as SettingsIcon } from "@mui/icons-material";
import type { SystemConfig } from "../types/trace";

interface SettingsPanelProps {
  config: SystemConfig | null;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ config }) => {
  if (!config) return null;

  const items = [
    { label: "Active LLM Provider", value: config.llm_provider.toUpperCase() },
    { label: "LLM Model", value: config.llm_model },
    { label: "Dense Embedding Model", value: config.embedding_model },
    { label: "Cross-Encoder Reranker", value: config.reranker_model },
    { label: "Confidence Gate Threshold", value: `${(config.confidence_threshold * 100).toFixed(0)}%` },
    { label: "Verification Acceptance Threshold", value: `${(config.verification_threshold * 100).toFixed(0)}%` },
    { label: "Semantic Drift Max Threshold", value: config.drift_threshold.toFixed(2) },
    { label: "Max Reflection Attempts", value: `${config.max_reflection_attempts} (Single-Pass)` },
    { label: "BM25 Top-K Candidates", value: config.bm25_top_k },
    { label: "Dense Top-K Candidates", value: config.dense_top_k },
    { label: "Reranker Output Top-K", value: config.rerank_top_k },
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
      <CardContent>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Box>
            <Typography variant="h6" sx={{ color: "#38bdf8", fontWeight: "bold", display: "flex", alignItems: "center", gap: 1 }}>
              <SettingsIcon /> System Hyperparameters & Architecture Settings
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Read-only active system configurations fetched directly from backend settings.
            </Typography>
          </Box>
        </Box>

        <Grid container spacing={2}>
          {items.map((item, idx) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={idx}>
              <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155" }}>
                <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase", fontWeight: "bold" }}>
                  {item.label}
                </Typography>
                <Typography variant="subtitle1" sx={{ color: "#38bdf8", mt: 0.5, fontWeight: "bold" }}>
                  {item.value}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};
