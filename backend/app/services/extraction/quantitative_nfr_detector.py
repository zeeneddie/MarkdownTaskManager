# Quantitative NFR Detector - Week 102: NFR Quick Wins
# NFR-QW-1: Detect NFRs with numeric specifications

"""
Quantitative NFR Detector

Detects and extracts Non-Functional Requirements with quantitative metrics:
- Performance (response time, throughput)
- Scalability (concurrent users, data volume)
- Availability (uptime percentage)
- Reliability (MTBF, error rates)
- Security (encryption strength, session timeout)
- Capacity (storage, memory, bandwidth)

Extracts:
- Metric values with units
- Thresholds and targets
- Measurement conditions
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple, Any
import re


class NFRCategory(Enum):
    """Categories of Non-Functional Requirements."""
    PERFORMANCE = "performance"
    SCALABILITY = "scalability"
    AVAILABILITY = "availability"
    RELIABILITY = "reliability"
    SECURITY = "security"
    CAPACITY = "capacity"
    USABILITY = "usability"
    MAINTAINABILITY = "maintainability"
    PORTABILITY = "portability"
    COMPLIANCE = "compliance"


class MetricUnit(Enum):
    """Units for quantitative metrics."""
    # Time units
    MILLISECONDS = "ms"
    SECONDS = "s"
    MINUTES = "min"
    HOURS = "h"
    DAYS = "d"

    # Rate units
    REQUESTS_PER_SECOND = "req/s"
    TRANSACTIONS_PER_SECOND = "tps"
    QUERIES_PER_SECOND = "qps"
    PER_SECOND = "/s"
    PER_MINUTE = "/min"
    PER_HOUR = "/h"

    # Data units
    BYTES = "B"
    KILOBYTES = "KB"
    MEGABYTES = "MB"
    GIGABYTES = "GB"
    TERABYTES = "TB"

    # Percentage
    PERCENT = "%"

    # Count units
    USERS = "users"
    CONNECTIONS = "connections"
    RECORDS = "records"

    # Other
    BITS = "bits"
    NINES = "nines"  # For availability (e.g., 99.99% = 4 nines)
    CUSTOM = "custom"


class ThresholdType(Enum):
    """Type of threshold constraint."""
    MAXIMUM = "maximum"      # Must not exceed (e.g., response time < 200ms)
    MINIMUM = "minimum"      # Must be at least (e.g., availability >= 99.9%)
    EXACT = "exact"          # Must be exactly (e.g., encryption = 256 bits)
    RANGE = "range"          # Must be between (e.g., 100-500 users)
    TARGET = "target"        # Goal/target (e.g., target 50ms average)


@dataclass
class QuantitativeMetric:
    """A quantitative metric extracted from NFR."""
    name: str
    value: float
    unit: MetricUnit
    threshold_type: ThresholdType
    raw_text: str
    upper_bound: Optional[float] = None  # For range types
    condition: Optional[str] = None      # e.g., "under normal load"
    confidence: float = 0.9

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit.value,
            "threshold_type": self.threshold_type.value,
            "upper_bound": self.upper_bound,
            "condition": self.condition,
            "raw_text": self.raw_text,
            "confidence": self.confidence
        }

    def formatted_value(self) -> str:
        """Return human-readable formatted value."""
        if self.threshold_type == ThresholdType.RANGE:
            return f"{self.value}-{self.upper_bound} {self.unit.value}"
        elif self.threshold_type == ThresholdType.MAXIMUM:
            return f"< {self.value} {self.unit.value}"
        elif self.threshold_type == ThresholdType.MINIMUM:
            return f">= {self.value} {self.unit.value}"
        else:
            return f"{self.value} {self.unit.value}"


@dataclass
class QuantitativeNFR:
    """A Non-Functional Requirement with quantitative specifications."""
    category: NFRCategory
    description: str
    metrics: List[QuantitativeMetric]
    source_text: str
    test_approach: str
    measurement_method: str
    priority: int = 2  # 1-5, 1 being highest
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "description": self.description,
            "metrics": [m.to_dict() for m in self.metrics],
            "source_text": self.source_text,
            "test_approach": self.test_approach,
            "measurement_method": self.measurement_method,
            "priority": self.priority,
            "tags": self.tags
        }

    @property
    def primary_metric(self) -> Optional[QuantitativeMetric]:
        """Return the primary metric (first one)."""
        return self.metrics[0] if self.metrics else None

    @property
    def is_testable(self) -> bool:
        """Check if NFR has clear, testable metrics."""
        return len(self.metrics) > 0 and all(
            m.confidence >= 0.7 for m in self.metrics
        )


@dataclass
class NFRDetectionResult:
    """Result of NFR detection process."""
    source: str
    detected_nfrs: List[QuantitativeNFR]
    unquantified_nfrs: List[str]  # NFRs found but lacking metrics
    statistics: Dict[str, Any]
    suggestions: List[str]

    def to_dict(self) -> dict:
        return {
            "detected_count": len(self.detected_nfrs),
            "unquantified_count": len(self.unquantified_nfrs),
            "nfrs": [n.to_dict() for n in self.detected_nfrs],
            "unquantified": self.unquantified_nfrs,
            "statistics": self.statistics,
            "suggestions": self.suggestions
        }


class QuantitativeNFRDetector:
    """
    Detects NFRs with quantitative specifications in text.

    Capabilities:
    - Extract numeric values with units
    - Categorize NFRs (performance, security, etc.)
    - Determine threshold types (max, min, range)
    - Identify measurement conditions
    - Suggest testing approaches

    Usage:
        detector = QuantitativeNFRDetector()

        text = "The API must respond within 200ms under normal load"
        result = detector.detect(text)

        for nfr in result.detected_nfrs:
            print(f"{nfr.category.value}: {nfr.primary_metric.formatted_value()}")
    """

    # Patterns for extracting numeric values with units
    TIME_PATTERNS = [
        (r"(\d+(?:\.\d+)?)\s*(milliseconds?|ms)", MetricUnit.MILLISECONDS),
        (r"(\d+(?:\.\d+)?)\s*(seconds?|secs?|s)(?!\w)", MetricUnit.SECONDS),
        (r"(\d+(?:\.\d+)?)\s*(minutes?|mins?|m)(?!\w)", MetricUnit.MINUTES),
        (r"(\d+(?:\.\d+)?)\s*(hours?|hrs?|h)(?!\w)", MetricUnit.HOURS),
        (r"(\d+(?:\.\d+)?)\s*(days?|d)(?!\w)", MetricUnit.DAYS),
    ]

    RATE_PATTERNS = [
        (r"(\d+(?:\.\d+)?)\s*(requests?\s*(?:per\s*)?(?:/\s*)?(?:sec(?:ond)?|s)|req/s|rps)", MetricUnit.REQUESTS_PER_SECOND),
        (r"(\d+(?:\.\d+)?)\s*(transactions?\s*(?:per\s*)?(?:/\s*)?(?:sec(?:ond)?|s)|tps)", MetricUnit.TRANSACTIONS_PER_SECOND),
        (r"(\d+(?:\.\d+)?)\s*(queries?\s*(?:per\s*)?(?:/\s*)?(?:sec(?:ond)?|s)|qps)", MetricUnit.QUERIES_PER_SECOND),
        (r"(\d+(?:\.\d+)?)\s*(?:per\s*|/)?(second|sec|s)(?!\w)", MetricUnit.PER_SECOND),
        (r"(\d+(?:\.\d+)?)\s*(?:per\s*|/)?(minute|min|m)(?!\w)", MetricUnit.PER_MINUTE),
    ]

    DATA_PATTERNS = [
        (r"(\d+(?:\.\d+)?)\s*(terabytes?|tb)", MetricUnit.TERABYTES),
        (r"(\d+(?:\.\d+)?)\s*(gigabytes?|gb)", MetricUnit.GIGABYTES),
        (r"(\d+(?:\.\d+)?)\s*(megabytes?|mb)", MetricUnit.MEGABYTES),
        (r"(\d+(?:\.\d+)?)\s*(kilobytes?|kb)", MetricUnit.KILOBYTES),
        (r"(\d+(?:\.\d+)?)\s*(bytes?|b)(?!\w)", MetricUnit.BYTES),
    ]

    PERCENTAGE_PATTERNS = [
        (r"(\d+(?:\.\d+)?)\s*%", MetricUnit.PERCENT),
        (r"(\d+(?:\.\d+)?)\s*percent", MetricUnit.PERCENT),
    ]

    COUNT_PATTERNS = [
        (r"(\d+(?:,\d+)*)\s*(concurrent\s+)?users?", MetricUnit.USERS),
        (r"(\d+(?:,\d+)*)\s*connections?", MetricUnit.CONNECTIONS),
        (r"(\d+(?:,\d+)*)\s*records?", MetricUnit.RECORDS),
    ]

    SECURITY_PATTERNS = [
        (r"(\d+)[\s-]*(bit)\s*(?:encryption|key|aes|rsa)", MetricUnit.BITS),
        (r"aes[\s-]*(\d+)", MetricUnit.BITS),
        (r"rsa[\s-]*(\d+)", MetricUnit.BITS),
    ]

    # NFR category indicators
    CATEGORY_INDICATORS = {
        NFRCategory.PERFORMANCE: [
            "response time", "latency", "throughput", "speed",
            "load time", "processing time", "execution time",
            "queries per second", "transactions per second",
        ],
        NFRCategory.SCALABILITY: [
            "concurrent", "simultaneous", "users", "connections",
            "scale", "horizontal", "vertical", "elastic",
            "peak load", "maximum load",
        ],
        NFRCategory.AVAILABILITY: [
            "uptime", "availability", "downtime", "sla",
            "service level", "99.9", "five nines", "four nines",
            "high availability", "failover",
        ],
        NFRCategory.RELIABILITY: [
            "mtbf", "mttr", "error rate", "failure rate",
            "fault tolerance", "recovery", "data loss",
            "mean time", "reliability",
        ],
        NFRCategory.SECURITY: [
            "encryption", "aes", "rsa", "ssl", "tls",
            "authentication", "authorization", "timeout",
            "session", "password", "token", "key length",
        ],
        NFRCategory.CAPACITY: [
            "storage", "memory", "disk", "bandwidth",
            "data volume", "file size", "database size",
            "capacity", "limit",
        ],
        NFRCategory.USABILITY: [
            "clicks", "steps", "time to complete",
            "learning curve", "accessibility", "wcag",
        ],
        NFRCategory.MAINTAINABILITY: [
            "code coverage", "cyclomatic complexity",
            "documentation", "modularity", "testability",
        ],
        NFRCategory.COMPLIANCE: [
            "gdpr", "hipaa", "pci", "sox", "iso",
            "regulation", "audit", "certification",
        ],
    }

    # Threshold type indicators
    THRESHOLD_INDICATORS = {
        ThresholdType.MAXIMUM: [
            "under", "within", "less than", "at most", "maximum",
            "max", "no more than", "not exceed", "<", "<=",
        ],
        ThresholdType.MINIMUM: [
            "at least", "minimum", "min", "greater than",
            "more than", ">=", ">", "above",
        ],
        ThresholdType.EXACT: [
            "exactly", "must be", "equals", "=",
        ],
        ThresholdType.TARGET: [
            "target", "goal", "aim", "strive for",
            "ideally", "optimally",
        ],
    }

    # Test approach mappings
    TEST_APPROACHES = {
        NFRCategory.PERFORMANCE: "Load testing with tools like k6, JMeter, or Gatling",
        NFRCategory.SCALABILITY: "Stress testing and horizontal scaling validation",
        NFRCategory.AVAILABILITY: "Chaos engineering and failover testing",
        NFRCategory.RELIABILITY: "Endurance testing and failure injection",
        NFRCategory.SECURITY: "Penetration testing and security scanning",
        NFRCategory.CAPACITY: "Capacity planning tests with realistic data volumes",
        NFRCategory.USABILITY: "User testing and analytics measurement",
        NFRCategory.MAINTAINABILITY: "Static code analysis and code review",
        NFRCategory.COMPLIANCE: "Compliance audit and certification testing",
        NFRCategory.PORTABILITY: "Cross-platform testing and compatibility checks",
    }

    # Measurement methods
    MEASUREMENT_METHODS = {
        NFRCategory.PERFORMANCE: "APM tools (New Relic, Datadog), browser dev tools, server metrics",
        NFRCategory.SCALABILITY: "Auto-scaling metrics, concurrent user monitoring",
        NFRCategory.AVAILABILITY: "Uptime monitoring services (Pingdom, UptimeRobot)",
        NFRCategory.RELIABILITY: "Error tracking (Sentry), log analysis, MTBF calculations",
        NFRCategory.SECURITY: "Vulnerability scanners, penetration test reports",
        NFRCategory.CAPACITY: "Infrastructure monitoring, storage metrics",
        NFRCategory.USABILITY: "User analytics, session recordings, surveys",
        NFRCategory.MAINTAINABILITY: "SonarQube, CodeClimate, coverage reports",
        NFRCategory.COMPLIANCE: "Audit reports, certification documents",
        NFRCategory.PORTABILITY: "Compatibility test matrices",
    }

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the detector.

        Args:
            strict_mode: If True, only return NFRs with high confidence metrics
        """
        self.strict_mode = strict_mode

    def detect(self, text: str) -> NFRDetectionResult:
        """
        Detect quantitative NFRs in text.

        Args:
            text: Text to analyze (requirements doc, spec, etc.)

        Returns:
            NFRDetectionResult with detected NFRs and statistics
        """
        detected_nfrs = []
        unquantified_nfrs = []

        # Split into sentences for analysis
        sentences = self._split_into_sentences(text)

        for sentence in sentences:
            # Check if sentence looks like an NFR
            category = self._detect_category(sentence)
            if category is None:
                continue

            # Extract metrics from sentence
            metrics = self._extract_metrics(sentence)

            if metrics:
                nfr = QuantitativeNFR(
                    category=category,
                    description=self._generate_description(sentence, category, metrics),
                    metrics=metrics,
                    source_text=sentence.strip(),
                    test_approach=self.TEST_APPROACHES.get(category, "Manual testing"),
                    measurement_method=self.MEASUREMENT_METHODS.get(category, "Custom measurement"),
                    priority=self._calculate_priority(category, metrics),
                    tags=self._generate_tags(category, metrics)
                )

                if not self.strict_mode or nfr.is_testable:
                    detected_nfrs.append(nfr)
            else:
                # NFR-like text but no metrics found
                unquantified_nfrs.append(sentence.strip())

        # Generate statistics
        statistics = self._generate_statistics(detected_nfrs, unquantified_nfrs)

        # Generate suggestions
        suggestions = self._generate_suggestions(detected_nfrs, unquantified_nfrs)

        return NFRDetectionResult(
            source=text,
            detected_nfrs=detected_nfrs,
            unquantified_nfrs=unquantified_nfrs,
            statistics=statistics,
            suggestions=suggestions
        )

    def detect_in_code(self, code: str) -> NFRDetectionResult:
        """
        Detect NFRs in code comments and constants.

        Args:
            code: Source code to analyze

        Returns:
            NFRDetectionResult with detected NFRs
        """
        # Extract comments and string literals
        comment_patterns = [
            r"//\s*(.+?)$",           # Single line //
            r"#\s*(.+?)$",            # Python/Ruby #
            r"/\*\s*(.+?)\s*\*/",     # Multi-line /* */
            r'"""(.+?)"""',           # Python docstring
            r"'''(.+?)'''",           # Python docstring
        ]

        extracted_text = []
        for pattern in comment_patterns:
            matches = re.findall(pattern, code, re.MULTILINE | re.DOTALL)
            extracted_text.extend(matches)

        # Also look for constants that might be NFR-related
        constant_patterns = [
            r"(?:const|final|CONST|MAX|MIN|TIMEOUT|LIMIT)\s*\w*\s*=\s*(.+?)(?:;|$)",
            r"(\w*(?:TIMEOUT|LIMIT|MAX|MIN|THRESHOLD|RETRY)\w*)\s*[:=]\s*(\d+)",
        ]

        for pattern in constant_patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    extracted_text.append(" ".join(match))
                else:
                    extracted_text.append(match)

        # Combine and detect
        combined_text = "\n".join(extracted_text)
        return self.detect(combined_text)

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Handle bullet points and numbered lists
        text = re.sub(r"^\s*[-•*]\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s*", "", text, flags=re.MULTILINE)

        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+|\n+", text)

        # Filter empty and too short
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def _detect_category(self, text: str) -> Optional[NFRCategory]:
        """Detect the NFR category from text."""
        text_lower = text.lower()

        # Score each category
        category_scores = {}
        for category, indicators in self.CATEGORY_INDICATORS.items():
            score = sum(1 for ind in indicators if ind in text_lower)
            if score > 0:
                category_scores[category] = score

        if category_scores:
            return max(category_scores.keys(), key=lambda k: category_scores[k])

        return None

    def _extract_metrics(self, text: str) -> List[QuantitativeMetric]:
        """Extract quantitative metrics from text."""
        metrics = []
        text_lower = text.lower()

        # Try each pattern group
        all_patterns = (
            self.TIME_PATTERNS +
            self.RATE_PATTERNS +
            self.DATA_PATTERNS +
            self.PERCENTAGE_PATTERNS +
            self.COUNT_PATTERNS +
            self.SECURITY_PATTERNS
        )

        for pattern, unit in all_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                value_str = match.group(1).replace(",", "")
                try:
                    value = float(value_str)
                except ValueError:
                    continue

                # Determine threshold type
                threshold_type = self._detect_threshold_type(text_lower, match.start())

                # Extract condition if present
                condition = self._extract_condition(text, match.end())

                # Generate metric name based on context
                metric_name = self._generate_metric_name(text, unit)

                metric = QuantitativeMetric(
                    name=metric_name,
                    value=value,
                    unit=unit,
                    threshold_type=threshold_type,
                    raw_text=match.group(0),
                    condition=condition,
                    confidence=self._calculate_metric_confidence(text, match)
                )

                metrics.append(metric)

        # Check for range patterns
        range_metrics = self._extract_ranges(text)
        metrics.extend(range_metrics)

        # Deduplicate
        return self._deduplicate_metrics(metrics)

    def _detect_threshold_type(self, text: str, match_pos: int) -> ThresholdType:
        """Detect the threshold type based on surrounding text."""
        # Look at text before the match
        prefix = text[max(0, match_pos - 50):match_pos].lower()

        for threshold_type, indicators in self.THRESHOLD_INDICATORS.items():
            if any(ind in prefix for ind in indicators):
                return threshold_type

        # Default based on metric type
        return ThresholdType.MAXIMUM

    def _extract_condition(self, text: str, end_pos: int) -> Optional[str]:
        """Extract measurement condition (e.g., 'under normal load')."""
        condition_patterns = [
            r"(?:under|during|at|with|for)\s+([^.]+?)(?:\.|$)",
            r"(?:when|while)\s+([^.]+?)(?:\.|$)",
        ]

        suffix = text[end_pos:end_pos + 100]
        for pattern in condition_patterns:
            match = re.search(pattern, suffix, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _generate_metric_name(self, text: str, unit: MetricUnit) -> str:
        """Generate a name for the metric based on context."""
        text_lower = text.lower()

        # Time-based metrics
        if unit in [MetricUnit.MILLISECONDS, MetricUnit.SECONDS, MetricUnit.MINUTES]:
            if "response" in text_lower:
                return "response_time"
            if "load" in text_lower:
                return "load_time"
            if "timeout" in text_lower:
                return "timeout"
            if "session" in text_lower:
                return "session_timeout"
            return "execution_time"

        # Rate metrics
        if unit in [MetricUnit.REQUESTS_PER_SECOND, MetricUnit.TRANSACTIONS_PER_SECOND]:
            return "throughput"

        # Percentage metrics
        if unit == MetricUnit.PERCENT:
            if "uptime" in text_lower or "availability" in text_lower:
                return "availability"
            if "error" in text_lower:
                return "error_rate"
            if "coverage" in text_lower:
                return "coverage"
            return "percentage"

        # Data metrics
        if unit in [MetricUnit.BYTES, MetricUnit.KILOBYTES, MetricUnit.MEGABYTES,
                    MetricUnit.GIGABYTES, MetricUnit.TERABYTES]:
            if "storage" in text_lower:
                return "storage_capacity"
            if "memory" in text_lower:
                return "memory_limit"
            if "file" in text_lower:
                return "file_size_limit"
            return "data_capacity"

        # Count metrics
        if unit == MetricUnit.USERS:
            return "concurrent_users"
        if unit == MetricUnit.CONNECTIONS:
            return "max_connections"

        # Security metrics
        if unit == MetricUnit.BITS:
            return "encryption_strength"

        return "metric"

    def _extract_ranges(self, text: str) -> List[QuantitativeMetric]:
        """Extract range-based metrics (e.g., '100-500 users')."""
        metrics = []

        range_patterns = [
            r"(\d+(?:,\d+)*)\s*[-–to]\s*(\d+(?:,\d+)*)\s*(users?|connections?|ms|seconds?|%)",
            r"between\s+(\d+(?:,\d+)*)\s+and\s+(\d+(?:,\d+)*)\s*(users?|connections?|ms|seconds?|%)",
        ]

        for pattern in range_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    lower = float(match.group(1).replace(",", ""))
                    upper = float(match.group(2).replace(",", ""))
                    unit_str = match.group(3).lower()

                    unit = self._parse_unit(unit_str)

                    metric = QuantitativeMetric(
                        name=self._generate_metric_name(text, unit),
                        value=lower,
                        unit=unit,
                        threshold_type=ThresholdType.RANGE,
                        upper_bound=upper,
                        raw_text=match.group(0),
                        confidence=0.85
                    )
                    metrics.append(metric)
                except (ValueError, IndexError):
                    continue

        return metrics

    def _parse_unit(self, unit_str: str) -> MetricUnit:
        """Parse unit string to MetricUnit enum."""
        unit_str = unit_str.lower().strip()

        mappings = {
            "ms": MetricUnit.MILLISECONDS,
            "milliseconds": MetricUnit.MILLISECONDS,
            "s": MetricUnit.SECONDS,
            "seconds": MetricUnit.SECONDS,
            "sec": MetricUnit.SECONDS,
            "%": MetricUnit.PERCENT,
            "percent": MetricUnit.PERCENT,
            "users": MetricUnit.USERS,
            "user": MetricUnit.USERS,
            "connections": MetricUnit.CONNECTIONS,
            "connection": MetricUnit.CONNECTIONS,
            "gb": MetricUnit.GIGABYTES,
            "mb": MetricUnit.MEGABYTES,
            "kb": MetricUnit.KILOBYTES,
        }

        return mappings.get(unit_str, MetricUnit.CUSTOM)

    def _calculate_metric_confidence(self, text: str, match: re.Match) -> float:
        """Calculate confidence in the extracted metric."""
        confidence = 0.8

        # Higher confidence if has clear threshold indicator
        prefix = text[max(0, match.start() - 30):match.start()].lower()
        if any(ind in prefix for indicators in self.THRESHOLD_INDICATORS.values() for ind in indicators):
            confidence += 0.1

        # Higher confidence if context is clear
        if any(word in text.lower() for word in ["must", "should", "shall", "require"]):
            confidence += 0.05

        return min(1.0, confidence)

    def _deduplicate_metrics(self, metrics: List[QuantitativeMetric]) -> List[QuantitativeMetric]:
        """Remove duplicate metrics."""
        seen = set()
        unique = []

        for metric in metrics:
            key = (metric.name, metric.value, metric.unit)
            if key not in seen:
                seen.add(key)
                unique.append(metric)

        return unique

    def _generate_description(
        self,
        text: str,
        category: NFRCategory,
        metrics: List[QuantitativeMetric]
    ) -> str:
        """Generate a clear description of the NFR."""
        primary = metrics[0] if metrics else None

        if not primary:
            return text.strip()

        category_descriptions = {
            NFRCategory.PERFORMANCE: f"System {primary.name} must be {primary.formatted_value()}",
            NFRCategory.SCALABILITY: f"System must support {primary.formatted_value()}",
            NFRCategory.AVAILABILITY: f"System availability must be {primary.formatted_value()}",
            NFRCategory.RELIABILITY: f"System reliability measured at {primary.formatted_value()}",
            NFRCategory.SECURITY: f"Security requirement: {primary.formatted_value()}",
            NFRCategory.CAPACITY: f"System capacity: {primary.formatted_value()}",
        }

        base = category_descriptions.get(category, text.strip())

        if primary.condition:
            base += f" ({primary.condition})"

        return base

    def _calculate_priority(
        self,
        category: NFRCategory,
        metrics: List[QuantitativeMetric]
    ) -> int:
        """Calculate priority (1-5, 1 being highest)."""
        # Base priority by category
        category_priorities = {
            NFRCategory.SECURITY: 1,
            NFRCategory.AVAILABILITY: 1,
            NFRCategory.RELIABILITY: 2,
            NFRCategory.PERFORMANCE: 2,
            NFRCategory.SCALABILITY: 3,
            NFRCategory.COMPLIANCE: 2,
            NFRCategory.CAPACITY: 3,
            NFRCategory.USABILITY: 4,
            NFRCategory.MAINTAINABILITY: 4,
            NFRCategory.PORTABILITY: 5,
        }

        return category_priorities.get(category, 3)

    def _generate_tags(
        self,
        category: NFRCategory,
        metrics: List[QuantitativeMetric]
    ) -> List[str]:
        """Generate tags for the NFR."""
        tags = [category.value]

        for metric in metrics:
            if metric.unit == MetricUnit.PERCENT:
                tags.append("percentage-based")
            if metric.threshold_type == ThresholdType.MAXIMUM:
                tags.append("upper-bound")
            if metric.threshold_type == ThresholdType.MINIMUM:
                tags.append("lower-bound")

        return tags

    def _generate_statistics(
        self,
        detected: List[QuantitativeNFR],
        unquantified: List[str]
    ) -> Dict[str, Any]:
        """Generate statistics about the detection."""
        category_counts = {}
        for nfr in detected:
            cat = nfr.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_detected": len(detected),
            "total_unquantified": len(unquantified),
            "by_category": category_counts,
            "testable_count": sum(1 for n in detected if n.is_testable),
            "avg_metrics_per_nfr": sum(len(n.metrics) for n in detected) / len(detected) if detected else 0,
        }

    def _generate_suggestions(
        self,
        detected: List[QuantitativeNFR],
        unquantified: List[str]
    ) -> List[str]:
        """Generate suggestions for improving NFRs."""
        suggestions = []

        # Unquantified NFRs
        if unquantified:
            suggestions.append(
                f"Add specific metrics to {len(unquantified)} unquantified NFR(s) for testability"
            )

        # Missing categories
        detected_categories = {n.category for n in detected}
        important_missing = {NFRCategory.SECURITY, NFRCategory.PERFORMANCE, NFRCategory.AVAILABILITY}
        missing = important_missing - detected_categories
        if missing:
            suggestions.append(
                f"Consider adding NFRs for: {', '.join(m.value for m in missing)}"
            )

        # Low confidence metrics
        low_conf = [n for n in detected if any(m.confidence < 0.7 for m in n.metrics)]
        if low_conf:
            suggestions.append(
                f"Review {len(low_conf)} NFR(s) with low-confidence metrics"
            )

        return suggestions


# Convenience functions
def detect_nfrs(text: str) -> List[QuantitativeNFR]:
    """
    Detect quantitative NFRs in text.

    Args:
        text: Text to analyze

    Returns:
        List of detected QuantitativeNFR objects
    """
    detector = QuantitativeNFRDetector()
    return detector.detect(text).detected_nfrs


def extract_metrics(text: str) -> List[QuantitativeMetric]:
    """
    Extract all quantitative metrics from text.

    Args:
        text: Text to analyze

    Returns:
        List of QuantitativeMetric objects
    """
    detector = QuantitativeNFRDetector()
    result = detector.detect(text)

    metrics = []
    for nfr in result.detected_nfrs:
        metrics.extend(nfr.metrics)
    return metrics


def has_quantitative_nfrs(text: str) -> bool:
    """
    Check if text contains quantitative NFRs.

    Args:
        text: Text to analyze

    Returns:
        True if quantitative NFRs found
    """
    return len(detect_nfrs(text)) > 0
