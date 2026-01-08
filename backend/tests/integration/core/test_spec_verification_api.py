"""
Tests for Spec Verification API (Week 60)

Agent OS Concepts:
1. Visual asset validation
2. Reusability check
3. Mandatory visuals folder
4. Strict scope limitation
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestSpecVerificationEndpoints:
    """Test spec verification endpoints."""

    def test_verify_spec_basic(self, client):
        """Test basic spec verification."""
        response = client.post(
            "/api/spec-verification/verify",
            json={
                "spec_content": """# Feature Spec

## Scope
This feature handles authentication.

### In Scope
- Login

### Out of Scope
- Social login

## Acceptance Criteria
- User can log in
""",
                "level": "standard"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall_passed" in data
        assert "score" in data
        assert "by_category" in data

    def test_verify_spec_with_visuals(self, client):
        """Test spec verification with visual references."""
        response = client.post(
            "/api/spec-verification/verify",
            json={
                "spec_content": """# Feature Spec

![Architecture](./visuals/arch.png)

```mermaid
graph TD
A --> B
```

## Scope
This feature handles data processing.
""",
                "level": "lenient"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "by_category" in data
        if "visual_assets" in data["by_category"]:
            visual_data = data["by_category"]["visual_assets"]
            # Should have visual references detected
            assert "score" in visual_data

    def test_verify_visual_assets_only(self, client):
        """Test visual assets verification endpoint."""
        response = client.post(
            "/api/spec-verification/verify-visual-assets",
            params={
                "spec_content": "# Spec with ![image](./img.png)"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "visual_assets"
        assert "passed" in data
        assert "score" in data
        assert "checks" in data

    def test_verify_reusability_only(self, client):
        """Test reusability verification endpoint."""
        response = client.post(
            "/api/spec-verification/verify-reusability",
            params={
                "spec_content": """# Design
Uses factory pattern for providers.
Dependency injection for services.
No hardcoded values.
"""
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "reusability"
        assert "passed" in data
        assert "score" in data

    def test_verify_scope_only(self, client):
        """Test scope verification endpoint."""
        response = client.post(
            "/api/spec-verification/verify-scope",
            params={
                "spec_content": """# Feature

## Scope
### In Scope
- Core feature

### Out of Scope
- Extended feature

## Acceptance Criteria
- Works correctly
"""
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "scope"
        assert "passed" in data
        assert data["score"] >= 0

    def test_verify_structure(self, client, tmp_path):
        """Test structure verification endpoint."""
        # Create minimal project structure
        doc_path = tmp_path / "doc"
        doc_path.mkdir()
        (tmp_path / "README.md").write_text("# Project")

        response = client.post(
            "/api/spec-verification/verify-structure",
            json={
                "project_path": str(tmp_path),
                "level": "standard"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "structure"
        assert "checks" in data

    def test_list_verification_levels(self, client):
        """Test levels endpoint."""
        response = client.get("/api/spec-verification/levels")
        assert response.status_code == 200
        levels = response.json()
        assert len(levels) == 3
        level_values = [l["value"] for l in levels]
        assert "lenient" in level_values
        assert "standard" in level_values
        assert "strict" in level_values

    def test_list_verification_categories(self, client):
        """Test categories endpoint."""
        response = client.get("/api/spec-verification/categories")
        assert response.status_code == 200
        categories = response.json()
        assert len(categories) == 4
        cat_names = [c["category"] for c in categories]
        assert "visual_assets" in cat_names
        assert "reusability" in cat_names
        assert "scope" in cat_names
        assert "structure" in cat_names

    def test_create_visuals_folder(self, client, tmp_path):
        """Test visuals folder creation endpoint."""
        response = client.post(
            "/api/spec-verification/create-visuals-folder",
            json={"project_path": str(tmp_path)}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["created"]) > 0
        assert "visuals_path" in data

        # Verify folders were created
        assert (tmp_path / "doc" / "visuals").exists()
        assert (tmp_path / "doc" / "visuals" / "diagrams").exists()
        assert (tmp_path / "doc" / "visuals" / "screenshots").exists()
        assert (tmp_path / "doc" / "visuals" / "mockups").exists()


class TestSpecVerificationService:
    """Test spec verification service directly."""

    def test_service_import(self):
        """Test service can be imported."""
        from app.services.spec_verification_service import (
            SpecVerificationService,
            VerificationLevel,
            VerificationCategory
        )
        assert SpecVerificationService is not None
        assert len(VerificationLevel) == 3
        assert len(VerificationCategory) == 4

    def test_service_verify(self):
        """Test service verification method."""
        from app.services.spec_verification_service import SpecVerificationService

        svc = SpecVerificationService()
        result = svc.verify_spec("# Simple Spec\n\nNo scope defined.")

        assert hasattr(result, "passed")
        assert hasattr(result, "score")
        assert hasattr(result, "checks")
        assert len(result.checks) > 0

    def test_service_summary(self):
        """Test service summary method."""
        from app.services.spec_verification_service import SpecVerificationService

        svc = SpecVerificationService()
        result = svc.verify_spec("# Spec with scope\n\n## Scope\nIn scope items.")
        summary = svc.get_verification_summary(result)

        assert "overall_passed" in summary
        assert "score" in summary
        assert "by_category" in summary
        assert "timestamp" in summary

    def test_verification_levels(self):
        """Test different verification levels."""
        from app.services.spec_verification_service import (
            SpecVerificationService,
            VerificationLevel
        )

        svc = SpecVerificationService()
        spec = "# Minimal spec without acceptance criteria"

        # Lenient should pass more easily
        lenient_result = svc.verify_spec(spec, level=VerificationLevel.LENIENT)

        # Strict should have more errors
        strict_result = svc.verify_spec(spec, level=VerificationLevel.STRICT)

        # Strict should typically have more errors or warnings
        assert strict_result.errors >= lenient_result.errors or strict_result.warnings >= lenient_result.warnings
