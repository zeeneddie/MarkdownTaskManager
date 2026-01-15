"""
Security Scanner Adapters.

Adapters for external CLI tools and custom scanners.
All adapters implement the BaseScanner interface and output
unified SecurityFinding models.
"""

from .base import (
    BaseScanner,
    ExternalCLIScanner,
    CustomPatternScanner,
    ScannerNotAvailableError,
    ScannerExecutionError,
)

from .opengrep_adapter import (
    OpenGrepAdapter,
    create_opengrep_adapter,
)

from .bandit_adapter import (
    BanditAdapter,
    create_bandit_adapter,
)

from .gosec_adapter import (
    GosecAdapter,
    create_gosec_adapter,
)

from .trivy_adapter import (
    TrivyAdapter,
    create_trivy_adapter,
)

from .asp_scanner import (
    ClassicASPScanner,
    create_asp_scanner,
)

from .secret_scanner import (
    SecretScanner,
    SecretPattern,
    SecretType,
    FalsePositiveFilter,
    EntropyAnalyzer,
)

from .owasp_scanner import (
    OWASPScanner,
    OWASPCategoryInfo,
    OWASPCoverageReport,
    OWASP_CATEGORY_INFO,
    BUILTIN_OWASP_PATTERNS,
    create_owasp_scanner,
)

from .cve_scanner import (
    CVEScanner,
    CVEDatabaseService,
    CVERecord,
    CVSSScore,
    DependencyInfo,
    VulnerabilityMatch,
    CVECoverageReport,
    create_cve_scanner,
)


__all__ = [
    # Base classes
    "BaseScanner",
    "ExternalCLIScanner",
    "CustomPatternScanner",
    "ScannerNotAvailableError",
    "ScannerExecutionError",
    # OpenGrep (30+ languages)
    "OpenGrepAdapter",
    "create_opengrep_adapter",
    # Bandit (Python)
    "BanditAdapter",
    "create_bandit_adapter",
    # Gosec (Go)
    "GosecAdapter",
    "create_gosec_adapter",
    # Trivy (Dependencies)
    "TrivyAdapter",
    "create_trivy_adapter",
    # Custom ASP
    "ClassicASPScanner",
    "create_asp_scanner",
    # Secret Detection (K3 - Fase 24)
    "SecretScanner",
    "SecretPattern",
    "SecretType",
    "FalsePositiveFilter",
    "EntropyAnalyzer",
    # OWASP Top 10 (K1 - Fase 24)
    "OWASPScanner",
    "OWASPCategoryInfo",
    "OWASPCoverageReport",
    "OWASP_CATEGORY_INFO",
    "BUILTIN_OWASP_PATTERNS",
    "create_owasp_scanner",
    # CVE Database (K2 - Fase 24)
    "CVEScanner",
    "CVEDatabaseService",
    "CVERecord",
    "CVSSScore",
    "DependencyInfo",
    "VulnerabilityMatch",
    "CVECoverageReport",
    "create_cve_scanner",
]
