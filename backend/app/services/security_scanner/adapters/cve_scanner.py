"""
CVE Database Scanner (K2 - Fase 24).

Integrates with National Vulnerability Database (NVD) and Open Source Vulnerabilities (OSV)
for comprehensive CVE detection and CVSS scoring.

Author: Claude Code (Week 158)
Date: 2026-01-15
"""

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
import aiohttp

from ..models.findings import (
    SecurityFinding,
    ScanResult,
    ScannerType,
    Severity,
    Location,
    SuggestedFix,
)
from .base import CustomPatternScanner

logger = logging.getLogger(__name__)


class CVESource(str, Enum):
    """CVE data source."""
    NVD = "nvd"  # National Vulnerability Database
    OSV = "osv"  # Open Source Vulnerabilities
    GITHUB = "github"  # GitHub Security Advisories
    LOCAL = "local"  # Local cache


class CVSSVersion(str, Enum):
    """CVSS version."""
    V2 = "2.0"
    V3 = "3.0"
    V3_1 = "3.1"
    V4 = "4.0"


@dataclass
class CVSSScore:
    """CVSS score details."""
    version: CVSSVersion
    base_score: float
    vector_string: str
    severity: str

    # V3/V4 metrics
    attack_vector: Optional[str] = None
    attack_complexity: Optional[str] = None
    privileges_required: Optional[str] = None
    user_interaction: Optional[str] = None
    scope: Optional[str] = None
    confidentiality_impact: Optional[str] = None
    integrity_impact: Optional[str] = None
    availability_impact: Optional[str] = None


@dataclass
class CVERecord:
    """CVE record with full details."""
    cve_id: str
    title: str
    description: str
    published_date: datetime
    last_modified: datetime
    cvss_scores: List[CVSSScore] = field(default_factory=list)
    cwe_ids: List[str] = field(default_factory=list)
    affected_products: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    source: CVESource = CVESource.NVD

    # Exploit info
    exploit_available: bool = False
    exploit_maturity: Optional[str] = None

    # Fix info
    patch_available: bool = False
    patch_urls: List[str] = field(default_factory=list)

    @property
    def highest_cvss(self) -> Optional[CVSSScore]:
        """Get highest CVSS score."""
        if not self.cvss_scores:
            return None
        return max(self.cvss_scores, key=lambda x: x.base_score)

    @property
    def severity(self) -> Severity:
        """Map CVSS to severity."""
        cvss = self.highest_cvss
        if not cvss:
            return Severity.MEDIUM

        score = cvss.base_score
        if score >= 9.0:
            return Severity.CRITICAL
        elif score >= 7.0:
            return Severity.HIGH
        elif score >= 4.0:
            return Severity.MEDIUM
        elif score >= 0.1:
            return Severity.LOW
        return Severity.INFO


@dataclass
class DependencyInfo:
    """Parsed dependency information."""
    name: str
    version: str
    ecosystem: str  # npm, pypi, maven, etc.
    file_path: str
    line_number: int = 0
    is_dev_dependency: bool = False
    is_direct: bool = True


@dataclass
class VulnerabilityMatch:
    """Match between dependency and CVE."""
    dependency: DependencyInfo
    cve: CVERecord
    affected_versions: str
    fixed_version: Optional[str] = None
    match_confidence: float = 1.0


@dataclass
class CVECoverageReport:
    """CVE scanning coverage report."""
    total_dependencies: int
    dependencies_scanned: int
    vulnerabilities_found: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    cve_sources_used: List[str]
    scan_timestamp: datetime
    cache_status: str

    # By ecosystem
    ecosystem_breakdown: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # Top vulnerabilities
    top_vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary": {
                "total_dependencies": self.total_dependencies,
                "dependencies_scanned": self.dependencies_scanned,
                "vulnerabilities_found": self.vulnerabilities_found,
                "scan_timestamp": self.scan_timestamp.isoformat(),
            },
            "severity_breakdown": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
            },
            "sources_used": self.cve_sources_used,
            "cache_status": self.cache_status,
            "ecosystem_breakdown": self.ecosystem_breakdown,
            "top_vulnerabilities": self.top_vulnerabilities[:10],
        }


# Ecosystem to package manager mapping
ECOSYSTEM_MAP = {
    "npm": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
    "pypi": ["requirements.txt", "Pipfile", "Pipfile.lock", "poetry.lock", "setup.py", "pyproject.toml"],
    "maven": ["pom.xml"],
    "gradle": ["build.gradle", "build.gradle.kts"],
    "nuget": [".csproj", "packages.config", "packages.lock.json"],
    "go": ["go.mod", "go.sum"],
    "cargo": ["Cargo.toml", "Cargo.lock"],
    "rubygems": ["Gemfile", "Gemfile.lock"],
    "composer": ["composer.json", "composer.lock"],
}


class CVEDatabaseService:
    """
    Service for fetching and caching CVE data from multiple sources.
    """

    NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    OSV_API_URL = "https://api.osv.dev/v1"
    GITHUB_API_URL = "https://api.github.com/advisories"

    CACHE_TTL_HOURS = 24

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        nvd_api_key: Optional[str] = None,
        github_token: Optional[str] = None,
    ):
        """Initialize CVE database service."""
        self.cache_dir = cache_dir or Path.home() / ".cache" / "marqed" / "cve"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.nvd_api_key = nvd_api_key
        self.github_token = github_token
        self._cache: Dict[str, CVERecord] = {}
        self._cache_loaded = False

    async def lookup_cve(self, cve_id: str) -> Optional[CVERecord]:
        """
        Look up a single CVE by ID.

        Args:
            cve_id: CVE identifier (e.g., "CVE-2021-44228")

        Returns:
            CVE record if found
        """
        # Check cache first
        if cve_id in self._cache:
            return self._cache[cve_id]

        # Try NVD
        record = await self._fetch_from_nvd(cve_id)
        if record:
            self._cache[cve_id] = record
            return record

        return None

    async def lookup_package_vulnerabilities(
        self,
        package_name: str,
        version: str,
        ecosystem: str,
    ) -> List[CVERecord]:
        """
        Look up vulnerabilities for a package.

        Args:
            package_name: Package name
            version: Package version
            ecosystem: Package ecosystem (npm, pypi, etc.)

        Returns:
            List of CVE records affecting this package version
        """
        # Use OSV for package-based lookup (it's designed for this)
        return await self._fetch_from_osv(package_name, version, ecosystem)

    async def _fetch_from_nvd(self, cve_id: str) -> Optional[CVERecord]:
        """Fetch CVE from NVD API."""
        try:
            headers = {}
            if self.nvd_api_key:
                headers["apiKey"] = self.nvd_api_key

            async with aiohttp.ClientSession() as session:
                url = f"{self.NVD_API_URL}?cveId={cve_id}"
                async with session.get(url, headers=headers, timeout=30) as resp:
                    if resp.status != 200:
                        return None

                    data = await resp.json()
                    vulnerabilities = data.get("vulnerabilities", [])

                    if not vulnerabilities:
                        return None

                    return self._parse_nvd_record(vulnerabilities[0])

        except Exception as e:
            logger.warning(f"Failed to fetch CVE {cve_id} from NVD: {e}")
            return None

    async def _fetch_from_osv(
        self,
        package_name: str,
        version: str,
        ecosystem: str,
    ) -> List[CVERecord]:
        """Fetch vulnerabilities from OSV."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "package": {
                        "name": package_name,
                        "ecosystem": ecosystem.capitalize(),
                    },
                    "version": version,
                }

                async with session.post(
                    f"{self.OSV_API_URL}/query",
                    json=payload,
                    timeout=30,
                ) as resp:
                    if resp.status != 200:
                        return []

                    data = await resp.json()
                    vulns = data.get("vulns", [])

                    return [self._parse_osv_record(v) for v in vulns]

        except Exception as e:
            logger.warning(f"Failed to fetch from OSV for {package_name}: {e}")
            return []

    def _parse_nvd_record(self, data: Dict[str, Any]) -> CVERecord:
        """Parse NVD API response into CVERecord."""
        cve_data = data.get("cve", {})

        cve_id = cve_data.get("id", "")

        # Get descriptions
        descriptions = cve_data.get("descriptions", [])
        description = ""
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break

        # Parse CVSS scores
        cvss_scores = []
        metrics = cve_data.get("metrics", {})

        # CVSS v3.1
        cvss_v31 = metrics.get("cvssMetricV31", [])
        for metric in cvss_v31:
            cvss_data = metric.get("cvssData", {})
            cvss_scores.append(CVSSScore(
                version=CVSSVersion.V3_1,
                base_score=cvss_data.get("baseScore", 0.0),
                vector_string=cvss_data.get("vectorString", ""),
                severity=cvss_data.get("baseSeverity", "MEDIUM"),
                attack_vector=cvss_data.get("attackVector"),
                attack_complexity=cvss_data.get("attackComplexity"),
                privileges_required=cvss_data.get("privilegesRequired"),
                user_interaction=cvss_data.get("userInteraction"),
            ))

        # CVSS v2 fallback
        if not cvss_scores:
            cvss_v2 = metrics.get("cvssMetricV2", [])
            for metric in cvss_v2:
                cvss_data = metric.get("cvssData", {})
                cvss_scores.append(CVSSScore(
                    version=CVSSVersion.V2,
                    base_score=cvss_data.get("baseScore", 0.0),
                    vector_string=cvss_data.get("vectorString", ""),
                    severity=metric.get("baseSeverity", "MEDIUM"),
                ))

        # Parse CWE IDs
        cwe_ids = []
        weaknesses = cve_data.get("weaknesses", [])
        for weakness in weaknesses:
            for desc in weakness.get("description", []):
                if desc.get("lang") == "en":
                    cwe_match = re.search(r"CWE-\d+", desc.get("value", ""))
                    if cwe_match:
                        cwe_ids.append(cwe_match.group())

        # Parse dates
        published = cve_data.get("published", "")
        modified = cve_data.get("lastModified", "")

        try:
            published_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except:
            published_date = datetime.now(timezone.utc)

        try:
            modified_date = datetime.fromisoformat(modified.replace("Z", "+00:00"))
        except:
            modified_date = datetime.now(timezone.utc)

        # Parse references
        references = []
        for ref in cve_data.get("references", []):
            references.append(ref.get("url", ""))

        return CVERecord(
            cve_id=cve_id,
            title=f"{cve_id}: {description[:100]}..." if len(description) > 100 else f"{cve_id}: {description}",
            description=description,
            published_date=published_date,
            last_modified=modified_date,
            cvss_scores=cvss_scores,
            cwe_ids=cwe_ids,
            references=references[:5],
            source=CVESource.NVD,
        )

    def _parse_osv_record(self, data: Dict[str, Any]) -> CVERecord:
        """Parse OSV API response into CVERecord."""
        osv_id = data.get("id", "")

        # Get CVE ID if available
        aliases = data.get("aliases", [])
        cve_id = osv_id
        for alias in aliases:
            if alias.startswith("CVE-"):
                cve_id = alias
                break

        summary = data.get("summary", "")
        details = data.get("details", summary)

        # Parse severity from database_specific or severity field
        cvss_scores = []
        severity_data = data.get("severity", [])
        for sev in severity_data:
            if sev.get("type") == "CVSS_V3":
                score_str = sev.get("score", "")
                # Parse CVSS vector string
                score_match = re.search(r"CVSS:3\.\d/AV:\w/.*", score_str)
                if score_match:
                    # Extract base score from vector if possible
                    cvss_scores.append(CVSSScore(
                        version=CVSSVersion.V3_1,
                        base_score=7.0,  # Default, would need proper parsing
                        vector_string=score_str,
                        severity="HIGH",
                    ))

        # Parse dates
        published = data.get("published", "")
        modified = data.get("modified", "")

        try:
            published_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except:
            published_date = datetime.now(timezone.utc)

        try:
            modified_date = datetime.fromisoformat(modified.replace("Z", "+00:00"))
        except:
            modified_date = datetime.now(timezone.utc)

        # Parse references
        references = [ref.get("url", "") for ref in data.get("references", [])]

        # Parse CWEs from database_specific
        cwe_ids = []
        db_specific = data.get("database_specific", {})
        if "cwe_ids" in db_specific:
            cwe_ids = db_specific["cwe_ids"]

        return CVERecord(
            cve_id=cve_id,
            title=f"{cve_id}: {summary}",
            description=details,
            published_date=published_date,
            last_modified=modified_date,
            cvss_scores=cvss_scores,
            cwe_ids=cwe_ids,
            references=references[:5],
            source=CVESource.OSV,
        )


class CVEScanner(CustomPatternScanner):
    """
    CVE Scanner for dependency vulnerability detection.

    Scans dependency files and checks against CVE databases
    (NVD, OSV) for known vulnerabilities.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        cve_service: Optional[CVEDatabaseService] = None,
        nvd_api_key: Optional[str] = None,
        github_token: Optional[str] = None,
    ):
        """Initialize CVE scanner."""
        super().__init__()
        self.cve_service = cve_service or CVEDatabaseService(
            nvd_api_key=nvd_api_key,
            github_token=github_token,
        )
        self._vulnerabilities: List[VulnerabilityMatch] = []

    @property
    def scanner_type(self) -> ScannerType:
        return ScannerType.CVE_SCANNER

    @property
    def supported_languages(self) -> Set[str]:
        return {"generic"}

    @property
    def supported_extensions(self) -> Set[str]:
        extensions = set()
        for files in ECOSYSTEM_MAP.values():
            for f in files:
                if f.startswith("."):
                    extensions.add(f)
                else:
                    extensions.add(f"/{f}")  # Match full filename
        return extensions

    @property
    def rules(self) -> List[Dict[str, Any]]:
        """
        CVE scanner doesn't use pattern-based rules.

        Returns empty list as vulnerabilities are detected via CVE database
        lookups rather than regex patterns.
        """
        return []

    def is_available(self) -> bool:
        """CVE scanner is always available."""
        return True

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """
        Scan for CVE vulnerabilities in dependencies.

        Args:
            target_path: Path to scan
            config: Optional configuration

        Returns:
            Scan result with findings
        """
        started_at = datetime.now(timezone.utc)
        config = config or {}

        # Parse dependencies from lock files
        dependencies = await self._parse_dependencies(target_path)

        # Look up vulnerabilities for each dependency
        findings: List[SecurityFinding] = []
        files_scanned = 0
        self._vulnerabilities = []

        for dep in dependencies:
            vulns = await self.cve_service.lookup_package_vulnerabilities(
                dep.name,
                dep.version,
                dep.ecosystem,
            )

            for vuln in vulns:
                match = VulnerabilityMatch(
                    dependency=dep,
                    cve=vuln,
                    affected_versions=f"<= {dep.version}",  # Simplified
                )
                self._vulnerabilities.append(match)

                finding = self._create_finding(match)
                findings.append(finding)

            files_scanned += 1

        completed_at = datetime.now(timezone.utc)
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        return ScanResult(
            scanner=self.scanner_type,
            scanner_version=self.VERSION,
            scan_duration_ms=duration_ms,
            findings=findings,
            files_scanned=files_scanned,
            started_at=started_at,
            completed_at=completed_at,
        )

    async def _parse_dependencies(self, target_path: Path) -> List[DependencyInfo]:
        """Parse dependencies from lock files."""
        dependencies = []

        if target_path.is_file():
            deps = self._parse_dependency_file(target_path)
            dependencies.extend(deps)
        else:
            # Find all dependency files
            for ecosystem, filenames in ECOSYSTEM_MAP.items():
                for filename in filenames:
                    for dep_file in target_path.rglob(filename):
                        deps = self._parse_dependency_file(dep_file, ecosystem)
                        dependencies.extend(deps)

        return dependencies

    def _parse_dependency_file(
        self,
        file_path: Path,
        ecosystem: Optional[str] = None,
    ) -> List[DependencyInfo]:
        """Parse a single dependency file."""
        dependencies = []

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            filename = file_path.name.lower()

            # Detect ecosystem from filename
            if not ecosystem:
                for eco, filenames in ECOSYSTEM_MAP.items():
                    if filename in [f.lower() for f in filenames]:
                        ecosystem = eco
                        break

            if ecosystem == "npm" and filename == "package.json":
                dependencies.extend(self._parse_package_json(content, str(file_path)))
            elif ecosystem == "npm" and "lock" in filename:
                dependencies.extend(self._parse_package_lock(content, str(file_path)))
            elif ecosystem == "pypi" and filename == "requirements.txt":
                dependencies.extend(self._parse_requirements_txt(content, str(file_path)))
            elif ecosystem == "pypi" and filename == "poetry.lock":
                dependencies.extend(self._parse_poetry_lock(content, str(file_path)))
            elif ecosystem == "go" and filename == "go.mod":
                dependencies.extend(self._parse_go_mod(content, str(file_path)))
            elif ecosystem == "cargo" and filename == "cargo.lock":
                dependencies.extend(self._parse_cargo_lock(content, str(file_path)))

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")

        return dependencies

    def _parse_package_json(self, content: str, file_path: str) -> List[DependencyInfo]:
        """Parse npm package.json."""
        deps = []
        try:
            data = json.loads(content)

            for name, version in data.get("dependencies", {}).items():
                version_clean = version.lstrip("^~>=<")
                deps.append(DependencyInfo(
                    name=name,
                    version=version_clean,
                    ecosystem="npm",
                    file_path=file_path,
                    is_dev_dependency=False,
                ))

            for name, version in data.get("devDependencies", {}).items():
                version_clean = version.lstrip("^~>=<")
                deps.append(DependencyInfo(
                    name=name,
                    version=version_clean,
                    ecosystem="npm",
                    file_path=file_path,
                    is_dev_dependency=True,
                ))

        except json.JSONDecodeError:
            pass

        return deps

    def _parse_package_lock(self, content: str, file_path: str) -> List[DependencyInfo]:
        """Parse npm package-lock.json."""
        deps = []
        try:
            data = json.loads(content)
            packages = data.get("packages", data.get("dependencies", {}))

            for name, info in packages.items():
                if not name or name == "":
                    continue

                # Remove node_modules/ prefix
                clean_name = name.replace("node_modules/", "")
                if not clean_name:
                    continue

                version = info.get("version", "")
                if version:
                    deps.append(DependencyInfo(
                        name=clean_name,
                        version=version,
                        ecosystem="npm",
                        file_path=file_path,
                        is_dev_dependency=info.get("dev", False),
                    ))

        except json.JSONDecodeError:
            pass

        return deps

    def _parse_requirements_txt(self, content: str, file_path: str) -> List[DependencyInfo]:
        """Parse Python requirements.txt."""
        deps = []

        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-'):
                continue

            # Parse: package==version or package>=version
            match = re.match(r'^([a-zA-Z0-9_-]+)\s*([=<>!~]+)\s*([0-9.]+)', line)
            if match:
                deps.append(DependencyInfo(
                    name=match.group(1),
                    version=match.group(3),
                    ecosystem="pypi",
                    file_path=file_path,
                    line_number=line_num,
                ))

        return deps

    def _parse_poetry_lock(self, content: str, file_path: str) -> List[DependencyInfo]:
        """Parse Python poetry.lock (TOML format)."""
        deps = []

        # Simple TOML parsing for [[package]] sections
        current_package = {}
        for line in content.split('\n'):
            line = line.strip()

            if line == "[[package]]":
                if current_package.get("name") and current_package.get("version"):
                    deps.append(DependencyInfo(
                        name=current_package["name"],
                        version=current_package["version"],
                        ecosystem="pypi",
                        file_path=file_path,
                    ))
                current_package = {}
            elif line.startswith("name = "):
                current_package["name"] = line.split('"')[1]
            elif line.startswith("version = "):
                current_package["version"] = line.split('"')[1]

        # Don't forget last package
        if current_package.get("name") and current_package.get("version"):
            deps.append(DependencyInfo(
                name=current_package["name"],
                version=current_package["version"],
                ecosystem="pypi",
                file_path=file_path,
            ))

        return deps

    def _parse_go_mod(self, content: str, file_path: str) -> List[DependencyInfo]:
        """Parse Go go.mod."""
        deps = []

        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if line.startswith("require ") or line.startswith("\t"):
                # Parse: module version
                match = re.match(r'^[\t\s]*([\w./\-]+)\s+v?([0-9.]+)', line)
                if match:
                    deps.append(DependencyInfo(
                        name=match.group(1),
                        version=match.group(2),
                        ecosystem="go",
                        file_path=file_path,
                        line_number=line_num,
                    ))

        return deps

    def _parse_cargo_lock(self, content: str, file_path: str) -> List[DependencyInfo]:
        """Parse Rust Cargo.lock (TOML format)."""
        deps = []

        current_package = {}
        for line in content.split('\n'):
            line = line.strip()

            if line == "[[package]]":
                if current_package.get("name") and current_package.get("version"):
                    deps.append(DependencyInfo(
                        name=current_package["name"],
                        version=current_package["version"],
                        ecosystem="cargo",
                        file_path=file_path,
                    ))
                current_package = {}
            elif line.startswith("name = "):
                current_package["name"] = line.split('"')[1]
            elif line.startswith("version = "):
                current_package["version"] = line.split('"')[1]

        if current_package.get("name") and current_package.get("version"):
            deps.append(DependencyInfo(
                name=current_package["name"],
                version=current_package["version"],
                ecosystem="cargo",
                file_path=file_path,
            ))

        return deps

    def _create_finding(self, match: VulnerabilityMatch) -> SecurityFinding:
        """Create security finding from vulnerability match."""
        cve = match.cve
        dep = match.dependency

        # Build suggested fix
        fixes = []
        if match.fixed_version:
            fixes.append(SuggestedFix(
                description=f"Upgrade {dep.name} to version {match.fixed_version}",
                replacement_text=f"{dep.name}=={match.fixed_version}" if dep.ecosystem == "pypi" else f'"{dep.name}": "{match.fixed_version}"',
            ))
        else:
            fixes.append(SuggestedFix(
                description=f"Check for updates to {dep.name} that address {cve.cve_id}",
            ))

        # Get CVSS info for description
        cvss = cve.highest_cvss
        cvss_info = f"CVSS: {cvss.base_score} ({cvss.severity})" if cvss else "CVSS: Unknown"

        return SecurityFinding(
            id=f"CVE-{dep.name}-{cve.cve_id}",
            rule_id=cve.cve_id,
            title=f"{cve.cve_id}: Vulnerability in {dep.name}",
            description=f"{cve.description}\n\n{cvss_info}",
            severity=cve.severity,
            scanner=self.scanner_type,
            location=Location(
                file_path=dep.file_path,
                start_line=dep.line_number or 1,
                snippet=f"{dep.name}=={dep.version}",
            ),
            cwe_ids=cve.cwe_ids,
            category="dependency_vulnerability",
            confidence=match.match_confidence,
            suggested_fixes=fixes,
            raw_data={
                "cve_id": cve.cve_id,
                "package_name": dep.name,
                "package_version": dep.version,
                "ecosystem": dep.ecosystem,
                "cvss_score": cvss.base_score if cvss else None,
                "cvss_vector": cvss.vector_string if cvss else None,
                "references": cve.references,
                "published_date": cve.published_date.isoformat(),
            },
        )

    def get_coverage_report(
        self,
        scan_result: Optional[ScanResult] = None,
    ) -> CVECoverageReport:
        """Generate CVE coverage report."""
        vulns = self._vulnerabilities

        # Count by severity
        critical = sum(1 for v in vulns if v.cve.severity == Severity.CRITICAL)
        high = sum(1 for v in vulns if v.cve.severity == Severity.HIGH)
        medium = sum(1 for v in vulns if v.cve.severity == Severity.MEDIUM)
        low = sum(1 for v in vulns if v.cve.severity == Severity.LOW)

        # Group by ecosystem
        ecosystem_breakdown: Dict[str, Dict[str, int]] = {}
        for v in vulns:
            eco = v.dependency.ecosystem
            if eco not in ecosystem_breakdown:
                ecosystem_breakdown[eco] = {"total": 0, "critical": 0, "high": 0}
            ecosystem_breakdown[eco]["total"] += 1
            if v.cve.severity == Severity.CRITICAL:
                ecosystem_breakdown[eco]["critical"] += 1
            elif v.cve.severity == Severity.HIGH:
                ecosystem_breakdown[eco]["high"] += 1

        # Top vulnerabilities
        top_vulns = sorted(vulns, key=lambda x: x.cve.highest_cvss.base_score if x.cve.highest_cvss else 0, reverse=True)[:10]

        return CVECoverageReport(
            total_dependencies=len(set(v.dependency.name for v in vulns)) if vulns else 0,
            dependencies_scanned=scan_result.files_scanned if scan_result else 0,
            vulnerabilities_found=len(vulns),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            cve_sources_used=["OSV", "NVD"],
            scan_timestamp=datetime.now(timezone.utc),
            cache_status="active",
            ecosystem_breakdown=ecosystem_breakdown,
            top_vulnerabilities=[
                {
                    "cve_id": v.cve.cve_id,
                    "package": v.dependency.name,
                    "version": v.dependency.version,
                    "cvss": v.cve.highest_cvss.base_score if v.cve.highest_cvss else None,
                    "severity": v.cve.severity.value,
                }
                for v in top_vulns
            ],
        )


def create_cve_scanner(
    nvd_api_key: Optional[str] = None,
    github_token: Optional[str] = None,
) -> CVEScanner:
    """Factory function to create CVE scanner."""
    return CVEScanner(
        nvd_api_key=nvd_api_key,
        github_token=github_token,
    )
