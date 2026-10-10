import React, { useState } from "react";
import {
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Box,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
} from "@mui/material";
import { ExpandMore, CompareArrows } from "@mui/icons-material";
import type { Phase2RetrievalTrace, Phase2Metadata } from "../types/trace";

interface RetrievalSectionProps {
  retrieval: Phase2RetrievalTrace;
  metadata: Phase2Metadata;
}

export const RetrievalSection: React.FC<RetrievalSectionProps> = ({
  retrieval,
  metadata,
}) => {
  const [tabIndex, setTabIndex] = useState(3); // Default to Cross-Encoder reranked

  return (
    <Card
      id="retrieval"
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
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2, flexWrap: "wrap" }}>
          <Box>
            <Typography variant="h6" sx={{ color: "#38bdf8", fontWeight: "bold", display: "flex", alignItems: "center", gap: 1 }}>
              <CompareArrows /> Section 1: Hybrid Retrieval & Cross-Encoder Reranking
            </Typography>
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              Combines BM25 lexical search with FAISS dense semantic search via Reciprocal Rank Fusion (RRF), followed by Cross-Encoder scoring.
            </Typography>
          </Box>
          <Box sx={{ display: "flex", gap: 1, my: { xs: 1, sm: 0 } }}>
            <Chip label={`BM25: ${metadata.bm25_time_ms.toFixed(1)}ms`} size="small" sx={{ bgcolor: "#0f172a", color: "#94a3b8" }} />
            <Chip label={`Dense: ${metadata.dense_time_ms.toFixed(1)}ms`} size="small" sx={{ bgcolor: "#0f172a", color: "#94a3b8" }} />
            <Chip label={`Fusion: ${metadata.fusion_time_ms.toFixed(1)}ms`} size="small" sx={{ bgcolor: "#0f172a", color: "#94a3b8" }} />
            <Chip label={`Reranker: ${metadata.reranking_time_ms.toFixed(1)}ms`} size="small" sx={{ bgcolor: "#0f172a", color: "#38bdf8", border: "1px solid #0284c7" }} />
          </Box>
        </Box>

        <Tabs
          value={tabIndex}
          onChange={(_, val) => setTabIndex(val)}
          textColor="inherit"
          indicatorColor="primary"
          sx={{
            borderBottom: "1px solid #334155",
            mb: 2,
            "& .MuiTab-root": { textTransform: "none", color: "#94a3b8" },
            "& .Mui-selected": { color: "#38bdf8", fontWeight: "bold" },
            "& .MuiTabs-indicator": { backgroundColor: "#38bdf8" },
          }}
        >
          <Tab label={`1. BM25 Sparse (${retrieval.bm25_results.length})`} />
          <Tab label={`2. Dense Vector (${retrieval.dense_results.length})`} />
          <Tab label={`3. Hybrid RRF (${retrieval.hybrid_results.length})`} />
          <Tab label={`4. Reranked Evidence (${retrieval.reranked_results.length})`} />
        </Tabs>

        {/* Tab 0: BM25 */}
        {tabIndex === 0 && (
          <Box>
            {retrieval.bm25_results.map((chunk) => (
              <Accordion key={chunk.chunk_id} sx={{ bgcolor: "#0f172a", color: "#f8fafc", mb: 1, border: "1px solid #334155" }}>
                <AccordionSummary expandIcon={<ExpandMore sx={{ color: "#38bdf8" }} />}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexWrap: "wrap", width: "100%" }}>
                    <Chip label={`Rank #${chunk.rank}`} size="small" sx={{ bgcolor: "#1e293b", color: "#38bdf8", fontWeight: "bold" }} />
                    <Typography variant="subtitle2" sx={{ fontWeight: "bold", color: "#f8fafc" }}>
                      {chunk.chunk_id} ({chunk.title})
                    </Typography>
                    <Chip label={`BM25 Score: ${chunk.bm25_score.toFixed(4)}`} size="small" sx={{ bgcolor: "#334155", color: "#e2e8f0", ml: "auto" }} />
                  </Box>
                </AccordionSummary>
                <AccordionDetails sx={{ borderTop: "1px solid #1e293b" }}>
                  <Typography variant="caption" sx={{ color: "#64748b", display: "block", mb: 0.5 }}>
                    Source Document: {chunk.source} | Index: {chunk.chunk_index}
                  </Typography>
                  <Typography variant="body2" sx={{ color: "#cbd5e1", whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: "0.85rem" }}>
                    {chunk.text}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}

        {/* Tab 1: Dense */}
        {tabIndex === 1 && (
          <Box>
            {retrieval.dense_results.map((chunk) => (
              <Accordion key={chunk.chunk_id} sx={{ bgcolor: "#0f172a", color: "#f8fafc", mb: 1, border: "1px solid #334155" }}>
                <AccordionSummary expandIcon={<ExpandMore sx={{ color: "#38bdf8" }} />}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexWrap: "wrap", width: "100%" }}>
                    <Chip label={`Rank #${chunk.rank}`} size="small" sx={{ bgcolor: "#1e293b", color: "#a78bfa", fontWeight: "bold" }} />
                    <Typography variant="subtitle2" sx={{ fontWeight: "bold", color: "#f8fafc" }}>
                      {chunk.chunk_id} ({chunk.title})
                    </Typography>
                    <Chip label={`Cosine Similarity: ${chunk.score.toFixed(4)}`} size="small" sx={{ bgcolor: "#334155", color: "#e2e8f0", ml: "auto" }} />
                  </Box>
                </AccordionSummary>
                <AccordionDetails sx={{ borderTop: "1px solid #1e293b" }}>
                  <Typography variant="caption" sx={{ color: "#64748b", display: "block", mb: 0.5 }}>
                    Source Document: {chunk.source} | Index: {chunk.chunk_index}
                  </Typography>
                  <Typography variant="body2" sx={{ color: "#cbd5e1", whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: "0.85rem" }}>
                    {chunk.text}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}

        {/* Tab 2: Hybrid RRF */}
        {tabIndex === 2 && (
          <Box>
            {retrieval.hybrid_results.map((chunk) => (
              <Accordion key={chunk.chunk_id} sx={{ bgcolor: "#0f172a", color: "#f8fafc", mb: 1, border: "1px solid #334155" }}>
                <AccordionSummary expandIcon={<ExpandMore sx={{ color: "#38bdf8" }} />}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexWrap: "wrap", width: "100%" }}>
                    <Chip label={`RRF #${chunk.rank}`} size="small" sx={{ bgcolor: "#1e293b", color: "#818cf8", fontWeight: "bold" }} />
                    <Typography variant="subtitle2" sx={{ fontWeight: "bold", color: "#f8fafc" }}>
                      {chunk.chunk_id} ({chunk.title})
                    </Typography>
                    <Chip label={`BM25 Rank: ${chunk.bm25_rank ?? "N/A"} | Dense Rank: ${chunk.dense_rank ?? "N/A"}`} size="small" sx={{ bgcolor: "#1e293b", color: "#94a3b8" }} />
                    <Chip label={`RRF Score: ${chunk.rrf_score.toFixed(4)}`} size="small" sx={{ bgcolor: "#0284c7", color: "#ffffff", ml: "auto" }} />
                  </Box>
                </AccordionSummary>
                <AccordionDetails sx={{ borderTop: "1px solid #1e293b" }}>
                  <Typography variant="caption" sx={{ color: "#64748b", display: "block", mb: 0.5 }}>
                    Source: {chunk.source}
                  </Typography>
                  <Typography variant="body2" sx={{ color: "#cbd5e1", whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: "0.85rem" }}>
                    {chunk.text}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}

        {/* Tab 3: Reranked Cross-Encoder Evidence */}
        {tabIndex === 3 && (
          <Box>
            {retrieval.reranked_results.map((chunk) => (
              <Accordion key={chunk.chunk_id} defaultExpanded sx={{ bgcolor: "#0f172a", color: "#f8fafc", mb: 1.5, border: "1px solid #38bdf8" }}>
                <AccordionSummary expandIcon={<ExpandMore sx={{ color: "#38bdf8" }} />}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexWrap: "wrap", width: "100%" }}>
                    <Chip label={`Final Rerank #${chunk.rerank_rank}`} size="small" sx={{ bgcolor: "#0284c7", color: "#ffffff", fontWeight: "bold" }} />
                    <Typography variant="subtitle2" sx={{ fontWeight: "bold", color: "#f8fafc" }}>
                      {chunk.chunk_id} ({chunk.title})
                    </Typography>
                    <Chip label={`Cross-Encoder Score: ${chunk.reranker_raw_score.toFixed(4)}`} size="small" sx={{ bgcolor: "rgba(56, 189, 248, 0.1)", color: "#38bdf8", border: "1px solid #0284c7", ml: "auto" }} />
                  </Box>
                </AccordionSummary>
                <AccordionDetails sx={{ borderTop: "1px solid #1e293b", pt: 1.5 }}>
                  <Box sx={{ display: "flex", gap: 2, mb: 1, flexWrap: "wrap" }}>
                    <Typography variant="caption" sx={{ color: "#94a3b8" }}>
                      BM25 Rank: {chunk.bm25_rank ?? "N/A"}
                    </Typography>
                    <Typography variant="caption" sx={{ color: "#94a3b8" }}>
                      Dense Rank: {chunk.dense_rank ?? "N/A"}
                    </Typography>
                    <Typography variant="caption" sx={{ color: "#94a3b8" }}>
                      RRF Score: {chunk.rrf_score.toFixed(4)}
                    </Typography>
                    <Typography variant="caption" sx={{ color: "#94a3b8" }}>
                      Source Document: {chunk.source}
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ color: "#e2e8f0", bgcolor: "#1e293b", p: 1.5, borderRadius: 1.5, fontFamily: "monospace", fontSize: "0.85rem", lineHeight: 1.5 }}>
                    {chunk.text}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
