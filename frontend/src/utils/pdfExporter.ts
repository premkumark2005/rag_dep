import jsPDF from "jspdf";
import type { Phase2QueryResponse } from "../types/trace";

export const exportPdfSummary = (trace: Phase2QueryResponse) => {
  const doc = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  let y = 15;

  // Title Header
  doc.setFillColor(24, 43, 73);
  doc.rect(0, 0, pageWidth, 28, "F");
  
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(16);
  doc.setFont("helvetica", "bold");
  doc.text("RAGVerify: Evaluator Trace Summary", 12, 12);

  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text(`Request ID: ${trace.request_id}  |  Generated: ${new Date().toLocaleString()}`, 12, 20);

  y = 36;
  doc.setTextColor(30, 30, 30);

  // Question Box
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("User Question:", 12, y);
  y += 6;
  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  const splitQuestion = doc.splitTextToSize(trace.question, pageWidth - 24);
  doc.text(splitQuestion, 12, y);
  y += splitQuestion.length * 5 + 4;

  // Final Answer Box
  doc.setFillColor(240, 244, 250);
  doc.setDrawColor(200, 215, 235);
  doc.roundedRect(12, y, pageWidth - 24, 28, 2, 2, "FD");
  
  doc.setFontSize(10);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(15, 60, 120);
  doc.text(`Final Selected Answer (Source: ${trace.controller.selected_answer_type})`, 16, y + 7);
  
  doc.setFontSize(9.5);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(40, 40, 40);
  const splitAnswer = doc.splitTextToSize(trace.final_answer, pageWidth - 32);
  doc.text(splitAnswer.slice(0, 3), 16, y + 14);
  y += 34;

  // Decision Summary Table
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(20, 20, 20);
  doc.text("Pipeline Decision Metrics:", 12, y);
  y += 6;

  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  const metricsData = [
    ["Overall Confidence Score", `${(trace.confidence.overall_confidence * 100).toFixed(1)}%`],
    ["Confidence Gate Decision", `${trace.routing.decision} (${trace.routing.next_action})`],
    ["Reflection Required / Executed", `${trace.reflection.reflection_required ? "Yes (Executed 1 Pass)" : "No (Passed High Conf)"}`],
    ["Verification Score", `${(trace.verification.verification_score * 100).toFixed(1)}% (${trace.verification.supported_claims.length} supported)`],
    ["Semantic Drift Score", `${trace.semantic_drift.drift_score.toFixed(3)} (Drift Detected: ${trace.semantic_drift.drift_detected ? "Yes" : "No"})`],
    ["Controller Decision", `${trace.controller.decision} (${trace.controller.final_status})`],
    ["Total Execution Time", `${trace.metadata.total_time_ms.toFixed(1)} ms`],
  ];

  metricsData.forEach(([label, val], idx) => {
    if (idx % 2 === 0) {
      doc.setFillColor(248, 250, 252);
      doc.rect(12, y - 4, pageWidth - 24, 7, "F");
    }
    doc.setFont("helvetica", "bold");
    doc.text(label, 14, y);
    doc.setFont("helvetica", "normal");
    doc.text(val, 95, y);
    y += 7;
  });

  y += 6;

  // Planning Summary
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("Evidence Planning Breakdown:", 12, y);
  y += 6;

  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text(`Question Intent: ${trace.plan.question_intent}`, 14, y);
  y += 5;
  doc.text(`Required Facts Count: ${trace.plan.required_facts.length}  |  Missing Facts Count: ${trace.plan.missing_facts.length}`, 14, y);
  y += 8;

  // Controller Reason Box
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("Controller Decision Explanation:", 12, y);
  y += 6;
  doc.setFontSize(9);
  doc.setFont("helvetica", "italic");
  const splitReason = doc.splitTextToSize(trace.controller.reason, pageWidth - 24);
  doc.text(splitReason, 14, y);
  y += splitReason.length * 5 + 10;

  // Footer
  doc.setFontSize(8);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(120, 120, 120);
  doc.text("Confidence-Gated Ultra-Lightweight Reflection RAG System — Academic Viva & Evaluation Export", 12, 285);

  doc.save(`RAGVerify_Trace_${trace.request_id}.pdf`);
};
