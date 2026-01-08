# backend/tests/services/week111/test_aspx_extractor.py
"""
Tests for ASPX/ASCX Business Rule Extractor.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline
"""

import pytest
from typing import List

from app.services.static_analysis.aspx_extractor import ASPXExtractor
from app.services.static_analysis.extraction_models import (
    BusinessRule,
    RuleType,
    Language,
    ExtractionTier,
)


@pytest.fixture
def extractor():
    """Create extractor instance."""
    return ASPXExtractor(
        extraction_tier=ExtractionTier.FREE,
        project_id=1,
    )


class TestASPXExtractorBasics:
    """Test basic extractor functionality."""

    def test_supported_extensions(self, extractor):
        """Test supported file extensions."""
        extensions = extractor.get_supported_extensions()
        assert '.aspx' in extensions
        assert '.ascx' in extensions
        assert '.master' in extensions

    def test_language(self, extractor):
        """Test language identification."""
        assert extractor.get_language() == Language.ASPX

    def test_rule_patterns_exist(self, extractor):
        """Test that rule patterns are defined."""
        patterns = extractor.get_rule_patterns()
        assert RuleType.VALIDATION in patterns
        assert RuleType.DATA_ACCESS in patterns
        assert RuleType.NAVIGATION in patterns
        assert RuleType.WORKFLOW in patterns


class TestLanguageDetection:
    """Test code language detection from page directives."""

    def test_detect_vb_language(self, extractor):
        """Test VB.NET language detection."""
        source = '<%@ Page Language="VB" AutoEventWireup="false" %>'
        lang = extractor._detect_code_language(source)
        assert lang == 'VB'

    def test_detect_csharp_language(self, extractor):
        """Test C# language detection."""
        source = '<%@ Page Language="C#" AutoEventWireup="true" %>'
        lang = extractor._detect_code_language(source)
        assert lang == 'C#'

    def test_detect_control_language(self, extractor):
        """Test language detection from Control directive."""
        source = '<%@ Control Language="VB" ClassName="UserControl1" %>'
        lang = extractor._detect_code_language(source)
        assert lang == 'VB'

    def test_default_to_vb(self, extractor):
        """Test default to VB when no directive found."""
        source = '<html><body>No directive here</body></html>'
        lang = extractor._detect_code_language(source)
        assert lang == 'VB'


class TestValidationExtraction:
    """Test validation control extraction."""

    @pytest.mark.asyncio
    async def test_required_field_validator(self, extractor):
        """Test RequiredFieldValidator extraction."""
        source = '''<%@ Page Language="VB" %>
<asp:TextBox ID="txtName" runat="server" />
<asp:RequiredFieldValidator ID="rfvName" runat="server"
    ControlToValidate="txtName"
    ErrorMessage="Name is required" />
'''
        result = await extractor.extract_from_file("test.aspx", source)

        validation_rules = [r for r in result.business_rules if r.rule_type == RuleType.VALIDATION]
        assert len(validation_rules) >= 1

        rule = validation_rules[0]
        assert 'txtName' in rule.variables_involved or 'txtName' in rule.condition
        assert rule.confidence >= 0.85

    @pytest.mark.asyncio
    async def test_range_validator(self, extractor):
        """Test RangeValidator extraction."""
        source = '''<%@ Page Language="VB" %>
<asp:TextBox ID="txtAge" runat="server" />
<asp:RangeValidator ID="rvAge" runat="server"
    ControlToValidate="txtAge"
    MinimumValue="0"
    MaximumValue="120"
    Type="Integer"
    ErrorMessage="Age must be between 0 and 120" />
'''
        result = await extractor.extract_from_file("test.aspx", source)

        validation_rules = [r for r in result.business_rules if r.rule_type == RuleType.VALIDATION]
        assert len(validation_rules) >= 1

        rule = validation_rules[0]
        assert '0' in rule.condition or '120' in rule.condition

    @pytest.mark.asyncio
    async def test_regex_validator(self, extractor):
        """Test RegularExpressionValidator extraction."""
        source = '''<%@ Page Language="VB" %>
<asp:TextBox ID="txtEmail" runat="server" />
<asp:RegularExpressionValidator ID="revEmail" runat="server"
    ControlToValidate="txtEmail"
    ValidationExpression="^\w+@\w+\.\w+$"
    ErrorMessage="Invalid email format" />
'''
        result = await extractor.extract_from_file("test.aspx", source)

        validation_rules = [r for r in result.business_rules if r.rule_type == RuleType.VALIDATION]
        assert len(validation_rules) >= 1
        assert 'pattern' in validation_rules[0].condition.lower() or 'regex' in validation_rules[0].condition.lower() or '@' in validation_rules[0].condition

    @pytest.mark.asyncio
    async def test_compare_validator(self, extractor):
        """Test CompareValidator extraction."""
        source = '''<%@ Page Language="VB" %>
<asp:TextBox ID="txtPassword" runat="server" TextMode="Password" />
<asp:TextBox ID="txtConfirm" runat="server" TextMode="Password" />
<asp:CompareValidator ID="cvPassword" runat="server"
    ControlToValidate="txtConfirm"
    ControlToCompare="txtPassword"
    ErrorMessage="Passwords must match" />
'''
        result = await extractor.extract_from_file("test.aspx", source)

        validation_rules = [r for r in result.business_rules if r.rule_type == RuleType.VALIDATION]
        assert len(validation_rules) >= 1


class TestDataBindingExtraction:
    """Test data binding expression extraction."""

    @pytest.mark.asyncio
    async def test_eval_binding(self, extractor):
        """Test Eval() data binding."""
        source = '''<%@ Page Language="VB" %>
<asp:Label ID="lblStatus" runat="server"
    Text='<%# Eval("Status") %>' />
'''
        result = await extractor.extract_from_file("test.aspx", source)
        # Simple Eval bindings are skipped, but conditional ones are captured
        assert result is not None

    @pytest.mark.asyncio
    async def test_conditional_binding(self, extractor):
        """Test conditional data binding expression."""
        source = '''<%@ Page Language="VB" %>
<asp:Label ID="lblStatus" runat="server"
    Text='<%# If(Eval("IsActive"), "Active", "Inactive") %>' />
'''
        result = await extractor.extract_from_file("test.aspx", source)

        # Should detect as branching due to conditional
        branching_rules = [r for r in result.business_rules if r.rule_type == RuleType.BRANCHING]
        assert len(branching_rules) >= 1

    @pytest.mark.asyncio
    async def test_calculation_binding(self, extractor):
        """Test calculation in data binding."""
        source = '''<%@ Page Language="VB" %>
<asp:Label ID="lblTotal" runat="server"
    Text='<%# Convert.ToDecimal(Eval("Price")) * Convert.ToDecimal(Eval("Quantity")) %>' />
'''
        result = await extractor.extract_from_file("test.aspx", source)

        calc_rules = [r for r in result.business_rules if r.rule_type == RuleType.CALCULATION]
        assert len(calc_rules) >= 1


class TestInlineCodeExtraction:
    """Test inline code block extraction."""

    @pytest.mark.asyncio
    async def test_vb_if_statement(self, extractor):
        """Test VB.NET If-Then in inline code."""
        source = '''<%@ Page Language="VB" %>
<% If User.IsInRole("Admin") Then %>
    <div>Admin Panel</div>
<% End If %>
'''
        result = await extractor.extract_from_file("test.aspx", source)

        branching_rules = [r for r in result.business_rules if r.rule_type == RuleType.BRANCHING]
        assert len(branching_rules) >= 1

    @pytest.mark.asyncio
    async def test_csharp_if_statement(self, extractor):
        """Test C# if statement in inline code."""
        source = '''<%@ Page Language="C#" %>
<% if (User.IsInRole("Admin")) { %>
    <div>Admin Panel</div>
<% } %>
'''
        result = await extractor.extract_from_file("test.aspx", source)

        branching_rules = [r for r in result.business_rules if r.rule_type == RuleType.BRANCHING]
        assert len(branching_rules) >= 1

    @pytest.mark.asyncio
    async def test_response_redirect(self, extractor):
        """Test Response.Redirect detection."""
        source = '''<%@ Page Language="VB" %>
<%
If Not User.Identity.IsAuthenticated Then
    Response.Redirect("Login.aspx")
End If
%>
'''
        result = await extractor.extract_from_file("test.aspx", source)

        nav_rules = [r for r in result.business_rules if r.rule_type == RuleType.NAVIGATION]
        assert len(nav_rules) >= 1


class TestEventHandlerExtraction:
    """Test event handler extraction."""

    @pytest.mark.asyncio
    async def test_button_click_handler(self, extractor):
        """Test OnClick event handler extraction."""
        source = '''<%@ Page Language="VB" %>
<asp:Button ID="btnSubmit" runat="server"
    Text="Submit"
    OnClick="btnSubmit_Click" />
'''
        result = await extractor.extract_from_file("test.aspx", source)

        workflow_rules = [r for r in result.business_rules if r.rule_type == RuleType.WORKFLOW]
        assert len(workflow_rules) >= 1

        rule = workflow_rules[0]
        assert 'btnSubmit_Click' in rule.action
        assert 'Click' in rule.condition

    @pytest.mark.asyncio
    async def test_gridview_row_command(self, extractor):
        """Test OnRowCommand event handler."""
        source = '''<%@ Page Language="VB" %>
<asp:GridView ID="gvItems" runat="server"
    OnRowCommand="gvItems_RowCommand"
    OnRowDataBound="gvItems_RowDataBound">
</asp:GridView>
'''
        result = await extractor.extract_from_file("test.aspx", source)

        workflow_rules = [r for r in result.business_rules if r.rule_type == RuleType.WORKFLOW]
        assert len(workflow_rules) >= 2  # RowCommand and RowDataBound


class TestConditionalVisibility:
    """Test conditional visibility extraction."""

    @pytest.mark.asyncio
    async def test_visible_binding(self, extractor):
        """Test Visible attribute with data binding."""
        source = '''<%@ Page Language="VB" %>
<asp:Panel ID="pnlAdmin" runat="server"
    Visible='<%# User.IsInRole("Admin") %>'>
    <h2>Admin Controls</h2>
</asp:Panel>
'''
        result = await extractor.extract_from_file("test.aspx", source)

        branching_rules = [r for r in result.business_rules if r.rule_type == RuleType.BRANCHING]
        assert len(branching_rules) >= 1

        rule = branching_rules[0]
        assert 'pnlAdmin' in rule.action or 'Show' in rule.action

    @pytest.mark.asyncio
    async def test_enabled_binding(self, extractor):
        """Test Enabled attribute with data binding."""
        source = '''<%@ Page Language="VB" %>
<asp:Button ID="btnEdit" runat="server"
    Enabled='<%# Eval("CanEdit") %>'
    Text="Edit" />
'''
        result = await extractor.extract_from_file("test.aspx", source)
        # Enabled bindings might be captured
        assert result is not None


class TestSymbolExtraction:
    """Test code symbol extraction."""

    @pytest.mark.asyncio
    async def test_page_symbol(self, extractor):
        """Test page directive as symbol."""
        source = '''<%@ Page Language="VB" Inherits="MyApp.WebPages.CustomerList" %>
<html><body></body></html>
'''
        result = await extractor.extract_from_file("CustomerList.aspx", source)

        # Should extract page as symbol
        page_symbols = [s for s in result.code_symbols if s.symbol_type == 'page']
        assert len(page_symbols) >= 1

    @pytest.mark.asyncio
    async def test_control_symbols(self, extractor):
        """Test server controls as symbols."""
        source = '''<%@ Page Language="VB" %>
<asp:TextBox ID="txtUsername" runat="server" />
<asp:Button ID="btnLogin" runat="server" Text="Login" />
<asp:Label ID="lblMessage" runat="server" />
'''
        result = await extractor.extract_from_file("test.aspx", source)

        # Should extract controls as symbols
        control_symbols = [s for s in result.code_symbols if s.symbol_type.startswith('asp:')]
        assert len(control_symbols) >= 3


class TestHCICRSPatterns:
    """Test HCI-CRS specific patterns (WebForms migration)."""

    @pytest.mark.asyncio
    async def test_dutch_validation_message(self, extractor):
        """Test Dutch error messages in validators."""
        source = '''<%@ Page Language="VB" %>
<asp:RequiredFieldValidator ID="rfvKlant" runat="server"
    ControlToValidate="txtKlantNummer"
    ErrorMessage="Klantnummer is verplicht" />
'''
        result = await extractor.extract_from_file("test.aspx", source)

        validation_rules = [r for r in result.business_rules if r.rule_type == RuleType.VALIDATION]
        assert len(validation_rules) >= 1

    @pytest.mark.asyncio
    async def test_permission_visibility(self, extractor):
        """Test permission-based visibility."""
        source = '''<%@ Page Language="VB" %>
<asp:Panel ID="pnlEdit" runat="server"
    Visible='<%# intCanEdit > 0 %>'>
    <asp:Button ID="btnSave" runat="server" Text="Opslaan" />
</asp:Panel>
'''
        result = await extractor.extract_from_file("test.aspx", source)

        # Should detect permission check
        branching_rules = [r for r in result.business_rules if r.rule_type == RuleType.BRANCHING]
        assert len(branching_rules) >= 1


class TestASCXUserControls:
    """Test ASCX user control extraction."""

    @pytest.mark.asyncio
    async def test_user_control_directive(self, extractor):
        """Test Control directive in ASCX."""
        source = '''<%@ Control Language="VB" ClassName="CustomerDetails" %>
<asp:Label ID="lblCustomerName" runat="server"
    Text='<%# Eval("CustomerName") %>' />
'''
        result = await extractor.extract_from_file("CustomerDetails.ascx", source)

        # Should detect as control, not page
        control_symbols = [s for s in result.code_symbols if s.symbol_type == 'control']
        assert len(control_symbols) >= 1


class TestMasterPages:
    """Test master page extraction."""

    @pytest.mark.asyncio
    async def test_master_page_directive(self, extractor):
        """Test Master directive."""
        source = '''<%@ Master Language="VB" %>
<html>
<head><title>Site Master</title></head>
<body>
    <asp:ContentPlaceHolder ID="MainContent" runat="server" />
</body>
</html>
'''
        result = await extractor.extract_from_file("Site.master", source)

        # Should detect as master
        master_symbols = [s for s in result.code_symbols if s.symbol_type == 'master']
        assert len(master_symbols) >= 1


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_file(self, extractor):
        """Test empty file handling."""
        result = await extractor.extract_from_file("empty.aspx", "")
        assert result is not None
        assert len(result.business_rules) == 0

    @pytest.mark.asyncio
    async def test_no_server_controls(self, extractor):
        """Test file with no server controls."""
        source = '''<%@ Page Language="VB" %>
<html>
<body>
    <h1>Static HTML Only</h1>
    <p>No ASP.NET controls here</p>
</body>
</html>
'''
        result = await extractor.extract_from_file("static.aspx", source)
        assert result is not None

    @pytest.mark.asyncio
    async def test_malformed_markup(self, extractor):
        """Test handling of malformed markup."""
        source = '''<%@ Page Language="VB" %>
<asp:TextBox ID="txtBroken" runat="server"
<asp:Button ID="btnMissing" runat="server" />
'''
        result = await extractor.extract_from_file("broken.aspx", source)
        # Should not crash
        assert result is not None

    @pytest.mark.asyncio
    async def test_nested_controls(self, extractor):
        """Test nested server controls."""
        source = '''<%@ Page Language="VB" %>
<asp:Panel ID="pnlOuter" runat="server">
    <asp:Panel ID="pnlInner" runat="server">
        <asp:Button ID="btnNested" runat="server" OnClick="btnNested_Click" />
    </asp:Panel>
</asp:Panel>
'''
        result = await extractor.extract_from_file("nested.aspx", source)

        # Should extract nested event handler
        workflow_rules = [r for r in result.business_rules if r.rule_type == RuleType.WORKFLOW]
        assert len(workflow_rules) >= 1


class TestConfidenceScores:
    """Test confidence score calculation."""

    @pytest.mark.asyncio
    async def test_validation_high_confidence(self, extractor):
        """Test validation rules have high confidence."""
        source = '''<%@ Page Language="VB" %>
<asp:RequiredFieldValidator ID="rfv1" runat="server"
    ControlToValidate="txt1"
    ErrorMessage="Required field" />
'''
        result = await extractor.extract_from_file("test.aspx", source)

        validation_rules = [r for r in result.business_rules if r.rule_type == RuleType.VALIDATION]
        assert len(validation_rules) >= 1
        assert validation_rules[0].confidence >= 0.85

    @pytest.mark.asyncio
    async def test_event_handler_high_confidence(self, extractor):
        """Test event handlers have high confidence."""
        source = '''<%@ Page Language="VB" %>
<asp:Button ID="btn1" runat="server" OnClick="btn1_Click" />
'''
        result = await extractor.extract_from_file("test.aspx", source)

        workflow_rules = [r for r in result.business_rules if r.rule_type == RuleType.WORKFLOW]
        assert len(workflow_rules) >= 1
        assert workflow_rules[0].confidence >= 0.85
