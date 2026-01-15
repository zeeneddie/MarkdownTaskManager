"""
Unit tests for DatabaseFirstMigrationService (D2 - Fase 24).

Tests cover:
- Session management
- Schema analysis
- Data type mappings
- Dual-write configuration
- Data validation
- Migration phases

Author: Claude Code (Week 158)
Date: 2026-01-15
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.services.database_first_migration_service import (
    DatabaseFirstMigrationService,
    DatabaseFirstSession,
    SchemaAnalysisResult,
    SchemaObjectAnalysis,
    SchemaObjectType,
    CompatibilityLevel,
    DataTypeMapping,
    DataTypeCategory,
    DualWriteConfig,
    DualWriteMode,
    DualWriteStatus,
    ValidationResult,
    ValidationLevel,
    MigrationPhase,
    MigrationScript,
    ORACLE_TO_POSTGRESQL,
    SQLSERVER_TO_POSTGRESQL,
    create_database_first_service,
)


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """Create a fresh DatabaseFirstMigrationService instance."""
    return DatabaseFirstMigrationService()


@pytest.fixture
def session(service):
    """Create a session for testing."""
    return service.create_session("oracle", "postgresql")


# ==================== Enum Tests ====================

class TestEnums:
    """Test enum definitions."""

    def test_schema_object_types(self):
        """Test SchemaObjectType enum values."""
        assert SchemaObjectType.TABLE.value == "table"
        assert SchemaObjectType.VIEW.value == "view"
        assert SchemaObjectType.PROCEDURE.value == "procedure"
        assert SchemaObjectType.TRIGGER.value == "trigger"

    def test_compatibility_levels(self):
        """Test CompatibilityLevel enum values."""
        assert CompatibilityLevel.FULL.value == "full"
        assert CompatibilityLevel.PARTIAL.value == "partial"
        assert CompatibilityLevel.MANUAL.value == "manual"
        assert CompatibilityLevel.INCOMPATIBLE.value == "incompatible"

    def test_dual_write_modes(self):
        """Test DualWriteMode enum values."""
        assert DualWriteMode.OFF.value == "off"
        assert DualWriteMode.SYNC.value == "sync"
        assert DualWriteMode.ASYNC.value == "async"
        assert DualWriteMode.SHADOW.value == "shadow"

    def test_validation_levels(self):
        """Test ValidationLevel enum values."""
        assert ValidationLevel.COUNT_ONLY.value == "count_only"
        assert ValidationLevel.CHECKSUM.value == "checksum"
        assert ValidationLevel.FULL.value == "full"

    def test_migration_phases(self):
        """Test MigrationPhase enum values."""
        assert MigrationPhase.ANALYSIS.value == "analysis"
        assert MigrationPhase.SCHEMA_DEPLOY.value == "schema_deploy"
        assert MigrationPhase.DUAL_WRITE_SETUP.value == "dual_write_setup"
        assert MigrationPhase.CUTOVER.value == "cutover"


# ==================== Data Type Mapping Tests ====================

class TestDataTypeMappings:
    """Test data type mapping configurations."""

    def test_oracle_varchar2_mapping(self):
        """Test Oracle VARCHAR2 maps to PostgreSQL VARCHAR."""
        mapping = ORACLE_TO_POSTGRESQL["VARCHAR2"]
        assert mapping.source_type == "VARCHAR2"
        assert mapping.target_type == "VARCHAR"
        assert mapping.compatibility == CompatibilityLevel.FULL

    def test_oracle_number_mapping(self):
        """Test Oracle NUMBER maps to PostgreSQL NUMERIC."""
        mapping = ORACLE_TO_POSTGRESQL["NUMBER"]
        assert mapping.target_type == "NUMERIC"
        assert mapping.category == DataTypeCategory.NUMERIC

    def test_oracle_date_requires_attention(self):
        """Test Oracle DATE has partial compatibility (includes time)."""
        mapping = ORACLE_TO_POSTGRESQL["DATE"]
        assert mapping.compatibility == CompatibilityLevel.PARTIAL
        assert "time" in mapping.notes.lower()

    def test_oracle_sdo_geometry_needs_postgis(self):
        """Test Oracle SDO_GEOMETRY requires manual intervention."""
        mapping = ORACLE_TO_POSTGRESQL["SDO_GEOMETRY"]
        assert mapping.compatibility == CompatibilityLevel.MANUAL
        assert "PostGIS" in mapping.notes

    def test_sqlserver_bit_to_boolean(self):
        """Test SQL Server BIT maps to PostgreSQL BOOLEAN."""
        mapping = SQLSERVER_TO_POSTGRESQL["BIT"]
        assert mapping.target_type == "BOOLEAN"
        assert mapping.category == DataTypeCategory.BOOLEAN

    def test_sqlserver_uniqueidentifier_to_uuid(self):
        """Test SQL Server UNIQUEIDENTIFIER maps to PostgreSQL UUID."""
        mapping = SQLSERVER_TO_POSTGRESQL["UNIQUEIDENTIFIER"]
        assert mapping.target_type == "UUID"

    def test_sqlserver_hierarchyid_manual(self):
        """Test SQL Server HIERARCHYID requires manual intervention."""
        mapping = SQLSERVER_TO_POSTGRESQL["HIERARCHYID"]
        assert mapping.compatibility == CompatibilityLevel.MANUAL


# ==================== Session Management Tests ====================

class TestSessionManagement:
    """Test session creation and management."""

    def test_create_session(self, service):
        """Test session creation."""
        session = service.create_session("oracle", "postgresql")

        assert session.session_id.startswith("dbf-")
        assert session.source_db == "oracle"
        assert session.target_db == "postgresql"
        assert session.phase == MigrationPhase.ANALYSIS

    def test_create_session_custom_id(self, service):
        """Test session creation with custom ID."""
        session = service.create_session("sqlserver", "postgresql", session_id="custom-123")

        assert session.session_id == "custom-123"

    def test_get_session(self, service, session):
        """Test retrieving an existing session."""
        retrieved = service.get_session(session.session_id)

        assert retrieved is not None
        assert retrieved.session_id == session.session_id

    def test_get_nonexistent_session(self, service):
        """Test retrieving a non-existent session returns None."""
        result = service.get_session("nonexistent")
        assert result is None

    def test_list_sessions(self, service):
        """Test listing all sessions."""
        service.create_session("oracle", "postgresql")
        service.create_session("sqlserver", "postgresql")

        sessions = service.list_sessions()
        assert len(sessions) == 2


# ==================== Schema Analysis Tests ====================

class TestSchemaAnalysis:
    """Test schema analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_schema(self, service, session):
        """Test basic schema analysis."""
        result = await service.analyze_schema(
            session.session_id,
            source_connection={"host": "localhost"}
        )

        assert isinstance(result, SchemaAnalysisResult)
        assert result.source_database == "oracle"
        assert result.target_database == "postgresql"
        assert result.total_objects > 0

    @pytest.mark.asyncio
    async def test_analyze_schema_counts_objects(self, service, session):
        """Test that schema analysis counts object types."""
        result = await service.analyze_schema(
            session.session_id,
            source_connection={}
        )

        # Should have sample tables, indexes, procedures
        assert result.tables > 0
        assert result.indexes > 0
        assert result.procedures > 0

    @pytest.mark.asyncio
    async def test_analyze_schema_calculates_compatibility(self, service, session):
        """Test compatibility score calculation."""
        result = await service.analyze_schema(
            session.session_id,
            source_connection={}
        )

        # Score should be between 0 and 100
        assert 0 <= result.compatibility_score <= 100

    @pytest.mark.asyncio
    async def test_analyze_schema_generates_recommendations(self, service, session):
        """Test that analysis generates recommendations."""
        result = await service.analyze_schema(
            session.session_id,
            source_connection={}
        )

        # Should have at least one recommendation
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_analyze_schema_invalid_session(self, service):
        """Test analyzing with invalid session raises error."""
        with pytest.raises(ValueError, match="not found"):
            await service.analyze_schema("invalid", source_connection={})


class TestSchemaAnalysisResult:
    """Test SchemaAnalysisResult dataclass."""

    def test_compatibility_score_empty(self):
        """Test compatibility score with no objects."""
        result = SchemaAnalysisResult(
            source_database="oracle",
            target_database="postgresql"
        )
        assert result.compatibility_score == 100.0

    def test_compatibility_score_calculation(self):
        """Test compatibility score calculation."""
        result = SchemaAnalysisResult(
            source_database="oracle",
            target_database="postgresql",
            total_objects=10,
            fully_compatible=5,
            partially_compatible=3,
            manual_intervention=2,
            incompatible=0
        )

        # (5*100 + 3*70 + 2*30) / 10 = (500 + 210 + 60) / 10 = 77.0
        assert result.compatibility_score == 77.0

    def test_is_migratable_true(self):
        """Test is_migratable when migration is possible."""
        result = SchemaAnalysisResult(
            source_database="oracle",
            target_database="postgresql",
            incompatible=0
        )
        assert result.is_migratable is True

    def test_is_migratable_false_incompatible(self):
        """Test is_migratable when there are incompatible objects."""
        result = SchemaAnalysisResult(
            source_database="oracle",
            target_database="postgresql",
            incompatible=1
        )
        assert result.is_migratable is False

    def test_is_migratable_false_blocking_issues(self):
        """Test is_migratable when there are blocking issues."""
        result = SchemaAnalysisResult(
            source_database="oracle",
            target_database="postgresql",
            blocking_issues=["Critical security issue"]
        )
        assert result.is_migratable is False


# ==================== Schema Deployment Tests ====================

class TestSchemaDeployment:
    """Test schema deployment functionality."""

    @pytest.mark.asyncio
    async def test_deploy_schema_dry_run(self, service, session):
        """Test dry run schema deployment."""
        await service.analyze_schema(session.session_id, source_connection={})

        scripts = await service.deploy_schema(
            session.session_id,
            target_connection={},
            dry_run=True
        )

        assert len(scripts) > 0
        assert all(isinstance(s, MigrationScript) for s in scripts)

    @pytest.mark.asyncio
    async def test_deploy_schema_generates_ddl(self, service, session):
        """Test that deployment generates DDL scripts."""
        await service.analyze_schema(session.session_id, source_connection={})

        scripts = await service.deploy_schema(
            session.session_id,
            target_connection={},
            dry_run=True
        )

        # Should have CREATE TABLE scripts
        table_scripts = [s for s in scripts if "create_table" in s.name]
        assert len(table_scripts) > 0

        # Scripts should have rollback
        for script in table_scripts:
            assert script.rollback_script is not None

    @pytest.mark.asyncio
    async def test_deploy_schema_without_analysis(self, service, session):
        """Test deployment without prior analysis raises error."""
        with pytest.raises(ValueError):
            await service.deploy_schema(session.session_id, target_connection={})


# ==================== Dual-Write Tests ====================

class TestDualWrite:
    """Test dual-write functionality."""

    @pytest.mark.asyncio
    async def test_setup_dual_write(self, service, session):
        """Test dual-write setup."""
        await service.analyze_schema(session.session_id, source_connection={})

        config = DualWriteConfig(mode=DualWriteMode.SYNC)
        status = await service.setup_dual_write(session.session_id, config)

        assert isinstance(status, DualWriteStatus)
        assert status.mode == DualWriteMode.SYNC
        assert status.active_since is not None

    @pytest.mark.asyncio
    async def test_get_dual_write_status(self, service, session):
        """Test getting dual-write status."""
        await service.analyze_schema(session.session_id, source_connection={})

        config = DualWriteConfig(mode=DualWriteMode.ASYNC)
        await service.setup_dual_write(session.session_id, config)

        status = await service.get_dual_write_status(session.session_id)
        assert status.mode == DualWriteMode.ASYNC

    @pytest.mark.asyncio
    async def test_disable_dual_write(self, service, session):
        """Test disabling dual-write."""
        await service.analyze_schema(session.session_id, source_connection={})

        config = DualWriteConfig(mode=DualWriteMode.SYNC)
        await service.setup_dual_write(session.session_id, config)

        result = await service.disable_dual_write(session.session_id)
        assert result is True

        status = await service.get_dual_write_status(session.session_id)
        assert status.mode == DualWriteMode.OFF


class TestDualWriteStatus:
    """Test DualWriteStatus dataclass."""

    def test_is_healthy_true(self):
        """Test is_healthy when status is good."""
        status = DualWriteStatus(
            mode=DualWriteMode.SYNC,
            errors=0,
            current_lag_seconds=100
        )
        assert status.is_healthy is True

    def test_is_healthy_false_errors(self):
        """Test is_healthy when there are errors."""
        status = DualWriteStatus(
            mode=DualWriteMode.SYNC,
            errors=1,
            current_lag_seconds=0
        )
        assert status.is_healthy is False

    def test_is_healthy_false_high_lag(self):
        """Test is_healthy when lag is too high."""
        status = DualWriteStatus(
            mode=DualWriteMode.SYNC,
            errors=0,
            current_lag_seconds=500
        )
        assert status.is_healthy is False


# ==================== Data Sync Tests ====================

class TestDataSync:
    """Test data synchronization functionality."""

    @pytest.mark.asyncio
    async def test_sync_data(self, service, session):
        """Test data synchronization."""
        await service.analyze_schema(session.session_id, source_connection={})

        stats = await service.sync_data(session.session_id)

        assert "tables_synced" in stats
        assert "total_rows" in stats
        assert stats["tables_synced"] > 0

    @pytest.mark.asyncio
    async def test_sync_specific_tables(self, service, session):
        """Test syncing specific tables only."""
        await service.analyze_schema(session.session_id, source_connection={})

        stats = await service.sync_data(
            session.session_id,
            tables=["CUSTOMERS"]
        )

        assert stats["tables_synced"] == 1


# ==================== Validation Tests ====================

class TestValidation:
    """Test data validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_data(self, service, session):
        """Test data validation."""
        await service.analyze_schema(session.session_id, source_connection={})

        results = await service.validate_data(
            session.session_id,
            level=ValidationLevel.CHECKSUM
        )

        assert len(results) > 0
        assert all(isinstance(r, ValidationResult) for r in results)

    @pytest.mark.asyncio
    async def test_validation_summary(self, service, session):
        """Test validation summary generation."""
        await service.analyze_schema(session.session_id, source_connection={})
        await service.validate_data(session.session_id)

        summary = service.get_validation_summary(session.session_id)

        assert "total_tables" in summary
        assert "passed" in summary
        assert "pass_rate" in summary


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_is_valid_true(self):
        """Test is_valid when all checks pass."""
        result = ValidationResult(
            table_name="test",
            validation_level=ValidationLevel.CHECKSUM,
            source_count=100,
            target_count=100,
            mismatched_rows=0,
            missing_in_target=0,
            checksum_match=True
        )
        assert result.is_valid is True

    def test_is_valid_false_count_mismatch(self):
        """Test is_valid when counts don't match."""
        result = ValidationResult(
            table_name="test",
            validation_level=ValidationLevel.CHECKSUM,
            source_count=100,
            target_count=99,
            checksum_match=True
        )
        assert result.is_valid is False

    def test_is_valid_false_checksum_mismatch(self):
        """Test is_valid when checksums don't match."""
        result = ValidationResult(
            table_name="test",
            validation_level=ValidationLevel.CHECKSUM,
            source_count=100,
            target_count=100,
            checksum_match=False
        )
        assert result.is_valid is False


# ==================== Cutover Tests ====================

class TestCutover:
    """Test cutover functionality."""

    @pytest.mark.asyncio
    async def test_cutover_requires_confirmation(self, service, session):
        """Test that cutover requires explicit confirmation."""
        await service.analyze_schema(session.session_id, source_connection={})
        await service.validate_data(session.session_id)

        result = await service.execute_cutover(session.session_id, confirm=False)

        assert result["status"] == "confirmation_required"

    @pytest.mark.asyncio
    async def test_cutover_with_confirmation(self, service, session):
        """Test cutover with confirmation."""
        await service.analyze_schema(session.session_id, source_connection={})
        await service.validate_data(session.session_id)

        result = await service.execute_cutover(session.session_id, confirm=True)

        assert result["status"] == "cutover_complete"

    @pytest.mark.asyncio
    async def test_cutover_blocked_by_validation(self, service, session):
        """Test that cutover is blocked if validation fails."""
        await service.analyze_schema(session.session_id, source_connection={})

        # Add a failing validation result
        session_obj = service.get_session(session.session_id)
        session_obj.validation_results = [
            ValidationResult(
                table_name="test",
                validation_level=ValidationLevel.CHECKSUM,
                source_count=100,
                target_count=99  # Mismatch
            )
        ]

        with pytest.raises(ValueError, match="validation not 100% passed"):
            await service.execute_cutover(session.session_id, confirm=True)


# ==================== Cleanup Tests ====================

class TestCleanup:
    """Test cleanup functionality."""

    @pytest.mark.asyncio
    async def test_cleanup(self, service, session):
        """Test cleanup after migration."""
        await service.analyze_schema(session.session_id, source_connection={})
        await service.validate_data(session.session_id)
        await service.execute_cutover(session.session_id, confirm=True)

        result = await service.cleanup(session.session_id)

        assert result["status"] == "cleanup_complete"
        assert "duration_hours" in result

    @pytest.mark.asyncio
    async def test_cleanup_disables_dual_write(self, service, session):
        """Test that cleanup disables dual-write."""
        await service.analyze_schema(session.session_id, source_connection={})

        config = DualWriteConfig(mode=DualWriteMode.SYNC)
        await service.setup_dual_write(session.session_id, config)
        await service.validate_data(session.session_id)
        await service.execute_cutover(session.session_id, confirm=True)
        await service.cleanup(session.session_id)

        status = await service.get_dual_write_status(session.session_id)
        assert status.mode == DualWriteMode.OFF


# ==================== Utility Method Tests ====================

class TestUtilityMethods:
    """Test utility methods."""

    def test_get_type_mapping(self, service):
        """Test type mapping retrieval."""
        mapping = service.get_type_mapping("oracle", "postgresql", "VARCHAR2")

        assert mapping is not None
        assert mapping.target_type == "VARCHAR"

    def test_get_type_mapping_case_insensitive(self, service):
        """Test type mapping is case-insensitive."""
        mapping = service.get_type_mapping("Oracle", "PostgreSQL", "varchar2")

        assert mapping is not None

    def test_register_custom_type_mapping(self, service):
        """Test registering custom type mappings."""
        custom_mapping = DataTypeMapping(
            source_type="CUSTOM_TYPE",
            target_type="TEXT",
            category=DataTypeCategory.STRING,
            compatibility=CompatibilityLevel.FULL
        )

        service.register_type_mapping(
            "oracle",
            "postgresql",
            {"CUSTOM_TYPE": custom_mapping}
        )

        result = service.get_type_mapping("oracle", "postgresql", "CUSTOM_TYPE")
        assert result.target_type == "TEXT"

    def test_get_session_status(self, service, session):
        """Test getting session status."""
        status = service.get_session_status(session.session_id)

        assert status["session_id"] == session.session_id
        assert status["source_db"] == "oracle"
        assert status["target_db"] == "postgresql"
        assert status["phase"] == "analysis"

    def test_get_session_status_nonexistent(self, service):
        """Test getting status of non-existent session."""
        status = service.get_session_status("nonexistent")
        assert "error" in status


# ==================== Factory Function Tests ====================

class TestFactoryFunction:
    """Test factory function."""

    def test_create_database_first_service(self):
        """Test factory function creates service correctly."""
        service = create_database_first_service()

        assert isinstance(service, DatabaseFirstMigrationService)
        assert service.VERSION == "1.0.0"


# ==================== Integration Tests ====================

class TestFullMigrationWorkflow:
    """Test complete migration workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, service):
        """Test complete database-first migration workflow."""
        # 1. Create session
        session = service.create_session("oracle", "postgresql")
        assert session.phase == MigrationPhase.ANALYSIS

        # 2. Analyze schema
        analysis = await service.analyze_schema(
            session.session_id,
            source_connection={"host": "legacy-db"}
        )
        assert analysis.is_migratable

        # 3. Deploy schema
        scripts = await service.deploy_schema(
            session.session_id,
            target_connection={"host": "new-db"},
            dry_run=True
        )
        assert len(scripts) > 0

        # 4. Setup dual-write
        config = DualWriteConfig(mode=DualWriteMode.SYNC)
        status = await service.setup_dual_write(session.session_id, config)
        assert status.mode == DualWriteMode.SYNC

        # 5. Sync data
        sync_stats = await service.sync_data(session.session_id)
        assert sync_stats["tables_synced"] > 0

        # 6. Validate data
        validations = await service.validate_data(session.session_id)
        assert all(v.is_valid for v in validations)

        # 7. Execute cutover
        cutover = await service.execute_cutover(session.session_id, confirm=True)
        assert cutover["status"] == "cutover_complete"

        # 8. Cleanup
        cleanup = await service.cleanup(session.session_id)
        assert cleanup["status"] == "cleanup_complete"

        # Verify final state
        final_session = service.get_session(session.session_id)
        assert final_session.is_complete
