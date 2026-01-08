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
            yield VisualRegressionService(screenshots_dir=tmpdir)

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
            mock_capture.return_value = sample_image_bytes

            result = await service.capture_baseline(
                test_id="visual-001",
                test_name="Baseline Capture Test",
                url="http://example.com/page",
            )

            assert result.result == ComparisonResult.NEW_BASELINE
            assert result.baseline_path is not None
            assert result.error is None

    @pytest.mark.asyncio
    async def test_capture_baseline_with_viewport(self, service, sample_image_bytes):
        """Test capturing baseline with custom viewport."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = sample_image_bytes

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
            mock_capture.return_value = sample_image_bytes

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
            mock_capture.return_value = sample_image_bytes

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
            # Match means diff_percentage is 0 or very low
            assert result.diff_percentage == 0.0

    @pytest.mark.asyncio
    async def test_compare_with_baseline_mismatch(self, service, sample_image_bytes, different_image_bytes):
        """Test comparison when screenshots differ."""
        # Create diffs directory for diff image storage
        diffs_dir = service._screenshots_dir / "diffs"
        diffs_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            # First call returns white image (baseline)
            mock_capture.return_value = sample_image_bytes

            await service.capture_baseline(
                test_id="compare-mismatch",
                test_name="Mismatch Test",
                url="http://legacy.example.com/page",
            )

            # Second call returns red image (new)
            mock_capture.return_value = different_image_bytes

            result = await service.compare_with_baseline(
                test_id="compare-mismatch",
                test_name="Mismatch Test",
                url="http://new.example.com/page",
            )

            assert result.result == ComparisonResult.MISMATCH
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
            mock_capture.return_value = sample_image_bytes

            await service.capture_baseline(
                test_id="compare-threshold",
                test_name="Threshold Test",
                url="http://legacy.example.com/page",
            )

            mock_capture.return_value = slightly_different

            # With high threshold, should pass
            result = await service.compare_with_baseline(
                test_id="compare-threshold",
                test_name="Threshold Test",
                url="http://new.example.com/page",
                threshold=0.5,  # 50% allowed
            )

            # Difference is very small (1 pixel out of 10000)
            assert result.diff_percentage < 0.5

    @pytest.mark.asyncio
    async def test_compare_missing_baseline(self, service):
        """Test comparison without baseline returns error."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = b''  # Not called but needed to prevent error

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
            mock_capture.return_value = sample_image_bytes

            # First capture baselines for both pages
            pages = [
                {"url": "http://example.com/page1", "name": "Page 1"},
                {"url": "http://example.com/page2", "name": "Page 2"},
            ]

            # Capture baselines first
            for i, page in enumerate(pages):
                await service.capture_baseline(
                    test_id=f"batch-001_page_{i}",
                    test_name=f"Batch Test - {page['name']}",
                    url=page["url"],
                )

            results = await service.run_batch_comparison(
                test_id="batch-001",
                test_name="Batch Test",
                pages=pages,
            )

            assert len(results) == 2
            assert all(r.result == ComparisonResult.MATCH for r in results)

    # =========================================================================
    # Image Comparison Logic Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_compare_identical_images(self, service, sample_image_bytes):
        """Test comparison of identical images."""
        # Save a baseline first
        baseline_path = service._get_baseline_path("identical-test")
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_bytes(sample_image_bytes)

        result = await service._compare_images(baseline_path, sample_image_bytes, "identical-test")

        assert result["diff_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_compare_different_images(self, service, sample_image_bytes, different_image_bytes):
        """Test comparison of different images."""
        # Save a baseline first
        baseline_path = service._get_baseline_path("different-test")
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_bytes(sample_image_bytes)

        # Create diffs directory for diff image storage
        diffs_dir = service._screenshots_dir / "diffs"
        diffs_dir.mkdir(parents=True, exist_ok=True)

        result = await service._compare_images(baseline_path, different_image_bytes, "different-test")

        assert result["diff_percentage"] > 0.0

    @pytest.mark.asyncio
    async def test_compare_partial_difference(self, service):
        """Test comparison with partial difference."""
        # Create white image for baseline
        img1 = Image.new('RGB', (100, 100), color='white')
        buffer1 = io.BytesIO()
        img1.save(buffer1, format='PNG')
        baseline_bytes = buffer1.getvalue()

        # Create image with bottom half different
        img2 = Image.new('RGB', (100, 100), color='white')
        for x in range(100):
            for y in range(50, 100):
                img2.putpixel((x, y), (0, 0, 0))
        buffer2 = io.BytesIO()
        img2.save(buffer2, format='PNG')
        actual_bytes = buffer2.getvalue()

        # Save baseline
        baseline_path = service._get_baseline_path("partial-test")
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_bytes(baseline_bytes)

        # Create diffs directory for diff image storage
        diffs_dir = service._screenshots_dir / "diffs"
        diffs_dir.mkdir(parents=True, exist_ok=True)

        result = await service._compare_images(baseline_path, actual_bytes, "partial-test")

        # Approximately 50% different
        assert 40.0 <= result["diff_percentage"] <= 60.0

    # =========================================================================
    # Diff Region Detection Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_detect_diff_regions(self, service):
        """Test detection of difference regions."""
        # Create white image for baseline
        img1 = Image.new('RGB', (200, 200), color='white')
        buffer1 = io.BytesIO()
        img1.save(buffer1, format='PNG')
        baseline_bytes = buffer1.getvalue()

        # Create image with distinct region difference
        img2 = Image.new('RGB', (200, 200), color='white')
        for x in range(50, 100):
            for y in range(50, 100):
                img2.putpixel((x, y), (255, 0, 0))
        buffer2 = io.BytesIO()
        img2.save(buffer2, format='PNG')
        actual_bytes = buffer2.getvalue()

        # Save baseline
        baseline_path = service._get_baseline_path("regions-test")
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_bytes(baseline_bytes)

        # Create diffs directory for diff image storage
        diffs_dir = service._screenshots_dir / "diffs"
        diffs_dir.mkdir(parents=True, exist_ok=True)

        result = await service._compare_images(baseline_path, actual_bytes, "regions-test")

        assert len(result["diff_regions"]) > 0
        region = result["diff_regions"][0]
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
            mock_capture.return_value = sample_image_bytes

            await service.capture_baseline(
                test_id="update-baseline",
                test_name="Update Test",
                url="http://example.com/page",
            )

            # Get baseline info
            baseline_info = service.get_baseline_info("update-baseline")
            assert baseline_info is not None

            # Capture an actual screenshot to update from
            actual_path = service._get_actual_path("update-baseline")
            actual_path.parent.mkdir(parents=True, exist_ok=True)
            actual_path.write_bytes(different_image_bytes)

            # Update baseline from actual
            success = await service.update_baseline("update-baseline", from_actual=True)
            assert success is True

    def test_get_nonexistent_baseline(self, service):
        """Test getting a baseline that doesn't exist."""
        baseline_info = service.get_baseline_info("nonexistent")
        assert baseline_info is None

    # =========================================================================
    # Dimension Handling Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_compare_different_dimensions(self, service):
        """Test comparison of images with different dimensions."""
        # Create 100x100 baseline
        img1 = Image.new('RGB', (100, 100), color='white')
        buffer1 = io.BytesIO()
        img1.save(buffer1, format='PNG')
        baseline_bytes = buffer1.getvalue()

        # Create 200x200 actual image
        img2 = Image.new('RGB', (200, 200), color='white')
        buffer2 = io.BytesIO()
        img2.save(buffer2, format='PNG')
        actual_bytes = buffer2.getvalue()

        # Save baseline
        baseline_path = service._get_baseline_path("dimension-test")
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_bytes(baseline_bytes)

        # Should resize and compare - with same colors should match
        result = await service._compare_images(baseline_path, actual_bytes, "dimension-test")

        # After resize, white images should match
        assert result["diff_percentage"] == 0.0

    # =========================================================================
    # Hide Selectors Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_capture_with_hide_selectors(self, service, sample_image_bytes):
        """Test capturing with elements hidden."""
        with patch.object(service, '_capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = sample_image_bytes

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
            mock_capture.return_value = sample_image_bytes

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

    def test_create_diff_image(self, service):
        """Test generation of diff highlight image."""
        img1 = Image.new('RGB', (100, 100), color='white')
        img2 = Image.new('RGB', (100, 100), color='white')

        # Add difference
        for x in range(25, 75):
            for y in range(25, 75):
                img2.putpixel((x, y), (255, 0, 0))

        from PIL import ImageChops
        diff = ImageChops.difference(img1, img2)

        diff_image = service._create_diff_image(img1, img2, diff)

        assert diff_image is not None
        assert diff_image.size == (100, 100)
        # Diff areas should be highlighted
