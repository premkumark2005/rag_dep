import React, { useState } from "react";
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Stack,
  Chip,
  Box,
  Slider,
  CircularProgress,
  Collapse,
  FormControl,
  Select,
  MenuItem,
} from "@mui/material";
import { Send, Tune, AutoAwesome } from "@mui/icons-material";

interface QuestionPanelProps {
  onSubmitQuestion: (question: string, contextK?: number, system?: string) => void;
  loading: boolean;
  statusMessage?: string;
}

export const QuestionPanel: React.FC<QuestionPanelProps> = ({
  onSubmitQuestion,
  loading,
  statusMessage,
}) => {
  const [question, setQuestion] = useState("");
  const [contextK, setContextK] = useState<number>(3);
  const [system, setSystem] = useState<string>("proposed_rag");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const sampleQuestions = [
    "Who created Python and when was it first released?",
    "What is FAISS and how is it used in dense vector retrieval?",
    "What are the key benefits of hybrid retrieval over dense-only retrieval?",
    "Explain how cross-encoder reranking improves relevance scoring.",
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !loading) {
      onSubmitQuestion(question.trim(), contextK, system);
    }
  };

  const handleSelectSample = (q: string) => {
    setQuestion(q);
  };

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
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5, flexWrap: "wrap", gap: 1 }}>
          <Typography variant="h6" sx={{ color: "#38bdf8", fontWeight: "bold", display: "flex", alignItems: "center", gap: 1 }}>
            <AutoAwesome fontSize="small" /> Execute RAG Pipeline Query
          </Typography>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Typography variant="caption" sx={{ color: "#94a3b8", fontWeight: "bold" }}>
                System:
              </Typography>
              <FormControl size="small" sx={{ minWidth: 190 }}>
                <Select
                  value={system}
                  onChange={(e) => setSystem(e.target.value)}
                  disabled={loading}
                  sx={{
                    bgcolor: "#0f172a",
                    color: "#38bdf8",
                    fontWeight: "bold",
                    fontSize: "0.85rem",
                    borderRadius: 2,
                    "& .MuiOutlinedInput-notchedOutline": { borderColor: "#334155" },
                    "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: "#38bdf8" },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": { borderColor: "#38bdf8" },
                    "& .MuiSvgIcon-root": { color: "#38bdf8" },
                  }}
                >
                  <MenuItem value="traditional_rag">Traditional RAG</MenuItem>
                  <MenuItem value="always_reflection">Always-Reflection RAG</MenuItem>
                  <MenuItem value="proposed_rag">Proposed RAG</MenuItem>
                </Select>
              </FormControl>
            </Box>

            <Button
              size="small"
              startIcon={<Tune />}
              onClick={() => setShowAdvanced(!showAdvanced)}
              sx={{ color: "#94a3b8", textTransform: "none" }}
            >
              {showAdvanced ? "Hide Controls" : "Pipeline Options"}
            </Button>
          </Box>
        </Box>

        <form onSubmit={handleSubmit}>
          <Box sx={{ display: "flex", gap: 1.5, mb: 2, flexDirection: { xs: "column", sm: "row" } }}>
            <TextField
              fullWidth
              multiline
              rows={2}
              placeholder="Ask a question about the document corpus (e.g. Python creator, FAISS index, RAG pipeline...)"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
              sx={{
                bgcolor: "#0f172a",
                borderRadius: 2,
                "& .MuiOutlinedInput-root": {
                  color: "#f8fafc",
                  "& fieldset": { borderColor: "#334155" },
                  "&:hover fieldset": { borderColor: "#38bdf8" },
                  "&.Mui-focused fieldset": { borderColor: "#38bdf8" },
                },
              }}
            />
            <Button
              type="submit"
              variant="contained"
              disabled={!question.trim() || loading}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Send />}
              sx={{
                bgcolor: "#0284c7",
                color: "#ffffff",
                px: 3,
                py: { xs: 1.5, sm: 0 },
                borderRadius: 2,
                fontWeight: "bold",
                minWidth: 140,
                alignSelf: { sm: "stretch" },
                "&:hover": { bgcolor: "#0369a1" },
              }}
            >
              {loading ? "Running..." : "Evaluate"}
            </Button>
          </Box>

          <Collapse in={showAdvanced}>
            <Box sx={{ p: 2, bgcolor: "#0f172a", borderRadius: 2, mb: 2, border: "1px solid #334155" }}>
              <Typography variant="subtitle2" sx={{ color: "#e2e8f0", mb: 1 }}>
                Reranked Top-K Context Window (final_context_k): {contextK}
              </Typography>
              <Slider
                value={contextK}
                onChange={(_, val) => setContextK(val as number)}
                min={1}
                max={10}
                step={1}
                valueLabelDisplay="auto"
                sx={{ color: "#38bdf8", width: "95%", mx: "auto" }}
              />
            </Box>
          </Collapse>
        </form>

        <Typography variant="caption" sx={{ color: "#94a3b8", display: "block", mb: 1 }}>
          Sample Test Queries for Demonstration & Viva:
        </Typography>
        <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", gap: 1 }}>
          {sampleQuestions.map((q, idx) => (
            <Chip
              key={idx}
              label={q}
              size="small"
              onClick={() => handleSelectSample(q)}
              disabled={loading}
              sx={{
                bgcolor: "#0f172a",
                color: "#cbd5e1",
                border: "1px solid #334155",
                cursor: "pointer",
                "&:hover": { bgcolor: "#334155", color: "#38bdf8" },
              }}
            />
          ))}
        </Stack>

        {loading && statusMessage && (
          <Box sx={{ mt: 2, p: 1.5, bgcolor: "rgba(56, 189, 248, 0.1)", borderRadius: 2, border: "1px solid #0284c7" }}>
            <Typography variant="body2" sx={{ color: "#38bdf8", fontWeight: "medium", display: "flex", alignItems: "center", gap: 1 }}>
              <CircularProgress size={16} color="inherit" /> {statusMessage}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
