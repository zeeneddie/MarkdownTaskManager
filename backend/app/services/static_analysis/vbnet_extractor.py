# backend/app/services/static_analysis/vbnet_extractor.py
"""
VB.NET Business Rule Extractor - Extracts business rules from VB.NET code.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline

Supports:
- VB.NET (.vb, .aspx.vb, .ascx.vb)
- ASP.NET code-behind files

Detection patterns:
- If-Then-Else blocks
- Select Case statements
- Property getters/setters with validation
- Event handlers with authorization checks
- Try-Catch error handling
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


class VBNetBusinessRuleExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from VB.NET source code.

    Uses regex-enhanced extraction (Tier 2) with optional LLM validation.
    Tested against HCI-CRS Agenda module (~1500 LOC, 235+ rules detected).
    """

    SUPPORTED_EXTENSIONS = ['.vb', '.aspx.vb', '.ascx.vb', '.aspx.cs']

    # VB.NET specific patterns for rule detection
    VBNET_PATTERNS: Dict[RuleType, List[str]] = {
        RuleType.VALIDATION: [
            r'If\s+(.+?)\s+Then',                           # General If-Then
            r'If\s+Not\s+(.+?)\s+Then',                     # Negated conditions
            r'If\s+String\.IsNullOrEmpty\s*\(',             # Null checks
            r'If\s+.*\.Length\s*[<>=]+',                    # Length validation
            r'If\s+.*Is\s+Nothing',                         # Nothing checks
            r'If\s+.*IsNot\s+Nothing',                      # Not nothing checks
        ],
        RuleType.AUTHORIZATION: [
            r'(CanView|CanEdit|CanDelete|CanAdd)',          # Permission flags
            r'(intCanView|intCanEdit|intCanDelete|intCanAdd)',  # Int permissions
            r'HasPermission\s*\(',                          # Permission check
            r'IsAllowed\s*\(',                              # Allowed check
            r'GetPrivileges\w*\s*\(',                       # Privilege lookup
            r'tablePermissions\.\w+',                       # Permission object
            r'CheckAccess\s*\(',                            # Access check
        ],
        RuleType.SCHEDULING: [
            r'(StartTime|EndTime|StartDate|EndDate)',       # Time boundaries
            r'(Duration|Interval)',                          # Time spans
            r'(datStart|datEnd|datumVan|datumTot)',         # Dutch date vars
            r'(AgendaStartTime|AgendaEndTime)',             # Agenda specific
            r'DateDiff\s*\(',                               # Date calculations
            r'TimeSpan',                                     # TimeSpan usage
        ],
        RuleType.WORKFLOW: [
            r'(Status|State)\s*(=|<>|Is)',                  # Status checks
            r'\.Status\s*=\s*["\'](\w+)["\']',              # Status assignment
            r'Case\s+Status\.',                             # Status case
        ],
        RuleType.BRANCHING: [
            r'Select\s+Case',                               # Select Case start
            r'Case\s+\d+',                                  # Numeric case
            r'Case\s+["\']',                                # String case
            r'Case\s+Else',                                 # Default case
            r'Case\s+Is\s*[<>=]',                           # Comparison case
        ],
        RuleType.THRESHOLD: [
            r'(\w+)\s*(>=|<=|>|<|=)\s*(\d+)',               # Numeric comparisons
            r'\.Count\s*[<>=]+\s*\d+',                      # Count checks
            r'\.Length\s*[<>=]+\s*\d+',                     # Length checks
        ],
        RuleType.DATA_ACCESS: [
            r'\.Execute\s*\(',                              # ADO Execute
            r'\.Open\s*\(',                                 # Connection open
            r'Recordset',                                   # ADO Recordset
            r'DataReader',                                  # DataReader
            r'DataAdapter',                                 # DataAdapter
            r'SqlCommand',                                  # SQL Command
            r'\.Fill\s*\(',                                 # Fill dataset
        ],
        RuleType.STATE_MANAGEMENT: [
            r'Session\s*\(',                                # Session access
            r'Session\s*\[',                                # Session indexer
            r'ViewState\s*\[',                              # ViewState
            r'Cache\s*\[',                                  # Cache access
            r'Application\s*\[',                            # Application state
        ],
        RuleType.ERROR_HANDLING: [
            r'Try\s*$',                                     # Try block
            r'Catch\s+',                                    # Catch block
            r'Finally\s*$',                                 # Finally block
            r'Throw\s+',                                    # Throw exception
            r'RaiseEvent\s+',                               # Raise event
            r'On\s+Error',                                  # Legacy error handling
        ],
        RuleType.NAVIGATION: [
            r'Response\.Redirect\s*\(',                     # Redirect
            r'Server\.Transfer\s*\(',                       # Server transfer
            r'NavigateUrl',                                 # Navigate URL
            r'\.Navigate\s*\(',                             # Navigation
        ],
    }

    # Symbol detection patterns
    CLASS_PATTERN = re.compile(
        r'^\s*(Partial\s+)?(Public\s+|Private\s+|Protected\s+|Friend\s+)?'
        r'(Class|Module|Interface)\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    SUB_PATTERN = re.compile(
        r'^\s*(Protected\s+|Private\s+|Public\s+|Friend\s+)?'
        r'(Overrides\s+|Overloads\s+|Shared\s+|MustOverride\s+)?'
        r'Sub\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    FUNCTION_PATTERN = re.compile(
        r'^\s*(Protected\s+|Private\s+|Public\s+|Friend\s+)?'
        r'(Overrides\s+|Overloads\s+|Shared\s+|MustOverride\s+)?'
        r'Function\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    PROPERTY_PATTERN = re.compile(
        r'^\s*(Protected\s+|Private\s+|Public\s+|Friend\s+)?'
        r'(Overrides\s+|Shared\s+|ReadOnly\s+|WriteOnly\s+)?'
        r'Property\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    ENUM_PATTERN = re.compile(
        r'^\s*(Protected\s+|Private\s+|Public\s+)?Enum\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    REGION_PATTERN = re.compile(
        r'#Region\s+"([^"]+)"',
        re.IGNORECASE
    )

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.FREE,
        project_id: Optional[int] = None,
    ):
        super().__init__(extraction_tier, project_id)
        self._current_region = ""
        self._compile_vbnet_patterns()

    def _compile_vbnet_patterns(self):
        """Compile VB.NET specific patterns."""
        self._vbnet_compiled: Dict[RuleType, List[re.Pattern]] = {}
        for rule_type, patterns in self.VBNET_PATTERNS.items():
            self._vbnet_compiled[rule_type] = [
                re.compile(p, re.IGNORECASE)
                for p in patterns
            ]

    def get_supported_extensions(self) -> List[str]:
        return self.SUPPORTED_EXTENSIONS

    def get_language(self) -> Language:
        return Language.VBNET

    def get_rule_patterns(self) -> Dict[RuleType, List[str]]:
        """Return VB.NET specific patterns."""
        return self.VBNET_PATTERNS

    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """Extract code symbols from VB.NET source."""
        symbols = []
        lines = source.split('\n')
        current_class = ""
        current_region = ""

        for i, line in enumerate(lines, 1):
            # Track regions
            region_match = self.REGION_PATTERN.search(line)
            if region_match:
                current_region = region_match.group(1)
            if '#End Region' in line:
                current_region = ""

            # Class/Module/Interface
            class_match = self.CLASS_PATTERN.match(line)
            if class_match:
                current_class = class_match.group(4)
                symbols.append(CodeSymbol(
                    name=current_class,
                    symbol_type="class",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Class'),
                    docstring=current_region,
                    parent="",
                    language=Language.VBNET,
                ))

            # Sub
            sub_match = self.SUB_PATTERN.match(line)
            if sub_match:
                symbols.append(CodeSymbol(
                    name=sub_match.group(3),
                    symbol_type="sub",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Sub'),
                    docstring=current_region,
                    parent=current_class,
                    language=Language.VBNET,
                ))

            # Function
            func_match = self.FUNCTION_PATTERN.match(line)
            if func_match:
                symbols.append(CodeSymbol(
                    name=func_match.group(3),
                    symbol_type="function",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Function'),
                    docstring=current_region,
                    parent=current_class,
                    language=Language.VBNET,
                ))

            # Property
            prop_match = self.PROPERTY_PATTERN.match(line)
            if prop_match:
                symbols.append(CodeSymbol(
                    name=prop_match.group(3),
                    symbol_type="property",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Property'),
                    docstring=current_region,
                    parent=current_class,
                    language=Language.VBNET,
                ))

            # Enum
            enum_match = self.ENUM_PATTERN.match(line)
            if enum_match:
                symbols.append(CodeSymbol(
                    name=enum_match.group(2),
                    symbol_type="enum",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'Enum'),
                    docstring="",
                    parent=current_class,
                    language=Language.VBNET,
                ))

        return symbols

    def _find_end_line(self, lines: List[str], start: int, block_type: str) -> int:
        """Find the End line for a VB.NET block."""
        end_pattern = re.compile(rf'^\s*End\s+{block_type}\b', re.IGNORECASE)
        depth = 1

        for i in range(start, len(lines)):
            line = lines[i]
            # Check for nested blocks of same type
            if re.search(rf'\b{block_type}\s+\w+', line, re.IGNORECASE) and i > start - 1:
                depth += 1
            if end_pattern.match(line):
                depth -= 1
                if depth == 0:
                    return i + 1

        return len(lines)

    async def _extract_rules_from_source(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from VB.NET source."""
        rules = []
        lines = source.split('\n')
        current_region = ""

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip empty lines and pure comments
            if not stripped or stripped.startswith("'"):
                continue

            # Track regions for context
            region_match = self.REGION_PATTERN.search(line)
            if region_match:
                current_region = region_match.group(1)
            if '#End Region' in line:
                current_region = ""

            # Try each rule type pattern
            for rule_type, patterns in self._vbnet_compiled.items():
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
                            region=current_region,
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
        region: str,
        symbols: List[CodeSymbol],
    ) -> Optional[BusinessRule]:
        """Create a BusinessRule from a regex match."""

        # Extract condition
        if rule_type == RuleType.VALIDATION and 'If ' in line:
            # Extract full If condition
            cond_match = re.search(r'If\s+(.+?)\s+Then', line, re.IGNORECASE)
            condition = cond_match.group(1) if cond_match else match.group(0)
        else:
            condition = match.group(0)

        # Extract action (next statement or after Then)
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
            language=Language.VBNET,
            extraction_method=ExtractionMethod.REGEX,
            extraction_tier=self.extraction_tier,
            code_snippet=line.strip()[:150],
            parent_function=parent_function,
            parent_class=parent_class,
            region=region,
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
        """Extract variables from VB.NET code."""
        # VB.NET identifier pattern
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, text)

        # VB.NET keywords to exclude
        keywords = {
            'if', 'then', 'else', 'elseif', 'end', 'select', 'case',
            'and', 'or', 'not', 'andalso', 'orelse', 'xor',
            'true', 'false', 'nothing', 'is', 'isnot', 'like',
            'dim', 'as', 'new', 'byval', 'byref', 'optional',
            'public', 'private', 'protected', 'friend', 'shared',
            'sub', 'function', 'property', 'class', 'module',
            'for', 'to', 'step', 'next', 'while', 'do', 'loop',
            'try', 'catch', 'finally', 'throw', 'return',
            'me', 'mybase', 'myclass', 'typeof', 'gettype',
            'string', 'integer', 'long', 'boolean', 'double', 'date',
            'object', 'variant', 'byte', 'short', 'single', 'decimal',
            'response', 'request', 'server', 'session', 'application',
        }

        return [m for m in matches if m.lower() not in keywords]

    def _extract_entities(self, text: str, variables: List[str]) -> List[str]:
        """Extract domain entities from VB.NET code."""
        entities = set()

        # HCI-CRS specific entity patterns
        hci_patterns = [
            r'\bta([A-Z][a-z]+\w*)',           # taAfspraak, taClient
            r'\b([A-Z][a-z]+(?:ID|Id))\b',     # AfspraakID, ClientId
            r'\brst([A-Z][a-z]+)',             # rstAfspraak (recordset)
            r'\btbl([A-Z][a-z]+)',             # tblAfspraak
        ]

        for pattern in hci_patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)

        # General entity patterns
        for var in variables:
            # CamelCase/PascalCase entities
            if len(var) > 3 and var[0].isupper():
                entities.add(var)

        return list(entities)
