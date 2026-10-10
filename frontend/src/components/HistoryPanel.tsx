import React, { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Chip,
  CircularProgress,
} from "@mui/material";
import { History as HistoryIcon, Visibility } from "@mui/icons-material";
import { fetchTraceList } from "../services/api";
import type { TraceSummary } from "../types/trace";

interface HistoryPanelProps {
  onSelectTrace: (requestId: string) => void;
}

export const HistoryPanel: React.FC<HistoryPanelProps> = ({ onSelectTrace }) => {
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [loading, setLoading] = useState(false);

  const loadTraces = async () => {
    setLoading(true);
    try {
      const data = await fetchTraceList();
      setTraces(data);
    } catch (err) {
      console.error("Failed to fetch traces", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTraces();
  }, []);

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
              <HistoryIcon /> Query Trace History
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Reopen any past execution trace by request_id. Traces are stored in-memory without recomputing.
            </Typography>
          </Box>
          <Button size="small" onClick={loadTraces} disabled={loading} sx={{ color: "#38bdf8" }}>
            Refresh List
          </Button>
        </Box>

        {loading ? (
          <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
            <CircularProgress color="primary" />
          </Box>
        ) : (
          <TableContainer component={Paper} sx={{ bgcolor: "#0f172a", border: "1px solid #334155" }}>
            <Table size="small">
              <TableHead sx={{ bgcolor: "#1e293b" }}>
                <TableRow>
                  <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Request ID</TableCell>
                  <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>System</TableCell>
                  <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Question</TableCell>
                  <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Controller Decision</TableCell>
                  <TableCell sx={{ color: "#94a3b8", fontWeight: "bold" }}>Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {traces.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} sx={{ color: "#94a3b8", textAlign: "center", py: 4 }}>
                      No past query traces stored yet. Execute a query above!
                    </TableCell>
                  </TableRow>
                ) : (
                  traces.map((item) => {
                    const sysLabel = item.system === "traditional_rag"
                      ? "Traditional RAG"
                      : item.system === "always_reflection"
                      ? "Always-Reflection RAG"
                      : "Proposed RAG";

                    return (
                      <TableRow key={item.request_id} sx={{ "&:hover": { bgcolor: "#1e293b" } }}>
                        <TableCell sx={{ color: "#38bdf8", fontFamily: "monospace", fontWeight: "bold" }}>
                          {item.request_id}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={sysLabel}
                            size="small"
                            sx={{
                              bgcolor: item.system === "traditional_rag"
                                ? "rgba(148, 163, 184, 0.1)"
                                : item.system === "always_reflection"
                                ? "rgba(192, 132, 252, 0.1)"
                                : "rgba(56, 189, 248, 0.1)",
                              color: item.system === "traditional_rag"
                                ? "#94a3b8"
                                : item.system === "always_reflection"
                                ? "#c084fc"
                                : "#38bdf8",
                              fontWeight: "bold",
                              fontSize: "0.75rem",
                            }}
                          />
                        </TableCell>
                        <TableCell sx={{ color: "#f8fafc", maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {item.question}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={item.decision}
                            size="small"
                            sx={{
                              bgcolor: item.decision === "RETURN_REFLECTED" ? "rgba(192, 132, 252, 0.1)" : "rgba(56, 189, 248, 0.1)",
                              color: item.decision === "RETURN_REFLECTED" ? "#c084fc" : "#38bdf8",
                              fontWeight: "bold",
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<Visibility />}
                            onClick={() => onSelectTrace(item.request_id)}
                            sx={{ color: "#38bdf8", borderColor: "#38bdf8", textTransform: "none", py: 0.2 }}
                          >
                            View Trace
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </CardContent>
    </Card>
  );
};
