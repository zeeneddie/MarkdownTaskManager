"""
Tests for VisualRegressionService - Week 134-135

Tests visual regression testing with screenshot capture and comparison.

Agent: Tessa (Test Engineer) + Vicky (Visual Designer)
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from PIL import Image
import io

from app.services.visual_regression_service import VisualRegressionService
from app.models.week134_testing import (
    ComparisonResult,
    VisualRegressionResult,
    DiffRegion,
)


class TestVisualRegressionService:
    """Test suite for VisualRegressionService."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield VisualRegressionService(baseline_dir=tmpdir)

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes."""
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    @pytest.fixture
    def different_image_bytes(self):
        """Create different sample image bytes."""
        img = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    # =========================================================================
    # Baseline Capture Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_capture_baseline_success(self, service, sample_image_bytes):
        """Test capturing a visual baseline successfully."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = (sample_image_bytes, 500)

            result = await service.capture_baseline(
                test_id="visual-001",
                test_name="Baseline Capture Test",
                url="http://example.com/page",
            )

            assert result.result == ComparisonResult.NEW_BASELINE
            assert result.baseline_path is not None
            assert result.error is None
            assert result.legacy_duration_ms == 500

    @pytest.mark.asyncio
    async def test_capture_baseline_with_viewport(self, service, sample_image_bytes):
        """Test capturing baseline with custom viewport."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = (sample_image_bytes, 400)

            result = await service.capture_baseline(
                test_id="visual-002",
                test_name="Viewport Test",
                url="http://example.com/page",
                viewport_width=1280,
                viewport_height=720,
            )

            mock_capture.assert_called_once()
            call_args = mock_capture.call_args
            assert call_args[1]['viewport_width'] == 1280
            assert call_args[1]['viewport_height'] == 720

    @pytest.mark.asyncio
    async def test_capture_baseline_full_page(self, service, sample_image_bytes):
        """Test capturing full page baseline."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = (sample_image_bytes, 600)

            result = await service.capture_baseline(
                test_id="visual-003",
                test_name="Full Page Test",
                url="http://example.com/page",
                full_page=True,
            )

            mock_capture.assert_called_once()
            call_args = mock_capture.call_args
            assert call_args[1]['full_page'] is True

    @pytest.mark.asyncio
    async def test_capture_baseline_error(self, service):
        """Test baseline capture handles errors."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.side_effect = Exception("Browser failed")

            result = await service.capture_baseline(
                test_id="visual-004",
                test_name="Error Test",
                url="http://example.com/page",
            )

            assert result.result == ComparisonResult.ERROR
            assert "Browser failed" in result.error

    # =========================================================================
    # Visual Comparison Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_compare_with_baseline_match(self, service, sample_image_bytes):
        """Test comparison when screenshots match."""
        # First capture baseline
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = (sample_image_bytes, 500)

            await service.capture_baseline(
                test_id="compare-match",
                test_name="Match Test",
                url="http://legacy.example.com/page",
            )

            # Then compare with same image
            result = await service.compare_with_baseline(
                test_id="compare-match",
                test_name="Match Test",
                url="http://new.example.com/page",
            )

            assert result.result == ComparisonResult.MATCH
            assert result.match_percentage == 100.0
            assert result.diff_percentage == 0.0

    @pytest.mark.asyncio
    async def test_compare_with_baseline_mismatch(self, service, sample_image_bytes, different_image_bytes):
        """Test comparison when screenshots differ."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            # First call returns white image (baseline)
            mock_capture.return_value = (sample_image_bytes, 500)

            await service.capture_baseline(
                test_id="compare-mismatch",
                test_name="Mismatch Test",
                url="http://legacy.example.com/page",
            )

            # Second call returns red image (new)
            mock_capture.return_value = (different_image_bytes, 400)

            result = await service.compare_with_baseline(
                test_id="compare-mismatch",
                test_name="Mismatch Test",
                url="http://new.example.com/page",
            )

            assert result.result == ComparisonResult.MISMATCH
            assert result.match_percentage < 100.0
            assert result.diff_percentage > 0.0

    @pytest.mark.asyncio
    async def test_compare_with_threshold(self, service, sample_image_bytes):
        """Test comparison with custom diff threshold."""
        # Create slightly different image
        img = Image.new('RGB', (100, 100), color='white')
        # Add a small difference
        img.putpixel((50, 50), (255, 0, 0))
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        slightly_different = buffer.getvalue()

        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = (sample_image_bytes, 500)

            await service.capture_baseline(
                test_id="compare-threshold",
                test_name="Threshold Test",
                url="http://legacy.example.com/page",
            )

            mock_capture.return_value = (slightly_different, 400)

            # With high threshold, should pass
            result = await service.compare_with_baseline(
                test_id="compare-threshold",
                test_name="Threshold Test",
                url="http://new.example.com/page",
                diff_threshold=0.5,  # 50% allowed
            )

            # Difference is very small (1 pixel out of 10000)
            assert result.diff_percentage < 0.5

    @pytest.mark.asyncio
    async def test_compare_missing_baseline(self, service):
        """Test comparison without baseline returns error."""
        result = await service.compare_with_baseline(
            test_id="nonexistent",
            test_name="Missing Baseline Test",
            url="http://new.example.com/page",
        )

        assert result.result == ComparisonResult.ERROR
        assert "baseline" in result.error.lower()

    # =========================================================================
    # Batch Comparison Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_batch_comparison(self, service, sample_image_bytes):
        """Test batch visual comparison."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = (sample_image_bytes, 500)

            legacy_urls = [
                "http://legacy.example.com/page1",
                "http://legacy.example.com/page2",
            ]
            new_urls = [
                "http://new.example.com/page1",
                "http://new.example.com/page2",
            ]

            results = await service.run_batch_comparison(
                test_id="batch-001",
                test_name="Batch Test",
                legacy_urls=legacy_urls,
                new_urls=new_urls,
            )

            assert len(results) == 2
            assert all(r.result == ComparisonResult.MATCH for r in results)

    # =========================================================================
    # Image Comparison Logic Tests
    # =========================================================================

    def test_compare_identical_images(self, service):
        """Test comparison of identical images."""
        img = Image.new('RGB', (100, 100), color='blue')

        diff_percentage, diff_regions = service._compare_images(img, img)

        assert diff_percentage == 0.0
        assert len(diff_regions) == 0

    def test_compare_different_images(self, service):
        """Test comparison of different images."""
        img1 = Image.new('RGB', (100, 100), color='white')
        img2 = Image.new('RGB', (100, 100), color='black')

        diff_percentage, diff_regions = service._compare_images(img1, img2)

        assert diff_percentage > 0.0
        assert len(diff_regions) > 0

    def test_compare_partial_difference(self, service):
        """Test comparison with partial difference."""
        img1 = Image.new('RGB', (100, 100), color='white')
        img2 = Image.new('RGB', (100, 100), color='white')

        # Make bottom half different
        for x in range(100):
            for y in range(50, 100):
                img2.putpixel((x, y), (0, 0, 0))

        diff_percentage, diff_regions = service._compare_images(img1, img2)

        # Approximately 50% different
        assert 40.0 <= diff_percentage <= 60.0

    # =========================================================================
    # Diff Region Detection Tests
    # =========================================================================

    def test_detect_diff_regions(self, service):
        """Test detection of difference regions."""
        img1 = Image.new('RGB', (200, 200), color='white')
        img2 = Image.new('RGB', (200, 200), color='white')

        # Create a distinct region difference
        for x in range(50, 100):
            for y in range(50, 100):
                img2.putpixel((x, y), (255, 0, 0))

        _, diff_regions = service._compare_images(img1, img2)

        assert len(diff_regions) > 0
        # At least one region should be detected
        region = diff_regions[0]
        assert isinstance(region, DiffRegion)
        assert region.width > 0
        assert region.height > 0

    # =========================================================================
    # Baseline Management Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_update_baseline(self, service, sample_image_bytes, different_image_bytes):
        """Test updating a baseline."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = (sample_image_bytes, 500)

            await service.capture_baseline(
                test_id="update-baseline",
                test_name="Update Test",
                url="http://example.com/page",
            )

            # Get baseline path
            baseline = service.get_baseline("update-baseline")
            assert baseline is not None

            # Save new screenshot
            new_path = Path(service._baseline_dir) / "new_screenshot.png"
            with open(new_path, 'wb') as f:
                f.write(different_image_bytes)

            # Update baseline
            success = await service.update_baseline("update-baseline", str(new_path))
            assert success is True

    def test_get_nonexistent_baseline(self, service):
        """Test getting a baseline that doesn't exist."""
        baseline = service.get_baseline("nonexistent")
        assert baseline is None

    # =========================================================================
    # Dimension Handling Tests
    # =========================================================================

    def test_compare_different_dimensions(self, service):
        """Test comparison of images with different dimensions."""
        img1 = Image.new('RGB', (100, 100), color='white')
        img2 = Image.new('RGB', (200, 200), color='white')

        diff_percentage, diff_regions = service._compare_images(img1, img2)

        # Should detect dimension difference
        assert diff_percentage > 0.0 or len(diff_regions) > 0

    # =========================================================================
    # Hide Selectors Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_capture_with_hide_selectors(self, service, sample_image_bytes):
        """Test capturing with elements hidden."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = (sample_image_bytes, 500)

            result = await service.capture_baseline(
                test_id="hide-001",
                test_name="Hide Selectors Test",
                url="http://example.com/page",
                hide_selectors=[".timestamp", "#random-id", ".ad-banner"],
            )

            mock_capture.assert_called_once()
            call_args = mock_capture.call_args
            assert call_args[1]['hide_selectors'] == [".timestamp", "#random-id", ".ad-banner"]

    # =========================================================================
    # Wait For Selector Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_capture_with_wait_for_selector(self, service, sample_image_bytes):
        """Test capturing with wait for selector."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = (sample_image_bytes, 500)

            result = await service.capture_baseline(
                test_id="wait-001",
                test_name="Wait Selector Test",
                url="http://example.com/page",
                wait_for_selector=".content-loaded",
            )

            mock_capture.assert_called_once()
            call_args = mock_capture.call_args
            assert call_args[1]['wait_for_selector'] == ".content-loaded"

    # =========================================================================
    # Diff Image Generation Tests
    # =========================================================================

    def test_generate_diff_image(self, service):
        """Test generation of diff highlight image."""
        img1 = Image.new('RGB', (100, 100), color='white')
        img2 = Image.new('RGB', (100, 100), color='white')

        # Add difference
        for x in range(25, 75):
            for y in range(25, 75):
                img2.putpixel((x, y), (255, 0, 0))

        diff_image = service._generate_diff_image(img1, img2)

        assert diff_image is not None
        assert diff_image.size == (100, 100)
        # Diff areas should be highlighted
