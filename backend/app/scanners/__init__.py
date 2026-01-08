"""
Quality Scanners Package

Stack-aware quality scanning system that runs appropriate scanners
based on project characteristics (detected tech stack).

Supported Stacks:
- Python: ruff, bandit, coverage, radon
- JavaScript/TypeScript: eslint, jshint
- .NET (C#/VB.NET): volume analyzer, duplication detector
- Java: checkstyle, spotbugs
- PHP: phpstan, phpcs
- Go: golangci-lint
"""

from .registry import ScannerRegistry, get_scanner_registry
from .base import (
    BaseScanner,
    ScanResult,
    ScanFinding,
    ScanMetrics,
    Severity,
    FindingType
)

__all__ = [
    'ScannerRegistry',
    'get_scanner_registry',
    'BaseScanner',
    'ScanResult',
    'ScanFinding',
    'ScanMetrics',
    'Severity',
    'FindingType'
]
