# PROJECT_CONTEXT.md - Universal Project Context Template
# MarQed.ai Multi-Stack AI Agent Platform - Week 101

## Overview

This template provides a universal project context format that can be transformed
to LLM-specific formats by the LLM Context Adapter Service.

---

## Core Context

### Project Identity
- **Project Name:** [PROJECT_NAME]
- **Version:** [VERSION]
- **Status:** [active|maintenance|legacy]
- **Start Date:** [YYYY-MM-DD]

### Tech Stack
- **Primary Language:** [Python|TypeScript|Go|Rust|Java|C#]
- **Framework:** [FastAPI|Django|Express|Next.js|Spring|.NET]
- **Database:** [PostgreSQL|MySQL|MongoDB|SQLite]
- **Cache:** [Redis|Memcached|None]
- **Message Queue:** [RabbitMQ|Kafka|Celery|None]

### Architecture Pattern
- **Style:** [Monolith|Microservices|Serverless|Modular Monolith]
- **Layers:** [3-tier|Clean Architecture|Hexagonal|CQRS]
- **API Style:** [REST|GraphQL|gRPC|Mixed]

---

## Code Generation Guidelines

### Implementation Order
1. **Domain Layer** - Entities, value objects, domain events
2. **Specifications** - Business rules as specification patterns (if applicable)
3. **Repository/Data Layer** - Database operations, migrations
4. **Service Layer** - Business logic, orchestration
5. **API Layer** - Controllers, routes, serialization
6. **UI Layer** - Components, pages, state management

### Database Change Process
1. Create Alembic migration: `alembic revision --autogenerate -m "description"`
2. Review generated migration for correctness
3. Apply migration: `alembic upgrade head`
4. Update models/__init__.py with new models
5. Add corresponding API endpoints

### Testing Requirements
- **Unit Tests:** Required for all services and utilities
- **Integration Tests:** Required for API endpoints
- **Coverage Target:** 80% minimum
- **Test Location:** `tests/` mirroring `app/` structure

### Naming Conventions
- **Classes:** PascalCase (e.g., `UserService`, `OrderRepository`)
- **Functions:** snake_case (e.g., `get_user_by_id`, `create_order`)
- **Files:** snake_case (e.g., `user_service.py`, `order_model.py`)
- **Constants:** SCREAMING_SNAKE_CASE (e.g., `MAX_RETRY_COUNT`)
- **Private Fields:** _underscore_prefix (e.g., `_internal_cache`)

---

## Authentication & Security Model

### Security Patterns
- **Authentication:** [JWT|OAuth2|Session|API Key]
- **Authorization:** [RBAC|ABAC|ACL|Custom]
- **Password Hashing:** [bcrypt|argon2|scrypt]
- **Token Expiry:** [duration]

### Compliance Requirements
- [ ] NEN7510 (Dutch Healthcare)
- [ ] ISO27001 (Information Security)
- [ ] HIPAA (US Healthcare)
- [ ] GDPR (EU Data Protection)
- [ ] PCI-DSS (Payment Card)
- [ ] SOC2 (Service Organization)

### Security Checklist
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF protection
- [ ] Rate limiting
- [ ] Audit logging

---

## Domain Vocabulary

### Business Terms
| Term | Definition | Code Entity |
|------|------------|-------------|
| [Term1] | [Definition1] | [Entity1] |
| [Term2] | [Definition2] | [Entity2] |

### Domain Events
| Event | Trigger | Handler |
|-------|---------|---------|
| [Event1] | [Trigger1] | [Handler1] |

### Aggregate Roots
- [AggregateRoot1]: [Description]
- [AggregateRoot2]: [Description]

---

## Error Handling

### Standard Error Codes
| Code | Meaning | HTTP Status |
|------|---------|-------------|
| `E001` | Validation Error | 400 |
| `E002` | Authentication Failed | 401 |
| `E003` | Authorization Denied | 403 |
| `E004` | Resource Not Found | 404 |
| `E005` | Conflict | 409 |
| `E006` | Internal Error | 500 |

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "E001",
    "message": "Validation failed",
    "details": [
      {"field": "email", "message": "Invalid email format"}
    ]
  }
}
```

---

## API Conventions

### Endpoint Patterns
- **List:** `GET /api/{resource}` - Returns paginated list
- **Get:** `GET /api/{resource}/{id}` - Returns single item
- **Create:** `POST /api/{resource}` - Creates new item
- **Update:** `PUT /api/{resource}/{id}` - Full update
- **Patch:** `PATCH /api/{resource}/{id}` - Partial update
- **Delete:** `DELETE /api/{resource}/{id}` - Soft or hard delete

### Pagination
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_prev": false
}
```

### Filtering & Sorting
- Filter: `?status=active&type=premium`
- Sort: `?sort=created_at&order=desc`
- Search: `?q=search_term`

---

## External Integrations

### Third-Party Services
| Service | Purpose | Auth Method |
|---------|---------|-------------|
| [Service1] | [Purpose1] | [Method1] |

### Webhooks
| Event | Endpoint | Payload |
|-------|----------|---------|
| [Event1] | [URL1] | [Schema1] |

---

## Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434
```

### Feature Flags
| Flag | Default | Description |
|------|---------|-------------|
| `ENABLE_FEATURE_X` | false | [Description] |

---

## Performance Guidelines

### Caching Strategy
- **Cache Duration:** [duration]
- **Cache Invalidation:** [strategy]
- **Cacheable Endpoints:** [list]

### Query Optimization
- Use eager loading for related entities
- Paginate all list endpoints
- Index frequently queried columns

---

## Monitoring & Observability

### Logging
- **Format:** JSON structured logging
- **Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Include:** request_id, user_id, timestamp, duration

### Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `request_count` | Counter | Total requests |
| `request_duration` | Histogram | Response time |
| `error_rate` | Gauge | Error percentage |

---

## Notes for AI Agents

### Do's
- Follow the implementation order strictly
- Write tests before or alongside implementation
- Use Result pattern for error handling
- Apply guard clauses for validation
- Check existing patterns before creating new ones

### Don'ts
- Skip database migrations for schema changes
- Bypass authentication/authorization
- Use raw SQL queries (use ORM)
- Create duplicate service functionality
- Ignore existing naming conventions

### Questions to Ask
- Is this feature already partially implemented?
- What existing services can be reused?
- Are there domain-specific rules to consider?
- What compliance requirements apply?

---

**Template Version:** 1.0.0
**Last Updated:** 2024-12-24
**Maintained By:** MarQed.ai Platform Team
