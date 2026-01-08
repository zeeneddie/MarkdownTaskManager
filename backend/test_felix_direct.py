#!/usr/bin/env python3
"""
Direct test of Felix integration without database dependencies
Tests the AgentService → TypeScript executor flow
"""
import asyncio
import sys
from pathlib import Path
from app.services.agent_service import AgentService

async def test_felix_integration():
    """Test Felix task generation integration."""
    print("🧪 Testing Felix Integration\n")

    # Initialize agent service
    service = AgentService()

    # Test 1: Generate Epics
    print("1️⃣ Testing Epic Generation...")
    try:
        spec_data = {
            "id": "test-spec-001",
            "project_id": "test-project-001",
            "content_json": {
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
                    {"name": "Admin Dashboard", "type": "frontend"},
                    {"name": "Customer Portal", "type": "frontend"},
                    {"name": "Mobile App", "type": "mobile"}
                ],
                "technical_requirements": [
                    "RESTful API with OpenAPI",
                    "PostgreSQL database",
                    "React frontend",
                    "JWT authentication"
                ]
            },
            "content_markdown": "# HLD Specification\n\n## Architecture\nMicroservices..."
        }

        result = await service.generate_epics_from_specification(
            specification=spec_data,
            project_id="test-project-001",
            options={"max_epics": 4}
        )

        print(f"   ✅ Generated {len(result.get('epics', []))} epics")
        print(f"   ✅ Generator: {result.get('metadata', {}).get('generator')}")

        # Get first epic for next test
        first_epic = result["epics"][0]
        print(f"   ✅ First epic: {first_epic['title']}\n")

    except Exception as e:
        print(f"   ❌ Epic generation failed: {e}\n")
        return False

    # Test 2: Generate Features
    print("2️⃣ Testing Feature Generation...")
    try:
        epic_data = {
            "id": "epic-001",
            "title": first_epic["title"],
            "description": first_epic["description"]
        }

        result = await service.generate_features_from_epic(
            epic=epic_data,
            specification_context={"architecture": {"style": "microservices"}},
            options={"max_features": 5}
        )

        print(f"   ✅ Generated {len(result.get('features', []))} features")

        # Get first feature for next test
        first_feature = result["features"][0]
        print(f"   ✅ First feature: {first_feature['title']}\n")

    except Exception as e:
        print(f"   ❌ Feature generation failed: {e}\n")
        return False

    # Test 3: Generate Stories
    print("3️⃣ Testing Story Generation...")
    try:
        feature_data = {
            "id": "feature-001",
            "title": first_feature["title"],
            "description": first_feature["description"]
        }

        result = await service.generate_stories_from_feature(
            feature=feature_data,
            epic_context={"title": first_epic["title"]},
            options={"max_stories": 4}
        )

        print(f"   ✅ Generated {len(result.get('stories', []))} stories")

        # Get first story for next test
        first_story = result["stories"][0]
        print(f"   ✅ First story: {first_story['title'][:60]}...\n")

    except Exception as e:
        print(f"   ❌ Story generation failed: {e}\n")
        return False

    # Test 4: Generate Tasks
    print("4️⃣ Testing Task Generation...")
    try:
        story_data = {
            "id": "story-001",
            "title": first_story["title"]
        }

        result = await service.generate_tasks_from_story(
            story=story_data,
            feature_context={"title": first_feature["title"]},
            options={"max_tasks": 3}
        )

        print(f"   ✅ Generated {len(result.get('tasks', []))} tasks")

        task = result["tasks"][0]
        print(f"   ✅ First task: {task['title'][:60]}...\n")

    except Exception as e:
        print(f"   ❌ Task generation failed: {e}\n")
        return False

    print("✨ All Felix integration tests passed!\n")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_felix_integration())
    sys.exit(0 if success else 1)
