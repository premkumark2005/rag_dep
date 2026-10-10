import React from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Chip,
  Box,
  Button,
  Tooltip,
} from "@mui/material";
import {
  CheckCircle,
  Download,
  PictureAsPdf,
  Psychology,
  Tune,
} from "@mui/icons-material";
import type { Phase2QueryResponse, SystemConfig } from "../types/trace";
import { exportPdfSummary } from "../utils/pdfExporter";

interface HeaderProps {
  config: SystemConfig | null;
  currentTrace: Phase2QueryResponse | null;
}

export const Header: React.FC<HeaderProps> = ({ config, currentTrace }) => {
  const handleExportJson = () => {
    if (!currentTrace) return;
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(currentTrace, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `trace_${currentTrace.request_id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <AppBar
      position="static"
      elevation={1}
      sx={{
        bgcolor: "#0f172a",
        borderBottom: "1px solid #1e293b",
        px: 1,
      }}
    >
      <Toolbar sx={{ justifyContent: "space-between", flexWrap: "wrap", py: 1 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <Psychology sx={{ fontSize: 32, color: "#38bdf8" }} />
          <Box>
            <Typography variant="h6" sx={{ color: "#f8fafc", fontWeight: "bold", lineHeight: 1.2 }}>
              RAGVerify: Evaluator Dashboard
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Confidence-Gated Ultra-Lightweight Reflection RAG System
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: "flex", flexDirection: "row", flexWrap: "wrap", gap: 1, alignItems: "center", my: { xs: 1, md: 0 } }}>
          <Tooltip title="FastAPI Status">
            <Chip
              icon={<CheckCircle style={{ color: "#4ade80" }} />}
              label="Backend Online"
              size="small"
              sx={{ bgcolor: "rgba(74, 222, 128, 0.1)", color: "#4ade80", border: "1px solid #22c55e" }}
            />
          </Tooltip>

          {config && (
            <>
              <Chip
                label={`LLM: ${config.llm_provider.toUpperCase()} (${config.llm_model})`}
                size="small"
                sx={{ bgcolor: "#1e293b", color: "#e2e8f0" }}
              />
              <Tooltip title="Confidence / Verification / Drift Thresholds">
                <Chip
                  icon={<Tune style={{ color: "#fbbf24" }} />}
                  label={`C:${config.confidence_threshold} V:${config.verification_threshold} D:${config.drift_threshold}`}
                  size="small"
                  sx={{ bgcolor: "#1e293b", color: "#fbbf24" }}
                />
              </Tooltip>
            </>
          )}

          {currentTrace && (
            <Box sx={{ display: "flex", gap: 1 }}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<Download />}
                onClick={handleExportJson}
                sx={{
                  color: "#38bdf8",
                  borderColor: "#38bdf8",
                  textTransform: "none",
                  "&:hover": { bgcolor: "rgba(56, 189, 248, 0.1)" },
                }}
              >
                JSON Trace
              </Button>
              <Button
                variant="contained"
                size="small"
                startIcon={<PictureAsPdf />}
                onClick={() => exportPdfSummary(currentTrace)}
                sx={{
                  bgcolor: "#0284c7",
                  color: "#ffffff",
                  textTransform: "none",
                  "&:hover": { bgcolor: "#0369a1" },
                }}
              >
                PDF Summary
              </Button>
            </Box>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};
