# backend/app/services/static_analysis/compliance_checker.py
"""
Compliance Checker - Pluggable compliance framework checker.

Supports:
- NEN7510: Dutch healthcare standard
- ISO27001: Information security management
- HIPAA: US healthcare (PHI protection)
- SOC2: Service organization controls
- GDPR: EU privacy regulation
- PCI-DSS: Payment card industry

Part of Fase 15: Hybrid Static-LLM Extraction Pipeline
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING
from enum import Enum
from abc import ABC, abstractmethod
import re
import logging

if TYPE_CHECKING:
    from .nfr_detector import NFRDetection

logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    NEN7510 = "NEN7510"      # Dutch healthcare
    ISO27001 = "ISO27001"    # Information security
    HIPAA = "HIPAA"          # US healthcare
    SOC2 = "SOC2"            # Service organization
    GDPR = "GDPR"            # EU privacy
    PCI_DSS = "PCI_DSS"      # Payment card


@dataclass
class ComplianceRequirement:
    """A compliance requirement definition."""
    id: str                    # e.g., "NEN7510-9.4.1"
    framework: ComplianceFramework
    title: str
    description: str
    category: str              # e.g., "Access Control", "Encryption"
    required_patterns: List[str]  # Patterns that should be present
    forbidden_patterns: List[str] # Patterns that should NOT be present
    severity: str              # critical, high, medium, low


@dataclass
class ComplianceViolation:
    """A detected compliance violation."""
    requirement: ComplianceRequirement
    violation_type: str        # "missing" or "forbidden"
    file_path: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    remediation: str


@dataclass
class ComplianceReport:
    """Complete compliance check report."""
    frameworks_checked: List[ComplianceFramework]
    violations: List[ComplianceViolation]
    passed_requirements: List[str]
    compliance_score: float    # 0.0 - 1.0
    by_framework: Dict[str, Dict]
    by_severity: Dict[str, List[ComplianceViolation]]


class ComplianceRuleSet(ABC):
    """Abstract base class for compliance rule sets."""

    @abstractmethod
    def get_requirements(self) -> List[ComplianceRequirement]:
        """Get all requirements for this framework."""
        pass

    @abstractmethod
    def get_framework(self) -> ComplianceFramework:
        """Get the framework this ruleset applies to."""
        pass


class NEN7510RuleSet(ComplianceRuleSet):
    """
    NEN7510 (Dutch healthcare) compliance rules.

    NEN7510 is the Dutch standard for information security in healthcare.
    Based on ISO27001 with additional healthcare-specific requirements.
    """

    def get_framework(self) -> ComplianceFramework:
        return ComplianceFramework.NEN7510

    def get_requirements(self) -> List[ComplianceRequirement]:
        return [
            ComplianceRequirement(
                id="NEN7510-9.4.1",
                framework=ComplianceFramework.NEN7510,
                title="Information access restriction",
                description="Access to information must be restricted based on access control policy",
                category="Access Control",
                required_patterns=[
                    r'@login_required|@authenticated|is_authenticated',
                    r'has_permission|check_permission|require_permission',
                    r'role_based|rbac|access_control',
                ],
                forbidden_patterns=[],
                severity="critical"
            ),
            ComplianceRequirement(
                id="NEN7510-9.4.2",
                framework=ComplianceFramework.NEN7510,
                title="Secure log-on procedures",
                description="Access to systems must use secure authentication",
                category="Access Control",
                required_patterns=[
                    r'password_hash|hash_password|bcrypt|argon2',
                    r'mfa|two_factor|2fa|otp',
                ],
                forbidden_patterns=[
                    r'password\s*=\s*["\'][^"\']{1,20}["\']',  # Short hardcoded passwords
                ],
                severity="high"
            ),
            ComplianceRequirement(
                id="NEN7510-10.1.1",
                framework=ComplianceFramework.NEN7510,
                title="Cryptographic controls",
                description="Encryption must be used for sensitive health data",
                category="Encryption",
                required_patterns=[
                    r'\.encrypt\(|\.decrypt\(|AES|RSA|fernet',
                    r'hash_password|bcrypt|argon2|pbkdf2',
                    r'ssl_context|https|tls',
                ],
                forbidden_patterns=[
                    r'password\s*=\s*["\'][^"\']+["\']',  # Hardcoded passwords
                    r'md5\(|sha1\(',  # Weak hashing (without salt)
                ],
                severity="high"
            ),
            ComplianceRequirement(
                id="NEN7510-10.1.2",
                framework=ComplianceFramework.NEN7510,
                title="Key management",
                description="Cryptographic keys must be properly managed",
                category="Encryption",
                required_patterns=[
                    r'secret_key|SECRET_KEY|encryption_key',
                    r'key_rotation|rotate_key',
                    r'environ\[|os\.getenv|settings\.',
                ],
                forbidden_patterns=[
                    r'SECRET_KEY\s*=\s*["\'][^"\']+["\']',  # Hardcoded secrets in code
                ],
                severity="high"
            ),
            ComplianceRequirement(
                id="NEN7510-12.4.1",
                framework=ComplianceFramework.NEN7510,
                title="Event logging",
                description="All access to patient data must be logged",
                category="Audit",
                required_patterns=[
                    r'logger\.|logging\.|audit_log|access_log',
                    r'log\.(info|warning|error|debug)',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
            ComplianceRequirement(
                id="NEN7510-12.4.3",
                framework=ComplianceFramework.NEN7510,
                title="Protection of log information",
                description="Logging facilities must be protected against tampering",
                category="Audit",
                required_patterns=[
                    r'log_level|LOG_LEVEL',
                    r'rotating.*handler|TimedRotatingFileHandler',
                ],
                forbidden_patterns=[],
                severity="medium"
            ),
            ComplianceRequirement(
                id="NEN7510-13.1.1",
                framework=ComplianceFramework.NEN7510,
                title="Network controls",
                description="Networks shall be managed and controlled",
                category="Network Security",
                required_patterns=[
                    r'firewall|ip_whitelist|allowed_hosts',
                    r'CORS|cors_origins',
                ],
                forbidden_patterns=[
                    r'CORS.*\*|allow_all_origins|ALLOWED_HOSTS\s*=\s*\[\s*["\*]',
                ],
                severity="high"
            ),
        ]


class ISO27001RuleSet(ComplianceRuleSet):
    """
    ISO 27001 compliance rules.

    International standard for information security management systems (ISMS).
    """

    def get_framework(self) -> ComplianceFramework:
        return ComplianceFramework.ISO27001

    def get_requirements(self) -> List[ComplianceRequirement]:
        return [
            ComplianceRequirement(
                id="ISO27001-A.9.4.1",
                framework=ComplianceFramework.ISO27001,
                title="Information access restriction",
                description="Access to information and application system functions shall be restricted",
                category="Access Control",
                required_patterns=[
                    r'@login_required|@authenticated',
                    r'role_required|permission_required',
                    r'authorization|authorize',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
            ComplianceRequirement(
                id="ISO27001-A.9.4.2",
                framework=ComplianceFramework.ISO27001,
                title="Secure log-on procedures",
                description="Access shall be controlled by secure log-on procedures",
                category="Access Control",
                required_patterns=[
                    r'password.*hash|bcrypt|argon2|pbkdf2',
                    r'session.*timeout|SESSION_COOKIE_AGE',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
            ComplianceRequirement(
                id="ISO27001-A.10.1.1",
                framework=ComplianceFramework.ISO27001,
                title="Cryptographic controls policy",
                description="A policy on the use of cryptographic controls shall be developed",
                category="Encryption",
                required_patterns=[
                    r'ssl|tls|https|encrypt',
                    r'SECURE_SSL_REDIRECT|SESSION_COOKIE_SECURE',
                ],
                forbidden_patterns=[
                    r'verify\s*=\s*False',  # SSL verification disabled
                    r'SECURE_SSL_REDIRECT\s*=\s*False',
                ],
                severity="high"
            ),
            ComplianceRequirement(
                id="ISO27001-A.12.4.1",
                framework=ComplianceFramework.ISO27001,
                title="Event logging",
                description="Event logs recording user activities shall be produced and kept",
                category="Logging",
                required_patterns=[
                    r'logging\.|logger\.',
                    r'audit|access_log',
                ],
                forbidden_patterns=[],
                severity="medium"
            ),
            ComplianceRequirement(
                id="ISO27001-A.12.6.1",
                framework=ComplianceFramework.ISO27001,
                title="Management of technical vulnerabilities",
                description="Information about technical vulnerabilities shall be obtained",
                category="Vulnerability Management",
                required_patterns=[
                    r'requirements\.txt|Pipfile|package\.json',
                    r'safety|snyk|dependabot',
                ],
                forbidden_patterns=[],
                severity="medium"
            ),
            ComplianceRequirement(
                id="ISO27001-A.14.2.1",
                framework=ComplianceFramework.ISO27001,
                title="Secure development policy",
                description="Rules for the development of software shall be established",
                category="Secure Development",
                required_patterns=[
                    r'test_|pytest|unittest',
                    r'type.*hint|typing\.',
                ],
                forbidden_patterns=[],
                severity="medium"
            ),
        ]


class HIPAARuleSet(ComplianceRuleSet):
    """
    HIPAA (US healthcare) compliance rules.

    Health Insurance Portability and Accountability Act requirements
    for protecting PHI (Protected Health Information).
    """

    def get_framework(self) -> ComplianceFramework:
        return ComplianceFramework.HIPAA

    def get_requirements(self) -> List[ComplianceRequirement]:
        return [
            ComplianceRequirement(
                id="HIPAA-164.312(a)(1)",
                framework=ComplianceFramework.HIPAA,
                title="Access Control",
                description="Implement technical policies for electronic systems maintaining PHI",
                category="Access Control",
                required_patterns=[
                    r'@authenticated|require_auth|is_authenticated',
                    r'role.*based|permission.*check',
                ],
                forbidden_patterns=[],
                severity="critical"
            ),
            ComplianceRequirement(
                id="HIPAA-164.312(a)(2)(i)",
                framework=ComplianceFramework.HIPAA,
                title="Unique User Identification",
                description="Assign a unique name and/or number for identifying users",
                category="Access Control",
                required_patterns=[
                    r'user_id|user\.id|current_user',
                    r'session.*user|authenticated_user',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
            ComplianceRequirement(
                id="HIPAA-164.312(a)(2)(iv)",
                framework=ComplianceFramework.HIPAA,
                title="Encryption and Decryption",
                description="Implement mechanism to encrypt/decrypt ePHI",
                category="Encryption",
                required_patterns=[
                    r'encrypt|decrypt|AES|fernet',
                    r'ssl|tls|https',
                ],
                forbidden_patterns=[],
                severity="critical"
            ),
            ComplianceRequirement(
                id="HIPAA-164.312(b)",
                framework=ComplianceFramework.HIPAA,
                title="Audit Controls",
                description="Implement hardware, software, and procedural mechanisms for recording PHI access",
                category="Audit",
                required_patterns=[
                    r'audit_log|access_log|logger\.',
                    r'log\.(info|warning|error)',
                ],
                forbidden_patterns=[],
                severity="critical"
            ),
            ComplianceRequirement(
                id="HIPAA-164.312(c)(1)",
                framework=ComplianceFramework.HIPAA,
                title="Integrity",
                description="Implement policies to protect ePHI from improper alteration or destruction",
                category="Data Integrity",
                required_patterns=[
                    r'checksum|hash|integrity',
                    r'backup|recovery',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
            ComplianceRequirement(
                id="HIPAA-164.312(e)(1)",
                framework=ComplianceFramework.HIPAA,
                title="Transmission Security",
                description="Implement technical security measures for ePHI transmission",
                category="Network Security",
                required_patterns=[
                    r'ssl|tls|https',
                    r'SECURE_SSL_REDIRECT',
                ],
                forbidden_patterns=[
                    r'http://(?!localhost|127\.0\.0\.1)',
                ],
                severity="critical"
            ),
        ]


class SOC2RuleSet(ComplianceRuleSet):
    """
    SOC 2 compliance rules.

    Service Organization Control 2 - Trust Services Criteria.
    """

    def get_framework(self) -> ComplianceFramework:
        return ComplianceFramework.SOC2

    def get_requirements(self) -> List[ComplianceRequirement]:
        return [
            ComplianceRequirement(
                id="SOC2-CC6.1",
                framework=ComplianceFramework.SOC2,
                title="Logical Access Security",
                description="Logical access security software, infrastructure, and architectures",
                category="Access Control",
                required_patterns=[
                    r'auth|login|permission',
                    r'role.*based|rbac',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
            ComplianceRequirement(
                id="SOC2-CC6.6",
                framework=ComplianceFramework.SOC2,
                title="Security Event Monitoring",
                description="Security events are logged and monitored",
                category="Monitoring",
                required_patterns=[
                    r'logging\.|logger\.|audit',
                    r'monitoring|alert|notification',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
            ComplianceRequirement(
                id="SOC2-CC6.7",
                framework=ComplianceFramework.SOC2,
                title="Data Transmission Protection",
                description="Data transmitted is protected",
                category="Encryption",
                required_patterns=[
                    r'ssl|tls|https|encrypt',
                ],
                forbidden_patterns=[
                    r'verify\s*=\s*False',
                ],
                severity="high"
            ),
            ComplianceRequirement(
                id="SOC2-CC7.2",
                framework=ComplianceFramework.SOC2,
                title="Vulnerability Management",
                description="Vulnerabilities are identified and addressed",
                category="Vulnerability Management",
                required_patterns=[
                    r'security.*scan|vulnerability',
                    r'safety|snyk|dependabot',
                ],
                forbidden_patterns=[],
                severity="medium"
            ),
            ComplianceRequirement(
                id="SOC2-CC8.1",
                framework=ComplianceFramework.SOC2,
                title="Change Management",
                description="Changes are authorized, designed, developed, tested, and approved",
                category="Change Management",
                required_patterns=[
                    r'test_|pytest|unittest',
                    r'ci/cd|github.*actions|gitlab.*ci',
                ],
                forbidden_patterns=[],
                severity="medium"
            ),
        ]


class GDPRRuleSet(ComplianceRuleSet):
    """
    GDPR (EU privacy) compliance rules.

    General Data Protection Regulation requirements.
    """

    def get_framework(self) -> ComplianceFramework:
        return ComplianceFramework.GDPR

    def get_requirements(self) -> List[ComplianceRequirement]:
        return [
            ComplianceRequirement(
                id="GDPR-Art.5(1)(f)",
                framework=ComplianceFramework.GDPR,
                title="Security of processing",
                description="Personal data shall be processed securely",
                category="Data Protection",
                required_patterns=[
                    r'encrypt|hash|pseudonymize',
                    r'ssl|tls|https',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
            ComplianceRequirement(
                id="GDPR-Art.17",
                framework=ComplianceFramework.GDPR,
                title="Right to erasure",
                description="Data subject has the right to obtain erasure of personal data",
                category="Data Rights",
                required_patterns=[
                    r'delete.*user|remove.*personal|anonymize',
                    r'gdpr.*delete|right.*forget',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
            ComplianceRequirement(
                id="GDPR-Art.20",
                framework=ComplianceFramework.GDPR,
                title="Right to data portability",
                description="Data subject has right to receive personal data in portable format",
                category="Data Rights",
                required_patterns=[
                    r'export.*data|download.*data|data.*export',
                    r'json|csv|xml',
                ],
                forbidden_patterns=[],
                severity="medium"
            ),
            ComplianceRequirement(
                id="GDPR-Art.25",
                framework=ComplianceFramework.GDPR,
                title="Data protection by design",
                description="Implement data protection principles in design",
                category="Privacy by Design",
                required_patterns=[
                    r'consent|privacy|data.*protection',
                    r'minimal.*data|data.*minimization',
                ],
                forbidden_patterns=[],
                severity="medium"
            ),
            ComplianceRequirement(
                id="GDPR-Art.30",
                framework=ComplianceFramework.GDPR,
                title="Records of processing activities",
                description="Maintain records of processing activities",
                category="Documentation",
                required_patterns=[
                    r'audit.*log|processing.*record|activity.*log',
                ],
                forbidden_patterns=[],
                severity="medium"
            ),
            ComplianceRequirement(
                id="GDPR-Art.33",
                framework=ComplianceFramework.GDPR,
                title="Notification of data breach",
                description="Notify supervisory authority of personal data breach",
                category="Incident Response",
                required_patterns=[
                    r'breach.*notif|incident.*report|security.*alert',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
        ]


class PCIDSSRuleSet(ComplianceRuleSet):
    """
    PCI-DSS (Payment Card Industry) compliance rules.

    Payment Card Industry Data Security Standard.
    """

    def get_framework(self) -> ComplianceFramework:
        return ComplianceFramework.PCI_DSS

    def get_requirements(self) -> List[ComplianceRequirement]:
        return [
            ComplianceRequirement(
                id="PCI-DSS-3.4",
                framework=ComplianceFramework.PCI_DSS,
                title="Render PAN unreadable",
                description="Render PAN unreadable anywhere it is stored",
                category="Data Protection",
                required_patterns=[
                    r'encrypt|mask|truncate|hash',
                    r'card.*number|pan|credit.*card',
                ],
                forbidden_patterns=[
                    r'card_number\s*=\s*["\'][0-9]{13,19}["\']',  # Hardcoded card numbers
                ],
                severity="critical"
            ),
            ComplianceRequirement(
                id="PCI-DSS-4.1",
                framework=ComplianceFramework.PCI_DSS,
                title="Use strong cryptography",
                description="Use strong cryptography and security protocols during transmission",
                category="Encryption",
                required_patterns=[
                    r'ssl|tls|https',
                    r'AES.*256|RSA.*2048',
                ],
                forbidden_patterns=[
                    r'ssl.*v2|ssl.*v3|tls.*1\.0',  # Deprecated protocols
                ],
                severity="critical"
            ),
            ComplianceRequirement(
                id="PCI-DSS-6.5",
                framework=ComplianceFramework.PCI_DSS,
                title="Secure coding",
                description="Develop applications based on secure coding guidelines",
                category="Secure Development",
                required_patterns=[
                    r'sanitize|escape|validate.*input',
                    r'parameterized|prepared.*statement',
                ],
                forbidden_patterns=[
                    r'eval\(|exec\(|os\.system',  # Dangerous functions
                ],
                severity="high"
            ),
            ComplianceRequirement(
                id="PCI-DSS-8.2.1",
                framework=ComplianceFramework.PCI_DSS,
                title="Strong authentication",
                description="Use strong authentication for administrative access",
                category="Access Control",
                required_patterns=[
                    r'mfa|two_factor|2fa',
                    r'password.*policy|min.*length|complexity',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
            ComplianceRequirement(
                id="PCI-DSS-10.2",
                framework=ComplianceFramework.PCI_DSS,
                title="Audit trails",
                description="Implement automated audit trails for system components",
                category="Audit",
                required_patterns=[
                    r'audit.*log|access.*log|security.*log',
                    r'logger\.|logging\.',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
        ]


class ComplianceChecker:
    """
    Pluggable compliance checker supporting multiple frameworks.

    Usage:
        checker = ComplianceChecker()
        checker.add_framework(ComplianceFramework.NEN7510)
        checker.add_framework(ComplianceFramework.ISO27001)
        report = await checker.check_compliance(files)
    """

    FRAMEWORK_RULESETS = {
        ComplianceFramework.NEN7510: NEN7510RuleSet,
        ComplianceFramework.ISO27001: ISO27001RuleSet,
        ComplianceFramework.HIPAA: HIPAARuleSet,
        ComplianceFramework.SOC2: SOC2RuleSet,
        ComplianceFramework.GDPR: GDPRRuleSet,
        ComplianceFramework.PCI_DSS: PCIDSSRuleSet,
    }

    def __init__(self):
        self.active_frameworks: List[ComplianceFramework] = []
        self.rulesets: List[ComplianceRuleSet] = []

    def add_framework(self, framework: ComplianceFramework):
        """Add a compliance framework to check."""
        if framework not in self.active_frameworks:
            self.active_frameworks.append(framework)
            ruleset_class = self.FRAMEWORK_RULESETS.get(framework)
            if ruleset_class:
                self.rulesets.append(ruleset_class())

    def remove_framework(self, framework: ComplianceFramework):
        """Remove a compliance framework."""
        if framework in self.active_frameworks:
            self.active_frameworks.remove(framework)
            self.rulesets = [rs for rs in self.rulesets if rs.get_framework() != framework]

    def set_frameworks_from_project(self, project_settings: Dict):
        """Configure frameworks from project settings."""
        self.active_frameworks.clear()
        self.rulesets.clear()

        framework_names = project_settings.get("compliance_frameworks", [])
        for name in framework_names:
            try:
                framework = ComplianceFramework(name)
                self.add_framework(framework)
            except ValueError:
                logger.warning(f"Unknown compliance framework: {name}")

    def get_all_requirements(self) -> List[ComplianceRequirement]:
        """Get all requirements from active frameworks."""
        requirements = []
        for ruleset in self.rulesets:
            requirements.extend(ruleset.get_requirements())
        return requirements

    async def check_compliance(self,
                                files: Dict[str, str],
                                nfr_detections: Optional[List['NFRDetection']] = None) -> ComplianceReport:
        """
        Check compliance across all active frameworks.

        Args:
            files: Dict mapping file paths to source code content
            nfr_detections: Optional NFR detections to use for compliance mapping

        Returns:
            ComplianceReport with all violations and passed requirements
        """
        all_violations = []
        passed = []

        # Combine all sources for project-wide searching
        combined_source = "\n\n".join(f"# {path}\n{content}" for path, content in files.items())

        for ruleset in self.rulesets:
            for requirement in ruleset.get_requirements():
                violations = self._check_requirement(requirement, files, combined_source)

                if violations:
                    all_violations.extend(violations)
                else:
                    passed.append(requirement.id)

        # Organize by framework and severity
        by_framework: Dict[str, Dict] = {}
        by_severity: Dict[str, List[ComplianceViolation]] = {"critical": [], "high": [], "medium": [], "low": []}

        for violation in all_violations:
            fw = violation.requirement.framework.value
            by_framework.setdefault(fw, {"violations": [], "passed": []})["violations"].append(violation)
            by_severity.setdefault(violation.requirement.severity, []).append(violation)

        for req_id in passed:
            # Find framework for passed requirement
            for ruleset in self.rulesets:
                for req in ruleset.get_requirements():
                    if req.id == req_id:
                        fw = req.framework.value
                        by_framework.setdefault(fw, {"violations": [], "passed": []})["passed"].append(req_id)

        # Calculate compliance score
        total_requirements = sum(len(rs.get_requirements()) for rs in self.rulesets)
        if total_requirements > 0:
            score = len(passed) / total_requirements
        else:
            score = 1.0

        return ComplianceReport(
            frameworks_checked=self.active_frameworks.copy(),
            violations=all_violations,
            passed_requirements=passed,
            compliance_score=score,
            by_framework=by_framework,
            by_severity=by_severity
        )

    def _check_requirement(self,
                           requirement: ComplianceRequirement,
                           files: Dict[str, str],
                           combined_source: str) -> List[ComplianceViolation]:
        """Check a single compliance requirement."""
        violations = []

        # Check required patterns (at least one should be present)
        if requirement.required_patterns:
            found_required = False
            for pattern in requirement.required_patterns:
                if re.search(pattern, combined_source, re.IGNORECASE):
                    found_required = True
                    break

            if not found_required:
                violations.append(ComplianceViolation(
                    requirement=requirement,
                    violation_type="missing",
                    file_path="(project-wide)",
                    line_number=None,
                    code_snippet=None,
                    remediation=f"Required pattern not found. Add one of: {', '.join(requirement.required_patterns[:3])}"
                ))

        # Check forbidden patterns (none should be present)
        for pattern in requirement.forbidden_patterns:
            for file_path, source in files.items():
                for match in re.finditer(pattern, source, re.IGNORECASE):
                    line_num = source[:match.start()].count('\n') + 1
                    lines = source.split('\n')
                    snippet = lines[line_num - 1] if line_num <= len(lines) else ""

                    violations.append(ComplianceViolation(
                        requirement=requirement,
                        violation_type="forbidden",
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=snippet[:200],
                        remediation=f"Forbidden pattern detected. Remove or refactor: {match.group(0)[:50]}"
                    ))

        return violations

    def get_summary(self, report: ComplianceReport) -> Dict:
        """Get summary statistics from compliance report."""
        return {
            "frameworks_checked": [fw.value for fw in report.frameworks_checked],
            "compliance_score": round(report.compliance_score, 2),
            "total_requirements": len(report.passed_requirements) + len(report.violations),
            "passed_count": len(report.passed_requirements),
            "violation_count": len(report.violations),
            "critical_violations": len(report.by_severity.get("critical", [])),
            "high_violations": len(report.by_severity.get("high", [])),
            "by_framework": {
                fw: {
                    "violations": len(data.get("violations", [])),
                    "passed": len(data.get("passed", []))
                }
                for fw, data in report.by_framework.items()
            }
        }
