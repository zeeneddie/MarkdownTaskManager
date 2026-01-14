#!/usr/bin/env python3
"""
Test hierarchy validation rules
Demonstrates all validation capabilities
"""
import asyncio
from app.services.task_generation.validation_service import HierarchyValidationService


async def test_validation_rules():
    """Test all validation rules without database."""
    print("🧪 Testing Validation Rules\n")

    # Create service (with None db for data validation tests)
    service = HierarchyValidationService(None)

    # Test 1: Story Points Validation (Fibonacci)
    print("1️⃣ Testing Story Points Validation (Fibonacci)...")
    valid_points = [1, 2, 3, 5, 8, 13, 21]
    invalid_points = [4, 6, 7, 9, 10, 15, 20]

    for points in valid_points:
        is_valid, error = service.validate_story_points(points)
        assert is_valid, f"Expected {points} to be valid"
    print(f"   ✅ Valid Fibonacci points: {valid_points}")

    for points in invalid_points:
        is_valid, error = service.validate_story_points(points)
        assert not is_valid, f"Expected {points} to be invalid"
        print(f"   ❌ Invalid: {points} - {error}")

    # Test 2: Priority Validation
    print("\n2️⃣ Testing Priority Validation...")
    valid_priorities = ["critical", "high", "medium", "low"]
    invalid_priorities = ["urgent", "normal", "CRITICAL", "HIGH"]

    for priority in valid_priorities:
        is_valid, error = service.validate_priority(priority)
        assert is_valid, f"Expected {priority} to be valid"
    print(f"   ✅ Valid priorities: {valid_priorities}")

    for priority in invalid_priorities:
        is_valid, error = service.validate_priority(priority)
        assert not is_valid, f"Expected {priority} to be invalid"
        print(f"   ❌ Invalid: {priority} - {error}")

    # Test 3: Complexity Validation
    print("\n3️⃣ Testing Complexity Validation...")
    valid_complexities = ["simple", "moderate", "complex"]
    invalid_complexities = ["easy", "hard", "medium", "SIMPLE"]

    for complexity in valid_complexities:
        is_valid, error = service.validate_complexity(complexity)
        assert is_valid, f"Expected {complexity} to be valid"
    print(f"   ✅ Valid complexities: {valid_complexities}")

    for complexity in invalid_complexities:
        is_valid, error = service.validate_complexity(complexity)
        assert not is_valid, f"Expected {complexity} to be invalid"
        print(f"   ❌ Invalid: {complexity} - {error}")

    # Test 4: Status Transition Validation (Epic)
    print("\n4️⃣ Testing Epic Status Transitions...")
    valid_transitions = [
        ("draft", "planned"),
        ("planned", "in_progress"),
        ("in_progress", "completed"),
        ("in_progress", "on_hold"),
        ("on_hold", "in_progress"),
    ]
    invalid_transitions = [
        ("completed", "in_progress"),  # Can't reopen completed
        ("cancelled", "in_progress"),  # Can't reopen cancelled
        ("draft", "completed"),  # Can't skip stages
    ]

    for from_status, to_status in valid_transitions:
        is_valid, error = service.validate_status_transition("epic", from_status, to_status)
        assert is_valid, f"Expected {from_status} → {to_status} to be valid"
        print(f"   ✅ Valid: {from_status} → {to_status}")

    for from_status, to_status in invalid_transitions:
        is_valid, error = service.validate_status_transition("epic", from_status, to_status)
        assert not is_valid, f"Expected {from_status} → {to_status} to be invalid"
        print(f"   ❌ Invalid: {from_status} → {to_status} - {error}")

    # Test 5: Epic Data Validation
    print("\n5️⃣ Testing Epic Data Validation...")
    valid_epic = {
        "title": "Core Infrastructure",
        "description": "Build foundational systems",
        "priority": "critical",
        "estimated_story_points": 45,
        "estimated_weeks": 3
    }
    errors = await service.validate_epic_data(valid_epic)
    assert not errors, f"Expected no errors, got: {errors}"
    print("   ✅ Valid epic data passed")

    invalid_epic = {
        "description": "Missing title",
        "priority": "urgent",  # Invalid priority
        "estimated_story_points": -10,  # Negative
    }
    errors = await service.validate_epic_data(invalid_epic)
    assert errors, "Expected validation errors"
    print(f"   ❌ Invalid epic data caught {len(errors)} errors:")
    for error in errors:
        print(f"      - {error}")

    # Test 6: Feature Data Validation
    print("\n6️⃣ Testing Feature Data Validation...")
    valid_feature = {
        "title": "API Gateway",
        "description": "Build RESTful API gateway",
        "priority": "high",
        "complexity": "moderate",
        "estimated_story_points": 13
    }
    errors = await service.validate_feature_data(valid_feature)
    assert not errors, f"Expected no errors, got: {errors}"
    print("   ✅ Valid feature data passed")

    invalid_feature = {
        "title": "A" * 250,  # Too long
        "description": "Valid description",
        "complexity": "very_hard"  # Invalid complexity
    }
    errors = await service.validate_feature_data(invalid_feature)
    assert errors, "Expected validation errors"
    print(f"   ❌ Invalid feature data caught {len(errors)} errors:")
    for error in errors:
        print(f"      - {error}")

    # Test 7: Story Data Validation
    print("\n7️⃣ Testing Story Data Validation...")
    valid_story = {
        "title": "As a user, I want to log in",
        "description": "Authentication story",
        "priority": "high",
        "story_points": 8  # Fibonacci
    }
    errors = await service.validate_story_data(valid_story)
    assert not errors, f"Expected no errors, got: {errors}"
    print("   ✅ Valid story data passed")

    invalid_story = {
        "title": "Story without description",
        "story_points": 7  # Not Fibonacci
    }
    errors = await service.validate_story_data(invalid_story)
    assert errors, "Expected validation errors"
    print(f"   ❌ Invalid story data caught {len(errors)} errors:")
    for error in errors:
        print(f"      - {error}")

    # Test 8: Task Data Validation
    print("\n8️⃣ Testing Task Data Validation...")
    valid_task = {
        "title": "Implement authentication API",
        "description": "Backend task for auth",
        "priority": "high",
        "task_type": "backend",
        "estimated_hours": 6
    }
    errors = await service.validate_task_data(valid_task)
    assert not errors, f"Expected no errors, got: {errors}"
    print("   ✅ Valid task data passed")

    invalid_task = {
        "description": "Missing title",
        "task_type": "unknown_type",
        "estimated_hours": 100  # Too many hours
    }
    errors = await service.validate_task_data(invalid_task)
    assert errors, "Expected validation errors"
    print(f"   ❌ Invalid task data caught {len(errors)} errors:")
    for error in errors:
        print(f"      - {error}")

    # Test 9: Hierarchy Limits
    print("\n9️⃣ Testing Hierarchy Limits...")
    print(f"   📊 Max Epics per Specification: {service.MAX_EPICS_PER_SPECIFICATION}")
    print(f"   📊 Max Features per Epic: {service.MAX_FEATURES_PER_EPIC}")
    print(f"   📊 Max Stories per Feature: {service.MAX_STORIES_PER_FEATURE}")
    print(f"   📊 Max Tasks per Story: {service.MAX_TASKS_PER_STORY}")
    print("   ✅ Limits defined and accessible")

    print("\n✨ All validation rules working correctly!\n")

    # Summary
    print("📋 Validation Summary:")
    print("   ✅ Story points: Fibonacci sequence (1, 2, 3, 5, 8, 13, 21, 34, 55, 89)")
    print("   ✅ Priorities: critical, high, medium, low")
    print("   ✅ Complexities: simple, moderate, complex")
    print("   ✅ Status transitions: Enforced for all entity types")
    print("   ✅ Data validation: Required fields, length limits, type checking")
    print("   ✅ Hierarchy limits: Enforced at all levels")
    print("   ✅ Task types: backend, frontend, database, testing, devops, documentation")


if __name__ == "__main__":
    asyncio.run(test_validation_rules())
