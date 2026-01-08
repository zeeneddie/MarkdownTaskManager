"""
Anti-Pattern Quality Gates

Week 110 - Anti-Pattern detectors (AP-1 to AP-9).

Based on Gregor Riegler's Augmented Coding Pattern Language:
- AP-1: Overspecification
- AP-2: Premature Genericization
- AP-3: Over-Configuration
- AP-4: Gold-plating
- AP-5: Not-Invented-Here
- AP-6: Feature Creep
- AP-7: Analysis Paralysis
- AP-8: Scope Creep
- AP-9: Perfect is the Enemy of Good

Example usage:
    detector = AntiPatternDetector()

    # Analyze code/spec for anti-patterns
    results = detector.analyze(
        content=spec_content,
        content_type="specification",
        context={"task": "user authentication"}
    )

    # Check specific anti-pattern
    if results.has_pattern("overspecification"):
        print("Warning: specification is too detailed for this phase")

    # Get quality gate result
    gate_result = detector.check_quality_gate(results, threshold=0.7)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Pattern, Tuple
from pathlib import Path
import json
import re
import uuid


class AntiPatternType(Enum):
    """Types of anti-patterns."""
    OVERSPECIFICATION = "overspecification"          # AP-1
    PREMATURE_GENERICIZATION = "premature_genericization"  # AP-2
    OVER_CONFIGURATION = "over_configuration"        # AP-3
    GOLD_PLATING = "gold_plating"                    # AP-4
    NOT_INVENTED_HERE = "not_invented_here"          # AP-5
    FEATURE_CREEP = "feature_creep"                  # AP-6
    ANALYSIS_PARALYSIS = "analysis_paralysis"        # AP-7
    SCOPE_CREEP = "scope_creep"                      # AP-8
    PERFECTIONISM = "perfectionism"                  # AP-9


class SeverityLevel(Enum):
    """Severity of detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContentType(Enum):
    """Type of content being analyzed."""
    SPECIFICATION = "specification"
    CODE = "code"
    DESIGN = "design"
    CONVERSATION = "conversation"
    COMMIT = "commit"
    REVIEW = "review"


@dataclass
class PatternIndicator:
    """An indicator of an anti-pattern."""
    pattern_type: AntiPatternType
    indicator_name: str
    description: str
    location: Optional[str] = None
    line_number: Optional[int] = None
    matched_text: Optional[str] = None
    confidence: float = 0.5
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "indicator_name": self.indicator_name,
            "description": self.description,
            "location": self.location,
            "line_number": self.line_number,
            "matched_text": self.matched_text[:100] if self.matched_text else None,
            "confidence": self.confidence,
            "suggestions": self.suggestions
        }


@dataclass
class PatternDetectionResult:
    """Result of detecting a specific anti-pattern."""
    pattern_type: AntiPatternType
    detected: bool
    severity: SeverityLevel
    confidence: float
    indicators: List[PatternIndicator]
    total_score: float
    threshold: float
    remediation: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "detected": self.detected,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "indicators": [i.to_dict() for i in self.indicators],
            "total_score": self.total_score,
            "threshold": self.threshold,
            "remediation": self.remediation
        }


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    id: str
    content_type: ContentType
    analyzed_at: datetime
    content_length: int
    patterns_detected: List[PatternDetectionResult]
    overall_health: float  # 0-1, higher is better
    quality_gate_passed: bool
    context: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_pattern(self, pattern_name: str) -> bool:
        """Check if a specific pattern was detected."""
        for p in self.patterns_detected:
            if p.pattern_type.value == pattern_name and p.detected:
                return True
        return False

    def get_pattern(self, pattern_name: str) -> Optional[PatternDetectionResult]:
        """Get detection result for a specific pattern."""
        for p in self.patterns_detected:
            if p.pattern_type.value == pattern_name:
                return p
        return None

    def get_critical_patterns(self) -> List[PatternDetectionResult]:
        """Get patterns with critical severity."""
        return [p for p in self.patterns_detected if p.detected and p.severity == SeverityLevel.CRITICAL]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content_type": self.content_type.value,
            "analyzed_at": self.analyzed_at.isoformat(),
            "content_length": self.content_length,
            "patterns_detected": [p.to_dict() for p in self.patterns_detected],
            "overall_health": self.overall_health,
            "quality_gate_passed": self.quality_gate_passed,
            "context": self.context,
            "metadata": self.metadata
        }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        status = "" if self.quality_gate_passed else ""
        health_pct = int(self.overall_health * 100)

        lines = [
            f"# Anti-Pattern Analysis Report {status}",
            "",
            f"**Content Type**: {self.content_type.value}",
            f"**Analyzed**: {self.analyzed_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Health Score**: {health_pct}%",
            f"**Quality Gate**: {'Passed' if self.quality_gate_passed else 'Failed'}",
            "",
            "## Patterns Detected",
            ""
        ]

        detected = [p for p in self.patterns_detected if p.detected]
        if detected:
            for pattern in detected:
                severity_icon = {
                    SeverityLevel.LOW: "",
                    SeverityLevel.MEDIUM: "",
                    SeverityLevel.HIGH: "",
                    SeverityLevel.CRITICAL: ""
                }.get(pattern.severity, "")

                lines.append(f"### {severity_icon} {pattern.pattern_type.value.replace('_', ' ').title()}")
                lines.append(f"**Confidence**: {int(pattern.confidence * 100)}%")
                lines.append(f"**Severity**: {pattern.severity.value}")
                lines.append("")

                if pattern.indicators:
                    lines.append("**Indicators**:")
                    for ind in pattern.indicators[:5]:
                        lines.append(f"- {ind.description}")
                    lines.append("")

                if pattern.remediation:
                    lines.append("**Remediation**:")
                    for rem in pattern.remediation:
                        lines.append(f"- {rem}")
                    lines.append("")
        else:
            lines.append("*No anti-patterns detected*")
            lines.append("")

        return "\n".join(lines)


class PatternDetectorBase:
    """Base class for pattern detectors."""

    pattern_type: AntiPatternType
    description: str
    default_threshold: float = 0.5

    def __init__(self):
        self.indicators: List[PatternIndicator] = []

    def detect(
        self,
        content: str,
        content_type: ContentType,
        context: Dict[str, Any]
    ) -> PatternDetectionResult:
        """Detect the anti-pattern in content."""
        raise NotImplementedError

    def _calculate_severity(self, score: float) -> SeverityLevel:
        """Calculate severity based on score."""
        if score >= 0.8:
            return SeverityLevel.CRITICAL
        elif score >= 0.6:
            return SeverityLevel.HIGH
        elif score >= 0.4:
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW


class OverspecificationDetector(PatternDetectorBase):
    """
    AP-1: Overspecification Detector

    Detects when specifications are too detailed for the current phase,
    including implementation details that should be decided later.
    """

    pattern_type = AntiPatternType.OVERSPECIFICATION
    description = "Specifications that include unnecessary implementation details"
    default_threshold = 0.4

    # Patterns that indicate over-specification
    IMPL_DETAIL_PATTERNS = [
        (r"(specific|exact)\s+(implementation|algorithm)", "Exact implementation specified"),
        (r"database\s+(schema|table|column)\s+names?", "Database schema details"),
        (r"(class|method|function)\s+names?\s+(should|must)\s+be", "Prescriptive naming"),
        (r"(using|use)\s+(specific|exactly)\s+\d+", "Specific numbers prescribed"),
        (r"(file|folder|directory)\s+structure", "File structure prescribed"),
        (r"(variable|field)\s+type\s+(must|should)\s+be", "Type specification"),
        (r"(milliseconds?|seconds?|bytes?|kb|mb)\s+(exactly|precisely)", "Precise measurements"),
        (r"line\s+\d+|column\s+\d+", "Line/column references"),
        (r"version\s+\d+\.\d+\.\d+", "Specific version numbers"),
    ]

    # Patterns indicating appropriate level of detail
    APPROPRIATE_PATTERNS = [
        r"should\s+(be\s+able\s+to|support|allow)",
        r"user\s+(can|should|wants)",
        r"system\s+(must|shall)\s+(provide|ensure)",
        r"(requirement|goal|objective)",
    ]

    def detect(
        self,
        content: str,
        content_type: ContentType,
        context: Dict[str, Any]
    ) -> PatternDetectionResult:
        indicators = []
        total_score = 0

        content_lower = content.lower()

        # Check for implementation detail patterns
        for pattern, description in self.IMPL_DETAIL_PATTERNS:
            matches = re.findall(pattern, content_lower)
            if matches:
                for match in matches[:3]:  # Limit to 3 examples
                    indicators.append(PatternIndicator(
                        pattern_type=self.pattern_type,
                        indicator_name="implementation_detail",
                        description=description,
                        matched_text=match if isinstance(match, str) else str(match),
                        confidence=0.7,
                        suggestions=["Remove implementation details", "Focus on what, not how"]
                    ))
                total_score += 0.15 * len(matches)

        # Check specification length vs requirements count
        lines = content.split('\n')
        requirement_keywords = sum(1 for line in lines if re.search(r'(must|shall|should|will)', line.lower()))
        if len(lines) > 100 and requirement_keywords < len(lines) * 0.1:
            indicators.append(PatternIndicator(
                pattern_type=self.pattern_type,
                indicator_name="low_requirement_density",
                description=f"Low requirement density: {requirement_keywords} requirements in {len(lines)} lines",
                confidence=0.6,
                suggestions=["Focus on actual requirements", "Remove explanatory text"]
            ))
            total_score += 0.2

        # Check for code snippets in specs
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        if content_type == ContentType.SPECIFICATION and len(code_blocks) > 2:
            indicators.append(PatternIndicator(
                pattern_type=self.pattern_type,
                indicator_name="code_in_spec",
                description=f"Found {len(code_blocks)} code blocks in specification",
                confidence=0.8,
                suggestions=["Move code examples to appendix", "Keep specs technology-agnostic"]
            ))
            total_score += 0.1 * len(code_blocks)

        total_score = min(total_score, 1.0)
        detected = total_score >= self.default_threshold

        return PatternDetectionResult(
            pattern_type=self.pattern_type,
            detected=detected,
            severity=self._calculate_severity(total_score),
            confidence=total_score,
            indicators=indicators,
            total_score=total_score,
            threshold=self.default_threshold,
            remediation=[
                "Focus on WHAT the system should do, not HOW",
                "Use declarative language instead of imperative",
                "Leave implementation decisions to developers",
                "Separate technical design from requirements"
            ] if detected else []
        )


class PrematureGenericizationDetector(PatternDetectorBase):
    """
    AP-2: Premature Genericization Detector

    Detects when code/design is made overly generic without current need.
    """

    pattern_type = AntiPatternType.PREMATURE_GENERICIZATION
    description = "Making code generic before the need is proven"
    default_threshold = 0.45

    GENERIC_PATTERNS = [
        (r"abstract\s+(factory|builder|handler|processor)", "Abstract pattern without concrete need"),
        (r"generic[<\[].*[>\]]", "Generic type parameters"),
        (r"interface\s+\w+\s*\{[^}]*\}\s*//?\s*for\s+future", "Interface for future use"),
        (r"plugin\s*(system|architecture|framework)", "Plugin system"),
        (r"(extensible|pluggable|modular)\s+(architecture|design|system)", "Premature extensibility"),
        (r"TODO:\s*(add|implement)\s*(more|additional)\s*(types|variants)", "Planned variants"),
        (r"(base|abstract)\s+class\s+\w+\s*\{[^}]{0,200}\}", "Abstract base with minimal implementation"),
        (r"factory\s+(method|pattern|class)", "Factory pattern"),
        (r"provider\s+(interface|pattern|abstraction)", "Provider abstraction"),
    ]

    YAGNI_INDICATORS = [
        r"might\s+need\s+later",
        r"just\s+in\s+case",
        r"for\s+future\s+(use|expansion)",
        r"could\s+be\s+extended",
        r"in\s+case\s+we\s+need",
    ]

    def detect(
        self,
        content: str,
        content_type: ContentType,
        context: Dict[str, Any]
    ) -> PatternDetectionResult:
        indicators = []
        total_score = 0

        content_lower = content.lower()

        # Check for generic patterns
        for pattern, description in self.GENERIC_PATTERNS:
            matches = re.findall(pattern, content_lower)
            if matches:
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="generic_pattern",
                    description=description,
                    matched_text=str(matches[0])[:50],
                    confidence=0.7,
                    suggestions=["Start with concrete implementation", "Extract abstraction only when needed"]
                ))
                total_score += 0.15

        # Check for YAGNI indicators
        for pattern in self.YAGNI_INDICATORS:
            if re.search(pattern, content_lower):
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="yagni_comment",
                    description="YAGNI violation indicated in comments",
                    matched_text=pattern,
                    confidence=0.85,
                    suggestions=["Remove speculative code", "Follow YAGNI principle"]
                ))
                total_score += 0.2

        # Check interface-to-implementation ratio (for code)
        if content_type == ContentType.CODE:
            interfaces = len(re.findall(r'interface\s+\w+', content_lower))
            classes = len(re.findall(r'class\s+\w+', content_lower))
            if interfaces > 0 and classes > 0:
                ratio = interfaces / classes
                if ratio > 0.5:
                    indicators.append(PatternIndicator(
                        pattern_type=self.pattern_type,
                        indicator_name="high_interface_ratio",
                        description=f"High interface-to-class ratio: {ratio:.2f}",
                        confidence=0.6,
                        suggestions=["Reduce unnecessary abstractions"]
                    ))
                    total_score += 0.15

        total_score = min(total_score, 1.0)
        detected = total_score >= self.default_threshold

        return PatternDetectionResult(
            pattern_type=self.pattern_type,
            detected=detected,
            severity=self._calculate_severity(total_score),
            confidence=total_score,
            indicators=indicators,
            total_score=total_score,
            threshold=self.default_threshold,
            remediation=[
                "Apply YAGNI: You Aren't Gonna Need It",
                "Start with concrete, extract abstraction when needed",
                "Three concrete uses before abstracting (Rule of Three)",
                "Prefer composition over inheritance"
            ] if detected else []
        )


class OverConfigurationDetector(PatternDetectorBase):
    """
    AP-3: Over-Configuration Detector

    Detects excessive configuration options that add complexity.
    """

    pattern_type = AntiPatternType.OVER_CONFIGURATION
    description = "Too many configuration options adding unnecessary complexity"
    default_threshold = 0.5

    CONFIG_PATTERNS = [
        (r"config\.(get|set)\(['\"][^'\"]+['\"]\)", "Config access"),
        (r"settings\.[A-Z_]+", "Settings constant"),
        (r"env\.(get|[A-Z_]+)", "Environment variable"),
        (r"options\s*:\s*\{", "Options object"),
        (r"(enable|disable)_\w+\s*=", "Feature flag"),
        (r"\bflags?\.\w+", "Flag access"),
    ]

    def detect(
        self,
        content: str,
        content_type: ContentType,
        context: Dict[str, Any]
    ) -> PatternDetectionResult:
        indicators = []
        total_score = 0

        # Count configuration points
        config_count = 0
        for pattern, description in self.CONFIG_PATTERNS:
            matches = re.findall(pattern, content)
            config_count += len(matches)
            if matches:
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="config_point",
                    description=f"{description}: {len(matches)} instances",
                    confidence=0.5,
                    suggestions=["Consider using convention over configuration"]
                ))

        # Check config density (configs per 100 lines)
        lines = len(content.split('\n'))
        if lines > 0:
            density = config_count / lines * 100
            if density > 5:
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="high_config_density",
                    description=f"High configuration density: {density:.1f} per 100 lines",
                    confidence=0.7,
                    suggestions=["Reduce configuration complexity", "Use sensible defaults"]
                ))
                total_score += min(density / 20, 0.4)

        # Check for config file complexity
        if content_type == ContentType.CODE:
            yaml_json_blocks = len(re.findall(r'(yaml|json|toml|ini)\s*(config|file)', content.lower()))
            if yaml_json_blocks > 3:
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="multiple_config_formats",
                    description=f"Multiple config format references: {yaml_json_blocks}",
                    confidence=0.6,
                    suggestions=["Standardize on one config format"]
                ))
                total_score += 0.2

        # Raw config count scoring
        if config_count > 50:
            total_score += 0.3
        elif config_count > 20:
            total_score += 0.15

        total_score = min(total_score, 1.0)
        detected = total_score >= self.default_threshold

        return PatternDetectionResult(
            pattern_type=self.pattern_type,
            detected=detected,
            severity=self._calculate_severity(total_score),
            confidence=total_score,
            indicators=indicators,
            total_score=total_score,
            threshold=self.default_threshold,
            remediation=[
                "Prefer convention over configuration",
                "Use sensible defaults that work for 80% of cases",
                "Hide advanced options until needed",
                "Document which configs are actually needed"
            ] if detected else []
        )


class GoldPlatingDetector(PatternDetectorBase):
    """
    AP-4: Gold-plating Detector

    Detects features/polish beyond requirements.
    """

    pattern_type = AntiPatternType.GOLD_PLATING
    description = "Adding features or polish beyond what was requested"
    default_threshold = 0.45

    GOLD_PLATING_PATTERNS = [
        (r"bonus\s+(feature|functionality)", "Bonus feature"),
        (r"nice\s+to\s+have", "Nice-to-have feature"),
        (r"also\s+added\s+\w+", "Unrequested addition"),
        (r"while\s+(I|we)\s+were?\s+(at\s+it|here)", "Scope expansion"),
        (r"extra\s+(polish|feature|functionality)", "Extra polish"),
        (r"(improved|enhanced)\s+beyond\s+requirements?", "Beyond requirements"),
        (r"additional\s+(animation|effect|style)", "Additional UI polish"),
        (r"user\s+might\s+(appreciate|like|enjoy)", "Speculative user preference"),
    ]

    def detect(
        self,
        content: str,
        content_type: ContentType,
        context: Dict[str, Any]
    ) -> PatternDetectionResult:
        indicators = []
        total_score = 0

        content_lower = content.lower()

        for pattern, description in self.GOLD_PLATING_PATTERNS:
            matches = re.findall(pattern, content_lower)
            if matches:
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="gold_plating_language",
                    description=description,
                    matched_text=str(matches[0])[:50],
                    confidence=0.75,
                    suggestions=["Focus on requirements only", "Save enhancements for later iteration"]
                ))
                total_score += 0.2

        # Check if requirements are mentioned
        requirements_mentioned = bool(re.search(r'requirement|spec|story|ticket', content_lower))
        if not requirements_mentioned and content_type in [ContentType.COMMIT, ContentType.REVIEW]:
            indicators.append(PatternIndicator(
                pattern_type=self.pattern_type,
                indicator_name="no_requirement_reference",
                description="No reference to requirements/specs",
                confidence=0.5,
                suggestions=["Link changes to specific requirements"]
            ))
            total_score += 0.15

        total_score = min(total_score, 1.0)
        detected = total_score >= self.default_threshold

        return PatternDetectionResult(
            pattern_type=self.pattern_type,
            detected=detected,
            severity=self._calculate_severity(total_score),
            confidence=total_score,
            indicators=indicators,
            total_score=total_score,
            threshold=self.default_threshold,
            remediation=[
                "Stick to the requirements exactly",
                "Save 'nice-to-haves' for future iterations",
                "Verify each feature against original spec",
                "Time-box polish work"
            ] if detected else []
        )


class NotInventedHereDetector(PatternDetectorBase):
    """
    AP-5: Not-Invented-Here Detector

    Detects reinvention of existing solutions.
    """

    pattern_type = AntiPatternType.NOT_INVENTED_HERE
    description = "Reinventing the wheel instead of using existing solutions"
    default_threshold = 0.5

    REINVENTION_PATTERNS = [
        (r"custom\s+(implementation|solution)\s+for\s+\w+", "Custom implementation"),
        (r"our\s+own\s+(version|implementation)", "Own version"),
        (r"wrote\s+(my|our)\s+own", "Wrote own"),
        (r"don't\s+want\s+to\s+use\s+\w+", "Avoiding existing solution"),
        (r"simpler\s+than\s+using\s+\w+", "Reinvention justification"),
    ]

    # Common things that shouldn't be reinvented
    COMMON_LIBRARIES = [
        "authentication", "authorization", "logging", "caching",
        "serialization", "validation", "http client", "date handling",
        "cryptography", "encryption", "hashing", "uuid generation",
        "email sending", "pdf generation", "csv parsing", "json parsing",
    ]

    def detect(
        self,
        content: str,
        content_type: ContentType,
        context: Dict[str, Any]
    ) -> PatternDetectionResult:
        indicators = []
        total_score = 0

        content_lower = content.lower()

        for pattern, description in self.REINVENTION_PATTERNS:
            matches = re.findall(pattern, content_lower)
            if matches:
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="reinvention_language",
                    description=description,
                    matched_text=str(matches[0])[:50],
                    confidence=0.7,
                    suggestions=["Consider existing libraries", "Evaluate build vs buy"]
                ))
                total_score += 0.25

        # Check for implementing common functionality
        for lib_category in self.COMMON_LIBRARIES:
            if f"implement {lib_category}" in content_lower or f"custom {lib_category}" in content_lower:
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="reinventing_common",
                    description=f"Implementing common functionality: {lib_category}",
                    confidence=0.8,
                    suggestions=[f"Use established library for {lib_category}"]
                ))
                total_score += 0.3

        total_score = min(total_score, 1.0)
        detected = total_score >= self.default_threshold

        return PatternDetectionResult(
            pattern_type=self.pattern_type,
            detected=detected,
            severity=self._calculate_severity(total_score),
            confidence=total_score,
            indicators=indicators,
            total_score=total_score,
            threshold=self.default_threshold,
            remediation=[
                "Research existing libraries first",
                "Evaluate build vs buy tradeoffs",
                "Custom code = maintenance burden",
                "Use battle-tested solutions for common problems"
            ] if detected else []
        )


class FeatureCreepDetector(PatternDetectorBase):
    """
    AP-6: Feature Creep Detector

    Detects uncontrolled addition of new features.
    """

    pattern_type = AntiPatternType.FEATURE_CREEP
    description = "Uncontrolled addition of features beyond original scope"
    default_threshold = 0.45

    CREEP_PATTERNS = [
        (r"(also|additionally)\s+(add|implement|include)", "Additional feature"),
        (r"while\s+we('re|\s+are)\s+(at\s+it|here)", "Scope expansion"),
        (r"wouldn't\s+it\s+be\s+(nice|great|cool)", "Feature suggestion"),
        (r"should\s+also\s+(have|include|support)", "Should also have"),
        (r"let's\s+also\s+(add|throw\s+in)", "Let's also add"),
        (r"one\s+more\s+(thing|feature)", "One more thing"),
        (r"quick(ly)?\s+add", "Quick addition"),
    ]

    def detect(
        self,
        content: str,
        content_type: ContentType,
        context: Dict[str, Any]
    ) -> PatternDetectionResult:
        indicators = []
        total_score = 0

        content_lower = content.lower()

        for pattern, description in self.CREEP_PATTERNS:
            matches = re.findall(pattern, content_lower)
            if matches:
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="creep_language",
                    description=description,
                    matched_text=str(matches[0])[:50],
                    confidence=0.7,
                    suggestions=["Document in backlog instead", "Focus on current scope"]
                ))
                total_score += 0.2

        # Count feature-related words
        feature_words = len(re.findall(r'\b(feature|functionality|capability|ability)\b', content_lower))
        if feature_words > 10:
            indicators.append(PatternIndicator(
                pattern_type=self.pattern_type,
                indicator_name="high_feature_count",
                description=f"High feature word frequency: {feature_words}",
                confidence=0.5,
                suggestions=["Reduce scope to core features"]
            ))
            total_score += 0.15

        total_score = min(total_score, 1.0)
        detected = total_score >= self.default_threshold

        return PatternDetectionResult(
            pattern_type=self.pattern_type,
            detected=detected,
            severity=self._calculate_severity(total_score),
            confidence=total_score,
            indicators=indicators,
            total_score=total_score,
            threshold=self.default_threshold,
            remediation=[
                "Add suggestions to backlog, not current work",
                "Use strict change control",
                "Finish current scope before adding new",
                "Ask: Is this in the original requirements?"
            ] if detected else []
        )


class AnalysisParalysisDetector(PatternDetectorBase):
    """
    AP-7: Analysis Paralysis Detector

    Detects overthinking/overplanning without action.
    """

    pattern_type = AntiPatternType.ANALYSIS_PARALYSIS
    description = "Excessive analysis preventing progress"
    default_threshold = 0.5

    PARALYSIS_PATTERNS = [
        (r"need\s+to\s+(further|more)\s+analyze", "Further analysis needed"),
        (r"investigate\s+(all|every)\s+option", "Investigate all options"),
        (r"compare\s+\d+\+?\s+alternatives", "Comparing many alternatives"),
        (r"research\s+more\s+(before|prior)", "More research needed"),
        (r"not\s+ready\s+to\s+(decide|choose)", "Not ready to decide"),
        (r"need\s+more\s+(data|information|input)", "Need more data"),
        (r"waiting\s+for\s+(approval|confirmation)", "Waiting for approval"),
        (r"still\s+(evaluating|assessing|reviewing)", "Still evaluating"),
    ]

    def detect(
        self,
        content: str,
        content_type: ContentType,
        context: Dict[str, Any]
    ) -> PatternDetectionResult:
        indicators = []
        total_score = 0

        content_lower = content.lower()

        for pattern, description in self.PARALYSIS_PATTERNS:
            matches = re.findall(pattern, content_lower)
            if matches:
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="paralysis_language",
                    description=description,
                    matched_text=str(matches[0])[:50],
                    confidence=0.7,
                    suggestions=["Make a decision", "Timebox analysis"]
                ))
                total_score += 0.2

        # Check for excessive options listing
        options = len(re.findall(r'option\s*\d+|alternative\s*\d+|choice\s*\d+', content_lower))
        if options > 5:
            indicators.append(PatternIndicator(
                pattern_type=self.pattern_type,
                indicator_name="too_many_options",
                description=f"Too many options listed: {options}",
                confidence=0.65,
                suggestions=["Limit to 2-3 viable options", "Use decision matrix"]
            ))
            total_score += 0.2

        total_score = min(total_score, 1.0)
        detected = total_score >= self.default_threshold

        return PatternDetectionResult(
            pattern_type=self.pattern_type,
            detected=detected,
            severity=self._calculate_severity(total_score),
            confidence=total_score,
            indicators=indicators,
            total_score=total_score,
            threshold=self.default_threshold,
            remediation=[
                "Timebox analysis to fixed duration",
                "Make reversible decisions quickly",
                "Use 'good enough' as criteria",
                "Start with MVP and iterate"
            ] if detected else []
        )


class ScopeCreepDetector(PatternDetectorBase):
    """
    AP-8: Scope Creep Detector

    Detects gradual expansion of project scope.
    """

    pattern_type = AntiPatternType.SCOPE_CREEP
    description = "Gradual expansion of project scope beyond original boundaries"
    default_threshold = 0.45

    CREEP_PATTERNS = [
        (r"while\s+I('m|s)?\s+(here|at it|doing this)", "While I'm here"),
        (r"also\s+(refactor|clean|improve|fix|update)", "Also refactor"),
        (r"might\s+as\s+well", "Might as well"),
        (r"let('s)?\s+(also|quickly)", "Let's also"),
        (r"should\s+(be|get)\s+refactored", "Should be refactored"),
        (r"(noticed|found)\s+(that|this|some)", "Noticed something"),
        (r"unrelated\s+but", "Unrelated but"),
        (r"side\s+note", "Side note"),
        (r"by\s+the\s+way", "By the way"),
        (r"out\s+of\s+scope\s+but", "Out of scope but"),
    ]

    def detect(
        self,
        content: str,
        content_type: ContentType,
        context: Dict[str, Any]
    ) -> PatternDetectionResult:
        indicators = []
        total_score = 0

        content_lower = content.lower()

        for pattern, description in self.CREEP_PATTERNS:
            matches = re.findall(pattern, content_lower)
            for match in matches:
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="scope_creep_language",
                    description=description,
                    matched_text=str(match)[:50],
                    confidence=0.8,
                    suggestions=["Create separate task", "Focus on original scope"]
                ))
                total_score += 0.25

        total_score = min(total_score, 1.0)
        detected = total_score >= self.default_threshold

        return PatternDetectionResult(
            pattern_type=self.pattern_type,
            detected=detected,
            severity=self._calculate_severity(total_score),
            confidence=total_score,
            indicators=indicators,
            total_score=total_score,
            threshold=self.default_threshold,
            remediation=[
                "Create separate tickets for out-of-scope work",
                "Use the Refactor Guard pattern",
                "Ask: Is this in my current task?",
                "Document scope boundaries clearly"
            ] if detected else []
        )


class PerfectionismDetector(PatternDetectorBase):
    """
    AP-9: Perfectionism Detector

    Detects "perfect is the enemy of good" behavior.
    """

    pattern_type = AntiPatternType.PERFECTIONISM
    description = "Pursuit of perfection preventing completion"
    default_threshold = 0.45

    PERFECTIONISM_PATTERNS = [
        (r"(perfect|ideal|optimal)\s+(solution|approach|way)", "Perfect solution seeking"),
        (r"100%\s+(coverage|complete|perfect)", "100% target"),
        (r"(needs?|requires?)\s+to\s+be\s+perfect", "Needs to be perfect"),
        (r"not\s+(quite|good|satisfied|happy)", "Not satisfied"),
        (r"(polish|refine|perfect)\s+(until|before)", "Polish until"),
        (r"can('t)?\s+(be|get)\s+(better|improved)", "Can be improved"),
        (r"(just|almost)\s+(one|a\s+few)\s+more\s+(tweak|change)", "Just one more tweak"),
        (r"nearly\s+(there|perfect|done)", "Nearly there"),
    ]

    def detect(
        self,
        content: str,
        content_type: ContentType,
        context: Dict[str, Any]
    ) -> PatternDetectionResult:
        indicators = []
        total_score = 0

        content_lower = content.lower()

        for pattern, description in self.PERFECTIONISM_PATTERNS:
            matches = re.findall(pattern, content_lower)
            if matches:
                indicators.append(PatternIndicator(
                    pattern_type=self.pattern_type,
                    indicator_name="perfectionism_language",
                    description=description,
                    matched_text=str(matches[0])[:50],
                    confidence=0.7,
                    suggestions=["Define 'done' criteria", "Accept good enough"]
                ))
                total_score += 0.2

        total_score = min(total_score, 1.0)
        detected = total_score >= self.default_threshold

        return PatternDetectionResult(
            pattern_type=self.pattern_type,
            detected=detected,
            severity=self._calculate_severity(total_score),
            confidence=total_score,
            indicators=indicators,
            total_score=total_score,
            threshold=self.default_threshold,
            remediation=[
                "Define clear 'done' criteria upfront",
                "80/20 rule: 80% of value from 20% of effort",
                "Ship, then iterate",
                "Good enough is good enough"
            ] if detected else []
        )


class AntiPatternDetector:
    """
    Main anti-pattern detector service.

    Coordinates all pattern detectors and provides unified analysis.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(".agent_memory/antipatterns")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize all detectors
        self.detectors: Dict[AntiPatternType, PatternDetectorBase] = {
            AntiPatternType.OVERSPECIFICATION: OverspecificationDetector(),
            AntiPatternType.PREMATURE_GENERICIZATION: PrematureGenericizationDetector(),
            AntiPatternType.OVER_CONFIGURATION: OverConfigurationDetector(),
            AntiPatternType.GOLD_PLATING: GoldPlatingDetector(),
            AntiPatternType.NOT_INVENTED_HERE: NotInventedHereDetector(),
            AntiPatternType.FEATURE_CREEP: FeatureCreepDetector(),
            AntiPatternType.ANALYSIS_PARALYSIS: AnalysisParalysisDetector(),
            AntiPatternType.SCOPE_CREEP: ScopeCreepDetector(),
            AntiPatternType.PERFECTIONISM: PerfectionismDetector(),
        }

        self.results: Dict[str, AnalysisResult] = {}

    def analyze(
        self,
        content: str,
        content_type: str = "code",
        context: Optional[Dict[str, Any]] = None,
        patterns: Optional[List[str]] = None,
        quality_threshold: float = 0.7
    ) -> AnalysisResult:
        """
        Analyze content for anti-patterns.

        Args:
            content: Content to analyze
            content_type: Type of content
            context: Additional context
            patterns: Specific patterns to check (None = all)
            quality_threshold: Threshold for quality gate

        Returns:
            AnalysisResult
        """
        ct = ContentType(content_type)
        ctx = context or {}

        # Determine which detectors to run
        detectors_to_run = self.detectors
        if patterns:
            detectors_to_run = {
                k: v for k, v in self.detectors.items()
                if k.value in patterns
            }

        # Run all detectors
        pattern_results = []
        for pattern_type, detector in detectors_to_run.items():
            result = detector.detect(content, ct, ctx)
            pattern_results.append(result)

        # Calculate overall health
        detected_count = sum(1 for p in pattern_results if p.detected)
        total_severity = sum(
            {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}[p.severity.value]
            for p in pattern_results if p.detected
        )

        if detected_count > 0:
            avg_severity = total_severity / detected_count
            overall_health = max(0, 1 - (detected_count / len(pattern_results)) * avg_severity)
        else:
            overall_health = 1.0

        # Check quality gate
        quality_gate_passed = overall_health >= quality_threshold

        result = AnalysisResult(
            id=str(uuid.uuid4()),
            content_type=ct,
            analyzed_at=datetime.now(),
            content_length=len(content),
            patterns_detected=pattern_results,
            overall_health=overall_health,
            quality_gate_passed=quality_gate_passed,
            context=ctx
        )

        self.results[result.id] = result
        self._save_result(result)

        return result

    def _save_result(self, result: AnalysisResult) -> None:
        """Save result to storage."""
        file_path = self.storage_path / f"{result.id}.json"
        file_path.write_text(json.dumps(result.to_dict(), indent=2, default=str))

    def get_result(self, result_id: str) -> Optional[AnalysisResult]:
        """Get result by ID."""
        return self.results.get(result_id)

    def check_quality_gate(
        self,
        result: AnalysisResult,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Check if analysis passes quality gate.

        Args:
            result: Analysis result
            threshold: Health threshold

        Returns:
            Gate result with details
        """
        passed = result.overall_health >= threshold
        blocking_patterns = result.get_critical_patterns()

        return {
            "passed": passed,
            "health_score": result.overall_health,
            "threshold": threshold,
            "blocking_patterns": [p.pattern_type.value for p in blocking_patterns],
            "patterns_detected": sum(1 for p in result.patterns_detected if p.detected),
            "recommendation": "Proceed" if passed else "Address anti-patterns before proceeding"
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        all_results = list(self.results.values())

        pattern_counts = {p.value: 0 for p in AntiPatternType}
        for result in all_results:
            for pattern in result.patterns_detected:
                if pattern.detected:
                    pattern_counts[pattern.pattern_type.value] += 1

        return {
            "total_analyses": len(all_results),
            "average_health": sum(r.overall_health for r in all_results) / len(all_results) if all_results else 0,
            "pattern_frequency": pattern_counts,
            "most_common": max(pattern_counts, key=pattern_counts.get) if pattern_counts else None,
            "quality_gate_pass_rate": sum(1 for r in all_results if r.quality_gate_passed) / len(all_results) if all_results else 0
        }
