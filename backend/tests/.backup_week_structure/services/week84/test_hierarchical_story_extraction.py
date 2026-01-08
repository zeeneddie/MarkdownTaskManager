"""
Tests for HierarchicalStoryExtractionService - Week 84

Tests:
- ExtractedStory dataclass
- LevelExtractionResult dataclass
- HierarchicalExtractionResult dataclass
- FewShotTemplates per stack
- HierarchicalStoryExtractionService extraction flow
- Prompt building
- Story parsing from LLM responses
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import json
from uuid import uuid4

from app.services.hierarchical_story_extraction_service import (
    HierarchicalStoryExtractionService,
    ExtractedStory,
    LevelExtractionResult,
    HierarchicalExtractionResult,
    FewShotTemplates,
    HierarchicalPromptBuilder,
    ExtractionLevel,
    StoryConfidence,
    get_hierarchical_extraction_service,
)
from app.models.deep_extraction import ExtractionTier, ItemType


class TestExtractedStory:
    """Tests for ExtractedStory dataclass."""

    def test_create_empty_story(self):
        """Should create story with defaults."""
        story = ExtractedStory()

        assert story.level == ExtractionLevel.FUNCTION
        assert story.item_type == ItemType.STORY
        assert story.title == ""
        assert story.acceptance_criteria == []
        assert story.confidence == 0.0

    def test_create_full_story(self):
        """Should create story with all fields."""
        story = ExtractedStory(
            level=ExtractionLevel.CLASS,
            item_type=ItemType.FEATURE,
            title="User Authentication",
            description="As a user, I want to authenticate",
            acceptance_criteria=["Login works", "Logout works"],
            source_file="auth/service.py",
            source_symbol="AuthService",
            confidence=0.85,
            complexity="high",
            tags=["security", "auth"],
            story_points=8,
            function_points=5.5,
        )

        assert story.level == ExtractionLevel.CLASS
        assert story.item_type == ItemType.FEATURE
        assert story.title == "User Authentication"
        assert len(story.acceptance_criteria) == 2
        assert story.confidence == 0.85
        assert story.story_points == 8

    def test_to_dict(self):
        """Should convert to dictionary."""
        story = ExtractedStory(
            title="Test Story",
            confidence=0.75,
        )

        result = story.to_dict()

        assert result["title"] == "Test Story"
        assert result["confidence"] == 0.75
        assert "id" in result
        assert "extracted_at" in result


class TestLevelExtractionResult:
    """Tests for LevelExtractionResult dataclass."""

    def test_create_empty_result(self):
        """Should create empty result."""
        result = LevelExtractionResult(level=ExtractionLevel.FUNCTION)

        assert result.level == ExtractionLevel.FUNCTION
        assert result.stories == []
        assert result.features == []
        assert result.total_items == 0

    def test_create_with_stories(self):
        """Should create result with stories."""
        stories = [
            ExtractedStory(title="Story 1", confidence=0.8),
            ExtractedStory(title="Story 2", confidence=0.9),
        ]

        result = LevelExtractionResult(
            level=ExtractionLevel.FUNCTION,
            stories=stories,
            total_items=2,
            avg_confidence=0.85,
            tokens_used=500,
        )

        assert len(result.stories) == 2
        assert result.total_items == 2
        assert result.avg_confidence == 0.85

    def test_to_dict(self):
        """Should convert to dictionary."""
        result = LevelExtractionResult(
            level=ExtractionLevel.CLASS,
            total_items=5,
            avg_confidence=0.75,
        )

        output = result.to_dict()

        assert output["level"] == "class"
        assert output["total_items"] == 5
        assert output["avg_confidence"] == 0.75


class TestHierarchicalExtractionResult:
    """Tests for HierarchicalExtractionResult dataclass."""

    def test_create_result(self):
        """Should create extraction result."""
        result = HierarchicalExtractionResult(
            project_id=1,
            repository_path="/opt/projects/test",
        )

        assert result.project_id == 1
        assert result.repository_path == "/opt/projects/test"
        assert result.tier == ExtractionTier.FREE

    def test_is_successful_no_errors(self):
        """Should be successful with no errors and stories."""
        result = HierarchicalExtractionResult(
            project_id=1,
            repository_path="/test",
            total_stories=10,
            errors=[],
        )

        assert result.is_successful is True

    def test_is_successful_with_errors(self):
        """Should not be successful with errors."""
        result = HierarchicalExtractionResult(
            project_id=1,
            repository_path="/test",
            total_stories=10,
            errors=["Something failed"],
        )

        assert result.is_successful is False

    def test_is_successful_no_stories(self):
        """Should not be successful with no stories."""
        result = HierarchicalExtractionResult(
            project_id=1,
            repository_path="/test",
            total_stories=0,
            errors=[],
        )

        assert result.is_successful is False

    def test_to_dict(self):
        """Should convert to dictionary."""
        result = HierarchicalExtractionResult(
            project_id=1,
            repository_path="/test",
            primary_stack="python",
            total_epics=5,
            total_features=15,
            total_stories=45,
            overall_confidence=0.78,
        )

        output = result.to_dict()

        assert output["project_id"] == 1
        assert output["primary_stack"] == "python"
        assert output["totals"]["epics"] == 5
        assert output["totals"]["features"] == 15
        assert output["totals"]["stories"] == 45
        assert output["overall_confidence"] == 0.78

    def test_to_llm_context(self):
        """Should generate LLM context string."""
        func_level = LevelExtractionResult(
            level=ExtractionLevel.FUNCTION,
            stories=[
                ExtractedStory(title="Auth login", confidence=0.9),
                ExtractedStory(title="Auth logout", confidence=0.85),
            ],
            total_items=2,
            avg_confidence=0.875,
        )

        result = HierarchicalExtractionResult(
            project_id=1,
            repository_path="/opt/myproject",
            primary_stack="python",
            function_level=func_level,
            total_stories=2,
            overall_confidence=0.875,
        )

        context = result.to_llm_context()

        assert "Hierarchical Story Extraction" in context
        assert "python" in context.lower()
        assert "Auth login" in context


class TestFewShotTemplates:
    """Tests for FewShotTemplates class."""

    def test_get_python_template(self):
        """Should return Python template."""
        template = FewShotTemplates.get_template_for_stack("python")

        assert "Python" in template
        assert "FastAPI" in template or "def " in template
        assert "### Example" in template

    def test_get_javascript_template(self):
        """Should return JavaScript template."""
        template = FewShotTemplates.get_template_for_stack("javascript")

        assert "JavaScript" in template or "TypeScript" in template
        assert "React" in template or "Express" in template

    def test_get_csharp_template(self):
        """Should return C# template."""
        template = FewShotTemplates.get_template_for_stack("csharp")

        assert "C#" in template or ".NET" in template

    def test_get_go_template(self):
        """Should return Go template."""
        template = FewShotTemplates.get_template_for_stack("go")

        assert "Go" in template
        assert "func " in template or "http" in template.lower()

    def test_get_java_template(self):
        """Should return Java template."""
        template = FewShotTemplates.get_template_for_stack("java")

        assert "Java" in template
        assert "Spring" in template or "@" in template

    def test_get_unknown_stack_defaults_to_python(self):
        """Should return Python template for unknown stack."""
        template = FewShotTemplates.get_template_for_stack("cobol")

        assert "Python" in template

    def test_get_all_stacks(self):
        """Should return all supported stacks."""
        stacks = FewShotTemplates.get_all_stacks()

        assert "python" in stacks
        assert "javascript" in stacks
        assert "csharp" in stacks
        assert "go" in stacks
        assert "java" in stacks
        assert len(stacks) == 6  # python, js, ts, csharp, go, java


class TestHierarchicalPromptBuilder:
    """Tests for HierarchicalPromptBuilder class."""

    def test_build_function_level_prompt(self):
        """Should build function-level prompt."""
        code = "def hello():\n    print('Hello')"
        template = FewShotTemplates.get_template_for_stack("python")

        prompt = HierarchicalPromptBuilder.build_function_level_prompt(
            code=code,
            file_path="main.py",
            few_shot_template=template,
        )

        assert "main.py" in prompt
        assert "def hello()" in prompt
        assert "Few-Shot Examples" in prompt
        assert "Output Format (JSON)" in prompt

    def test_build_class_level_prompt(self):
        """Should build class-level prompt."""
        code = "class UserService:\n    def get_user(self): pass"
        template = FewShotTemplates.get_template_for_stack("python")
        stories = [ExtractedStory(title="Get user by ID")]

        prompt = HierarchicalPromptBuilder.build_class_level_prompt(
            class_code=code,
            class_name="UserService",
            file_path="services/user.py",
            few_shot_template=template,
            method_stories=stories,
        )

        assert "UserService" in prompt
        assert "Method Stories Already Extracted" in prompt
        assert "Get user by ID" in prompt

    def test_build_module_level_prompt(self):
        """Should build module-level prompt."""
        files = ["main.py", "utils.py", "config.py"]
        features = [ExtractedStory(title="User Management", item_type=ItemType.FEATURE)]

        prompt = HierarchicalPromptBuilder.build_module_level_prompt(
            module_files=files,
            class_features=features,
            module_name="users",
            dependencies=["database", "auth"],
        )

        assert "users" in prompt
        assert "User Management" in prompt
        assert "main.py" in prompt
        assert "database" in prompt


class TestHierarchicalStoryExtractionService:
    """Tests for HierarchicalStoryExtractionService."""

    def test_init_service(self):
        """Should initialize service."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        assert service.db == mock_db
        assert service.aggregator is not None
        assert service.prompt_builder is not None

    def test_extract_json_from_code_block(self):
        """Should extract JSON from markdown code block."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        content = '''Here is the result:
```json
{"stories": [{"title": "Test Story"}]}
```
'''
        result = service._extract_json(content)

        assert '{"stories"' in result
        parsed = json.loads(result)
        assert parsed["stories"][0]["title"] == "Test Story"

    def test_extract_json_direct(self):
        """Should extract JSON without code block."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        content = '{"stories": [{"title": "Direct"}]}'
        result = service._extract_json(content)

        parsed = json.loads(result)
        assert parsed["stories"][0]["title"] == "Direct"

    def test_get_confidence_level_high(self):
        """Should return HIGH for >= 0.8."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        assert service._get_confidence_level(0.8) == StoryConfidence.HIGH
        assert service._get_confidence_level(0.95) == StoryConfidence.HIGH

    def test_get_confidence_level_medium(self):
        """Should return MEDIUM for 0.6-0.79."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        assert service._get_confidence_level(0.6) == StoryConfidence.MEDIUM
        assert service._get_confidence_level(0.79) == StoryConfidence.MEDIUM

    def test_get_confidence_level_low(self):
        """Should return LOW for < 0.6."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        assert service._get_confidence_level(0.5) == StoryConfidence.LOW
        assert service._get_confidence_level(0.0) == StoryConfidence.LOW

    def test_calculate_cost_free_tier(self):
        """Should return 0 cost for FREE tier."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        cost = service._calculate_cost(1_000_000, ExtractionTier.FREE)

        assert cost == 0.0

    def test_calculate_cost_premium_tier(self):
        """Should calculate cost for PREMIUM tier."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        cost = service._calculate_cost(1_000_000, ExtractionTier.PREMIUM)

        assert cost == 5.0  # $5 per 1M tokens

    def test_parse_stories_from_response(self):
        """Should parse stories from JSON response."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        content = json.dumps({
            "stories": [
                {
                    "title": "User Login",
                    "description": "As a user, I want to login",
                    "acceptance_criteria": ["Valid credentials work"],
                    "confidence": 0.85,
                    "complexity": "medium",
                    "tags": ["auth"],
                }
            ]
        })

        stories = service._parse_stories_from_response(
            content, "auth.py", ExtractionLevel.FUNCTION
        )

        assert len(stories) == 1
        assert stories[0].title == "User Login"
        assert stories[0].confidence == 0.85
        assert stories[0].source_file == "auth.py"

    def test_parse_stories_invalid_json(self):
        """Should handle invalid JSON gracefully."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        content = "This is not JSON"

        stories = service._parse_stories_from_response(
            content, "test.py", ExtractionLevel.FUNCTION
        )

        assert stories == []

    @pytest.mark.asyncio
    async def test_extract_nonexistent_path(self):
        """Should handle non-existent path."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        # Mock the aggregator to return error
        service.aggregator.analyze = AsyncMock(return_value=Mock(
            is_successful=False,
            technology=Mock(primary_stack="python"),
        ))

        result = await service.extract_hierarchical(
            project_id=1,
            repository_path="/nonexistent/path/12345",
        )

        assert not result.is_successful
        assert len(result.errors) > 0

    def test_factory_function(self):
        """Should create service via factory function."""
        mock_db = Mock()
        service = get_hierarchical_extraction_service(mock_db)

        assert isinstance(service, HierarchicalStoryExtractionService)


class TestIntegration:
    """Integration tests for hierarchical extraction."""

    @pytest.mark.asyncio
    async def test_extract_with_temp_directory(self):
        """Should extract from temporary directory."""
        mock_db = Mock()
        service = HierarchicalStoryExtractionService(mock_db)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python file
            py_file = Path(tmpdir) / "main.py"
            py_file.write_text('''
def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user with username and password."""
    # Check credentials
    if not username or not password:
        return False
    # Verify against database
    return verify_credentials(username, password)
''')

            # Mock aggregator
            service.aggregator.analyze = AsyncMock(return_value=Mock(
                is_successful=True,
                technology=Mock(
                    primary_stack="python",
                    secondary_stacks=[],
                    database_type=None,
                    total_files=1,
                    total_loc=10,
                ),
                dependencies=None,
            ))

            # Mock LLM call
            async def mock_call_llm(provider, prompt):
                return {
                    "content": json.dumps({
                        "stories": [{
                            "title": "User Authentication",
                            "description": "As a user, I want to authenticate",
                            "acceptance_criteria": ["Valid login works"],
                            "confidence": 0.8,
                            "complexity": "medium",
                            "tags": ["auth"],
                        }]
                    }),
                    "tokens": 100,
                }

            service._call_llm = mock_call_llm

            result = await service.extract_hierarchical(
                project_id=1,
                repository_path=tmpdir,
                levels=[ExtractionLevel.FUNCTION],
                max_files=10,
            )

        assert result.project_id == 1
        assert result.primary_stack == "python"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
