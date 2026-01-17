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

from .generic_security_scanner import (
    GenericSecurityScanner,
    GenericSecurityRule,
    LanguagePattern,
    LanguageDefinition,
    GENERIC_SECURITY_RULES,
    SUPPORTED_LANGUAGES,
    create_generic_security_scanner,
)

from .code_quality_scanner import (
    CodeQualityScanner,
    CodeQualityRule,
    QualityCategory,
    CODE_QUALITY_RULES,
    create_code_quality_scanner,
)

# Fase 36: Logic & Crypto Scanners
from .crypto_error_detector import (
    CryptoErrorDetector,
    CryptoRule,
    CRYPTO_RULES,
    create_crypto_error_detector,
)

from .control_flow_logic_detector import (
    ControlFlowLogicDetector,
    ControlFlowRule,
    CONTROL_FLOW_RULES,
    create_control_flow_logic_detector,
)

from .boolean_logic_detector import (
    BooleanLogicDetector,
    BooleanLogicRule,
    BOOLEAN_LOGIC_RULES,
    create_boolean_logic_detector,
)

# Fase 38: Memory Safety & Concurrency Scanners
from .memory_safety_detector import (
    MemorySafetyDetector,
    MemorySafetyRule,
    MEMORY_SAFETY_RULES,
    create_memory_safety_detector,
)

from .concurrency_error_detector import (
    ConcurrencyErrorDetector,
    ConcurrencyRule,
    CONCURRENCY_RULES,
    create_concurrency_error_detector,
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
    # Generic Multi-Language Security (CVD-2025-001)
    "GenericSecurityScanner",
    "GenericSecurityRule",
    "LanguagePattern",
    "LanguageDefinition",
    "GENERIC_SECURITY_RULES",
    "SUPPORTED_LANGUAGES",
    "create_generic_security_scanner",
    # Code Quality Scanner (Common Programming Mistakes)
    "CodeQualityScanner",
    "CodeQualityRule",
    "QualityCategory",
    "CODE_QUALITY_RULES",
    "create_code_quality_scanner",
    # Fase 36: Crypto Error Detector
    "CryptoErrorDetector",
    "CryptoRule",
    "CRYPTO_RULES",
    "create_crypto_error_detector",
    # Fase 36: Control Flow Logic Detector
    "ControlFlowLogicDetector",
    "ControlFlowRule",
    "CONTROL_FLOW_RULES",
    "create_control_flow_logic_detector",
    # Fase 36: Boolean Logic Detector
    "BooleanLogicDetector",
    "BooleanLogicRule",
    "BOOLEAN_LOGIC_RULES",
    "create_boolean_logic_detector",
    # Fase 38: Memory Safety Detector
    "MemorySafetyDetector",
    "MemorySafetyRule",
    "MEMORY_SAFETY_RULES",
    "create_memory_safety_detector",
    # Fase 38: Concurrency Error Detector
    "ConcurrencyErrorDetector",
    "ConcurrencyRule",
    "CONCURRENCY_RULES",
    "create_concurrency_error_detector",
]
