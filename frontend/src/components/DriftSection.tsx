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
import { TrendingFlat, Warning, CheckCircle } from "@mui/icons-material";
import type { SemanticDriftReport } from "../types/trace";

interface DriftSectionProps {
  drift: SemanticDriftReport;
  driftTimeMs: number;
}

export const DriftSection: React.FC<DriftSectionProps> = ({
  drift,
  driftTimeMs,
}) => {
  const isApplicable = drift && (drift as any).applicable !== false && typeof drift.drift_score === "number";

  if (!isApplicable) {
    return (
      <Card
        id="semantic_drift"
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
                <TrendingFlat /> Section 8: Semantic Drift Detector
              </Typography>
              <Typography variant="caption" sx={{ color: "#64748b" }}>
                Ensures reflection candidate answer has not drifted away from original question intent or dropped planner constraints.
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
  const isDrifted = drift.drift_detected;

  return (
    <Card
      id="semantic_drift"
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
              <TrendingFlat /> Section 8: Semantic Drift Detector
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Ensures reflection candidate answer has not drifted away from original question intent or dropped planner constraints.
            </Typography>
          </Box>
          <Chip label={`Time: ${driftTimeMs.toFixed(1)}ms`} size="small" sx={{ bgcolor: "#0f172a", color: "#38bdf8", border: "1px solid #0284c7" }} />
        </Box>

        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155" }}>
              <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase" }}>
                Drift Score
              </Typography>
              <Typography variant="h5" sx={{ color: isDrifted ? "#ef4444" : "#4ade80", mt: 0.5, fontWeight: "bold" }}>
                {drift.drift_score.toFixed(3)}
              </Typography>
            </Paper>
          </Grid>

          <Grid size={{ xs: 12, sm: 6 }}>
            <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: `1px solid ${isDrifted ? "#ef4444" : "#22c55e"}` }}>
              <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase" }}>
                Drift Status
              </Typography>
              <Box sx={{ mt: 0.5 }}>
                <Chip
                  icon={isDrifted ? <Warning style={{ color: "#ef4444" }} /> : <CheckCircle style={{ color: "#22c55e" }} />}
                  label={isDrifted ? "SEMANTIC DRIFT DETECTED" : "NO DRIFT DETECTED"}
                  sx={{
                    bgcolor: isDrifted ? "rgba(239, 68, 68, 0.1)" : "rgba(34, 197, 94, 0.1)",
                    color: isDrifted ? "#ef4444" : "#22c55e",
                    fontWeight: "bold",
                  }}
                />
              </Box>
            </Paper>
          </Grid>
        </Grid>

        <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155", mb: 2 }}>
          <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase", fontWeight: "bold" }}>
            Drift Analysis Reason:
          </Typography>
          <Typography variant="body2" sx={{ color: "#cbd5e1", mt: 0.5, fontStyle: "italic" }}>
            "{drift.drift_reason}"
          </Typography>
        </Paper>

        {drift.added_information && drift.added_information.length > 0 && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="caption" sx={{ color: "#fbbf24", fontWeight: "bold" }}>
              Extraneous / Added Information:
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: "wrap", gap: 1 }}>
              {drift.added_information.map((item, idx) => (
                <Chip key={idx} label={item} size="small" sx={{ bgcolor: "rgba(251, 191, 36, 0.1)", color: "#fbbf24" }} />
              ))}
            </Stack>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
