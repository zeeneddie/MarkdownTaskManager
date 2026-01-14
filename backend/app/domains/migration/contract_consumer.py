# Analysis Contract Consumer
# Consumes AnalysisContract to create MigrationContext
#
# This consumer is THE key component that makes Migration independent
# from Brown Paper. It consumes a standard AnalysisContract and creates
# the context needed for the 7-phase migration workflow.
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 (Week 145-146)

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

from ...contracts import (
    AnalysisContract,
    AnalysisSourceType,
    DomainSummary,
    ModuleSummary,
    EpicSummary,
    StabilityInfo,
)

logger = logging.getLogger(__name__)


@dataclass
class MigrationRisk:
    """A migration risk identified from analysis."""
    category: str  # stability, complexity, size, dependency
    severity: str  # critical, high, medium, low
    description: str
    mitigation: str = ""
    source: str = ""  # Where this risk was identified


@dataclass
class MigrationPhaseConfig:
    """Configuration for a migration phase."""
    phase_number: int
    name: str
    description: str
    estimated_hours: float = 0.0
    dependencies: List[int] = field(default_factory=list)
    focus_domains: List[str] = field(default_factory=list)


@dataclass
class MigrationContext:
    """
    Context for migration execution.
    Created from AnalysisContract, contains everything Migration needs.

    Key principle: NO reference to brown_paper_session_id, only analysis_id.
    """
    # === Identity ===
    analysis_id: str  # Reference to source contract
    project_name: str
    project_path: str

    # === Project Analysis ===
    total_domains: int = 0
    total_modules: int = 0
    total_epics: int = 0
    total_features: int = 0
    estimated_fp: float = 0.0
    estimated_weeks: float = 0.0

    # === Risk Assessment ===
    overall_risk_level: str = "low"  # critical, high, medium, low
    stability_score: int = 100
    risks: List[MigrationRisk] = field(default_factory=list)

    # === Domain Priorities ===
    # Domains ordered by migration priority
    domain_priority: List[str] = field(default_factory=list)

    # === Phase Configuration ===
    phases: List[MigrationPhaseConfig] = field(default_factory=list)

    # === Detailed Data (for phase execution) ===
    domains: List[Dict[str, Any]] = field(default_factory=list)
    modules: List[Dict[str, Any]] = field(default_factory=list)
    epics: List[Dict[str, Any]] = field(default_factory=list)
    stability_findings: List[Dict[str, Any]] = field(default_factory=list)

    # === Metadata ===
    source_type: str = "brown_paper"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analysis_id": self.analysis_id,
            "project_name": self.project_name,
            "project_path": self.project_path,
            "total_domains": self.total_domains,
            "total_modules": self.total_modules,
            "total_epics": self.total_epics,
            "total_features": self.total_features,
            "estimated_fp": self.estimated_fp,
            "estimated_weeks": self.estimated_weeks,
            "overall_risk_level": self.overall_risk_level,
            "stability_score": self.stability_score,
            "risks": [
                {
                    "category": r.category,
                    "severity": r.severity,
                    "description": r.description,
                    "mitigation": r.mitigation,
                }
                for r in self.risks
            ],
            "domain_priority": self.domain_priority,
            "phases": [
                {
                    "phase_number": p.phase_number,
                    "name": p.name,
                    "description": p.description,
                    "estimated_hours": p.estimated_hours,
                }
                for p in self.phases
            ],
            "source_type": self.source_type,
            "created_at": self.created_at.isoformat(),
        }


class AnalysisContractConsumer:
    """
    Consumer that creates MigrationContext from AnalysisContract.

    Usage:
        consumer = AnalysisContractConsumer()
        is_valid, issues = consumer.validate_for_migration(contract)
        if is_valid:
            context = consumer.consume(contract)

    The context contains everything needed for Migration,
    with NO reference to Brown Paper internals.
    """

    # 7-Phase Migration Workflow
    MIGRATION_PHASES = [
        MigrationPhaseConfig(
            phase_number=1,
            name="Foundation Setup",
            description="Set up target architecture, CI/CD, and core infrastructure",
        ),
        MigrationPhaseConfig(
            phase_number=2,
            name="Database Migration",
            description="Migrate database schema and data",
            dependencies=[1],
        ),
        MigrationPhaseConfig(
            phase_number=3,
            name="Core Services",
            description="Migrate core business logic and services",
            dependencies=[1, 2],
        ),
        MigrationPhaseConfig(
            phase_number=4,
            name="Integration Layer",
            description="Migrate APIs and external integrations",
            dependencies=[3],
        ),
        MigrationPhaseConfig(
            phase_number=5,
            name="Quality Validation",
            description="Run quality gates and validation tests",
            dependencies=[3, 4],
        ),
        MigrationPhaseConfig(
            phase_number=6,
            name="Deployment",
            description="Deploy to target environment",
            dependencies=[5],
        ),
        MigrationPhaseConfig(
            phase_number=7,
            name="Cutover",
            description="Final cutover and decommission legacy",
            dependencies=[6],
        ),
    ]

    def validate_for_migration(
        self,
        contract: AnalysisContract,
    ) -> Tuple[bool, List[str]]:
        """
        Validate if contract has sufficient data for migration.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        return contract.validate_for_migration()

    def consume(
        self,
        contract: AnalysisContract,
    ) -> MigrationContext:
        """
        Consume AnalysisContract and create MigrationContext.

        Args:
            contract: The analysis contract to consume

        Returns:
            MigrationContext ready for 7-phase migration

        Raises:
            ValueError: If contract is invalid for migration
        """
        logger.info(f"Consuming AnalysisContract {contract.analysis_id} for migration")

        # Validate first
        is_valid, issues = self.validate_for_migration(contract)
        if not is_valid:
            raise ValueError(f"Contract not valid for migration: {', '.join(issues)}")

        # Assess risks
        risks = self._assess_risks(contract)
        overall_risk = self._calculate_overall_risk(risks, contract.stability)

        # Prioritize domains
        domain_priority = self._prioritize_domains(contract.domains, contract.stability)

        # Configure phases
        phases = self._configure_phases(contract, domain_priority)

        # Create context
        context = MigrationContext(
            analysis_id=contract.analysis_id,
            project_name=contract.project.name,
            project_path=contract.project.path,
            total_domains=contract.total_domains,
            total_modules=contract.total_modules,
            total_epics=contract.total_epics,
            total_features=contract.total_features,
            estimated_fp=contract.total_fp,
            estimated_weeks=contract.total_weeks,
            overall_risk_level=overall_risk,
            stability_score=contract.stability.overall_score,
            risks=risks,
            domain_priority=domain_priority,
            phases=phases,
            domains=[d.to_dict() for d in contract.domains],
            modules=[m.to_dict() for m in contract.modules],
            epics=[e.to_dict() for e in contract.epics],
            stability_findings=[f.to_dict() for f in contract.stability.top_findings],
            source_type=contract.source_type.value,
            created_at=datetime.now(timezone.utc),
        )

        logger.info(
            f"Created MigrationContext with risk={overall_risk}, "
            f"{len(phases)} phases, {len(domain_priority)} domains"
        )

        return context

    def _assess_risks(
        self,
        contract: AnalysisContract,
    ) -> List[MigrationRisk]:
        """Assess migration risks from contract data."""
        risks = []

        # Stability risks
        if contract.stability.critical_count > 0:
            risks.append(MigrationRisk(
                category="stability",
                severity="critical",
                description=f"{contract.stability.critical_count} critical stability issues found",
                mitigation="Address critical stability issues before migration",
                source="stability_analysis",
            ))
        elif contract.stability.high_count > 5:
            risks.append(MigrationRisk(
                category="stability",
                severity="high",
                description=f"{contract.stability.high_count} high severity stability issues",
                mitigation="Review and prioritize stability fixes",
                source="stability_analysis",
            ))

        # Size/complexity risks
        if contract.total_modules > 100:
            risks.append(MigrationRisk(
                category="size",
                severity="high",
                description=f"Large codebase with {contract.total_modules} modules",
                mitigation="Consider phased migration approach",
                source="module_analysis",
            ))

        if contract.total_fp > 1000:
            risks.append(MigrationRisk(
                category="complexity",
                severity="high",
                description=f"High complexity: {contract.total_fp:.0f} function points",
                mitigation="Plan for extended timeline and thorough testing",
                source="fp_estimation",
            ))

        # Domain coupling risks
        high_complexity_domains = [
            d for d in contract.domains
            if d.estimated_complexity == "high"
        ]
        if len(high_complexity_domains) > 3:
            risks.append(MigrationRisk(
                category="complexity",
                severity="medium",
                description=f"{len(high_complexity_domains)} high-complexity domains",
                mitigation="Prioritize domain dependencies and migration order",
                source="domain_analysis",
            ))

        return risks

    def _calculate_overall_risk(
        self,
        risks: List[MigrationRisk],
        stability: StabilityInfo,
    ) -> str:
        """Calculate overall migration risk level."""
        critical_risks = sum(1 for r in risks if r.severity == "critical")
        high_risks = sum(1 for r in risks if r.severity == "high")

        if critical_risks > 0 or stability.overall_risk == "CRITICAL":
            return "critical"
        elif high_risks > 2 or stability.overall_risk == "HIGH":
            return "high"
        elif high_risks > 0 or stability.overall_risk == "MEDIUM":
            return "medium"
        return "low"

    def _prioritize_domains(
        self,
        domains: List[DomainSummary],
        stability: StabilityInfo,
    ) -> List[str]:
        """
        Prioritize domains for migration order.

        Strategy:
        1. Core/foundational domains first
        2. Lower complexity domains before higher
        3. Domains with fewer stability issues first
        """
        if not domains:
            return []

        # Score each domain
        scored_domains = []
        for domain in domains:
            score = 0

            # Lower complexity = higher priority (migrate first)
            complexity_scores = {"low": 3, "medium": 2, "high": 1}
            score += complexity_scores.get(domain.estimated_complexity, 2) * 10

            # Fewer dependencies = higher priority
            score += max(0, 10 - len(domain.modules))

            # Check for stability issues in domain's modules
            # (simplified - in production would cross-reference with findings)

            scored_domains.append((domain.name, score))

        # Sort by score descending
        scored_domains.sort(key=lambda x: x[1], reverse=True)

        return [name for name, _ in scored_domains]

    def _configure_phases(
        self,
        contract: AnalysisContract,
        domain_priority: List[str],
    ) -> List[MigrationPhaseConfig]:
        """Configure phases with estimates based on contract data."""
        phases = []

        for phase_template in self.MIGRATION_PHASES:
            phase = MigrationPhaseConfig(
                phase_number=phase_template.phase_number,
                name=phase_template.name,
                description=phase_template.description,
                dependencies=phase_template.dependencies.copy(),
                focus_domains=[],
            )

            # Estimate hours based on contract data
            phase.estimated_hours = self._estimate_phase_hours(
                phase.phase_number,
                contract,
            )

            # Assign domains to phases
            if phase.phase_number == 3:  # Core Services
                # First half of domains
                mid = len(domain_priority) // 2
                phase.focus_domains = domain_priority[:mid] if domain_priority else []
            elif phase.phase_number == 4:  # Integration Layer
                # Second half of domains
                mid = len(domain_priority) // 2
                phase.focus_domains = domain_priority[mid:] if domain_priority else []

            phases.append(phase)

        return phases

    def _estimate_phase_hours(
        self,
        phase_number: int,
        contract: AnalysisContract,
    ) -> float:
        """Estimate hours for a phase based on contract data."""
        base_hours = {
            1: 40,   # Foundation Setup
            2: 60,   # Database Migration
            3: 100,  # Core Services
            4: 80,   # Integration Layer
            5: 40,   # Quality Validation
            6: 24,   # Deployment
            7: 16,   # Cutover
        }

        hours = base_hours.get(phase_number, 40)

        # Adjust based on size
        size_multiplier = 1.0
        if contract.total_modules > 50:
            size_multiplier = 1.5
        elif contract.total_modules > 100:
            size_multiplier = 2.0

        # Adjust based on complexity
        complexity_multiplier = 1.0
        if contract.total_fp > 500:
            complexity_multiplier = 1.3
        elif contract.total_fp > 1000:
            complexity_multiplier = 1.6

        return hours * size_multiplier * complexity_multiplier
