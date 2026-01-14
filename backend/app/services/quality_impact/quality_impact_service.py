"""
Quality Impact Mapping Service.

Main orchestrator that combines all mappers to provide comprehensive
quality-to-functionality impact analysis.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from collections import defaultdict
import logging

from .types import (
    QualityIssue,
    FunctionalityImpact,
    QualityImpactMapping,
    ImpactSummary,
    ProjectImpactReport,
    IssueType,
    ImpactSeverity,
)
from .code_to_functionality_mapper import CodeToFunctionalityMapper
from .security_impact_mapper import SecurityImpactMapper
from .performance_impact_mapper import PerformanceImpactMapper
from .memory_leak_impact_mapper import MemoryLeakImpactMapper
from .impact_score_calculator import ImpactScoreCalculator, ImpactWeights

logger = logging.getLogger(__name__)


class QualityImpactMappingService:
    """
    Orchestrates quality-to-functionality impact mapping.

    Integrates:
    - Code to functionality mapper (Brown Paper / Traceability)
    - Security impact mapper (GhostCrew / Static Analysis)
    - Performance impact mapper (SQL Analyzer)
    - Memory leak impact mapper (Stability Analyzer)
    - Impact score calculator (prioritization)
    """

    def __init__(
        self,
        code_mapper: CodeToFunctionalityMapper,
        security_mapper: SecurityImpactMapper,
        performance_mapper: PerformanceImpactMapper,
        memory_leak_mapper: MemoryLeakImpactMapper,
        score_calculator: ImpactScoreCalculator,
        base_user_count: int = 1000,
    ):
        """
        Initialize the quality impact mapping service.

        Args:
            code_mapper: Code to functionality mapper
            security_mapper: Security impact mapper
            performance_mapper: Performance impact mapper
            memory_leak_mapper: Memory leak impact mapper
            score_calculator: Impact score calculator
            base_user_count: Default daily user count for impact estimation
        """
        self.code_mapper = code_mapper
        self.security_mapper = security_mapper
        self.performance_mapper = performance_mapper
        self.memory_leak_mapper = memory_leak_mapper
        self.score_calculator = score_calculator
        self.base_user_count = base_user_count

    def analyze_project(
        self,
        project_id: str,
        project_name: str,
        issues: List[QualityIssue],
        domain_mappings: Optional[Dict[str, Any]] = None,
        traceability: Optional[Dict[str, Any]] = None,
    ) -> ProjectImpactReport:
        """
        Run complete quality impact analysis for a project.

        Args:
            project_id: Project identifier
            project_name: Project name
            issues: List of quality issues from various scanners
            domain_mappings: Optional Brown Paper domain data
            traceability: Optional story-to-code traceability

        Returns:
            ProjectImpactReport with full analysis
        """
        logger.info(f"Starting quality impact analysis for project {project_id}")

        # Load domain data if provided
        if domain_mappings:
            self.code_mapper.load_domain_mappings(
                list(domain_mappings.values()) if isinstance(domain_mappings, dict)
                else domain_mappings
            )

        if traceability:
            self.code_mapper.load_traceability(traceability)

        # Map all issues
        all_mappings = self.map_all_issues(issues)

        # Calculate scores and rank
        ranked_mappings = self.score_calculator.rank_mappings(all_mappings)

        # Build summaries by epic and feature
        epic_summaries = self._build_epic_summaries(ranked_mappings)
        feature_summaries = self._build_feature_summaries(ranked_mappings)

        # Get critical issues
        critical_issues = [
            m for m in ranked_mappings
            if m.issue.severity == ImpactSeverity.CRITICAL
        ]

        # Identify unmapped issues
        unmapped = [
            m.issue for m in ranked_mappings
            if not m.impact.epic_id and not m.impact.feature_id
        ]

        # Calculate overall metrics
        overall_health = self.score_calculator.calculate_health_score(ranked_mappings)

        # Count by severity
        by_severity = defaultdict(int)
        by_type = defaultdict(int)
        for mapping in ranked_mappings:
            by_severity[mapping.issue.severity.value] += 1
            by_type[mapping.issue.issue_type.value] += 1

        report = ProjectImpactReport(
            project_id=project_id,
            project_name=project_name,
            analysis_timestamp=datetime.now(timezone.utc),
            overall_health_score=overall_health,
            total_mappings=len(ranked_mappings),
            mappings_by_severity=dict(by_severity),
            mappings_by_type=dict(by_type),
            epic_summaries=epic_summaries,
            feature_summaries=feature_summaries,
            critical_issues=critical_issues,
            unmapped_issues=unmapped,
        )

        logger.info(
            f"Completed analysis: {len(ranked_mappings)} mappings, "
            f"{len(critical_issues)} critical, health={overall_health:.1f}%"
        )

        return report

    def map_all_issues(
        self,
        issues: List[QualityIssue],
    ) -> List[QualityImpactMapping]:
        """
        Map all issues to their functionality impact.

        Args:
            issues: List of quality issues

        Returns:
            List of QualityImpactMapping
        """
        mappings = []

        for issue in issues:
            try:
                mapping = self._map_single_issue(issue)
                mappings.append(mapping)
            except Exception as e:
                logger.warning(f"Failed to map issue {issue.issue_id}: {e}")

        return mappings

    def _map_single_issue(self, issue: QualityIssue) -> QualityImpactMapping:
        """Map a single issue using the appropriate mapper."""
        if issue.issue_type in (IssueType.SECURITY, IssueType.PRIVACY):
            return self.security_mapper.map_issue(issue, self.base_user_count)

        elif issue.issue_type == IssueType.PERFORMANCE:
            return self.performance_mapper.map_issue(issue, self.base_user_count)

        elif issue.issue_type in (IssueType.MEMORY_LEAK, IssueType.RESOURCE_LEAK):
            return self.memory_leak_mapper.map_issue(issue, self.base_user_count)

        else:
            # Generic mapping for other issue types
            return self._map_generic_issue(issue)

    def _map_generic_issue(self, issue: QualityIssue) -> QualityImpactMapping:
        """Map issue types without specific mappers."""
        file_path = issue.location.get("file", "")
        func_name = issue.location.get("function", "")

        func_mapping = self.code_mapper.map_code_location(
            file_path=file_path,
            function_name=func_name,
        )

        impact = FunctionalityImpact(
            epic_id=func_mapping.epic_id,
            epic_name=func_mapping.epic_name,
            feature_id=func_mapping.feature_id,
            feature_name=func_mapping.feature_name,
            story_id=func_mapping.story_id,
            story_name=func_mapping.story_name,
            users_affected_daily=self.base_user_count // 10,  # Conservative estimate
            business_process=func_mapping.epic_name or "Unknown",
            regulatory_risks=[],
            business_impact_description=f"{issue.issue_type.value}: {issue.description[:100]}",
            financial_risk_estimate="Impact assessment pending",
            confidence_score=func_mapping.confidence,
        )

        return QualityImpactMapping(issue=issue, impact=impact)

    def _build_epic_summaries(
        self,
        mappings: List[QualityImpactMapping],
    ) -> List[ImpactSummary]:
        """Build summaries grouped by epic."""
        # Group by epic
        by_epic: Dict[str, List[QualityImpactMapping]] = defaultdict(list)

        for mapping in mappings:
            epic_key = mapping.impact.epic_id or mapping.impact.epic_name or "Unmapped"
            by_epic[epic_key].append(mapping)

        # Create summaries
        summaries = []
        for epic_key, epic_mappings in by_epic.items():
            if epic_key == "Unmapped":
                continue

            # Get epic name from first mapping
            epic_name = epic_mappings[0].impact.epic_name or epic_key

            summary = self.score_calculator.create_summary(
                entity_type="epic",
                entity_id=epic_key,
                entity_name=epic_name,
                mappings=epic_mappings,
            )
            summaries.append(summary)

        # Sort by health score (worst first)
        return sorted(summaries, key=lambda s: s.health_score)

    def _build_feature_summaries(
        self,
        mappings: List[QualityImpactMapping],
    ) -> List[ImpactSummary]:
        """Build summaries grouped by feature."""
        # Group by feature
        by_feature: Dict[str, List[QualityImpactMapping]] = defaultdict(list)

        for mapping in mappings:
            feature_key = (
                mapping.impact.feature_id or
                mapping.impact.feature_name or
                "Unmapped"
            )
            by_feature[feature_key].append(mapping)

        # Create summaries
        summaries = []
        for feature_key, feature_mappings in by_feature.items():
            if feature_key == "Unmapped":
                continue

            feature_name = feature_mappings[0].impact.feature_name or feature_key

            summary = self.score_calculator.create_summary(
                entity_type="feature",
                entity_id=feature_key,
                entity_name=feature_name,
                mappings=feature_mappings,
            )
            summaries.append(summary)

        # Sort by health score (worst first)
        return sorted(summaries, key=lambda s: s.health_score)

    def get_epic_impact(
        self,
        epic_id: str,
        issues: List[QualityIssue],
    ) -> ImpactSummary:
        """
        Get impact summary for a specific epic.

        Args:
            epic_id: Epic identifier
            issues: All project issues

        Returns:
            ImpactSummary for the epic
        """
        mappings = self.map_all_issues(issues)
        epic_mappings = [
            m for m in mappings
            if m.impact.epic_id == epic_id
        ]

        if not epic_mappings:
            return ImpactSummary(
                entity_type="epic",
                entity_id=epic_id,
                entity_name=epic_id,
                health_score=100.0,
            )

        return self.score_calculator.create_summary(
            entity_type="epic",
            entity_id=epic_id,
            entity_name=epic_mappings[0].impact.epic_name or epic_id,
            mappings=epic_mappings,
        )

    def get_feature_impact(
        self,
        feature_id: str,
        issues: List[QualityIssue],
    ) -> ImpactSummary:
        """
        Get impact summary for a specific feature.

        Args:
            feature_id: Feature identifier
            issues: All project issues

        Returns:
            ImpactSummary for the feature
        """
        mappings = self.map_all_issues(issues)
        feature_mappings = [
            m for m in mappings
            if m.impact.feature_id == feature_id
        ]

        if not feature_mappings:
            return ImpactSummary(
                entity_type="feature",
                entity_id=feature_id,
                entity_name=feature_id,
                health_score=100.0,
            )

        return self.score_calculator.create_summary(
            entity_type="feature",
            entity_id=feature_id,
            entity_name=feature_mappings[0].impact.feature_name or feature_id,
            mappings=feature_mappings,
        )

    def get_critical_issues(
        self,
        issues: List[QualityIssue],
    ) -> List[QualityImpactMapping]:
        """
        Get all critical issues with their impact analysis.

        Args:
            issues: All project issues

        Returns:
            List of critical issue mappings, ranked by impact
        """
        mappings = self.map_all_issues(issues)
        critical = [
            m for m in mappings
            if m.issue.severity == ImpactSeverity.CRITICAL
        ]
        return self.score_calculator.rank_mappings(critical)


def create_quality_impact_service(
    base_user_count: int = 1000,
    max_daily_users: int = 10000,
    weights: Optional[ImpactWeights] = None,
) -> QualityImpactMappingService:
    """
    Factory function to create fully configured QualityImpactMappingService.

    Args:
        base_user_count: Default daily user count
        max_daily_users: Maximum users for score normalization
        weights: Custom impact weights

    Returns:
        Configured QualityImpactMappingService
    """
    code_mapper = CodeToFunctionalityMapper()
    score_calculator = ImpactScoreCalculator(
        weights=weights,
        max_daily_users=max_daily_users,
    )

    security_mapper = SecurityImpactMapper(code_mapper)
    performance_mapper = PerformanceImpactMapper(code_mapper)
    memory_leak_mapper = MemoryLeakImpactMapper(code_mapper)

    return QualityImpactMappingService(
        code_mapper=code_mapper,
        security_mapper=security_mapper,
        performance_mapper=performance_mapper,
        memory_leak_mapper=memory_leak_mapper,
        score_calculator=score_calculator,
        base_user_count=base_user_count,
    )
