"""
Security Pattern Loader Service

Loads security scanning patterns from external YAML configuration files.
This allows patterns to be extended and modified without code changes.

Pattern files location: backend/app/config/security-patterns/
"""

import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels aligned with CVSS."""
    CRITICAL = "critical"   # CVSS 9.0-10.0
    HIGH = "high"           # CVSS 7.0-8.9
    MEDIUM = "medium"       # CVSS 4.0-6.9
    LOW = "low"             # CVSS 0.1-3.9
    INFO = "info"           # Informational


class OWASPCategory(str, Enum):
    """OWASP Top 10 2021 categories."""
    A01_BROKEN_ACCESS_CONTROL = "A01:2021-Broken Access Control"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021-Cryptographic Failures"
    A03_INJECTION = "A03:2021-Injection"
    A04_INSECURE_DESIGN = "A04:2021-Insecure Design"
    A05_SECURITY_MISCONFIGURATION = "A05:2021-Security Misconfiguration"
    A06_VULNERABLE_COMPONENTS = "A06:2021-Vulnerable and Outdated Components"
    A07_AUTH_FAILURES = "A07:2021-Identification and Authentication Failures"
    A08_DATA_INTEGRITY_FAILURES = "A08:2021-Software and Data Integrity Failures"
    A09_LOGGING_FAILURES = "A09:2021-Security Logging and Monitoring Failures"
    A10_SSRF = "A10:2021-Server-Side Request Forgery"


# Map short OWASP codes to enum
OWASP_CODE_MAP = {
    "A01": OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
    "A02": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
    "A03": OWASPCategory.A03_INJECTION,
    "A04": OWASPCategory.A04_INSECURE_DESIGN,
    "A05": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
    "A06": OWASPCategory.A06_VULNERABLE_COMPONENTS,
    "A07": OWASPCategory.A07_AUTH_FAILURES,
    "A08": OWASPCategory.A08_DATA_INTEGRITY_FAILURES,
    "A09": OWASPCategory.A09_LOGGING_FAILURES,
    "A10": OWASPCategory.A10_SSRF,
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SecurityPattern:
    """A single security scanning pattern."""
    id: str
    pattern: str
    title: str
    description: str
    severity: VulnerabilitySeverity
    owasp_category: OWASPCategory
    cwe_id: Optional[str] = None
    remediation: Optional[str] = None
    references: List[str] = field(default_factory=list)
    false_positive_hints: List[str] = field(default_factory=list)
    compiled_pattern: Optional[re.Pattern] = None

    def __post_init__(self):
        """Compile the regex pattern."""
        try:
            self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            logger.warning(f"Invalid regex pattern for {self.id}: {e}")
            self.compiled_pattern = None


@dataclass
class LanguagePatterns:
    """Patterns for a specific language/platform."""
    language: str
    version: str
    file_extensions: List[str]
    patterns: List[SecurityPattern] = field(default_factory=list)

    @property
    def pattern_count(self) -> int:
        """Total number of patterns."""
        return len(self.patterns)

    def get_patterns_by_owasp(self, category: OWASPCategory) -> List[SecurityPattern]:
        """Get patterns for a specific OWASP category."""
        return [p for p in self.patterns if p.owasp_category == category]

    def get_patterns_by_severity(self, severity: VulnerabilitySeverity) -> List[SecurityPattern]:
        """Get patterns with specific severity."""
        return [p for p in self.patterns if p.severity == severity]


# ============================================================================
# PATTERN LOADER
# ============================================================================

class SecurityPatternLoader:
    """
    Loads security patterns from YAML configuration files.

    Provides caching and hot-reloading capabilities.
    """

    DEFAULT_PATTERNS_DIR = Path(__file__).parent.parent / "config" / "security-patterns"

    def __init__(self, patterns_dir: Optional[Path] = None):
        """
        Initialize the pattern loader.

        Args:
            patterns_dir: Directory containing pattern YAML files
        """
        self.patterns_dir = patterns_dir or self.DEFAULT_PATTERNS_DIR
        self._cache: Dict[str, LanguagePatterns] = {}
        self._extension_map: Dict[str, str] = {}  # .ext -> language
        self._loaded = False

    def load_all_patterns(self, force_reload: bool = False) -> Dict[str, LanguagePatterns]:
        """
        Load all pattern files from the patterns directory.

        Args:
            force_reload: Force reload even if cached

        Returns:
            Dictionary mapping language to LanguagePatterns
        """
        if self._loaded and not force_reload:
            return self._cache

        self._cache.clear()
        self._extension_map.clear()

        if not self.patterns_dir.exists():
            logger.warning(f"Patterns directory not found: {self.patterns_dir}")
            return self._cache

        for yaml_file in self.patterns_dir.glob("*.yaml"):
            if yaml_file.name == "schema.yaml":
                continue  # Skip schema file

            try:
                lang_patterns = self._load_pattern_file(yaml_file)
                if lang_patterns:
                    self._cache[lang_patterns.language] = lang_patterns
                    # Build extension map
                    for ext in lang_patterns.file_extensions:
                        self._extension_map[ext] = lang_patterns.language
                    logger.info(f"Loaded {lang_patterns.pattern_count} patterns for {lang_patterns.language}")
            except Exception as e:
                logger.error(f"Error loading pattern file {yaml_file}: {e}")

        self._loaded = True
        logger.info(f"Loaded patterns for {len(self._cache)} languages")
        return self._cache

    def _load_pattern_file(self, yaml_file: Path) -> Optional[LanguagePatterns]:
        """Load patterns from a single YAML file."""
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        language = data.get('language', yaml_file.stem)
        version = data.get('version', '1.0')
        file_extensions = data.get('file_extensions', [])

        patterns = []
        patterns_data = data.get('patterns', {})

        # Patterns are organized by category (injection, crypto, etc.)
        for category_name, category_patterns in patterns_data.items():
            if not isinstance(category_patterns, list):
                continue

            for pattern_data in category_patterns:
                pattern = self._parse_pattern(pattern_data)
                if pattern:
                    patterns.append(pattern)

        return LanguagePatterns(
            language=language,
            version=version,
            file_extensions=file_extensions,
            patterns=patterns
        )

    def _parse_pattern(self, data: Dict[str, Any]) -> Optional[SecurityPattern]:
        """Parse a single pattern from YAML data."""
        try:
            # Map severity
            severity_str = data.get('severity', 'medium').lower()
            try:
                severity = VulnerabilitySeverity(severity_str)
            except ValueError:
                severity = VulnerabilitySeverity.MEDIUM

            # Map OWASP category
            owasp_code = data.get('owasp', 'A04')
            owasp_category = OWASP_CODE_MAP.get(owasp_code, OWASPCategory.A04_INSECURE_DESIGN)

            return SecurityPattern(
                id=data.get('id', 'unknown'),
                pattern=data.get('pattern', ''),
                title=data.get('title', 'Unknown vulnerability'),
                description=data.get('description', ''),
                severity=severity,
                owasp_category=owasp_category,
                cwe_id=data.get('cwe'),
                remediation=data.get('remediation'),
                references=data.get('references', []),
                false_positive_hints=data.get('false_positive_hints', [])
            )
        except Exception as e:
            logger.warning(f"Error parsing pattern: {e}")
            return None

    def get_patterns_for_file(self, file_path: str) -> List[SecurityPattern]:
        """
        Get applicable patterns for a given file based on extension.

        Args:
            file_path: Path to the file

        Returns:
            List of applicable patterns
        """
        if not self._loaded:
            self.load_all_patterns()

        ext = Path(file_path).suffix.lower()
        language = self._extension_map.get(ext)

        if not language:
            return []

        lang_patterns = self._cache.get(language)
        if not lang_patterns:
            return []

        return lang_patterns.patterns

    def get_language_for_extension(self, extension: str) -> Optional[str]:
        """Get language name for a file extension."""
        if not self._loaded:
            self.load_all_patterns()
        return self._extension_map.get(extension)

    def get_all_extensions(self) -> Set[str]:
        """Get all supported file extensions."""
        if not self._loaded:
            self.load_all_patterns()
        return set(self._extension_map.keys())

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        if not self._loaded:
            self.load_all_patterns()
        return list(self._cache.keys())

    def get_patterns_by_language(self, language: str) -> Optional[LanguagePatterns]:
        """Get all patterns for a specific language."""
        if not self._loaded:
            self.load_all_patterns()
        return self._cache.get(language)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded patterns."""
        if not self._loaded:
            self.load_all_patterns()

        stats = {
            "total_languages": len(self._cache),
            "total_patterns": sum(lp.pattern_count for lp in self._cache.values()),
            "total_extensions": len(self._extension_map),
            "by_language": {},
            "by_severity": {sev.value: 0 for sev in VulnerabilitySeverity},
            "by_owasp": {cat.value: 0 for cat in OWASPCategory}
        }

        for lang, lang_patterns in self._cache.items():
            stats["by_language"][lang] = {
                "patterns": lang_patterns.pattern_count,
                "extensions": lang_patterns.file_extensions
            }
            for pattern in lang_patterns.patterns:
                stats["by_severity"][pattern.severity.value] += 1
                stats["by_owasp"][pattern.owasp_category.value] += 1

        return stats

    def add_custom_pattern(
        self,
        language: str,
        pattern: SecurityPattern
    ) -> bool:
        """
        Add a custom pattern at runtime (not persisted).

        Args:
            language: Language to add pattern to
            pattern: Pattern to add

        Returns:
            True if successful
        """
        if not self._loaded:
            self.load_all_patterns()

        lang_patterns = self._cache.get(language)
        if not lang_patterns:
            return False

        lang_patterns.patterns.append(pattern)
        return True


# ============================================================================
# MODULE FUNCTIONS
# ============================================================================

# Singleton instance
_pattern_loader: Optional[SecurityPatternLoader] = None


def get_pattern_loader() -> SecurityPatternLoader:
    """Get the singleton pattern loader instance."""
    global _pattern_loader
    if _pattern_loader is None:
        _pattern_loader = SecurityPatternLoader()
    return _pattern_loader


def reload_patterns() -> Dict[str, LanguagePatterns]:
    """Force reload all patterns."""
    loader = get_pattern_loader()
    return loader.load_all_patterns(force_reload=True)


def get_patterns_for_file(file_path: str) -> List[SecurityPattern]:
    """Get patterns applicable to a file."""
    loader = get_pattern_loader()
    return loader.get_patterns_for_file(file_path)


def get_pattern_statistics() -> Dict[str, Any]:
    """Get pattern loading statistics."""
    loader = get_pattern_loader()
    return loader.get_statistics()
