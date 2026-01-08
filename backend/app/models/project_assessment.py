"""
Project Assessment & Migration Planning Models

Week 69: Gestandaardiseerde Project Workflows
SQLAlchemy models for standardized project analysis and migration planning.

Models:
- ProjectAssessment: Workflow 1 output - complete project health analysis
- MigrationPlan: Workflow 2 output - migration planning (requires assessment)
- AssessmentPhase: Phase tracking for workflow execution

Author: Claude Code (Week 69)
Date: 2025-12-15
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ProjectAssessment(Base):
    """
    Workflow 1 Output: Complete project health assessment

    Contains results from:
    - ApplicationRegistry scan (registration)
    - Miguel AS-IS architecture analysis
    - CodeRAG code analysis
    - Quinn security findings
    - Quinn quality report
    - Diana health report
    """
    __tablename__ = 'project_assessments'

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='SET NULL'), nullable=True)

    # Project identification
    project_name = Column(String(255), nullable=False)
    directory_path = Column(String(1024), nullable=False)

    # Assessment metadata
    assessment_date = Column(DateTime(timezone=True), server_default=func.now())
    assessment_version = Column(Integer, default=1)

    # === Phase 1: Registration (ApplicationRegistry) ===
    detected_stacks = Column(JSONB, default=[])  # ["python", "javascript", "sql"]
    primary_stack = Column(String(50))
    file_count = Column(Integer, default=0)
    line_count = Column(Integer, default=0)
    component_count = Column(Integer, default=0)

    # === Phase 2: AS-IS Architecture (Miguel) ===
    as_is_architecture = Column(JSONB, default={})
    architecture_pattern = Column(String(50))  # monolith, layered, microservices, etc.
    architecture_layers = Column(JSONB, default=[])  # ["presentation", "business", "data"]
    architecture_components = Column(JSONB, default=[])  # [{name, type, dependencies}]
    architecture_score = Column(Integer)  # 0-100
    architecture_issues = Column(JSONB, default=[])  # [{issue, severity, recommendation}]

    # === Phase 3: Code Analysis (CodeRAG) ===
    code_analysis = Column(JSONB, default={})
    code_patterns = Column(JSONB, default=[])  # Detected patterns
    code_dependencies = Column(JSONB, default=[])  # External dependencies
    code_complexity = Column(JSONB, default={})  # Cyclomatic, cognitive, etc.
    code_duplication_percent = Column(Float)
    code_test_coverage_percent = Column(Float)

    # === Phase 4: Security Analysis (Quinn) ===
    security_findings = Column(JSONB, default=[])  # [{finding, severity, owasp, file, line}]
    security_finding_count = Column(Integer, default=0)
    security_critical_count = Column(Integer, default=0)
    security_high_count = Column(Integer, default=0)
    security_medium_count = Column(Integer, default=0)
    security_low_count = Column(Integer, default=0)
    security_risk_score = Column(Integer)  # 0-100
    security_grade = Column(String(1))  # A-F
    owasp_coverage = Column(JSONB, default={})  # {"A01": 3, "A03": 5, ...}

    # === Phase 5: Quality Analysis (Quinn) ===
    quality_report = Column(JSONB, default={})
    quality_issues = Column(JSONB, default=[])  # [{issue, type, severity, file}]
    quality_issue_count = Column(Integer, default=0)
    tech_debt_hours = Column(Float)  # Estimated hours to fix
    code_smell_count = Column(Integer, default=0)
    maintainability_index = Column(Float)  # 0-100
    quality_score = Column(Integer)  # 0-100
    quality_grade = Column(String(1))  # A-F

    # === Overall Assessment ===
    overall_health_score = Column(Integer)  # 0-100 weighted average
    overall_grade = Column(String(1))  # A-F
    health_summary = Column(Text)  # Diana-generated summary

    # Recommendations (consolidated)
    recommendations = Column(JSONB, default=[])  # [{category, priority, title, description}]
    blockers = Column(JSONB, default=[])  # Critical issues that block migration

    # === Workflow Status ===
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    current_phase = Column(String(50))  # registration, as_is, code, security, quality, report
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text)

    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    phases = relationship("AssessmentPhase", back_populates="assessment", cascade="all, delete-orphan")
    migration_plans = relationship("MigrationPlan", back_populates="assessment", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id else None,
            "application_id": self.application_id,
            "project_name": self.project_name,
            "directory_path": self.directory_path,
            "assessment_date": self.assessment_date.isoformat() if self.assessment_date else None,
            "assessment_version": self.assessment_version,
            # Registration
            "detected_stacks": self.detected_stacks,
            "primary_stack": self.primary_stack,
            "file_count": self.file_count,
            "line_count": self.line_count,
            "component_count": self.component_count,
            # AS-IS Architecture
            "as_is_architecture": self.as_is_architecture,
            "architecture_pattern": self.architecture_pattern,
            "architecture_layers": self.architecture_layers,
            "architecture_components": self.architecture_components,
            "architecture_score": self.architecture_score,
            "architecture_issues": self.architecture_issues,
            # Code Analysis
            "code_analysis": self.code_analysis,
            "code_patterns": self.code_patterns,
            "code_dependencies": self.code_dependencies,
            "code_complexity": self.code_complexity,
            "code_duplication_percent": self.code_duplication_percent,
            "code_test_coverage_percent": self.code_test_coverage_percent,
            # Security
            "security_findings": self.security_findings,
            "security_finding_count": self.security_finding_count,
            "security_critical_count": self.security_critical_count,
            "security_high_count": self.security_high_count,
            "security_medium_count": self.security_medium_count,
            "security_low_count": self.security_low_count,
            "security_risk_score": self.security_risk_score,
            "security_grade": self.security_grade,
            "owasp_coverage": self.owasp_coverage,
            # Quality
            "quality_report": self.quality_report,
            "quality_issues": self.quality_issues,
            "quality_issue_count": self.quality_issue_count,
            "tech_debt_hours": self.tech_debt_hours,
            "code_smell_count": self.code_smell_count,
            "maintainability_index": self.maintainability_index,
            "quality_score": self.quality_score,
            "quality_grade": self.quality_grade,
            # Overall
            "overall_health_score": self.overall_health_score,
            "overall_grade": self.overall_grade,
            "health_summary": self.health_summary,
            "recommendations": self.recommendations,
            "blockers": self.blockers,
            # Status
            "status": self.status,
            "current_phase": self.current_phase,
            "progress_percent": self.progress_percent,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Compact summary for list views"""
        return {
            "id": str(self.id) if self.id else None,
            "project_name": self.project_name,
            "primary_stack": self.primary_stack,
            "overall_health_score": self.overall_health_score,
            "overall_grade": self.overall_grade,
            "security_grade": self.security_grade,
            "quality_grade": self.quality_grade,
            "status": self.status,
            "assessment_date": self.assessment_date.isoformat() if self.assessment_date else None,
        }


class MigrationPlan(Base):
    """
    Workflow 2 Output: Migration planning (requires completed assessment)

    Contains results from:
    - Eliza FP estimation
    - Felix target architecture
    - Felix migration strategy
    - Diana migration report
    """
    __tablename__ = 'migration_plans'

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    assessment_id = Column(PGUUID(as_uuid=True), ForeignKey('project_assessments.id', ondelete='CASCADE'), nullable=False)

    # === NEW: Brown Paper Enhanced Integration (Week 128) ===
    brown_paper_session_id = Column(String(100))  # Link to BROWN_PAPER_ENHANCED session
    project_name = Column(String(200))  # Human-readable project name

    # Source codebase info
    source_path = Column(String(500))  # Legacy codebase location
    source_loc = Column(Integer)  # Lines of Code
    source_file_count = Column(Integer)  # Number of files

    # Foundation detection results (from FoundationDetectionService)
    foundation_modules = Column(JSONB, default=[])  # [{path, category, reference_count, confidence}]
    business_modules = Column(JSONB, default=[])  # [{path, domain, complexity}]
    foundation_summary = Column(JSONB, default={})  # {total, by_category: {database: 441, security: 91, ...}}

    # === NEW: Dual-Stack Support (Week 128) ===
    # Multiple target stacks for parallel migration evaluation
    target_stacks = Column(JSONB, default=[])  # [{id, name, technology, database, frontend, status, scores}]
    evaluation_mode = Column(String(20), default='single')  # single, dual, multi
    evaluation_criteria = Column(JSONB, default=[])  # [{name, weight, description}]
    stack_comparison = Column(JSONB, default={})  # Comparison results after evaluation

    # Target configuration (kept for backward compatibility - primary stack)
    target_technology = Column(String(50), nullable=False)  # python_fastapi, dotnet8, nodejs
    target_database = Column(String(50))  # postgresql, mysql, mongodb
    target_frontend = Column(String(50))  # react, vue, blazor

    # === Phase 7: FP Estimation (Eliza) ===
    # IFPUG components
    unadjusted_fp = Column(Integer)
    adjusted_fp = Column(Integer)
    vaf = Column(Numeric(4, 2))  # Value Adjustment Factor (0.65-1.35)

    # GSC (General System Characteristics)
    gsc_factors = Column(JSONB, default={})  # 14 factors with 0-5 scores

    # Effort breakdown
    total_hours = Column(Integer)
    total_days = Column(Integer)
    total_weeks = Column(Integer)

    # Phase breakdown
    phase_breakdown = Column(JSONB, default=[])  # [{phase, percentage, hours, days}]

    # Team sizing
    team_size_recommended = Column(Integer)
    team_composition = Column(JSONB, default={})  # {senior: 2, mid: 3, junior: 2}

    # === Phase 8: Target Architecture (Felix) ===
    target_architecture = Column(JSONB, default={})
    architecture_pattern = Column(String(50))  # clean_architecture, hexagonal, microservices
    architecture_layers = Column(JSONB, default=[])  # Target layers

    # Component mapping
    component_mapping = Column(JSONB, default=[])  # [{legacy, target, effort_hours}]
    api_contracts = Column(JSONB, default=[])  # [{endpoint, method, request, response}]
    data_migration_plan = Column(JSONB, default=[])  # [{source_table, target_table, transformations}]

    # Architecture Decision Records
    architecture_decisions = Column(JSONB, default=[])  # [{id, title, context, decision, consequences}]

    # === Phase 9: Migration Strategy (Felix) ===
    migration_strategy = Column(String(50))  # strangler_fig, big_bang, parallel_run, incremental, phased
    migration_phases = Column(JSONB, default=[])  # [{name, description, duration_weeks, dependencies, deliverables}]

    # Timeline
    timeline_weeks = Column(Integer)
    milestones = Column(JSONB, default=[])  # [{name, week, deliverables}]

    # Dependencies and prerequisites
    prerequisites = Column(JSONB, default=[])  # What must be in place before migration
    external_dependencies = Column(JSONB, default=[])  # External systems, APIs, etc.

    # === Risks and Blockers ===
    risks = Column(JSONB, default=[])  # [{title, probability, impact, mitigation}]
    blockers = Column(JSONB, default=[])  # From assessment + new blockers

    # === Recommendations ===
    recommendations = Column(JSONB, default=[])  # Felix recommendations
    success_criteria = Column(JSONB, default=[])  # Definition of done

    # === Diana Report ===
    report_type = Column(String(50), default='full_migration_plan')
    report_content = Column(Text)  # Markdown content
    report_metadata = Column(JSONB, default={})

    # === Workflow Status ===
    status = Column(String(20), default='draft')  # draft, in_review, approved, rejected
    current_phase = Column(String(50))  # estimation, architecture, strategy, report
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text)

    # Review
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)

    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    assessment = relationship("ProjectAssessment", back_populates="migration_plans")
    phases = relationship("AssessmentPhase", back_populates="migration_plan", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id else None,
            "assessment_id": str(self.assessment_id) if self.assessment_id else None,
            # Brown Paper Integration (NEW)
            "brown_paper_session_id": self.brown_paper_session_id,
            "project_name": self.project_name,
            # Source Info (NEW)
            "source_path": self.source_path,
            "source_loc": self.source_loc,
            "source_file_count": self.source_file_count,
            # Foundation Detection (NEW)
            "foundation_modules": self.foundation_modules,
            "business_modules": self.business_modules,
            "foundation_summary": self.foundation_summary,
            # Dual-Stack Support (NEW)
            "target_stacks": self.target_stacks,
            "evaluation_mode": self.evaluation_mode,
            "evaluation_criteria": self.evaluation_criteria,
            "stack_comparison": self.stack_comparison,
            # Target (backward compatible)
            "target_technology": self.target_technology,
            "target_database": self.target_database,
            "target_frontend": self.target_frontend,
            # FP Estimation
            "unadjusted_fp": self.unadjusted_fp,
            "adjusted_fp": self.adjusted_fp,
            "vaf": float(self.vaf) if self.vaf else None,
            "gsc_factors": self.gsc_factors,
            "total_hours": self.total_hours,
            "total_days": self.total_days,
            "total_weeks": self.total_weeks,
            "phase_breakdown": self.phase_breakdown,
            "team_size_recommended": self.team_size_recommended,
            "team_composition": self.team_composition,
            # Architecture
            "target_architecture": self.target_architecture,
            "architecture_pattern": self.architecture_pattern,
            "architecture_layers": self.architecture_layers,
            "component_mapping": self.component_mapping,
            "api_contracts": self.api_contracts,
            "data_migration_plan": self.data_migration_plan,
            "architecture_decisions": self.architecture_decisions,
            # Strategy
            "migration_strategy": self.migration_strategy,
            "migration_phases": self.migration_phases,
            "timeline_weeks": self.timeline_weeks,
            "milestones": self.milestones,
            "prerequisites": self.prerequisites,
            "external_dependencies": self.external_dependencies,
            # Risks
            "risks": self.risks,
            "blockers": self.blockers,
            "recommendations": self.recommendations,
            "success_criteria": self.success_criteria,
            # Report
            "report_type": self.report_type,
            "report_content": self.report_content,
            "report_metadata": self.report_metadata,
            # Status
            "status": self.status,
            "current_phase": self.current_phase,
            "progress_percent": self.progress_percent,
            "error_message": self.error_message,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_notes": self.review_notes,
            # Timestamps
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Compact summary for list views"""
        return {
            "id": str(self.id) if self.id else None,
            "assessment_id": str(self.assessment_id) if self.assessment_id else None,
            "target_technology": self.target_technology,
            "adjusted_fp": self.adjusted_fp,
            "total_weeks": self.total_weeks,
            "migration_strategy": self.migration_strategy,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_markdown(self) -> str:
        """
        Generate a complete migration plan document in Markdown format.
        This is the canonical output format for handoff between workflows.
        """
        from datetime import datetime

        lines = []

        # Header
        lines.append(f"# Migratieplan: {self.project_name or 'Unnamed Project'}")
        lines.append("")
        lines.append(f"**Versie:** 1.0 (Auto-generated)")
        lines.append(f"**Datum:** {datetime.now().strftime('%Y-%m-%d')}")
        lines.append(f"**Status:** {self.status or 'draft'}")
        if self.evaluation_mode == 'dual':
            lines.append(f"**Aanpak:** Dual-Stack Evaluatie")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Section 1: Overview
        lines.append("## 1. Projectoverzicht")
        lines.append("")
        lines.append(f"| Kenmerk | Waarde |")
        lines.append(f"|---------|--------|")
        lines.append(f"| **Projectnaam** | {self.project_name or 'N/A'} |")
        lines.append(f"| **Source Path** | `{self.source_path or 'N/A'}` |")
        lines.append(f"| **Lines of Code** | {self.source_loc or 0:,} |")
        lines.append(f"| **Aantal Bestanden** | {self.source_file_count or 0:,} |")
        if self.brown_paper_session_id:
            lines.append(f"| **Brown Paper Session** | `{self.brown_paper_session_id}` |")
        lines.append("")

        # Section 2: Target Stack(s)
        lines.append("## 2. Doelarchitectuur")
        lines.append("")

        if self.evaluation_mode == 'dual' and self.target_stacks:
            lines.append("### 2.1 Dual-Stack Evaluatie")
            lines.append("")
            lines.append("| Stack | Technologie | Database | Frontend | Status |")
            lines.append("|-------|-------------|----------|----------|--------|")
            for stack in self.target_stacks:
                lines.append(f"| **{stack.get('name', 'N/A')}** | {stack.get('technology', 'N/A')} | {stack.get('database', 'N/A')} | {stack.get('frontend', 'N/A')} | {stack.get('status', 'pending')} |")
            lines.append("")

            if self.evaluation_criteria:
                lines.append("### 2.2 Evaluatiecriteria")
                lines.append("")
                lines.append("| Criterium | Gewicht | Beschrijving |")
                lines.append("|-----------|---------|--------------|")
                for criterion in self.evaluation_criteria:
                    lines.append(f"| {criterion.get('name', 'N/A')} | {criterion.get('weight', 0)}% | {criterion.get('description', '')} |")
                lines.append("")
        else:
            lines.append(f"| Component | Keuze |")
            lines.append(f"|-----------|-------|")
            lines.append(f"| **Backend** | {self.target_technology or 'N/A'} |")
            lines.append(f"| **Database** | {self.target_database or 'N/A'} |")
            lines.append(f"| **Frontend** | {self.target_frontend or 'N/A'} |")
            if self.architecture_pattern:
                lines.append(f"| **Architectuur Patroon** | {self.architecture_pattern} |")
            lines.append("")

        # Section 3: Foundation Analysis
        if self.foundation_summary:
            lines.append("## 3. Foundation Analyse")
            lines.append("")
            summary = self.foundation_summary
            total_foundation = summary.get('total_foundation', 0)
            total_business = summary.get('total_business', 0)
            total = total_foundation + total_business
            if total > 0:
                foundation_pct = (total_foundation / total) * 100
                business_pct = (total_business / total) * 100
                lines.append(f"```")
                lines.append(f"FOUNDATION MODULES: {total_foundation:,} ({foundation_pct:.1f}%)")
                by_category = summary.get('by_category', {})
                for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
                    lines.append(f"├── {cat}: {count:,} modules")
                lines.append(f"")
                lines.append(f"BUSINESS MODULES: {total_business:,} ({business_pct:.1f}%)")
                lines.append(f"```")
                lines.append("")
                lines.append("**Migratie Implicatie:** Foundation modules moeten EERST gemigreerd worden.")
                lines.append("")

        # Section 4: Estimation
        if self.adjusted_fp or self.total_hours:
            lines.append("## 4. Schatting")
            lines.append("")
            lines.append("### 4.1 Function Points (IFPUG)")
            lines.append("")
            lines.append(f"| Metric | Waarde |")
            lines.append(f"|--------|--------|")
            if self.unadjusted_fp:
                lines.append(f"| Unadjusted FP | {self.unadjusted_fp:,} |")
            if self.adjusted_fp:
                lines.append(f"| Adjusted FP | {self.adjusted_fp:,} |")
            if self.vaf:
                lines.append(f"| VAF | {float(self.vaf):.2f} |")
            lines.append("")

            lines.append("### 4.2 Effort")
            lines.append("")
            lines.append(f"| Metric | Waarde |")
            lines.append(f"|--------|--------|")
            if self.total_hours:
                lines.append(f"| Totaal Uren | {self.total_hours:,} |")
            if self.total_days:
                lines.append(f"| Totaal Dagen | {self.total_days:,} |")
            if self.total_weeks:
                lines.append(f"| Totaal Weken | {self.total_weeks:,} |")
            if self.team_size_recommended:
                lines.append(f"| Team Grootte | {self.team_size_recommended} |")
            lines.append("")

            if self.phase_breakdown:
                lines.append("### 4.3 Fase Breakdown")
                lines.append("")
                lines.append("| Fase | Percentage | Uren | Dagen |")
                lines.append("|------|------------|------|-------|")
                for phase in self.phase_breakdown:
                    lines.append(f"| {phase.get('phase', 'N/A')} | {phase.get('percentage', 0)}% | {phase.get('hours', 0)} | {phase.get('days', 0)} |")
                lines.append("")

        # Section 5: Migration Strategy
        if self.migration_strategy:
            lines.append("## 5. Migratiestrategie")
            lines.append("")
            lines.append(f"**Strategie:** {self.migration_strategy}")
            lines.append("")

            if self.migration_phases:
                lines.append("### 5.1 Migratiefases")
                lines.append("")
                for i, phase in enumerate(self.migration_phases, 1):
                    lines.append(f"#### Fase {i}: {phase.get('name', 'N/A')}")
                    lines.append(f"- **Duur:** {phase.get('duration_weeks', 'N/A')} weken")
                    if phase.get('description'):
                        lines.append(f"- **Beschrijving:** {phase.get('description')}")
                    if phase.get('deliverables'):
                        lines.append(f"- **Deliverables:** {', '.join(phase.get('deliverables', []))}")
                    lines.append("")

            if self.milestones:
                lines.append("### 5.2 Milestones")
                lines.append("")
                lines.append("| Week | Milestone | Deliverables |")
                lines.append("|------|-----------|--------------|")
                for ms in self.milestones:
                    delivs = ', '.join(ms.get('deliverables', []))
                    lines.append(f"| {ms.get('week', 'N/A')} | {ms.get('name', 'N/A')} | {delivs} |")
                lines.append("")

        # Section 6: Component Mapping
        if self.component_mapping:
            lines.append("## 6. Component Mapping")
            lines.append("")
            lines.append("| Legacy | Target | Effort (uur) |")
            lines.append("|--------|--------|--------------|")
            for comp in self.component_mapping[:20]:  # Limit to 20 for readability
                lines.append(f"| {comp.get('legacy', 'N/A')} | {comp.get('target', 'N/A')} | {comp.get('effort_hours', 'N/A')} |")
            if len(self.component_mapping) > 20:
                lines.append(f"| ... | *{len(self.component_mapping) - 20} meer* | ... |")
            lines.append("")

        # Section 7: Risks
        if self.risks:
            lines.append("## 7. Risico's en Mitigatie")
            lines.append("")
            lines.append("| Risico | Kans | Impact | Mitigatie |")
            lines.append("|--------|------|--------|-----------|")
            for risk in self.risks:
                lines.append(f"| {risk.get('title', 'N/A')} | {risk.get('probability', 'N/A')} | {risk.get('impact', 'N/A')} | {risk.get('mitigation', 'N/A')} |")
            lines.append("")

        # Section 8: Recommendations
        if self.recommendations:
            lines.append("## 8. Aanbevelingen")
            lines.append("")
            for rec in self.recommendations:
                if isinstance(rec, dict):
                    lines.append(f"- **{rec.get('title', 'N/A')}**: {rec.get('description', '')}")
                else:
                    lines.append(f"- {rec}")
            lines.append("")

        # Section 9: Success Criteria
        if self.success_criteria:
            lines.append("## 9. Succescriteria")
            lines.append("")
            for criterion in self.success_criteria:
                if isinstance(criterion, dict):
                    lines.append(f"- [ ] {criterion.get('description', str(criterion))}")
                else:
                    lines.append(f"- [ ] {criterion}")
            lines.append("")

        # Section 10: Next Steps
        lines.append("## 10. Volgende Stappen")
        lines.append("")
        if self.status == 'draft':
            lines.append("1. [ ] Review en goedkeuring van dit migratieplan")
            lines.append("2. [ ] Start MIGRATION_ENHANCED workflow")
        elif self.status == 'approved':
            lines.append("1. [ ] Start MIGRATION_ENHANCED Phase 1: Preparation")
            lines.append("2. [ ] Environment setup voor target stack(s)")
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"**Auto-generated from MigrationPlan ID:** `{self.id}`")
        lines.append(f"**Gegenereerd:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        return "\n".join(lines)


class AssessmentPhase(Base):
    """
    Phase execution tracking for both workflows

    Tracks individual phase execution with timing and results.
    """
    __tablename__ = 'assessment_phases'

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    assessment_id = Column(PGUUID(as_uuid=True), ForeignKey('project_assessments.id', ondelete='CASCADE'), nullable=True)
    migration_plan_id = Column(PGUUID(as_uuid=True), ForeignKey('migration_plans.id', ondelete='CASCADE'), nullable=True)

    # Phase identification
    workflow = Column(String(20), nullable=False)  # assessment, migration, full
    phase_number = Column(Integer, nullable=False)  # 1-6 for assessment, 7-10 for migration
    phase_name = Column(String(50), nullable=False)  # registration, as_is, code, security, quality, report, estimation, architecture, strategy, final_report

    # Execution
    agent_name = Column(String(50))  # miguel, quinn, eliza, felix, diana
    status = Column(String(20), default='pending')  # pending, running, completed, failed, skipped

    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Results
    result_summary = Column(Text)  # Brief summary of phase results
    result_data = Column(JSONB, default={})  # Detailed results
    error_message = Column(Text)

    # Metrics
    items_processed = Column(Integer)  # Files, findings, etc.
    items_found = Column(Integer)  # Issues, patterns, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    assessment = relationship("ProjectAssessment", back_populates="phases")
    migration_plan = relationship("MigrationPlan", back_populates="phases")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id else None,
            "assessment_id": str(self.assessment_id) if self.assessment_id else None,
            "migration_plan_id": str(self.migration_plan_id) if self.migration_plan_id else None,
            "workflow": self.workflow,
            "phase_number": self.phase_number,
            "phase_name": self.phase_name,
            "agent_name": self.agent_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "result_summary": self.result_summary,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "items_processed": self.items_processed,
            "items_found": self.items_found,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
