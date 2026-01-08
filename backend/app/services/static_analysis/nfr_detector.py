# backend/app/services/static_analysis/nfr_detector.py
"""
NFR Detector - Detects Non-Functional Requirements patterns in code.

Categories:
- Security: Authentication, authorization, encryption, input validation
- Performance: Caching, pagination, async operations, indexing
- Reliability: Error handling, retries, circuit breakers, health checks
- Maintainability: Logging, documentation, modularity, testing
- Scalability: Message queues, partitioning, load balancing
- Usability: Accessibility patterns, i18n, user feedback
- Accessibility: WCAG compliance patterns

Part of Fase 15: Hybrid Static-LLM Extraction Pipeline
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class NFRCategory(Enum):
    """Categories of non-functional requirements."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    SCALABILITY = "scalability"
    USABILITY = "usability"
    ACCESSIBILITY = "accessibility"


@dataclass
class NFRDetection:
    """A detected NFR pattern."""
    id: str
    category: NFRCategory
    pattern_matched: str
    source_file: str
    source_line: int
    code_snippet: str
    confidence: float
    description: str
    recommendation: Optional[str] = None
    compliance_relevance: List[str] = field(default_factory=list)


@dataclass
class NFRReport:
    """Report of all NFR detections."""
    detections: List[NFRDetection]
    by_category: Dict[NFRCategory, List[NFRDetection]]
    coverage_score: float  # 0.0 - 1.0, how well NFRs are addressed
    gaps: List[str]        # Categories with no detections


class NFRDetector:
    """
    Detects Non-Functional Requirements patterns in code.

    Categories:
    - Security: Authentication, authorization, encryption, input validation
    - Performance: Caching, pagination, async operations, indexing
    - Reliability: Error handling, retries, circuit breakers, health checks
    - Maintainability: Logging, documentation, modularity, testing
    - Scalability: Message queues, partitioning, load balancing
    - Usability: User feedback, i18n support
    - Accessibility: WCAG compliance patterns
    """

    NFR_PATTERNS = {
        NFRCategory.SECURITY: {
            "patterns": [
                # Credential handling
                (r'(?:password|secret|api_key|token|credentials?)\s*=\s*["\'][^"\']+["\']', "Hardcoded credential detected - SECURITY RISK", 0.95),
                (r'(?:password|secret|api_key|token)\s*=\s*os\.(?:environ|getenv)', "Credential from environment - GOOD", 0.85),
                # Authentication
                (r'@(?:login_required|authenticated|require_auth)', "Authentication decorator", 0.9),
                (r'\.(?:authenticate|login|verify_password)\(', "Authentication check", 0.85),
                (r'JWT|JsonWebToken|bearer\s+token', "JWT authentication", 0.85),
                # Encryption
                (r'\.(?:encrypt|decrypt)\(', "Encryption/decryption used", 0.85),
                (r'(?:AES|RSA|Fernet|bcrypt|argon2|pbkdf2)', "Cryptographic algorithm", 0.9),
                (r'hash(?:lib)?\.(?:sha256|sha512|md5)', "Hashing used", 0.8),
                # Input validation
                (r'(?:sanitize|escape|validate)_?(?:input|html|sql|query)', "Input sanitization", 0.9),
                (r'html\.escape|bleach\.clean|markupsafe', "XSS prevention", 0.9),
                (r'sqlalchemy|prepared_statement|parameterized', "SQL injection prevention", 0.85),
                # Security headers
                (r'Content-Security-Policy|X-Frame-Options|X-XSS-Protection', "Security headers", 0.85),
                (r'X-Content-Type-Options|Strict-Transport-Security', "Security headers", 0.85),
                # CSRF
                (r'(?:csrf|CSRF)_(?:token|protect|exempt)', "CSRF protection", 0.9),
                (r'@csrf_protect|csrf_token', "CSRF token", 0.9),
                # Rate limiting
                (r'rate_limit|throttle|RateLimiter', "Rate limiting", 0.85),
                (r'@ratelimit|@throttle', "Rate limit decorator", 0.9),
                # SSL/TLS
                (r'ssl_context|verify_ssl|https_only|HTTPS', "SSL/TLS configuration", 0.85),
                (r'certifi|ssl\.create_default_context', "SSL certificate handling", 0.8),
            ],
            "compliance": ["NEN7510", "ISO27001", "SOC2", "PCI_DSS"],
        },
        NFRCategory.PERFORMANCE: {
            "patterns": [
                # Caching
                (r'@cache|\.cache\(|lru_cache|memoize', "Caching implementation", 0.9),
                (r'redis|memcached|functools\.cache', "Cache backend", 0.85),
                (r'cache_timeout|cache_key|invalidate_cache', "Cache management", 0.8),
                # Pagination
                (r'pagination|paginate|page_size|per_page', "Pagination", 0.85),
                (r'limit\s*=\s*\d+|offset\s*=', "Limit/offset pagination", 0.8),
                (r'cursor_pagination|keyset_pagination', "Cursor pagination", 0.85),
                # Async operations
                (r'async\s+def|await\s+', "Async/await pattern", 0.8),
                (r'asyncio\.|aiohttp|aiofiles', "Async libraries", 0.85),
                (r'Promise|async\s*\(|\.then\(', "Promise/async (JS)", 0.8),
                # Database optimization
                (r'(?:db_)?index|create_index|add_index|Index\(', "Database indexing", 0.85),
                (r'select_related|prefetch_related', "N+1 query prevention", 0.9),
                (r'bulk_(?:create|update|insert)|batch_', "Bulk operations", 0.85),
                (r'\.only\(|\.defer\(|lazy_load', "Lazy loading", 0.8),
                # Connection management
                (r'connection_pool|pool_size|max_connections', "Connection pooling", 0.85),
                (r'(?:response_)?timeout\s*=', "Timeout configuration", 0.8),
                # Query optimization
                (r'EXPLAIN\s+ANALYZE|query_plan', "Query analysis", 0.9),
                (r'\.values\(|\.values_list\(', "Query optimization", 0.75),
            ],
            "compliance": [],
        },
        NFRCategory.RELIABILITY: {
            "patterns": [
                # Error handling
                (r'try\s*:|except\s+\w+', "Exception handling", 0.7),
                (r'except\s+(?:Exception|BaseException)\s*:', "Broad exception catch - review", 0.6),
                (r'finally\s*:', "Cleanup handling", 0.75),
                (r'raise\s+\w+Error', "Custom exceptions", 0.8),
                # Retry mechanisms
                (r'@retry|retry_on_|max_retries|Retry\(', "Retry mechanism", 0.9),
                (r'backoff|exponential_backoff', "Backoff strategy", 0.9),
                (r'tenacity|retrying\.retry', "Retry library", 0.9),
                # Circuit breakers
                (r'circuit_breaker|CircuitBreaker|pybreaker', "Circuit breaker pattern", 0.95),
                (r'fallback|degraded_mode', "Fallback mechanism", 0.85),
                # Health checks
                (r'health_check|healthz|ready|liveness', "Health check endpoint", 0.9),
                (r'/health|/ready|/alive', "Health endpoint", 0.85),
                # Transaction management
                (r'@transactional|with\s+transaction|atomic', "Transaction management", 0.85),
                (r'commit\(\)|rollback\(\)', "Transaction control", 0.8),
                # Data integrity
                (r'backup|recover|rollback_to', "Backup/recovery", 0.8),
                (r'checksum|integrity_check|validate_data', "Data integrity", 0.85),
                # Fault tolerance
                (r'failover|fallback|redundan', "Failover/redundancy", 0.85),
                (r'dead_letter|dlq|error_queue', "Dead letter queue", 0.9),
                (r'idempoten', "Idempotency", 0.9),
            ],
            "compliance": [],
        },
        NFRCategory.MAINTAINABILITY: {
            "patterns": [
                # Logging
                (r'logger\.|logging\.|log\.(debug|info|warning|error|critical)', "Logging implementation", 0.85),
                (r'structlog|loguru', "Structured logging", 0.9),
                (r'audit_log|access_log', "Audit logging", 0.9),
                # Documentation
                (r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', "Docstring present", 0.7),
                (r'@param|@return|@type|:param|:return:', "Parameter documentation", 0.75),
                (r'# TODO|# FIXME|# XXX|# HACK', "Technical debt marker", 0.8),
                # Testing
                (r'def\s+test_|class\s+Test|@pytest|unittest', "Unit tests", 0.9),
                (r'mock\.|patch\.|MagicMock', "Mocking", 0.85),
                (r'fixture|@pytest\.fixture', "Test fixtures", 0.85),
                (r'assert_|assertEqual|assertTrue', "Assertions", 0.8),
                # Code structure
                (r'@dataclass|@attr\.s|NamedTuple|TypedDict', "Structured data classes", 0.75),
                (r'from\s+abc\s+import|ABC,?\s*abstractmethod', "Abstract interfaces", 0.8),
                (r'Protocol\[|typing\.Protocol', "Protocol classes", 0.85),
                # Configuration
                (r'config\.|settings\.|\.env|environ\[', "Configuration externalized", 0.8),
                (r'pydantic\.BaseSettings|dynaconf', "Configuration library", 0.85),
                # Type hints
                (r':\s*(?:str|int|float|bool|List|Dict|Optional|Union)\b', "Type annotations", 0.75),
                (r'->\s*(?:str|int|float|bool|List|Dict|Optional|None)\b', "Return type hints", 0.75),
                # Dependency injection
                (r'@inject|Depends\(|dependency_injection', "Dependency injection", 0.85),
            ],
            "compliance": [],
        },
        NFRCategory.SCALABILITY: {
            "patterns": [
                # Message queues
                (r'celery|rabbitmq|kafka|redis\..*queue', "Message queue", 0.9),
                (r'\.delay\(|\.apply_async\(|@task', "Async task queue", 0.9),
                (r'producer|consumer|broker', "Message broker patterns", 0.8),
                # Data partitioning
                (r'shard|partition|replica', "Data partitioning", 0.9),
                (r'sharding_key|partition_by', "Partitioning config", 0.85),
                # Load balancing
                (r'load_balanc|round_robin|least_conn', "Load balancing", 0.9),
                (r'nginx|haproxy|traefik', "Load balancer", 0.85),
                # Stateless design
                (r'stateless|session_store|external_session', "Stateless design", 0.85),
                (r'redis_session|memcached_session', "External session store", 0.9),
                # Horizontal scaling
                (r'horizontal_scal|auto_scal|scale_out', "Horizontal scaling", 0.9),
                (r'kubernetes|k8s|docker_swarm|ecs', "Container orchestration", 0.85),
                (r'replica_count|replicas\s*:', "Replica configuration", 0.85),
                # Distributed systems
                (r'distributed_lock|consul|etcd|zookeeper', "Distributed coordination", 0.9),
                (r'service_discovery|service_mesh', "Service discovery", 0.85),
            ],
            "compliance": [],
        },
        NFRCategory.USABILITY: {
            "patterns": [
                # User feedback
                (r'toast|notification|alert|snackbar', "User notifications", 0.8),
                (r'loading|spinner|progress', "Loading indicators", 0.75),
                (r'error_message|success_message|feedback', "User feedback", 0.8),
                # Internationalization
                (r'i18n|gettext|_\(|ngettext', "Internationalization", 0.9),
                (r'locale|language|translation', "Localization support", 0.85),
                (r'datetime\.strftime|date_format', "Date formatting", 0.75),
                # Form handling
                (r'validation_error|form_error|field_error', "Form validation feedback", 0.8),
                (r'placeholder|hint|helper_text', "Input hints", 0.75),
                # Navigation
                (r'breadcrumb|navigation|menu', "Navigation patterns", 0.7),
                (r'redirect|router|navigate', "Routing", 0.7),
            ],
            "compliance": [],
        },
        NFRCategory.ACCESSIBILITY: {
            "patterns": [
                # ARIA
                (r'aria-|role=|tabindex', "ARIA attributes", 0.9),
                (r'aria-label|aria-describedby|aria-hidden', "ARIA labels", 0.9),
                # Semantic HTML
                (r'<(main|nav|header|footer|article|section|aside)[\s>]', "Semantic HTML", 0.85),
                (r'<(h[1-6])[\s>]', "Heading hierarchy", 0.8),
                # Alt text
                (r'alt=|alt_text|image_alt', "Alt text for images", 0.9),
                # Keyboard navigation
                (r'onkeydown|onkeyup|onkeypress|tabIndex', "Keyboard handling", 0.85),
                (r'focus_trap|focus_management', "Focus management", 0.9),
                # Screen reader
                (r'screen_reader|sr-only|visually-hidden', "Screen reader support", 0.9),
                # Color contrast
                (r'contrast|color_ratio', "Color contrast consideration", 0.8),
            ],
            "compliance": ["WCAG"],
        },
    }

    def __init__(self):
        self._detection_counter = 0
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        self.compiled_patterns: Dict[NFRCategory, List[Tuple[re.Pattern, str, float]]] = {}
        for category, config in self.NFR_PATTERNS.items():
            self.compiled_patterns[category] = [
                (re.compile(pattern, re.IGNORECASE | re.MULTILINE), desc, conf)
                for pattern, desc, conf in config["patterns"]
            ]

    async def detect_in_file(self,
                              file_path: str,
                              source: str) -> List[NFRDetection]:
        """Detect NFR patterns in a single file."""
        detections = []
        lines = source.split('\n')

        for category, patterns in self.compiled_patterns.items():
            compliance = self.NFR_PATTERNS[category].get("compliance", [])

            for pattern, description, confidence in patterns:
                for match in pattern.finditer(source):
                    # Find line number
                    line_num = source[:match.start()].count('\n') + 1

                    # Get code snippet (context around match)
                    start_line = max(0, line_num - 2)
                    end_line = min(len(lines), line_num + 2)
                    snippet = '\n'.join(lines[start_line:end_line])

                    self._detection_counter += 1

                    detections.append(NFRDetection(
                        id=f"NFR-{self._detection_counter:04d}",
                        category=category,
                        pattern_matched=match.group(0)[:100],
                        source_file=file_path,
                        source_line=line_num,
                        code_snippet=snippet[:500],
                        confidence=confidence,
                        description=description,
                        compliance_relevance=compliance,
                        recommendation=self._get_recommendation(category, description)
                    ))

        return detections

    async def detect_all(self,
                         files: Dict[str, str]) -> NFRReport:
        """Detect NFR patterns across all files."""
        all_detections = []

        for file_path, source in files.items():
            try:
                detections = await self.detect_in_file(file_path, source)
                all_detections.extend(detections)
            except Exception as e:
                logger.warning(f"Error detecting NFRs in {file_path}: {e}")
                continue

        # Organize by category
        by_category: Dict[NFRCategory, List[NFRDetection]] = {}
        for detection in all_detections:
            by_category.setdefault(detection.category, []).append(detection)

        # Find gaps (categories with no detections)
        all_categories = set(NFRCategory)
        detected_categories = set(by_category.keys())
        gaps = [cat.value for cat in (all_categories - detected_categories)]

        # Calculate coverage score
        coverage = len(detected_categories) / len(all_categories)

        return NFRReport(
            detections=all_detections,
            by_category=by_category,
            coverage_score=coverage,
            gaps=gaps
        )

    def _get_recommendation(self, category: NFRCategory, description: str) -> Optional[str]:
        """Get recommendation based on detection."""
        recommendations = {
            "Hardcoded credential detected": "Move credentials to environment variables or secrets manager",
            "Broad exception catch": "Catch specific exceptions to avoid masking errors",
            "Technical debt marker": "Create a ticket to address this technical debt",
            "Authentication decorator": "Ensure all protected endpoints have this decorator",
            "Caching implementation": "Monitor cache hit rates and invalidation",
            "Database indexing": "Verify index is used by query planner",
        }

        for key, rec in recommendations.items():
            if key.lower() in description.lower():
                return rec
        return None

    def get_recommendations(self, report: NFRReport) -> List[str]:
        """Generate recommendations based on NFR gaps."""
        recommendations = []

        gap_recommendations = {
            "security": "Consider adding authentication, input validation, and encryption",
            "performance": "Consider adding caching, pagination, and async operations",
            "reliability": "Consider adding error handling, retries, and health checks",
            "maintainability": "Consider adding logging, documentation, and unit tests",
            "scalability": "Consider adding message queues and stateless design",
            "usability": "Consider adding user feedback and internationalization",
            "accessibility": "Consider adding ARIA labels and keyboard navigation",
        }

        for gap in report.gaps:
            if gap in gap_recommendations:
                recommendations.append(gap_recommendations[gap])

        return recommendations

    def get_summary(self, report: NFRReport) -> Dict:
        """Get summary statistics from NFR report."""
        return {
            "total_detections": len(report.detections),
            "coverage_score": round(report.coverage_score, 2),
            "categories_covered": len(report.by_category),
            "categories_missing": report.gaps,
            "by_category": {
                cat.value: len(dets) for cat, dets in report.by_category.items()
            },
            "high_confidence_count": sum(
                1 for d in report.detections if d.confidence >= 0.85
            ),
            "compliance_relevant": sum(
                1 for d in report.detections if d.compliance_relevance
            ),
        }
