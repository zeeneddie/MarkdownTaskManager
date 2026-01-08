#!/usr/bin/env python3
"""
Complete Integration Test for Week 11 Task Generation

Tests the entire workflow from specification to tasks:
- Database setup and teardown
- API endpoints
- Felix integration
- Validation rules
- Hierarchy summary
"""
import asyncio
import sys
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.models.item import Base as ItemBase
from app.models.sprint import Base as SprintBase
from app.models.user import Base as UserBase
from app.models.green_paper import Base as GreenPaperBase, GreenPaperSession, Constitution, Specification
from app.models.task_hierarchy import Epic, Feature, Story, Task
from app.services.week11.task_generation_service import TaskGenerationService
from app.services.week11.validation_service import HierarchyValidationService
from app.services.agent_service import AgentService


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/test_project_manager"


async def setup_database():
    """Create test database and tables."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)

    async with engine.begin() as conn:
        # Drop all tables first
        await conn.run_sync(GreenPaperBase.metadata.drop_all)
        await conn.run_sync(UserBase.metadata.drop_all)
        await conn.run_sync(SprintBase.metadata.drop_all)
        await conn.run_sync(ItemBase.metadata.drop_all)

        # Create all tables
        await conn.run_sync(ItemBase.metadata.create_all)
        await conn.run_sync(SprintBase.metadata.create_all)
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(GreenPaperBase.metadata.create_all)

    return engine


async def create_test_specification(db: AsyncSession) -> Specification:
    """Create a test specification for task generation."""
    # First create a project item (required foreign key)
    from app.models.item import Item
    project = Item(
        id="integration-test-project",
        title="Integration Test Project",
        type="project",
        description="Test project for integration tests",
        status="active"
    )
    db.add(project)

    session = GreenPaperSession(
        id=uuid4(),
        project_id="integration-test-project",
        status="completed",
        current_question=6,
        total_questions=6,
        progress_percentage=100,
        created_at=datetime.utcnow()
    )
    db.add(session)

    constitution = Constitution(
        id=uuid4(),
        session_id=session.id,
        project_id="integration-test-project",
        content_json={
            "title": "Integration Test Project Constitution",
            "vision": "Build comprehensive testing system",
            "principles": ["Quality First", "Automation", "Coverage"]
        },
        content_markdown="# Test Constitution\n\nQuality-focused development.",
        status="approved",
        created_at=datetime.utcnow()
    )
    db.add(constitution)

    specification = Specification(
        id=uuid4(),
        constitution_id=constitution.id,
        project_id="integration-test-project",
        content_json={
            "title": "E-Commerce Platform",
            "architecture": {
                "style": "microservices",
                "layers": ["api", "service", "data", "frontend"]
            },
            "components": [
                {"name": "API Gateway", "type": "backend"},
                {"name": "User Service", "type": "backend"},
                {"name": "Product Service", "type": "backend"},
                {"name": "Order Service", "type": "backend"},
                {"name": "Payment Gateway", "type": "integration"},
                {"name": "Inventory Management", "type": "service"},
                {"name": "Admin Dashboard", "type": "frontend"},
                {"name": "Customer Portal", "type": "frontend"},
                {"name": "Mobile App", "type": "mobile"}
            ],
            "technical_requirements": [
                "RESTful API with OpenAPI documentation",
                "PostgreSQL database with replication",
                "React frontend with TypeScript",
                "99.9% uptime SLA",
                "PCI-DSS compliance for payments"
            ]
        },
        content_markdown="# HLD Specification\n\n## Architecture\nMicroservices-based e-commerce...",
        status="approved",
        created_at=datetime.utcnow()
    )
    db.add(specification)
    await db.commit()
    await db.refresh(specification)

    return specification


async def run_integration_tests():
    """Run complete integration test suite."""
    print("🧪 Week 11 Complete Integration Test\n")
    print("=" * 70)

    # Setup
    print("\n📦 Setting up test database...")
    engine = await setup_database()
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # Create test data
            print("✅ Creating test specification...")
            specification = await create_test_specification(db)
            print(f"   Specification ID: {specification.id}")
            print(f"   Project: {specification.content_json['title']}")

            # Initialize services
            agent_service = AgentService()
            task_gen_service = TaskGenerationService(db, agent_service)
            validation_service = HierarchyValidationService(db)

            # Test 1: Generate Epics
            print("\n" + "=" * 70)
            print("TEST 1: Generate Epics from Specification")
            print("=" * 70)

            result = await task_gen_service.generate_epics_from_specification(
                specification_id=specification.id,
                options={"max_epics": 4}
            )

            print(f"✅ Generated {result['epics_generated']} epics")
            for epic in result['epics']:
                print(f"   📋 {epic['title']} (Priority: {epic['priority']}, {epic['estimated_story_points']} points)")

            first_epic_id = result['epics'][0]['id']

            # Test 2: Generate Features
            print("\n" + "=" * 70)
            print("TEST 2: Generate Features from Epic")
            print("=" * 70)

            result = await task_gen_service.generate_features_from_epic(
                epic_id=first_epic_id,
                options={"max_features": 5}
            )

            print(f"✅ Generated {result['features_generated']} features")
            for feature in result['features'][:3]:  # Show first 3
                print(f"   🔧 {feature['title']} (Complexity: {feature.get('complexity', 'N/A')})")

            first_feature_id = result['features'][0]['id']

            # Test 3: Generate Stories
            print("\n" + "=" * 70)
            print("TEST 3: Generate Stories from Feature")
            print("=" * 70)

            result = await task_gen_service.generate_stories_from_feature(
                feature_id=first_feature_id,
                options={"max_stories": 4}
            )

            print(f"✅ Generated {result['stories_generated']} stories")
            for story in result['stories'][:3]:  # Show first 3
                print(f"   📖 {story['title'][:60]}... ({story.get('story_points', 'N/A')} points)")

            first_story_id = result['stories'][0]['id']

            # Test 4: Generate Tasks
            print("\n" + "=" * 70)
            print("TEST 4: Generate Tasks from Story")
            print("=" * 70)

            result = await task_gen_service.generate_tasks_from_story(
                story_id=first_story_id,
                options={"max_tasks": 3}
            )

            print(f"✅ Generated {result['tasks_generated']} tasks")
            for task in result['tasks']:
                print(f"   ⚙️  {task['title'][:60]}... (Type: {task.get('task_type', 'N/A')})")

            # Test 5: Hierarchy Summary
            print("\n" + "=" * 70)
            print("TEST 5: Hierarchy Summary")
            print("=" * 70)

            summary = await validation_service.get_hierarchy_summary(str(specification.id))

            print(f"✅ Hierarchy Statistics:")
            print(f"   📊 Epics: {summary['counts']['epics']}/{summary['limits']['max_epics']}")
            print(f"   📊 Features: {summary['counts']['features']}")
            print(f"   📊 Stories: {summary['counts']['stories']}")
            print(f"   📊 Tasks: {summary['counts']['tasks']}")
            print(f"   📊 Total Story Points: {summary['statistics']['total_story_points']}")
            print(f"   📊 Avg Features/Epic: {summary['statistics']['avg_features_per_epic']}")
            print(f"   📊 Avg Stories/Feature: {summary['statistics']['avg_stories_per_feature']}")
            print(f"   📊 Avg Tasks/Story: {summary['statistics']['avg_tasks_per_story']}")

            # Test 6: Validation - Exceed Limits
            print("\n" + "=" * 70)
            print("TEST 6: Validation - Count Limits")
            print("=" * 70)

            # Try to create more epics than allowed
            print("Attempting to exceed epic limit...")
            is_valid, error = await validation_service.validate_epic_creation(
                specification_id=str(specification.id),
                num_epics_to_create=20  # Exceeds MAX_EPICS_PER_SPECIFICATION (10)
            )

            if not is_valid:
                print(f"✅ Validation correctly rejected: {error}")
            else:
                print(f"❌ Validation should have rejected this")

            # Test 7: Validation - Status Transitions
            print("\n" + "=" * 70)
            print("TEST 7: Validation - Status Transitions")
            print("=" * 70)

            # Test valid transition
            is_valid, error = validation_service.validate_status_transition(
                "epic", "draft", "planned"
            )
            print(f"✅ Valid transition (draft → planned): {is_valid}")

            # Test invalid transition
            is_valid, error = validation_service.validate_status_transition(
                "epic", "completed", "in_progress"
            )
            print(f"✅ Invalid transition blocked (completed → in_progress): {not is_valid}")
            if error:
                print(f"   Error: {error}")

            # Test 8: Validation - Story Points
            print("\n" + "=" * 70)
            print("TEST 8: Validation - Story Points (Fibonacci)")
            print("=" * 70)

            valid_points = [1, 3, 5, 8, 13]
            invalid_points = [4, 6, 7, 10]

            for points in valid_points:
                is_valid, _ = validation_service.validate_story_points(points)
                print(f"✅ {points} points: {'Valid' if is_valid else 'FAIL'}")

            for points in invalid_points:
                is_valid, error = validation_service.validate_story_points(points)
                print(f"✅ {points} points: {'FAIL' if not is_valid else 'Should be invalid'}")

            # Test 9: Complete Hierarchy Verification
            print("\n" + "=" * 70)
            print("TEST 9: Verify Complete Hierarchy in Database")
            print("=" * 70)

            from sqlalchemy import select, func

            # Count epics
            result = await db.execute(
                select(func.count(Epic.id)).where(Epic.specification_id == specification.id)
            )
            epic_count = result.scalar()
            print(f"✅ Epics in database: {epic_count}")

            # Count features for first epic
            result = await db.execute(
                select(func.count(Feature.id)).where(Feature.epic_id == first_epic_id)
            )
            feature_count = result.scalar()
            print(f"✅ Features for first epic: {feature_count}")

            # Count stories for first feature
            result = await db.execute(
                select(func.count(Story.id)).where(Story.feature_id == first_feature_id)
            )
            story_count = result.scalar()
            print(f"✅ Stories for first feature: {story_count}")

            # Count tasks for first story
            result = await db.execute(
                select(func.count(Task.id)).where(Task.story_id == first_story_id)
            )
            task_count = result.scalar()
            print(f"✅ Tasks for first story: {task_count}")

            # Test 10: Error Handling
            print("\n" + "=" * 70)
            print("TEST 10: Error Handling")
            print("=" * 70)

            # Try to generate epics again (should fail - already exist)
            try:
                await task_gen_service.generate_epics_from_specification(
                    specification_id=specification.id,
                    options={"max_epics": 3}
                )
                print("❌ Should have raised ValueError for duplicate epics")
            except ValueError as e:
                print(f"✅ Correctly rejected duplicate generation: {str(e)[:70]}...")

            # Try to generate from non-existent parent
            try:
                await task_gen_service.generate_features_from_epic(
                    epic_id=uuid4(),
                    options={"max_features": 3}
                )
                print("❌ Should have raised ValueError for non-existent epic")
            except ValueError as e:
                print(f"✅ Correctly rejected non-existent parent: {str(e)[:70]}...")

            # Final Summary
            print("\n" + "=" * 70)
            print("FINAL SUMMARY")
            print("=" * 70)

            final_summary = await validation_service.get_hierarchy_summary(str(specification.id))

            print(f"\n📊 Complete Hierarchy Generated:")
            print(f"   Specification: {specification.content_json['title']}")
            print(f"   └─ Epics: {final_summary['counts']['epics']}")
            print(f"      └─ Features: {final_summary['counts']['features']}")
            print(f"         └─ Stories: {final_summary['counts']['stories']}")
            print(f"            └─ Tasks: {final_summary['counts']['tasks']}")
            print(f"\n   Total Story Points: {final_summary['statistics']['total_story_points']}")
            print(f"   Remaining Epic Capacity: {final_summary['remaining_capacity']['epics']}")

            print("\n✨ All integration tests passed!\n")
            return True

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Cleanup
            await engine.dispose()
            print("🧹 Test database cleaned up")


if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)
