# backend/app/services/static_analysis/aspx_extractor.py
"""
ASPX/ASCX Business Rule Extractor - Extracts business rules from ASP.NET WebForms markup.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline

Supports:
- ASP.NET WebForms pages (.aspx)
- ASP.NET User Controls (.ascx)
- Master pages (.master)
- Inline code blocks (<% %>, <%= %>, <%# %>)
- Server controls with validation
- Data binding expressions

Detection patterns:
- Inline VB.NET/C# code blocks
- Data binding expressions (<%# %>)
- Validation controls (RequiredFieldValidator, etc.)
- Server control event handlers
- Page directives (Language detection)
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


class ASPXExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from ASP.NET WebForms markup (.aspx, .ascx, .master).

    Handles:
    - Mixed HTML/ASP.NET content
    - Inline code blocks (<% code %>, <%= expression %>, <%# binding %>)
    - Server control validation
    - Event handlers in markup
    - Page/Control directives for language detection
    """

    SUPPORTED_EXTENSIONS = ['.aspx', '.ascx', '.master']

    # ASPX specific patterns
    ASPX_PATTERNS: Dict[RuleType, List[str]] = {
        RuleType.VALIDATION: [
            # Validation controls
            r'<asp:RequiredFieldValidator[^>]+ControlToValidate\s*=\s*["\']([^"\']+)',
            r'<asp:RangeValidator[^>]+MinimumValue\s*=\s*["\']([^"\']+)',
            r'<asp:RegularExpressionValidator[^>]+ValidationExpression\s*=\s*["\']([^"\']+)',
            r'<asp:CompareValidator[^>]+ControlToCompare\s*=\s*["\']([^"\']+)',
            r'<asp:CustomValidator[^>]+ClientValidationFunction\s*=\s*["\']([^"\']+)',
            # Inline validation
            r'<%\s*If\s+(.+?)\s+Then',
            r'<%\s*if\s*\((.+?)\)',
        ],
        RuleType.AUTHORIZATION: [
            # Authorization patterns
            r'<%#\s*Eval\s*\(\s*["\'](?:CanEdit|CanView|CanDelete|HasPermission)',
            r'Visible\s*=\s*["\']<%#\s*.*(?:IsAdmin|HasRole|IsAuthorized)',
            r'<location\s+path\s*=\s*["\'][^"\']+["\']>\s*<authorization>',
        ],
        RuleType.BRANCHING: [
            # Conditional rendering
            r'Visible\s*=\s*["\']<%#\s*(.+?)%>["\']',
            r'Enabled\s*=\s*["\']<%#\s*(.+?)%>["\']',
            r'<%\s*If\s+(.+?)\s+Then\s*%>',
            r'<%\s*if\s*\((.+?)\)\s*{?\s*%>',
        ],
        RuleType.DATA_ACCESS: [
            # Data binding
            r'<%#\s*Eval\s*\(\s*["\'](\w+)["\']',
            r'<%#\s*Bind\s*\(\s*["\'](\w+)["\']',
            r'<%#\s*DataBinder\.Eval\s*\(',
            r'DataSourceID\s*=\s*["\']([^"\']+)',
            r'SelectCommand\s*=\s*["\']([^"\']+)',
            r'InsertCommand\s*=\s*["\']([^"\']+)',
            r'UpdateCommand\s*=\s*["\']([^"\']+)',
            r'DeleteCommand\s*=\s*["\']([^"\']+)',
        ],
        RuleType.NAVIGATION: [
            # Navigation patterns
            r'Response\.Redirect\s*\(\s*["\']([^"\']+)',
            r'NavigateUrl\s*=\s*["\']([^"\']+)',
            r'PostBackUrl\s*=\s*["\']([^"\']+)',
            r'<asp:HyperLink[^>]+NavigateUrl\s*=\s*["\']([^"\']+)',
        ],
        RuleType.WORKFLOW: [
            # Event handlers
            r'On(?:Click|Command|TextChanged|SelectedIndexChanged)\s*=\s*["\'](\w+)',
            r'On(?:Load|Init|PreRender|Unload)\s*=\s*["\'](\w+)',
            r'OnRowCommand\s*=\s*["\'](\w+)',
            r'OnItemCommand\s*=\s*["\'](\w+)',
        ],
        RuleType.STATE_MANAGEMENT: [
            # State access in markup
            r'<%#\s*Session\s*\[\s*["\'](\w+)',
            r'<%#\s*ViewState\s*\[\s*["\'](\w+)',
            r'<%=\s*Session\s*\[\s*["\'](\w+)',
            r'<%=\s*ViewState\s*\[\s*["\'](\w+)',
            r'<%=\s*Request\s*\[\s*["\'](\w+)',
            r'<%=\s*Request\.QueryString\s*\[\s*["\'](\w+)',
        ],
        RuleType.CALCULATION: [
            # Calculated expressions
            r'<%#\s*(?:Convert|Math|Decimal|Int32)\.\w+\s*\(',
            r'<%=\s*(?:Convert|Math|Decimal|Int32)\.\w+\s*\(',
            r'<%#\s*\(\s*\w+\s*[+\-*/]\s*\w+\s*\)',
        ],
        RuleType.CONSTRAINT: [
            # Control constraints
            r'MaxLength\s*=\s*["\'](\d+)',
            r'MinimumValue\s*=\s*["\']([^"\']+)',
            r'MaximumValue\s*=\s*["\']([^"\']+)',
            r'Rows\s*=\s*["\'](\d+)',
            r'Columns\s*=\s*["\'](\d+)',
        ],
    }

    # Page directive pattern for language detection
    PAGE_DIRECTIVE_PATTERN = re.compile(
        r'<%@\s*(?:Page|Control|Master)[^%]*Language\s*=\s*["\'](\w+)["\']',
        re.IGNORECASE
    )

    # Inline code block patterns
    CODE_BLOCK_PATTERN = re.compile(r'<%(?!@)(?!=)(?!#)(.+?)%>', re.DOTALL)
    EXPRESSION_PATTERN = re.compile(r'<%=(.+?)%>', re.DOTALL)
    BINDING_PATTERN = re.compile(r'<%#(.+?)%>', re.DOTALL)
    DIRECTIVE_PATTERN = re.compile(r'<%@(.+?)%>', re.DOTALL)

    # Server control pattern
    SERVER_CONTROL_PATTERN = re.compile(
        r'<asp:(\w+)[^>]*runat\s*=\s*["\']server["\'][^>]*>',
        re.IGNORECASE | re.DOTALL
    )

    # Validation control pattern
    VALIDATION_CONTROL_PATTERN = re.compile(
        r'<asp:(\w*Validator)[^>]*>',
        re.IGNORECASE | re.DOTALL
    )

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.FREE,
        project_id: Optional[int] = None,
    ):
        super().__init__(extraction_tier, project_id)
        self._compile_aspx_patterns()

    def _compile_aspx_patterns(self):
        """Compile ASPX specific patterns."""
        self._aspx_compiled: Dict[RuleType, List[re.Pattern]] = {}
        for rule_type, patterns in self.ASPX_PATTERNS.items():
            self._aspx_compiled[rule_type] = [
                re.compile(p, re.IGNORECASE | re.DOTALL)
                for p in patterns
            ]

    def get_supported_extensions(self) -> List[str]:
        return self.SUPPORTED_EXTENSIONS

    def get_language(self) -> Language:
        return Language.ASPX

    def get_rule_patterns(self) -> Dict[RuleType, List[str]]:
        """Return ASPX specific patterns."""
        return self.ASPX_PATTERNS

    def _detect_code_language(self, source: str) -> str:
        """
        Detect the code language from page directive.
        Returns 'VB' or 'C#', defaults to 'VB'.
        """
        match = self.PAGE_DIRECTIVE_PATTERN.search(source)
        if match:
            lang = match.group(1)
            # Check for C# variations (case-insensitive)
            if lang.upper() in ('C#', 'CS', 'CSHARP') or lang == 'C#':
                return 'C#'
            elif lang.upper() in ('VB', 'VB.NET', 'VBNET'):
                return 'VB'
        # Also check for literal C# in the source
        if 'Language="C#"' in source or "Language='C#'" in source:
            return 'C#'
        return 'VB'  # Default for legacy ASP.NET

    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """Extract code symbols from ASPX source."""
        symbols = []
        lines = source.split('\n')
        code_language = self._detect_code_language(source)

        # Extract page/control directive info
        for i, line in enumerate(lines, 1):
            # Page directive
            if '<%@' in line and ('Page' in line or 'Control' in line or 'Master' in line):
                directive_type = 'page' if 'Page' in line else ('control' if 'Control' in line else 'master')
                symbols.append(CodeSymbol(
                    name=self._extract_page_name(line, file_path),
                    symbol_type=directive_type,
                    line_start=i,
                    line_end=i,
                    docstring=f"ASPX {directive_type} ({code_language})",
                    parent="",
                    language=Language.ASPX,
                ))

            # Server controls (as symbols)
            for match in self.SERVER_CONTROL_PATTERN.finditer(line):
                control_type = match.group(1)
                control_id = self._extract_control_id(line)
                if control_id:
                    symbols.append(CodeSymbol(
                        name=control_id,
                        symbol_type=f"asp:{control_type}",
                        line_start=i,
                        line_end=i,
                        docstring="",
                        parent="",
                        language=Language.ASPX,
                    ))

        return symbols

    def _extract_page_name(self, line: str, file_path: str) -> str:
        """Extract page name from directive or filename."""
        # Try to get from Inherits
        inherits_match = re.search(r'Inherits\s*=\s*["\']([^"\']+)', line, re.IGNORECASE)
        if inherits_match:
            return inherits_match.group(1).split('.')[-1]

        # Try to get from CodeFile
        codefile_match = re.search(r'CodeFile\s*=\s*["\']([^"\']+)', line, re.IGNORECASE)
        if codefile_match:
            return codefile_match.group(1).replace('.vb', '').replace('.cs', '')

        # Fallback to filename
        import os
        return os.path.basename(file_path).split('.')[0]

    def _extract_control_id(self, line: str) -> Optional[str]:
        """Extract control ID from server control markup."""
        id_match = re.search(r'\bID\s*=\s*["\'](\w+)', line, re.IGNORECASE)
        return id_match.group(1) if id_match else None

    async def _extract_rules_from_source(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from ASPX source."""
        rules = []
        lines = source.split('\n')
        code_language = self._detect_code_language(source)

        # First pass: Extract validation controls (may span multiple lines)
        self._extract_validation_controls(source, file_path, symbols, rules)

        # Second pass: Extract multi-line code blocks
        self._extract_multiline_code_blocks(source, file_path, symbols, rules, code_language)

        for i, line in enumerate(lines, 1):
            # Process data binding expressions
            self._extract_binding_rules(line, i, file_path, symbols, rules)

            # Process inline code blocks
            self._extract_code_block_rules(line, i, lines, file_path, symbols, rules, code_language)

            # Process server control attributes
            self._extract_control_rules(line, i, file_path, symbols, rules)

        return rules

    def _extract_validation_controls(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol],
        rules: List[BusinessRule],
    ):
        """Extract validation rules from validation controls (handles multi-line tags)."""
        # Pattern to match complete validator tags (may span multiple lines)
        validator_pattern = re.compile(
            r'<asp:(\w*Validator)\s+([^>]+?)(?:/>|>)',
            re.IGNORECASE | re.DOTALL
        )

        for match in validator_pattern.finditer(source):
            validator_type = match.group(1)
            attributes = match.group(2)

            # Find line number
            line_num = source[:match.start()].count('\n') + 1

            # Extract control being validated
            ctrl_match = re.search(r'ControlToValidate\s*=\s*["\'](\w+)', attributes, re.IGNORECASE)
            control_to_validate = ctrl_match.group(1) if ctrl_match else "field"

            # Extract error message
            err_match = re.search(r'ErrorMessage\s*=\s*["\']([^"\']+)', attributes, re.IGNORECASE)
            error_message = err_match.group(1) if err_match else ""

            # Build condition based on validator type
            condition = self._build_validation_condition(validator_type, attributes)
            action = error_message or f"Validate {control_to_validate}"

            rule = BusinessRule(
                id=self._generate_rule_id(),
                rule_type=RuleType.VALIDATION,
                condition=condition[:200],
                action=action[:200],
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=0.90,
                natural_language=f"When {control_to_validate} fails {validator_type} validation, show: {error_message}",
                variables_involved=[control_to_validate],
                related_entities=[],
                language=Language.ASPX,
                extraction_method=ExtractionMethod.REGEX,
                extraction_tier=self.extraction_tier,
                code_snippet=match.group(0).strip()[:150],
                parent_function="",
                parent_class="",
            )
            rules.append(rule)

    def _extract_multiline_code_blocks(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol],
        rules: List[BusinessRule],
        code_language: str,
    ):
        """Extract rules from multi-line code blocks."""
        # Pattern to match multi-line code blocks (not directives, not expressions, not bindings)
        multiline_pattern = re.compile(
            r'<%\s*\n(.+?)\n\s*%>',
            re.DOTALL
        )

        for match in multiline_pattern.finditer(source):
            code = match.group(1).strip()
            line_num = source[:match.start()].count('\n') + 1

            # Skip empty or very short code
            if len(code) < 5:
                continue

            # Check for Response.Redirect (navigation)
            redirect_match = re.search(r'Response\.Redirect\s*\(\s*["\']([^"\']+)', code, re.IGNORECASE)
            if redirect_match:
                rule = BusinessRule(
                    id=self._generate_rule_id(),
                    rule_type=RuleType.NAVIGATION,
                    condition=self._extract_if_condition(code, code_language) or "condition",
                    action=f"Redirect to {redirect_match.group(1)}",
                    source_file=file_path,
                    source_lines=(line_num, line_num),
                    confidence=0.90,
                    natural_language=f"Navigate to {redirect_match.group(1)} when condition is met",
                    variables_involved=self._extract_variables(code),
                    related_entities=[],
                    language=Language.ASPX,
                    extraction_method=ExtractionMethod.REGEX,
                    extraction_tier=self.extraction_tier,
                    code_snippet=code[:150],
                    parent_function="",
                    parent_class="",
                )
                rules.append(rule)
                continue

            # Check for other patterns
            rule_type = self._classify_code_block(code, code_language)
            if rule_type:
                condition, action = self._extract_condition_action(code, code_language)
                rule = BusinessRule(
                    id=self._generate_rule_id(),
                    rule_type=rule_type,
                    condition=condition[:200],
                    action=action[:200],
                    source_file=file_path,
                    source_lines=(line_num, line_num),
                    confidence=0.80,
                    natural_language=self._generate_natural_language(rule_type, condition, action),
                    variables_involved=self._extract_variables(code),
                    related_entities=[],
                    language=Language.ASPX,
                    extraction_method=ExtractionMethod.REGEX,
                    extraction_tier=self.extraction_tier,
                    code_snippet=code[:150],
                    parent_function="",
                    parent_class="",
                )
                rules.append(rule)

    def _extract_if_condition(self, code: str, code_language: str) -> Optional[str]:
        """Extract condition from If/if statement in code block."""
        if code_language == 'VB':
            match = re.search(r'If\s+(.+?)\s+Then', code, re.IGNORECASE)
        else:
            match = re.search(r'if\s*\((.+?)\)', code, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_validation_rules(
        self,
        line: str,
        line_num: int,
        file_path: str,
        symbols: List[CodeSymbol],
        rules: List[BusinessRule],
    ):
        """Extract rules from validation controls."""
        for match in self.VALIDATION_CONTROL_PATTERN.finditer(line):
            validator_type = match.group(1)

            # Extract control being validated
            ctrl_match = re.search(r'ControlToValidate\s*=\s*["\'](\w+)', line, re.IGNORECASE)
            control_to_validate = ctrl_match.group(1) if ctrl_match else "field"

            # Extract error message
            err_match = re.search(r'ErrorMessage\s*=\s*["\']([^"\']+)', line, re.IGNORECASE)
            error_message = err_match.group(1) if err_match else ""

            # Build condition based on validator type
            condition = self._build_validation_condition(validator_type, line)
            action = error_message or f"Validate {control_to_validate}"

            rule = BusinessRule(
                id=self._generate_rule_id(),
                rule_type=RuleType.VALIDATION,
                condition=condition[:200],
                action=action[:200],
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=0.90,
                natural_language=f"When {control_to_validate} fails {validator_type} validation, show: {error_message}",
                variables_involved=[control_to_validate],
                related_entities=[],
                language=Language.ASPX,
                extraction_method=ExtractionMethod.REGEX,
                extraction_tier=self.extraction_tier,
                code_snippet=line.strip()[:150],
                parent_function="",
                parent_class="",
            )
            rules.append(rule)

    def _build_validation_condition(self, validator_type: str, line: str) -> str:
        """Build condition string based on validator type."""
        if 'RequiredField' in validator_type:
            return "Field is empty or not provided"
        elif 'Range' in validator_type:
            min_val = re.search(r'MinimumValue\s*=\s*["\']([^"\']+)', line)
            max_val = re.search(r'MaximumValue\s*=\s*["\']([^"\']+)', line)
            min_str = min_val.group(1) if min_val else "?"
            max_str = max_val.group(1) if max_val else "?"
            return f"Value not between {min_str} and {max_str}"
        elif 'RegularExpression' in validator_type:
            expr = re.search(r'ValidationExpression\s*=\s*["\']([^"\']+)', line)
            return f"Value doesn't match pattern: {expr.group(1)[:50] if expr else '...'}"
        elif 'Compare' in validator_type:
            ctrl = re.search(r'ControlToCompare\s*=\s*["\']([^"\']+)', line)
            return f"Value doesn't match {ctrl.group(1) if ctrl else 'other field'}"
        elif 'Custom' in validator_type:
            func = re.search(r'(?:Client|Server)ValidationFunction\s*=\s*["\']([^"\']+)', line)
            return f"Custom validation: {func.group(1) if func else 'function'}"
        return validator_type

    def _extract_binding_rules(
        self,
        line: str,
        line_num: int,
        file_path: str,
        symbols: List[CodeSymbol],
        rules: List[BusinessRule],
    ):
        """Extract rules from data binding expressions."""
        for match in self.BINDING_PATTERN.finditer(line):
            binding_expr = match.group(1).strip()

            # Skip simple field bindings
            if re.match(r'^Eval\s*\(\s*["\'][a-zA-Z_]\w*["\']\s*\)$', binding_expr):
                continue  # Simple column binding, not a rule

            # Check for conditional bindings
            if any(op in binding_expr for op in ['?', ':', 'If(', 'IIf(']):
                rule_type = RuleType.BRANCHING
                confidence = 0.85
            elif any(op in binding_expr for op in ['Convert.', 'Math.', '+', '-', '*', '/']):
                rule_type = RuleType.CALCULATION
                confidence = 0.80
            elif 'Session' in binding_expr or 'ViewState' in binding_expr:
                rule_type = RuleType.STATE_MANAGEMENT
                confidence = 0.85
            else:
                rule_type = RuleType.DATA_ACCESS
                confidence = 0.75

            # Extract variables
            variables = self._extract_variables(binding_expr)

            rule = BusinessRule(
                id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=binding_expr[:200],
                action="Bind data to control",
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=confidence,
                natural_language=f"Data binding: {binding_expr[:100]}",
                variables_involved=variables[:10],
                related_entities=self._extract_entities(binding_expr, variables),
                language=Language.ASPX,
                extraction_method=ExtractionMethod.REGEX,
                extraction_tier=self.extraction_tier,
                code_snippet=line.strip()[:150],
                parent_function="",
                parent_class="",
            )
            rules.append(rule)

    def _extract_code_block_rules(
        self,
        line: str,
        line_num: int,
        lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol],
        rules: List[BusinessRule],
        code_language: str,
    ):
        """Extract rules from inline code blocks."""
        # Find all code blocks on this line
        for match in self.CODE_BLOCK_PATTERN.finditer(line):
            code = match.group(1).strip()

            # Skip empty or very short code
            if len(code) < 5:
                continue

            # Detect rule type
            rule_type = self._classify_code_block(code, code_language)
            if not rule_type:
                continue

            condition, action = self._extract_condition_action(code, code_language)

            rule = BusinessRule(
                id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=condition[:200],
                action=action[:200],
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=0.80,
                natural_language=self._generate_natural_language(rule_type, condition, action),
                variables_involved=self._extract_variables(code),
                related_entities=[],
                language=Language.ASPX,
                extraction_method=ExtractionMethod.REGEX,
                extraction_tier=self.extraction_tier,
                code_snippet=code[:150],
                parent_function="",
                parent_class="",
            )
            rules.append(rule)

    def _classify_code_block(self, code: str, code_language: str) -> Optional[RuleType]:
        """Classify the type of rule in a code block."""
        code_lower = code.lower()

        # VB.NET patterns
        if code_language == 'VB':
            if re.search(r'\bif\b.*\bthen\b', code_lower):
                return RuleType.BRANCHING
            if re.search(r'\bselect\s+case\b', code_lower):
                return RuleType.BRANCHING
            if re.search(r'\bresponse\.redirect\b', code_lower):
                return RuleType.NAVIGATION
            if re.search(r'\bsession\b|\bviewstate\b', code_lower):
                return RuleType.STATE_MANAGEMENT
        # C# patterns
        else:
            if re.search(r'\bif\s*\(', code_lower):
                return RuleType.BRANCHING
            if re.search(r'\bswitch\s*\(', code_lower):
                return RuleType.BRANCHING
            if re.search(r'\bresponse\.redirect\b', code_lower):
                return RuleType.NAVIGATION
            if re.search(r'\bsession\b|\bviewstate\b', code_lower):
                return RuleType.STATE_MANAGEMENT

        return None

    def _extract_condition_action(self, code: str, code_language: str) -> Tuple[str, str]:
        """Extract condition and action from code block."""
        if code_language == 'VB':
            # VB.NET: If condition Then action
            match = re.search(r'If\s+(.+?)\s+Then\s*(.+)?', code, re.IGNORECASE)
            if match:
                return match.group(1).strip(), (match.group(2) or 'continue').strip()

            # VB.NET: Select Case
            match = re.search(r'Select\s+Case\s+(\w+)', code, re.IGNORECASE)
            if match:
                return f"Case on {match.group(1)}", "branch"
        else:
            # C#: if (condition) { action }
            match = re.search(r'if\s*\((.+?)\)\s*\{?\s*(.+)?', code, re.IGNORECASE)
            if match:
                return match.group(1).strip(), (match.group(2) or 'continue').strip()

            # C#: switch (expression)
            match = re.search(r'switch\s*\((.+?)\)', code, re.IGNORECASE)
            if match:
                return f"Switch on {match.group(1)}", "branch"

        return code[:100], "execute"

    def _extract_control_rules(
        self,
        line: str,
        line_num: int,
        file_path: str,
        symbols: List[CodeSymbol],
        rules: List[BusinessRule],
    ):
        """Extract rules from server control attributes."""
        # Look for conditional visibility
        vis_match = re.search(r'Visible\s*=\s*["\']<%#\s*(.+?)%>["\']', line, re.IGNORECASE)
        if vis_match:
            condition = vis_match.group(1).strip()
            control_id = self._extract_control_id(line) or "control"

            rule = BusinessRule(
                id=self._generate_rule_id(),
                rule_type=RuleType.BRANCHING,
                condition=condition[:200],
                action=f"Show/hide {control_id}",
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=0.85,
                natural_language=f"Show {control_id} when {condition[:50]}",
                variables_involved=self._extract_variables(condition),
                related_entities=[],
                language=Language.ASPX,
                extraction_method=ExtractionMethod.REGEX,
                extraction_tier=self.extraction_tier,
                code_snippet=line.strip()[:150],
                parent_function="",
                parent_class="",
            )
            rules.append(rule)

        # Look for event handlers
        for handler_match in re.finditer(r'On(\w+)\s*=\s*["\'](\w+)["\']', line, re.IGNORECASE):
            event_type = handler_match.group(1)
            handler_name = handler_match.group(2)
            control_id = self._extract_control_id(line) or "control"

            rule = BusinessRule(
                id=self._generate_rule_id(),
                rule_type=RuleType.WORKFLOW,
                condition=f"{control_id}.{event_type}",
                action=f"Call {handler_name}",
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=0.90,
                natural_language=f"When {control_id} triggers {event_type}, execute {handler_name}",
                variables_involved=[control_id, handler_name],
                related_entities=[],
                language=Language.ASPX,
                extraction_method=ExtractionMethod.REGEX,
                extraction_tier=self.extraction_tier,
                code_snippet=line.strip()[:150],
                parent_function="",
                parent_class="",
            )
            rules.append(rule)

    def _extract_variables(self, text: str) -> List[str]:
        """Extract variables from ASPX code."""
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, text)

        # Keywords to exclude
        keywords = {
            'if', 'then', 'else', 'end', 'select', 'case', 'and', 'or', 'not',
            'true', 'false', 'nothing', 'null', 'dim', 'as', 'new', 'for', 'each',
            'visible', 'enabled', 'runat', 'server', 'id', 'text', 'value',
            'eval', 'bind', 'databinder', 'container', 'dataitem',
            'string', 'int', 'integer', 'boolean', 'date', 'decimal', 'object',
            'response', 'request', 'session', 'viewstate', 'server', 'page',
            'convert', 'math', 'tostring', 'toint32', 'parse',
        }

        return list(set(m for m in matches if m.lower() not in keywords))

    def _extract_entities(self, text: str, variables: List[str]) -> List[str]:
        """Extract domain entities from ASPX code."""
        entities = set()

        # Entity patterns
        entity_patterns = [
            r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b',  # PascalCase entities
            r'"(\w+)"',  # Column names in Eval
        ]

        for pattern in entity_patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)

        return list(entities)[:5]
