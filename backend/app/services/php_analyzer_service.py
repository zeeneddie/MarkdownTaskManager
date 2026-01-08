"""
PHP Analyzer Service

Week 65 Day 6: Specialized analyzer for PHP legacy code.
Detects PHP 4/5 procedural patterns, deprecated mysql_* functions,
Laravel 4.x/5.x legacy, Symfony 2.x/3.x, and other PHP frameworks.

Features:
- PHP 4/5 procedural code detection
- Deprecated mysql_* function detection (SQL injection risks)
- Legacy Laravel patterns (4.x/5.x)
- Symfony 2.x/3.x patterns
- CodeIgniter/CakePHP legacy detection
- Global variables and include/require patterns
- Security vulnerability detection

Author: Claude Code (Week 65)
Date: 2025-12-12
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.migration_analysis import (
    MigrationAnalysis,
    MigrationModule,
    LegacyPattern,
    FPBreakdown
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PHPClass:
    """Represents a PHP class"""
    file_path: str
    class_name: str
    namespace: Optional[str] = None
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    is_abstract: bool = False
    is_final: bool = False
    loc: int = 0
    complexity: float = 0.0


@dataclass
class PHPFunction:
    """Represents a standalone PHP function"""
    file_path: str
    function_name: str
    parameters: List[str] = field(default_factory=list)
    is_procedural: bool = True
    has_return_type: bool = False
    loc: int = 0


@dataclass
class LaravelComponent:
    """Represents a Laravel component"""
    file_path: str
    component_name: str
    component_type: str  # controller, model, middleware, etc.
    laravel_version: str = "unknown"
    uses_facades: bool = False
    uses_eloquent: bool = False
    route_model_binding: bool = False
    loc: int = 0


@dataclass
class SymfonyComponent:
    """Represents a Symfony component"""
    file_path: str
    component_name: str
    component_type: str  # controller, service, entity, etc.
    symfony_version: str = "unknown"
    uses_annotations: bool = False
    uses_yaml_config: bool = False
    loc: int = 0


@dataclass
class PHPPatternMatch:
    """A detected PHP legacy pattern"""
    pattern_name: str
    pattern_category: str
    file_path: str
    line_number: int
    code_snippet: str
    risk_level: str
    migration_note: str
    migration_target: str
    fp_multiplier: float = 1.0
    is_security_issue: bool = False


@dataclass
class PHPAnalysisResult:
    """Complete PHP analysis result"""
    php_classes: List[PHPClass] = field(default_factory=list)
    php_functions: List[PHPFunction] = field(default_factory=list)
    laravel_components: List[LaravelComponent] = field(default_factory=list)
    symfony_components: List[SymfonyComponent] = field(default_factory=list)
    legacy_patterns: List[PHPPatternMatch] = field(default_factory=list)
    total_php_files: int = 0
    total_loc: int = 0
    php_version_detected: str = "unknown"
    framework_detected: Optional[str] = None
    migration_difficulty: str = "medium"
    security_issues_count: int = 0


# ============================================================================
# PATTERN DEFINITIONS
# ============================================================================

# PHP 4/5 Procedural and Deprecated Patterns
PHP_LEGACY_PATTERNS = {
    "mysql_connect": {
        "pattern": r"mysql_connect\s*\(",
        "risk": "critical",
        "note": "mysql_* functions removed in PHP 7, vulnerable to SQL injection",
        "target": "PDO or MySQLi with prepared statements",
        "multiplier": 2.0,
        "security": True,
    },
    "mysql_query": {
        "pattern": r"mysql_query\s*\(",
        "risk": "critical",
        "note": "mysql_query is deprecated and SQL injection vulnerable",
        "target": "PDO::prepare() with bound parameters",
        "multiplier": 2.0,
        "security": True,
    },
    "mysql_escape_string": {
        "pattern": r"mysql_escape_string\s*\(|mysql_real_escape_string\s*\(",
        "risk": "high",
        "note": "Escaping is not sufficient protection against SQL injection",
        "target": "Prepared statements with PDO or MySQLi",
        "multiplier": 1.8,
        "security": True,
    },
    "mysql_fetch": {
        "pattern": r"mysql_fetch_(array|assoc|row|object)\s*\(",
        "risk": "high",
        "note": "mysql_fetch_* functions removed in PHP 7",
        "target": "PDOStatement::fetch() or mysqli_fetch_*",
        "multiplier": 1.5,
    },
    "ereg_functions": {
        "pattern": r"ereg[i]?\s*\(|ereg[i]?_replace\s*\(",
        "risk": "high",
        "note": "ereg functions removed in PHP 7, use preg_* instead",
        "target": "preg_match() and preg_replace()",
        "multiplier": 1.3,
    },
    "split_function": {
        "pattern": r"(?<![a-zA-Z_])split\s*\(",
        "risk": "medium",
        "note": "split() removed in PHP 7, use explode() or preg_split()",
        "target": "explode() or preg_split()",
        "multiplier": 1.2,
    },
    "global_keyword": {
        "pattern": r"^\s*global\s+\$",
        "risk": "medium",
        "note": "Global variables make code hard to test and maintain",
        "target": "Dependency injection or class properties",
        "multiplier": 1.3,
    },
    "register_globals": {
        "pattern": r"register_globals|import_request_variables",
        "risk": "critical",
        "note": "register_globals removed in PHP 5.4, severe security risk",
        "target": "Use $_GET, $_POST, $_REQUEST explicitly",
        "multiplier": 2.5,
        "security": True,
    },
    "magic_quotes": {
        "pattern": r"magic_quotes_gpc|get_magic_quotes_gpc|magic_quotes_runtime",
        "risk": "high",
        "note": "Magic quotes removed in PHP 5.4",
        "target": "Use proper escaping or prepared statements",
        "multiplier": 1.5,
    },
    "short_open_tag": {
        "pattern": r"<\?\s+(?!php|=)",
        "risk": "low",
        "note": "Short open tags not portable across servers",
        "target": "Use <?php or <?=",
        "multiplier": 1.0,
    },
    "var_keyword": {
        "pattern": r"^\s*var\s+\$",
        "risk": "low",
        "note": "var keyword is PHP 4 syntax",
        "target": "Use public/private/protected visibility",
        "multiplier": 1.1,
    },
    "create_function": {
        "pattern": r"create_function\s*\(",
        "risk": "critical",
        "note": "create_function deprecated in PHP 7.2, security risk (eval)",
        "target": "Use anonymous functions (closures)",
        "multiplier": 2.0,
        "security": True,
    },
    "eval_usage": {
        "pattern": r"(?<![a-zA-Z_])eval\s*\(",
        "risk": "critical",
        "note": "eval() is a severe security risk, allows code injection",
        "target": "Refactor to avoid dynamic code execution",
        "multiplier": 2.5,
        "security": True,
    },
    "extract_usage": {
        "pattern": r"extract\s*\(\s*\$_(GET|POST|REQUEST|COOKIE)",
        "risk": "critical",
        "note": "extract() on user input creates variable injection vulnerability",
        "target": "Access superglobals directly with validation",
        "multiplier": 2.0,
        "security": True,
    },
    "include_variable": {
        "pattern": r"(include|require)(_once)?\s*\(\s*\$",
        "risk": "critical",
        "note": "Dynamic include/require allows Local File Inclusion (LFI)",
        "target": "Use autoloading and whitelisted paths",
        "multiplier": 2.0,
        "security": True,
    },
    "unserialize_user": {
        "pattern": r"unserialize\s*\(\s*\$_(GET|POST|REQUEST|COOKIE)",
        "risk": "critical",
        "note": "unserialize on user input allows object injection attacks",
        "target": "Use JSON encoding or validate/whitelist classes",
        "multiplier": 2.5,
        "security": True,
    },
    "md5_password": {
        "pattern": r"md5\s*\(\s*\$.*password|sha1\s*\(\s*\$.*password",
        "risk": "critical",
        "note": "MD5/SHA1 are not suitable for password hashing",
        "target": "Use password_hash() with PASSWORD_DEFAULT",
        "multiplier": 2.0,
        "security": True,
    },
    "file_get_contents_url": {
        "pattern": r"file_get_contents\s*\(\s*['\"]https?://|file_get_contents\s*\(\s*\$",
        "risk": "high",
        "note": "file_get_contents on URLs can be SSRF vulnerability",
        "target": "Use cURL with proper validation",
        "multiplier": 1.5,
        "security": True,
    },
    "shell_exec": {
        "pattern": r"shell_exec\s*\(|exec\s*\(|system\s*\(|passthru\s*\(|`.*\$.*`",
        "risk": "critical",
        "note": "Shell execution with user input is command injection",
        "target": "Use escapeshellarg/escapeshellcmd or avoid shell",
        "multiplier": 2.5,
        "security": True,
    },
    "header_injection": {
        "pattern": r"header\s*\(\s*['\"]Location:\s*['\"]?\s*\.\s*\$",
        "risk": "high",
        "note": "Header injection vulnerability if user input not sanitized",
        "target": "Validate and sanitize redirect URLs",
        "multiplier": 1.8,
        "security": True,
    },
    "xss_echo": {
        "pattern": r"echo\s+\$_(GET|POST|REQUEST|COOKIE)|print\s+\$_(GET|POST|REQUEST|COOKIE)",
        "risk": "critical",
        "note": "Direct output of user input causes XSS vulnerability",
        "target": "Use htmlspecialchars() or template engine escaping",
        "multiplier": 2.0,
        "security": True,
    },
}

# Laravel Legacy Patterns (4.x/5.x)
LARAVEL_LEGACY_PATTERNS = {
    "laravel4_route": {
        "pattern": r"Route::(get|post|put|delete)\s*\(\s*['\"][^'\"]+['\"]\s*,\s*['\"][^'\"]+@",
        "risk": "medium",
        "note": "Laravel 4 string-based controller routing",
        "target": "Laravel 8+ route syntax with controller classes",
        "multiplier": 1.3,
    },
    "laravel4_filter": {
        "pattern": r"Route::filter\s*\(|->before\s*\(|->after\s*\(",
        "risk": "medium",
        "note": "Laravel 4 route filters replaced by middleware",
        "target": "Use middleware classes",
        "multiplier": 1.4,
    },
    "laravel_facades_string": {
        "pattern": r"['\"](App|Auth|Cache|Config|DB|Event|File|Hash|Input|Lang|Log|Mail|Queue|Redirect|Request|Response|Route|Schema|Session|Storage|URL|Validator|View)['\"]",
        "risk": "low",
        "note": "String-based facade references are less type-safe",
        "target": "Use facade class imports",
        "multiplier": 1.1,
    },
    "laravel_input_facade": {
        "pattern": r"Input::(get|all|has|only|except)\s*\(",
        "risk": "medium",
        "note": "Input facade deprecated in Laravel 5.x",
        "target": "Use Request injection or request() helper",
        "multiplier": 1.3,
    },
    "eloquent_mass_assign": {
        "pattern": r"\$fillable\s*=\s*\[\s*\]|\$guarded\s*=\s*\[\s*\]",
        "risk": "high",
        "note": "Empty fillable/guarded allows mass assignment vulnerability",
        "target": "Explicitly define fillable or use guarded = ['id']",
        "multiplier": 1.5,
        "security": True,
    },
    "laravel_raw_query": {
        "pattern": r"DB::raw\s*\(\s*['\"].*\$|DB::select\s*\(\s*['\"].*\$",
        "risk": "critical",
        "note": "Raw queries with variables are SQL injection risk",
        "target": "Use query builder bindings or Eloquent",
        "multiplier": 2.0,
        "security": True,
    },
    "laravel4_queue": {
        "pattern": r"Queue::push\s*\(\s*['\"]",
        "risk": "medium",
        "note": "Laravel 4 queue syntax with string job names",
        "target": "Use job classes with dispatch()",
        "multiplier": 1.3,
    },
    "laravel_array_helper": {
        "pattern": r"array_(get|set|has|forget|pull|first|last)\s*\(",
        "risk": "low",
        "note": "Laravel array helpers moved to Arr facade in Laravel 6+",
        "target": "Use Arr::get(), Arr::set(), etc.",
        "multiplier": 1.1,
    },
    "laravel_str_helper": {
        "pattern": r"str_(slug|limit|contains|start|finish|random|plural|singular)\s*\(",
        "risk": "low",
        "note": "Laravel string helpers moved to Str facade",
        "target": "Use Str::slug(), Str::limit(), etc.",
        "multiplier": 1.1,
    },
    "blade_raw_php": {
        "pattern": r"@php\s*\n.*\n\s*@endphp|<\?php.*\?>",
        "risk": "medium",
        "note": "Raw PHP in Blade templates reduces separation of concerns",
        "target": "Move logic to controllers or view composers",
        "multiplier": 1.2,
    },
    "laravel_env_direct": {
        "pattern": r"env\s*\(\s*['\"][^'\"]+['\"]\s*\)(?!.*config)",
        "risk": "medium",
        "note": "Direct env() calls fail when config is cached",
        "target": "Use config() with env() only in config files",
        "multiplier": 1.3,
    },
}

# Symfony Legacy Patterns (2.x/3.x)
SYMFONY_LEGACY_PATTERNS = {
    "symfony2_annotation": {
        "pattern": r"@Route\s*\(|@Method\s*\(|@Template\s*\(",
        "risk": "low",
        "note": "Symfony annotations work but attributes are preferred in PHP 8",
        "target": "Use PHP 8 attributes: #[Route()]",
        "multiplier": 1.2,
    },
    "symfony_container_get": {
        "pattern": r"\$this->container->get\s*\(|\$container->get\s*\(",
        "risk": "medium",
        "note": "Direct container access is service locator anti-pattern",
        "target": "Use constructor dependency injection",
        "multiplier": 1.4,
    },
    "symfony_get_doctrine": {
        "pattern": r"\$this->getDoctrine\s*\(\)",
        "risk": "medium",
        "note": "getDoctrine() deprecated in Symfony 5.4",
        "target": "Inject EntityManagerInterface or Repository",
        "multiplier": 1.3,
    },
    "symfony_yaml_routing": {
        "pattern": r"routing\.ya?ml",
        "risk": "low",
        "note": "YAML routing works but annotations/attributes are preferred",
        "target": "Use PHP attributes for routing",
        "multiplier": 1.1,
    },
    "symfony_twig_extension": {
        "pattern": r"extends\s+\\?Twig_Extension(?!_)|\bTwig_Extension\b",
        "risk": "high",
        "note": "Twig_Extension class renamed in Twig 2.x/3.x",
        "target": "Extend AbstractExtension",
        "multiplier": 1.5,
    },
    "symfony_form_builder": {
        "pattern": r"->add\s*\(\s*['\"][^'\"]+['\"]\s*,\s*['\"]text['\"]",
        "risk": "low",
        "note": "String form types deprecated, use class constants",
        "target": "Use TextType::class, etc.",
        "multiplier": 1.2,
    },
    "symfony_security_yaml": {
        "pattern": r"security:\s*\n\s*encoders:|password_hashers:",
        "risk": "medium",
        "note": "Security encoders renamed to password_hashers in Symfony 5.3",
        "target": "Use password_hashers configuration",
        "multiplier": 1.3,
    },
    "doctrine_annotation_reader": {
        "pattern": r"AnnotationReader|@ORM\\",
        "risk": "low",
        "note": "Doctrine annotations work but PHP 8 attributes are preferred",
        "target": "Use #[ORM\\Entity], #[ORM\\Column], etc.",
        "multiplier": 1.2,
    },
    "symfony_validator_constraints": {
        "pattern": r"@Assert\\",
        "risk": "low",
        "note": "Validator annotations work but PHP 8 attributes are preferred",
        "target": "Use #[Assert\\NotBlank], etc.",
        "multiplier": 1.1,
    },
}

# CodeIgniter/CakePHP Legacy Patterns
FRAMEWORK_LEGACY_PATTERNS = {
    "codeigniter_query": {
        "pattern": r"\$this->db->query\s*\(\s*['\"].*\$",
        "risk": "critical",
        "note": "CodeIgniter raw query with variables is SQL injection",
        "target": "Use query builder with bindings",
        "multiplier": 2.0,
        "security": True,
    },
    "codeigniter_active_record": {
        "pattern": r"\$this->db->(get|insert|update|delete)\s*\(",
        "risk": "low",
        "note": "CodeIgniter Active Record pattern",
        "target": "Consider Laravel Eloquent or Doctrine",
        "multiplier": 1.2,
    },
    "codeigniter_session": {
        "pattern": r"\$this->session->userdata\s*\(",
        "risk": "medium",
        "note": "CodeIgniter 3.x session syntax",
        "target": "Use CodeIgniter 4.x Session library",
        "multiplier": 1.3,
    },
    "cakephp_find": {
        "pattern": r"\$this->\w+->find\s*\(\s*['\"]all['\"]\s*,",
        "risk": "low",
        "note": "CakePHP 2.x find syntax",
        "target": "Use CakePHP 4.x ORM syntax",
        "multiplier": 1.2,
    },
    "cakephp_controller": {
        "pattern": r"class\s+\w+Controller\s+extends\s+AppController",
        "risk": "low",
        "note": "CakePHP controller detected",
        "target": "Consider migration to Laravel or Symfony",
        "multiplier": 1.0,
    },
    "wordpress_wpdb": {
        "pattern": r"\$wpdb->query\s*\(\s*['\"].*\$|\$wpdb->prepare\s*\(",
        "risk": "high",
        "note": "WordPress direct database access",
        "target": "Use WordPress APIs or consider headless CMS",
        "multiplier": 1.5,
    },
    "wordpress_nonce": {
        "pattern": r"wp_nonce_field|check_admin_referer|wp_verify_nonce",
        "risk": "low",
        "note": "WordPress CSRF protection",
        "target": "Framework-native CSRF protection",
        "multiplier": 1.0,
    },
}


# ============================================================================
# PHP ANALYZER SERVICE
# ============================================================================

class PHPAnalyzerService:
    """
    Specialized analyzer for PHP legacy code.

    Analyzes:
    - PHP 4/5 procedural code
    - Deprecated mysql_* functions
    - Laravel 4.x/5.x legacy patterns
    - Symfony 2.x/3.x patterns
    - CodeIgniter/CakePHP legacy
    - Security vulnerabilities
    """

    PHP_EXTENSIONS = {".php", ".phtml", ".php3", ".php4", ".php5", ".phps"}
    CONFIG_FILES = {"composer.json", "artisan", "config/app.php", "app/config/config.yml"}
    SKIP_DIRS = {"vendor", "node_modules", ".git", "cache", "storage/framework"}

    def __init__(self, db: AsyncSession):
        """Initialize with database session"""
        self.db = db
        self.result = PHPAnalysisResult()

    async def analyze(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> PHPAnalysisResult:
        """
        Perform complete PHP analysis.

        Args:
            analysis: Parent MigrationAnalysis record
            repo_path: Path to repository

        Returns:
            PHPAnalysisResult with all findings
        """
        logger.info(f"Starting PHP analysis for {repo_path}")

        # Phase 1: Detect framework
        self._detect_framework(repo_path)

        # Phase 2: Scan PHP classes
        await self._analyze_classes(analysis, repo_path)

        # Phase 3: Scan standalone functions
        await self._analyze_functions(analysis, repo_path)

        # Phase 4: Analyze Laravel components (if detected)
        if self.result.framework_detected == "laravel":
            await self._analyze_laravel(analysis, repo_path)

        # Phase 5: Analyze Symfony components (if detected)
        if self.result.framework_detected == "symfony":
            await self._analyze_symfony(analysis, repo_path)

        # Phase 6: Detect all legacy patterns
        await self._detect_legacy_patterns(analysis, repo_path)

        # Phase 7: Calculate metrics
        self._calculate_metrics()

        logger.info(
            f"PHP analysis complete: {len(self.result.php_classes)} classes, "
            f"{len(self.result.php_functions)} functions, "
            f"{len(self.result.legacy_patterns)} patterns, "
            f"{self.result.security_issues_count} security issues"
        )

        return self.result

    def _detect_framework(self, repo_path: Path) -> None:
        """Detect which PHP framework is used"""
        # Check for Laravel
        if (repo_path / "artisan").exists():
            self.result.framework_detected = "laravel"
            # Detect Laravel version from composer.json
            composer_path = repo_path / "composer.json"
            if composer_path.exists():
                try:
                    composer = json.loads(composer_path.read_text())
                    laravel_version = composer.get("require", {}).get("laravel/framework", "unknown")
                    logger.info(f"Detected Laravel version: {laravel_version}")
                except Exception:
                    pass
            return

        # Check for Symfony
        if (repo_path / "bin" / "console").exists() or (repo_path / "symfony.lock").exists():
            self.result.framework_detected = "symfony"
            return

        # Check for CodeIgniter
        if (repo_path / "system" / "core" / "CodeIgniter.php").exists():
            self.result.framework_detected = "codeigniter"
            return

        # Check for CakePHP
        if (repo_path / "config" / "bootstrap.php").exists() and (repo_path / "src" / "Controller").exists():
            self.result.framework_detected = "cakephp"
            return

        # Check for WordPress
        if (repo_path / "wp-config.php").exists() or (repo_path / "wp-includes").exists():
            self.result.framework_detected = "wordpress"
            return

        # Plain PHP
        self.result.framework_detected = "plain_php"

    async def _analyze_classes(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze PHP classes"""
        logger.info("Analyzing PHP classes...")

        for php_path in repo_path.rglob("*.php"):
            if self._should_skip(php_path):
                continue

            try:
                content = php_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            self.result.total_php_files += 1
            self.result.total_loc += len([l for l in content.splitlines() if l.strip()])

            # Find classes
            class_pattern = r"(?:abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?"
            for match in re.finditer(class_pattern, content):
                php_class = PHPClass(
                    file_path=str(php_path.relative_to(repo_path)),
                    class_name=match.group(1),
                    extends=match.group(2),
                    implements=match.group(3).split(",") if match.group(3) else [],
                    is_abstract="abstract" in content[:match.start()].split("\n")[-1],
                    is_final="final" in content[:match.start()].split("\n")[-1],
                )

                # Extract namespace
                ns_match = re.search(r"namespace\s+([\w\\]+);", content)
                if ns_match:
                    php_class.namespace = ns_match.group(1)

                # Extract methods
                php_class.methods = re.findall(
                    r"(?:public|private|protected)\s+function\s+(\w+)\s*\(",
                    content
                )

                # Extract properties
                php_class.properties = re.findall(
                    r"(?:public|private|protected)\s+(?:static\s+)?\$(\w+)",
                    content
                )

                # Extract traits
                php_class.traits = re.findall(r"use\s+(\w+);", content)

                # Calculate LOC and complexity
                php_class.loc = len([l for l in content.splitlines() if l.strip()])
                php_class.complexity = len(php_class.methods) * 1.5 + len(php_class.properties) * 0.5

                self.result.php_classes.append(php_class)

                # Create module record
                db_module = MigrationModule(
                    analysis_id=analysis.id,
                    name=php_class.class_name,
                    module_type="php_class",
                    stack_type=self.result.framework_detected or "php",
                    file_path=str(php_path.relative_to(repo_path)),
                    loc=php_class.loc,
                    cyclomatic_complexity=php_class.complexity,
                    migration_difficulty=self._assess_class_difficulty(php_class),
                    migration_target="Modern PHP 8+ with proper typing",
                )
                self.db.add(db_module)

        await self.db.commit()

    async def _analyze_functions(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze standalone PHP functions (procedural code)"""
        logger.info("Analyzing PHP functions...")

        for php_path in repo_path.rglob("*.php"):
            if self._should_skip(php_path):
                continue

            try:
                content = php_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Find functions not inside classes
            # Simple heuristic: functions defined before any class or at file level
            func_pattern = r"^function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*(\w+))?"
            for match in re.finditer(func_pattern, content, re.MULTILINE):
                php_func = PHPFunction(
                    file_path=str(php_path.relative_to(repo_path)),
                    function_name=match.group(1),
                    parameters=match.group(2).split(",") if match.group(2) else [],
                    has_return_type=match.group(3) is not None,
                )
                self.result.php_functions.append(php_func)

    async def _analyze_laravel(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze Laravel-specific components"""
        logger.info("Analyzing Laravel components...")

        # Controllers
        controllers_path = repo_path / "app" / "Http" / "Controllers"
        if controllers_path.exists():
            for ctrl_path in controllers_path.rglob("*.php"):
                try:
                    content = ctrl_path.read_text(encoding="utf-8", errors="ignore")
                    name_match = re.search(r"class\s+(\w+)", content)
                    if name_match:
                        component = LaravelComponent(
                            file_path=str(ctrl_path.relative_to(repo_path)),
                            component_name=name_match.group(1),
                            component_type="controller",
                            uses_facades=bool(re.search(r"use\s+Illuminate\\Support\\Facades\\", content)),
                            loc=len([l for l in content.splitlines() if l.strip()]),
                        )
                        self.result.laravel_components.append(component)
                except Exception:
                    continue

        # Models
        models_path = repo_path / "app" / "Models"
        if not models_path.exists():
            models_path = repo_path / "app"  # Laravel 7 and earlier

        for model_path in models_path.rglob("*.php"):
            if "Controller" in model_path.name:
                continue
            try:
                content = model_path.read_text(encoding="utf-8", errors="ignore")
                if "extends Model" in content or "extends Eloquent" in content:
                    name_match = re.search(r"class\s+(\w+)", content)
                    if name_match:
                        component = LaravelComponent(
                            file_path=str(model_path.relative_to(repo_path)),
                            component_name=name_match.group(1),
                            component_type="model",
                            uses_eloquent=True,
                            loc=len([l for l in content.splitlines() if l.strip()]),
                        )
                        self.result.laravel_components.append(component)
            except Exception:
                continue

    async def _analyze_symfony(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze Symfony-specific components"""
        logger.info("Analyzing Symfony components...")

        # Controllers
        src_path = repo_path / "src"
        if src_path.exists():
            for ctrl_path in src_path.rglob("*Controller.php"):
                try:
                    content = ctrl_path.read_text(encoding="utf-8", errors="ignore")
                    name_match = re.search(r"class\s+(\w+)", content)
                    if name_match:
                        component = SymfonyComponent(
                            file_path=str(ctrl_path.relative_to(repo_path)),
                            component_name=name_match.group(1),
                            component_type="controller",
                            uses_annotations=bool(re.search(r"@Route|@Method", content)),
                            loc=len([l for l in content.splitlines() if l.strip()]),
                        )
                        self.result.symfony_components.append(component)
                except Exception:
                    continue

            # Entities
            for entity_path in src_path.rglob("**/Entity/*.php"):
                try:
                    content = entity_path.read_text(encoding="utf-8", errors="ignore")
                    name_match = re.search(r"class\s+(\w+)", content)
                    if name_match:
                        component = SymfonyComponent(
                            file_path=str(entity_path.relative_to(repo_path)),
                            component_name=name_match.group(1),
                            component_type="entity",
                            uses_annotations=bool(re.search(r"@ORM\\", content)),
                            loc=len([l for l in content.splitlines() if l.strip()]),
                        )
                        self.result.symfony_components.append(component)
                except Exception:
                    continue

    async def _detect_legacy_patterns(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Detect legacy patterns across all PHP files"""
        logger.info("Detecting PHP legacy patterns...")

        # Combine all pattern sets
        all_patterns = {}
        all_patterns.update({f"php_{k}": {**v, "category": "php_legacy"} for k, v in PHP_LEGACY_PATTERNS.items()})

        if self.result.framework_detected == "laravel":
            all_patterns.update({f"laravel_{k}": {**v, "category": "laravel"} for k, v in LARAVEL_LEGACY_PATTERNS.items()})

        if self.result.framework_detected == "symfony":
            all_patterns.update({f"symfony_{k}": {**v, "category": "symfony"} for k, v in SYMFONY_LEGACY_PATTERNS.items()})

        # Add framework legacy patterns
        all_patterns.update({f"framework_{k}": {**v, "category": "framework"} for k, v in FRAMEWORK_LEGACY_PATTERNS.items()})

        for php_path in repo_path.rglob("*.php"):
            if self._should_skip(php_path):
                continue

            try:
                content = php_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern_name, pattern_def in all_patterns.items():
                try:
                    matches = list(re.finditer(pattern_def["pattern"], content, re.MULTILINE | re.IGNORECASE))
                except re.error:
                    continue

                for match in matches[:5]:  # Limit per pattern per file
                    line_num = content[:match.start()].count('\n') + 1

                    is_security = pattern_def.get("security", False)
                    if is_security:
                        self.result.security_issues_count += 1

                    # Create pattern match
                    pattern_match = PHPPatternMatch(
                        pattern_name=pattern_name,
                        pattern_category=pattern_def["category"],
                        file_path=str(php_path.relative_to(repo_path)),
                        line_number=line_num,
                        code_snippet=match.group()[:100],
                        risk_level=pattern_def["risk"],
                        migration_note=pattern_def["note"],
                        migration_target=pattern_def["target"],
                        fp_multiplier=pattern_def.get("multiplier", 1.0),
                        is_security_issue=is_security,
                    )
                    self.result.legacy_patterns.append(pattern_match)

                    # Store in database
                    db_pattern = LegacyPattern(
                        analysis_id=analysis.id,
                        pattern_name=pattern_name,
                        pattern_category=pattern_def["category"],
                        file_path=str(php_path.relative_to(repo_path)),
                        line_number=line_num,
                        code_snippet=match.group()[:200],
                        risk_level=pattern_def["risk"],
                        fp_multiplier=pattern_def.get("multiplier", 1.0),
                        migration_note=pattern_def["note"],
                        migration_target=pattern_def["target"],
                        is_security_issue=is_security,
                    )
                    self.db.add(db_pattern)

        await self.db.commit()

    def _calculate_metrics(self) -> None:
        """Calculate overall metrics"""
        # Determine PHP version from patterns
        has_php4 = any("var_keyword" in p.pattern_name for p in self.result.legacy_patterns)
        has_mysql_ext = any("mysql_" in p.pattern_name for p in self.result.legacy_patterns)

        if has_php4:
            self.result.php_version_detected = "PHP 4.x/5.x"
        elif has_mysql_ext:
            self.result.php_version_detected = "PHP 5.x (pre-7.0)"
        else:
            self.result.php_version_detected = "PHP 7.x+"

        # Migration difficulty
        critical_patterns = sum(1 for p in self.result.legacy_patterns if p.risk_level == "critical")
        high_patterns = sum(1 for p in self.result.legacy_patterns if p.risk_level == "high")
        security_issues = self.result.security_issues_count

        if critical_patterns > 10 or security_issues > 20:
            self.result.migration_difficulty = "complex"
        elif critical_patterns > 5 or high_patterns > 20 or security_issues > 10:
            self.result.migration_difficulty = "hard"
        elif high_patterns > 5 or critical_patterns > 0:
            self.result.migration_difficulty = "medium"
        else:
            self.result.migration_difficulty = "easy"

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        return any(skip in file_path.parts for skip in self.SKIP_DIRS)

    def _assess_class_difficulty(self, php_class: PHPClass) -> str:
        """Assess migration difficulty for a PHP class"""
        score = len(php_class.methods) + len(php_class.properties) * 0.5
        if php_class.traits:
            score += len(php_class.traits) * 2

        if score > 30:
            return "complex"
        elif score > 15:
            return "hard"
        elif score > 5:
            return "medium"
        return "easy"


def get_php_analyzer_service(db: AsyncSession) -> PHPAnalyzerService:
    """Factory function to create PHPAnalyzerService instance"""
    return PHPAnalyzerService(db)
