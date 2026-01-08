"""
CDC Integration Service - Change Data Capture for Dual-System Sync

Part of Fase 24: Data Architecture (Week 136-137)

Enables synchronization between legacy and new systems during migration:
- Shadow mode: new system receives data, no writes
- Mirror mode: full sync, writes allowed
- Cutover support: switch from legacy to new

Supports integration with:
- Debezium (Kafka-based CDC)
- AWS DMS (Database Migration Service)
- Custom polling (for systems without native CDC)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class CDCMode(str, Enum):
    """CDC operation modes"""
    SHADOW = "shadow"           # Read-only, new system receives data
    MIRROR = "mirror"           # Full sync, writes allowed
    CUTOVER = "cutover"         # Switch primary from legacy to new
    ROLLBACK = "rollback"       # Revert to legacy as primary


class CDCProvider(str, Enum):
    """Supported CDC providers"""
    DEBEZIUM = "debezium"       # Kafka-based CDC (PostgreSQL, MySQL, SQL Server)
    AWS_DMS = "aws_dms"         # AWS Database Migration Service
    POLLING = "polling"         # Custom polling (fallback for any database)
    TRIGGER = "trigger"         # Database trigger-based CDC


class ChangeOperation(str, Enum):
    """Types of data changes"""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    SNAPSHOT = "snapshot"       # Initial data load


class SyncStatus(str, Enum):
    """Synchronization status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


@dataclass
class ChangeEvent:
    """Represents a single data change event"""
    id: str
    table: str
    operation: ChangeOperation
    timestamp: datetime
    legacy_data: Dict[str, Any]
    new_data: Optional[Dict[str, Any]] = None
    primary_key: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "1.0"
    source_lsn: Optional[str] = None  # Log Sequence Number
    sync_status: SyncStatus = SyncStatus.PENDING
    error_message: Optional[str] = None
    retries: int = 0


@dataclass
class TableMapping:
    """Maps legacy table to new table with field transformations"""
    legacy_table: str
    new_table: str
    legacy_schema: str = "dbo"
    new_schema: str = "public"
    field_mappings: Dict[str, str] = field(default_factory=dict)  # legacy -> new
    transform_functions: Dict[str, str] = field(default_factory=dict)  # field -> transform
    filter_condition: Optional[str] = None  # SQL WHERE clause
    enabled: bool = True
    priority: int = 100  # Lower = higher priority


@dataclass
class ConflictResolution:
    """Conflict resolution strategy"""
    table: str
    conflict_type: str  # "concurrent_update", "missing_parent", "constraint_violation"
    resolution_strategy: str  # "legacy_wins", "new_wins", "manual", "merge"
    legacy_data: Dict[str, Any]
    new_data: Dict[str, Any]
    resolved_data: Optional[Dict[str, Any]] = None
    resolved_by: Optional[str] = None  # "auto", "eddie", etc.
    resolved_at: Optional[datetime] = None


@dataclass
class CDCSession:
    """Represents a CDC synchronization session"""
    id: str
    name: str
    mode: CDCMode
    provider: CDCProvider
    legacy_connection: Dict[str, str]
    new_connection: Dict[str, str]
    table_mappings: List[TableMapping] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    status: str = "created"  # created, running, paused, stopped, failed
    last_lsn: Optional[str] = None
    events_processed: int = 0
    events_failed: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0


@dataclass
class CDCMetrics:
    """Real-time CDC metrics"""
    session_id: str
    timestamp: datetime
    events_per_second: float
    latency_ms: float
    queue_depth: int
    tables_synced: int
    tables_pending: int
    bytes_transferred: int
    errors_last_hour: int


class CDCIntegrationService:
    """
    Change Data Capture Integration Service

    Enables dual-system synchronization during migration with:
    - Multiple CDC providers (Debezium, AWS DMS, Polling)
    - Shadow mode for read-only testing
    - Mirror mode for full sync
    - Cutover support for going live
    - Conflict detection and resolution
    """

    def __init__(self):
        self.sessions: Dict[str, CDCSession] = {}
        self.events: Dict[str, List[ChangeEvent]] = {}  # session_id -> events
        self.conflicts: Dict[str, List[ConflictResolution]] = {}
        self.metrics: Dict[str, List[CDCMetrics]] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}

    # ==================== Session Management ====================

    async def create_session(
        self,
        name: str,
        mode: CDCMode,
        provider: CDCProvider,
        legacy_connection: Dict[str, str],
        new_connection: Dict[str, str],
        table_mappings: Optional[List[TableMapping]] = None
    ) -> CDCSession:
        """Create a new CDC session"""
        session = CDCSession(
            id=str(uuid4()),
            name=name,
            mode=mode,
            provider=provider,
            legacy_connection=legacy_connection,
            new_connection=new_connection,
            table_mappings=table_mappings or []
        )

        self.sessions[session.id] = session
        self.events[session.id] = []
        self.conflicts[session.id] = []
        self.metrics[session.id] = []

        logger.info(f"Created CDC session: {session.id} ({name}) in {mode.value} mode")
        return session

    async def get_session(self, session_id: str) -> Optional[CDCSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    async def list_sessions(self, status: Optional[str] = None) -> List[CDCSession]:
        """List all sessions, optionally filtered by status"""
        sessions = list(self.sessions.values())
        if status:
            sessions = [s for s in sessions if s.status == status]
        return sessions

    # ==================== Table Mapping ====================

    async def add_table_mapping(
        self,
        session_id: str,
        legacy_table: str,
        new_table: str,
        field_mappings: Optional[Dict[str, str]] = None,
        transform_functions: Optional[Dict[str, str]] = None
    ) -> TableMapping:
        """Add a table mapping to the session"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        mapping = TableMapping(
            legacy_table=legacy_table,
            new_table=new_table,
            field_mappings=field_mappings or {},
            transform_functions=transform_functions or {}
        )

        session.table_mappings.append(mapping)
        logger.info(f"Added table mapping: {legacy_table} -> {new_table}")
        return mapping

    async def auto_detect_mappings(
        self,
        session_id: str,
        legacy_tables: List[str]
    ) -> List[TableMapping]:
        """Auto-detect table mappings based on naming conventions"""
        mappings = []

        for legacy_table in legacy_tables:
            # Common naming convention transformations
            new_table = legacy_table.lower()

            # Handle common prefixes
            if new_table.startswith("tbl_"):
                new_table = new_table[4:]
            if new_table.startswith("tbl"):
                new_table = new_table[3:]

            # Convert CamelCase to snake_case
            import re
            new_table = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', new_table)
            new_table = re.sub('([a-z0-9])([A-Z])', r'\1_\2', new_table).lower()

            # Pluralize if not already plural
            if not new_table.endswith('s'):
                new_table = f"{new_table}s"

            mapping = await self.add_table_mapping(
                session_id=session_id,
                legacy_table=legacy_table,
                new_table=new_table
            )
            mappings.append(mapping)

        return mappings

    # ==================== CDC Operations ====================

    async def start_session(self, session_id: str) -> CDCSession:
        """Start CDC synchronization"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.status = "running"
        session.started_at = datetime.now(timezone.utc)

        # Start the appropriate CDC provider
        if session.provider == CDCProvider.DEBEZIUM:
            task = asyncio.create_task(self._run_debezium_cdc(session))
        elif session.provider == CDCProvider.AWS_DMS:
            task = asyncio.create_task(self._run_aws_dms_cdc(session))
        elif session.provider == CDCProvider.POLLING:
            task = asyncio.create_task(self._run_polling_cdc(session))
        else:
            task = asyncio.create_task(self._run_trigger_cdc(session))

        self._running_tasks[session_id] = task
        logger.info(f"Started CDC session: {session_id}")
        return session

    async def stop_session(self, session_id: str) -> CDCSession:
        """Stop CDC synchronization"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.status = "stopped"
        session.stopped_at = datetime.now(timezone.utc)

        # Cancel the running task
        if session_id in self._running_tasks:
            self._running_tasks[session_id].cancel()
            del self._running_tasks[session_id]

        logger.info(f"Stopped CDC session: {session_id}")
        return session

    async def pause_session(self, session_id: str) -> CDCSession:
        """Pause CDC synchronization (maintains position)"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.status = "paused"
        logger.info(f"Paused CDC session: {session_id}")
        return session

    async def resume_session(self, session_id: str) -> CDCSession:
        """Resume paused CDC synchronization"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.status = "running"
        logger.info(f"Resumed CDC session: {session_id}")
        return session

    # ==================== Mode Transitions ====================

    async def switch_mode(
        self,
        session_id: str,
        new_mode: CDCMode,
        approved_by: str = "system"
    ) -> CDCSession:
        """
        Switch CDC mode (requires approval for cutover/rollback)

        Mode transitions:
        - SHADOW -> MIRROR: Enable writes to new system
        - MIRROR -> CUTOVER: New system becomes primary
        - CUTOVER -> ROLLBACK: Revert to legacy (emergency)
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        old_mode = session.mode

        # Validate transition
        valid_transitions = {
            CDCMode.SHADOW: [CDCMode.MIRROR],
            CDCMode.MIRROR: [CDCMode.CUTOVER, CDCMode.SHADOW],
            CDCMode.CUTOVER: [CDCMode.ROLLBACK],
            CDCMode.ROLLBACK: [CDCMode.SHADOW]
        }

        if new_mode not in valid_transitions.get(old_mode, []):
            raise ValueError(
                f"Invalid transition: {old_mode.value} -> {new_mode.value}. "
                f"Valid: {[m.value for m in valid_transitions.get(old_mode, [])]}"
            )

        # Critical transitions require explicit approval
        if new_mode in [CDCMode.CUTOVER, CDCMode.ROLLBACK]:
            if approved_by not in ["eddie", "admin"]:
                raise ValueError(
                    f"Cutover/rollback requires approval from eddie or admin. "
                    f"Got: {approved_by}"
                )

        session.mode = new_mode
        logger.info(
            f"CDC mode switched: {old_mode.value} -> {new_mode.value} "
            f"(approved by {approved_by})"
        )

        return session

    # ==================== Change Event Processing ====================

    async def process_event(
        self,
        session_id: str,
        event: ChangeEvent
    ) -> ChangeEvent:
        """Process a single change event"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        try:
            # Find table mapping
            mapping = next(
                (m for m in session.table_mappings
                 if m.legacy_table == event.table),
                None
            )

            if not mapping:
                logger.warning(f"No mapping for table: {event.table}")
                event.sync_status = SyncStatus.FAILED
                event.error_message = f"No mapping for table: {event.table}"
                return event

            # Transform data according to mapping
            transformed_data = self._transform_data(
                event.legacy_data,
                mapping.field_mappings,
                mapping.transform_functions
            )
            event.new_data = transformed_data

            # Apply based on mode
            if session.mode == CDCMode.SHADOW:
                # Read-only: just validate, don't write
                event.sync_status = SyncStatus.COMPLETED
                logger.debug(f"Shadow mode: validated {event.operation.value} on {event.table}")

            elif session.mode in [CDCMode.MIRROR, CDCMode.CUTOVER]:
                # Full sync: apply to new system
                await self._apply_to_new_system(session, mapping, event)
                event.sync_status = SyncStatus.COMPLETED
                session.events_processed += 1

            else:
                # Rollback mode: sync back to legacy
                await self._apply_to_legacy_system(session, mapping, event)
                event.sync_status = SyncStatus.COMPLETED

        except Exception as e:
            event.sync_status = SyncStatus.FAILED
            event.error_message = str(e)
            event.retries += 1
            session.events_failed += 1
            logger.error(f"Event processing failed: {e}")

        self.events[session_id].append(event)
        return event

    def _transform_data(
        self,
        data: Dict[str, Any],
        field_mappings: Dict[str, str],
        transform_functions: Dict[str, str]
    ) -> Dict[str, Any]:
        """Transform legacy data to new schema"""
        result = {}

        for legacy_field, value in data.items():
            # Get new field name
            new_field = field_mappings.get(legacy_field, legacy_field.lower())

            # Apply transformation if specified
            if legacy_field in transform_functions:
                transform = transform_functions[legacy_field]
                value = self._apply_transform(value, transform)

            result[new_field] = value

        return result

    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply a transformation function to a value"""
        if transform == "uppercase":
            return str(value).upper() if value else value
        elif transform == "lowercase":
            return str(value).lower() if value else value
        elif transform == "trim":
            return str(value).strip() if value else value
        elif transform == "to_date":
            if isinstance(value, str):
                from dateutil.parser import parse
                return parse(value).date()
            return value
        elif transform == "to_datetime":
            if isinstance(value, str):
                from dateutil.parser import parse
                return parse(value)
            return value
        elif transform == "to_int":
            return int(value) if value else None
        elif transform == "to_float":
            return float(value) if value else None
        elif transform == "to_bool":
            if isinstance(value, str):
                return value.lower() in ('true', 'yes', '1', 'y')
            return bool(value)
        else:
            return value

    async def _apply_to_new_system(
        self,
        session: CDCSession,
        mapping: TableMapping,
        event: ChangeEvent
    ):
        """Apply change to new system (stub - would connect to real DB)"""
        # In production, this would execute SQL against the new database
        logger.debug(
            f"Apply to new: {event.operation.value} on {mapping.new_table} "
            f"with {event.new_data}"
        )

    async def _apply_to_legacy_system(
        self,
        session: CDCSession,
        mapping: TableMapping,
        event: ChangeEvent
    ):
        """Apply change back to legacy system (for rollback)"""
        logger.debug(
            f"Apply to legacy: {event.operation.value} on {mapping.legacy_table}"
        )

    # ==================== Conflict Detection ====================

    async def detect_conflict(
        self,
        session_id: str,
        table: str,
        primary_key: Dict[str, Any],
        legacy_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> Optional[ConflictResolution]:
        """Detect and record a conflict"""
        # Compare data
        conflicts = []
        for key in set(legacy_data.keys()) | set(new_data.keys()):
            legacy_val = legacy_data.get(key)
            new_val = new_data.get(key)
            if legacy_val != new_val:
                conflicts.append(key)

        if not conflicts:
            return None

        conflict = ConflictResolution(
            table=table,
            conflict_type="concurrent_update",
            resolution_strategy="manual",
            legacy_data=legacy_data,
            new_data=new_data
        )

        session = self.sessions.get(session_id)
        if session:
            session.conflicts_detected += 1

        self.conflicts[session_id].append(conflict)
        logger.warning(f"Conflict detected on {table}: {conflicts}")

        return conflict

    async def resolve_conflict(
        self,
        session_id: str,
        conflict_index: int,
        strategy: str,
        resolved_by: str = "system",
        resolved_data: Optional[Dict[str, Any]] = None
    ) -> ConflictResolution:
        """Resolve a conflict"""
        conflicts = self.conflicts.get(session_id, [])
        if conflict_index >= len(conflicts):
            raise ValueError(f"Conflict index out of range: {conflict_index}")

        conflict = conflicts[conflict_index]
        conflict.resolution_strategy = strategy
        conflict.resolved_by = resolved_by
        conflict.resolved_at = datetime.now(timezone.utc)

        if strategy == "legacy_wins":
            conflict.resolved_data = conflict.legacy_data
        elif strategy == "new_wins":
            conflict.resolved_data = conflict.new_data
        elif strategy == "merge":
            # Merge: prefer new, fill gaps with legacy
            merged = {**conflict.legacy_data, **conflict.new_data}
            conflict.resolved_data = merged
        elif strategy == "manual":
            if not resolved_data:
                raise ValueError("Manual resolution requires resolved_data")
            conflict.resolved_data = resolved_data

        session = self.sessions.get(session_id)
        if session:
            session.conflicts_resolved += 1

        logger.info(f"Conflict resolved: {strategy} by {resolved_by}")
        return conflict

    async def get_conflicts(
        self,
        session_id: str,
        unresolved_only: bool = False
    ) -> List[ConflictResolution]:
        """Get conflicts for a session"""
        conflicts = self.conflicts.get(session_id, [])
        if unresolved_only:
            conflicts = [c for c in conflicts if c.resolved_at is None]
        return conflicts

    # ==================== CDC Provider Implementations ====================

    async def _run_debezium_cdc(self, session: CDCSession):
        """Run Debezium-based CDC (Kafka consumer)"""
        logger.info(f"Starting Debezium CDC for session: {session.id}")

        # In production, this would:
        # 1. Connect to Kafka
        # 2. Subscribe to Debezium topics for configured tables
        # 3. Process change events

        while session.status == "running":
            await asyncio.sleep(1)  # Simulated polling

            # Would process Kafka messages here
            if session.status == "paused":
                await asyncio.sleep(5)
                continue

    async def _run_aws_dms_cdc(self, session: CDCSession):
        """Run AWS DMS-based CDC"""
        logger.info(f"Starting AWS DMS CDC for session: {session.id}")

        # In production, this would:
        # 1. Start/monitor DMS replication task
        # 2. Process change events from DMS

        while session.status == "running":
            await asyncio.sleep(1)

    async def _run_polling_cdc(self, session: CDCSession):
        """Run polling-based CDC (fallback for any database)"""
        logger.info(f"Starting Polling CDC for session: {session.id}")

        poll_interval = 5  # seconds

        while session.status == "running":
            if session.status == "paused":
                await asyncio.sleep(poll_interval)
                continue

            # Poll each table for changes
            for mapping in session.table_mappings:
                if not mapping.enabled:
                    continue

                # Would query for changes since last_lsn/timestamp
                # Using triggers or timestamp columns
                pass

            await asyncio.sleep(poll_interval)

    async def _run_trigger_cdc(self, session: CDCSession):
        """Run trigger-based CDC"""
        logger.info(f"Starting Trigger CDC for session: {session.id}")

        # In production, this would:
        # 1. Create triggers on legacy tables
        # 2. Process changes captured by triggers

        while session.status == "running":
            await asyncio.sleep(1)

    # ==================== Metrics & Monitoring ====================

    async def get_metrics(self, session_id: str) -> CDCMetrics:
        """Get current CDC metrics"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        events = self.events.get(session_id, [])

        # Calculate metrics
        now = datetime.now(timezone.utc)
        recent_events = [
            e for e in events
            if (now - e.timestamp).total_seconds() < 3600  # Last hour
        ]

        metrics = CDCMetrics(
            session_id=session_id,
            timestamp=now,
            events_per_second=len(recent_events) / 3600 if recent_events else 0,
            latency_ms=0,  # Would calculate from event timestamps
            queue_depth=len([e for e in events if e.sync_status == SyncStatus.PENDING]),
            tables_synced=len([m for m in session.table_mappings if m.enabled]),
            tables_pending=0,
            bytes_transferred=0,  # Would track actual data size
            errors_last_hour=len([e for e in recent_events if e.sync_status == SyncStatus.FAILED])
        )

        self.metrics[session_id].append(metrics)
        return metrics

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of CDC session"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        metrics = await self.get_metrics(session_id)
        conflicts = await self.get_conflicts(session_id)

        return {
            "session": {
                "id": session.id,
                "name": session.name,
                "mode": session.mode.value,
                "provider": session.provider.value,
                "status": session.status,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "stopped_at": session.stopped_at.isoformat() if session.stopped_at else None
            },
            "tables": {
                "total": len(session.table_mappings),
                "enabled": len([m for m in session.table_mappings if m.enabled])
            },
            "events": {
                "processed": session.events_processed,
                "failed": session.events_failed,
                "pending": metrics.queue_depth
            },
            "conflicts": {
                "total": session.conflicts_detected,
                "resolved": session.conflicts_resolved,
                "unresolved": len([c for c in conflicts if c.resolved_at is None])
            },
            "metrics": {
                "events_per_second": metrics.events_per_second,
                "errors_last_hour": metrics.errors_last_hour
            }
        }


# Singleton instance
_cdc_service: Optional[CDCIntegrationService] = None


def get_cdc_service() -> CDCIntegrationService:
    """Get or create CDC service singleton"""
    global _cdc_service
    if _cdc_service is None:
        _cdc_service = CDCIntegrationService()
    return _cdc_service
