import React, { useState } from "react";
import {
  Box,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  TextField,
  Button,
  Paper,
  Alert,
  CircularProgress,
} from "@mui/material";
import {
  Dashboard,
  History,
  BarChart,
  Settings,
  Info,
  Search,
  CloudUpload,
} from "@mui/icons-material";
import { ingestDocuments } from "../services/api";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onSearchTrace: (requestId: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  onSearchTrace,
}) => {
  const [searchId, setSearchId] = useState("");
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchId.trim()) {
      onSearchTrace(searchId.trim());
    }
  };

  const handleIngest = async () => {
    setIngestLoading(true);
    setIngestStatus(null);
    try {
      const res = await ingestDocuments();
      setIngestStatus(`Success: Processed ${res.documents_processed} docs (${res.chunks_created} chunks).`);
    } catch (err: any) {
      setIngestStatus(`Error: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setIngestLoading(false);
    }
  };

  const navItems = [
    { id: "dashboard", label: "Pipeline Visualizer", icon: <Dashboard /> },
    { id: "history", label: "Query History", icon: <History /> },
    { id: "metrics", label: "System Metrics", icon: <BarChart /> },
    { id: "settings", label: "System Settings", icon: <Settings /> },
    { id: "about", label: "Architecture & About", icon: <Info /> },
  ];

  return (
    <Box
      sx={{
        width: { xs: "100%", md: 280 },
        bgcolor: "#0f172a",
        borderRight: "1px solid #1e293b",
        p: 2,
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      <Typography variant="overline" sx={{ color: "#64748b", fontWeight: "bold", letterSpacing: 1.2 }}>
        Navigation
      </Typography>

      <List disablePadding>
        {navItems.map((item) => {
          const selected = activeTab === item.id;
          return (
            <ListItemButton
              key={item.id}
              selected={selected}
              onClick={() => setActiveTab(item.id)}
              sx={{
                borderRadius: 1.5,
                mb: 0.5,
                bgcolor: selected ? "#1e293b" : "transparent",
                color: selected ? "#38bdf8" : "#94a3b8",
                "&:hover": {
                  bgcolor: "#1e293b",
                  color: "#f8fafc",
                },
              }}
            >
              <ListItemIcon sx={{ color: selected ? "#38bdf8" : "#64748b", minWidth: 40 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                slotProps={{
                  primary: {
                    sx: { fontSize: "0.9rem", fontWeight: selected ? "bold" : "normal" },
                  },
                }}
              />
            </ListItemButton>
          );
        })}
      </List>

      <Divider sx={{ borderColor: "#1e293b", my: 1 }} />

      <Typography variant="overline" sx={{ color: "#64748b", fontWeight: "bold", letterSpacing: 1.2 }}>
        Trace Lookup
      </Typography>
      <Paper
        component="form"
        onSubmit={handleSearch}
        elevation={0}
        sx={{
          p: 1,
          bgcolor: "#1e293b",
          borderRadius: 2,
          display: "flex",
          gap: 1,
        }}
      >
        <TextField
          size="small"
          placeholder="Enter Request ID..."
          value={searchId}
          onChange={(e) => setSearchId(e.target.value)}
          variant="standard"
          slotProps={{
            input: {
              disableUnderline: true,
              style: { color: "#f8fafc", fontSize: "0.85rem" },
            },
          }}
          sx={{ px: 1, flex: 1 }}
        />
        <Button
          type="submit"
          variant="contained"
          size="small"
          sx={{ bgcolor: "#0284c7", minWidth: 36, px: 1 }}
        >
          <Search fontSize="small" />
        </Button>
      </Paper>

      <Divider sx={{ borderColor: "#1e293b", my: 1 }} />

      <Typography variant="overline" sx={{ color: "#64748b", fontWeight: "bold", letterSpacing: 1.2 }}>
        Data Management
      </Typography>
      <Button
        variant="outlined"
        startIcon={ingestLoading ? <CircularProgress size={16} color="inherit" /> : <CloudUpload />}
        onClick={handleIngest}
        disabled={ingestLoading}
        sx={{
          color: "#cbd5e1",
          borderColor: "#334155",
          textTransform: "none",
          "&:hover": { borderColor: "#38bdf8", color: "#38bdf8" },
        }}
      >
        {ingestLoading ? "Ingesting..." : "Ingest Documents"}
      </Button>

      {ingestStatus && (
        <Alert
          severity={ingestStatus.startsWith("Success") ? "success" : "error"}
          sx={{ fontSize: "0.75rem", py: 0.5, px: 1 }}
        >
          {ingestStatus}
        </Alert>
      )}

      <Box sx={{ mt: "auto", pt: 2 }}>
        <Paper sx={{ p: 1.5, bgcolor: "#1e293b", borderRadius: 2, border: "1px solid #334155" }}>
          <Typography variant="caption" sx={{ color: "#94a3b8", display: "block" }}>
            Final Year Project Evaluation
          </Typography>
          <Typography variant="caption" sx={{ color: "#38bdf8", fontWeight: "bold" }}>
            Dynamic Reflection RAG v7.0
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};
