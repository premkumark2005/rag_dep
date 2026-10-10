"""Unit tests for Phase 5 Evidence Verification and Semantic Drift Detection.

Covers:
  - Existing tests (preserved)
  - TEST 1  : Valid abstention
  - TEST 2  : Correct venv answer not contradicted
  - TEST 3  : Absence of evidence is UNSUPPORTED, not CONTRADICTED
  - TEST 4  : Explicit contradiction is CONTRADICTED
  - TEST 5  : Definition restatement → no drift
  - TEST 6  : Actual semantic drift
  - TEST 7  : Concise equivalent answer → no drift
"""

from backend.drift.semantic_drift_detector import SemanticDriftDetector
from backend.models.schemas import FactEvidence, FactStatus, PlanOutput, RequiredFact, RerankedChunk
from backend.verification.claim_extractor import ClaimExtractor
from backend.verification.evidence_verifier import EvidenceVerifier
from backend.verification.schemas import ClaimStatus
from backend.verification.verification_service import VerificationService


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _chunk(chunk_id: str, text: str, doc_id: str = "doc_1") -> RerankedChunk:
    return RerankedChunk(
        rerank_rank=1,
        chunk_id=chunk_id,
        document_id=doc_id,
        title="python",
        text=text,
        source="python.txt",
        chunk_index=0,
        reranker_raw_score=0.9,
        rrf_score=0.1,
    )


def _dummy_evidence() -> list[RerankedChunk]:
    return [_chunk("chunk_1", "Python was created by Guido van Rossum in 1991.")]


def _plan(requirements: list[tuple[str, FactStatus, str]], missing: list[str] | None = None) -> PlanOutput:
    """Build a minimal PlanOutput for testing."""
    facts = [
        RequiredFact(
            fact_id=f"f{i}",
            requirement=req,
            status=status,
            evidence=(
                [FactEvidence(chunk_id="chunk_1", document_id="doc_1", supported_fact=note)]
                if status == FactStatus.FOUND else []
            ),
        )
        for i, (req, status, note) in enumerate(requirements, start=1)
    ]
    return PlanOutput(
        question_intent="Test intent",
        required_facts=facts,
        missing_facts=missing or [],
        conflicting_facts=[],
        answer_instruction="Answer the question.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Existing tests (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def test_claim_extractor():
    extractor = ClaimExtractor()
    claims = extractor.extract_claims("Python was created by Guido van Rossum and released in 1991.")
    assert len(claims) >= 1
    assert any("Guido" in c.claim_text for c in claims)


def test_verification_service_all_supported():
    service = VerificationService()
    evidence = _dummy_evidence()

    report, latency_ms = service.verify(
        candidate_answer="Python was created by Guido van Rossum.",
        initial_answer="Python created by Guido.",
        evidence=evidence,
    )

    assert report.verification_score == 1.0
    assert len(report.supported_claims) >= 1
    assert len(report.unsupported_claims) == 0
    assert len(report.contradicted_claims) == 0


def test_verification_service_unsupported_and_contradicted():
    verifier = EvidenceVerifier()
    evidence = _dummy_evidence()

    # Contradicted case: Python released in 1985 when evidence says 1991
    claims_contradicted = ClaimExtractor().extract_claims("Python was created by Guido in 1985.")
    items_contradicted = verifier.verify_claims(claims_contradicted, evidence)
    assert any(item.status == ClaimStatus.CONTRADICTED for item in items_contradicted)

    # Unsupported case: Quantum computing features
    claims_unsupported = ClaimExtractor().extract_claims("Quantum computing is natively integrated.")
    items_unsupported = verifier.verify_claims(claims_unsupported, evidence)
    assert any(item.status == ClaimStatus.UNSUPPORTED for item in items_unsupported)


def test_semantic_drift_detector_no_drift():
    detector = SemanticDriftDetector()
    plan = _plan([("Python creator", FactStatus.FOUND, "Guido")])

    report, _ = detector.detect_drift(
        question="Who created Python?",
        plan=plan,
        candidate_answer="Python was created by Guido van Rossum.",
        initial_answer="Guido created Python.",
    )

    assert report.drift_detected is False
    assert report.drift_score < 0.5


def test_semantic_drift_detector_high_drift():
    detector = SemanticDriftDetector()
    # Use multi-token requirements so they are not skipped by the single-token guard
    plan = _plan([
        ("Guido van Rossum creator", FactStatus.FOUND, "Guido"),
        ("Python programming language", FactStatus.FOUND, "Python"),
    ])

    report, _ = detector.detect_drift(
        question="Who created Python?",
        plan=plan,
        candidate_answer="Java was released in 1995 by Sun Microsystems.",
        initial_answer="Guido created Python.",
    )

    assert report.drift_detected is True


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — Valid abstention
# ─────────────────────────────────────────────────────────────────────────────

def test_abstention_is_not_penalised():
    """Abstention answers must not extract any claims and must receive a high
    verification score when the planner confirms a required fact is MISSING."""
    extractor = ClaimExtractor()
    service = VerificationService()

    abstention = (
        "The provided knowledge base does not contain sufficient information "
        "to answer this question about space exploration."
    )

    # ClaimExtractor must return zero claims for an abstention answer.
    claims = extractor.extract_claims(abstention)
    assert claims == [], f"Expected zero claims for abstention, got: {claims}"
    assert extractor.is_abstention(abstention) is True

    # VerificationService must not penalise the abstention when the plan confirms missing facts.
    plan = _plan(
        requirements=[("space exploration Python", FactStatus.MISSING, "")],
        missing=["space exploration Python"],
    )

    evidence: list[RerankedChunk] = []  # no relevant chunks
    report, _ = service.verify(
        candidate_answer=abstention,
        initial_answer=abstention,
        evidence=evidence,
        plan=plan,
    )

    assert report.abstention_detected is True, "abstention_detected should be True"
    assert report.abstention_valid is True, "abstention_valid should be True when planner has MISSING facts"
    assert report.verification_score >= 0.9, f"Score should be high for valid abstention, got {report.verification_score}"
    assert report.contradicted_claims == [], "Abstention must not produce any contradicted claims"


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Correct venv answer is not marked CONTRADICTED
# ─────────────────────────────────────────────────────────────────────────────

def test_venv_answer_not_contradicted():
    """'The venv module.' or 'venv' must not be CONTRADICTED by unrelated evidence."""
    verifier = EvidenceVerifier()

    # Evidence that discusses Python tools in general — no mention of venv specifically
    evidence = [
        _chunk("doc_027", "Python provides tools for creating isolated environments.", "doc_027"),
        _chunk("doc_022", "Package management in Python is handled by pip.", "doc_022"),
    ]

    claims = ClaimExtractor().extract_claims("The venv module is used to create virtual environments.")
    items = verifier.verify_claims(claims, evidence)

    for item in items:
        assert item.status != ClaimStatus.CONTRADICTED, (
            f"Claim '{item.claim_text}' was incorrectly marked CONTRADICTED by evidence "
            f"that does not explicitly contradict it. Contradicting chunks: {item.contradicting_chunks}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — Absence of evidence → UNSUPPORTED, not CONTRADICTED
# ─────────────────────────────────────────────────────────────────────────────

def test_absence_is_unsupported_not_contradicted():
    """Evidence that does not mention venv at all must yield UNSUPPORTED, not CONTRADICTED."""
    verifier = EvidenceVerifier()

    # Completely unrelated evidence — no overlap at all with the venv claim
    evidence = [
        _chunk("chunk_x", "NumPy is a library for numerical computing in Python."),
        _chunk("chunk_y", "Django is a high-level Python web framework."),
    ]

    claims = ClaimExtractor().extract_claims("venv is used to create virtual environments.")
    items = verifier.verify_claims(claims, evidence)

    assert len(items) >= 1
    for item in items:
        assert item.status == ClaimStatus.UNSUPPORTED, (
            f"Expected UNSUPPORTED but got {item.status} for claim: '{item.claim_text}'"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — Explicit contradiction is CONTRADICTED
# ─────────────────────────────────────────────────────────────────────────────

def test_explicit_contradiction_is_detected():
    """Evidence that explicitly names an incompatible fact must trigger CONTRADICTED."""
    verifier = EvidenceVerifier()

    # Year-conflict contradiction: claim says 1991, evidence says 1989
    evidence_year = [_chunk("chunk_1", "Python was first released by Guido in 1989.")]
    claims_year = ClaimExtractor().extract_claims("Python was released in 1991.")
    items_year = verifier.verify_claims(claims_year, evidence_year)
    assert any(item.status == ClaimStatus.CONTRADICTED for item in items_year), (
        "Expected CONTRADICTED for year-conflict claim, got: "
        + str([i.status for i in items_year])
    )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — Definition restatement → drift_detected = False
# ─────────────────────────────────────────────────────────────────────────────

def test_definition_restatement_no_drift():
    """A more detailed restatement of the same fact must not be classified as drift."""
    detector = SemanticDriftDetector()
    plan = _plan([("pip install packages", FactStatus.FOUND, "pip installs packages")])

    report, _ = detector.detect_drift(
        question="What is pip commonly used for?",
        plan=plan,
        candidate_answer=(
            "pip is commonly used to install Python packages from package "
            "indexes such as PyPI."
        ),
        initial_answer="pip is used to install Python packages.",
    )

    assert report.drift_detected is False, (
        f"Expected no drift for a valid elaboration, got drift_score={report.drift_score}, "
        f"reason='{report.drift_reason}'"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6 — Actual semantic drift
# ─────────────────────────────────────────────────────────────────────────────

def test_actual_semantic_drift_detected():
    """A candidate that answers a completely different question must be flagged as drift."""
    detector = SemanticDriftDetector()
    # Multi-token requirements so the guard doesn't skip them
    plan = _plan([
        ("pip install packages", FactStatus.FOUND, "pip installs packages"),
        ("package manager Python", FactStatus.FOUND, "pip is a package manager"),
    ])

    report, _ = detector.detect_drift(
        question="What is pip commonly used for?",
        plan=plan,
        candidate_answer="pip is a Python interpreter used to execute Python programs.",
        initial_answer="pip is used to install Python packages.",
    )

    assert report.drift_detected is True, (
        f"Expected drift for a topic-switching candidate, got drift_score={report.drift_score}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7 — Concise equivalent answer → drift_detected = False
# ─────────────────────────────────────────────────────────────────────────────

def test_concise_equivalent_no_drift():
    """A one-word initial answer expanded to a full sentence should not be flagged as drift."""
    detector = SemanticDriftDetector()
    plan = _plan([("venv virtual environments", FactStatus.FOUND, "venv module")])

    report, _ = detector.detect_drift(
        question="What module can be used to create virtual environments?",
        plan=plan,
        candidate_answer="The venv module is used to create isolated Python environments.",
        initial_answer="venv",
    )

    assert report.drift_detected is False, (
        f"Expected no drift for an equivalent elaborated answer, "
        f"got drift_score={report.drift_score}, reason='{report.drift_reason}'"
    )
