"""
Tests for Week 96 Design OS Services

Tests for:
- ImplementationPromptService
- ScreenWireframeService
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import uuid4


class TestImplementationPromptService:
    """Tests for ImplementationPromptService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock async database session."""
        db = Mock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        # Mock execute for queries
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
        db.execute = AsyncMock(return_value=mock_result)

        return db

    @pytest.fixture
    def mock_prompt(self):
        """Create a mock ImplementationPrompt."""
        prompt = Mock()
        prompt.id = uuid4()
        prompt.project_id = "test-project"
        prompt.section_id = "section-001"
        prompt.name = "Test Component"
        prompt.prompt_type = "component"
        prompt.prompt_content = "# Test Prompt Content"
        prompt.target_stack = "react"
        prompt.included_context = {}
        prompt.estimated_complexity = "moderate"
        prompt.dependencies = []
        prompt.tier = "PREMIUM"
        prompt.times_used = 0
        prompt.last_used_at = None
        prompt.created_at = datetime.now(timezone.utc)
        prompt.to_dict = Mock(return_value={
            "id": str(prompt.id),
            "project_id": prompt.project_id,
            "name": prompt.name,
            "prompt_type": prompt.prompt_type,
        })
        return prompt

    @pytest.mark.asyncio
    async def test_create_prompt(self, mock_db):
        """Test creating an implementation prompt."""
        from app.services.design_os_service import ImplementationPromptService

        service = ImplementationPromptService(mock_db)

        result = await service.create_prompt(
            project_id="test-project",
            name="Test Component",
            prompt_type="component",
            prompt_content="# Test Prompt",
            section_id="section-001",
            target_stack="react",
        )

        # Verify db operations were called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_prompt(self, mock_db, mock_prompt):
        """Test getting a prompt by ID."""
        from app.services.design_os_service import ImplementationPromptService

        # Setup mock to return the prompt
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_prompt)
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ImplementationPromptService(mock_db)
        result = await service.get_prompt(str(mock_prompt.id))

        assert result is not None
        assert result.id == mock_prompt.id

    @pytest.mark.asyncio
    async def test_get_prompts_for_project(self, mock_db, mock_prompt):
        """Test getting all prompts for a project."""
        from app.services.design_os_service import ImplementationPromptService

        # Setup mock to return list of prompts
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[mock_prompt])))
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ImplementationPromptService(mock_db)
        result = await service.get_prompts_for_project("test-project")

        assert len(result) == 1
        assert result[0].id == mock_prompt.id

    @pytest.mark.asyncio
    async def test_generate_component_prompt(self, mock_db):
        """Test generating a component prompt."""
        from app.services.design_os_service import ImplementationPromptService

        service = ImplementationPromptService(mock_db)

        result = await service.generate_component_prompt(
            project_id="test-project",
            section_id="section-001",
            component_name="UserCard",
            design_tokens={"colors": {"primary": "#3b82f6"}},
            target_stack="react",
        )

        # Verify the prompt was created
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_feature_prompt(self, mock_db):
        """Test generating a feature prompt."""
        from app.services.design_os_service import ImplementationPromptService

        service = ImplementationPromptService(mock_db)

        result = await service.generate_feature_prompt(
            project_id="test-project",
            section_id="section-001",
            feature_name="User Profile",
            description="Complete user profile management",
            components=["UserCard", "ProfileForm", "AvatarUpload"],
            target_stack="react",
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_prompt_usage(self, mock_db, mock_prompt):
        """Test recording prompt usage."""
        from app.services.design_os_service import ImplementationPromptService

        # Setup mock to return the prompt
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_prompt)
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ImplementationPromptService(mock_db)
        await service.record_prompt_usage(str(mock_prompt.id))

        # Verify usage was incremented
        assert mock_prompt.times_used == 1
        mock_db.commit.assert_called_once()


class TestScreenWireframeService:
    """Tests for ScreenWireframeService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock async database session."""
        db = Mock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
        db.execute = AsyncMock(return_value=mock_result)

        return db

    @pytest.fixture
    def mock_wireframe(self):
        """Create a mock ScreenWireframe."""
        wireframe = Mock()
        wireframe.id = uuid4()
        wireframe.project_id = "test-project"
        wireframe.name = "Dashboard"
        wireframe.screen_type = "desktop"
        wireframe.spec_id = None
        wireframe.wireframe_svg = None
        wireframe.wireframe_structure = {"layout": "sidebar"}
        wireframe.annotations = []
        wireframe.components = []
        wireframe.responsive_variants = {}
        wireframe.version = 1
        wireframe.parent_version_id = None
        wireframe.tier = "PROFESSIONAL"
        wireframe.created_at = datetime.now(timezone.utc)
        wireframe.to_dict = Mock(return_value={
            "id": str(wireframe.id),
            "name": wireframe.name,
            "version": wireframe.version,
        })
        return wireframe

    @pytest.mark.asyncio
    async def test_create_wireframe(self, mock_db):
        """Test creating a wireframe."""
        from app.services.design_os_service import ScreenWireframeService

        service = ScreenWireframeService(mock_db)

        result = await service.create_wireframe(
            project_id="test-project",
            name="Dashboard",
            screen_type="desktop",
            wireframe_structure={"layout": "sidebar"},
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_wireframe(self, mock_db, mock_wireframe):
        """Test getting a wireframe by ID."""
        from app.services.design_os_service import ScreenWireframeService

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_wireframe)
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ScreenWireframeService(mock_db)
        result = await service.get_wireframe(str(mock_wireframe.id))

        assert result is not None
        assert result.id == mock_wireframe.id

    @pytest.mark.asyncio
    async def test_get_wireframes_for_project(self, mock_db, mock_wireframe):
        """Test getting all wireframes for a project."""
        from app.services.design_os_service import ScreenWireframeService

        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[mock_wireframe])))
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ScreenWireframeService(mock_db)
        result = await service.get_wireframes_for_project("test-project")

        assert len(result) == 1
        assert result[0].id == mock_wireframe.id

    @pytest.mark.asyncio
    async def test_create_version(self, mock_db, mock_wireframe):
        """Test creating a new version of a wireframe."""
        from app.services.design_os_service import ScreenWireframeService

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_wireframe)
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ScreenWireframeService(mock_db)

        result = await service.create_version(
            wireframe_id=str(mock_wireframe.id),
            wireframe_structure={"layout": "top_nav"},
        )

        # Should add a new wireframe
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_annotation(self, mock_db, mock_wireframe):
        """Test adding an annotation to a wireframe."""
        from app.services.design_os_service import ScreenWireframeService

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_wireframe)
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ScreenWireframeService(mock_db)

        result = await service.add_annotation(
            wireframe_id=str(mock_wireframe.id),
            x=100,
            y=200,
            text="Header section",
            annotation_type="note",
        )

        assert len(mock_wireframe.annotations) == 1
        assert mock_wireframe.annotations[0]["text"] == "Header section"

    @pytest.mark.asyncio
    async def test_add_component(self, mock_db, mock_wireframe):
        """Test adding a component to a wireframe."""
        from app.services.design_os_service import ScreenWireframeService

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_wireframe)
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ScreenWireframeService(mock_db)

        result = await service.add_component(
            wireframe_id=str(mock_wireframe.id),
            name="Button",
            position={"x": 50, "y": 100},
            props={"variant": "primary"},
        )

        assert len(mock_wireframe.components) == 1
        assert mock_wireframe.components[0]["name"] == "Button"

    @pytest.mark.asyncio
    async def test_add_responsive_variant(self, mock_db, mock_wireframe):
        """Test adding a responsive variant."""
        from app.services.design_os_service import ScreenWireframeService

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_wireframe)
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ScreenWireframeService(mock_db)

        result = await service.add_responsive_variant(
            wireframe_id=str(mock_wireframe.id),
            breakpoint="mobile",
            variant_structure={"layout": "stacked"},
        )

        assert "mobile" in mock_wireframe.responsive_variants
        assert mock_wireframe.responsive_variants["mobile"]["layout"] == "stacked"

    def test_generate_basic_wireframe_structure_sidebar(self):
        """Test generating sidebar layout structure."""
        from app.services.design_os_service import ScreenWireframeService

        service = ScreenWireframeService(None)

        result = service.generate_basic_wireframe_structure(
            screen_name="Dashboard",
            layout="sidebar",
        )

        assert result["name"] == "Dashboard"
        assert result["layout"] == "sidebar"
        assert "sidebar" in result["sections"]
        assert result["sections"]["sidebar"]["position"] == "left"

    def test_generate_basic_wireframe_structure_top_nav(self):
        """Test generating top nav layout structure."""
        from app.services.design_os_service import ScreenWireframeService

        service = ScreenWireframeService(None)

        result = service.generate_basic_wireframe_structure(
            screen_name="Landing",
            layout="top_nav",
        )

        assert result["layout"] == "top_nav"
        assert "navbar" in result["sections"]
        assert result["sections"]["navbar"]["fixed"] is True

    def test_generate_basic_wireframe_structure_wizard(self):
        """Test generating wizard layout structure."""
        from app.services.design_os_service import ScreenWireframeService

        service = ScreenWireframeService(None)

        result = service.generate_basic_wireframe_structure(
            screen_name="Onboarding",
            layout="wizard",
        )

        assert result["layout"] == "wizard"
        assert "header" in result["sections"]
        assert result["sections"]["header"]["stepIndicator"] is True


class TestPromptTypes:
    """Test prompt type constants."""

    def test_prompt_type_values(self):
        """Test PromptType enum values."""
        from app.models.design_os import PromptType

        assert PromptType.COMPONENT.value == "component"
        assert PromptType.PAGE.value == "page"
        assert PromptType.FEATURE.value == "feature"
        assert PromptType.INTEGRATION.value == "integration"
        assert PromptType.API.value == "api"
        assert PromptType.FULL_PROJECT.value == "full_project"
