# backend/app/services/static_analysis/php_extractor.py
"""
PHP Business Rule Extractor - Extracts business rules from PHP code.

Part of Week 112-114: Hybrid Business Rule Extraction Pipeline - Phase 4

Supports:
- Laravel framework patterns
- WordPress patterns
- Generic PHP patterns

Detection patterns:
- Laravel validation, authorization, routing
- WordPress hooks, capabilities, database
- Generic if/switch, try/catch, PDO/MySQLi
"""

from typing import List, Dict, Optional, Tuple
import re
import logging

from .base_business_rule_extractor import BaseBusinessRuleExtractor
from .extraction_models import (
    BusinessRule,
    CodeSymbol,
    RuleType,
    Language,
    ExtractionTier,
    ExtractionMethod,
)

logger = logging.getLogger(__name__)


class PHPBusinessRuleExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from PHP source code.

    Uses regex-enhanced extraction (Tier 2) with framework-specific patterns
    for Laravel, WordPress, and generic PHP applications.
    """

    SUPPORTED_EXTENSIONS = ['.php', '.phtml', '.inc']

    # PHP specific patterns for rule detection
    PHP_PATTERNS: Dict[RuleType, List[str]] = {
        RuleType.VALIDATION: [
            # Laravel validation
            r'\$request\s*->\s*validate\s*\(',             # $request->validate()
            r'Validator\s*::\s*make\s*\(',                 # Validator::make()
            r'\$this\s*->\s*validate\s*\(',                # $this->validate()
            r'validated\s*\(\)',                           # ->validated()
            r'\'required\'|"required"',                    # Validation rule
            r'\'email\'|"email"',                          # Email validation
            r'\'min:\d+\'|"min:\d+"',                      # Min length validation
            r'\'max:\d+\'|"max:\d+"',                      # Max length validation
            r'\'unique:',                                   # Unique validation
            r'\'exists:',                                   # Exists validation
            # Generic PHP validation
            r'if\s*\(\s*empty\s*\(',                       # empty() check
            r'if\s*\(\s*!empty\s*\(',                      # !empty() check
            r'if\s*\(\s*isset\s*\(',                       # isset() check
            r'if\s*\(\s*!isset\s*\(',                      # !isset() check
            r'if\s*\(\s*is_null\s*\(',                     # is_null() check
            r'if\s*\(\s*strlen\s*\(',                      # strlen() check
            r'filter_var\s*\(',                            # filter_var()
            r'preg_match\s*\(',                            # preg_match() validation
            # WordPress sanitization
            r'sanitize_text_field\s*\(',                   # WordPress sanitize
            r'sanitize_email\s*\(',                        # WordPress sanitize email
            r'esc_html\s*\(',                              # WordPress escape
            r'esc_attr\s*\(',                              # WordPress escape attr
            r'wp_kses\s*\(',                               # WordPress KSES
        ],
        RuleType.AUTHORIZATION: [
            # Laravel authorization
            r'\$this\s*->\s*authorize\s*\(',               # $this->authorize()
            r'Gate\s*::\s*allows\s*\(',                    # Gate::allows()
            r'Gate\s*::\s*denies\s*\(',                    # Gate::denies()
            r'Gate\s*::\s*check\s*\(',                     # Gate::check()
            r'->\s*can\s*\(',                              # ->can()
            r'->\s*cannot\s*\(',                           # ->cannot()
            r'->\s*ability\s*\(',                          # ->ability()
            r'@can\s*\(',                                  # Blade @can
            r'@cannot\s*\(',                               # Blade @cannot
            r'middleware\s*\(\s*[\'"]auth',                # auth middleware
            r'middleware\s*\(\s*[\'"]admin',               # admin middleware
            r'middleware\s*\(\s*[\'"]role:',               # role middleware
            r'middleware\s*\(\s*[\'"]permission:',         # permission middleware
            # WordPress capabilities
            r'current_user_can\s*\(',                      # WP capability check
            r'user_can\s*\(',                              # WP user can
            r'is_admin\s*\(\)',                            # WP is_admin
            r'is_user_logged_in\s*\(\)',                   # WP is logged in
            r'wp_verify_nonce\s*\(',                       # WP nonce verify
            r'check_admin_referer\s*\(',                   # WP referer check
            # Generic PHP
            r'if\s*\(\s*\$_SESSION\s*\[',                  # Session check
            r'\$role\s*[=!]=',                             # Role check
            r'\$permission\s*[=!]=',                       # Permission check
            r'isAdmin\s*\(',                               # isAdmin check
            r'hasPermission\s*\(',                         # hasPermission check
        ],
        RuleType.WORKFLOW: [
            # Status/state management
            r'->\s*status\s*=',                            # Status assignment
            r'\$status\s*[=!]=',                           # Status check
            r'->\s*setState\s*\(',                         # setState()
            r'->\s*transition\s*\(',                       # transition()
            r'case\s+[\'"]?(?:pending|approved|rejected|active|inactive)',  # Status cases
            # Laravel workflow patterns
            r'->\s*update\s*\(\s*\[\s*[\'"]status',        # Update status
            r'->\s*where\s*\(\s*[\'"]status',              # Where status
        ],
        RuleType.BRANCHING: [
            r'switch\s*\(',                                # Switch statement
            r'case\s+[\'"]',                               # String case
            r'case\s+\d+',                                 # Numeric case
            r'default\s*:',                                # Default case
            r'match\s*\(',                                 # PHP 8 match expression
        ],
        RuleType.THRESHOLD: [
            r'if\s*\(\s*\$\w+\s*[<>=]+\s*\d+',             # Numeric comparison
            r'if\s*\(\s*count\s*\(',                       # Count check
            r'if\s*\(\s*sizeof\s*\(',                      # sizeof check
            r'->\s*count\s*\(\)\s*[<>=]+\s*\d+',           # Collection count
            r'->\s*take\s*\(\s*\d+',                       # Laravel take/limit
            r'->\s*limit\s*\(\s*\d+',                      # Laravel limit
            r'LIMIT\s+\d+',                                # SQL LIMIT
        ],
        RuleType.DATA_ACCESS: [
            # Laravel Eloquent
            r'::\s*find\s*\(',                             # Model::find()
            r'::\s*findOrFail\s*\(',                       # Model::findOrFail()
            r'::\s*where\s*\(',                            # Model::where()
            r'::\s*create\s*\(',                           # Model::create()
            r'::\s*update\s*\(',                           # Model::update()
            r'::\s*delete\s*\(',                           # Model::delete()
            r'::\s*all\s*\(',                              # Model::all()
            r'::\s*first\s*\(',                            # Model::first()
            r'::\s*get\s*\(',                              # ->get()
            r'->\s*save\s*\(',                             # ->save()
            r'->\s*delete\s*\(',                           # ->delete()
            r'->\s*insert\s*\(',                           # ->insert()
            r'->\s*updateOrCreate\s*\(',                   # ->updateOrCreate()
            r'DB\s*::\s*table\s*\(',                       # DB::table()
            r'DB\s*::\s*select\s*\(',                      # DB::select()
            r'DB\s*::\s*insert\s*\(',                      # DB::insert()
            r'DB\s*::\s*update\s*\(',                      # DB::update()
            r'DB\s*::\s*delete\s*\(',                      # DB::delete()
            # WordPress database
            r'\$wpdb\s*->\s*get_results\s*\(',             # WP get_results
            r'\$wpdb\s*->\s*get_row\s*\(',                 # WP get_row
            r'\$wpdb\s*->\s*get_var\s*\(',                 # WP get_var
            r'\$wpdb\s*->\s*insert\s*\(',                  # WP insert
            r'\$wpdb\s*->\s*update\s*\(',                  # WP update
            r'\$wpdb\s*->\s*delete\s*\(',                  # WP delete
            r'\$wpdb\s*->\s*query\s*\(',                   # WP query
            r'\$wpdb\s*->\s*prepare\s*\(',                 # WP prepare
            r'get_post\s*\(',                              # WP get_post
            r'get_posts\s*\(',                             # WP get_posts
            r'wp_insert_post\s*\(',                        # WP insert post
            r'wp_update_post\s*\(',                        # WP update post
            r'get_option\s*\(',                            # WP get_option
            r'update_option\s*\(',                         # WP update_option
            r'get_user_meta\s*\(',                         # WP get user meta
            r'update_user_meta\s*\(',                      # WP update user meta
            # Generic PHP database
            r'PDO\s*::',                                   # PDO
            r'->\s*prepare\s*\(',                          # PDO prepare
            r'->\s*execute\s*\(',                          # PDO execute
            r'->\s*fetch\s*\(',                            # PDO fetch
            r'->\s*fetchAll\s*\(',                         # PDO fetchAll
            r'mysqli_query\s*\(',                          # mysqli query
            r'->\s*query\s*\(',                            # mysqli OO query
        ],
        RuleType.STATE_MANAGEMENT: [
            r'\$_SESSION\s*\[',                            # Session access
            r'session\s*\(\s*\[?\s*[\'"]',                 # Laravel session
            r'Session\s*::\s*put\s*\(',                    # Laravel Session::put
            r'Session\s*::\s*get\s*\(',                    # Laravel Session::get
            r'session\s*\(\)\s*->\s*put\s*\(',             # session()->put()
            r'session\s*\(\)\s*->\s*get\s*\(',             # session()->get()
            r'Cache\s*::\s*put\s*\(',                      # Laravel Cache::put
            r'Cache\s*::\s*get\s*\(',                      # Laravel Cache::get
            r'cache\s*\(\)\s*->\s*put\s*\(',               # cache()->put()
            r'cache\s*\(\)\s*->\s*get\s*\(',               # cache()->get()
            r'Redis\s*::\s*set\s*\(',                      # Redis set
            r'Redis\s*::\s*get\s*\(',                      # Redis get
            # WordPress transients
            r'set_transient\s*\(',                         # WP set transient
            r'get_transient\s*\(',                         # WP get transient
            r'delete_transient\s*\(',                      # WP delete transient
        ],
        RuleType.ERROR_HANDLING: [
            r'try\s*\{',                                   # Try block
            r'catch\s*\(',                                 # Catch block
            r'finally\s*\{',                               # Finally block
            r'throw\s+new\s+',                             # Throw exception
            r'throw\s+\$',                                 # Re-throw
            r'Exception\s*\(',                             # Exception
            r'abort\s*\(\s*\d{3}',                         # Laravel abort(404)
            r'abort_if\s*\(',                              # Laravel abort_if
            r'abort_unless\s*\(',                          # Laravel abort_unless
            r'Log\s*::\s*error\s*\(',                      # Laravel Log::error
            r'report\s*\(',                                # Laravel report()
            r'error_log\s*\(',                             # PHP error_log
            r'trigger_error\s*\(',                         # PHP trigger_error
            # WordPress error handling
            r'wp_die\s*\(',                                # WP die
            r'is_wp_error\s*\(',                           # WP error check
            r'WP_Error\s*\(',                              # WP Error
        ],
        RuleType.NAVIGATION: [
            r'redirect\s*\(',                              # Laravel redirect
            r'Redirect\s*::\s*to\s*\(',                    # Redirect::to()
            r'Redirect\s*::\s*route\s*\(',                 # Redirect::route()
            r'Redirect\s*::\s*back\s*\(',                  # Redirect::back()
            r'->\s*redirect\s*\(',                         # ->redirect()
            r'return\s+redirect\s*\(',                     # return redirect()
            r'header\s*\(\s*[\'"]Location:',               # header('Location:')
            r'wp_redirect\s*\(',                           # WP redirect
            r'wp_safe_redirect\s*\(',                      # WP safe redirect
        ],
        RuleType.CALCULATION: [
            r'\$\w+\s*=\s*\$\w+\s*[\+\-\*/]\s*\$?\w+',     # Arithmetic
            r'round\s*\(',                                 # round()
            r'floor\s*\(',                                 # floor()
            r'ceil\s*\(',                                  # ceil()
            r'abs\s*\(',                                   # abs()
            r'number_format\s*\(',                         # number_format()
            r'->\s*sum\s*\(',                              # Laravel sum()
            r'->\s*avg\s*\(',                              # Laravel avg()
            r'->\s*max\s*\(',                              # Laravel max()
            r'->\s*min\s*\(',                              # Laravel min()
            r'bcadd\s*\(',                                 # BC math
            r'bcmul\s*\(',                                 # BC math
            r'bcdiv\s*\(',                                 # BC math
        ],
        RuleType.SCHEDULING: [
            r'Carbon\s*::\s*now\s*\(',                     # Carbon::now()
            r'Carbon\s*::\s*parse\s*\(',                   # Carbon::parse()
            r'Carbon\s*::\s*today\s*\(',                   # Carbon::today()
            r'->\s*addDays\s*\(',                          # ->addDays()
            r'->\s*subDays\s*\(',                          # ->subDays()
            r'->\s*diffInDays\s*\(',                       # ->diffInDays()
            r'->\s*isBefore\s*\(',                         # ->isBefore()
            r'->\s*isAfter\s*\(',                          # ->isAfter()
            r'strtotime\s*\(',                             # strtotime()
            r'date\s*\(\s*[\'"]',                          # date()
            r'DateTime\s*::',                              # DateTime
            r'DateInterval\s*::',                          # DateInterval
            r'wp_schedule_event\s*\(',                     # WP cron
            r'wp_schedule_single_event\s*\(',              # WP single event
        ],
    }

    # Symbol detection patterns
    CLASS_PATTERN = re.compile(
        r'^\s*(abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+[\w,\s]+)?',
        re.IGNORECASE | re.MULTILINE
    )

    INTERFACE_PATTERN = re.compile(
        r'^\s*interface\s+(\w+)(?:\s+extends\s+[\w,\s]+)?',
        re.IGNORECASE | re.MULTILINE
    )

    TRAIT_PATTERN = re.compile(
        r'^\s*trait\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    FUNCTION_PATTERN = re.compile(
        r'^\s*(public\s+|private\s+|protected\s+)?(static\s+)?function\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    CONST_PATTERN = re.compile(
        r'^\s*(public\s+|private\s+|protected\s+)?const\s+(\w+)\s*=',
        re.IGNORECASE | re.MULTILINE
    )

    NAMESPACE_PATTERN = re.compile(
        r'^\s*namespace\s+([\w\\]+)',
        re.IGNORECASE | re.MULTILINE
    )

    USE_PATTERN = re.compile(
        r'^\s*use\s+([\w\\]+)',
        re.IGNORECASE | re.MULTILINE
    )

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.FREE,
        project_id: Optional[int] = None,
    ):
        super().__init__(extraction_tier, project_id)
        self._compile_php_patterns()
        self._current_namespace = ""

    def _compile_php_patterns(self):
        """Compile PHP specific patterns."""
        self._php_compiled: Dict[RuleType, List[re.Pattern]] = {}
        for rule_type, patterns in self.PHP_PATTERNS.items():
            self._php_compiled[rule_type] = [
                re.compile(p, re.IGNORECASE)
                for p in patterns
            ]

    def get_supported_extensions(self) -> List[str]:
        return self.SUPPORTED_EXTENSIONS

    def get_language(self) -> Language:
        return Language.PHP

    def get_rule_patterns(self) -> Dict[RuleType, List[str]]:
        """Return PHP specific patterns."""
        return self.PHP_PATTERNS

    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """Extract code symbols from PHP source."""
        symbols = []
        lines = source.split('\n')
        current_class = ""
        self._current_namespace = ""

        for i, line in enumerate(lines, 1):
            # Track namespace
            namespace_match = self.NAMESPACE_PATTERN.search(line)
            if namespace_match:
                self._current_namespace = namespace_match.group(1)

            # Classes
            class_match = self.CLASS_PATTERN.match(line)
            if class_match:
                current_class = class_match.group(2)
                parent_class = class_match.group(3) if class_match.group(3) else ""
                symbols.append(CodeSymbol(
                    name=current_class,
                    symbol_type="class",
                    line_start=i,
                    line_end=self._find_closing_brace(lines, i),
                    docstring=self._extract_docblock(lines, i),
                    parent=parent_class,
                    language=Language.PHP,
                ))

            # Interfaces
            interface_match = self.INTERFACE_PATTERN.match(line)
            if interface_match:
                symbols.append(CodeSymbol(
                    name=interface_match.group(1),
                    symbol_type="interface",
                    line_start=i,
                    line_end=self._find_closing_brace(lines, i),
                    docstring="",
                    parent="",
                    language=Language.PHP,
                ))

            # Traits
            trait_match = self.TRAIT_PATTERN.match(line)
            if trait_match:
                symbols.append(CodeSymbol(
                    name=trait_match.group(1),
                    symbol_type="trait",
                    line_start=i,
                    line_end=self._find_closing_brace(lines, i),
                    docstring="",
                    parent="",
                    language=Language.PHP,
                ))

            # Functions/Methods
            func_match = self.FUNCTION_PATTERN.match(line)
            if func_match:
                visibility = func_match.group(1).strip() if func_match.group(1) else "public"
                is_static = bool(func_match.group(2))
                func_name = func_match.group(3)
                symbols.append(CodeSymbol(
                    name=func_name,
                    symbol_type="method" if current_class else "function",
                    line_start=i,
                    line_end=self._find_closing_brace(lines, i),
                    docstring=self._extract_docblock(lines, i),
                    parent=current_class,
                    language=Language.PHP,
                ))

            # Constants
            const_match = self.CONST_PATTERN.match(line)
            if const_match:
                symbols.append(CodeSymbol(
                    name=const_match.group(2),
                    symbol_type="constant",
                    line_start=i,
                    line_end=i,
                    docstring="",
                    parent=current_class,
                    language=Language.PHP,
                ))

            # Track class end
            if current_class and line.strip() == '}':
                # Check if this is the class closing brace
                brace_count = 0
                for j in range(i - 1, -1, -1):
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    if brace_count == 0:
                        break
                if brace_count <= 0:
                    current_class = ""

        return symbols

    def _find_closing_brace(self, lines: List[str], start: int) -> int:
        """Find the closing brace for a PHP block."""
        brace_count = 0
        found_open = False

        for i in range(start - 1, len(lines)):
            line = lines[i]
            # Remove string literals to avoid counting braces in strings
            line_clean = re.sub(r'"[^"]*"', '', line)
            line_clean = re.sub(r"'[^']*'", '', line_clean)

            brace_count += line_clean.count('{')
            if brace_count > 0:
                found_open = True
            brace_count -= line_clean.count('}')

            if found_open and brace_count == 0:
                return i + 1

        return len(lines)

    def _extract_docblock(self, lines: List[str], line_num: int) -> str:
        """Extract PHPDoc comment before a symbol."""
        doclines = []
        for i in range(line_num - 2, max(0, line_num - 20), -1):
            line = lines[i].strip()
            if line.startswith('*/'):
                continue
            if line.startswith('*') or line.startswith('/**'):
                doclines.insert(0, line.lstrip('/* '))
            elif not line:
                continue
            else:
                break
        return ' '.join(doclines)[:200]

    async def _extract_rules_from_source(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from PHP source."""
        rules = []
        lines = source.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip empty lines and pure comments
            if not stripped or stripped.startswith('//') or stripped.startswith('*'):
                continue

            # Skip PHP open/close tags
            if stripped in ('<?php', '?>', '<?'):
                continue

            # Try each rule type pattern
            for rule_type, patterns in self._php_compiled.items():
                for pattern in patterns:
                    match = pattern.search(line)
                    if match:
                        rule = self._create_rule_from_match(
                            match=match,
                            rule_type=rule_type,
                            line=line,
                            line_num=i,
                            lines=lines,
                            file_path=file_path,
                            symbols=symbols,
                        )
                        if rule:
                            rules.append(rule)
                        break  # Only one rule per line

        return rules

    def _create_rule_from_match(
        self,
        match: re.Match,
        rule_type: RuleType,
        line: str,
        line_num: int,
        lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol],
    ) -> Optional[BusinessRule]:
        """Create a BusinessRule from a regex match."""

        # Extract condition
        condition = match.group(0)

        # For if statements, try to get the full condition
        if rule_type == RuleType.VALIDATION and 'if' in line.lower():
            cond_match = re.search(r'if\s*\((.+?)\)\s*\{?', line, re.IGNORECASE)
            if cond_match:
                condition = cond_match.group(1)

        # Extract action (next line or after condition)
        action = self._extract_action(line, lines, line_num)

        # Extract variables
        variables = self._extract_variables(line)

        # Extract entities
        entities = self._extract_entities(line, variables)

        # Find parent symbol
        parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

        # Calculate confidence
        confidence = self._calculate_confidence(
            rule_type=rule_type,
            condition=condition,
            variables=variables,
            has_clear_action=bool(action),
        )

        # Detect framework for additional context
        framework = self._detect_framework(line)

        # Generate natural language
        natural_language = self._generate_natural_language(rule_type, condition, action)

        return BusinessRule(
            id=self._generate_rule_id(),
            rule_type=rule_type,
            condition=condition[:200],
            action=action[:200],
            source_file=file_path,
            source_lines=(line_num, line_num),
            confidence=confidence,
            natural_language=natural_language,
            variables_involved=variables[:10],
            related_entities=entities[:5],
            language=Language.PHP,
            extraction_method=ExtractionMethod.REGEX,
            extraction_tier=self.extraction_tier,
            code_snippet=line.strip()[:150],
            parent_function=parent_function,
            parent_class=parent_class,
            region=framework,  # Store framework as region
        )

    def _extract_action(self, line: str, lines: List[str], line_num: int) -> str:
        """Extract the action part of a rule."""
        # Check if action is after the pattern on same line
        if '{' in line:
            # Check next line
            if line_num < len(lines):
                next_line = lines[line_num].strip()
                if next_line and not next_line.startswith('//'):
                    return next_line

        # For Laravel/WordPress function calls, action is often the result
        if '->' in line or '::' in line:
            # The entire call is often the action
            return line.strip()

        # Check next line for block content
        if line_num < len(lines):
            next_line = lines[line_num].strip()
            if next_line and not next_line.startswith('//'):
                return next_line

        return "continue"

    def _extract_variables(self, text: str) -> List[str]:
        """Extract variables from PHP code."""
        # PHP variable pattern (with $)
        pattern = r'\$([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, text)

        # PHP keywords/superglobals to exclude
        excludes = {
            'this', '_GET', '_POST', '_REQUEST', '_SESSION', '_COOKIE',
            '_SERVER', '_FILES', '_ENV', 'GLOBALS', 'wpdb',
        }

        return [m for m in matches if m not in excludes]

    def _extract_entities(self, text: str, variables: List[str]) -> List[str]:
        """Extract domain entities from PHP code."""
        entities = set()

        # Class/Model patterns
        entity_patterns = [
            r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\s*::',       # Model::method()
            r'new\s+([A-Z][a-z]+(?:[A-Z][a-z]+)*)',        # new Model()
            r'\'([a-z_]+)\'\s*=>\s*',                      # 'table_name' =>
            r'table\s*\(\s*[\'"]([\w_]+)[\'"]',            # table('name')
            r'wp_(\w+)',                                    # WordPress tables
        ]

        for pattern in entity_patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)

        # Convert PascalCase variables to entities
        for var in variables:
            if len(var) > 2 and var[0].isupper():
                entities.add(var)

        return list(entities)

    def _detect_framework(self, line: str) -> str:
        """Detect which PHP framework patterns are used."""
        if any(p in line for p in ['Laravel', 'Illuminate', 'Eloquent', '::find', '::where']):
            return "Laravel"
        if any(p in line for p in ['wp_', 'WordPress', 'WP_', 'wpdb', 'add_action', 'add_filter', 'current_user_can', 'is_user_logged_in']):
            return "WordPress"
        if any(p in line for p in ['Symfony', 'Doctrine']):
            return "Symfony"
        if any(p in line for p in ['Yii', 'ActiveRecord']):
            return "Yii"
        return "PHP"
