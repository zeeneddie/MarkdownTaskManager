"""
G3: API Gateway Templates

REST facade templates voor legacy systemen met standaard patterns
voor authentication, rate limiting en caching.

Template Types:
1. Simple Proxy - Direct doorsturen
2. Aggregator - Meerdere legacy calls combineren
3. Transformer - Request/response transformatie
4. Cached - Met caching layer
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import UUID, uuid4
import json
import re


class GatewayTemplateType(str, Enum):
    """Types of API Gateway templates."""
    SIMPLE_PROXY = "simple_proxy"
    AGGREGATOR = "aggregator"
    TRANSFORMER = "transformer"
    CACHED = "cached"


class HttpMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class AuthType(str, Enum):
    """Authentication types."""
    NONE = "none"
    API_KEY = "api_key"
    BASIC = "basic"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    CUSTOM = "custom"


class CacheStrategy(str, Enum):
    """Caching strategies."""
    NO_CACHE = "no_cache"
    TTL = "ttl"  # Time-to-live based
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"
    CACHE_FIRST = "cache_first"
    NETWORK_FIRST = "network_first"


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""
    NONE = "none"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


# ============================================================================
# Configuration Components
# ============================================================================

@dataclass
class AuthConfig:
    """Authentication configuration."""
    auth_type: AuthType
    api_key_header: str = "X-API-Key"
    api_key_query_param: str = "api_key"
    bearer_header: str = "Authorization"
    basic_header: str = "Authorization"
    oauth2_token_url: str = ""
    oauth2_client_id: str = ""
    oauth2_scope: str = ""
    custom_header: str = ""
    custom_validator: Optional[str] = None  # Function name for custom validation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "auth_type": self.auth_type.value,
            "api_key_header": self.api_key_header,
            "api_key_query_param": self.api_key_query_param,
            "bearer_header": self.bearer_header,
            "oauth2_token_url": self.oauth2_token_url,
            "oauth2_client_id": self.oauth2_client_id,
            "oauth2_scope": self.oauth2_scope,
            "custom_header": self.custom_header
        }


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    strategy: RateLimitStrategy
    requests_per_second: int = 100
    requests_per_minute: int = 1000
    burst_size: int = 50
    window_size_seconds: int = 60
    key_by: str = "ip"  # ip, api_key, user_id, custom

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "requests_per_second": self.requests_per_second,
            "requests_per_minute": self.requests_per_minute,
            "burst_size": self.burst_size,
            "window_size_seconds": self.window_size_seconds,
            "key_by": self.key_by
        }


@dataclass
class CacheConfig:
    """Caching configuration."""
    strategy: CacheStrategy
    ttl_seconds: int = 300  # 5 minutes default
    stale_ttl_seconds: int = 60  # How long stale content can be served
    cache_key_pattern: str = "{method}:{path}:{query}"
    vary_by_headers: List[str] = field(default_factory=list)
    exclude_paths: List[str] = field(default_factory=list)
    include_query_params: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "ttl_seconds": self.ttl_seconds,
            "stale_ttl_seconds": self.stale_ttl_seconds,
            "cache_key_pattern": self.cache_key_pattern,
            "vary_by_headers": self.vary_by_headers,
            "exclude_paths": self.exclude_paths,
            "include_query_params": self.include_query_params
        }


@dataclass
class TimeoutConfig:
    """Timeout configuration."""
    connect_timeout_ms: int = 5000
    read_timeout_ms: int = 30000
    write_timeout_ms: int = 30000
    total_timeout_ms: int = 60000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connect_timeout_ms": self.connect_timeout_ms,
            "read_timeout_ms": self.read_timeout_ms,
            "write_timeout_ms": self.write_timeout_ms,
            "total_timeout_ms": self.total_timeout_ms
        }


@dataclass
class RetryConfig:
    """Retry configuration."""
    enabled: bool = True
    max_retries: int = 3
    initial_delay_ms: int = 100
    max_delay_ms: int = 5000
    exponential_backoff: bool = True
    retry_on_status_codes: List[int] = field(default_factory=lambda: [502, 503, 504])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_retries": self.max_retries,
            "initial_delay_ms": self.initial_delay_ms,
            "max_delay_ms": self.max_delay_ms,
            "exponential_backoff": self.exponential_backoff,
            "retry_on_status_codes": self.retry_on_status_codes
        }


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    enabled: bool = True
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 30
    half_open_max_calls: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "timeout_seconds": self.timeout_seconds,
            "half_open_max_calls": self.half_open_max_calls
        }


# ============================================================================
# Transformation Components
# ============================================================================

@dataclass
class HeaderTransform:
    """Header transformation rule."""
    action: str  # add, remove, rename, set
    source: str  # Header name to transform
    target: Optional[str] = None  # New header name (for rename/add)
    value: Optional[str] = None  # Value (for add/set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "source": self.source,
            "target": self.target,
            "value": self.value
        }


@dataclass
class BodyTransform:
    """Body transformation rule."""
    source_path: str  # JSONPath or XPath to source field
    target_path: str  # JSONPath to target field
    transform: Optional[str] = None  # Transform function name
    default_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": self.source_path,
            "target_path": self.target_path,
            "transform": self.transform,
            "default_value": self.default_value
        }


@dataclass
class PathTransform:
    """URL path transformation."""
    pattern: str  # Regex pattern to match
    replacement: str  # Replacement pattern with groups

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern,
            "replacement": self.replacement
        }


@dataclass
class TransformConfig:
    """Complete transformation configuration."""
    request_headers: List[HeaderTransform] = field(default_factory=list)
    response_headers: List[HeaderTransform] = field(default_factory=list)
    request_body: List[BodyTransform] = field(default_factory=list)
    response_body: List[BodyTransform] = field(default_factory=list)
    path_transforms: List[PathTransform] = field(default_factory=list)
    strip_prefix: Optional[str] = None  # Remove prefix from path
    add_prefix: Optional[str] = None  # Add prefix to path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_headers": [h.to_dict() for h in self.request_headers],
            "response_headers": [h.to_dict() for h in self.response_headers],
            "request_body": [b.to_dict() for b in self.request_body],
            "response_body": [b.to_dict() for b in self.response_body],
            "path_transforms": [p.to_dict() for p in self.path_transforms],
            "strip_prefix": self.strip_prefix,
            "add_prefix": self.add_prefix
        }


# ============================================================================
# Gateway Route & Endpoint
# ============================================================================

@dataclass
class LegacyEndpoint:
    """Legacy system endpoint definition."""
    base_url: str
    path: str
    method: HttpMethod
    auth: Optional[AuthConfig] = None
    timeout: Optional[TimeoutConfig] = None
    headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "path": self.path,
            "method": self.method.value,
            "auth": self.auth.to_dict() if self.auth else None,
            "timeout": self.timeout.to_dict() if self.timeout else None,
            "headers": self.headers
        }


@dataclass
class GatewayRoute:
    """A single gateway route configuration."""
    id: UUID
    name: str
    description: str

    # Incoming request matching
    path_pattern: str  # e.g., /api/v1/users/{id}
    methods: List[HttpMethod]

    # Outgoing to legacy
    legacy_endpoint: LegacyEndpoint

    # Optional features
    auth: Optional[AuthConfig] = None
    rate_limit: Optional[RateLimitConfig] = None
    cache: Optional[CacheConfig] = None
    transform: Optional[TransformConfig] = None
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    retry: Optional[RetryConfig] = None

    # Metadata
    enabled: bool = True
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "path_pattern": self.path_pattern,
            "methods": [m.value for m in self.methods],
            "legacy_endpoint": self.legacy_endpoint.to_dict(),
            "auth": self.auth.to_dict() if self.auth else None,
            "rate_limit": self.rate_limit.to_dict() if self.rate_limit else None,
            "cache": self.cache.to_dict() if self.cache else None,
            "transform": self.transform.to_dict() if self.transform else None,
            "circuit_breaker": self.circuit_breaker.to_dict() if self.circuit_breaker else None,
            "retry": self.retry.to_dict() if self.retry else None,
            "enabled": self.enabled,
            "tags": self.tags
        }


# ============================================================================
# Aggregator Components
# ============================================================================

@dataclass
class AggregatorStep:
    """A step in an aggregation pipeline."""
    id: str
    name: str
    legacy_endpoint: LegacyEndpoint
    depends_on: List[str] = field(default_factory=list)  # IDs of steps this depends on
    extract_to: str = ""  # JSONPath where to place result in response
    condition: Optional[str] = None  # Condition expression for conditional execution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "legacy_endpoint": self.legacy_endpoint.to_dict(),
            "depends_on": self.depends_on,
            "extract_to": self.extract_to,
            "condition": self.condition
        }


@dataclass
class AggregatorConfig:
    """Configuration for aggregator template."""
    steps: List[AggregatorStep]
    parallel_execution: bool = True  # Execute independent steps in parallel
    fail_fast: bool = True  # Stop on first failure
    timeout_ms: int = 30000
    response_template: Optional[str] = None  # JSON template for response assembly

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": [s.to_dict() for s in self.steps],
            "parallel_execution": self.parallel_execution,
            "fail_fast": self.fail_fast,
            "timeout_ms": self.timeout_ms,
            "response_template": self.response_template
        }


# ============================================================================
# Gateway Templates
# ============================================================================

@dataclass
class GatewayTemplate:
    """Complete API Gateway template configuration."""
    id: UUID
    name: str
    description: str
    template_type: GatewayTemplateType
    version: str

    # Routes for simple proxy/transformer/cached
    routes: List[GatewayRoute] = field(default_factory=list)

    # Aggregator config (for aggregator type)
    aggregator: Optional[AggregatorConfig] = None

    # Global settings
    global_auth: Optional[AuthConfig] = None
    global_rate_limit: Optional[RateLimitConfig] = None
    global_cache: Optional[CacheConfig] = None
    global_timeout: Optional[TimeoutConfig] = None
    global_circuit_breaker: Optional[CircuitBreakerConfig] = None

    # CORS settings
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_headers: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization"])

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type.value,
            "version": self.version,
            "routes": [r.to_dict() for r in self.routes],
            "aggregator": self.aggregator.to_dict() if self.aggregator else None,
            "global_auth": self.global_auth.to_dict() if self.global_auth else None,
            "global_rate_limit": self.global_rate_limit.to_dict() if self.global_rate_limit else None,
            "global_cache": self.global_cache.to_dict() if self.global_cache else None,
            "global_timeout": self.global_timeout.to_dict() if self.global_timeout else None,
            "global_circuit_breaker": self.global_circuit_breaker.to_dict() if self.global_circuit_breaker else None,
            "cors": {
                "enabled": self.cors_enabled,
                "origins": self.cors_origins,
                "methods": self.cors_methods,
                "headers": self.cors_headers
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags
        }


# ============================================================================
# Service
# ============================================================================

class APIGatewayTemplateService:
    """
    Service voor het genereren van API Gateway templates.

    Template Types:
    1. Simple Proxy - Direct forwarding met auth/rate limiting
    2. Aggregator - Combine multiple legacy calls
    3. Transformer - Request/response transformation
    4. Cached - Add caching layer to legacy endpoints
    """

    def __init__(self):
        self._templates: Dict[UUID, GatewayTemplate] = {}

    # =========================================================================
    # Template Creation
    # =========================================================================

    def create_simple_proxy(
        self,
        name: str,
        description: str,
        legacy_base_url: str,
        routes: List[Dict[str, Any]],
        auth: Optional[AuthConfig] = None,
        rate_limit: Optional[RateLimitConfig] = None
    ) -> GatewayTemplate:
        """
        Create a simple proxy template.

        Simple proxy forwards requests directly to legacy with minimal transformation.
        """
        gateway_routes = []
        for route in routes:
            gateway_routes.append(GatewayRoute(
                id=uuid4(),
                name=route.get("name", ""),
                description=route.get("description", ""),
                path_pattern=route["path"],
                methods=[HttpMethod(m) for m in route.get("methods", ["GET"])],
                legacy_endpoint=LegacyEndpoint(
                    base_url=legacy_base_url,
                    path=route.get("legacy_path", route["path"]),
                    method=HttpMethod(route.get("methods", ["GET"])[0])
                ),
                auth=auth,
                rate_limit=rate_limit
            ))

        template = GatewayTemplate(
            id=uuid4(),
            name=name,
            description=description,
            template_type=GatewayTemplateType.SIMPLE_PROXY,
            version="1.0",
            routes=gateway_routes,
            global_auth=auth,
            global_rate_limit=rate_limit
        )

        self._templates[template.id] = template
        return template

    def create_aggregator(
        self,
        name: str,
        description: str,
        path_pattern: str,
        steps: List[Dict[str, Any]],
        response_template: Optional[str] = None
    ) -> GatewayTemplate:
        """
        Create an aggregator template.

        Aggregator combines multiple legacy calls into a single API response.
        """
        aggregator_steps = []
        for step in steps:
            aggregator_steps.append(AggregatorStep(
                id=step["id"],
                name=step.get("name", step["id"]),
                legacy_endpoint=LegacyEndpoint(
                    base_url=step["base_url"],
                    path=step["path"],
                    method=HttpMethod(step.get("method", "GET"))
                ),
                depends_on=step.get("depends_on", []),
                extract_to=step.get("extract_to", f"$.{step['id']}"),
                condition=step.get("condition")
            ))

        template = GatewayTemplate(
            id=uuid4(),
            name=name,
            description=description,
            template_type=GatewayTemplateType.AGGREGATOR,
            version="1.0",
            routes=[GatewayRoute(
                id=uuid4(),
                name=f"{name}_route",
                description=description,
                path_pattern=path_pattern,
                methods=[HttpMethod.GET],
                legacy_endpoint=LegacyEndpoint(
                    base_url="aggregator://",
                    path=path_pattern,
                    method=HttpMethod.GET
                )
            )],
            aggregator=AggregatorConfig(
                steps=aggregator_steps,
                response_template=response_template
            )
        )

        self._templates[template.id] = template
        return template

    def create_transformer(
        self,
        name: str,
        description: str,
        legacy_base_url: str,
        routes: List[Dict[str, Any]],
        default_transform: Optional[TransformConfig] = None
    ) -> GatewayTemplate:
        """
        Create a transformer template.

        Transformer applies request/response transformations.
        """
        gateway_routes = []
        for route in routes:
            # Build transform config for this route
            transform = default_transform or TransformConfig()

            if "request_body_mapping" in route:
                transform.request_body = [
                    BodyTransform(source_path=src, target_path=tgt)
                    for src, tgt in route["request_body_mapping"].items()
                ]

            if "response_body_mapping" in route:
                transform.response_body = [
                    BodyTransform(source_path=src, target_path=tgt)
                    for src, tgt in route["response_body_mapping"].items()
                ]

            gateway_routes.append(GatewayRoute(
                id=uuid4(),
                name=route.get("name", ""),
                description=route.get("description", ""),
                path_pattern=route["path"],
                methods=[HttpMethod(m) for m in route.get("methods", ["GET"])],
                legacy_endpoint=LegacyEndpoint(
                    base_url=legacy_base_url,
                    path=route.get("legacy_path", route["path"]),
                    method=HttpMethod(route.get("methods", ["GET"])[0])
                ),
                transform=transform
            ))

        template = GatewayTemplate(
            id=uuid4(),
            name=name,
            description=description,
            template_type=GatewayTemplateType.TRANSFORMER,
            version="1.0",
            routes=gateway_routes
        )

        self._templates[template.id] = template
        return template

    def create_cached(
        self,
        name: str,
        description: str,
        legacy_base_url: str,
        routes: List[Dict[str, Any]],
        cache_config: Optional[CacheConfig] = None
    ) -> GatewayTemplate:
        """
        Create a cached proxy template.

        Cached proxy adds a caching layer to legacy endpoints.
        """
        default_cache = cache_config or CacheConfig(
            strategy=CacheStrategy.TTL,
            ttl_seconds=300
        )

        gateway_routes = []
        for route in routes:
            route_cache = CacheConfig(
                strategy=CacheStrategy(route.get("cache_strategy", default_cache.strategy.value)),
                ttl_seconds=route.get("ttl_seconds", default_cache.ttl_seconds),
                stale_ttl_seconds=route.get("stale_ttl_seconds", default_cache.stale_ttl_seconds)
            )

            gateway_routes.append(GatewayRoute(
                id=uuid4(),
                name=route.get("name", ""),
                description=route.get("description", ""),
                path_pattern=route["path"],
                methods=[HttpMethod(m) for m in route.get("methods", ["GET"])],
                legacy_endpoint=LegacyEndpoint(
                    base_url=legacy_base_url,
                    path=route.get("legacy_path", route["path"]),
                    method=HttpMethod(route.get("methods", ["GET"])[0])
                ),
                cache=route_cache
            ))

        template = GatewayTemplate(
            id=uuid4(),
            name=name,
            description=description,
            template_type=GatewayTemplateType.CACHED,
            version="1.0",
            routes=gateway_routes,
            global_cache=default_cache
        )

        self._templates[template.id] = template
        return template

    # =========================================================================
    # Template Management
    # =========================================================================

    def get_template(self, template_id: Union[UUID, str]) -> Optional[GatewayTemplate]:
        """Get a template by ID."""
        if isinstance(template_id, str):
            template_id = UUID(template_id)
        return self._templates.get(template_id)

    def list_templates(
        self,
        template_type: Optional[GatewayTemplateType] = None
    ) -> List[GatewayTemplate]:
        """List all templates, optionally filtered by type."""
        templates = list(self._templates.values())
        if template_type:
            templates = [t for t in templates if t.template_type == template_type]
        return templates

    def delete_template(self, template_id: Union[UUID, str]) -> bool:
        """Delete a template."""
        if isinstance(template_id, str):
            template_id = UUID(template_id)
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False

    def add_route(
        self,
        template_id: Union[UUID, str],
        route: GatewayRoute
    ) -> Optional[GatewayTemplate]:
        """Add a route to an existing template."""
        template = self.get_template(template_id)
        if template:
            template.routes.append(route)
            template.updated_at = datetime.now()
            return template
        return None

    # =========================================================================
    # Export
    # =========================================================================

    def export_template(
        self,
        template_id: Union[UUID, str],
        format: str = "json"
    ) -> str:
        """Export template to JSON, YAML-like, or OpenAPI format."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        if format == "json":
            return json.dumps(template.to_dict(), indent=2)
        elif format == "openapi":
            return self._export_openapi(template)
        elif format == "nginx":
            return self._export_nginx_config(template)
        elif format == "kong":
            return self._export_kong_config(template)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_openapi(self, template: GatewayTemplate) -> str:
        """Export as OpenAPI 3.0 specification."""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": template.name,
                "description": template.description,
                "version": template.version
            },
            "servers": [
                {"url": "/api", "description": "API Gateway"}
            ],
            "paths": {}
        }

        for route in template.routes:
            path_spec = {}
            for method in route.methods:
                method_spec = {
                    "summary": route.name,
                    "description": route.description,
                    "operationId": f"{route.name}_{method.value.lower()}",
                    "responses": {
                        "200": {"description": "Successful response"},
                        "400": {"description": "Bad request"},
                        "401": {"description": "Unauthorized"},
                        "429": {"description": "Rate limit exceeded"},
                        "500": {"description": "Internal server error"}
                    },
                    "tags": route.tags or [template.template_type.value]
                }

                # Add security if auth is configured
                if route.auth or template.global_auth:
                    auth = route.auth or template.global_auth
                    if auth.auth_type == AuthType.API_KEY:
                        method_spec["security"] = [{"ApiKeyAuth": []}]
                    elif auth.auth_type == AuthType.BEARER:
                        method_spec["security"] = [{"BearerAuth": []}]

                path_spec[method.value.lower()] = method_spec

            # Convert path pattern to OpenAPI format
            openapi_path = re.sub(r'\{(\w+)\}', r'{\1}', route.path_pattern)
            spec["paths"][openapi_path] = path_spec

        # Add security schemes
        spec["components"] = {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                },
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer"
                }
            }
        }

        return json.dumps(spec, indent=2)

    def _export_nginx_config(self, template: GatewayTemplate) -> str:
        """Export as nginx configuration."""
        lines = [
            f"# API Gateway: {template.name}",
            f"# Generated: {datetime.now().isoformat()}",
            "",
            "upstream legacy_backend {",
        ]

        # Get unique backends
        backends = set()
        for route in template.routes:
            backends.add(route.legacy_endpoint.base_url)

        for backend in backends:
            # Parse URL to get host:port
            host = backend.replace("http://", "").replace("https://", "").split("/")[0]
            lines.append(f"    server {host};")

        lines.extend([
            "}",
            "",
            "server {",
            "    listen 80;",
            "    server_name api.example.com;",
            ""
        ])

        # Add rate limiting if configured
        if template.global_rate_limit:
            rl = template.global_rate_limit
            lines.extend([
                f"    # Rate limiting: {rl.requests_per_second} req/s",
                f"    limit_req_zone $binary_remote_addr zone=api_limit:10m rate={rl.requests_per_second}r/s;",
                ""
            ])

        # Add routes
        for route in template.routes:
            nginx_path = route.path_pattern.replace("{", "$").replace("}", "")
            lines.extend([
                f"    # Route: {route.name}",
                f"    location {nginx_path} {{",
            ])

            if template.global_rate_limit:
                lines.append(f"        limit_req zone=api_limit burst={template.global_rate_limit.burst_size};")

            # Add caching if configured
            if route.cache or template.global_cache:
                cache = route.cache or template.global_cache
                lines.extend([
                    f"        proxy_cache api_cache;",
                    f"        proxy_cache_valid 200 {cache.ttl_seconds}s;",
                ])

            lines.extend([
                f"        proxy_pass {route.legacy_endpoint.base_url}{route.legacy_endpoint.path};",
                f"        proxy_set_header Host $host;",
                f"        proxy_set_header X-Real-IP $remote_addr;",
                "    }",
                ""
            ])

        lines.append("}")

        return "\n".join(lines)

    def _export_kong_config(self, template: GatewayTemplate) -> str:
        """Export as Kong declarative configuration."""
        config = {
            "_format_version": "3.0",
            "services": [],
            "routes": [],
            "plugins": []
        }

        for i, route in enumerate(template.routes):
            service_name = f"legacy-service-{i}"
            route_name = f"route-{route.name.replace(' ', '-').lower()}"

            # Service
            config["services"].append({
                "name": service_name,
                "url": f"{route.legacy_endpoint.base_url}{route.legacy_endpoint.path}"
            })

            # Route
            config["routes"].append({
                "name": route_name,
                "service": service_name,
                "paths": [route.path_pattern],
                "methods": [m.value for m in route.methods]
            })

            # Rate limiting plugin
            if route.rate_limit or template.global_rate_limit:
                rl = route.rate_limit or template.global_rate_limit
                config["plugins"].append({
                    "name": "rate-limiting",
                    "service": service_name,
                    "config": {
                        "second": rl.requests_per_second,
                        "minute": rl.requests_per_minute,
                        "policy": "local"
                    }
                })

            # Caching plugin
            if route.cache or template.global_cache:
                cache = route.cache or template.global_cache
                config["plugins"].append({
                    "name": "proxy-cache",
                    "service": service_name,
                    "config": {
                        "strategy": "memory",
                        "cache_ttl": cache.ttl_seconds,
                        "content_type": ["application/json"]
                    }
                })

        return json.dumps(config, indent=2)

    # =========================================================================
    # Pre-built Templates
    # =========================================================================

    def get_prebuilt_simple_proxy(
        self,
        legacy_base_url: str,
        api_prefix: str = "/api/v1"
    ) -> GatewayTemplate:
        """Get a pre-built simple proxy template with best practices."""
        return self.create_simple_proxy(
            name="Simple Proxy Template",
            description="Direct proxy to legacy system with auth and rate limiting",
            legacy_base_url=legacy_base_url,
            routes=[
                {"path": f"{api_prefix}/{{resource}}", "methods": ["GET", "POST", "PUT", "DELETE"]},
                {"path": f"{api_prefix}/{{resource}}/{{id}}", "methods": ["GET", "PUT", "DELETE"]},
            ],
            auth=AuthConfig(auth_type=AuthType.API_KEY),
            rate_limit=RateLimitConfig(
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                requests_per_second=100,
                burst_size=50
            )
        )

    def get_prebuilt_cached_proxy(
        self,
        legacy_base_url: str,
        cache_ttl_seconds: int = 300
    ) -> GatewayTemplate:
        """Get a pre-built cached proxy template."""
        return self.create_cached(
            name="Cached Proxy Template",
            description="Proxy with intelligent caching for legacy read endpoints",
            legacy_base_url=legacy_base_url,
            routes=[
                {
                    "path": "/api/v1/{resource}",
                    "methods": ["GET"],
                    "cache_strategy": "ttl",
                    "ttl_seconds": cache_ttl_seconds
                },
                {
                    "path": "/api/v1/{resource}/{id}",
                    "methods": ["GET"],
                    "cache_strategy": "stale_while_revalidate",
                    "ttl_seconds": cache_ttl_seconds,
                    "stale_ttl_seconds": 60
                },
            ],
            cache_config=CacheConfig(
                strategy=CacheStrategy.STALE_WHILE_REVALIDATE,
                ttl_seconds=cache_ttl_seconds
            )
        )

    def get_prebuilt_aggregator(
        self,
        user_service_url: str,
        order_service_url: str,
        inventory_service_url: str
    ) -> GatewayTemplate:
        """Get a pre-built aggregator template for common pattern."""
        return self.create_aggregator(
            name="Customer Dashboard Aggregator",
            description="Aggregates user, orders, and inventory data into single response",
            path_pattern="/api/v1/dashboard/{user_id}",
            steps=[
                {
                    "id": "user",
                    "name": "Get User Details",
                    "base_url": user_service_url,
                    "path": "/users/{user_id}",
                    "method": "GET",
                    "extract_to": "$.user"
                },
                {
                    "id": "orders",
                    "name": "Get User Orders",
                    "base_url": order_service_url,
                    "path": "/orders?user_id={user_id}",
                    "method": "GET",
                    "depends_on": ["user"],
                    "extract_to": "$.orders"
                },
                {
                    "id": "inventory",
                    "name": "Check Inventory",
                    "base_url": inventory_service_url,
                    "path": "/inventory/available",
                    "method": "GET",
                    "extract_to": "$.inventory"
                }
            ],
            response_template=json.dumps({
                "user": "$.user",
                "recent_orders": "$.orders[0:5]",
                "inventory_status": "$.inventory.status"
            })
        )
