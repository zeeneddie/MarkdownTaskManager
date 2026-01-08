# Industry Standard NFR Templates - Week 102: NFR Quick Wins
# NFR-QW-3: Templates for ISO 25010, NEN7510, HIPAA, PCI-DSS

"""
Industry Standard NFR Templates

Pre-built NFR templates based on industry standards:
- ISO 25010: Software Quality Model
- NEN 7510: Healthcare Information Security (Dutch/EU)
- HIPAA: Health Insurance Portability and Accountability
- PCI-DSS: Payment Card Industry Data Security
- SOC 2: Service Organization Controls
- GDPR: General Data Protection Regulation

Each template provides:
- Standard reference
- Default metric thresholds
- Test approach
- Compliance notes
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class IndustryStandard(Enum):
    """Supported industry standards."""
    ISO_25010 = "iso_25010"      # Software Quality
    NEN_7510 = "nen_7510"        # Dutch Healthcare Security
    HIPAA = "hipaa"              # US Healthcare Privacy
    PCI_DSS = "pci_dss"          # Payment Security
    SOC_2 = "soc_2"              # Service Controls
    GDPR = "gdpr"                # EU Data Protection
    ISO_27001 = "iso_27001"      # Information Security
    WCAG = "wcag"                # Web Accessibility


class NFRDomain(Enum):
    """NFR domains based on ISO 25010."""
    FUNCTIONAL_SUITABILITY = "functional_suitability"
    PERFORMANCE_EFFICIENCY = "performance_efficiency"
    COMPATIBILITY = "compatibility"
    USABILITY = "usability"
    RELIABILITY = "reliability"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    PORTABILITY = "portability"


class ComplianceLevel(Enum):
    """Compliance level requirements."""
    MANDATORY = "mandatory"     # Must have for compliance
    RECOMMENDED = "recommended" # Should have
    OPTIONAL = "optional"       # Nice to have


@dataclass
class NFRTemplate:
    """A template for a specific NFR."""
    id: str
    name: str
    description: str
    domain: NFRDomain
    standard: IndustryStandard
    standard_reference: str     # e.g., "ISO 25010 - 4.2.1"
    compliance_level: ComplianceLevel
    default_metric: str         # Default metric specification
    metric_unit: str
    test_approach: str
    implementation_guidance: str
    examples: List[str] = field(default_factory=list)
    related_templates: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "domain": self.domain.value,
            "standard": self.standard.value,
            "standard_reference": self.standard_reference,
            "compliance_level": self.compliance_level.value,
            "default_metric": self.default_metric,
            "metric_unit": self.metric_unit,
            "test_approach": self.test_approach,
            "implementation_guidance": self.implementation_guidance,
            "examples": self.examples,
            "tags": self.tags
        }

    def to_requirement(self, custom_metric: Optional[str] = None) -> str:
        """Generate a requirement statement from template."""
        metric = custom_metric or self.default_metric
        return f"{self.name}: {self.description} ({metric} {self.metric_unit})"


@dataclass
class TemplateSet:
    """A collection of related NFR templates."""
    standard: IndustryStandard
    name: str
    description: str
    version: str
    templates: List[NFRTemplate]
    applicability: str
    certification_notes: str

    def get_mandatory(self) -> List[NFRTemplate]:
        """Get all mandatory templates."""
        return [t for t in self.templates if t.compliance_level == ComplianceLevel.MANDATORY]

    def get_by_domain(self, domain: NFRDomain) -> List[NFRTemplate]:
        """Get templates for a specific domain."""
        return [t for t in self.templates if t.domain == domain]

    def to_dict(self) -> dict:
        return {
            "standard": self.standard.value,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "template_count": len(self.templates),
            "mandatory_count": len(self.get_mandatory()),
            "templates": [t.to_dict() for t in self.templates],
            "applicability": self.applicability
        }


# =============================================================================
# ISO 25010 Templates (Software Quality Model)
# =============================================================================

ISO_25010_TEMPLATES = TemplateSet(
    standard=IndustryStandard.ISO_25010,
    name="ISO/IEC 25010:2011 Software Quality",
    description="System and software quality models",
    version="2011",
    applicability="All software systems",
    certification_notes="Self-assessment; no formal certification required",
    templates=[
        # Performance Efficiency
        NFRTemplate(
            id="iso25010-pe-01",
            name="Response Time",
            description="Time to respond to user actions under normal load",
            domain=NFRDomain.PERFORMANCE_EFFICIENCY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.2.1 Time Behaviour",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="< 200",
            metric_unit="ms",
            test_approach="Load testing with realistic user scenarios using k6 or JMeter",
            implementation_guidance="Optimize database queries, implement caching, use CDN for static assets",
            examples=[
                "API endpoint response time < 200ms for 95th percentile",
                "Page load time < 3 seconds on 3G connection"
            ],
            tags=["performance", "response-time", "latency"]
        ),
        NFRTemplate(
            id="iso25010-pe-02",
            name="Throughput",
            description="Number of transactions processed per time unit",
            domain=NFRDomain.PERFORMANCE_EFFICIENCY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.2.1 Time Behaviour",
            compliance_level=ComplianceLevel.RECOMMENDED,
            default_metric="> 1000",
            metric_unit="requests/second",
            test_approach="Stress testing to find throughput limits",
            implementation_guidance="Horizontal scaling, async processing, connection pooling",
            examples=["System handles 1000 concurrent API requests"],
            tags=["performance", "throughput", "scalability"]
        ),
        NFRTemplate(
            id="iso25010-pe-03",
            name="Resource Utilization",
            description="CPU and memory usage under normal operation",
            domain=NFRDomain.PERFORMANCE_EFFICIENCY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.2.2 Resource Utilization",
            compliance_level=ComplianceLevel.RECOMMENDED,
            default_metric="< 70",
            metric_unit="% average",
            test_approach="Monitor resource usage during load tests",
            implementation_guidance="Profile and optimize hot paths, implement memory management",
            examples=["CPU usage < 70% at peak load"],
            tags=["performance", "resources", "efficiency"]
        ),
        # Reliability
        NFRTemplate(
            id="iso25010-rel-01",
            name="Availability",
            description="System uptime percentage",
            domain=NFRDomain.RELIABILITY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.3.2 Availability",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric=">= 99.9",
            metric_unit="%",
            test_approach="Uptime monitoring with Pingdom or UptimeRobot",
            implementation_guidance="Redundancy, failover, health checks, auto-recovery",
            examples=["99.9% uptime (8.76 hours downtime/year)"],
            tags=["reliability", "availability", "uptime"]
        ),
        NFRTemplate(
            id="iso25010-rel-02",
            name="Fault Tolerance",
            description="System continues operating despite failures",
            domain=NFRDomain.RELIABILITY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.3.3 Fault Tolerance",
            compliance_level=ComplianceLevel.RECOMMENDED,
            default_metric="< 5",
            metric_unit="seconds recovery",
            test_approach="Chaos engineering with failure injection",
            implementation_guidance="Circuit breakers, retry logic, graceful degradation",
            examples=["Automatic failover within 5 seconds"],
            tags=["reliability", "fault-tolerance", "resilience"]
        ),
        NFRTemplate(
            id="iso25010-rel-03",
            name="Recoverability",
            description="Recovery time after system failure",
            domain=NFRDomain.RELIABILITY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.3.4 Recoverability",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="< 4",
            metric_unit="hours RTO",
            test_approach="Disaster recovery testing",
            implementation_guidance="Automated backups, documented recovery procedures",
            examples=["RTO < 4 hours, RPO < 1 hour"],
            tags=["reliability", "recovery", "disaster-recovery"]
        ),
        # Security
        NFRTemplate(
            id="iso25010-sec-01",
            name="Confidentiality",
            description="Data protection against unauthorized access",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.4.1 Confidentiality",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="AES-256",
            metric_unit="encryption",
            test_approach="Security audit, penetration testing",
            implementation_guidance="Encryption at rest and in transit, access controls",
            examples=["All PII encrypted with AES-256"],
            tags=["security", "encryption", "confidentiality"]
        ),
        NFRTemplate(
            id="iso25010-sec-02",
            name="Authentication",
            description="User identity verification",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.4.3 Authenticity",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="MFA required",
            metric_unit="for sensitive operations",
            test_approach="Authentication testing, session management review",
            implementation_guidance="OAuth 2.0/OIDC, MFA, secure session handling",
            examples=["MFA required for admin access"],
            tags=["security", "authentication", "mfa"]
        ),
        # Usability
        NFRTemplate(
            id="iso25010-usa-01",
            name="Learnability",
            description="Time for new users to become productive",
            domain=NFRDomain.USABILITY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.5.1 Learnability",
            compliance_level=ComplianceLevel.RECOMMENDED,
            default_metric="< 30",
            metric_unit="minutes to first task",
            test_approach="User testing with new users",
            implementation_guidance="Onboarding flow, tooltips, documentation",
            examples=["New users complete first task within 30 minutes"],
            tags=["usability", "learnability", "onboarding"]
        ),
        NFRTemplate(
            id="iso25010-usa-02",
            name="Accessibility",
            description="WCAG compliance level",
            domain=NFRDomain.USABILITY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.5.5 Accessibility",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="WCAG 2.1",
            metric_unit="Level AA",
            test_approach="Automated accessibility testing (axe, WAVE), manual testing",
            implementation_guidance="Semantic HTML, ARIA labels, keyboard navigation, color contrast",
            examples=["All public pages meet WCAG 2.1 AA"],
            tags=["usability", "accessibility", "wcag"]
        ),
        # Maintainability
        NFRTemplate(
            id="iso25010-mnt-01",
            name="Code Coverage",
            description="Percentage of code covered by tests",
            domain=NFRDomain.MAINTAINABILITY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.7.2 Testability",
            compliance_level=ComplianceLevel.RECOMMENDED,
            default_metric=">= 80",
            metric_unit="%",
            test_approach="Code coverage tools (Jest, pytest-cov)",
            implementation_guidance="Unit tests for business logic, integration tests for APIs",
            examples=["80% code coverage for core modules"],
            tags=["maintainability", "testing", "coverage"]
        ),
        NFRTemplate(
            id="iso25010-mnt-02",
            name="Documentation",
            description="API and code documentation completeness",
            domain=NFRDomain.MAINTAINABILITY,
            standard=IndustryStandard.ISO_25010,
            standard_reference="ISO 25010 - 4.7.1 Modularity",
            compliance_level=ComplianceLevel.RECOMMENDED,
            default_metric="100",
            metric_unit="% public API documented",
            test_approach="Documentation review, automated doc generation",
            implementation_guidance="OpenAPI specs, JSDoc/docstrings, architecture docs",
            examples=["All public APIs have OpenAPI documentation"],
            tags=["maintainability", "documentation", "api"]
        ),
    ]
)

# =============================================================================
# HIPAA Templates (Healthcare)
# =============================================================================

HIPAA_TEMPLATES = TemplateSet(
    standard=IndustryStandard.HIPAA,
    name="HIPAA Security Rule",
    description="Health Insurance Portability and Accountability Act - Security Standards",
    version="2013 Omnibus Rule",
    applicability="Healthcare providers, health plans, clearinghouses, business associates",
    certification_notes="No formal certification; compliance verified through audits",
    templates=[
        NFRTemplate(
            id="hipaa-sec-01",
            name="PHI Encryption at Rest",
            description="All Protected Health Information must be encrypted when stored",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.HIPAA,
            standard_reference="45 CFR 164.312(a)(2)(iv)",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="AES-256",
            metric_unit="encryption",
            test_approach="Security audit verifying encryption of all PHI storage",
            implementation_guidance="Use AES-256 for databases, file storage; implement key management",
            examples=["Database encryption with AES-256", "Encrypted backups"],
            tags=["hipaa", "encryption", "phi", "mandatory"]
        ),
        NFRTemplate(
            id="hipaa-sec-02",
            name="PHI Encryption in Transit",
            description="All PHI must be encrypted during transmission",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.HIPAA,
            standard_reference="45 CFR 164.312(e)(1)",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="TLS 1.2+",
            metric_unit="protocol",
            test_approach="SSL/TLS testing, API security scanning",
            implementation_guidance="TLS 1.2 minimum, TLS 1.3 preferred; disable weak ciphers",
            examples=["HTTPS only with TLS 1.2+", "Encrypted API communications"],
            tags=["hipaa", "encryption", "tls", "mandatory"]
        ),
        NFRTemplate(
            id="hipaa-sec-03",
            name="Access Control",
            description="Unique user identification and role-based access",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.HIPAA,
            standard_reference="45 CFR 164.312(a)(2)(i)",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="RBAC",
            metric_unit="with audit logging",
            test_approach="Access control testing, privilege escalation testing",
            implementation_guidance="Implement RBAC, unique user IDs, minimum necessary access",
            examples=["Role-based access to patient records", "Unique user IDs for all staff"],
            tags=["hipaa", "access-control", "rbac", "mandatory"]
        ),
        NFRTemplate(
            id="hipaa-sec-04",
            name="Audit Controls",
            description="Record and examine activity in PHI systems",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.HIPAA,
            standard_reference="45 CFR 164.312(b)",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric=">= 6",
            metric_unit="years retention",
            test_approach="Audit log review, log integrity verification",
            implementation_guidance="Comprehensive logging, tamper-proof storage, regular review",
            examples=["All PHI access logged", "Audit logs retained 6 years"],
            tags=["hipaa", "audit", "logging", "mandatory"]
        ),
        NFRTemplate(
            id="hipaa-sec-05",
            name="Automatic Logoff",
            description="Automatic session termination after inactivity",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.HIPAA,
            standard_reference="45 CFR 164.312(a)(2)(iii)",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="<= 15",
            metric_unit="minutes",
            test_approach="Session timeout testing",
            implementation_guidance="Implement idle timeout, secure session invalidation",
            examples=["Auto-logout after 15 minutes of inactivity"],
            tags=["hipaa", "session", "timeout", "mandatory"]
        ),
        NFRTemplate(
            id="hipaa-sec-06",
            name="Emergency Access",
            description="Procedures for accessing PHI during emergencies",
            domain=NFRDomain.RELIABILITY,
            standard=IndustryStandard.HIPAA,
            standard_reference="45 CFR 164.312(a)(2)(ii)",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="Documented",
            metric_unit="break-glass procedure",
            test_approach="Emergency access drill testing",
            implementation_guidance="Break-glass procedures, emergency access logging",
            examples=["Documented emergency access procedure", "Break-glass access with audit"],
            tags=["hipaa", "emergency", "access", "mandatory"]
        ),
        NFRTemplate(
            id="hipaa-sec-07",
            name="Data Backup",
            description="Retrievable exact copy of PHI",
            domain=NFRDomain.RELIABILITY,
            standard=IndustryStandard.HIPAA,
            standard_reference="45 CFR 164.308(a)(7)(ii)(A)",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="Daily",
            metric_unit="encrypted backups",
            test_approach="Backup restoration testing",
            implementation_guidance="Daily encrypted backups, off-site storage, restore testing",
            examples=["Daily encrypted backups", "Monthly restore testing"],
            tags=["hipaa", "backup", "recovery", "mandatory"]
        ),
    ]
)

# =============================================================================
# PCI-DSS Templates (Payment Security)
# =============================================================================

PCI_DSS_TEMPLATES = TemplateSet(
    standard=IndustryStandard.PCI_DSS,
    name="PCI DSS v4.0",
    description="Payment Card Industry Data Security Standard",
    version="4.0 (March 2024)",
    applicability="Any organization that stores, processes, or transmits cardholder data",
    certification_notes="Annual assessment required; SAQ or QSA audit depending on volume",
    templates=[
        NFRTemplate(
            id="pci-sec-01",
            name="Cardholder Data Encryption",
            description="Protect stored cardholder data with strong encryption",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.PCI_DSS,
            standard_reference="PCI DSS 3.5",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="AES-256",
            metric_unit="encryption",
            test_approach="Encryption verification, key management audit",
            implementation_guidance="AES-256, secure key management, minimize stored data",
            examples=["PANs encrypted with AES-256", "CVV never stored"],
            tags=["pci", "encryption", "cardholder", "mandatory"]
        ),
        NFRTemplate(
            id="pci-sec-02",
            name="Transmission Encryption",
            description="Encrypt cardholder data during transmission",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.PCI_DSS,
            standard_reference="PCI DSS 4.1",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="TLS 1.2+",
            metric_unit="protocol",
            test_approach="SSL/TLS testing, network scanning",
            implementation_guidance="TLS 1.2+, strong cipher suites, certificate validation",
            examples=["All payment API calls over TLS 1.2+"],
            tags=["pci", "encryption", "tls", "mandatory"]
        ),
        NFRTemplate(
            id="pci-sec-03",
            name="Access Restriction",
            description="Restrict access to cardholder data by business need",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.PCI_DSS,
            standard_reference="PCI DSS 7.1",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="Need-to-know",
            metric_unit="access only",
            test_approach="Access control review, privilege audit",
            implementation_guidance="Least privilege, role-based access, regular review",
            examples=["Only payment team has PAN access", "Quarterly access review"],
            tags=["pci", "access-control", "least-privilege", "mandatory"]
        ),
        NFRTemplate(
            id="pci-sec-04",
            name="Authentication",
            description="Unique ID and strong authentication for system access",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.PCI_DSS,
            standard_reference="PCI DSS 8.3",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="MFA required",
            metric_unit="for CDE access",
            test_approach="Authentication testing, MFA verification",
            implementation_guidance="MFA for all CDE access, strong password policy",
            examples=["MFA for admin and CDE access", "12+ character passwords"],
            tags=["pci", "authentication", "mfa", "mandatory"]
        ),
        NFRTemplate(
            id="pci-sec-05",
            name="Audit Logging",
            description="Track all access to cardholder data",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.PCI_DSS,
            standard_reference="PCI DSS 10.1",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric=">= 1",
            metric_unit="year retention",
            test_approach="Log review, integrity verification",
            implementation_guidance="Log all access, centralized logging, tamper protection",
            examples=["All CDE access logged", "Logs retained 1 year minimum"],
            tags=["pci", "audit", "logging", "mandatory"]
        ),
        NFRTemplate(
            id="pci-sec-06",
            name="Vulnerability Management",
            description="Regular vulnerability scanning and patching",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.PCI_DSS,
            standard_reference="PCI DSS 6.3, 11.3",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="Quarterly",
            metric_unit="external scans",
            test_approach="ASV scans, penetration testing",
            implementation_guidance="Regular patching, quarterly ASV scans, annual pentest",
            examples=["Quarterly ASV scans", "Annual penetration test"],
            tags=["pci", "vulnerability", "scanning", "mandatory"]
        ),
        NFRTemplate(
            id="pci-sec-07",
            name="PAN Masking",
            description="Mask PAN when displayed",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.PCI_DSS,
            standard_reference="PCI DSS 3.4",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="First 6 / Last 4",
            metric_unit="digits visible max",
            test_approach="UI testing, log review for masked PANs",
            implementation_guidance="Mask middle digits, never log full PAN",
            examples=["Display as 4111 **** **** 1111", "No full PAN in logs"],
            tags=["pci", "masking", "pan", "mandatory"]
        ),
    ]
)

# =============================================================================
# NEN 7510 Templates (Dutch Healthcare Security)
# =============================================================================

NEN_7510_TEMPLATES = TemplateSet(
    standard=IndustryStandard.NEN_7510,
    name="NEN 7510:2017",
    description="Information security management in healthcare (Dutch standard)",
    version="2017",
    applicability="Dutch healthcare organizations and their suppliers",
    certification_notes="Certification available via accredited bodies; often required for Dutch healthcare contracts",
    templates=[
        NFRTemplate(
            id="nen7510-sec-01",
            name="Patient Data Classification",
            description="Classification and handling of patient data",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.NEN_7510,
            standard_reference="NEN 7510 - 8.2.1",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="Classified",
            metric_unit="by sensitivity",
            test_approach="Data classification audit",
            implementation_guidance="Implement data classification scheme, handling procedures",
            examples=["Patient data classified as 'confidential'", "Clear handling guidelines"],
            tags=["nen7510", "classification", "patient-data", "mandatory"]
        ),
        NFRTemplate(
            id="nen7510-sec-02",
            name="Access Management",
            description="Role-based access to patient information",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.NEN_7510,
            standard_reference="NEN 7510 - 9.2",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="RBAC",
            metric_unit="with treatment relationship",
            test_approach="Access control testing, role audit",
            implementation_guidance="RBAC based on treatment relationship, regular review",
            examples=["Access based on treatment relationship", "Quarterly access review"],
            tags=["nen7510", "access-control", "rbac", "mandatory"]
        ),
        NFRTemplate(
            id="nen7510-sec-03",
            name="Logging and Monitoring",
            description="Comprehensive logging of patient data access",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.NEN_7510,
            standard_reference="NEN 7510 - 12.4",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric=">= 2",
            metric_unit="years retention",
            test_approach="Log audit, patient access report generation",
            implementation_guidance="Log all patient data access, enable patient access reports",
            examples=["All EPD access logged", "Patient can request access report"],
            tags=["nen7510", "logging", "audit", "mandatory"]
        ),
        NFRTemplate(
            id="nen7510-sec-04",
            name="Encryption",
            description="Encryption of patient data at rest and in transit",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.NEN_7510,
            standard_reference="NEN 7510 - 10.1.1",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="AES-256 / TLS 1.2+",
            metric_unit="encryption",
            test_approach="Encryption verification, TLS testing",
            implementation_guidance="AES-256 at rest, TLS 1.2+ in transit",
            examples=["EPD database encrypted", "All API calls over TLS 1.2"],
            tags=["nen7510", "encryption", "tls", "mandatory"]
        ),
        NFRTemplate(
            id="nen7510-sec-05",
            name="Business Continuity",
            description="Continuity of patient care systems",
            domain=NFRDomain.RELIABILITY,
            standard=IndustryStandard.NEN_7510,
            standard_reference="NEN 7510 - 17.1",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric=">= 99.5",
            metric_unit="% availability",
            test_approach="BC/DR testing, failover testing",
            implementation_guidance="Redundancy, documented recovery procedures, regular testing",
            examples=["99.5% uptime SLA", "Annual BC/DR test"],
            tags=["nen7510", "availability", "continuity", "mandatory"]
        ),
        NFRTemplate(
            id="nen7510-sec-06",
            name="Incident Management",
            description="Security incident response and reporting",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.NEN_7510,
            standard_reference="NEN 7510 - 16.1",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="< 72",
            metric_unit="hours to report breach",
            test_approach="Incident response drill",
            implementation_guidance="Incident response plan, AP notification procedures",
            examples=["Data breach reported within 72 hours", "Annual incident drill"],
            tags=["nen7510", "incident", "breach", "mandatory"]
        ),
    ]
)

# =============================================================================
# GDPR Templates (EU Data Protection)
# =============================================================================

GDPR_TEMPLATES = TemplateSet(
    standard=IndustryStandard.GDPR,
    name="GDPR",
    description="General Data Protection Regulation",
    version="2016/679",
    applicability="Any organization processing EU residents' personal data",
    certification_notes="No formal certification; compliance demonstrated through documentation and audits",
    templates=[
        NFRTemplate(
            id="gdpr-priv-01",
            name="Data Minimization",
            description="Collect only necessary personal data",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.GDPR,
            standard_reference="GDPR Article 5(1)(c)",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="Necessary",
            metric_unit="data only",
            test_approach="Data inventory review, purpose limitation audit",
            implementation_guidance="Document purpose for each data field, remove unnecessary fields",
            examples=["Only collect data required for stated purpose"],
            tags=["gdpr", "privacy", "minimization", "mandatory"]
        ),
        NFRTemplate(
            id="gdpr-priv-02",
            name="Right to Access",
            description="Provide personal data to users on request",
            domain=NFRDomain.USABILITY,
            standard=IndustryStandard.GDPR,
            standard_reference="GDPR Article 15",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="< 30",
            metric_unit="days response",
            test_approach="Subject access request testing",
            implementation_guidance="Self-service data export, SAR processing workflow",
            examples=["User can export their data", "SAR completed within 30 days"],
            tags=["gdpr", "privacy", "access", "mandatory"]
        ),
        NFRTemplate(
            id="gdpr-priv-03",
            name="Right to Erasure",
            description="Delete personal data on request",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.GDPR,
            standard_reference="GDPR Article 17",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="< 30",
            metric_unit="days completion",
            test_approach="Deletion request testing, data verification",
            implementation_guidance="Data deletion workflow, backup handling, verification",
            examples=["Account deletion removes all personal data", "Backups purged within 90 days"],
            tags=["gdpr", "privacy", "erasure", "mandatory"]
        ),
        NFRTemplate(
            id="gdpr-priv-04",
            name="Consent Management",
            description="Obtain and manage user consent",
            domain=NFRDomain.USABILITY,
            standard=IndustryStandard.GDPR,
            standard_reference="GDPR Article 7",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="Explicit",
            metric_unit="opt-in consent",
            test_approach="Consent flow testing, preference center review",
            implementation_guidance="Granular consent options, easy withdrawal, consent records",
            examples=["Cookie consent banner", "Marketing opt-in separate from account creation"],
            tags=["gdpr", "privacy", "consent", "mandatory"]
        ),
        NFRTemplate(
            id="gdpr-priv-05",
            name="Breach Notification",
            description="Notify authorities and users of data breaches",
            domain=NFRDomain.SECURITY,
            standard=IndustryStandard.GDPR,
            standard_reference="GDPR Articles 33, 34",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="< 72",
            metric_unit="hours to authority",
            test_approach="Breach simulation, notification process testing",
            implementation_guidance="Incident response plan, authority notification template",
            examples=["Notify DPA within 72 hours", "User notification for high-risk breaches"],
            tags=["gdpr", "privacy", "breach", "mandatory"]
        ),
        NFRTemplate(
            id="gdpr-priv-06",
            name="Data Portability",
            description="Provide data in machine-readable format",
            domain=NFRDomain.PORTABILITY,
            standard=IndustryStandard.GDPR,
            standard_reference="GDPR Article 20",
            compliance_level=ComplianceLevel.MANDATORY,
            default_metric="JSON/CSV",
            metric_unit="export format",
            test_approach="Data export testing, format verification",
            implementation_guidance="Standard export formats, complete data coverage",
            examples=["Export user data as JSON", "Include all user-provided data"],
            tags=["gdpr", "privacy", "portability", "mandatory"]
        ),
    ]
)

# =============================================================================
# Template Loader
# =============================================================================

class IndustryNFRTemplateLoader:
    """
    Loads and provides access to industry standard NFR templates.

    Usage:
        loader = IndustryNFRTemplateLoader()

        # Get all HIPAA templates
        hipaa = loader.get_templates(IndustryStandard.HIPAA)
        for template in hipaa.get_mandatory():
            print(template.to_requirement())

        # Get templates for a specific domain
        security_templates = loader.get_templates_by_domain(
            IndustryStandard.PCI_DSS,
            NFRDomain.SECURITY
        )

        # Generate requirements from templates
        requirements = loader.generate_requirements(IndustryStandard.GDPR)
    """

    # All available template sets
    TEMPLATE_SETS = {
        IndustryStandard.ISO_25010: ISO_25010_TEMPLATES,
        IndustryStandard.HIPAA: HIPAA_TEMPLATES,
        IndustryStandard.PCI_DSS: PCI_DSS_TEMPLATES,
        IndustryStandard.NEN_7510: NEN_7510_TEMPLATES,
        IndustryStandard.GDPR: GDPR_TEMPLATES,
    }

    def get_templates(self, standard: IndustryStandard) -> Optional[TemplateSet]:
        """Get all templates for a standard."""
        return self.TEMPLATE_SETS.get(standard)

    def get_all_standards(self) -> List[IndustryStandard]:
        """Get list of all available standards."""
        return list(self.TEMPLATE_SETS.keys())

    def get_templates_by_domain(
        self,
        standard: IndustryStandard,
        domain: NFRDomain
    ) -> List[NFRTemplate]:
        """Get templates for a specific domain within a standard."""
        template_set = self.get_templates(standard)
        if not template_set:
            return []
        return template_set.get_by_domain(domain)

    def get_mandatory_templates(self, standard: IndustryStandard) -> List[NFRTemplate]:
        """Get all mandatory templates for a standard."""
        template_set = self.get_templates(standard)
        if not template_set:
            return []
        return template_set.get_mandatory()

    def generate_requirements(
        self,
        standard: IndustryStandard,
        compliance_level: Optional[ComplianceLevel] = None
    ) -> List[str]:
        """Generate requirement statements from templates."""
        template_set = self.get_templates(standard)
        if not template_set:
            return []

        templates = template_set.templates
        if compliance_level:
            templates = [t for t in templates if t.compliance_level == compliance_level]

        return [t.to_requirement() for t in templates]

    def get_template_by_id(self, template_id: str) -> Optional[NFRTemplate]:
        """Find a template by its ID across all standards."""
        for template_set in self.TEMPLATE_SETS.values():
            for template in template_set.templates:
                if template.id == template_id:
                    return template
        return None

    def get_applicable_standards(self, domains: List[str]) -> List[IndustryStandard]:
        """Suggest applicable standards based on business domains."""
        suggestions = []

        domain_mappings = {
            "healthcare": [IndustryStandard.HIPAA, IndustryStandard.NEN_7510],
            "finance": [IndustryStandard.PCI_DSS],
            "payment": [IndustryStandard.PCI_DSS],
            "eu": [IndustryStandard.GDPR],
            "europe": [IndustryStandard.GDPR],
            "dutch": [IndustryStandard.NEN_7510],
            "netherlands": [IndustryStandard.NEN_7510],
            "software": [IndustryStandard.ISO_25010],
        }

        for domain in domains:
            domain_lower = domain.lower()
            for key, standards in domain_mappings.items():
                if key in domain_lower:
                    suggestions.extend(standards)

        # Always include ISO 25010 as baseline
        if IndustryStandard.ISO_25010 not in suggestions:
            suggestions.append(IndustryStandard.ISO_25010)

        return list(set(suggestions))


# Convenience functions
def get_hipaa_templates() -> List[NFRTemplate]:
    """Get all HIPAA templates."""
    return HIPAA_TEMPLATES.templates


def get_pci_templates() -> List[NFRTemplate]:
    """Get all PCI-DSS templates."""
    return PCI_DSS_TEMPLATES.templates


def get_gdpr_templates() -> List[NFRTemplate]:
    """Get all GDPR templates."""
    return GDPR_TEMPLATES.templates


def get_iso25010_templates() -> List[NFRTemplate]:
    """Get all ISO 25010 templates."""
    return ISO_25010_TEMPLATES.templates


def get_nen7510_templates() -> List[NFRTemplate]:
    """Get all NEN 7510 templates."""
    return NEN_7510_TEMPLATES.templates


def generate_compliance_checklist(standard: IndustryStandard) -> List[Dict[str, Any]]:
    """Generate a compliance checklist for a standard."""
    loader = IndustryNFRTemplateLoader()
    template_set = loader.get_templates(standard)

    if not template_set:
        return []

    return [
        {
            "id": t.id,
            "name": t.name,
            "requirement": t.to_requirement(),
            "compliance_level": t.compliance_level.value,
            "test_approach": t.test_approach,
            "reference": t.standard_reference,
            "compliant": None,  # To be filled during assessment
            "evidence": None,   # To be filled during assessment
        }
        for t in template_set.templates
    ]
