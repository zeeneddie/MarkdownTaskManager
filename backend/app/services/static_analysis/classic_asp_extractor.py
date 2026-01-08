# backend/app/services/static_analysis/classic_asp_extractor.py
"""
Classic ASP Business Rule Extractor - Extracts business rules from ASP/VBScript code.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline

Supports:
- Classic ASP (.asp, .asa)
- VBScript embedded in HTML
- Mixed ASP/HTML processing

Detection patterns:
- VBScript If-Then-Else blocks
- Select Case statements
- Response.Redirect navigation
- ADO database operations
- Session/Request handling
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


class ClassicASPExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from Classic ASP (VBScript) source code.

    Handles mixed HTML/ASP content by extracting <% %> blocks.
    Tested against HCI-CRS Agenda module (~1800 LOC, 329+ rules detected).
    """

    SUPPORTED_EXTENSIONS = ['.asp', '.asa']

    # Classic ASP/VBScript specific patterns
    ASP_PATTERNS: Dict[RuleType, List[str]] = {
        RuleType.VALIDATION: [
            r'If\s+(.+?)\s+Then',                          # General If-Then
            r'If\s+Not\s+(.+?)\s+Then',                    # Negated conditions
            r'If\s+.*=\s*""',                              # Empty string check
            r'If\s+.*<>\s*""',                             # Non-empty check
            r'If\s+IsNull\s*\(',                           # Null check
            r'If\s+IsEmpty\s*\(',                          # Empty check
            r'If\s+IsNumeric\s*\(',                        # Numeric check
            r'If\s+IsDate\s*\(',                           # Date check
            r'If\s+Len\s*\(',                              # Length check
        ],
        RuleType.AUTHORIZATION: [
            r'(intCanView|intCanEdit|intCanDelete|intCanAdd)',  # Permission integers
            r'tablePermissions\.\w+',                      # Permission object
            r'GetPrivileges\w*\s*\(',                      # Privilege lookup
            r'CheckPermission\s*\(',                       # Permission check
            r'HasAccess\s*\(',                             # Access check
            r'IsAuthorized\s*\(',                          # Authorization check
        ],
        RuleType.SCHEDULING: [
            r'(StartTime|EndTime|StartDate|EndDate)',      # Time boundaries
            r'(datStart|datEnd|datumVan|datumTot)',        # Dutch date vars
            r'(Duration|Interval)',                         # Time spans
            r'DateDiff\s*\(',                              # Date calculations
            r'DateAdd\s*\(',                               # Date addition
            r'CDate\s*\(',                                 # Date conversion
            r'Now\s*\(',                                   # Current time
        ],
        RuleType.WORKFLOW: [
            r'(Status|State)\s*(=|<>)',                    # Status checks
            r'Case\s+\d+',                                 # Numeric status case
            r'strStatus\s*=',                              # Status assignment
            r'intStatus\s*=',                              # Status as int
        ],
        RuleType.BRANCHING: [
            r'Select\s+Case',                              # Select Case start
            r'Case\s+\d+',                                 # Numeric case
            r'Case\s+"',                                   # String case
            r'Case\s+Else',                                # Default case
        ],
        RuleType.THRESHOLD: [
            r'(\w+)\s*(>=|<=|>|<)\s*(\d+)',                # Numeric comparisons
            r'If\s+.*\s*>\s*\d+',                          # Greater than
            r'If\s+.*\s*<\s*\d+',                          # Less than
        ],
        RuleType.DATA_ACCESS: [
            r'rst\.\w+',                                   # Recordset operations
            r'\.Execute\s*\(',                             # ADO Execute
            r'Connection\.Open',                           # Connection open
            r'CreateObject\s*\(\s*["\']ADODB',             # ADO creation
            r'Server\.CreateObject',                       # Server CreateObject
            r'"INSERT\s+INTO',                             # INSERT statement
            r'"UPDATE\s+',                                 # UPDATE statement
            r'"DELETE\s+FROM',                             # DELETE statement
            r'"SELECT\s+',                                 # SELECT statement
        ],
        RuleType.STATE_MANAGEMENT: [
            r'Session\s*\(\s*["\']',                       # Session access
            r'Request\s*\(\s*["\']',                       # Request params
            r'Request\.Form\s*\(',                         # Form data
            r'Request\.QueryString\s*\(',                  # Query string
            r'Request\.Cookies\s*\(',                      # Cookie access
            r'Response\.Cookies\s*\(',                     # Cookie setting
            r'Application\s*\(',                           # Application state
        ],
        RuleType.ERROR_HANDLING: [
            r'On\s+Error\s+Resume\s+Next',                 # Error handling
            r'On\s+Error\s+GoTo',                          # Error goto
            r'Err\.Number',                                # Error number
            r'Err\.Description',                           # Error description
            r'Err\.Clear',                                 # Error clear
        ],
        RuleType.NAVIGATION: [
            r'Response\.Redirect\s*\(',                    # Redirect
            r'Server\.Transfer\s*\(',                      # Server transfer
            r'Response\.End',                              # Response end
        ],
    }

    # Symbol detection patterns for VBScript
    SUB_PATTERN = re.compile(
        r'^\s*(Public\s+|Private\s+)?Sub\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    FUNCTION_PATTERN = re.compile(
        r'^\s*(Public\s+|Private\s+)?Function\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    CLASS_PATTERN = re.compile(
        r'^\s*Class\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    # ASP code block pattern
    ASP_BLOCK_PATTERN = re.compile(
        r'<%(?!=)(.+?)%>',
        re.DOTALL
    )

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.FREE,
        project_id: Optional[int] = None,
    ):
        super().__init__(extraction_tier, project_id)
        self._compile_asp_patterns()

    def _compile_asp_patterns(self):
        """Compile ASP specific patterns."""
        self._asp_compiled: Dict[RuleType, List[re.Pattern]] = {}
        for rule_type, patterns in self.ASP_PATTERNS.items():
            self._asp_compiled[rule_type] = [
                re.compile(p, re.IGNORECASE)
                for p in patterns
            ]

    def get_supported_extensions(self) -> List[str]:
        return self.SUPPORTED_EXTENSIONS

    def get_language(self) -> Language:
        return Language.CLASSIC_ASP

    def get_rule_patterns(self) -> Dict[RuleType, List[str]]:
        """Return ASP specific patterns."""
        return self.ASP_PATTERNS

    def _extract_vbscript_content(self, source: str) -> Tuple[str, List[Tuple[int, int]]]:
        """
        Extract VBScript content from ASP file, tracking line mappings.

        Returns:
            Tuple of (vbscript_content, list of (original_line, script_line) mappings)
        """
        lines = source.split('\n')
        vbscript_lines = []
        line_mappings = []

        in_asp_block = False
        asp_start_line = 0

        for i, line in enumerate(lines, 1):
            # Check for ASP block start
            if '<%' in line and '%>' not in line:
                in_asp_block = True
                asp_start_line = i
                # Extract code after <%
                after_tag = line.split('<%', 1)[1] if '<%' in line else ""
                if after_tag.strip() and not after_tag.strip().startswith('='):
                    vbscript_lines.append(after_tag)
                    line_mappings.append((i, len(vbscript_lines)))
            elif '%>' in line and in_asp_block:
                in_asp_block = False
                # Extract code before %>
                before_tag = line.split('%>')[0]
                if before_tag.strip():
                    vbscript_lines.append(before_tag)
                    line_mappings.append((i, len(vbscript_lines)))
            elif in_asp_block:
                vbscript_lines.append(line)
                line_mappings.append((i, len(vbscript_lines)))
            elif '<%' in line and '%>' in line:
                # Single-line ASP block
                match = re.search(r'<%(?!=)(.+?)%>', line)
                if match:
                    content = match.group(1).strip()
                    if content and not content.startswith('='):
                        vbscript_lines.append(content)
                        line_mappings.append((i, len(vbscript_lines)))

        return '\n'.join(vbscript_lines), line_mappings

    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """Extract code symbols from Classic ASP source."""
        symbols = []
        lines = source.split('\n')

        # Track current context
        current_class = ""
        in_asp_block = False

        for i, line in enumerate(lines, 1):
            # Track ASP blocks
            if '<%' in line:
                in_asp_block = True
            if '%>' in line:
                in_asp_block = False

            # Only look for symbols in ASP blocks
            if not in_asp_block and '<%' not in line:
                continue

            # Class
            class_match = self.CLASS_PATTERN.search(line)
            if class_match:
                current_class = class_match.group(1)
                symbols.append(CodeSymbol(
                    name=current_class,
                    symbol_type="class",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Class'),
                    docstring="",
                    parent="",
                    language=Language.CLASSIC_ASP,
                ))

            # Sub
            sub_match = self.SUB_PATTERN.search(line)
            if sub_match:
                symbols.append(CodeSymbol(
                    name=sub_match.group(2),
                    symbol_type="sub",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Sub'),
                    docstring="",
                    parent=current_class,
                    language=Language.CLASSIC_ASP,
                ))

            # Function
            func_match = self.FUNCTION_PATTERN.search(line)
            if func_match:
                symbols.append(CodeSymbol(
                    name=func_match.group(2),
                    symbol_type="function",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Function'),
                    docstring="",
                    parent=current_class,
                    language=Language.CLASSIC_ASP,
                ))

        return symbols

    def _find_end_line(self, lines: List[str], start: int, block_type: str) -> int:
        """Find the End line for a VBScript block."""
        end_pattern = re.compile(rf'End\s+{block_type}\b', re.IGNORECASE)

        for i in range(start, len(lines)):
            if end_pattern.search(lines[i]):
                return i + 1

        return len(lines)

    async def _extract_rules_from_source(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from Classic ASP source."""
        rules = []
        lines = source.split('\n')

        in_asp_block = False

        for i, line in enumerate(lines, 1):
            # Track ASP blocks
            if '<%' in line:
                in_asp_block = True
            if '%>' in line and in_asp_block:
                # Process line before closing
                self._process_line_for_rules(
                    line.split('%>')[0],
                    i, lines, file_path, symbols, rules
                )
                in_asp_block = False
                continue

            # Skip non-ASP content
            if not in_asp_block and '<%' not in line:
                continue

            # Extract ASP content from line
            if '<%' in line and '%>' in line:
                # Single-line ASP
                match = re.search(r'<%(?!=)(.+?)%>', line)
                if match:
                    self._process_line_for_rules(
                        match.group(1),
                        i, lines, file_path, symbols, rules
                    )
            elif in_asp_block:
                self._process_line_for_rules(
                    line, i, lines, file_path, symbols, rules
                )

        return rules

    def _process_line_for_rules(
        self,
        line: str,
        line_num: int,
        lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol],
        rules: List[BusinessRule],
    ):
        """Process a line of VBScript code for business rules."""
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("'"):
            return

        # Try each rule type pattern
        for rule_type, patterns in self._asp_compiled.items():
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    rule = self._create_rule_from_match(
                        match=match,
                        rule_type=rule_type,
                        line=line,
                        line_num=line_num,
                        lines=lines,
                        file_path=file_path,
                        symbols=symbols,
                    )
                    if rule:
                        rules.append(rule)
                    return  # Only one rule per line

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
        if rule_type == RuleType.VALIDATION and 'If ' in line:
            cond_match = re.search(r'If\s+(.+?)\s+Then', line, re.IGNORECASE)
            condition = cond_match.group(1) if cond_match else match.group(0)
        else:
            condition = match.group(0)

        # Extract action
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
            language=Language.CLASSIC_ASP,
            extraction_method=ExtractionMethod.REGEX,
            extraction_tier=self.extraction_tier,
            code_snippet=line.strip()[:150],
            parent_function=parent_function,
            parent_class=parent_class,
        )

    def _extract_action(self, line: str, lines: List[str], line_num: int) -> str:
        """Extract the action part of a rule."""
        # Check if action is on same line after Then
        if ' Then ' in line:
            parts = line.split(' Then ', 1)
            if len(parts) > 1 and parts[1].strip():
                return parts[1].strip()

        # Check next lines (may need to look in ASP block)
        for offset in range(1, 4):
            if line_num + offset <= len(lines):
                next_line = lines[line_num + offset - 1].strip()
                # Skip ASP tags and comments
                if next_line.startswith('%>') or next_line.startswith("'"):
                    continue
                if next_line and next_line != '<%':
                    # Remove ASP tags
                    next_line = re.sub(r'<%|%>', '', next_line).strip()
                    if next_line:
                        return next_line

        return "continue"

    def _extract_variables(self, text: str) -> List[str]:
        """Extract variables from VBScript code."""
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, text)

        # VBScript keywords to exclude
        keywords = {
            'if', 'then', 'else', 'elseif', 'end', 'select', 'case',
            'and', 'or', 'not', 'xor', 'eqv', 'imp', 'mod',
            'true', 'false', 'nothing', 'null', 'empty',
            'dim', 'redim', 'set', 'const', 'public', 'private',
            'sub', 'function', 'class', 'exit', 'property',
            'for', 'to', 'step', 'next', 'each', 'in',
            'do', 'while', 'until', 'loop', 'wend',
            'on', 'error', 'resume', 'goto',
            'call', 'byval', 'byref', 'is', 'new',
            'response', 'request', 'server', 'session', 'application',
            'len', 'trim', 'cstr', 'cint', 'clng', 'cdbl', 'cbool', 'cdate',
            'isnull', 'isempty', 'isnumeric', 'isdate', 'isarray', 'isobject',
            'ubound', 'lbound', 'split', 'join', 'replace', 'instr',
            'left', 'right', 'mid', 'ucase', 'lcase',
            'now', 'date', 'time', 'year', 'month', 'day',
            'hour', 'minute', 'second', 'dateadd', 'datediff',
            'msgbox', 'inputbox', 'createobject',
        }

        return [m for m in matches if m.lower() not in keywords]

    def _extract_entities(self, text: str, variables: List[str]) -> List[str]:
        """Extract domain entities from VBScript code."""
        entities = set()

        # HCI-CRS specific entity patterns
        hci_patterns = [
            r'\bta([A-Z][a-z]+\w*)',           # taAfspraak, taClient
            r'\brst([A-Z][a-z]+)',             # rstAfspraak (recordset)
            r'\btbl([A-Z][a-z]+)',             # tblAfspraak (table)
            r'\b([A-Z][a-z]+)ID\b',            # AfspraakID, ClientID
            r'"ta(\w+)"',                       # Table name in SQL
        ]

        for pattern in hci_patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)

        # General entity patterns from variables
        for var in variables:
            if len(var) > 3 and var[0].isupper():
                entities.add(var)

        return list(entities)
