"""
MP-QW-6: Constrained Tests DSL Service

Create DSL that makes invalid tests impossible.
External DSL ensures test specifications are complete and valid.

Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- Parse YAML-based test specifications
- Validate completeness and correctness
- Generate test code for multiple languages
- Track coverage contribution

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
import logging
import yaml
import re

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of test rules."""
    GIVEN = "given"
    WHEN = "when"
    THEN = "then"
    AND = "and"
    BUT = "but"


class AssertionType(Enum):
    """Types of assertions."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    MATCHES = "matches"
    THROWS = "throws"
    DOES_NOT_THROW = "does_not_throw"


class ValidationErrorType(Enum):
    """Types of validation errors."""
    MISSING_GIVEN = "missing_given"
    MISSING_WHEN = "missing_when"
    MISSING_THEN = "missing_then"
    INVALID_ASSERTION = "invalid_assertion"
    INCOMPLETE_RULE = "incomplete_rule"
    DUPLICATE_TEST = "duplicate_test"
    INVALID_SUBJECT = "invalid_subject"
    SYNTAX_ERROR = "syntax_error"


@dataclass
class TestRule:
    """A single test rule (Given/When/Then)."""
    type: RuleType
    subject: str
    predicate: str
    expected: Any
    assertion_type: Optional[AssertionType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationError:
    """A validation error in a test specification."""
    error_type: ValidationErrorType
    message: str
    line: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validating a test specification."""
    valid: bool
    errors: List[ValidationError]
    warnings: List[str]
    coverage_contribution: float  # Estimated contribution to coverage
    complexity_score: int  # 1-10


@dataclass
class TestSpecification:
    """A complete test specification."""
    id: UUID
    name: str
    description: Optional[str]
    dsl_content: str
    parsed_rules: List[TestRule]
    validation_result: Optional[ValidationResult]
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedTest:
    """Generated test code."""
    spec_id: UUID
    language: str
    code: str
    framework: str  # pytest, jest, junit, etc.
    generated_at: datetime


@dataclass
class CoverageReport:
    """Coverage report for a set of specifications."""
    total_specs: int
    valid_specs: int
    total_rules: int
    given_count: int
    when_count: int
    then_count: int
    estimated_coverage: float
    gaps: List[str]


class ConstrainedTestsService:
    """
    Service for managing constrained test specifications.

    Uses a YAML-based DSL that makes invalid tests impossible
    by requiring complete Given/When/Then specifications.
    """

    def __init__(self):
        self._specifications: Dict[UUID, TestSpecification] = {}
        self._generated_tests: Dict[UUID, List[GeneratedTest]] = {}

    def parse_dsl(
        self,
        dsl_content: str,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> TestSpecification:
        """
        Parse a DSL test specification.

        Args:
            dsl_content: YAML DSL content
            name: Optional name (extracted from content if not provided)
            tags: Optional tags for categorization

        Returns:
            Parsed TestSpecification
        """
        now = datetime.now(timezone.utc)

        # Parse YAML
        try:
            parsed = yaml.safe_load(dsl_content)
        except yaml.YAMLError as e:
            # Create spec with parse error
            spec = TestSpecification(
                id=uuid4(),
                name=name or "Parse Error",
                description=None,
                dsl_content=dsl_content,
                parsed_rules=[],
                validation_result=ValidationResult(
                    valid=False,
                    errors=[ValidationError(
                        error_type=ValidationErrorType.SYNTAX_ERROR,
                        message=f"YAML parse error: {str(e)}",
                    )],
                    warnings=[],
                    coverage_contribution=0.0,
                    complexity_score=0,
                ),
                created_at=now,
                updated_at=now,
                tags=tags or [],
            )
            self._specifications[spec.id] = spec
            return spec

        # Extract test info
        test_name = name or parsed.get("test", parsed.get("name", "Unnamed Test"))
        description = parsed.get("description")

        # Parse rules
        rules = self._parse_rules(parsed)

        # Create specification
        spec = TestSpecification(
            id=uuid4(),
            name=test_name,
            description=description,
            dsl_content=dsl_content,
            parsed_rules=rules,
            validation_result=None,
            created_at=now,
            updated_at=now,
            tags=tags or parsed.get("tags", []),
            metadata=parsed.get("metadata", {}),
        )

        # Validate
        spec.validation_result = self._validate_specification(spec)

        self._specifications[spec.id] = spec
        logger.info(f"Parsed test specification '{test_name}' ({spec.id})")

        return spec

    def validate_specification(self, spec_id: UUID) -> ValidationResult:
        """Validate a test specification."""
        spec = self._specifications.get(spec_id)
        if not spec:
            raise ValueError(f"Specification {spec_id} not found")

        result = self._validate_specification(spec)
        spec.validation_result = result
        spec.updated_at = datetime.now(timezone.utc)

        return result

    def generate_test_code(
        self,
        spec_id: UUID,
        language: str,
        framework: Optional[str] = None
    ) -> GeneratedTest:
        """
        Generate test code from a specification.

        Args:
            spec_id: The specification ID
            language: Target language (python, javascript, java, etc.)
            framework: Testing framework (pytest, jest, junit, etc.)

        Returns:
            Generated test code
        """
        spec = self._specifications.get(spec_id)
        if not spec:
            raise ValueError(f"Specification {spec_id} not found")

        if spec.validation_result and not spec.validation_result.valid:
            raise ValueError("Cannot generate code for invalid specification")

        # Default frameworks per language
        default_frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "junit",
            "csharp": "nunit",
            "go": "testing",
        }
        framework = framework or default_frameworks.get(language.lower(), "unknown")

        # Generate code
        code = self._generate_code(spec, language.lower(), framework)

        generated = GeneratedTest(
            spec_id=spec_id,
            language=language,
            code=code,
            framework=framework,
            generated_at=datetime.now(timezone.utc),
        )

        if spec_id not in self._generated_tests:
            self._generated_tests[spec_id] = []
        self._generated_tests[spec_id].append(generated)

        logger.info(f"Generated {language}/{framework} test for spec {spec_id}")
        return generated

    def check_coverage_completeness(
        self,
        spec_ids: Optional[List[UUID]] = None
    ) -> CoverageReport:
        """
        Check coverage completeness for specifications.

        Args:
            spec_ids: Specific spec IDs to check, or all if None

        Returns:
            CoverageReport with analysis
        """
        if spec_ids:
            specs = [self._specifications[sid] for sid in spec_ids if sid in self._specifications]
        else:
            specs = list(self._specifications.values())

        valid_specs = [s for s in specs if s.validation_result and s.validation_result.valid]

        # Count rules
        all_rules = []
        for spec in valid_specs:
            all_rules.extend(spec.parsed_rules)

        given_count = sum(1 for r in all_rules if r.type == RuleType.GIVEN)
        when_count = sum(1 for r in all_rules if r.type == RuleType.WHEN)
        then_count = sum(1 for r in all_rules if r.type == RuleType.THEN)

        # Estimate coverage (simplified)
        estimated_coverage = min(100.0, len(valid_specs) * 5.0)

        # Identify gaps
        gaps = []
        if given_count < len(valid_specs):
            gaps.append("Some tests missing setup conditions (Given)")
        if when_count < len(valid_specs):
            gaps.append("Some tests missing action definitions (When)")
        if then_count < len(valid_specs):
            gaps.append("Some tests missing assertions (Then)")

        return CoverageReport(
            total_specs=len(specs),
            valid_specs=len(valid_specs),
            total_rules=len(all_rules),
            given_count=given_count,
            when_count=when_count,
            then_count=then_count,
            estimated_coverage=estimated_coverage,
            gaps=gaps,
        )

    def get_specification(self, spec_id: UUID) -> Optional[TestSpecification]:
        """Get a specification by ID."""
        return self._specifications.get(spec_id)

    def get_all_specifications(
        self,
        valid_only: bool = False,
        tag: Optional[str] = None
    ) -> List[TestSpecification]:
        """Get all specifications with optional filtering."""
        specs = list(self._specifications.values())

        if valid_only:
            specs = [s for s in specs if s.validation_result and s.validation_result.valid]

        if tag:
            specs = [s for s in specs if tag in s.tags]

        return sorted(specs, key=lambda s: s.created_at, reverse=True)

    def delete_specification(self, spec_id: UUID) -> bool:
        """Delete a specification."""
        if spec_id in self._specifications:
            del self._specifications[spec_id]
            if spec_id in self._generated_tests:
                del self._generated_tests[spec_id]
            return True
        return False

    def _parse_rules(self, parsed: Dict[str, Any]) -> List[TestRule]:
        """Parse rules from YAML content."""
        rules = []

        # Parse Given rules
        for given in parsed.get("given", []):
            if isinstance(given, str):
                rules.append(self._parse_rule_string(RuleType.GIVEN, given))
            elif isinstance(given, dict):
                for subject, predicate in given.items():
                    rules.append(TestRule(
                        type=RuleType.GIVEN,
                        subject=subject,
                        predicate=str(predicate),
                        expected=None,
                    ))

        # Parse When rules
        for when in parsed.get("when", []):
            if isinstance(when, str):
                rules.append(self._parse_rule_string(RuleType.WHEN, when))
            elif isinstance(when, dict):
                for action, details in when.items():
                    rules.append(TestRule(
                        type=RuleType.WHEN,
                        subject=action,
                        predicate=str(details) if details else action,
                        expected=None,
                    ))

        # Parse Then rules (assertions)
        for then in parsed.get("then", []):
            if isinstance(then, str):
                rules.append(self._parse_rule_string(RuleType.THEN, then))
            elif isinstance(then, dict):
                for subject, expected in then.items():
                    assertion_type = self._infer_assertion_type(subject, expected)
                    rules.append(TestRule(
                        type=RuleType.THEN,
                        subject=subject,
                        predicate="equals" if assertion_type == AssertionType.EQUALS else subject,
                        expected=expected,
                        assertion_type=assertion_type,
                    ))

        return rules

    def _parse_rule_string(self, rule_type: RuleType, text: str) -> TestRule:
        """Parse a rule from a string."""
        # Simple parsing - split on first ':'
        if ":" in text:
            subject, predicate = text.split(":", 1)
            return TestRule(
                type=rule_type,
                subject=subject.strip(),
                predicate=predicate.strip(),
                expected=None,
            )
        return TestRule(
            type=rule_type,
            subject=text,
            predicate=text,
            expected=None,
        )

    def _infer_assertion_type(self, subject: str, expected: Any) -> AssertionType:
        """Infer assertion type from subject and expected value."""
        subject_lower = subject.lower()

        if "error" in subject_lower or "exception" in subject_lower:
            return AssertionType.THROWS
        if expected is True:
            return AssertionType.IS_TRUE
        if expected is False:
            return AssertionType.IS_FALSE
        if expected is None:
            return AssertionType.IS_NULL
        if "contains" in subject_lower:
            return AssertionType.CONTAINS
        if "greater" in subject_lower:
            return AssertionType.GREATER_THAN
        if "less" in subject_lower:
            return AssertionType.LESS_THAN

        return AssertionType.EQUALS

    def _validate_specification(self, spec: TestSpecification) -> ValidationResult:
        """Validate a test specification."""
        errors = []
        warnings = []

        # Check for required rule types
        has_given = any(r.type == RuleType.GIVEN for r in spec.parsed_rules)
        has_when = any(r.type == RuleType.WHEN for r in spec.parsed_rules)
        has_then = any(r.type == RuleType.THEN for r in spec.parsed_rules)

        if not has_given:
            errors.append(ValidationError(
                error_type=ValidationErrorType.MISSING_GIVEN,
                message="Test specification must have at least one 'given' condition",
                suggestion="Add a 'given' section to set up the test preconditions",
            ))

        if not has_when:
            errors.append(ValidationError(
                error_type=ValidationErrorType.MISSING_WHEN,
                message="Test specification must have at least one 'when' action",
                suggestion="Add a 'when' section to define the action being tested",
            ))

        if not has_then:
            errors.append(ValidationError(
                error_type=ValidationErrorType.MISSING_THEN,
                message="Test specification must have at least one 'then' assertion",
                suggestion="Add a 'then' section with expected outcomes",
            ))

        # Check for incomplete rules
        for rule in spec.parsed_rules:
            if not rule.subject or rule.subject.strip() == "":
                errors.append(ValidationError(
                    error_type=ValidationErrorType.INCOMPLETE_RULE,
                    message=f"Rule of type '{rule.type.value}' has empty subject",
                ))

            if rule.type == RuleType.THEN and rule.expected is None and rule.assertion_type is None:
                warnings.append(f"Then rule '{rule.subject}' has no explicit expected value")

        # Calculate complexity
        complexity = min(10, len(spec.parsed_rules))

        # Estimate coverage contribution
        coverage = 0.0
        if not errors:
            # Base coverage per valid test
            coverage = 5.0
            # Bonus for multiple assertions
            then_count = sum(1 for r in spec.parsed_rules if r.type == RuleType.THEN)
            coverage += min(5.0, then_count * 1.0)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            coverage_contribution=coverage,
            complexity_score=complexity,
        )

    def _generate_code(self, spec: TestSpecification, language: str, framework: str) -> str:
        """Generate test code for a specification."""
        if language == "python" and framework == "pytest":
            return self._generate_pytest(spec)
        elif language in ("javascript", "typescript") and framework == "jest":
            return self._generate_jest(spec)
        elif language == "java" and framework == "junit":
            return self._generate_junit(spec)
        else:
            return self._generate_generic(spec, language)

    def _generate_pytest(self, spec: TestSpecification) -> str:
        """Generate pytest code."""
        lines = [
            f'"""Test: {spec.name}"""',
            "",
            "import pytest",
            "",
            "",
            f"def test_{self._to_snake_case(spec.name)}():",
        ]

        # Given
        lines.append("    # Given")
        for rule in spec.parsed_rules:
            if rule.type == RuleType.GIVEN:
                lines.append(f"    # {rule.subject}: {rule.predicate}")
                lines.append(f"    {self._to_snake_case(rule.subject)} = None  # TODO: Setup")

        lines.append("")

        # When
        lines.append("    # When")
        for rule in spec.parsed_rules:
            if rule.type == RuleType.WHEN:
                lines.append(f"    # {rule.subject}")
                lines.append(f"    result = None  # TODO: Execute {rule.predicate}")

        lines.append("")

        # Then
        lines.append("    # Then")
        for rule in spec.parsed_rules:
            if rule.type == RuleType.THEN:
                assertion = self._generate_pytest_assertion(rule)
                lines.append(f"    {assertion}")

        return "\n".join(lines)

    def _generate_pytest_assertion(self, rule: TestRule) -> str:
        """Generate a pytest assertion."""
        if rule.assertion_type == AssertionType.IS_TRUE:
            return f"assert {self._to_snake_case(rule.subject)} is True"
        elif rule.assertion_type == AssertionType.IS_FALSE:
            return f"assert {self._to_snake_case(rule.subject)} is False"
        elif rule.assertion_type == AssertionType.IS_NULL:
            return f"assert {self._to_snake_case(rule.subject)} is None"
        elif rule.assertion_type == AssertionType.CONTAINS:
            return f"assert {repr(rule.expected)} in {self._to_snake_case(rule.subject)}"
        elif rule.assertion_type == AssertionType.THROWS:
            return f"with pytest.raises(Exception):  # TODO: Specify exception"
        else:
            return f"assert {self._to_snake_case(rule.subject)} == {repr(rule.expected)}"

    def _generate_jest(self, spec: TestSpecification) -> str:
        """Generate Jest test code."""
        lines = [
            f"describe('{spec.name}', () => {{",
            f"  it('should {spec.name.lower()}', () => {{",
        ]

        # Given
        lines.append("    // Given")
        for rule in spec.parsed_rules:
            if rule.type == RuleType.GIVEN:
                lines.append(f"    // {rule.subject}: {rule.predicate}")
                lines.append(f"    const {self._to_camel_case(rule.subject)} = null; // TODO: Setup")

        lines.append("")

        # When
        lines.append("    // When")
        for rule in spec.parsed_rules:
            if rule.type == RuleType.WHEN:
                lines.append(f"    // {rule.subject}")
                lines.append(f"    const result = null; // TODO: Execute {rule.predicate}")

        lines.append("")

        # Then
        lines.append("    // Then")
        for rule in spec.parsed_rules:
            if rule.type == RuleType.THEN:
                assertion = self._generate_jest_assertion(rule)
                lines.append(f"    {assertion}")

        lines.append("  });")
        lines.append("});")

        return "\n".join(lines)

    def _generate_jest_assertion(self, rule: TestRule) -> str:
        """Generate a Jest assertion."""
        subject = self._to_camel_case(rule.subject)
        if rule.assertion_type == AssertionType.IS_TRUE:
            return f"expect({subject}).toBe(true);"
        elif rule.assertion_type == AssertionType.IS_FALSE:
            return f"expect({subject}).toBe(false);"
        elif rule.assertion_type == AssertionType.IS_NULL:
            return f"expect({subject}).toBeNull();"
        elif rule.assertion_type == AssertionType.CONTAINS:
            return f"expect({subject}).toContain({repr(rule.expected)});"
        elif rule.assertion_type == AssertionType.THROWS:
            return f"expect(() => {{ /* action */ }}).toThrow();"
        else:
            expected = "null" if rule.expected is None else repr(rule.expected)
            return f"expect({subject}).toBe({expected});"

    def _generate_junit(self, spec: TestSpecification) -> str:
        """Generate JUnit test code."""
        class_name = self._to_pascal_case(spec.name) + "Test"
        method_name = "test" + self._to_pascal_case(spec.name)

        lines = [
            "import org.junit.jupiter.api.Test;",
            "import static org.junit.jupiter.api.Assertions.*;",
            "",
            f"class {class_name} {{",
            "",
            "    @Test",
            f"    void {method_name}() {{",
        ]

        # Given
        lines.append("        // Given")
        for rule in spec.parsed_rules:
            if rule.type == RuleType.GIVEN:
                lines.append(f"        // {rule.subject}: {rule.predicate}")

        lines.append("")

        # When
        lines.append("        // When")
        for rule in spec.parsed_rules:
            if rule.type == RuleType.WHEN:
                lines.append(f"        // {rule.subject}")

        lines.append("")

        # Then
        lines.append("        // Then")
        for rule in spec.parsed_rules:
            if rule.type == RuleType.THEN:
                lines.append(f"        // TODO: Assert {rule.subject} == {rule.expected}")

        lines.append("    }")
        lines.append("}")

        return "\n".join(lines)

    def _generate_generic(self, spec: TestSpecification, language: str) -> str:
        """Generate generic test pseudocode."""
        lines = [
            f"// Test: {spec.name}",
            f"// Language: {language}",
            "",
            "// Given",
        ]

        for rule in spec.parsed_rules:
            if rule.type == RuleType.GIVEN:
                lines.append(f"//   {rule.subject}: {rule.predicate}")

        lines.append("")
        lines.append("// When")

        for rule in spec.parsed_rules:
            if rule.type == RuleType.WHEN:
                lines.append(f"//   {rule.subject}: {rule.predicate}")

        lines.append("")
        lines.append("// Then")

        for rule in spec.parsed_rules:
            if rule.type == RuleType.THEN:
                lines.append(f"//   Assert {rule.subject} == {rule.expected}")

        return "\n".join(lines)

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        # Remove special characters and convert to snake_case
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        text = re.sub(r'\s+', '_', text.strip())
        return text.lower()

    def _to_camel_case(self, text: str) -> str:
        """Convert text to camelCase."""
        words = re.sub(r'[^a-zA-Z0-9\s]', '', text).split()
        if not words:
            return "value"
        return words[0].lower() + ''.join(w.title() for w in words[1:])

    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase."""
        words = re.sub(r'[^a-zA-Z0-9\s]', '', text).split()
        return ''.join(w.title() for w in words) if words else "Test"
