"""
Intake to Backlog Service - Bridge between Code Analysis and Project Planning.

Transforms SoftwareIntakeService output (IntakeReport) into:
1. Business Domains (grouped components)
2. Epics (per domain)
3. Features (per epic)
4. Stories (per feature)
5. User Journeys (end-user workflows)

Flow:
    IntakeReport → Domains → Epics → Features → Stories → User Journeys

Week 158 - Created to connect code-driven intake to backlog generation.
Week 158 - Extended with user journey integration.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from uuid import UUID, uuid4

from app.schemas.intake import (
    IntakeReport,
    ComponentMapping,
    DetectedLayer,
    ExtractedBusinessRule,
    Finding,
    Severity,
)
from app.contracts.analysis_contract import DomainSummary, ModuleSummary
from app.confucius.models.user_journey import (
    UserJourney,
    JourneyStep,
    Persona,
    PersonaType,
    JourneyComplexity,
    InteractionType,
    ScreenInfo,
    UserJourneyExtractionResult,
)
from app.services.epic_searchers import (
    CombinedEpicSearcher,
    CombinedSearchConfig,
    DetectedEpic,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================

class DomainType(str, Enum):
    """Types of business domains."""
    CORE = "core"           # Core business logic
    SUPPORTING = "supporting"  # Supporting functions
    GENERIC = "generic"     # Generic/infrastructure
    EXTERNAL = "external"   # External integrations


class EpicType(str, Enum):
    """Types of migration epics."""
    DOMAIN = "domain"           # Business domain epic
    INFRASTRUCTURE = "infrastructure"  # Technical infrastructure
    SECURITY = "security"       # Security remediation
    QUALITY = "quality"         # Quality improvements
    INTEGRATION = "integration"  # External integrations
    DATA = "data"               # Data migration


@dataclass
class ExtractedDomain:
    """A business domain extracted from code analysis."""
    id: str
    name: str
    description: str
    domain_type: DomainType = DomainType.CORE

    # Components in this domain
    components: List[str] = field(default_factory=list)
    modules: List[ModuleSummary] = field(default_factory=list)

    # Business rules in this domain
    business_rules: List[str] = field(default_factory=list)

    # Metrics
    estimated_loc: int = 0
    estimated_fp: float = 0.0
    complexity: str = "medium"

    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    depended_by: List[str] = field(default_factory=list)

    # Priority (calculated)
    priority_score: float = 0.0

    # Additional metadata from epic detection (journey info, actions, messages)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "domain_type": self.domain_type.value,
            "components": self.components,
            "business_rules": self.business_rules,
            "estimated_loc": self.estimated_loc,
            "estimated_fp": self.estimated_fp,
            "complexity": self.complexity,
            "depends_on": self.depends_on,
            "depended_by": self.depended_by,
            "priority_score": self.priority_score,
            "metadata": self.metadata,
        }


@dataclass
class GeneratedEpic:
    """An epic generated from a domain."""
    id: str
    title: str
    description: str
    epic_type: EpicType = EpicType.DOMAIN

    # Source
    source_domain: Optional[str] = None

    # Scope
    components: List[str] = field(default_factory=list)
    business_rules: List[str] = field(default_factory=list)
    security_findings: List[str] = field(default_factory=list)

    # Estimation
    estimated_fp: float = 0.0
    estimated_hours: float = 0.0
    complexity: str = "medium"

    # Priority
    priority: int = 1  # 1=highest

    # Generated features
    features: List["GeneratedFeature"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "epic_type": self.epic_type.value,
            "source_domain": self.source_domain,
            "components": self.components,
            "business_rules": self.business_rules,
            "security_findings": self.security_findings,
            "estimated_fp": self.estimated_fp,
            "estimated_hours": self.estimated_hours,
            "complexity": self.complexity,
            "priority": self.priority,
            "features": [f.to_dict() for f in self.features],
        }


@dataclass
class GeneratedFeature:
    """A feature generated within an epic."""
    id: str
    title: str
    description: str

    # Source
    source_component: Optional[str] = None

    # Estimation
    estimated_fp: float = 0.0
    estimated_hours: float = 0.0

    # Stories
    stories: List["GeneratedStory"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "source_component": self.source_component,
            "estimated_fp": self.estimated_fp,
            "estimated_hours": self.estimated_hours,
            "stories": [s.to_dict() for s in self.stories],
        }


@dataclass
class GeneratedStory:
    """A user story generated within a feature."""
    id: str
    title: str
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)

    # Source
    source_business_rule: Optional[str] = None
    source_finding: Optional[str] = None

    # Estimation
    story_points: int = 0
    estimated_hours: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "source_business_rule": self.source_business_rule,
            "source_finding": self.source_finding,
            "story_points": self.story_points,
            "estimated_hours": self.estimated_hours,
        }


@dataclass
class GeneratedUserJourney:
    """A user journey connecting personas to features/stories."""
    id: str
    name: str
    description: str

    # Persona
    persona_id: str
    persona_name: str
    persona_type: str  # PersonaType value

    # Journey characteristics
    complexity: str  # JourneyComplexity value
    business_value: str  # "high", "medium", "low"
    frequency: str  # "100x/day", "10x/week", etc.

    # Journey flow
    trigger: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    outcome: str = ""

    # Linked items
    related_epics: List[str] = field(default_factory=list)
    related_features: List[str] = field(default_factory=list)
    related_stories: List[str] = field(default_factory=list)
    screens_involved: List[str] = field(default_factory=list)

    # Estimation
    estimated_duration_minutes: int = 5

    # Source
    source_evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "persona_id": self.persona_id,
            "persona_name": self.persona_name,
            "persona_type": self.persona_type,
            "complexity": self.complexity,
            "business_value": self.business_value,
            "frequency": self.frequency,
            "trigger": self.trigger,
            "steps": self.steps,
            "success_criteria": self.success_criteria,
            "outcome": self.outcome,
            "related_epics": self.related_epics,
            "related_features": self.related_features,
            "related_stories": self.related_stories,
            "screens_involved": self.screens_involved,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "source_evidence": self.source_evidence,
            "confidence": self.confidence,
        }


@dataclass
class BacklogGenerationResult:
    """Result of backlog generation from intake."""
    intake_id: UUID
    generated_at: datetime

    # Extracted domains
    domains: List[ExtractedDomain] = field(default_factory=list)

    # Generated backlog items
    epics: List[GeneratedEpic] = field(default_factory=list)

    # User journeys (end-user workflows)
    user_journeys: List[GeneratedUserJourney] = field(default_factory=list)

    # Statistics
    total_epics: int = 0
    total_features: int = 0
    total_stories: int = 0
    total_user_journeys: int = 0
    total_estimated_fp: float = 0.0
    total_estimated_hours: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intake_id": str(self.intake_id),
            "generated_at": self.generated_at.isoformat(),
            "domains": [d.to_dict() for d in self.domains],
            "epics": [e.to_dict() for e in self.epics],
            "user_journeys": [j.to_dict() for j in self.user_journeys],
            "statistics": {
                "total_epics": self.total_epics,
                "total_features": self.total_features,
                "total_stories": self.total_stories,
                "total_user_journeys": self.total_user_journeys,
                "total_estimated_fp": self.total_estimated_fp,
                "total_estimated_hours": self.total_estimated_hours,
            }
        }


# =============================================================================
# SERVICE
# =============================================================================

class IntakeToBacklogService:
    """
    Service to transform IntakeReport into a structured backlog.

    Process:
    1. Extract domains from architecture components and business rules
    2. Generate epics from domains (1 epic per domain + special epics)
    3. Generate features from components within each domain
    4. Generate stories from business rules and findings

    Special epics are also created for:
    - Security remediation (from security findings)
    - Infrastructure/Foundation (from detected layers)
    - Data migration (from database analysis)
    """

    # Domain detection patterns
    DOMAIN_KEYWORDS = {
        "patient": "Patient Management",
        "user": "User Management",
        "auth": "Authentication & Authorization",
        "login": "Authentication & Authorization",
        "security": "Security",
        "billing": "Billing & Payments",
        "invoice": "Billing & Payments",
        "payment": "Billing & Payments",
        "order": "Order Management",
        "product": "Product Catalog",
        "inventory": "Inventory Management",
        "report": "Reporting & Analytics",
        "dashboard": "Reporting & Analytics",
        "notification": "Notifications",
        "email": "Communications",
        "message": "Communications",
        "document": "Document Management",
        "file": "Document Management",
        "workflow": "Workflow & Process",
        "task": "Task Management",
        "schedule": "Scheduling",
        "calendar": "Scheduling",
        "config": "Configuration",
        "setting": "Configuration",
        "admin": "Administration",
        "integration": "External Integrations",
        "api": "API Layer",
        "sync": "Data Synchronization",
        "import": "Data Import/Export",
        "export": "Data Import/Export",
        "audit": "Audit & Logging",
        "log": "Audit & Logging",
    }

    # Story point mapping from complexity
    STORY_POINTS = {
        "trivial": 1,
        "low": 2,
        "medium": 5,
        "high": 8,
        "very_high": 13,
    }

    # Hours per function point (average)
    HOURS_PER_FP = 5.0

    def __init__(self):
        """Initialize the service."""
        self._domain_counter = 0
        self._epic_counter = 0
        self._feature_counter = 0
        self._story_counter = 0

    def generate_backlog(self, report: IntakeReport) -> BacklogGenerationResult:
        """
        Generate a complete backlog from an IntakeReport.

        Args:
            report: The IntakeReport from SoftwareIntakeService

        Returns:
            BacklogGenerationResult with domains, epics, features, and stories
        """
        logger.info(f"Generating backlog from intake {report.id}")

        # Reset counters
        self._domain_counter = 0
        self._epic_counter = 0
        self._feature_counter = 0
        self._story_counter = 0

        result = BacklogGenerationResult(
            intake_id=report.id,
            generated_at=datetime.now(timezone.utc),
        )

        # Step 1: Extract domains from architecture and business rules
        result.domains = self._extract_domains(report)
        logger.info(f"Extracted {len(result.domains)} domains")

        # Step 2: Generate epics from domains
        domain_epics = self._generate_domain_epics(result.domains, report)
        result.epics.extend(domain_epics)

        # Step 3: Generate special epics
        special_epics = self._generate_special_epics(report)
        result.epics.extend(special_epics)

        # Step 4: Extract and link user journeys
        result.user_journeys = self._extract_user_journeys(report, result.epics)
        logger.info(f"Extracted {len(result.user_journeys)} user journeys")

        # Step 5: Calculate statistics
        result.total_epics = len(result.epics)
        result.total_features = sum(len(e.features) for e in result.epics)
        result.total_stories = sum(
            len(f.stories) for e in result.epics for f in e.features
        )
        result.total_user_journeys = len(result.user_journeys)
        result.total_estimated_fp = sum(e.estimated_fp for e in result.epics)
        result.total_estimated_hours = sum(e.estimated_hours for e in result.epics)

        logger.info(
            f"Backlog generated: {result.total_epics} epics, "
            f"{result.total_features} features, {result.total_stories} stories, "
            f"{result.total_user_journeys} user journeys, "
            f"{result.total_estimated_fp:.0f} FP, {result.total_estimated_hours:.0f} hours"
        )

        return result

    # =========================================================================
    # DOMAIN EXTRACTION
    # =========================================================================

    def _extract_domains(self, report: IntakeReport) -> List[ExtractedDomain]:
        """Extract business domains from the intake report.

        Uses CombinedEpicSearcher when a project_path is available for
        intelligent journey-based and folder-based epic detection.
        Falls back to keyword-based detection for backwards compatibility.
        """
        # Try using CombinedEpicSearcher for intelligent domain detection
        if report.project_path:
            try:
                detected_domains = self._extract_domains_with_epic_searcher(report)
                if detected_domains:
                    logger.info(f"CombinedEpicSearcher detected {len(detected_domains)} domains")
                    return detected_domains
            except Exception as e:
                logger.warning(f"CombinedEpicSearcher failed, falling back to keyword detection: {e}")

        # Fallback: keyword-based detection
        domains: Dict[str, ExtractedDomain] = {}

        # Extract from architecture components
        if report.architecture:
            for component in report.architecture.component_mapping:
                domain_name = self._detect_domain_from_component(component)
                if domain_name not in domains:
                    domains[domain_name] = self._create_domain(domain_name)

                domains[domain_name].components.append(component.legacy_component)
                domains[domain_name].estimated_loc += component.effort_hours * 10  # Rough estimate

        # Extract from business rules
        if report.business_rules:
            all_rules = (
                report.business_rules.validation_rules +
                report.business_rules.calculations +
                report.business_rules.workflows +
                report.business_rules.constraints
            )
            for rule in all_rules:
                domain_name = self._detect_domain_from_rule(rule)
                if domain_name not in domains:
                    domains[domain_name] = self._create_domain(domain_name)

                domains[domain_name].business_rules.append(rule.id)

        # Extract from detected layers (as generic domains)
        if report.architecture and report.architecture.detected_layers:
            for layer in report.architecture.detected_layers:
                # Map layers to infrastructure domain
                if layer.name.lower() in ("data", "database", "persistence"):
                    if "Data Layer" not in domains:
                        domains["Data Layer"] = self._create_domain(
                            "Data Layer", DomainType.GENERIC
                        )
                    domains["Data Layer"].estimated_loc += layer.loc

        # Calculate domain metrics and dependencies
        domain_list = list(domains.values())
        self._calculate_domain_metrics(domain_list, report)
        self._calculate_domain_dependencies(domain_list, report)
        self._calculate_domain_priorities(domain_list, report)

        # Sort by priority
        domain_list.sort(key=lambda d: d.priority_score, reverse=True)

        return domain_list

    def _detect_domain_from_component(self, component: ComponentMapping) -> str:
        """Detect domain name from a component."""
        name_lower = component.legacy_component.lower()

        for keyword, domain in self.DOMAIN_KEYWORDS.items():
            if keyword in name_lower:
                return domain

        # Use component type as fallback
        if component.legacy_type:
            type_lower = component.legacy_type.lower()
            if "controller" in type_lower or "handler" in type_lower:
                return "API Layer"
            if "service" in type_lower:
                return "Business Logic"
            if "repository" in type_lower or "dal" in type_lower:
                return "Data Access"
            if "model" in type_lower or "entity" in type_lower:
                return "Domain Models"

        return "General"

    def _extract_domains_with_epic_searcher(
        self,
        report: IntakeReport
    ) -> List[ExtractedDomain]:
        """
        Extract domains using CombinedEpicSearcher for intelligent detection.

        This method uses journey-based and folder-based detection to find
        meaningful business domains instead of falling back to "General".

        Args:
            report: The IntakeReport with project_path

        Returns:
            List of ExtractedDomain objects, or empty list if detection fails
        """
        if not report.project_path:
            return []

        # Configure the combined searcher
        config = CombinedSearchConfig(
            project_path=report.project_path,
            max_journey_depth=6,
            min_screens_per_journey=2,
            include_infrastructure=True,
            include_uncovered_folders=True,
        )

        # Run the combined search
        searcher = CombinedEpicSearcher(config)
        detected_epics: List[DetectedEpic] = searcher.search()

        if not detected_epics:
            logger.info("CombinedEpicSearcher found no epics")
            return []

        # Convert detected epics to ExtractedDomain objects
        domains: List[ExtractedDomain] = []

        for epic in detected_epics:
            # Determine domain type based on epic category
            if epic.category == "infrastructure":
                domain_type = DomainType.GENERIC
            else:
                domain_type = DomainType.CORE

            # Create domain from epic
            domain = ExtractedDomain(
                id=f"DOM-{len(domains) + 1:03d}",
                name=epic.name,
                description=epic.description,
                domain_type=domain_type,
            )

            # Add components from source folders
            domain.components = epic.source_folders

            # Add estimated metrics
            domain.estimated_loc = epic.file_count * 50  # Rough estimate: 50 LOC per file
            domain.estimated_fp = max(1, epic.file_count // 2)  # Rough FP estimate

            # Set complexity based on file count
            if epic.file_count > 50:
                domain.complexity = "high"
            elif epic.file_count > 20:
                domain.complexity = "medium"
            else:
                domain.complexity = "low"

            # Add journey metadata if available
            if epic.metadata:
                journey_count = epic.metadata.get("journey_count", 0)
                actions = epic.metadata.get("actions", [])
                messages = epic.metadata.get("messages", [])

                # Store metadata for later use in story generation
                domain.metadata = {
                    "journey_count": journey_count,
                    "discovered_actions": actions,
                    "discovered_messages": messages,
                    "confidence": epic.confidence,
                }

            domains.append(domain)

        # Calculate metrics and dependencies
        self._calculate_domain_metrics(domains, report)
        self._calculate_domain_dependencies(domains, report)
        self._calculate_domain_priorities(domains, report)

        # Sort by priority
        domains.sort(key=lambda d: d.priority_score, reverse=True)

        logger.info(f"CombinedEpicSearcher converted {len(detected_epics)} epics to {len(domains)} domains")
        return domains

    def _detect_domain_from_rule(self, rule: ExtractedBusinessRule) -> str:
        """Detect domain name from a business rule."""
        desc_lower = rule.description.lower()

        for keyword, domain in self.DOMAIN_KEYWORDS.items():
            if keyword in desc_lower:
                return domain

        # Use rule domain or type as fallback
        if rule.domain:
            return rule.domain.title()
        return rule.rule_type.replace("_", " ").title() if rule.rule_type else "Business Rules"

    def _create_domain(
        self,
        name: str,
        domain_type: DomainType = DomainType.CORE
    ) -> ExtractedDomain:
        """Create a new domain."""
        self._domain_counter += 1
        return ExtractedDomain(
            id=f"DOM-{self._domain_counter:03d}",
            name=name,
            description=f"Business domain for {name}",
            domain_type=domain_type,
        )

    def _calculate_domain_metrics(
        self,
        domains: List[ExtractedDomain],
        report: IntakeReport
    ):
        """Calculate metrics for each domain."""
        total_loc = report.summary.total_loc or 1

        for domain in domains:
            # Estimate FP based on components and rules
            component_fp = len(domain.components) * 5  # ~5 FP per component
            rule_fp = len(domain.business_rules) * 2  # ~2 FP per rule
            domain.estimated_fp = component_fp + rule_fp

            # Estimate LOC if not set
            if domain.estimated_loc == 0:
                domain.estimated_loc = int(domain.estimated_fp * 100)  # ~100 LOC per FP

            # Determine complexity
            if domain.estimated_fp > 100:
                domain.complexity = "high"
            elif domain.estimated_fp > 50:
                domain.complexity = "medium"
            else:
                domain.complexity = "low"

    def _calculate_domain_dependencies(
        self,
        domains: List[ExtractedDomain],
        report: IntakeReport
    ):
        """Calculate dependencies between domains."""
        if not report.dependencies:
            return

        # Build component to domain mapping
        component_to_domain: Dict[str, str] = {}
        for domain in domains:
            for comp in domain.components:
                component_to_domain[comp] = domain.id

        # Analyze internal dependencies
        for dep in report.dependencies.internal_dependencies:
            source_domain = component_to_domain.get(dep.source_module)
            target_domain = component_to_domain.get(dep.target_module)

            if source_domain and target_domain and source_domain != target_domain:
                # Find domains and update
                for domain in domains:
                    if domain.id == source_domain:
                        if target_domain not in domain.depends_on:
                            domain.depends_on.append(target_domain)
                    if domain.id == target_domain:
                        if source_domain not in domain.depended_by:
                            domain.depended_by.append(source_domain)

    def _calculate_domain_priorities(
        self,
        domains: List[ExtractedDomain],
        report: IntakeReport
    ):
        """Calculate priority scores for domains."""
        for domain in domains:
            score = 0.0

            # Higher score for more business rules (core logic)
            score += len(domain.business_rules) * 10

            # Higher score for more dependents (foundational)
            score += len(domain.depended_by) * 15

            # Lower score for many dependencies (should come later)
            score -= len(domain.depends_on) * 5

            # Adjust for domain type
            if domain.domain_type == DomainType.CORE:
                score += 20
            elif domain.domain_type == DomainType.SUPPORTING:
                score += 10

            # Adjust for security-related domains
            if "security" in domain.name.lower() or "auth" in domain.name.lower():
                score += 25  # Security first

            domain.priority_score = max(0, score)

    # =========================================================================
    # EPIC GENERATION
    # =========================================================================

    def _generate_domain_epics(
        self,
        domains: List[ExtractedDomain],
        report: IntakeReport
    ) -> List[GeneratedEpic]:
        """Generate epics from domains."""
        epics = []

        for i, domain in enumerate(domains):
            self._epic_counter += 1

            epic = GeneratedEpic(
                id=f"EPIC-{self._epic_counter:03d}",
                title=f"Migrate {domain.name}",
                description=self._generate_epic_description(domain, report),
                epic_type=EpicType.DOMAIN,
                source_domain=domain.id,
                components=domain.components,
                business_rules=domain.business_rules,
                estimated_fp=domain.estimated_fp,
                estimated_hours=domain.estimated_fp * self.HOURS_PER_FP,
                complexity=domain.complexity,
                priority=i + 1,
            )

            # Generate features for this epic
            epic.features = self._generate_features_for_domain(domain, report)

            epics.append(epic)

        return epics

    def _generate_epic_description(
        self,
        domain: ExtractedDomain,
        report: IntakeReport
    ) -> str:
        """Generate a description for a domain epic."""
        lines = [
            f"Migrate the {domain.name} domain to the target architecture.",
            "",
            "**Scope:**",
            f"- {len(domain.components)} components to migrate",
            f"- {len(domain.business_rules)} business rules to preserve",
            f"- Estimated {domain.estimated_fp:.0f} function points",
            "",
        ]

        if domain.depends_on:
            lines.append(f"**Dependencies:** {', '.join(domain.depends_on)}")
        if domain.depended_by:
            lines.append(f"**Depended by:** {', '.join(domain.depended_by)}")

        return "\n".join(lines)

    def _generate_special_epics(self, report: IntakeReport) -> List[GeneratedEpic]:
        """Generate special epics for security, infrastructure, etc."""
        epics = []

        # Security Remediation Epic
        if report.security and report.security.top_findings:
            critical_high = [
                f for f in report.security.top_findings
                if f.severity in (Severity.CRITICAL, Severity.HIGH)
            ]
            if critical_high:
                self._epic_counter += 1
                security_epic = GeneratedEpic(
                    id=f"EPIC-{self._epic_counter:03d}",
                    title="Security Remediation",
                    description=self._generate_security_epic_description(report),
                    epic_type=EpicType.SECURITY,
                    security_findings=[f.id for f in critical_high],
                    estimated_hours=report.security.estimated_remediation_hours or 0,
                    complexity="high",
                    priority=0,  # Security first!
                )
                security_epic.features = self._generate_security_features(report)
                epics.append(security_epic)

        # Infrastructure Epic
        if report.architecture and report.architecture.detected_layers:
            self._epic_counter += 1
            infra_epic = GeneratedEpic(
                id=f"EPIC-{self._epic_counter:03d}",
                title="Infrastructure & Foundation",
                description="Set up the technical foundation for the migration.",
                epic_type=EpicType.INFRASTRUCTURE,
                complexity="medium",
                priority=1,  # After security
            )
            infra_epic.features = self._generate_infrastructure_features(report)
            epics.append(infra_epic)

        # Data Migration Epic
        if report.dependencies and report.summary.databases:
            self._epic_counter += 1
            data_epic = GeneratedEpic(
                id=f"EPIC-{self._epic_counter:03d}",
                title="Data Migration",
                description=f"Migrate data from {', '.join(report.summary.databases)}.",
                epic_type=EpicType.DATA,
                complexity="high",
                priority=2,
            )
            data_epic.features = self._generate_data_migration_features(report)
            epics.append(data_epic)

        return epics

    def _generate_security_epic_description(self, report: IntakeReport) -> str:
        """Generate description for security epic."""
        security = report.security
        lines = [
            "Address critical and high-severity security findings before migration.",
            "",
            "**Findings Summary:**",
            f"- Critical: {security.findings_by_severity.get('critical', 0)}",
            f"- High: {security.findings_by_severity.get('high', 0)}",
            f"- Estimated remediation: {security.estimated_remediation_hours:.0f} hours",
        ]
        return "\n".join(lines)

    # =========================================================================
    # FEATURE GENERATION
    # =========================================================================

    def _generate_features_for_domain(
        self,
        domain: ExtractedDomain,
        report: IntakeReport
    ) -> List[GeneratedFeature]:
        """Generate features for a domain."""
        features = []

        # Group components by type
        component_groups: Dict[str, List[str]] = {}
        if report.architecture:
            for mapping in report.architecture.component_mapping:
                if mapping.legacy_component in domain.components:
                    comp_type = mapping.legacy_type or "component"
                    if comp_type not in component_groups:
                        component_groups[comp_type] = []
                    component_groups[comp_type].append(mapping.legacy_component)

        # Create feature per component type
        for comp_type, components in component_groups.items():
            self._feature_counter += 1
            feature = GeneratedFeature(
                id=f"FEAT-{self._feature_counter:03d}",
                title=f"Migrate {comp_type.title()}s",
                description=f"Migrate {len(components)} {comp_type}(s) to target architecture.",
                estimated_fp=len(components) * 5,
                estimated_hours=len(components) * 5 * self.HOURS_PER_FP,
            )

            # Generate stories for this feature
            feature.stories = self._generate_stories_for_components(
                components, domain, report
            )
            features.append(feature)

        # Create feature for business rules
        if domain.business_rules:
            self._feature_counter += 1
            rules_feature = GeneratedFeature(
                id=f"FEAT-{self._feature_counter:03d}",
                title=f"Implement Business Rules",
                description=f"Implement {len(domain.business_rules)} business rules.",
                estimated_fp=len(domain.business_rules) * 2,
                estimated_hours=len(domain.business_rules) * 2 * self.HOURS_PER_FP,
            )
            rules_feature.stories = self._generate_stories_for_rules(
                domain.business_rules, report
            )
            features.append(rules_feature)

        return features

    def _generate_security_features(self, report: IntakeReport) -> List[GeneratedFeature]:
        """Generate features for security epic."""
        features = []

        if not report.security:
            return features

        # Group findings by OWASP category
        owasp_groups: Dict[str, List[Finding]] = {}
        for finding in report.security.top_findings:
            category = finding.owasp_category or "Other"
            if category not in owasp_groups:
                owasp_groups[category] = []
            owasp_groups[category].append(finding)

        for category, findings in owasp_groups.items():
            self._feature_counter += 1
            feature = GeneratedFeature(
                id=f"FEAT-{self._feature_counter:03d}",
                title=f"Fix {category}",
                description=f"Remediate {len(findings)} {category} findings.",
                estimated_hours=sum(f.effort_hours or 4 for f in findings),
            )
            feature.stories = self._generate_stories_for_findings(findings)
            features.append(feature)

        return features

    def _generate_infrastructure_features(
        self,
        report: IntakeReport
    ) -> List[GeneratedFeature]:
        """Generate features for infrastructure epic."""
        features = []

        # Project setup feature
        self._feature_counter += 1
        features.append(GeneratedFeature(
            id=f"FEAT-{self._feature_counter:03d}",
            title="Project Setup",
            description="Create target project structure and configuration.",
            estimated_hours=16,
            stories=[
                self._create_story(
                    "Set up repository and CI/CD",
                    "As a developer, I need the project repository configured with CI/CD pipelines.",
                    ["Repository created", "CI/CD pipeline configured", "Branch protection enabled"]
                ),
                self._create_story(
                    "Configure development environment",
                    "As a developer, I need local development environment documentation.",
                    ["README with setup instructions", "Docker compose for local dev", "IDE configuration"]
                ),
            ]
        ))

        # Architecture foundation feature
        self._feature_counter += 1
        features.append(GeneratedFeature(
            id=f"FEAT-{self._feature_counter:03d}",
            title="Architecture Foundation",
            description="Implement base architecture patterns and shared components.",
            estimated_hours=40,
            stories=[
                self._create_story(
                    "Implement base architecture",
                    "As a developer, I need the base architecture patterns in place.",
                    ["Domain layer structure", "Application layer structure", "Infrastructure layer"]
                ),
                self._create_story(
                    "Create shared utilities",
                    "As a developer, I need shared utilities and helpers.",
                    ["Logging configured", "Error handling", "Validation utilities"]
                ),
            ]
        ))

        return features

    def _generate_data_migration_features(
        self,
        report: IntakeReport
    ) -> List[GeneratedFeature]:
        """Generate features for data migration epic."""
        features = []

        # Schema migration feature
        self._feature_counter += 1
        features.append(GeneratedFeature(
            id=f"FEAT-{self._feature_counter:03d}",
            title="Schema Migration",
            description="Migrate database schema to target database.",
            estimated_hours=40,
            stories=[
                self._create_story(
                    "Analyze source schema",
                    "As a DBA, I need to understand the source database schema.",
                    ["Schema documentation", "Entity relationships mapped", "Data types analyzed"]
                ),
                self._create_story(
                    "Create target schema",
                    "As a DBA, I need to create the target database schema.",
                    ["Migration scripts created", "Indexes optimized", "Constraints verified"]
                ),
            ]
        ))

        # Data migration feature
        self._feature_counter += 1
        features.append(GeneratedFeature(
            id=f"FEAT-{self._feature_counter:03d}",
            title="Data Transfer",
            description="Transfer and validate data from source to target.",
            estimated_hours=60,
            stories=[
                self._create_story(
                    "Create ETL pipelines",
                    "As a developer, I need ETL pipelines for data migration.",
                    ["Extract scripts", "Transform logic", "Load procedures"]
                ),
                self._create_story(
                    "Validate migrated data",
                    "As a QA, I need to verify data integrity after migration.",
                    ["Row counts match", "Data checksums verified", "Sample records validated"]
                ),
            ]
        ))

        return features

    # =========================================================================
    # STORY GENERATION
    # =========================================================================

    def _generate_stories_for_components(
        self,
        components: List[str],
        domain: ExtractedDomain,
        report: IntakeReport
    ) -> List[GeneratedStory]:
        """Generate stories for components."""
        stories = []

        for component in components[:10]:  # Limit to avoid explosion
            stories.append(self._create_story(
                f"Migrate {component}",
                f"As a developer, I need to migrate {component} to the target architecture.",
                [
                    "Component migrated",
                    "Unit tests passing",
                    "Integration tests passing",
                    "Code review completed"
                ]
            ))

        if len(components) > 10:
            # Create a summary story for remaining
            stories.append(self._create_story(
                f"Migrate remaining {len(components) - 10} components",
                f"As a developer, I need to migrate the remaining components.",
                ["All components migrated", "Full test coverage"]
            ))

        return stories

    def _generate_stories_for_rules(
        self,
        rule_ids: List[str],
        report: IntakeReport
    ) -> List[GeneratedStory]:
        """Generate stories for business rules."""
        stories = []

        if not report.business_rules:
            return stories

        # Find actual rules (combined from all rule types)
        all_rules = (
            report.business_rules.validation_rules +
            report.business_rules.calculations +
            report.business_rules.workflows +
            report.business_rules.constraints
        )
        rules_by_id = {r.id: r for r in all_rules}

        for rule_id in rule_ids[:10]:
            rule = rules_by_id.get(rule_id)
            if rule:
                stories.append(self._create_story(
                    f"Implement {rule_id}",
                    rule.description,
                    [
                        "Business rule implemented",
                        "Unit tests for rule",
                        "Edge cases covered"
                    ],
                    source_business_rule=rule_id
                ))

        return stories

    def _generate_stories_for_findings(
        self,
        findings: List[Finding]
    ) -> List[GeneratedStory]:
        """Generate stories for security findings."""
        stories = []

        for finding in findings[:10]:
            stories.append(self._create_story(
                f"Fix {finding.id}: {finding.title}",
                finding.description,
                [
                    "Vulnerability fixed",
                    "Security test passing",
                    "No regression introduced"
                ],
                source_finding=finding.id,
                story_points=self.STORY_POINTS.get(
                    "high" if finding.severity in (Severity.CRITICAL, Severity.HIGH) else "medium",
                    5
                )
            ))

        return stories

    def _create_story(
        self,
        title: str,
        description: str,
        acceptance_criteria: List[str],
        source_business_rule: Optional[str] = None,
        source_finding: Optional[str] = None,
        story_points: int = 5
    ) -> GeneratedStory:
        """Create a story."""
        self._story_counter += 1
        return GeneratedStory(
            id=f"US-{self._story_counter:04d}",
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            source_business_rule=source_business_rule,
            source_finding=source_finding,
            story_points=story_points,
            estimated_hours=story_points * 2,  # ~2 hours per story point
        )

    # =========================================================================
    # USER JOURNEY EXTRACTION
    # =========================================================================

    def _extract_user_journeys(
        self,
        report: IntakeReport,
        epics: List[GeneratedEpic]
    ) -> List[GeneratedUserJourney]:
        """
        Extract user journeys from the intake report and link to epics/features.

        User journeys are inferred from:
        1. Detected UI screens (architecture layers)
        2. Business rules (workflow rules)
        3. API endpoints (user-facing operations)
        4. Authorization roles (personas)

        Args:
            report: The IntakeReport
            epics: Generated epics to link journeys to

        Returns:
            List of GeneratedUserJourney
        """
        journeys: List[GeneratedUserJourney] = []
        self._journey_counter = 0

        # Step 1: Extract personas from roles/authorization
        personas = self._extract_personas(report)

        # Step 2: Extract screen flows
        screens = self._extract_screens(report)

        # Step 3: Generate journeys from workflows and screen flows
        if report.business_rules:
            workflow_rules = report.business_rules.workflows
            for workflow in workflow_rules[:10]:  # Limit to top 10
                journey = self._create_journey_from_workflow(
                    workflow, personas, screens, epics
                )
                if journey:
                    journeys.append(journey)

        # Step 4: Generate journeys from UI layers
        if report.architecture and report.architecture.detected_layers:
            for layer in report.architecture.detected_layers:
                # DetectedLayer has name, not layer_type
                layer_name = layer.name.lower()
                if any(kw in layer_name for kw in ["ui", "presentation", "web", "view", "frontend"]):
                    layer_journeys = self._create_journeys_from_layer(
                        layer, personas, screens, epics
                    )
                    journeys.extend(layer_journeys[:5])  # Limit per layer

        # Step 5: If no journeys found, create generic journeys from domains
        if not journeys:
            for epic in epics[:3]:  # Top 3 epics
                if epic.epic_type == EpicType.DOMAIN:
                    journey = self._create_generic_journey(epic, personas)
                    if journey:
                        journeys.append(journey)

        return journeys

    def _extract_personas(self, report: IntakeReport) -> List[Dict[str, Any]]:
        """Extract personas from authorization and roles."""
        personas = []

        # Default personas based on common patterns
        default_personas = [
            {
                "id": "PERSONA-001",
                "name": "End User",
                "type": PersonaType.CUSTOMER.value,
                "role_code": "USER",
            },
            {
                "id": "PERSONA-002",
                "name": "Administrator",
                "type": PersonaType.ADMINISTRATOR.value,
                "role_code": "ADMIN",
            },
        ]

        # Try to extract from business rules
        if report.business_rules:
            for rule in report.business_rules.validation_rules[:5]:
                if any(kw in rule.description.lower() for kw in ["role", "permission", "auth", "user"]):
                    # Extract role from description
                    role_name = self._extract_role_from_description(rule.description)
                    if role_name and not any(p["name"] == role_name for p in personas):
                        personas.append({
                            "id": f"PERSONA-{len(personas) + 1:03d}",
                            "name": role_name,
                            "type": PersonaType.EMPLOYEE.value,
                            "role_code": role_name.upper().replace(" ", "_"),
                        })

        # Add default personas if none found
        if not personas:
            personas = default_personas

        return personas

    def _extract_role_from_description(self, description: str) -> Optional[str]:
        """Extract role name from a rule description."""
        role_keywords = [
            "admin", "administrator", "beheerder",
            "user", "gebruiker", "medewerker",
            "manager", "supervisor",
            "operator", "agent",
            "customer", "klant", "client",
        ]

        desc_lower = description.lower()
        for keyword in role_keywords:
            if keyword in desc_lower:
                return keyword.title()
        return None

    def _extract_screens(self, report: IntakeReport) -> List[Dict[str, Any]]:
        """Extract screen information from architecture."""
        screens = []

        if report.architecture and report.architecture.component_mapping:
            for component in report.architecture.component_mapping:
                # ComponentMapping has legacy_type and target_type
                component_type = component.legacy_type.lower()
                if any(kw in component_type for kw in ["ui", "view", "page", "form", "screen", "presentation", "web"]):
                    screens.append({
                        "id": f"SCREEN-{len(screens) + 1:03d}",
                        "name": component.legacy_component,
                        "type": component_type,
                        "path": component.legacy_location,
                    })

        return screens

    def _create_journey_from_workflow(
        self,
        workflow: ExtractedBusinessRule,
        personas: List[Dict[str, Any]],
        screens: List[Dict[str, Any]],
        epics: List[GeneratedEpic]
    ) -> Optional[GeneratedUserJourney]:
        """Create a user journey from a workflow business rule."""
        self._journey_counter += 1

        # Pick a persona based on workflow description
        persona = personas[0] if personas else {
            "id": "PERSONA-001", "name": "User", "type": "customer"
        }

        # Find related epics
        related_epic_ids = []
        related_feature_ids = []
        related_story_ids = []

        for epic in epics:
            if any(kw in epic.title.lower() for kw in workflow.name.lower().split()):
                related_epic_ids.append(epic.id)
                for feature in epic.features[:2]:
                    related_feature_ids.append(feature.id)
                    for story in feature.stories[:2]:
                        related_story_ids.append(story.id)

        return GeneratedUserJourney(
            id=f"UJ-{self._journey_counter:03d}",
            name=workflow.name,
            description=workflow.description,
            persona_id=persona["id"],
            persona_name=persona["name"],
            persona_type=persona.get("type", "customer"),
            complexity=workflow.complexity.value if hasattr(workflow, 'complexity') else "moderate",
            business_value="high" if workflow.complexity == "high" else "medium",
            frequency="daily",
            trigger=f"User initiates {workflow.name}",
            steps=self._generate_journey_steps(workflow),
            success_criteria=[f"{workflow.name} completed successfully"],
            outcome=f"User has completed {workflow.name}",
            related_epics=related_epic_ids,
            related_features=related_feature_ids,
            related_stories=related_story_ids,
            screens_involved=[s["name"] for s in screens[:3]],
            estimated_duration_minutes=5,
            source_evidence=[{"rule_id": workflow.id, "type": "workflow"}],
            confidence=workflow.confidence if hasattr(workflow, 'confidence') else 0.7,
        )

    def _generate_journey_steps(
        self,
        workflow: ExtractedBusinessRule
    ) -> List[Dict[str, Any]]:
        """Generate journey steps from a workflow rule."""
        steps = []

        # Parse description for steps
        desc = workflow.description
        if ";" in desc:
            parts = desc.split(";")
        elif "," in desc:
            parts = desc.split(",")
        else:
            parts = [desc]

        for i, part in enumerate(parts[:5], 1):
            steps.append({
                "sequence": i,
                "action": part.strip()[:100],
                "interaction_type": "input" if i < len(parts) else "confirm",
            })

        return steps

    def _create_journeys_from_layer(
        self,
        layer: DetectedLayer,
        personas: List[Dict[str, Any]],
        screens: List[Dict[str, Any]],
        epics: List[GeneratedEpic]
    ) -> List[GeneratedUserJourney]:
        """Create user journeys from a UI layer."""
        journeys = []

        # DetectedLayer has directories, not components
        # Extract component names from directories
        components = []
        for directory in layer.directories[:5]:
            # Extract meaningful name from directory path
            parts = directory.strip("/").split("/")
            if parts:
                component_name = parts[-1].replace("_", " ").title()
                if component_name:
                    components.append(component_name)

        for component in components[:5]:
            self._journey_counter += 1
            persona = personas[0] if personas else {"id": "PERSONA-001", "name": "User", "type": "customer"}

            # Find related epic
            related_epic_ids = []
            for epic in epics:
                if epic.epic_type == EpicType.DOMAIN:
                    related_epic_ids.append(epic.id)
                    break

            journeys.append(GeneratedUserJourney(
                id=f"UJ-{self._journey_counter:03d}",
                name=f"Use {component}",
                description=f"User journey through {component}",
                persona_id=persona["id"],
                persona_name=persona["name"],
                persona_type=persona.get("type", "customer"),
                complexity="moderate",
                business_value="medium",
                frequency="daily",
                trigger=f"User accesses {component}",
                steps=[
                    {"sequence": 1, "action": f"Navigate to {component}", "interaction_type": "navigate"},
                    {"sequence": 2, "action": "View information", "interaction_type": "view"},
                    {"sequence": 3, "action": "Perform action", "interaction_type": "input"},
                ],
                success_criteria=[f"{component} workflow completed"],
                outcome=f"User interaction with {component} completed",
                related_epics=related_epic_ids,
                related_features=[],
                related_stories=[],
                screens_involved=[component],
                estimated_duration_minutes=3,
                source_evidence=[{"layer": layer.name, "directory": component}],
                confidence=0.6,
            ))

        return journeys

    def _create_generic_journey(
        self,
        epic: GeneratedEpic,
        personas: List[Dict[str, Any]]
    ) -> Optional[GeneratedUserJourney]:
        """Create a generic user journey from an epic."""
        self._journey_counter += 1
        persona = personas[0] if personas else {"id": "PERSONA-001", "name": "User", "type": "customer"}

        # Get feature and story IDs
        feature_ids = [f.id for f in epic.features[:3]]
        story_ids = [s.id for f in epic.features[:2] for s in f.stories[:2]]

        return GeneratedUserJourney(
            id=f"UJ-{self._journey_counter:03d}",
            name=f"{epic.title.replace('Migrate ', '')} Workflow",
            description=f"User journey for {epic.title}",
            persona_id=persona["id"],
            persona_name=persona["name"],
            persona_type=persona.get("type", "customer"),
            complexity="moderate",
            business_value="medium",
            frequency="weekly",
            trigger=f"User needs to work with {epic.title.replace('Migrate ', '')}",
            steps=[
                {"sequence": 1, "action": "Access system", "interaction_type": "navigate"},
                {"sequence": 2, "action": "Select operation", "interaction_type": "select"},
                {"sequence": 3, "action": "Enter data", "interaction_type": "input"},
                {"sequence": 4, "action": "Confirm and save", "interaction_type": "confirm"},
            ],
            success_criteria=["Operation completed successfully", "Data saved correctly"],
            outcome="User has completed the workflow",
            related_epics=[epic.id],
            related_features=feature_ids,
            related_stories=story_ids,
            screens_involved=[],
            estimated_duration_minutes=5,
            source_evidence=[{"epic_id": epic.id, "type": "generic"}],
            confidence=0.5,
        )
