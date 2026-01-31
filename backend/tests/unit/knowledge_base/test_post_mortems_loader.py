"""
Tests for KB5 - Post-Mortems Knowledge Base Loader.

Tests cover:
- Data validation: count >= 50, required fields, unique IDs, valid categories, company diversity >= 10
- Loader: load_single, load_all, stats, clear (mock ChromaService)
"""

import pytest
from unittest.mock import MagicMock

from app.services.knowledge_base.post_mortems_loader import (
    POST_MORTEMS_DATA,
    PostMortemsLoader,
)


# =============================================================================
# DATA VALIDATION
# =============================================================================


class TestPostMortemsDataValidation:
    """Tests for the static POST_MORTEMS_DATA dataset."""

    def test_minimum_count(self):
        """Dataset should contain at least 50 post-mortems."""
        assert len(POST_MORTEMS_DATA) >= 50

    def test_all_have_required_fields(self):
        """Every post-mortem must have all required fields."""
        required_fields = [
            "post_mortem_id", "title", "content", "company", "date",
            "duration", "affected_services", "root_cause_category",
            "impact_category", "remediation_actions", "tags", "source_url",
        ]
        for pm in POST_MORTEMS_DATA:
            for field in required_fields:
                assert field in pm, (
                    f"Post-mortem {pm.get('post_mortem_id', '?')} missing field: {field}"
                )

    def test_unique_ids(self):
        """All post_mortem_ids must be unique."""
        ids = [pm["post_mortem_id"] for pm in POST_MORTEMS_DATA]
        assert len(ids) == len(set(ids)), "Duplicate post_mortem_ids found"

    def test_valid_root_cause_categories(self):
        """All root_cause_categories must be from the allowed set."""
        valid_categories = {
            "config", "deployment", "infrastructure", "code",
            "dependency", "human", "scaling",
        }
        for pm in POST_MORTEMS_DATA:
            assert pm["root_cause_category"] in valid_categories, (
                f"PM {pm['post_mortem_id']} has invalid root_cause_category: {pm['root_cause_category']}"
            )

    def test_valid_impact_categories(self):
        """All impact_categories must be from the allowed set."""
        valid_impacts = {"partial", "major", "complete"}
        for pm in POST_MORTEMS_DATA:
            assert pm["impact_category"] in valid_impacts, (
                f"PM {pm['post_mortem_id']} has invalid impact_category: {pm['impact_category']}"
            )

    def test_company_diversity(self):
        """Should have post-mortems from at least 10 different companies."""
        companies = set(pm["company"] for pm in POST_MORTEMS_DATA)
        assert len(companies) >= 10, (
            f"Only {len(companies)} companies: {companies}"
        )

    def test_affected_services_not_empty(self):
        """Each post-mortem should list at least one affected service."""
        for pm in POST_MORTEMS_DATA:
            assert len(pm["affected_services"]) >= 1, (
                f"PM {pm['post_mortem_id']} has no affected services"
            )

    def test_remediation_actions_not_empty(self):
        """Each post-mortem should list at least one remediation action."""
        for pm in POST_MORTEMS_DATA:
            assert len(pm["remediation_actions"]) >= 1, (
                f"PM {pm['post_mortem_id']} has no remediation actions"
            )

    def test_tags_not_empty(self):
        """Each post-mortem should have at least one tag."""
        for pm in POST_MORTEMS_DATA:
            assert len(pm["tags"]) >= 1, (
                f"PM {pm['post_mortem_id']} has no tags"
            )

    def test_content_not_empty(self):
        """Each post-mortem must have non-empty content."""
        for pm in POST_MORTEMS_DATA:
            assert len(pm["content"]) > 20, (
                f"PM {pm['post_mortem_id']} has too short content"
            )

    def test_id_format(self):
        """Post-mortem IDs should follow PM-NNN format."""
        import re
        pattern = re.compile(r"^PM-\d{3}$")
        for pm in POST_MORTEMS_DATA:
            assert pattern.match(pm["post_mortem_id"]), (
                f"Invalid post_mortem_id format: {pm['post_mortem_id']}"
            )

    def test_date_format(self):
        """Dates should be in YYYY-MM-DD format."""
        import re
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for pm in POST_MORTEMS_DATA:
            assert pattern.match(pm["date"]), (
                f"PM {pm['post_mortem_id']} has invalid date format: {pm['date']}"
            )

    def test_root_cause_distribution(self):
        """Should have post-mortems across multiple root cause categories."""
        categories = set(pm["root_cause_category"] for pm in POST_MORTEMS_DATA)
        assert len(categories) >= 5, (
            f"Only {len(categories)} root cause categories: {categories}"
        )

    def test_contains_key_companies(self):
        """Should contain post-mortems from well-known companies."""
        companies = {pm["company"] for pm in POST_MORTEMS_DATA}
        assert "GitHub" in companies
        assert "AWS" in companies
        assert "Google" in companies
        assert "Cloudflare" in companies

    def test_source_url_format(self):
        """Source URLs should be valid HTTP(S) URLs."""
        for pm in POST_MORTEMS_DATA:
            url = pm["source_url"]
            assert url.startswith("http://") or url.startswith("https://"), (
                f"PM {pm['post_mortem_id']} has invalid source_url: {url}"
            )


# =============================================================================
# LOADER
# =============================================================================


class TestPostMortemsLoader:
    """Tests for the PostMortemsLoader class."""

    def _make_mock_chroma(self):
        """Create a mock ChromaService."""
        mock = MagicMock()
        mock.add_document = MagicMock()
        mock.get_collection_count = MagicMock(return_value=0)
        mock.delete_collection = MagicMock()
        return mock

    def test_load_single_post_mortem(self):
        """Should load a single post-mortem into ChromaDB."""
        mock_chroma = self._make_mock_chroma()
        loader = PostMortemsLoader(mock_chroma)

        pm = POST_MORTEMS_DATA[0]
        result = loader.load_post_mortem(pm)

        assert result == pm["post_mortem_id"]
        mock_chroma.add_document.assert_called_once()
        call_kwargs = mock_chroma.add_document.call_args
        assert call_kwargs[1]["collection_name"] == "post_mortems"
        assert call_kwargs[1]["document_id"] == pm["post_mortem_id"]

    def test_load_all(self):
        """Should load all post-mortems and return stats."""
        mock_chroma = self._make_mock_chroma()
        loader = PostMortemsLoader(mock_chroma)

        stats = loader.load_all()

        assert stats["loaded"] == len(POST_MORTEMS_DATA)
        assert stats["errors"] == 0
        assert stats["total_available"] == len(POST_MORTEMS_DATA)
        assert len(stats["root_cause_categories"]) >= 5
        assert len(stats["companies"]) >= 10
        assert mock_chroma.add_document.call_count == len(POST_MORTEMS_DATA)

    def test_load_all_with_error(self):
        """Should handle errors during loading gracefully."""
        mock_chroma = self._make_mock_chroma()
        mock_chroma.add_document.side_effect = [None] * 3 + [Exception("DB error")] + [None] * 100
        loader = PostMortemsLoader(mock_chroma)

        stats = loader.load_all()

        assert stats["errors"] == 1
        assert len(stats["error_details"]) == 1

    def test_get_load_status_empty(self):
        """Should return status with zero loaded count when empty."""
        mock_chroma = self._make_mock_chroma()
        loader = PostMortemsLoader(mock_chroma)

        status = loader.get_load_status()

        assert status["collection"] == "post_mortems"
        assert status["loaded_count"] == 0
        assert status["available_count"] == len(POST_MORTEMS_DATA)
        assert len(status["root_cause_categories"]) >= 5
        assert len(status["companies"]) >= 10

    def test_get_load_status_loaded(self):
        """Should return correct count when post-mortems are loaded."""
        mock_chroma = self._make_mock_chroma()
        mock_chroma.get_collection_count.return_value = 50
        loader = PostMortemsLoader(mock_chroma)

        status = loader.get_load_status()

        assert status["loaded_count"] == 50

    def test_get_load_status_chroma_error(self):
        """Should return 0 count if ChromaDB errors."""
        mock_chroma = self._make_mock_chroma()
        mock_chroma.get_collection_count.side_effect = Exception("Connection failed")
        loader = PostMortemsLoader(mock_chroma)

        status = loader.get_load_status()

        assert status["loaded_count"] == 0

    def test_clear_collection(self):
        """Should clear the collection."""
        mock_chroma = self._make_mock_chroma()
        loader = PostMortemsLoader(mock_chroma)

        loader.clear_collection()

        mock_chroma.delete_collection.assert_called_once_with("post_mortems")

    def test_document_text_contains_key_fields(self):
        """Document text sent to ChromaDB should contain key fields."""
        mock_chroma = self._make_mock_chroma()
        loader = PostMortemsLoader(mock_chroma)

        pm = POST_MORTEMS_DATA[0]
        loader.load_post_mortem(pm)

        call_kwargs = mock_chroma.add_document.call_args[1]
        doc_text = call_kwargs["text"]

        assert pm["title"] in doc_text
        assert pm["company"] in doc_text
        assert pm["content"] in doc_text

    def test_metadata_contains_required_fields(self):
        """Metadata sent to ChromaDB should contain required fields."""
        mock_chroma = self._make_mock_chroma()
        loader = PostMortemsLoader(mock_chroma)

        pm = POST_MORTEMS_DATA[0]
        loader.load_post_mortem(pm)

        call_kwargs = mock_chroma.add_document.call_args[1]
        metadata = call_kwargs["metadata"]

        assert metadata["post_mortem_id"] == pm["post_mortem_id"]
        assert metadata["title"] == pm["title"]
        assert metadata["company"] == pm["company"]
        assert metadata["root_cause_category"] == pm["root_cause_category"]
        assert metadata["impact_category"] == pm["impact_category"]
        assert metadata["source"] == "post_mortems"
