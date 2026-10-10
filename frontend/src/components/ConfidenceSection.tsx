import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  LinearProgress,
  Paper,
  Chip,
} from "@mui/material";
import { VerifiedUser, Speed } from "@mui/icons-material";
import type { ConfidenceResult } from "../types/trace";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";

interface ConfidenceSectionProps {
  confidence: ConfidenceResult;
  confidenceTimeMs: number;
}

export const ConfidenceSection: React.FC<ConfidenceSectionProps> = ({
  confidence,
  confidenceTimeMs,
}) => {
  const isApplicable = confidence && (confidence as any).applicable !== false && typeof confidence.overall_confidence === "number";

  if (!isApplicable) {
    return (
      <Card
        id="confidence"
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
              <Typography variant="h6" sx={{ color: "#94a3b8", fontWeight: "bold", display: "flex", alignItems: "center", gap: 1 }}>
                <VerifiedUser /> Section 4: Multi-Metric Confidence Estimator
              </Typography>
              <Typography variant="caption" sx={{ color: "#64748b" }}>
                Computes 5 non-LLM composite confidence sub-scores to determine overall hallucination risk.
              </Typography>
            </Box>
            <Chip label="N/A" size="small" sx={{ bgcolor: "#0f172a", color: "#94a3b8", border: "1px solid #334155" }} />
          </Box>
          <Paper sx={{ p: 2.5, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155" }}>
            <Typography variant="body2" sx={{ color: "#94a3b8", fontStyle: "italic" }}>
              Not applicable
            </Typography>
          </Paper>
        </CardContent>
      </Card>
    );
  }
  const getScoreColor = (val: number) => {
    if (val >= 0.7) return "#4ade80";
    if (val >= 0.5) return "#fbbf24";
    return "#f87171";
  };

  const metricsData = [
    { name: "Retrieval Conf", score: confidence.retrieval_confidence },
    { name: "Evidence Support", score: confidence.evidence_support },
    { name: "Fact Coverage", score: confidence.fact_coverage },
    { name: "Answer Consistency", score: confidence.answer_consistency },
    { name: "Evidence Agreement", score: confidence.evidence_agreement },
  ];

  return (
    <Card
      id="confidence"
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
              <VerifiedUser /> Section 4: Multi-Metric Confidence Estimator
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Computes 5 non-LLM composite confidence sub-scores to determine overall hallucination risk.
            </Typography>
          </Box>
          <Chip label={`Time: ${confidenceTimeMs.toFixed(1)}ms`} size="small" sx={{ bgcolor: "#0f172a", color: "#4ade80", border: "1px solid #4ade80" }} />
        </Box>

        <Grid container spacing={3} sx={{ alignItems: "center" }}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Paper
              sx={{
                p: 3,
                bgcolor: "#0f172a",
                borderRadius: 3,
                textAlign: "center",
                border: `2px solid ${getScoreColor(confidence.overall_confidence)}`,
              }}
            >
              <Typography variant="overline" sx={{ color: "#94a3b8", fontWeight: "bold" }}>
                Overall Confidence Score
              </Typography>
              <Typography
                variant="h2"
                sx={{ color: getScoreColor(confidence.overall_confidence), my: 1, fontWeight: "bold" }}
              >
                {(confidence.overall_confidence * 100).toFixed(1)}%
              </Typography>
              <Chip
                icon={<Speed style={{ color: getScoreColor(confidence.overall_confidence) }} />}
                label={
                  confidence.overall_confidence >= 0.7
                    ? "HIGH CONFIDENCE"
                    : confidence.overall_confidence >= 0.5
                    ? "MODERATE CONFIDENCE"
                    : "LOW CONFIDENCE"
                }
                sx={{
                  bgcolor: `${getScoreColor(confidence.overall_confidence)}20`,
                  color: getScoreColor(confidence.overall_confidence),
                  fontWeight: "bold",
                  border: `1px solid ${getScoreColor(confidence.overall_confidence)}`,
                }}
              />
            </Paper>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {metricsData.map((m) => (
                <Box key={m.name}>
                  <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                    <Typography variant="body2" sx={{ color: "#cbd5e1", fontSize: "0.85rem" }}>
                      {m.name}
                    </Typography>
                    <Typography variant="body2" sx={{ color: getScoreColor(m.score), fontWeight: "bold" }}>
                      {(m.score * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(100, Math.max(0, m.score * 100))}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      bgcolor: "#0f172a",
                      "& .MuiLinearProgress-bar": {
                        bgcolor: getScoreColor(m.score),
                        borderRadius: 4,
                      },
                    }}
                  />
                </Box>
              ))}
            </Box>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Box sx={{ height: 200, width: "100%" }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metricsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 9 }} interval={0} />
                  <YAxis domain={[0, 1]} stroke="#64748b" tick={{ fontSize: 9 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc" }}
                    formatter={(val: unknown) => [`${((val as number) * 100).toFixed(1)}%`, "Score"]}
                  />

                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {metricsData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getScoreColor(entry.score)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
