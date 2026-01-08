"""
Tests for Quick Spec API - Week 60

Tests the quick spec template generation functionality.
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.fixture
def client():
    """Create async test client."""
    from httpx import ASGITransport
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_list_templates(client):
    """Test listing all quick spec templates."""
    async with client as ac:
        response = await ac.get("/quick-specs/templates")
        assert response.status_code == 200

        templates = response.json()
        assert len(templates) == 4

        # Check all template types exist
        types = [t["type"] for t in templates]
        assert "bug_fix" in types
        assert "enhancement" in types
        assert "refactoring" in types
        assert "hotfix" in types


@pytest.mark.asyncio
async def test_get_bug_fix_template(client):
    """Test getting bug fix template details."""
    async with client as ac:
        response = await ac.get("/quick-specs/templates/bug_fix")
        assert response.status_code == 200

        template = response.json()
        assert template["type"] == "bug_fix"
        assert template["name"] == "Bug Fix"
        assert "title" in template["required_fields"]
        assert "reproduction_steps" in template["required_fields"]
        assert "template" in template


@pytest.mark.asyncio
async def test_get_nonexistent_template(client):
    """Test getting a template that doesn't exist."""
    async with client as ac:
        response = await ac.get("/quick-specs/templates/invalid_type")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_bug_fix_spec(client):
    """Test generating a bug fix specification."""
    async with client as ac:
        response = await ac.post("/quick-specs/generate", json={
            "template_type": "bug_fix",
            "fields": {
                "title": "Login button not working",
                "reproduction_steps": "1. Go to login page\n2. Click login",
                "expected_behavior": "User should be logged in",
                "actual_behavior": "Nothing happens"
            }
        })
        assert response.status_code == 200

        result = response.json()
        assert result["type"] == "bug_fix"
        assert "Login button not working" in result["content"]
        assert "generated_at" in result


@pytest.mark.asyncio
async def test_generate_spec_missing_fields(client):
    """Test generating spec with missing required fields."""
    async with client as ac:
        response = await ac.post("/quick-specs/generate", json={
            "template_type": "bug_fix",
            "fields": {
                "title": "Bug title only"
                # Missing reproduction_steps, expected_behavior, actual_behavior
            }
        })
        assert response.status_code == 400
        assert "Missing required fields" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_enhancement_spec(client):
    """Test generating an enhancement specification."""
    async with client as ac:
        response = await ac.post("/quick-specs/generate", json={
            "template_type": "enhancement",
            "fields": {
                "title": "Add dark mode",
                "current_behavior": "Only light theme available",
                "desired_behavior": "User can toggle dark mode",
                "user_benefit": "Reduces eye strain"
            }
        })
        assert response.status_code == 200

        result = response.json()
        assert result["type"] == "enhancement"
        assert "dark mode" in result["content"].lower()


@pytest.mark.asyncio
async def test_generate_hotfix_spec(client):
    """Test generating a hotfix specification."""
    async with client as ac:
        response = await ac.post("/quick-specs/generate", json={
            "template_type": "hotfix",
            "fields": {
                "title": "Payment processing failure",
                "issue_description": "All payments failing since last deploy",
                "impact": "Revenue loss, customer complaints",
                "fix_description": "Revert database migration"
            }
        })
        assert response.status_code == 200

        result = response.json()
        assert result["type"] == "hotfix"
        assert "HOTFIX" in result["content"]
        assert "URGENT" in result["content"]


@pytest.mark.asyncio
async def test_validate_fields(client):
    """Test field validation without generating."""
    async with client as ac:
        response = await ac.post("/quick-specs/validate", json={
            "template_type": "bug_fix",
            "fields": {
                "title": "Test bug"
            }
        })
        assert response.status_code == 200

        result = response.json()
        assert result["valid"] is False
        assert "reproduction_steps" in result["missing_required"]


@pytest.mark.asyncio
async def test_list_template_types(client):
    """Test listing template types for dropdowns."""
    async with client as ac:
        response = await ac.get("/quick-specs/types")
        assert response.status_code == 200

        types = response.json()
        assert len(types) == 4

        # Check structure
        for t in types:
            assert "value" in t
            assert "label" in t
            assert "icon" in t
