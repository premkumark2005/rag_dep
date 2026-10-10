import React, { useEffect, useState } from "react";
import {
  Box,
  Container,
  CssBaseline,
  ThemeProvider,
  createTheme,
  Alert,
  Snackbar,
} from "@mui/material";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { QuestionPanel } from "./components/QuestionPanel";
import { PipelineVisualizer } from "./components/PipelineVisualizer";
import { RetrievalSection } from "./components/RetrievalSection";
import { PlanningSection } from "./components/PlanningSection";
import { InitialAnswerSection } from "./components/InitialAnswerSection";
import { ConfidenceSection } from "./components/ConfidenceSection";
import { ConfidenceGateSection } from "./components/ConfidenceGateSection";
import { ReflectionSection } from "./components/ReflectionSection";
import { VerificationSection } from "./components/VerificationSection";
import { DriftSection } from "./components/DriftSection";
import { ControllerSection } from "./components/ControllerSection";
import { FinalAnswerSection } from "./components/FinalAnswerSection";
import { MetricsPanel } from "./components/MetricsPanel";
import { HistoryPanel } from "./components/HistoryPanel";
import { SettingsPanel } from "./components/SettingsPanel";
import { AboutPanel } from "./components/AboutPanel";
import { fetchSystemConfig, fetchTrace, queryPipeline } from "./services/api";
import type { Phase2QueryResponse, SystemConfig } from "./types/trace";

const darkTheme = createTheme({
  palette: {
    mode: "dark",
    background: {
      default: "#090d16",
      paper: "#0f172a",
    },
    primary: {
      main: "#38bdf8",
    },
    secondary: {
      main: "#c084fc",
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [currentTrace, setCurrentTrace] = useState<Phase2QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [toast, setToast] = useState<{ message: string; severity: "success" | "error" | "info" } | null>(null);
  const statusTimers = React.useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const cfg = await fetchSystemConfig();
        setConfig(cfg);
      } catch (err) {
        console.error("Failed to load system config", err);
      }
    };
    loadConfig();
  }, []);

  const clearStatusTimers = () => {
    statusTimers.current.forEach(clearTimeout);
    statusTimers.current = [];
  };

  const handleExecuteQuery = async (question: string, contextK?: number, system: string = "proposed_rag") => {
    clearStatusTimers();
    setLoading(true);

    if (system === "traditional_rag") {
      setStatusMessage("Running Dense FAISS Retrieval & Direct Answer Generation...");
    } else if (system === "always_reflection") {
      setStatusMessage("Running Retrieval, Initial Answer Generation & Mandatory Reflection...");
    } else {
      setStatusMessage("Running Hybrid Retrieval (BM25 + Dense FAISS)...");
      statusTimers.current = [
        setTimeout(() => setStatusMessage("Re-ranking Candidates & Planning Required Facts..."), 400),
        setTimeout(() => setStatusMessage("Generating Planned Initial Answer..."), 800),
        setTimeout(() => setStatusMessage("Estimating Multi-Metric Confidence..."), 1200),
        setTimeout(() => setStatusMessage("Evaluating Confidence Gate & Ultra-Lightweight Reflection..."), 1600),
        setTimeout(() => setStatusMessage("Verifying Claims & Detecting Semantic Drift..."), 2000),
        setTimeout(() => setStatusMessage("Executing Dynamic Reflection Controller Decision..."), 2400),
      ];
    }

    try {
      const trace = await queryPipeline(question, contextK, system);
      setCurrentTrace(trace);
      setActiveTab("dashboard");
      setToast({ message: `Query completed! Request ID: ${trace.request_id}`, severity: "success" });
    } catch (err: any) {
      console.error("Query execution failed", err);
      const errMsg = err?.response?.data?.detail || err.message || "Failed to execute query.";
      setToast({ message: `Error: ${errMsg}`, severity: "error" });
    } finally {
      clearStatusTimers();
      setLoading(false);
      setStatusMessage("");
    }
  };


  const handleSearchTrace = async (requestId: string) => {
    setLoading(true);
    try {
      const trace = await fetchTrace(requestId);
      setCurrentTrace(trace);
      setActiveTab("dashboard");
      setToast({ message: `Loaded trace for ${requestId}`, severity: "info" });
    } catch (err: any) {
      const errMsg = err?.response?.data?.detail || "Trace not found.";
      setToast({ message: `Lookup Error: ${errMsg}`, severity: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleScrollToStage = (stageId: string) => {
    const elem = document.getElementById(stageId);
    if (elem) {
      elem.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ minHeight: "100vh", bgcolor: "#090d16", display: "flex", flexDirection: "column" }}>
        <Header config={config} currentTrace={currentTrace} />

        <Box sx={{ display: "flex", flex: 1, flexDirection: { xs: "column", md: "row" } }}>
          <Sidebar
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            onSearchTrace={handleSearchTrace}
          />

          <Box component="main" sx={{ flex: 1, p: { xs: 2, md: 3 }, overflowY: "auto" }}>
            <Container maxWidth="xl" disableGutters>
              {/* Question Panel is always visible on Dashboard */}
              {activeTab === "dashboard" && (
                <>
                  <QuestionPanel
                    onSubmitQuestion={handleExecuteQuery}
                    loading={loading}
                    statusMessage={statusMessage}
                  />

                  {currentTrace && (
                    <>
                      {/* Step-by-Step Interactive Pipeline Flow */}
                      <PipelineVisualizer
                        trace={currentTrace}
                        onSelectStage={handleScrollToStage}
                      />

                      {/* Final Answer Banner */}
                      <FinalAnswerSection trace={currentTrace} />

                      {/* Controller Section */}
                      <ControllerSection
                        controller={currentTrace.controller}
                        controllerTimeMs={currentTrace.metadata.controller_time_ms}
                      />

                      {/* Drift Section */}
                      <DriftSection
                        drift={currentTrace.semantic_drift}
                        driftTimeMs={currentTrace.metadata.drift_time_ms}
                      />

                      {/* Verification Section */}
                      <VerificationSection
                        verification={currentTrace.verification}
                        verificationTimeMs={currentTrace.metadata.verification_time_ms}
                      />

                      {/* Reflection Section */}
                      <ReflectionSection
                        reflection={currentTrace.reflection}
                        reflectionTimeMs={currentTrace.metadata.reflection_time_ms}
                      />

                      {/* Confidence Gate Section */}
                      <ConfidenceGateSection routing={currentTrace.routing} />

                      {/* Confidence Estimator Section */}
                      <ConfidenceSection
                        confidence={currentTrace.confidence}
                        confidenceTimeMs={currentTrace.metadata.confidence_time_ms}
                      />

                      {/* Initial Answer Section */}
                      <InitialAnswerSection
                        initialAnswer={currentTrace.initial_answer}
                        generationTimeMs={currentTrace.metadata.generation_time_ms}
                      />

                      {/* Planning Section */}
                      <PlanningSection
                        plan={currentTrace.plan}
                        planningTimeMs={currentTrace.metadata.planning_time_ms}
                      />

                      {/* Retrieval Section */}
                      <RetrievalSection
                        retrieval={currentTrace.retrieval}
                        metadata={currentTrace.metadata}
                      />
                    </>
                  )}
                </>
              )}

              {activeTab === "history" && (
                <HistoryPanel onSelectTrace={handleSearchTrace} />
              )}

              {activeTab === "metrics" && currentTrace && (
                <MetricsPanel metadata={currentTrace.metadata} />
              )}

              {activeTab === "settings" && (
                <SettingsPanel config={config} />
              )}

              {activeTab === "about" && (
                <AboutPanel />
              )}
            </Container>
          </Box>
        </Box>

        <Snackbar
          open={!!toast}
          autoHideDuration={4000}
          onClose={() => setToast(null)}
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        >
          {toast ? (
            <Alert onClose={() => setToast(null)} severity={toast.severity} sx={{ width: "100%" }}>
              {toast.message}
            </Alert>
          ) : undefined}
        </Snackbar>
      </Box>
    </ThemeProvider>
  );
};

export default App;
