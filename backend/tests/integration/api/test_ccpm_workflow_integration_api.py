"""
Week 89: CCPM Workflow Worktree Integration API Tests

Tests for workflow-specific worktree management endpoints.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime


@pytest.mark.asyncio
async def test_get_supported_workflow_types(client: AsyncClient):
    """Test getting supported workflow types."""
    response = await client.get("/api/ccpm/workflow-worktrees/types")

    assert response.status_code == 200
    data = response.json()
    assert "supported_types" in data
    assert "configs" in data
    assert "GREEN_PAPER" in data["supported_types"]
    assert "BROWN_PAPER" in data["supported_types"]
    assert "MIGRATION" in data["supported_types"]
    assert "NEW_FEATURE" in data["supported_types"]
    assert "BUG" in data["supported_types"]


@pytest.mark.asyncio
async def test_workflow_config_structure(client: AsyncClient):
    """Test workflow configuration structure."""
    response = await client.get("/api/ccpm/workflow-worktrees/types")

    assert response.status_code == 200
    data = response.json()
    configs = data["configs"]

    # Check GREEN_PAPER config
    assert "GREEN_PAPER" in configs
    gp_config = configs["GREEN_PAPER"]
    assert "phases" in gp_config
    assert "agents" in gp_config
    assert "base_branch" in gp_config
    assert "merge_strategy" in gp_config
    assert gp_config["phases"] == ["analysis", "architecture", "implementation"]
    assert gp_config["agents"] == ["peter", "felix", "diana"]


@pytest.mark.asyncio
async def test_start_workflow_session_validation(client: AsyncClient):
    """Test workflow session start with invalid workflow type."""
    request_data = {
        "workflow_type": "INVALID_TYPE",
        "project_id": 1
    }

    response = await client.post("/api/ccpm/workflow-worktrees/start", json=request_data)

    assert response.status_code == 400
    assert "Unsupported workflow type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_workflow_worktrees_validation(client: AsyncClient):
    """Test listing worktrees with invalid workflow type."""
    response = await client.get("/api/ccpm/workflow-worktrees/INVALID_TYPE/1")

    assert response.status_code == 400
    assert "Unsupported workflow type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_workflow_worktrees_empty(client: AsyncClient):
    """Test listing worktrees when none exist."""
    response = await client.get("/api/ccpm/workflow-worktrees/GREEN_PAPER/9999")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_merge_workflow_session_validation(client: AsyncClient):
    """Test merge with invalid workflow type."""
    response = await client.post("/api/ccpm/workflow-worktrees/INVALID_TYPE/1/merge")

    assert response.status_code == 400
    assert "Unsupported workflow type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_sync_workflow_worktrees_validation(client: AsyncClient):
    """Test sync with invalid workflow type."""
    response = await client.post("/api/ccpm/workflow-worktrees/INVALID_TYPE/1/sync")

    assert response.status_code == 400
    assert "Unsupported workflow type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cleanup_workflow_session_validation(client: AsyncClient):
    """Test cleanup with invalid workflow type."""
    response = await client.delete("/api/ccpm/workflow-worktrees/INVALID_TYPE/1")

    assert response.status_code == 400
    assert "Unsupported workflow type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_workflow_worktree_stats(client: AsyncClient):
    """Test getting workflow worktree statistics."""
    response = await client.get("/api/ccpm/workflow-worktrees/stats")

    assert response.status_code == 200
    data = response.json()
    assert "by_workflow" in data
    assert "supported_workflows" in data
    assert "GREEN_PAPER" in data["by_workflow"]
    assert "BROWN_PAPER" in data["by_workflow"]


@pytest.mark.asyncio
async def test_workflow_worktree_stats_with_project(client: AsyncClient):
    """Test getting workflow worktree statistics for specific project."""
    response = await client.get("/api/ccpm/workflow-worktrees/stats", params={"project_id": 1})

    assert response.status_code == 200
    data = response.json()
    assert "by_workflow" in data


@pytest.mark.asyncio
async def test_complete_phase_not_found(client: AsyncClient):
    """Test completing phase for non-existent worktree."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.post(
        f"/api/ccpm/workflow-worktrees/{fake_id}/complete-phase",
        json={"message": "Complete phase"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_workflow_config_merge_strategies(client: AsyncClient):
    """Test different merge strategies in workflow configs."""
    response = await client.get("/api/ccpm/workflow-worktrees/types")

    assert response.status_code == 200
    configs = response.json()["configs"]

    # GREEN_PAPER and BROWN_PAPER use sequential
    assert configs["GREEN_PAPER"]["merge_strategy"] == "sequential"
    assert configs["BROWN_PAPER"]["merge_strategy"] == "sequential"

    # MIGRATION uses parallel
    assert configs["MIGRATION"]["merge_strategy"] == "parallel"

    # NEW_FEATURE uses PR
    assert configs["NEW_FEATURE"]["merge_strategy"] == "pr_required"

    # BUG uses immediate
    assert configs["BUG"]["merge_strategy"] == "immediate"


@pytest.mark.asyncio
async def test_workflow_base_branches(client: AsyncClient):
    """Test base branches for different workflows."""
    response = await client.get("/api/ccpm/workflow-worktrees/types")

    assert response.status_code == 200
    configs = response.json()["configs"]

    # Most workflows use main
    assert configs["GREEN_PAPER"]["base_branch"] == "main"
    assert configs["BROWN_PAPER"]["base_branch"] == "main"
    assert configs["BUG"]["base_branch"] == "main"

    # NEW_FEATURE uses develop
    assert configs["NEW_FEATURE"]["base_branch"] == "develop"


@pytest.mark.asyncio
async def test_workflow_agents_assignment(client: AsyncClient):
    """Test correct agent assignment for workflows."""
    response = await client.get("/api/ccpm/workflow-worktrees/types")

    assert response.status_code == 200
    configs = response.json()["configs"]

    # BUG workflow uses betty and tessa
    assert "betty" in configs["BUG"]["agents"]
    assert "tessa" in configs["BUG"]["agents"]

    # MIGRATION uses miguel, felix, tessa
    assert "miguel" in configs["MIGRATION"]["agents"]

    # GREEN_PAPER uses peter, felix, diana
    assert "peter" in configs["GREEN_PAPER"]["agents"]


@pytest.mark.asyncio
async def test_list_empty_workflow_worktrees(client: AsyncClient):
    """Test listing worktrees for valid workflow with no worktrees."""
    response = await client.get("/api/ccpm/workflow-worktrees/GREEN_PAPER/99999")

    assert response.status_code == 200
    data = response.json()
    assert data == []
