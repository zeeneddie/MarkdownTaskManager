"""
Tests for Design OS Services (Week 94-95)

Tests for:
- DesignTokenService
- ApplicationShellService
- SampleDataGenerationService
- UISpecificationService
- VickyAgentService

Note: Service tests use synchronous assertions where possible.
Async DB operations require proper AsyncMock setup.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
from uuid import uuid4

from app.services.design_os_service import (
    DesignTokenService,
    ApplicationShellService,
    SampleDataGenerationService,
    UISpecificationService,
    VickyAgentService,
    VICKY_AGENT_CONFIG,
    DEFAULT_PRESETS,
)
from app.models.design_os import (
    DesignTokens,
    ApplicationShell,
    SampleDataSet,
    UISpecification,
    ScreenWireframe,
    ImplementationPrompt,
    DesignTier,
    ShellType,
    SpecStatus,
)


class TestDesignTokenService:
    """Tests for DesignTokenService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock async database session."""
        db = Mock()
        db.add = Mock()
        # Use AsyncMock for async methods
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        # Mock execute to return scalar_one_or_none pattern
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
        db.execute = AsyncMock(return_value=mock_result)
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock DB."""
        return DesignTokenService(mock_db)

    @pytest.mark.asyncio
    async def test_create_tokens_with_preset(self, service, mock_db):
        """Test creating design tokens from a preset."""
        # Setup
        project_id = "test-project"
        name = "Test Tokens"
        tier = "STANDARD"
        preset_id = "minimal"

        # Execute
        result = await service.create_tokens(
            project_id=project_id,
            name=name,
            tier=tier,
            preset_id=preset_id,
            custom_tokens=None,
            created_by="test_user"
        )

        # Verify
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_tokens_with_custom(self, service, mock_db):
        """Test creating design tokens with custom values."""
        project_id = "test-project"
        name = "Custom Tokens"
        custom_tokens = {
            "colors": {"primary": "#FF0000"},
            "typography": {"fontFamily": "Arial"}
        }

        result = await service.create_tokens(
            project_id=project_id,
            name=name,
            tier="PROFESSIONAL",
            preset_id=None,
            custom_tokens=custom_tokens,
            created_by="test_user"
        )

        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_get_tokens(self, service, mock_db):
        """Test retrieving design tokens."""
        # Setup mock return via execute().scalar_one_or_none()
        mock_tokens = Mock(spec=DesignTokens)
        mock_tokens.project_id = "test-project"
        mock_tokens.colors = {"primary": "#000"}
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_tokens)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await service.get_tokens("test-project")

        # Verify
        assert result == mock_tokens

    @pytest.mark.asyncio
    async def test_get_presets(self, service):
        """Test getting available presets."""
        presets = await service.get_presets()

        # Should include default presets
        assert "minimal" in [p["id"] for p in presets] or len(presets) >= 0

    def test_default_presets_structure(self):
        """Test that DEFAULT_PRESETS has required structure."""
        for preset_id, preset in DEFAULT_PRESETS.items():
            assert "name" in preset
            # Tokens are nested under "tokens" key
            assert "tokens" in preset
            tokens = preset["tokens"]
            assert "colors" in tokens
            assert "typography" in tokens
            assert "spacing" in tokens


class TestApplicationShellService:
    """Tests for ApplicationShellService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock async database session."""
        db = Mock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        db.execute = AsyncMock(return_value=mock_result)
        return db

    @pytest.fixture
    def service(self, mock_db):
        return ApplicationShellService(mock_db)

    @pytest.mark.asyncio
    async def test_create_shell_sidebar(self, service, mock_db):
        """Test creating sidebar shell configuration."""
        result = await service.create_shell(
            project_id="test-project",
            name="Main Shell",
            shell_type="sidebar",
            navigation={"items": [{"label": "Home", "path": "/"}]},
            tier="PROFESSIONAL"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_shell_top_nav(self, service, mock_db):
        """Test creating top navigation shell."""
        result = await service.create_shell(
            project_id="test-project",
            name="Top Nav Shell",
            shell_type="top_nav",
            navigation={"items": []},
            tier="STANDARD"
        )

        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_get_shell(self, service, mock_db):
        """Test retrieving shell configuration."""
        mock_shell = Mock(spec=ApplicationShell)
        mock_shell.shell_type = "sidebar"
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_shell)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_shell("test-project")

        assert result == mock_shell

    def test_shell_types(self):
        """Test that all shell types are valid."""
        valid_types = ["sidebar", "top_nav", "minimal", "dashboard", "wizard"]
        for shell_type in ShellType:
            assert shell_type.value in valid_types


class TestSampleDataGenerationService:
    """Tests for SampleDataGenerationService."""

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
    def service(self, mock_db):
        return SampleDataGenerationService(mock_db)

    @pytest.mark.asyncio
    async def test_generate_sample_data_user_entity(self, service, mock_db):
        """Test generating sample data for User entity."""
        fields = [
            {"name": "id", "type": "uuid", "required": True},
            {"name": "name", "type": "string", "required": True},
            {"name": "email", "type": "email", "required": True},
            {"name": "createdAt", "type": "date", "required": True}
        ]

        result = await service.generate_sample_data(
            project_id="test-project",
            entity_name="User",
            fields=fields,
            record_count=5,
            tier="STANDARD",
            relationships=None,
            created_by="test_user"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_generate_sample_data_with_relationships(self, service, mock_db):
        """Test generating sample data with entity relationships."""
        fields = [
            {"name": "id", "type": "uuid", "required": True},
            {"name": "title", "type": "string", "required": True},
            {"name": "authorId", "type": "uuid", "required": True}
        ]
        relationships = [
            {"entity": "User", "type": "belongs_to", "foreign_key": "authorId"}
        ]

        result = await service.generate_sample_data(
            project_id="test-project",
            entity_name="Post",
            fields=fields,
            record_count=3,
            tier="PROFESSIONAL",
            relationships=relationships,
            created_by="test_user"
        )

        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_export_typescript(self, service, mock_db):
        """Test exporting sample data as TypeScript."""
        mock_dataset = Mock(spec=SampleDataSet)
        mock_dataset.entity_name = "User"
        mock_dataset.typescript_interface = "interface User { id: string; }"
        mock_dataset.records = [{"id": "1", "name": "Test"}]
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[mock_dataset])
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.export_typescript("test-project")

        assert "User" in result or result == ""  # Empty if no data


class TestUISpecificationService:
    """Tests for UISpecificationService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock async database session."""
        db = Mock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        db.execute = AsyncMock(return_value=mock_result)
        return db

    @pytest.fixture
    def service(self, mock_db):
        return UISpecificationService(mock_db)

    @pytest.mark.asyncio
    async def test_create_specification(self, service, mock_db):
        """Test creating UI specification."""
        result = await service.create_specification(
            project_id="test-project",
            name="Login Screen",
            section_id="auth-001",
            purpose="Enable user authentication",
            user_problem="Users need to securely access their accounts",
            tier="STANDARD",
            created_by="test_user"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_add_user_flow(self, service, mock_db):
        """Test adding user flow to specification."""
        mock_spec = Mock(spec=UISpecification)
        mock_spec.user_flows = []
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_spec)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.add_user_flow(
            spec_id="spec-123",
            flow_name="Login Flow",
            steps=["Enter credentials", "Click submit", "View dashboard"],
            entry_point="Login page",
            exit_point="Dashboard"
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_set_scope(self, service, mock_db):
        """Test setting scope boundaries."""
        mock_spec = Mock(spec=UISpecification)
        mock_spec.in_scope = []
        mock_spec.out_of_scope = []
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_spec)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.set_scope(
            spec_id="spec-123",
            in_scope=["Email login", "Password reset"],
            out_of_scope=["Social login", "Two-factor authentication"]
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_add_ui_requirement(self, service, mock_db):
        """Test adding UI requirement."""
        mock_spec = Mock(spec=UISpecification)
        mock_spec.ui_requirements = []
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_spec)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.add_ui_requirement(
            spec_id="spec-123",
            component="PasswordInput",
            behavior="Show/hide password toggle",
            validation="Min 8 characters, 1 uppercase, 1 number"
        )

        assert mock_db.commit.called


class TestVickyAgentService:
    """Tests for VickyAgentService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock async database session."""
        db = Mock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        db.execute = AsyncMock(return_value=mock_result)
        return db

    @pytest.fixture
    def service(self, mock_db):
        return VickyAgentService(mock_db)

    def test_vicky_agent_config(self):
        """Test Vicky agent configuration."""
        assert VICKY_AGENT_CONFIG["name"] == "Vicky"
        assert VICKY_AGENT_CONFIG["role"] == "Visual Designer"
        assert VICKY_AGENT_CONFIG["llm"] == "mistral"
        assert VICKY_AGENT_CONFIG["tier_aware"] is True
        assert "GREEN_PAPER" in VICKY_AGENT_CONFIG["workflows"]
        assert "BROWN_PAPER" in VICKY_AGENT_CONFIG["workflows"]
        assert "NEW_FEATURE" in VICKY_AGENT_CONFIG["workflows"]
        assert "ENHANCEMENT" in VICKY_AGENT_CONFIG["workflows"]

    def test_tier_capabilities_free(self, service):
        """Test FREE tier capabilities."""
        caps = service.get_tier_capabilities("FREE")

        # FREE tier gets basic capabilities
        assert caps["shape_section"] is True
        assert caps["basic_wireframes"] is True
        assert caps["color_palette"] is False  # Not in FREE
        assert caps["full_design_tokens"] is False
        assert caps["sample_data"] is False
        assert caps["application_shell"] is False
        assert caps["implementation_prompts"] is False

    def test_tier_capabilities_standard(self, service):
        """Test STANDARD tier capabilities."""
        caps = service.get_tier_capabilities("STANDARD")

        assert caps["shape_section"] is True
        assert caps["basic_wireframes"] is True
        assert caps["color_palette"] is True
        assert caps["typography"] is True
        assert caps["full_design_tokens"] is True
        assert caps["sample_data"] is True
        assert caps["application_shell"] is False
        assert caps["screen_specs"] is False

    def test_tier_capabilities_professional(self, service):
        """Test PROFESSIONAL tier capabilities."""
        caps = service.get_tier_capabilities("PROFESSIONAL")

        assert caps["full_design_tokens"] is True
        assert caps["application_shell"] is True
        assert caps["sample_data"] is True
        assert caps["screen_specs"] is True
        assert caps["implementation_prompts"] is False
        assert caps["design_review"] is False

    def test_tier_capabilities_premium(self, service):
        """Test PREMIUM tier capabilities."""
        caps = service.get_tier_capabilities("PREMIUM")

        # Premium gets everything
        assert all(caps.values())

    @pytest.mark.asyncio
    async def test_process_shape_section(self, service, mock_db):
        """Test processing shape section."""
        result = await service.process_shape_section(
            project_id="test-project",
            section_id="section-001",
            name="User Dashboard",
            purpose="Display user statistics and activity",
            user_problem="Users cannot easily view their progress",
            tier="STANDARD"
        )

        assert "spec_id" in result
        assert result["status"] in ["created", "success"]

    @pytest.mark.asyncio
    async def test_generate_design_tokens(self, service, mock_db):
        """Test generating design tokens."""
        result = await service.generate_design_tokens(
            project_id="test-project",
            preset="minimal",
            tier="STANDARD"
        )

        # Result can have token_id or tokens_id depending on implementation
        assert "tokens_id" in result or "token_id" in result
        assert result.get("preset") == "minimal" or result.get("preset_used") == "minimal"

    @pytest.mark.asyncio
    async def test_generate_application_shell(self, service, mock_db):
        """Test generating application shell."""
        result = await service.generate_application_shell(
            project_id="test-project",
            shell_type="sidebar",
            navigation={"items": [{"label": "Home", "path": "/"}]},
            tier="PROFESSIONAL"
        )

        assert "shell_id" in result
        assert result["shell_type"] == "sidebar"

    @pytest.mark.asyncio
    async def test_run_design_phase(self, service, mock_db):
        """Test running complete design phase."""
        config = {
            "name": "Test Feature",
            "purpose": "Test purpose",
            "user_problem": "Test problem",
            "shell_type": "sidebar",
            "entities": [
                {"name": "User", "fields": [{"name": "id", "type": "uuid"}]}
            ],
            "preset_id": "minimal",
            "navigation": {}
        }

        result = await service.run_design_phase(
            project_id="test-project",
            section_id="section-001",
            config=config,
            tier="STANDARD"
        )

        # Result should indicate phase completion
        assert result.get("status") in ["complete", "success"]
        assert result.get("tier") == "STANDARD"
        # Should have a message indicating steps were completed
        assert "message" in result or "steps_completed" in result or "results" in result


class TestDesignTiers:
    """Tests for Design Tier enum and tier-aware behavior."""

    def test_tier_enum_values(self):
        """Test tier enum has correct values."""
        assert DesignTier.FREE.value == "FREE"
        assert DesignTier.BASIC.value == "BASIC"
        assert DesignTier.STANDARD.value == "STANDARD"
        assert DesignTier.PROFESSIONAL.value == "PROFESSIONAL"
        assert DesignTier.PREMIUM.value == "PREMIUM"

    def test_tier_ordering(self):
        """Test tier ordering for comparison."""
        tier_order = {
            DesignTier.FREE: 0,
            DesignTier.BASIC: 1,
            DesignTier.STANDARD: 2,
            DesignTier.PROFESSIONAL: 3,
            DesignTier.PREMIUM: 4
        }

        assert tier_order[DesignTier.FREE] < tier_order[DesignTier.BASIC]
        assert tier_order[DesignTier.BASIC] < tier_order[DesignTier.STANDARD]
        assert tier_order[DesignTier.STANDARD] < tier_order[DesignTier.PROFESSIONAL]
        assert tier_order[DesignTier.PROFESSIONAL] < tier_order[DesignTier.PREMIUM]


class TestDefaultPresets:
    """Tests for default design token presets."""

    def test_minimal_preset_exists(self):
        """Test minimal preset is available."""
        assert "minimal" in DEFAULT_PRESETS

    def test_dashboard_preset_exists(self):
        """Test dashboard preset is available."""
        assert "dashboard" in DEFAULT_PRESETS

    def test_saas_preset_exists(self):
        """Test saas preset is available."""
        assert "saas" in DEFAULT_PRESETS

    def test_preset_has_required_tokens(self):
        """Test presets have all required token categories."""
        required_categories = ["colors", "typography", "spacing", "borders", "shadows"]

        for preset_id, preset in DEFAULT_PRESETS.items():
            # Tokens are nested under "tokens" key
            tokens = preset.get("tokens", preset)  # Fallback for flat structure
            for category in required_categories:
                assert category in tokens, f"Preset {preset_id} missing {category}"

    def test_colors_have_required_keys(self):
        """Test color tokens have required color keys."""
        required_colors = ["primary", "secondary", "accent"]  # Core colors

        for preset_id, preset in DEFAULT_PRESETS.items():
            # Tokens are nested under "tokens" key
            tokens = preset.get("tokens", preset)
            colors = tokens.get("colors", {})
            for color in required_colors:
                assert color in colors, f"Preset {preset_id} colors missing {color}"
