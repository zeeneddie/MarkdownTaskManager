"""
SWOTGeneratorService - Automated SWOT Matrix Generator

Week 77: Generates Strengths, Weaknesses, Opportunities, Threats
from analysis results for business, management, and technical stakeholders.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FindingCategory(Enum):
    """Categories for SWOT findings."""
    ARCHITECTURE = "architecture"
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    DATABASE = "database"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


class ImpactLevel(Enum):
    """Impact levels for findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SWOTItem:
    """Single SWOT item."""
    category: FindingCategory
    title: str
    description: str
    impact: ImpactLevel
    evidence: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "impact": self.impact.value,
            "evidence": self.evidence,
            "affected_components": self.affected_components,
            "metrics": self.metrics,
        }


@dataclass
class PrioritizedWeakness:
    """Weakness with prioritization info."""
    weakness: SWOTItem
    priority: int  # 1-5, 1 is highest
    effort_days: float
    risk_if_not_done: ImpactLevel
    dependencies: List[str] = field(default_factory=list)
    quick_win: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weakness": self.weakness.to_dict(),
            "priority": self.priority,
            "effort_days": self.effort_days,
            "risk_if_not_done": self.risk_if_not_done.value,
            "dependencies": self.dependencies,
            "quick_win": self.quick_win,
        }


@dataclass
class SWOTMatrix:
    """Complete SWOT analysis matrix."""
    strengths: List[SWOTItem] = field(default_factory=list)
    weaknesses: List[SWOTItem] = field(default_factory=list)
    opportunities: List[SWOTItem] = field(default_factory=list)
    threats: List[SWOTItem] = field(default_factory=list)

    # Categorized findings
    findings_by_category: Dict[str, Dict[str, List[SWOTItem]]] = field(default_factory=dict)

    # Prioritization
    prioritized_weaknesses: List[PrioritizedWeakness] = field(default_factory=list)
    quick_wins: List[PrioritizedWeakness] = field(default_factory=list)
    strategic_items: List[PrioritizedWeakness] = field(default_factory=list)

    # Scores
    overall_health_score: int = 0
    technical_debt_score: int = 0
    modernization_readiness: int = 0

    # Top recommendations
    top_recommendations: List[str] = field(default_factory=list)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matrix": {
                "strengths": [s.to_dict() for s in self.strengths],
                "weaknesses": [w.to_dict() for w in self.weaknesses],
                "opportunities": [o.to_dict() for o in self.opportunities],
                "threats": [t.to_dict() for t in self.threats],
            },
            "summary": {
                "strengths_count": len(self.strengths),
                "weaknesses_count": len(self.weaknesses),
                "opportunities_count": len(self.opportunities),
                "threats_count": len(self.threats),
            },
            "findings_by_category": {
                cat: {
                    "strengths": [s.to_dict() for s in findings.get("strengths", [])],
                    "weaknesses": [w.to_dict() for w in findings.get("weaknesses", [])],
                }
                for cat, findings in self.findings_by_category.items()
            },
            "prioritization": {
                "prioritized_weaknesses": [p.to_dict() for p in self.prioritized_weaknesses],
                "quick_wins": [q.to_dict() for q in self.quick_wins],
                "strategic_items": [s.to_dict() for s in self.strategic_items],
            },
            "scores": {
                "overall_health": self.overall_health_score,
                "technical_debt": self.technical_debt_score,
                "modernization_readiness": self.modernization_readiness,
            },
            "recommendations": {
                "top": self.top_recommendations,
                "risk_assessment": self.risk_assessment,
            },
        }


class SWOTGeneratorService:
    """
    Generate SWOT matrix from analysis results.
    Combines VBScript, StoredProcedure, and other analyses.
    """

    def __init__(self):
        self.matrix = SWOTMatrix()

    async def generate(
        self,
        vbscript_analysis: Optional[Dict[str, Any]] = None,
        sp_analysis: Optional[Dict[str, Any]] = None,
        code_analysis: Optional[Dict[str, Any]] = None,
        security_analysis: Optional[Dict[str, Any]] = None,
    ) -> SWOTMatrix:
        """
        Generate SWOT matrix from multiple analysis sources.

        Args:
            vbscript_analysis: VBScriptAnalyzerService results
            sp_analysis: StoredProcedureAnalyzerService results
            code_analysis: General code analysis results
            security_analysis: Security scan results

        Returns:
            Complete SWOTMatrix
        """
        self.matrix = SWOTMatrix()

        # Extract findings from each source
        if vbscript_analysis:
            self._process_vbscript_analysis(vbscript_analysis)

        if sp_analysis:
            self._process_sp_analysis(sp_analysis)

        if code_analysis:
            self._process_code_analysis(code_analysis)

        if security_analysis:
            self._process_security_analysis(security_analysis)

        # Identify opportunities
        self._identify_opportunities()

        # Identify threats
        self._identify_threats()

        # Organize by category
        self._organize_by_category()

        # Prioritize weaknesses
        await self.prioritize_weaknesses(self.matrix.weaknesses)

        # Calculate scores
        self._calculate_scores()

        # Generate recommendations
        self._generate_recommendations()

        return self.matrix

    def _process_vbscript_analysis(self, analysis: Dict[str, Any]) -> None:
        """Process VBScript analysis into SWOT items."""
        scores = analysis.get("scores", {})
        file_inventory = analysis.get("file_inventory", {})
        security_findings = analysis.get("security_findings", {})
        extraction_counts = analysis.get("extraction_counts", {})

        # Strengths from VBScript
        if scores.get("maintainability", 0) >= 70:
            self.matrix.strengths.append(SWOTItem(
                category=FindingCategory.MAINTAINABILITY,
                title="Good Code Organization",
                description="VBScript codebase shows good maintainability patterns",
                impact=ImpactLevel.MEDIUM,
                evidence=[f"Maintainability score: {scores.get('maintainability')}"],
                metrics={"maintainability_score": scores.get("maintainability")},
            ))

        if extraction_counts.get("functions", 0) > 0:
            func_count = extraction_counts.get("functions", 0) + extraction_counts.get("subs", 0)
            self.matrix.strengths.append(SWOTItem(
                category=FindingCategory.CODE_QUALITY,
                title="Modular Code Structure",
                description=f"Code is organized into {func_count} functions/subs",
                impact=ImpactLevel.MEDIUM,
                evidence=[f"{func_count} reusable code units found"],
                metrics={"function_count": func_count},
            ))

        # Weaknesses from VBScript
        sql_injection = security_findings.get("sql_injection", [])
        if sql_injection:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.SECURITY,
                title="SQL Injection Vulnerabilities",
                description=f"{len(sql_injection)} potential SQL injection points found",
                impact=ImpactLevel.CRITICAL,
                evidence=[f"Location: {item.get('file')}:{item.get('line')}" for item in sql_injection[:5]],
                affected_components=[item.get('file') for item in sql_injection[:10]],
                metrics={"sql_injection_count": len(sql_injection)},
            ))

        xss_risks = security_findings.get("xss", [])
        if xss_risks:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.SECURITY,
                title="XSS Vulnerabilities",
                description=f"{len(xss_risks)} potential XSS vulnerabilities found",
                impact=ImpactLevel.HIGH,
                evidence=[f"Location: {item.get('file')}:{item.get('line')}" for item in xss_risks[:5]],
                metrics={"xss_count": len(xss_risks)},
            ))

        error_handling = security_findings.get("error_handling", [])
        if error_handling:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.CODE_QUALITY,
                title="Insufficient Error Handling",
                description=f"{len(error_handling)} error handling issues found",
                impact=ImpactLevel.MEDIUM,
                evidence=["On Error Resume Next without proper error checking"],
                metrics={"error_handling_issues": len(error_handling)},
            ))

        # Legacy technology as weakness
        total_files = file_inventory.get("total_files", 0)
        if total_files > 0:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.ARCHITECTURE,
                title="Legacy Technology Stack",
                description="Classic ASP/VBScript is end-of-life technology",
                impact=ImpactLevel.HIGH,
                evidence=[
                    f"{file_inventory.get('asp_files', 0)} ASP files",
                    f"{file_inventory.get('vbs_files', 0)} VBS files",
                    f"{file_inventory.get('inc_files', 0)} include files",
                ],
                metrics=file_inventory,
            ))

    def _process_sp_analysis(self, analysis: Dict[str, Any]) -> None:
        """Process stored procedure analysis into SWOT items."""
        inventory = analysis.get("inventory", {})
        scores = analysis.get("scores", {})
        business_logic = analysis.get("business_logic", {})
        complexity = analysis.get("complexity", {})
        migration_indicators = analysis.get("migration_indicators", {})

        # Strengths from SP analysis
        business_rules = business_logic.get("business_rules", [])
        if business_rules:
            self.matrix.strengths.append(SWOTItem(
                category=FindingCategory.DATABASE,
                title="Business Logic in Database",
                description=f"{len(business_rules)} business rules captured in stored procedures",
                impact=ImpactLevel.HIGH,
                evidence=[f"Rule: {rule.get('description')}" for rule in business_rules[:3]],
                metrics={"business_rule_count": len(business_rules)},
            ))

        validation_logic = business_logic.get("validation_logic", [])
        if validation_logic:
            self.matrix.strengths.append(SWOTItem(
                category=FindingCategory.DATABASE,
                title="Data Validation at Database Level",
                description=f"{len(validation_logic)} validation rules in stored procedures",
                impact=ImpactLevel.MEDIUM,
                evidence=[f"Validation: {v.get('validation_type')} on {v.get('field_name')}" for v in validation_logic[:3]],
                metrics={"validation_count": len(validation_logic)},
            ))

        # Weaknesses from SP analysis
        distribution = complexity.get("distribution", {})
        critical_count = distribution.get("critical", 0)
        high_count = distribution.get("high", 0)

        if critical_count > 0 or high_count > 3:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.DATABASE,
                title="High Complexity Stored Procedures",
                description=f"{critical_count} critical and {high_count} high complexity SPs",
                impact=ImpactLevel.HIGH,
                evidence=[f"SP: {sp.get('name')} (complexity: {sp.get('complexity')})"
                         for sp in complexity.get("most_complex", [])[:5]],
                metrics={"critical_sps": critical_count, "high_sps": high_count},
            ))

        vendor_specific = migration_indicators.get("vendor_specific", [])
        if vendor_specific:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.DATABASE,
                title="Vendor-Specific SQL Features",
                description=f"{len(vendor_specific)} vendor-specific features requiring migration attention",
                impact=ImpactLevel.MEDIUM,
                evidence=[f"{f.get('feature')} in {f.get('sp_name')}" for f in vendor_specific[:5]],
                metrics={"vendor_specific_count": len(vendor_specific)},
            ))

        performance_concerns = migration_indicators.get("performance_concerns", [])
        if performance_concerns:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.PERFORMANCE,
                title="Database Performance Issues",
                description=f"{len(performance_concerns)} performance concerns identified",
                impact=ImpactLevel.MEDIUM,
                evidence=[f"{p.get('concern_type')} in {p.get('sp_name')}" for p in performance_concerns[:5]],
                metrics={"performance_issues": len(performance_concerns)},
            ))

        # Business logic coverage
        bl_coverage = scores.get("business_logic_coverage", 0)
        if bl_coverage > 50:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.ARCHITECTURE,
                title="Business Logic Tightly Coupled to Database",
                description=f"{bl_coverage}% of business logic is in stored procedures",
                impact=ImpactLevel.HIGH,
                evidence=["High coupling makes modernization difficult"],
                metrics={"business_logic_coverage": bl_coverage},
            ))

    def _process_code_analysis(self, analysis: Dict[str, Any]) -> None:
        """Process general code analysis into SWOT items."""
        # Test coverage
        test_coverage = analysis.get("test_coverage", 0)
        if test_coverage >= 70:
            self.matrix.strengths.append(SWOTItem(
                category=FindingCategory.TESTING,
                title="Good Test Coverage",
                description=f"Test coverage at {test_coverage}%",
                impact=ImpactLevel.HIGH,
                evidence=[f"Coverage: {test_coverage}%"],
                metrics={"test_coverage": test_coverage},
            ))
        elif test_coverage < 30:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.TESTING,
                title="Low Test Coverage",
                description=f"Test coverage only at {test_coverage}%",
                impact=ImpactLevel.HIGH,
                evidence=["Insufficient automated testing"],
                metrics={"test_coverage": test_coverage},
            ))

        # Documentation
        doc_coverage = analysis.get("documentation_coverage", 0)
        if doc_coverage < 30:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.DOCUMENTATION,
                title="Poor Documentation",
                description=f"Only {doc_coverage}% of code is documented",
                impact=ImpactLevel.MEDIUM,
                evidence=["Lack of inline comments and documentation"],
                metrics={"documentation_coverage": doc_coverage},
            ))

        # Dependencies
        outdated_deps = analysis.get("outdated_dependencies", [])
        if outdated_deps:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.MAINTAINABILITY,
                title="Outdated Dependencies",
                description=f"{len(outdated_deps)} outdated dependencies",
                impact=ImpactLevel.MEDIUM,
                evidence=[f"{d.get('name')}: {d.get('current')} → {d.get('latest')}" for d in outdated_deps[:5]],
                metrics={"outdated_count": len(outdated_deps)},
            ))

    def _process_security_analysis(self, analysis: Dict[str, Any]) -> None:
        """Process security scan results into SWOT items."""
        vulnerabilities = analysis.get("vulnerabilities", [])

        critical = [v for v in vulnerabilities if v.get("severity") == "critical"]
        high = [v for v in vulnerabilities if v.get("severity") == "high"]

        if critical:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.SECURITY,
                title="Critical Security Vulnerabilities",
                description=f"{len(critical)} critical security issues",
                impact=ImpactLevel.CRITICAL,
                evidence=[v.get("description", "")[:100] for v in critical[:3]],
                metrics={"critical_vulns": len(critical)},
            ))

        if high:
            self.matrix.weaknesses.append(SWOTItem(
                category=FindingCategory.SECURITY,
                title="High Severity Security Issues",
                description=f"{len(high)} high severity security issues",
                impact=ImpactLevel.HIGH,
                evidence=[v.get("description", "")[:100] for v in high[:3]],
                metrics={"high_vulns": len(high)},
            ))

        # Compliance
        compliance = analysis.get("compliance", {})
        if compliance.get("passed", False):
            self.matrix.strengths.append(SWOTItem(
                category=FindingCategory.SECURITY,
                title="Security Compliance Met",
                description=f"Passes {compliance.get('standard', 'security')} requirements",
                impact=ImpactLevel.HIGH,
                evidence=[f"Compliance: {compliance.get('standard')}"],
                metrics=compliance,
            ))

    def _identify_opportunities(self) -> None:
        """Identify opportunities based on weaknesses."""
        # Modernization opportunity
        legacy_found = any(w.title == "Legacy Technology Stack" for w in self.matrix.weaknesses)
        if legacy_found:
            self.matrix.opportunities.append(SWOTItem(
                category=FindingCategory.ARCHITECTURE,
                title="Modernization to Cloud-Native",
                description="Migrate to modern web framework with cloud deployment",
                impact=ImpactLevel.HIGH,
                evidence=["Legacy ASP can be migrated to .NET Core, Python, or Node.js"],
                metrics={"potential_cost_reduction": "30-50%"},
            ))

        # Security improvement opportunity
        security_issues = [w for w in self.matrix.weaknesses if w.category == FindingCategory.SECURITY]
        if security_issues:
            self.matrix.opportunities.append(SWOTItem(
                category=FindingCategory.SECURITY,
                title="Security Posture Improvement",
                description="Implement modern security practices",
                impact=ImpactLevel.HIGH,
                evidence=["Parameterized queries", "Input validation", "Output encoding"],
            ))

        # Performance optimization
        perf_issues = [w for w in self.matrix.weaknesses if w.category == FindingCategory.PERFORMANCE]
        if perf_issues:
            self.matrix.opportunities.append(SWOTItem(
                category=FindingCategory.PERFORMANCE,
                title="Performance Optimization",
                description="Optimize database queries and caching",
                impact=ImpactLevel.MEDIUM,
                evidence=["Query optimization", "Caching layer", "Index improvements"],
            ))

        # Automation opportunity
        low_test = any(w.title == "Low Test Coverage" for w in self.matrix.weaknesses)
        if low_test:
            self.matrix.opportunities.append(SWOTItem(
                category=FindingCategory.TESTING,
                title="Test Automation",
                description="Implement automated testing pipeline",
                impact=ImpactLevel.MEDIUM,
                evidence=["CI/CD integration", "Automated regression tests"],
            ))

    def _identify_threats(self) -> None:
        """Identify threats based on analysis."""
        # End-of-life technology threat
        legacy_found = any(w.title == "Legacy Technology Stack" for w in self.matrix.weaknesses)
        if legacy_found:
            self.matrix.threats.append(SWOTItem(
                category=FindingCategory.ARCHITECTURE,
                title="Technology Obsolescence Risk",
                description="Classic ASP no longer receives security updates",
                impact=ImpactLevel.CRITICAL,
                evidence=["No vendor support", "Diminishing talent pool", "Security exposure"],
            ))

        # Security breach threat
        security_issues = [w for w in self.matrix.weaknesses
                         if w.category == FindingCategory.SECURITY and w.impact == ImpactLevel.CRITICAL]
        if security_issues:
            self.matrix.threats.append(SWOTItem(
                category=FindingCategory.SECURITY,
                title="Data Breach Risk",
                description="Critical vulnerabilities increase breach probability",
                impact=ImpactLevel.CRITICAL,
                evidence=[f"{len(security_issues)} critical security issues"],
            ))

        # Business continuity threat
        bl_in_db = any("Business Logic" in w.title for w in self.matrix.weaknesses)
        if bl_in_db:
            self.matrix.threats.append(SWOTItem(
                category=FindingCategory.DATABASE,
                title="Vendor Lock-in Risk",
                description="Heavy database dependency limits flexibility",
                impact=ImpactLevel.HIGH,
                evidence=["Business logic in stored procedures"],
            ))

        # Maintainability threat
        high_complexity = any("High Complexity" in w.title for w in self.matrix.weaknesses)
        if high_complexity:
            self.matrix.threats.append(SWOTItem(
                category=FindingCategory.MAINTAINABILITY,
                title="Technical Debt Accumulation",
                description="Complex code increases future maintenance costs",
                impact=ImpactLevel.MEDIUM,
                evidence=["High cyclomatic complexity", "Difficult to modify safely"],
            ))

    def _organize_by_category(self) -> None:
        """Organize findings by category."""
        for category in FindingCategory:
            self.matrix.findings_by_category[category.value] = {
                "strengths": [s for s in self.matrix.strengths if s.category == category],
                "weaknesses": [w for w in self.matrix.weaknesses if w.category == category],
            }

    async def prioritize_weaknesses(self, weaknesses: List[SWOTItem]) -> List[PrioritizedWeakness]:
        """
        Prioritize weaknesses based on impact, effort, and risk.

        Args:
            weaknesses: List of weakness items

        Returns:
            Prioritized list of weaknesses
        """
        prioritized = []

        for weakness in weaknesses:
            # Calculate effort estimate
            effort = self._estimate_effort(weakness)

            # Calculate priority (1-5)
            priority = self._calculate_priority(weakness, effort)

            # Determine if it's a quick win
            quick_win = effort <= 5 and weakness.impact in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]

            pw = PrioritizedWeakness(
                weakness=weakness,
                priority=priority,
                effort_days=effort,
                risk_if_not_done=weakness.impact,
                quick_win=quick_win,
            )

            prioritized.append(pw)

        # Sort by priority
        prioritized.sort(key=lambda x: (x.priority, -x.effort_days))

        self.matrix.prioritized_weaknesses = prioritized
        self.matrix.quick_wins = [p for p in prioritized if p.quick_win]
        self.matrix.strategic_items = [p for p in prioritized if not p.quick_win and p.priority <= 2]

        return prioritized

    def _estimate_effort(self, weakness: SWOTItem) -> float:
        """Estimate effort in days to address weakness."""
        # Base effort by category
        category_effort = {
            FindingCategory.SECURITY: 5,
            FindingCategory.ARCHITECTURE: 20,
            FindingCategory.DATABASE: 10,
            FindingCategory.CODE_QUALITY: 3,
            FindingCategory.PERFORMANCE: 5,
            FindingCategory.MAINTAINABILITY: 8,
            FindingCategory.TESTING: 10,
            FindingCategory.DOCUMENTATION: 3,
        }

        base = category_effort.get(weakness.category, 5)

        # Adjust by impact
        impact_multiplier = {
            ImpactLevel.CRITICAL: 2.0,
            ImpactLevel.HIGH: 1.5,
            ImpactLevel.MEDIUM: 1.0,
            ImpactLevel.LOW: 0.5,
        }

        multiplier = impact_multiplier.get(weakness.impact, 1.0)

        # Adjust by scope
        affected = len(weakness.affected_components)
        scope_factor = 1 + (affected * 0.1) if affected > 0 else 1

        return round(base * multiplier * scope_factor, 1)

    def _calculate_priority(self, weakness: SWOTItem, effort: float) -> int:
        """Calculate priority (1-5) based on impact and effort."""
        # Impact score (higher is worse)
        impact_score = {
            ImpactLevel.CRITICAL: 4,
            ImpactLevel.HIGH: 3,
            ImpactLevel.MEDIUM: 2,
            ImpactLevel.LOW: 1,
        }.get(weakness.impact, 2)

        # ROI = impact / effort (higher is better priority)
        roi = impact_score / (effort / 5)  # Normalize effort

        if roi >= 3:
            return 1  # Highest priority
        elif roi >= 2:
            return 2
        elif roi >= 1:
            return 3
        elif roi >= 0.5:
            return 4
        else:
            return 5  # Lowest priority

    def _calculate_scores(self) -> None:
        """Calculate overall scores."""
        # Health score (0-100, higher is better)
        health = 100

        for weakness in self.matrix.weaknesses:
            if weakness.impact == ImpactLevel.CRITICAL:
                health -= 15
            elif weakness.impact == ImpactLevel.HIGH:
                health -= 10
            elif weakness.impact == ImpactLevel.MEDIUM:
                health -= 5
            else:
                health -= 2

        for strength in self.matrix.strengths:
            if strength.impact == ImpactLevel.HIGH:
                health += 5
            elif strength.impact == ImpactLevel.MEDIUM:
                health += 3

        self.matrix.overall_health_score = max(0, min(100, health))

        # Technical debt score (0-100, higher is more debt)
        debt = 0
        debt_categories = [FindingCategory.CODE_QUALITY, FindingCategory.MAINTAINABILITY,
                         FindingCategory.TESTING, FindingCategory.DOCUMENTATION]

        for weakness in self.matrix.weaknesses:
            if weakness.category in debt_categories:
                if weakness.impact == ImpactLevel.CRITICAL:
                    debt += 20
                elif weakness.impact == ImpactLevel.HIGH:
                    debt += 15
                elif weakness.impact == ImpactLevel.MEDIUM:
                    debt += 10
                else:
                    debt += 5

        self.matrix.technical_debt_score = min(100, debt)

        # Modernization readiness (0-100, higher is more ready)
        readiness = 50  # Start at middle

        # Positive factors
        readiness += len(self.matrix.strengths) * 5

        # Negative factors
        critical_weaknesses = [w for w in self.matrix.weaknesses if w.impact == ImpactLevel.CRITICAL]
        readiness -= len(critical_weaknesses) * 10

        architecture_issues = [w for w in self.matrix.weaknesses if w.category == FindingCategory.ARCHITECTURE]
        readiness -= len(architecture_issues) * 8

        self.matrix.modernization_readiness = max(0, min(100, readiness))

    def _generate_recommendations(self) -> None:
        """Generate top recommendations."""
        recommendations = []

        # Based on quick wins
        for qw in self.matrix.quick_wins[:3]:
            recommendations.append(
                f"QUICK WIN: {qw.weakness.title} - {qw.effort_days} days, {qw.weakness.impact.value} impact"
            )

        # Based on critical threats
        critical_threats = [t for t in self.matrix.threats if t.impact == ImpactLevel.CRITICAL]
        for threat in critical_threats[:2]:
            recommendations.append(f"ADDRESS THREAT: {threat.title} - {threat.description}")

        # Based on opportunities
        for opp in self.matrix.opportunities[:2]:
            recommendations.append(f"OPPORTUNITY: {opp.title} - {opp.description}")

        self.matrix.top_recommendations = recommendations[:5]

        # Risk assessment
        critical_count = len([w for w in self.matrix.weaknesses if w.impact == ImpactLevel.CRITICAL])
        high_count = len([w for w in self.matrix.weaknesses if w.impact == ImpactLevel.HIGH])

        if critical_count >= 3 or (critical_count >= 1 and high_count >= 5):
            risk_level = "critical"
        elif critical_count >= 1 or high_count >= 3:
            risk_level = "high"
        elif high_count >= 1:
            risk_level = "medium"
        else:
            risk_level = "low"

        self.matrix.risk_assessment = {
            "level": risk_level,
            "critical_issues": critical_count,
            "high_issues": high_count,
            "factors": [
                f"{critical_count} critical vulnerabilities",
                f"{high_count} high priority issues",
                f"{len(self.matrix.threats)} identified threats",
            ],
        }
