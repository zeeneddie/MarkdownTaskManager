"""
Integration tests for Felix task generation
Tests the complete flow: API → Service → AgentService → TypeScript Executor
"""
import pytest
import json
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.green_paper import GreenPaperSession, Constitution, Specification
from app.models.task_hierarchy import Epic, Feature, Story, Task


@pytest.fixture
async def test_specification(db_session: AsyncSession):
    """Create a test specification for task generation."""
    # Create green paper session
    session = GreenPaperSession(
        id=uuid.uuid4(),
        project_id="test-project-001",
        status="completed",
        current_phase="specification",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(session)

    # Create constitution
    constitution = Constitution(
        id=uuid.uuid4(),
        session_id=session.id,
        content_json={
            "title": "Test Project Constitution",
            "vision": "Build a comprehensive test system",
            "principles": ["Quality First", "Test Coverage", "Documentation"]
        },
        content_markdown="# Test Constitution\n\nQuality-focused development.",
        status="approved",
        version=1,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(constitution)

    # Create specification
    specification = Specification(
        id=uuid.uuid4(),
        session_id=session.id,
        constitution_id=constitution.id,
        project_id="test-project-001",
        content_json={
            "title": "Test Management System",
            "architecture": {
                "style": "microservices",
                "layers": ["api", "service", "data"]
            },
            "components": [
                {"name": "API Gateway", "type": "backend"},
                {"name": "User Service", "type": "backend"},
                {"name": "Test Runner", "type": "service"},
                {"name": "Report Generator", "type": "service"},
                {"name": "Web UI", "type": "frontend"},
                {"name": "Mobile App", "type": "frontend"}
            ],
            "technical_requirements": [
                "RESTful API with OpenAPI docs",
                "PostgreSQL database",
                "React frontend",
                "99.9% uptime SLA"
            ]
        },
        content_markdown="# HLD Specification\n\n## Architecture\nMicroservices-based system...",
        status="approved",
        version=1,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(specification)
    await db_session.commit()
    await db_session.refresh(specification)

    return specification


class TestFelixTaskGeneration:
    """Test Felix agent integration for task generation."""

    async def test_generate_epics_from_specification(
        self,
        client: AsyncClient,
        test_specification: Specification
    ):
        """Test epic generation from specification."""
        # Call the API endpoint
        response = await client.post(
            f"/api/task-generation/specifications/{test_specification.id}/epics",
            json={
                "options": {
                    "max_epics": 5,
                    "include_estimates": True
                }
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "epics" in data
        assert "metadata" in data
        assert isinstance(data["epics"], list)
        assert len(data["epics"]) > 0

        # Verify epic structure
        epic = data["epics"][0]
        assert "id" in epic
        assert "title" in epic
        assert "description" in epic
        assert "business_value" in epic
        assert "user_personas" in epic
        assert "acceptance_criteria" in epic
        assert "estimated_story_points" in epic

        # Verify metadata
        metadata = data["metadata"]
        assert metadata["specification_id"] == str(test_specification.id)
        assert metadata["project_id"] == test_specification.project_id
        assert "generated_at" in metadata
        assert "generator" in metadata

    async def test_generate_features_from_epic(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_specification: Specification
    ):
        """Test feature generation from epic."""
        # First generate epics
        epics_response = await client.post(
            f"/api/task-generation/specifications/{test_specification.id}/epics",
            json={"options": {"max_epics": 3}}
        )
        assert epics_response.status_code == 201
        epics_data = epics_response.json()

        # Get the first epic from database
        epic_id = uuid.UUID(epics_data["epics"][0]["id"])

        # Generate features from epic
        response = await client.post(
            f"/api/task-generation/epics/{epic_id}/features",
            json={
                "options": {
                    "max_features": 7,
                    "include_technical_details": True
                }
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "features" in data
        assert "metadata" in data
        assert isinstance(data["features"], list)
        assert len(data["features"]) > 0

        # Verify feature structure
        feature = data["features"][0]
        assert "id" in feature
        assert "title" in feature
        assert "description" in feature
        assert "technical_approach" in feature
        assert "api_endpoints" in feature
        assert "database_changes" in feature
        assert "estimated_story_points" in feature

    async def test_generate_stories_from_feature(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_specification: Specification
    ):
        """Test story generation from feature."""
        # Generate epics → features
        epics_response = await client.post(
            f"/api/task-generation/specifications/{test_specification.id}/epics",
            json={"options": {"max_epics": 2}}
        )
        epics_data = epics_response.json()
        epic_id = uuid.UUID(epics_data["epics"][0]["id"])

        features_response = await client.post(
            f"/api/task-generation/epics/{epic_id}/features",
            json={"options": {"max_features": 3}}
        )
        features_data = features_response.json()
        feature_id = uuid.UUID(features_data["features"][0]["id"])

        # Generate stories from feature
        response = await client.post(
            f"/api/task-generation/features/{feature_id}/stories",
            json={
                "options": {
                    "max_stories": 5,
                    "include_acceptance_criteria": True
                }
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "stories" in data
        assert "metadata" in data
        assert isinstance(data["stories"], list)
        assert len(data["stories"]) > 0

        # Verify story structure
        story = data["stories"][0]
        assert "id" in story
        assert "title" in story
        assert "description" in story
        assert "user_type" in story
        assert "user_goal" in story
        assert "user_benefit" in story
        assert "acceptance_criteria" in story
        assert "story_points" in story

        # Verify acceptance criteria structure
        ac = story["acceptance_criteria"][0]
        assert "given" in ac
        assert "when" in ac
        assert "then" in ac

    async def test_generate_tasks_from_story(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_specification: Specification
    ):
        """Test task generation from story."""
        # Generate full hierarchy: epics → features → stories
        epics_response = await client.post(
            f"/api/task-generation/specifications/{test_specification.id}/epics",
            json={"options": {"max_epics": 2}}
        )
        epics_data = epics_response.json()
        epic_id = uuid.UUID(epics_data["epics"][0]["id"])

        features_response = await client.post(
            f"/api/task-generation/epics/{epic_id}/features",
            json={"options": {"max_features": 2}}
        )
        features_data = features_response.json()
        feature_id = uuid.UUID(features_data["features"][0]["id"])

        stories_response = await client.post(
            f"/api/task-generation/features/{feature_id}/stories",
            json={"options": {"max_stories": 2}}
        )
        stories_data = stories_response.json()
        story_id = uuid.UUID(stories_data["stories"][0]["id"])

        # Generate tasks from story
        response = await client.post(
            f"/api/task-generation/stories/{story_id}/tasks",
            json={
                "options": {
                    "max_tasks": 4,
                    "include_technical_notes": True
                }
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "tasks" in data
        assert "metadata" in data
        assert isinstance(data["tasks"], list)
        assert len(data["tasks"]) > 0

        # Verify task structure
        task = data["tasks"][0]
        assert "id" in task
        assert "title" in task
        assert "description" in task
        assert "task_type" in task
        assert "technical_notes" in task
        assert "code_files" in task
        assert "estimated_hours" in task

    async def test_complete_hierarchy_generation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_specification: Specification
    ):
        """Test generating the complete task hierarchy."""
        # Step 1: Generate epics
        epics_response = await client.post(
            f"/api/task-generation/specifications/{test_specification.id}/epics",
            json={"options": {"max_epics": 3}}
        )
        assert epics_response.status_code == 201
        epics_data = epics_response.json()
        assert len(epics_data["epics"]) == 3

        # Step 2: Generate features for each epic
        all_features = []
        for epic in epics_data["epics"]:
            epic_id = uuid.UUID(epic["id"])
            features_response = await client.post(
                f"/api/task-generation/epics/{epic_id}/features",
                json={"options": {"max_features": 2}}
            )
            assert features_response.status_code == 201
            features_data = features_response.json()
            all_features.extend(features_data["features"])

        assert len(all_features) >= 6  # At least 2 features per epic

        # Step 3: Generate stories for first feature
        first_feature_id = uuid.UUID(all_features[0]["id"])
        stories_response = await client.post(
            f"/api/task-generation/features/{first_feature_id}/stories",
            json={"options": {"max_stories": 3}}
        )
        assert stories_response.status_code == 201
        stories_data = stories_response.json()
        assert len(stories_data["stories"]) >= 3

        # Step 4: Generate tasks for first story
        first_story_id = uuid.UUID(stories_data["stories"][0]["id"])
        tasks_response = await client.post(
            f"/api/task-generation/stories/{first_story_id}/tasks",
            json={"options": {"max_tasks": 3}}
        )
        assert tasks_response.status_code == 201
        tasks_data = tasks_response.json()
        assert len(tasks_data["tasks"]) >= 2

        # Verify the complete hierarchy exists in database
        from sqlalchemy import select

        # Check epics
        result = await db_session.execute(
            select(Epic).where(Epic.specification_id == test_specification.id)
        )
        db_epics = result.scalars().all()
        assert len(db_epics) == 3

        # Check features
        result = await db_session.execute(
            select(Feature).where(Feature.epic_id == uuid.UUID(epics_data["epics"][0]["id"]))
        )
        db_features = result.scalars().all()
        assert len(db_features) >= 2

        # Check stories
        result = await db_session.execute(
            select(Story).where(Story.feature_id == first_feature_id)
        )
        db_stories = result.scalars().all()
        assert len(db_stories) >= 3

        # Check tasks
        result = await db_session.execute(
            select(Task).where(Task.story_id == first_story_id)
        )
        db_tasks = result.scalars().all()
        assert len(db_tasks) >= 2

    async def test_retrieval_endpoints(
        self,
        client: AsyncClient,
        test_specification: Specification
    ):
        """Test GET endpoints for retrieving generated items."""
        # Generate some data first
        epics_response = await client.post(
            f"/api/task-generation/specifications/{test_specification.id}/epics",
            json={"options": {"max_epics": 2}}
        )
        epics_data = epics_response.json()
        epic_id = uuid.UUID(epics_data["epics"][0]["id"])

        # Test: Get epics for specification
        response = await client.get(
            f"/api/task-generation/specifications/{test_specification.id}/epics"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

        # Test: Get features for epic
        features_response = await client.post(
            f"/api/task-generation/epics/{epic_id}/features",
            json={"options": {"max_features": 3}}
        )

        response = await client.get(f"/api/task-generation/epics/{epic_id}/features")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_error_handling_invalid_specification(
        self,
        client: AsyncClient
    ):
        """Test error handling for invalid specification ID."""
        invalid_id = uuid.uuid4()

        response = await client.post(
            f"/api/task-generation/specifications/{invalid_id}/epics",
            json={"options": {}}
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    async def test_error_handling_unapproved_specification(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_specification: Specification
    ):
        """Test error handling for unapproved specification."""
        # Update specification status to draft
        test_specification.status = "draft"
        await db_session.commit()

        response = await client.post(
            f"/api/task-generation/specifications/{test_specification.id}/epics",
            json={"options": {}}
        )

        assert response.status_code == 400
        assert "approved" in response.json()["detail"].lower()

        # Reset status
        test_specification.status = "approved"
        await db_session.commit()


class TestFelixExecutorDirect:
    """Test the TypeScript Felix executor directly."""

    async def test_executor_epics_generation(self):
        """Test executor generates valid epics."""
        import subprocess
        import json

        # Prepare input payload
        payload = {
            "command": "generate-epics",
            "specification": {
                "id": str(uuid.uuid4()),
                "project_id": "test-project",
                "content_json": {
                    "title": "Test System",
                    "architecture": {"style": "monolithic"},
                    "components": [
                        {"name": "API", "type": "backend"},
                        {"name": "UI", "type": "frontend"},
                        {"name": "DB", "type": "database"}
                    ]
                },
                "content_markdown": "# Test Spec"
            },
            "projectId": "test-project",
            "options": {"max_epics": 5}
        }

        # Call executor
        process = subprocess.run(
            ["node", "ts-node", "execute-felix-task-generation.ts"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd="/home/eddie/Projects/MarkdownTaskManager/backend/agents"
        )

        assert process.returncode == 0, f"Executor failed: {process.stderr}"

        # Parse output
        result = json.loads(process.stdout)

        # Verify structure
        assert "epics" in result
        assert "metadata" in result
        assert len(result["epics"]) > 0
        assert len(result["epics"]) <= 5

        # Verify epic structure
        epic = result["epics"][0]
        assert "title" in epic
        assert "description" in epic
        assert "business_value" in epic
        assert "user_personas" in epic
        assert "acceptance_criteria" in epic

    async def test_executor_features_generation(self):
        """Test executor generates valid features."""
        import subprocess
        import json

        payload = {
            "command": "generate-features",
            "epic": {
                "id": str(uuid.uuid4()),
                "title": "Core Infrastructure",
                "description": "Build foundational systems"
            },
            "specificationContext": {
                "architecture": {"style": "microservices"}
            },
            "options": {"max_features": 7}
        }

        process = subprocess.run(
            ["node", "ts-node", "execute-felix-task-generation.ts"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd="/home/eddie/Projects/MarkdownTaskManager/backend/agents"
        )

        assert process.returncode == 0, f"Executor failed: {process.stderr}"

        result = json.loads(process.stdout)

        assert "features" in result
        assert len(result["features"]) > 0

        feature = result["features"][0]
        assert "title" in feature
        assert "description" in feature
        assert "technical_approach" in feature
        assert "api_endpoints" in feature
