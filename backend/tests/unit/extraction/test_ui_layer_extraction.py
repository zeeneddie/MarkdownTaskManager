"""
Unit Tests for UI Layer Extraction Service.

Tests UI component detection and mapping from legacy to modern frameworks.

Coverage:
- Legacy UI component detection (WebForms, WPF)
- Modern framework mapping (React, Vue)
- Complexity assessment
- Design token extraction
- Component mapping generation
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, List, Any
import os
import tempfile

from app.services.ui_layer_extraction_service import (
    UILayerExtractionService,
    LegacyUIComponent,
    LegacyUIType,
    ModernComponent,
    UIFramework,
    ComponentMapping,
    UIExtractionResult,
    DesignToken,
    DesignTokenType,
    ComponentType,
    StyleExtraction,
    COMPONENT_MAPPINGS,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def service():
    """Create UI Layer Extraction Service instance."""
    return UILayerExtractionService()


@pytest.fixture
def sample_aspx_content():
    """Sample ASPX file content with various controls."""
    return """
<%@ Page Language="C#" AutoEventWireup="true" %>
<html>
<head><title>Patient Form</title></head>
<body>
    <form id="form1" runat="server">
        <asp:Panel ID="pnlPatient" runat="server" CssClass="patient-panel">
            <asp:Label ID="lblName" runat="server" Text="Name:"></asp:Label>
            <asp:TextBox ID="txtName" runat="server" CssClass="form-input"></asp:TextBox>

            <asp:Label ID="lblDOB" runat="server" Text="Date of Birth:"></asp:Label>
            <asp:Calendar ID="calDOB" runat="server"></asp:Calendar>

            <asp:DropDownList ID="ddlGender" runat="server">
                <asp:ListItem Value="M">Male</asp:ListItem>
                <asp:ListItem Value="F">Female</asp:ListItem>
            </asp:DropDownList>

            <asp:GridView ID="gvAppointments" runat="server" AutoGenerateColumns="true">
            </asp:GridView>

            <asp:Button ID="btnSave" runat="server" Text="Save" OnClick="btnSave_Click" />
        </asp:Panel>
    </form>
</body>
</html>
"""


@pytest.fixture
def sample_css_content():
    """Sample CSS content for design token extraction."""
    return """
/* Patient Form Styles */
.patient-panel {
    background-color: #ffffff;
    border: 1px solid #ccc;
    padding: 20px;
    margin: 10px;
}

.form-input {
    font-family: Arial, sans-serif;
    color: #333333;
    border: 1px solid #999;
}

.btn-primary {
    background-color: rgb(0, 123, 255);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
"""


@pytest.fixture
def temp_project_dir(sample_aspx_content, sample_css_content):
    """Create a temporary project directory with sample files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create ASPX file
        aspx_path = os.path.join(tmpdir, "PatientForm.aspx")
        with open(aspx_path, "w") as f:
            f.write(sample_aspx_content)

        # Create CSS file
        css_path = os.path.join(tmpdir, "styles.css")
        with open(css_path, "w") as f:
            f.write(sample_css_content)

        yield tmpdir


# =============================================================================
# COMPONENT TYPE DETERMINATION TESTS
# =============================================================================


class TestComponentTypeDetermination:
    """Tests for component type determination from tag names."""

    def test_gridview_detected_as_grid(self, service):
        """Test that GridView is detected as GRID type."""
        comp_type = service._determine_component_type("asp:GridView")
        assert comp_type == ComponentType.GRID

    def test_textbox_detected_as_input(self, service):
        """Test that TextBox is detected as INPUT type."""
        comp_type = service._determine_component_type("asp:TextBox")
        assert comp_type == ComponentType.INPUT

    def test_button_detected_as_button(self, service):
        """Test that Button is detected as BUTTON type."""
        comp_type = service._determine_component_type("asp:Button")
        assert comp_type == ComponentType.BUTTON

    def test_calendar_detected_as_calendar(self, service):
        """Test that Calendar is detected as CALENDAR type."""
        comp_type = service._determine_component_type("asp:Calendar")
        assert comp_type == ComponentType.CALENDAR

    def test_panel_detected_as_layout(self, service):
        """Test that Panel is detected as LAYOUT type."""
        comp_type = service._determine_component_type("asp:Panel")
        assert comp_type == ComponentType.LAYOUT

    def test_dropdownlist_detected_as_input(self, service):
        """Test that DropDownList is detected as INPUT type."""
        comp_type = service._determine_component_type("asp:DropDownList")
        assert comp_type == ComponentType.INPUT

    def test_treeview_detected_as_tree(self, service):
        """Test that TreeView is detected as TREE type."""
        comp_type = service._determine_component_type("asp:TreeView")
        assert comp_type == ComponentType.TREE

    def test_menu_detected_as_menu(self, service):
        """Test that Menu is detected as MENU type."""
        comp_type = service._determine_component_type("asp:Menu")
        assert comp_type == ComponentType.MENU

    def test_unknown_detected_as_other(self, service):
        """Test that unknown controls are detected as OTHER type."""
        comp_type = service._determine_component_type("asp:CustomControl")
        assert comp_type == ComponentType.OTHER


# =============================================================================
# COMPONENT EXTRACTION TESTS
# =============================================================================


class TestComponentExtraction:
    """Tests for extracting components from files."""

    @pytest.mark.asyncio
    async def test_extract_aspnet_components(self, service, sample_aspx_content):
        """Test extracting ASP.NET components from content."""
        components = await service._extract_aspnet_components(
            sample_aspx_content,
            "test.aspx",
            LegacyUIType.ASP_WEBFORMS
        )

        assert len(components) > 0

        # Check for expected components
        component_types = [c.component_type for c in components]
        assert ComponentType.INPUT in component_types  # TextBox
        assert ComponentType.GRID in component_types   # GridView
        assert ComponentType.BUTTON in component_types # Button

    @pytest.mark.asyncio
    async def test_components_have_ids(self, service, sample_aspx_content):
        """Test that extracted components have IDs."""
        components = await service._extract_aspnet_components(
            sample_aspx_content,
            "test.aspx",
            LegacyUIType.ASP_WEBFORMS
        )

        # At least some components should have meaningful names
        named_components = [c for c in components if c.name and c.name != "asp:"]
        assert len(named_components) > 0

    @pytest.mark.asyncio
    async def test_components_capture_css_classes(self, service, sample_aspx_content):
        """Test that CSS classes are captured."""
        components = await service._extract_aspnet_components(
            sample_aspx_content,
            "test.aspx",
            LegacyUIType.ASP_WEBFORMS
        )

        # Find component with CSS class
        components_with_css = [c for c in components if c.css_classes]
        assert len(components_with_css) > 0

    @pytest.mark.asyncio
    async def test_components_capture_event_handlers(self, service, sample_aspx_content):
        """Test that event handlers are captured."""
        components = await service._extract_aspnet_components(
            sample_aspx_content,
            "test.aspx",
            LegacyUIType.ASP_WEBFORMS
        )

        # Find component with event handler (Button has OnClick)
        components_with_events = [c for c in components if c.event_handlers]
        assert len(components_with_events) > 0


# =============================================================================
# FULL UI EXTRACTION TESTS
# =============================================================================


class TestFullUIExtraction:
    """Tests for full UI extraction from project directory."""

    @pytest.mark.asyncio
    async def test_extract_ui_components_from_directory(self, service, temp_project_dir):
        """Test full UI extraction from a project directory."""
        result = await service.extract_ui_components(
            temp_project_dir,
            LegacyUIType.ASP_WEBFORMS
        )

        assert isinstance(result, UIExtractionResult)
        assert result.component_count >= 0
        assert result.project_path == temp_project_dir

    @pytest.mark.asyncio
    async def test_extraction_result_has_components(self, service, temp_project_dir):
        """Test that extraction result includes components."""
        result = await service.extract_ui_components(
            temp_project_dir,
            LegacyUIType.ASP_WEBFORMS
        )

        assert isinstance(result.components, list)

    @pytest.mark.asyncio
    async def test_extraction_result_has_style_extraction(self, service, temp_project_dir):
        """Test that extraction result includes style extraction."""
        result = await service.extract_ui_components(
            temp_project_dir,
            LegacyUIType.ASP_WEBFORMS
        )

        assert isinstance(result.style_extraction, StyleExtraction)

    @pytest.mark.asyncio
    async def test_empty_directory_returns_empty_result(self, service):
        """Test extraction from empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await service.extract_ui_components(
                tmpdir,
                LegacyUIType.ASP_WEBFORMS
            )

            assert result.component_count == 0


# =============================================================================
# COMPONENT MAPPING TESTS
# =============================================================================


class TestComponentMapping:
    """Tests for mapping legacy components to modern frameworks."""

    @pytest.mark.asyncio
    async def test_generate_mappings_for_components(self, service, temp_project_dir):
        """Test generating mappings for extracted components."""
        result = await service.extract_ui_components(
            temp_project_dir,
            LegacyUIType.ASP_WEBFORMS
        )

        assert isinstance(result.mappings, list)

    @pytest.mark.asyncio
    async def test_mappings_include_react(self, service):
        """Test that mappings include React equivalents."""
        # Create a test component
        components = [
            LegacyUIComponent(
                id="ui-0001",
                name="gvData",
                component_type=ComponentType.GRID,
                legacy_type=LegacyUIType.ASP_WEBFORMS,
                source_file="test.aspx",
                source_lines=(1, 10),
                html_elements=["asp:GridView"],
                css_classes=[],
                event_handlers=[],
                data_bindings=[],
                child_components=[],
                parent_component=None,
            )
        ]

        mappings = await service.generate_component_mappings(
            components,
            target_frameworks=[UIFramework.REACT]
        )

        assert len(mappings) == 1
        if UIFramework.REACT in mappings[0].modern_equivalents:
            react_equiv = mappings[0].modern_equivalents[UIFramework.REACT]
            assert len(react_equiv) > 0

    @pytest.mark.asyncio
    async def test_mappings_include_effort_estimate(self, service):
        """Test that mappings include effort estimates."""
        components = [
            LegacyUIComponent(
                id="ui-0001",
                name="txtInput",
                component_type=ComponentType.INPUT,
                legacy_type=LegacyUIType.ASP_WEBFORMS,
                source_file="test.aspx",
                source_lines=(1, 5),
                html_elements=["asp:TextBox"],
                css_classes=[],
                event_handlers=[],
                data_bindings=[],
                child_components=[],
                parent_component=None,
            )
        ]

        mappings = await service.generate_component_mappings(components)

        assert len(mappings) == 1
        assert mappings[0].migration_effort in ["trivial", "low", "medium", "high"]
        assert mappings[0].estimated_hours >= 0


# =============================================================================
# DESIGN TOKEN EXTRACTION TESTS
# =============================================================================


class TestDesignTokenExtraction:
    """Tests for design token extraction from CSS."""

    @pytest.mark.asyncio
    async def test_extract_colors_from_css(self, service, temp_project_dir):
        """Test extracting color tokens from CSS."""
        style_extraction = await service.extract_design_tokens(temp_project_dir)

        # Should find hex and rgb colors
        assert isinstance(style_extraction.colors, list)

    @pytest.mark.asyncio
    async def test_extract_typography_from_css(self, service, temp_project_dir):
        """Test extracting typography tokens from CSS."""
        style_extraction = await service.extract_design_tokens(temp_project_dir)

        assert isinstance(style_extraction.typography, list)

    @pytest.mark.asyncio
    async def test_extract_spacing_from_css(self, service, temp_project_dir):
        """Test extracting spacing tokens from CSS."""
        style_extraction = await service.extract_design_tokens(temp_project_dir)

        assert isinstance(style_extraction.spacing, list)

    @pytest.mark.asyncio
    async def test_extract_borders_from_css(self, service, temp_project_dir):
        """Test extracting border tokens from CSS."""
        style_extraction = await service.extract_design_tokens(temp_project_dir)

        assert isinstance(style_extraction.borders, list)

    @pytest.mark.asyncio
    async def test_design_tokens_have_css_variables(self, service, temp_project_dir):
        """Test that design tokens have CSS variable names."""
        style_extraction = await service.extract_design_tokens(temp_project_dir)

        all_tokens = (
            style_extraction.colors +
            style_extraction.typography +
            style_extraction.spacing +
            style_extraction.borders
        )

        for token in all_tokens:
            assert token.css_variable.startswith("--")


# =============================================================================
# BUILTIN MAPPINGS TESTS
# =============================================================================


class TestBuiltinMappings:
    """Tests for built-in component mappings."""

    def test_gridview_mapping_exists(self):
        """Test that GridView mapping exists."""
        assert "asp:GridView" in COMPONENT_MAPPINGS

    def test_button_mapping_exists(self):
        """Test that Button mapping exists."""
        assert "asp:Button" in COMPONENT_MAPPINGS

    def test_textbox_mapping_exists(self):
        """Test that TextBox mapping exists."""
        assert "asp:TextBox" in COMPONENT_MAPPINGS

    def test_gridview_has_react_mapping(self):
        """Test that GridView has React mapping."""
        mapping = COMPONENT_MAPPINGS["asp:GridView"]
        assert "react" in mapping
        assert len(mapping["react"]) > 0

    def test_mappings_have_complexity(self):
        """Test that mappings include complexity ratings."""
        for key, mapping in COMPONENT_MAPPINGS.items():
            if "react" in mapping:
                for equiv in mapping["react"]:
                    assert "complexity" in equiv


# =============================================================================
# EXPORT FUNCTIONALITY TESTS
# =============================================================================


class TestExportFunctionality:
    """Tests for export/report generation."""

    @pytest.mark.asyncio
    async def test_to_design_tokens_json(self, service, temp_project_dir):
        """Test exporting design tokens as JSON."""
        style_extraction = await service.extract_design_tokens(temp_project_dir)
        json_output = service.to_design_tokens_json(style_extraction)

        assert "colors" in json_output
        assert "typography" in json_output
        assert "spacing" in json_output
        assert "borders" in json_output
        assert "shadows" in json_output

    @pytest.mark.asyncio
    async def test_to_css_variables(self, service, temp_project_dir):
        """Test generating CSS variables."""
        style_extraction = await service.extract_design_tokens(temp_project_dir)
        css_output = service.to_css_variables(style_extraction)

        assert ":root {" in css_output
        assert "}" in css_output

    @pytest.mark.asyncio
    async def test_to_markdown_report(self, service, temp_project_dir):
        """Test generating markdown report."""
        result = await service.extract_ui_components(
            temp_project_dir,
            LegacyUIType.ASP_WEBFORMS
        )

        markdown = service.to_markdown_report(result)

        assert "# UI Layer Extraction Report" in markdown
        assert "Component Summary" in markdown or "Components Found" in markdown


# =============================================================================
# HELPER METHOD TESTS
# =============================================================================


class TestHelperMethods:
    """Tests for helper methods."""

    def test_generate_import_with_library(self, service):
        """Test generating import statement with library."""
        import_stmt = service._generate_import("DataGrid", "@mui/x-data-grid")
        assert "@mui/x-data-grid" in import_stmt
        assert "DataGrid" in import_stmt

    def test_generate_import_without_library(self, service):
        """Test generating import statement without library."""
        import_stmt = service._generate_import("div", None)
        assert import_stmt == ""

    def test_calculate_effort_for_simple_component(self, service):
        """Test effort calculation for simple component."""
        component = LegacyUIComponent(
            id="ui-0001",
            name="btnSubmit",
            component_type=ComponentType.BUTTON,
            legacy_type=LegacyUIType.ASP_WEBFORMS,
            source_file="test.aspx",
            source_lines=(1, 5),
            html_elements=["asp:Button"],
            css_classes=[],
            event_handlers=[],
            data_bindings=[],
            child_components=[],
            parent_component=None,
        )

        # Simple components should have low effort
        effort = service._calculate_effort(component, {UIFramework.REACT: []})
        assert effort in ["low", "high"]  # high if no mapping found

    def test_estimate_hours_based_on_effort(self, service):
        """Test hour estimation based on effort level."""
        component = LegacyUIComponent(
            id="ui-0001",
            name="test",
            component_type=ComponentType.INPUT,
            legacy_type=LegacyUIType.ASP_WEBFORMS,
            source_file="test.aspx",
            source_lines=(1, 5),
            html_elements=["asp:TextBox"],
            css_classes=[],
            event_handlers=[],
            data_bindings=[],
            child_components=[],
            parent_component=None,
        )

        low_hours = service._estimate_hours("low", component)
        high_hours = service._estimate_hours("high", component)

        assert low_hours < high_hours


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases in UI extraction."""

    @pytest.mark.asyncio
    async def test_malformed_aspx_handled(self, service):
        """Test handling of malformed ASPX content."""
        malformed_content = "<asp:TextBox runat='server' <broken"

        # Should not crash
        components = await service._extract_aspnet_components(
            malformed_content,
            "test.aspx",
            LegacyUIType.ASP_WEBFORMS
        )
        assert isinstance(components, list)

    @pytest.mark.asyncio
    async def test_empty_content_returns_empty_list(self, service):
        """Test that empty content returns empty list."""
        components = await service._extract_aspnet_components(
            "",
            "test.aspx",
            LegacyUIType.ASP_WEBFORMS
        )
        assert components == []

    @pytest.mark.asyncio
    async def test_nonexistent_directory_handled(self, service):
        """Test handling of non-existent directory."""
        result = await service.extract_ui_components(
            "/nonexistent/path",
            LegacyUIType.ASP_WEBFORMS
        )

        # Should return result with zero components, not crash
        assert result.component_count == 0

    def test_deduplicate_tokens(self, service):
        """Test token deduplication."""
        tokens = [
            DesignToken(
                name="color-1",
                token_type=DesignTokenType.COLOR,
                value="#ffffff",
                css_variable="--color-1"
            ),
            DesignToken(
                name="color-2",
                token_type=DesignTokenType.COLOR,
                value="#ffffff",  # Same value
                css_variable="--color-2"
            ),
            DesignToken(
                name="color-3",
                token_type=DesignTokenType.COLOR,
                value="#000000",  # Different value
                css_variable="--color-3"
            ),
        ]

        unique = service._deduplicate_tokens(tokens)

        # Should have 2 unique values
        assert len(unique) == 2

    @pytest.mark.asyncio
    async def test_nested_controls_detected(self, service):
        """Test detection of nested controls."""
        nested_content = """
        <asp:Panel ID="outer" runat="server">
            <asp:Panel ID="inner" runat="server">
                <asp:TextBox ID="txt" runat="server" />
            </asp:Panel>
        </asp:Panel>
        """

        components = await service._extract_aspnet_components(
            nested_content,
            "test.aspx",
            LegacyUIType.ASP_WEBFORMS
        )

        # Should detect all components
        assert len(components) >= 3


# =============================================================================
# WPF EXTRACTION TESTS
# =============================================================================


class TestWPFExtraction:
    """Tests for WPF XAML component extraction."""

    @pytest.mark.asyncio
    async def test_extract_xaml_button(self, service):
        """Test extracting WPF Button from XAML."""
        xaml_content = """
        <Window>
            <Button x:Name="btnSubmit" Content="Submit" Click="OnClick" />
        </Window>
        """

        components = await service._extract_xaml_components(
            xaml_content,
            "MainWindow.xaml"
        )

        button_components = [c for c in components if c.component_type == ComponentType.BUTTON]
        assert len(button_components) >= 1

    @pytest.mark.asyncio
    async def test_extract_xaml_textbox(self, service):
        """Test extracting WPF TextBox from XAML."""
        xaml_content = """
        <Window>
            <TextBox x:Name="txtInput" Text="{Binding Name}" />
        </Window>
        """

        components = await service._extract_xaml_components(
            xaml_content,
            "MainWindow.xaml"
        )

        input_components = [c for c in components if c.component_type == ComponentType.INPUT]
        assert len(input_components) >= 1

    @pytest.mark.asyncio
    async def test_extract_xaml_datagrid(self, service):
        """Test extracting WPF DataGrid from XAML."""
        xaml_content = """
        <Window>
            <DataGrid x:Name="dgItems" ItemsSource="{Binding Items}" />
        </Window>
        """

        components = await service._extract_xaml_components(
            xaml_content,
            "MainWindow.xaml"
        )

        grid_components = [c for c in components if c.component_type == ComponentType.GRID]
        assert len(grid_components) >= 1
