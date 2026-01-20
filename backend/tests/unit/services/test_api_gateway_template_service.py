"""
Unit tests for APIGatewayTemplateService (G3 - Fase 24)

Tests API Gateway template creation, configuration management,
and export functionality (JSON, OpenAPI, nginx, Kong).
"""

import pytest
import json
from datetime import datetime
from uuid import UUID, uuid4

from app.services.api_gateway_template_service import (
    APIGatewayTemplateService,
    GatewayTemplateType,
    HttpMethod,
    AuthType,
    CacheStrategy,
    RateLimitStrategy,
    AuthConfig,
    RateLimitConfig,
    CacheConfig,
    TimeoutConfig,
    RetryConfig,
    CircuitBreakerConfig,
    HeaderTransform,
    BodyTransform,
    PathTransform,
    TransformConfig,
    LegacyEndpoint,
    GatewayRoute,
    AggregatorStep,
    AggregatorConfig,
    GatewayTemplate,
)


# ============================================================================
# Configuration Component Tests
# ============================================================================

class TestAuthConfig:
    """Tests for AuthConfig dataclass."""

    def test_api_key_auth(self):
        """Test API key authentication config."""
        auth = AuthConfig(
            auth_type=AuthType.API_KEY,
            api_key_header="X-Custom-Key"
        )
        assert auth.auth_type == AuthType.API_KEY
        assert auth.api_key_header == "X-Custom-Key"

    def test_oauth2_auth(self):
        """Test OAuth2 authentication config."""
        auth = AuthConfig(
            auth_type=AuthType.OAUTH2,
            oauth2_token_url="https://auth.example.com/token",
            oauth2_client_id="client_123",
            oauth2_scope="read write"
        )
        data = auth.to_dict()
        assert data["auth_type"] == "oauth2"
        assert data["oauth2_token_url"] == "https://auth.example.com/token"


class TestRateLimitConfig:
    """Tests for RateLimitConfig dataclass."""

    def test_token_bucket_config(self):
        """Test token bucket rate limiting config."""
        config = RateLimitConfig(
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            requests_per_second=50,
            burst_size=100
        )
        assert config.strategy == RateLimitStrategy.TOKEN_BUCKET
        assert config.requests_per_second == 50
        assert config.burst_size == 100

    def test_sliding_window_config(self):
        """Test sliding window rate limiting config."""
        config = RateLimitConfig(
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            requests_per_minute=1000,
            window_size_seconds=60,
            key_by="api_key"
        )
        data = config.to_dict()
        assert data["strategy"] == "sliding_window"
        assert data["key_by"] == "api_key"


class TestCacheConfig:
    """Tests for CacheConfig dataclass."""

    def test_ttl_cache_config(self):
        """Test TTL-based cache config."""
        config = CacheConfig(
            strategy=CacheStrategy.TTL,
            ttl_seconds=600,
            vary_by_headers=["Authorization", "Accept-Language"]
        )
        assert config.strategy == CacheStrategy.TTL
        assert config.ttl_seconds == 600
        assert "Authorization" in config.vary_by_headers

    def test_stale_while_revalidate_config(self):
        """Test stale-while-revalidate cache config."""
        config = CacheConfig(
            strategy=CacheStrategy.STALE_WHILE_REVALIDATE,
            ttl_seconds=300,
            stale_ttl_seconds=60
        )
        data = config.to_dict()
        assert data["strategy"] == "stale_while_revalidate"
        assert data["stale_ttl_seconds"] == 60


class TestTimeoutConfig:
    """Tests for TimeoutConfig dataclass."""

    def test_timeout_defaults(self):
        """Test default timeout values."""
        config = TimeoutConfig()
        assert config.connect_timeout_ms == 5000
        assert config.read_timeout_ms == 30000
        assert config.total_timeout_ms == 60000

    def test_custom_timeouts(self):
        """Test custom timeout values."""
        config = TimeoutConfig(
            connect_timeout_ms=2000,
            read_timeout_ms=10000,
            write_timeout_ms=10000,
            total_timeout_ms=20000
        )
        data = config.to_dict()
        assert data["connect_timeout_ms"] == 2000
        assert data["total_timeout_ms"] == 20000


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_retry_defaults(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.enabled
        assert config.max_retries == 3
        assert config.exponential_backoff
        assert 502 in config.retry_on_status_codes

    def test_custom_retry(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            enabled=True,
            max_retries=5,
            initial_delay_ms=200,
            retry_on_status_codes=[500, 502, 503, 504]
        )
        data = config.to_dict()
        assert data["max_retries"] == 5
        assert 500 in data["retry_on_status_codes"]


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig dataclass."""

    def test_circuit_breaker_defaults(self):
        """Test default circuit breaker configuration."""
        config = CircuitBreakerConfig()
        assert config.enabled
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout_seconds == 30

    def test_custom_circuit_breaker(self):
        """Test custom circuit breaker configuration."""
        config = CircuitBreakerConfig(
            enabled=True,
            failure_threshold=10,
            half_open_max_calls=5
        )
        data = config.to_dict()
        assert data["failure_threshold"] == 10
        assert data["half_open_max_calls"] == 5


# ============================================================================
# Transformation Tests
# ============================================================================

class TestHeaderTransform:
    """Tests for HeaderTransform dataclass."""

    def test_add_header(self):
        """Test add header transformation."""
        transform = HeaderTransform(
            action="add",
            source="X-Custom-Header",
            value="custom-value"
        )
        data = transform.to_dict()
        assert data["action"] == "add"
        assert data["value"] == "custom-value"

    def test_rename_header(self):
        """Test rename header transformation."""
        transform = HeaderTransform(
            action="rename",
            source="X-Old-Header",
            target="X-New-Header"
        )
        data = transform.to_dict()
        assert data["action"] == "rename"
        assert data["target"] == "X-New-Header"


class TestBodyTransform:
    """Tests for BodyTransform dataclass."""

    def test_body_transform(self):
        """Test body transformation."""
        transform = BodyTransform(
            source_path="$.data.user_name",
            target_path="$.userName",
            transform="camelCase"
        )
        data = transform.to_dict()
        assert data["source_path"] == "$.data.user_name"
        assert data["target_path"] == "$.userName"


class TestTransformConfig:
    """Tests for TransformConfig dataclass."""

    def test_full_transform_config(self):
        """Test complete transformation configuration."""
        config = TransformConfig(
            request_headers=[HeaderTransform(action="add", source="X-API-Version", value="v1")],
            response_headers=[HeaderTransform(action="remove", source="X-Internal-Header")],
            request_body=[BodyTransform(source_path="$.name", target_path="$.full_name")],
            strip_prefix="/api/v1",
            add_prefix="/legacy"
        )
        data = config.to_dict()
        assert len(data["request_headers"]) == 1
        assert data["strip_prefix"] == "/api/v1"
        assert data["add_prefix"] == "/legacy"


# ============================================================================
# Route & Endpoint Tests
# ============================================================================

class TestLegacyEndpoint:
    """Tests for LegacyEndpoint dataclass."""

    def test_legacy_endpoint(self):
        """Test legacy endpoint definition."""
        endpoint = LegacyEndpoint(
            base_url="http://legacy.internal:8080",
            path="/api/users",
            method=HttpMethod.GET,
            headers={"X-Legacy-Auth": "token123"}
        )
        data = endpoint.to_dict()
        assert data["base_url"] == "http://legacy.internal:8080"
        assert data["method"] == "GET"
        assert "X-Legacy-Auth" in data["headers"]

    def test_legacy_endpoint_with_auth(self):
        """Test legacy endpoint with authentication."""
        endpoint = LegacyEndpoint(
            base_url="http://legacy.internal:8080",
            path="/api/secure",
            method=HttpMethod.POST,
            auth=AuthConfig(auth_type=AuthType.BASIC)
        )
        data = endpoint.to_dict()
        assert data["auth"]["auth_type"] == "basic"


class TestGatewayRoute:
    """Tests for GatewayRoute dataclass."""

    def test_gateway_route_basic(self):
        """Test basic gateway route."""
        route = GatewayRoute(
            id=uuid4(),
            name="Get Users",
            description="Retrieve all users",
            path_pattern="/api/v1/users",
            methods=[HttpMethod.GET],
            legacy_endpoint=LegacyEndpoint(
                base_url="http://legacy:8080",
                path="/users",
                method=HttpMethod.GET
            )
        )
        data = route.to_dict()
        assert data["name"] == "Get Users"
        assert "GET" in data["methods"]

    def test_gateway_route_with_all_features(self):
        """Test gateway route with all optional features."""
        route = GatewayRoute(
            id=uuid4(),
            name="Update User",
            description="Update user by ID",
            path_pattern="/api/v1/users/{id}",
            methods=[HttpMethod.PUT, HttpMethod.PATCH],
            legacy_endpoint=LegacyEndpoint(
                base_url="http://legacy:8080",
                path="/users/{id}",
                method=HttpMethod.PUT
            ),
            auth=AuthConfig(auth_type=AuthType.BEARER),
            rate_limit=RateLimitConfig(strategy=RateLimitStrategy.TOKEN_BUCKET),
            cache=CacheConfig(strategy=CacheStrategy.NO_CACHE),
            circuit_breaker=CircuitBreakerConfig(enabled=True),
            retry=RetryConfig(max_retries=2),
            tags=["users", "write"]
        )
        data = route.to_dict()
        assert len(data["methods"]) == 2
        assert data["auth"]["auth_type"] == "bearer"
        assert data["rate_limit"]["strategy"] == "token_bucket"
        assert "users" in data["tags"]


# ============================================================================
# Aggregator Tests
# ============================================================================

class TestAggregatorStep:
    """Tests for AggregatorStep dataclass."""

    def test_aggregator_step(self):
        """Test aggregator step definition."""
        step = AggregatorStep(
            id="get_user",
            name="Get User Details",
            legacy_endpoint=LegacyEndpoint(
                base_url="http://user-service:8080",
                path="/users/{user_id}",
                method=HttpMethod.GET
            ),
            extract_to="$.user"
        )
        data = step.to_dict()
        assert data["id"] == "get_user"
        assert data["extract_to"] == "$.user"

    def test_aggregator_step_with_dependency(self):
        """Test aggregator step with dependency."""
        step = AggregatorStep(
            id="get_orders",
            name="Get User Orders",
            legacy_endpoint=LegacyEndpoint(
                base_url="http://order-service:8080",
                path="/orders",
                method=HttpMethod.GET
            ),
            depends_on=["get_user"],
            condition="user.active == true"
        )
        data = step.to_dict()
        assert "get_user" in data["depends_on"]
        assert data["condition"] == "user.active == true"


class TestAggregatorConfig:
    """Tests for AggregatorConfig dataclass."""

    def test_aggregator_config(self):
        """Test aggregator configuration."""
        steps = [
            AggregatorStep(
                id="user", name="User",
                legacy_endpoint=LegacyEndpoint(
                    base_url="http://svc1:8080", path="/user", method=HttpMethod.GET
                )
            ),
            AggregatorStep(
                id="orders", name="Orders",
                legacy_endpoint=LegacyEndpoint(
                    base_url="http://svc2:8080", path="/orders", method=HttpMethod.GET
                ),
                depends_on=["user"]
            )
        ]
        config = AggregatorConfig(
            steps=steps,
            parallel_execution=True,
            fail_fast=True,
            timeout_ms=10000
        )
        data = config.to_dict()
        assert len(data["steps"]) == 2
        assert data["parallel_execution"]
        assert data["timeout_ms"] == 10000


# ============================================================================
# APIGatewayTemplateService Tests
# ============================================================================

class TestAPIGatewayTemplateService:
    """Tests for APIGatewayTemplateService."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return APIGatewayTemplateService()

    def test_create_simple_proxy(self, service):
        """Test creating a simple proxy template."""
        template = service.create_simple_proxy(
            name="User API Proxy",
            description="Proxy to legacy user service",
            legacy_base_url="http://legacy-users:8080",
            routes=[
                {"path": "/api/users", "methods": ["GET", "POST"]},
                {"path": "/api/users/{id}", "methods": ["GET", "PUT", "DELETE"]}
            ],
            auth=AuthConfig(auth_type=AuthType.API_KEY),
            rate_limit=RateLimitConfig(
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                requests_per_second=100
            )
        )

        assert template.name == "User API Proxy"
        assert template.template_type == GatewayTemplateType.SIMPLE_PROXY
        assert len(template.routes) == 2
        assert template.global_auth.auth_type == AuthType.API_KEY

    def test_create_aggregator(self, service):
        """Test creating an aggregator template."""
        template = service.create_aggregator(
            name="Dashboard Aggregator",
            description="Combines user, orders, and inventory",
            path_pattern="/api/v1/dashboard/{user_id}",
            steps=[
                {
                    "id": "user",
                    "name": "Get User",
                    "base_url": "http://user-svc:8080",
                    "path": "/users/{user_id}",
                    "method": "GET",
                    "extract_to": "$.user"
                },
                {
                    "id": "orders",
                    "name": "Get Orders",
                    "base_url": "http://order-svc:8080",
                    "path": "/orders?user={user_id}",
                    "method": "GET",
                    "depends_on": ["user"],
                    "extract_to": "$.orders"
                }
            ],
            response_template='{"user": "$.user", "orders": "$.orders"}'
        )

        assert template.template_type == GatewayTemplateType.AGGREGATOR
        assert template.aggregator is not None
        assert len(template.aggregator.steps) == 2

    def test_create_transformer(self, service):
        """Test creating a transformer template."""
        transform_config = TransformConfig(
            request_headers=[HeaderTransform(action="add", source="X-Version", value="v2")],
            strip_prefix="/api/v2"
        )

        template = service.create_transformer(
            name="API Transformer",
            description="Transform requests for legacy system",
            legacy_base_url="http://legacy:8080",
            routes=[
                {
                    "path": "/api/v2/users",
                    "methods": ["GET", "POST"],
                    "legacy_path": "/old-api/users",
                    "request_body_mapping": {
                        "$.firstName": "$.first_name",
                        "$.lastName": "$.last_name"
                    }
                }
            ],
            default_transform=transform_config
        )

        assert template.template_type == GatewayTemplateType.TRANSFORMER
        assert len(template.routes) == 1
        assert template.routes[0].transform is not None

    def test_create_cached(self, service):
        """Test creating a cached proxy template."""
        template = service.create_cached(
            name="Cached API",
            description="API with caching layer",
            legacy_base_url="http://legacy:8080",
            routes=[
                {
                    "path": "/api/products",
                    "methods": ["GET"],
                    "cache_strategy": "ttl",
                    "ttl_seconds": 300
                },
                {
                    "path": "/api/products/{id}",
                    "methods": ["GET"],
                    "cache_strategy": "stale_while_revalidate",
                    "ttl_seconds": 600,
                    "stale_ttl_seconds": 120
                }
            ],
            cache_config=CacheConfig(strategy=CacheStrategy.TTL, ttl_seconds=300)
        )

        assert template.template_type == GatewayTemplateType.CACHED
        assert template.global_cache is not None
        assert template.routes[0].cache.ttl_seconds == 300

    def test_get_template(self, service):
        """Test retrieving a template by ID."""
        template = service.create_simple_proxy(
            "Test", "Test", "http://legacy:8080",
            routes=[{"path": "/test", "methods": ["GET"]}]
        )

        retrieved = service.get_template(template.id)
        assert retrieved == template

        # Test with string ID
        retrieved_str = service.get_template(str(template.id))
        assert retrieved_str == template

    def test_list_templates(self, service):
        """Test listing all templates."""
        service.create_simple_proxy(
            "Proxy1", "Proxy 1", "http://svc1:8080",
            routes=[{"path": "/api1", "methods": ["GET"]}]
        )
        service.create_cached(
            "Cached1", "Cached 1", "http://svc2:8080",
            routes=[{"path": "/api2", "methods": ["GET"]}]
        )

        all_templates = service.list_templates()
        assert len(all_templates) == 2

        # Filter by type
        proxy_templates = service.list_templates(GatewayTemplateType.SIMPLE_PROXY)
        assert len(proxy_templates) == 1

    def test_delete_template(self, service):
        """Test deleting a template."""
        template = service.create_simple_proxy(
            "ToDelete", "Delete me", "http://legacy:8080",
            routes=[{"path": "/test", "methods": ["GET"]}]
        )

        assert service.delete_template(template.id)
        assert service.get_template(template.id) is None

        # Delete non-existent
        assert not service.delete_template(uuid4())

    def test_add_route(self, service):
        """Test adding a route to existing template."""
        template = service.create_simple_proxy(
            "Test", "Test", "http://legacy:8080",
            routes=[{"path": "/api/v1", "methods": ["GET"]}]
        )

        new_route = GatewayRoute(
            id=uuid4(),
            name="New Route",
            description="Added later",
            path_pattern="/api/v2",
            methods=[HttpMethod.GET, HttpMethod.POST],
            legacy_endpoint=LegacyEndpoint(
                base_url="http://legacy:8080",
                path="/v2",
                method=HttpMethod.GET
            )
        )

        updated = service.add_route(template.id, new_route)
        assert len(updated.routes) == 2

    def test_export_template_json(self, service):
        """Test exporting template to JSON."""
        template = service.create_simple_proxy(
            "Export Test", "Test export", "http://legacy:8080",
            routes=[{"path": "/api", "methods": ["GET"]}]
        )

        json_export = service.export_template(template.id, format="json")
        data = json.loads(json_export)
        assert data["name"] == "Export Test"
        assert data["template_type"] == "simple_proxy"

    def test_export_template_openapi(self, service):
        """Test exporting template to OpenAPI format."""
        template = service.create_simple_proxy(
            "OpenAPI Test", "Test OpenAPI export", "http://legacy:8080",
            routes=[
                {"name": "Get Users", "path": "/api/users", "methods": ["GET"]},
                {"name": "Create User", "path": "/api/users", "methods": ["POST"]}
            ],
            auth=AuthConfig(auth_type=AuthType.API_KEY)
        )

        openapi_export = service.export_template(template.id, format="openapi")
        spec = json.loads(openapi_export)

        assert spec["openapi"] == "3.0.0"
        assert spec["info"]["title"] == "OpenAPI Test"
        assert "/api/users" in spec["paths"]
        assert "components" in spec
        assert "ApiKeyAuth" in spec["components"]["securitySchemes"]

    def test_export_template_nginx(self, service):
        """Test exporting template to nginx config."""
        template = service.create_simple_proxy(
            "Nginx Test", "Test nginx export", "http://backend:8080",
            routes=[{"path": "/api/users", "methods": ["GET"]}],
            rate_limit=RateLimitConfig(
                strategy=RateLimitStrategy.FIXED_WINDOW,
                requests_per_second=100,
                burst_size=50
            )
        )

        nginx_config = service.export_template(template.id, format="nginx")
        assert "upstream legacy_backend" in nginx_config
        assert "limit_req_zone" in nginx_config
        assert "proxy_pass" in nginx_config

    def test_export_template_kong(self, service):
        """Test exporting template to Kong config."""
        template = service.create_simple_proxy(
            "Kong Test", "Test Kong export", "http://backend:8080",
            routes=[{"name": "users", "path": "/api/users", "methods": ["GET"]}],
            rate_limit=RateLimitConfig(
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                requests_per_second=50,
                requests_per_minute=500
            )
        )

        kong_config = service.export_template(template.id, format="kong")
        config = json.loads(kong_config)

        assert config["_format_version"] == "3.0"
        assert len(config["services"]) > 0
        assert len(config["routes"]) > 0
        assert any(p["name"] == "rate-limiting" for p in config["plugins"])

    def test_export_template_invalid_format(self, service):
        """Test export with invalid format."""
        template = service.create_simple_proxy(
            "Test", "Test", "http://legacy:8080",
            routes=[{"path": "/api", "methods": ["GET"]}]
        )

        with pytest.raises(ValueError, match="Unsupported format"):
            service.export_template(template.id, format="yaml")

    def test_export_template_not_found(self, service):
        """Test export non-existent template."""
        with pytest.raises(ValueError, match="Template not found"):
            service.export_template(uuid4())

    def test_prebuilt_simple_proxy(self, service):
        """Test pre-built simple proxy template."""
        template = service.get_prebuilt_simple_proxy(
            legacy_base_url="http://legacy:8080",
            api_prefix="/api/v1"
        )

        assert template.template_type == GatewayTemplateType.SIMPLE_PROXY
        assert template.global_auth.auth_type == AuthType.API_KEY
        assert template.global_rate_limit.strategy == RateLimitStrategy.TOKEN_BUCKET

    def test_prebuilt_cached_proxy(self, service):
        """Test pre-built cached proxy template."""
        template = service.get_prebuilt_cached_proxy(
            legacy_base_url="http://legacy:8080",
            cache_ttl_seconds=600
        )

        assert template.template_type == GatewayTemplateType.CACHED
        assert template.global_cache.ttl_seconds == 600

    def test_prebuilt_aggregator(self, service):
        """Test pre-built aggregator template."""
        template = service.get_prebuilt_aggregator(
            user_service_url="http://users:8080",
            order_service_url="http://orders:8080",
            inventory_service_url="http://inventory:8080"
        )

        assert template.template_type == GatewayTemplateType.AGGREGATOR
        assert len(template.aggregator.steps) == 3


# ============================================================================
# Enum Tests
# ============================================================================

class TestEnums:
    """Tests for service enums."""

    def test_gateway_template_type_values(self):
        """Test gateway template type enum values."""
        assert GatewayTemplateType.SIMPLE_PROXY.value == "simple_proxy"
        assert GatewayTemplateType.AGGREGATOR.value == "aggregator"
        assert GatewayTemplateType.TRANSFORMER.value == "transformer"
        assert GatewayTemplateType.CACHED.value == "cached"

    def test_http_method_values(self):
        """Test HTTP method enum values."""
        assert HttpMethod.GET.value == "GET"
        assert HttpMethod.POST.value == "POST"
        assert HttpMethod.PUT.value == "PUT"
        assert HttpMethod.DELETE.value == "DELETE"
        assert HttpMethod.PATCH.value == "PATCH"

    def test_auth_type_values(self):
        """Test auth type enum values."""
        assert AuthType.NONE.value == "none"
        assert AuthType.API_KEY.value == "api_key"
        assert AuthType.BASIC.value == "basic"
        assert AuthType.BEARER.value == "bearer"
        assert AuthType.OAUTH2.value == "oauth2"

    def test_cache_strategy_values(self):
        """Test cache strategy enum values."""
        assert CacheStrategy.NO_CACHE.value == "no_cache"
        assert CacheStrategy.TTL.value == "ttl"
        assert CacheStrategy.STALE_WHILE_REVALIDATE.value == "stale_while_revalidate"
        assert CacheStrategy.CACHE_FIRST.value == "cache_first"
        assert CacheStrategy.NETWORK_FIRST.value == "network_first"

    def test_rate_limit_strategy_values(self):
        """Test rate limit strategy enum values."""
        assert RateLimitStrategy.NONE.value == "none"
        assert RateLimitStrategy.FIXED_WINDOW.value == "fixed_window"
        assert RateLimitStrategy.SLIDING_WINDOW.value == "sliding_window"
        assert RateLimitStrategy.TOKEN_BUCKET.value == "token_bucket"
        assert RateLimitStrategy.LEAKY_BUCKET.value == "leaky_bucket"


# ============================================================================
# GatewayTemplate Tests
# ============================================================================

class TestGatewayTemplate:
    """Tests for GatewayTemplate dataclass."""

    def test_gateway_template_to_dict(self):
        """Test gateway template serialization."""
        template = GatewayTemplate(
            id=uuid4(),
            name="Test Template",
            description="A test template",
            template_type=GatewayTemplateType.SIMPLE_PROXY,
            version="1.0",
            routes=[],
            cors_enabled=True,
            cors_origins=["https://example.com"],
            cors_methods=["GET", "POST"],
            tags={"env": "production"}
        )
        data = template.to_dict()

        assert data["name"] == "Test Template"
        assert data["template_type"] == "simple_proxy"
        assert data["cors"]["enabled"]
        assert "https://example.com" in data["cors"]["origins"]
        assert data["tags"]["env"] == "production"

    def test_gateway_template_with_global_settings(self):
        """Test gateway template with global settings."""
        template = GatewayTemplate(
            id=uuid4(),
            name="Full Template",
            description="Template with all global settings",
            template_type=GatewayTemplateType.SIMPLE_PROXY,
            version="2.0",
            routes=[],
            global_auth=AuthConfig(auth_type=AuthType.BEARER),
            global_rate_limit=RateLimitConfig(strategy=RateLimitStrategy.TOKEN_BUCKET),
            global_cache=CacheConfig(strategy=CacheStrategy.TTL),
            global_timeout=TimeoutConfig(total_timeout_ms=30000),
            global_circuit_breaker=CircuitBreakerConfig(failure_threshold=10)
        )
        data = template.to_dict()

        assert data["global_auth"]["auth_type"] == "bearer"
        assert data["global_rate_limit"]["strategy"] == "token_bucket"
        assert data["global_cache"]["strategy"] == "ttl"
        assert data["global_timeout"]["total_timeout_ms"] == 30000
        assert data["global_circuit_breaker"]["failure_threshold"] == 10
