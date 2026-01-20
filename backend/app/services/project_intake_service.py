"""
Project Intake Service - Week 145

Service layer for Project Intake Wizard functionality.
Handles business logic for Brown Paper, Green Paper, and Migration trajecten.

Trajecten:
- Brown Paper: Discovery bestaand systeem -> maintenance OR migration
- Green Paper: Nieuw project vanaf scratch
- Migration: Transformatie (vereist Brown Paper als voorwaarde)
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.project_intake import (
    ProjectIntake,
    ProjectIntakeSource,
    ProjectIntakeIntegration,
    ProjectIntakeScope,
    ProjectIntakeFeature,
    ProjectIntakeEvent,
    TrajectType,
    MigrationType,
    IntakeStatus,
    IntegrationAction,
    AnalysisTier,
    ExpectedOutcome,
    MigrationStrategy,
    BrownPaperDecision,
    PREDEFINED_FEATURES,
)
from app.models.marqed_session import MarQedSession


logger = logging.getLogger(__name__)


class ProjectIntakeService:
    """Service for managing Project Intake Wizard operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # INTAKE CRUD OPERATIONS
    # =========================================================================

    async def create_intake(
        self,
        name: str,
        traject_type: TrajectType,
        organization: Optional[str] = None,
        contact_person: Optional[str] = None,
        contact_email: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> ProjectIntake:
        """Create a new project intake."""
        intake = ProjectIntake(
            name=name,
            traject_type=traject_type,
            organization=organization,
            contact_person=contact_person,
            contact_email=contact_email,
            description=description,
            status=IntakeStatus.draft,
            created_by=created_by,
        )
        self.db.add(intake)
        await self.db.flush()

        # Add created event
        await self._add_event(
            intake_id=intake.id,
            event_type="created",
            event_data={"traject_type": traject_type.value, "name": name},
            created_by=created_by,
        )

        # For Green Paper, initialize with predefined features
        if traject_type == TrajectType.green_paper:
            await self._initialize_green_paper_features(intake.id)

        # For Brown Paper, initialize scope with defaults
        if traject_type == TrajectType.brown_paper:
            await self._initialize_brown_paper_scope(intake.id)

        await self.db.commit()
        await self.db.refresh(intake)
        return intake

    async def get_intake(self, intake_id: UUID) -> Optional[ProjectIntake]:
        """Get intake by ID with all relationships."""
        result = await self.db.execute(
            select(ProjectIntake)
            .options(
                selectinload(ProjectIntake.sources),
                selectinload(ProjectIntake.integrations),
                selectinload(ProjectIntake.scope),
                selectinload(ProjectIntake.features),
                selectinload(ProjectIntake.events),
            )
            .filter(ProjectIntake.id == intake_id)
        )
        return result.scalar_one_or_none()

    async def list_intakes(
        self,
        traject_type: Optional[TrajectType] = None,
        status: Optional[IntakeStatus] = None,
        organization: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[ProjectIntake], int]:
        """List intakes with optional filtering."""
        query = select(ProjectIntake)

        conditions = []
        if traject_type:
            conditions.append(ProjectIntake.traject_type == traject_type)
        if status:
            conditions.append(ProjectIntake.status == status)
        if organization:
            conditions.append(ProjectIntake.organization.ilike(f"%{organization}%"))

        if conditions:
            query = query.filter(and_(*conditions))

        # Count total
        count_result = await self.db.execute(
            select(ProjectIntake.id).filter(and_(*conditions)) if conditions else select(ProjectIntake.id)
        )
        total = len(count_result.all())

        # Get paginated results
        result = await self.db.execute(
            query.order_by(ProjectIntake.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all(), total

    async def update_intake(
        self,
        intake_id: UUID,
        updates: Dict[str, Any],
        modified_by: Optional[str] = None,
    ) -> Optional[ProjectIntake]:
        """Update intake fields."""
        intake = await self.get_intake(intake_id)
        if not intake:
            return None

        # Track changes for audit
        changes = []
        for field, value in updates.items():
            if hasattr(intake, field):
                old_value = getattr(intake, field)
                if old_value != value:
                    setattr(intake, field, value)
                    changes.append({
                        "field": field,
                        "old_value": str(old_value) if old_value else None,
                        "new_value": str(value) if value else None,
                    })

        if changes:
            intake.updated_at = datetime.now(timezone.utc)
            intake.last_modified_by = modified_by
            await self._add_event(
                intake_id=intake_id,
                event_type="updated",
                event_data={"changes": changes},
                created_by=modified_by,
            )
            await self.db.commit()

        return intake

    async def delete_intake(self, intake_id: UUID) -> bool:
        """Delete an intake (soft delete by setting status to cancelled)."""
        intake = await self.get_intake(intake_id)
        if not intake:
            return False

        # Only allow deletion of draft intakes
        if intake.status != IntakeStatus.draft:
            raise ValueError("Alleen draft intakes kunnen worden verwijderd")

        await self.db.delete(intake)
        await self.db.commit()
        return True

    # =========================================================================
    # BROWN PAPER OPERATIONS
    # =========================================================================

    async def _initialize_brown_paper_scope(self, intake_id: UUID) -> ProjectIntakeScope:
        """Initialize Brown Paper scope with default settings."""
        scope = ProjectIntakeScope(
            intake_id=intake_id,
            analyze_functionality=True,
            analyze_quality=True,
            analyze_security=True,
            analyze_tech_debt=True,
            analyze_performance=False,
            analyze_database=False,
            analyze_integrations=False,
            analyze_documentation=False,
            tier=AnalysisTier.standard,
            has_local_files=True,
            has_database_access=False,
        )
        self.db.add(scope)
        await self.db.flush()
        return scope

    async def update_brown_paper_scope(
        self,
        intake_id: UUID,
        scope_data: Dict[str, Any],
        modified_by: Optional[str] = None,
    ) -> Optional[ProjectIntakeScope]:
        """Update Brown Paper analysis scope."""
        intake = await self.get_intake(intake_id)
        if not intake or intake.traject_type != TrajectType.brown_paper:
            return None

        if not intake.scope:
            intake.scope = await self._initialize_brown_paper_scope(intake_id)

        for field, value in scope_data.items():
            if hasattr(intake.scope, field):
                setattr(intake.scope, field, value)

        intake.scope.updated_at = datetime.now(timezone.utc)
        await self._add_event(
            intake_id=intake_id,
            event_type="scope_updated",
            event_data=scope_data,
            created_by=modified_by,
        )
        await self.db.commit()
        return intake.scope

    async def start_brown_paper_analysis(
        self,
        intake_id: UUID,
        started_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start Brown Paper analysis."""
        intake = await self.get_intake(intake_id)
        if not intake:
            raise ValueError("Intake niet gevonden")

        if intake.traject_type != TrajectType.brown_paper:
            raise ValueError("Deze intake is geen Brown Paper traject")

        if not intake.can_start_analysis:
            raise ValueError("Brown Paper vereist systeem_path of repository_url")

        # Update status
        intake.status = IntakeStatus.analyzing
        intake.updated_at = datetime.now(timezone.utc)

        await self._add_event(
            intake_id=intake_id,
            event_type="analysis_started",
            event_data={
                "tier": intake.scope.tier.value if intake.scope else "standard",
                "system_path": intake.scope.system_path if intake.scope else None,
            },
            created_by=started_by,
        )
        await self.db.commit()

        # TODO: Integrate with existing brown_paper_service to run analysis
        # This should trigger background analysis job
        return {
            "status": "started",
            "intake_id": str(intake_id),
            "tier": intake.scope.tier.value if intake.scope else "standard",
            "message": "Brown Paper analyse gestart",
        }

    async def complete_brown_paper_analysis(
        self,
        intake_id: UUID,
        analysis_results: Dict[str, Any],
        marqed_session_id: Optional[str] = None,
    ) -> ProjectIntake:
        """Complete Brown Paper analysis with results."""
        intake = await self.get_intake(intake_id)
        if not intake:
            raise ValueError("Intake niet gevonden")

        intake.status = IntakeStatus.awaiting_decision
        intake.analysis_results = analysis_results

        # Create source record linking to Brown Paper session
        if marqed_session_id:
            source = ProjectIntakeSource(
                intake_id=intake_id,
                brown_paper_session_id=marqed_session_id,
                system_name=intake.name,
                system_path=intake.scope.system_path if intake.scope else None,
                module_count=analysis_results.get("module_count"),
                loc_count=analysis_results.get("loc_count"),
                file_count=analysis_results.get("file_count"),
                quality_score=analysis_results.get("quality_score"),
                security_score=analysis_results.get("security_score"),
                tech_stack=analysis_results.get("tech_stack"),
                analysis_summary=analysis_results,
            )
            self.db.add(source)

        await self._add_event(
            intake_id=intake_id,
            event_type="analysis_completed",
            event_data=analysis_results,
        )
        await self.db.commit()
        return intake

    async def make_brown_paper_decision(
        self,
        intake_id: UUID,
        decision: BrownPaperDecision,
        decision_by: str,
        decision_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make decision after Brown Paper analysis."""
        intake = await self.get_intake(intake_id)
        if not intake:
            raise ValueError("Intake niet gevonden")

        if not intake.can_make_decision:
            raise ValueError("Analyse moet voltooid zijn voordat een beslissing kan worden genomen")

        intake.brown_paper_decision = decision
        intake.decision_date = datetime.now(timezone.utc)
        intake.decision_by = decision_by
        intake.decision_notes = decision_notes
        intake.status = IntakeStatus.completed
        intake.completed_at = datetime.now(timezone.utc)

        await self._add_event(
            intake_id=intake_id,
            event_type="decision_made",
            event_data={
                "decision": decision.value,
                "decision_by": decision_by,
                "notes": decision_notes,
            },
            created_by=decision_by,
        )

        result = {
            "decision": decision.value,
            "intake_id": str(intake_id),
            "follow_up_migration_id": None,
        }

        # If decision is migration, create follow-up migration intake
        if decision == BrownPaperDecision.migration:
            migration_intake = await self._create_follow_up_migration(intake, decision_by)
            intake.follow_up_migration_id = migration_intake.id
            result["follow_up_migration_id"] = str(migration_intake.id)

        await self.db.commit()
        return result

    async def _create_follow_up_migration(
        self,
        brown_paper_intake: ProjectIntake,
        created_by: str,
    ) -> ProjectIntake:
        """Create migration intake following a Brown Paper decision."""
        migration = ProjectIntake(
            name=f"{brown_paper_intake.name} - Migratie",
            traject_type=TrajectType.migration,
            organization=brown_paper_intake.organization,
            contact_person=brown_paper_intake.contact_person,
            contact_email=brown_paper_intake.contact_email,
            description=f"Migratie volgend op Brown Paper analyse van {brown_paper_intake.name}",
            status=IntakeStatus.draft,
            created_by=created_by,
        )
        self.db.add(migration)
        await self.db.flush()

        # Copy Brown Paper sources to migration
        for source in brown_paper_intake.sources:
            new_source = ProjectIntakeSource(
                intake_id=migration.id,
                brown_paper_session_id=source.brown_paper_session_id,
                system_name=source.system_name,
                system_path=source.system_path,
                repository_url=source.repository_url,
                module_count=source.module_count,
                loc_count=source.loc_count,
                file_count=source.file_count,
                quality_score=source.quality_score,
                security_score=source.security_score,
                tech_stack=source.tech_stack,
                analysis_summary=source.analysis_summary,
            )
            self.db.add(new_source)

        await self._add_event(
            intake_id=migration.id,
            event_type="created",
            event_data={
                "traject_type": "migration",
                "source_brown_paper_id": str(brown_paper_intake.id),
            },
            created_by=created_by,
        )

        return migration

    # =========================================================================
    # GREEN PAPER OPERATIONS
    # =========================================================================

    async def _initialize_green_paper_features(self, intake_id: UUID) -> List[ProjectIntakeFeature]:
        """Initialize Green Paper with predefined features."""
        features = []
        for i, feature_def in enumerate(PREDEFINED_FEATURES):
            feature = ProjectIntakeFeature(
                intake_id=intake_id,
                feature_name=feature_def["name"],
                feature_category=feature_def["category"],
                enabled=feature_def["default_enabled"],
                configuration=feature_def.get("config"),
                display_order=i,
            )
            self.db.add(feature)
            features.append(feature)
        await self.db.flush()
        return features

    async def update_green_paper_stack(
        self,
        intake_id: UUID,
        target_stack: Dict[str, Any],
        target_architecture: Optional[str] = None,
        modified_by: Optional[str] = None,
    ) -> Optional[ProjectIntake]:
        """Update Green Paper target stack configuration."""
        intake = await self.get_intake(intake_id)
        if not intake or intake.traject_type != TrajectType.green_paper:
            return None

        intake.target_stack = target_stack
        if target_architecture:
            intake.target_architecture = target_architecture
        intake.updated_at = datetime.now(timezone.utc)

        await self._add_event(
            intake_id=intake_id,
            event_type="stack_configured",
            event_data={"target_stack": target_stack, "target_architecture": target_architecture},
            created_by=modified_by,
        )
        await self.db.commit()
        return intake

    async def update_green_paper_features(
        self,
        intake_id: UUID,
        features: List[Dict[str, Any]],
        modified_by: Optional[str] = None,
    ) -> List[ProjectIntakeFeature]:
        """Update Green Paper feature selections."""
        intake = await self.get_intake(intake_id)
        if not intake or intake.traject_type != TrajectType.green_paper:
            return []

        updated_features = []
        for feature_data in features:
            feature_name = feature_data.get("feature_name")
            existing = next(
                (f for f in intake.features if f.feature_name == feature_name),
                None,
            )
            if existing:
                existing.enabled = feature_data.get("enabled", existing.enabled)
                if "configuration" in feature_data:
                    existing.configuration = feature_data["configuration"]
                updated_features.append(existing)

        await self._add_event(
            intake_id=intake_id,
            event_type="features_updated",
            event_data={"features": features},
            created_by=modified_by,
        )
        await self.db.commit()
        return updated_features

    async def generate_green_paper_project(
        self,
        intake_id: UUID,
        generated_by: str,
    ) -> Dict[str, Any]:
        """Generate project artifacts from Green Paper configuration."""
        intake = await self.get_intake(intake_id)
        if not intake:
            raise ValueError("Intake niet gevonden")

        if intake.traject_type != TrajectType.green_paper:
            raise ValueError("Deze intake is geen Green Paper traject")

        # Validate required configuration
        if not intake.target_stack:
            raise ValueError("Target stack moet geconfigureerd zijn")

        enabled_features = [f for f in intake.features if f.enabled]
        if not enabled_features:
            raise ValueError("Minimaal één feature moet geselecteerd zijn")

        # Update status
        intake.status = IntakeStatus.active

        await self._add_event(
            intake_id=intake_id,
            event_type="project_generation_started",
            event_data={
                "enabled_features": [f.feature_name for f in enabled_features],
                "target_stack": intake.target_stack,
            },
            created_by=generated_by,
        )

        # TODO: Integrate with project generation logic
        # This should create:
        # 1. Project record
        # 2. Epics for enabled features
        # 3. Initial kanban items

        result = {
            "status": "started",
            "intake_id": str(intake_id),
            "enabled_features": [f.feature_name for f in enabled_features],
            "message": "Project generatie gestart",
        }

        await self.db.commit()
        return result

    # =========================================================================
    # MIGRATION OPERATIONS
    # =========================================================================

    async def get_available_brown_paper_sources(
        self,
        organization: Optional[str] = None,
    ) -> List[ProjectIntake]:
        """Get completed Brown Paper intakes that can be used as migration sources."""
        query = select(ProjectIntake).filter(
            and_(
                ProjectIntake.traject_type == TrajectType.brown_paper,
                ProjectIntake.status == IntakeStatus.completed,
                or_(
                    ProjectIntake.brown_paper_decision == BrownPaperDecision.report_only,
                    ProjectIntake.brown_paper_decision == BrownPaperDecision.maintenance,
                    # Exclude those already linked to a migration
                    ProjectIntake.follow_up_migration_id.is_(None),
                ),
            )
        )
        if organization:
            query = query.filter(ProjectIntake.organization == organization)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def set_migration_type(
        self,
        intake_id: UUID,
        migration_type: MigrationType,
        modified_by: Optional[str] = None,
    ) -> Optional[ProjectIntake]:
        """Set migration type (modernize, consolidate, hybrid)."""
        intake = await self.get_intake(intake_id)
        if not intake or intake.traject_type != TrajectType.migration:
            return None

        intake.migration_type = migration_type
        intake.updated_at = datetime.now(timezone.utc)

        await self._add_event(
            intake_id=intake_id,
            event_type="migration_type_set",
            event_data={"migration_type": migration_type.value},
            created_by=modified_by,
        )
        await self.db.commit()
        return intake

    async def add_migration_source(
        self,
        intake_id: UUID,
        brown_paper_session_id: str,
        system_name: str,
        system_path: Optional[str] = None,
        repository_url: Optional[str] = None,
    ) -> ProjectIntakeSource:
        """Add a Brown Paper source to migration."""
        intake = await self.get_intake(intake_id)
        if not intake or intake.traject_type != TrajectType.migration:
            raise ValueError("Intake moet een migratie traject zijn")

        # Get analysis summary from Brown Paper session if available
        analysis_summary = None
        if brown_paper_session_id:
            result = await self.db.execute(
                select(MarQedSession).filter(MarQedSession.id == brown_paper_session_id)
            )
            marqed_session = result.scalar_one_or_none()
            if marqed_session and marqed_session.analysis_result:
                analysis_summary = marqed_session.analysis_result

        source = ProjectIntakeSource(
            intake_id=intake_id,
            brown_paper_session_id=brown_paper_session_id,
            system_name=system_name,
            system_path=system_path,
            repository_url=repository_url,
            analysis_summary=analysis_summary,
            display_order=len(intake.sources),
        )
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def remove_migration_source(
        self,
        intake_id: UUID,
        source_id: UUID,
    ) -> bool:
        """Remove a source from migration."""
        result = await self.db.execute(
            select(ProjectIntakeSource).filter(
                and_(
                    ProjectIntakeSource.id == source_id,
                    ProjectIntakeSource.intake_id == intake_id,
                )
            )
        )
        source = result.scalar_one_or_none()
        if not source:
            return False

        await self.db.delete(source)
        await self.db.commit()
        return True

    async def set_migration_target(
        self,
        intake_id: UUID,
        target_stack: Dict[str, Any],
        target_architecture: Optional[str] = None,
        modified_by: Optional[str] = None,
    ) -> Optional[ProjectIntake]:
        """Set migration target stack and architecture."""
        intake = await self.get_intake(intake_id)
        if not intake or intake.traject_type != TrajectType.migration:
            return None

        intake.target_stack = target_stack
        if target_architecture:
            intake.target_architecture = target_architecture
        intake.updated_at = datetime.now(timezone.utc)

        await self._add_event(
            intake_id=intake_id,
            event_type="migration_target_set",
            event_data={
                "target_stack": target_stack,
                "target_architecture": target_architecture,
            },
            created_by=modified_by,
        )
        await self.db.commit()
        return intake

    async def set_migration_strategy(
        self,
        intake_id: UUID,
        strategy: MigrationStrategy,
        parallel_run_weeks: Optional[int] = None,
        start_date: Optional[datetime] = None,
        target_go_live: Optional[datetime] = None,
        hard_deadline: bool = False,
        modified_by: Optional[str] = None,
    ) -> Optional[ProjectIntake]:
        """Set migration strategy and timeline."""
        intake = await self.get_intake(intake_id)
        if not intake or intake.traject_type != TrajectType.migration:
            return None

        intake.migration_strategy = strategy
        if parallel_run_weeks is not None:
            intake.parallel_run_weeks = parallel_run_weeks
        if start_date:
            intake.start_date = start_date
        if target_go_live:
            intake.target_go_live = target_go_live
        intake.hard_deadline = hard_deadline
        intake.updated_at = datetime.now(timezone.utc)

        await self._add_event(
            intake_id=intake_id,
            event_type="migration_strategy_set",
            event_data={
                "strategy": strategy.value,
                "parallel_run_weeks": parallel_run_weeks,
                "start_date": str(start_date) if start_date else None,
                "target_go_live": str(target_go_live) if target_go_live else None,
            },
            created_by=modified_by,
        )
        await self.db.commit()
        return intake

    async def update_integration(
        self,
        intake_id: UUID,
        integration_id: UUID,
        action: IntegrationAction,
        library_name: Optional[str] = None,
        library_type: Optional[str] = None,
        decision_notes: Optional[str] = None,
        modified_by: Optional[str] = None,
    ) -> Optional[ProjectIntakeIntegration]:
        """Update integration decision."""
        result = await self.db.execute(
            select(ProjectIntakeIntegration).filter(
                and_(
                    ProjectIntakeIntegration.id == integration_id,
                    ProjectIntakeIntegration.intake_id == intake_id,
                )
            )
        )
        integration = result.scalar_one_or_none()
        if not integration:
            return None

        integration.action = action
        if action == IntegrationAction.library:
            integration.library_name = library_name
            integration.library_type = library_type
        integration.decision_notes = decision_notes
        integration.updated_at = datetime.now(timezone.utc)

        await self._add_event(
            intake_id=intake_id,
            event_type="integration_decision",
            event_data={
                "integration_id": str(integration_id),
                "integration_name": integration.integration_name,
                "action": action.value,
                "library_name": library_name,
            },
            created_by=modified_by,
        )
        await self.db.commit()
        return integration

    async def start_migration(
        self,
        intake_id: UUID,
        started_by: str,
    ) -> Dict[str, Any]:
        """Start migration execution."""
        intake = await self.get_intake(intake_id)
        if not intake:
            raise ValueError("Intake niet gevonden")

        if intake.traject_type != TrajectType.migration:
            raise ValueError("Deze intake is geen migratie traject")

        if not intake.can_start_migration:
            raise ValueError(
                "Migratie vereist: migratie type, minimaal één bron, "
                "target stack, en migratie strategie"
            )

        # Update status
        intake.status = IntakeStatus.active
        intake.updated_at = datetime.now(timezone.utc)

        await self._add_event(
            intake_id=intake_id,
            event_type="migration_started",
            event_data={
                "migration_type": intake.migration_type.value,
                "strategy": intake.migration_strategy.value,
                "source_count": len(intake.sources),
            },
            created_by=started_by,
        )

        # TODO: Integrate with migration_enhanced service for execution
        result = {
            "status": "started",
            "intake_id": str(intake_id),
            "migration_type": intake.migration_type.value,
            "strategy": intake.migration_strategy.value,
            "source_count": len(intake.sources),
            "message": "Migratie gestart",
        }

        await self.db.commit()
        return result

    # =========================================================================
    # EVENT TRACKING
    # =========================================================================

    async def _add_event(
        self,
        intake_id: UUID,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> ProjectIntakeEvent:
        """Add audit event for intake."""
        event = ProjectIntakeEvent(
            intake_id=intake_id,
            event_type=event_type,
            event_data=event_data,
            old_value=old_value,
            new_value=new_value,
            created_by=created_by,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_intake_events(
        self,
        intake_id: UUID,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[ProjectIntakeEvent]:
        """Get events for an intake."""
        query = select(ProjectIntakeEvent).filter(
            ProjectIntakeEvent.intake_id == intake_id
        )
        if event_type:
            query = query.filter(ProjectIntakeEvent.event_type == event_type)

        query = query.order_by(ProjectIntakeEvent.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()


# Factory function for dependency injection
async def get_project_intake_service(db: AsyncSession) -> ProjectIntakeService:
    """Factory function to create ProjectIntakeService."""
    return ProjectIntakeService(db)
