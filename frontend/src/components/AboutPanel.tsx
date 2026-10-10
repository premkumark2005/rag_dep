import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Paper,
  Divider,
} from "@mui/material";
import { AutoAwesome, Security, School } from "@mui/icons-material";

export const AboutPanel: React.FC = () => {
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
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2 }}>
          <School sx={{ fontSize: 36, color: "#38bdf8" }} />
          <Box>
            <Typography variant="h5" sx={{ color: "#f8fafc", fontWeight: "bold" }}>
              Confidence-Gated Ultra-Lightweight Reflection RAG Architecture
            </Typography>
            <Typography variant="subtitle2" sx={{ color: "#94a3b8" }}>
              Final Year Project & Research Demonstration Framework
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ borderColor: "#334155", my: 2 }} />

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 2.5, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155" }}>
              <Typography variant="subtitle1" sx={{ color: "#38bdf8", mb: 1, fontWeight: "bold", display: "flex", alignItems: "center", gap: 1 }}>
                <AutoAwesome fontSize="small" /> Key Technical Contributions
              </Typography>
              <Typography variant="body2" sx={{ color: "#cbd5e1", lineHeight: 1.6 }}>
                1. <strong>Hybrid Retrieval & Re-ranking</strong>: Merges BM25 lexical search and FAISS dense vector search via Reciprocal Rank Fusion (RRF) and Cross-Encoder reranking.<br /><br />
                2. <strong>Evidence-Grounded Planning</strong>: Decomposes query intent into explicit required facts before generating the initial answer.<br /><br />
                3. <strong>Multi-Metric Confidence Gating</strong>: Evaluates retrieval confidence, evidence support, fact coverage, answer consistency, and evidence agreement without calling LLM judges.<br /><br />
                4. <strong>Single-Pass Ultra-Lightweight Reflection</strong>: Solves low-confidence hallucination in exactly ONE single reflection pass (no infinite loops or token bloat).
              </Typography>
            </Paper>
          </Grid>

          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 2.5, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155" }}>
              <Typography variant="subtitle1" sx={{ color: "#4ade80", mb: 1, fontWeight: "bold", display: "flex", alignItems: "center", gap: 1 }}>
                <Security fontSize="small" /> Verification & Decision Control
              </Typography>
              <Typography variant="body2" sx={{ color: "#cbd5e1", lineHeight: 1.6 }}>
                5. <strong>Evidence Verification Engine</strong>: Decomposes candidate answers into independent factual units and verifies each against retrieved evidence chunks ONLY.<br /><br />
                6. <strong>Semantic Drift Detection</strong>: Analyzes intent shift and missing requirement drift between initial and reflected answers.<br /><br />
                7. <strong>Dynamic Reflection Controller</strong>: Final arbiter module that evaluates verification, drift, and confidence scores against configurable thresholds to select the final response with safe fallback handling.
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
