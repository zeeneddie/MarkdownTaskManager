# backend/app/services/static_analysis/vb6_extractor.py
"""
VB6 Business Rule Extractor - Extracts business rules from Visual Basic 6 legacy code.

Part of Week 112-114: Hybrid Business Rule Extraction Pipeline - Phase 4

Supports:
- VB6 Form files (.frm)
- VB6 Module files (.bas)
- VB6 Class modules (.cls)
- VB6 User controls (.ctl)

Detection patterns:
- If-Then-Else blocks
- Select Case statements
- Error handling (On Error)
- Database operations (ADO/DAO)
- Form event handlers
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


class VB6BusinessRuleExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from Visual Basic 6 source code.

    Uses regex-enhanced extraction (Tier 2) for legacy VB6 code.
    Handles the unique syntax differences from VB.NET.
    """

    SUPPORTED_EXTENSIONS = ['.frm', '.bas', '.cls', '.ctl']

    # VB6 specific patterns for rule detection
    VB6_PATTERNS: Dict[RuleType, List[str]] = {
        RuleType.VALIDATION: [
            r'If\s+(.+?)\s+Then',                           # General If-Then
            r'If\s+Len\s*\(\s*(.+?)\s*\)\s*[=<>]',         # Len() checks
            r'If\s+IsNull\s*\(',                            # IsNull checks
            r'If\s+IsEmpty\s*\(',                           # IsEmpty checks
            r'If\s+IsNumeric\s*\(',                         # IsNumeric checks
            r'If\s+IsDate\s*\(',                            # IsDate checks
            r'If\s+.*\s*=\s*""',                            # Empty string check
            r'If\s+.*\s*<>\s*""',                           # Non-empty string check
            r'If\s+Not\s+(.+?)\s+Then',                     # Negated conditions
        ],
        RuleType.AUTHORIZATION: [
            r'(blnCanEdit|blnCanDelete|blnCanAdd|blnCanView)',  # Boolean permissions
            r'(intAccess|intPermission|intLevel)',              # Int permissions
            r'CheckPermission\s*\(',                            # Permission check
            r'HasAccess\s*\(',                                  # Access check
            r'If\s+.*Permission',                               # Permission in condition
            r'If\s+.*Rights',                                   # Rights check
            r'UserLevel\s*[<>=]+',                              # User level check
        ],
        RuleType.WORKFLOW: [
            r'(Status|State|Mode)\s*=',                     # Status assignment
            r'If\s+(Status|State|Mode)\s*[=<>]',            # Status check
            r'Case\s+(Status|State)',                       # Status case
            r'\.Status\s*=',                                # Object status
        ],
        RuleType.BRANCHING: [
            r'Select\s+Case',                               # Select Case start
            r'Case\s+\d+',                                  # Numeric case
            r'Case\s+"',                                    # String case
            r'Case\s+Else',                                 # Default case
            r'Case\s+Is\s*[<>=]',                           # Comparison case
            r'Case\s+[A-Z]\w+\.',                           # Enum case
        ],
        RuleType.THRESHOLD: [
            r'If\s+\w+\s*[<>=]+\s*\d+',                     # Numeric comparisons
            r'If\s+\w+\s*>\s*\d+',                          # Greater than
            r'If\s+\w+\s*<\s*\d+',                          # Less than
            r'\.Count\s*[<>=]+\s*\d+',                      # Count checks
            r'UBound\s*\(',                                 # Array bounds
        ],
        RuleType.DATA_ACCESS: [
            r'\.Execute\s*\(',                              # ADO Execute
            r'\.Open\s*\(',                                 # Connection/Recordset open
            r'Set\s+\w+\s*=\s*\w+\.OpenRecordset',         # DAO Recordset
            r'DoCmd\.(RunSQL|OpenQuery)',                   # Access DoCmd
            r'CurrentDb\.Execute',                          # Access CurrentDb
            r'\.AddNew',                                    # Add new record
            r'\.Update',                                    # Update record
            r'\.Delete',                                    # Delete record
            r'\.MoveFirst|\.MoveLast|\.MoveNext',          # Recordset navigation
            r'\.EOF|\.BOF',                                 # Recordset position
            r'ADODB\.Recordset',                            # ADO Recordset
            r'ADODB\.Connection',                           # ADO Connection
        ],
        RuleType.STATE_MANAGEMENT: [
            r'Set\s+Session\s*=',                           # Session set
            r'Session\s*\(',                                # Session access
            r'gbl\w+',                                      # Global variables
            r'g_\w+',                                       # Global prefix
            r'Public\s+\w+\s+As',                           # Public module vars
            r'Static\s+\w+\s+As',                           # Static vars
        ],
        RuleType.ERROR_HANDLING: [
            r'On\s+Error\s+GoTo',                           # Error handler
            r'On\s+Error\s+Resume\s+Next',                  # Ignore errors
            r'Err\.Number',                                 # Error number
            r'Err\.Description',                            # Error description
            r'Err\.Raise',                                  # Raise error
            r'Resume\s+Next',                               # Resume next
            r'Exit\s+Sub',                                  # Exit on error
            r'Exit\s+Function',                             # Exit on error
        ],
        RuleType.NAVIGATION: [
            r'\.Show',                                      # Form show
            r'\.Hide',                                      # Form hide
            r'Unload\s+',                                   # Unload form
            r'Load\s+',                                     # Load form
            r'DoCmd\.OpenForm',                             # Access open form
            r'DoCmd\.Close',                                # Access close
        ],
        RuleType.CALCULATION: [
            r'(\w+)\s*=\s*\w+\s*[\+\-\*/]\s*\w+',           # Arithmetic
            r'Round\s*\(',                                  # Round function
            r'Int\s*\(',                                    # Int function
            r'CDbl\s*\(',                                   # CDbl conversion
            r'CCur\s*\(',                                   # CCur conversion
            r'Format\s*\(',                                 # Format function
            r'DateDiff\s*\(',                               # Date calculation
            r'DateAdd\s*\(',                                # Date calculation
        ],
        RuleType.SCHEDULING: [
            r'(dtStart|dtEnd|datStart|datEnd)',             # Date variables
            r'Date\s*[<>=]',                                # Date comparison
            r'Now\s*[<>=]',                                 # Now comparison
            r'Timer\s*[<>=]',                               # Timer comparison
            r'TimeValue\s*\(',                              # Time value
            r'DateValue\s*\(',                              # Date value
        ],
    }

    # Symbol detection patterns
    SUB_PATTERN = re.compile(
        r'^\s*(Private\s+|Public\s+)?Sub\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    FUNCTION_PATTERN = re.compile(
        r'^\s*(Private\s+|Public\s+)?Function\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    PROPERTY_PATTERN = re.compile(
        r'^\s*(Private\s+|Public\s+)?Property\s+(Get|Let|Set)\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    CLASS_PATTERN = re.compile(
        r'^VERSION\s+\d+\.\d+\s+CLASS',
        re.IGNORECASE | re.MULTILINE
    )

    FORM_PATTERN = re.compile(
        r'^VERSION\s+\d+\.\d+',
        re.IGNORECASE | re.MULTILINE
    )

    TYPE_PATTERN = re.compile(
        r'^\s*(Private\s+|Public\s+)?Type\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    ENUM_PATTERN = re.compile(
        r'^\s*(Private\s+|Public\s+)?Enum\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    # Form control event pattern
    EVENT_PATTERN = re.compile(
        r'^\s*Private\s+Sub\s+(\w+)_(Click|Change|Load|Unload|KeyPress|KeyDown|'
        r'DblClick|GotFocus|LostFocus|MouseDown|MouseUp|MouseMove|Validate|'
        r'BeforeUpdate|AfterUpdate|Enter|Exit)\s*\(',
        re.IGNORECASE | re.MULTILINE
    )

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.FREE,
        project_id: Optional[int] = None,
    ):
        super().__init__(extraction_tier, project_id)
        self._compile_vb6_patterns()

    def _compile_vb6_patterns(self):
        """Compile VB6 specific patterns."""
        self._vb6_compiled: Dict[RuleType, List[re.Pattern]] = {}
        for rule_type, patterns in self.VB6_PATTERNS.items():
            self._vb6_compiled[rule_type] = [
                re.compile(p, re.IGNORECASE)
                for p in patterns
            ]

    def get_supported_extensions(self) -> List[str]:
        return self.SUPPORTED_EXTENSIONS

    def get_language(self) -> Language:
        return Language.VB6

    def get_rule_patterns(self) -> Dict[RuleType, List[str]]:
        """Return VB6 specific patterns."""
        return self.VB6_PATTERNS

    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """Extract code symbols from VB6 source."""
        symbols = []
        lines = source.split('\n')

        # Detect file type
        is_class = bool(self.CLASS_PATTERN.search(source))
        is_form = file_path.lower().endswith('.frm')
        is_module = file_path.lower().endswith('.bas')
        is_control = file_path.lower().endswith('.ctl')

        # Determine module name from file
        import os
        module_name = os.path.splitext(os.path.basename(file_path))[0]

        # Add module/class symbol
        if is_class or is_form or is_control:
            symbols.append(CodeSymbol(
                name=module_name,
                symbol_type="class" if is_class else ("form" if is_form else "control"),
                line_start=1,
                line_end=len(lines),
                docstring="",
                parent="",
                language=Language.VB6,
            ))
        elif is_module:
            symbols.append(CodeSymbol(
                name=module_name,
                symbol_type="module",
                line_start=1,
                line_end=len(lines),
                docstring="",
                parent="",
                language=Language.VB6,
            ))

        for i, line in enumerate(lines, 1):
            # Sub procedures
            sub_match = self.SUB_PATTERN.match(line)
            if sub_match:
                symbols.append(CodeSymbol(
                    name=sub_match.group(2),
                    symbol_type="sub",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Sub'),
                    docstring="",
                    parent=module_name,
                    language=Language.VB6,
                ))

            # Functions
            func_match = self.FUNCTION_PATTERN.match(line)
            if func_match:
                symbols.append(CodeSymbol(
                    name=func_match.group(2),
                    symbol_type="function",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Function'),
                    docstring="",
                    parent=module_name,
                    language=Language.VB6,
                ))

            # Properties
            prop_match = self.PROPERTY_PATTERN.match(line)
            if prop_match:
                prop_type = prop_match.group(2)  # Get, Let, or Set
                prop_name = prop_match.group(3)
                symbols.append(CodeSymbol(
                    name=f"{prop_name}_{prop_type}",
                    symbol_type="property",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Property'),
                    docstring="",
                    parent=module_name,
                    language=Language.VB6,
                ))

            # Type definitions
            type_match = self.TYPE_PATTERN.match(line)
            if type_match:
                symbols.append(CodeSymbol(
                    name=type_match.group(2),
                    symbol_type="type",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Type'),
                    docstring="",
                    parent=module_name,
                    language=Language.VB6,
                ))

            # Enums
            enum_match = self.ENUM_PATTERN.match(line)
            if enum_match:
                symbols.append(CodeSymbol(
                    name=enum_match.group(2),
                    symbol_type="enum",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Enum'),
                    docstring="",
                    parent=module_name,
                    language=Language.VB6,
                ))

        return symbols

    def _find_end_line(self, lines: List[str], start: int, block_type: str) -> int:
        """Find the End line for a VB6 block."""
        end_pattern = re.compile(rf'^\s*End\s+{block_type}\b', re.IGNORECASE)

        for i in range(start, len(lines)):
            line = lines[i]
            if end_pattern.match(line):
                return i + 1

        return len(lines)

    async def _extract_rules_from_source(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from VB6 source."""
        rules = []
        lines = source.split('\n')

        # Skip binary/design portion of .frm files
        code_start = 0
        if file_path.lower().endswith('.frm'):
            # Find where code begins (after "Attribute VB_Name" section)
            for i, line in enumerate(lines):
                if line.strip().startswith('Attribute VB_'):
                    code_start = i
                elif code_start > 0 and not line.strip().startswith('Attribute'):
                    code_start = i
                    break

        for i, line in enumerate(lines[code_start:], code_start + 1):
            stripped = line.strip()

            # Skip empty lines, pure comments, and form design lines
            if not stripped or stripped.startswith("'") or stripped.startswith("Attribute"):
                continue

            # Skip form design elements (Begin/End blocks)
            if stripped.startswith("Begin ") or stripped == "End":
                continue

            # Try each rule type pattern
            for rule_type, patterns in self._vb6_compiled.items():
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
            language=Language.VB6,
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

        # Check next line
        if line_num < len(lines):
            next_line = lines[line_num].strip()
            if next_line and not next_line.startswith("'"):
                return next_line

        return "continue"

    def _extract_variables(self, text: str) -> List[str]:
        """Extract variables from VB6 code."""
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, text)

        # VB6 keywords to exclude
        keywords = {
            'if', 'then', 'else', 'elseif', 'end', 'select', 'case',
            'and', 'or', 'not', 'xor', 'eqv', 'imp',
            'true', 'false', 'nothing', 'null', 'empty', 'is', 'like',
            'dim', 'as', 'new', 'byval', 'byref', 'optional', 'paramarray',
            'public', 'private', 'friend', 'static', 'global', 'const',
            'sub', 'function', 'property', 'get', 'let', 'set', 'type', 'enum',
            'for', 'to', 'step', 'next', 'while', 'wend', 'do', 'loop', 'until',
            'with', 'each', 'in', 'exit', 'goto', 'gosub', 'return', 'resume',
            'on', 'error', 'call', 'me', 'typeof',
            'string', 'integer', 'long', 'boolean', 'double', 'date', 'single',
            'object', 'variant', 'byte', 'currency', 'decimal', 'any',
            'debug', 'print', 'msgbox', 'inputbox', 'len', 'left', 'right', 'mid',
            'ubound', 'lbound', 'isempty', 'isnull', 'isnumeric', 'isdate', 'isarray',
            'cbool', 'cbyte', 'ccur', 'cdate', 'cdbl', 'cint', 'clng', 'csng', 'cstr', 'cvar',
            'err', 'now', 'date', 'time', 'timer', 'doevents', 'app',
        }

        return [m for m in matches if m.lower() not in keywords]

    def _extract_entities(self, text: str, variables: List[str]) -> List[str]:
        """Extract domain entities from VB6 code."""
        entities = set()

        # Common VB6 entity patterns
        entity_patterns = [
            r'\brs([A-Z][a-z]+\w*)',           # rsCustomer (recordset)
            r'\btbl([A-Z][a-z]+)',              # tblCustomer
            r'\bfrm([A-Z][a-z]+)',              # frmCustomer
            r'\bcls([A-Z][a-z]+)',              # clsCustomer
            r'\b([A-Z][a-z]+(?:ID|Id))\b',      # CustomerID
            r'\"([A-Z][a-z]+)\"',               # "Customer" in SQL strings
        ]

        for pattern in entity_patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)

        # Variables with entity-like names
        for var in variables:
            if len(var) > 3 and var[0].isupper():
                entities.add(var)

        return list(entities)
