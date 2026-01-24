# Product Requirements Document - Change Request
# Change ID: [CHANGE-XXX]
# Generated: [DATE]

---

## Change Overview

**Title**: [Feature/Change title]
**Type**: [New Feature / Enhancement / Refactor / Integration]
**Priority**: [P0 / P1 / P2 / P3]
**Requested by**: [Name or MarQed.ai]
**Requested Date**: [Date]

**Description**: 
[Detailed description of the change/feature]

**Business Value**:
- [Value proposition 1]
- [Value proposition 2]
- [Value proposition 3]

**Success Metrics**:
- [Metric 1: e.g., Reduce processing time by 50%]
- [Metric 2: e.g., Increase user satisfaction score]
- [Metric 3: e.g., Reduce errors by 80%]

---

## Current vs Desired State

**Current Situation**:
[How it works now, what are the pain points]

**Desired Situation**:
[How it should work after implementation]

**Gap Analysis**:
- [Gap 1]
- [Gap 2]
- [Gap 3]

---

## Claude Code Task Configuration

**Task List ID**: `CHANGE-XXX`
**Total Estimated Time**: Varies per feature (4-40 hours typical)
**Parallelization**: High (independent features can run parallel)

**Set environment before starting**:
```bash
export CLAUDE_CODE_TASK_LIST_ID="CHANGE-XXX"
```

**Task Dependencies** (example with 3 features):
```
task-1 (Feature A) → task-4 (Integration Tests)
task-2 (Feature B) → task-4
task-3 (Feature C) → task-4
                 ↓
            task-5 (Regression) → task-6 (Docs)

Parallel opportunities:
- task-1, task-2, task-3 can all run in parallel if independent
- Each feature can have parallel sub-tasks (implementation + tests)
```

---

## Requirements

### Feature 1: [Feature Name]
**Task ID**: `task-1`
**Dependencies**: `[]`
**Can Parallelize**: Yes (if independent from other features)
**Estimated Time**: 4-8 hours
**Priority**: HIGH

**Sub-Tasks** (can be parallelized):
- **task-1a**: Design & Architecture (Dependencies: `[]`)
- **task-1b**: Implementation (Dependencies: `[task-1a]`)
- **task-1c**: Unit Tests (Dependencies: `[task-1b]` - PARALLEL with task-1d)
- **task-1d**: Integration Tests (Dependencies: `[task-1b]` - PARALLEL with task-1c)

**Description**: 
[Detailed description of this feature]

**User Story**:
As a [user type], I want [functionality], so that [benefit].

**Acceptance Criteria**:
1. [ ] [Criterion 1]
2. [ ] [Criterion 2]
3. [ ] [Criterion 3]

**Technical Requirements**:
- [Technical requirement 1]
- [Technical requirement 2]
- [Technical requirement 3]

**UI/UX Requirements** (if applicable):
- [Mockup/wireframe reference]
- [Design specifications]
- [User flow diagram]

**Validation Steps**:
1. [ ] Core functionality implemented
2. [ ] All acceptance criteria met
3. [ ] Unit tests pass (> 80% coverage)
4. [ ] Integration tests pass
5. [ ] UI matches design specifications
6. [ ] No performance degradation
7. [ ] Accessibility requirements met
8. [ ] Security review completed

**Passes**: false

---

### Feature 2: [Feature Name]
**Task ID**: `task-2`
**Dependencies**: `[]` or `[task-1]` if dependent
**Can Parallelize**: Yes/No
**Estimated Time**: 4-8 hours
**Priority**: MEDIUM

**Description**: 
[Detailed description of this feature]

**User Story**:
As a [user type], I want [functionality], so that [benefit].

**Acceptance Criteria**:
1. [ ] [Criterion 1]
2. [ ] [Criterion 2]
3. [ ] [Criterion 3]

**Technical Requirements**:
- [Technical requirement 1]
- [Technical requirement 2]

**Validation Steps**:
1. [ ] Core functionality implemented
2. [ ] All acceptance criteria met
3. [ ] Tests pass
4. [ ] No regressions

**Passes**: false

---

### Feature 3: [Feature Name]
**Task ID**: `task-3`
**Dependencies**: `[]` or `[task-1, task-2]` if dependent
**Can Parallelize**: Yes/No
**Estimated Time**: 4-8 hours
**Priority**: MEDIUM

**Description**: 
[Detailed description of this feature]

**User Story**:
As a [user type], I want [functionality], so that [benefit].

**Acceptance Criteria**:
1. [ ] [Criterion 1]
2. [ ] [Criterion 2]
3. [ ] [Criterion 3]

**Validation Steps**:
1. [ ] Core functionality implemented
2. [ ] All acceptance criteria met
3. [ ] Tests pass
4. [ ] No regressions

**Passes**: false

---

### Integration & E2E Testing
**Task ID**: `task-4`
**Dependencies**: `[task-1, task-2, task-3]`
**Can Parallelize**: Partially (test scenarios can be parallel)
**Estimated Time**: 2-4 hours
**Priority**: HIGH

**Description**: Test all features together and validate end-to-end workflows.

**Tasks**:
- [ ] Test feature interactions
- [ ] Test complete user workflows
- [ ] Cross-browser testing (if web)
- [ ] Performance testing
- [ ] Accessibility testing

**Test Scenarios**:
1. [ ] Happy path workflow
2. [ ] Error scenarios
3. [ ] Edge cases
4. [ ] Cross-feature interactions
5. [ ] Performance under load

**Validation Steps**:
1. [ ] All E2E scenarios pass
2. [ ] Features work together correctly
3. [ ] Performance acceptable
4. [ ] No user experience issues
5. [ ] Works in all supported environments

**Passes**: false

---

### Regression Testing
**Task ID**: `task-5`
**Dependencies**: `[task-4]`
**Can Parallelize**: No
**Estimated Time**: 2-4 hours
**Priority**: CRITICAL

**Description**: Ensure new features don't break existing functionality.

**Tasks**:
- [ ] Run full test suite
- [ ] Test related features
- [ ] Verify no breaking changes
- [ ] Check performance impact
- [ ] Validate data integrity

**Validation Steps**:
1. [ ] All existing tests pass
2. [ ] No regressions detected
3. [ ] Related features still work
4. [ ] Performance not degraded
5. [ ] Data integrity maintained

**Passes**: false

---

### Documentation & Training
**Task ID**: `task-6`
**Dependencies**: `[task-5]`
**Can Parallelize**: No
**Estimated Time**: 1-2 hours
**Priority**: MEDIUM

**Description**: Update all relevant documentation.

**Tasks**:
- [ ] Update user documentation
- [ ] Update API documentation (if applicable)
- [ ] Update technical documentation
- [ ] Create training materials (if needed)
- [ ] Update changelog

**Validation Steps**:
1. [ ] User docs updated and accurate
2. [ ] API docs auto-generated (Swagger)
3. [ ] Technical docs reflect changes
4. [ ] Changelog updated
5. [ ] Training materials ready (if applicable)

**Passes**: false

---

## Success Criteria

The change is complete when:
- [ ] All features marked with `passes: true`
- [ ] All acceptance criteria met
- [ ] All tests passing (unit, integration, E2E)
- [ ] No regression issues detected
- [ ] Documentation updated
- [ ] Performance meets requirements
- [ ] Security review completed
- [ ] Stakeholder sign-off received

---

## Non-Functional Requirements

**Performance**:
- API response time: < 200ms (p95)
- Page load time: < 2s (p95)
- Database query time: < 100ms

**Security**:
- [ ] Input validation implemented
- [ ] Output encoding applied
- [ ] SQL injection prevented
- [ ] XSS prevented
- [ ] CSRF protection applied
- [ ] Authentication/Authorization checked

**Accessibility** (if UI changes):
- [ ] WCAG 2.1 Level AA compliant
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Sufficient color contrast

**Scalability**:
- [ ] Handles expected user load
- [ ] Database queries optimized
- [ ] Caching implemented where appropriate

**Compliance** (if applicable):
- [ ] NEN7510 requirements met
- [ ] GDPR requirements met
- [ ] Audit logging implemented
- [ ] Data encryption applied

---

## Technical Design

**Architecture Changes**:
[Describe any architectural changes or new components]

**Database Changes**:
```sql
-- Add any new tables, columns, or indexes
-- Example:
ALTER TABLE Users ADD COLUMN LastLoginDate DATETIME;
CREATE INDEX IX_Users_LastLoginDate ON Users(LastLoginDate);
```

**API Changes**:
```
GET    /api/[resource]         - [Description]
POST   /api/[resource]         - [Description]
PUT    /api/[resource]/{id}    - [Description]
DELETE /api/[resource]/{id}    - [Description]
```

**Configuration Changes**:
- [Config item 1]
- [Config item 2]

---

## Dependencies & Risks

**External Dependencies**:
- [Dependency 1: e.g., Third-party API]
- [Dependency 2: e.g., Library upgrade]

**Internal Dependencies**:
- [Dependency 1: e.g., Database migration]
- [Dependency 2: e.g., Authentication system]

**Risks & Mitigations**:
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Risk 1] | Low/Med/High | Low/Med/High | [Mitigation strategy] |
| [Risk 2] | Low/Med/High | Low/Med/High | [Mitigation strategy] |

---

## Timeline & Effort

**Estimated Duration**: [X weeks]

| Task | Effort | Duration | Dependencies |
|------|--------|----------|--------------|
| Feature 1 | 4-8h | 1-2 days | None |
| Feature 2 | 4-8h | 1-2 days | None or Feature 1 |
| Feature 3 | 4-8h | 1-2 days | None or Feature 1,2 |
| Integration Testing | 2-4h | 1 day | All features |
| Regression Testing | 2-4h | 1 day | Integration |
| Documentation | 1-2h | 1 day | Regression |

**Total Estimated Effort**: 18-38 hours

---

## MarQed.ai Integration

**Project ID**: [MarQed.ai project ID]
**Function Points**: [Calculated by MarQed.ai]
**Complexity Rating**: [Simple / Medium / Complex]
**Code Quality Impact**: [Expected improvement]

**Estimated Costs**:
- Development: € [amount]
- Testing: € [amount]
- Documentation: € [amount]
- **Total**: € [total]

---

## WBSO R&D Eligibility

**Qualifies for WBSO**: [YES / NO / PARTIAL]

**If YES - R&D Activities**:
- [Technical uncertainty 1]
- [Systematic investigation approach]
- [Experimentation performed]

**Estimated S&O Hours**: [hours] ([percentage]% of total)

---

## MarQed.ai Execution

**Loop Mode**: Enabled
**Max Iterations**: 20
**Self-Validation**: Vercel Agent Browser

**Execution Command**:
```bash
# Initialize change request session
./workflows/marqed-changes.sh --init --change CHANGE-XXX

# Convert PRD to Claude Code tasks
./workflows/common/prd-to-tasks.sh \
    change-CHANGE-XXX/PRD.md \
    ~/.claude/tasks/CHANGE-XXX.json

# Start MarQed loop with Claude Code tasks
export CLAUDE_CODE_TASK_LIST_ID="CHANGE-XXX"
./workflows/marqed-changes.sh --change CHANGE-XXX --iterations 20
```

**Parallel Execution** (for independent features):
```bash
# Spawn parallel agents for independent features
export CLAUDE_CODE_TASK_LIST_ID="CHANGE-XXX"

# Agent 1: Feature 1
claude-code --focus "feature-1" --task-filter "task-1" &

# Agent 2: Feature 2  
claude-code --focus "feature-2" --task-filter "task-2" &

# Agent 3: Feature 3
claude-code --focus "feature-3" --task-filter "task-3" &

wait

# Then run integration testing in single session
claude-code --focus "integration" --task-filter "task-4,task-5,task-6"
```

---

**IMPORTANT**: Only output "PROMISE_COMPLETE" when ALL features above have `passes: true` AND all Claude Code tasks are marked complete.

---

**Template Version**: 2.0 (with Claude Code Tasks)
**Compatible With**: MarQed.ai v2.0, Claude Code Tasks
**Last Updated**: January 2026
