"""
Legacy Quickscan Analyzers.

Fase 24 - A1: Individual analyzers for the 15-minute assessment.
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple

from .models import (
    QuickscanConfig,
    QuickscanResult,
    TechnologyStack,
    ComplexityScore,
    RiskAssessment,
    RiskLevel,
    SecurityRisk,
    EffortEstimate,
)

logger = logging.getLogger(__name__)


# =============================================================================
# LANGUAGE DETECTION
# =============================================================================

EXTENSION_TO_LANGUAGE = {
    # Web
    ".asp": "Classic ASP",
    ".asa": "Classic ASP",
    ".inc": "Classic ASP",
    ".php": "PHP",
    ".phtml": "PHP",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".less": "LESS",
    # .NET
    ".cs": "C#",
    ".vb": "VB.NET",
    ".aspx": "ASP.NET WebForms",
    ".ascx": "ASP.NET WebForms",
    ".asmx": "ASP.NET WebForms",
    ".cshtml": "ASP.NET MVC/Razor",
    ".vbhtml": "ASP.NET MVC/Razor",
    ".razor": "Blazor",
    # JVM
    ".java": "Java",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".groovy": "Groovy",
    ".jsp": "JSP",
    # Python
    ".py": "Python",
    ".pyw": "Python",
    # Ruby
    ".rb": "Ruby",
    ".erb": "Ruby",
    # Go
    ".go": "Go",
    # Rust
    ".rs": "Rust",
    # C/C++
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cc": "C++",
    # Legacy
    ".cbl": "COBOL",
    ".cob": "COBOL",
    ".cpy": "COBOL",
    ".rpg": "RPG",
    ".rpgle": "RPG",
    ".dpr": "Delphi",
    ".pas": "Delphi/Pascal",
    ".dfm": "Delphi",
    ".frm": "VB6",
    ".bas": "VB6",
    ".cls": "VB6",
    ".vbs": "VBScript",
    # Config
    ".xml": "XML",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".sql": "SQL",
}

FRAMEWORK_INDICATORS = {
    # .NET
    "System.Web.Mvc": ("ASP.NET MVC", "C#"),
    "Microsoft.AspNetCore": ("ASP.NET Core", "C#"),
    "Blazor": ("Blazor", "C#"),
    "System.Windows.Forms": ("Windows Forms", "C#"),
    "System.Web.UI": ("ASP.NET WebForms", "C#"),
    # Java
    "org.springframework": ("Spring", "Java"),
    "javax.servlet": ("Java Servlet", "Java"),
    "javax.faces": ("JSF", "Java"),
    "org.hibernate": ("Hibernate", "Java"),
    # JavaScript
    "react": ("React", "JavaScript"),
    "angular": ("Angular", "TypeScript"),
    "vue": ("Vue.js", "JavaScript"),
    "express": ("Express.js", "JavaScript"),
    "next": ("Next.js", "JavaScript"),
    "jquery": ("jQuery", "JavaScript"),
    # Python
    "django": ("Django", "Python"),
    "flask": ("Flask", "Python"),
    "fastapi": ("FastAPI", "Python"),
    # PHP
    "laravel": ("Laravel", "PHP"),
    "symfony": ("Symfony", "PHP"),
    "wordpress": ("WordPress", "PHP"),
    # Ruby
    "rails": ("Ruby on Rails", "Ruby"),
}

DATABASE_INDICATORS = {
    # Connection strings
    "sqlserver": "SQL Server",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "oracle": "Oracle",
    "mongodb": "MongoDB",
    "sqlite": "SQLite",
    "redis": "Redis",
    # ORM
    "entityframework": "SQL Server",
    "hibernate": "SQL Server/Oracle",
    "sequelize": "SQL Server/MySQL/PostgreSQL",
}

LEGACY_INDICATORS = {
    "Classic ASP": ["Response.Write", "Request.Form", "ADODB", "Server.CreateObject"],
    "VB6": ["Private Sub", "Public Function", "Dim As", "Set ="],
    "COBOL": ["IDENTIFICATION DIVISION", "PROCEDURE DIVISION", "WORKING-STORAGE"],
    "Delphi": ["TForm", "TButton", "procedure TForm", "uses"],
    "ASP.NET WebForms": ["runat=\"server\"", "ViewState", "Page_Load", "AutoPostBack"],
    "jQuery": ["$(document).ready", "$.ajax", "$('#"],
}


class BaseAnalyzer(ABC):
    """Base class for quickscan analyzers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Analyzer name."""
        pass

    @abstractmethod
    async def analyze(self, config: QuickscanConfig) -> QuickscanResult:
        """Execute analysis."""
        pass

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0


# =============================================================================
# TECHNOLOGY DETECTOR
# =============================================================================


class TechnologyDetector(BaseAnalyzer):
    """Detects technology stack from source code."""

    @property
    def name(self) -> str:
        return "technology_detector"

    async def analyze(self, config: QuickscanConfig) -> QuickscanResult:
        started = datetime.utcnow()
        errors = []

        try:
            # Scan files
            language_loc: Dict[str, int] = defaultdict(int)
            frameworks: Set[str] = set()
            databases: Set[str] = set()
            legacy_found: Set[str] = set()
            modern_found: Set[str] = set()

            files_scanned = 0
            sample_content = ""

            for file_path in config.project_path.rglob("*"):
                if not file_path.is_file():
                    continue

                # Skip excluded
                if any(excl in str(file_path) for excl in config.exclude_patterns):
                    continue

                ext = file_path.suffix.lower()
                if ext in EXTENSION_TO_LANGUAGE:
                    lang = EXTENSION_TO_LANGUAGE[ext]
                    loc = self._count_lines(file_path)
                    language_loc[lang] += loc
                    files_scanned += 1

                    # Sample content for framework detection
                    if files_scanned <= 100:
                        try:
                            content = file_path.read_text(encoding="utf-8", errors="replace")[:5000]
                            sample_content += content.lower()

                            # Check legacy indicators
                            for legacy_lang, indicators in LEGACY_INDICATORS.items():
                                for indicator in indicators:
                                    if indicator.lower() in content.lower():
                                        legacy_found.add(f"{legacy_lang}: {indicator}")
                                        break
                        except Exception:
                            pass

            # Detect frameworks
            for pattern, (framework, _) in FRAMEWORK_INDICATORS.items():
                if pattern.lower() in sample_content:
                    frameworks.add(framework)

            # Detect databases
            for pattern, db in DATABASE_INDICATORS.items():
                if pattern.lower() in sample_content:
                    databases.add(db)

            # Modern indicators
            if any(f in frameworks for f in ["React", "Angular", "Vue.js", "ASP.NET Core", "Blazor"]):
                modern_found.add("Modern frontend framework")
            if "TypeScript" in language_loc:
                modern_found.add("TypeScript usage")

            # Determine primary language
            primary_language = max(language_loc.items(), key=lambda x: x[1])[0] if language_loc else "Unknown"

            # Estimate age
            age_years = self._estimate_age(primary_language, legacy_found, modern_found)

            # Calculate confidence
            total_loc = sum(language_loc.values())
            confidence = min(1.0, total_loc / 10000) if total_loc > 0 else 0.0

            stack = TechnologyStack(
                primary_language=primary_language,
                languages=dict(language_loc),
                frameworks=list(frameworks),
                databases=list(databases),
                legacy_indicators=list(legacy_found)[:10],
                modern_indicators=list(modern_found),
                estimated_age_years=age_years,
                detection_confidence=round(confidence, 2),
            )

            duration = (datetime.utcnow() - started).total_seconds()
            return QuickscanResult(
                analyzer_name=self.name,
                success=True,
                duration_seconds=duration,
                data={"technology_stack": stack},
            )

        except Exception as e:
            logger.error(f"Technology detection failed: {e}")
            errors.append(str(e))
            duration = (datetime.utcnow() - started).total_seconds()
            return QuickscanResult(
                analyzer_name=self.name,
                success=False,
                duration_seconds=duration,
                errors=errors,
            )

    def _estimate_age(self, primary_lang: str, legacy: Set[str], modern: Set[str]) -> int:
        """Estimate codebase age in years."""
        if primary_lang in ["Classic ASP", "VB6", "COBOL"]:
            return 20
        if primary_lang in ["Delphi/Pascal", "ASP.NET WebForms"]:
            return 15
        if "jQuery" in str(legacy):
            return 10
        if modern:
            return 3
        return 8


# =============================================================================
# COMPLEXITY ANALYZER
# =============================================================================


class ComplexityAnalyzer(BaseAnalyzer):
    """Analyzes code complexity metrics."""

    @property
    def name(self) -> str:
        return "complexity_analyzer"

    async def analyze(self, config: QuickscanConfig) -> QuickscanResult:
        started = datetime.utcnow()
        errors = []

        try:
            total_loc = 0
            total_files = 0
            total_functions = 0
            total_classes = 0
            complexity_values: List[int] = []
            high_complexity_files: List[Tuple[str, int]] = []
            duplicated_lines = 0

            for file_path in config.project_path.rglob("*"):
                if not file_path.is_file():
                    continue

                if any(excl in str(file_path) for excl in config.exclude_patterns):
                    continue

                ext = file_path.suffix.lower()
                if ext not in EXTENSION_TO_LANGUAGE:
                    continue

                total_files += 1
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    lines = content.split("\n")
                    total_loc += len(lines)

                    # Count functions/classes (rough estimate)
                    funcs = len(re.findall(r'\b(?:function|def|sub|procedure|func)\b', content, re.I))
                    classes = len(re.findall(r'\b(?:class|interface|struct)\b', content, re.I))
                    total_functions += funcs
                    total_classes += classes

                    # Estimate cyclomatic complexity per file
                    cc = self._estimate_complexity(content)
                    complexity_values.append(cc)
                    if cc > 20:
                        high_complexity_files.append((str(file_path.relative_to(config.project_path)), cc))

                except Exception:
                    pass

            # Calculate metrics
            avg_complexity = sum(complexity_values) / len(complexity_values) if complexity_values else 0
            max_complexity = max(complexity_values) if complexity_values else 0

            # Maintainability index (simplified)
            mi = self._calculate_maintainability_index(avg_complexity, total_loc, total_files)

            # Technical debt (rough: 1 hour per 10 complexity points over threshold)
            debt_hours = sum(max(0, c - 10) / 10 for c in complexity_values)

            # Duplication (simplified estimate)
            dup_pct = self._estimate_duplication(total_loc, total_files)

            # Overall complexity score (0-100, higher = more complex)
            overall_score = min(100, (
                (avg_complexity / 30) * 30 +
                (1 - mi / 100) * 30 +
                (dup_pct / 50) * 20 +
                (max_complexity / 100) * 20
            ))

            # Sort high complexity files
            high_complexity_files.sort(key=lambda x: -x[1])

            score = ComplexityScore(
                overall_score=round(overall_score, 1),
                cyclomatic_complexity_avg=round(avg_complexity, 2),
                cyclomatic_complexity_max=max_complexity,
                lines_of_code=total_loc,
                files_count=total_files,
                functions_count=total_functions,
                classes_count=total_classes,
                maintainability_index=round(mi, 1),
                technical_debt_hours=round(debt_hours, 1),
                duplication_percentage=round(dup_pct, 1),
                high_complexity_files=[f[0] for f in high_complexity_files[:10]],
            )

            duration = (datetime.utcnow() - started).total_seconds()
            return QuickscanResult(
                analyzer_name=self.name,
                success=True,
                duration_seconds=duration,
                data={"complexity_score": score},
            )

        except Exception as e:
            logger.error(f"Complexity analysis failed: {e}")
            errors.append(str(e))
            duration = (datetime.utcnow() - started).total_seconds()
            return QuickscanResult(
                analyzer_name=self.name,
                success=False,
                duration_seconds=duration,
                errors=errors,
            )

    def _estimate_complexity(self, content: str) -> int:
        """Estimate cyclomatic complexity from content."""
        # Count decision points
        decisions = len(re.findall(
            r'\b(?:if|else|elif|elsif|case|when|for|foreach|while|do|catch|and|or|&&|\|\|)\b',
            content, re.I
        ))
        # Normalize by file size
        lines = len(content.split("\n"))
        if lines < 10:
            return 1
        return max(1, decisions)

    def _calculate_maintainability_index(self, avg_cc: float, loc: int, files: int) -> float:
        """Calculate maintainability index (0-100)."""
        if loc == 0 or files == 0:
            return 100.0
        avg_loc_per_file = loc / files
        # Simplified MI formula
        mi = 171 - 5.2 * (avg_loc_per_file / 100) - 0.23 * avg_cc - 16.2 * 0
        return max(0, min(100, mi))

    def _estimate_duplication(self, loc: int, files: int) -> float:
        """Estimate duplication percentage."""
        if files == 0:
            return 0.0
        # Rough estimate based on LOC per file
        avg_loc = loc / files
        if avg_loc > 500:
            return 15.0
        elif avg_loc > 200:
            return 10.0
        else:
            return 5.0


# =============================================================================
# SECURITY ANALYZER
# =============================================================================


class SecurityAnalyzer(BaseAnalyzer):
    """Analyzes security risks using existing security scanner."""

    @property
    def name(self) -> str:
        return "security_analyzer"

    async def analyze(self, config: QuickscanConfig) -> QuickscanResult:
        started = datetime.utcnow()
        errors = []

        try:
            # Import security scanner
            from app.services.security_scanner import create_security_orchestrator

            orchestrator = create_security_orchestrator()
            report = await orchestrator.scan_with_report(config.project_path)

            # Extract findings
            critical = report["summary"]["by_severity"].get("critical", 0)
            high = report["summary"]["by_severity"].get("high", 0)
            medium = report["summary"]["by_severity"].get("medium", 0)
            low = report["summary"]["by_severity"].get("low", 0)

            # Group by CWE
            cwe_counts: Dict[str, int] = defaultdict(int)
            cwe_titles: Dict[str, str] = {}
            cwe_severities: Dict[str, str] = {}

            for finding in report["findings"]:
                for cwe in finding.get("cwe_ids", []):
                    cwe_counts[cwe] += 1
                    cwe_titles[cwe] = finding["title"]
                    cwe_severities[cwe] = finding["severity"]

            security_risks = [
                SecurityRisk(
                    cwe_id=cwe,
                    title=cwe_titles.get(cwe, "Unknown"),
                    severity=cwe_severities.get(cwe, "medium"),
                    count=count,
                )
                for cwe, count in sorted(cwe_counts.items(), key=lambda x: -x[1])[:10]
            ]

            # Calculate risk score
            risk_score = min(100, (
                critical * 25 +
                high * 10 +
                medium * 3 +
                low * 1
            ))

            # Determine risk level
            if risk_score >= 75:
                risk_level = RiskLevel.CRITICAL
            elif risk_score >= 50:
                risk_level = RiskLevel.HIGH
            elif risk_score >= 25:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW

            assessment = RiskAssessment(
                overall_risk_score=round(risk_score, 1),
                risk_level=risk_level,
                critical_findings=critical,
                high_findings=high,
                medium_findings=medium,
                low_findings=low,
                security_risks=security_risks,
            )

            duration = (datetime.utcnow() - started).total_seconds()
            return QuickscanResult(
                analyzer_name=self.name,
                success=True,
                duration_seconds=duration,
                data={"risk_assessment": assessment},
            )

        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            errors.append(str(e))
            duration = (datetime.utcnow() - started).total_seconds()

            # Return minimal assessment on error
            return QuickscanResult(
                analyzer_name=self.name,
                success=False,
                duration_seconds=duration,
                data={"risk_assessment": RiskAssessment(overall_risk_score=50.0)},
                errors=errors,
            )


# =============================================================================
# EFFORT ESTIMATOR
# =============================================================================


class EffortEstimator(BaseAnalyzer):
    """Estimates modernization effort."""

    @property
    def name(self) -> str:
        return "effort_estimator"

    # Productivity factors (LOC per person-month)
    PRODUCTIVITY_BY_LANGUAGE = {
        "Classic ASP": 800,
        "VB6": 700,
        "COBOL": 600,
        "Delphi/Pascal": 900,
        "ASP.NET WebForms": 1000,
        "PHP": 1200,
        "Java": 1100,
        "C#": 1200,
        "JavaScript": 1500,
        "TypeScript": 1400,
        "Python": 1600,
        "Go": 1300,
    }

    async def analyze(self, config: QuickscanConfig) -> QuickscanResult:
        started = datetime.utcnow()
        errors = []

        try:
            # Get technology and complexity from previous results
            # For now, do a quick scan
            detector = TechnologyDetector()
            tech_result = await detector.analyze(config)
            tech_stack = tech_result.data.get("technology_stack")

            complexity_analyzer = ComplexityAnalyzer()
            complexity_result = await complexity_analyzer.analyze(config)
            complexity = complexity_result.data.get("complexity_score")

            if not tech_stack or not complexity:
                raise ValueError("Missing technology or complexity data")

            # Base estimate from LOC
            total_loc = complexity.lines_of_code
            primary_lang = tech_stack.primary_language
            productivity = self.PRODUCTIVITY_BY_LANGUAGE.get(primary_lang, 1000)

            # Base effort
            base_months = total_loc / productivity

            # Complexity multiplier
            complexity_multiplier = 1 + (complexity.overall_score / 100)

            # Legacy multiplier
            legacy_multiplier = 1.0
            if primary_lang in ["Classic ASP", "VB6", "COBOL"]:
                legacy_multiplier = 1.5
            elif primary_lang in ["Delphi/Pascal", "ASP.NET WebForms"]:
                legacy_multiplier = 1.3

            # Total effort
            total_months = base_months * complexity_multiplier * legacy_multiplier

            # Phase breakdown
            analysis_pct = 0.15
            dev_pct = 0.55
            test_pct = 0.20
            deploy_pct = 0.10

            estimate = EffortEstimate(
                total_person_months=round(total_months, 1),
                confidence=0.6,  # Rough estimate
                analysis_months=round(total_months * analysis_pct, 1),
                development_months=round(total_months * dev_pct, 1),
                testing_months=round(total_months * test_pct, 1),
                deployment_months=round(total_months * deploy_pct, 1),
                optimistic_months=round(total_months * 0.7, 1),
                pessimistic_months=round(total_months * 1.5, 1),
                assumptions=[
                    f"Based on {total_loc:,} LOC in {primary_lang}",
                    f"Productivity factor: {productivity} LOC/person-month",
                    f"Complexity multiplier: {complexity_multiplier:.2f}x",
                    "Assumes experienced team",
                    "Does not include infrastructure setup",
                ],
            )

            duration = (datetime.utcnow() - started).total_seconds()
            return QuickscanResult(
                analyzer_name=self.name,
                success=True,
                duration_seconds=duration,
                data={"effort_estimate": estimate},
            )

        except Exception as e:
            logger.error(f"Effort estimation failed: {e}")
            errors.append(str(e))
            duration = (datetime.utcnow() - started).total_seconds()
            return QuickscanResult(
                analyzer_name=self.name,
                success=False,
                duration_seconds=duration,
                errors=errors,
            )
