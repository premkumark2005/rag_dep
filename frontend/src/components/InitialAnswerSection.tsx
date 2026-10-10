import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  Chip,
} from "@mui/material";
import { Create } from "@mui/icons-material";

interface InitialAnswerSectionProps {
  initialAnswer: string;
  generationTimeMs: number;
}

export const InitialAnswerSection: React.FC<InitialAnswerSectionProps> = ({
  initialAnswer,
  generationTimeMs,
}) => {
  return (
    <Card
      id="initial_answer"
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
              <Create /> Section 3: Initial Answer Generation
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Initial planned response produced by LLM grounded strictly on retrieved reranked evidence.
            </Typography>
          </Box>
          <Chip label={`Gen Time: ${generationTimeMs.toFixed(1)}ms`} size="small" sx={{ bgcolor: "#0f172a", color: "#fb7185", border: "1px solid #fb7185" }} />
        </Box>

        <Paper sx={{ p: 2.5, bgcolor: "#0f172a", borderRadius: 2, border: "1px solid #334155" }}>
          <Typography variant="body1" sx={{ color: "#f8fafc", whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
            {initialAnswer}
          </Typography>
        </Paper>
      </CardContent>
    </Card>
  );
};
