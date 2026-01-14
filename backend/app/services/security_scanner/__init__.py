"""
Security Scanner Service Module.

Fase 31: CWE Top 25 Security Scanner Suite.

A language-agnostic security scanning orchestrator that integrates
multiple open-source scanners with unified SARIF-based output.

Supported Scanners:
- OpenGrep (30+ languages) - LGPL 2.1
- Bandit (Python) - Apache 2.0
- Gosec (Go) - Apache 2.0
- Trivy (Dependencies) - Apache 2.0
- Custom ASP Scanner (Classic ASP/VBScript)

All external tools are fully open source and extensible.
"""

from .models import (
    # SARIF
    SarifLog,
    SarifRun,
    SarifResult,
    SarifLevel,
    # Findings
    Severity,
    FindingStatus,
    ScannerType,
    CWE_TOP_25,
    Location,
    SuggestedFix,
    SecurityFinding,
    ScanResult,
    SecurityReport,
)

from .parsers import (
    SarifParser,
    create_sarif_parser,
)

from .adapters import (
    # Base classes
    BaseScanner,
    ExternalCLIScanner,
    CustomPatternScanner,
    ScannerNotAvailableError,
    ScannerExecutionError,
    # Adapters
    OpenGrepAdapter,
    BanditAdapter,
    GosecAdapter,
    TrivyAdapter,
    ClassicASPScanner,
    # Factories
    create_opengrep_adapter,
    create_bandit_adapter,
    create_gosec_adapter,
    create_trivy_adapter,
    create_asp_scanner,
)

from .orchestrator import (
    SecurityScanOrchestrator,
    create_security_orchestrator,
    EXTENSION_TO_LANGUAGE,
    LANGUAGE_SCANNERS,
)


__all__ = [
    # SARIF models
    "SarifLog",
    "SarifRun",
    "SarifResult",
    "SarifLevel",
    # Finding models
    "Severity",
    "FindingStatus",
    "ScannerType",
    "CWE_TOP_25",
    "Location",
    "SuggestedFix",
    "SecurityFinding",
    "ScanResult",
    "SecurityReport",
    # Parser
    "SarifParser",
    "create_sarif_parser",
    # Base classes
    "BaseScanner",
    "ExternalCLIScanner",
    "CustomPatternScanner",
    "ScannerNotAvailableError",
    "ScannerExecutionError",
    # Adapters
    "OpenGrepAdapter",
    "BanditAdapter",
    "GosecAdapter",
    "TrivyAdapter",
    "ClassicASPScanner",
    # Factories
    "create_opengrep_adapter",
    "create_bandit_adapter",
    "create_gosec_adapter",
    "create_trivy_adapter",
    "create_asp_scanner",
    # Orchestrator
    "SecurityScanOrchestrator",
    "create_security_orchestrator",
    "EXTENSION_TO_LANGUAGE",
    "LANGUAGE_SCANNERS",
]
