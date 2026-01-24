# Bug Fix PRD Template - MarQed.ai Methodology

**Project**: [Project Name]  
**Bug ID**: [BUG-YYYY-MM-DD-NNN]  
**Priority**: [Critical/High/Medium/Low]  
**Reported**: [Date]  
**Reporter**: [Name/System]

---

## 🐛 Bug Description

### Summary
[Clear, concise description of the bug]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Impact
- **Users Affected**: [Number/Percentage]
- **Severity**: [Business impact]
- **Workaround Available**: [Yes/No - describe if yes]

---

## 🎯 Root Cause Analysis

### Investigation Findings
[What was discovered during investigation]

### Root Cause
[The underlying cause of the bug]

### Related Code/Components
- [File/Module 1]
- [File/Module 2]
- [File/Module 3]

---

## 🔧 Solution Design

### Approach
[High-level description of the fix]

### Changes Required
1. [Change 1]
2. [Change 2]
3. [Change 3]

### Risk Assessment
- **Regression Risk**: [Low/Medium/High]
- **Areas of Concern**: [List potential side effects]
- **Mitigation Strategy**: [How to minimize risk]

---

## ✅ Validation Phases

### Phase 1: Root Cause Verification
**Duration**: ~30 minutes  
**Objective**: Confirm the root cause is correctly identified

**Tasks**:
```json
{
  "id": "bug-phase1-verify",
  "title": "Verify root cause of bug",
  "description": "Analyze code and logs to confirm root cause",
  "dependencies": [],
  "estimatedTime": "30m",
  "parallelizable": false
}
```

**Validation**:
- [ ] Root cause clearly identified and documented
- [ ] Supporting evidence (logs, stack traces) collected
- [ ] Code path to bug traced and understood

**Passes**: false  
**Notes**: []

---

### Phase 2: Fix Implementation
**Duration**: ~2 hours  
**Objective**: Implement the bug fix

**Tasks**:
```json
{
  "id": "bug-phase2-implement",
  "title": "Implement bug fix",
  "description": "Write code to fix the identified bug",
  "dependencies": ["bug-phase1-verify"],
  "estimatedTime": "2h",
  "parallelizable": false
}
```

**Validation**:
- [ ] Code changes implement the planned fix
- [ ] Code follows project style guidelines
- [ ] No obvious new bugs introduced
- [ ] Error handling is appropriate

**Passes**: false  
**Notes**: []

---

### Phase 3: Unit Testing
**Duration**: ~1 hour  
**Objective**: Create tests that verify the fix

**Tasks**:
```json
{
  "id": "bug-phase3-unittest",
  "title": "Write unit tests for bug fix",
  "description": "Create tests that would have caught this bug",
  "dependencies": ["bug-phase2-implement"],
  "estimatedTime": "1h",
  "parallelizable": false
}
```

**Validation**:
- [ ] Test reproduces the original bug (fails before fix)
- [ ] Test passes with the fix applied
- [ ] Test covers edge cases
- [ ] Test is maintainable and clear

**Passes**: false  
**Notes**: []

---

### Phase 4: Integration Testing
**Duration**: ~1 hour  
**Objective**: Verify fix works in broader context

**Tasks**:
```json
{
  "id": "bug-phase4-integration",
  "title": "Run integration tests",
  "description": "Test fix in integration with other components",
  "dependencies": ["bug-phase3-unittest"],
  "estimatedTime": "1h",
  "parallelizable": false
}
```

**Validation**:
- [ ] All existing tests still pass
- [ ] Integration with dependent modules verified
- [ ] No performance regressions detected
- [ ] Cross-component interactions work correctly

**Passes**: false  
**Notes**: []

---

### Phase 5: Regression Testing
**Duration**: ~1.5 hours  
**Objective**: Ensure no new bugs introduced

**Tasks**:
```json
{
  "id": "bug-phase5-regression",
  "title": "Execute regression test suite",
  "description": "Run full regression tests to catch side effects",
  "dependencies": ["bug-phase4-integration"],
  "estimatedTime": "1.5h",
  "parallelizable": false
}
```

**Validation**:
- [ ] Full regression suite passes
- [ ] No new test failures
- [ ] Performance benchmarks stable
- [ ] Memory/resource usage normal

**Passes**: false  
**Notes**: []

---

### Phase 6: Code Review & Documentation
**Duration**: ~45 minutes  
**Objective**: Peer review and documentation update

**Tasks**:
```json
{
  "id": "bug-phase6-review",
  "title": "Code review and documentation",
  "description": "Get peer review and update docs",
  "dependencies": ["bug-phase5-regression"],
  "estimatedTime": "45m",
  "parallelizable": false
}
```

**Validation**:
- [ ] Code reviewed by peer/senior developer
- [ ] Review comments addressed
- [ ] Documentation updated (if needed)
- [ ] Changelog entry added

**Passes**: false  
**Notes**: []

---

### Phase 7: Deployment Preparation
**Duration**: ~30 minutes  
**Objective**: Prepare fix for deployment

**Tasks**:
```json
{
  "id": "bug-phase7-deploy-prep",
  "title": "Prepare deployment package",
  "description": "Create deployment artifacts and rollback plan",
  "dependencies": ["bug-phase6-review"],
  "estimatedTime": "30m",
  "parallelizable": false
}
```

**Validation**:
- [ ] Deployment package created
- [ ] Rollback plan documented
- [ ] Deployment steps verified
- [ ] Monitoring plan in place

**Passes**: false  
**Notes**: []

---

## 📊 Metrics & Tracking

### Effort Estimation
- **Total Estimated Time**: ~7.25 hours
- **Actual Time Spent**: [TBD]
- **Variance**: [TBD]

### Quality Metrics
- **Tests Added**: [Number]
- **Test Coverage**: [Percentage]
- **Code Review Score**: [TBD]

### Success Criteria
- [ ] Bug no longer reproducible
- [ ] All tests pass (unit + integration + regression)
- [ ] No new bugs introduced
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Deployment successful

---

## 📝 Post-Deployment

### Monitoring
- **Metrics to Watch**: [List key metrics]
- **Alert Thresholds**: [Define alerts]
- **Monitoring Period**: [Duration]

### Verification
- [ ] Bug confirmed fixed in production
- [ ] No related incidents reported
- [ ] Performance metrics normal
- [ ] User feedback positive

### Lessons Learned
[What can we learn to prevent similar bugs?]

---

## 🔄 MarQed.ai Workflow Integration

This bug fix follows the MarQed.ai methodology:

1. **Initialization**: `prd-to-tasks.sh` converts this PRD to Claude Code tasks
2. **Execution**: `marqed-bugfix.sh` runs the bug fix workflow
3. **Validation**: Each phase validated before progression
4. **Persistence**: All state tracked in Claude Code tasks
5. **Reporting**: Auto-generated WBSO reports from task completion

### Task List ID
```bash
TASK_LIST_ID="BUG-[YYYY-MM-DD-NNN]"
```

### Related Files
- **Workflow Script**: `workflows/marqed-bugfix.sh`
- **Prompt**: `templates/prompts/prompt-bugfix.md`
- **Settings**: `settings/settings-bugfix.json`

---

**Template Version**: 2.0  
**Last Updated**: January 23, 2026  
**Methodology**: MarQed.ai AI-Driven Development