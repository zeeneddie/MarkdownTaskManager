"""
Migration Report Service - Diana Integration

Week 68 Day 4-5: Markdown report generation for legacy migrations
Diana agent specializes in API docs, architecture docs, and user guides.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from pathlib import Path
from datetime import datetime
import uuid


# ==================== Enums ====================

class ReportType(Enum):
    """Types of migration reports"""
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_ASSESSMENT = "technical_assessment"
    SECURITY_AUDIT = "security_audit"
    ESTIMATION_REPORT = "estimation_report"
    ARCHITECTURE_RECOMMENDATION = "architecture_recommendation"
    FULL_MIGRATION_PLAN = "full_migration_plan"
    PROGRESS_REPORT = "progress_report"


class ReportFormat(Enum):
    """Output formats for reports"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"  # Placeholder for future
    JSON = "json"


class ReportSection(Enum):
    """Report sections"""
    EXECUTIVE_SUMMARY = "executive_summary"
    SYSTEM_OVERVIEW = "system_overview"
    TECHNOLOGY_ANALYSIS = "technology_analysis"
    SECURITY_FINDINGS = "security_findings"
    EFFORT_ESTIMATION = "effort_estimation"
    ARCHITECTURE_DESIGN = "architecture_design"
    MIGRATION_ROADMAP = "migration_roadmap"
    RISK_ASSESSMENT = "risk_assessment"
    RECOMMENDATIONS = "recommendations"
    APPENDICES = "appendices"


# ==================== Data Classes ====================

@dataclass
class ReportMetadata:
    """Report metadata"""
    report_id: str
    title: str
    report_type: ReportType
    created_at: str
    author: str
    version: str
    project_name: str
    directory_analyzed: str


@dataclass
class ReportSectionContent:
    """Content for a report section"""
    section: ReportSection
    title: str
    content: str
    subsections: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class DianaContext:
    """Context for Diana agent review"""
    summary: str
    key_findings: List[str]
    document_structure: List[str]
    style_guidelines: List[str]
    target_audience: str
    questions_for_review: List[str]


@dataclass
class MigrationReport:
    """Complete migration report"""
    metadata: ReportMetadata
    sections: List[ReportSectionContent]
    diana_context: DianaContext
    raw_data: Dict[str, Any]
    format: ReportFormat

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "report_id": self.metadata.report_id,
                "title": self.metadata.title,
                "report_type": self.metadata.report_type.value,
                "created_at": self.metadata.created_at,
                "author": self.metadata.author,
                "version": self.metadata.version,
                "project_name": self.metadata.project_name,
                "directory": self.metadata.directory_analyzed
            },
            "sections": [
                {
                    "section": s.section.value,
                    "title": s.title,
                    "content_length": len(s.content),
                    "subsection_count": len(s.subsections)
                }
                for s in self.sections
            ],
            "diana_context": {
                "summary": self.diana_context.summary,
                "key_findings": self.diana_context.key_findings,
                "target_audience": self.diana_context.target_audience,
                "questions_for_review": self.diana_context.questions_for_review
            },
            "format": self.format.value,
            "total_sections": len(self.sections)
        }

    def to_markdown(self) -> str:
        """Generate full markdown report"""
        lines = []

        # Title
        lines.append(f"# {self.metadata.title}")
        lines.append("")
        lines.append(f"**Report ID:** {self.metadata.report_id}")
        lines.append(f"**Generated:** {self.metadata.created_at}")
        lines.append(f"**Author:** {self.metadata.author}")
        lines.append(f"**Version:** {self.metadata.version}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Table of Contents
        lines.append("## Table of Contents")
        lines.append("")
        for i, section in enumerate(self.sections, 1):
            lines.append(f"{i}. [{section.title}](#{section.section.value})")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Sections
        for section in self.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

            for subsection in section.subsections:
                lines.append(f"### {subsection.get('title', 'Subsection')}")
                lines.append("")
                lines.append(subsection.get('content', ''))
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)


# ==================== Report Templates ====================

REPORT_TEMPLATES = {
    ReportType.EXECUTIVE_SUMMARY: {
        "sections": [
            ReportSection.EXECUTIVE_SUMMARY,
            ReportSection.RISK_ASSESSMENT,
            ReportSection.RECOMMENDATIONS
        ],
        "max_pages": 5,
        "audience": "C-level executives, project sponsors"
    },
    ReportType.TECHNICAL_ASSESSMENT: {
        "sections": [
            ReportSection.SYSTEM_OVERVIEW,
            ReportSection.TECHNOLOGY_ANALYSIS,
            ReportSection.ARCHITECTURE_DESIGN,
            ReportSection.RECOMMENDATIONS
        ],
        "max_pages": 20,
        "audience": "Technical leads, architects"
    },
    ReportType.SECURITY_AUDIT: {
        "sections": [
            ReportSection.EXECUTIVE_SUMMARY,
            ReportSection.SECURITY_FINDINGS,
            ReportSection.RISK_ASSESSMENT,
            ReportSection.RECOMMENDATIONS
        ],
        "max_pages": 15,
        "audience": "Security team, compliance officers"
    },
    ReportType.ESTIMATION_REPORT: {
        "sections": [
            ReportSection.EXECUTIVE_SUMMARY,
            ReportSection.EFFORT_ESTIMATION,
            ReportSection.MIGRATION_ROADMAP,
            ReportSection.RISK_ASSESSMENT
        ],
        "max_pages": 10,
        "audience": "Project managers, budget owners"
    },
    ReportType.ARCHITECTURE_RECOMMENDATION: {
        "sections": [
            ReportSection.SYSTEM_OVERVIEW,
            ReportSection.TECHNOLOGY_ANALYSIS,
            ReportSection.ARCHITECTURE_DESIGN,
            ReportSection.RECOMMENDATIONS,
            ReportSection.APPENDICES
        ],
        "max_pages": 30,
        "audience": "Architects, senior developers"
    },
    ReportType.FULL_MIGRATION_PLAN: {
        "sections": [
            ReportSection.EXECUTIVE_SUMMARY,
            ReportSection.SYSTEM_OVERVIEW,
            ReportSection.TECHNOLOGY_ANALYSIS,
            ReportSection.SECURITY_FINDINGS,
            ReportSection.EFFORT_ESTIMATION,
            ReportSection.ARCHITECTURE_DESIGN,
            ReportSection.MIGRATION_ROADMAP,
            ReportSection.RISK_ASSESSMENT,
            ReportSection.RECOMMENDATIONS,
            ReportSection.APPENDICES
        ],
        "max_pages": 50,
        "audience": "All stakeholders"
    }
}


# ==================== Service Implementation ====================

class MigrationReportService:
    """
    Diana integration for migration report generation.

    Generates comprehensive markdown reports combining:
    - Security analysis (Quinn)
    - Effort estimation (Eliza)
    - Architecture recommendations (Felix)
    """

    def __init__(self):
        self.supported_types = list(ReportType)
        self.supported_formats = list(ReportFormat)

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "MigrationReportService",
            "version": "1.0.0",
            "agent": "Diana",
            "capabilities": [
                "Executive summary generation",
                "Technical assessment reports",
                "Security audit reports",
                "Estimation reports",
                "Architecture recommendations",
                "Full migration plans"
            ],
            "supported_report_types": [t.value for t in self.supported_types],
            "supported_formats": [f.value for f in self.supported_formats],
            "section_types": [s.value for s in ReportSection]
        }

    def generate_report(
        self,
        report_type: ReportType,
        project_name: str,
        directory: str,
        security_data: Optional[Dict[str, Any]] = None,
        estimation_data: Optional[Dict[str, Any]] = None,
        architecture_data: Optional[Dict[str, Any]] = None,
        output_format: ReportFormat = ReportFormat.MARKDOWN
    ) -> MigrationReport:
        """
        Generate a migration report.

        Args:
            report_type: Type of report to generate
            project_name: Name of the project
            directory: Directory being analyzed
            security_data: Data from Quinn security analysis
            estimation_data: Data from Eliza estimation
            architecture_data: Data from Felix architecture recommendations
            output_format: Output format for the report

        Returns:
            Complete migration report
        """
        template = REPORT_TEMPLATES[report_type]

        # Generate metadata
        metadata = ReportMetadata(
            report_id=str(uuid.uuid4()),
            title=self._generate_title(report_type, project_name),
            report_type=report_type,
            created_at=datetime.now().isoformat(),
            author="Diana (AI Documentation Agent)",
            version="1.0.0",
            project_name=project_name,
            directory_analyzed=directory
        )

        # Generate sections based on template
        sections = []
        for section_type in template["sections"]:
            section_content = self._generate_section(
                section_type,
                security_data or {},
                estimation_data or {},
                architecture_data or {}
            )
            sections.append(section_content)

        # Generate Diana context
        diana_context = self._generate_diana_context(
            report_type,
            template["audience"],
            security_data,
            estimation_data,
            architecture_data
        )

        return MigrationReport(
            metadata=metadata,
            sections=sections,
            diana_context=diana_context,
            raw_data={
                "security": security_data,
                "estimation": estimation_data,
                "architecture": architecture_data
            },
            format=output_format
        )

    def _generate_title(self, report_type: ReportType, project_name: str) -> str:
        """Generate report title"""
        titles = {
            ReportType.EXECUTIVE_SUMMARY: f"{project_name} Migration - Executive Summary",
            ReportType.TECHNICAL_ASSESSMENT: f"{project_name} Technical Assessment Report",
            ReportType.SECURITY_AUDIT: f"{project_name} Security Audit Report",
            ReportType.ESTIMATION_REPORT: f"{project_name} Migration Estimation Report",
            ReportType.ARCHITECTURE_RECOMMENDATION: f"{project_name} Architecture Recommendation",
            ReportType.FULL_MIGRATION_PLAN: f"{project_name} Complete Migration Plan",
            ReportType.PROGRESS_REPORT: f"{project_name} Migration Progress Report"
        }
        return titles.get(report_type, f"{project_name} Migration Report")

    def _generate_section(
        self,
        section_type: ReportSection,
        security_data: Dict[str, Any],
        estimation_data: Dict[str, Any],
        architecture_data: Dict[str, Any]
    ) -> ReportSectionContent:
        """Generate content for a report section"""

        generators = {
            ReportSection.EXECUTIVE_SUMMARY: self._generate_executive_summary,
            ReportSection.SYSTEM_OVERVIEW: self._generate_system_overview,
            ReportSection.TECHNOLOGY_ANALYSIS: self._generate_technology_analysis,
            ReportSection.SECURITY_FINDINGS: self._generate_security_findings,
            ReportSection.EFFORT_ESTIMATION: self._generate_effort_estimation,
            ReportSection.ARCHITECTURE_DESIGN: self._generate_architecture_design,
            ReportSection.MIGRATION_ROADMAP: self._generate_migration_roadmap,
            ReportSection.RISK_ASSESSMENT: self._generate_risk_assessment,
            ReportSection.RECOMMENDATIONS: self._generate_recommendations,
            ReportSection.APPENDICES: self._generate_appendices
        }

        generator = generators.get(section_type, self._generate_placeholder)
        return generator(security_data, estimation_data, architecture_data)

    def _generate_executive_summary(
        self,
        security: Dict,
        estimation: Dict,
        architecture: Dict
    ) -> ReportSectionContent:
        """Generate executive summary section"""
        lines = []

        lines.append("This report presents a comprehensive analysis of the legacy system migration opportunity.")
        lines.append("")

        # Key Metrics
        lines.append("### Key Metrics")
        lines.append("")

        if estimation:
            fp = estimation.get("adjusted_fp", estimation.get("unadjusted_fp", "N/A"))
            hours = estimation.get("total_hours", "N/A")
            lines.append(f"- **Estimated Function Points:** {fp}")
            lines.append(f"- **Total Effort Hours:** {hours}")

        if security:
            findings = security.get("total_findings", 0)
            risk_score = security.get("risk_score", {}).get("total", "N/A")
            lines.append(f"- **Security Findings:** {findings}")
            lines.append(f"- **Risk Score:** {risk_score}")

        if architecture:
            pattern = architecture.get("architecture", {}).get("pattern", "N/A")
            strategy = architecture.get("architecture", {}).get("migration_strategy", "N/A")
            lines.append(f"- **Recommended Architecture:** {pattern}")
            lines.append(f"- **Migration Strategy:** {strategy}")

        lines.append("")

        # Key Findings
        lines.append("### Key Findings")
        lines.append("")

        if security and security.get("total_findings", 0) > 0:
            critical = security.get("risk_score", {}).get("critical_issues", 0)
            if critical > 0:
                lines.append(f"- **CRITICAL:** {critical} critical security issues require immediate attention")

        if estimation:
            lines.append(f"- Migration estimated at {estimation.get('total_days', 'N/A')} days with {estimation.get('team_size', 5)} developers")

        if architecture:
            confidence = architecture.get("metrics", {}).get("confidence_score", 0) * 100
            lines.append(f"- Architecture recommendation confidence: {confidence:.0f}%")

        lines.append("")

        # Recommendation
        lines.append("### Recommendation")
        lines.append("")
        lines.append("Based on the analysis, we recommend proceeding with the migration using ")
        lines.append("the proposed architecture pattern and strategy. Key success factors include ")
        lines.append("addressing critical security findings before migration and allocating ")
        lines.append("appropriate resources for each phase.")

        return ReportSectionContent(
            section=ReportSection.EXECUTIVE_SUMMARY,
            title="Executive Summary",
            content="\n".join(lines),
            subsections=[]
        )

    def _generate_system_overview(
        self,
        security: Dict,
        estimation: Dict,
        architecture: Dict
    ) -> ReportSectionContent:
        """Generate system overview section"""
        lines = []

        lines.append("### Current System Analysis")
        lines.append("")

        if architecture:
            source = architecture.get("source_analysis", {})
            lines.append(f"- **Total Files Analyzed:** {source.get('total_files', 'N/A')}")
            lines.append(f"- **Screen/Page Count:** {source.get('screen_count', 'N/A')}")
            lines.append(f"- **Database Tables:** {source.get('estimated_tables', 'N/A')}")
            lines.append(f"- **System Size Category:** {source.get('system_size', 'N/A')}")

        if security:
            stacks = security.get("stacks_detected", [])
            if stacks:
                lines.append(f"- **Technology Stacks Detected:** {', '.join(stacks)}")

        lines.append("")
        lines.append("### Component Distribution")
        lines.append("")

        if architecture:
            legacy = architecture.get("legacy_components", [])
            lines.append("| Layer | Component Count | Complexity |")
            lines.append("|-------|-----------------|------------|")
            layers = {}
            for comp in legacy:
                layer = comp.get("layer", "unknown")
                if layer not in layers:
                    layers[layer] = {"count": 0, "complexity": []}
                layers[layer]["count"] += 1
                layers[layer]["complexity"].append(comp.get("complexity", "medium"))

            for layer, data in layers.items():
                avg_complexity = max(set(data["complexity"]), key=data["complexity"].count)
                lines.append(f"| {layer} | {data['count']} | {avg_complexity} |")

        return ReportSectionContent(
            section=ReportSection.SYSTEM_OVERVIEW,
            title="System Overview",
            content="\n".join(lines),
            subsections=[]
        )

    def _generate_technology_analysis(
        self,
        security: Dict,
        estimation: Dict,
        architecture: Dict
    ) -> ReportSectionContent:
        """Generate technology analysis section"""
        lines = []

        lines.append("### Legacy Technology Stack")
        lines.append("")

        if security:
            stacks = security.get("stacks_detected", [])
            for stack in stacks:
                lines.append(f"- **{stack}**")
            lines.append("")

        lines.append("### Technology Debt Assessment")
        lines.append("")

        lines.append("The following technology debt items were identified:")
        lines.append("")
        lines.append("1. **Outdated Frameworks** - Legacy frameworks lack security updates")
        lines.append("2. **Deprecated APIs** - Several APIs are deprecated or unsupported")
        lines.append("3. **Security Vulnerabilities** - Known CVEs in legacy dependencies")
        lines.append("4. **Performance Limitations** - Architecture limits scalability")
        lines.append("")

        lines.append("### Target Technology Stack")
        lines.append("")

        if architecture:
            tech_stack = architecture.get("felix_context", {}).get("technology_stack", {})
            for key, value in tech_stack.items():
                lines.append(f"- **{key.title()}:** {value}")

        return ReportSectionContent(
            section=ReportSection.TECHNOLOGY_ANALYSIS,
            title="Technology Analysis",
            content="\n".join(lines),
            subsections=[]
        )

    def _generate_security_findings(
        self,
        security: Dict,
        estimation: Dict,
        architecture: Dict
    ) -> ReportSectionContent:
        """Generate security findings section"""
        lines = []

        lines.append("### Security Assessment Summary")
        lines.append("")

        if security:
            risk_score = security.get("risk_score", {})
            lines.append(f"- **Overall Risk Score:** {risk_score.get('total', 'N/A')}")
            lines.append(f"- **Risk Grade:** {risk_score.get('grade', 'N/A')}")
            lines.append("")

            lines.append("### Findings by Severity")
            lines.append("")
            lines.append("| Severity | Count |")
            lines.append("|----------|-------|")
            lines.append(f"| Critical | {risk_score.get('critical_issues', 0)} |")
            lines.append(f"| High | {risk_score.get('high_issues', 0)} |")
            lines.append(f"| Medium | {risk_score.get('medium_issues', 0)} |")
            lines.append(f"| Low | {risk_score.get('low_issues', 0)} |")
            lines.append("")

            lines.append("### OWASP Top 10 Coverage")
            lines.append("")
            owasp = risk_score.get("owasp_coverage", {})
            for category, findings in owasp.items():
                status = "✅" if findings == 0 else "⚠️" if findings < 3 else "❌"
                lines.append(f"- {status} **{category}:** {findings} findings")
            lines.append("")

            lines.append("### Top Risks")
            lines.append("")
            top_risks = risk_score.get("top_risks", [])
            for i, risk in enumerate(top_risks[:5], 1):
                lines.append(f"{i}. {risk}")

        else:
            lines.append("*No security analysis data available. Run Quinn security scan first.*")

        return ReportSectionContent(
            section=ReportSection.SECURITY_FINDINGS,
            title="Security Findings",
            content="\n".join(lines),
            subsections=[]
        )

    def _generate_effort_estimation(
        self,
        security: Dict,
        estimation: Dict,
        architecture: Dict
    ) -> ReportSectionContent:
        """Generate effort estimation section"""
        lines = []

        lines.append("### Function Point Analysis")
        lines.append("")

        if estimation:
            lines.append(f"- **Unadjusted Function Points (UFP):** {estimation.get('unadjusted_fp', 'N/A')}")
            lines.append(f"- **Adjusted Function Points (AFP):** {estimation.get('adjusted_fp', 'N/A')}")
            lines.append(f"- **Value Adjustment Factor (VAF):** {estimation.get('vaf', 'N/A')}")
            lines.append("")

            lines.append("### Component Breakdown")
            lines.append("")
            lines.append("| Component Type | Count | Function Points |")
            lines.append("|----------------|-------|-----------------|")

            components = estimation.get("components", [])
            by_type = {}
            for comp in components:
                comp_type = comp.get("type", "unknown")
                if comp_type not in by_type:
                    by_type[comp_type] = {"count": 0, "fp": 0}
                by_type[comp_type]["count"] += 1
                by_type[comp_type]["fp"] += comp.get("function_points", 0)

            for comp_type, data in by_type.items():
                lines.append(f"| {comp_type} | {data['count']} | {data['fp']:.1f} |")
            lines.append("")

            lines.append("### Effort Summary")
            lines.append("")
            lines.append(f"- **Total Hours:** {estimation.get('total_hours', 'N/A')}")
            lines.append(f"- **Total Days:** {estimation.get('total_days', 'N/A')}")
            lines.append(f"- **Team Size:** {estimation.get('team_size', 'N/A')}")
            lines.append(f"- **Duration (weeks):** {estimation.get('duration_weeks', 'N/A')}")
            lines.append("")

            lines.append("### Phase Distribution")
            lines.append("")
            lines.append("| Phase | Hours | Days | Percentage |")
            lines.append("|-------|-------|------|------------|")

            phases = estimation.get("phases", [])
            for phase in phases:
                lines.append(f"| {phase.get('phase', 'N/A')} | {phase.get('hours', 0):.0f} | {phase.get('days', 0):.1f} | {phase.get('percentage', 0):.1f}% |")

        else:
            lines.append("*No estimation data available. Run Eliza estimation first.*")

        return ReportSectionContent(
            section=ReportSection.EFFORT_ESTIMATION,
            title="Effort Estimation",
            content="\n".join(lines),
            subsections=[]
        )

    def _generate_architecture_design(
        self,
        security: Dict,
        estimation: Dict,
        architecture: Dict
    ) -> ReportSectionContent:
        """Generate architecture design section"""
        lines = []

        if architecture:
            arch_info = architecture.get("architecture", {})
            lines.append("### Recommended Architecture")
            lines.append("")
            lines.append(f"- **Pattern:** {arch_info.get('pattern', 'N/A')}")
            lines.append(f"- **Migration Strategy:** {arch_info.get('migration_strategy', 'N/A')}")
            lines.append("")

            lines.append("### Design Principles")
            lines.append("")
            principles = arch_info.get("design_principles", [])
            for principle in principles:
                lines.append(f"- {principle}")
            lines.append("")

            lines.append("### Target Components")
            lines.append("")
            lines.append("| Component | Layer | Technology | Effort (hrs) |")
            lines.append("|-----------|-------|------------|--------------|")

            components = architecture.get("target_components", [])
            for comp in components:
                lines.append(
                    f"| {comp.get('name', 'N/A')} | "
                    f"{comp.get('layer', 'N/A')} | "
                    f"{comp.get('technology', 'N/A')} | "
                    f"{comp.get('effort_hours', 0):.0f} |"
                )
            lines.append("")

            lines.append("### Architecture Decision Records")
            lines.append("")
            adrs = architecture.get("architecture_decisions", [])
            for adr in adrs:
                lines.append(f"#### {adr.get('id', 'ADR')}: {adr.get('title', 'Decision')}")
                lines.append("")
                lines.append(f"**Status:** {adr.get('status', 'proposed')}")
                lines.append("")
                lines.append(f"**Decision:** {adr.get('decision', 'N/A')}")
                lines.append("")

        else:
            lines.append("*No architecture data available. Run Felix analysis first.*")

        return ReportSectionContent(
            section=ReportSection.ARCHITECTURE_DESIGN,
            title="Architecture Design",
            content="\n".join(lines),
            subsections=[]
        )

    def _generate_migration_roadmap(
        self,
        security: Dict,
        estimation: Dict,
        architecture: Dict
    ) -> ReportSectionContent:
        """Generate migration roadmap section"""
        lines = []

        lines.append("### Migration Phases")
        lines.append("")
        lines.append("```")
        lines.append("Phase 1: Discovery & Planning (10%)")
        lines.append("  └─ Week 1-2: Assessment and documentation")
        lines.append("")
        lines.append("Phase 2: Foundation (15%)")
        lines.append("  └─ Week 3-4: Infrastructure and core setup")
        lines.append("")
        lines.append("Phase 3: Development (40%)")
        lines.append("  └─ Week 5-12: Feature migration")
        lines.append("")
        lines.append("Phase 4: Testing (20%)")
        lines.append("  └─ Week 13-16: Integration and UAT")
        lines.append("")
        lines.append("Phase 5: Deployment (15%)")
        lines.append("  └─ Week 17-20: Parallel run and cutover")
        lines.append("```")
        lines.append("")

        lines.append("### Data Migration Sequence")
        lines.append("")

        if architecture:
            data_plan = architecture.get("data_migration", [])
            if data_plan:
                lines.append("| Order | Source Table | Target Table | Dependencies |")
                lines.append("|-------|--------------|--------------|--------------|")
                for item in data_plan[:10]:  # Top 10
                    lines.append(
                        f"| {item.get('order', 'N/A')} | "
                        f"{item.get('source', 'N/A')} | "
                        f"{item.get('target', 'N/A')} | "
                        f"{len(item.get('dependencies', []))} |"
                    )

        lines.append("")
        lines.append("### Key Milestones")
        lines.append("")
        lines.append("- [ ] **M1:** Foundation complete")
        lines.append("- [ ] **M2:** Core features migrated")
        lines.append("- [ ] **M3:** Integration testing complete")
        lines.append("- [ ] **M4:** User acceptance sign-off")
        lines.append("- [ ] **M5:** Production cutover")

        return ReportSectionContent(
            section=ReportSection.MIGRATION_ROADMAP,
            title="Migration Roadmap",
            content="\n".join(lines),
            subsections=[]
        )

    def _generate_risk_assessment(
        self,
        security: Dict,
        estimation: Dict,
        architecture: Dict
    ) -> ReportSectionContent:
        """Generate risk assessment section"""
        lines = []

        lines.append("### Risk Matrix")
        lines.append("")
        lines.append("| Risk | Impact | Likelihood | Mitigation |")
        lines.append("|------|--------|------------|------------|")

        risks = []

        if security:
            risk_data = security.get("risk_score", {})
            if risk_data.get("critical_issues", 0) > 0:
                risks.append({
                    "risk": "Critical security vulnerabilities",
                    "impact": "High",
                    "likelihood": "High",
                    "mitigation": "Address before migration"
                })

            blockers = risk_data.get("migration_blockers", [])
            for blocker in blockers[:3]:
                risks.append({
                    "risk": blocker,
                    "impact": "High",
                    "likelihood": "Medium",
                    "mitigation": "Create remediation plan"
                })

        if architecture:
            arch_risks = architecture.get("risks", [])
            for risk in arch_risks[:5]:
                risks.append({
                    "risk": risk,
                    "impact": "Medium",
                    "likelihood": "Medium",
                    "mitigation": "Monitor and address"
                })

        # Default risks
        default_risks = [
            {"risk": "Knowledge loss from legacy team", "impact": "High", "likelihood": "Medium", "mitigation": "Document thoroughly"},
            {"risk": "Data migration issues", "impact": "High", "likelihood": "Medium", "mitigation": "Test data migration early"},
            {"risk": "Performance regression", "impact": "Medium", "likelihood": "Medium", "mitigation": "Benchmark comparison"},
            {"risk": "Timeline slippage", "impact": "Medium", "likelihood": "High", "mitigation": "Build in contingency"}
        ]
        risks.extend(default_risks)

        for r in risks[:10]:
            lines.append(f"| {r['risk'][:40]} | {r['impact']} | {r['likelihood']} | {r['mitigation'][:30]} |")

        lines.append("")
        lines.append("### Contingency Planning")
        lines.append("")
        lines.append("1. **Rollback Plan:** Maintain legacy system availability throughout migration")
        lines.append("2. **Data Recovery:** Regular backups during data migration phases")
        lines.append("3. **Resource Backup:** Identify backup resources for key roles")
        lines.append("4. **Timeline Buffer:** 20% contingency built into estimates")

        return ReportSectionContent(
            section=ReportSection.RISK_ASSESSMENT,
            title="Risk Assessment",
            content="\n".join(lines),
            subsections=[]
        )

    def _generate_recommendations(
        self,
        security: Dict,
        estimation: Dict,
        architecture: Dict
    ) -> ReportSectionContent:
        """Generate recommendations section"""
        lines = []

        lines.append("### Immediate Actions")
        lines.append("")

        immediate = []
        if security:
            critical = security.get("risk_score", {}).get("critical_issues", 0)
            if critical > 0:
                immediate.append(f"🚨 Address {critical} critical security issues before migration")

        immediate.extend([
            "📋 Complete stakeholder alignment and sign-off",
            "📅 Finalize resource allocation and timeline",
            "📚 Document all undocumented business rules"
        ])

        for i, action in enumerate(immediate, 1):
            lines.append(f"{i}. {action}")

        lines.append("")
        lines.append("### Technical Recommendations")
        lines.append("")

        tech_recs = []
        if architecture:
            tech_recs = architecture.get("recommendations", [])[:5]
        else:
            tech_recs = [
                "Implement automated testing pipeline",
                "Set up CI/CD for new system",
                "Create feature flags for gradual rollout",
                "Establish monitoring and alerting"
            ]

        for rec in tech_recs:
            lines.append(f"- {rec}")

        lines.append("")
        lines.append("### Process Recommendations")
        lines.append("")
        lines.append("- Conduct weekly migration status meetings")
        lines.append("- Establish clear escalation paths")
        lines.append("- Document decisions in ADR format")
        lines.append("- Regular stakeholder communication")

        lines.append("")
        lines.append("### Success Criteria")
        lines.append("")
        lines.append("- [ ] All critical security issues resolved")
        lines.append("- [ ] Data migration validated with 99.9% accuracy")
        lines.append("- [ ] Performance meets or exceeds legacy system")
        lines.append("- [ ] User acceptance testing passed")
        lines.append("- [ ] Zero-downtime cutover achieved")

        return ReportSectionContent(
            section=ReportSection.RECOMMENDATIONS,
            title="Recommendations",
            content="\n".join(lines),
            subsections=[]
        )

    def _generate_appendices(
        self,
        security: Dict,
        estimation: Dict,
        architecture: Dict
    ) -> ReportSectionContent:
        """Generate appendices section"""
        lines = []

        lines.append("### Appendix A: Glossary")
        lines.append("")
        lines.append("| Term | Definition |")
        lines.append("|------|------------|")
        lines.append("| UFP | Unadjusted Function Points |")
        lines.append("| AFP | Adjusted Function Points |")
        lines.append("| VAF | Value Adjustment Factor |")
        lines.append("| OWASP | Open Web Application Security Project |")
        lines.append("| ADR | Architecture Decision Record |")
        lines.append("| IFPUG | International Function Point Users Group |")
        lines.append("")

        lines.append("### Appendix B: References")
        lines.append("")
        lines.append("- IFPUG CPM 4.3.1 - Function Point Counting Practices Manual")
        lines.append("- OWASP Top 10 2021 - Web Application Security Risks")
        lines.append("- ISO/IEC 20926:2009 - Software measurement functional size")
        lines.append("")

        lines.append("### Appendix C: Tool Versions")
        lines.append("")
        lines.append("| Tool | Version |")
        lines.append("|------|---------|")
        lines.append("| Quinn Security Scanner | 1.0.0 |")
        lines.append("| Eliza Estimation Engine | 1.0.0 |")
        lines.append("| Felix Architecture Analyzer | 1.0.0 |")
        lines.append("| Diana Report Generator | 1.0.0 |")

        return ReportSectionContent(
            section=ReportSection.APPENDICES,
            title="Appendices",
            content="\n".join(lines),
            subsections=[]
        )

    def _generate_placeholder(
        self,
        security: Dict,
        estimation: Dict,
        architecture: Dict
    ) -> ReportSectionContent:
        """Generate placeholder for missing sections"""
        return ReportSectionContent(
            section=ReportSection.APPENDICES,
            title="Additional Information",
            content="*Section content to be added.*",
            subsections=[]
        )

    def _generate_diana_context(
        self,
        report_type: ReportType,
        audience: str,
        security: Optional[Dict],
        estimation: Optional[Dict],
        architecture: Optional[Dict]
    ) -> DianaContext:
        """Generate Diana agent context"""
        key_findings = []

        if security:
            findings = security.get("total_findings", 0)
            key_findings.append(f"Security: {findings} vulnerabilities found")

        if estimation:
            hours = estimation.get("total_hours", 0)
            key_findings.append(f"Estimation: {hours} total hours estimated")

        if architecture:
            pattern = architecture.get("architecture", {}).get("pattern", "N/A")
            key_findings.append(f"Architecture: {pattern} recommended")

        return DianaContext(
            summary=f"Migration report generation for {audience}",
            key_findings=key_findings,
            document_structure=[s.value for s in REPORT_TEMPLATES[report_type]["sections"]],
            style_guidelines=[
                "Use professional technical writing style",
                "Include executive summary for non-technical readers",
                "Provide actionable recommendations",
                "Use tables for data presentation",
                "Include risk assessment with mitigations"
            ],
            target_audience=audience,
            questions_for_review=[
                "Is the report structure appropriate for the audience?",
                "Are technical details at the right level?",
                "Are recommendations actionable and specific?",
                "Is the risk assessment comprehensive?",
                "Does the report provide clear next steps?"
            ]
        )

    def get_report_types(self) -> List[Dict[str, Any]]:
        """Get all available report types"""
        return [
            {
                "id": t.value,
                "name": t.name.replace("_", " ").title(),
                "sections": [s.value for s in REPORT_TEMPLATES[t]["sections"]],
                "max_pages": REPORT_TEMPLATES[t]["max_pages"],
                "audience": REPORT_TEMPLATES[t]["audience"]
            }
            for t in ReportType
            if t in REPORT_TEMPLATES
        ]

    def get_sections(self) -> List[Dict[str, str]]:
        """Get all available report sections"""
        return [
            {
                "id": s.value,
                "name": s.name.replace("_", " ").title()
            }
            for s in ReportSection
        ]
