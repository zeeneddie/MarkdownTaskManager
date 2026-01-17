"""
NFR Architecture Mapper - Week 106
NFR-M-1: Cross-Reference NFR with Architecture

Maps Non-Functional Requirements to architectural components:
- Performance → Caching, load balancers, async processing
- Security → Auth, encryption, audit logging
- Scalability → Microservices, horizontal scaling
- Reliability → Redundancy, circuit breakers, retry logic
- Maintainability → Clean code, DI, modular design
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
from enum import Enum
from datetime import datetime, timezone
import re
import json


class NFRCategory(Enum):
    """Categories of Non-Functional Requirements."""
    PERFORMANCE = "performance"
    SECURITY = "security"
    SCALABILITY = "scalability"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    USABILITY = "usability"
    AVAILABILITY = "availability"
    COMPLIANCE = "compliance"
    PORTABILITY = "portability"
    INTEROPERABILITY = "interoperability"


class ArchitecturalPattern(Enum):
    """Common architectural patterns addressing NFRs."""
    # Performance patterns
    CACHING = "caching"
    LOAD_BALANCING = "load_balancing"
    ASYNC_PROCESSING = "async_processing"
    CDN = "cdn"
    DATABASE_INDEXING = "database_indexing"
    CONNECTION_POOLING = "connection_pooling"

    # Security patterns
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ENCRYPTION = "encryption"
    AUDIT_LOGGING = "audit_logging"
    INPUT_VALIDATION = "input_validation"
    RATE_LIMITING = "rate_limiting"

    # Scalability patterns
    MICROSERVICES = "microservices"
    HORIZONTAL_SCALING = "horizontal_scaling"
    SHARDING = "sharding"
    CQRS = "cqrs"
    EVENT_SOURCING = "event_sourcing"

    # Reliability patterns
    CIRCUIT_BREAKER = "circuit_breaker"
    RETRY_LOGIC = "retry_logic"
    REDUNDANCY = "redundancy"
    HEALTH_CHECKS = "health_checks"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    SAGA_PATTERN = "saga_pattern"

    # Maintainability patterns
    DEPENDENCY_INJECTION = "dependency_injection"
    LAYERED_ARCHITECTURE = "layered_architecture"
    REPOSITORY_PATTERN = "repository_pattern"
    FACTORY_PATTERN = "factory_pattern"
    OBSERVER_PATTERN = "observer_pattern"

    # Monitoring patterns
    LOGGING = "logging"
    METRICS = "metrics"
    TRACING = "tracing"
    ALERTING = "alerting"


class ImplementationStatus(Enum):
    """Status of NFR implementation."""
    NOT_IMPLEMENTED = "not_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    FULLY_IMPLEMENTED = "fully_implemented"
    NEEDS_REVIEW = "needs_review"


@dataclass
class NFRequirement:
    """A Non-Functional Requirement."""
    id: str
    category: NFRCategory
    name: str
    description: str
    priority: str  # P0, P1, P2, P3
    acceptance_criteria: List[str] = field(default_factory=list)
    metrics: Dict[str, str] = field(default_factory=dict)
    compliance_standards: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "acceptance_criteria": self.acceptance_criteria,
            "metrics": self.metrics,
            "compliance_standards": self.compliance_standards
        }


@dataclass
class ArchitecturalComponent:
    """An architectural component that addresses NFRs."""
    id: str
    name: str
    pattern: ArchitecturalPattern
    description: str
    file_paths: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "pattern": self.pattern.value,
            "description": self.description,
            "file_paths": self.file_paths,
            "technologies": self.technologies,
            "configuration": self.configuration
        }


@dataclass
class NFRMapping:
    """Mapping between NFR and architectural component."""
    nfr_id: str
    component_id: str
    coverage_percentage: float  # 0-100
    status: ImplementationStatus
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nfr_id": self.nfr_id,
            "component_id": self.component_id,
            "coverage_percentage": self.coverage_percentage,
            "status": self.status.value,
            "gaps": self.gaps,
            "recommendations": self.recommendations,
            "evidence": self.evidence
        }


# NFR to Pattern mapping knowledge base
NFR_PATTERN_MAPPING: Dict[NFRCategory, List[ArchitecturalPattern]] = {
    NFRCategory.PERFORMANCE: [
        ArchitecturalPattern.CACHING,
        ArchitecturalPattern.LOAD_BALANCING,
        ArchitecturalPattern.ASYNC_PROCESSING,
        ArchitecturalPattern.CDN,
        ArchitecturalPattern.DATABASE_INDEXING,
        ArchitecturalPattern.CONNECTION_POOLING,
    ],
    NFRCategory.SECURITY: [
        ArchitecturalPattern.AUTHENTICATION,
        ArchitecturalPattern.AUTHORIZATION,
        ArchitecturalPattern.ENCRYPTION,
        ArchitecturalPattern.AUDIT_LOGGING,
        ArchitecturalPattern.INPUT_VALIDATION,
        ArchitecturalPattern.RATE_LIMITING,
    ],
    NFRCategory.SCALABILITY: [
        ArchitecturalPattern.MICROSERVICES,
        ArchitecturalPattern.HORIZONTAL_SCALING,
        ArchitecturalPattern.SHARDING,
        ArchitecturalPattern.CQRS,
        ArchitecturalPattern.EVENT_SOURCING,
        ArchitecturalPattern.ASYNC_PROCESSING,
    ],
    NFRCategory.RELIABILITY: [
        ArchitecturalPattern.CIRCUIT_BREAKER,
        ArchitecturalPattern.RETRY_LOGIC,
        ArchitecturalPattern.REDUNDANCY,
        ArchitecturalPattern.HEALTH_CHECKS,
        ArchitecturalPattern.GRACEFUL_DEGRADATION,
        ArchitecturalPattern.SAGA_PATTERN,
    ],
    NFRCategory.MAINTAINABILITY: [
        ArchitecturalPattern.DEPENDENCY_INJECTION,
        ArchitecturalPattern.LAYERED_ARCHITECTURE,
        ArchitecturalPattern.REPOSITORY_PATTERN,
        ArchitecturalPattern.FACTORY_PATTERN,
        ArchitecturalPattern.LOGGING,
    ],
    NFRCategory.AVAILABILITY: [
        ArchitecturalPattern.REDUNDANCY,
        ArchitecturalPattern.LOAD_BALANCING,
        ArchitecturalPattern.HEALTH_CHECKS,
        ArchitecturalPattern.CIRCUIT_BREAKER,
    ],
}

# Code patterns that indicate architectural patterns
PATTERN_CODE_INDICATORS: Dict[ArchitecturalPattern, List[str]] = {
    ArchitecturalPattern.CACHING: [
        r"@cache", r"@cached", r"cache\.get", r"cache\.set",
        r"redis", r"memcache", r"lru_cache"
    ],
    ArchitecturalPattern.AUTHENTICATION: [
        r"@authenticate", r"jwt", r"oauth", r"login", r"session",
        r"bearer", r"token_required", r"current_user"
    ],
    ArchitecturalPattern.AUTHORIZATION: [
        r"@requires?_role", r"@permission", r"has_permission",
        r"rbac", r"acl", r"can_access", r"is_authorized"
    ],
    ArchitecturalPattern.ENCRYPTION: [
        r"encrypt", r"decrypt", r"aes", r"rsa", r"fernet",
        r"bcrypt", r"hashlib", r"pbkdf2"
    ],
    ArchitecturalPattern.AUDIT_LOGGING: [
        r"audit_log", r"log_action", r"track_change",
        r"activity_log", r"event_log"
    ],
    ArchitecturalPattern.CIRCUIT_BREAKER: [
        r"circuit_breaker", r"CircuitBreaker", r"@circuit",
        r"circuitbreaker", r"pybreaker"
    ],
    ArchitecturalPattern.RETRY_LOGIC: [
        r"@retry", r"Retry", r"backoff", r"max_retries",
        r"retry_on", r"tenacity"
    ],
    ArchitecturalPattern.HEALTH_CHECKS: [
        r"/health", r"/healthz", r"/ready", r"health_check",
        r"liveness", r"readiness"
    ],
    ArchitecturalPattern.RATE_LIMITING: [
        r"rate_limit", r"throttle", r"RateLimiter",
        r"requests_per", r"@ratelimit"
    ],
    ArchitecturalPattern.DEPENDENCY_INJECTION: [
        r"@inject", r"Depends", r"Container", r"Provider",
        r"injector", r"dependency_overrides"
    ],
    ArchitecturalPattern.ASYNC_PROCESSING: [
        r"async def", r"await", r"asyncio", r"celery",
        r"BackgroundTasks", r"@task"
    ],
    ArchitecturalPattern.LOGGING: [
        r"logging\.getLogger", r"logger\.", r"structlog",
        r"loguru", r"@log"
    ],
    ArchitecturalPattern.METRICS: [
        r"prometheus", r"metrics\.", r"Counter\(",
        r"Histogram\(", r"statsd", r"@metric"
    ],
    ArchitecturalPattern.TRACING: [
        r"opentelemetry", r"jaeger", r"zipkin",
        r"trace_id", r"span_id", r"@trace"
    ],
}


class NFRArchitectureMapper:
    """
    Maps Non-Functional Requirements to architectural components.

    Analyzes codebase to identify:
    - Which architectural patterns are implemented
    - How well they address each NFR
    - Gaps and recommendations
    """

    def __init__(self):
        self.nfrs: Dict[str, NFRequirement] = {}
        self.components: Dict[str, ArchitecturalComponent] = {}
        self.mappings: List[NFRMapping] = []
        self._nfr_counter = 0
        self._component_counter = 0

    def add_nfr(
        self,
        category: NFRCategory,
        name: str,
        description: str,
        priority: str = "P1",
        acceptance_criteria: Optional[List[str]] = None,
        metrics: Optional[Dict[str, str]] = None,
        compliance: Optional[List[str]] = None
    ) -> str:
        """Add a Non-Functional Requirement."""
        self._nfr_counter += 1
        nfr_id = f"NFR-{self._nfr_counter:03d}"

        nfr = NFRequirement(
            id=nfr_id,
            category=category,
            name=name,
            description=description,
            priority=priority,
            acceptance_criteria=acceptance_criteria or [],
            metrics=metrics or {},
            compliance_standards=compliance or []
        )

        self.nfrs[nfr_id] = nfr
        return nfr_id

    def add_component(
        self,
        name: str,
        pattern: ArchitecturalPattern,
        description: str,
        file_paths: Optional[List[str]] = None,
        technologies: Optional[List[str]] = None
    ) -> str:
        """Add an architectural component."""
        self._component_counter += 1
        comp_id = f"COMP-{self._component_counter:03d}"

        component = ArchitecturalComponent(
            id=comp_id,
            name=name,
            pattern=pattern,
            description=description,
            file_paths=file_paths or [],
            technologies=technologies or []
        )

        self.components[comp_id] = component
        return comp_id

    def analyze_codebase(
        self,
        code_files: Dict[str, str]  # path -> content
    ) -> List[ArchitecturalComponent]:
        """
        Analyze codebase to detect architectural patterns.

        Args:
            code_files: Dictionary mapping file paths to content

        Returns:
            List of detected architectural components
        """
        detected = []

        for file_path, content in code_files.items():
            for pattern, indicators in PATTERN_CODE_INDICATORS.items():
                for indicator in indicators:
                    if re.search(indicator, content, re.IGNORECASE):
                        # Found a pattern implementation
                        comp_id = self.add_component(
                            name=f"{pattern.value} in {file_path}",
                            pattern=pattern,
                            description=f"Implementation of {pattern.value} pattern",
                            file_paths=[file_path]
                        )
                        detected.append(self.components[comp_id])
                        break  # Only add once per pattern per file

        return detected

    def generate_mappings(self) -> List[NFRMapping]:
        """
        Generate mappings between NFRs and components.

        Creates mappings based on:
        1. NFR category to pattern mapping
        2. Component patterns
        3. Coverage analysis
        """
        self.mappings = []

        for nfr_id, nfr in self.nfrs.items():
            # Get relevant patterns for this NFR category
            relevant_patterns = NFR_PATTERN_MAPPING.get(nfr.category, [])

            # Find components implementing these patterns
            matching_components = [
                comp for comp in self.components.values()
                if comp.pattern in relevant_patterns
            ]

            if matching_components:
                # Calculate coverage based on how many patterns are implemented
                implemented_patterns = set(c.pattern for c in matching_components)
                coverage = len(implemented_patterns) / len(relevant_patterns) * 100

                # Determine status
                if coverage >= 80:
                    status = ImplementationStatus.FULLY_IMPLEMENTED
                elif coverage >= 40:
                    status = ImplementationStatus.PARTIALLY_IMPLEMENTED
                else:
                    status = ImplementationStatus.NEEDS_REVIEW

                # Identify gaps
                missing_patterns = set(relevant_patterns) - implemented_patterns
                gaps = [f"Missing {p.value} pattern" for p in missing_patterns]

                # Generate recommendations
                recommendations = self._generate_recommendations(
                    nfr, missing_patterns
                )

                for comp in matching_components:
                    mapping = NFRMapping(
                        nfr_id=nfr_id,
                        component_id=comp.id,
                        coverage_percentage=coverage,
                        status=status,
                        gaps=gaps,
                        recommendations=recommendations,
                        evidence=comp.file_paths
                    )
                    self.mappings.append(mapping)

            else:
                # No components found for this NFR
                mapping = NFRMapping(
                    nfr_id=nfr_id,
                    component_id="",
                    coverage_percentage=0,
                    status=ImplementationStatus.NOT_IMPLEMENTED,
                    gaps=[f"No implementation found for {nfr.category.value}"],
                    recommendations=self._generate_recommendations(
                        nfr, set(relevant_patterns)
                    )
                )
                self.mappings.append(mapping)

        return self.mappings

    def _generate_recommendations(
        self,
        nfr: NFRequirement,
        missing_patterns: Set[ArchitecturalPattern]
    ) -> List[str]:
        """Generate recommendations for missing patterns."""
        recommendations = []

        for pattern in missing_patterns:
            if pattern == ArchitecturalPattern.CACHING:
                recommendations.append(
                    "Implement caching with Redis or in-memory cache for frequent data access"
                )
            elif pattern == ArchitecturalPattern.CIRCUIT_BREAKER:
                recommendations.append(
                    "Add circuit breaker (pybreaker) for external service calls"
                )
            elif pattern == ArchitecturalPattern.RETRY_LOGIC:
                recommendations.append(
                    "Implement retry with exponential backoff (tenacity) for transient failures"
                )
            elif pattern == ArchitecturalPattern.RATE_LIMITING:
                recommendations.append(
                    "Add rate limiting middleware to prevent API abuse"
                )
            elif pattern == ArchitecturalPattern.AUDIT_LOGGING:
                recommendations.append(
                    "Implement audit logging for security-sensitive operations"
                )
            elif pattern == ArchitecturalPattern.HEALTH_CHECKS:
                recommendations.append(
                    "Add /health and /ready endpoints for container orchestration"
                )

        # Add compliance-specific recommendations
        if "GDPR" in nfr.compliance_standards:
            recommendations.append(
                "Ensure data anonymization and consent management for GDPR compliance"
            )
        if "PCI-DSS" in nfr.compliance_standards:
            recommendations.append(
                "Implement PCI-DSS controls: encryption, access logging, data masking"
            )
        if "NEN7510" in nfr.compliance_standards:
            recommendations.append(
                "Add healthcare-specific security: 2FA, PHI access logging, session timeout"
            )

        return recommendations

    def get_coverage_summary(self) -> Dict[str, Any]:
        """Get summary of NFR coverage."""
        summary = {
            "total_nfrs": len(self.nfrs),
            "by_status": {},
            "by_category": {},
            "overall_coverage": 0.0
        }

        status_counts = {}
        category_coverage = {}

        for mapping in self.mappings:
            # Count by status
            status = mapping.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # Track coverage by category
            nfr = self.nfrs.get(mapping.nfr_id)
            if nfr:
                cat = nfr.category.value
                if cat not in category_coverage:
                    category_coverage[cat] = []
                category_coverage[cat].append(mapping.coverage_percentage)

        summary["by_status"] = status_counts

        # Calculate average coverage per category
        for cat, coverages in category_coverage.items():
            summary["by_category"][cat] = {
                "count": len(coverages),
                "avg_coverage": sum(coverages) / len(coverages) if coverages else 0
            }

        # Overall coverage
        all_coverages = [m.coverage_percentage for m in self.mappings]
        summary["overall_coverage"] = sum(all_coverages) / len(all_coverages) if all_coverages else 0

        return summary

    def get_gap_analysis(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get detailed gap analysis."""
        gaps_by_priority = {"P0": [], "P1": [], "P2": [], "P3": []}

        for mapping in self.mappings:
            if mapping.status != ImplementationStatus.FULLY_IMPLEMENTED:
                nfr = self.nfrs.get(mapping.nfr_id)
                if nfr:
                    gap_info = {
                        "nfr_id": nfr.id,
                        "nfr_name": nfr.name,
                        "category": nfr.category.value,
                        "current_coverage": mapping.coverage_percentage,
                        "gaps": mapping.gaps,
                        "recommendations": mapping.recommendations
                    }
                    priority = nfr.priority if nfr.priority in gaps_by_priority else "P3"
                    gaps_by_priority[priority].append(gap_info)

        return gaps_by_priority

    def export(self, format: str = "json") -> str:
        """Export the NFR-Architecture mapping."""
        if format == "json":
            return self._to_json()
        elif format == "markdown":
            return self._to_markdown()
        elif format == "cafcr":
            return self._to_cafcr()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _to_json(self) -> str:
        """Export as JSON."""
        return json.dumps({
            "nfrs": {nid: n.to_dict() for nid, n in self.nfrs.items()},
            "components": {cid: c.to_dict() for cid, c in self.components.items()},
            "mappings": [m.to_dict() for m in self.mappings],
            "coverage_summary": self.get_coverage_summary(),
            "gap_analysis": self.get_gap_analysis(),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }, indent=2, default=str)

    def _to_markdown(self) -> str:
        """Export as Markdown report."""
        lines = ["# NFR Architecture Analysis Report\n"]

        # Summary section
        summary = self.get_coverage_summary()
        lines.append("## Coverage Summary\n")
        lines.append(f"- **Total NFRs**: {summary['total_nfrs']}")
        lines.append(f"- **Overall Coverage**: {summary['overall_coverage']:.1f}%\n")

        # Status breakdown
        lines.append("### By Status\n")
        for status, count in summary['by_status'].items():
            lines.append(f"- {status}: {count}")

        # Category breakdown
        lines.append("\n### By Category\n")
        lines.append("| Category | Count | Avg Coverage |")
        lines.append("|----------|-------|--------------|")
        for cat, info in summary['by_category'].items():
            lines.append(f"| {cat} | {info['count']} | {info['avg_coverage']:.1f}% |")

        # Gap Analysis
        lines.append("\n## Gap Analysis\n")
        gaps = self.get_gap_analysis()

        for priority in ["P0", "P1", "P2", "P3"]:
            if gaps[priority]:
                lines.append(f"\n### {priority} Priority Gaps\n")
                for gap in gaps[priority]:
                    lines.append(f"#### {gap['nfr_name']} ({gap['nfr_id']})")
                    lines.append(f"- Category: {gap['category']}")
                    lines.append(f"- Coverage: {gap['current_coverage']:.1f}%")
                    lines.append("- Gaps:")
                    for g in gap['gaps']:
                        lines.append(f"  - {g}")
                    lines.append("- Recommendations:")
                    for r in gap['recommendations']:
                        lines.append(f"  - {r}")
                    lines.append("")

        # Architectural Components
        lines.append("\n## Detected Components\n")
        lines.append("| Component | Pattern | Files |")
        lines.append("|-----------|---------|-------|")
        for comp in self.components.values():
            files = ", ".join(comp.file_paths[:2])
            if len(comp.file_paths) > 2:
                files += f" (+{len(comp.file_paths) - 2} more)"
            lines.append(f"| {comp.name} | {comp.pattern.value} | {files} |")

        return '\n'.join(lines)

    def _to_cafcr(self) -> str:
        """Export in CAFCR format (Customer-Application-Functional-Conceptual-Realization)."""
        cafcr = {
            "customer": {
                "stakeholders": list(set(
                    n.compliance_standards for n in self.nfrs.values()
                    if n.compliance_standards
                )),
                "concerns": [n.name for n in self.nfrs.values()]
            },
            "functional": {
                "requirements": [n.to_dict() for n in self.nfrs.values()]
            },
            "conceptual": {
                "patterns": list(set(c.pattern.value for c in self.components.values()))
            },
            "realization": {
                "components": [c.to_dict() for c in self.components.values()],
                "mappings": [m.to_dict() for m in self.mappings]
            }
        }

        return json.dumps(cafcr, indent=2, default=str)
