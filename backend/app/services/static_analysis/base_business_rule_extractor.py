# backend/app/services/static_analysis/base_business_rule_extractor.py
"""
Base Business Rule Extractor - Abstract base class for language-specific extractors.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline

Design:
- Abstract base class with common functionality
- Language-specific extractors inherit and implement extract methods
- Tier-aware extraction with optional LLM validation
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
import re
import logging
import time

from .extraction_models import (
    BusinessRule,
    CodeSymbol,
    NFRIndicator,
    ExtractionResult,
    RuleType,
    Language,
    ExtractionTier,
    ExtractionMethod,
    EXTENSION_LANGUAGE_MAP,
    TIER_TARGET_CONFIDENCE,
)

logger = logging.getLogger(__name__)


class BaseBusinessRuleExtractor(ABC):
    """
    Abstract base class for language-specific business rule extractors.

    Implements the 3-tier extraction strategy:
    - Tier 1 (AST): Full parsing where available
    - Tier 2 (Regex): Pattern-based extraction for legacy languages
    - Tier 3 (LLM): Optional LLM-assisted validation/enhancement

    Subclasses must implement:
    - get_supported_extensions()
    - get_language()
    - _extract_symbols()
    - _extract_rules_from_source()
    """

    # Common rule type patterns (can be overridden by subclasses)
    COMMON_PATTERNS: Dict[RuleType, List[str]] = {
        RuleType.VALIDATION: [
            r'if\s+.*(?:is_valid|validate|check)',
            r'if\s+.*(?:empty|null|none|blank)',
            r'if\s+len\s*\(',
            r'if\s+.*(?:min|max|range)',
        ],
        RuleType.AUTHORIZATION: [
            r'(?:can|has|is)_(?:admin|auth|permission|allowed)',
            r'(?:check|verify)_(?:permission|role|access)',
            r'(?:require|need).*(?:auth|permission|role)',
        ],
        RuleType.WORKFLOW: [
            r'(?:status|state)\s*[=<>!]',
            r'(?:transition|change_state|set_status)',
            r'(?:approve|reject|submit|cancel|complete)',
        ],
        RuleType.CALCULATION: [
            r'(?:total|sum|avg|calculate|compute)',
            r'(?:price|cost|amount|tax|discount)\s*[=+\-*/]',
        ],
        RuleType.ERROR_HANDLING: [
            r'(?:try|catch|except|finally|throw|raise)',
            r'(?:error|exception|fail)',
        ],
    }

    # NFR category indicators
    NFR_INDICATORS: Dict[str, List[Tuple[str, str]]] = {
        'performance': [
            (r'cache|caching', 'Caching implemented for performance'),
            (r'async|await|thread', 'Asynchronous/parallel processing'),
            (r'batch|bulk', 'Batch processing for efficiency'),
        ],
        'security': [
            (r'encrypt|hash|secure', 'Data security measures'),
            (r'auth|permission|access', 'Access control implemented'),
            (r'session|token|jwt', 'Session/token management'),
        ],
        'usability': [
            (r'message|alert|notify', 'User feedback mechanisms'),
            (r'redirect|navigate', 'User navigation handling'),
            (r'validation|required', 'Input validation for users'),
        ],
        'reliability': [
            (r'try|catch|error|exception', 'Error handling for reliability'),
            (r'log|trace|debug', 'Logging for diagnostics'),
            (r'rollback|transaction', 'Transaction handling'),
        ],
        'maintainability': [
            (r'const|readonly|final', 'Constants for maintainability'),
            (r'enum|enumeration', 'Enumerations for type safety'),
            (r'region|comment|doc', 'Code organization'),
        ],
    }

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.FREE,
        project_id: Optional[int] = None,
    ):
        """
        Initialize the extractor.

        Args:
            extraction_tier: Customer tier determining LLM access
            project_id: Optional project ID for tracking
        """
        self.extraction_tier = extraction_tier
        self.project_id = project_id
        self._rule_counter = 0
        self._nfr_counter = 0
        self._compiled_patterns: Dict[RuleType, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        patterns = self.get_rule_patterns()
        for rule_type, pattern_list in patterns.items():
            self._compiled_patterns[rule_type] = [
                re.compile(p, re.IGNORECASE | re.MULTILINE)
                for p in pattern_list
            ]

    def get_rule_patterns(self) -> Dict[RuleType, List[str]]:
        """
        Get rule detection patterns. Override in subclasses for language-specific patterns.

        Returns:
            Dictionary mapping RuleType to list of regex patterns
        """
        return self.COMMON_PATTERNS

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of file extensions this extractor supports.

        Returns:
            List of extensions like ['.vb', '.aspx.vb']
        """
        pass

    @abstractmethod
    def get_language(self) -> Language:
        """
        Get the language this extractor handles.

        Returns:
            Language enum value
        """
        pass

    @abstractmethod
    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """
        Extract code symbols (classes, methods, functions, etc.) from source.

        Args:
            source: Source code content
            file_path: Path to source file

        Returns:
            List of CodeSymbol objects
        """
        pass

    @abstractmethod
    async def _extract_rules_from_source(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """
        Extract business rules from source code.

        Args:
            source: Source code content
            file_path: Path to source file
            symbols: Already extracted code symbols for context

        Returns:
            List of BusinessRule objects
        """
        pass

    def supports_file(self, file_path: str) -> bool:
        """Check if this extractor supports the given file."""
        path = Path(file_path)

        # Check compound extensions first (e.g., .aspx.vb)
        for ext in self.get_supported_extensions():
            if file_path.lower().endswith(ext.lower()):
                return True

        # Check simple extension
        return path.suffix.lower() in [ext.lower() for ext in self.get_supported_extensions()]

    def _generate_rule_id(self) -> str:
        """Generate a unique rule ID."""
        self._rule_counter += 1
        return f"BR-{self._rule_counter:04d}"

    def _generate_nfr_id(self) -> str:
        """Generate a unique NFR ID."""
        self._nfr_counter += 1
        return f"NFR-{self._nfr_counter:03d}"

    def _classify_rule_type(self, text: str) -> Optional[RuleType]:
        """
        Classify the type of business rule based on text content.

        Args:
            text: Code or condition text to classify

        Returns:
            RuleType or None if no match
        """
        for rule_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return rule_type
        return None

    def _calculate_confidence(
        self,
        rule_type: RuleType,
        condition: str,
        variables: List[str],
        has_clear_action: bool = True,
    ) -> float:
        """
        Calculate confidence score for a detected rule.

        Args:
            rule_type: Detected rule type
            condition: The condition/trigger
            variables: Variables involved
            has_clear_action: Whether action is clearly defined

        Returns:
            Confidence score 0.0-1.0
        """
        base_confidence = 0.5

        # Higher confidence for certain rule types
        type_boost = {
            RuleType.AUTHORIZATION: 0.15,
            RuleType.VALIDATION: 0.10,
            RuleType.WORKFLOW: 0.10,
            RuleType.DATA_ACCESS: 0.10,
            RuleType.ERROR_HANDLING: 0.05,
        }
        base_confidence += type_boost.get(rule_type, 0.0)

        # Boost for domain-like variable names
        domain_indicators = ['id', 'name', 'date', 'time', 'status', 'type', 'code', 'amount']
        domain_vars = [v for v in variables if any(ind in v.lower() for ind in domain_indicators)]
        base_confidence += min(len(domain_vars) * 0.05, 0.15)

        # Boost for clear action
        if has_clear_action:
            base_confidence += 0.1

        # Adjust based on tier targets
        min_target, max_target = TIER_TARGET_CONFIDENCE[self.extraction_tier]

        return min(base_confidence, 0.95)

    def _generate_natural_language(
        self,
        rule_type: RuleType,
        condition: str,
        action: str,
    ) -> str:
        """
        Generate human-readable description of the rule.

        Args:
            rule_type: Type of rule
            condition: Condition/trigger
            action: Action/consequence

        Returns:
            Natural language description
        """
        templates = {
            RuleType.VALIDATION: "WHEN {condition}, THEN validate {action}",
            RuleType.AUTHORIZATION: "IF {condition}, THEN authorize {action}",
            RuleType.SCHEDULING: "WHEN {condition}, THEN schedule {action}",
            RuleType.WORKFLOW: "WHEN {condition}, THEN transition to {action}",
            RuleType.BRANCHING: "WHEN {condition}, THEN branch to {action}",
            RuleType.THRESHOLD: "IF {condition}, THEN enforce limit {action}",
            RuleType.DATA_ACCESS: "WHEN {condition}, THEN access data {action}",
            RuleType.STATE_MANAGEMENT: "WHEN {condition}, THEN manage state {action}",
            RuleType.ERROR_HANDLING: "IF {condition}, THEN handle error {action}",
            RuleType.NAVIGATION: "WHEN {condition}, THEN navigate to {action}",
            RuleType.CALCULATION: "WHEN {condition}, THEN calculate {action}",
            RuleType.CONSTRAINT: "ENFORCE that {condition} results in {action}",
            RuleType.DERIVATION: "DERIVE {action} FROM {condition}",
        }

        template = templates.get(rule_type, "IF {condition} THEN {action}")

        # Truncate long conditions/actions
        cond_short = condition[:80] + "..." if len(condition) > 80 else condition
        action_short = action[:80] + "..." if len(action) > 80 else action

        return template.format(condition=cond_short, action=action_short)

    def _extract_variables(self, text: str) -> List[str]:
        """
        Extract variable names from code text.

        Args:
            text: Code text to analyze

        Returns:
            List of variable names
        """
        # Match identifier patterns
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, text)

        # Filter out common keywords (language-agnostic)
        keywords = {
            'if', 'else', 'then', 'end', 'and', 'or', 'not', 'true', 'false',
            'null', 'none', 'is', 'in', 'as', 'for', 'while', 'do', 'loop',
            'select', 'case', 'when', 'where', 'from', 'to', 'step',
            'function', 'sub', 'class', 'public', 'private', 'protected',
            'dim', 'const', 'let', 'var', 'return', 'set', 'get',
            'new', 'me', 'this', 'self', 'typeof', 'instanceof',
        }

        return [m for m in matches if m.lower() not in keywords]

    def _extract_entities(self, text: str, variables: List[str]) -> List[str]:
        """
        Extract domain entity names from text and variables.

        Args:
            text: Code text
            variables: Already extracted variables

        Returns:
            List of likely entity names
        """
        entities = set()

        # Common entity patterns
        entity_patterns = [
            r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b',  # PascalCase
            r'ta([A-Z][a-z]+)',  # HCI-CRS table prefix
            r'tbl([A-Z][a-z]+)',  # Common table prefix
            r'(?:record|row|item|entry)_?([A-Z][a-z]+)',
        ]

        for pattern in entity_patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)

        # Also check variables for entity-like names
        for var in variables:
            if var[0].isupper() and len(var) > 3:
                entities.add(var)

        return list(entities)

    async def _extract_nfrs(self, source: str, file_path: str) -> List[NFRIndicator]:
        """
        Detect non-functional requirement indicators in source.

        Args:
            source: Source code content
            file_path: Path to source file

        Returns:
            List of NFRIndicator objects
        """
        nfrs = []

        for category, indicators in self.NFR_INDICATORS.items():
            for pattern, description in indicators:
                matches = re.findall(pattern, source, re.IGNORECASE)
                if matches:
                    nfrs.append(NFRIndicator(
                        id=self._generate_nfr_id(),
                        category=category,
                        description=description,
                        metric=f"{len(matches)} occurrences",
                        source_text=f"Pattern: {pattern}",
                        source_file=file_path,
                    ))

        return nfrs

    async def extract_from_file(
        self,
        file_path: str,
        source: Optional[str] = None,
    ) -> ExtractionResult:
        """
        Extract all business rules, symbols, and NFRs from a file.

        Args:
            file_path: Path to source file
            source: Optional source content (if not provided, file will be read)

        Returns:
            ExtractionResult with all extracted data
        """
        start_time = time.time()

        # Read file if source not provided
        if source is None:
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    source = f.read()
            except UnicodeDecodeError:
                # Try with latin-1 as fallback
                with open(file_path, 'r', encoding='latin-1') as f:
                    source = f.read()
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                return ExtractionResult(
                    source_path=file_path,
                    language=self.get_language(),
                    extraction_tier=self.extraction_tier,
                    extraction_method=ExtractionMethod.REGEX,
                    business_rules=[],
                    code_symbols=[],
                    nfr_indicators=[],
                    errors=[str(e)],
                )

        lines_of_code = len(source.split('\n'))

        # Extract symbols first (provides context for rule extraction)
        try:
            symbols = await self._extract_symbols(source, file_path)
        except Exception as e:
            logger.warning(f"Error extracting symbols from {file_path}: {e}")
            symbols = []

        # Extract business rules
        try:
            rules = await self._extract_rules_from_source(source, file_path, symbols)
        except Exception as e:
            logger.warning(f"Error extracting rules from {file_path}: {e}")
            rules = []

        # Extract NFRs
        try:
            nfrs = await self._extract_nfrs(source, file_path)
        except Exception as e:
            logger.warning(f"Error extracting NFRs from {file_path}: {e}")
            nfrs = []

        extraction_time = int((time.time() - start_time) * 1000)

        return ExtractionResult(
            source_path=file_path,
            language=self.get_language(),
            extraction_tier=self.extraction_tier,
            extraction_method=ExtractionMethod.REGEX,  # Default, override in subclasses
            business_rules=rules,
            code_symbols=symbols,
            nfr_indicators=nfrs,
            lines_of_code=lines_of_code,
            extraction_time_ms=extraction_time,
        )

    async def extract_from_directory(
        self,
        directory: str,
        recursive: bool = True,
    ) -> Dict[str, ExtractionResult]:
        """
        Extract from all supported files in a directory.

        Args:
            directory: Path to directory
            recursive: Whether to scan subdirectories

        Returns:
            Dictionary mapping file paths to ExtractionResults
        """
        results = {}
        path = Path(directory)

        if not path.exists():
            logger.error(f"Directory not found: {directory}")
            return results

        # Find all supported files
        pattern = '**/*' if recursive else '*'
        for file_path in path.glob(pattern):
            if file_path.is_file() and self.supports_file(str(file_path)):
                try:
                    result = await self.extract_from_file(str(file_path))
                    results[str(file_path)] = result
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")

        return results

    def _find_parent_symbol(
        self,
        line_num: int,
        symbols: List[CodeSymbol],
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Find the parent class and function for a given line number.

        Args:
            line_num: Line number to find parent for
            symbols: List of code symbols

        Returns:
            Tuple of (parent_class, parent_function)
        """
        parent_class = None
        parent_function = None

        for symbol in symbols:
            if symbol.line_start <= line_num <= symbol.line_end:
                if symbol.symbol_type == 'class':
                    parent_class = symbol.name
                elif symbol.symbol_type in ('method', 'function', 'sub'):
                    parent_function = symbol.name

        return parent_class, parent_function
