"""
Migration Planning Orchestrator (Workflow 2)

Week 69: Gestandaardiseerde Project Workflows
Orchestrates the migration planning workflow (requires completed assessment):
7. FP Estimation (Eliza agent)
8. Target Architecture (Felix agent)
9. Migration Strategy (Felix agent)
10. Migration Report Generation (Diana agent)

This workflow requires a completed Workflow 1 (Project Assessment) as prerequisite.

Author: Claude Code (Week 69)
Date: 2025-12-15
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import UUID
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.project_assessment import ProjectAssessment, MigrationPlan, AssessmentPhase

logger = logging.getLogger(__name__)

# Optional: LLM Provider for agent reasoning
try:
    from app.providers.registry import get_provider_registry
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM Provider not available. Running in rule-based mode.")

# Optional: ChromaDB for historical context
try:
    from app.services.chroma_service import get_chroma_service
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available. Running without historical context.")

# Optional: Experience Store for learning from past migrations
try:
    from app.services.experience_store_service import ExperienceStoreService
    EXPERIENCE_AVAILABLE = True
except ImportError:
    EXPERIENCE_AVAILABLE = False


@dataclass
class PhaseResult:
    """Result from a single planning phase"""
    success: bool
    phase_name: str
    data: Dict[str, Any]
    error: Optional[str] = None
    duration_seconds: int = 0
    items_processed: int = 0
    items_found: int = 0


# Target technology configurations
TARGET_TECHNOLOGIES = {
    "python_fastapi": {
        "name": "Python FastAPI",
        "patterns": ["clean_architecture", "hexagonal", "layered"],
        "default_database": "postgresql",
        "default_frontend": "react"
    },
    "dotnet8": {
        "name": ".NET 8 Web API",
        "patterns": ["clean_architecture", "cqrs", "ddd"],
        "default_database": "postgresql",
        "default_frontend": "blazor"
    },
    "nodejs_nestjs": {
        "name": "Node.js NestJS",
        "patterns": ["modular_monolith", "microservices"],
        "default_database": "postgresql",
        "default_frontend": "react"
    },
    "java_spring": {
        "name": "Java Spring Boot",
        "patterns": ["hexagonal", "ddd", "microservices"],
        "default_database": "postgresql",
        "default_frontend": "react"
    },
    "go_fiber": {
        "name": "Go Fiber",
        "patterns": ["clean_architecture", "layered"],
        "default_database": "postgresql",
        "default_frontend": "vue"
    }
}

# Migration strategies with characteristics
MIGRATION_STRATEGIES = {
    "strangler_fig": {
        "name": "Strangler Fig Pattern",
        "description": "Gradually replace legacy components with new implementations",
        "best_for": ["large_codebase", "critical_system", "risk_averse"],
        "timeline_multiplier": 1.5,
        "risk_level": "low"
    },
    "big_bang": {
        "name": "Big Bang Migration",
        "description": "Complete rewrite and switch over at once",
        "best_for": ["small_codebase", "non_critical", "fresh_start"],
        "timeline_multiplier": 0.8,
        "risk_level": "high"
    },
    "parallel_run": {
        "name": "Parallel Running",
        "description": "Run both systems simultaneously during transition",
        "best_for": ["critical_system", "compliance_required"],
        "timeline_multiplier": 1.3,
        "risk_level": "low"
    },
    "incremental": {
        "name": "Incremental Migration",
        "description": "Migrate module by module with continuous integration",
        "best_for": ["medium_codebase", "agile_team"],
        "timeline_multiplier": 1.2,
        "risk_level": "medium"
    },
    "phased": {
        "name": "Phased Migration",
        "description": "Migrate in defined phases with milestones",
        "best_for": ["enterprise", "multiple_stakeholders"],
        "timeline_multiplier": 1.4,
        "risk_level": "low"
    },
    "blue_green": {
        "name": "Blue-Green Deployment",
        "description": "Maintain two identical environments for instant rollback",
        "best_for": ["high_availability", "zero_downtime"],
        "timeline_multiplier": 1.1,
        "risk_level": "low"
    }
}

# IFPUG General System Characteristics (GSC)
GSC_FACTORS = [
    "data_communications",
    "distributed_data_processing",
    "performance",
    "heavily_used_configuration",
    "transaction_rate",
    "online_data_entry",
    "end_user_efficiency",
    "online_update",
    "complex_processing",
    "reusability",
    "installation_ease",
    "operational_ease",
    "multiple_sites",
    "facilitate_change"
]


class MigrationPlanningOrchestrator:
    """
    Orchestrates Workflow 2: Migration Planning

    This workflow requires a completed Project Assessment (Workflow 1)
    and creates a comprehensive migration plan.

    Phases:
    7. FP Estimation - IFPUG function point estimation (Eliza)
    8. Target Architecture - Design target architecture (Felix)
    9. Migration Strategy - Select and detail migration approach (Felix)
    10. Report Generation - Create migration plan report (Diana)
    """

    def __init__(self, db: AsyncSession, use_llm: bool = False):
        self.db = db
        self.use_llm = use_llm and LLM_AVAILABLE

        # Initialize ChromaDB for historical context
        self.chroma = None
        if CHROMA_AVAILABLE:
            try:
                self.chroma = get_chroma_service()
                logger.info("ChromaDB service initialized for historical migration context")
            except Exception as e:
                logger.warning(f"ChromaDB initialization failed: {e}")

        # Initialize LLM provider if requested
        self.llm_provider = None
        if self.use_llm:
            try:
                registry = get_provider_registry()
                self.llm_provider = registry.get_provider("ollama")  # Default to local
                logger.info("LLM provider initialized for migration planning")
            except Exception as e:
                logger.warning(f"LLM provider initialization failed: {e}")
                self.use_llm = False

    async def start_planning(
        self,
        assessment_id: UUID,
        target_technology: str,
        target_database: Optional[str] = None,
        target_frontend: Optional[str] = None
    ) -> MigrationPlan:
        """
        Start migration planning for a completed assessment

        Args:
            assessment_id: ID of completed ProjectAssessment
            target_technology: Target technology stack
            target_database: Target database (optional, uses default)
            target_frontend: Target frontend (optional, uses default)

        Returns:
            Created MigrationPlan with 'draft' status
        """
        # Get and validate assessment
        result = await self.db.execute(
            select(ProjectAssessment).where(ProjectAssessment.id == assessment_id)
        )
        assessment = result.scalar_one_or_none()

        if not assessment:
            raise ValueError(f"Assessment not found: {assessment_id}")

        if assessment.status != "completed":
            raise ValueError(f"Assessment must be completed. Current status: {assessment.status}")

        if assessment.blockers:
            raise ValueError(f"Assessment has blockers that must be resolved: {assessment.blockers}")

        # Validate target technology
        if target_technology not in TARGET_TECHNOLOGIES:
            raise ValueError(f"Unknown target technology: {target_technology}")

        tech_config = TARGET_TECHNOLOGIES[target_technology]

        # Create migration plan
        plan = MigrationPlan(
            assessment_id=assessment_id,
            target_technology=target_technology,
            target_database=target_database or tech_config["default_database"],
            target_frontend=target_frontend or tech_config["default_frontend"],
            status="draft",
            current_phase="estimation",
            progress_percent=0,
            started_at=datetime.now(timezone.utc)
        )

        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)

        return plan

    async def run_planning(self, plan_id: UUID) -> MigrationPlan:
        """
        Run the complete migration planning workflow

        Args:
            plan_id: ID of the migration plan to process

        Returns:
            Updated MigrationPlan with results
        """
        # Get plan and assessment
        result = await self.db.execute(
            select(MigrationPlan).where(MigrationPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise ValueError(f"Migration plan not found: {plan_id}")

        # Get the associated assessment
        result = await self.db.execute(
            select(ProjectAssessment).where(ProjectAssessment.id == plan.assessment_id)
        )
        assessment = result.scalar_one_or_none()

        if not assessment:
            raise ValueError(f"Assessment not found for plan: {plan_id}")

        try:
            # Phase 7: FP Estimation
            await self._update_phase(plan, "estimation", 7)
            fp_result = await self._run_fp_estimation_phase(plan, assessment)
            await self._save_phase_result(plan, fp_result, 7)
            plan.progress_percent = 25

            # Phase 8: Target Architecture
            await self._update_phase(plan, "architecture", 8)
            arch_result = await self._run_architecture_phase(plan, assessment)
            await self._save_phase_result(plan, arch_result, 8)
            plan.progress_percent = 50

            # Phase 9: Migration Strategy
            await self._update_phase(plan, "strategy", 9)
            strategy_result = await self._run_strategy_phase(plan, assessment)
            await self._save_phase_result(plan, strategy_result, 9)
            plan.progress_percent = 75

            # Phase 10: Report Generation
            await self._update_phase(plan, "report", 10)
            report_result = await self._run_report_phase(plan, assessment)
            await self._save_phase_result(plan, report_result, 10)
            plan.progress_percent = 100

            # Mark as in_review (ready for human approval)
            plan.status = "in_review"
            plan.completed_at = datetime.now(timezone.utc)
            plan.current_phase = "completed"

            await self.db.commit()
            return plan

        except Exception as e:
            plan.status = "draft"
            plan.error_message = str(e)
            await self.db.commit()
            raise

    async def _update_phase(self, plan: MigrationPlan, phase: str, phase_num: int):
        """Update current phase in plan"""
        plan.current_phase = phase
        await self.db.commit()

    async def _save_phase_result(
        self,
        plan: MigrationPlan,
        result: PhaseResult,
        phase_number: int
    ):
        """Save phase execution result"""
        phase = AssessmentPhase(
            migration_plan_id=plan.id,
            workflow="migration",
            phase_number=phase_number,
            phase_name=result.phase_name,
            agent_name=self._get_agent_for_phase(result.phase_name),
            status="completed" if result.success else "failed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            duration_seconds=result.duration_seconds,
            result_summary=result.error if not result.success else f"Processed {result.items_processed} items",
            result_data=result.data,
            error_message=result.error,
            items_processed=result.items_processed,
            items_found=result.items_found
        )
        self.db.add(phase)
        await self.db.commit()

    def _get_agent_for_phase(self, phase_name: str) -> str:
        """Get the responsible agent for each phase"""
        agent_mapping = {
            "estimation": "eliza",
            "architecture": "felix",
            "strategy": "felix",
            "report": "diana"
        }
        return agent_mapping.get(phase_name, "unknown")

    # ========== Phase Implementations ==========

    async def _run_fp_estimation_phase(
        self,
        plan: MigrationPlan,
        assessment: ProjectAssessment
    ) -> PhaseResult:
        """Phase 7: Function Point Estimation (Eliza)"""
        start_time = datetime.now(timezone.utc)

        try:
            # Get historical estimation data from ChromaDB
            historical_estimates = []
            if self.chroma:
                try:
                    # Find similar projects to learn from their estimations
                    context_query = f"{assessment.primary_stack or ''} migration {plan.target_technology}"
                    similar = self.chroma.find_similar_projects(
                        project_description=context_query,
                        top_k=5
                    )
                    historical_estimates = similar.get("similar_projects", [])
                    logger.info(f"Found {len(historical_estimates)} historical estimates for calibration")
                except Exception as e:
                    logger.warning(f"Historical estimation lookup failed: {e}")

            # Calculate UFP based on assessment data
            file_count = assessment.file_count or 0
            line_count = assessment.line_count or 0
            components = len(assessment.architecture_components or [])

            # Estimate IFPUG components
            # EI (External Inputs) - rough estimate from components
            ei_count = max(5, components // 3)
            ei_fp = ei_count * 4  # Average complexity

            # EO (External Outputs) - API endpoints estimate
            eo_count = max(3, components // 4)
            eo_fp = eo_count * 5

            # EQ (External Queries) - read operations
            eq_count = max(3, components // 5)
            eq_fp = eq_count * 4

            # ILF (Internal Logical Files) - data entities
            ilf_count = max(5, components // 4)
            ilf_fp = ilf_count * 10

            # EIF (External Interface Files)
            eif_count = 2  # Assume 2 external interfaces
            eif_fp = eif_count * 7

            # Calculate Unadjusted Function Points
            unadjusted_fp = ei_fp + eo_fp + eq_fp + ilf_fp + eif_fp

            # Calculate GSC factors (simplified - use defaults with adjustments)
            gsc_scores = {}
            base_score = 3  # Average

            # Adjust based on assessment data
            if assessment.security_critical_count > 0:
                base_score += 1  # More complexity

            for factor in GSC_FACTORS:
                gsc_scores[factor] = base_score

            # Calculate TDI (Total Degree of Influence)
            tdi = sum(gsc_scores.values())

            # Calculate VAF (Value Adjustment Factor)
            vaf = Decimal("0.65") + Decimal("0.01") * Decimal(tdi)

            # Calculate Adjusted Function Points
            adjusted_fp = int(float(unadjusted_fp) * float(vaf))

            # Calculate effort (8 hours per FP is industry standard)
            hours_per_fp = 8
            total_hours = adjusted_fp * hours_per_fp
            total_days = total_hours // 8
            total_weeks = total_days // 5

            # Phase breakdown (typical SDLC)
            phase_breakdown = [
                {"phase": "Requirements & Design", "percentage": 20, "hours": total_hours * 0.20, "days": total_days * 0.20},
                {"phase": "Development", "percentage": 40, "hours": total_hours * 0.40, "days": total_days * 0.40},
                {"phase": "Testing", "percentage": 25, "hours": total_hours * 0.25, "days": total_days * 0.25},
                {"phase": "Deployment & Training", "percentage": 15, "hours": total_hours * 0.15, "days": total_days * 0.15},
            ]

            # Team sizing (1 FP per developer per day)
            if total_weeks > 26:  # > 6 months
                team_size = max(5, adjusted_fp // 200)
            elif total_weeks > 13:  # > 3 months
                team_size = max(3, adjusted_fp // 150)
            else:
                team_size = max(2, adjusted_fp // 100)

            team_composition = {
                "senior_developers": max(1, team_size // 3),
                "mid_developers": max(1, team_size // 2),
                "junior_developers": max(0, team_size - (team_size // 3) - (team_size // 2)),
                "qa_engineers": max(1, team_size // 4),
                "devops": 1
            }

            # Update plan
            plan.unadjusted_fp = unadjusted_fp
            plan.adjusted_fp = adjusted_fp
            plan.vaf = vaf
            plan.gsc_factors = gsc_scores
            plan.total_hours = total_hours
            plan.total_days = total_days
            plan.total_weeks = total_weeks
            plan.phase_breakdown = phase_breakdown
            plan.team_size_recommended = team_size
            plan.team_composition = team_composition

            # Optional: LLM-enhanced estimation (Eliza agent reasoning)
            eliza_insights = None
            if self.use_llm and self.llm_provider:
                try:
                    eliza_insights = await self._get_eliza_insights(
                        assessment, plan, adjusted_fp, total_weeks, historical_estimates
                    )
                except Exception as e:
                    logger.warning(f"Eliza insight generation failed: {e}")

            duration = (datetime.now(timezone.utc) - start_time).seconds

            result_data = {
                "unadjusted_fp": unadjusted_fp,
                "adjusted_fp": adjusted_fp,
                "total_weeks": total_weeks,
                "team_size": team_size,
                "historical_calibration_count": len(historical_estimates)
            }
            if eliza_insights:
                result_data["eliza_insights"] = eliza_insights

            return PhaseResult(
                success=True,
                phase_name="estimation",
                data=result_data,
                duration_seconds=duration,
                items_processed=5,  # 5 IFPUG component types
                items_found=adjusted_fp
            )

        except Exception as e:
            return PhaseResult(
                success=False,
                phase_name="estimation",
                data={},
                error=str(e)
            )

    async def _get_eliza_insights(
        self,
        assessment: ProjectAssessment,
        plan: MigrationPlan,
        adjusted_fp: int,
        total_weeks: int,
        historical_estimates: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Get Eliza agent's LLM-enhanced estimation insights"""
        if not self.llm_provider:
            return None

        prompt = f"""You are Eliza, the Estimation Engine agent. Review this FP estimation:

**Project**: {assessment.project_name}
**Source Stack**: {assessment.primary_stack or 'Unknown'}
**Target Stack**: {plan.target_technology}
**Files**: {assessment.file_count:,}
**Lines of Code**: {assessment.line_count:,}
**Components**: {len(assessment.architecture_components or [])}

**IFPUG Estimation**:
- Adjusted FP: {adjusted_fp}
- Estimated Duration: {total_weeks} weeks

**Historical Similar Projects**: {len(historical_estimates)}

Based on IFPUG CPM 4.3.1 methodology, provide:
1. Confidence level in this estimate
2. Risk factors that could increase duration
3. Optimization suggestions

Respond in JSON format:
{{"confidence": "low|medium|high", "risk_factors": ["..."], "optimization_suggestions": ["..."], "adjusted_weeks_range": [min, max]}}"""

        try:
            response = await self.llm_provider.generate(prompt)
            import json
            json_match = response.find('{')
            if json_match >= 0:
                json_end = response.rfind('}') + 1
                return json.loads(response[json_match:json_end])
        except Exception as e:
            logger.warning(f"Eliza insight parsing failed: {e}")
        return None

    async def _run_architecture_phase(
        self,
        plan: MigrationPlan,
        assessment: ProjectAssessment
    ) -> PhaseResult:
        """Phase 8: Target Architecture Design (Felix)"""
        start_time = datetime.now(timezone.utc)

        try:
            tech_config = TARGET_TECHNOLOGIES.get(plan.target_technology, {})
            preferred_patterns = tech_config.get("patterns", ["clean_architecture"])

            # Select architecture pattern based on assessment
            if assessment.architecture_pattern in preferred_patterns:
                target_pattern = assessment.architecture_pattern
            else:
                target_pattern = preferred_patterns[0]

            # Define target layers
            target_layers = [
                {"name": "API", "responsibility": "HTTP endpoints, request/response handling"},
                {"name": "Application", "responsibility": "Use cases, business orchestration"},
                {"name": "Domain", "responsibility": "Business entities, rules, value objects"},
                {"name": "Infrastructure", "responsibility": "Database, external services, implementations"}
            ]

            # Component mapping from source to target
            component_mapping = []
            for comp in (assessment.architecture_components or [])[:20]:
                target_type = self._map_component_type(comp.get("type", "unknown"), plan.target_technology)
                component_mapping.append({
                    "legacy_name": comp.get("name"),
                    "legacy_type": comp.get("type"),
                    "target_name": comp.get("name"),
                    "target_type": target_type,
                    "target_layer": self._get_layer_for_component(target_type),
                    "effort_hours": self._estimate_component_effort(comp.get("type"))
                })

            # Generate API contracts (stub)
            api_contracts = [
                {"endpoint": "/api/health", "method": "GET", "description": "Health check endpoint"},
                {"endpoint": "/api/v1/resources", "method": "GET", "description": "List resources"},
                {"endpoint": "/api/v1/resources", "method": "POST", "description": "Create resource"},
                {"endpoint": "/api/v1/resources/{id}", "method": "GET", "description": "Get resource by ID"},
                {"endpoint": "/api/v1/resources/{id}", "method": "PUT", "description": "Update resource"},
                {"endpoint": "/api/v1/resources/{id}", "method": "DELETE", "description": "Delete resource"},
            ]

            # Data migration plan
            data_migration = [
                {"step": 1, "action": "Export schema definition", "target": "DDL scripts"},
                {"step": 2, "action": "Transform data types", "target": f"{plan.target_database} compatible"},
                {"step": 3, "action": "Create new schema", "target": "Target database"},
                {"step": 4, "action": "Migrate data with validation", "target": "Verified data transfer"},
                {"step": 5, "action": "Verify integrity", "target": "Data consistency checks"},
            ]

            # Architecture Decision Records
            adrs = [
                {
                    "id": "ADR-001",
                    "title": f"Use {target_pattern.replace('_', ' ').title()} Pattern",
                    "context": f"Need a maintainable architecture for {plan.target_technology}",
                    "decision": f"Adopt {target_pattern} to ensure separation of concerns",
                    "consequences": ["Clear boundaries between layers", "Testable components", "Dependency inversion"]
                },
                {
                    "id": "ADR-002",
                    "title": f"Use {plan.target_database} as Database",
                    "context": "Need a reliable, scalable database solution",
                    "decision": f"Use {plan.target_database} for data persistence",
                    "consequences": ["ACID compliance", "Mature ecosystem", "Good tooling support"]
                }
            ]

            # Update plan
            plan.target_architecture = {
                "pattern": target_pattern,
                "layers": target_layers,
                "technology": tech_config.get("name", plan.target_technology)
            }
            plan.architecture_pattern = target_pattern
            plan.architecture_layers = target_layers
            plan.component_mapping = component_mapping
            plan.api_contracts = api_contracts
            plan.data_migration_plan = data_migration
            plan.architecture_decisions = adrs

            duration = (datetime.now(timezone.utc) - start_time).seconds

            return PhaseResult(
                success=True,
                phase_name="architecture",
                data={
                    "pattern": target_pattern,
                    "components_mapped": len(component_mapping),
                    "adrs": len(adrs)
                },
                duration_seconds=duration,
                items_processed=len(assessment.architecture_components or []),
                items_found=len(component_mapping)
            )

        except Exception as e:
            return PhaseResult(
                success=False,
                phase_name="architecture",
                data={},
                error=str(e)
            )

    def _map_component_type(self, source_type: str, target_tech: str) -> str:
        """Map source component type to target architecture type"""
        mapping = {
            "controller": "Controller",
            "service": "Service",
            "repository": "Repository",
            "model": "Entity",
            "viewmodel": "DTO",
            "handler": "Handler",
            "validator": "Validator",
        }
        return mapping.get(source_type, "Component")

    def _get_layer_for_component(self, component_type: str) -> str:
        """Determine which layer a component belongs to"""
        layer_mapping = {
            "Controller": "API",
            "Service": "Application",
            "Handler": "Application",
            "Repository": "Infrastructure",
            "Entity": "Domain",
            "DTO": "Application",
            "Validator": "Domain",
        }
        return layer_mapping.get(component_type, "Application")

    def _estimate_component_effort(self, component_type: str) -> int:
        """Estimate hours to migrate a component type"""
        effort_mapping = {
            "controller": 8,
            "service": 16,
            "repository": 12,
            "model": 4,
            "viewmodel": 6,
            "handler": 8,
            "validator": 4,
        }
        return effort_mapping.get(component_type, 8)

    async def _run_strategy_phase(
        self,
        plan: MigrationPlan,
        assessment: ProjectAssessment
    ) -> PhaseResult:
        """Phase 9: Migration Strategy Selection (Felix)"""
        start_time = datetime.now(timezone.utc)

        try:
            # Select strategy based on project characteristics
            file_count = assessment.file_count or 0
            security_issues = assessment.security_critical_count or 0

            # Strategy selection logic
            if file_count > 1000 or security_issues > 5:
                strategy_key = "strangler_fig"
            elif file_count < 100:
                strategy_key = "big_bang"
            elif assessment.overall_grade in ["A", "B"]:
                strategy_key = "incremental"
            else:
                strategy_key = "phased"

            strategy = MIGRATION_STRATEGIES[strategy_key]

            # Calculate timeline with strategy multiplier
            base_weeks = plan.total_weeks or 12
            timeline_weeks = int(base_weeks * strategy["timeline_multiplier"])

            # Define migration phases
            if strategy_key == "strangler_fig":
                migration_phases = [
                    {"name": "Foundation", "description": "Set up new infrastructure and CI/CD", "duration_weeks": 2, "deliverables": ["Infrastructure", "Pipelines"]},
                    {"name": "Core Services", "description": "Migrate core business logic", "duration_weeks": timeline_weeks // 3, "deliverables": ["Domain layer", "Core services"]},
                    {"name": "Integration Layer", "description": "Build API gateway and adapters", "duration_weeks": timeline_weeks // 4, "deliverables": ["API gateway", "Adapters"]},
                    {"name": "UI Migration", "description": "Gradually migrate UI components", "duration_weeks": timeline_weeks // 4, "deliverables": ["New UI components"]},
                    {"name": "Cutover", "description": "Final switch and decommission", "duration_weeks": 2, "deliverables": ["Full cutover", "Legacy shutdown"]},
                ]
            elif strategy_key == "big_bang":
                migration_phases = [
                    {"name": "Development", "description": "Complete rewrite", "duration_weeks": timeline_weeks - 2, "deliverables": ["New application"]},
                    {"name": "Testing", "description": "Comprehensive testing", "duration_weeks": 1, "deliverables": ["Test results"]},
                    {"name": "Cutover", "description": "Switch to new system", "duration_weeks": 1, "deliverables": ["Go-live"]},
                ]
            else:
                migration_phases = [
                    {"name": "Phase 1: Foundation", "description": "Infrastructure and tooling", "duration_weeks": timeline_weeks // 4, "deliverables": ["Infrastructure"]},
                    {"name": "Phase 2: Core", "description": "Core functionality migration", "duration_weeks": timeline_weeks // 3, "deliverables": ["Core modules"]},
                    {"name": "Phase 3: Features", "description": "Feature migration", "duration_weeks": timeline_weeks // 3, "deliverables": ["All features"]},
                    {"name": "Phase 4: Finalize", "description": "Testing and cutover", "duration_weeks": timeline_weeks // 6, "deliverables": ["Production ready"]},
                ]

            # Define milestones
            milestones = [
                {"name": "Project Kickoff", "week": 0, "deliverables": ["Team assembled", "Environment ready"]},
                {"name": "Architecture Approved", "week": 2, "deliverables": ["Technical design", "ADRs signed off"]},
                {"name": "MVP Complete", "week": timeline_weeks // 2, "deliverables": ["Core functionality working"]},
                {"name": "UAT Start", "week": timeline_weeks - 4, "deliverables": ["Feature complete", "UAT environment"]},
                {"name": "Go-Live", "week": timeline_weeks, "deliverables": ["Production deployment", "Handover"]},
            ]

            # Prerequisites
            prerequisites = [
                "Development environment setup",
                "CI/CD pipeline configured",
                "Database provisioned",
                "Team onboarded",
                "Access to legacy system documentation",
            ]

            # External dependencies
            external_deps = []
            if assessment.primary_stack and "sql" in (assessment.primary_stack or "").lower():
                external_deps.append("Database migration tools (e.g., Flyway, Alembic)")

            # Risks based on assessment
            risks = []
            if assessment.security_critical_count > 0:
                risks.append({
                    "title": "Security vulnerabilities in legacy code",
                    "probability": 4,
                    "impact": 5,
                    "mitigation": "Address critical security issues before or during migration"
                })

            if assessment.tech_debt_hours and assessment.tech_debt_hours > 100:
                risks.append({
                    "title": "High technical debt may slow migration",
                    "probability": 3,
                    "impact": 3,
                    "mitigation": "Include debt reduction in migration scope"
                })

            risks.append({
                "title": "Knowledge loss during migration",
                "probability": 3,
                "impact": 4,
                "mitigation": "Document legacy system, involve original developers"
            })

            # Success criteria
            success_criteria = [
                "All functionality migrated and tested",
                "Performance meets or exceeds legacy system",
                "Zero critical security vulnerabilities",
                "100% of automated tests passing",
                "User acceptance sign-off obtained",
                "Documentation complete",
            ]

            # Update plan
            plan.migration_strategy = strategy_key
            plan.migration_phases = migration_phases
            plan.timeline_weeks = timeline_weeks
            plan.milestones = milestones
            plan.prerequisites = prerequisites
            plan.external_dependencies = external_deps
            plan.risks = risks
            plan.blockers = assessment.blockers or []
            plan.recommendations = [
                {"category": "process", "priority": "high", "title": "Follow migration strategy", "description": f"Use {strategy['name']} approach for this project"},
                {"category": "team", "priority": "medium", "title": "Team composition", "description": f"Recommend {plan.team_size_recommended} team members"},
            ]
            plan.success_criteria = success_criteria

            duration = (datetime.now(timezone.utc) - start_time).seconds

            return PhaseResult(
                success=True,
                phase_name="strategy",
                data={
                    "strategy": strategy_key,
                    "timeline_weeks": timeline_weeks,
                    "phases": len(migration_phases),
                    "risks": len(risks)
                },
                duration_seconds=duration,
                items_processed=1,
                items_found=len(migration_phases)
            )

        except Exception as e:
            return PhaseResult(
                success=False,
                phase_name="strategy",
                data={},
                error=str(e)
            )

    async def _run_report_phase(
        self,
        plan: MigrationPlan,
        assessment: ProjectAssessment
    ) -> PhaseResult:
        """Phase 10: Migration Report Generation (Diana)"""
        start_time = datetime.now(timezone.utc)

        try:
            strategy = MIGRATION_STRATEGIES.get(plan.migration_strategy, {})
            tech_config = TARGET_TECHNOLOGIES.get(plan.target_technology, {})

            report_lines = [
                f"# Migration Plan: {assessment.project_name}",
                "",
                f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
                f"**Assessment ID**: {assessment.id}",
                "",
                "---",
                "",
                "## Executive Summary",
                "",
                f"This migration plan outlines the approach for migrating **{assessment.project_name}** ",
                f"from {assessment.primary_stack or 'legacy stack'} to {tech_config.get('name', plan.target_technology)}.",
                "",
                f"- **Estimated Effort**: {plan.adjusted_fp} Function Points ({plan.total_weeks} weeks)",
                f"- **Recommended Team Size**: {plan.team_size_recommended} developers",
                f"- **Migration Strategy**: {strategy.get('name', plan.migration_strategy)}",
                f"- **Risk Level**: {strategy.get('risk_level', 'medium').upper()}",
                "",
                "## Source System Assessment",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Primary Stack | {assessment.primary_stack or 'Unknown'} |",
                f"| Total Files | {assessment.file_count:,} |",
                f"| Total Lines | {assessment.line_count:,} |",
                f"| Architecture Score | {assessment.architecture_score}/100 |",
                f"| Security Grade | {assessment.security_grade or 'N/A'} |",
                f"| Quality Grade | {assessment.quality_grade or 'N/A'} |",
                f"| Overall Health | {assessment.overall_grade or 'N/A'} |",
                "",
                "## Target Architecture",
                "",
                f"**Pattern**: {plan.architecture_pattern}",
                "",
                "### Layers",
                "",
            ]

            for layer in (plan.architecture_layers or []):
                report_lines.append(f"- **{layer.get('name')}**: {layer.get('responsibility')}")

            report_lines.extend([
                "",
                "## Effort Estimation (IFPUG)",
                "",
                f"| Component | Value |",
                f"|-----------|-------|",
                f"| Unadjusted FP | {plan.unadjusted_fp} |",
                f"| VAF | {plan.vaf} |",
                f"| Adjusted FP | {plan.adjusted_fp} |",
                f"| Total Hours | {plan.total_hours:,} |",
                f"| Total Days | {plan.total_days:,} |",
                f"| Total Weeks | {plan.total_weeks} |",
                "",
                "### Phase Breakdown",
                "",
            ])

            for phase in (plan.phase_breakdown or []):
                report_lines.append(f"- **{phase.get('phase')}**: {phase.get('percentage')}% ({int(phase.get('hours', 0))} hours)")

            report_lines.extend([
                "",
                "## Migration Strategy",
                "",
                f"**Strategy**: {strategy.get('name', plan.migration_strategy)}",
                "",
                f"> {strategy.get('description', '')}",
                "",
                "### Timeline",
                "",
                f"Total Duration: **{plan.timeline_weeks} weeks**",
                "",
            ])

            for phase in (plan.migration_phases or []):
                report_lines.append(f"- **{phase.get('name')}** ({phase.get('duration_weeks')} weeks): {phase.get('description')}")

            report_lines.extend([
                "",
                "## Risks",
                "",
            ])

            for risk in (plan.risks or []):
                report_lines.append(f"- **{risk.get('title')}** (P:{risk.get('probability')}/I:{risk.get('impact')})")
                report_lines.append(f"  - Mitigation: {risk.get('mitigation')}")

            report_lines.extend([
                "",
                "## Success Criteria",
                "",
            ])

            for criterion in (plan.success_criteria or []):
                report_lines.append(f"- [ ] {criterion}")

            report_lines.extend([
                "",
                "---",
                "",
                "*This migration plan was generated by the MarQed AI Agent Platform.*",
                "*Human review and approval required before execution.*",
            ])

            plan.report_type = "full_migration_plan"
            plan.report_content = "\n".join(report_lines)
            plan.report_metadata = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sections": ["executive_summary", "assessment", "architecture", "estimation", "strategy", "risks", "success_criteria"],
                "word_count": len(" ".join(report_lines).split())
            }

            duration = (datetime.now(timezone.utc) - start_time).seconds

            return PhaseResult(
                success=True,
                phase_name="report",
                data={
                    "report_type": plan.report_type,
                    "word_count": plan.report_metadata.get("word_count", 0)
                },
                duration_seconds=duration,
                items_processed=1,
                items_found=1
            )

        except Exception as e:
            return PhaseResult(
                success=False,
                phase_name="report",
                data={},
                error=str(e)
            )

    async def approve_plan(
        self,
        plan_id: UUID,
        reviewer: str,
        notes: Optional[str] = None
    ) -> MigrationPlan:
        """Approve a migration plan after human review"""
        result = await self.db.execute(
            select(MigrationPlan).where(MigrationPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        if plan.status != "in_review":
            raise ValueError(f"Plan must be in_review to approve. Current status: {plan.status}")

        plan.status = "approved"
        plan.reviewed_by = reviewer
        plan.reviewed_at = datetime.now(timezone.utc)
        plan.review_notes = notes

        await self.db.commit()
        return plan

    async def reject_plan(
        self,
        plan_id: UUID,
        reviewer: str,
        notes: str
    ) -> MigrationPlan:
        """Reject a migration plan"""
        result = await self.db.execute(
            select(MigrationPlan).where(MigrationPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        plan.status = "rejected"
        plan.reviewed_by = reviewer
        plan.reviewed_at = datetime.now(timezone.utc)
        plan.review_notes = notes

        await self.db.commit()
        return plan


async def run_migration_planning(
    db: AsyncSession,
    assessment_id: UUID,
    target_technology: str,
    target_database: Optional[str] = None,
    target_frontend: Optional[str] = None,
    use_llm: bool = False
) -> MigrationPlan:
    """
    Convenience function to run complete migration planning

    Args:
        db: Database session
        assessment_id: ID of completed ProjectAssessment
        target_technology: Target technology stack
        target_database: Optional target database
        target_frontend: Optional target frontend
        use_llm: Enable LLM-enhanced analysis (default: False)

    Returns:
        Completed MigrationPlan (in_review status)
    """
    orchestrator = MigrationPlanningOrchestrator(db, use_llm=use_llm)
    plan = await orchestrator.start_planning(
        assessment_id=assessment_id,
        target_technology=target_technology,
        target_database=target_database,
        target_frontend=target_frontend
    )
    return await orchestrator.run_planning(plan.id)
