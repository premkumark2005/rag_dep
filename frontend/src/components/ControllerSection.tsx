import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import { Gavel } from "@mui/icons-material";
import type { ControllerResult } from "../types/trace";

interface ControllerSectionProps {
  controller: ControllerResult;
  controllerTimeMs: number;
}

export const ControllerSection: React.FC<ControllerSectionProps> = ({
  controller,
  controllerTimeMs,
}) => {
  const isApplicable = controller && (controller as any).applicable !== false && !!controller.decision;

  if (!isApplicable) {
    return (
      <Card
        id="controller"
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
                <Gavel /> Section 9: Dynamic Reflection Controller
              </Typography>
              <Typography variant="caption" sx={{ color: "#64748b" }}>
                Final arbiter pipeline module. Evaluates confidence, verification, and drift scores to select optimal answer.
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
  const isReflected = controller.decision === "RETURN_REFLECTED";
  const isInitial = controller.decision === "RETURN_INITIAL";

  const getDecisionColor = () => {
    if (isReflected) return "#c084fc";
    if (isInitial) return "#38bdf8";
    return "#ef4444";
  };

  return (
    <Card
      id="controller"
      elevation={2}
      sx={{
        bgcolor: "#1e293b",
        color: "#f8fafc",
        borderRadius: 3,
        border: `2px solid ${getDecisionColor()}`,
        mb: 3,
      }}
    >
      <CardContent>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Box>
            <Typography variant="h6" sx={{ color: getDecisionColor(), fontWeight: "bold", display: "flex", alignItems: "center", gap: 1 }}>
              <Gavel /> Section 9: Dynamic Reflection Controller
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Final arbiter pipeline module. Evaluates confidence, verification, and drift scores to select optimal answer.
            </Typography>
          </Box>
          <Chip label={`Controller Time: ${controllerTimeMs.toFixed(2)}ms`} size="small" sx={{ bgcolor: "#0f172a", color: getDecisionColor(), border: `1px solid ${getDecisionColor()}` }} />
        </Box>

        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: `1px solid ${getDecisionColor()}` }}>
              <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase" }}>
                Controller Final Decision
              </Typography>
              <Typography variant="h6" sx={{ color: getDecisionColor(), mt: 0.5, fontWeight: "bold" }}>
                {controller.decision}
              </Typography>
            </Paper>
          </Grid>

          <Grid size={{ xs: 12, sm: 4 }}>
            <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155" }}>
              <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase" }}>
                Selected Answer Type
              </Typography>
              <Typography variant="h6" sx={{ color: "#f8fafc", mt: 0.5, fontWeight: "bold" }}>
                {controller.selected_answer_type}
              </Typography>
            </Paper>
          </Grid>

          <Grid size={{ xs: 12, sm: 4 }}>
            <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155" }}>
              <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase" }}>
                Final Status Code
              </Typography>
              <Box sx={{ mt: 0.5 }}>
                <Chip
                  label={controller.final_status}
                  size="small"
                  sx={{ bgcolor: `${getDecisionColor()}20`, color: getDecisionColor(), fontWeight: "bold" }}
                />
              </Box>
            </Paper>
          </Grid>
        </Grid>

        <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155", mb: 2 }}>
          <Typography variant="caption" sx={{ color: "#64748b", textTransform: "uppercase", fontWeight: "bold" }}>
            Controller Rationale:
          </Typography>
          <Typography variant="body2" sx={{ color: "#e2e8f0", mt: 0.5, fontStyle: "italic", lineHeight: 1.5 }}>
            "{controller.reason}"
          </Typography>
        </Paper>

        <Typography variant="subtitle2" sx={{ color: "#e2e8f0", mb: 1, fontWeight: "bold" }}>
          Decision Engine Signals & Threshold Evaluation Table:
        </Typography>

        <TableContainer component={Paper} sx={{ bgcolor: "#0f172a", border: "1px solid #334155" }}>
          <Table size="small">
            <TableHead sx={{ bgcolor: "#1e293b" }}>
              <TableRow>
                <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Metric Signal</TableCell>
                <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Measured Value</TableCell>
                <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Configured Threshold</TableCell>
                <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Evaluation Outcome</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell sx={{ color: "#f8fafc" }}>Overall Confidence</TableCell>
                <TableCell sx={{ color: "#38bdf8", fontWeight: "bold" }}>{(controller.metrics.confidence * 100).toFixed(1)}%</TableCell>
                <TableCell sx={{ color: "#94a3b8" }}>70.0%</TableCell>
                <TableCell sx={{ color: controller.metrics.confidence >= 0.7 ? "#4ade80" : "#fbbf24" }}>
                  {controller.metrics.confidence >= 0.7 ? "Gate Passed (Skip Reflection)" : "Low Confidence (Reflection Triggered)"}
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ color: "#f8fafc" }}>Evidence Verification Score</TableCell>
                <TableCell sx={{ color: "#38bdf8", fontWeight: "bold" }}>{(controller.metrics.verification * 100).toFixed(1)}%</TableCell>
                <TableCell sx={{ color: "#94a3b8" }}>{(controller.metrics.verification_threshold * 100).toFixed(1)}%</TableCell>
                <TableCell sx={{ color: controller.metrics.verification >= controller.metrics.verification_threshold ? "#4ade80" : "#f87171" }}>
                  {controller.metrics.verification >= controller.metrics.verification_threshold ? "Verification Passed ✅" : "Verification Failed ❌"}
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ color: "#f8fafc" }}>Semantic Drift Score</TableCell>
                <TableCell sx={{ color: "#38bdf8", fontWeight: "bold" }}>{controller.metrics.drift.toFixed(3)}</TableCell>
                <TableCell sx={{ color: "#94a3b8" }}>{controller.metrics.drift_threshold.toFixed(2)}</TableCell>
                <TableCell sx={{ color: controller.metrics.drift <= controller.metrics.drift_threshold ? "#4ade80" : "#f87171" }}>
                  {controller.metrics.drift <= controller.metrics.drift_threshold ? "Low Drift (Safe) ✅" : "High Drift (Rejected) ❌"}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};
