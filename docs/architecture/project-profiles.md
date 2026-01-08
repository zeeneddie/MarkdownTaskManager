# Project Profile Architecture

**Status:** Week 53 COMPLETE
**Impact:** Dynamic agent configuration based on project size and focus areas
**Design:** "One profile, all agents" - Set once at project creation, influences entire lifecycle

---

## Design Filosofie

> **"A small volunteer club app shouldn't be evaluated like an enterprise fintech platform."**

**Kernprincipes:**
1. **Proportionate Evaluation** - Strictness scales with project size
2. **Focus Area Customization** - Emphasize what matters for YOUR project
3. **Preset Templates** - Quick start with common configurations
4. **Lifecycle Consistency** - All agents use same profile throughout

---

## High-Level Architectuur

```
+---------------------------------------------------------------------+
|                     PROJECT PROFILE SYSTEM                           |
|                                                                      |
|  +---------------------------------------------------------------+  |
|  |                    PROJECT PROFILE                             |  |
|  |                                                                |  |
|  |  +------------+  +------------+  +------------+                |  |
|  |  | SIZE       |  | FOCUS      |  | METADATA   |                |  |
|  |  |            |  | AREAS      |  |            |                |  |
|  |  | hobby      |  | security   |  | team_size  |                |  |
|  |  | small      |  | usability  |  | users      |                |  |
|  |  | medium     |  | compliance |  | budget     |                |  |
|  |  | large      |  | ...        |  | timeline   |                |  |
|  |  | enterprise |  |            |  |            |                |  |
|  |  +------------+  +------------+  +------------+                |  |
|  +----------------------------+------------------------------------+  |
|                               |                                      |
|  +---------------------------------------------------------------+  |
|  |                    AGENT CONFIG GENERATOR                      |  |
|  |                                                                |  |
|  |  profile.get_agent_config("quinn") -> AgentConfig {            |  |
|  |    min_quality_score: 5.0,                                     |  |
|  |    critical_issue_threshold: 4,                                |  |
|  |    strictness_by_area: {...},                                  |  |
|  |    context_instructions: "PROJECT SIZE: SMALL\n..."            |  |
|  |  }                                                             |  |
|  +----------------------------+------------------------------------+  |
|                               |                                      |
|  +---------------------------------------------------------------+  |
|  |                    AGENT APPLICATION                           |  |
|  |                                                                |  |
|  |  +----------+ +----------+ +----------+ +----------+           |  |
|  |  | Quinn    | | Felix    | | Eliza    | | All 10   |           |  |
|  |  | (QA)     | |(Architect| |(Estimate)| | Agents   |           |  |
|  |  |          | |          | |          | |          |           |  |
|  |  | Adjusted | | Adjusted | | Adjusted | | Adjusted |           |  |
|  |  | Scoring  | | Review   | | Thresholds| | Behavior|           |  |
|  |  +----------+ +----------+ +----------+ +----------+           |  |
|  +---------------------------------------------------------------+  |
+---------------------------------------------------------------------+
```

---

## Data Model

### ProjectSize Enum

```python
class ProjectSize(str, Enum):
    HOBBY = "hobby"           # 1 dev, <100 users
    SMALL = "small"           # 2-5 devs, <1000 users
    MEDIUM = "medium"         # 5-15 devs, <10K users
    LARGE = "large"           # 15-50 devs, <100K users
    ENTERPRISE = "enterprise" # 50+ devs, 100K+ users
```

### FocusArea Enum

```python
class FocusArea(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    SCALABILITY = "scalability"
    USABILITY = "usability"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    COMPLIANCE = "compliance"
    COST = "cost"
```

### StrictnessLevel Enum

```python
class StrictnessLevel(str, Enum):
    IGNORE = "ignore"      # Don't evaluate
    RELAXED = "relaxed"    # Advisory only
    NORMAL = "normal"      # Standard checks
    STRICT = "strict"      # Thorough review
    CRITICAL = "critical"  # Maximum scrutiny
```

---

## Preset Profiles

| Preset | Size | Focus | Use Case |
|--------|------|-------|----------|
| `hobby` | HOBBY | Relaxed all | Personal projects |
| `club_app` | SMALL | Usability STRICT | Volunteer/club apps |
| `startup_mvp` | SMALL | Cost STRICT | Fast MVP |
| `saas_product` | MEDIUM | Security/Performance STRICT | Production SaaS |
| `fintech` | LARGE | Security/Compliance CRITICAL | Financial services |
| `healthcare` | ENTERPRISE | Security/Compliance CRITICAL | HIPAA apps |

---

## Quinn/Felix Two-Agent Review System

**Implementation:** `backend/app/api/spec_review.py`, `backend/app/services/spec_review_service.py`

```
+---------------------------------------------------------------------+
|                 TWO-AGENT SPECIFICATION REVIEW                       |
|                                                                      |
|  +---------------------------------------------------------------+  |
|  |  STAGE 1: QUINN REVIEW                                         |  |
|  |                                                                |  |
|  |  Specification -> Quinn (QA) -> Suggestions                    |  |
|  |                      |                                         |  |
|  |  - Quality Score (0-10)                                        |  |
|  |  - Suggestions with priority (LOW/MEDIUM/HIGH/CRITICAL)        |  |
|  |  - Profile-adjusted thresholds                                 |  |
|  +---------------------------------------------------------------+  |
|                              |                                       |
|  +---------------------------------------------------------------+  |
|  |  STAGE 2: FELIX PROCESSING                                     |  |
|  |                                                                |  |
|  |  Suggestions -> Felix (Architect) -> Accept/Reject             |  |
|  |                      |                                         |  |
|  |  - Accept suggestion with reasoning                            |  |
|  |  - Reject suggestion with justification                        |  |
|  |  - Escalate if uncertain (confidence < threshold)              |  |
|  +---------------------------------------------------------------+  |
|                              |                                       |
|  +---------------------------------------------------------------+  |
|  |  FINAL OUTCOME                                                 |  |
|  |                                                                |  |
|  |  - auto_approved: Score >= threshold, no critical issues       |  |
|  |  - auto_improved: Suggestions accepted and applied             |  |
|  |  - needs_human_review: Escalated or low consensus              |  |
|  +---------------------------------------------------------------+  |
+---------------------------------------------------------------------+
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/spec-review/profiles` | GET | List available profiles and options |
| `/api/spec-review/profiles/{preset}` | GET | Get preset profile details |
| `/api/spec-review/specifications/{id}/review` | POST | Quinn reviews specification |
| `/api/spec-review/specifications/{id}/full-review` | POST | Full Quinn + Felix cycle |
| `/api/spec-review/health` | GET | Check Ollama model availability |

---

## Integration Points

### Green Paper Integration
- Profile can be set at session creation (`/api/week10/sessions`)
- Stored in `generation_metadata` JSONB column
- Used throughout project lifecycle

### All Agents
- `profile.get_agent_config(agent_name)` returns agent-specific configuration
- Context instructions included in LLM prompts
- Thresholds adjust scoring and escalation logic

---

## Verified Results

**Test: Klaverjas Specification with `club_app` Profile**

| Metric | Without Profile | With Profile |
|--------|-----------------|--------------|
| Quality Score | 4.0/10 | 7.0/10 |
| Status | needs_human_review | auto_improved |
| Suggestions Accepted | 0/7 | 7/7 |
| Min Score Threshold | 6.0 (default) | 5.0 (adjusted) |

---

**Related Documents:**
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [Quality Gates System](./quality-gates.md) - Quality validation rules
- [LLM Council](./llm-council.md) - Multi-model decision making
