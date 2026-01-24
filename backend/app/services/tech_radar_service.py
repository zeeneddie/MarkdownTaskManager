"""
Technology Radar Service - A3 (Fase 24)

Tracks technology End-of-Life (EOL) dates and provides risk assessment.

Features:
- EOL database for common technologies
- Deprecated technology detection
- Version comparison (current vs latest)
- Risk assessment based on EOL proximity
- Technology recommendations
- Integration with stack detection

Version: 1.0.0
Week: 129 (Fase 24)
"""

import re
import logging
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set

logger = logging.getLogger(__name__)


class TechnologyCategory(str, Enum):
    """Categories of technologies tracked."""
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    RUNTIME = "runtime"
    OS = "operating_system"
    LIBRARY = "library"
    TOOL = "tool"
    CLOUD = "cloud"


class EOLStatus(str, Enum):
    """End-of-Life status."""
    ACTIVE = "active"               # Fully supported
    MAINTENANCE = "maintenance"      # Security fixes only
    EXTENDED = "extended"            # Extended support (often paid)
    EOL = "eol"                      # End of life, no support
    DEPRECATED = "deprecated"        # Still works but will be removed
    UNKNOWN = "unknown"              # Status not known


class RiskLevel(str, Enum):
    """Risk level based on EOL status."""
    CRITICAL = "critical"   # Already EOL or deprecated
    HIGH = "high"           # EOL within 6 months
    MEDIUM = "medium"       # EOL within 12 months
    LOW = "low"             # EOL within 24 months
    SAFE = "safe"           # Fully supported, EOL > 24 months
    UNKNOWN = "unknown"     # Version not in EOL database


@dataclass
class EOLInfo:
    """
    End-of-Life information for a technology version.

    Attributes:
        technology: Name of the technology
        version: Version string
        category: Technology category
        release_date: When this version was released
        eol_date: End of life date
        status: Current support status
        lts: Whether this is a Long Term Support version
        latest_version: Latest available version
        successor: Recommended successor version/technology
        notes: Additional notes
    """
    technology: str
    version: str
    category: TechnologyCategory
    release_date: Optional[date] = None
    eol_date: Optional[date] = None
    status: EOLStatus = EOLStatus.UNKNOWN
    lts: bool = False
    latest_version: Optional[str] = None
    successor: Optional[str] = None
    notes: Optional[str] = None

    def get_risk_level(self) -> RiskLevel:
        """Calculate risk level based on EOL date."""
        if self.status == EOLStatus.EOL:
            return RiskLevel.CRITICAL
        if self.status == EOLStatus.DEPRECATED:
            return RiskLevel.CRITICAL

        if not self.eol_date:
            return RiskLevel.SAFE

        today = date.today()
        days_until_eol = (self.eol_date - today).days

        if days_until_eol < 0:
            return RiskLevel.CRITICAL
        if days_until_eol < 180:  # 6 months
            return RiskLevel.HIGH
        if days_until_eol < 365:  # 12 months
            return RiskLevel.MEDIUM
        if days_until_eol < 730:  # 24 months
            return RiskLevel.LOW
        return RiskLevel.SAFE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "technology": self.technology,
            "version": self.version,
            "category": self.category.value,
            "release_date": self.release_date.isoformat() if self.release_date else None,
            "eol_date": self.eol_date.isoformat() if self.eol_date else None,
            "status": self.status.value,
            "lts": self.lts,
            "latest_version": self.latest_version,
            "successor": self.successor,
            "notes": self.notes,
            "risk_level": self.get_risk_level().value,
        }


@dataclass
class TechnologyAssessment:
    """
    Assessment of a technology in a codebase.

    Attributes:
        technology: Name of the technology
        detected_version: Version detected in codebase
        eol_info: EOL information if found
        risk_level: Overall risk level
        recommendation: Upgrade recommendation
        detection_sources: Where this was detected
    """
    technology: str
    detected_version: Optional[str] = None
    eol_info: Optional[EOLInfo] = None
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    recommendation: str = ""
    detection_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "technology": self.technology,
            "detected_version": self.detected_version,
            "eol_info": self.eol_info.to_dict() if self.eol_info else None,
            "risk_level": self.risk_level.value,
            "recommendation": self.recommendation,
            "detection_sources": self.detection_sources,
        }


@dataclass
class TechRadarResult:
    """
    Result of technology radar scan.

    Attributes:
        assessments: List of technology assessments
        risk_summary: Count per risk level
        critical_items: Technologies requiring immediate attention
        recommended_upgrades: Recommended version upgrades
        scan_date: When scan was performed
    """
    assessments: List[TechnologyAssessment] = field(default_factory=list)
    risk_summary: Dict[str, int] = field(default_factory=dict)
    critical_items: List[str] = field(default_factory=list)
    recommended_upgrades: List[Dict[str, str]] = field(default_factory=list)
    scan_date: datetime = field(default_factory=lambda: datetime.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "assessments": [a.to_dict() for a in self.assessments],
            "risk_summary": self.risk_summary,
            "critical_items": self.critical_items,
            "recommended_upgrades": self.recommended_upgrades,
            "scan_date": self.scan_date.isoformat(),
        }


class TechRadarService:
    """
    Service for tracking technology EOL and providing risk assessment.

    Usage:
        service = TechRadarService()

        # Get EOL info for a specific technology
        info = service.get_eol_info("python", "3.8")

        # Scan files for technology versions
        result = service.scan_files({"requirements.txt": "...", "package.json": "..."})

        # Generate radar report
        report = service.generate_radar_report(result)
    """

    # EOL database - based on https://endoflife.date
    # Updated: January 2026
    EOL_DATABASE: Dict[str, Dict[str, Dict[str, Any]]] = {
        # Languages
        "python": {
            "category": TechnologyCategory.LANGUAGE,
            "latest": "3.13",
            "versions": {
                "3.13": {"release": "2024-10-01", "eol": "2029-10-01", "status": EOLStatus.ACTIVE},
                "3.12": {"release": "2023-10-02", "eol": "2028-10-02", "status": EOLStatus.ACTIVE, "lts": True},
                "3.11": {"release": "2022-10-24", "eol": "2027-10-24", "status": EOLStatus.ACTIVE},
                "3.10": {"release": "2021-10-04", "eol": "2026-10-04", "status": EOLStatus.MAINTENANCE},
                "3.9": {"release": "2020-10-05", "eol": "2025-10-05", "status": EOLStatus.MAINTENANCE},
                "3.8": {"release": "2019-10-14", "eol": "2024-10-14", "status": EOLStatus.EOL},
                "3.7": {"release": "2018-06-27", "eol": "2023-06-27", "status": EOLStatus.EOL},
                "2.7": {"release": "2010-07-03", "eol": "2020-01-01", "status": EOLStatus.EOL},
            }
        },
        "node": {
            "category": TechnologyCategory.RUNTIME,
            "latest": "22",
            "versions": {
                "22": {"release": "2024-04-24", "eol": "2027-04-30", "status": EOLStatus.ACTIVE, "lts": True},
                "21": {"release": "2023-10-17", "eol": "2024-06-01", "status": EOLStatus.EOL},
                "20": {"release": "2023-04-18", "eol": "2026-04-30", "status": EOLStatus.ACTIVE, "lts": True},
                "18": {"release": "2022-04-19", "eol": "2025-04-30", "status": EOLStatus.MAINTENANCE, "lts": True},
                "16": {"release": "2021-04-20", "eol": "2024-09-11", "status": EOLStatus.EOL},
                "14": {"release": "2020-04-21", "eol": "2023-04-30", "status": EOLStatus.EOL},
            }
        },
        "java": {
            "category": TechnologyCategory.LANGUAGE,
            "latest": "21",
            "versions": {
                "21": {"release": "2023-09-19", "eol": "2031-09-01", "status": EOLStatus.ACTIVE, "lts": True},
                "17": {"release": "2021-09-14", "eol": "2029-09-01", "status": EOLStatus.ACTIVE, "lts": True},
                "11": {"release": "2018-09-25", "eol": "2026-09-01", "status": EOLStatus.EXTENDED, "lts": True},
                "8": {"release": "2014-03-18", "eol": "2025-03-01", "status": EOLStatus.EXTENDED, "lts": True},
            }
        },
        "dotnet": {
            "category": TechnologyCategory.FRAMEWORK,
            "latest": "9.0",
            "versions": {
                "9.0": {"release": "2024-11-12", "eol": "2026-05-12", "status": EOLStatus.ACTIVE},
                "8.0": {"release": "2023-11-14", "eol": "2026-11-10", "status": EOLStatus.ACTIVE, "lts": True},
                "7.0": {"release": "2022-11-08", "eol": "2024-05-14", "status": EOLStatus.EOL},
                "6.0": {"release": "2021-11-08", "eol": "2024-11-12", "status": EOLStatus.EOL, "lts": True},
            }
        },
        "angular": {
            "category": TechnologyCategory.FRAMEWORK,
            "latest": "19",
            "versions": {
                "19": {"release": "2024-11-19", "eol": "2026-05-19", "status": EOLStatus.ACTIVE},
                "18": {"release": "2024-05-22", "eol": "2025-11-22", "status": EOLStatus.ACTIVE, "lts": True},
                "17": {"release": "2023-11-08", "eol": "2025-05-15", "status": EOLStatus.MAINTENANCE},
                "16": {"release": "2023-05-03", "eol": "2024-11-08", "status": EOLStatus.EOL},
            }
        },
        "react": {
            "category": TechnologyCategory.FRAMEWORK,
            "latest": "19",
            "versions": {
                "19": {"release": "2024-12-05", "eol": None, "status": EOLStatus.ACTIVE},
                "18": {"release": "2022-03-29", "eol": None, "status": EOLStatus.MAINTENANCE},
                "17": {"release": "2020-10-20", "eol": "2025-12-31", "status": EOLStatus.MAINTENANCE},
                "16": {"release": "2017-09-26", "eol": "2024-12-31", "status": EOLStatus.EOL},
            }
        },
        "vue": {
            "category": TechnologyCategory.FRAMEWORK,
            "latest": "3.5",
            "versions": {
                "3.5": {"release": "2024-09-01", "eol": None, "status": EOLStatus.ACTIVE},
                "3.4": {"release": "2023-12-28", "eol": None, "status": EOLStatus.MAINTENANCE},
                "2": {"release": "2016-10-01", "eol": "2023-12-31", "status": EOLStatus.EOL},
            }
        },
        "django": {
            "category": TechnologyCategory.FRAMEWORK,
            "latest": "5.1",
            "versions": {
                "5.1": {"release": "2024-08-07", "eol": "2025-12-01", "status": EOLStatus.ACTIVE},
                "5.0": {"release": "2023-12-04", "eol": "2025-04-01", "status": EOLStatus.MAINTENANCE},
                "4.2": {"release": "2023-04-03", "eol": "2026-04-01", "status": EOLStatus.ACTIVE, "lts": True},
                "3.2": {"release": "2021-04-06", "eol": "2024-04-01", "status": EOLStatus.EOL, "lts": True},
            }
        },
        "spring-boot": {
            "category": TechnologyCategory.FRAMEWORK,
            "latest": "3.3",
            "versions": {
                "3.3": {"release": "2024-05-23", "eol": "2025-11-23", "status": EOLStatus.ACTIVE},
                "3.2": {"release": "2023-11-23", "eol": "2025-05-23", "status": EOLStatus.MAINTENANCE},
                "2.7": {"release": "2022-05-19", "eol": "2025-08-24", "status": EOLStatus.EXTENDED},
            }
        },
        "postgresql": {
            "category": TechnologyCategory.DATABASE,
            "latest": "17",
            "versions": {
                "17": {"release": "2024-09-26", "eol": "2029-11-14", "status": EOLStatus.ACTIVE},
                "16": {"release": "2023-09-14", "eol": "2028-11-09", "status": EOLStatus.ACTIVE},
                "15": {"release": "2022-10-13", "eol": "2027-11-11", "status": EOLStatus.ACTIVE},
                "14": {"release": "2021-09-30", "eol": "2026-11-12", "status": EOLStatus.ACTIVE},
                "13": {"release": "2020-09-24", "eol": "2025-11-13", "status": EOLStatus.MAINTENANCE},
                "12": {"release": "2019-10-03", "eol": "2024-11-14", "status": EOLStatus.EOL},
            }
        },
        "mysql": {
            "category": TechnologyCategory.DATABASE,
            "latest": "8.4",
            "versions": {
                "8.4": {"release": "2024-04-30", "eol": "2032-04-30", "status": EOLStatus.ACTIVE, "lts": True},
                "8.0": {"release": "2018-04-19", "eol": "2026-04-30", "status": EOLStatus.MAINTENANCE, "lts": True},
                "5.7": {"release": "2015-10-21", "eol": "2023-10-31", "status": EOLStatus.EOL},
            }
        },
        "mongodb": {
            "category": TechnologyCategory.DATABASE,
            "latest": "8.0",
            "versions": {
                "8.0": {"release": "2024-08-19", "eol": None, "status": EOLStatus.ACTIVE},
                "7.0": {"release": "2023-08-15", "eol": None, "status": EOLStatus.ACTIVE},
                "6.0": {"release": "2022-07-19", "eol": None, "status": EOLStatus.MAINTENANCE},
                "5.0": {"release": "2021-07-13", "eol": "2024-10-31", "status": EOLStatus.EOL},
            }
        },
        "redis": {
            "category": TechnologyCategory.DATABASE,
            "latest": "7.4",
            "versions": {
                "7.4": {"release": "2024-07-31", "eol": None, "status": EOLStatus.ACTIVE},
                "7.2": {"release": "2023-08-15", "eol": None, "status": EOLStatus.ACTIVE},
                "7.0": {"release": "2022-04-27", "eol": None, "status": EOLStatus.MAINTENANCE},
                "6.2": {"release": "2021-02-22", "eol": "2024-02-28", "status": EOLStatus.EOL},
            }
        },
        "ubuntu": {
            "category": TechnologyCategory.OS,
            "latest": "24.04",
            "versions": {
                "24.04": {"release": "2024-04-25", "eol": "2029-04-25", "status": EOLStatus.ACTIVE, "lts": True},
                "22.04": {"release": "2022-04-21", "eol": "2027-04-21", "status": EOLStatus.ACTIVE, "lts": True},
                "20.04": {"release": "2020-04-23", "eol": "2025-04-23", "status": EOLStatus.MAINTENANCE, "lts": True},
                "18.04": {"release": "2018-04-26", "eol": "2023-04-26", "status": EOLStatus.EOL, "lts": True},
            }
        },
        "windows-server": {
            "category": TechnologyCategory.OS,
            "latest": "2025",
            "versions": {
                "2025": {"release": "2024-11-01", "eol": "2034-10-10", "status": EOLStatus.ACTIVE},
                "2022": {"release": "2021-08-18", "eol": "2031-10-14", "status": EOLStatus.ACTIVE},
                "2019": {"release": "2018-11-13", "eol": "2029-01-09", "status": EOLStatus.ACTIVE},
                "2016": {"release": "2016-10-12", "eol": "2027-01-11", "status": EOLStatus.EXTENDED},
                "2012R2": {"release": "2013-10-18", "eol": "2023-10-10", "status": EOLStatus.EOL},
            }
        },
    }

    # Version detection patterns
    VERSION_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
        "requirements.txt": [
            (r'^python\s*[<>=~!]*\s*([\d.]+)', "python"),
            (r'^django\s*[<>=~!]*\s*([\d.]+)', "django"),
            (r'^flask\s*[<>=~!]*\s*([\d.]+)', "flask"),
            (r'^numpy\s*[<>=~!]*\s*([\d.]+)', "numpy"),
            (r'^pandas\s*[<>=~!]*\s*([\d.]+)', "pandas"),
        ],
        "package.json": [
            (r'"node"\s*:\s*["\']?[<>=~^]*\s*([\d.]+)', "node"),
            (r'"react"\s*:\s*["\']?[<>=~^]*\s*([\d.]+)', "react"),
            (r'"vue"\s*:\s*["\']?[<>=~^]*\s*([\d.]+)', "vue"),
            (r'"@angular/core"\s*:\s*["\']?[<>=~^]*\s*([\d.]+)', "angular"),
            (r'"next"\s*:\s*["\']?[<>=~^]*\s*([\d.]+)', "next"),
        ],
        "pom.xml": [
            (r'<java\.version>\s*([\d.]+)', "java"),
            (r'<spring-boot\.version>\s*([\d.]+)', "spring-boot"),
            (r'<spring\.version>\s*([\d.]+)', "spring"),
        ],
        "build.gradle": [
            (r'sourceCompatibility\s*=\s*["\']?([\d.]+)', "java"),
            (r"springBootVersion\s*=\s*['\"]?([\d.]+)", "spring-boot"),
        ],
        ".csproj": [
            (r'<TargetFramework>net([\d.]+)', "dotnet"),
            (r'<LangVersion>\s*([\d.]+)', "csharp"),
        ],
        "Dockerfile": [
            (r'FROM\s+python:([\d.]+)', "python"),
            (r'FROM\s+node:([\d.]+)', "node"),
            (r'FROM\s+openjdk:([\d.]+)', "java"),
            (r'FROM\s+ubuntu:([\d.]+)', "ubuntu"),
            (r'FROM\s+postgres:([\d.]+)', "postgresql"),
            (r'FROM\s+mysql:([\d.]+)', "mysql"),
            (r'FROM\s+mongo:([\d.]+)', "mongodb"),
            (r'FROM\s+redis:([\d.]+)', "redis"),
        ],
        ".nvmrc": [
            (r'^v?([\d.]+)', "node"),
        ],
        ".python-version": [
            (r'^([\d.]+)', "python"),
        ],
    }

    def __init__(self):
        self._compiled_patterns: Dict[str, List[Tuple[re.Pattern, str]]] = {}
        self._compile_patterns()
        logger.info("TechRadarService initialized")

    def _compile_patterns(self) -> None:
        """Compile version detection patterns."""
        for file_type, patterns in self.VERSION_PATTERNS.items():
            self._compiled_patterns[file_type] = [
                (re.compile(p, re.IGNORECASE | re.MULTILINE), tech)
                for p, tech in patterns
            ]

    def get_eol_info(
        self,
        technology: str,
        version: str
    ) -> Optional[EOLInfo]:
        """
        Get EOL information for a specific technology version.

        Args:
            technology: Technology name (e.g., "python", "node")
            version: Version string (e.g., "3.8", "18")

        Returns:
            EOLInfo if found, None otherwise
        """
        tech_lower = technology.lower()
        if tech_lower not in self.EOL_DATABASE:
            return None

        tech_data = self.EOL_DATABASE[tech_lower]

        # Normalize version (remove 'v' prefix, take major.minor)
        version_clean = version.lstrip('v').split('-')[0]
        major_minor = '.'.join(version_clean.split('.')[:2])

        # Try exact match first, then major.minor
        version_data = tech_data["versions"].get(version_clean)
        if not version_data:
            version_data = tech_data["versions"].get(major_minor)
        if not version_data:
            # Try major version only
            major = version_clean.split('.')[0]
            version_data = tech_data["versions"].get(major)

        if not version_data:
            return None

        return EOLInfo(
            technology=technology,
            version=version,
            category=tech_data["category"],
            release_date=date.fromisoformat(version_data["release"]) if version_data.get("release") else None,
            eol_date=date.fromisoformat(version_data["eol"]) if version_data.get("eol") else None,
            status=version_data.get("status", EOLStatus.UNKNOWN),
            lts=version_data.get("lts", False),
            latest_version=tech_data.get("latest"),
        )

    def _detect_file_type(self, filepath: str) -> Optional[str]:
        """Detect file type from path."""
        filename = filepath.rsplit("/", 1)[-1].lower()

        if filename == "requirements.txt" or filename.endswith("requirements.txt"):
            return "requirements.txt"
        if filename == "package.json":
            return "package.json"
        if filename == "pom.xml":
            return "pom.xml"
        if filename == "build.gradle" or filename.endswith(".gradle"):
            return "build.gradle"
        if filename.endswith(".csproj"):
            return ".csproj"
        if filename == "dockerfile" or filename.startswith("dockerfile"):
            return "Dockerfile"
        if filename == ".nvmrc":
            return ".nvmrc"
        if filename == ".python-version":
            return ".python-version"

        return None

    def _extract_versions(
        self,
        content: str,
        file_type: str
    ) -> List[Tuple[str, str]]:
        """Extract technology versions from file content."""
        versions = []
        patterns = self._compiled_patterns.get(file_type, [])

        for pattern, tech in patterns:
            for match in pattern.finditer(content):
                version = match.group(1)
                versions.append((tech, version))

        return versions

    def scan_files(
        self,
        files: Dict[str, str]
    ) -> TechRadarResult:
        """
        Scan files for technology versions and assess risks.

        Args:
            files: Dict of filepath -> content

        Returns:
            TechRadarResult with assessments
        """
        result = TechRadarResult()
        tech_findings: Dict[str, List[Tuple[str, str]]] = {}  # tech -> [(version, source)]

        # Extract versions from files
        for filepath, content in files.items():
            file_type = self._detect_file_type(filepath)
            if not file_type:
                continue

            versions = self._extract_versions(content, file_type)
            for tech, version in versions:
                if tech not in tech_findings:
                    tech_findings[tech] = []
                tech_findings[tech].append((version, filepath))

        # Build assessments
        for tech, findings in tech_findings.items():
            # Use most specific version found
            versions = [v for v, _ in findings]
            sources = [s for _, s in findings]
            detected_version = versions[0]  # Take first found

            eol_info = self.get_eol_info(tech, detected_version)

            if eol_info:
                risk_level = eol_info.get_risk_level()
                recommendation = self._generate_recommendation(tech, detected_version, eol_info)
            else:
                risk_level = RiskLevel.UNKNOWN
                recommendation = f"Version {detected_version} not in EOL database"

            assessment = TechnologyAssessment(
                technology=tech,
                detected_version=detected_version,
                eol_info=eol_info,
                risk_level=risk_level,
                recommendation=recommendation,
                detection_sources=sources,
            )
            result.assessments.append(assessment)

            # Track critical items
            if risk_level == RiskLevel.CRITICAL:
                result.critical_items.append(f"{tech} {detected_version}")

            # Track recommended upgrades
            if eol_info and eol_info.latest_version and detected_version != eol_info.latest_version:
                result.recommended_upgrades.append({
                    "technology": tech,
                    "current": detected_version,
                    "recommended": eol_info.latest_version,
                    "risk_level": risk_level.value,
                })

        # Calculate risk summary
        for level in RiskLevel:
            count = len([a for a in result.assessments if a.risk_level == level])
            result.risk_summary[level.value] = count

        logger.info(
            f"Tech radar scan: {len(result.assessments)} technologies, "
            f"{len(result.critical_items)} critical"
        )

        return result

    def _generate_recommendation(
        self,
        tech: str,
        version: str,
        eol_info: EOLInfo
    ) -> str:
        """Generate upgrade recommendation."""
        if eol_info.status == EOLStatus.EOL:
            if eol_info.latest_version:
                return f"CRITICAL: {tech} {version} is EOL. Upgrade to {eol_info.latest_version}"
            return f"CRITICAL: {tech} {version} is EOL. Upgrade immediately"

        if eol_info.status == EOLStatus.DEPRECATED:
            return f"DEPRECATED: {tech} {version} is deprecated. Plan migration"

        if eol_info.eol_date:
            days_until = (eol_info.eol_date - date.today()).days
            if days_until < 180:
                return f"EOL in {days_until} days. Plan upgrade to {eol_info.latest_version}"
            if days_until < 365:
                return f"EOL in {days_until} days. Consider upgrading to {eol_info.latest_version}"

        if eol_info.latest_version and version != eol_info.latest_version:
            return f"Newer version available: {eol_info.latest_version}"

        return "Up to date"

    def generate_radar_report(self, result: TechRadarResult) -> str:
        """Generate markdown radar report."""
        lines = [
            "# Technology Radar Report",
            "",
            f"**Scan Date:** {result.scan_date.strftime('%Y-%m-%d %H:%M')}",
            f"**Technologies Scanned:** {len(result.assessments)}",
            "",
            "## Risk Summary",
            "",
            "| Risk Level | Count |",
            "|------------|-------|",
        ]

        for level in RiskLevel:
            count = result.risk_summary.get(level.value, 0)
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "safe": "✅", "unknown": "⚪"}.get(level.value, "⚪")
            lines.append(f"| {emoji} {level.value.title()} | {count} |")

        if result.critical_items:
            lines.extend([
                "",
                "## 🚨 Critical Items (Require Immediate Attention)",
                "",
            ])
            for item in result.critical_items:
                lines.append(f"- **{item}**")

        if result.recommended_upgrades:
            lines.extend([
                "",
                "## Recommended Upgrades",
                "",
                "| Technology | Current | Recommended | Risk |",
                "|------------|---------|-------------|------|",
            ])
            for upgrade in sorted(result.recommended_upgrades, key=lambda x: x["risk_level"]):
                lines.append(
                    f"| {upgrade['technology']} | {upgrade['current']} | "
                    f"{upgrade['recommended']} | {upgrade['risk_level']} |"
                )

        lines.extend([
            "",
            "## Technology Details",
            "",
        ])

        for assessment in sorted(result.assessments, key=lambda x: x.risk_level.value):
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "safe": "✅", "unknown": "⚪"}.get(assessment.risk_level.value, "⚪")
            lines.append(f"### {emoji} {assessment.technology} {assessment.detected_version or ''}")
            lines.append(f"- **Risk Level:** {assessment.risk_level.value}")
            if assessment.eol_info:
                if assessment.eol_info.eol_date:
                    lines.append(f"- **EOL Date:** {assessment.eol_info.eol_date}")
                lines.append(f"- **Status:** {assessment.eol_info.status.value}")
                if assessment.eol_info.lts:
                    lines.append("- **LTS:** Yes")
            lines.append(f"- **Recommendation:** {assessment.recommendation}")
            lines.append(f"- **Sources:** {', '.join(assessment.detection_sources)}")
            lines.append("")

        return "\n".join(lines)
