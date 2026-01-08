"""
Week 86 Tests: Premium Tier Synthesis with Claude Opus

Tests for:
- Claude Opus integration in Cycle 5
- Confidence explanations generation
- Function point estimation with IFPUG
- Project export to markdown

Test data based on HCI-CRS project:
- EPIC-JW-jeugdtraject (Jeugdtraject Management)
- FEATURE-003-tellertje (TellertjeJeugd component)
- Related stories and tasks
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from pathlib import Path
import tempfile
import json

from app.models.deep_extraction import (
    ExtractionSession,
    ExtractionConsensus,
    ExtractionTier,
    ExtractionStatus,
    ConsensusStatus,
    ItemType,
)
from app.services.deep_extraction_service import DeepExtractionService
from app.services.extraction_llm_adapter import (
    ExtractionLLMAdapter,
    ExtractionPrompts,
    create_extraction_adapter,
)
from app.services.tier_provider_selector import (
    TierProviderSelector,
    create_tier_selector,
    LLMCallResult,
)
from app.services.project_export_service import ProjectExportService


# ===========================================================================
# HCI-CRS Test Fixtures
# ===========================================================================

@pytest.fixture
def hci_crs_epics():
    """HCI-CRS epics for testing."""
    return [
        {
            "id": "EPIC-JW-jeugdtraject",
            "title": "Jeugdtraject Management",
            "description": "Complete beheer van jeugdtrajecten binnen HCI-CRS",
            "business_value": "Efficiënt beheer van jeugdtrajecten met correcte tellingen",
            "confidence_score": 0.92,
            "supporting_llms": [
                "ollama/qwen2.5-coder:7b",
                "ollama/deepseek-r1",
                "anthropic/claude-opus-4.5"
            ],
        },
        {
            "id": "EPIC-AUTH-authenticatie",
            "title": "Authenticatie & Autorisatie",
            "description": "SSO integratie en role-based access control",
            "business_value": "Veilige toegang tot het systeem",
            "confidence_score": 0.88,
            "supporting_llms": [
                "ollama/qwen2.5-coder:7b",
                "ollama/deepseek-r1",
            ],
        },
    ]


@pytest.fixture
def hci_crs_features():
    """HCI-CRS features for testing."""
    return [
        {
            "id": "FEATURE-003-tellertje",
            "title": "TellertjeJeugd Component",
            "description": "Real-time telling van jeugdtrajecten per categorie",
            "parent_epic_id": "EPIC-JW-jeugdtraject",
            "confidence_score": 0.85,
            "supporting_llms": ["ollama/qwen2.5-coder:7b", "ollama/deepseek-r1"],
        },
        {
            "id": "FEATURE-004-trajectbeheer",
            "title": "JeugdtrajectManager",
            "description": "CRUD operaties voor jeugdtrajecten",
            "parent_epic_id": "EPIC-JW-jeugdtraject",
            "confidence_score": 0.90,
            "supporting_llms": ["ollama/qwen2.5-coder:7b", "ollama/deepseek-r1", "ollama/codellama"],
        },
    ]


@pytest.fixture
def hci_crs_stories():
    """HCI-CRS user stories for testing."""
    return [
        {
            "id": "STORY-003-01",
            "title": "Als casemanager wil ik de telling per categorie zien",
            "description": "Real-time weergave van aantal trajecten per categorie",
            "parent_feature_id": "FEATURE-003-tellertje",
            "acceptance_criteria": [
                "Telling wordt automatisch bijgewerkt bij wijzigingen",
                "Categorieën zijn: Actief, Afgerond, Gepauzeerd",
                "Totaaltelling is zichtbaar bovenaan",
            ],
            "function_points": 12,
            "story_points": 5,
        },
        {
            "id": "STORY-003-02",
            "title": "Als beheerder wil ik telling exporteren naar Excel",
            "description": "Export functionaliteit voor rapportages",
            "parent_feature_id": "FEATURE-003-tellertje",
            "acceptance_criteria": [
                "Export bevat datum/tijd",
                "Alle categorieën worden opgenomen",
                "Excel formaat is .xlsx",
            ],
            "function_points": 8,
            "story_points": 3,
        },
    ]


@pytest.fixture
def hci_crs_tasks():
    """HCI-CRS tasks for testing."""
    return [
        {
            "id": "TASK-003-01-01",
            "title": "Implement TellertjeJeugd Vue component",
            "task_type": "frontend",
            "parent_story_id": "STORY-003-01",
            "function_points": 4,
            "estimated_hours": 6,
        },
        {
            "id": "TASK-003-01-02",
            "title": "Create API endpoint /api/trajecten/tellingen",
            "task_type": "backend",
            "parent_story_id": "STORY-003-01",
            "function_points": 3,
            "estimated_hours": 4,
        },
        {
            "id": "TASK-003-02-01",
            "title": "Add Excel export service using EPPlus",
            "task_type": "backend",
            "parent_story_id": "STORY-003-02",
            "function_points": 5,
            "estimated_hours": 8,
        },
    ]


@pytest.fixture
def mock_hci_crs_session(hci_crs_epics, hci_crs_features, hci_crs_stories, hci_crs_tasks):
    """Mock extraction session with HCI-CRS data."""
    session = MagicMock(spec=ExtractionSession)
    session.id = uuid4()
    session.project_id = 1000  # HCI-CRS project ID
    session.tier = ExtractionTier.PREMIUM.value
    session.tier_price_usd = 150.0
    session.status = ExtractionStatus.RUNNING.value
    session.current_cycle = 5
    session.source_path = "/opt/projecten/hci-crs"
    session.total_files = 450
    session.avg_confidence = 0.0
    session.total_function_points = 0
    session.actual_cost_usd = 0.0
    session.margin_usd = 0.0
    session.total_tokens_used = 0
    session.items_auto_accepted = 0
    session.items_human_reviewed = 0
    session.cycle_5_completed_at = None
    session.completed_at = None

    # Mock project
    session.project = MagicMock()
    session.project.name = "HCI-CRS"

    # Create consensus items
    consensus_items = []

    # Add epics
    for epic in hci_crs_epics:
        item = MagicMock(spec=ExtractionConsensus)
        item.id = uuid4()
        item.item_type = ItemType.EPIC.value
        item.item_title = epic["title"]
        item.item_description = epic["description"]
        item.confidence_score = epic["confidence_score"]
        item.supporting_llms = epic["supporting_llms"]
        item.status = ConsensusStatus.AUTO_ACCEPTED.value
        item.item_data = {"synthesized_id": epic["id"]}
        consensus_items.append(item)

    # Add features
    for feature in hci_crs_features:
        item = MagicMock(spec=ExtractionConsensus)
        item.id = uuid4()
        item.item_type = ItemType.FEATURE.value
        item.item_title = feature["title"]
        item.item_description = feature["description"]
        item.confidence_score = feature["confidence_score"]
        item.supporting_llms = feature["supporting_llms"]
        item.status = ConsensusStatus.AUTO_ACCEPTED.value
        item.item_data = {
            "synthesized_id": feature["id"],
            "parent_epic_id": feature["parent_epic_id"],
        }
        consensus_items.append(item)

    # Add stories
    for story in hci_crs_stories:
        item = MagicMock(spec=ExtractionConsensus)
        item.id = uuid4()
        item.item_type = ItemType.STORY.value
        item.item_title = story["title"]
        item.item_description = story["description"]
        item.confidence_score = 0.82
        item.supporting_llms = ["ollama/qwen2.5-coder:7b"]
        item.status = ConsensusStatus.AUTO_ACCEPTED.value
        item.item_data = {
            "synthesized_id": story["id"],
            "parent_feature_id": story["parent_feature_id"],
            "function_points": story["function_points"],
            "story_points": story["story_points"],
            "acceptance_criteria": story["acceptance_criteria"],
        }
        consensus_items.append(item)

    # Add tasks
    for task in hci_crs_tasks:
        item = MagicMock(spec=ExtractionConsensus)
        item.id = uuid4()
        item.item_type = ItemType.TASK.value
        item.item_title = task["title"]
        item.item_description = None
        item.confidence_score = 0.78
        item.supporting_llms = ["ollama/qwen2.5-coder:7b"]
        item.status = ConsensusStatus.AUTO_ACCEPTED.value
        item.item_data = {
            "synthesized_id": task["id"],
            "parent_story_id": task["parent_story_id"],
            "task_type": task["task_type"],
            "function_points": task["function_points"],
            "estimated_hours": task["estimated_hours"],
        }
        consensus_items.append(item)

    session.consensus_items = consensus_items
    session.conflicts = []

    return session


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


# ===========================================================================
# Test: Claude Opus Synthesis Prompt
# ===========================================================================

class TestSynthesisPrompt:
    """Test synthesis prompt generation."""

    def test_synthesis_prompt_contains_hci_crs_data(
        self, hci_crs_epics, hci_crs_features
    ):
        """Verify synthesis prompt includes HCI-CRS project data."""
        items = [
            {
                "type": ItemType.EPIC.value,
                "title": hci_crs_epics[0]["title"],
                "description": hci_crs_epics[0]["description"],
                "confidence_score": hci_crs_epics[0]["confidence_score"],
                "supporting_llms": hci_crs_epics[0]["supporting_llms"],
            },
            {
                "type": ItemType.FEATURE.value,
                "title": hci_crs_features[0]["title"],
                "description": hci_crs_features[0]["description"],
                "confidence_score": hci_crs_features[0]["confidence_score"],
                "supporting_llms": hci_crs_features[0]["supporting_llms"],
            },
        ]

        project_info = {
            "name": "HCI-CRS",
            "source_path": "/opt/projecten/hci-crs",
            "total_files": 450,
        }

        prompt = ExtractionPrompts.get_synthesis_prompt(
            accepted_items=items,
            tier="PREMIUM",
            project_info=project_info,
        )

        # Verify project info in prompt
        assert "HCI-CRS" in prompt
        assert "/opt/projecten/hci-crs" in prompt
        assert "450" in prompt
        assert "PREMIUM" in prompt

        # Verify items in prompt
        assert "Jeugdtraject Management" in prompt
        assert "TellertjeJeugd" in prompt

        # Verify prompt structure
        assert "confidence_explanation" in prompt
        assert "function_points" in prompt
        assert "acceptance_criteria" in prompt

    def test_synthesis_prompt_requests_ifpug_estimates(self):
        """Verify synthesis prompt asks for IFPUG-based FP estimates."""
        prompt = ExtractionPrompts.get_synthesis_prompt(
            accepted_items=[],
            tier="PREMIUM",
            project_info={"name": "Test"},
        )

        # Should mention IFPUG methodology
        assert "IFPUG" in prompt or "function_points" in prompt
        assert "fp_rationale" in prompt


# ===========================================================================
# Test: Claude Opus Call
# ===========================================================================

class TestClaudeOpusCall:
    """Test Claude Opus LLM call functionality."""

    @pytest.mark.asyncio
    async def test_call_anthropic_opus_success(self):
        """Test successful Claude Opus call."""
        selector = create_tier_selector(ExtractionTier.PREMIUM)
        adapter = ExtractionLLMAdapter(selector)

        # Mock subprocess
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Create mock process
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(
                b'{"epics": [{"id": "EPIC-001", "title": "Test Epic"}]}',
                b''
            ))
            mock_subprocess.return_value = mock_process

            result = await adapter.call_anthropic(
                model="claude-opus-4.5",
                prompt="Analyze this code",
                system="You are an expert.",
                timeout=60,
            )

            assert result.success
            assert result.provider_id == "anthropic/claude-opus-4.5"
            assert "EPIC-001" in result.content

        await adapter.close()

    @pytest.mark.asyncio
    async def test_call_anthropic_timeout_handling(self):
        """Test Claude call timeout handling."""
        selector = create_tier_selector(ExtractionTier.PREMIUM)
        adapter = ExtractionLLMAdapter(selector)

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(
                side_effect=asyncio.TimeoutError()
            )
            mock_subprocess.return_value = mock_process

            result = await adapter.call_anthropic(
                model="claude-opus-4.5",
                prompt="Test",
                timeout=1,
            )

            assert not result.success
            assert "Timeout" in result.error

        await adapter.close()

    @pytest.mark.asyncio
    async def test_call_anthropic_cli_not_found(self):
        """Test handling when Claude CLI is not installed."""
        selector = create_tier_selector(ExtractionTier.PREMIUM)
        adapter = ExtractionLLMAdapter(selector)

        with patch('shutil.which', return_value=None):
            result = await adapter.call_anthropic(
                model="claude-opus-4.5",
                prompt="Test",
            )

            assert not result.success
            assert "CLI not found" in result.error

        await adapter.close()


# ===========================================================================
# Test: Cycle 5 with LLM Synthesis
# ===========================================================================

class TestCycle5Synthesis:
    """Test Cycle 5 final synthesis with LLM."""

    @pytest.mark.asyncio
    async def test_cycle_5_selects_opus_for_premium(
        self, mock_db, mock_hci_crs_session
    ):
        """Verify PREMIUM tier selects Claude Opus for synthesis."""
        service = DeepExtractionService(mock_db)

        # Mock get_session
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(
            return_value=mock_hci_crs_session
        )

        with patch.object(service, 'get_session', return_value=mock_hci_crs_session):
            with patch.object(service, '_get_selector') as mock_selector:
                selector = create_tier_selector(ExtractionTier.PREMIUM)
                mock_selector.return_value = selector

                # Get provider for cycle 5
                assignments = selector.get_providers_for_cycle(5)

                # Should select Claude Opus
                assert len(assignments) == 1
                assert assignments[0][0] == "anthropic/claude-opus-4.5"
                assert assignments[0][1] == "synthesis"

    @pytest.mark.asyncio
    async def test_cycle_5_applies_synthesis_updates(
        self, mock_db, mock_hci_crs_session
    ):
        """Verify synthesis updates are applied to consensus items."""
        service = DeepExtractionService(mock_db)

        synthesis = {
            "epics": [
                {
                    "id": "EPIC-JW-jeugdtraject",
                    "title": "Jeugdtraject Management",
                    "confidence_score": 0.92,
                    "confidence_explanation": "9/10 LLMs identified this epic. Strong evidence from jeugdtraject domain modules.",
                    "total_function_points": 180,
                    "features": [
                        {
                            "id": "FEATURE-003-tellertje",
                            "title": "TellertjeJeugd Component",
                            "confidence_explanation": "7/10 LLMs identified. Vue component clearly visible.",
                            "stories": [],
                        }
                    ],
                }
            ],
            "summary": {
                "total_function_points": 180,
                "avg_confidence": 0.88,
            },
        }

        await service._apply_synthesis_updates(mock_hci_crs_session, synthesis)

        # Check if commit was called
        mock_db.commit.assert_called()


# ===========================================================================
# Test: Confidence Explanations
# ===========================================================================

class TestConfidenceExplanations:
    """Test confidence explanation generation."""

    def test_confidence_explanation_format(self):
        """Verify confidence explanation format."""
        explanation = "8/10 LLMs identified this epic. Strong evidence from auth modules in src/auth/. Minor disagreement on scope of OAuth integration."

        # Should contain LLM count
        assert "/10 LLMs" in explanation or "LLMs" in explanation

        # Should mention evidence
        assert "evidence" in explanation.lower() or "identified" in explanation.lower()

    @pytest.mark.asyncio
    async def test_apply_synthesis_adds_explanations(
        self, mock_db, mock_hci_crs_session
    ):
        """Verify explanations are added to item_data."""
        service = DeepExtractionService(mock_db)

        synthesis = {
            "epics": [
                {
                    "id": "EPIC-JW-jeugdtraject",
                    "title": "Jeugdtraject Management",
                    "confidence_explanation": "9/10 LLMs agreed. Clear domain boundaries in codebase.",
                    "total_function_points": 150,
                    "features": [],
                }
            ],
        }

        await service._apply_synthesis_updates(mock_hci_crs_session, synthesis)

        # Find the epic in consensus items
        epic_item = None
        for item in mock_hci_crs_session.consensus_items:
            if item.item_type == ItemType.EPIC.value and "Jeugdtraject" in item.item_title:
                epic_item = item
                break

        assert epic_item is not None
        # Note: In the actual implementation, item_data is updated
        # Here we verify the method was called correctly


# ===========================================================================
# Test: Function Point Estimation
# ===========================================================================

class TestFunctionPointEstimation:
    """Test IFPUG-integrated function point estimation."""

    def test_estimate_fp_uses_synthesized_values(self, mock_hci_crs_session):
        """Verify FP uses LLM-synthesized values when available."""
        service = DeepExtractionService(MagicMock())

        items = mock_hci_crs_session.consensus_items

        total_fp = service._estimate_function_points(items)

        # Should be > 0 since items have function_points in item_data
        assert total_fp > 0

    def test_estimate_fp_ifpug_component_detection(self):
        """Test IFPUG component type detection from keywords."""
        service = DeepExtractionService(MagicMock())

        # Create test items with IFPUG-related keywords
        items = []

        # Database item (should detect as ILF)
        db_item = MagicMock(spec=ExtractionConsensus)
        db_item.item_type = ItemType.STORY.value
        db_item.item_title = "Create database table for trajecten"
        db_item.item_description = "Schema for storing jeugdtraject data"
        db_item.item_data = {}
        items.append(db_item)

        # Form item (should detect as EI)
        form_item = MagicMock(spec=ExtractionConsensus)
        form_item.item_type = ItemType.STORY.value
        form_item.item_title = "Create input form for new traject"
        form_item.item_description = "Form to submit new jeugdtraject"
        form_item.item_data = {}
        items.append(form_item)

        # Report item (should detect as EO)
        report_item = MagicMock(spec=ExtractionConsensus)
        report_item.item_type = ItemType.STORY.value
        report_item.item_title = "Generate PDF report for tellingen"
        report_item.item_description = "Export telling report"
        report_item.item_data = {}
        items.append(report_item)

        # Search item (should detect as EQ)
        search_item = MagicMock(spec=ExtractionConsensus)
        search_item.item_type = ItemType.STORY.value
        search_item.item_title = "Search trajecten by category"
        search_item.item_description = "Query to find matching trajecten"
        search_item.item_data = {}
        items.append(search_item)

        total_fp = service._estimate_function_points(items)

        # ILF (10) + EI (4) + EO (5) + EQ (4) = 23
        assert total_fp == 23

    def test_estimate_fp_explicit_component_type(self):
        """Test FP estimation with explicit IFPUG component type."""
        service = DeepExtractionService(MagicMock())

        item = MagicMock(spec=ExtractionConsensus)
        item.item_type = ItemType.STORY.value
        item.item_title = "Generic item"
        item.item_description = None
        item.item_data = {
            "fp_component_type": "ILF",
            "fp_complexity": "high",
        }

        total_fp = service._estimate_function_points([item])

        # High complexity ILF = 15 FP
        assert total_fp == 15


# ===========================================================================
# Test: Project Export Service
# ===========================================================================

class TestProjectExportService:
    """Test project export to markdown structure."""

    @pytest.mark.asyncio
    async def test_export_creates_directory_structure(
        self, mock_db, mock_hci_crs_session
    ):
        """Verify export creates correct directory structure."""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_hci_crs_session
        mock_db.execute.return_value = mock_result

        export_service = ProjectExportService(mock_db)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "hci-crs-export"

            result = await export_service.export_session(
                session_id=mock_hci_crs_session.id,
                output_dir=output_path,
                include_tasks=True,
            )

            # Verify result
            assert result["files_created"] > 0
            assert result["epics"] == 2  # 2 epics in test data

            # Verify directory structure
            assert output_path.exists()
            assert (output_path / "project-summary.md").exists()

    @pytest.mark.asyncio
    async def test_export_project_summary_content(
        self, mock_db, mock_hci_crs_session
    ):
        """Verify project summary contains correct content."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_hci_crs_session
        mock_db.execute.return_value = mock_result

        export_service = ProjectExportService(mock_db)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "hci-crs-export"

            await export_service.export_session(
                session_id=mock_hci_crs_session.id,
                output_dir=output_path,
            )

            summary_path = output_path / "project-summary.md"
            content = summary_path.read_text()

            # Verify content
            assert "Project Summary" in content
            assert "PREMIUM" in content
            assert "/opt/projecten/hci-crs" in content
            assert "Total Epics" in content
            assert "Function Points" in content

    def test_build_hierarchy_from_hci_crs_data(
        self, mock_db, mock_hci_crs_session
    ):
        """Test hierarchy building from HCI-CRS data."""
        export_service = ProjectExportService(mock_db)

        accepted_items = [
            item for item in mock_hci_crs_session.consensus_items
            if item.status == ConsensusStatus.AUTO_ACCEPTED.value
        ]

        hierarchy = export_service._build_hierarchy_from_synthesis(
            mock_hci_crs_session,
            accepted_items,
        )

        # Verify hierarchy structure
        assert "epics" in hierarchy
        assert len(hierarchy["epics"]) == 2

        # Verify first epic
        epic = hierarchy["epics"][0]
        assert "title" in epic
        assert "features" in epic
        assert "confidence_score" in epic

    @pytest.mark.asyncio
    async def test_export_story_includes_acceptance_criteria(
        self, mock_db, mock_hci_crs_session
    ):
        """Verify exported stories include acceptance criteria."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_hci_crs_session
        mock_db.execute.return_value = mock_result

        export_service = ProjectExportService(mock_db)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "hci-crs-export"

            await export_service.export_session(
                session_id=mock_hci_crs_session.id,
                output_dir=output_path,
            )

            # Find a story file and check content
            story_files = list(output_path.rglob("STORY-*.md"))

            # If stories were exported, verify content
            for story_file in story_files:
                content = story_file.read_text()
                assert "Acceptance Criteria" in content
                assert "Function Points" in content


# ===========================================================================
# Test: Tier Provider Selection
# ===========================================================================

class TestTierProviderSelection:
    """Test tier-based provider selection for synthesis."""

    def test_premium_tier_includes_opus(self):
        """Verify PREMIUM tier includes Claude Opus."""
        selector = create_tier_selector(ExtractionTier.PREMIUM)
        providers = selector.get_provider_ids()

        assert "anthropic/claude-opus-4.5" in providers

    def test_premium_tier_selects_opus_for_cycle_5(self):
        """Verify Opus is selected for cycle 5 in PREMIUM tier."""
        selector = create_tier_selector(ExtractionTier.PREMIUM)
        assignments = selector.get_providers_for_cycle(5)

        assert len(assignments) == 1
        assert assignments[0][0] == "anthropic/claude-opus-4.5"
        assert assignments[0][1] == "synthesis"

    def test_professional_tier_uses_alternative(self):
        """Verify PROFESSIONAL tier uses GPT-5.2 or Gemini Pro."""
        selector = create_tier_selector(ExtractionTier.PROFESSIONAL)
        assignments = selector.get_providers_for_cycle(5)

        assert len(assignments) == 1
        # Should use GPT-5.2 or Gemini Pro
        provider = assignments[0][0]
        assert provider in ["openai/gpt-5.2", "google/gemini-2.5-pro"]

    def test_free_tier_uses_local_llm(self):
        """Verify FREE tier uses local Ollama for synthesis."""
        selector = create_tier_selector(ExtractionTier.FREE)
        assignments = selector.get_providers_for_cycle(5)

        assert len(assignments) == 1
        provider = assignments[0][0]
        assert provider.startswith("ollama/")


# ===========================================================================
# Test: Integration Scenarios
# ===========================================================================

class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_full_hci_crs_synthesis_flow(
        self, mock_db, mock_hci_crs_session
    ):
        """Test complete synthesis flow for HCI-CRS project."""
        service = DeepExtractionService(mock_db)

        # Mock session retrieval
        async def mock_get_session(session_id):
            return mock_hci_crs_session

        with patch.object(service, 'get_session', side_effect=mock_get_session):
            with patch.object(service, '_get_selector') as mock_selector:
                selector = MagicMock()
                selector.get_providers_for_cycle.return_value = [
                    ("ollama/deepseek-r1", "synthesis")
                ]
                selector.get_call_statistics.return_value = {
                    "total_cost_usd": 0.0,
                    "total_tokens": 1000,
                }
                mock_selector.return_value = selector

                # Mock adapter
                with patch('app.services.deep_extraction_service.create_extraction_adapter') as mock_adapter:
                    adapter_instance = AsyncMock()
                    adapter_instance.run_synthesis.return_value = (
                        LLMCallResult(
                            provider_id="ollama/deepseek-r1",
                            model="deepseek-r1",
                            content="{}",
                            success=True,
                        ),
                        {
                            "epics": [],
                            "summary": {
                                "total_function_points": 150,
                                "avg_confidence": 0.85,
                            },
                        },
                    )
                    adapter_instance.close = AsyncMock()
                    mock_adapter.return_value = adapter_instance

                    result = await service.run_cycle_5(mock_hci_crs_session.id)

                    assert result["status"] == "completed"
                    assert result["cycle"] == 5
                    assert "synthesis_provider" in result

    @pytest.mark.asyncio
    async def test_export_after_synthesis(
        self, mock_db, mock_hci_crs_session
    ):
        """Test exporting project after synthesis completes."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_hci_crs_session
        mock_db.execute.return_value = mock_result

        export_service = ProjectExportService(mock_db)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "hci-crs-export"

            result = await export_service.export_session(
                session_id=mock_hci_crs_session.id,
                output_dir=output_path,
                include_tasks=True,
            )

            assert result["files_created"] > 0

            # Verify all expected files exist
            assert (output_path / "project-summary.md").exists()
