"""
Tests for Improve Skills API - Week 60

Tests the agent skill improvement functionality.
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
async def test_list_agents(client):
    """Test listing all agents available for improvement."""
    async with client as ac:
        response = await ac.get("/api/improve-skills/agents")
        assert response.status_code == 200

        agents = response.json()
        assert len(agents) == 10  # 10 core agents

        # Check all core agents exist
        agent_ids = [a["id"] for a in agents]
        assert "felix" in agent_ids
        assert "quinn" in agent_ids
        assert "betty" in agent_ids
        assert "eliza" in agent_ids
        assert "diana" in agent_ids
        assert "marcus" in agent_ids
        assert "tessa" in agent_ids
        assert "miguel" in agent_ids
        assert "peter" in agent_ids
        assert "paul" in agent_ids


@pytest.mark.asyncio
async def test_get_agent_skills(client):
    """Test getting skills for a specific agent."""
    async with client as ac:
        response = await ac.get("/api/improve-skills/agents/felix")
        assert response.status_code == 200

        agent = response.json()
        assert agent["id"] == "felix"
        assert agent["name"] == "Felix"
        assert agent["role"] == "Feature Architect"
        assert len(agent["base_skills"]) >= 5
        assert "System design" in agent["base_skills"][0]


@pytest.mark.asyncio
async def test_get_nonexistent_agent(client):
    """Test getting skills for an agent that doesn't exist."""
    async with client as ac:
        response = await ac.get("/api/improve-skills/agents/invalid_agent")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_analyze_felix_skills(client):
    """Test analyzing Felix's skills for improvement."""
    async with client as ac:
        response = await ac.post("/api/improve-skills/analyze", json={
            "agent_id": "felix"
        })
        assert response.status_code == 200

        result = response.json()
        assert result["agent_id"] == "felix"
        assert result["agent_name"] == "Felix"
        assert "current_skills" in result
        assert "suggested_improvements" in result
        assert "improvement_score" in result
        assert 0 <= result["improvement_score"] <= 1


@pytest.mark.asyncio
async def test_analyze_with_focus_area(client):
    """Test analyzing skills with a specific focus area."""
    async with client as ac:
        response = await ac.post("/api/improve-skills/analyze", json={
            "agent_id": "quinn",
            "focus_area": "security"
        })
        assert response.status_code == 200

        result = response.json()
        assert result["agent_id"] == "quinn"
        # Suggestions should prioritize security-related skills
        suggestions = result["suggested_improvements"]
        assert len(suggestions) > 0


@pytest.mark.asyncio
async def test_analyze_all_agents(client):
    """Test that all 10 agents can be analyzed."""
    agent_ids = ["felix", "quinn", "betty", "eliza", "diana",
                 "marcus", "tessa", "miguel", "peter", "paul"]

    async with client as ac:
        for agent_id in agent_ids:
            response = await ac.post("/api/improve-skills/analyze", json={
                "agent_id": agent_id
            })
            assert response.status_code == 200, f"Failed for agent: {agent_id}"
            result = response.json()
            assert result["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_apply_improvements(client):
    """Test applying improvements to an agent."""
    async with client as ac:
        response = await ac.post(
            "/api/improve-skills/apply",
            params={"agent_id": "felix"},
            json=["Microservices decomposition", "API versioning"]
        )
        assert response.status_code == 200

        result = response.json()
        assert result["agent_id"] == "felix"
        assert result["status"] == "queued"
        assert len(result["improvements_queued"]) == 2


@pytest.mark.asyncio
async def test_get_improvement_history(client):
    """Test getting improvement history for an agent."""
    async with client as ac:
        response = await ac.get("/api/improve-skills/history/felix")
        assert response.status_code == 200

        history = response.json()
        assert isinstance(history, list)
        # Check history structure
        if len(history) > 0:
            entry = history[0]
            assert "timestamp" in entry
            assert "improvement" in entry
            assert "impact_score" in entry


@pytest.mark.asyncio
async def test_improvement_recommendation(client):
    """Test that recommendations are generated based on score."""
    async with client as ac:
        response = await ac.post("/api/improve-skills/analyze", json={
            "agent_id": "betty"
        })
        assert response.status_code == 200

        result = response.json()
        assert "recommendation" in result
        assert len(result["recommendation"]) > 0
