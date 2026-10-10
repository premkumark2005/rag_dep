import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
  Paper,
} from "@mui/material";
import { AltRoute, CheckCircle, AutoFixHigh } from "@mui/icons-material";
import type { RoutingResult } from "../types/trace";

interface ConfidenceGateSectionProps {
  routing: RoutingResult;
}

export const ConfidenceGateSection: React.FC<ConfidenceGateSectionProps> = ({
  routing,
}) => {
  const isApplicable = routing && (routing as any).applicable !== false && !!routing.decision;

  if (!isApplicable) {
    return (
      <Card
        id="confidence_gate"
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
                <AltRoute /> Section 5: Confidence Gate Routing Layer
              </Typography>
              <Typography variant="caption" sx={{ color: "#64748b" }}>
                Gates high-confidence queries directly to output while routing low-confidence queries to Ultra-Lightweight Reflection.
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
  const passed = routing.decision === "HIGH_CONFIDENCE";

  return (
    <Card
      id="confidence_gate"
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
              <AltRoute /> Section 5: Confidence Gate Routing Layer
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Gates high-confidence queries directly to output while routing low-confidence queries to Ultra-Lightweight Reflection.
            </Typography>
          </Box>
        </Box>

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155" }}>
              <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase" }}>
                Confidence Threshold
              </Typography>
              <Typography variant="h5" sx={{ color: "#f8fafc", mt: 0.5, fontWeight: "bold" }}>
                {(routing.threshold * 100).toFixed(0)}%
              </Typography>
            </Paper>
          </Grid>

          <Grid size={{ xs: 12, sm: 4 }}>
            <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: `1px solid ${passed ? "#22c55e" : "#fbbf24"}` }}>
              <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase" }}>
                Gate Decision
              </Typography>
              <Box sx={{ mt: 0.5 }}>
                <Chip
                  icon={passed ? <CheckCircle style={{ color: "#22c55e" }} /> : <AutoFixHigh style={{ color: "#fbbf24" }} />}
                  label={routing.decision}
                  sx={{
                    bgcolor: passed ? "rgba(34, 197, 94, 0.1)" : "rgba(251, 191, 36, 0.1)",
                    color: passed ? "#22c55e" : "#fbbf24",
                    fontWeight: "bold",
                  }}
                />
              </Box>
            </Paper>
          </Grid>

          <Grid size={{ xs: 12, sm: 4 }}>
            <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155" }}>
              <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase" }}>
                Next Action
              </Typography>
              <Typography variant="subtitle1" sx={{ color: "#38bdf8", mt: 0.5, fontWeight: "bold" }}>
                {routing.next_action}
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155", mt: 2 }}>
          <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase", fontWeight: "bold" }}>
            Gate Evaluation Reason:
          </Typography>
          <Typography variant="body2" sx={{ color: "#cbd5e1", mt: 0.5, fontStyle: "italic" }}>
            "{routing.reason}"
          </Typography>
        </Paper>
      </CardContent>
    </Card>
  );
};
