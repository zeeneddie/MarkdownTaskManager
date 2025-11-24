# Week 13 - Agent Dashboard Testing Guide

**Created**: 2025-11-16
**Purpose**: Test checklist for Agent Dashboard UI (Week 13 Day 1-2 deliverable)

---

## 📋 Prerequisites

1. **Backend Server Running**:
   ```bash
   cd /home/eddie/Projects/MarkdownTaskManager/backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Browser Access**:
   ```
   Open: http://localhost:8000/frontend/agent-dashboard.html
   or: file:///home/eddie/Projects/MarkdownTaskManager/frontend/agent-dashboard.html
   ```

3. **Check API Endpoints**:
   ```bash
   # Verify agents endpoint
   curl http://localhost:8000/api/workflows/agents

   # Verify statistics endpoint
   curl http://localhost:8000/api/workflows/statistics
   ```

---

## ✅ Test Checklist

### 1. Page Load & UI Components

- [ ] Page loads without errors
- [ ] Header displays correctly with navigation links
- [ ] Agent status cards are visible
- [ ] Workflow execution form is present
- [ ] Statistics dashboard is visible
- [ ] No console errors (press F12 to check)

### 2. Agent Status Display

Verify that all 10 agents are displayed:

- [ ] **Felix** - Feature Architect (qwen2.5-coder:7b)
- [ ] **Marcus** - Maintenance Specialist (qwen2.5-coder:7b)
- [ ] **Quinn** - Quality Inspector (deepseek-r1:latest)
- [ ] **Betty** - Bug Hunter (codellama:latest)
- [ ] **Eliza** - Estimation Engine (deepseek-r1:latest)
- [ ] **Tessa** - Test Engineer (qwen2.5-coder:7b)
- [ ] **Miguel** - Migration Architect (qwen2.5-coder:7b)
- [ ] **Diana** - Documentation Writer (mistral:latest)
- [ ] **Peter** - Product Owner (deepseek-r1:latest)
- [ ] **Paul** - Project Lead (qwen2.5:7b)

**For each agent, verify**:
- [ ] Name displays correctly
- [ ] Role displays correctly
- [ ] Description is shown
- [ ] Status badge shows (ready/not_configured/error)
- [ ] Tools count is visible
- [ ] Ready checkmark displays when status is "ready"

### 3. Live Polling (3-second updates)

- [ ] Agent status updates every 3 seconds
- [ ] Statistics refresh automatically
- [ ] No flickering or UI jumps
- [ ] Network tab shows polling requests (F12 → Network)

### 4. Test All 9 Work Types

#### 4.1 NEW_FEATURE

**Test Input**:
- Work Type: `NEW_FEATURE`
- Description: `Build user authentication system with OAuth2 support`
- Priority: `Medium`

**Expected**:
- [ ] Workflow executes successfully
- [ ] Shows agent timeline (Peter → Felix → Diana)
- [ ] Displays constitution, specification, tasks
- [ ] Execution time shown
- [ ] Status: success

#### 4.2 MAINTENANCE

**Test Input**:
- Work Type: `MAINTENANCE`
- Description: `Update all npm dependencies and refactor deprecated code`
- Priority: `Low`

**Expected**:
- [ ] Workflow executes (Marcus → Quinn → Tessa → Eliza)
- [ ] Shows maintenance plan
- [ ] Audit results displayed
- [ ] Status: success

#### 4.3 BUG

**Test Input**:
- Work Type: `BUG`
- Description: `Fix login page throwing 500 error when password is empty`
- Priority: `Critical`

**Expected**:
- [ ] Workflow executes (Betty → Tessa → Diana)
- [ ] Shows bug analysis
- [ ] Fix recommendations displayed
- [ ] Test plan included
- [ ] Status: success

#### 4.4 QUALITY_AUDIT

**Test Input**:
- Work Type: `QUALITY_AUDIT`
- Description: `Security audit for payment processing module`
- Priority: `High`

**Expected**:
- [ ] Workflow executes (Quinn → Felix → Marcus)
- [ ] Shows SuperClaude integration results
- [ ] Quality scores displayed
- [ ] Remediation plan included
- [ ] Status: success

#### 4.5 ENHANCEMENT

**Test Input**:
- Work Type: `ENHANCEMENT`
- Description: `Add dark mode theme to user dashboard`
- Priority: `Medium`

**Expected**:
- [ ] Workflow executes (Felix → Tessa → Diana)
- [ ] Design improvements shown
- [ ] Test coverage plan displayed
- [ ] Status: success

#### 4.6 MIGRATION

**Test Input**:
- Work Type: `MIGRATION`
- Description: `Migrate from Python 3.9 to Python 3.11`
- Priority: `Medium`

**Expected**:
- [ ] Workflow executes (Miguel → Felix → Tessa → Diana)
- [ ] Migration plan displayed
- [ ] Risk assessment shown
- [ ] Compatibility checks included
- [ ] Status: success

#### 4.7 QUALITY_IMPROVEMENT

**Test Input**:
- Work Type: `QUALITY_IMPROVEMENT`
- Description: `Reduce technical debt in user service module`
- Priority: `Low`

**Expected**:
- [ ] Workflow executes (Quinn → Marcus → Tessa)
- [ ] Code quality metrics shown
- [ ] Refactoring recommendations displayed
- [ ] Status: success

#### 4.8 TESTING

**Test Input**:
- Work Type: `TESTING`
- Description: `Improve test coverage for API endpoints to 80%`
- Priority: `Medium`

**Expected**:
- [ ] Workflow executes (Tessa → Quinn → Diana)
- [ ] Test strategy displayed
- [ ] Coverage analysis shown
- [ ] Test cases generated
- [ ] Status: success

#### 4.9 PROJECT_DEFINITION

**Test Input**:
- Work Type: `PROJECT_DEFINITION`
- Description: `Define new e-commerce platform for SMB market`
- Priority: `High`
- Context: `Budget: €50k, Timeline: 6 months, Team: 5 devs`

**Expected**:
- [ ] Workflow executes (Peter → Felix → Paul → Diana)
- [ ] Complete project charter displayed
- [ ] Architecture plan shown
- [ ] Epics, features, stories generated
- [ ] Folder structure created
- [ ] Status: success

### 5. Statistics Dashboard

After executing several workflows:

- [ ] Total Workflows count increases
- [ ] Success Rate displays correctly (0-100%)
- [ ] Avg Execution Time updates
- [ ] Workflows by Type pie chart populates
- [ ] Work type breakdown shows all executed types
- [ ] Counts match actual executions

### 6. Results Display

For each workflow execution:

- [ ] Work Type is shown
- [ ] Agent timeline displays (agent names with arrows)
- [ ] Total execution time is shown
- [ ] Status is visible (success/failed/partial)
- [ ] Result data is formatted (JSON)
- [ ] Errors are displayed (if any)
- [ ] Timestamp is accurate

### 7. Form Validation

- [ ] Cannot submit without work type
- [ ] Cannot submit without description
- [ ] Priority defaults to "Medium"
- [ ] Context is optional
- [ ] Button disables during execution
- [ ] Loading spinner shows during execution

### 8. Error Handling

**Test backend offline**:
- [ ] Shows error alert when backend is down
- [ ] Friendly error message displayed
- [ ] UI doesn't crash

**Test invalid input**:
- [ ] Empty description shows validation error
- [ ] Very long description (>10,000 chars) handled

**Test network timeout**:
- [ ] Timeout handled gracefully
- [ ] Error message displayed
- [ ] Button re-enabled

### 9. Responsive Design

- [ ] Desktop (1920x1080) - all elements visible
- [ ] Laptop (1366x768) - no horizontal scroll
- [ ] Tablet (768x1024) - grid adapts to 1 column
- [ ] Mobile (375x667) - readable and usable

### 10. Performance

- [ ] Initial page load < 1 second
- [ ] Agent card rendering < 500ms
- [ ] Workflow execution response time depends on backend
- [ ] Polling doesn't slow down page
- [ ] No memory leaks (check after 5 minutes of polling)

---

## 🐛 Common Issues & Solutions

### Issue: "Failed to load agent status"

**Cause**: Backend not running or wrong port

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/api/workflows/agents

# If not, start backend
cd backend
uvicorn app.main:app --reload --port 8000
```

### Issue: "No agents available"

**Cause**: Agent service not initialized or Ollama not running

**Solution**:
```bash
# Check Ollama
ollama list

# Pull required models
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1:latest
ollama pull codellama:latest
ollama pull mistral:latest
ollama pull qwen2.5:7b

# Restart backend
```

### Issue: Workflow execution fails immediately

**Cause**: Work type classification error or agent initialization failed

**Solution**:
- Check backend logs for errors
- Verify all agents are "ready" status
- Try simpler description first

### Issue: Statistics not updating

**Cause**: Polling stopped or API endpoint error

**Solution**:
- Check console for errors (F12)
- Verify `/api/workflows/statistics` endpoint
- Refresh page to restart polling

---

## 📊 Success Criteria (Week 13 Day 2)

✅ **Agent Dashboard Complete** when:

1. All 10 agents display correctly
2. All 9 work types execute successfully
3. Results display properly for each type
4. Statistics update in real-time
5. UI is responsive and performant
6. No console errors
7. Polling works for 10+ minutes without issues

---

## 📝 Test Results Log

**Date**: _______________
**Tester**: _______________

| Work Type | Status | Execution Time | Notes |
|-----------|--------|----------------|-------|
| NEW_FEATURE | ☐ Pass ☐ Fail | _____s | |
| MAINTENANCE | ☐ Pass ☐ Fail | _____s | |
| BUG | ☐ Pass ☐ Fail | _____s | |
| QUALITY_AUDIT | ☐ Pass ☐ Fail | _____s | |
| ENHANCEMENT | ☐ Pass ☐ Fail | _____s | |
| MIGRATION | ☐ Pass ☐ Fail | _____s | |
| QUALITY_IMPROVEMENT | ☐ Pass ☐ Fail | _____s | |
| TESTING | ☐ Pass ☐ Fail | _____s | |
| PROJECT_DEFINITION | ☐ Pass ☐ Fail | _____s | |

**Overall Result**: ☐ PASS ☐ FAIL

**Issues Found**:
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

---

## 🚀 Next Steps (Week 13 Day 3-5)

After Agent Dashboard is tested and working:

1. **Function Point Calculator** (backend)
   - Implement IFPUG methodology
   - Create `/api/estimation/function-points` endpoint
   - Test with historical data

2. **Integration**
   - Add Function Point calculator link to Agent Dashboard
   - Test FP calculation from UI
   - Document FP calculator usage

---

**Last Updated**: 2025-11-16
**Version**: 1.0
**Status**: Ready for testing
