import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import { BarChart as ChartIcon } from "@mui/icons-material";
import type { Phase2Metadata } from "../types/trace";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";

interface MetricsPanelProps {
  metadata: Phase2Metadata;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ metadata }) => {
  const chartData = [
    { stage: "BM25", ms: metadata.bm25_time_ms, fill: "#818cf8" },
    { stage: "Dense", ms: metadata.dense_time_ms, fill: "#818cf8" },
    { stage: "Fusion", ms: metadata.fusion_time_ms, fill: "#818cf8" },
    { stage: "Reranker", ms: metadata.reranking_time_ms, fill: "#a78bfa" },
    { stage: "Planning", ms: metadata.planning_time_ms, fill: "#f472b6" },
    { stage: "Generation", ms: metadata.generation_time_ms, fill: "#fb7185" },
    { stage: "Confidence", ms: metadata.confidence_time_ms, fill: "#4ade80" },
    { stage: "Reflection", ms: metadata.reflection_time_ms, fill: "#c084fc" },
    { stage: "Verification", ms: metadata.verification_time_ms, fill: "#38bdf8" },
    { stage: "Drift", ms: metadata.drift_time_ms, fill: "#fbbf24" },
    { stage: "Controller", ms: metadata.controller_time_ms, fill: "#22c55e" },
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
              <ChartIcon /> System Latency & Performance Metrics
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Granular latency measurement (in ms) across all 11 stages of the RAG pipeline.
            </Typography>
          </Box>
        </Box>

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 7 }}>
            <TableContainer component={Paper} sx={{ bgcolor: "#0f172a", border: "1px solid #334155" }}>
              <Table size="small">
                <TableHead sx={{ bgcolor: "#1e293b" }}>
                  <TableRow>
                    <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Pipeline Stage</TableCell>
                    <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Latency (ms)</TableCell>
                    <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>% of Total Time</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {chartData.map((row) => {
                    const pct = metadata.total_time_ms > 0 ? (row.ms / metadata.total_time_ms) * 100 : 0;
                    return (
                      <TableRow key={row.stage}>
                        <TableCell sx={{ color: "#f8fafc" }}>{row.stage}</TableCell>
                        <TableCell sx={{ color: "#38bdf8", fontWeight: "bold" }}>{row.ms.toFixed(1)} ms</TableCell>
                        <TableCell sx={{ color: "#94a3b8" }}>{pct.toFixed(1)}%</TableCell>
                      </TableRow>
                    );
                  })}
                  <TableRow sx={{ bgcolor: "#1e293b" }}>
                    <TableCell sx={{ color: "#4ade80", fontWeight: "bold" }}>Total Execution Time</TableCell>
                    <TableCell sx={{ color: "#4ade80", fontWeight: "bold" }}>{metadata.total_time_ms.toFixed(1)} ms</TableCell>
                    <TableCell sx={{ color: "#4ade80", fontWeight: "bold" }}>100.0%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>

          <Grid size={{ xs: 12, md: 5 }}>
            <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155", height: 320 }}>
              <Typography variant="subtitle2" sx={{ color: "#e2e8f0", mb: 2, fontWeight: "bold" }}>
                Latency Breakdown per Stage (ms):
              </Typography>
              <ResponsiveContainer width="100%" height="85%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 20, left: 20, bottom: 0 }}>
                  <XAxis type="number" stroke="#64748b" tick={{ fontSize: 9 }} />
                  <YAxis dataKey="stage" type="category" stroke="#64748b" tick={{ fontSize: 9 }} width={65} />
                  <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc" }} />
                  <Bar dataKey="ms" radius={[0, 4, 4, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
