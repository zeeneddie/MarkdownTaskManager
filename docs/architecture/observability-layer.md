# Observability Layer Architecture

**Parent Document:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
**Status:** Week 61 COMPLETE (CCTrace) | Week 76 COMPLETE (Claude-Mem)
**Last Updated:** 2025-12-17

---

## Overview

De Observability Layer biedt deep agent behavior analysis via drie kerncomponenten:
1. **CCTrace Integration** - Thinking blocks, tool I/O, session export
2. **Claude-Mem Session Memory** - Persistent session memory met auto-tagging
3. **Token Cache Metrics** - Cost tracking en optimization

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    UNIFIED OBSERVABILITY LAYER                           │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                      PROVIDER ADAPTERS                              ││
│  │                                                                     ││
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               ││
│  │  │ Claude CLI  │   │ Codex CLI   │   │ Ollama      │               ││
│  │  │ Adapter     │   │ Adapter     │   │ Adapter     │               ││
│  │  │             │   │             │   │             │               ││
│  │  │ • Native    │   │ • Wrapper   │   │ • CoT Force │               ││
│  │  │   thinking  │   │   pseudo-   │   │   thinking  │               ││
│  │  │ • Token     │   │   thinking  │   │ • Timing    │               ││
│  │  │   cache     │   │ • Timing    │   │   metrics   │               ││
│  │  │ • Tool I/O  │   │   metrics   │   │ • Tool I/O  │               ││
│  │  └─────────────┘   └─────────────┘   └─────────────┘               ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                   NORMALIZED OBSERVATION FORMAT                     ││
│  │  {                                                                  ││
│  │    "thinking_blocks": [...],     # Unified across providers         ││
│  │    "tool_executions": [...],     # Complete I/O (geen truncatie)    ││
│  │    "token_metrics": {                                               ││
│  │      "input", "output", "cache_creation", "cache_read"              ││
│  │    },                                                               ││
│  │    "message_tree": {...}         # Parent-child relationships       ││
│  │  }                                                                  ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    SELF-EVOLUTION INTEGRATION                       ││
│  │  ChromaDB: thinking_patterns, tool_usage_patterns, decision_rationales││
│  │  Self-Questioning: "Welke redenering leidde tot succes/falen?"       ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1. CCTrace Integration (Week 61)

**Bronnen:** github.com/jimmc414/cctrace, github.com/alexfazio/cc-trace

### Provider Adapters

| Provider | Thinking Support | Implementation | Token Cache |
|----------|-----------------|----------------|-------------|
| Claude CLI | Native `thinking` blocks | Direct extraction | Native |
| Codex CLI | Pseudo-thinking | Wrapper-based extraction | N/A |
| Ollama | CoT forcing | `<thinking>` tags in prompt | N/A |

### Database Schema

```sql
-- Thinking blocks capture (multi-provider)
CREATE TABLE thinking_blocks (
    id UUID PRIMARY KEY,
    action_id UUID REFERENCES agent_actions(id),
    provider VARCHAR(20) NOT NULL,  -- claude, codex, ollama
    content TEXT NOT NULL,          -- Complete thinking content
    extraction_method VARCHAR(20),   -- native, wrapper, cot_forcing
    created_at TIMESTAMP DEFAULT NOW()
);

-- Complete tool I/O (geen truncatie)
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY,
    action_id UUID REFERENCES agent_actions(id),
    tool_name VARCHAR(100) NOT NULL,
    input_full TEXT,                 -- Complete input
    output_full TEXT,                -- Complete output
    input_tokens INTEGER,
    output_tokens INTEGER,
    execution_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT
);

-- Message relationships (conversation threading)
CREATE TABLE message_relationships (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    message_id UUID NOT NULL,
    parent_message_id UUID,
    sequence_number INTEGER,
    message_type VARCHAR(20)  -- user, assistant, tool_use, tool_result
);

-- Extend agent_actions with cache metrics
ALTER TABLE agent_actions ADD COLUMN token_cache_creation INTEGER DEFAULT 0;
ALTER TABLE agent_actions ADD COLUMN token_cache_read INTEGER DEFAULT 0;
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/observability/thinking/{session_id}` | GET | Get thinking blocks |
| `/api/observability/thinking/patterns/{agent}` | GET | Thinking patterns per agent |
| `/api/observability/tools/{action_id}` | GET | Full tool I/O |
| `/api/observability/tools/stats/{agent}` | GET | Tool usage statistics |
| `/api/observability/export/{session_id}` | POST | Export session (MD/JSON/XML) |
| `/api/observability/messages/{session_id}/tree` | GET | Message tree |

---

## 2. Claude-Mem Session Memory (Week 76)

**Doel:** Persistent session memory for Claude Code/CLI sessions met token-efficient context management.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLAUDE-MEM SESSION MEMORY                             │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    OBSERVATION LAYER                                 ││
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            ││
│  │  │ Auto-Tagging  │  │ Priority      │  │ Source        │            ││
│  │  │ (11 patterns) │  │ (critical →   │  │ Context       │            ││
│  │  │               │  │  → low)       │  │ Tracking      │            ││
│  │  └───────────────┘  └───────────────┘  └───────────────┘            ││
│  │                                                                      ││
│  │  Tags: decision, bugfix, architecture, performance, security,        ││
│  │        refactor, test, documentation, dependency, config, api        ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    CONTEXT WINDOW LAYER                              ││
│  │  ┌───────────────────────────────────────────────────────────────┐  ││
│  │  │ Progressive Disclosure Engine                                  │  ││
│  │  │ • Token budgets: 500 - 32,000 tokens                          │  ││
│  │  │ • Recency weighting (newer = higher priority)                 │  ││
│  │  │ • Priority weighting (critical > high > normal > low)         │  ││
│  │  │ • Automatic truncation within budget                          │  ││
│  │  └───────────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    MEMORY MANAGEMENT LAYER                           ││
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            ││
│  │  │ Compression   │  │ Endless Mode  │  │ Search        │            ││
│  │  │ (LLM-based    │  │ (context      │  │ (full-text +  │            ││
│  │  │  summaries)   │  │  injection)   │  │  tag-based)   │            ││
│  │  └───────────────┘  └───────────────┘  └───────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Auto-Tag Patterns (11)

| Tag | Trigger Pattern | Priority |
|-----|-----------------|----------|
| `decision` | "decided", "chose", "selected" | high |
| `bugfix` | "fixed", "resolved", "bug" | high |
| `architecture` | "design", "structure", "pattern" | high |
| `performance` | "optimize", "speed", "cache" | normal |
| `security` | "vulnerability", "auth", "injection" | critical |
| `refactor` | "refactor", "cleanup", "reorganize" | normal |
| `test` | "test", "coverage", "assertion" | normal |
| `documentation` | "docs", "readme", "comment" | low |
| `dependency` | "package", "version", "upgrade" | normal |
| `config` | "setting", "environment", "config" | normal |
| `api` | "endpoint", "route", "request" | normal |

### Database Schema

```sql
-- Session management
CREATE TABLE claude_mem_sessions (
    id UUID PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    title VARCHAR(255),
    endless_mode BOOLEAN DEFAULT FALSE,
    token_budget INTEGER DEFAULT 4000,
    compression_ratio FLOAT DEFAULT 0.1,
    auto_tag BOOLEAN DEFAULT TRUE,
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Observation storage with auto-tagging
CREATE TABLE claude_mem_observations (
    id UUID PRIMARY KEY,
    session_id VARCHAR(100) REFERENCES claude_mem_sessions(session_id),
    content TEXT NOT NULL,
    tags JSONB DEFAULT '[]',  -- ["decision", "architecture"]
    priority VARCHAR(20) DEFAULT 'normal',
    observation_type VARCHAR(50),  -- insight, decision, error, progress
    source_context TEXT,
    related_files JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Compressed memory summaries
CREATE TABLE claude_mem_summaries (
    id UUID PRIMARY KEY,
    session_id VARCHAR(100) REFERENCES claude_mem_sessions(session_id),
    original_count INTEGER,
    summary TEXT NOT NULL,
    compression_ratio FLOAT,
    token_count INTEGER,
    tags_summary JSONB DEFAULT '{}',  -- {"decision": 5, "bugfix": 3}
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints (17)

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| Sessions | `/api/claude-mem/sessions` | POST | Create new session |
| | `/api/claude-mem/sessions` | GET | List all sessions |
| | `/api/claude-mem/sessions/{id}` | GET | Get session details |
| | `/api/claude-mem/sessions/{id}` | PUT | Update session |
| | `/api/claude-mem/sessions/{id}` | DELETE | Delete session |
| Observations | `/api/claude-mem/sessions/{id}/observations` | POST | Add observation |
| | `/api/claude-mem/sessions/{id}/observations` | GET | List observations |
| Context | `/api/claude-mem/sessions/{id}/context` | GET | Get context window |
| | `/api/claude-mem/sessions/{id}/compress` | POST | Compress memories |
| | `/api/claude-mem/sessions/{id}/endless` | POST | Enable endless mode |
| Statistics | `/api/claude-mem/sessions/{id}/statistics` | GET | Get statistics |
| Search | `/api/claude-mem/search` | POST | Search observations |
| Health | `/api/claude-mem/health` | GET | Service health |

---

## 3. Self-Evolution Integration

De Observability Layer voedt de Self-Evolution Layer:

```
Observations → ChromaDB Collections:
├── thinking_patterns      # Successful reasoning strategies
├── tool_usage_patterns    # Effective tool combinations
├── decision_rationales    # Why certain choices worked
├── error_patterns         # Common failure modes
└── context_preferences    # Optimal context sizes
```

### ChromaDB Collections (5)

| Collection | Purpose | Source |
|------------|---------|--------|
| `thinking_patterns` | Reasoning that led to success | thinking_blocks |
| `tool_usage_patterns` | Tool sequences that work | tool_executions |
| `decision_rationales` | Why decisions were made | claude_mem_observations |
| `error_patterns` | What went wrong | agent_actions (success=false) |
| `context_preferences` | Optimal token budgets | session statistics |

---

## Related Documents

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [self-evolution.md](./self-evolution.md) - Self-Evolution Layer details
- [llm-council.md](./llm-council.md) - LLM Council architecture
