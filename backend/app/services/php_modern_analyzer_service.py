"""
PHP Modern Analyzer Service

Fase 24 GAP Item B6: PHP Analyzer Enhancement
Week 159 - Modern PHP analysis for PHP 8.x and modern frameworks.

Features:
- PHP 8.x feature detection (attributes, enums, readonly, match, etc.)
- Laravel 8/9/10/11 modern patterns
- Symfony 5/6/7 modern patterns
- Composer dependency analysis
- PSR compliance checking
- Migration recommendations

This complements the existing php_analyzer_service.py which focuses
on legacy PHP patterns.

Author: Claude Code (Week 159)
Date: 2026-01-24
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class PHPVersion(str, Enum):
    """PHP version detection."""
    PHP_5_6 = "5.6"
    PHP_7_0 = "7.0"
    PHP_7_1 = "7.1"
    PHP_7_2 = "7.2"
    PHP_7_3 = "7.3"
    PHP_7_4 = "7.4"
    PHP_8_0 = "8.0"
    PHP_8_1 = "8.1"
    PHP_8_2 = "8.2"
    PHP_8_3 = "8.3"
    UNKNOWN = "unknown"


class FrameworkType(str, Enum):
    """PHP framework types."""
    LARAVEL = "laravel"
    SYMFONY = "symfony"
    CODEIGNITER = "codeigniter"
    CAKEPHP = "cakephp"
    YII = "yii"
    SLIM = "slim"
    LUMEN = "lumen"
    WORDPRESS = "wordpress"
    DRUPAL = "drupal"
    NONE = "none"


class DependencyStatus(str, Enum):
    """Dependency status."""
    UP_TO_DATE = "up_to_date"
    OUTDATED = "outdated"
    ABANDONED = "abandoned"
    SECURITY_ISSUE = "security_issue"
    UNKNOWN = "unknown"


# ============================================================================
# DATA CLASSES - PHP 8.x Features
# ============================================================================

@dataclass
class PHP8Attribute:
    """Represents a PHP 8 attribute."""
    name: str
    arguments: List[str]
    target: str  # class, method, property, parameter
    file_path: str
    line_number: int


@dataclass
class PHP8Enum:
    """Represents a PHP 8.1 enum."""
    file_path: str
    enum_name: str
    namespace: Optional[str] = None
    backed_type: Optional[str] = None  # int, string, or None for unit enum
    cases: List[Dict[str, Any]] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    uses_traits: List[str] = field(default_factory=list)


@dataclass
class PHP8Feature:
    """Detected PHP 8.x feature."""
    feature_name: str
    php_version_required: str
    file_path: str
    line_number: int
    code_snippet: str
    description: str


@dataclass
class ReadonlyProperty:
    """Represents a readonly property (PHP 8.1+)."""
    class_name: str
    property_name: str
    property_type: str
    file_path: str
    line_number: int


@dataclass
class ConstructorPromotion:
    """Represents constructor property promotion (PHP 8.0+)."""
    class_name: str
    promoted_properties: List[Dict[str, str]]
    file_path: str
    line_number: int


# ============================================================================
# DATA CLASSES - Composer
# ============================================================================

@dataclass
class ComposerPackage:
    """Represents a Composer package."""
    name: str
    version_constraint: str
    installed_version: Optional[str] = None
    latest_version: Optional[str] = None
    status: DependencyStatus = DependencyStatus.UNKNOWN
    is_dev_dependency: bool = False
    is_abandoned: bool = False
    replacement_package: Optional[str] = None
    description: Optional[str] = None
    php_requirement: Optional[str] = None


@dataclass
class ComposerAnalysis:
    """Complete Composer analysis result."""
    project_name: Optional[str] = None
    project_description: Optional[str] = None
    php_version_required: Optional[str] = None
    autoload_psr4: Dict[str, str] = field(default_factory=dict)
    autoload_classmap: List[str] = field(default_factory=list)
    packages: List[ComposerPackage] = field(default_factory=list)
    dev_packages: List[ComposerPackage] = field(default_factory=list)
    scripts: Dict[str, Any] = field(default_factory=dict)
    total_packages: int = 0
    outdated_packages: int = 0
    abandoned_packages: int = 0
    security_issues: int = 0
    psr4_compliant: bool = True
    has_lock_file: bool = False


# ============================================================================
# DATA CLASSES - Modern Laravel
# ============================================================================

@dataclass
class LaravelModernComponent:
    """Modern Laravel component (8+)."""
    file_path: str
    component_name: str
    component_type: str  # livewire, blade_component, action, etc.
    laravel_version: str = "10+"
    uses_typed_properties: bool = False
    uses_attributes: bool = False
    uses_enums: bool = False


@dataclass
class LivewireComponent:
    """Laravel Livewire component."""
    file_path: str
    component_name: str
    namespace: Optional[str] = None
    properties: List[Dict[str, str]] = field(default_factory=list)
    computed_properties: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    listeners: List[str] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)
    uses_wire_model: bool = False
    uses_wire_loading: bool = False
    alpine_integration: bool = False


@dataclass
class LaravelAction:
    """Laravel Action class pattern."""
    file_path: str
    class_name: str
    handle_method: bool = False
    as_controller: bool = False
    as_job: bool = False
    as_listener: bool = False


# ============================================================================
# DATA CLASSES - Modern Symfony
# ============================================================================

@dataclass
class SymfonyModernComponent:
    """Modern Symfony component (5+)."""
    file_path: str
    component_name: str
    component_type: str
    symfony_version: str = "6+"
    uses_php_attributes: bool = False
    uses_autowiring: bool = True


@dataclass
class SymfonyMessengerHandler:
    """Symfony Messenger message handler."""
    file_path: str
    handler_class: str
    handles_message: str
    is_async: bool = False
    transport: Optional[str] = None


# ============================================================================
# DATA CLASSES - Analysis Result
# ============================================================================

@dataclass
class PHPModernAnalysisResult:
    """Complete modern PHP analysis result."""
    # PHP Version and Features
    detected_php_version: PHPVersion = PHPVersion.UNKNOWN
    minimum_php_required: PHPVersion = PHPVersion.UNKNOWN
    php8_features: List[PHP8Feature] = field(default_factory=list)
    php8_enums: List[PHP8Enum] = field(default_factory=list)
    php8_attributes: List[PHP8Attribute] = field(default_factory=list)
    readonly_properties: List[ReadonlyProperty] = field(default_factory=list)
    constructor_promotions: List[ConstructorPromotion] = field(default_factory=list)

    # Framework detection
    framework: FrameworkType = FrameworkType.NONE
    framework_version: Optional[str] = None

    # Laravel Modern
    livewire_components: List[LivewireComponent] = field(default_factory=list)
    laravel_actions: List[LaravelAction] = field(default_factory=list)
    laravel_modern_components: List[LaravelModernComponent] = field(default_factory=list)

    # Symfony Modern
    symfony_modern_components: List[SymfonyModernComponent] = field(default_factory=list)
    messenger_handlers: List[SymfonyMessengerHandler] = field(default_factory=list)

    # Composer
    composer_analysis: Optional[ComposerAnalysis] = None

    # Statistics
    total_files_scanned: int = 0
    total_loc: int = 0
    php8_feature_count: int = 0
    modernization_score: float = 0.0  # 0-100

    # Migration recommendations
    migration_recommendations: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scan_duration_ms: float = 0.0


# ============================================================================
# PHP 8.x FEATURE PATTERNS
# ============================================================================

PHP8_FEATURE_PATTERNS = {
    # PHP 8.0 features
    "named_arguments": {
        "pattern": r'\w+\s*\(\s*\w+\s*:\s*[^,)]+',
        "version": "8.0",
        "description": "Named arguments allow passing arguments by parameter name"
    },
    "attributes": {
        "pattern": r'#\[\s*\w+(?:\s*\([^)]*\))?\s*\]',
        "version": "8.0",
        "description": "PHP 8 attributes (replaces docblock annotations)"
    },
    "constructor_promotion": {
        "pattern": r'__construct\s*\([^)]*(?:public|protected|private|readonly)\s+\w+\s+\$\w+',
        "version": "8.0",
        "description": "Constructor property promotion"
    },
    "match_expression": {
        "pattern": r'\bmatch\s*\([^)]+\)\s*\{',
        "version": "8.0",
        "description": "Match expression (improved switch)"
    },
    "nullsafe_operator": {
        "pattern": r'\?\->',
        "version": "8.0",
        "description": "Nullsafe operator (?->)"
    },
    "union_types": {
        "pattern": r'(?:function|fn)\s+\w+\s*\([^)]*\)\s*:\s*\w+\s*\|\s*\w+',
        "version": "8.0",
        "description": "Union types (Type1|Type2)"
    },
    "mixed_type": {
        "pattern": r':\s*mixed\b',
        "version": "8.0",
        "description": "Mixed type declaration"
    },
    "throw_expression": {
        "pattern": r'\$\w+\s*\?\?\s*throw\s+new',
        "version": "8.0",
        "description": "Throw as expression"
    },
    "static_return_type": {
        "pattern": r':\s*static\b',
        "version": "8.0",
        "description": "Static return type"
    },

    # PHP 8.1 features
    "enums": {
        "pattern": r'\benum\s+\w+(?:\s*:\s*(?:int|string))?\s*(?:implements\s+[^{]+)?\s*\{',
        "version": "8.1",
        "description": "PHP 8.1 enumerations"
    },
    "readonly_property": {
        "pattern": r'(?:public|protected|private)\s+readonly\s+\w+\s+\$\w+',
        "version": "8.1",
        "description": "Readonly properties"
    },
    "first_class_callable": {
        "pattern": r'\$\w+\s*=\s*\$?\w+\s*\.\.\.\s*;|\w+\(\.\.\.\)',
        "version": "8.1",
        "description": "First-class callable syntax"
    },
    "intersection_types": {
        "pattern": r':\s*\w+\s*&\s*\w+',
        "version": "8.1",
        "description": "Intersection types (Type1&Type2)"
    },
    "never_return_type": {
        "pattern": r':\s*never\b',
        "version": "8.1",
        "description": "Never return type"
    },
    "new_in_initializers": {
        "pattern": r'=\s*new\s+\w+\s*\([^)]*\)\s*[,)]',
        "version": "8.1",
        "description": "New in initializers"
    },

    # PHP 8.2 features
    "readonly_class": {
        "pattern": r'\breadonly\s+class\s+\w+',
        "version": "8.2",
        "description": "Readonly classes"
    },
    "disjunctive_normal_form_types": {
        "pattern": r':\s*\([^)]+\)\s*\|',
        "version": "8.2",
        "description": "DNF types ((A&B)|C)"
    },
    "null_false_true_types": {
        "pattern": r':\s*(?:null|false|true)\b',
        "version": "8.2",
        "description": "Standalone null, false, true types"
    },
    "constants_in_traits": {
        "pattern": r'trait\s+\w+\s*\{[^}]*\bconst\s+',
        "version": "8.2",
        "description": "Constants in traits"
    },

    # PHP 8.3 features
    "typed_class_constants": {
        "pattern": r'\bconst\s+\w+\s+\w+\s*=',
        "version": "8.3",
        "description": "Typed class constants"
    },
    "dynamic_class_constant_fetch": {
        "pattern": r'\w+::\{\$\w+\}',
        "version": "8.3",
        "description": "Dynamic class constant fetch"
    },
    "override_attribute": {
        "pattern": r'#\[\s*Override\s*\]',
        "version": "8.3",
        "description": "#[Override] attribute"
    },
}


# ============================================================================
# MODERN LARAVEL PATTERNS
# ============================================================================

LARAVEL_MODERN_PATTERNS = {
    "livewire_component": {
        "pattern": r'class\s+\w+\s+extends\s+(?:Livewire\\)?Component',
        "type": "livewire",
        "version": "8+"
    },
    "blade_component_class": {
        "pattern": r'class\s+\w+\s+extends\s+(?:Illuminate\\View\\)?Component',
        "type": "blade_component",
        "version": "8+"
    },
    "action_class": {
        "pattern": r'class\s+\w+(?:Action)?\s*\{[^}]*public\s+function\s+handle\s*\(',
        "type": "action",
        "version": "8+"
    },
    "form_request": {
        "pattern": r'class\s+\w+\s+extends\s+FormRequest',
        "type": "form_request",
        "version": "5.1+"
    },
    "resource_class": {
        "pattern": r'class\s+\w+\s+extends\s+(?:Json)?Resource',
        "type": "api_resource",
        "version": "5.5+"
    },
    "sanctum_auth": {
        "pattern": r'HasApiTokens|Sanctum::actingAs',
        "type": "sanctum",
        "version": "7+"
    },
    "pest_test": {
        "pattern": r'(?:it|test)\s*\(\s*[\'"][^\'"]+[\'"]\s*,\s*function',
        "type": "pest_test",
        "version": "8+"
    },
    "model_factory": {
        "pattern": r'class\s+\w+Factory\s+extends\s+Factory',
        "type": "factory",
        "version": "8+"
    },
    "enum_cast": {
        "pattern": r'protected\s+\$casts\s*=\s*\[[^\]]*\w+::class',
        "type": "enum_cast",
        "version": "9+"
    },
    "invokable_controller": {
        "pattern": r'public\s+function\s+__invoke\s*\([^)]*Request',
        "type": "invokable_controller",
        "version": "5.3+"
    },
}


# ============================================================================
# MODERN SYMFONY PATTERNS
# ============================================================================

SYMFONY_MODERN_PATTERNS = {
    "php_attribute_route": {
        "pattern": r'#\[\s*Route\s*\(',
        "type": "attribute_routing",
        "version": "5.2+"
    },
    "autowire_attribute": {
        "pattern": r'#\[\s*(?:Autowire|AutowireLocator|TaggedLocator)',
        "type": "autowire",
        "version": "6.1+"
    },
    "messenger_handler": {
        "pattern": r'#\[\s*AsMessageHandler\s*\]',
        "type": "messenger",
        "version": "6.0+"
    },
    "messenger_attribute": {
        "pattern": r'class\s+\w+\s*\{[^}]*#\[\s*AsMessageHandler',
        "type": "messenger_handler",
        "version": "6.0+"
    },
    "security_attribute": {
        "pattern": r'#\[\s*(?:IsGranted|Security)\s*\(',
        "type": "security",
        "version": "6.0+"
    },
    "required_attribute": {
        "pattern": r'#\[\s*Required\s*\]',
        "type": "di_required",
        "version": "6.0+"
    },
    "scheduler_attribute": {
        "pattern": r'#\[\s*AsScheduledTask\s*\(',
        "type": "scheduler",
        "version": "6.3+"
    },
    "lock_attribute": {
        "pattern": r'#\[\s*Lock\s*\(',
        "type": "lock",
        "version": "6.3+"
    },
    "value_resolver": {
        "pattern": r'#\[\s*(?:MapEntity|MapQueryString|MapRequestPayload)',
        "type": "value_resolver",
        "version": "6.3+"
    },
}


# ============================================================================
# SERVICE CLASS
# ============================================================================

class PHPModernAnalyzerService:
    """
    Analyzer for modern PHP applications (PHP 8.x).

    Detects and analyzes:
    - PHP 8.x features (attributes, enums, readonly, etc.)
    - Modern Laravel patterns (Livewire, Actions, etc.)
    - Modern Symfony patterns (attributes, Messenger, etc.)
    - Composer dependencies
    - PSR compliance
    """

    PHP_EXTENSIONS = {".php", ".phtml"}
    SKIP_DIRS = {"vendor", "node_modules", ".git", "storage", "cache", "var"}

    def __init__(self):
        """Initialize the analyzer."""
        self._compiled_php8_patterns = {
            name: re.compile(info["pattern"], re.MULTILINE)
            for name, info in PHP8_FEATURE_PATTERNS.items()
        }
        self._compiled_laravel_patterns = {
            name: re.compile(info["pattern"], re.MULTILINE)
            for name, info in LARAVEL_MODERN_PATTERNS.items()
        }
        self._compiled_symfony_patterns = {
            name: re.compile(info["pattern"], re.MULTILINE)
            for name, info in SYMFONY_MODERN_PATTERNS.items()
        }
        logger.info("PHPModernAnalyzerService initialized")

    async def analyze(
        self,
        project_path: str,
        include_composer: bool = True,
        include_framework_analysis: bool = True
    ) -> PHPModernAnalysisResult:
        """
        Analyze a PHP project for modern features.

        Args:
            project_path: Path to the project root
            include_composer: Whether to analyze composer.json
            include_framework_analysis: Whether to detect framework patterns

        Returns:
            Complete analysis result
        """
        import time
        start_time = time.time()

        result = PHPModernAnalysisResult()
        path = Path(project_path)

        if not path.exists():
            logger.error(f"Project path does not exist: {project_path}")
            return result

        # Analyze Composer first (helps with framework detection)
        if include_composer:
            result.composer_analysis = await self._analyze_composer(path)
            if result.composer_analysis:
                result.framework = self._detect_framework_from_composer(
                    result.composer_analysis
                )

        # Scan PHP files
        php_files = self._find_php_files(path)
        result.total_files_scanned = len(php_files)

        for php_file in php_files:
            await self._analyze_php_file(php_file, result, include_framework_analysis)

        # Calculate metrics
        self._calculate_metrics(result)

        # Generate migration recommendations
        result.migration_recommendations = self._generate_recommendations(result)

        result.scan_duration_ms = (time.time() - start_time) * 1000

        logger.info(
            f"PHP modern analysis complete: {result.total_files_scanned} files, "
            f"{result.php8_feature_count} PHP 8.x features, "
            f"framework: {result.framework.value}"
        )

        return result

    def _find_php_files(self, root: Path) -> List[Path]:
        """Find all PHP files."""
        files = []
        for ext in self.PHP_EXTENSIONS:
            for f in root.rglob(f"*{ext}"):
                if not any(skip in f.parts for skip in self.SKIP_DIRS):
                    files.append(f)
        return files

    async def _analyze_composer(self, root: Path) -> Optional[ComposerAnalysis]:
        """Analyze composer.json and composer.lock."""
        composer_json = root / "composer.json"
        composer_lock = root / "composer.lock"

        if not composer_json.exists():
            return None

        try:
            with open(composer_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            analysis = ComposerAnalysis(
                project_name=data.get("name"),
                project_description=data.get("description"),
                has_lock_file=composer_lock.exists()
            )

            # PHP version requirement
            require = data.get("require", {})
            if "php" in require:
                analysis.php_version_required = require["php"]

            # Autoload PSR-4
            autoload = data.get("autoload", {})
            if "psr-4" in autoload:
                analysis.autoload_psr4 = autoload["psr-4"]
            if "classmap" in autoload:
                analysis.autoload_classmap = autoload["classmap"]

            # Scripts
            analysis.scripts = data.get("scripts", {})

            # Parse packages
            for pkg_name, version in require.items():
                if pkg_name == "php" or pkg_name.startswith("ext-"):
                    continue

                package = ComposerPackage(
                    name=pkg_name,
                    version_constraint=version,
                    is_dev_dependency=False
                )

                # Check for known abandoned packages
                if self._is_abandoned_package(pkg_name):
                    package.is_abandoned = True
                    package.status = DependencyStatus.ABANDONED

                analysis.packages.append(package)

            # Dev packages
            require_dev = data.get("require-dev", {})
            for pkg_name, version in require_dev.items():
                package = ComposerPackage(
                    name=pkg_name,
                    version_constraint=version,
                    is_dev_dependency=True
                )
                analysis.dev_packages.append(package)

            # Calculate totals
            analysis.total_packages = len(analysis.packages) + len(analysis.dev_packages)
            analysis.abandoned_packages = sum(
                1 for p in analysis.packages if p.is_abandoned
            )

            # Check PSR-4 compliance
            analysis.psr4_compliant = bool(analysis.autoload_psr4)

            return analysis

        except Exception as e:
            logger.warning(f"Failed to parse composer.json: {e}")
            return None

    def _is_abandoned_package(self, package_name: str) -> bool:
        """Check if package is known to be abandoned."""
        abandoned_packages = {
            "phpunit/dbunit",
            "phpunit/php-invoker",
            "league/csv-doctrine",
            "swiftmailer/swiftmailer",  # Replaced by symfony/mailer
            "fzaninotto/faker",  # Replaced by fakerphp/faker
            "prophecy/prophecy",
            "phpspec/prophecy",
        }
        return package_name.lower() in abandoned_packages

    def _detect_framework_from_composer(self, analysis: ComposerAnalysis) -> FrameworkType:
        """Detect framework from Composer packages."""
        package_names = {p.name.lower() for p in analysis.packages}

        if "laravel/framework" in package_names:
            return FrameworkType.LARAVEL
        elif "symfony/framework-bundle" in package_names:
            return FrameworkType.SYMFONY
        elif "codeigniter4/framework" in package_names:
            return FrameworkType.CODEIGNITER
        elif "cakephp/cakephp" in package_names:
            return FrameworkType.CAKEPHP
        elif "yiisoft/yii2" in package_names:
            return FrameworkType.YII
        elif "slim/slim" in package_names:
            return FrameworkType.SLIM
        elif "laravel/lumen-framework" in package_names:
            return FrameworkType.LUMEN

        return FrameworkType.NONE

    async def _analyze_php_file(
        self,
        file_path: Path,
        result: PHPModernAnalysisResult,
        include_framework_analysis: bool
    ) -> None:
        """Analyze a PHP file for modern features."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            result.total_loc += len(lines)

            # Detect PHP 8.x features
            for name, pattern in self._compiled_php8_patterns.items():
                for match in pattern.finditer(content):
                    feature = PHP8Feature(
                        feature_name=name,
                        php_version_required=PHP8_FEATURE_PATTERNS[name]["version"],
                        file_path=str(file_path),
                        line_number=content[:match.start()].count("\n") + 1,
                        code_snippet=match.group(0)[:100],
                        description=PHP8_FEATURE_PATTERNS[name]["description"]
                    )
                    result.php8_features.append(feature)

            # Detect enums
            enums = self._detect_enums(file_path, content)
            result.php8_enums.extend(enums)

            # Detect attributes
            attributes = self._detect_attributes(file_path, content)
            result.php8_attributes.extend(attributes)

            # Detect readonly properties
            readonly = self._detect_readonly_properties(file_path, content)
            result.readonly_properties.extend(readonly)

            # Detect constructor promotion
            promotions = self._detect_constructor_promotion(file_path, content)
            result.constructor_promotions.extend(promotions)

            # Framework-specific analysis
            if include_framework_analysis:
                if result.framework == FrameworkType.LARAVEL:
                    self._analyze_laravel_file(file_path, content, result)
                elif result.framework == FrameworkType.SYMFONY:
                    self._analyze_symfony_file(file_path, content, result)

        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")

    def _detect_enums(self, file_path: Path, content: str) -> List[PHP8Enum]:
        """Detect PHP 8.1 enums."""
        enums = []

        pattern = re.compile(
            r'enum\s+(\w+)(?:\s*:\s*(int|string))?\s*'
            r'(?:implements\s+([^{]+))?\s*\{([^}]+)\}',
            re.MULTILINE | re.DOTALL
        )

        for match in pattern.finditer(content):
            enum_name = match.group(1)
            backed_type = match.group(2)
            implements = match.group(3)
            body = match.group(4)

            enum = PHP8Enum(
                file_path=str(file_path),
                enum_name=enum_name,
                backed_type=backed_type,
                implements=implements.split(",") if implements else []
            )

            # Parse cases
            case_pattern = re.compile(r'case\s+(\w+)(?:\s*=\s*([^;]+))?;')
            for case_match in case_pattern.finditer(body):
                enum.cases.append({
                    "name": case_match.group(1),
                    "value": case_match.group(2)
                })

            # Parse methods
            method_pattern = re.compile(r'(?:public|private|protected)\s+function\s+(\w+)')
            for method_match in method_pattern.finditer(body):
                enum.methods.append(method_match.group(1))

            enums.append(enum)

        return enums

    def _detect_attributes(self, file_path: Path, content: str) -> List[PHP8Attribute]:
        """Detect PHP 8 attributes."""
        attributes = []

        pattern = re.compile(r'#\[\s*(\w+)(?:\s*\(([^)]*)\))?\s*\]')

        for match in pattern.finditer(content):
            attr_name = match.group(1)
            args = match.group(2) or ""

            # Determine target
            after_attr = content[match.end():match.end()+200]
            target = "unknown"
            if re.match(r'\s*(?:final\s+)?(?:abstract\s+)?class\s+', after_attr):
                target = "class"
            elif re.match(r'\s*(?:public|private|protected)\s+function\s+', after_attr):
                target = "method"
            elif re.match(r'\s*(?:public|private|protected)\s+(?:readonly\s+)?\$', after_attr):
                target = "property"

            attr = PHP8Attribute(
                name=attr_name,
                arguments=args.split(",") if args else [],
                target=target,
                file_path=str(file_path),
                line_number=content[:match.start()].count("\n") + 1
            )
            attributes.append(attr)

        return attributes

    def _detect_readonly_properties(self, file_path: Path, content: str) -> List[ReadonlyProperty]:
        """Detect readonly properties."""
        properties = []

        # Get class context
        class_match = re.search(r'class\s+(\w+)', content)
        class_name = class_match.group(1) if class_match else "Unknown"

        pattern = re.compile(
            r'(?:public|protected|private)\s+readonly\s+(\w+)\s+\$(\w+)'
        )

        for match in pattern.finditer(content):
            prop = ReadonlyProperty(
                class_name=class_name,
                property_type=match.group(1),
                property_name=match.group(2),
                file_path=str(file_path),
                line_number=content[:match.start()].count("\n") + 1
            )
            properties.append(prop)

        return properties

    def _detect_constructor_promotion(
        self,
        file_path: Path,
        content: str
    ) -> List[ConstructorPromotion]:
        """Detect constructor property promotion."""
        promotions = []

        class_match = re.search(r'class\s+(\w+)', content)
        class_name = class_match.group(1) if class_match else "Unknown"

        # Find constructor with promoted properties
        ctor_pattern = re.compile(
            r'function\s+__construct\s*\(([^)]+)\)',
            re.MULTILINE | re.DOTALL
        )

        for match in ctor_pattern.finditer(content):
            params = match.group(1)
            promoted = []

            # Look for visibility keywords in parameters
            param_pattern = re.compile(
                r'(?:public|protected|private|readonly)\s+'
                r'(?:readonly\s+)?(\w+)\s+\$(\w+)'
            )

            for param_match in param_pattern.finditer(params):
                promoted.append({
                    "type": param_match.group(1),
                    "name": param_match.group(2)
                })

            if promoted:
                promotions.append(ConstructorPromotion(
                    class_name=class_name,
                    promoted_properties=promoted,
                    file_path=str(file_path),
                    line_number=content[:match.start()].count("\n") + 1
                ))

        return promotions

    def _analyze_laravel_file(
        self,
        file_path: Path,
        content: str,
        result: PHPModernAnalysisResult
    ) -> None:
        """Analyze Laravel-specific patterns."""
        # Check for Livewire components
        if "extends Component" in content and "Livewire" in content:
            component = self._detect_livewire_component(file_path, content)
            if component:
                result.livewire_components.append(component)

        # Check for Laravel Actions
        if "function handle" in content:
            action = self._detect_laravel_action(file_path, content)
            if action:
                result.laravel_actions.append(action)

        # Check for modern patterns
        for name, info in LARAVEL_MODERN_PATTERNS.items():
            pattern = self._compiled_laravel_patterns[name]
            if pattern.search(content):
                component = LaravelModernComponent(
                    file_path=str(file_path),
                    component_name=file_path.stem,
                    component_type=info["type"],
                    laravel_version=info["version"]
                )
                result.laravel_modern_components.append(component)

    def _detect_livewire_component(
        self,
        file_path: Path,
        content: str
    ) -> Optional[LivewireComponent]:
        """Detect Livewire component details."""
        class_match = re.search(r'class\s+(\w+)\s+extends', content)
        if not class_match:
            return None

        component = LivewireComponent(
            file_path=str(file_path),
            component_name=class_match.group(1)
        )

        # Detect properties
        prop_pattern = re.compile(r'public\s+(?:\w+\s+)?\$(\w+)')
        for match in prop_pattern.finditer(content):
            component.properties.append({"name": match.group(1)})

        # Detect computed properties
        if "getListeners" in content or "#[Computed]" in content:
            component.computed_properties.append("detected")

        # Detect actions (public methods)
        action_pattern = re.compile(r'public\s+function\s+(\w+)\s*\(')
        for match in action_pattern.finditer(content):
            method = match.group(1)
            if not method.startswith(("render", "mount", "boot", "__")):
                component.actions.append(method)

        # Detect wire:model usage
        component.uses_wire_model = "wire:model" in content

        return component

    def _detect_laravel_action(
        self,
        file_path: Path,
        content: str
    ) -> Optional[LaravelAction]:
        """Detect Laravel Action class."""
        class_match = re.search(r'class\s+(\w+)', content)
        if not class_match:
            return None

        action = LaravelAction(
            file_path=str(file_path),
            class_name=class_match.group(1),
            handle_method="function handle" in content,
            as_controller="AsController" in content,
            as_job="AsJob" in content,
            as_listener="AsListener" in content
        )

        return action if action.handle_method else None

    def _analyze_symfony_file(
        self,
        file_path: Path,
        content: str,
        result: PHPModernAnalysisResult
    ) -> None:
        """Analyze Symfony-specific patterns."""
        # Check for Messenger handlers
        if "#[AsMessageHandler]" in content:
            handler = self._detect_messenger_handler(file_path, content)
            if handler:
                result.messenger_handlers.append(handler)

        # Check for modern patterns
        for name, info in SYMFONY_MODERN_PATTERNS.items():
            pattern = self._compiled_symfony_patterns[name]
            if pattern.search(content):
                component = SymfonyModernComponent(
                    file_path=str(file_path),
                    component_name=file_path.stem,
                    component_type=info["type"],
                    symfony_version=info["version"],
                    uses_php_attributes=True
                )
                result.symfony_modern_components.append(component)

    def _detect_messenger_handler(
        self,
        file_path: Path,
        content: str
    ) -> Optional[SymfonyMessengerHandler]:
        """Detect Symfony Messenger handler."""
        class_match = re.search(r'class\s+(\w+)', content)
        if not class_match:
            return None

        handler = SymfonyMessengerHandler(
            file_path=str(file_path),
            handler_class=class_match.group(1),
            handles_message="",
            is_async="Async" in content or "async" in content.lower()
        )

        # Try to detect message class
        invoke_match = re.search(r'__invoke\s*\(\s*(\w+)\s+\$', content)
        if invoke_match:
            handler.handles_message = invoke_match.group(1)

        return handler

    def _calculate_metrics(self, result: PHPModernAnalysisResult) -> None:
        """Calculate analysis metrics."""
        # Count PHP 8 features
        result.php8_feature_count = (
            len(result.php8_features) +
            len(result.php8_enums) +
            len(result.php8_attributes) +
            len(result.readonly_properties) +
            len(result.constructor_promotions)
        )

        # Determine minimum PHP version required
        versions_used = set()
        for feature in result.php8_features:
            versions_used.add(feature.php_version_required)
        if result.php8_enums:
            versions_used.add("8.1")
        if result.readonly_properties:
            versions_used.add("8.1")

        if versions_used:
            max_version = max(versions_used)
            version_map = {
                "8.0": PHPVersion.PHP_8_0,
                "8.1": PHPVersion.PHP_8_1,
                "8.2": PHPVersion.PHP_8_2,
                "8.3": PHPVersion.PHP_8_3,
            }
            result.minimum_php_required = version_map.get(max_version, PHPVersion.PHP_8_0)
            result.detected_php_version = result.minimum_php_required

        # Calculate modernization score (0-100)
        score = 0

        # PHP 8 features usage (up to 40 points)
        if result.php8_feature_count > 0:
            score += min(40, result.php8_feature_count * 2)

        # Composer setup (up to 20 points)
        if result.composer_analysis:
            if result.composer_analysis.psr4_compliant:
                score += 10
            if result.composer_analysis.has_lock_file:
                score += 5
            if result.composer_analysis.abandoned_packages == 0:
                score += 5

        # Framework modern patterns (up to 40 points)
        modern_components = (
            len(result.livewire_components) +
            len(result.laravel_actions) +
            len(result.laravel_modern_components) +
            len(result.symfony_modern_components) +
            len(result.messenger_handlers)
        )
        score += min(40, modern_components * 5)

        result.modernization_score = min(100, score)

    def _generate_recommendations(
        self,
        result: PHPModernAnalysisResult
    ) -> List[Dict[str, Any]]:
        """Generate migration/modernization recommendations."""
        recommendations = []

        # PHP version recommendations
        if result.detected_php_version == PHPVersion.UNKNOWN:
            recommendations.append({
                "category": "php_version",
                "priority": "high",
                "title": "Upgrade to PHP 8.x",
                "description": "No PHP 8.x features detected. Consider upgrading to leverage modern PHP features.",
                "benefits": ["Better performance", "Type safety", "Attributes", "Enums", "Named arguments"]
            })
        elif result.detected_php_version.value < "8.2":
            recommendations.append({
                "category": "php_version",
                "priority": "medium",
                "title": f"Upgrade from PHP {result.detected_php_version.value} to 8.3",
                "description": "Newer PHP versions offer additional features and security improvements.",
                "benefits": ["Readonly classes", "Typed constants", "Performance improvements"]
            })

        # Composer recommendations
        if result.composer_analysis:
            if not result.composer_analysis.psr4_compliant:
                recommendations.append({
                    "category": "autoloading",
                    "priority": "medium",
                    "title": "Migrate to PSR-4 autoloading",
                    "description": "PSR-4 autoloading is the modern standard for PHP class loading.",
                    "benefits": ["Better organization", "Faster autoloading", "Industry standard"]
                })

            if result.composer_analysis.abandoned_packages > 0:
                recommendations.append({
                    "category": "dependencies",
                    "priority": "high",
                    "title": f"Replace {result.composer_analysis.abandoned_packages} abandoned packages",
                    "description": "Some dependencies are no longer maintained.",
                    "benefits": ["Security", "Continued support", "Bug fixes"]
                })

        # Framework-specific recommendations
        if result.framework == FrameworkType.LARAVEL:
            if not result.livewire_components:
                recommendations.append({
                    "category": "laravel",
                    "priority": "low",
                    "title": "Consider Livewire for interactive UIs",
                    "description": "Livewire provides reactive components without writing JavaScript.",
                    "benefits": ["Simpler development", "Less JavaScript", "Laravel integration"]
                })

        if result.framework == FrameworkType.SYMFONY:
            attr_count = sum(1 for c in result.symfony_modern_components if c.uses_php_attributes)
            if attr_count < len(result.symfony_modern_components) / 2:
                recommendations.append({
                    "category": "symfony",
                    "priority": "medium",
                    "title": "Migrate from annotations to PHP attributes",
                    "description": "PHP 8 attributes are the modern replacement for doctrine annotations.",
                    "benefits": ["Native PHP", "Better IDE support", "Type safety"]
                })

        return recommendations

    def get_summary(self, result: PHPModernAnalysisResult) -> Dict[str, Any]:
        """Get a summary of the analysis result."""
        return {
            "php_version": {
                "detected": result.detected_php_version.value,
                "minimum_required": result.minimum_php_required.value
            },
            "framework": {
                "type": result.framework.value,
                "version": result.framework_version
            },
            "php8_features": {
                "total": result.php8_feature_count,
                "enums": len(result.php8_enums),
                "attributes": len(result.php8_attributes),
                "readonly_properties": len(result.readonly_properties),
                "constructor_promotions": len(result.constructor_promotions)
            },
            "modern_components": {
                "livewire": len(result.livewire_components),
                "laravel_actions": len(result.laravel_actions),
                "laravel_modern": len(result.laravel_modern_components),
                "symfony_modern": len(result.symfony_modern_components),
                "messenger_handlers": len(result.messenger_handlers)
            },
            "composer": {
                "total_packages": result.composer_analysis.total_packages if result.composer_analysis else 0,
                "abandoned": result.composer_analysis.abandoned_packages if result.composer_analysis else 0,
                "psr4_compliant": result.composer_analysis.psr4_compliant if result.composer_analysis else False
            },
            "metrics": {
                "files_scanned": result.total_files_scanned,
                "loc": result.total_loc,
                "modernization_score": result.modernization_score,
                "scan_duration_ms": result.scan_duration_ms
            },
            "recommendations_count": len(result.migration_recommendations)
        }
