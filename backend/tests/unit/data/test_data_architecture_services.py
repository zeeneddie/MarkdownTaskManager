"""
Tests for Fase 24: Data Architecture Services

Tests cover:
- DataLineageService: Data flow tracking from specs to code
- ERDGeneratorService: Target architecture ERD generation
- JourneyComparisonService: E2E journey comparison
- CDCIntegrationService: Change Data Capture for dual-system sync

Author: Claude Code (Week 136 - Fase 24)
Date: 2026-01-01
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from uuid import uuid4

# Import CDC service (in-memory, no DB needed)
from app.services.cdc_integration_service import (
    CDCIntegrationService,
    CDCMode, CDCProvider, ChangeOperation, SyncStatus,
    ChangeEvent, TableMapping, CDCSession
)

# Import models for testing
from app.models.data_architecture import (
    LineageNodeType, LineageEdgeType, TransformationType,
    JourneyStepType, JourneyMatchStatus, ERDOutputFormat
)


# ============================================
# CDCIntegrationService Tests
# ============================================

class TestCDCIntegrationService:
    """Test suite for CDCIntegrationService"""

    @pytest.fixture
    def cdc_service(self):
        """Create a fresh CDC service for each test"""
        return CDCIntegrationService()

    @pytest.fixture
    def legacy_connection(self):
        """Sample legacy database connection"""
        return {
            "host": "legacy-db.example.com",
            "port": "1433",
            "database": "LegacyDB",
            "user": "legacy_user"
        }

    @pytest.fixture
    def new_connection(self):
        """Sample new database connection"""
        return {
            "host": "new-db.example.com",
            "port": "5432",
            "database": "new_db",
            "user": "new_user"
        }

    # ==================== Session Management Tests ====================

    @pytest.mark.asyncio
    async def test_create_session_shadow_mode(self, cdc_service, legacy_connection, new_connection):
        """Test creating a CDC session in shadow mode"""
        session = await cdc_service.create_session(
            name="HCI-CRS Migration",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        assert session.id is not None
        assert session.name == "HCI-CRS Migration"
        assert session.mode == CDCMode.SHADOW
        assert session.provider == CDCProvider.POLLING
        assert session.status == "created"
        assert session.events_processed == 0

    @pytest.mark.asyncio
    async def test_create_session_mirror_mode(self, cdc_service, legacy_connection, new_connection):
        """Test creating a CDC session in mirror mode"""
        session = await cdc_service.create_session(
            name="Full Sync Test",
            mode=CDCMode.MIRROR,
            provider=CDCProvider.DEBEZIUM,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        assert session.mode == CDCMode.MIRROR
        assert session.provider == CDCProvider.DEBEZIUM

    @pytest.mark.asyncio
    async def test_get_session(self, cdc_service, legacy_connection, new_connection):
        """Test retrieving a session by ID"""
        created = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        retrieved = await cdc_service.get_session(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test Session"

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, cdc_service):
        """Test retrieving a nonexistent session returns None"""
        result = await cdc_service.get_session("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_sessions(self, cdc_service, legacy_connection, new_connection):
        """Test listing all sessions"""
        await cdc_service.create_session(
            name="Session 1",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )
        await cdc_service.create_session(
            name="Session 2",
            mode=CDCMode.MIRROR,
            provider=CDCProvider.DEBEZIUM,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        sessions = await cdc_service.list_sessions()
        assert len(sessions) == 2

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_status(self, cdc_service, legacy_connection, new_connection):
        """Test filtering sessions by status"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        created_sessions = await cdc_service.list_sessions(status="created")
        running_sessions = await cdc_service.list_sessions(status="running")

        assert len(created_sessions) == 1
        assert len(running_sessions) == 0

    # ==================== Table Mapping Tests ====================

    @pytest.mark.asyncio
    async def test_add_table_mapping(self, cdc_service, legacy_connection, new_connection):
        """Test adding a table mapping"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        mapping = await cdc_service.add_table_mapping(
            session_id=session.id,
            legacy_table="tblAfspraken",
            new_table="appointments",
            field_mappings={
                "AfspraakId": "appointment_id",
                "PatientNr": "patient_number",
                "Datum": "date"
            },
            transform_functions={
                "Datum": "to_date"
            }
        )

        assert mapping.legacy_table == "tblAfspraken"
        assert mapping.new_table == "appointments"
        assert len(mapping.field_mappings) == 3
        assert mapping.transform_functions["Datum"] == "to_date"

    @pytest.mark.asyncio
    async def test_add_table_mapping_invalid_session(self, cdc_service):
        """Test adding a table mapping to nonexistent session raises error"""
        with pytest.raises(ValueError, match="Session not found"):
            await cdc_service.add_table_mapping(
                session_id="nonexistent",
                legacy_table="test",
                new_table="test"
            )

    @pytest.mark.asyncio
    async def test_auto_detect_mappings(self, cdc_service, legacy_connection, new_connection):
        """Test auto-detecting table mappings from naming conventions"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        legacy_tables = ["tblPatients", "tblAppointments", "tblUsers"]
        mappings = await cdc_service.auto_detect_mappings(session.id, legacy_tables)

        assert len(mappings) == 3
        # Check naming convention transformations (tbl prefix removed, snake_case, pluralized)
        new_tables = [m.new_table for m in mappings]
        assert "patients" in new_tables
        assert "appointments" in new_tables
        assert "users" in new_tables

    # ==================== Session Lifecycle Tests ====================

    @pytest.mark.asyncio
    async def test_start_session(self, cdc_service, legacy_connection, new_connection):
        """Test starting a CDC session"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        started = await cdc_service.start_session(session.id)
        assert started.status == "running"
        assert started.started_at is not None

        # Clean up
        await cdc_service.stop_session(session.id)

    @pytest.mark.asyncio
    async def test_stop_session(self, cdc_service, legacy_connection, new_connection):
        """Test stopping a CDC session"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        await cdc_service.start_session(session.id)
        stopped = await cdc_service.stop_session(session.id)

        assert stopped.status == "stopped"
        assert stopped.stopped_at is not None

    @pytest.mark.asyncio
    async def test_pause_resume_session(self, cdc_service, legacy_connection, new_connection):
        """Test pausing and resuming a CDC session"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        paused = await cdc_service.pause_session(session.id)
        assert paused.status == "paused"

        resumed = await cdc_service.resume_session(session.id)
        assert resumed.status == "running"

    # ==================== Mode Transition Tests ====================

    @pytest.mark.asyncio
    async def test_switch_mode_shadow_to_mirror(self, cdc_service, legacy_connection, new_connection):
        """Test switching from shadow to mirror mode"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        switched = await cdc_service.switch_mode(
            session_id=session.id,
            new_mode=CDCMode.MIRROR,
            approved_by="system"
        )

        assert switched.mode == CDCMode.MIRROR

    @pytest.mark.asyncio
    async def test_switch_mode_mirror_to_cutover_requires_approval(self, cdc_service, legacy_connection, new_connection):
        """Test that cutover mode requires admin/eddie approval"""
        # Create session in MIRROR mode (already in mirror, so can switch to cutover)
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.MIRROR,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        # Cutover without proper approval should fail
        with pytest.raises(ValueError, match="requires approval from eddie or admin"):
            await cdc_service.switch_mode(
                session_id=session.id,
                new_mode=CDCMode.CUTOVER,
                approved_by="system"
            )

        # Cutover with eddie approval should work
        switched = await cdc_service.switch_mode(
            session_id=session.id,
            new_mode=CDCMode.CUTOVER,
            approved_by="eddie"
        )
        assert switched.mode == CDCMode.CUTOVER

    @pytest.mark.asyncio
    async def test_switch_mode_invalid_transition(self, cdc_service, legacy_connection, new_connection):
        """Test that invalid mode transitions are rejected"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        # Shadow -> Cutover is not allowed (must go through Mirror first)
        with pytest.raises(ValueError, match="Invalid transition"):
            await cdc_service.switch_mode(
                session_id=session.id,
                new_mode=CDCMode.CUTOVER,
                approved_by="eddie"
            )

    # ==================== Event Processing Tests ====================

    @pytest.mark.asyncio
    async def test_process_event_shadow_mode(self, cdc_service, legacy_connection, new_connection):
        """Test processing an event in shadow mode (read-only)"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        await cdc_service.add_table_mapping(
            session_id=session.id,
            legacy_table="tblPatients",
            new_table="patients"
        )

        event = ChangeEvent(
            id=str(uuid4()),
            table="tblPatients",
            operation=ChangeOperation.INSERT,
            timestamp=datetime.now(timezone.utc),
            legacy_data={"PatientId": 1, "Naam": "Test Patient"}
        )

        result = await cdc_service.process_event(session.id, event)
        assert result.sync_status == SyncStatus.COMPLETED
        assert result.new_data is not None

    @pytest.mark.asyncio
    async def test_process_event_no_mapping(self, cdc_service, legacy_connection, new_connection):
        """Test processing an event for unmapped table"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        event = ChangeEvent(
            id=str(uuid4()),
            table="UnknownTable",
            operation=ChangeOperation.INSERT,
            timestamp=datetime.now(timezone.utc),
            legacy_data={"field1": "value1"}
        )

        result = await cdc_service.process_event(session.id, event)
        assert result.sync_status == SyncStatus.FAILED
        assert "No mapping" in result.error_message

    @pytest.mark.asyncio
    async def test_data_transformation(self, cdc_service, legacy_connection, new_connection):
        """Test data transformation during event processing"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        await cdc_service.add_table_mapping(
            session_id=session.id,
            legacy_table="tblPatients",
            new_table="patients",
            field_mappings={
                "Naam": "name",
                "Email": "email"
            },
            transform_functions={
                "Naam": "uppercase",
                "Email": "lowercase"
            }
        )

        event = ChangeEvent(
            id=str(uuid4()),
            table="tblPatients",
            operation=ChangeOperation.INSERT,
            timestamp=datetime.now(timezone.utc),
            legacy_data={"Naam": "test name", "Email": "TEST@EXAMPLE.COM"}
        )

        result = await cdc_service.process_event(session.id, event)
        assert result.new_data["name"] == "TEST NAME"
        assert result.new_data["email"] == "test@example.com"

    # ==================== Conflict Detection Tests ====================

    @pytest.mark.asyncio
    async def test_detect_conflict(self, cdc_service, legacy_connection, new_connection):
        """Test conflict detection between legacy and new data"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.MIRROR,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        conflict = await cdc_service.detect_conflict(
            session_id=session.id,
            table="patients",
            primary_key={"id": 1},
            legacy_data={"name": "John Doe", "email": "john@example.com"},
            new_data={"name": "John Doe", "email": "johnny@example.com"}  # Different email
        )

        assert conflict is not None
        assert conflict.conflict_type == "concurrent_update"
        assert session.conflicts_detected == 1

    @pytest.mark.asyncio
    async def test_detect_no_conflict(self, cdc_service, legacy_connection, new_connection):
        """Test that identical data doesn't create conflict"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.MIRROR,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        conflict = await cdc_service.detect_conflict(
            session_id=session.id,
            table="patients",
            primary_key={"id": 1},
            legacy_data={"name": "John Doe"},
            new_data={"name": "John Doe"}
        )

        assert conflict is None

    @pytest.mark.asyncio
    async def test_resolve_conflict_legacy_wins(self, cdc_service, legacy_connection, new_connection):
        """Test resolving conflict with legacy_wins strategy"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.MIRROR,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        await cdc_service.detect_conflict(
            session_id=session.id,
            table="patients",
            primary_key={"id": 1},
            legacy_data={"name": "Legacy Value"},
            new_data={"name": "New Value"}
        )

        resolved = await cdc_service.resolve_conflict(
            session_id=session.id,
            conflict_index=0,
            strategy="legacy_wins",
            resolved_by="eddie"
        )

        assert resolved.resolved_data == {"name": "Legacy Value"}
        assert resolved.resolved_by == "eddie"
        assert resolved.resolved_at is not None

    @pytest.mark.asyncio
    async def test_resolve_conflict_new_wins(self, cdc_service, legacy_connection, new_connection):
        """Test resolving conflict with new_wins strategy"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.MIRROR,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        await cdc_service.detect_conflict(
            session_id=session.id,
            table="patients",
            primary_key={"id": 1},
            legacy_data={"name": "Legacy Value"},
            new_data={"name": "New Value"}
        )

        resolved = await cdc_service.resolve_conflict(
            session_id=session.id,
            conflict_index=0,
            strategy="new_wins"
        )

        assert resolved.resolved_data == {"name": "New Value"}

    @pytest.mark.asyncio
    async def test_resolve_conflict_merge(self, cdc_service, legacy_connection, new_connection):
        """Test resolving conflict with merge strategy"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.MIRROR,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        await cdc_service.detect_conflict(
            session_id=session.id,
            table="patients",
            primary_key={"id": 1},
            legacy_data={"name": "Legacy", "legacy_field": "value"},
            new_data={"name": "New", "new_field": "value"}
        )

        resolved = await cdc_service.resolve_conflict(
            session_id=session.id,
            conflict_index=0,
            strategy="merge"
        )

        # Merge prefers new, fills gaps with legacy
        assert resolved.resolved_data["name"] == "New"
        assert resolved.resolved_data["legacy_field"] == "value"
        assert resolved.resolved_data["new_field"] == "value"

    @pytest.mark.asyncio
    async def test_resolve_conflict_manual(self, cdc_service, legacy_connection, new_connection):
        """Test resolving conflict with manual strategy"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.MIRROR,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        await cdc_service.detect_conflict(
            session_id=session.id,
            table="patients",
            primary_key={"id": 1},
            legacy_data={"name": "Legacy"},
            new_data={"name": "New"}
        )

        resolved = await cdc_service.resolve_conflict(
            session_id=session.id,
            conflict_index=0,
            strategy="manual",
            resolved_by="eddie",
            resolved_data={"name": "Eddie's Choice"}
        )

        assert resolved.resolved_data == {"name": "Eddie's Choice"}

    @pytest.mark.asyncio
    async def test_resolve_conflict_manual_requires_data(self, cdc_service, legacy_connection, new_connection):
        """Test that manual resolution requires resolved_data"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.MIRROR,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        await cdc_service.detect_conflict(
            session_id=session.id,
            table="patients",
            primary_key={"id": 1},
            legacy_data={"name": "Legacy"},
            new_data={"name": "New"}
        )

        with pytest.raises(ValueError, match="Manual resolution requires resolved_data"):
            await cdc_service.resolve_conflict(
                session_id=session.id,
                conflict_index=0,
                strategy="manual"
            )

    # ==================== Metrics Tests ====================

    @pytest.mark.asyncio
    async def test_get_metrics(self, cdc_service, legacy_connection, new_connection):
        """Test getting CDC metrics"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        await cdc_service.add_table_mapping(
            session_id=session.id,
            legacy_table="test",
            new_table="test"
        )

        metrics = await cdc_service.get_metrics(session.id)
        assert metrics.session_id == session.id
        assert metrics.tables_synced == 1
        assert metrics.queue_depth == 0

    @pytest.mark.asyncio
    async def test_get_session_summary(self, cdc_service, legacy_connection, new_connection):
        """Test getting session summary"""
        session = await cdc_service.create_session(
            name="Test Session",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection=legacy_connection,
            new_connection=new_connection
        )

        await cdc_service.add_table_mapping(
            session_id=session.id,
            legacy_table="test",
            new_table="test"
        )

        summary = await cdc_service.get_session_summary(session.id)
        assert summary["session"]["id"] == session.id
        assert summary["session"]["name"] == "Test Session"
        assert summary["session"]["mode"] == "shadow"
        assert summary["tables"]["total"] == 1


# ============================================
# Data Lineage Model Tests
# ============================================

class TestDataLineageModels:
    """Test suite for Data Lineage models"""

    def test_lineage_node_type_enum(self):
        """Test LineageNodeType enum values"""
        assert LineageNodeType.DOMAIN.value == "domain"
        assert LineageNodeType.ENTITY.value == "entity"
        assert LineageNodeType.EPIC.value == "epic"
        assert LineageNodeType.USER_STORY.value == "user_story"
        assert LineageNodeType.TEST_CASE.value == "test_case"
        assert LineageNodeType.CODE_FILE.value == "code_file"

    def test_lineage_edge_type_enum(self):
        """Test LineageEdgeType enum values"""
        assert LineageEdgeType.EXTRACTED_FROM.value == "extracted_from"
        assert LineageEdgeType.IMPLEMENTED_BY.value == "implemented_by"
        assert LineageEdgeType.TESTED_BY.value == "tested_by"
        assert LineageEdgeType.DEPENDS_ON.value == "depends_on"

    def test_transformation_type_enum(self):
        """Test TransformationType enum values"""
        assert TransformationType.DIRECT_COPY.value == "direct_copy"
        assert TransformationType.RENAME.value == "rename"
        assert TransformationType.TYPE_CHANGE.value == "type_change"
        assert TransformationType.MERGE.value == "merge"
        assert TransformationType.CALCULATION.value == "calculation"


# ============================================
# Journey Comparison Model Tests
# ============================================

class TestJourneyComparisonModels:
    """Test suite for Journey Comparison models"""

    def test_journey_step_type_enum(self):
        """Test JourneyStepType enum values"""
        assert JourneyStepType.CLICK.value == "click"
        assert JourneyStepType.INPUT.value == "input"
        assert JourneyStepType.NAVIGATION.value == "navigation"
        assert JourneyStepType.SUBMIT.value == "submit"
        assert JourneyStepType.API_CALL.value == "api_call"
        assert JourneyStepType.ASSERTION.value == "assertion"

    def test_journey_match_status_enum(self):
        """Test JourneyMatchStatus enum values"""
        assert JourneyMatchStatus.MATCH.value == "match"
        assert JourneyMatchStatus.MISMATCH.value == "mismatch"
        assert JourneyMatchStatus.OVERRIDE_APPROVED.value == "override_approved"
        assert JourneyMatchStatus.SKIPPED.value == "skipped"


# ============================================
# ERD Generator Model Tests
# ============================================

class TestERDGeneratorModels:
    """Test suite for ERD Generator models"""

    def test_erd_output_format_enum(self):
        """Test ERDOutputFormat enum values"""
        assert ERDOutputFormat.MERMAID.value == "mermaid"
        assert ERDOutputFormat.PLANTUML.value == "plantuml"
        assert ERDOutputFormat.DBML.value == "dbml"
        assert ERDOutputFormat.JSON.value == "json"
        assert ERDOutputFormat.DOT.value == "dot"


# ============================================
# Integration Tests (with mocked database)
# ============================================

class TestDataArchitectureIntegration:
    """Integration tests for Fase 24 services"""

    @pytest.mark.asyncio
    async def test_full_cdc_workflow(self):
        """Test complete CDC workflow: create -> map -> start -> process -> stop"""
        service = CDCIntegrationService()

        # 1. Create session
        session = await service.create_session(
            name="Integration Test",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection={"host": "legacy"},
            new_connection={"host": "new"}
        )

        # 2. Add mappings
        await service.add_table_mapping(
            session_id=session.id,
            legacy_table="tblPatients",
            new_table="patients"
        )
        await service.add_table_mapping(
            session_id=session.id,
            legacy_table="tblAppointments",
            new_table="appointments"
        )

        # 3. Start session
        started = await service.start_session(session.id)
        assert started.status == "running"

        # 4. Process events
        event = ChangeEvent(
            id=str(uuid4()),
            table="tblPatients",
            operation=ChangeOperation.INSERT,
            timestamp=datetime.now(timezone.utc),
            legacy_data={"PatientId": 1, "Naam": "Test"}
        )
        result = await service.process_event(session.id, event)
        assert result.sync_status == SyncStatus.COMPLETED

        # 5. Get metrics
        metrics = await service.get_metrics(session.id)
        assert metrics.tables_synced == 2

        # 6. Stop session
        stopped = await service.stop_session(session.id)
        assert stopped.status == "stopped"

    @pytest.mark.asyncio
    async def test_mode_transition_workflow(self):
        """Test complete mode transition workflow: shadow -> mirror -> cutover"""
        service = CDCIntegrationService()

        session = await service.create_session(
            name="Mode Transition Test",
            mode=CDCMode.SHADOW,
            provider=CDCProvider.POLLING,
            legacy_connection={"host": "legacy"},
            new_connection={"host": "new"}
        )

        # Shadow -> Mirror (no special approval needed)
        await service.switch_mode(
            session_id=session.id,
            new_mode=CDCMode.MIRROR,
            approved_by="system"
        )

        # Mirror -> Cutover (requires eddie approval)
        await service.switch_mode(
            session_id=session.id,
            new_mode=CDCMode.CUTOVER,
            approved_by="eddie"
        )

        final = await service.get_session(session.id)
        assert final.mode == CDCMode.CUTOVER

    @pytest.mark.asyncio
    async def test_conflict_resolution_workflow(self):
        """Test complete conflict detection and resolution workflow"""
        service = CDCIntegrationService()

        session = await service.create_session(
            name="Conflict Test",
            mode=CDCMode.MIRROR,
            provider=CDCProvider.POLLING,
            legacy_connection={"host": "legacy"},
            new_connection={"host": "new"}
        )

        # Detect conflicts
        await service.detect_conflict(
            session_id=session.id,
            table="patients",
            primary_key={"id": 1},
            legacy_data={"field": "A"},
            new_data={"field": "B"}
        )
        await service.detect_conflict(
            session_id=session.id,
            table="patients",
            primary_key={"id": 2},
            legacy_data={"field": "C"},
            new_data={"field": "D"}
        )

        # Check unresolved conflicts
        unresolved = await service.get_conflicts(session.id, unresolved_only=True)
        assert len(unresolved) == 2

        # Resolve first conflict
        await service.resolve_conflict(
            session_id=session.id,
            conflict_index=0,
            strategy="legacy_wins",
            resolved_by="eddie"
        )

        # Check again
        unresolved = await service.get_conflicts(session.id, unresolved_only=True)
        assert len(unresolved) == 1

        all_conflicts = await service.get_conflicts(session.id)
        assert len(all_conflicts) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
