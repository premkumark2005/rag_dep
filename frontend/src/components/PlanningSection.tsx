import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
  Paper,
  Stack,
} from "@mui/material";
import { FormatListBulleted, CheckCircle, Warning, Help } from "@mui/icons-material";
import type { PlanOutput } from "../types/trace";

interface PlanningSectionProps {
  plan: PlanOutput;
  planningTimeMs: number;
}

export const PlanningSection: React.FC<PlanningSectionProps> = ({
  plan,
  planningTimeMs,
}) => {
  const isApplicable = plan && (plan as any).applicable !== false && Array.isArray((plan as any).required_facts);

  if (!isApplicable) {
    return (
      <Card
        id="planning"
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
                <FormatListBulleted /> Section 2: Evidence-Grounded Planning Module
              </Typography>
              <Typography variant="caption" sx={{ color: "#64748b" }}>
                Decomposes user query intent and extracts mandatory required facts from retrieved evidence prior to generation.
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
  return (
    <Card
      id="planning"
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
              <FormatListBulleted /> Section 2: Evidence-Grounded Planning Module
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Decomposes user query intent and extracts mandatory required facts from retrieved evidence prior to generation.
            </Typography>
          </Box>
          <Chip label={`Time: ${planningTimeMs.toFixed(1)}ms`} size="small" sx={{ bgcolor: "#0f172a", color: "#f472b6", border: "1px solid #f472b6" }} />
        </Box>

        <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155", mb: 2 }}>
          <Typography variant="caption" sx={{ color: "#64748b", fontWeight: "bold", textTransform: "uppercase", letterSpacing: 1 }}>
            Identified Question Intent
          </Typography>
          <Typography variant="body1" sx={{ color: "#38bdf8", mt: 0.5 }}>
            "{plan.question_intent}"
          </Typography>
        </Paper>

        <Typography variant="subtitle2" sx={{ color: "#e2e8f0", mb: 1, fontWeight: "bold" }}>
          Required Fact Requirements & Evidence Status:
        </Typography>

        <Grid container spacing={2} sx={{ mb: 2 }}>
          {plan.required_facts.length === 0 ? (
            <Grid size={{ xs: 12 }}>
              <Paper sx={{ p: 2, bgcolor: "#0f172a", border: "1px solid #334155" }}>
                <Typography variant="body2" sx={{ color: "#94a3b8" }}>
                  No explicit required facts decomposed by planner.
                </Typography>
              </Paper>
            </Grid>
          ) : (
            plan.required_facts.map((fact) => {
              const isFound = fact.status === "FOUND";
              const isMissing = fact.status === "MISSING";

              return (
                <Grid size={{ xs: 12, md: 6 }} key={fact.fact_id}>
                  <Paper
                    sx={{
                      p: 2,
                      bgcolor: "#0f172a",
                      borderRadius: 2,
                      border: `1px solid ${isFound ? "#22c55e" : isMissing ? "#ef4444" : "#f59e0b"}`,
                    }}
                  >
                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 1 }}>
                      <Typography variant="subtitle2" sx={{ color: "#f8fafc", fontWeight: "bold" }}>
                        {fact.requirement}
                      </Typography>
                      <Chip
                        icon={isFound ? <CheckCircle style={{ color: "#22c55e" }} /> : isMissing ? <Help style={{ color: "#ef4444" }} /> : <Warning style={{ color: "#f59e0b" }} />}
                        label={fact.status}
                        size="small"
                        sx={{
                          bgcolor: isFound ? "rgba(34, 197, 94, 0.1)" : isMissing ? "rgba(239, 68, 68, 0.1)" : "rgba(245, 158, 11, 0.1)",
                          color: isFound ? "#22c55e" : isMissing ? "#ef4444" : "#f59e0b",
                          fontWeight: "bold",
                        }}
                      />
                    </Box>

                    {fact.evidence.length > 0 ? (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" sx={{ color: "#64748b" }}>
                          Linked Evidence Chunks:
                        </Typography>
                        {fact.evidence.map((ev, idx) => (
                          <Typography key={idx} variant="caption" sx={{ display: "block", color: "#38bdf8", fontFamily: "monospace" }}>
                            • {ev.chunk_id} ({ev.supported_fact})
                          </Typography>
                        ))}
                      </Box>
                    ) : (
                      <Typography variant="caption" sx={{ color: "#ef4444", display: "block" }}>
                        No supporting evidence found in retrieved chunks.
                      </Typography>
                    )}
                  </Paper>
                </Grid>
              );
            })
          )}
        </Grid>

        {plan.missing_facts.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" sx={{ color: "#ef4444", fontWeight: "bold", textTransform: "uppercase" }}>
              Missing Facts Identified:
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: "wrap", gap: 1 }}>
              {plan.missing_facts.map((mf, i) => (
                <Chip key={i} label={mf} size="small" sx={{ bgcolor: "rgba(239, 68, 68, 0.1)", color: "#ef4444", border: "1px solid #ef4444" }} />
              ))}
            </Stack>
          </Box>
        )}

        <Paper sx={{ p: 1.5, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155" }}>
          <Typography variant="caption" sx={{ color: "#64748b", fontWeight: "bold", textTransform: "uppercase" }}>
            Planner Answer Instruction:
          </Typography>
          <Typography variant="body2" sx={{ color: "#cbd5e1", mt: 0.5, fontStyle: "italic" }}>
            "{plan.answer_instruction}"
          </Typography>
        </Paper>
      </CardContent>
    </Card>
  );
};
