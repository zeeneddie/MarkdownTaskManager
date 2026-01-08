"""
Scanner Registry

Manages available scanners and selects appropriate ones based on project stack.
"""

from typing import List, Dict, Type, Optional, Any
from pathlib import Path
import logging

from .base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class ScannerRegistry:
    """
    Registry of available scanners.

    Automatically selects appropriate scanners based on detected project stack.
    """

    def __init__(self):
        self._scanners: Dict[str, Type[BaseScanner]] = {}
        self._stack_mapping: Dict[str, List[str]] = {
            # Python stacks
            'python': ['ruff', 'bandit', 'radon'],
            'django': ['ruff', 'bandit', 'radon', 'django-security'],
            'flask': ['ruff', 'bandit', 'radon'],
            'fastapi': ['ruff', 'bandit', 'radon'],

            # JavaScript/TypeScript stacks
            'javascript': ['eslint', 'jshint'],
            'typescript': ['eslint', 'tsc'],
            'react': ['eslint', 'react-scanner'],
            'vue': ['eslint', 'vue-scanner'],
            'node': ['eslint', 'npm-audit'],

            # .NET stacks
            'dotnet': ['dotnet-volume', 'dotnet-duplication'],
            'csharp': ['dotnet-volume', 'dotnet-duplication'],
            'vbnet': ['dotnet-volume', 'dotnet-duplication'],
            'aspnet': ['dotnet-volume', 'dotnet-duplication', 'aspnet-security'],

            # Java stacks
            'java': ['checkstyle', 'spotbugs'],
            'spring': ['checkstyle', 'spotbugs', 'spring-security'],

            # PHP stacks
            'php': ['phpstan', 'phpcs'],
            'laravel': ['phpstan', 'phpcs', 'larastan'],

            # Go
            'go': ['golangci-lint'],

            # Rust
            'rust': ['clippy'],

            # Generic
            'generic': ['loc-counter', 'duplication-detector']
        }

    def register(self, scanner_class: Type[BaseScanner]) -> None:
        """Register a scanner class"""
        instance = scanner_class.__new__(scanner_class)
        name = instance.name if hasattr(instance, 'name') else scanner_class.__name__
        self._scanners[name] = scanner_class
        logger.info(f"Registered scanner: {name}")

    def get_scanner(self, name: str, project_path: str) -> Optional[BaseScanner]:
        """Get a scanner instance by name"""
        if name not in self._scanners:
            logger.warning(f"Scanner not found: {name}")
            return None
        return self._scanners[name](project_path)

    def get_scanners_for_stack(
        self,
        stack: str,
        project_path: str,
        scanner_types: Optional[List[str]] = None
    ) -> List[BaseScanner]:
        """
        Get all scanners appropriate for a given stack.

        Args:
            stack: Detected tech stack (e.g., 'python', 'dotnet')
            project_path: Path to the project
            scanner_types: Optional filter by scanner type (e.g., ['linter', 'security'])

        Returns:
            List of scanner instances
        """
        stack_lower = stack.lower()
        scanner_names = self._stack_mapping.get(stack_lower, self._stack_mapping['generic'])

        scanners = []
        for name in scanner_names:
            if name in self._scanners:
                scanner = self._scanners[name](project_path)
                if scanner.is_available():
                    if scanner_types is None or scanner.scanner_type in scanner_types:
                        scanners.append(scanner)
                else:
                    logger.debug(f"Scanner {name} not available")

        return scanners

    def get_all_scanners_for_project(
        self,
        stacks: List[str],
        project_path: str
    ) -> List[BaseScanner]:
        """
        Get all scanners for a project with multiple detected stacks.

        Args:
            stacks: List of detected tech stacks
            project_path: Path to the project

        Returns:
            List of unique scanner instances
        """
        seen = set()
        scanners = []

        for stack in stacks:
            for scanner in self.get_scanners_for_stack(stack, project_path):
                if scanner.name not in seen:
                    seen.add(scanner.name)
                    scanners.append(scanner)

        return scanners

    async def run_scan(
        self,
        project_path: str,
        stacks: List[str],
        scanner_names: Optional[List[str]] = None
    ) -> Dict[str, ScanResult]:
        """
        Run scans for a project.

        Args:
            project_path: Path to the project
            stacks: Detected tech stacks
            scanner_names: Optional specific scanners to run (overrides stack-based selection)

        Returns:
            Dict mapping scanner name to scan result
        """
        results = {}

        if scanner_names:
            # Run specific scanners
            for name in scanner_names:
                scanner = self.get_scanner(name, project_path)
                if scanner:
                    try:
                        result = await scanner.scan()
                        results[name] = result
                    except Exception as e:
                        logger.error(f"Scanner {name} failed: {e}")
        else:
            # Auto-select based on stacks
            scanners = self.get_all_scanners_for_project(stacks, project_path)
            for scanner in scanners:
                try:
                    result = await scanner.scan()
                    results[scanner.name] = result
                except Exception as e:
                    logger.error(f"Scanner {scanner.name} failed: {e}")

        return results

    @property
    def available_scanners(self) -> List[str]:
        """List of registered scanner names"""
        return list(self._scanners.keys())

    @property
    def stack_mappings(self) -> Dict[str, List[str]]:
        """Current stack to scanner mappings"""
        return self._stack_mapping.copy()


# Singleton instance
_registry: Optional[ScannerRegistry] = None


def get_scanner_registry() -> ScannerRegistry:
    """Get the global scanner registry instance"""
    global _registry
    if _registry is None:
        _registry = ScannerRegistry()
        _register_default_scanners(_registry)
    return _registry


def _register_default_scanners(registry: ScannerRegistry) -> None:
    """Register all default scanners"""
    # Import and register scanners
    try:
        from .dotnet.dotnet_scanner import DotNetVolumeScanner, DotNetDuplicationScanner
        registry.register(DotNetVolumeScanner)
        registry.register(DotNetDuplicationScanner)
    except ImportError as e:
        logger.debug(f"Could not load .NET scanners: {e}")

    try:
        from .python.python_scanner import RuffScanner, BanditScanner, RadonScanner
        registry.register(RuffScanner)
        registry.register(BanditScanner)
        registry.register(RadonScanner)
    except ImportError as e:
        logger.debug(f"Could not load Python scanners: {e}")

    # Register Metrics Layer scanners (Week 126)
    try:
        from .metrics.complexity_analyzer import ComplexityAnalyzer
        from .metrics.interfacing_analyzer import InterfacingAnalyzer
        from .metrics.coupling_analyzer import CouplingAnalyzer
        from .metrics.balance_analyzer import BalanceAnalyzer
        from .metrics.duplication_analyzer import DuplicationAnalyzer

        registry.register(ComplexityAnalyzer)
        registry.register(InterfacingAnalyzer)
        registry.register(CouplingAnalyzer)
        registry.register(BalanceAnalyzer)
        registry.register(DuplicationAnalyzer)
        logger.info("Registered Metrics Layer scanners (Week 126)")
    except ImportError as e:
        logger.debug(f"Could not load Metrics Layer scanners: {e}")

    logger.info(f"Registered {len(registry.available_scanners)} scanners")
