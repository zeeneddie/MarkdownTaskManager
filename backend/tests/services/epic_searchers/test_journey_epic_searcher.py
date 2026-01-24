"""
Tests for JourneyBasedEpicSearcher

Tests screen scanning, navigation graph building, journey tracing,
and action/message extraction.
"""

import tempfile
from pathlib import Path

import pytest

from app.services.epic_searchers import (
    JourneyBasedEpicSearcher,
    JourneySearchConfig,
    DetectedScreen,
    DetectedJourney,
)


class TestJourneyBasedEpicSearcher:
    """Tests for JourneyBasedEpicSearcher class."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create a WEB folder with ASPX files
            web_folder = project_path / "WEB"
            web_folder.mkdir()

            # Create Menu.aspx
            (web_folder / "Menu.aspx").write_text('''
<%@ Page Language="VB" %>
<html>
<body>
    <asp:HyperLink ID="lnkDossier" NavigateUrl="DossierList.aspx" Text="Dossiers" runat="server" />
    <asp:HyperLink ID="lnkSettings" NavigateUrl="Settings.aspx" Text="Settings" runat="server" />
</body>
</html>
''')

            # Create DossierList.aspx
            (web_folder / "DossierList.aspx").write_text('''
<%@ Page Language="VB" %>
<html>
<body>
    <asp:GridView ID="gvDossiers" runat="server">
    </asp:GridView>
    <asp:Button ID="btnNew" Text="Nieuw Dossier" OnClick="btnNew_Click" runat="server" />
    <asp:HyperLink ID="lnkDetail" NavigateUrl="DossierDetail.aspx" runat="server" />
</body>
</html>
''')

            # Create DossierDetail.aspx
            (web_folder / "DossierDetail.aspx").write_text('''
<%@ Page Language="VB" %>
<html>
<body>
    <asp:TextBox ID="txtName" runat="server" />
    <asp:Button ID="btnSave" Text="Opslaan" OnClick="btnSave_Click" runat="server" />
    <asp:Button ID="btnDelete" Text="Verwijderen" OnClick="btnDelete_Click" runat="server" />
    <asp:Label ID="lblMessage" Text="" runat="server" />
</body>
</html>
<script runat="server">
    Sub btnSave_Click(sender As Object, e As EventArgs)
        lblMessage.Text = "Dossier opgeslagen"
    End Sub
</script>
''')

            # Create DossierEdit.aspx
            (web_folder / "DossierEdit.aspx").write_text('''
<%@ Page Language="VB" %>
<html>
<body>
    <asp:TextBox ID="txtField1" runat="server" />
    <asp:Button ID="btnSave" Text="Wijzigingen Opslaan" PostBackUrl="DossierDetail.aspx" runat="server" />
    <asp:Button ID="btnCancel" Text="Annuleren" runat="server" />
</body>
</html>
<script runat="server">
    Sub ShowError()
        MsgBox("Verplichte velden ontbreken")
    End Sub
</script>
''')

            # Create Settings.aspx
            (web_folder / "Settings.aspx").write_text('''
<%@ Page Language="VB" %>
<html>
<body>
    <asp:TextBox ID="txtSetting1" runat="server" />
    <asp:Button ID="btnSave" Text="Save" runat="server" />
</body>
</html>
''')

            yield project_path

    def test_search_finds_screens(self, temp_project):
        """Test that search finds all screen files."""
        config = JourneySearchConfig(
            project_path=str(temp_project),
            max_journey_depth=6,
            min_screens_per_journey=2,
        )
        searcher = JourneyBasedEpicSearcher(config)
        searcher._scan_all_screens()

        # Should find 5 screens
        assert len(searcher.screens) == 5
        assert "Menu" in searcher.screens
        assert "DossierList" in searcher.screens
        assert "DossierDetail" in searcher.screens
        assert "DossierEdit" in searcher.screens
        assert "Settings" in searcher.screens

    def test_extract_navigation_targets(self, temp_project):
        """Test that navigation targets are extracted correctly."""
        config = JourneySearchConfig(project_path=str(temp_project))
        searcher = JourneyBasedEpicSearcher(config)
        searcher._scan_all_screens()

        # Menu should have 2 exit points
        menu = searcher.screens["Menu"]
        assert "DossierList" in menu.exit_points
        assert "Settings" in menu.exit_points

        # DossierList should have exit to DossierDetail
        dossier_list = searcher.screens["DossierList"]
        assert "DossierDetail" in dossier_list.exit_points

        # DossierEdit should have exit to DossierDetail (PostBackUrl)
        dossier_edit = searcher.screens["DossierEdit"]
        assert "DossierDetail" in dossier_edit.exit_points

    def test_extract_buttons(self, temp_project):
        """Test that buttons are extracted from screens."""
        config = JourneySearchConfig(project_path=str(temp_project))
        searcher = JourneyBasedEpicSearcher(config)
        searcher._scan_all_screens()

        # DossierDetail should have Save and Delete buttons
        detail = searcher.screens["DossierDetail"]
        assert "Opslaan" in detail.buttons
        assert "Verwijderen" in detail.buttons

        # DossierEdit should have buttons
        edit = searcher.screens["DossierEdit"]
        assert "Wijzigingen Opslaan" in edit.buttons
        assert "Annuleren" in edit.buttons

    def test_extract_messages(self, temp_project):
        """Test that messages are extracted from screens."""
        config = JourneySearchConfig(project_path=str(temp_project))
        searcher = JourneyBasedEpicSearcher(config)
        searcher._scan_all_screens()

        # DossierDetail should have a message
        detail = searcher.screens["DossierDetail"]
        assert "Dossier opgeslagen" in detail.messages

        # DossierEdit should have an error message
        edit = searcher.screens["DossierEdit"]
        assert "Verplichte velden ontbreken" in edit.messages

    def test_detect_screen_type(self, temp_project):
        """Test that screen types are detected correctly."""
        config = JourneySearchConfig(project_path=str(temp_project))
        searcher = JourneyBasedEpicSearcher(config)
        searcher._scan_all_screens()

        # Menu should be detected as menu
        assert searcher.screens["Menu"].screen_type == "menu"

        # DossierList should be detected as list
        assert searcher.screens["DossierList"].screen_type == "list"

        # DossierDetail should be detected as detail
        assert searcher.screens["DossierDetail"].screen_type == "detail"

        # DossierEdit should be detected as edit
        assert searcher.screens["DossierEdit"].screen_type == "edit"

    def test_build_navigation_graph(self, temp_project):
        """Test that navigation graph is built correctly."""
        config = JourneySearchConfig(project_path=str(temp_project))
        searcher = JourneyBasedEpicSearcher(config)
        searcher._scan_all_screens()
        searcher._build_navigation_graph()

        # Menu should have 2 outgoing edges
        assert len(searcher.navigation_graph.get("Menu", set())) == 2

        # DossierList should have entry from Menu
        assert "Menu" in searcher.screens["DossierList"].entry_points

    def test_find_entry_points(self, temp_project):
        """Test that entry points are found correctly."""
        config = JourneySearchConfig(project_path=str(temp_project))
        searcher = JourneyBasedEpicSearcher(config)
        searcher._scan_all_screens()
        searcher._build_navigation_graph()

        entry_points = searcher._find_entry_points()

        # Menu should be an entry point
        assert "Menu" in entry_points

    def test_trace_all_paths(self, temp_project):
        """Test that paths are traced correctly."""
        config = JourneySearchConfig(project_path=str(temp_project))
        searcher = JourneyBasedEpicSearcher(config)
        searcher._scan_all_screens()
        searcher._build_navigation_graph()

        paths = searcher._trace_all_paths("Menu", max_depth=5)

        # Should find at least one path
        assert len(paths) > 0

        # Check for Menu -> DossierList path
        assert any(
            path[0] == "Menu" and "DossierList" in path
            for path in paths
        )

    def test_full_search(self, temp_project):
        """Test the complete search process."""
        config = JourneySearchConfig(
            project_path=str(temp_project),
            max_journey_depth=6,
            min_screens_per_journey=2,
        )
        searcher = JourneyBasedEpicSearcher(config)
        journeys = searcher.search()

        # Should find at least one journey
        assert len(journeys) > 0

        # Each journey should have required fields
        for journey in journeys:
            assert journey.id
            assert journey.name
            assert len(journey.screen_path) >= 2

    def test_humanize_name(self, temp_project):
        """Test that screen names are humanized correctly."""
        config = JourneySearchConfig(project_path=str(temp_project))
        searcher = JourneyBasedEpicSearcher(config)

        # CamelCase
        assert searcher._humanize_name("DossierDetail") == "Dossier Detail"

        # With prefix
        assert searcher._humanize_name("frmPatientList") == "Patient List"

        # With suffix
        assert searcher._humanize_name("DossierForm") == "Dossier"

        # snake_case
        assert searcher._humanize_name("patient_detail") == "Patient Detail"


class TestJourneySearchConfig:
    """Tests for JourneySearchConfig."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = JourneySearchConfig(project_path="/test")

        assert config.max_journey_depth == 6
        assert config.min_screens_per_journey == 2
        assert config.scan_aspx is True
        assert config.scan_vb is True
        assert config.scan_razor is True
        assert config.scan_jsx is True
        assert config.scan_vue is True
        assert config.scan_html is True

    def test_custom_values(self):
        """Test that custom values can be set."""
        config = JourneySearchConfig(
            project_path="/test",
            max_journey_depth=10,
            min_screens_per_journey=3,
            scan_jsx=False,
        )

        assert config.max_journey_depth == 10
        assert config.min_screens_per_journey == 3
        assert config.scan_jsx is False


class TestDetectedScreen:
    """Tests for DetectedScreen dataclass."""

    def test_create_screen(self):
        """Test creating a DetectedScreen."""
        screen = DetectedScreen(
            id="TestScreen",
            name="Test Screen",
            file_path="/path/to/screen.aspx",
            screen_type="form",
        )

        assert screen.id == "TestScreen"
        assert screen.name == "Test Screen"
        assert screen.screen_type == "form"
        assert screen.entry_points == []
        assert screen.exit_points == []
        assert screen.buttons == []
        assert screen.messages == []


class TestDetectedJourney:
    """Tests for DetectedJourney dataclass."""

    def test_create_journey(self):
        """Test creating a DetectedJourney."""
        journey = DetectedJourney(
            id="JOURNEY-001",
            name="Test Journey",
            description="A test journey",
            start_screen="Menu",
            screen_path=["Menu", "List", "Detail"],
        )

        assert journey.id == "JOURNEY-001"
        assert journey.name == "Test Journey"
        assert len(journey.screen_path) == 3
        assert journey.persona == "User"
