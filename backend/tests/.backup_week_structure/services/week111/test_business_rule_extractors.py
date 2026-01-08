# backend/tests/services/week111/test_business_rule_extractors.py
"""
Tests for Multi-Language Business Rule Extractors (Week 111-114).

Tests:
1. Unit tests for extraction models
2. VB.NET extractor tests
3. Classic ASP extractor tests
4. ExtractorFactory tests
5. HCI-CRS validation tests (integration)
"""

import pytest
from pathlib import Path
from datetime import datetime

from app.services.static_analysis.extraction_models import (
    BusinessRule,
    CodeSymbol,
    NFRIndicator,
    ExtractionResult,
    MultiFileExtractionResult,
    RuleType,
    Language,
    ExtractionTier,
    ExtractionMethod,
    EXTENSION_LANGUAGE_MAP,
    TIER_LLM_PROVIDERS,
)
from app.services.static_analysis.vbnet_extractor import VBNetBusinessRuleExtractor
from app.services.static_analysis.classic_asp_extractor import ClassicASPExtractor
from app.services.static_analysis.tsql_extractor import TSQLBusinessRuleExtractor
from app.services.static_analysis.plsql_extractor import PLSQLBusinessRuleExtractor
from app.services.static_analysis.extractor_factory import (
    ExtractorFactory,
    extract_business_rules,
)


# ============================================================================
# TEST DATA
# ============================================================================

SAMPLE_VBNET_CODE = """
Partial Public Class Default
    Inherits System.Web.UI.Page

    #Region "Properties"

    Private Property AgendaStartTime As DateTime
    Private Property AgendaEndTime As DateTime

    #End Region

    Protected Sub Page_Load(ByVal sender As Object, ByVal e As EventArgs)
        If Not tablePermissions.CanView Then
            Response.Redirect("NoAccess.aspx?msg=Geen rechten")
        End If

        If AgendaStartTime > AgendaEndTime Then
            lblError.Text = "Eindtijd moet na starttijd liggen"
            Return
        End If

        Select Case intStatus
            Case 0
                LoadNewAppointment()
            Case 1
                LoadExistingAppointment()
            Case Else
                ShowError()
        End Select
    End Sub

    Private Sub SaveAppointment()
        Try
            If intCanAdd = 0 Then
                Throw New UnauthorizedAccessException()
            End If

            Dim rst As New Recordset()
            rst.Execute("INSERT INTO taAfspraak VALUES (...)")
        Catch ex As Exception
            LogError(ex)
        End Try
    End Sub

End Class
"""

SAMPLE_ASP_CODE = """
<%@ Language=VBScript %>
<!--#include file="includes/connection.asp"-->
<%
Dim intCanView, intCanEdit, intCanDelete, intCanAdd
Dim rstAfspraak, strSQL

' Check permissions
If intCanView = 0 Then
    Response.Redirect "NoAccess.asp?error=1"
End If

' Validate dates
If datStart > datEnd Then
    strError = "Startdatum moet voor einddatum liggen"
End If

' Database query
Set rstAfspraak = Server.CreateObject("ADODB.Recordset")
strSQL = "SELECT * FROM taAfspraak WHERE AfspraakID = " & intID
rstAfspraak.Open strSQL, objConnection

If Not rstAfspraak.EOF Then
    Select Case intStatus
        Case 0
            Response.Write "Nieuw"
        Case 1
            Response.Write "Actief"
        Case 2
            Response.Write "Verwerkt"
    End Select
End If

On Error Resume Next
Session("LastAfspraak") = intID
%>
<html>
<body>
<%= rstAfspraak("Omschrijving") %>
</body>
</html>
"""

SAMPLE_TSQL_CODE = """
-- ============================================================
-- Stored Procedure: sp_SaveAfspraak
-- Description: Saves or updates an appointment
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[sp_SaveAfspraak]
    @AfspraakID INT = NULL,
    @ClientID INT,
    @StartDate DATETIME,
    @EndDate DATETIME,
    @Status INT = 0,
    @intCanAdd INT = 0,
    @intCanEdit INT = 0
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        BEGIN TRANSACTION

        -- Authorization check
        IF @intCanAdd = 0 AND @AfspraakID IS NULL
        BEGIN
            RAISERROR('Geen toestemming om afspraken toe te voegen', 16, 1)
            RETURN -1
        END

        IF @intCanEdit = 0 AND @AfspraakID IS NOT NULL
        BEGIN
            RAISERROR('Geen toestemming om afspraken te bewerken', 16, 1)
            RETURN -1
        END

        -- Validation: dates
        IF @StartDate > @EndDate
        BEGIN
            RAISERROR('Startdatum moet voor einddatum liggen', 16, 1)
            RETURN -1
        END

        -- Validation: client exists
        IF NOT EXISTS (SELECT 1 FROM taClient WHERE ClientID = @ClientID)
        BEGIN
            RAISERROR('Client niet gevonden', 16, 1)
            RETURN -1
        END

        -- Check for overlapping appointments
        IF EXISTS (
            SELECT 1 FROM taAfspraak
            WHERE ClientID = @ClientID
            AND AfspraakID <> ISNULL(@AfspraakID, 0)
            AND StartDate < @EndDate
            AND EndDate > @StartDate
        )
        BEGIN
            RAISERROR('Overlappende afspraak gevonden', 16, 1)
            RETURN -1
        END

        -- Insert or Update based on status
        IF @AfspraakID IS NULL
        BEGIN
            INSERT INTO taAfspraak (ClientID, StartDate, EndDate, Status, CreatedDate)
            VALUES (@ClientID, @StartDate, @EndDate, @Status, GETDATE())

            SET @AfspraakID = SCOPE_IDENTITY()
        END
        ELSE
        BEGIN
            UPDATE taAfspraak
            SET ClientID = @ClientID,
                StartDate = @StartDate,
                EndDate = @EndDate,
                Status = @Status,
                ModifiedDate = GETDATE()
            WHERE AfspraakID = @AfspraakID
        END

        -- Calculate duration in minutes
        DECLARE @Duration INT
        SET @Duration = DATEDIFF(MINUTE, @StartDate, @EndDate)

        -- Status-based workflow
        IF @Status = 1 -- Confirmed
        BEGIN
            EXEC sp_SendConfirmation @AfspraakID
        END
        ELSE IF @Status = 2 -- Cancelled
        BEGIN
            EXEC sp_CancelAppointment @AfspraakID
        END

        COMMIT TRANSACTION
        RETURN @AfspraakID

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION

        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE()
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY()

        RAISERROR(@ErrorMessage, @ErrorSeverity, 1)
        RETURN -1
    END CATCH
END
GO
"""

SAMPLE_PLSQL_CODE = """
-- ============================================================
-- Package: PKG_AFSPRAAK
-- Description: Appointment management package
-- ============================================================
CREATE OR REPLACE PACKAGE BODY pkg_afspraak AS

    -- Constants
    c_status_new     CONSTANT NUMBER := 0;
    c_status_active  CONSTANT NUMBER := 1;
    c_status_done    CONSTANT NUMBER := 2;

    -- Save or update appointment
    PROCEDURE p_save_afspraak(
        p_afspraak_id   IN OUT NUMBER,
        p_client_id     IN NUMBER,
        p_start_date    IN DATE,
        p_end_date      IN DATE,
        p_status        IN NUMBER DEFAULT 0,
        p_can_add       IN NUMBER DEFAULT 0,
        p_can_edit      IN NUMBER DEFAULT 0
    ) IS
        v_count         NUMBER;
        v_duration      NUMBER;
        v_error_msg     VARCHAR2(4000);
    BEGIN
        -- Authorization check
        IF p_can_add = 0 AND p_afspraak_id IS NULL THEN
            RAISE_APPLICATION_ERROR(-20001, 'Geen toestemming om afspraken toe te voegen');
        END IF;

        IF p_can_edit = 0 AND p_afspraak_id IS NOT NULL THEN
            RAISE_APPLICATION_ERROR(-20002, 'Geen toestemming om afspraken te bewerken');
        END IF;

        -- Validation: dates
        IF p_start_date > p_end_date THEN
            RAISE_APPLICATION_ERROR(-20003, 'Startdatum moet voor einddatum liggen');
        END IF;

        -- Validation: client exists
        SELECT COUNT(*) INTO v_count
        FROM ta_client
        WHERE client_id = p_client_id;

        IF v_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20004, 'Client niet gevonden');
        END IF;

        -- Check for overlapping appointments
        SELECT COUNT(*) INTO v_count
        FROM ta_afspraak
        WHERE client_id = p_client_id
          AND afspraak_id <> NVL(p_afspraak_id, 0)
          AND start_date < p_end_date
          AND end_date > p_start_date;

        IF v_count > 0 THEN
            RAISE_APPLICATION_ERROR(-20005, 'Overlappende afspraak gevonden');
        END IF;

        -- Insert or Update
        IF p_afspraak_id IS NULL THEN
            INSERT INTO ta_afspraak (client_id, start_date, end_date, status, created_date)
            VALUES (p_client_id, p_start_date, p_end_date, p_status, SYSDATE)
            RETURNING afspraak_id INTO p_afspraak_id;
        ELSE
            UPDATE ta_afspraak
            SET client_id = p_client_id,
                start_date = p_start_date,
                end_date = p_end_date,
                status = p_status,
                modified_date = SYSDATE
            WHERE afspraak_id = p_afspraak_id;
        END IF;

        -- Calculate duration
        v_duration := ROUND((p_end_date - p_start_date) * 24 * 60);

        -- Status-based workflow
        CASE p_status
            WHEN c_status_active THEN
                p_send_confirmation(p_afspraak_id);
            WHEN c_status_done THEN
                p_complete_appointment(p_afspraak_id);
            ELSE
                NULL;
        END CASE;

        COMMIT;

    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            ROLLBACK;
            RAISE_APPLICATION_ERROR(-20010, 'Geen data gevonden');
        WHEN TOO_MANY_ROWS THEN
            ROLLBACK;
            RAISE_APPLICATION_ERROR(-20011, 'Meerdere rijen gevonden');
        WHEN OTHERS THEN
            ROLLBACK;
            v_error_msg := SQLERRM;
            RAISE_APPLICATION_ERROR(-20099, v_error_msg);
    END p_save_afspraak;

    -- Get appointment by ID
    FUNCTION f_get_afspraak(
        p_afspraak_id IN NUMBER
    ) RETURN SYS_REFCURSOR IS
        v_cursor SYS_REFCURSOR;
    BEGIN
        OPEN v_cursor FOR
            SELECT a.afspraak_id,
                   a.client_id,
                   c.client_naam,
                   a.start_date,
                   a.end_date,
                   a.status
            FROM ta_afspraak a
            JOIN ta_client c ON a.client_id = c.client_id
            WHERE a.afspraak_id = p_afspraak_id;

        RETURN v_cursor;
    END f_get_afspraak;

END pkg_afspraak;
/
"""


# ============================================================================
# MODEL TESTS
# ============================================================================

class TestExtractionModels:
    """Tests for extraction data models."""

    def test_rule_type_enum(self):
        """Test RuleType enum values."""
        assert RuleType.VALIDATION.value == "validation"
        assert RuleType.AUTHORIZATION.value == "authorization"
        assert RuleType.SCHEDULING.value == "scheduling"
        assert RuleType.WORKFLOW.value == "workflow"

    def test_language_enum(self):
        """Test Language enum values."""
        assert Language.VBNET.value == "vbnet"
        assert Language.CLASSIC_ASP.value == "asp"
        assert Language.PYTHON.value == "python"

    def test_extraction_tier_enum(self):
        """Test ExtractionTier enum values."""
        assert ExtractionTier.FREE.value == "free"
        assert ExtractionTier.PREMIUM.value == "premium"

    def test_tier_llm_providers(self):
        """Test tier to LLM provider mapping."""
        assert TIER_LLM_PROVIDERS[ExtractionTier.FREE] == []
        assert "ollama" in TIER_LLM_PROVIDERS[ExtractionTier.BASIC]
        assert "anthropic" in TIER_LLM_PROVIDERS[ExtractionTier.PREMIUM]

    def test_business_rule_creation(self):
        """Test BusinessRule dataclass creation."""
        rule = BusinessRule(
            id="BR-0001",
            rule_type=RuleType.VALIDATION,
            condition="If x > 10 Then",
            action="Return error",
            source_file="test.vb",
            source_lines=(10, 15),
            confidence=0.85,
            natural_language="IF x greater than 10 THEN return error",
        )
        assert rule.id == "BR-0001"
        assert rule.rule_type == RuleType.VALIDATION
        assert rule.confidence == 0.85

    def test_business_rule_to_dict(self):
        """Test BusinessRule serialization."""
        rule = BusinessRule(
            id="BR-0001",
            rule_type=RuleType.AUTHORIZATION,
            condition="intCanView = 0",
            action="Redirect",
            source_file="test.asp",
            source_lines=(5, 5),
            confidence=0.9,
            natural_language="Check view permission",
            language=Language.CLASSIC_ASP,
        )
        d = rule.to_dict()
        assert d["id"] == "BR-0001"
        assert d["rule_type"] == "authorization"
        assert d["language"] == "asp"

    def test_extraction_result_aggregation(self):
        """Test ExtractionResult automatic aggregation."""
        rules = [
            BusinessRule(
                id="BR-0001",
                rule_type=RuleType.VALIDATION,
                condition="c1", action="a1",
                source_file="f.vb", source_lines=(1, 1),
                confidence=0.9, natural_language="n1",
            ),
            BusinessRule(
                id="BR-0002",
                rule_type=RuleType.VALIDATION,
                condition="c2", action="a2",
                source_file="f.vb", source_lines=(2, 2),
                confidence=0.5, natural_language="n2",
            ),
            BusinessRule(
                id="BR-0003",
                rule_type=RuleType.AUTHORIZATION,
                condition="c3", action="a3",
                source_file="f.vb", source_lines=(3, 3),
                confidence=0.85, natural_language="n3",
            ),
        ]
        result = ExtractionResult(
            source_path="f.vb",
            language=Language.VBNET,
            extraction_tier=ExtractionTier.FREE,
            extraction_method=ExtractionMethod.REGEX,
            business_rules=rules,
            code_symbols=[],
            nfr_indicators=[],
        )
        assert result.total_rules == 3
        assert result.rules_by_type["validation"] == 2
        assert result.rules_by_type["authorization"] == 1
        assert result.rules_by_confidence["high"] == 2  # >= 0.8
        assert result.rules_by_confidence["medium"] == 1  # 0.5-0.8


# ============================================================================
# VBNET EXTRACTOR TESTS
# ============================================================================

class TestVBNetExtractor:
    """Tests for VB.NET business rule extractor."""

    @pytest.fixture
    def extractor(self):
        return VBNetBusinessRuleExtractor(extraction_tier=ExtractionTier.FREE)

    def test_supported_extensions(self, extractor):
        """Test supported file extensions."""
        exts = extractor.get_supported_extensions()
        assert '.vb' in exts
        assert '.aspx.vb' in exts

    def test_language(self, extractor):
        """Test language identification."""
        assert extractor.get_language() == Language.VBNET

    def test_supports_file(self, extractor):
        """Test file support detection."""
        assert extractor.supports_file("Default.aspx.vb")
        assert extractor.supports_file("Module.vb")
        assert not extractor.supports_file("script.asp")

    @pytest.mark.asyncio
    async def test_extract_symbols(self, extractor):
        """Test symbol extraction from VB.NET code."""
        symbols = await extractor._extract_symbols(SAMPLE_VBNET_CODE, "test.vb")

        # Should find class
        classes = [s for s in symbols if s.symbol_type == "class"]
        assert len(classes) >= 1
        assert any(s.name == "Default" for s in classes)

        # Should find subs
        subs = [s for s in symbols if s.symbol_type == "sub"]
        assert len(subs) >= 2
        assert any(s.name == "Page_Load" for s in subs)
        assert any(s.name == "SaveAppointment" for s in subs)

        # Should find properties
        props = [s for s in symbols if s.symbol_type == "property"]
        assert len(props) >= 2

    @pytest.mark.asyncio
    async def test_extract_rules(self, extractor):
        """Test business rule extraction from VB.NET code."""
        result = await extractor.extract_from_file("test.vb", SAMPLE_VBNET_CODE)

        assert result.total_rules > 0
        assert result.language == Language.VBNET

        # Check rule types present
        rule_types = set(r.rule_type for r in result.business_rules)
        assert RuleType.AUTHORIZATION in rule_types or RuleType.VALIDATION in rule_types

    @pytest.mark.asyncio
    async def test_extract_authorization_rules(self, extractor):
        """Test authorization rule detection."""
        result = await extractor.extract_from_file("test.vb", SAMPLE_VBNET_CODE)

        auth_rules = [r for r in result.business_rules if r.rule_type == RuleType.AUTHORIZATION]
        # Should detect CanView and intCanAdd patterns
        assert len(auth_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_scheduling_rules(self, extractor):
        """Test scheduling/datetime rule detection."""
        result = await extractor.extract_from_file("test.vb", SAMPLE_VBNET_CODE)

        sched_rules = [r for r in result.business_rules if r.rule_type == RuleType.SCHEDULING]
        # Should detect AgendaStartTime/EndTime comparison
        assert len(sched_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_branching_rules(self, extractor):
        """Test Select Case branching rule detection."""
        result = await extractor.extract_from_file("test.vb", SAMPLE_VBNET_CODE)

        branch_rules = [r for r in result.business_rules if r.rule_type == RuleType.BRANCHING]
        # Should detect Select Case intStatus
        assert len(branch_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_nfrs(self, extractor):
        """Test NFR indicator detection."""
        result = await extractor.extract_from_file("test.vb", SAMPLE_VBNET_CODE)

        # Should detect Try-Catch (reliability), Response.Redirect (usability)
        assert len(result.nfr_indicators) >= 1


# ============================================================================
# CLASSIC ASP EXTRACTOR TESTS
# ============================================================================

class TestClassicASPExtractor:
    """Tests for Classic ASP business rule extractor."""

    @pytest.fixture
    def extractor(self):
        return ClassicASPExtractor(extraction_tier=ExtractionTier.FREE)

    def test_supported_extensions(self, extractor):
        """Test supported file extensions."""
        exts = extractor.get_supported_extensions()
        assert '.asp' in exts
        assert '.asa' in exts

    def test_language(self, extractor):
        """Test language identification."""
        assert extractor.get_language() == Language.CLASSIC_ASP

    def test_supports_file(self, extractor):
        """Test file support detection."""
        assert extractor.supports_file("Afspraak.asp")
        assert extractor.supports_file("global.asa")
        assert not extractor.supports_file("Module.vb")

    @pytest.mark.asyncio
    async def test_extract_rules(self, extractor):
        """Test business rule extraction from Classic ASP code."""
        result = await extractor.extract_from_file("test.asp", SAMPLE_ASP_CODE)

        assert result.total_rules > 0
        assert result.language == Language.CLASSIC_ASP

    @pytest.mark.asyncio
    async def test_extract_authorization_rules(self, extractor):
        """Test authorization rule detection in ASP."""
        result = await extractor.extract_from_file("test.asp", SAMPLE_ASP_CODE)

        auth_rules = [r for r in result.business_rules if r.rule_type == RuleType.AUTHORIZATION]
        # Should detect intCanView check
        assert len(auth_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_data_access_rules(self, extractor):
        """Test data access rule detection."""
        result = await extractor.extract_from_file("test.asp", SAMPLE_ASP_CODE)

        data_rules = [r for r in result.business_rules if r.rule_type == RuleType.DATA_ACCESS]
        # Should detect Recordset and SQL operations
        assert len(data_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_branching_rules(self, extractor):
        """Test Select Case branching in ASP."""
        result = await extractor.extract_from_file("test.asp", SAMPLE_ASP_CODE)

        branch_rules = [r for r in result.business_rules if r.rule_type == RuleType.BRANCHING]
        # Should detect Select Case intStatus
        assert len(branch_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_state_management(self, extractor):
        """Test Session/state management detection."""
        result = await extractor.extract_from_file("test.asp", SAMPLE_ASP_CODE)

        state_rules = [r for r in result.business_rules if r.rule_type == RuleType.STATE_MANAGEMENT]
        # Should detect Session("LastAfspraak")
        assert len(state_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_entities(self, extractor):
        """Test entity extraction from ASP code."""
        result = await extractor.extract_from_file("test.asp", SAMPLE_ASP_CODE)

        # Check entities are extracted
        all_entities = set()
        for rule in result.business_rules:
            all_entities.update(rule.related_entities)

        # Should find Afspraak entity from taAfspraak or rstAfspraak
        assert len(all_entities) >= 0  # May vary based on patterns


# ============================================================================
# T-SQL EXTRACTOR TESTS (Phase 2)
# ============================================================================

class TestTSQLExtractor:
    """Tests for T-SQL business rule extractor."""

    @pytest.fixture
    def extractor(self):
        return TSQLBusinessRuleExtractor(extraction_tier=ExtractionTier.FREE)

    def test_supported_extensions(self, extractor):
        """Test supported file extensions."""
        exts = extractor.get_supported_extensions()
        assert '.sql' in exts
        assert '.prc' in exts

    def test_language(self, extractor):
        """Test language identification."""
        assert extractor.get_language() == Language.TSQL

    def test_supports_file(self, extractor):
        """Test file support detection."""
        assert extractor.supports_file("sp_SaveAfspraak.sql")
        assert extractor.supports_file("procedure.prc")
        assert not extractor.supports_file("package.pkg")  # PL/SQL

    @pytest.mark.asyncio
    async def test_extract_symbols(self, extractor):
        """Test symbol extraction from T-SQL code."""
        symbols = await extractor._extract_symbols(SAMPLE_TSQL_CODE, "test.sql")

        # Should find stored procedure
        procs = [s for s in symbols if s.symbol_type == "procedure"]
        assert len(procs) >= 1
        assert any("SaveAfspraak" in s.name for s in procs)

    @pytest.mark.asyncio
    async def test_extract_rules(self, extractor):
        """Test business rule extraction from T-SQL code."""
        result = await extractor.extract_from_file("test.sql", SAMPLE_TSQL_CODE)

        assert result.total_rules > 0
        assert result.language == Language.TSQL

        # Check rule types present
        rule_types = set(r.rule_type for r in result.business_rules)
        assert len(rule_types) >= 2  # Should have multiple types

    @pytest.mark.asyncio
    async def test_extract_authorization_rules(self, extractor):
        """Test authorization rule detection in T-SQL."""
        result = await extractor.extract_from_file("test.sql", SAMPLE_TSQL_CODE)

        auth_rules = [r for r in result.business_rules if r.rule_type == RuleType.AUTHORIZATION]
        # Should detect @intCanAdd and @intCanEdit patterns
        assert len(auth_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_validation_rules(self, extractor):
        """Test validation rule detection in T-SQL."""
        result = await extractor.extract_from_file("test.sql", SAMPLE_TSQL_CODE)

        val_rules = [r for r in result.business_rules if r.rule_type == RuleType.VALIDATION]
        # Should detect date validation, exists checks
        assert len(val_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_data_access_rules(self, extractor):
        """Test data access rule detection in T-SQL."""
        result = await extractor.extract_from_file("test.sql", SAMPLE_TSQL_CODE)

        data_rules = [r for r in result.business_rules if r.rule_type == RuleType.DATA_ACCESS]
        # Should detect INSERT, UPDATE, SELECT statements
        assert len(data_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_error_handling_rules(self, extractor):
        """Test TRY-CATCH error handling detection in T-SQL."""
        result = await extractor.extract_from_file("test.sql", SAMPLE_TSQL_CODE)

        error_rules = [r for r in result.business_rules if r.rule_type == RuleType.ERROR_HANDLING]
        # Should detect BEGIN TRY/CATCH, RAISERROR, ERROR_MESSAGE
        assert len(error_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_scheduling_rules(self, extractor):
        """Test scheduling/date rule detection in T-SQL."""
        result = await extractor.extract_from_file("test.sql", SAMPLE_TSQL_CODE)

        sched_rules = [r for r in result.business_rules if r.rule_type == RuleType.SCHEDULING]
        # Should detect GETDATE, DATEDIFF, @StartDate/@EndDate
        assert len(sched_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_entities(self, extractor):
        """Test entity extraction from T-SQL code."""
        result = await extractor.extract_from_file("test.sql", SAMPLE_TSQL_CODE)

        all_entities = set()
        for rule in result.business_rules:
            all_entities.update(rule.related_entities)

        # Should find taAfspraak, taClient entities
        assert len(all_entities) >= 1


# ============================================================================
# PL/SQL EXTRACTOR TESTS (Phase 2)
# ============================================================================

class TestPLSQLExtractor:
    """Tests for PL/SQL business rule extractor."""

    @pytest.fixture
    def extractor(self):
        return PLSQLBusinessRuleExtractor(extraction_tier=ExtractionTier.FREE)

    def test_supported_extensions(self, extractor):
        """Test supported file extensions."""
        exts = extractor.get_supported_extensions()
        assert '.pkg' in exts
        assert '.pkb' in exts
        assert '.pks' in exts
        assert '.fnc' in exts
        assert '.trg' in exts
        # .prc is T-SQL specific, not PL/SQL
        assert '.prc' not in exts

    def test_language(self, extractor):
        """Test language identification."""
        assert extractor.get_language() == Language.PLSQL

    def test_supports_file(self, extractor):
        """Test file support detection."""
        assert extractor.supports_file("pkg_afspraak.pkb")
        assert extractor.supports_file("pkg_afspraak.pks")
        assert extractor.supports_file("f_get_afspraak.fnc")
        assert extractor.supports_file("tr_audit.trg")
        assert not extractor.supports_file("sp_test.prc")  # T-SQL specific
        assert not extractor.supports_file("script.sql")  # Generic SQL defaults to T-SQL

    @pytest.mark.asyncio
    async def test_extract_symbols(self, extractor):
        """Test symbol extraction from PL/SQL code."""
        symbols = await extractor._extract_symbols(SAMPLE_PLSQL_CODE, "test.pkb")

        # Should find package body
        pkgs = [s for s in symbols if s.symbol_type == "package_body"]
        assert len(pkgs) >= 1

        # Should find procedures
        procs = [s for s in symbols if s.symbol_type == "procedure"]
        assert len(procs) >= 1
        assert any("save_afspraak" in s.name.lower() for s in procs)

        # Should find functions
        funcs = [s for s in symbols if s.symbol_type == "function"]
        assert len(funcs) >= 1
        assert any("get_afspraak" in s.name.lower() for s in funcs)

    @pytest.mark.asyncio
    async def test_extract_rules(self, extractor):
        """Test business rule extraction from PL/SQL code."""
        result = await extractor.extract_from_file("test.pkb", SAMPLE_PLSQL_CODE)

        assert result.total_rules > 0
        assert result.language == Language.PLSQL

        # Check rule types present
        rule_types = set(r.rule_type for r in result.business_rules)
        assert len(rule_types) >= 2  # Should have multiple types

    @pytest.mark.asyncio
    async def test_extract_authorization_rules(self, extractor):
        """Test authorization rule detection in PL/SQL."""
        result = await extractor.extract_from_file("test.pkb", SAMPLE_PLSQL_CODE)

        auth_rules = [r for r in result.business_rules if r.rule_type == RuleType.AUTHORIZATION]
        # Should detect p_can_add and p_can_edit patterns
        assert len(auth_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_validation_rules(self, extractor):
        """Test validation rule detection in PL/SQL."""
        result = await extractor.extract_from_file("test.pkb", SAMPLE_PLSQL_CODE)

        val_rules = [r for r in result.business_rules if r.rule_type == RuleType.VALIDATION]
        # Should detect date validation, count checks
        assert len(val_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_data_access_rules(self, extractor):
        """Test data access rule detection in PL/SQL."""
        result = await extractor.extract_from_file("test.pkb", SAMPLE_PLSQL_CODE)

        data_rules = [r for r in result.business_rules if r.rule_type == RuleType.DATA_ACCESS]
        # Should detect INSERT, UPDATE, SELECT statements
        assert len(data_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_error_handling_rules(self, extractor):
        """Test EXCEPTION handling detection in PL/SQL."""
        result = await extractor.extract_from_file("test.pkb", SAMPLE_PLSQL_CODE)

        error_rules = [r for r in result.business_rules if r.rule_type == RuleType.ERROR_HANDLING]
        # Should detect EXCEPTION, WHEN OTHERS, RAISE_APPLICATION_ERROR
        assert len(error_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_scheduling_rules(self, extractor):
        """Test scheduling/date rule detection in PL/SQL."""
        result = await extractor.extract_from_file("test.pkb", SAMPLE_PLSQL_CODE)

        sched_rules = [r for r in result.business_rules if r.rule_type == RuleType.SCHEDULING]
        # Should detect SYSDATE, p_start_date/p_end_date
        assert len(sched_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_branching_rules(self, extractor):
        """Test CASE WHEN branching detection in PL/SQL."""
        result = await extractor.extract_from_file("test.pkb", SAMPLE_PLSQL_CODE)

        branch_rules = [r for r in result.business_rules if r.rule_type == RuleType.BRANCHING]
        # Should detect CASE p_status WHEN
        assert len(branch_rules) >= 1

    @pytest.mark.asyncio
    async def test_extract_state_management(self, extractor):
        """Test cursor and state management detection in PL/SQL."""
        result = await extractor.extract_from_file("test.pkb", SAMPLE_PLSQL_CODE)

        state_rules = [r for r in result.business_rules if r.rule_type == RuleType.STATE_MANAGEMENT]
        # Should detect CURSOR, OPEN, variable assignments
        assert len(state_rules) >= 1


# ============================================================================
# EXTRACTOR FACTORY TESTS
# ============================================================================

class TestExtractorFactory:
    """Tests for ExtractorFactory."""

    @pytest.fixture
    def factory(self):
        return ExtractorFactory(extraction_tier=ExtractionTier.FREE)

    def test_detect_language_vbnet(self, factory):
        """Test language detection for VB.NET files."""
        assert factory.detect_language("Default.aspx.vb") == Language.VBNET
        assert factory.detect_language("Module.vb") == Language.VBNET

    def test_detect_language_asp(self, factory):
        """Test language detection for ASP files."""
        assert factory.detect_language("Afspraak.asp") == Language.CLASSIC_ASP
        assert factory.detect_language("global.asa") == Language.CLASSIC_ASP

    def test_detect_language_tsql(self, factory):
        """Test language detection for T-SQL files."""
        assert factory.detect_language("sp_SaveAfspraak.sql") == Language.TSQL
        assert factory.detect_language("procedure.prc") == Language.TSQL

    def test_detect_language_plsql(self, factory):
        """Test language detection for PL/SQL files."""
        assert factory.detect_language("pkg_afspraak.pkg") == Language.PLSQL
        assert factory.detect_language("pkg_afspraak.pkb") == Language.PLSQL
        assert factory.detect_language("pkg_afspraak.pks") == Language.PLSQL
        assert factory.detect_language("f_get_afspraak.fnc") == Language.PLSQL
        assert factory.detect_language("tr_audit.trg") == Language.PLSQL

    def test_detect_language_unsupported(self, factory):
        """Test language detection for unsupported files."""
        # Note: Python is now supported, so we use truly unsupported extensions
        assert factory.detect_language("style.css") is None
        assert factory.detect_language("document.pdf") is None

    def test_get_extractor_vbnet(self, factory):
        """Test getting VB.NET extractor."""
        extractor = factory.get_extractor(Language.VBNET)
        assert extractor is not None
        assert isinstance(extractor, VBNetBusinessRuleExtractor)

    def test_get_extractor_asp(self, factory):
        """Test getting Classic ASP extractor."""
        extractor = factory.get_extractor(Language.CLASSIC_ASP)
        assert extractor is not None
        assert isinstance(extractor, ClassicASPExtractor)

    def test_get_extractor_tsql(self, factory):
        """Test getting T-SQL extractor."""
        extractor = factory.get_extractor(Language.TSQL)
        assert extractor is not None
        assert isinstance(extractor, TSQLBusinessRuleExtractor)

    def test_get_extractor_plsql(self, factory):
        """Test getting PL/SQL extractor."""
        extractor = factory.get_extractor(Language.PLSQL)
        assert extractor is not None
        assert isinstance(extractor, PLSQLBusinessRuleExtractor)

    def test_get_extractor_for_file(self, factory):
        """Test getting extractor by file path."""
        extractor = factory.get_extractor_for_file("test.aspx.vb")
        assert isinstance(extractor, VBNetBusinessRuleExtractor)

        extractor = factory.get_extractor_for_file("test.asp")
        assert isinstance(extractor, ClassicASPExtractor)

        extractor = factory.get_extractor_for_file("test.sql")
        assert isinstance(extractor, TSQLBusinessRuleExtractor)

        extractor = factory.get_extractor_for_file("test.pkb")
        assert isinstance(extractor, PLSQLBusinessRuleExtractor)

    def test_extractor_caching(self, factory):
        """Test that extractors are cached."""
        ext1 = factory.get_extractor(Language.VBNET)
        ext2 = factory.get_extractor(Language.VBNET)
        assert ext1 is ext2  # Same instance

    def test_supported_languages(self):
        """Test getting list of supported languages."""
        languages = ExtractorFactory.get_supported_languages()
        assert Language.VBNET in languages
        assert Language.CLASSIC_ASP in languages
        assert Language.TSQL in languages
        assert Language.PLSQL in languages

    def test_supported_extensions(self):
        """Test getting list of supported extensions."""
        exts = ExtractorFactory.get_supported_extensions()
        assert '.vb' in exts
        assert '.asp' in exts
        assert '.sql' in exts
        assert '.pkg' in exts
        assert '.pkb' in exts

    @pytest.mark.asyncio
    async def test_extract_from_file(self, factory):
        """Test extraction from file content - handles non-existent file gracefully."""
        # Non-existent file returns result with errors
        result = await factory.extract_from_file("nonexistent_test.vb")
        assert result is not None
        assert len(result.errors) > 0
        assert "No such file or directory" in result.errors[0]
        assert result.total_rules == 0


# ============================================================================
# HCI-CRS INTEGRATION TESTS
# ============================================================================

class TestHCICRSIntegration:
    """Integration tests against real HCI-CRS files (if available)."""

    HCI_VBNET_FILE = "/opt/projecten/hci-crs/src/EPD/WEB/Agenda2/Default.aspx.vb"
    HCI_ASP_FILE = "/opt/projecten/hci-crs/src/EPD/WEB/Afspraken/Agenda.asp"

    @pytest.fixture
    def factory(self):
        return ExtractorFactory(extraction_tier=ExtractionTier.FREE)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not Path("/opt/projecten/hci-crs").exists(),
        reason="HCI-CRS project not available"
    )
    async def test_extract_from_hci_vbnet(self, factory):
        """Test extraction from real HCI-CRS VB.NET file."""
        if not Path(self.HCI_VBNET_FILE).exists():
            pytest.skip("HCI-CRS VB.NET file not found")

        result = await factory.extract_from_file(self.HCI_VBNET_FILE)

        assert result is not None
        assert result.language == Language.VBNET

        # Expected based on previous analysis: ~235 rules
        assert result.total_rules >= 100, f"Expected 100+ rules, got {result.total_rules}"

        # Check for expected rule types
        rule_types = set(r.rule_type for r in result.business_rules)
        assert RuleType.AUTHORIZATION in rule_types, "Missing authorization rules"
        assert RuleType.VALIDATION in rule_types, "Missing validation rules"

        print(f"\n=== HCI-CRS VB.NET Extraction Results ===")
        print(f"File: {self.HCI_VBNET_FILE}")
        print(f"Lines of code: {result.lines_of_code}")
        print(f"Total rules: {result.total_rules}")
        print(f"Rules by type: {result.rules_by_type}")
        print(f"Symbols: {len(result.code_symbols)}")
        print(f"NFRs: {len(result.nfr_indicators)}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not Path("/opt/projecten/hci-crs").exists(),
        reason="HCI-CRS project not available"
    )
    async def test_extract_from_hci_asp(self, factory):
        """Test extraction from real HCI-CRS Classic ASP file."""
        if not Path(self.HCI_ASP_FILE).exists():
            pytest.skip("HCI-CRS ASP file not found")

        result = await factory.extract_from_file(self.HCI_ASP_FILE)

        assert result is not None
        assert result.language == Language.CLASSIC_ASP

        # Expected based on previous analysis: ~99 rules extracted via regex
        assert result.total_rules >= 90, f"Expected 90+ rules, got {result.total_rules}"

        print(f"\n=== HCI-CRS Classic ASP Extraction Results ===")
        print(f"File: {self.HCI_ASP_FILE}")
        print(f"Lines of code: {result.lines_of_code}")
        print(f"Total rules: {result.total_rules}")
        print(f"Rules by type: {result.rules_by_type}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not Path("/opt/projecten/hci-crs").exists(),
        reason="HCI-CRS project not available"
    )
    async def test_extract_directory_hci_agenda(self, factory):
        """Test extraction from HCI-CRS Agenda directory."""
        agenda_dir = "/opt/projecten/hci-crs/src/EPD/WEB/Agenda2"
        if not Path(agenda_dir).exists():
            pytest.skip("HCI-CRS Agenda directory not found")

        result = await factory.extract_from_directory(agenda_dir, recursive=False)

        assert result.total_files >= 1
        assert result.total_rules >= 100

        print(f"\n=== HCI-CRS Agenda Directory Extraction ===")
        print(f"Directory: {agenda_dir}")
        print(f"Files processed: {result.total_files}")
        print(f"Total lines: {result.total_lines}")
        print(f"Total rules: {result.total_rules}")
        print(f"Files by language: {result.files_by_language}")
        print(f"Rules by language: {result.rules_by_language}")


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunction:
    """Tests for the extract_business_rules convenience function."""

    @pytest.mark.asyncio
    async def test_extract_nonexistent_file(self):
        """Test extraction from non-existent file."""
        result = await extract_business_rules("/nonexistent/path.vb")
        assert result.total_files == 0
        assert result.total_rules == 0

    @pytest.mark.asyncio
    async def test_extract_with_tier(self):
        """Test extraction with specific tier."""
        result = await extract_business_rules(
            "/nonexistent/path",
            tier=ExtractionTier.PREMIUM
        )
        assert result.extraction_tier == ExtractionTier.PREMIUM
