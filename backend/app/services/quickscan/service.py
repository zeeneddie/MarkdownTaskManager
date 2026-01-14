"""
Legacy Quickscan Service.

Fase 24 - A1: Main orchestrator for 15-minute legacy assessment.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .models import (
    QuickscanConfig,
    QuickscanReport,
    QuickscanResult,
    Recommendation,
    ModernizationApproach,
    RiskLevel,
)
from .analyzers import (
    TechnologyDetector,
    ComplexityAnalyzer,
    SecurityAnalyzer,
    EffortEstimator,
)

logger = logging.getLogger(__name__)


class LegacyQuickscanService:
    """
    15-minute automated legacy assessment service.

    Provides Go/No-Go decision for legacy modernization projects.

    Features:
    - Technology stack detection
    - Complexity analysis
    - Security risk assessment
    - Effort estimation
    - Go/No-Go recommendation
    """

    def __init__(self):
        self.analyzers = [
            TechnologyDetector(),
            ComplexityAnalyzer(),
            SecurityAnalyzer(),
            EffortEstimator(),
        ]

    async def scan(self, config: QuickscanConfig) -> QuickscanReport:
        """
        Execute quickscan and return comprehensive report.

        Target: < 15 minutes for 100K LOC

        Args:
            config: Quickscan configuration

        Returns:
            QuickscanReport with all analysis results and recommendation
        """
        started = datetime.utcnow()
        report = QuickscanReport(
            project_name=config.project_name,
            project_path=str(config.project_path),
            started_at=started,
        )

        logger.info(f"Starting quickscan for {config.project_name} at {config.project_path}")

        # Run analyzers in parallel with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[
                    analyzer.analyze(config)
                    for analyzer in self.analyzers
                ], return_exceptions=True),
                timeout=config.max_scan_time_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Quickscan timed out after {config.max_scan_time_seconds}s")
            results = []

        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Analyzer failed: {result}")
                report.analyzer_results.append(QuickscanResult(
                    analyzer_name="unknown",
                    success=False,
                    duration_seconds=0,
                    errors=[str(result)],
                ))
                continue

            report.analyzer_results.append(result)

            # Extract specific data
            if result.success:
                if "technology_stack" in result.data:
                    report.technology_stack = result.data["technology_stack"]
                if "complexity_score" in result.data:
                    report.complexity_score = result.data["complexity_score"]
                if "risk_assessment" in result.data:
                    report.risk_assessment = result.data["risk_assessment"]
                if "effort_estimate" in result.data:
                    report.effort_estimate = result.data["effort_estimate"]

        # Generate recommendation
        self._generate_recommendation(report)

        # Generate key findings
        self._generate_findings(report)

        # Finalize
        report.completed_at = datetime.utcnow()
        report.duration_seconds = (report.completed_at - started).total_seconds()

        logger.info(
            f"Quickscan completed in {report.duration_seconds:.1f}s - "
            f"Recommendation: {report.recommendation.value}"
        )

        return report

    def _generate_recommendation(self, report: QuickscanReport) -> None:
        """Generate Go/No-Go recommendation based on analysis results."""
        score = 50.0  # Start neutral
        reasons = []

        # Technology scoring
        if report.technology_stack:
            tech = report.technology_stack
            primary = tech.primary_language

            # Legacy languages reduce score
            if primary in ["Classic ASP", "VB6", "COBOL"]:
                score -= 15
                reasons.append(f"Legacy technology: {primary} requires specialized skills")
            elif primary in ["Delphi/Pascal", "ASP.NET WebForms"]:
                score -= 10
                reasons.append(f"Older technology: {primary} may limit modernization options")
            else:
                score += 5
                reasons.append(f"Technology stack ({primary}) is relatively modern")

            # Multiple languages complexity
            if len(tech.languages) > 5:
                score -= 5
                reasons.append(f"Multi-language codebase ({len(tech.languages)} languages) adds complexity")

            # Modern indicators
            if tech.modern_indicators:
                score += 5
                reasons.append("Some modern patterns detected")

        # Complexity scoring
        if report.complexity_score:
            comp = report.complexity_score

            # LOC factor
            if comp.lines_of_code > 500000:
                score -= 15
                reasons.append(f"Very large codebase: {comp.lines_of_code:,} LOC")
            elif comp.lines_of_code > 100000:
                score -= 10
                reasons.append(f"Large codebase: {comp.lines_of_code:,} LOC")
            elif comp.lines_of_code < 10000:
                score += 10
                reasons.append(f"Manageable codebase size: {comp.lines_of_code:,} LOC")

            # Complexity factor
            if comp.overall_score > 70:
                score -= 15
                reasons.append(f"High complexity score: {comp.overall_score:.0f}/100")
            elif comp.overall_score < 30:
                score += 10
                reasons.append(f"Low complexity score: {comp.overall_score:.0f}/100")

            # Maintainability
            if comp.maintainability_index < 40:
                score -= 10
                reasons.append(f"Poor maintainability index: {comp.maintainability_index:.0f}/100")
            elif comp.maintainability_index > 70:
                score += 5
                reasons.append(f"Good maintainability index: {comp.maintainability_index:.0f}/100")

        # Security scoring
        if report.risk_assessment:
            risk = report.risk_assessment

            if risk.risk_level == RiskLevel.CRITICAL:
                score -= 20
                reasons.append(f"Critical security risks detected ({risk.critical_findings} critical findings)")
            elif risk.risk_level == RiskLevel.HIGH:
                score -= 10
                reasons.append(f"High security risks detected ({risk.high_findings} high findings)")
            elif risk.risk_level == RiskLevel.LOW:
                score += 5
                reasons.append("Low security risk profile")

        # Effort scoring
        if report.effort_estimate:
            effort = report.effort_estimate

            if effort.total_person_months > 100:
                score -= 10
                reasons.append(f"High estimated effort: {effort.total_person_months:.0f} person-months")
            elif effort.total_person_months < 20:
                score += 10
                reasons.append(f"Manageable estimated effort: {effort.total_person_months:.0f} person-months")

        # Normalize score
        score = max(0, min(100, score))

        # Determine recommendation
        if score >= 60:
            recommendation = Recommendation.GO
        elif score >= 35:
            recommendation = Recommendation.CONDITIONAL
        else:
            recommendation = Recommendation.NO_GO

        report.recommendation = recommendation
        report.recommendation_score = round(score, 1)
        report.recommendation_reasons = reasons

        # Determine modernization approach
        report.suggested_approach, report.approach_rationale = self._determine_approach(report)

    def _determine_approach(self, report: QuickscanReport) -> tuple:
        """Determine recommended modernization approach."""
        if not report.technology_stack or not report.complexity_score:
            return ModernizationApproach.REFACTOR, "Default approach due to incomplete analysis"

        tech = report.technology_stack
        comp = report.complexity_score
        primary = tech.primary_language

        # Very old legacy - consider replace/rebuild
        if primary in ["COBOL", "VB6"]:
            if comp.lines_of_code > 100000:
                return (
                    ModernizationApproach.REPLACE,
                    f"Large {primary} codebase - consider COTS replacement or greenfield rebuild"
                )
            else:
                return (
                    ModernizationApproach.REBUILD,
                    f"{primary} modernization typically requires full rewrite"
                )

        # Classic ASP - refactor to ASP.NET Core
        if primary == "Classic ASP":
            return (
                ModernizationApproach.REFACTOR,
                "Classic ASP can be modernized to ASP.NET Core with business logic preservation"
            )

        # ASP.NET WebForms - replatform to MVC/Blazor
        if primary in ["ASP.NET WebForms", "ASP.NET MVC/Razor"]:
            return (
                ModernizationApproach.REPLATFORM,
                "ASP.NET WebForms/MVC can be migrated to Blazor/ASP.NET Core"
            )

        # Low complexity modern code - rehost
        if comp.overall_score < 30 and primary in ["C#", "Java", "JavaScript", "TypeScript"]:
            return (
                ModernizationApproach.REHOST,
                "Low complexity modern codebase - consider lift & shift to cloud"
            )

        # Default
        return (
            ModernizationApproach.REFACTOR,
            "Standard refactoring approach recommended"
        )

    def _generate_findings(self, report: QuickscanReport) -> None:
        """Generate key findings, opportunities and challenges."""
        key_findings = []
        opportunities = []
        challenges = []
        next_steps = []

        # Technology findings
        if report.technology_stack:
            tech = report.technology_stack
            key_findings.append(
                f"Primary technology: {tech.primary_language} "
                f"({sum(tech.languages.values()):,} total LOC)"
            )
            if tech.estimated_age_years:
                key_findings.append(f"Estimated codebase age: ~{tech.estimated_age_years} years")

            if tech.databases:
                key_findings.append(f"Databases detected: {', '.join(tech.databases)}")

            if tech.modern_indicators:
                opportunities.append("Modern patterns already in use - incremental modernization possible")

            if tech.legacy_indicators:
                challenges.append(f"Legacy patterns detected: {len(tech.legacy_indicators)} indicators")

        # Complexity findings
        if report.complexity_score:
            comp = report.complexity_score
            key_findings.append(
                f"Complexity score: {comp.overall_score:.0f}/100 "
                f"(maintainability: {comp.maintainability_index:.0f}/100)"
            )

            if comp.duplication_percentage > 15:
                challenges.append(f"High code duplication: {comp.duplication_percentage:.0f}%")
            else:
                opportunities.append("Low code duplication - cleaner modernization")

            if comp.high_complexity_files:
                challenges.append(
                    f"High complexity hotspots: {len(comp.high_complexity_files)} files need attention"
                )

            if comp.technical_debt_hours > 100:
                challenges.append(f"Technical debt estimate: {comp.technical_debt_hours:.0f} hours")

        # Security findings
        if report.risk_assessment:
            risk = report.risk_assessment
            total_findings = risk.critical_findings + risk.high_findings + risk.medium_findings
            key_findings.append(
                f"Security risk level: {risk.risk_level.value.upper()} "
                f"({total_findings} findings)"
            )

            if risk.critical_findings > 0:
                challenges.append(f"{risk.critical_findings} critical security issues require immediate attention")

            if risk.security_risks:
                top_risks = [r.cwe_id for r in risk.security_risks[:3]]
                challenges.append(f"Top security risks: {', '.join(top_risks)}")

        # Effort findings
        if report.effort_estimate:
            effort = report.effort_estimate
            key_findings.append(
                f"Estimated effort: {effort.total_person_months:.0f} person-months "
                f"(range: {effort.optimistic_months:.0f}-{effort.pessimistic_months:.0f})"
            )

        # Generate next steps based on recommendation
        if report.recommendation == Recommendation.GO:
            next_steps = [
                "Schedule detailed Brown Paper analysis session",
                "Identify pilot module for proof of concept",
                "Assemble modernization team",
                "Define target architecture",
                "Create detailed migration roadmap",
            ]
            opportunities.append("Project is a good candidate for modernization")
        elif report.recommendation == Recommendation.CONDITIONAL:
            next_steps = [
                "Address critical security findings first",
                "Perform deeper analysis on high-complexity areas",
                "Evaluate business case ROI",
                "Consider phased approach starting with lowest-risk modules",
                "Get stakeholder alignment on risks and timeline",
            ]
            challenges.append("Project requires careful planning and risk mitigation")
        else:  # NO_GO
            next_steps = [
                "Evaluate COTS replacement options",
                "Consider greenfield rebuild if business critical",
                "Document business rules for potential rewrite",
                "Assess minimal maintenance strategy",
                "Review business case for modernization investment",
            ]
            challenges.append("Modernization may not be cost-effective - consider alternatives")

        report.key_findings = key_findings
        report.opportunities = opportunities
        report.challenges = challenges
        report.recommended_next_steps = next_steps


def create_quickscan_service() -> LegacyQuickscanService:
    """Factory function to create quickscan service."""
    return LegacyQuickscanService()
