"""
API Inventory Models - Fase 26: Migration Execution (Week 140-141)

Dataclasses for API endpoint extraction and external API detection.

Author: Claude Code (Week 140 - Fase 26)
Date: 2026-01-01
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class HTTPMethod(Enum):
    """HTTP methods for API endpoints."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ParameterLocation(Enum):
    """Location of API parameters."""
    PATH = "path"
    QUERY = "query"
    BODY = "body"
    HEADER = "header"
    COOKIE = "cookie"


class AuthType(Enum):
    """Authentication types for APIs."""
    NONE = "none"
    BASIC = "basic"
    JWT = "jwt"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    SESSION = "session"
    BEARER = "bearer"
    CUSTOM = "custom"


class APIType(Enum):
    """Type of API (internal or external)."""
    INTERNAL = "internal"      # Defined in codebase (routes)
    EXTERNAL = "external"      # Called from codebase (http calls)
    WEBHOOK = "webhook"        # Incoming webhooks


class APIFramework(Enum):
    """Detected web framework."""
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO = "django"
    EXPRESS = "express"
    NESTJS = "nestjs"
    ASPNET = "aspnet"
    ASPNET_CORE = "aspnet_core"
    SPRING = "spring"
    LARAVEL = "laravel"
    RAILS = "rails"
    GIN = "gin"
    ACTIX = "actix"
    UNKNOWN = "unknown"


@dataclass
class Parameter:
    """API parameter definition."""
    name: str
    location: ParameterLocation
    type_hint: Optional[str] = None
    required: bool = True
    default_value: Optional[str] = None
    description: Optional[str] = None
    example: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "location": self.location.value,
            "type_hint": self.type_hint,
            "required": self.required,
            "default_value": self.default_value,
            "description": self.description,
            "example": self.example,
        }


@dataclass
class Endpoint:
    """Internal API endpoint extracted from source code."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    path: str = ""                              # "/users/{id}"
    methods: List[HTTPMethod] = field(default_factory=list)  # [GET, PUT]
    handler_function: str = ""                  # "get_user"
    handler_class: Optional[str] = None         # "UserController"
    source_file: str = ""
    source_line_start: int = 0
    source_line_end: int = 0
    parameters: List[Parameter] = field(default_factory=list)
    request_body_type: Optional[str] = None     # "UserCreate"
    response_type: Optional[str] = None         # "User"
    response_status_codes: List[int] = field(default_factory=lambda: [200])
    authentication: AuthType = AuthType.NONE
    required_roles: List[str] = field(default_factory=list)  # ["admin", "user"]
    rate_limited: bool = False
    deprecated: bool = False
    documentation: Optional[str] = None         # Extracted docstring
    tags: List[str] = field(default_factory=list)
    business_rules: List[str] = field(default_factory=list)  # ["BR-0001", "BR-0002"]
    framework: APIFramework = APIFramework.UNKNOWN
    confidence: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "methods": [m.value for m in self.methods],
            "handler_function": self.handler_function,
            "handler_class": self.handler_class,
            "source_file": self.source_file,
            "source_line_start": self.source_line_start,
            "source_line_end": self.source_line_end,
            "parameters": [p.to_dict() for p in self.parameters],
            "request_body_type": self.request_body_type,
            "response_type": self.response_type,
            "response_status_codes": self.response_status_codes,
            "authentication": self.authentication.value,
            "required_roles": self.required_roles,
            "rate_limited": self.rate_limited,
            "deprecated": self.deprecated,
            "documentation": self.documentation,
            "tags": self.tags,
            "business_rules": self.business_rules,
            "framework": self.framework.value,
            "confidence": self.confidence,
        }


@dataclass
class ExternalAPICall:
    """A specific call to an external API."""
    url: str
    method: HTTPMethod
    source_file: str
    source_line: int
    function_name: Optional[str] = None
    class_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "method": self.method.value,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "function_name": self.function_name,
            "class_name": self.class_name,
        }


@dataclass
class ExternalAPI:
    """External API detected in source code (outbound calls)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""                              # "Stripe", "SendGrid", "api.weather.com"
    base_url: Optional[str] = None              # "https://api.stripe.com"
    detected_domain: str = ""                   # "api.stripe.com"
    endpoints_called: List[str] = field(default_factory=list)  # ["/v1/charges", "/v1/customers"]
    call_locations: List[ExternalAPICall] = field(default_factory=list)
    http_methods: List[HTTPMethod] = field(default_factory=list)
    auth_method: AuthType = AuthType.NONE
    business_rules: List[str] = field(default_factory=list)
    criticality: str = "required"               # required, optional, deprecated
    category: str = "unknown"                   # payment, email, analytics, etc.
    confidence: float = 0.7

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "detected_domain": self.detected_domain,
            "endpoints_called": self.endpoints_called,
            "call_locations": [c.to_dict() for c in self.call_locations],
            "http_methods": [m.value for m in self.http_methods],
            "auth_method": self.auth_method.value,
            "business_rules": self.business_rules,
            "criticality": self.criticality,
            "category": self.category,
            "confidence": self.confidence,
        }


@dataclass
class FrameworkDetection:
    """Detected web framework in the project."""
    framework: APIFramework
    confidence: float
    detection_file: str
    detection_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "framework": self.framework.value,
            "confidence": self.confidence,
            "detection_file": self.detection_file,
            "detection_patterns": self.detection_patterns,
        }


@dataclass
class APIInventorySession:
    """Session for API inventory extraction."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    name: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    status: str = "created"  # created, scanning, completed, error
    error_message: Optional[str] = None


@dataclass
class APIInventoryResult:
    """Complete result of API inventory extraction."""
    session_id: str
    project_id: str
    scan_date: datetime = field(default_factory=lambda: datetime.utcnow())
    internal_endpoints: List[Endpoint] = field(default_factory=list)
    external_apis: List[ExternalAPI] = field(default_factory=list)
    frameworks_detected: List[FrameworkDetection] = field(default_factory=list)
    total_internal: int = 0
    total_external: int = 0
    languages_scanned: List[str] = field(default_factory=list)
    files_scanned: int = 0
    scan_duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Update totals after initialization."""
        self.total_internal = len(self.internal_endpoints)
        self.total_external = len(self.external_apis)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "scan_date": self.scan_date.isoformat(),
            "summary": {
                "internal_endpoints": self.total_internal,
                "external_apis": self.total_external,
                "frameworks": [f.to_dict() for f in self.frameworks_detected],
                "languages": self.languages_scanned,
                "files_scanned": self.files_scanned,
                "scan_duration_seconds": self.scan_duration_seconds,
            },
            "internal_endpoints": [e.to_dict() for e in self.internal_endpoints],
            "external_apis": [a.to_dict() for a in self.external_apis],
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def get_endpoints_by_method(self, method: HTTPMethod) -> List[Endpoint]:
        """Filter endpoints by HTTP method."""
        return [e for e in self.internal_endpoints if method in e.methods]

    def get_endpoints_by_path(self, path_contains: str) -> List[Endpoint]:
        """Filter endpoints by path substring."""
        return [e for e in self.internal_endpoints if path_contains in e.path]

    def get_external_by_domain(self, domain: str) -> List[ExternalAPI]:
        """Filter external APIs by domain."""
        return [a for a in self.external_apis if domain in a.detected_domain]

    def get_endpoints_requiring_auth(self) -> List[Endpoint]:
        """Get all endpoints that require authentication."""
        return [e for e in self.internal_endpoints if e.authentication != AuthType.NONE]

    def get_deprecated_endpoints(self) -> List[Endpoint]:
        """Get all deprecated endpoints."""
        return [e for e in self.internal_endpoints if e.deprecated]


# Well-known external API categorization
KNOWN_API_CATEGORIES: Dict[str, str] = {
    # Payment
    "stripe.com": "payment",
    "paypal.com": "payment",
    "braintree.com": "payment",
    "square.com": "payment",
    "adyen.com": "payment",

    # Email
    "sendgrid.com": "email",
    "mailchimp.com": "email",
    "mailgun.com": "email",
    "postmarkapp.com": "email",
    "ses.amazonaws.com": "email",

    # SMS
    "twilio.com": "sms",
    "messagebird.com": "sms",
    "nexmo.com": "sms",

    # Storage
    "s3.amazonaws.com": "storage",
    "storage.googleapis.com": "storage",
    "blob.core.windows.net": "storage",

    # Analytics
    "google-analytics.com": "analytics",
    "mixpanel.com": "analytics",
    "segment.com": "analytics",
    "amplitude.com": "analytics",

    # Auth
    "auth0.com": "auth",
    "okta.com": "auth",
    "cognito": "auth",

    # Maps
    "maps.googleapis.com": "maps",
    "api.mapbox.com": "maps",

    # Social
    "graph.facebook.com": "social",
    "api.twitter.com": "social",
    "api.linkedin.com": "social",

    # AI/ML
    "api.openai.com": "ai",
    "api.anthropic.com": "ai",
    "generativelanguage.googleapis.com": "ai",
}


def categorize_external_api(domain: str) -> str:
    """Categorize an external API by its domain."""
    domain_lower = domain.lower()
    for known_domain, category in KNOWN_API_CATEGORIES.items():
        if known_domain in domain_lower:
            return category
    return "unknown"
