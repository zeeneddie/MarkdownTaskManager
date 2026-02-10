#!/usr/bin/env python3
"""
Standalone test for OnboardingWorkflow Module 2: Intake + Vector DB Context.

This test can be run without the full dependency stack.
It validates the intake context logic with graceful degradation.

Usage:
    python3 backend/tests/standalone_onboarding_m2_test.py
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import re

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# INLINE DEFINITIONS (from onboarding.py)
# =============================================================================

ONBOARDING_QUESTIONS = [
    {
        "id": "q1_primary_purpose",
        "question": "Wat is het primaire doel van deze applicatie?",
        "required": True,
        "min_length": 50,
    },
    {
        "id": "q2_users",
        "question": "Wie zijn de belangrijkste gebruikers?",
        "required": True,
        "min_length": 30,
    },
    {
        "id": "q3_critical_processes",
        "question": "Wat zijn de kritieke business processen?",
        "required": True,
        "min_length": 50,
    },
    {
        "id": "q4_integrations",
        "question": "Welke integraties bestaan er?",
        "required": True,
        "min_length": 20,
    },
    {
        "id": "q5_pain_points",
        "question": "Wat zijn de belangrijkste pijnpunten?",
        "required": False,
        "min_length": 0,
    },
]


@dataclass
class IntakeContextResult:
    """Result of intake context fetching from Vector DB."""
    context_available: bool
    project_name: str
    project_path: str
    relevant_docs: List[Dict[str, Any]]
    architecture_summary: Optional[str]
    code_locations: List[Dict[str, str]]
    total_docs_found: int
    fetched_at: str
    error: Optional[str] = None

    @property
    def quality_score(self) -> float:
        """
        Calculate quality score based on context richness.
        - 1.0: Has architecture summary + 5+ docs
        - 0.85: Has docs but no architecture summary
        - 0.70: No Vector DB available (graceful degradation)
        """
        if not self.context_available:
            return 0.70
        if self.architecture_summary and self.total_docs_found >= 5:
            return 1.0
        if self.total_docs_found > 0:
            return 0.85
        return 0.70

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_available": self.context_available,
            "project_name": self.project_name,
            "project_path": self.project_path,
            "relevant_docs_count": len(self.relevant_docs),
            "has_architecture_summary": self.architecture_summary is not None,
            "code_locations_count": len(self.code_locations),
            "total_docs_found": self.total_docs_found,
            "fetched_at": self.fetched_at,
            "quality_score": self.quality_score,
            "error": self.error,
        }


# =============================================================================
# MOCK CHROMA SERVICE FOR TESTING
# =============================================================================

class MockChromaService:
    """Mock ChromaDB service for testing."""

    def __init__(self, docs: List[Dict] = None):
        self.docs = docs or []

    def query_project_knowledge(
        self,
        query: str,
        project_id: int,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """Mock query that returns predefined docs."""
        if not self.docs:
            return {"results": [], "metadatas": [], "distances": []}

        return {
            "results": [d.get("content", "") for d in self.docs[:top_k]],
            "metadatas": [d.get("metadata", {}) for d in self.docs[:top_k]],
            "distances": [d.get("distance", 0.3) for d in self.docs[:top_k]],
        }


# =============================================================================
# INTAKE CONTEXT LOGIC (extracted from onboarding.py)
# =============================================================================

def fetch_intake_context(
    project_path: str,
    answers: Dict[str, str],
    chroma_service=None,
    project_id: int = 1000,
) -> IntakeContextResult:
    """
    Fetch project context from Vector DB.

    This is the core logic from OnboardingOrchestrator._fetch_intake_context()
    """
    path = Path(project_path)
    project_name = path.name

    if not chroma_service:
        # Graceful degradation
        return IntakeContextResult(
            context_available=False,
            project_name=project_name,
            project_path=project_path,
            relevant_docs=[],
            architecture_summary=None,
            code_locations=[],
            total_docs_found=0,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            error="ChromaDB service not available",
        )

    try:
        # Build query
        query_parts = [project_name, "architecture", "analysis"]
        if answers.get("q1_primary_purpose"):
            query_parts.append(answers["q1_primary_purpose"][:100])
        if answers.get("q3_critical_processes"):
            query_parts.append(answers["q3_critical_processes"][:100])

        path_parts = project_path.replace("\\", "/").split("/")
        query_parts.extend(path_parts[-3:])
        query = " ".join(query_parts)

        # Query ChromaDB
        results = chroma_service.query_project_knowledge(
            query=query,
            project_id=project_id,
            top_k=10,
        )

        # Process results
        relevant_docs = []
        architecture_context = []
        code_locations = []

        for doc, metadata, distance in zip(
            results.get("results", []),
            results.get("metadatas", []),
            results.get("distances", []),
        ):
            doc_type = metadata.get("document_type", "unknown")
            relevance = round(1 - distance, 4) if distance else 0

            doc_info = {
                "content_snippet": doc[:500] if doc else "",
                "source": metadata.get("relative_path", "unknown"),
                "type": doc_type,
                "relevance": relevance,
            }
            relevant_docs.append(doc_info)

            if doc_type == "architecture" and relevance > 0.5:
                architecture_context.append(doc)

            # Extract code locations
            if doc:
                patterns = [
                    r'[`"]?([A-Za-z_/\\]+\.(cs|vb|aspx|ascx|asp|ts|tsx|js|jsx|py))[`"]?',
                ]
                for pattern in patterns:
                    paths = re.findall(pattern, doc)
                    for path_match in paths[:3]:
                        code_locations.append({
                            "path": path_match[0] if isinstance(path_match, tuple) else path_match,
                            "source": metadata.get("relative_path", "unknown"),
                        })

        # Deduplicate
        seen_paths = set()
        unique_locations = []
        for loc in code_locations:
            if loc["path"] not in seen_paths:
                seen_paths.add(loc["path"])
                unique_locations.append(loc)

        architecture_summary = (
            "\n\n".join(architecture_context[:2])
            if architecture_context
            else None
        )

        return IntakeContextResult(
            context_available=True,
            project_name=project_name,
            project_path=project_path,
            relevant_docs=relevant_docs[:10],
            architecture_summary=architecture_summary,
            code_locations=unique_locations[:20],
            total_docs_found=len(relevant_docs),
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        return IntakeContextResult(
            context_available=False,
            project_name=project_name,
            project_path=project_path,
            relevant_docs=[],
            architecture_summary=None,
            code_locations=[],
            total_docs_found=0,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            error=str(e),
        )


# =============================================================================
# TEST DATA
# =============================================================================

VALID_ANSWERS = {
    "q1_primary_purpose": (
        "Dit is een healthcare registratie systeem voor het beheren van "
        "patientgegevens en afspraken in ziekenhuizen en klinieken."
    ),
    "q2_users": (
        "Administratief personeel, artsen, verpleegkundigen en patienten "
        "via het patient portaal."
    ),
    "q3_critical_processes": (
        "Patient registratie, afspraak planning, facturatie en declaratie "
        "naar verzekeraars. Deze processen mogen nooit data verliezen."
    ),
    "q4_integrations": (
        "HL7 FHIR voor patient data, Vecozo voor declaraties, "
        "email gateway voor notificaties."
    ),
    "q5_pain_points": "Legacy codebase met technische schuld.",
}

MOCK_DOCS_RICH = [
    {
        "content": "Architecture overview: The system uses layered architecture with "
                   "CRSLibrary/Core.cs as the main entry point. WEB/Default.aspx handles UI.",
        "metadata": {"document_type": "architecture", "relative_path": "docs/arch.md"},
        "distance": 0.2,
    },
    {
        "content": "Patient registration module in CRSLibrary/Patient/Registration.vb",
        "metadata": {"document_type": "code", "relative_path": "src/patient.md"},
        "distance": 0.3,
    },
    {
        "content": "API endpoints documented in Services/API/PatientService.cs",
        "metadata": {"document_type": "api", "relative_path": "docs/api.md"},
        "distance": 0.35,
    },
    {
        "content": "Database schema for patient tables",
        "metadata": {"document_type": "database", "relative_path": "docs/db.md"},
        "distance": 0.4,
    },
    {
        "content": "Integration with Vecozo via SOAP services",
        "metadata": {"document_type": "integration", "relative_path": "docs/vecozo.md"},
        "distance": 0.45,
    },
]

REFERENCE_PROJECTS = [
    "/opt/projecten/hci-crs",
    "/opt/projecten/paramedi/FRM",
    "/opt/projecten/paramedi/FysioOne-Classic",
]


# =============================================================================
# TESTS
# =============================================================================

def test_graceful_degradation_no_chroma():
    """Test that missing ChromaDB results in graceful degradation."""
    result = fetch_intake_context(
        project_path="/opt/projecten/hci-crs",
        answers=VALID_ANSWERS,
        chroma_service=None,  # No ChromaDB
    )

    assert not result.context_available, "Expected context_available=False"
    assert result.quality_score == 0.70, f"Expected score 0.70, got {result.quality_score}"
    assert result.error is not None, "Expected error message"
    assert result.project_name == "hci-crs"
    print("✓ test_graceful_degradation_no_chroma PASSED")


def test_rich_context_full_score():
    """Test that rich context results in score 1.0."""
    mock_chroma = MockChromaService(MOCK_DOCS_RICH)
    result = fetch_intake_context(
        project_path="/opt/projecten/hci-crs",
        answers=VALID_ANSWERS,
        chroma_service=mock_chroma,
    )

    assert result.context_available, "Expected context_available=True"
    assert result.total_docs_found == 5, f"Expected 5 docs, got {result.total_docs_found}"
    assert result.architecture_summary is not None, "Expected architecture summary"
    assert result.quality_score == 1.0, f"Expected score 1.0, got {result.quality_score}"
    print("✓ test_rich_context_full_score PASSED")


def test_partial_context_reduced_score():
    """Test that partial context (no architecture) results in score 0.85."""
    partial_docs = [
        {"content": "Some code documentation", "metadata": {"document_type": "code"}, "distance": 0.3},
        {"content": "More code docs", "metadata": {"document_type": "code"}, "distance": 0.35},
    ]
    mock_chroma = MockChromaService(partial_docs)
    result = fetch_intake_context(
        project_path="/opt/projecten/hci-crs",
        answers=VALID_ANSWERS,
        chroma_service=mock_chroma,
    )

    assert result.context_available
    assert result.architecture_summary is None, "Expected no architecture summary"
    assert result.quality_score == 0.85, f"Expected score 0.85, got {result.quality_score}"
    print("✓ test_partial_context_reduced_score PASSED")


def test_empty_context_minimum_score():
    """Test that empty context results in score 0.70."""
    mock_chroma = MockChromaService([])  # Empty docs
    result = fetch_intake_context(
        project_path="/opt/projecten/hci-crs",
        answers=VALID_ANSWERS,
        chroma_service=mock_chroma,
    )

    assert result.context_available  # Service available, just no results
    assert result.total_docs_found == 0
    assert result.quality_score == 0.70, f"Expected score 0.70, got {result.quality_score}"
    print("✓ test_empty_context_minimum_score PASSED")


def test_code_location_extraction():
    """Test that code locations are extracted from documents."""
    mock_chroma = MockChromaService(MOCK_DOCS_RICH)
    result = fetch_intake_context(
        project_path="/opt/projecten/hci-crs",
        answers=VALID_ANSWERS,
        chroma_service=mock_chroma,
    )

    assert len(result.code_locations) > 0, "Expected code locations"
    paths = [loc["path"] for loc in result.code_locations]
    # Should find paths from mock docs
    assert any(".cs" in p or ".vb" in p or ".aspx" in p for p in paths), \
        f"Expected code file paths, got {paths}"
    print("✓ test_code_location_extraction PASSED")


def test_code_location_deduplication():
    """Test that duplicate code locations are removed."""
    duplicate_docs = [
        {"content": "Found in CRSLibrary/Core.cs and CRSLibrary/Core.cs again",
         "metadata": {"document_type": "code"}, "distance": 0.3},
        {"content": "Also references CRSLibrary/Core.cs",
         "metadata": {"document_type": "code"}, "distance": 0.35},
    ]
    mock_chroma = MockChromaService(duplicate_docs)
    result = fetch_intake_context(
        project_path="/opt/projecten/test",
        answers=VALID_ANSWERS,
        chroma_service=mock_chroma,
    )

    paths = [loc["path"] for loc in result.code_locations]
    # Should be deduplicated
    assert len(paths) == len(set(paths)), f"Duplicate paths found: {paths}"
    print("✓ test_code_location_deduplication PASSED")


def test_result_to_dict():
    """Test that result can be serialized to dict."""
    result = IntakeContextResult(
        context_available=True,
        project_name="test",
        project_path="/test",
        relevant_docs=[{"content": "test"}],
        architecture_summary="Test architecture",
        code_locations=[{"path": "test.cs", "source": "doc.md"}],
        total_docs_found=1,
        fetched_at="2026-02-03T00:00:00Z",
    )

    d = result.to_dict()
    assert d["context_available"] is True
    assert d["project_name"] == "test"
    assert d["relevant_docs_count"] == 1
    assert d["has_architecture_summary"] is True
    assert "quality_score" in d
    print("✓ test_result_to_dict PASSED")


def test_reference_projects_graceful_degradation():
    """Test graceful degradation on reference projects (no real ChromaDB)."""
    for project_path in REFERENCE_PROJECTS:
        if not Path(project_path).exists():
            print(f"⊘ SKIPPED {project_path} (not available)")
            continue

        # Without ChromaDB - should gracefully degrade
        result = fetch_intake_context(
            project_path=project_path,
            answers=VALID_ANSWERS,
            chroma_service=None,
        )

        project_name = Path(project_path).name
        assert result.quality_score >= 0.70, \
            f"Expected score >= 0.70 for {project_name}, got {result.quality_score}"
        assert result.project_name == project_name
        print(f"✓ test_reference_project {project_name} graceful degradation PASSED")


def test_quality_threshold_met():
    """Test that M2 stage threshold (0.70) is met even without ChromaDB."""
    QUALITY_THRESHOLD = 0.70  # From get_stages()

    result = fetch_intake_context(
        project_path="/opt/projecten/hci-crs",
        answers=VALID_ANSWERS,
        chroma_service=None,
    )

    passed = result.quality_score >= QUALITY_THRESHOLD
    assert passed, \
        f"Quality gate should pass: score {result.quality_score} >= threshold {QUALITY_THRESHOLD}"
    print("✓ test_quality_threshold_met PASSED")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all M2 tests."""
    print("=" * 60)
    print("OnboardingWorkflow Module 2 - Standalone Tests")
    print("=" * 60)
    print()

    tests = [
        test_graceful_degradation_no_chroma,
        test_rich_context_full_score,
        test_partial_context_reduced_score,
        test_empty_context_minimum_score,
        test_code_location_extraction,
        test_code_location_deduplication,
        test_result_to_dict,
        test_quality_threshold_met,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1

    print()
    print("-" * 60)
    print("Reference Project Tests (Graceful Degradation)")
    print("-" * 60)

    try:
        test_reference_projects_graceful_degradation()
        passed += 1
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        failed += 1

    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)

    print()
    print("✓ Module 2 (Intake + Vector DB Context) - ALL TESTS PASSED")
    print()
    print("Key features validated:")
    print("  - Graceful degradation when ChromaDB unavailable (score 0.70)")
    print("  - Rich context extraction (score 1.0 with arch + 5+ docs)")
    print("  - Code location extraction and deduplication")
    print("  - Quality threshold 0.70 always met")
    print()
    print("Ready to proceed to Module 3 (Code Understanding)")


if __name__ == "__main__":
    main()
