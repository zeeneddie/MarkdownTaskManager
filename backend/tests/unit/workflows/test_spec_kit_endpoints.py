"""
E2E API tests for Spec-Kit workflow endpoints

Tests all 4 Spec-Kit endpoints with real HTTP calls:
1. POST /api/workflows/spec-kit - Complete 3-stage workflow
2. POST /api/workflows/spec-kit/constitution - Constitution only
3. POST /api/workflows/spec-kit/specification - Specification only
4. POST /api/workflows/spec-kit/tasks - Tasks only

NOTE: These tests require the TypeScript agent system to be running.
Skip when agents are unavailable.
"""
import pytest
from httpx import AsyncClient
import json
import os
from pathlib import Path
from typing import Dict, Any

# Check if TypeScript agents are available and functional
# These tests require:
# 1. agents/dist/*.js to exist (TypeScript compiled)
# 2. Node.js and ts-node to be available
# 3. Ollama or other LLM providers to be running
AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "agents"
RUN_AGENT_INTEGRATION_TESTS = os.getenv("RUN_AGENT_INTEGRATION_TESTS", "false").lower() == "true"

# Skip all tests in this module unless explicitly enabled
pytestmark = pytest.mark.skipif(
    not RUN_AGENT_INTEGRATION_TESTS,
    reason="Agent integration tests disabled. Set RUN_AGENT_INTEGRATION_TESTS=true to run."
)


# ========================================
# TEST DATA
# ========================================

SAMPLE_REQUEST_MINIMAL = {
    "business_case": "Build a modern task management system for agile teams",
    "stakeholders": ["Product Owner", "Development Team", "End Users"],
    "constraints": [
        "Budget: €50,000",
        "Timeline: 6 months",
        "Team size: 5 developers"
    ],
    "success_criteria": [
        "Support 1,000 concurrent users",
        "99.5% uptime",
        "< 3 second page load time"
    ]
}

SAMPLE_REQUEST_FULL = {
    "business_case": "Build an e-commerce platform to enable online sales for small and medium businesses",
    "stakeholders": ["CEO", "CTO", "Sales Team", "Customer Support", "End Users"],
    "constraints": [
        "Budget: €100,000",
        "Timeline: 9 months",
        "Team size: 8 developers (4 frontend, 4 backend)",
        "Must integrate with existing inventory system",
        "PCI-DSS compliance required"
    ],
    "success_criteria": [
        "Support 10,000 concurrent users",
        "99.9% uptime",
        "< 2 second page load time",
        "Payment processing PCI-DSS compliant",
        "Support for 5 payment methods",
        "Mobile-responsive design"
    ],
    "technical_context": {
        "existing_systems": ["Legacy Inventory DB", "CRM System (Salesforce)", "Email Marketing (Mailchimp)"],
        "technologies": ["FastAPI", "Vue.js 3", "PostgreSQL", "Redis", "Docker"],
        "team_size": 8,
        "timeline": "9 months",
        "deployment_target": "AWS ECS",
        "compliance_requirements": ["PCI-DSS", "GDPR"]
    },
    "project_path": "projects/ecommerce-platform",
    "project_name": "E-commerce Platform"
}


# ========================================
# HELPER FUNCTIONS
# ========================================

def assert_constitution_structure(result: Dict[str, Any]):
    """Validate constitution result structure"""
    assert "principles" in result, "Constitution must include principles"
    assert "requirements" in result, "Constitution must include requirements"
    assert "constraints" in result, "Constitution must include constraints"
    assert "risks" in result, "Constitution must include risks"
    assert "scope" in result, "Constitution must include scope"

    # Principles validation
    assert isinstance(result["principles"], list), "Principles must be a list"
    assert len(result["principles"]) >= 3, "Must have at least 3 guiding principles"

    # Requirements validation
    assert "functional" in result["requirements"], "Must have functional requirements"
    assert "non_functional" in result["requirements"], "Must have non-functional requirements"
    assert isinstance(result["requirements"]["functional"], list)
    assert isinstance(result["requirements"]["non_functional"], list)

    # Scope validation
    assert "in_scope" in result["scope"], "Must define in-scope items"
    assert "out_of_scope" in result["scope"], "Must define out-of-scope items"


def assert_specification_structure(result: Dict[str, Any]):
    """Validate specification result structure"""
    assert "architecture" in result, "Specification must include architecture"
    assert "components" in result, "Specification must include components"
    assert "interfaces" in result, "Specification must include interfaces"
    assert "data_model" in result, "Specification must include data model"
    assert "quality_requirements" in result, "Specification must include quality requirements"

    # Architecture validation
    assert "pattern" in result["architecture"], "Must specify architecture pattern"
    assert result["architecture"]["pattern"] in [
        "Monolith", "Microservices", "Serverless", "Modular Monolith",
        "Event-Driven", "Layered", "Hexagonal", "CQRS"
    ], "Must use recognized architecture pattern"

    # Components validation
    assert isinstance(result["components"], list), "Components must be a list"
    assert len(result["components"]) > 0, "Must have at least one component"
    if result["components"]:
        component = result["components"][0]
        assert "name" in component
        assert "responsibility" in component
        assert "dependencies" in component


def assert_tasks_structure(result: Dict[str, Any]):
    """Validate tasks result structure"""
    assert "epics" in result, "Tasks must include epics"
    assert "features" in result, "Tasks must include features"
    assert "stories" in result, "Tasks must include stories"
    assert "tasks" in result, "Tasks must include tasks"

    # Epics validation
    assert isinstance(result["epics"], list), "Epics must be a list"
    assert len(result["epics"]) > 0, "Must have at least one epic"

    # Features validation
    assert isinstance(result["features"], list), "Features must be a list"

    # Validate epic structure
    if result["epics"]:
        epic = result["epics"][0]
        assert "name" in epic
        assert "description" in epic
        assert "story_points" in epic
        # CRITICAL: All estimates must be TBD (Planning Poker)
        assert epic["story_points"] in [0, None, "TBD"], \
            f"Epic estimates must be TBD for Planning Poker, got: {epic['story_points']}"


def assert_generated_files_structure(files: list):
    """Validate generated files structure"""
    assert isinstance(files, list), "Files must be a list"
    assert len(files) >= 4, "Must generate at least 4 files (constitution, specification, tasks, metadata)"

    # Check required files are present
    file_paths = [f["path"] for f in files]
    assert any("constitution" in p for p in file_paths), "Must include constitution.md"
    assert any("specification" in p for p in file_paths), "Must include specification.md"
    assert any("tasks" in p for p in file_paths), "Must include tasks.md"
    assert any("metadata" in p for p in file_paths), "Must include metadata.json"

    # Validate each file has required fields
    for file in files:
        assert "path" in file, "File must have path"
        assert "content" in file, "File must have content"
        assert isinstance(file["content"], str), "File content must be string"
        assert len(file["content"]) > 0, "File content must not be empty"


# ========================================
# ENDPOINT TESTS
# ========================================

@pytest.mark.asyncio
async def test_complete_spec_kit_workflow(client: AsyncClient):
    """Test complete Spec-Kit workflow (Constitution → Specification → Tasks)"""

    response = await client.post(
        "/api/workflows/spec-kit",
        json=SAMPLE_REQUEST_FULL
    )

    # Basic response validation
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    result = response.json()

    # Validate response structure
    assert "status" in result, "Response must include status"
    assert result["status"] == "success", f"Expected success, got: {result.get('status')}"

    assert "constitution" in result, "Response must include constitution"
    assert "specification" in result, "Response must include specification"
    assert "tasks" in result, "Response must include tasks"
    assert "files" in result, "Response must include files"
    assert "workflow_summary" in result, "Response must include workflow summary"

    # Validate each stage
    assert_constitution_structure(result["constitution"])
    assert_specification_structure(result["specification"])
    assert_tasks_structure(result["tasks"])
    assert_generated_files_structure(result["files"])

    # Validate workflow summary
    summary = result["workflow_summary"]
    assert "total_time" in summary
    assert "stages_completed" in summary
    assert summary["stages_completed"] == 3, "All 3 stages must complete"

    print(f"✅ Complete workflow test passed - {summary['stages_completed']} stages in {summary['total_time']}s")


@pytest.mark.asyncio
async def test_constitution_stage_only(client: AsyncClient):
    """Test Constitution stage only"""

    response = await client.post(
        "/api/workflows/spec-kit/constitution",
        json=SAMPLE_REQUEST_MINIMAL
    )

    # Basic validation
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    result = response.json()

    # Validate constitution structure
    assert_constitution_structure(result)

    # Validate principles content
    principles = result["principles"]
    assert all(isinstance(p, dict) for p in principles), "Each principle must be a dict"
    assert all("name" in p and "description" in p for p in principles), \
        "Each principle must have name and description"

    # Validate requirements
    functional_reqs = result["requirements"]["functional"]
    assert len(functional_reqs) > 0, "Must have functional requirements"
    assert all(isinstance(req, str) for req in functional_reqs), "Requirements must be strings"

    print(f"✅ Constitution test passed - {len(principles)} principles, "
          f"{len(functional_reqs)} functional requirements")


@pytest.mark.asyncio
async def test_specification_stage_only(client: AsyncClient):
    """Test Specification stage only"""

    response = await client.post(
        "/api/workflows/spec-kit/specification",
        json=SAMPLE_REQUEST_FULL
    )

    # Basic validation
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    result = response.json()

    # Validate specification structure
    assert_specification_structure(result)

    # Validate components
    components = result["components"]
    assert len(components) >= 3, "E-commerce platform should have at least 3 major components"

    # Check for common e-commerce components
    component_names = [c["name"].lower() for c in components]
    # At least one of these should be present
    expected_components = ["auth", "product", "cart", "order", "payment", "user"]
    assert any(exp in " ".join(component_names) for exp in expected_components), \
        f"E-commerce should have standard components, got: {component_names}"

    # Validate interfaces
    interfaces = result["interfaces"]
    assert len(interfaces) > 0, "Must define at least one interface"

    print(f"✅ Specification test passed - {len(components)} components, "
          f"{len(interfaces)} interfaces, pattern: {result['architecture']['pattern']}")


@pytest.mark.asyncio
async def test_tasks_stage_only(client: AsyncClient):
    """Test Tasks stage only"""

    response = await client.post(
        "/api/workflows/spec-kit/tasks",
        json=SAMPLE_REQUEST_MINIMAL
    )

    # Basic validation
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    result = response.json()

    # Validate tasks structure
    assert_tasks_structure(result)

    # Validate epic → feature → story → task hierarchy
    epics = result["epics"]
    features = result["features"]
    stories = result["stories"]
    tasks = result["tasks"]

    assert len(epics) >= 1, "Must have at least 1 epic"
    assert len(features) >= len(epics), "Should have at least as many features as epics"
    assert len(stories) >= len(features), "Should have at least as many stories as features"
    assert len(tasks) >= len(stories), "Should have at least as many tasks as stories"

    # CRITICAL: Verify Planning Poker enforcement
    for epic in epics:
        assert epic["story_points"] in [0, None, "TBD"], \
            f"Epic '{epic['name']}' has estimate {epic['story_points']}, " \
            "but all estimates must be TBD for team Planning Poker session"

    for feature in features:
        if "story_points" in feature:
            assert feature["story_points"] in [0, None, "TBD"], \
                f"Feature '{feature['name']}' has estimate, but should be TBD"

    print(f"✅ Tasks test passed - {len(epics)} epics, {len(features)} features, "
          f"{len(stories)} stories, {len(tasks)} tasks (all estimates TBD ✓)")


# ========================================
# EDGE CASE TESTS
# ========================================

@pytest.mark.asyncio
async def test_missing_required_fields(client: AsyncClient):
    """Test validation with missing required fields"""

    # Missing business_case
    invalid_request = {
        "stakeholders": ["Test"],
        "constraints": ["Test"],
        "success_criteria": ["Test"]
    }

    response = await client.post(
        "/api/workflows/spec-kit",
        json=invalid_request
    )

    assert response.status_code == 422, "Should return 422 for validation error"
    error = response.json()
    assert "detail" in error, "Error response must include detail"

    print("✅ Missing fields validation test passed")


@pytest.mark.asyncio
async def test_empty_lists(client: AsyncClient):
    """Test with empty stakeholders/constraints/criteria"""

    invalid_request = {
        "business_case": "Test project",
        "stakeholders": [],  # Empty list
        "constraints": ["Budget: €10k"],
        "success_criteria": ["Works"]
    }

    response = await client.post(
        "/api/workflows/spec-kit",
        json=invalid_request
    )

    # Should fail validation (min_items=1)
    assert response.status_code == 422, "Should return 422 for empty stakeholders list"

    print("✅ Empty lists validation test passed")


@pytest.mark.asyncio
async def test_very_short_business_case(client: AsyncClient):
    """Test with business case shorter than minimum length"""

    invalid_request = {
        "business_case": "Short",  # Less than 10 characters
        "stakeholders": ["Test"],
        "constraints": ["Test"],
        "success_criteria": ["Test"]
    }

    response = await client.post(
        "/api/workflows/spec-kit",
        json=invalid_request
    )

    # Should fail validation (min_length=10)
    assert response.status_code == 422, "Should return 422 for too short business case"

    print("✅ Short business case validation test passed")


@pytest.mark.asyncio
async def test_special_characters_in_project_name(client: AsyncClient):
    """Test with special characters in project name"""

    request_with_special_chars = {
        **SAMPLE_REQUEST_MINIMAL,
        "project_name": "E-Commerce Platform v2.0 (MVP) #1",
        "project_path": "projects/ecommerce-v2-mvp-1"
    }

    response = await client.post(
        "/api/workflows/spec-kit",
        json=request_with_special_chars
    )

    # Should succeed (special chars in name are OK, path is sanitized)
    assert response.status_code == 200, f"Should handle special chars, got {response.status_code}"
    result = response.json()
    assert result["status"] == "success"

    print("✅ Special characters test passed")


@pytest.mark.asyncio
async def test_large_input_stress_test(client: AsyncClient):
    """Test with very large input (stress test)"""

    large_request = {
        "business_case": "Build an enterprise-grade platform " * 100,  # Very long
        "stakeholders": [f"Stakeholder {i}" for i in range(50)],  # 50 stakeholders
        "constraints": [f"Constraint {i}: Details here" for i in range(30)],  # 30 constraints
        "success_criteria": [f"Criteria {i}: Must achieve X" for i in range(40)],  # 40 criteria
        "technical_context": {
            "existing_systems": [f"System {i}" for i in range(20)],
            "technologies": [f"Tech {i}" for i in range(30)],
            "team_size": 50,
            "timeline": "24 months"
        }
    }

    response = await client.post(
        "/api/workflows/spec-kit",
        json=large_request,
        timeout=60.0  # Longer timeout for large input
    )

    # Should succeed (may take longer)
    assert response.status_code == 200, f"Should handle large input, got {response.status_code}"
    result = response.json()
    assert result["status"] == "success"

    print("✅ Large input stress test passed")


# ========================================
# FILE GENERATION TESTS
# ========================================

@pytest.mark.asyncio
async def test_file_generation_with_project_path(client: AsyncClient):
    """Test file generation when project_path is provided"""

    request_with_path = {
        **SAMPLE_REQUEST_MINIMAL,
        "project_path": "projects/test-project",
        "project_name": "Test Project"
    }

    response = await client.post(
        "/api/workflows/spec-kit",
        json=request_with_path
    )

    assert response.status_code == 200
    result = response.json()

    # Validate files array
    files = result["files"]
    assert len(files) >= 4, "Must generate at least 4 files"

    # Check file paths include project path
    for file in files:
        assert "projects/test-project" in file["path"], \
            f"File path should include project path: {file['path']}"

    # Validate file contents are not empty
    for file in files:
        assert len(file["content"]) > 100, \
            f"File {file['path']} content seems too short: {len(file['content'])} chars"

    # Check for Planning Poker guide in tasks.md
    tasks_file = next((f for f in files if "tasks" in f["path"]), None)
    assert tasks_file is not None, "Must generate tasks.md"
    assert "Planning Poker" in tasks_file["content"], \
        "tasks.md must include Planning Poker guide"
    assert "TBD" in tasks_file["content"], \
        "tasks.md must mark estimates as TBD"

    print(f"✅ File generation test passed - {len(files)} files generated with Planning Poker guide")


@pytest.mark.asyncio
async def test_file_generation_without_project_path(client: AsyncClient):
    """Test file generation when project_path is omitted"""

    # No project_path provided
    response = await client.post(
        "/api/workflows/spec-kit",
        json=SAMPLE_REQUEST_MINIMAL
    )

    assert response.status_code == 200
    result = response.json()

    # Files should still be generated (with default path)
    assert "files" in result
    files = result["files"]
    assert len(files) >= 4, "Must generate files even without explicit path"

    print(f"✅ File generation without path test passed - {len(files)} files with default path")


# ========================================
# PERFORMANCE BASELINE TESTS
# ========================================

@pytest.mark.asyncio
async def test_performance_constitution_baseline(client: AsyncClient):
    """Measure baseline performance for Constitution stage"""
    import time

    start = time.time()
    response = await client.post(
        "/api/workflows/spec-kit/constitution",
        json=SAMPLE_REQUEST_MINIMAL
    )
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 30.0, f"Constitution should complete within 30s, took {duration:.2f}s"

    print(f"📊 Constitution baseline: {duration:.2f}s")


@pytest.mark.asyncio
async def test_performance_specification_baseline(client: AsyncClient):
    """Measure baseline performance for Specification stage"""
    import time

    start = time.time()
    response = await client.post(
        "/api/workflows/spec-kit/specification",
        json=SAMPLE_REQUEST_MINIMAL
    )
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 45.0, f"Specification should complete within 45s, took {duration:.2f}s"

    print(f"📊 Specification baseline: {duration:.2f}s")


@pytest.mark.asyncio
async def test_performance_tasks_baseline(client: AsyncClient):
    """Measure baseline performance for Tasks stage"""
    import time

    start = time.time()
    response = await client.post(
        "/api/workflows/spec-kit/tasks",
        json=SAMPLE_REQUEST_MINIMAL
    )
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 60.0, f"Tasks should complete within 60s, took {duration:.2f}s"

    print(f"📊 Tasks baseline: {duration:.2f}s")


@pytest.mark.asyncio
async def test_performance_complete_workflow_baseline(client: AsyncClient):
    """Measure baseline performance for complete 3-stage workflow"""
    import time

    start = time.time()
    response = await client.post(
        "/api/workflows/spec-kit",
        json=SAMPLE_REQUEST_MINIMAL,
        timeout=120.0  # 2 minute timeout
    )
    duration = time.time() - start

    assert response.status_code == 200
    result = response.json()

    # Complete workflow should finish within reasonable time
    assert duration < 120.0, f"Complete workflow should finish within 2 minutes, took {duration:.2f}s"

    # Get individual stage timings from workflow summary
    summary = result.get("workflow_summary", {})
    total_time = summary.get("total_time", duration)

    print(f"📊 Complete workflow baseline: {total_time:.2f}s (measured: {duration:.2f}s)")
    print(f"   - Stages completed: {summary.get('stages_completed', 'unknown')}")


if __name__ == "__main__":
    # Run with: pytest backend/tests/api/test_spec_kit_endpoints.py -v -s
    pytest.main([__file__, "-v", "-s"])
