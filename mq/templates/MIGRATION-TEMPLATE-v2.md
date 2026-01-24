# Product Requirements Document - Migration
# Migration ID: [MIG-XXX]
# Generated: [DATE]

---

## Migration Overview

**Title**: [Migration title - e.g., "Authentication Module ASP Classic to .NET 8"]
**Type**: [feature / module / service]
**Source System**: [asp-classic / webforms / mixed]
**Target System**: [dotnet-core / dotnet8]
**Project Manager**: [Name or MarQed.ai]
**Started Date**: [Date]

**Description**: 
[Detailed description of what is being migrated and why]

**Business Justification**:
- Technical Debt Reduction
- Performance Improvement
- Security Enhancement
- Developer Productivity
- Future-Proofing

**Scope**:
- In Scope: [List what's included]
- Out of Scope: [List what's NOT included]

---

## Current State Analysis

**Legacy System Details**:
- Technology: [ASP Classic / ASP.NET WebForms / etc.]
- Lines of Code: [Estimate]
- Number of Files: [Estimate]
- Database: [SQL Server version]
- Dependencies: [List critical dependencies]

**Pain Points**:
1. [Pain point 1]
2. [Pain point 2]
3. [Pain point 3]

**Risks**:
- [Risk 1 and mitigation]
- [Risk 2 and mitigation]

---

## Target Architecture

**Modern Stack**:
- Backend: [.NET 8 / .NET Core]
- Frontend: [Razor Pages / Blazor / React]
- API: [REST / GraphQL]
- Database: [Same or migrated]

**Deployment Strategy**: Strangler Fig Pattern
- Legacy and Modern run side-by-side
- Routing layer (IIS URL Rewrite / Nginx)
- Incremental traffic migration
- Zero downtime required

---

## Claude Code Task Configuration

**Task List ID**: `MIG-XXX`
**Total Estimated Time**: 80-200 hours (depends on scope)
**Parallelization**: High (many independent tasks)

**Set environment before starting**:
```bash
export CLAUDE_CODE_TASK_LIST_ID="MIG-XXX"
```

**Task Dependencies** (example for auth module):
```
task-1 (Infrastructure) → task-2 (Authentication) → task-4 (Compliance)
                                    ↓
                               task-3 (Core Module) → task-6 (Integration Tests)
                                    ↓
                               task-5 (Data Migration)
                                    ↓
                               task-7 (Regression Tests) → task-8 (Documentation) → task-9 (Deployment)

Parallel opportunities:
- task-3, task-5 can run parallel after task-2
- task-6 tests can run parallel with task-7
```

---

## Migration Phases

### Phase 1: Infrastructure Setup
**Task ID**: `task-1`
**Dependencies**: `[]`
**Can Parallelize**: No
**Estimated Time**: 8-16 hours
**Priority**: CRITICAL

**Description**: Deploy modern system alongside legacy with routing layer.

**Tasks**:
- [ ] Deploy .NET 8 application alongside legacy
- [ ] Configure IIS URL Rewrite rules (or Nginx)
- [ ] Setup monitoring and logging
- [ ] Configure health checks
- [ ] Test basic connectivity

**Validation Steps**:
1. [ ] Both systems running simultaneously
2. [ ] Routing layer configured correctly
3. [ ] No impact on legacy system performance
4. [ ] Monitoring shows both systems healthy
5. [ ] Can switch traffic between systems via config

**Passes**: false

---

### Phase 2: Authentication Migration
**Task ID**: `task-2`
**Dependencies**: `[task-1]`
**Can Parallelize**: No
**Estimated Time**: 16-24 hours
**Priority**: CRITICAL

**Description**: Implement JWT-based authentication bridge between legacy and modern systems.

**Tasks**:
- [ ] Implement JWT token generation endpoint in .NET 8
- [ ] Configure JWT validation middleware
- [ ] Update legacy login to call JWT endpoint
- [ ] Store JWT in HttpOnly cookie (accessible by both)
- [ ] Test authentication flow end-to-end
- [ ] Implement token refresh mechanism

**Implementation Details**:
```csharp
// JWT generation endpoint (only callable by legacy via internal key)
[HttpPost("api/auth/generate-token")]
public IActionResult GenerateToken([FromBody] TokenRequest request)
{
    // Verify internal auth key
    // Generate JWT with claims
    // Return token
}
```

**Validation Steps**:
1. [ ] Legacy login generates valid JWT
2. [ ] JWT stored in cookie correctly (HttpOnly, Secure)
3. [ ] .NET 8 validates JWT successfully
4. [ ] Legacy can read JWT from cookie
5. [ ] Session bridge works (legacy sessions → JWT)
6. [ ] Logout invalidates JWT in both systems
7. [ ] Token refresh works correctly
8. [ ] Audit logging captures all auth events

**Passes**: false

---

### Phase 3: Core Module Migration
**Task ID**: `task-3`
**Dependencies**: `[task-2]`
**Can Parallelize**: Partially (sub-tasks can be parallel)
**Estimated Time**: 40-80 hours
**Priority**: HIGH

**Sub-Tasks** (can be parallelized):
- **task-3a**: Implement repository layer (Dependencies: `[task-2]`)
- **task-3b**: Implement service layer (Dependencies: `[task-3a]`)
- **task-3c**: Implement API controllers (Dependencies: `[task-3b]`)
- **task-3d**: Implement UI (Dependencies: `[task-3c]`)
- **task-3e**: Write unit tests (Dependencies: `[task-3a, task-3b]` - PARALLEL)
- **task-3f**: Write integration tests (Dependencies: `[task-3c]` - PARALLEL)

**Description**: Migrate core business logic from legacy to modern stack.

**Tasks**:
- [ ] Analyze legacy code patterns (use MarQed.ai)
- [ ] Design modern architecture (Clean Architecture)
- [ ] Implement repository layer (data access)
- [ ] Implement service layer (business logic)
- [ ] Implement API controllers (REST endpoints)
- [ ] Implement UI (Razor Pages/Blazor/React)
- [ ] Ensure business logic parity with legacy
- [ ] Write comprehensive tests

**Architecture Pattern**:
```
Controller → Service → Repository → Database
    ↓
   View/API Response
```

**Validation Steps**:
1. [ ] All CRUD operations work correctly
2. [ ] Business logic matches legacy behavior exactly
3. [ ] Data integrity maintained
4. [ ] Performance acceptable (< 200ms API, < 1s pages)
5. [ ] Unit tests pass (> 80% coverage)
6. [ ] Integration tests pass
7. [ ] UI matches requirements
8. [ ] API documentation generated (Swagger)

**Passes**: false

---

### Phase 4: Compliance & Security
**Task ID**: `task-4`
**Dependencies**: `[task-2, task-3]`
**Can Parallelize**: No
**Estimated Time**: 16-24 hours
**Priority**: CRITICAL

**Description**: Implement NEN7510/ISO27001/GDPR compliance requirements.

**Tasks**:
- [ ] Implement RBAC authorization
- [ ] Implement patient access control (NEN7510)
- [ ] Implement comprehensive audit logging
- [ ] Implement data encryption (AES-256)
- [ ] Implement GDPR data subject rights endpoints
- [ ] Security testing and penetration testing
- [ ] Compliance documentation

**NEN7510 Requirements**:
```csharp
// All patient data access must be logged
await _auditLogger.LogAsync(new AuditEntry
{
    UserId = userId,
    Action = "VIEW_PATIENT",
    ResourceType = "Patient",
    ResourceId = patientId.ToString(),
    Timestamp = DateTime.UtcNow,
    IpAddress = ipAddress
});
```

**Validation Steps**:
1. [ ] Authorization checks work correctly
2. [ ] Unauthorized access blocked and logged
3. [ ] All data access logged (NEN7510 compliant)
4. [ ] Audit logs tamper-proof
5. [ ] Encryption working (TLS 1.3, AES-256)
6. [ ] GDPR data export works
7. [ ] GDPR data deletion respects retention periods
8. [ ] Security scan clean (no vulnerabilities)

**Passes**: false

---

### Phase 5: Data Migration (if needed)
**Task ID**: `task-5`
**Dependencies**: `[task-3]`
**Can Parallelize**: Yes (can run parallel with task-4)
**Estimated Time**: 16-32 hours
**Priority**: MEDIUM

**Description**: Migrate database schema incrementally using compatibility layers.

**Strategy**: Views + INSTEAD OF Triggers
```sql
-- Create new table with improved schema
CREATE TABLE Patients_New (
    PatientId INT PRIMARY KEY,
    FirstName NVARCHAR(100),
    LastName NVARCHAR(100),
    -- ... modern schema
);

-- Create view for legacy compatibility
CREATE VIEW Patients AS
SELECT 
    PatientId,
    FirstName + ' ' + LastName AS PatientName,
    -- ... legacy schema format
FROM Patients_New;

-- INSTEAD OF trigger for INSERT/UPDATE/DELETE
CREATE TRIGGER TR_Patients_Insert
ON Patients INSTEAD OF INSERT AS
BEGIN
    -- Parse legacy format and insert into new table
END;
```

**Tasks**:
- [ ] Design new schema (normalized, best practices)
- [ ] Create compatibility views
- [ ] Implement INSTEAD OF triggers
- [ ] Write data migration scripts
- [ ] Test data integrity
- [ ] Create rollback scripts
- [ ] Document schema changes

**Validation Steps**:
1. [ ] New tables created successfully
2. [ ] Views provide legacy compatibility
3. [ ] Triggers handle legacy DML correctly
4. [ ] Data migration script tested
5. [ ] Data integrity verified (checksums)
6. [ ] Legacy system still works via views
7. [ ] Modern system uses new schema
8. [ ] Rollback tested and works

**Passes**: false

---

### Phase 6: Integration Testing
**Task ID**: `task-6`
**Dependencies**: `[task-3, task-4, task-5]`
**Can Parallelize**: Partially (scenarios can be parallel)
**Estimated Time**: 16-24 hours
**Priority**: HIGH

**Description**: Comprehensive end-to-end testing of migrated functionality.

**Sub-Tasks** (can be parallelized):
- **task-6a**: Authentication flow tests (Dependencies: `[task-4]`)
- **task-6b**: User workflow tests (Dependencies: `[task-3]`)
- **task-6c**: Authorization tests (Dependencies: `[task-4]`)
- **task-6d**: Performance tests (Dependencies: `[task-3]`)

**Tasks**:
- [ ] Create E2E test suite (Vercel Agent Browser)
- [ ] Test all authentication flows
- [ ] Test all user workflows
- [ ] Test authorization matrix
- [ ] Test error handling
- [ ] Performance testing
- [ ] Load testing
- [ ] Cross-browser testing

**Test Scenarios**:
1. [ ] User can login and access authorized resources
2. [ ] Unauthorized access is properly blocked
3. [ ] All CRUD operations work
4. [ ] Business workflows complete successfully
5. [ ] Error messages are user-friendly
6. [ ] Performance meets SLA (< 200ms API)
7. [ ] System handles expected load
8. [ ] Works in all supported browsers

**Validation Steps**:
1. [ ] All E2E tests pass
2. [ ] Authentication flow works end-to-end
3. [ ] All user workflows functional
4. [ ] Authorization matrix validated
5. [ ] Error handling appropriate
6. [ ] Performance meets targets
7. [ ] Load test successful
8. [ ] Cross-browser compatible

**Passes**: false

---

### Phase 7: Regression Testing
**Task ID**: `task-7`
**Dependencies**: `[task-6]`
**Can Parallelize**: No
**Estimated Time**: 16-24 hours
**Priority**: CRITICAL

**Description**: Ensure no regressions in legacy system or related functionality.

**Tasks**:
- [ ] Run full legacy test suite
- [ ] Test legacy-modern integration points
- [ ] Test routing between systems
- [ ] Verify no legacy performance degradation
- [ ] Test legacy data access via views
- [ ] Validate audit logs from both systems
- [ ] Test edge cases and boundary conditions

**Regression Test Areas**:
1. [ ] Legacy system core functionality
2. [ ] Features NOT migrated yet
3. [ ] Legacy-modern authentication bridge
4. [ ] Data consistency between systems
5. [ ] Routing layer behavior
6. [ ] Audit logging from both systems
7. [ ] Performance of both systems

**Validation Steps**:
1. [ ] All legacy tests pass
2. [ ] No regressions introduced
3. [ ] Integration points work correctly
4. [ ] Routing reliable and fast
5. [ ] Both systems can coexist
6. [ ] Audit trail complete and consistent
7. [ ] No data inconsistencies

**Passes**: false

---

### Phase 8: Documentation & Training
**Task ID**: `task-8`
**Dependencies**: `[task-7]`
**Can Parallelize**: Partially (different docs can be parallel)
**Estimated Time**: 8-16 hours
**Priority**: MEDIUM

**Description**: Complete technical and user documentation.

**Sub-Tasks** (can be parallelized):
- **task-8a**: Architecture documentation (Dependencies: `[task-7]`)
- **task-8b**: API documentation (Dependencies: `[task-7]`)
- **task-8c**: Deployment guide (Dependencies: `[task-7]`)
- **task-8d**: User guide (Dependencies: `[task-7]`)

**Tasks**:
- [ ] Update architecture documentation
- [ ] Generate API documentation (Swagger)
- [ ] Write deployment guide
- [ ] Create runbook for operations
- [ ] Update user documentation
- [ ] Create training materials
- [ ] Train development team
- [ ] Train operations team

**Documentation Deliverables**:
- [ ] Architecture diagram (modern system)
- [ ] Migration overview (what changed)
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Deployment guide (step-by-step)
- [ ] Runbook (troubleshooting, monitoring)
- [ ] User guide (end-user facing)
- [ ] Training slides/videos

**Validation Steps**:
1. [ ] Architecture docs accurate and complete
2. [ ] API docs auto-generated and tested
3. [ ] Deployment guide validated (dry run)
4. [ ] Runbook covers common scenarios
5. [ ] User guide reviewed by stakeholders
6. [ ] Team training completed
7. [ ] All documentation accessible

**Passes**: false

---

### Phase 9: Deployment & Cutover
**Task ID**: `task-9`
**Dependencies**: `[task-8]`
**Can Parallelize**: No
**Estimated Time**: 8-16 hours
**Priority**: CRITICAL

**Description**: Deploy to production and gradually migrate traffic.

**Tasks**:
- [ ] Deploy to staging environment
- [ ] User acceptance testing (UAT)
- [ ] Deploy to production (alongside legacy)
- [ ] Update routing rules (10% traffic)
- [ ] Monitor for 24 hours
- [ ] Increase to 50% traffic
- [ ] Monitor for 48 hours
- [ ] Increase to 100% traffic
- [ ] Final monitoring
- [ ] Decommission legacy (later, when stable)

**Gradual Rollout Plan**:
```
Day 1: 10% traffic → Modern, 90% → Legacy
Day 2-3: Monitor metrics, review logs
Day 4: 50% traffic → Modern, 50% → Legacy
Day 5-6: Monitor metrics, review logs
Day 7: 100% traffic → Modern
Week 2-4: Monitor stability
Month 2: Decommission legacy
```

**Rollback Plan**:
```bash
# Immediate rollback (update routing)
# In IIS web.config or Nginx config:
# Change URL rewrite rules to route 100% to legacy
# Takes effect immediately, no code deployment needed
```

**Validation Steps**:
1. [ ] Staging deployment successful
2. [ ] UAT passed by stakeholders
3. [ ] Production deployment successful
4. [ ] Routing updated to 10%
5. [ ] No errors in logs (10% phase)
6. [ ] Performance metrics normal
7. [ ] Increased to 50% successfully
8. [ ] Increased to 100% successfully
9. [ ] Full monitoring dashboard green
10. [ ] Rollback plan tested and ready

**Passes**: false

---

## Success Criteria

The migration is complete when:
- [ ] All phases marked "passes: true"
- [ ] 100% of traffic on modern system
- [ ] Zero critical bugs in production
- [ ] Performance meets or exceeds legacy
- [ ] All compliance requirements met (NEN7510/GDPR)
- [ ] Documentation complete
- [ ] Team trained and confident
- [ ] Legacy system can be decommissioned

---

## Risk Management

**High Risks & Mitigations**:

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Data loss during migration | Low | Critical | Full backups, dry runs, checksums |
| Downtime during cutover | Medium | High | Strangler Fig pattern, gradual rollout |
| Performance degradation | Medium | High | Load testing, monitoring, auto-rollback |
| Security vulnerabilities | Low | Critical | Security testing, pen testing, audits |
| Incomplete business logic | Medium | High | Extensive testing, parallel validation |

**Rollback Triggers**:
- Error rate > 1%
- Response time > 2x legacy
- Any critical bug discovered
- Stakeholder request

---

## Timeline & Effort

**Estimated Duration**: 12-20 weeks (depends on scope)

| Phase | Effort | Duration | Dependencies |
|-------|--------|----------|--------------|
| Phase 1: Infrastructure | 8-16h | 1 week | None |
| Phase 2: Authentication | 16-24h | 1-2 weeks | Phase 1 |
| Phase 3: Core Module | 40-80h | 4-8 weeks | Phase 2 |
| Phase 4: Compliance | 16-24h | 1-2 weeks | Phase 2, 3 |
| Phase 5: Data Migration | 16-32h | 1-3 weeks | Phase 3 |
| Phase 6: Integration Testing | 16-24h | 1-2 weeks | Phase 3, 4, 5 |
| Phase 7: Regression Testing | 16-24h | 1-2 weeks | Phase 6 |
| Phase 8: Documentation | 8-16h | 1 week | Phase 7 |
| Phase 9: Deployment | 8-16h | 2-4 weeks | Phase 8 |

**Total Estimated Effort**: 144-256 hours

---

## MarQed.ai Integration

**Project ID**: [MarQed.ai project ID]
**Analysis File**: [MarQed analysis JSON]

**Function Points**: [Calculated by MarQed.ai]
**Code Complexity**: [From MarQed.ai analysis]
**Technical Debt Score**: [From MarQed.ai]

**Estimated ROI**:
- Development Cost: € [cost]
- Annual Maintenance Savings: € [savings]
- Payback Period: [months]

---

## WBSO R&D Eligibility

**Qualifies for WBSO**: YES

**S&O Classification**:
- Technical Innovation: Strangler Fig pattern implementation
- Technical Uncertainty: 
  - Unknown if legacy business logic can be accurately replicated
  - Uncertainty in dual-system session management
  - Unknown performance characteristics of new architecture
- Systematic Investigation:
  - Analysis of legacy codebase patterns
  - Experimentation with routing strategies
  - Testing of authentication bridge
  - Validation of business logic equivalence

**Estimated S&O Hours**: [hours] ([percentage]% of total)

**R&D Activities**:
1. Legacy code pattern analysis
2. Authentication bridge experimentation
3. Performance optimization research
4. Dual-system coordination methodology

---

## MarQed.ai Execution

**Loop Mode**: Enabled
**Max Iterations**: 50 (migrations take longer)
**Self-Validation**: Vercel Agent Browser + Regression Tests

**Execution Command**:
```bash
# Initialize migration session
./workflows/marqed-migration.sh --init --migration MIG-XXX \
    --type module --source asp-classic --target dotnet8

# Convert PRD to Claude Code tasks
./workflows/common/prd-to-tasks.sh \
    migration-MIG-XXX/PRD.md \
    ~/.claude/tasks/MIG-XXX.json

# Start MarQed loop with Claude Code tasks (parallel agents)
export CLAUDE_CODE_TASK_LIST_ID="MIG-XXX"
./workflows/marqed-migration.sh --migration MIG-XXX --iterations 50 --parallel
```

**Parallel Execution** (for independent tasks):
```bash
# Spawn 3 parallel agents after Phase 2 complete
export CLAUDE_CODE_TASK_LIST_ID="MIG-XXX"

# Agent 1: Core Module
claude-code --focus "core-module" --task-filter "task-3" &

# Agent 2: Data Migration
claude-code --focus "data-migration" --task-filter "task-5" &

# Agent 3: Compliance
claude-code --focus "compliance" --task-filter "task-4" &

wait
```

---

**IMPORTANT**: Only output "PROMISE_COMPLETE" when ALL phases above have `passes: true` AND all Claude Code tasks are marked complete.

---

**Template Version**: 2.0 (with Claude Code Tasks)
**Compatible With**: MarQed.ai v2.0, Claude Code Tasks
**Last Updated**: January 2026
