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
]
