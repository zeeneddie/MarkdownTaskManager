# Fase 2: Retry, Blocking & Peer Assistance System

**Status**: ✅ COMPLETE
**Implementation Date**: November 13, 2025
**Version**: 1.0.0

## Overview

Fase 2 implements a sophisticated retry mechanism with peer-to-peer assistance for the Agentic Task Management System. When agents encounter blockers, they can receive help from peer agents during daily standups before escalating to human intervention.

## Key Features

### 1. 3-Attempt Retry Logic
- **Exponential Backoff**: 2s → 4s → 8s between retries
- **Configurable**: Max attempts, backoff strategy (linear/exponential/fixed)
- **Feedback Integration**: Each retry includes learnings from previous attempts
- **Status Tracking**: RETRY_1, RETRY_2, RETRY_3 states

### 2. Peer Assistance System
- **6 Assistance Types**:
  - `TIP`: Quick suggestion or tip
  - `RESOURCE`: Share documentation or code examples
  - `TAKEOVER`: Different agent takes over the task
  - `PAIR`: Two agents work together (pair programming)
  - `REVIEW`: Peer reviews work and gives feedback
  - `CONSULT`: Brief consultation or Q&A

- **Confidence-Based Matching**: Agents analyze blockers and offer help if confidence > 0.6
- **Agent Expertise Mapping**: Each of 10 agents has specializations

### 3. Daily Standup Integration
- **Blocker Review**: All blocked tasks are discussed
- **Peer Help Requests**: Agents request assistance from peers
- **Emergency Standups**: Triggered for CRITICAL blockers
- **Metrics Tracking**: Success rate, time saved, escalations

### 4. Human Escalation
- **Last Resort**: Only after peer assistance fails
- **Multi-Channel**: EMAIL, SLACK, WEBHOOK, LOG
- **Priority-Based**: LOW, MEDIUM, HIGH, CRITICAL
- **Immediate Escalation**: BUG and QUALITY_AUDIT work types

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    execute-workflow.ts                       │
│  (Main orchestrator with retry integration)                 │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──► retryHandler.ts
             │    • executeWithRetry()
             │    • 3-attempt logic with exponential backoff
             │    • Feedback loop integration
             │
             ├──► peerAssistance.ts
             │    • requestPeerAssistance()
             │    • selectBestHelper()
             │    • executePeerAssistance()
             │    • Agent expertise matching
             │
             ├──► blockingHandler.ts
             │    • isBlockingIssue()
             │    • escalateToHuman()
             │    • Multi-channel notifications
             │    • Priority determination
             │
             └──► dailyStandup.ts
                  • executeDailyStandup()
                  • triggerEmergencyStandup()
                  • Orchestrates peer help flow
                  • Metrics collection

┌─────────────────────────────────────────────────────────────┐
│                     Type Definitions                         │
├─────────────────────────────────────────────────────────────┤
│  TaskStatus.ts      │  Task status enums, retry config      │
│  Assistance.ts      │  Peer help types, agent expertise     │
└─────────────────────────────────────────────────────────────┘
```

## Files Created

### Type Definitions
1. **types/TaskStatus.ts** (144 lines)
   - Task status enums (PENDING, IN_PROGRESS, RETRY_1/2/3, BLOCKED, etc.)
   - `BlockingIssue` interface
   - `RetryConfig` interface
   - Helper functions: `isRetryState()`, `isBlocked()`, `calculateBackoff()`

2. **types/Assistance.ts** (238 lines)
   - `AssistanceType` enum
   - `AssistanceOffer`, `PeerAssistanceRequest`, `PeerAssistanceResponse` interfaces
   - `AgentExpertise` interface with specializations for 10 agents
   - `calculateRelevance()` function for confidence scoring

### Workflow Implementations
3. **workflows/retryHandler.ts** (308 lines)
   - `executeWithRetry()`: Main retry orchestration
   - `retryWithPeerHelp()`: Retry with peer assistance
   - Exponential backoff calculation
   - Feedback and peer help integration

4. **workflows/peerAssistance.ts** (451 lines)
   - `requestPeerAssistance()`: Find agents willing to help
   - `analyzeAndOfferHelp()`: Calculate relevance and confidence
   - `generateSuggestion()`: Agent-specific tips
   - `findRelevantResources()`: Share documentation and examples
   - `executePeerAssistance()`: Execute help action
   - `updateAgentExpertise()`: Track success rates

5. **workflows/blockingHandler.ts** (323 lines)
   - `isBlockingIssue()`: Detect when task is blocked
   - `escalateToHuman()`: Multi-channel human notification
   - `createBlockingIssue()`: Create structured blocker
   - `formatEscalationMessage()`: Human-readable escalation
   - `canAutoResolve()`: Check for self-correcting errors
   - Priority determination (LOW/MEDIUM/HIGH/CRITICAL)

6. **workflows/dailyStandup.ts** (361 lines)
   - `executeDailyStandup()`: Orchestrate daily ceremony
   - `collectStandupReport()`: Gather agent reports
   - `triggerEmergencyStandup()`: Handle critical blockers
   - Metrics collection and reporting
   - Auto-resolution attempts

### Integration
7. **execute-workflow.ts** (MODIFIED)
   - Added retry mechanism to agent execution
   - Integrated peer assistance flow
   - Track retry statistics
   - New request parameters: `enableRetry`, `enablePeerHelp`, `maxRetries`
   - Enhanced result with `retryStats`, `blockingIssues`, `standupExecuted`

## Agent Expertise Mapping

Each of the 10 agents has specializations for peer assistance:

| Agent   | Specializations                                    | Can Help With                  |
|---------|---------------------------------------------------|--------------------------------|
| Felix   | Architecture, system design, API design           | NEW_FEATURE, ENHANCEMENT       |
| Quinn   | Quality, security, code review                    | QUALITY_AUDIT, QUALITY_IMPROVEMENT |
| Betty   | Debugging, troubleshooting, error analysis        | BUG, runtime errors            |
| Tessa   | Testing, test automation, coverage                | TESTING, test design           |
| Eliza   | Estimation, complexity analysis                   | NEW_FEATURE, scope analysis    |
| Marcus  | Refactoring, tech debt, code quality              | MAINTENANCE, QUALITY_IMPROVEMENT |
| Miguel  | Migration, platform upgrades, data migration      | MIGRATION, compatibility       |
| Diana   | Documentation, technical writing                  | Documentation, clarity         |
| Peter   | Product management, requirements                  | PROJECT_DEFINITION, requirements |
| Paul    | Project planning, resource allocation             | PROJECT_DEFINITION, planning   |

## Flow Examples

### Example 1: Successful Retry After Peer Help

```
1. Felix attempts NEW_FEATURE task
   └─► Attempt 1: FAILED (OAuth configuration error)
   └─► Attempt 2: FAILED (still OAuth issue)
   └─► Attempt 3: FAILED (max attempts reached)
   └─► Status: BLOCKED

2. Emergency Standup Triggered
   └─► Request peer assistance
   └─► Quinn offers TIP (confidence: 0.9)
       "For mobile OAuth, use Authorization Code Flow with PKCE (RFC 7636)"
   └─► Tessa offers RESOURCE (confidence: 0.7)
       OAuth test suite examples
   └─► Select Quinn (highest confidence)

3. Execute Peer Assistance
   └─► Felix retries with Quinn's tip
   └─► Attempt 4: SUCCESS ✅
   └─► Update Quinn's expertise: successRate++

4. Result
   └─► Task completed without human escalation
   └─► Time saved: ~15 minutes
   └─► Knowledge shared across team
```

### Example 2: Escalation to Human

```
1. Betty attempts BUG task (P0 - Critical)
   └─► Attempt 1: FAILED (database connection timeout)
   └─► Attempt 2: FAILED (timeout persists)
   └─► Attempt 3: FAILED (infrastructure issue)
   └─► Status: BLOCKED

2. Emergency Standup Triggered
   └─► Request peer assistance
   └─► No agents confident (infrastructure issue outside agent scope)
   └─► Best offer: Marcus with 0.4 confidence (below 0.6 threshold)

3. Immediate Escalation (BUG = CRITICAL priority)
   └─► Multi-channel notification:
       ✉️  Email to ops@company.com
       💬 Slack to #incidents
       🔗 Webhook to PagerDuty
   └─► Human intervention required

4. Escalation Message Includes
   └─► Full error context
   └─► All 3 attempt details
   └─► Peer assistance attempted: YES
   └─► Suggested actions:
       - Check database connection pool
       - Verify network connectivity
       - Review recent infrastructure changes
```

## API Changes

### execute-workflow.ts Request

**New Optional Parameters**:
```typescript
interface ExecuteRequest {
  description: string;
  context?: Record<string, any>;
  priority?: string;

  // NEW in Fase 2:
  enableRetry?: boolean;        // Default: true
  enablePeerHelp?: boolean;     // Default: true
  maxRetries?: number;          // Default: 3
}
```

**Example Usage**:
```bash
# With default settings (retry enabled, peer help enabled, 3 attempts)
echo '{"description": "Implement OAuth login"}' | npx ts-node execute-workflow.ts

# Disable retry (direct execution)
echo '{
  "description": "Quick analysis task",
  "enableRetry": false
}' | npx ts-node execute-workflow.ts

# Custom retry settings
echo '{
  "description": "Complex migration",
  "maxRetries": 5,
  "enablePeerHelp": true
}' | npx ts-node execute-workflow.ts
```

### execute-workflow.ts Response

**Enhanced Result**:
```typescript
interface ExecuteResult {
  workType: string;
  status: 'success' | 'failed' | 'partial' | 'blocked';  // Added 'blocked'

  agentsExecuted: Array<{
    name: string;
    role: string;
    output: Record<string, any>;
    executionTime: number;
    status: 'success' | 'failed' | 'skipped' | 'retry' | 'blocked';  // Added 'retry', 'blocked'

    // NEW in Fase 2:
    attempts?: number;           // Number of retry attempts
    peerHelpUsed?: boolean;      // Whether peer help was used
    peerHelpers?: string[];      // Names of agents who helped
  }>;

  result: Record<string, any>;
  error?: string;

  // NEW in Fase 2:
  retryStats?: {
    totalRetries: number;
    successAfterRetry: number;
    peerHelpInvoked: number;
    blockedTasks: number;
  };
  blockingIssues?: BlockingIssue[];
  standupExecuted?: boolean;
}
```

**Example Response**:
```json
{
  "workType": "NEW_FEATURE",
  "status": "success",
  "agentsExecuted": [
    {
      "name": "Felix",
      "role": "Software Architect",
      "output": { "phase": 1, "completed": true },
      "executionTime": 12.45,
      "status": "success",
      "attempts": 2,
      "peerHelpUsed": true,
      "peerHelpers": ["Quinn"]
    },
    {
      "name": "Eliza",
      "role": "Estimation Engineer",
      "output": { "phase": 2, "completed": true },
      "executionTime": 3.21,
      "status": "success",
      "attempts": 1
    }
  ],
  "result": {
    "workType": "NEW_FEATURE",
    "agentsCompleted": 5,
    "agentsTotal": 5,
    "totalExecutionTime": 45.67,
    "retryStats": {
      "totalRetries": 1,
      "successAfterRetry": 1,
      "peerHelpInvoked": 1,
      "blockedTasks": 0
    }
  },
  "retryStats": {
    "totalRetries": 1,
    "successAfterRetry": 1,
    "peerHelpInvoked": 1,
    "blockedTasks": 0
  },
  "standupExecuted": true
}
```

## Configuration

### Retry Configuration

```typescript
// types/TaskStatus.ts
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  backoffStrategy: 'exponential',  // 'linear' | 'exponential' | 'fixed'
  backoffMultiplier: 2,            // 2^n * 1000ms
  enablePeerHelp: true,
  escalateAfterFailedPeerHelp: true
};
```

### Escalation Configuration

```typescript
// workflows/blockingHandler.ts
export const DEFAULT_ESCALATION_CONFIG: EscalationConfig = {
  channels: [
    { type: 'LOG', destination: 'console', enabled: true }
    // Add more channels in production:
    // { type: 'EMAIL', destination: 'ops@company.com', enabled: true }
    // { type: 'SLACK', destination: '#incidents', enabled: true }
    // { type: 'WEBHOOK', destination: 'https://pagerduty.com/api', enabled: true }
  ],
  immediateEscalation: ['BUG', 'QUALITY_AUDIT'],  // No delay for these work types
  escalationDelay: 0  // Minutes to wait before escalating
};
```

## Testing

### Manual Testing

1. **Test Successful Retry**:
```bash
cd /home/eddie/Projects/MarkdownTaskManager/backend/agents

# Test with retry enabled (default)
echo '{
  "description": "Test retry mechanism",
  "context": { "testRetry": true }
}' | npx ts-node execute-workflow.ts
```

2. **Test Peer Assistance**:
```bash
# Simulate blocker requiring peer help
echo '{
  "description": "Complex OAuth implementation",
  "context": { "complexity": "high" },
  "enablePeerHelp": true
}' | npx ts-node execute-workflow.ts
```

3. **Test Escalation**:
```bash
# Critical bug that should escalate immediately
echo '{
  "description": "Critical database connection issue",
  "context": { "severity": "P0" },
  "priority": "CRITICAL"
}' | npx ts-node execute-workflow.ts
```

### Integration Testing

The FastAPI backend automatically integrates with the retry system:

```bash
# Start backend
cd /home/eddie/Projects/MarkdownTaskManager/backend
source .venv/bin/activate
uvicorn app.main:app --reload

# Test via API
curl -X POST http://localhost:8000/api/v1/agents/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "work_type": "NEW_FEATURE",
    "description": "Implement user authentication",
    "context": {},
    "enable_retry": true,
    "enable_peer_help": true,
    "max_retries": 3
  }'
```

## Metrics & Monitoring

The system tracks:

1. **Retry Metrics**:
   - Total retry attempts
   - Success rate after retry
   - Average attempts per task
   - Blocker frequency by work type

2. **Peer Assistance Metrics**:
   - Peer help invocation rate
   - Success rate by assistance type
   - Most helpful agents
   - Time saved by peer help

3. **Escalation Metrics**:
   - Escalation frequency
   - Escalation by priority
   - Time to resolution
   - Human intervention rate

## Performance Impact

- **No Retry**: ~2-5s per agent (baseline)
- **1st Retry**: +2s backoff (4-7s total)
- **2nd Retry**: +4s backoff (8-11s total)
- **3rd Retry**: +8s backoff (16-19s total)
- **Peer Help**: +5-15s (standup + retry)
- **Escalation**: +0-5s (notification)

**Trade-off**: Longer execution time for higher success rate and reduced human intervention.

## Next Steps (Fase 2 Week 6 Day 3-5)

1. **Scrum Ceremonies**: Implement remaining ceremonies
   - Sprint Planning
   - Sprint Review
   - Sprint Retrospective

2. **Quality Gates**: Add validation after each agent phase
   - Output quality checks
   - Acceptance criteria validation
   - Automated feedback generation

3. **Enhanced Metrics**: Add dashboards and reporting
   - Real-time retry statistics
   - Peer assistance effectiveness
   - Blocker trend analysis

## Troubleshooting

### Common Issues

1. **Ollama API Key Error**:
   ```
   Error: API key is missing
   ```
   **Solution**: Configure Ollama in agent llmConfig or set environment variable:
   ```bash
   export OLLAMA_BASE_URL="http://localhost:11434"
   ```

2. **Peer Assistance Not Triggered**:
   - Check `enablePeerHelp` is `true`
   - Verify agents have expertise mapping
   - Ensure confidence threshold > 0.6

3. **Escalation Not Working**:
   - Check escalation channels are enabled
   - Verify work type in `immediateEscalation` list
   - Review escalation logs in console

## Conclusion

Fase 2 successfully implements a sophisticated retry and peer assistance system that:
- ✅ Reduces human intervention by enabling agent-to-agent help
- ✅ Improves success rates through retry with feedback
- ✅ Maintains knowledge sharing across the agent team
- ✅ Provides structured escalation when human help is truly needed
- ✅ Tracks comprehensive metrics for continuous improvement

**Total Lines of Code**: ~1,825 lines
**Compilation**: ✅ Successful
**Integration**: ✅ Complete
**Testing**: 🔄 Ready for manual testing

---

**Documentation Version**: 1.0.0
**Last Updated**: November 13, 2025
**Maintained By**: Agentic Task Management Team
