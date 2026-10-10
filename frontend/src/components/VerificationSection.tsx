import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
} from "@mui/material";
import { FactCheck, CheckCircle, Warning, Cancel } from "@mui/icons-material";
import type { VerificationReport } from "../types/trace";

interface VerificationSectionProps {
  verification: VerificationReport;
  verificationTimeMs: number;
}

export const VerificationSection: React.FC<VerificationSectionProps> = ({
  verification,
  verificationTimeMs,
}) => {
  const isApplicable = verification && (verification as any).applicable !== false && typeof verification.verification_score === "number";

  if (!isApplicable) {
    return (
      <Card
        id="verification"
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
                <FactCheck /> Section 7: Evidence Verification Engine
              </Typography>
              <Typography variant="caption" sx={{ color: "#64748b" }}>
                Decomposes candidate answers into independent factual units and verifies each against retrieved evidence chunks ONLY.
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
  const vScore = verification.verification_score;

  return (
    <Card
      id="verification"
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
              <FactCheck /> Section 7: Evidence Verification Engine
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Decomposes candidate answers into independent factual units and verifies each against retrieved evidence chunks ONLY.
            </Typography>
          </Box>
          <Chip label={`Time: ${verificationTimeMs.toFixed(1)}ms`} size="small" sx={{ bgcolor: "#0f172a", color: "#38bdf8", border: "1px solid #0284c7" }} />
        </Box>

        <Paper sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155", mb: 2 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
            <Typography variant="subtitle2" sx={{ color: "#e2e8f0", fontWeight: "bold" }}>
              Verification Score (Supported Claims / Total Claims):
            </Typography>
            <Typography variant="h6" sx={{ color: vScore >= 0.8 ? "#4ade80" : "#f87171", fontWeight: "bold" }}>
              {(vScore * 100).toFixed(1)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={vScore * 100}
            sx={{
              height: 10,
              borderRadius: 5,
              bgcolor: "#1e293b",
              "& .MuiLinearProgress-bar": {
                bgcolor: vScore >= 0.8 ? "#4ade80" : "#f87171",
                borderRadius: 5,
              },
            }}
          />
        </Paper>

        <Typography variant="subtitle2" sx={{ color: "#e2e8f0", mb: 1, fontWeight: "bold" }}>
          Extracted Claims Grounding Breakdown ({verification.verified_claims.length} Claims):
        </Typography>

        <TableContainer component={Paper} sx={{ bgcolor: "#0f172a", border: "1px solid #334155" }}>
          <Table size="small">
            <TableHead sx={{ bgcolor: "#1e293b" }}>
              <TableRow>
                <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Claim ID</TableCell>
                <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Extracted Factual Unit</TableCell>
                <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Status</TableCell>
                <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Supporting Evidence Chunks</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {verification.verified_claims.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} sx={{ color: "#94a3b8", textAlign: "center", py: 3 }}>
                    No factual claims extracted for verification.
                  </TableCell>
                </TableRow>
              ) : (
                verification.verified_claims.map((claim) => {
                  const isSupported = claim.status === "SUPPORTED";
                  const isContradicted = claim.status === "CONTRADICTED";

                  return (
                    <TableRow key={claim.claim_id} sx={{ "&:hover": { bgcolor: "#1e293b" } }}>
                      <TableCell sx={{ color: "#38bdf8", fontFamily: "monospace", fontSize: "0.8rem" }}>
                        {claim.claim_id}
                      </TableCell>
                      <TableCell sx={{ color: "#f8fafc", fontSize: "0.85rem" }}>
                        {claim.claim_text}
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={isSupported ? <CheckCircle style={{ color: "#22c55e" }} /> : isContradicted ? <Cancel style={{ color: "#ef4444" }} /> : <Warning style={{ color: "#f59e0b" }} />}
                          label={claim.status}
                          size="small"
                          sx={{
                            bgcolor: isSupported ? "rgba(34, 197, 94, 0.1)" : isContradicted ? "rgba(239, 68, 68, 0.1)" : "rgba(245, 158, 11, 0.1)",
                            color: isSupported ? "#22c55e" : isContradicted ? "#ef4444" : "#f59e0b",
                            fontWeight: "bold",
                            fontSize: "0.75rem",
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ color: "#cbd5e1", fontSize: "0.8rem", fontFamily: "monospace" }}>
                        {claim.supporting_chunks && claim.supporting_chunks.length > 0 ? (
                          claim.supporting_chunks.join(", ")
                        ) : (
                          <span style={{ color: "#64748b" }}>None</span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};
