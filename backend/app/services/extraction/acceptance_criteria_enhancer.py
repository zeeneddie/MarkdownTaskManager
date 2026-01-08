# Acceptance Criteria Enhancer - Week 102: Functional Requirements Quick Wins
# FR-QW-3: Convert plain text to Given/When/Then format

"""
Acceptance Criteria Enhancer

Transforms plain text acceptance criteria into structured Gherkin format:
- Given (preconditions/context)
- When (action/trigger)
- Then (expected outcome)

Also detects and extracts:
- Test data requirements
- Edge cases
- Negative scenarios
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple
import re


class ACType(Enum):
    """Type of acceptance criterion."""
    FUNCTIONAL = "functional"       # Feature behavior
    VALIDATION = "validation"       # Input validation
    AUTHORIZATION = "authorization" # Access control
    NAVIGATION = "navigation"       # UI navigation
    INTEGRATION = "integration"     # External system
    PERFORMANCE = "performance"     # Non-functional
    ERROR = "error"                 # Error handling
    DATA = "data"                   # Data operations


class ScenarioType(Enum):
    """Type of test scenario."""
    HAPPY_PATH = "happy_path"
    EDGE_CASE = "edge_case"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    ERROR_HANDLING = "error_handling"


@dataclass
class GherkinScenario:
    """A scenario in Given/When/Then format."""
    name: str
    given: List[str]  # Preconditions
    when: List[str]   # Actions
    then: List[str]   # Expected outcomes
    and_clauses: List[Tuple[str, str]] = field(default_factory=list)  # (type, clause)
    scenario_type: ScenarioType = ScenarioType.HAPPY_PATH
    tags: List[str] = field(default_factory=list)
    examples: Optional[Dict[str, List[str]]] = None  # For scenario outlines

    def to_gherkin(self) -> str:
        """Convert to Gherkin syntax string."""
        lines = []

        # Tags
        if self.tags:
            lines.append("  " + " ".join(f"@{tag}" for tag in self.tags))

        # Scenario name
        if self.examples:
            lines.append(f"  Scenario Outline: {self.name}")
        else:
            lines.append(f"  Scenario: {self.name}")

        # Given
        for i, g in enumerate(self.given):
            keyword = "Given" if i == 0 else "And"
            lines.append(f"    {keyword} {g}")

        # When
        for i, w in enumerate(self.when):
            keyword = "When" if i == 0 else "And"
            lines.append(f"    {keyword} {w}")

        # Then
        for i, t in enumerate(self.then):
            keyword = "Then" if i == 0 else "And"
            lines.append(f"    {keyword} {t}")

        # Examples table
        if self.examples:
            lines.append("")
            lines.append("    Examples:")
            headers = list(self.examples.keys())
            lines.append("      | " + " | ".join(headers) + " |")

            # Get number of rows from first column
            num_rows = len(list(self.examples.values())[0])
            for i in range(num_rows):
                row = [self.examples[h][i] for h in headers]
                lines.append("      | " + " | ".join(row) + " |")

        return "\n".join(lines)


@dataclass
class EnhancedAcceptanceCriteria:
    """Enhanced acceptance criteria with structured format."""
    original: str
    scenarios: List[GherkinScenario]
    ac_type: ACType
    test_data: List[str]
    edge_cases: List[str]
    confidence: float  # 0.0-1.0 confidence in transformation

    def to_gherkin_feature(self, feature_name: str = "Feature") -> str:
        """Convert all scenarios to a complete Gherkin feature file."""
        lines = [f"Feature: {feature_name}", ""]

        for scenario in self.scenarios:
            lines.append(scenario.to_gherkin())
            lines.append("")

        return "\n".join(lines)


@dataclass
class ACEnhancementResult:
    """Result of enhancing multiple acceptance criteria."""
    original_criteria: List[str]
    enhanced_criteria: List[EnhancedAcceptanceCriteria]
    feature_file: str
    statistics: Dict[str, int]
    suggestions: List[str]


class AcceptanceCriteriaEnhancer:
    """
    Transforms plain text acceptance criteria into Gherkin format.

    Capabilities:
    - Convert plain text to Given/When/Then
    - Detect AC type (functional, validation, etc.)
    - Generate edge cases and negative scenarios
    - Create scenario outlines with examples
    - Extract test data requirements

    Usage:
        enhancer = AcceptanceCriteriaEnhancer()

        plain_ac = "User can login with valid email and password"
        result = enhancer.enhance(plain_ac)
        print(result.scenarios[0].to_gherkin())

        # Or enhance multiple at once:
        criteria = ["Login works", "Password is validated"]
        bulk_result = enhancer.enhance_all(criteria, "Login Feature")
    """

    # Patterns for detecting Given/When/Then components
    GIVEN_PATTERNS = [
        r"(?i)^(given|assuming|provided|when)\s+(.+)",
        r"(?i)(user|customer|admin)\s+(is|has|was)\s+(.+)",
        r"(?i)(system|application|page)\s+(is|shows|displays)\s+(.+)",
        r"(?i)(there|we have)\s+(is|are|exist)\s+(.+)",
        r"(?i)^(with|having)\s+(.+)",
    ]

    WHEN_PATTERNS = [
        r"(?i)(user|customer|admin)\s+(clicks?|selects?|enters?|submits?|types?|chooses?)\s+(.+)",
        r"(?i)(when|if|after)\s+(.+)\s+(is|are)\s+(clicked|selected|submitted|entered)",
        r"(?i)(user|customer|admin)\s+(attempts?|tries?|wants?)\s+to\s+(.+)",
        r"(?i)(clicking|selecting|entering|submitting|typing)\s+(.+)",
        r"(?i)^(performs?|executes?|runs?|triggers?)\s+(.+)",
    ]

    THEN_PATTERNS = [
        r"(?i)(should|must|will|shall)\s+(be|have|show|display|return|redirect|receive)\s+(.+)",
        r"(?i)(system|application|page)\s+(displays?|shows?|returns?|redirects?)\s+(.+)",
        r"(?i)(user|customer)\s+(sees?|receives?|gets?|is\s+shown)\s+(.+)",
        r"(?i)(error|message|notification|alert)\s+(is\s+)?(displayed|shown|appears?)",
        r"(?i)^(verify|ensure|confirm|check)\s+(that\s+)?(.+)",
    ]

    # AC Type detection patterns
    AC_TYPE_PATTERNS = {
        ACType.VALIDATION: [
            r"(?i)(valid|invalid|required|format|pattern|length|range)",
            r"(?i)(email|phone|password|input)\s+(must|should|is)\s+(valid|validated)",
            r"(?i)(minimum|maximum|at\s+least|at\s+most|between)",
        ],
        ACType.AUTHORIZATION: [
            r"(?i)(only|restricted|allowed|permitted|authorized)",
            r"(?i)(admin|role|permission|access|deny|forbid)",
            r"(?i)(logged\s+in|authenticated|authorized)\s+user",
        ],
        ACType.NAVIGATION: [
            r"(?i)(navigate|redirect|route|go\s+to|open|close)",
            r"(?i)(page|screen|view|modal|dialog)",
            r"(?i)(click|tap|press)\s+.+\s+(button|link|tab)",
        ],
        ACType.INTEGRATION: [
            r"(?i)(api|service|endpoint|webhook|external)",
            r"(?i)(third.?party|integration|connect)",
            r"(?i)(send|receive|sync|fetch)\s+.+\s+(data|request|response)",
        ],
        ACType.PERFORMANCE: [
            r"(?i)(within|under|less\s+than)\s+\d+\s*(ms|seconds?|minutes?)",
            r"(?i)(fast|quick|responsive|performance)",
            r"(?i)(load|response)\s+time",
        ],
        ACType.ERROR: [
            r"(?i)(error|exception|failure|fail|invalid)",
            r"(?i)(handle|catch|graceful)",
            r"(?i)(try|attempt)\s+.+\s+(fail|invalid|wrong)",
        ],
        ACType.DATA: [
            r"(?i)(save|store|persist|create|update|delete|read)",
            r"(?i)(database|record|entry|row)",
            r"(?i)(data|information)\s+(is\s+)?(saved|stored|persisted)",
        ],
    }

    # Edge case patterns
    EDGE_CASE_TRIGGERS = {
        "empty": ["empty", "blank", "null", "none", "missing"],
        "boundary": ["minimum", "maximum", "limit", "boundary", "edge"],
        "special_chars": ["special character", "unicode", "emoji", "symbol"],
        "whitespace": ["space", "whitespace", "tab", "newline"],
        "duplicate": ["duplicate", "existing", "already", "same"],
        "concurrent": ["simultaneous", "concurrent", "parallel", "multiple"],
    }

    def __init__(self, generate_edge_cases: bool = True, generate_negatives: bool = True):
        """
        Initialize the enhancer.

        Args:
            generate_edge_cases: Auto-generate edge case scenarios
            generate_negatives: Auto-generate negative scenarios
        """
        self.generate_edge_cases = generate_edge_cases
        self.generate_negatives = generate_negatives

    def enhance(self, plain_ac: str) -> EnhancedAcceptanceCriteria:
        """
        Enhance a single acceptance criterion.

        Args:
            plain_ac: Plain text acceptance criterion

        Returns:
            EnhancedAcceptanceCriteria with Gherkin scenarios
        """
        # Detect AC type
        ac_type = self._detect_ac_type(plain_ac)

        # Parse into GWT components
        given, when, then = self._parse_gwt_components(plain_ac)

        # Create main scenario
        main_scenario = self._create_scenario(
            name=self._generate_scenario_name(plain_ac),
            given=given,
            when=when,
            then=then,
            scenario_type=ScenarioType.HAPPY_PATH
        )

        scenarios = [main_scenario]
        edge_cases = []
        test_data = []

        # Generate edge cases if enabled
        if self.generate_edge_cases:
            edge_scenarios, detected_edges = self._generate_edge_cases(plain_ac, given, when, then)
            scenarios.extend(edge_scenarios)
            edge_cases.extend(detected_edges)

        # Generate negative scenarios if enabled
        if self.generate_negatives:
            negative_scenarios = self._generate_negative_scenarios(plain_ac, ac_type, given, when, then)
            scenarios.extend(negative_scenarios)

        # Extract test data requirements
        test_data = self._extract_test_data_requirements(plain_ac, ac_type)

        # Calculate confidence based on how well we parsed
        confidence = self._calculate_confidence(plain_ac, given, when, then)

        return EnhancedAcceptanceCriteria(
            original=plain_ac,
            scenarios=scenarios,
            ac_type=ac_type,
            test_data=test_data,
            edge_cases=edge_cases,
            confidence=confidence
        )

    def enhance_all(
        self,
        criteria: List[str],
        feature_name: str = "Feature"
    ) -> ACEnhancementResult:
        """
        Enhance multiple acceptance criteria.

        Args:
            criteria: List of plain text acceptance criteria
            feature_name: Name for the generated feature file

        Returns:
            ACEnhancementResult with all enhanced criteria and feature file
        """
        enhanced = [self.enhance(ac) for ac in criteria]

        # Combine all scenarios into one feature file
        all_scenarios = []
        for eac in enhanced:
            all_scenarios.extend(eac.scenarios)

        # Generate feature file
        feature_lines = [f"Feature: {feature_name}", ""]
        for scenario in all_scenarios:
            feature_lines.append(scenario.to_gherkin())
            feature_lines.append("")

        feature_file = "\n".join(feature_lines)

        # Calculate statistics
        statistics = {
            "total_criteria": len(criteria),
            "total_scenarios": len(all_scenarios),
            "happy_path": sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.HAPPY_PATH),
            "edge_cases": sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.EDGE_CASE),
            "negative": sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.NEGATIVE),
            "avg_confidence": sum(e.confidence for e in enhanced) / len(enhanced) if enhanced else 0
        }

        # Generate suggestions
        suggestions = self._generate_suggestions(enhanced)

        return ACEnhancementResult(
            original_criteria=criteria,
            enhanced_criteria=enhanced,
            feature_file=feature_file,
            statistics=statistics,
            suggestions=suggestions
        )

    def _detect_ac_type(self, text: str) -> ACType:
        """Detect the type of acceptance criterion."""
        text_lower = text.lower()

        # Score each type
        type_scores = {}
        for ac_type, patterns in self.AC_TYPE_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, text_lower))
            if score > 0:
                type_scores[ac_type] = score

        if type_scores:
            return max(type_scores.keys(), key=lambda k: type_scores[k])

        return ACType.FUNCTIONAL

    def _parse_gwt_components(self, text: str) -> Tuple[List[str], List[str], List[str]]:
        """Parse Given/When/Then components from plain text."""
        given = []
        when = []
        then = []

        # Check if already in GWT format
        gwt_match = re.search(
            r"(?i)given\s+(.+?)\s+when\s+(.+?)\s+then\s+(.+)",
            text,
            re.DOTALL
        )
        if gwt_match:
            given.append(gwt_match.group(1).strip())
            when.append(gwt_match.group(2).strip())
            then.append(gwt_match.group(3).strip())
            return given, when, then

        # Try to extract components using patterns
        text_lower = text.lower()

        # Extract Given (context/preconditions)
        given = self._extract_preconditions(text)

        # Extract When (actions)
        when = self._extract_actions(text)

        # Extract Then (outcomes)
        then = self._extract_outcomes(text)

        # If we couldn't parse, create reasonable defaults
        if not given:
            given = [self._infer_precondition(text)]
        if not when:
            when = [self._infer_action(text)]
        if not then:
            then = [self._infer_outcome(text)]

        return given, when, then

    def _extract_preconditions(self, text: str) -> List[str]:
        """Extract preconditions from text."""
        preconditions = []

        # Look for explicit precondition patterns
        patterns = [
            r"(?i)(?:given|assuming|provided)\s+(.+?)(?:\s+when|\s+then|$)",
            r"(?i)(?:user|customer|admin)\s+(?:is|has|was)\s+(.+?)(?:\s+and\s+|,|$)",
            r"(?i)(?:system|application|page)\s+(?:is|shows|displays)\s+(.+?)(?:\s+and\s+|,|$)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            preconditions.extend([m.strip() for m in matches if m.strip()])

        return preconditions[:3]  # Limit to 3

    def _extract_actions(self, text: str) -> List[str]:
        """Extract actions from text."""
        actions = []

        patterns = [
            r"(?i)(?:user|customer|admin)\s+(clicks?|selects?|enters?|submits?|types?|chooses?|fills?)\s+(.+?)(?:\s+and\s+|,|\.|$)",
            r"(?i)(?:when)\s+(.+?)(?:\s+then|$)",
            r"(?i)(clicks?|selects?|enters?|submits?)\s+(?:the\s+)?(.+?)(?:\s+button|\s+link|\s+field)?(?:\s+and\s+|,|\.|$)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    action = " ".join(m.strip() for m in match if m.strip())
                else:
                    action = match.strip()
                if action:
                    actions.append(action)

        return actions[:3]

    def _extract_outcomes(self, text: str) -> List[str]:
        """Extract expected outcomes from text."""
        outcomes = []

        patterns = [
            r"(?i)(?:should|must|will|shall)\s+(.+?)(?:\s+and\s+|,|\.|$)",
            r"(?i)(?:then)\s+(.+?)(?:\s+and\s+|$)",
            r"(?i)(?:system|application|page)\s+(?:displays?|shows?|returns?)\s+(.+?)(?:\s+and\s+|,|\.|$)",
            r"(?i)(?:user|customer)\s+(?:sees?|receives?|gets?)\s+(.+?)(?:\s+and\s+|,|\.|$)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            outcomes.extend([m.strip() for m in matches if m.strip()])

        return outcomes[:3]

    def _infer_precondition(self, text: str) -> str:
        """Infer a reasonable precondition from text."""
        text_lower = text.lower()

        if any(word in text_lower for word in ["login", "authentication", "session"]):
            return "the user is on the login page"
        if any(word in text_lower for word in ["register", "signup", "create account"]):
            return "the user is on the registration page"
        if any(word in text_lower for word in ["edit", "update", "modify"]):
            return "the user has existing data to modify"
        if any(word in text_lower for word in ["delete", "remove"]):
            return "there is existing data to delete"
        if any(word in text_lower for word in ["search", "find", "filter"]):
            return "there is data available to search"
        if any(word in text_lower for word in ["admin", "administrator"]):
            return "the user is logged in as an administrator"

        return "the user is on the application"

    def _infer_action(self, text: str) -> str:
        """Infer the main action from text."""
        text_lower = text.lower()

        # Try to extract verb + object
        action_match = re.search(
            r"(?i)(can|able to|should be able to)\s+(\w+)\s+(.+?)(?:\s+with|\s+using|\s+by|$)",
            text
        )
        if action_match:
            return f"{action_match.group(2)} {action_match.group(3).strip()}"

        # Try simple verb extraction
        verb_match = re.search(
            r"(?i)(login|register|submit|create|update|delete|search|view|select|click|enter)\s*(.+?)(?:\s+and|\s+then|,|\.|$)",
            text
        )
        if verb_match:
            return f"the user {verb_match.group(1)}s {verb_match.group(2).strip()}"

        # Default: rephrase the entire AC as an action
        return f"the user performs the action"

    def _infer_outcome(self, text: str) -> str:
        """Infer the expected outcome from text."""
        text_lower = text.lower()

        # Try to find should/must patterns
        outcome_match = re.search(
            r"(?i)(should|must|will|shall)\s+(.+?)$",
            text
        )
        if outcome_match:
            return f"the system {outcome_match.group(2).strip()}"

        # Common outcome types
        if any(word in text_lower for word in ["error", "invalid", "fail"]):
            return "an appropriate error message is displayed"
        if any(word in text_lower for word in ["success", "confirm", "complete"]):
            return "a success message is displayed"
        if any(word in text_lower for word in ["redirect", "navigate"]):
            return "the user is redirected to the appropriate page"
        if any(word in text_lower for word in ["save", "store", "create"]):
            return "the data is saved successfully"

        return "the expected result is achieved"

    def _create_scenario(
        self,
        name: str,
        given: List[str],
        when: List[str],
        then: List[str],
        scenario_type: ScenarioType = ScenarioType.HAPPY_PATH,
        tags: Optional[List[str]] = None
    ) -> GherkinScenario:
        """Create a Gherkin scenario."""
        # Clean up components
        given = [self._clean_clause(g) for g in given]
        when = [self._clean_clause(w) for w in when]
        then = [self._clean_clause(t) for t in then]

        # Determine tags based on scenario type
        auto_tags = tags or []
        if scenario_type == ScenarioType.HAPPY_PATH:
            auto_tags.append("happy-path")
        elif scenario_type == ScenarioType.EDGE_CASE:
            auto_tags.append("edge-case")
        elif scenario_type == ScenarioType.NEGATIVE:
            auto_tags.append("negative")
        elif scenario_type == ScenarioType.BOUNDARY:
            auto_tags.append("boundary")

        return GherkinScenario(
            name=name,
            given=given,
            when=when,
            then=then,
            scenario_type=scenario_type,
            tags=auto_tags
        )

    def _clean_clause(self, clause: str) -> str:
        """Clean a Given/When/Then clause."""
        # Remove leading Given/When/Then keywords
        clause = re.sub(r"^(?i)(given|when|then|and|but)\s+", "", clause)
        # Capitalize first letter
        if clause:
            clause = clause[0].upper() + clause[1:] if len(clause) > 1 else clause.upper()
        return clause.strip()

    def _generate_scenario_name(self, text: str) -> str:
        """Generate a scenario name from AC text."""
        # Try to extract key action
        verb_match = re.search(
            r"(?i)(login|register|submit|create|update|delete|search|view|select|validate|verify|can)\s+(\w+(?:\s+\w+)?)",
            text
        )
        if verb_match:
            verb = verb_match.group(1).capitalize()
            obj = verb_match.group(2).strip()
            return f"{verb} {obj} successfully"

        # Truncate and clean
        name = text[:50].strip()
        if len(text) > 50:
            name += "..."
        return name

    def _generate_edge_cases(
        self,
        text: str,
        given: List[str],
        when: List[str],
        then: List[str]
    ) -> Tuple[List[GherkinScenario], List[str]]:
        """Generate edge case scenarios."""
        scenarios = []
        detected_edges = []
        text_lower = text.lower()

        # Check for input-related patterns
        if any(word in text_lower for word in ["enter", "input", "type", "fill"]):
            # Empty input edge case
            scenarios.append(self._create_scenario(
                name="Handle empty input",
                given=given.copy(),
                when=["the user submits without entering any data"],
                then=["an appropriate validation message is displayed"],
                scenario_type=ScenarioType.EDGE_CASE
            ))
            detected_edges.append("empty input")

            # Whitespace-only input
            scenarios.append(self._create_scenario(
                name="Handle whitespace-only input",
                given=given.copy(),
                when=["the user enters only whitespace characters"],
                then=["the input is trimmed and validated"],
                scenario_type=ScenarioType.EDGE_CASE
            ))
            detected_edges.append("whitespace input")

        # Check for numeric patterns
        if re.search(r"(?i)(amount|quantity|number|count|age|price)", text):
            # Zero value
            scenarios.append(self._create_scenario(
                name="Handle zero value",
                given=given.copy(),
                when=["the user enters 0 as the value"],
                then=["the system handles zero appropriately"],
                scenario_type=ScenarioType.BOUNDARY
            ))
            detected_edges.append("zero value")

            # Negative value
            scenarios.append(self._create_scenario(
                name="Handle negative value",
                given=given.copy(),
                when=["the user enters a negative value"],
                then=["appropriate validation is applied"],
                scenario_type=ScenarioType.BOUNDARY
            ))
            detected_edges.append("negative value")

        # Check for list/collection patterns
        if any(word in text_lower for word in ["list", "items", "results", "records"]):
            # Empty list
            scenarios.append(self._create_scenario(
                name="Handle empty list",
                given=["there are no items in the system"],
                when=when.copy(),
                then=["an empty state message is displayed"],
                scenario_type=ScenarioType.EDGE_CASE
            ))
            detected_edges.append("empty list")

        return scenarios, detected_edges

    def _generate_negative_scenarios(
        self,
        text: str,
        ac_type: ACType,
        given: List[str],
        when: List[str],
        then: List[str]
    ) -> List[GherkinScenario]:
        """Generate negative test scenarios."""
        scenarios = []
        text_lower = text.lower()

        # Validation-related negatives
        if ac_type == ACType.VALIDATION or "valid" in text_lower:
            scenarios.append(self._create_scenario(
                name="Reject invalid input format",
                given=given.copy(),
                when=["the user enters data in an invalid format"],
                then=["a validation error is displayed", "the form is not submitted"],
                scenario_type=ScenarioType.NEGATIVE
            ))

        # Authorization-related negatives
        if ac_type == ACType.AUTHORIZATION or any(w in text_lower for w in ["admin", "role", "permission"]):
            scenarios.append(self._create_scenario(
                name="Deny access to unauthorized users",
                given=["the user does not have required permissions"],
                when=when.copy(),
                then=["access is denied", "an authorization error is displayed"],
                scenario_type=ScenarioType.NEGATIVE
            ))

        # Login/authentication negatives
        if any(word in text_lower for word in ["login", "password", "credential"]):
            scenarios.append(self._create_scenario(
                name="Reject invalid credentials",
                given=["the user is on the login page"],
                when=["the user enters invalid credentials", "the user clicks submit"],
                then=["login is rejected", "an error message is displayed"],
                scenario_type=ScenarioType.NEGATIVE
            ))

        # Data operation negatives
        if ac_type == ACType.DATA or any(w in text_lower for w in ["save", "create", "update"]):
            scenarios.append(self._create_scenario(
                name="Handle duplicate data gracefully",
                given=["similar data already exists in the system"],
                when=when.copy(),
                then=["an appropriate duplicate warning is shown"],
                scenario_type=ScenarioType.NEGATIVE
            ))

        return scenarios

    def _extract_test_data_requirements(self, text: str, ac_type: ACType) -> List[str]:
        """Extract test data requirements from AC."""
        requirements = []
        text_lower = text.lower()

        # Email patterns
        if "email" in text_lower:
            requirements.append("Valid email addresses (e.g., user@example.com)")
            requirements.append("Invalid email formats for negative tests")

        # Password patterns
        if "password" in text_lower:
            requirements.append("Valid passwords meeting requirements")
            requirements.append("Weak/invalid passwords for negative tests")

        # User data patterns
        if any(w in text_lower for w in ["user", "customer", "account"]):
            requirements.append("Test user accounts with various roles")

        # Numeric data
        if re.search(r"(?i)(amount|quantity|number|price|age)", text):
            requirements.append("Numeric test data: positive, zero, negative, boundary values")

        # Date patterns
        if any(w in text_lower for w in ["date", "time", "schedule"]):
            requirements.append("Date test data: past, present, future, edge dates")

        # Based on AC type
        if ac_type == ACType.AUTHORIZATION:
            requirements.append("Users with different permission levels")
        if ac_type == ACType.PERFORMANCE:
            requirements.append("Large dataset for performance testing")

        return requirements

    def _calculate_confidence(
        self,
        original: str,
        given: List[str],
        when: List[str],
        then: List[str]
    ) -> float:
        """Calculate confidence in the transformation."""
        confidence = 0.5  # Start neutral

        # Was already in GWT format
        if re.search(r"(?i)given\s+.+\s+when\s+.+\s+then\s+.+", original):
            confidence = 0.95

        # Good extraction indicators
        if given and given[0] != "the user is on the application":
            confidence += 0.15
        if when and "performs the action" not in when[0]:
            confidence += 0.15
        if then and "expected result is achieved" not in then[0]:
            confidence += 0.15

        # Length of original affects confidence
        word_count = len(original.split())
        if word_count >= 10:
            confidence += 0.1
        elif word_count < 5:
            confidence -= 0.1

        return min(1.0, max(0.0, confidence))

    def _generate_suggestions(self, enhanced: List[EnhancedAcceptanceCriteria]) -> List[str]:
        """Generate suggestions for improving AC quality."""
        suggestions = []

        # Low confidence items
        low_conf = [e for e in enhanced if e.confidence < 0.6]
        if low_conf:
            suggestions.append(
                f"{len(low_conf)} acceptance criteria may need manual review (low transformation confidence)"
            )

        # Missing edge cases
        no_edges = [e for e in enhanced if not e.edge_cases]
        if len(no_edges) > len(enhanced) // 2:
            suggestions.append(
                "Consider adding explicit edge case acceptance criteria"
            )

        # Check for common missing scenarios
        all_types = [e.ac_type for e in enhanced]
        if ACType.ERROR not in all_types:
            suggestions.append(
                "No error handling acceptance criteria detected - consider adding error scenarios"
            )
        if ACType.VALIDATION not in all_types and len(enhanced) > 3:
            suggestions.append(
                "No validation acceptance criteria detected - consider adding input validation"
            )

        return suggestions


# Convenience functions
def enhance_ac(plain_ac: str) -> EnhancedAcceptanceCriteria:
    """
    Enhance a single acceptance criterion.

    Args:
        plain_ac: Plain text acceptance criterion

    Returns:
        EnhancedAcceptanceCriteria with Gherkin scenarios
    """
    enhancer = AcceptanceCriteriaEnhancer()
    return enhancer.enhance(plain_ac)


def to_gherkin(plain_ac: str) -> str:
    """
    Convert plain AC to Gherkin format.

    Args:
        plain_ac: Plain text acceptance criterion

    Returns:
        Gherkin scenario string
    """
    result = enhance_ac(plain_ac)
    return result.scenarios[0].to_gherkin() if result.scenarios else ""


def generate_feature_file(criteria: List[str], feature_name: str) -> str:
    """
    Generate a complete Gherkin feature file from acceptance criteria.

    Args:
        criteria: List of plain text acceptance criteria
        feature_name: Name for the feature

    Returns:
        Complete Gherkin feature file content
    """
    enhancer = AcceptanceCriteriaEnhancer()
    result = enhancer.enhance_all(criteria, feature_name)
    return result.feature_file
