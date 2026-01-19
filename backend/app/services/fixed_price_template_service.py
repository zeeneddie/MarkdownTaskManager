"""
Fixed-Price Template Service (A2 - Fase 24).

Contract template generator for fixed-price legacy modernization projects.
Provides transparent risk allocation, milestone definitions, and pricing models.

Author: Claude Code (Week 158)
Date: 2026-01-19
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class RiskOwner(str, Enum):
    """Risk allocation owner."""
    CLIENT = "client"
    VENDOR = "vendor"
    SHARED = "shared"


class RiskCategory(str, Enum):
    """Risk categories for migration projects."""
    SCOPE_CREEP = "scope_creep"
    TECHNICAL_COMPLEXITY = "technical_complexity"
    DATA_QUALITY = "data_quality"
    TIMELINE_DELAY = "timeline_delay"
    RESOURCE_AVAILABILITY = "resource_availability"
    INTEGRATION_ISSUES = "integration_issues"
    SECURITY_COMPLIANCE = "security_compliance"
    TESTING_COVERAGE = "testing_coverage"


class ProjectPhase(str, Enum):
    """Standard migration project phases."""
    DISCOVERY = "discovery"
    ANALYSIS = "analysis"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    MIGRATION = "migration"
    HYPERCARE = "hypercare"


class ChangeRequestStatus(str, Enum):
    """Change request status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


# Default risk buffer percentages per phase
DEFAULT_RISK_BUFFERS = {
    ProjectPhase.DISCOVERY: 0.05,
    ProjectPhase.ANALYSIS: 0.10,
    ProjectPhase.DESIGN: 0.10,
    ProjectPhase.DEVELOPMENT: 0.15,
    ProjectPhase.TESTING: 0.10,
    ProjectPhase.MIGRATION: 0.20,
    ProjectPhase.HYPERCARE: 0.05,
}

# Default risk allocation matrix
DEFAULT_RISK_ALLOCATION = {
    RiskCategory.SCOPE_CREEP: RiskOwner.SHARED,
    RiskCategory.TECHNICAL_COMPLEXITY: RiskOwner.VENDOR,
    RiskCategory.DATA_QUALITY: RiskOwner.CLIENT,
    RiskCategory.TIMELINE_DELAY: RiskOwner.SHARED,
    RiskCategory.RESOURCE_AVAILABILITY: RiskOwner.SHARED,
    RiskCategory.INTEGRATION_ISSUES: RiskOwner.VENDOR,
    RiskCategory.SECURITY_COMPLIANCE: RiskOwner.SHARED,
    RiskCategory.TESTING_COVERAGE: RiskOwner.VENDOR,
}


@dataclass
class PhaseEstimate:
    """Estimate for a single project phase."""
    phase: ProjectPhase
    description: str
    base_price: float
    risk_buffer_percent: float
    duration_weeks: int
    team_size: int
    deliverables: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)

    @property
    def risk_buffer_amount(self) -> float:
        return self.base_price * self.risk_buffer_percent

    @property
    def total_price(self) -> float:
        return self.base_price + self.risk_buffer_amount

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "description": self.description,
            "base_price": self.base_price,
            "risk_buffer_percent": f"{self.risk_buffer_percent * 100:.0f}%",
            "risk_buffer_amount": self.risk_buffer_amount,
            "total_price": self.total_price,
            "duration_weeks": self.duration_weeks,
            "team_size": self.team_size,
            "deliverables": self.deliverables,
            "acceptance_criteria": self.acceptance_criteria,
        }


@dataclass
class Milestone:
    """Project milestone with payment trigger."""
    milestone_id: str
    name: str
    phase: ProjectPhase
    description: str
    deliverables: List[str]
    acceptance_criteria: List[str]
    payment_percent: float
    due_date: Optional[datetime] = None
    status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "name": self.name,
            "phase": self.phase.value,
            "description": self.description,
            "deliverables": self.deliverables,
            "acceptance_criteria": self.acceptance_criteria,
            "payment_percent": f"{self.payment_percent * 100:.0f}%",
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
        }


@dataclass
class RiskAllocation:
    """Risk allocation entry."""
    category: RiskCategory
    owner: RiskOwner
    description: str
    mitigation_strategy: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "owner": self.owner.value,
            "description": self.description,
            "mitigation_strategy": self.mitigation_strategy,
        }


@dataclass
class ChangeRequestProcedure:
    """Change request handling procedure."""
    max_response_days: int = 5
    approval_threshold_percent: float = 0.10
    escalation_contacts: List[str] = field(default_factory=list)
    pricing_formula: str = "hourly_rate * estimated_hours * complexity_factor"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_response_days": self.max_response_days,
            "approval_threshold_percent": f"{self.approval_threshold_percent * 100:.0f}%",
            "escalation_contacts": self.escalation_contacts,
            "pricing_formula": self.pricing_formula,
            "procedure_steps": [
                "1. Client submits change request via project portal",
                "2. Vendor acknowledges within 2 business days",
                f"3. Impact assessment completed within {self.max_response_days} business days",
                "4. Pricing and timeline impact communicated to client",
                f"5. Changes under {self.approval_threshold_percent * 100:.0f}% of total budget: PM approval",
                f"6. Changes over {self.approval_threshold_percent * 100:.0f}% of total budget: Steering committee approval",
                "7. Signed change order before work begins",
            ],
        }


@dataclass
class FixedPriceContract:
    """Complete fixed-price contract template."""
    contract_id: UUID
    project_name: str
    client_name: str
    vendor_name: str
    created_at: datetime

    # Source system info (from Quickscan)
    source_system: str
    source_technology: str
    source_loc: int
    complexity_score: float

    # Target system info
    target_platform: str
    target_technology: str

    # Pricing
    phase_estimates: List[PhaseEstimate] = field(default_factory=list)
    total_base_price: float = 0.0
    total_risk_buffer: float = 0.0
    total_price: float = 0.0
    currency: str = "EUR"

    # Schedule
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_duration_weeks: int = 0

    # Risk
    risk_allocations: List[RiskAllocation] = field(default_factory=list)

    # Milestones
    milestones: List[Milestone] = field(default_factory=list)

    # Change management
    change_procedure: Optional[ChangeRequestProcedure] = None

    # SLA
    sla_terms: Dict[str, Any] = field(default_factory=dict)

    def calculate_totals(self) -> None:
        """Calculate total prices and duration."""
        self.total_base_price = sum(p.base_price for p in self.phase_estimates)
        self.total_risk_buffer = sum(p.risk_buffer_amount for p in self.phase_estimates)
        self.total_price = self.total_base_price + self.total_risk_buffer
        self.total_duration_weeks = sum(p.duration_weeks for p in self.phase_estimates)

        if self.start_date:
            self.end_date = self.start_date + timedelta(weeks=self.total_duration_weeks)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": str(self.contract_id),
            "project_name": self.project_name,
            "client_name": self.client_name,
            "vendor_name": self.vendor_name,
            "created_at": self.created_at.isoformat(),
            "source_system": {
                "name": self.source_system,
                "technology": self.source_technology,
                "lines_of_code": self.source_loc,
                "complexity_score": self.complexity_score,
            },
            "target_system": {
                "platform": self.target_platform,
                "technology": self.target_technology,
            },
            "pricing": {
                "currency": self.currency,
                "phases": [p.to_dict() for p in self.phase_estimates],
                "total_base_price": self.total_base_price,
                "total_risk_buffer": self.total_risk_buffer,
                "average_risk_buffer_percent": f"{(self.total_risk_buffer / self.total_base_price * 100):.1f}%" if self.total_base_price else "0%",
                "total_price": self.total_price,
            },
            "schedule": {
                "start_date": self.start_date.isoformat() if self.start_date else None,
                "end_date": self.end_date.isoformat() if self.end_date else None,
                "total_duration_weeks": self.total_duration_weeks,
            },
            "risk_allocation": [r.to_dict() for r in self.risk_allocations],
            "milestones": [m.to_dict() for m in self.milestones],
            "change_procedure": self.change_procedure.to_dict() if self.change_procedure else None,
            "sla_terms": self.sla_terms,
        }

    def to_markdown(self) -> str:
        """Generate markdown contract document."""
        lines = [
            f"# FIXED-PRICE LEGACY MODERNIZATION CONTRACT",
            f"",
            f"**Contract ID:** {self.contract_id}",
            f"**Date:** {self.created_at.strftime('%Y-%m-%d')}",
            f"",
            f"---",
            f"",
            f"## 1. PARTIES",
            f"",
            f"**Client:** {self.client_name}",
            f"**Vendor:** {self.vendor_name}",
            f"",
            f"---",
            f"",
            f"## 2. PROJECT SCOPE",
            f"",
            f"### 2.1 Source System",
            f"- **System Name:** {self.source_system}",
            f"- **Technology Stack:** {self.source_technology}",
            f"- **Lines of Code:** {self.source_loc:,}",
            f"- **Complexity Score:** {self.complexity_score:.1f}/100",
            f"",
            f"### 2.2 Target System",
            f"- **Target Platform:** {self.target_platform}",
            f"- **Target Technology:** {self.target_technology}",
            f"",
            f"---",
            f"",
            f"## 3. PRICING MODEL",
            f"",
            f"| Phase | Base Price | Risk Buffer | Total |",
            f"|-------|------------|-------------|-------|",
        ]

        for phase in self.phase_estimates:
            lines.append(
                f"| {phase.phase.value.title()} | {self.currency} {phase.base_price:,.0f} | "
                f"{phase.risk_buffer_percent*100:.0f}% ({self.currency} {phase.risk_buffer_amount:,.0f}) | "
                f"{self.currency} {phase.total_price:,.0f} |"
            )

        avg_buffer = (self.total_risk_buffer / self.total_base_price * 100) if self.total_base_price else 0
        lines.extend([
            f"| **TOTAL** | **{self.currency} {self.total_base_price:,.0f}** | "
            f"**{avg_buffer:.1f}% ({self.currency} {self.total_risk_buffer:,.0f})** | "
            f"**{self.currency} {self.total_price:,.0f}** |",
            f"",
            f"---",
            f"",
            f"## 4. RISK ALLOCATION MATRIX",
            f"",
            f"| Risk Category | Owner | Description |",
            f"|---------------|-------|-------------|",
        ])

        for risk in self.risk_allocations:
            owner_symbol = {"client": "Client", "vendor": "Vendor", "shared": "Shared"}.get(risk.owner.value, risk.owner.value)
            lines.append(f"| {risk.category.value.replace('_', ' ').title()} | {owner_symbol} | {risk.description} |")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 5. MILESTONES & PAYMENT SCHEDULE",
            f"",
            f"| # | Milestone | Phase | Payment | Due Date |",
            f"|---|-----------|-------|---------|----------|",
        ])

        for i, milestone in enumerate(self.milestones, 1):
            due = milestone.due_date.strftime('%Y-%m-%d') if milestone.due_date else "TBD"
            payment = f"{milestone.payment_percent * 100:.0f}%"
            lines.append(f"| {i} | {milestone.name} | {milestone.phase.value.title()} | {payment} | {due} |")

        lines.extend([
            f"",
            f"### Acceptance Criteria per Milestone",
            f"",
        ])

        for milestone in self.milestones:
            lines.append(f"**{milestone.name}:**")
            for criterion in milestone.acceptance_criteria:
                lines.append(f"- [ ] {criterion}")
            lines.append("")

        lines.extend([
            f"---",
            f"",
            f"## 6. CHANGE REQUEST PROCEDURE",
            f"",
        ])

        if self.change_procedure:
            for step in self.change_procedure.to_dict()["procedure_steps"]:
                lines.append(step)
            lines.append("")
            lines.append(f"**Pricing Formula:** `{self.change_procedure.pricing_formula}`")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 7. SERVICE LEVEL AGREEMENT",
            f"",
        ])

        if self.sla_terms:
            for key, value in self.sla_terms.items():
                lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 8. SIGNATURES",
            f"",
            f"**Client Representative:**",
            f"",
            f"Name: ___________________________ Date: _______________",
            f"",
            f"Signature: ___________________________",
            f"",
            f"",
            f"**Vendor Representative:**",
            f"",
            f"Name: ___________________________ Date: _______________",
            f"",
            f"Signature: ___________________________",
        ])

        return "\n".join(lines)


class FixedPriceTemplateService:
    """
    Service for generating fixed-price contract templates.

    Features:
    - Auto-fill from Quickscan results
    - Risk matrix calculation
    - Milestone definition with payment triggers
    - Change request procedures
    - SLA templates
    """

    def __init__(
        self,
        hourly_rate: float = 125.0,
        currency: str = "EUR",
    ):
        """
        Initialize service.

        Args:
            hourly_rate: Default hourly rate for calculations
            currency: Currency code
        """
        self.hourly_rate = hourly_rate
        self.currency = currency
        self.contracts: Dict[UUID, FixedPriceContract] = {}

    def generate_contract(
        self,
        project_name: str,
        client_name: str,
        vendor_name: str,
        quickscan_result: Dict[str, Any],
        target_platform: str,
        target_technology: str,
        start_date: Optional[datetime] = None,
        custom_risk_allocation: Optional[Dict[RiskCategory, RiskOwner]] = None,
    ) -> FixedPriceContract:
        """
        Generate a fixed-price contract from Quickscan results.

        Args:
            project_name: Project name
            client_name: Client organization name
            vendor_name: Vendor organization name
            quickscan_result: Results from Legacy Quickscan
            target_platform: Target platform (e.g., "Azure", "AWS")
            target_technology: Target technology (e.g., ".NET 8", "Java Spring")
            start_date: Project start date
            custom_risk_allocation: Override default risk allocation

        Returns:
            Generated contract
        """
        contract = FixedPriceContract(
            contract_id=uuid4(),
            project_name=project_name,
            client_name=client_name,
            vendor_name=vendor_name,
            created_at=datetime.now(timezone.utc),
            source_system=quickscan_result.get("project_name", "Unknown"),
            source_technology=quickscan_result.get("technology_stack", "Unknown"),
            source_loc=quickscan_result.get("lines_of_code", 0),
            complexity_score=quickscan_result.get("complexity_score", 50),
            target_platform=target_platform,
            target_technology=target_technology,
            start_date=start_date,
            currency=self.currency,
        )

        # Generate phase estimates based on LOC and complexity
        contract.phase_estimates = self._calculate_phase_estimates(
            loc=contract.source_loc,
            complexity=contract.complexity_score,
        )

        # Generate risk allocation
        risk_allocation = custom_risk_allocation or DEFAULT_RISK_ALLOCATION
        contract.risk_allocations = self._generate_risk_allocation(risk_allocation)

        # Generate milestones
        contract.milestones = self._generate_milestones(
            phase_estimates=contract.phase_estimates,
            start_date=start_date,
        )

        # Add change procedure
        contract.change_procedure = ChangeRequestProcedure(
            max_response_days=5,
            approval_threshold_percent=0.10,
            escalation_contacts=[
                f"Project Manager - {vendor_name}",
                f"Account Manager - {vendor_name}",
                f"Project Sponsor - {client_name}",
            ],
        )

        # Add SLA terms
        contract.sla_terms = self._generate_sla_terms()

        # Calculate totals
        contract.calculate_totals()

        # Store contract
        self.contracts[contract.contract_id] = contract

        logger.info(f"Generated contract: {contract.contract_id} for {project_name}")
        return contract

    def _calculate_phase_estimates(
        self,
        loc: int,
        complexity: float,
    ) -> List[PhaseEstimate]:
        """Calculate phase estimates based on LOC and complexity."""
        # Complexity factor: 0.5 (simple) to 2.0 (very complex)
        complexity_factor = 0.5 + (complexity / 100) * 1.5

        # Base effort calculation (person-days per 1000 LOC)
        base_effort_per_kloc = 5 * complexity_factor
        total_effort_days = (loc / 1000) * base_effort_per_kloc

        # Distribute effort across phases
        phase_distribution = {
            ProjectPhase.DISCOVERY: 0.05,
            ProjectPhase.ANALYSIS: 0.15,
            ProjectPhase.DESIGN: 0.10,
            ProjectPhase.DEVELOPMENT: 0.40,
            ProjectPhase.TESTING: 0.15,
            ProjectPhase.MIGRATION: 0.10,
            ProjectPhase.HYPERCARE: 0.05,
        }

        estimates = []
        daily_rate = self.hourly_rate * 8

        for phase, distribution in phase_distribution.items():
            phase_effort = total_effort_days * distribution
            phase_weeks = max(1, int(phase_effort / 5))  # 5 days per week
            team_size = max(1, int(phase_effort / (phase_weeks * 5)))
            base_price = phase_effort * daily_rate

            estimates.append(PhaseEstimate(
                phase=phase,
                description=self._get_phase_description(phase),
                base_price=round(base_price, -2),  # Round to hundreds
                risk_buffer_percent=DEFAULT_RISK_BUFFERS[phase],
                duration_weeks=phase_weeks,
                team_size=team_size,
                deliverables=self._get_phase_deliverables(phase),
                acceptance_criteria=self._get_phase_acceptance_criteria(phase),
            ))

        return estimates

    def _get_phase_description(self, phase: ProjectPhase) -> str:
        """Get description for a phase."""
        descriptions = {
            ProjectPhase.DISCOVERY: "Initial assessment and project setup",
            ProjectPhase.ANALYSIS: "Detailed analysis of legacy system and requirements",
            ProjectPhase.DESIGN: "Architecture and detailed design of target system",
            ProjectPhase.DEVELOPMENT: "Implementation and unit testing",
            ProjectPhase.TESTING: "Integration, system, and UAT testing",
            ProjectPhase.MIGRATION: "Data migration and cutover execution",
            ProjectPhase.HYPERCARE: "Post-go-live support and stabilization",
        }
        return descriptions.get(phase, "Phase activities")

    def _get_phase_deliverables(self, phase: ProjectPhase) -> List[str]:
        """Get deliverables for a phase."""
        deliverables = {
            ProjectPhase.DISCOVERY: [
                "Project charter",
                "Stakeholder register",
                "Initial risk assessment",
                "Communication plan",
            ],
            ProjectPhase.ANALYSIS: [
                "As-Is architecture documentation",
                "Business rules inventory",
                "Data dictionary",
                "Interface catalog",
                "Gap analysis report",
            ],
            ProjectPhase.DESIGN: [
                "To-Be architecture design",
                "Database design",
                "API specifications",
                "Security design",
                "Migration strategy document",
            ],
            ProjectPhase.DEVELOPMENT: [
                "Source code (version controlled)",
                "Unit test suite",
                "Code review reports",
                "CI/CD pipeline",
                "Technical documentation",
            ],
            ProjectPhase.TESTING: [
                "Test plans and cases",
                "Test execution reports",
                "Defect reports",
                "Performance test results",
                "Security scan reports",
            ],
            ProjectPhase.MIGRATION: [
                "Migration scripts",
                "Rollback procedures",
                "Data validation report",
                "Cutover checklist",
                "Go-live sign-off",
            ],
            ProjectPhase.HYPERCARE: [
                "Incident reports",
                "Performance monitoring reports",
                "Knowledge transfer sessions",
                "Operations runbook",
                "Project closure report",
            ],
        }
        return deliverables.get(phase, [])

    def _get_phase_acceptance_criteria(self, phase: ProjectPhase) -> List[str]:
        """Get acceptance criteria for a phase."""
        criteria = {
            ProjectPhase.DISCOVERY: [
                "Project charter approved by steering committee",
                "All stakeholders identified and contacted",
                "Initial risks documented and assigned owners",
            ],
            ProjectPhase.ANALYSIS: [
                "100% of legacy features documented",
                "All business rules validated with SMEs",
                "Data model complete and reviewed",
            ],
            ProjectPhase.DESIGN: [
                "Architecture approved by technical board",
                "All interfaces documented",
                "Security requirements addressed",
            ],
            ProjectPhase.DEVELOPMENT: [
                "All features implemented per specifications",
                "Code coverage > 80%",
                "No critical or high severity bugs",
            ],
            ProjectPhase.TESTING: [
                "All test cases executed",
                "UAT sign-off obtained",
                "Performance benchmarks met",
            ],
            ProjectPhase.MIGRATION: [
                "Data migration 100% complete",
                "Data integrity validated",
                "Rollback tested successfully",
            ],
            ProjectPhase.HYPERCARE: [
                "System stable for 2 weeks",
                "No P1/P2 incidents open",
                "Knowledge transfer complete",
            ],
        }
        return criteria.get(phase, [])

    def _generate_risk_allocation(
        self,
        allocation: Dict[RiskCategory, RiskOwner],
    ) -> List[RiskAllocation]:
        """Generate risk allocation entries."""
        descriptions = {
            RiskCategory.SCOPE_CREEP: "Changes to project scope after contract signing",
            RiskCategory.TECHNICAL_COMPLEXITY: "Unforeseen technical challenges during implementation",
            RiskCategory.DATA_QUALITY: "Data quality issues in source system",
            RiskCategory.TIMELINE_DELAY: "Project delays due to various factors",
            RiskCategory.RESOURCE_AVAILABILITY: "Key personnel availability",
            RiskCategory.INTEGRATION_ISSUES: "Issues integrating with external systems",
            RiskCategory.SECURITY_COMPLIANCE: "Security and compliance requirements",
            RiskCategory.TESTING_COVERAGE: "Insufficient test coverage",
        }

        mitigations = {
            RiskCategory.SCOPE_CREEP: "Change request procedure with impact assessment",
            RiskCategory.TECHNICAL_COMPLEXITY: "Technical spikes and proof-of-concepts",
            RiskCategory.DATA_QUALITY: "Data profiling and cleansing before migration",
            RiskCategory.TIMELINE_DELAY: "Regular status meetings and early warning system",
            RiskCategory.RESOURCE_AVAILABILITY: "Backup resources identified upfront",
            RiskCategory.INTEGRATION_ISSUES: "Interface testing in early phases",
            RiskCategory.SECURITY_COMPLIANCE: "Security reviews at each phase gate",
            RiskCategory.TESTING_COVERAGE: "Test coverage requirements in acceptance criteria",
        }

        return [
            RiskAllocation(
                category=cat,
                owner=owner,
                description=descriptions.get(cat, ""),
                mitigation_strategy=mitigations.get(cat, ""),
            )
            for cat, owner in allocation.items()
        ]

    def _generate_milestones(
        self,
        phase_estimates: List[PhaseEstimate],
        start_date: Optional[datetime],
    ) -> List[Milestone]:
        """Generate milestones from phase estimates."""
        milestones = []
        current_date = start_date or datetime.now(timezone.utc)

        # Payment distribution per phase
        payment_distribution = {
            ProjectPhase.DISCOVERY: 0.05,
            ProjectPhase.ANALYSIS: 0.15,
            ProjectPhase.DESIGN: 0.10,
            ProjectPhase.DEVELOPMENT: 0.35,
            ProjectPhase.TESTING: 0.15,
            ProjectPhase.MIGRATION: 0.15,
            ProjectPhase.HYPERCARE: 0.05,
        }

        for i, phase_est in enumerate(phase_estimates):
            milestone = Milestone(
                milestone_id=f"M{i+1:02d}",
                name=f"{phase_est.phase.value.title()} Complete",
                phase=phase_est.phase,
                description=f"Completion of {phase_est.phase.value} phase",
                deliverables=phase_est.deliverables,
                acceptance_criteria=phase_est.acceptance_criteria,
                payment_percent=payment_distribution.get(phase_est.phase, 0.1),
                due_date=current_date + timedelta(weeks=phase_est.duration_weeks),
            )
            milestones.append(milestone)
            current_date = milestone.due_date

        return milestones

    def _generate_sla_terms(self) -> Dict[str, Any]:
        """Generate standard SLA terms."""
        return {
            "response_time_critical": "2 hours",
            "response_time_high": "4 hours",
            "response_time_medium": "8 hours",
            "response_time_low": "24 hours",
            "resolution_time_critical": "8 hours",
            "resolution_time_high": "24 hours",
            "resolution_time_medium": "3 business days",
            "resolution_time_low": "5 business days",
            "availability_target": "99.5%",
            "maintenance_window": "Sundays 02:00-06:00 CET",
            "support_hours": "24/7 for Critical/High, Business hours for Medium/Low",
            "escalation_path": "L1 Support → L2 Support → Development Team → Project Manager",
        }

    def get_contract(self, contract_id: UUID) -> Optional[FixedPriceContract]:
        """Get contract by ID."""
        return self.contracts.get(contract_id)

    def export_markdown(self, contract_id: UUID) -> Optional[str]:
        """Export contract as markdown."""
        contract = self.contracts.get(contract_id)
        if contract:
            return contract.to_markdown()
        return None

    def export_json(self, contract_id: UUID) -> Optional[Dict[str, Any]]:
        """Export contract as JSON."""
        contract = self.contracts.get(contract_id)
        if contract:
            return contract.to_dict()
        return None


def create_fixed_price_template_service(
    hourly_rate: float = 125.0,
    currency: str = "EUR",
) -> FixedPriceTemplateService:
    """Factory function to create Fixed-Price Template service."""
    return FixedPriceTemplateService(hourly_rate=hourly_rate, currency=currency)
