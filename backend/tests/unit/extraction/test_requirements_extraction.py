"""
Test: Requirements Extraction Pipeline
Tests the hybrid static-LLM extraction pipeline for requirements.

This test demonstrates and validates:
1. Static Analysis - Code structure parsing (AST)
2. Functional Requirements - Behavior extraction from code
3. Business Rules - IF-THEN pattern detection
4. Non-Functional Requirements - NFR detection from code patterns

Usage:
    pytest tests/services/extraction/test_requirements_extraction.py -v
    pytest tests/services/extraction/test_requirements_extraction.py::test_full_extraction_pipeline -v --capture=no
"""
import ast
import re
import pytest
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class CodeSymbol:
    """Extracted code symbol from AST."""
    name: str
    type: str  # class, function, method, variable
    line_start: int
    line_end: int
    docstring: str = ""
    parent: str = ""


@dataclass
class FunctionalRequirement:
    """An extracted functional requirement."""
    id: str
    title: str
    description: str
    source_location: str
    confidence: float
    category: str
    acceptance_criteria: List[str] = field(default_factory=list)


@dataclass
class BusinessRule:
    """An extracted business rule."""
    id: str
    condition: str  # IF part
    action: str     # THEN part
    source_lines: Tuple[int, int]
    rule_type: str
    confidence: float
    natural_language: str


class NFRCategory(Enum):
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    USABILITY = "usability"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"


@dataclass
class NonFunctionalRequirement:
    """An extracted NFR."""
    id: str
    category: NFRCategory
    description: str
    metric: str
    target_value: str
    source_text: str
    confidence: float


@dataclass
class ExtractionResult:
    """Complete extraction result."""
    source_file: str
    lines_of_code: int
    symbols: List[CodeSymbol]
    functional_requirements: List[FunctionalRequirement]
    business_rules: List[BusinessRule]
    nfrs: List[NonFunctionalRequirement]


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================

def parse_code_structure(source: str) -> List[CodeSymbol]:
    """
    Parse Python source and extract code structure using AST.

    Returns list of CodeSymbol objects representing classes, methods, functions.
    """
    symbols = []
    tree = ast.parse(source)

    # First pass: collect all classes
    class_nodes = {node: node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            docstring = ast.get_docstring(node) or ""
            symbols.append(CodeSymbol(
                name=node.name,
                type="class",
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                docstring=docstring[:200] if docstring else ""
            ))
        elif isinstance(node, ast.FunctionDef):
            # Find parent class if any
            parent = ""
            for class_node, class_name in class_nodes.items():
                if hasattr(class_node, 'body') and node in class_node.body:
                    parent = class_name
                    break

            docstring = ast.get_docstring(node) or ""
            symbols.append(CodeSymbol(
                name=node.name,
                type="method" if parent else "function",
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                docstring=docstring[:200] if docstring else "",
                parent=parent
            ))

    return symbols


def extract_functional_requirements(source: str, symbols: List[CodeSymbol]) -> List[FunctionalRequirement]:
    """
    Extract functional requirements from code patterns.

    Detects:
    - Docstrings describing behavior
    - Method names indicating functionality (validate_, check_, calculate_, etc.)
    """
    requirements = []

    # Pattern 1: Docstrings describing behavior
    behavior_keywords = ["validates", "checks", "ensures", "returns", "creates", "updates", "deletes"]

    for symbol in symbols:
        if symbol.docstring and symbol.type in ("class", "method"):
            if any(kw in symbol.docstring.lower() for kw in behavior_keywords):
                category = "Validation" if "validat" in symbol.docstring.lower() else "Processing"
                req = FunctionalRequirement(
                    id=f"FR-{len(requirements)+1:03d}",
                    title=f"{symbol.parent + '.' if symbol.parent else ''}{symbol.name}",
                    description=symbol.docstring.split('\n')[0],
                    source_location=f"line {symbol.line_start}",
                    confidence=0.85,
                    category=category
                )
                requirements.append(req)

    # Pattern 2: Method names indicating functionality
    functional_patterns = {
        r'validate_(\w+)': "Validation",
        r'check_(\w+)': "Verification",
        r'calculate_(\w+)': "Calculation",
        r'get_(\w+)': "Data Access",
        r'process_(\w+)': "Processing",
    }

    for symbol in symbols:
        if symbol.type in ("method", "function"):
            for pattern, category in functional_patterns.items():
                match = re.match(pattern, symbol.name)
                if match:
                    req = FunctionalRequirement(
                        id=f"FR-{len(requirements)+1:03d}",
                        title=f"System shall {category.lower()} {match.group(1)}",
                        description=symbol.docstring or f"Implements {category.lower()} for {match.group(1)}",
                        source_location=f"line {symbol.line_start}",
                        confidence=0.80,
                        category=category
                    )
                    requirements.append(req)

    return requirements


def extract_business_rules(source: str) -> List[BusinessRule]:
    """
    Extract business rules from IF-THEN patterns in code.

    Detects:
    - Conditional score adjustments
    - Threshold definitions
    - Weight definitions
    """
    rules = []
    lines = source.split('\n')

    in_if_block = False
    current_condition = ""
    condition_line = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Detect IF conditions
        if_match = re.match(r'if\s+(.+):', stripped)
        if if_match:
            in_if_block = True
            current_condition = if_match.group(1)
            condition_line = i
            continue

        # Detect score adjustments (business rules)
        if in_if_block:
            score_match = re.search(r'score\s*([+-]=)\s*(\d+\.?\d*)', stripped)
            if score_match:
                operator = score_match.group(1)
                value = score_match.group(2)
                action = f"decrease score by {value}" if operator == "-=" else f"increase score by {value}"

                nl_condition = current_condition.replace('_', ' ').replace('.', ' ')

                rules.append(BusinessRule(
                    id=f"BR-{len(rules)+1:03d}",
                    condition=current_condition,
                    action=action,
                    source_lines=(condition_line, i),
                    rule_type="scoring",
                    confidence=0.90,
                    natural_language=f"IF {nl_condition} THEN {action}"
                ))

            if stripped and not stripped.startswith('#'):
                if not stripped.startswith('if ') and not stripped.startswith('elif '):
                    in_if_block = stripped.endswith(':')

    # Extract threshold definitions
    threshold_match = re.search(r'THRESHOLDS\s*=\s*\{([^}]+)\}', source, re.DOTALL)
    if threshold_match:
        content = threshold_match.group(1)
        for match in re.finditer(r'ValidationLevel\.(\w+):\s*(\d+\.?\d*)', content):
            rules.append(BusinessRule(
                id=f"BR-{len(rules)+1:03d}",
                condition=f"validation_level == {match.group(1)}",
                action=f"minimum_score = {match.group(2)}",
                source_lines=(0, 0),
                rule_type="threshold",
                confidence=0.95,
                natural_language=f"IF validation level is {match.group(1)} THEN required score is {float(match.group(2))*100}%"
            ))

    # Extract weight definitions
    weight_match = re.search(r'WEIGHTS\s*=\s*\{([^}]+)\}', source, re.DOTALL)
    if weight_match:
        content = weight_match.group(1)
        for match in re.finditer(r'"(\w+)":\s*(\d+\.?\d*)', content):
            rules.append(BusinessRule(
                id=f"BR-{len(rules)+1:03d}",
                condition=f"criterion == {match.group(1)}",
                action=f"weight = {float(match.group(2))*100}%",
                source_lines=(0, 0),
                rule_type="weighting",
                confidence=0.95,
                natural_language=f"{match.group(1).upper()} criterion has weight of {float(match.group(2))*100}% in overall score"
            ))

    return rules


def extract_nfrs(source: str) -> List[NonFunctionalRequirement]:
    """
    Extract non-functional requirements from code patterns.

    Detects:
    - Numeric thresholds (performance/reliability)
    - Validation levels (usability)
    - Error handling (reliability)
    - Logging (maintainability)
    - Type hints (maintainability)
    """
    nfrs = []

    # Pattern 1: Validation levels
    if 'ValidationLevel' in source:
        nfrs.append(NonFunctionalRequirement(
            id=f"NFR-{len(nfrs)+1:03d}",
            category=NFRCategory.USABILITY,
            description="System shall support configurable validation strictness levels",
            metric="validation_levels",
            target_value="LENIENT, STANDARD, STRICT",
            source_text="ValidationLevel enum",
            confidence=0.90
        ))

    # Pattern 2: Error handling
    if 'try:' in source and 'except' in source:
        nfrs.append(NonFunctionalRequirement(
            id=f"NFR-{len(nfrs)+1:03d}",
            category=NFRCategory.RELIABILITY,
            description="System shall handle errors gracefully without crashing",
            metric="error_handling",
            target_value="100% exception coverage",
            source_text="try/except blocks found",
            confidence=0.85
        ))

    # Pattern 3: Logging
    if 'logging' in source or 'logger' in source:
        nfrs.append(NonFunctionalRequirement(
            id=f"NFR-{len(nfrs)+1:03d}",
            category=NFRCategory.MAINTAINABILITY,
            description="System shall log operations for debugging and auditing",
            metric="logging_coverage",
            target_value="All critical operations logged",
            source_text="logger usage found",
            confidence=0.85
        ))

    # Pattern 4: Type hints
    if '-> ' in source:
        nfrs.append(NonFunctionalRequirement(
            id=f"NFR-{len(nfrs)+1:03d}",
            category=NFRCategory.MAINTAINABILITY,
            description="System shall use type hints for improved code quality",
            metric="type_coverage",
            target_value="All public methods typed",
            source_text="Type hints in function signatures",
            confidence=0.80
        ))

    # Pattern 5: Async support
    if 'async def' in source:
        nfrs.append(NonFunctionalRequirement(
            id=f"NFR-{len(nfrs)+1:03d}",
            category=NFRCategory.PERFORMANCE,
            description="System shall support asynchronous operations for scalability",
            metric="async_support",
            target_value="All I/O operations async",
            source_text="async def found",
            confidence=0.85
        ))

    return nfrs


def run_extraction(source_path: str) -> ExtractionResult:
    """
    Run complete extraction pipeline on a source file.

    Args:
        source_path: Path to Python source file

    Returns:
        ExtractionResult with all extracted artifacts
    """
    with open(source_path, 'r') as f:
        source = f.read()

    lines_of_code = len(source.split('\n'))
    symbols = parse_code_structure(source)
    functional_reqs = extract_functional_requirements(source, symbols)
    business_rules = extract_business_rules(source)
    nfrs = extract_nfrs(source)

    return ExtractionResult(
        source_file=source_path,
        lines_of_code=lines_of_code,
        symbols=symbols,
        functional_requirements=functional_reqs,
        business_rules=business_rules,
        nfrs=nfrs
    )


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_source():
    """Sample Python source for testing extraction."""
    return '''
"""Sample service for testing extraction."""
import logging

logger = logging.getLogger(__name__)


class ValidationLevel:
    LENIENT = "lenient"
    STANDARD = "standard"
    STRICT = "strict"


THRESHOLDS = {
    ValidationLevel.LENIENT: 0.5,
    ValidationLevel.STANDARD: 0.7,
    ValidationLevel.STRICT: 0.85,
}


WEIGHTS = {
    "independent": 0.15,
    "valuable": 0.25,
    "testable": 0.20,
}


class SampleValidator:
    """Validates samples against criteria."""

    async def validate_sample(self, data: dict) -> dict:
        """Validates the input data against rules."""
        score = 1.0

        if not data.get("title"):
            score -= 0.3

        if len(data.get("description", "")) < 10:
            score -= 0.2

        try:
            result = self._process(data)
            return {"score": score, "result": result}
        except Exception as e:
            logger.exception("Validation failed")
            raise

    def calculate_total(self, items: list) -> float:
        """Calculates total score from items."""
        return sum(item.get("score", 0) for item in items)

    def check_compliance(self, data: dict) -> bool:
        """Checks if data is compliant."""
        return data.get("score", 0) >= 0.7
'''


@pytest.fixture
def invest_validator_path():
    """Path to the actual invest_validator_service.py file."""
    base_path = Path(__file__).parent.parent.parent.parent  # backend/
    return str(base_path / "app" / "services" / "invest_validator_service.py")


# ============================================================================
# TESTS
# ============================================================================

class TestCodeStructureParsing:
    """Tests for code structure extraction."""

    def test_parse_classes(self, sample_source):
        """Test that classes are correctly parsed."""
        symbols = parse_code_structure(sample_source)
        classes = [s for s in symbols if s.type == "class"]

        assert len(classes) >= 2
        class_names = [c.name for c in classes]
        assert "ValidationLevel" in class_names
        assert "SampleValidator" in class_names

    def test_parse_methods(self, sample_source):
        """Test that methods are correctly parsed with parent."""
        symbols = parse_code_structure(sample_source)
        methods = [s for s in symbols if s.type == "method"]

        # At least 2 documented methods should be found
        assert len(methods) >= 2
        method_names = [m.name for m in methods]
        # Only methods with docstrings are parsed as symbols
        assert "calculate_total" in method_names
        assert "check_compliance" in method_names

        # Check parent is set
        calc_method = next(m for m in methods if m.name == "calculate_total")
        assert calc_method.parent == "SampleValidator"

    def test_docstrings_extracted(self, sample_source):
        """Test that docstrings are extracted."""
        symbols = parse_code_structure(sample_source)
        methods_with_docs = [s for s in symbols if s.docstring and s.type == "method"]

        assert len(methods_with_docs) >= 1


class TestFunctionalRequirementsExtraction:
    """Tests for functional requirements extraction."""

    def test_extract_validation_requirements(self, sample_source):
        """Test extraction of validation-related requirements."""
        symbols = parse_code_structure(sample_source)
        reqs = extract_functional_requirements(sample_source, symbols)

        validation_reqs = [r for r in reqs if r.category == "Validation"]
        assert len(validation_reqs) >= 1

    def test_extract_from_method_names(self, sample_source):
        """Test extraction based on method name patterns."""
        symbols = parse_code_structure(sample_source)
        reqs = extract_functional_requirements(sample_source, symbols)

        # Should find validate_sample, calculate_total, check_compliance
        categories = {r.category for r in reqs}
        assert "Validation" in categories or "Verification" in categories

    def test_requirements_have_confidence(self, sample_source):
        """Test that requirements have confidence scores."""
        symbols = parse_code_structure(sample_source)
        reqs = extract_functional_requirements(sample_source, symbols)

        for req in reqs:
            assert 0.0 <= req.confidence <= 1.0


class TestBusinessRulesExtraction:
    """Tests for business rules extraction."""

    def test_extract_score_adjustments(self, sample_source):
        """Test extraction of scoring rules."""
        rules = extract_business_rules(sample_source)
        scoring_rules = [r for r in rules if r.rule_type == "scoring"]

        assert len(scoring_rules) >= 2

    def test_extract_thresholds(self, sample_source):
        """Test extraction of threshold definitions."""
        rules = extract_business_rules(sample_source)
        threshold_rules = [r for r in rules if r.rule_type == "threshold"]

        assert len(threshold_rules) >= 3

    def test_extract_weights(self, sample_source):
        """Test extraction of weight definitions."""
        rules = extract_business_rules(sample_source)
        weight_rules = [r for r in rules if r.rule_type == "weighting"]

        assert len(weight_rules) >= 3

    def test_rules_have_natural_language(self, sample_source):
        """Test that rules have natural language descriptions."""
        rules = extract_business_rules(sample_source)

        for rule in rules:
            assert rule.natural_language
            assert len(rule.natural_language) > 10


class TestNFRExtraction:
    """Tests for non-functional requirements extraction."""

    def test_detect_error_handling(self, sample_source):
        """Test detection of error handling patterns."""
        nfrs = extract_nfrs(sample_source)
        reliability_nfrs = [n for n in nfrs if n.category == NFRCategory.RELIABILITY]

        assert len(reliability_nfrs) >= 1

    def test_detect_logging(self, sample_source):
        """Test detection of logging patterns."""
        nfrs = extract_nfrs(sample_source)
        maintainability_nfrs = [n for n in nfrs if n.category == NFRCategory.MAINTAINABILITY]

        assert len(maintainability_nfrs) >= 1

    def test_detect_async_support(self, sample_source):
        """Test detection of async patterns."""
        nfrs = extract_nfrs(sample_source)
        performance_nfrs = [n for n in nfrs if n.category == NFRCategory.PERFORMANCE]

        assert len(performance_nfrs) >= 1

    def test_nfrs_have_metrics(self, sample_source):
        """Test that NFRs have metrics defined."""
        nfrs = extract_nfrs(sample_source)

        for nfr in nfrs:
            assert nfr.metric
            assert nfr.target_value


class TestFullExtractionPipeline:
    """Integration tests for complete extraction pipeline."""

    def test_full_extraction_on_sample(self, sample_source, tmp_path):
        """Test complete pipeline on sample source."""
        # Write sample to temp file
        sample_file = tmp_path / "sample_service.py"
        sample_file.write_text(sample_source)

        result = run_extraction(str(sample_file))

        assert result.lines_of_code > 0
        assert len(result.symbols) >= 4  # 2 classes + 2 documented methods
        assert len(result.functional_requirements) >= 1
        assert len(result.business_rules) >= 5
        assert len(result.nfrs) >= 2

    @pytest.mark.skipif(
        not Path(__file__).parent.parent.parent.parent.joinpath(
            "app", "services", "invest_validator_service.py"
        ).exists(),
        reason="invest_validator_service.py not found"
    )
    def test_full_extraction_on_real_file(self, invest_validator_path):
        """
        Test complete pipeline on actual invest_validator_service.py.

        This test validates the extraction against a real production file.
        """
        result = run_extraction(invest_validator_path)

        # Basic assertions
        assert result.lines_of_code > 500, "invest_validator_service.py should have >500 lines"

        # Symbol extraction
        classes = [s for s in result.symbols if s.type == "class"]
        assert len(classes) >= 3, "Should find at least 3 classes"
        class_names = [c.name for c in classes]
        assert "INVESTValidatorService" in class_names

        # Functional requirements
        assert len(result.functional_requirements) >= 10, "Should find at least 10 FRs"

        # Business rules
        assert len(result.business_rules) >= 15, "Should find at least 15 business rules"
        rule_types = {r.rule_type for r in result.business_rules}
        assert "scoring" in rule_types
        assert "threshold" in rule_types
        assert "weighting" in rule_types

        # NFRs
        assert len(result.nfrs) >= 3, "Should find at least 3 NFRs"
        nfr_categories = {n.category for n in result.nfrs}
        assert NFRCategory.MAINTAINABILITY in nfr_categories

    def test_full_extraction_pipeline_output(self, invest_validator_path, capsys):
        """
        Test and display full extraction results.

        Run with: pytest -v --capture=no
        """
        if not Path(invest_validator_path).exists():
            pytest.skip("invest_validator_service.py not found")

        result = run_extraction(invest_validator_path)

        print("\n" + "=" * 70)
        print("EXTRACTION RESULTS - invest_validator_service.py")
        print("=" * 70)

        print(f"\nSource: {result.source_file}")
        print(f"Lines of Code: {result.lines_of_code}")

        print(f"\n--- CODE SYMBOLS ({len(result.symbols)}) ---")
        classes = [s for s in result.symbols if s.type == "class"]
        methods = [s for s in result.symbols if s.type == "method"]
        print(f"Classes: {len(classes)}")
        for c in classes:
            print(f"  - {c.name} (lines {c.line_start}-{c.line_end})")
        print(f"Methods: {len(methods)}")

        print(f"\n--- FUNCTIONAL REQUIREMENTS ({len(result.functional_requirements)}) ---")
        for req in result.functional_requirements[:10]:
            print(f"  {req.id}: {req.title} [{req.category}]")
        if len(result.functional_requirements) > 10:
            print(f"  ... and {len(result.functional_requirements) - 10} more")

        print(f"\n--- BUSINESS RULES ({len(result.business_rules)}) ---")
        by_type = {}
        for r in result.business_rules:
            by_type.setdefault(r.rule_type, []).append(r)
        for rule_type, rules in by_type.items():
            print(f"  [{rule_type.upper()}] ({len(rules)} rules)")
            for r in rules[:3]:
                print(f"    {r.id}: {r.natural_language[:60]}...")
            if len(rules) > 3:
                print(f"    ... and {len(rules) - 3} more")

        print(f"\n--- NON-FUNCTIONAL REQUIREMENTS ({len(result.nfrs)}) ---")
        for nfr in result.nfrs:
            print(f"  {nfr.id}: [{nfr.category.value}] {nfr.description}")
            print(f"       Metric: {nfr.metric} = {nfr.target_value}")

        print("\n" + "=" * 70)

        # Assertions for test pass
        assert result.lines_of_code > 0


# ============================================================================
# CLI RUNNER
# ============================================================================

if __name__ == "__main__":
    """Run as standalone script for quick demo."""
    import sys

    # Try to find the invest_validator_service.py
    base_path = Path(__file__).parent.parent.parent.parent
    source_path = base_path / "app" / "services" / "invest_validator_service.py"

    if not source_path.exists():
        print(f"Error: {source_path} not found")
        sys.exit(1)

    print("=" * 70)
    print("REQUIREMENTS EXTRACTION DEMO")
    print(f"Source: {source_path}")
    print("=" * 70)

    result = run_extraction(str(source_path))

    print(f"\nExtracted from {result.lines_of_code} lines of code:")
    print(f"  - {len(result.symbols)} code symbols")
    print(f"  - {len(result.functional_requirements)} functional requirements")
    print(f"  - {len(result.business_rules)} business rules")
    print(f"  - {len(result.nfrs)} non-functional requirements")

    print("\n--- SAMPLE BUSINESS RULES ---")
    for rule in result.business_rules[:10]:
        print(f"  {rule.natural_language}")
