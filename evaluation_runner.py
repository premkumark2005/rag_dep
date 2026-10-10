"""Evaluation Runner CLI for RAGVerify.

Usage:
    python evaluation_runner.py --system traditional_rag
    python evaluation_runner.py --system always_reflection
    python evaluation_runner.py --system proposed_rag
    python evaluation_runner.py --system all
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.config import settings
from backend.services.rag_service import RAGService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluation_runner")


def run_evaluation(system_name: str, questions: list[dict], rag_service: RAGService, out_file: Path) -> list[dict]:
    """Run evaluation for a single system on the provided questions."""
    logger.info("Starting evaluation for system: %s (%d questions)", system_name, len(questions))
    results = []

    for index, q_item in enumerate(questions, start=1):
        q_id = q_item.get("id", f"Q{index:03d}")
        question_text = q_item.get("question", "")

        logger.info("[%d/%d] System: %s | Question ID: %s | %s", index, len(questions), system_name, q_id, question_text[:60])
        start_t = time.perf_counter()

        try:
            response = rag_service.query_phase2(question=question_text, system=system_name)
            elapsed_ms = (time.perf_counter() - start_t) * 1000

            res_dict = {
                "question_id": q_id,
                "question": question_text,
                "category": q_item.get("category"),
                "system": response.system,
                "answer": response.final_answer,
                "latency_ms": round(response.latency_ms or response.metadata.total_time_ms or elapsed_ms, 3),
                "llm_calls": response.llm_calls,
                "retrieval": response.retrieval.model_dump() if hasattr(response.retrieval, "model_dump") else response.retrieval,
                "confidence": response.confidence.model_dump() if hasattr(response.confidence, "model_dump") and response.confidence is not None else response.confidence,
                "reflection": response.reflection.model_dump() if hasattr(response.reflection, "model_dump") and response.reflection is not None else response.reflection,
                "verification": response.verification.model_dump() if hasattr(response.verification, "model_dump") and response.verification is not None else response.verification,
                "semantic_drift": response.semantic_drift.model_dump() if hasattr(response.semantic_drift, "model_dump") and response.semantic_drift is not None else response.semantic_drift,
                "controller": response.controller.model_dump() if hasattr(response.controller, "model_dump") and response.controller is not None else response.controller,
                "metadata": response.metadata.model_dump() if hasattr(response.metadata, "model_dump") else response.metadata,
            }
        except Exception as exc:
            logger.error("Error evaluating question ID %s on system %s: %s", q_id, system_name, exc)
            res_dict = {
                "question_id": q_id,
                "question": question_text,
                "category": q_item.get("category"),
                "system": system_name,
                "answer": f"ERROR: {exc}",
                "latency_ms": 0.0,
                "llm_calls": 0,
                "error": str(exc),
                "confidence": {"applicable": False},
                "reflection": {"applicable": False},
                "verification": {"applicable": False},
                "semantic_drift": {"applicable": False},
                "controller": {"applicable": False},
            }

        results.append(res_dict)

        # Write results incrementally to output file
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluation Runner for RAGVerify Baseline Comparison.")
    parser.add_argument(
        "--system",
        choices=["traditional_rag", "always_reflection", "proposed_rag", "all"],
        default="all",
        help="Target system to evaluate (traditional_rag, always_reflection, proposed_rag, or all).",
    )
    parser.add_argument(
        "--input",
        default="data/evaluation/evaluation_questions.json",
        help="Path to input evaluation questions JSON file.",
    )
    parser.add_argument(
        "--output_dir",
        default="data/evaluation/results",
        help="Directory to save evaluation results.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Run only the first N evaluation questions.",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("Input file not found: %s", input_path.resolve())
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    if args.limit is not None:
        if args.limit <= 0:
            parser.error("--limit must be greater than 0")
        questions = questions[: args.limit]
        logger.info("--limit %d applied: running %d question(s).", args.limit, len(questions))

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rag_service = RAGService(settings)
    rag_service.ensure_index_loaded()

    systems_to_run = (
        ["traditional_rag", "always_reflection", "proposed_rag"]
        if args.system == "all"
        else [args.system]
    )

    combined_results = {}

    for sys_name in systems_to_run:
        out_file = out_dir / f"{sys_name}_results.json"
        results = run_evaluation(sys_name, questions, rag_service, out_file)
        combined_results[sys_name] = results
        logger.info("Saved %s results (%d entries) to %s", sys_name, len(results), out_file.resolve())

    if args.system == "all":
        combined_file = out_dir / "combined_results.json"
        with open(combined_file, "w", encoding="utf-8") as f:
            json.dump(combined_results, f, indent=2)
        logger.info("Saved combined results for all 3 systems to %s", combined_file.resolve())

    logger.info("Evaluation runner completed successfully.")


if __name__ == "__main__":
    main()
