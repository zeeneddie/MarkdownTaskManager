"""
Tests for KB1 - Famous Bugs Knowledge Base Loader.

Tests cover:
- Data validation: count >= 30, required fields, unique IDs, valid categories, CWE format
- Loader: load_single, load_all, stats, clear, duplicate handling (mock ChromaService)
"""

import pytest
from unittest.mock import MagicMock, patch, call

from app.services.knowledge_base.famous_bugs_loader import (
    FAMOUS_BUGS_DATA,
    FamousBugsLoader,
)


# =============================================================================
# DATA VALIDATION
# =============================================================================


class TestFamousBugsDataValidation:
    """Tests for the static FAMOUS_BUGS_DATA dataset."""

    def test_minimum_count(self):
        """Dataset should contain at least 30 bugs."""
        assert len(FAMOUS_BUGS_DATA) >= 30

    def test_all_have_required_fields(self):
        """Every bug must have all required fields."""
        required_fields = [
            "bug_id", "title", "description", "category",
            "year", "impact", "root_cause", "lessons_learned",
            "cwe_ids", "technologies",
        ]
        for bug in FAMOUS_BUGS_DATA:
            for field in required_fields:
                assert field in bug, f"Bug {bug.get('bug_id', '?')} missing field: {field}"

    def test_unique_ids(self):
        """All bug_ids must be unique."""
        ids = [bug["bug_id"] for bug in FAMOUS_BUGS_DATA]
        assert len(ids) == len(set(ids)), "Duplicate bug_ids found"

    def test_valid_categories(self):
        """All categories must be from the allowed set."""
        valid_categories = {"problems", "outages", "bugs", "worms", "ai"}
        for bug in FAMOUS_BUGS_DATA:
            assert bug["category"] in valid_categories, (
                f"Bug {bug['bug_id']} has invalid category: {bug['category']}"
            )

    def test_cwe_format(self):
        """All CWE IDs must follow CWE-NNN format."""
        import re
        cwe_pattern = re.compile(r"^CWE-\d+$")
        for bug in FAMOUS_BUGS_DATA:
            assert len(bug["cwe_ids"]) > 0, f"Bug {bug['bug_id']} has no CWE IDs"
            for cwe in bug["cwe_ids"]:
                assert cwe_pattern.match(cwe), (
                    f"Bug {bug['bug_id']} has invalid CWE format: {cwe}"
                )

    def test_year_range(self):
        """Years should be between 1960 and 2025."""
        for bug in FAMOUS_BUGS_DATA:
            assert 1960 <= bug["year"] <= 2025, (
                f"Bug {bug['bug_id']} has unusual year: {bug['year']}"
            )

    def test_technologies_not_empty(self):
        """Each bug should list at least one technology."""
        for bug in FAMOUS_BUGS_DATA:
            assert len(bug["technologies"]) >= 1, (
                f"Bug {bug['bug_id']} has no technologies"
            )

    def test_description_not_empty(self):
        """Each bug must have a non-empty description."""
        for bug in FAMOUS_BUGS_DATA:
            assert len(bug["description"]) > 20, (
                f"Bug {bug['bug_id']} has too short description"
            )

    def test_impact_not_empty(self):
        """Each bug must have a non-empty impact."""
        for bug in FAMOUS_BUGS_DATA:
            assert len(bug["impact"]) > 10, (
                f"Bug {bug['bug_id']} has too short impact"
            )

    def test_lessons_learned_not_empty(self):
        """Each bug must have non-empty lessons_learned."""
        for bug in FAMOUS_BUGS_DATA:
            assert len(bug["lessons_learned"]) > 10, (
                f"Bug {bug['bug_id']} has too short lessons_learned"
            )

    def test_category_distribution(self):
        """Should have bugs across multiple categories."""
        categories = set(bug["category"] for bug in FAMOUS_BUGS_DATA)
        assert len(categories) >= 4, f"Only {len(categories)} categories represented"

    def test_contains_key_bugs(self):
        """Should contain well-known famous bugs."""
        titles = {bug["title"] for bug in FAMOUS_BUGS_DATA}
        # Check for some key entries
        assert any("Ariane" in t for t in titles), "Missing Ariane 5"
        assert any("Therac" in t for t in titles), "Missing Therac-25"
        assert any("Log4" in t for t in titles), "Missing Log4Shell"
        assert any("Heartbleed" in t for t in titles), "Missing Heartbleed"
        assert any("Y2K" in t for t in titles), "Missing Y2K"
        assert any("Morris" in t for t in titles), "Missing Morris Worm"
        assert any("CrowdStrike" in t for t in titles), "Missing CrowdStrike 2024"

    def test_id_format(self):
        """Bug IDs should follow FB-NNN format."""
        import re
        pattern = re.compile(r"^FB-\d{3}$")
        for bug in FAMOUS_BUGS_DATA:
            assert pattern.match(bug["bug_id"]), (
                f"Invalid bug_id format: {bug['bug_id']}"
            )


# =============================================================================
# LOADER
# =============================================================================


class TestFamousBugsLoader:
    """Tests for the FamousBugsLoader class."""

    def _make_mock_chroma(self):
        """Create a mock ChromaService."""
        mock = MagicMock()
        mock.add_document = MagicMock()
        mock.get_collection_count = MagicMock(return_value=0)
        mock.delete_collection = MagicMock()
        return mock

    def test_load_single_bug(self):
        """Should load a single bug into ChromaDB."""
        mock_chroma = self._make_mock_chroma()
        loader = FamousBugsLoader(mock_chroma)

        bug = FAMOUS_BUGS_DATA[0]
        result = loader.load_bug(bug)

        assert result == bug["bug_id"]
        mock_chroma.add_document.assert_called_once()
        call_kwargs = mock_chroma.add_document.call_args
        assert call_kwargs[1]["collection_name"] == "famous_bugs"
        assert call_kwargs[1]["document_id"] == bug["bug_id"]

    def test_load_all(self):
        """Should load all bugs and return stats."""
        mock_chroma = self._make_mock_chroma()
        loader = FamousBugsLoader(mock_chroma)

        stats = loader.load_all()

        assert stats["loaded"] == len(FAMOUS_BUGS_DATA)
        assert stats["errors"] == 0
        assert stats["total_available"] == len(FAMOUS_BUGS_DATA)
        assert len(stats["categories"]) >= 4
        assert mock_chroma.add_document.call_count == len(FAMOUS_BUGS_DATA)

    def test_load_all_with_error(self):
        """Should handle errors during loading gracefully."""
        mock_chroma = self._make_mock_chroma()
        mock_chroma.add_document.side_effect = [None] * 5 + [Exception("DB error")] + [None] * 100
        loader = FamousBugsLoader(mock_chroma)

        stats = loader.load_all()

        assert stats["errors"] == 1
        assert stats["loaded"] == len(FAMOUS_BUGS_DATA) - 1
        assert len(stats["error_details"]) == 1

    def test_get_load_status_empty(self):
        """Should return status with zero loaded count when empty."""
        mock_chroma = self._make_mock_chroma()
        mock_chroma.get_collection_count.return_value = 0
        loader = FamousBugsLoader(mock_chroma)

        status = loader.get_load_status()

        assert status["collection"] == "famous_bugs"
        assert status["loaded_count"] == 0
        assert status["available_count"] == len(FAMOUS_BUGS_DATA)
        assert len(status["categories"]) >= 4

    def test_get_load_status_loaded(self):
        """Should return correct count when bugs are loaded."""
        mock_chroma = self._make_mock_chroma()
        mock_chroma.get_collection_count.return_value = 30
        loader = FamousBugsLoader(mock_chroma)

        status = loader.get_load_status()

        assert status["loaded_count"] == 30

    def test_get_load_status_chroma_error(self):
        """Should return 0 count if ChromaDB errors."""
        mock_chroma = self._make_mock_chroma()
        mock_chroma.get_collection_count.side_effect = Exception("Connection failed")
        loader = FamousBugsLoader(mock_chroma)

        status = loader.get_load_status()

        assert status["loaded_count"] == 0

    def test_clear_collection(self):
        """Should clear the collection."""
        mock_chroma = self._make_mock_chroma()
        loader = FamousBugsLoader(mock_chroma)

        loader.clear_collection()

        mock_chroma.delete_collection.assert_called_once_with("famous_bugs")

    def test_document_text_contains_key_fields(self):
        """Document text sent to ChromaDB should contain key fields."""
        mock_chroma = self._make_mock_chroma()
        loader = FamousBugsLoader(mock_chroma)

        bug = FAMOUS_BUGS_DATA[0]
        loader.load_bug(bug)

        call_kwargs = mock_chroma.add_document.call_args[1]
        doc_text = call_kwargs["text"]

        assert bug["title"] in doc_text
        assert bug["description"] in doc_text
        assert bug["root_cause"] in doc_text
        assert str(bug["year"]) in doc_text

    def test_metadata_contains_required_fields(self):
        """Metadata sent to ChromaDB should contain required fields."""
        mock_chroma = self._make_mock_chroma()
        loader = FamousBugsLoader(mock_chroma)

        bug = FAMOUS_BUGS_DATA[0]
        loader.load_bug(bug)

        call_kwargs = mock_chroma.add_document.call_args[1]
        metadata = call_kwargs["metadata"]

        assert metadata["bug_id"] == bug["bug_id"]
        assert metadata["title"] == bug["title"]
        assert metadata["category"] == bug["category"]
        assert metadata["year"] == bug["year"]
        assert metadata["source"] == "famous_bugs"
