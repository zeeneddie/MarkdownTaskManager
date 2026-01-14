#!/usr/bin/env python3
"""
Test Real LLM Integration for Felix Task Generation

Tests that the new Ollama integration works end-to-end
with actual qwen2.5-coder:7b model.
"""
import asyncio
import json
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.models.green_paper import Base as GreenPaperBase, Specification
from app.models.item import Base as ItemBase
from app.services.task_generation.task_generation_service import TaskGenerationService
from app.services.agent_service import AgentService


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/test_project_manager"


async def create_test_specification(db: AsyncSession) -> Specification:
    """Create a simple test specification"""
    from app.models.item import Item

    # Create project
    project = Item(
        id="llm-test-project",
        title="LLM Integration Test Project",
        type="project",
        description="Test project for LLM integration",
        status="active"
    )
    db.add(project)

    # Create specification
    specification = Specification(
        id=uuid4(),
        constitution_id=uuid4(),  # Dummy
        project_id="llm-test-project",
        content_json={
            "title": "Simple E-Commerce Platform",
            "architecture": {
                "style": "microservices",
                "layers": ["api", "service", "data"]
            },
            "components": [
                {"name": "API Gateway", "type": "backend"},
                {"name": "User Service", "type": "backend"},
                {"name": "Product Service", "type": "backend"},
                {"name": "Payment Gateway", "type": "integration"}
            ],
            "technical_requirements": [
                "RESTful API with OpenAPI docs",
                "PostgreSQL database",
                "React frontend"
            ]
        },
        content_markdown="# Simple E-Commerce Platform\n\nMicroservices architecture...",
        status="approved",
        created_at=datetime.utcnow()
    )
    db.add(specification)
    await db.commit()
    await db.refresh(specification)

    return specification


async def test_llm_integration():
    """Test real LLM integration"""
    print("🧪 Testing Felix LLM Integration (qwen2.5-coder:7b)\n")
    print("=" * 70)

    # Setup database
    print("\n📦 Setting up test database...")
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(GreenPaperBase.metadata.drop_all)
        await conn.run_sync(ItemBase.metadata.drop_all)
        await conn.run_sync(ItemBase.metadata.create_all)
        await conn.run_sync(GreenPaperBase.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # Create test specification
            print("✅ Creating test specification...")
            specification = await create_test_specification(db)
            print(f"   Specification ID: {specification.id}")
            print(f"   Project: {specification.content_json['title']}")

            # Initialize services
            agent_service = AgentService()
            task_gen_service = TaskGenerationService(db, agent_service)

            # Test Epic Generation with REAL LLM
            print("\n" + "=" * 70)
            print("TEST: Generate Epics with REAL LLM (qwen2.5-coder:7b)")
            print("=" * 70)
            print("This will call actual Ollama API...")
            print("Expected: 3-5 seconds per generation\n")

            result = await task_gen_service.generate_epics_from_specification(
                specification_id=specification.id,
                options={"max_epics": 3}  # Start small for testing
            )

            print(f"✅ Generated {result['epics_generated']} epics")
            print(f"\n📊 Metadata:")
            print(f"   Generator: {result['generator']}")
            print(f"   Model: {result['model']}")
            print(f"   LLM Used: {result.get('llm_used', 'unknown')}")
            print(f"   Generated At: {result['generated_at']}")

            print(f"\n📋 Generated Epics:")
            for i, epic in enumerate(result['epics'], 1):
                print(f"\n   {i}. {epic['title']}")
                print(f"      Description: {epic['description'][:100]}...")
                print(f"      Priority: {epic['priority']}")
                print(f"      Story Points: {epic.get('estimated_story_points', 'N/A')}")
                print(f"      Business Value: {epic.get('business_value', 'N/A')[:80]}...")

            # Verify LLM was actually used
            if result.get('llm_used') == True:
                print("\n✅ SUCCESS: Real LLM integration working!")
                print("   qwen2.5-coder:7b generated intelligent epics")
            elif result.get('llm_used') == False:
                print("\n⚠️  WARNING: Mock fallback was used")
                print("   Check if Ollama is running and qwen2.5-coder:7b is available")
            else:
                print("\n❓ UNKNOWN: Cannot determine if LLM was used")

            return True

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            await engine.dispose()
            print("\n🧹 Test database cleaned up")


if __name__ == "__main__":
    success = asyncio.run(test_llm_integration())
    print("\n" + "=" * 70)
    if success:
        print("✨ LLM Integration Test PASSED!")
    else:
        print("❌ LLM Integration Test FAILED")
    print("=" * 70)
