import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  Chip,
  Stack,
  Alert,
} from "@mui/material";
import { AutoFixHigh, ErrorOutlined } from "@mui/icons-material";

import type { ReflectionReport } from "../types/trace";

interface ReflectionSectionProps {
  reflection: ReflectionReport;
  reflectionTimeMs: number;
}

export const ReflectionSection: React.FC<ReflectionSectionProps> = ({
  reflection,
  reflectionTimeMs,
}) => {
  const isApplicable = reflection && (reflection as any).applicable !== false;

  if (!isApplicable) {
    return (
      <Card
        id="reflection"
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
                <AutoFixHigh /> Section 6: Ultra-Lightweight Reflection Module
              </Typography>
              <Typography variant="caption" sx={{ color: "#64748b" }}>
                Executes exactly ONCE for low-confidence queries to revise answers using grounded reflection prompts without iterative loops.
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
  const executed = reflection.reflection_required;

  return (
    <Card
      id="reflection"
      elevation={2}
      sx={{
        bgcolor: "#1e293b",
        color: "#f8fafc",
        borderRadius: 3,
        border: `1px solid ${executed ? "#c084fc" : "#334155"}`,
        mb: 3,
      }}
    >
      <CardContent>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Box>
            <Typography variant="h6" sx={{ color: "#c084fc", fontWeight: "bold", display: "flex", alignItems: "center", gap: 1 }}>
              <AutoFixHigh /> Section 6: Ultra-Lightweight Reflection Module
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Executes exactly ONCE for low-confidence queries to revise answers using grounded reflection prompts without iterative loops.
            </Typography>
          </Box>
          <Chip
            label={executed ? `Executed (${reflectionTimeMs.toFixed(1)}ms)` : "Bypassed (0ms)"}
            size="small"
            sx={{
              bgcolor: executed ? "rgba(192, 132, 252, 0.1)" : "#0f172a",
              color: executed ? "#c084fc" : "#64748b",
              border: `1px solid ${executed ? "#c084fc" : "#334155"}`,
            }}
          />
        </Box>

        {!executed ? (
          <Alert severity="info" sx={{ bgcolor: "#0f172a", color: "#94a3b8", border: "1px solid #334155" }}>
            Reflection was bypassed because the initial answer passed the high-confidence gate threshold.
          </Alert>
        ) : (
          <Box>
            <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155", mb: 2 }}>
              <Typography variant="caption" sx={{ color: "#c084fc", textTransform: "uppercase", fontWeight: "bold" }}>
                Reflection Diagnosis & Reason:
              </Typography>
              <Typography variant="body2" sx={{ color: "#cbd5e1", mt: 0.5 }}>
                {reflection.reflection_reason}
              </Typography>
            </Paper>

            {reflection.identified_problems.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: "#e2e8f0", mb: 1, fontWeight: "bold" }}>
                  Identified Quality Issues:
                </Typography>
                <Stack spacing={1}>
                  {reflection.identified_problems.map((prob, idx) => (
                    <Paper key={idx} sx={{ p: 1.5, bgcolor: "#0f172a", border: "1px solid #f59e0b", display: "flex", alignItems: "center", gap: 1.5 }}>
                      <ErrorOutlined style={{ color: "#f59e0b" }} />
                      <Box>

                        <Typography variant="body2" sx={{ color: "#f59e0b", fontWeight: "bold" }}>
                          [{prob.problem_type}] {prob.description}
                        </Typography>
                        <Typography variant="caption" sx={{ color: "#64748b" }}>
                          Severity: {prob.severity}
                        </Typography>
                      </Box>
                    </Paper>
                  ))}
                </Stack>
              </Box>
            )}

            <Typography variant="subtitle2" sx={{ color: "#c084fc", mb: 1, fontWeight: "bold" }}>
              Candidate Revised Answer:
            </Typography>
            <Paper sx={{ p: 2.5, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #c084fc" }}>
              <Typography variant="body1" sx={{ color: "#f8fafc", whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
                {reflection.candidate_answer || "No candidate answer generated."}
              </Typography>
            </Paper>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
