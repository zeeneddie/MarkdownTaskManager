# backend/tests/services/week118/test_duplicate_detector_service.py
"""
Tests for DuplicateDetectorService - Week 118 Client Portal 2.0 Phase 2
ChromaDB-based duplicate detection for feature requests.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.duplicate_detector_service import DuplicateDetectorService, CHROMADB_AVAILABLE
from app.models.portal_enhancements import FeatureDuplicate, DuplicateStatus


class TestDuplicateDetectorService:
    """Test suite for DuplicateDetectorService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock db."""
        return DuplicateDetectorService(mock_db)

    # ============== Confidence Level Tests ==============

    def test_get_confidence_level_high(self, service):
        """Test high confidence threshold."""
        assert service._get_confidence_level(0.90) == "high"
        assert service._get_confidence_level(0.85) == "high"

    def test_get_confidence_level_medium(self, service):
        """Test medium confidence threshold."""
        assert service._get_confidence_level(0.80) == "medium"
        assert service._get_confidence_level(0.70) == "medium"

    def test_get_confidence_level_low(self, service):
        """Test low confidence threshold."""
        assert service._get_confidence_level(0.65) == "low"
        assert service._get_confidence_level(0.60) == "low"

    # ============== Recommendation Tests ==============

    def test_get_recommendation_no_duplicates(self, service):
        """Test recommendation when no duplicates found."""
        recommendation = service._get_recommendation([])
        assert "unique" in recommendation.lower()

    def test_get_recommendation_high_confidence(self, service):
        """Test recommendation with high confidence duplicate."""
        duplicates = [
            {"feature_id": 123, "confidence": "high", "similarity_score": 0.90}
        ]
        recommendation = service._get_recommendation(duplicates)
        assert "merging" in recommendation.lower() or "high confidence" in recommendation.lower()
        assert "123" in recommendation

    def test_get_recommendation_medium_confidence(self, service):
        """Test recommendation with medium confidence duplicates."""
        duplicates = [
            {"feature_id": 123, "confidence": "medium", "similarity_score": 0.75},
            {"feature_id": 456, "confidence": "medium", "similarity_score": 0.72},
        ]
        recommendation = service._get_recommendation(duplicates)
        assert "potential" in recommendation.lower() or "review" in recommendation.lower()

    # ============== Indexing Tests ==============

    @pytest.mark.asyncio
    async def test_index_feature_chromadb_unavailable(self, service):
        """Test indexing when ChromaDB is not available."""
        with patch.object(service, '_get_collection', return_value=None):
            result = await service.index_feature(
                feature_id=42,
                title="Test Feature",
                description="Test description",
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_index_feature_success(self, service):
        """Test successful feature indexing."""
        mock_collection = MagicMock()
        mock_collection.upsert = MagicMock()

        with patch.object(service, '_get_collection', return_value=mock_collection):
            result = await service.index_feature(
                feature_id=42,
                title="Test Feature",
                description="Test description",
                project_id=1,
            )

            assert result is True
            mock_collection.upsert.assert_called_once()

    # ============== Similarity Search Tests ==============

    @pytest.mark.asyncio
    async def test_find_similar_chromadb_unavailable(self, service):
        """Test similarity search falls back to keyword matching."""
        with patch.object(service, '_get_collection', return_value=None):
            result = await service.find_similar(
                feature_id=42,
                title="Test Feature",
                description="Test description",
            )
            # Falls back to keyword matching which returns empty
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_find_similar_success(self, service):
        """Test successful similarity search."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            'ids': [['100', '42', '200']],  # 42 is self, should be filtered
            'distances': [[0.1, 0.0, 0.3]],  # Lower distance = higher similarity
            'metadatas': [[
                {'title': 'Similar Feature', 'feature_id': 100},
                {'title': 'Self', 'feature_id': 42},
                {'title': 'Another Feature', 'feature_id': 200},
            ]],
        }

        with patch.object(service, '_get_collection', return_value=mock_collection):
            result = await service.find_similar(
                feature_id=42,
                title="Test Feature",
                description="Test description",
                limit=5,
            )

            # Should filter out self (42) and return similar features
            assert len(result) <= 5
            # Check self is not in results
            feature_ids = [r['feature_id'] for r in result]
            assert 42 not in feature_ids

    # ============== Duplicate Detection Tests ==============

    @pytest.mark.asyncio
    async def test_check_for_duplicates_none_found(self, service, mock_db):
        """Test when no duplicates are found."""
        with patch.object(service, 'find_similar', return_value=[]):
            result = await service.check_for_duplicates(
                feature_id=42,
                title="Unique Feature",
                description="Completely unique description",
                auto_record=False,
            )

            assert result["duplicates_found"] == 0
            assert "unique" in result["recommendation"].lower()

    @pytest.mark.asyncio
    async def test_check_for_duplicates_found(self, service, mock_db):
        """Test when duplicates are found."""
        similar = [
            {
                "feature_id": 100,
                "title": "Similar Feature",
                "similarity_score": 0.85,
                "confidence": "high",
                "detection_method": "chromadb",
            }
        ]

        # Mock no existing record - use MagicMock as scalar_one_or_none is sync
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        async def mock_refresh(obj):
            obj.id = uuid4()

        mock_db.refresh.side_effect = mock_refresh

        with patch.object(service, 'find_similar', return_value=similar):
            result = await service.check_for_duplicates(
                feature_id=42,
                title="Test Feature",
                description="Test description",
                auto_record=True,
            )

            assert result["duplicates_found"] == 1
            assert result["high_confidence"] == 1
            assert len(result["recorded_ids"]) == 1

    # ============== Resolution Tests ==============

    @pytest.mark.asyncio
    async def test_resolve_duplicate_confirmed(self, service, mock_db):
        """Test confirming a duplicate."""
        duplicate = FeatureDuplicate(
            id=uuid4(),
            source_feature_id=42,
            duplicate_feature_id=100,
            status=DuplicateStatus.PENDING.value,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = duplicate
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.resolve_duplicate(
            duplicate_id=duplicate.id,
            resolution="confirmed",
            resolved_by="admin",
        )

        assert result["success"] is True
        assert duplicate.status == "confirmed"
        assert duplicate.resolved_by == "admin"
        assert duplicate.resolved_at is not None

    @pytest.mark.asyncio
    async def test_resolve_duplicate_not_found(self, service, mock_db):
        """Test resolving non-existent duplicate."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.resolve_duplicate(
            duplicate_id=uuid4(),
            resolution="confirmed",
            resolved_by="admin",
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_merge_features(self, service, mock_db):
        """Test merging duplicate features."""
        duplicates = [
            FeatureDuplicate(
                id=uuid4(),
                source_feature_id=42,
                duplicate_feature_id=100,
                status=DuplicateStatus.PENDING.value,
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = duplicates
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.merge_features(
            source_feature_id=42,
            target_feature_id=100,
            resolved_by="admin",
        )

        assert result["success"] is True
        assert result["records_updated"] == 1
        assert duplicates[0].status == DuplicateStatus.MERGED.value
        assert duplicates[0].merge_target_id == 100

    # ============== Pending Review Tests ==============

    @pytest.mark.asyncio
    async def test_get_pending_duplicates(self, service, mock_db):
        """Test getting pending duplicates for review."""
        pending = [
            FeatureDuplicate(
                id=uuid4(),
                source_feature_id=42,
                source_title="Feature A",
                duplicate_feature_id=100,
                duplicate_title="Feature B",
                similarity_score=0.85,
                detection_method="chromadb",
                status=DuplicateStatus.PENDING.value,
                created_at=datetime.now(timezone.utc),
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = pending
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_pending_duplicates(limit=10)

        assert len(result) == 1
        assert result[0]["source_feature_id"] == 42
        assert result[0]["confidence"] == "high"

    # ============== Statistics Tests ==============

    @pytest.mark.asyncio
    async def test_get_statistics(self, service, mock_db):
        """Test getting duplicate detection statistics."""
        duplicates = [
            FeatureDuplicate(status=DuplicateStatus.PENDING.value, similarity_score=0.85),
            FeatureDuplicate(status=DuplicateStatus.CONFIRMED.value, similarity_score=0.90),
            FeatureDuplicate(status=DuplicateStatus.MERGED.value, similarity_score=0.95),
            FeatureDuplicate(status=DuplicateStatus.REJECTED.value, similarity_score=0.70),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = duplicates
        mock_db.execute = AsyncMock(return_value=mock_result)

        stats = await service.get_statistics()

        assert stats["total_detected"] == 4
        assert stats["pending_review"] == 1
        assert stats["confirmed"] == 1
        assert stats["merged"] == 1
        assert stats["rejected"] == 1
        assert stats["average_similarity"] == 0.85

    # ============== Model Helper Tests ==============

    def test_feature_duplicate_is_high_confidence(self):
        """Test is_high_confidence helper."""
        high = FeatureDuplicate(similarity_score=0.90)
        low = FeatureDuplicate(similarity_score=0.70)

        assert high.is_high_confidence() is True
        assert low.is_high_confidence() is False
        assert high.is_high_confidence(threshold=0.95) is False
