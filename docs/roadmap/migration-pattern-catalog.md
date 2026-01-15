# Migration Pattern Catalog
# MarQed AI Platform - Complete Reference

> **Version**: 1.0
> **Created**: Week 158 (January 2026)
> **Purpose**: Complete inventory of known migration patterns for legacy modernization
> **Status**: Reference document - implement when needed

---

## Pattern Overview

| # | Pattern | Status | ROI | Complexity | Use Case |
|---|---------|--------|-----|------------|----------|
| 1 | Strangler Fig | IMPLEMENTED | 9.0 | High | Gradual replacement |
| 2 | Blue-Green Deployment | IMPLEMENTED | 8.5 | Medium | Zero-downtime |
| 3 | Parallel Run | IMPLEMENTED | 8.0 | High | Validation |
| 4 | Phased Migration | IMPLEMENTED | 7.5 | Medium | Large systems |
| 5 | Incremental | IMPLEMENTED | 7.0 | Low | Continuous delivery |
| 6 | Big Bang | IMPLEMENTED | 5.0 | Low | Small systems |
| 7 | Database-First | IMPLEMENTED | 8.0 | High | Data-centric apps |
| 8 | Anti-Corruption Layer | PLANNED | 8.5 | Medium | Domain isolation |
| 9 | Branch by Abstraction | PLANNED | 7.5 | Medium | Gradual refactoring |
| 10 | Bubble Context | PLANNED | 7.0 | Medium | DDD migration |
| 11 | Event Interception | PLANNED | 8.0 | High | Event-driven |
| 12 | Asset Capture | PLANNED | 6.5 | Low | Quick wins |
| 13 | Feature Toggle | IMPLEMENTED | 8.0 | Low | Controlled rollout |
| 14 | Canary Release | IMPLEMENTED | 8.5 | Medium | Risk mitigation |
| 15 | Dark Launch | PLANNED | 7.5 | Medium | Silent testing |
| 16 | Shadow Traffic | PLANNED | 8.0 | High | Load testing |
| 17 | Contract-First | PLANNED | 7.0 | Medium | API migration |
| 18 | Facade Pattern | PLANNED | 6.5 | Low | Interface abstraction |
| 19 | Adapter Pattern | PLANNED | 6.0 | Low | Protocol translation |
| 20 | Decompose by Subdomain | PLANNED | 8.5 | High | Microservices |
| 21 | Decompose by Business Capability | PLANNED | 8.0 | High | Strategic alignment |
| 22 | Extract Service | PLANNED | 7.5 | Medium | Service isolation |
| 23 | Wrap & Replace | PLANNED | 7.0 | Medium | Component modernization |
| 24 | Replatforming | PLANNED | 6.0 | Medium | Infrastructure change |
| 25 | Refactoring | PLANNED | 5.5 | Low | Code improvement |

---

## IMPLEMENTED PATTERNS

### 1. Strangler Fig Pattern
**File**: `app/services/strangler_fig_service.py`
**Status**: FULLY IMPLEMENTED

#### Description
Gradually replace legacy system functionality by routing traffic between old and new implementations.

#### Components
- `FeatureFlag` - Toggle between legacy/new
- `TrafficRule` - Routing decisions
- `MigrationComponent` - Component tracking
- `RolloutPlan` - Phased rollout
- `HealthCheck` - System monitoring

#### Use Cases
- Large monolith to microservices
- Long-running migrations (6+ months)
- Risk-averse organizations
- Systems that can't afford downtime

#### Example
```python
from app.services.strangler_fig_service import StranglerFigService

service = StranglerFigService()
session = service.create_session(project_id="...")
service.add_component(session.id, component)
service.set_traffic_split(session.id, "orders", percentage=25)
```

---

### 2. Blue-Green Deployment
**File**: `app/services/migration_planning_orchestrator.py`
**Status**: IMPLEMENTED (Strategy)

#### Description
Run two identical production environments. Switch traffic instantly between blue (current) and green (new).

#### Benefits
- Zero-downtime deployment
- Instant rollback capability
- Easy A/B testing
- Reduced risk

#### When to Use
- Mission-critical systems
- Systems requiring instant rollback
- Regulatory compliance environments

---

### 3. Parallel Run Pattern
**File**: `app/services/migration_planning_orchestrator.py`
**Status**: IMPLEMENTED (Strategy)

#### Description
Run legacy and new systems simultaneously, comparing outputs for validation.

#### Components
- Request duplicator
- Response comparator
- Discrepancy logger
- Reconciliation reports

#### When to Use
- Financial systems
- Data accuracy critical
- Regulatory requirements
- Building confidence in new system

---

### 4. Phased Migration
**File**: `app/services/migration_planning_orchestrator.py`
**Status**: IMPLEMENTED (Strategy)

#### Description
Migrate in planned phases, each with clear milestones and deliverables.

#### Phase Structure
1. Assessment & Planning
2. Foundation & Infrastructure
3. Core Business Logic
4. UI/UX Migration
5. Integration & Testing
6. Cutover & Stabilization

---

### 5. Feature Toggle Pattern
**File**: `app/services/strangler_fig_service.py`
**Status**: IMPLEMENTED

#### Description
Control feature availability through configuration without code deployment.

#### Toggle Types
- Release toggles (short-lived)
- Experiment toggles (A/B testing)
- Ops toggles (kill switches)
- Permission toggles (user segments)

---

### 6. Canary Release
**File**: `app/services/strangler_fig_service.py`
**Status**: IMPLEMENTED

#### Description
Deploy to small subset of users/servers first, then gradually expand.

#### Rollout Stages
```
1% → 5% → 10% → 25% → 50% → 100%
```

---

### 7. Database-First Migration
**File**: `app/services/database_first_migration_service.py`
**Status**: FULLY IMPLEMENTED (Week 158)
**Tests**: 55 unit tests

#### Description
Migrate database schema and data first, then application logic. Complete implementation with dual-write support, data validation, and 7-phase migration workflow.

#### Features
- Schema analysis with compatibility scoring (Oracle→PostgreSQL, SQLServer→PostgreSQL)
- DDL script generation with rollback support
- Dual-write modes: SYNC, ASYNC, SHADOW, LEGACY_PRIMARY, NEW_PRIMARY
- Data validation at multiple levels: COUNT_ONLY, CHECKSUM, SAMPLE, FULL, BUSINESS_RULES
- Session management with phase tracking
- Cutover with confirmation requirement
- Cleanup with legacy archival option

#### Migration Phases
1. **ANALYSIS** - Schema analysis & compatibility check
2. **SCHEMA_DEPLOY** - Deploy target schema
3. **DUAL_WRITE_SETUP** - Configure dual-write
4. **INITIAL_SYNC** - Initial data migration
5. **INCREMENTAL_SYNC** - Ongoing sync
6. **VALIDATION** - Data integrity verification
7. **CUTOVER** - Switch to new database
8. **CLEANUP** - Disable dual-write, archive legacy

#### Example
```python
from app.services.database_first_migration_service import (
    DatabaseFirstMigrationService,
    DualWriteConfig,
    DualWriteMode,
    ValidationLevel
)

service = DatabaseFirstMigrationService()

# Create migration session
session = service.create_session("oracle", "postgresql")

# Analyze schema
analysis = await service.analyze_schema(session.session_id, source_connection={...})
print(f"Compatibility: {analysis.compatibility_score}%")

# Deploy schema
scripts = await service.deploy_schema(session.session_id, target_connection={...})

# Setup dual-write
config = DualWriteConfig(mode=DualWriteMode.SYNC)
await service.setup_dual_write(session.session_id, config)

# Sync and validate
await service.sync_data(session.session_id)
validations = await service.validate_data(session.session_id, ValidationLevel.CHECKSUM)

# Cutover and cleanup
await service.execute_cutover(session.session_id, confirm=True)
await service.cleanup(session.session_id)
```

---

## PLANNED PATTERNS (To Implement)

### 8. Anti-Corruption Layer (ACL)
**Priority**: HIGH | **ROI**: 8.5 | **Effort**: 2 weeks

#### Description
Create a translation layer between legacy and new system to prevent legacy concepts from "corrupting" the new domain model.

#### Components
- Translator services
- Facade interfaces
- Domain adapters
- Event mappers

#### Use Cases
- DDD migrations
- Third-party integrations
- Legacy API wrapping
- Protocol translation

#### Implementation Plan
```python
class AntiCorruptionLayer:
    """
    ACL pattern for domain isolation.
    """

    def __init__(self, legacy_adapter: LegacyAdapter):
        self.legacy = legacy_adapter
        self.translators: Dict[str, Translator] = {}

    def translate_to_new_model(self, legacy_entity: Any) -> DomainEntity:
        """Translate legacy entity to new domain model."""
        pass

    def translate_to_legacy(self, domain_entity: DomainEntity) -> Any:
        """Translate new domain entity to legacy format."""
        pass
```

---

### 9. Branch by Abstraction
**Priority**: MEDIUM | **ROI**: 7.5 | **Effort**: 2 weeks

#### Description
Create an abstraction layer over code that needs to change, then swap implementations behind the abstraction.

#### Steps
1. Identify change area
2. Create abstraction interface
3. Wrap existing code
4. Create new implementation
5. Switch to new implementation
6. Remove old code

#### When to Use
- Replacing libraries
- Changing frameworks
- Database technology change
- Service extraction

---

### 10. Bubble Context Pattern
**Priority**: MEDIUM | **ROI**: 7.0 | **Effort**: 2 weeks

#### Description
Create isolated "bubbles" of new code within legacy system, with clear boundaries.

#### Characteristics
- Small, well-defined scope
- Clean interfaces to legacy
- Own data storage (optional)
- Can evolve independently

#### Use Cases
- Greenfield features in brownfield
- Team isolation
- Technology experiments
- DDD bounded contexts

---

### 11. Event Interception Pattern
**Priority**: HIGH | **ROI**: 8.0 | **Effort**: 3 weeks

#### Description
Intercept events/messages from legacy system to trigger new system functionality.

#### Components
- Event interceptor
- Message translator
- Event router
- Dead letter queue

#### Implementation
```python
class EventInterceptor:
    """
    Intercept legacy events and route to new handlers.
    """

    def intercept(self, event: LegacyEvent) -> None:
        translated = self.translate(event)
        self.router.route(translated)

    def translate(self, event: LegacyEvent) -> DomainEvent:
        """Translate legacy event format to domain event."""
        pass
```

---

### 12. Asset Capture Pattern
**Priority**: LOW | **ROI**: 6.5 | **Effort**: 1 week

#### Description
Identify and extract reusable assets from legacy system (business rules, algorithms, data).

#### Assets to Capture
- Business rules
- Validation logic
- Calculation algorithms
- Reference data
- Configuration

---

### 13. Dark Launch Pattern
**Priority**: MEDIUM | **ROI**: 7.5 | **Effort**: 2 weeks

#### Description
Deploy new features to production but hide from users. Test with real traffic without user visibility.

#### Use Cases
- Performance testing
- Integration validation
- Load testing
- Pre-launch confidence

---

### 14. Shadow Traffic Pattern
**Priority**: HIGH | **ROI**: 8.0 | **Effort**: 3 weeks

#### Description
Duplicate production traffic to new system without affecting users. Compare responses for validation.

#### Components
- Traffic duplicator
- Response comparator
- Metrics collector
- Anomaly detector

---

### 15. Contract-First Migration
**Priority**: MEDIUM | **ROI**: 7.0 | **Effort**: 2 weeks

#### Description
Define API contracts first, then implement. Enables parallel development.

#### Steps
1. Define OpenAPI/AsyncAPI spec
2. Generate client stubs
3. Implement endpoints
4. Integration testing
5. Cutover

---

### 16-20. Decomposition Patterns

#### Decompose by Subdomain
Split monolith along DDD subdomain boundaries.

#### Decompose by Business Capability
Split based on business functions (orders, inventory, billing).

#### Extract Service
Pull out specific functionality into independent service.

#### Wrap & Replace
Wrap legacy component, gradually replace internal logic.

---

## PATTERN SELECTION GUIDE

### By System Size

| Size | LOC | Recommended Patterns |
|------|-----|---------------------|
| Small | <10K | Big Bang, Refactoring |
| Medium | 10K-100K | Phased, Branch by Abstraction |
| Large | 100K-1M | Strangler Fig, Decomposition |
| Very Large | >1M | Strangler Fig + Bubble Context |

### By Risk Tolerance

| Risk Level | Patterns |
|------------|----------|
| Low (can afford outage) | Big Bang, Phased |
| Medium | Blue-Green, Canary |
| High (zero tolerance) | Strangler Fig, Parallel Run, Shadow Traffic |

### By Team Size

| Team | Patterns |
|------|----------|
| 1-3 developers | Asset Capture, Refactoring, Incremental |
| 4-8 developers | Strangler Fig, Phased, Branch by Abstraction |
| 8+ developers | Decomposition, Multiple parallel patterns |

### By Timeline

| Timeline | Patterns |
|----------|----------|
| <1 month | Big Bang, Replatforming |
| 1-6 months | Phased, Blue-Green |
| 6-18 months | Strangler Fig, Incremental |
| >18 months | Full decomposition, Multiple patterns |

---

## IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Current)
- [x] Strangler Fig Service
- [x] Feature Flags
- [x] Traffic Splitting
- [x] Health Monitoring
- [x] Migration Planning Orchestrator

### Phase 2: Data Patterns (Week 158) ✅ COMPLETE
- [x] Database-First Migration
- [x] Dual-Write Support
- [x] Data Validation Framework

### Phase 3: Isolation Patterns (Week 162-164)
- [ ] Anti-Corruption Layer
- [ ] Branch by Abstraction
- [ ] Bubble Context

### Phase 4: Event Patterns (Week 165-167)
- [ ] Event Interception
- [ ] Shadow Traffic
- [ ] Dark Launch

### Phase 5: Decomposition (Week 168-172)
- [ ] Decompose by Subdomain
- [ ] Extract Service
- [ ] Service Mesh Integration

---

## REFERENCES

### Books
- "Working Effectively with Legacy Code" - Michael Feathers
- "Refactoring" - Martin Fowler
- "Building Microservices" - Sam Newman
- "Monolith to Microservices" - Sam Newman
- "Domain-Driven Design" - Eric Evans

### Articles
- Martin Fowler: Strangler Fig Application
- Microsoft: Cloud Adoption Framework
- AWS: Migration Strategies (6 R's)
- ThoughtWorks: Technology Radar

### Industry Sources
- PAQT (NL) - Legacy Modernization
- LinkIT (NL) - Low-code Migration
- Netrom (NL) - Enterprise Integration
- XTi (NL) - Cloud Native
- Sogeti (NL) - Application Modernization
- Accenture - Migration Factory

---

## METRICS & SUCCESS CRITERIA

### Migration Health Metrics
- **Error Rate**: < 0.1% during migration
- **Latency Impact**: < 10% increase acceptable
- **Rollback Time**: < 5 minutes
- **Data Consistency**: 100% validation pass

### Progress Metrics
- Components migrated vs total
- Traffic percentage on new system
- Test coverage of migrated code
- Technical debt reduction

---

*Document maintained by: Migration Team*
*Last updated: 2026-01-15*
