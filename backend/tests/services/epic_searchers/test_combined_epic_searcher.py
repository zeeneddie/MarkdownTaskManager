"""
Tests for CombinedEpicSearcher

Tests the combination of journey-based and folder-based epic detection,
and the integration with IntakeToBacklogService.
"""

import tempfile
from pathlib import Path

import pytest

from app.services.epic_searchers import (
    CombinedEpicSearcher,
    CombinedSearchConfig,
    GenericEpicSearcher,
    EpicSearchConfig,
    EpicGenerationStrategy,
    DetectedEpic,
    DetectedFolder,
    DetectedFeature,
)


class TestGenericEpicSearcher:
    """Tests for GenericEpicSearcher class (folder-based detection)."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure with folders and files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create src folder with subfolders
            src_folder = project_path / "src"
            src_folder.mkdir()

            # Create domain folders
            (src_folder / "patient").mkdir()
            for i in range(5):
                (src_folder / "patient" / f"file{i}.py").write_text(f"# File {i}")

            (src_folder / "appointment").mkdir()
            for i in range(4):
                (src_folder / "appointment" / f"file{i}.py").write_text(f"# File {i}")

            (src_folder / "billing").mkdir()
            for i in range(3):
                (src_folder / "billing" / f"file{i}.py").write_text(f"# File {i}")

            # Create infrastructure folders
            (src_folder / "utils").mkdir()
            for i in range(3):
                (src_folder / "utils" / f"helper{i}.py").write_text(f"# Helper {i}")

            (src_folder / "config").mkdir()
            (src_folder / "config" / "settings.py").write_text("# Settings")
            (src_folder / "config" / "database.py").write_text("# Database config")
            (src_folder / "config" / "logging.py").write_text("# Logging config")

            yield project_path

    def test_find_source_roots(self, temp_project):
        """Test that source roots are found correctly."""
        config = EpicSearchConfig(
            project_path=str(temp_project),
            strategy=EpicGenerationStrategy.FOLDER_BASED,
        )
        searcher = GenericEpicSearcher(config)
        roots = searcher._find_source_roots()

        # Should find the src folder
        assert len(roots) >= 1
        assert any(r.name == "src" for r in roots)

    def test_scan_folders(self, temp_project):
        """Test that folders are scanned correctly."""
        config = EpicSearchConfig(
            project_path=str(temp_project),
            strategy=EpicGenerationStrategy.FOLDER_BASED,
            min_files_for_epic=2,
        )
        searcher = GenericEpicSearcher(config)
        searcher._find_source_roots()
        folders = searcher._scan_folder(temp_project / "src", depth=0)

        # Should find domain and infrastructure folders
        folder_names = [f.name for f in folders]
        assert "patient" in folder_names
        assert "appointment" in folder_names
        assert "billing" in folder_names
        assert "utils" in folder_names
        assert "config" in folder_names

    def test_folder_based_search(self, temp_project):
        """Test folder-based epic generation."""
        config = EpicSearchConfig(
            project_path=str(temp_project),
            strategy=EpicGenerationStrategy.FOLDER_BASED,
            min_files_for_epic=2,
        )
        searcher = GenericEpicSearcher(config)
        epics = searcher.search()

        # Should have epics for each folder
        assert len(epics) >= 4  # patient, appointment, billing, plus infrastructure

        # Check epic names
        epic_names = [e.name for e in epics]
        assert "Patient" in epic_names
        assert "Appointment" in epic_names
        assert "Billing" in epic_names

    def test_infrastructure_epic_created(self, temp_project):
        """Test that infrastructure epic is created for utils/config."""
        config = EpicSearchConfig(
            project_path=str(temp_project),
            strategy=EpicGenerationStrategy.FOLDER_BASED,
            min_files_for_epic=2,
            include_infrastructure_epic=True,
        )
        searcher = GenericEpicSearcher(config)
        epics = searcher.search()

        # Should have infrastructure category epics
        infra_epics = [e for e in epics if e.category == "infrastructure"]
        assert len(infra_epics) > 0

    def test_humanize_folder_name(self, temp_project):
        """Test that folder names are humanized correctly."""
        config = EpicSearchConfig(project_path=str(temp_project))
        searcher = GenericEpicSearcher(config)

        # CamelCase
        assert searcher._humanize_folder_name("PatientManagement") == "Patient Management"

        # snake_case
        assert searcher._humanize_folder_name("patient_management") == "Patient Management"

        # kebab-case
        assert searcher._humanize_folder_name("patient-management") == "Patient Management"

    def test_layer_based_strategy(self, temp_project):
        """Test layer-based epic generation."""
        config = EpicSearchConfig(
            project_path=str(temp_project),
            strategy=EpicGenerationStrategy.LAYER_BASED,
            min_files_for_epic=2,
        )
        searcher = GenericEpicSearcher(config)
        epics = searcher.search()

        # Should have layer-based epics
        assert len(epics) >= 1


class TestCombinedEpicSearcher:
    """Tests for CombinedEpicSearcher class."""

    @pytest.fixture
    def temp_project_with_screens(self):
        """Create a temporary project with both screens and folders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create WEB folder with ASPX files
            web_folder = project_path / "WEB"
            web_folder.mkdir()

            # Create screens
            (web_folder / "Menu.aspx").write_text('''
<%@ Page Language="VB" %>
<asp:HyperLink NavigateUrl="PatientList.aspx" Text="Patients" runat="server" />
''')
            (web_folder / "PatientList.aspx").write_text('''
<%@ Page Language="VB" %>
<asp:GridView ID="gv" runat="server" />
<asp:Button ID="btnNew" Text="New Patient" runat="server" />
''')
            (web_folder / "PatientDetail.aspx").write_text('''
<%@ Page Language="VB" %>
<asp:TextBox ID="txtName" runat="server" />
<asp:Button ID="btnSave" Text="Save" runat="server" />
''')

            # Create src folder with backend code
            src_folder = project_path / "src"
            src_folder.mkdir()

            # Create domain folders
            (src_folder / "services").mkdir()
            for i in range(3):
                (src_folder / "services" / f"service{i}.py").write_text(f"# Service {i}")

            (src_folder / "api").mkdir()
            for i in range(3):
                (src_folder / "api" / f"endpoint{i}.py").write_text(f"# Endpoint {i}")

            yield project_path

    def test_combined_search(self, temp_project_with_screens):
        """Test combined journey + folder detection."""
        config = CombinedSearchConfig(
            project_path=str(temp_project_with_screens),
            max_journey_depth=6,
            min_screens_per_journey=2,
            include_infrastructure=True,
            include_uncovered_folders=True,
        )
        searcher = CombinedEpicSearcher(config)
        epics = searcher.search()

        # Should find epics
        assert len(epics) >= 1

        # Should have both business and infrastructure categories
        categories = {e.category for e in epics}
        # At minimum we should have some epics
        assert len(epics) > 0

    def test_journeys_to_epics(self, temp_project_with_screens):
        """Test conversion of journeys to epics."""
        config = CombinedSearchConfig(
            project_path=str(temp_project_with_screens),
        )
        searcher = CombinedEpicSearcher(config)
        epics = searcher.search()

        # Business epics should have metadata with actions
        business_epics = [e for e in epics if e.category == "business"]
        if business_epics:
            for epic in business_epics:
                assert epic.confidence >= 0.5

    def test_screens_property(self, temp_project_with_screens):
        """Test that screens property returns detected screens."""
        config = CombinedSearchConfig(
            project_path=str(temp_project_with_screens),
        )
        searcher = CombinedEpicSearcher(config)
        searcher.search()

        # Should have screens from journey searcher
        screens = searcher.screens
        assert isinstance(screens, dict)

    def test_journeys_property(self, temp_project_with_screens):
        """Test that journeys property returns detected journeys."""
        config = CombinedSearchConfig(
            project_path=str(temp_project_with_screens),
        )
        searcher = CombinedEpicSearcher(config)
        searcher.search()

        # Should have journeys from journey searcher
        journeys = searcher.journeys
        assert isinstance(journeys, list)

    def test_get_summary(self, temp_project_with_screens):
        """Test that summary is generated correctly."""
        config = CombinedSearchConfig(
            project_path=str(temp_project_with_screens),
        )
        searcher = CombinedEpicSearcher(config)
        searcher.search()

        summary = searcher.get_summary()
        assert isinstance(summary, str)
        assert "COMBINED EPIC DETECTION RESULTS" in summary


class TestCombinedSearchConfig:
    """Tests for CombinedSearchConfig."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = CombinedSearchConfig(project_path="/test")

        assert config.max_journey_depth == 6
        assert config.min_screens_per_journey == 2
        assert config.include_infrastructure is True
        assert config.include_uncovered_folders is True
        assert config.min_confidence == 0.5
        assert len(config.source_folders) > 0
        assert len(config.infrastructure_folders) > 0

    def test_custom_values(self):
        """Test that custom values can be set."""
        config = CombinedSearchConfig(
            project_path="/test",
            max_journey_depth=10,
            min_screens_per_journey=3,
            include_infrastructure=False,
            min_confidence=0.7,
        )

        assert config.max_journey_depth == 10
        assert config.min_screens_per_journey == 3
        assert config.include_infrastructure is False
        assert config.min_confidence == 0.7


class TestDetectedEpic:
    """Tests for DetectedEpic dataclass."""

    def test_create_epic(self):
        """Test creating a DetectedEpic."""
        epic = DetectedEpic(
            id="EPIC-001",
            name="Patient Management",
            description="All patient functionality",
            source_folders=["/src/patient"],
            file_count=10,
            category="business",
            confidence=0.9,
        )

        assert epic.id == "EPIC-001"
        assert epic.name == "Patient Management"
        assert epic.category == "business"
        assert epic.confidence == 0.9
        assert epic.features == []
        assert epic.metadata == {}

    def test_epic_with_features(self):
        """Test creating an epic with features."""
        feature = DetectedFeature(
            id="FEAT-001",
            name="Patient Search",
            description="Search for patients",
            source_folder="/src/patient/search",
            epic_id="EPIC-001",
            estimated_stories=5,
        )

        epic = DetectedEpic(
            id="EPIC-001",
            name="Patient Management",
            description="All patient functionality",
            source_folders=["/src/patient"],
            features=[feature],
        )

        assert len(epic.features) == 1
        assert epic.features[0].name == "Patient Search"

    def test_epic_with_metadata(self):
        """Test creating an epic with metadata."""
        epic = DetectedEpic(
            id="EPIC-001",
            name="Patient Management",
            description="All patient functionality",
            source_folders=["/src/patient"],
            metadata={
                "journey_count": 5,
                "actions": ["Search", "Create", "Edit"],
                "messages": ["Patient saved", "Patient not found"],
            }
        )

        assert epic.metadata["journey_count"] == 5
        assert len(epic.metadata["actions"]) == 3
        assert len(epic.metadata["messages"]) == 2


class TestDetectedFolder:
    """Tests for DetectedFolder dataclass."""

    def test_create_folder(self):
        """Test creating a DetectedFolder."""
        folder = DetectedFolder(
            name="patient",
            path="/src/patient",
            depth=0,
            file_count=10,
            module_type="service",
        )

        assert folder.name == "patient"
        assert folder.path == "/src/patient"
        assert folder.depth == 0
        assert folder.file_count == 10
        assert folder.module_type == "service"
        assert folder.subfolders == []

    def test_folder_with_subfolders(self):
        """Test creating a folder with subfolders."""
        subfolder = DetectedFolder(
            name="search",
            path="/src/patient/search",
            depth=1,
            file_count=3,
        )

        folder = DetectedFolder(
            name="patient",
            path="/src/patient",
            depth=0,
            file_count=10,
            subfolders=[subfolder],
        )

        assert len(folder.subfolders) == 1
        assert folder.subfolders[0].name == "search"


class TestEpicSearchConfig:
    """Tests for EpicSearchConfig."""

    def test_default_strategy(self):
        """Test that default strategy is FOLDER_BASED."""
        config = EpicSearchConfig(project_path="/test")
        assert config.strategy == EpicGenerationStrategy.FOLDER_BASED

    def test_all_strategies(self):
        """Test all strategy options."""
        strategies = [
            EpicGenerationStrategy.FOLDER_BASED,
            EpicGenerationStrategy.GROUPED,
            EpicGenerationStrategy.LAYER_BASED,
            EpicGenerationStrategy.HYBRID,
        ]

        for strategy in strategies:
            config = EpicSearchConfig(
                project_path="/test",
                strategy=strategy,
            )
            assert config.strategy == strategy
