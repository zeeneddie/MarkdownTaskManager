# Confucius Code Agent Orchestrator Integration Plan

**Project:** MarQed AI Agent Software Platform
**Document Version:** 2.0
**Created:** 2026-01-12
**Updated:** 2026-01-14
**Status:** ✅ COMPLETE
**Target Phase:** Fase 23.5 (Week 149-154)
**Actual Completion:** Week 153-154
**Effort:** 120 uur (~6 weken)
**Prerequisites:** Fase 21.5 (Workflow Separation), Fase 22 (FP Methodology)

---

## Executive Summary

Dit document beschrijft de integratie van de **Confucius Code Agent (CCA)** als centrale orchestrator voor het MarQed platform. CCA, ontwikkeld door Meta en Harvard (december 2025), biedt state-of-the-art agent scaffolding met hierarchisch geheugen, cross-session learning, en modulaire extensies.

**Doel:** Vervang de huidige ad-hoc agent orchestration door de Confucius SDK om:
- 40%+ context reductie via adaptive compression
- Cross-session learning voor alle 11 agents
- Unified execution loop met quality gates
- Modulaire tool integratie via extension hooks

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Target Architecture](#2-target-architecture)
3. [Integration Strategy](#3-integration-strategy)
4. [Week-by-Week Implementation Plan](#4-week-by-week-implementation-plan)
5. [Technical Specifications](#5-technical-specifications)
6. [Agent Migration Plan](#6-agent-migration-plan)
7. [Extension Development](#7-extension-development)
8. [Memory Architecture](#8-memory-architecture)
9. [Quality Gate Integration](#9-quality-gate-integration)
10. [API Changes](#10-api-changes)
11. [Database Schema](#11-database-schema)
12. [Testing Strategy](#12-testing-strategy)
13. [Rollout Strategy](#13-rollout-strategy)
14. [Risk Mitigation](#14-risk-mitigation)
15. [Success Metrics](#15-success-metrics)
16. [Dependencies](#16-dependencies)
17. [References](#17-references)

---

## 1. Current State Analysis

### 1.1 Huidige Agent Architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│                   CURRENT STATE (AD-HOC)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐    Direct Calls    ┌─────────────────────┐   │
│   │   API       │ ──────────────────▶│     Individual      │   │
│   │  Endpoints  │                    │      Agents         │   │
│   └─────────────┘                    └─────────────────────┘   │
│                                              │                   │
│   Problems:                                  │                   │
│   ├── No shared memory                       │                   │
│   ├── No cross-session learning              │                   │
│   ├── Context loaded per-request             │                   │
│   ├── No unified quality gates               │                   │
│   └── Manual agent coordination              │                   │
│                                                                  │
│   Agents (11):                                                   │
│   Felix (Architect) | Quinn (Quality) | Betty (Business)        │
│   Eliza (Estimation) | Diana (Documentation) | Marcus (Migration)│
│   Tessa (Testing) | Miguel (Metrics) | Peter (Product Owner)    │
│   Paul (Planning) | Vicky (Validation)                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Identified Pain Points

| Issue | Impact | Frequency | Severity |
|-------|--------|-----------|----------|
| **Context Overload** | Tokens wasted on irrelevant refs | Every request | HIGH |
| **No Learning** | Same mistakes repeated | Cross-session | HIGH |
| **Agent Silos** | Agents can't share insights | Multi-agent tasks | MEDIUM |
| **Manual Coordination** | User must orchestrate agents | Complex workflows | HIGH |
| **No Quality Gates** | Output quality inconsistent | Every response | MEDIUM |
| **Memory Loss** | Context lost between sessions | Long projects | HIGH |

### 1.3 Current Workflow Example (Brown Paper)

```
User Request: "Analyze legacy ASP codebase"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ CURRENT FLOW (Inefficient)                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. API receives request                                         │
│  2. BrownPaperService manually calls:                           │
│     ├── Miguel (Metrics) - loads full context                   │
│     ├── Felix (Architect) - loads full context AGAIN            │
│     ├── Quinn (Quality) - loads full context AGAIN              │
│     ├── Eliza (Estimation) - loads full context AGAIN           │
│     └── Diana (Documentation) - loads full context AGAIN        │
│                                                                  │
│  Problems:                                                       │
│  ├── 5x context loading = 5x token cost                         │
│  ├── No shared insights between agents                          │
│  ├── No memory of previous analyses                             │
│  └── Quality varies per agent                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Target Architecture

### 2.1 Confucius Orchestrator Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TARGET STATE: CONFUCIUS ORCHESTRATOR                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │                    CONFUCIUS ORCHESTRATOR                              │ │
│   │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│   │  │                  HIERARCHICAL WORKING MEMORY                     │  │ │
│   │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │  │ │
│   │  │  │session_scope│  │entry_scope  │  │runnable_scope           │  │  │ │
│   │  │  │(cross-task) │  │(per-task)   │  │(tool execution)         │  │  │ │
│   │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │  │ │
│   │  └─────────────────────────────────────────────────────────────────┘  │ │
│   │                                                                        │ │
│   │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│   │  │                    EXTENSION SYSTEM                              │  │ │
│   │  │  on_input_messages │ on_llm_output │ on_execute │ on_post       │  │ │
│   │  └─────────────────────────────────────────────────────────────────┘  │ │
│   │                                                                        │ │
│   │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│   │  │                    NOTE-TAKING SYSTEM                            │  │ │
│   │  │  Problem → Solution → Insights (Markdown nodes)                  │  │ │
│   │  └─────────────────────────────────────────────────────────────────┘  │ │
│   │                                                                        │ │
│   │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│   │  │                    META-AGENT                                    │  │ │
│   │  │  Build → Test → Improve loop for agent configuration             │  │ │
│   │  └─────────────────────────────────────────────────────────────────┘  │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│          ┌───────────────────────────┼───────────────────────────┐          │
│          ▼                           ▼                           ▼          │
│   ┌─────────────┐            ┌─────────────┐            ┌─────────────┐    │
│   │   Felix     │            │   Quinn     │            │   Eliza     │    │
│   │  Extension  │            │  Extension  │            │  Extension  │    │
│   └─────────────┘            └─────────────┘            └─────────────┘    │
│          │                           │                           │          │
│   ┌─────────────┐            ┌─────────────┐            ┌─────────────┐    │
│   │   Diana     │            │   Marcus    │            │   Miguel    │    │
│   │  Extension  │            │  Extension  │            │  Extension  │    │
│   └─────────────┘            └─────────────┘            └─────────────┘    │
│          │                           │                           │          │
│   ┌─────────────┐            ┌─────────────┐            ┌─────────────┐    │
│   │   Tessa     │            │   Peter     │            │   Paul      │    │
│   │  Extension  │            │  Extension  │            │  Extension  │    │
│   └─────────────┘            └─────────────┘            └─────────────┘    │
│          │                                                       │          │
│   ┌─────────────┐                                        ┌─────────────┐   │
│   │   Betty     │                                        │   Vicky     │   │
│   │  Extension  │                                        │  Extension  │   │
│   └─────────────┘                                        └─────────────┘   │
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │                         QUALITY GATES                                  │ │
│   │  Score ≥ 0.85 │ Critical Issues = 0 │ Max Iterations = 3              │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Three-Axis Design (AX/UX/DX)

| Axis | Focus | MarQed Implementation |
|------|-------|----------------------|
| **Agent Experience (AX)** | What agents see | Distilled working memory, adaptive summaries, context compression |
| **User Experience (UX)** | Transparency | Streaming traces, code diffs, progress indicators |
| **Developer Experience (DX)** | Extensibility | Modular agent extensions, plugin system, debugging tools |

### 2.3 Integration with Existing Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MARQED + CONFUCIUS INTEGRATION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────┐         ┌─────────────────────────────────────┐  │
│   │   EXISTING LAYER    │         │        CONFUCIUS LAYER               │  │
│   ├─────────────────────┤         ├─────────────────────────────────────┤  │
│   │                     │         │                                      │  │
│   │   Workflows:        │ ◀─────▶ │   Orchestrator:                      │  │
│   │   ├── Brown Paper   │         │   ├── Memory Management              │  │
│   │   ├── Migration     │         │   ├── Extension Dispatch             │  │
│   │   ├── Quality       │         │   ├── Quality Gates                  │  │
│   │   └── Green Paper   │         │   └── Note-Taking                    │  │
│   │                     │         │                                      │  │
│   │   Contracts:        │ ◀─────▶ │   Memory Scopes:                     │  │
│   │   ├── Analysis      │         │   ├── session_scope                  │  │
│   │   ├── Quality       │         │   ├── entry_scope                    │  │
│   │   └── Stability     │         │   └── runnable_scope                 │  │
│   │                     │         │                                      │  │
│   │   Infrastructure:   │ ◀─────▶ │   Extensions:                        │  │
│   │   ├── Stability     │         │   ├── on_input_messages              │  │
│   │   ├── Metrics       │         │   ├── on_llm_output                  │  │
│   │   └── Estimation    │         │   ├── on_execute                     │  │
│   │                     │         │   └── on_post                        │  │
│   └─────────────────────┘         └─────────────────────────────────────┘  │
│                                                                              │
│   Key Principle: Confucius ENHANCES existing architecture, doesn't replace  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Integration Strategy

### 3.1 Phased Approach

| Phase | Week | Focus | Risk | Rollback |
|-------|------|-------|------|----------|
| **Phase 1** | 149-150 | Core SDK Integration | LOW | Remove package |
| **Phase 2** | 150-151 | Memory Architecture | LOW | Disable feature |
| **Phase 3** | 151-152 | Agent Extensions | MEDIUM | Fall back to direct calls |
| **Phase 4** | 152-153 | Quality Gates | LOW | Disable gates |
| **Phase 5** | 153-154 | Full Migration | MEDIUM | Parallel operation |

### 3.2 Non-Breaking Changes First

```
Week 149-150: Foundation (Non-Breaking)
├── Install Confucius SDK
├── Create ConfuciusOrchestrator wrapper
├── Add memory tables (parallel to existing)
├── Create extension base classes
└── Unit tests for new components

Week 150-151: Memory Layer (Non-Breaking)
├── Implement hierarchical memory
├── Add context compression
├── Create note-taking service
└── Integration with existing sessions

Week 151-152: Agent Extensions (Parallel Operation)
├── Wrap existing agents as extensions
├── Implement extension hooks
├── Add routing logic
└── A/B testing capability

Week 152-153: Quality Gates (Feature Flag)
├── Implement quality scoring
├── Add iteration logic
├── Create escalation paths
└── Dashboard integration

Week 153-154: Full Migration (Gradual)
├── Route workflows through orchestrator
├── Remove direct agent calls
├── Performance optimization
└── Documentation
```

### 3.3 Backwards Compatibility

| Component | Strategy |
|-----------|----------|
| **Existing APIs** | Maintain all endpoints, internal routing changes only |
| **Agent Responses** | Same format, enhanced metadata |
| **Workflows** | Add orchestrator layer above existing services |
| **Database** | New tables, existing tables unchanged |
| **Frontend** | Optional streaming, graceful degradation |

---

## 4. Week-by-Week Implementation Plan

### Week 149: Core SDK Integration

| Task | Hours | Output | Owner |
|------|-------|--------|-------|
| Install Confucius SDK | 2 | `requirements.txt` updated | DevOps |
| Create `confucius/` module structure | 4 | Module skeleton | Backend |
| Implement `ConfuciusOrchestrator` class | 8 | Main orchestrator | Backend |
| Create `BaseAgentExtension` abstract class | 6 | Extension base | Backend |
| Add configuration management | 4 | `confucius_config.py` | Backend |
| Database migration (memory tables) | 4 | Migration 070 | Backend |
| Unit tests | 8 | 30+ tests | QA |
| **Total** | **36** | | |

**Deliverables Week 149:**
```
backend/app/
├── confucius/
│   ├── __init__.py
│   ├── orchestrator.py          # Main ConfuciusOrchestrator
│   ├── config.py                # Configuration management
│   ├── extensions/
│   │   ├── __init__.py
│   │   └── base.py              # BaseAgentExtension
│   └── memory/
│       ├── __init__.py
│       └── types.py             # Memory scope types
│
├── alembic/versions/
│   └── 070_confucius_memory.py  # Memory tables
│
└── tests/unit/confucius/
    ├── test_orchestrator.py
    └── test_base_extension.py
```

### Week 150: Memory Architecture

| Task | Hours | Output | Owner |
|------|-------|--------|-------|
| Implement `HierarchicalMemory` class | 8 | Memory management | Backend |
| Create `ContextCompressor` service | 6 | Adaptive compression | Backend |
| Implement `NoteTaker` agent | 6 | Cross-session learning | Backend |
| Add `MemoryRepository` | 4 | Database persistence | Backend |
| Create memory scope serializers | 4 | JSON/DB serialization | Backend |
| Integration tests | 6 | Memory flow tests | QA |
| Performance benchmarks | 4 | Baseline metrics | DevOps |
| **Total** | **38** | | |

**Deliverables Week 150:**
```
backend/app/confucius/
├── memory/
│   ├── hierarchical.py          # HierarchicalMemory
│   ├── compressor.py            # ContextCompressor
│   ├── note_taker.py            # NoteTaker agent
│   ├── repository.py            # MemoryRepository
│   └── serializers.py           # Memory serialization
│
└── tests/integration/confucius/
    └── test_memory_flow.py
```

### Week 151: Agent Extensions

| Task | Hours | Output | Owner |
|------|-------|--------|-------|
| Create `FelixExtension` (Architect) | 4 | Felix as extension | Backend |
| Create `QuinnExtension` (Quality) | 4 | Quinn as extension | Backend |
| Create `ElizaExtension` (Estimation) | 4 | Eliza as extension | Backend |
| Create `DianaExtension` (Documentation) | 3 | Diana as extension | Backend |
| Create `MarcusExtension` (Migration) | 4 | Marcus as extension | Backend |
| Create `MiguelExtension` (Metrics) | 3 | Miguel as extension | Backend |
| Create remaining 5 extensions | 10 | Betty, Tessa, Peter, Paul, Vicky | Backend |
| Extension routing logic | 4 | Router service | Backend |
| Extension tests | 8 | Per-extension tests | QA |
| **Total** | **44** | | |

**Deliverables Week 151:**
```
backend/app/confucius/extensions/
├── __init__.py
├── base.py                      # BaseAgentExtension
├── felix_extension.py           # Architect
├── quinn_extension.py           # Quality
├── eliza_extension.py           # Estimation
├── diana_extension.py           # Documentation
├── marcus_extension.py          # Migration
├── miguel_extension.py          # Metrics
├── tessa_extension.py           # Testing
├── peter_extension.py           # Product Owner
├── paul_extension.py            # Planning
├── betty_extension.py           # Business
├── vicky_extension.py           # Validation
└── router.py                    # Extension router
```

### Week 152: Quality Gates

| Task | Hours | Output | Owner |
|------|-------|--------|-------|
| Implement `QualityGateEvaluator` | 6 | Score calculation | Backend |
| Create `IterationController` | 4 | PIV loop management | Backend |
| Add `EscalationService` | 4 | Failure handling | Backend |
| Implement quality scoring rules | 6 | Domain-specific rules | Backend |
| Create quality dashboard widgets | 4 | Frontend components | Frontend |
| Add SSE streaming for progress | 6 | Real-time updates | Backend |
| Integration tests | 6 | E2E quality flow | QA |
| **Total** | **36** | | |

**Deliverables Week 152:**
```
backend/app/confucius/
├── quality/
│   ├── __init__.py
│   ├── evaluator.py             # QualityGateEvaluator
│   ├── iteration.py             # IterationController
│   ├── escalation.py            # EscalationService
│   └── rules.py                 # Quality scoring rules
│
├── api/
│   └── confucius_api.py         # New API endpoints
│
frontend/
└── components/
    └── confucius/
        ├── quality-dashboard.js
        └── progress-stream.js
```

### Week 153-154: Full Migration & Optimization

| Task | Hours | Output | Owner |
|------|-------|--------|-------|
| Integrate with Brown Paper workflow | 6 | Orchestrated analysis | Backend |
| Integrate with Migration workflow | 6 | Orchestrated migration | Backend |
| Integrate with Quality workflow | 4 | Orchestrated quality | Backend |
| Integrate with Green Paper workflow | 4 | Orchestrated green paper | Backend |
| Performance optimization | 6 | Latency reduction | Backend |
| Load testing | 4 | Scalability validation | DevOps |
| Documentation | 6 | User guide, API docs | Docs |
| Rollout monitoring | 4 | Metrics dashboards | DevOps |
| Bug fixes & polish | 8 | Quality improvements | Team |
| **Total** | **48** | | |

---

## 5. Technical Specifications

### 5.1 ConfuciusOrchestrator Class

```python
# backend/app/confucius/orchestrator.py

from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio

from .memory.hierarchical import HierarchicalMemory
from .memory.compressor import ContextCompressor
from .memory.note_taker import NoteTaker
from .extensions.base import BaseAgentExtension
from .extensions.router import ExtensionRouter
from .quality.evaluator import QualityGateEvaluator
from .quality.iteration import IterationController


class OrchestratorState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    ITERATING = "iterating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class OrchestratorConfig:
    """Confucius Orchestrator configuration."""
    max_iterations: int = 3
    quality_threshold: float = 0.85
    context_compression_threshold: int = 100000  # tokens
    enable_note_taking: bool = True
    enable_streaming: bool = True
    timeout_per_extension: int = 60  # seconds
    enable_parallel_extensions: bool = True


@dataclass
class ExecutionResult:
    """Result of orchestrated execution."""
    success: bool
    output: Dict[str, Any]
    quality_score: float
    iterations_used: int
    extensions_called: List[str]
    memory_state: Dict[str, Any]
    notes_generated: List[Dict[str, Any]]
    execution_time_ms: int
    token_usage: Dict[str, int]


class ConfuciusOrchestrator:
    """
    Main orchestrator implementing Confucius SDK patterns for MarQed.

    Manages:
    - Hierarchical working memory (session/entry/runnable scopes)
    - Agent extensions with lifecycle hooks
    - Quality gates and iteration control
    - Cross-session learning via note-taking
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        memory: HierarchicalMemory,
        compressor: ContextCompressor,
        note_taker: NoteTaker,
        router: ExtensionRouter,
        quality_evaluator: QualityGateEvaluator,
        iteration_controller: IterationController,
    ):
        self.config = config
        self.memory = memory
        self.compressor = compressor
        self.note_taker = note_taker
        self.router = router
        self.quality_evaluator = quality_evaluator
        self.iteration_controller = iteration_controller
        self.state = OrchestratorState.IDLE
        self._extensions: Dict[str, BaseAgentExtension] = {}

    def register_extension(self, extension: BaseAgentExtension) -> None:
        """Register an agent extension with the orchestrator."""
        self._extensions[extension.name] = extension
        extension.set_orchestrator(self)

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute a task through the orchestrated pipeline.

        Implements the PIV (Plan-Implement-Validate) loop:
        1. Route task to appropriate extension(s)
        2. Load relevant memory and compress context
        3. Execute extension(s) with lifecycle hooks
        4. Evaluate quality and iterate if needed
        5. Generate notes for cross-session learning
        """
        self.state = OrchestratorState.PLANNING
        iteration = 0

        # Load session memory
        if session_id:
            await self.memory.load_session(session_id)

        # Create entry scope for this task
        entry_id = await self.memory.create_entry(task, context)

        while iteration < self.config.max_iterations:
            iteration += 1
            self.state = OrchestratorState.EXECUTING

            # Route to extensions
            extensions = await self.router.route(task, context)

            # Compress context if needed
            compressed_context = await self._prepare_context(context, extensions)

            # Execute extensions with hooks
            results = await self._execute_extensions(
                extensions, task, compressed_context, entry_id
            )

            # Evaluate quality
            self.state = OrchestratorState.EVALUATING
            quality_result = await self.quality_evaluator.evaluate(results)

            if quality_result.passes_threshold(self.config.quality_threshold):
                self.state = OrchestratorState.COMPLETED

                # Generate notes for learning
                if self.config.enable_note_taking:
                    await self.note_taker.record(
                        task=task,
                        result=results,
                        quality_score=quality_result.score,
                    )

                return self._create_result(
                    success=True,
                    output=results,
                    quality_score=quality_result.score,
                    iterations=iteration,
                    extensions=[e.name for e in extensions],
                )

            # Iterate with feedback
            self.state = OrchestratorState.ITERATING
            context = await self.iteration_controller.prepare_retry(
                original_context=context,
                results=results,
                quality_feedback=quality_result.feedback,
            )

        # Max iterations reached
        self.state = OrchestratorState.FAILED
        return self._create_result(
            success=False,
            output=results,
            quality_score=quality_result.score,
            iterations=iteration,
            extensions=[e.name for e in extensions],
        )

    async def execute_streaming(
        self,
        task: str,
        context: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute with SSE streaming for real-time progress updates.

        Yields events:
        - {"type": "state", "state": "planning"}
        - {"type": "extension_start", "extension": "Felix"}
        - {"type": "extension_progress", "extension": "Felix", "progress": 0.5}
        - {"type": "extension_complete", "extension": "Felix", "result": {...}}
        - {"type": "quality", "score": 0.87, "passes": true}
        - {"type": "complete", "result": {...}}
        """
        # Implementation with yield statements for streaming
        pass

    async def _prepare_context(
        self,
        context: Dict[str, Any],
        extensions: List[BaseAgentExtension],
    ) -> Dict[str, Any]:
        """Prepare and compress context based on extension needs."""
        # Get relevant memory
        relevant_memory = await self.memory.get_relevant(
            task_context=context,
            extensions=[e.name for e in extensions],
        )

        # Merge with context
        enriched_context = {**context, "memory": relevant_memory}

        # Compress if over threshold
        token_count = self._estimate_tokens(enriched_context)
        if token_count > self.config.context_compression_threshold:
            enriched_context = await self.compressor.compress(
                enriched_context,
                target_tokens=self.config.context_compression_threshold,
            )

        return enriched_context

    async def _execute_extensions(
        self,
        extensions: List[BaseAgentExtension],
        task: str,
        context: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Execute extensions with full lifecycle hooks."""
        results = {}

        for extension in extensions:
            # on_input_messages hook
            modified_context = await extension.on_input_messages(task, context)

            # Main execution
            try:
                async with asyncio.timeout(self.config.timeout_per_extension):
                    raw_output = await extension.execute(task, modified_context)
            except asyncio.TimeoutError:
                raw_output = {"error": "timeout", "partial": extension.get_partial()}

            # on_llm_output hook
            parsed_output = await extension.on_llm_output(raw_output)

            # on_execute hook (tool calls)
            executed_output = await extension.on_execute(parsed_output)

            # on_post hook (memory/artifacts)
            final_output = await extension.on_post(executed_output, entry_id)

            results[extension.name] = final_output

            # Update runnable scope memory
            await self.memory.update_runnable(entry_id, extension.name, final_output)

        return results

    def _estimate_tokens(self, context: Dict[str, Any]) -> int:
        """Estimate token count for context."""
        import json
        text = json.dumps(context)
        return len(text) // 4  # Rough estimate

    def _create_result(self, **kwargs) -> ExecutionResult:
        """Create execution result with memory state."""
        return ExecutionResult(
            memory_state=self.memory.get_state(),
            notes_generated=self.note_taker.get_recent_notes(),
            execution_time_ms=0,  # Set by caller
            token_usage={},  # Set by caller
            **kwargs,
        )
```

### 5.2 BaseAgentExtension Class

```python
# backend/app/confucius/extensions/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..orchestrator import ConfuciusOrchestrator


@dataclass
class ExtensionMetadata:
    """Metadata for agent extension."""
    name: str
    description: str
    capabilities: list[str]
    domains: list[str]
    priority: int = 0
    parallel_safe: bool = True


class BaseAgentExtension(ABC):
    """
    Base class for agent extensions in the Confucius orchestrator.

    Each MarQed agent (Felix, Quinn, etc.) is wrapped as an extension
    with four lifecycle hooks:

    1. on_input_messages: Modify prompts before LLM invocation
    2. on_llm_output: Parse LLM responses into actions
    3. on_execute: Execute actions (tool calls)
    4. on_post: Record outcomes to memory/artifacts
    """

    def __init__(self, metadata: ExtensionMetadata):
        self.metadata = metadata
        self._orchestrator: Optional["ConfuciusOrchestrator"] = None
        self._partial_result: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return self.metadata.name

    def set_orchestrator(self, orchestrator: "ConfuciusOrchestrator") -> None:
        """Set reference to parent orchestrator."""
        self._orchestrator = orchestrator

    # ========== LIFECYCLE HOOKS ==========

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Hook 1: Modify context before LLM invocation.

        Use cases:
        - Add agent-specific system prompts
        - Filter irrelevant context
        - Inject relevant memories
        - Add domain-specific instructions
        """
        return context  # Default: no modification

    @abstractmethod
    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main execution method.

        This wraps the existing agent logic and returns raw output.
        """
        pass

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Hook 2: Parse LLM output into structured actions.

        Use cases:
        - Extract tool calls from response
        - Parse structured data
        - Validate output format
        - Handle errors/retries
        """
        return raw_output  # Default: no modification

    async def on_execute(
        self,
        parsed_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Hook 3: Execute actions from parsed output.

        Use cases:
        - Execute tool calls
        - Run code analysis
        - Call external services
        - Perform file operations
        """
        return parsed_output  # Default: no tool execution

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """
        Hook 4: Post-processing and memory recording.

        Use cases:
        - Record to memory scopes
        - Generate artifacts
        - Update metrics
        - Trigger notifications
        """
        return executed_output  # Default: no post-processing

    # ========== UTILITY METHODS ==========

    def get_partial(self) -> Dict[str, Any]:
        """Get partial result (for timeout scenarios)."""
        return self._partial_result

    def update_partial(self, update: Dict[str, Any]) -> None:
        """Update partial result during execution."""
        self._partial_result.update(update)

    async def get_relevant_memory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant memory from orchestrator."""
        if self._orchestrator:
            return await self._orchestrator.memory.get_relevant(
                task_context=context,
                extensions=[self.name],
            )
        return {}
```

### 5.3 HierarchicalMemory Class

```python
# backend/app/confucius/memory/hierarchical.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class MemoryScope(Enum):
    SESSION = "session"   # Cross-task insights
    ENTRY = "entry"       # Per-task summaries
    RUNNABLE = "runnable" # Tool execution outputs


@dataclass
class MemoryNode:
    """A single memory node in the hierarchy."""
    id: str
    scope: MemoryScope
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    relevance_score: float = 1.0
    compressed: bool = False


@dataclass
class SessionMemory:
    """Session-level memory (cross-task)."""
    session_id: str
    project_id: str
    insights: List[Dict[str, Any]]
    patterns: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


@dataclass
class EntryMemory:
    """Entry-level memory (per-task)."""
    entry_id: str
    session_id: str
    task: str
    context_summary: str
    results_summary: str
    quality_score: float
    runnable_ids: List[str]
    created_at: datetime


@dataclass
class RunnableMemory:
    """Runnable-level memory (tool execution)."""
    runnable_id: str
    entry_id: str
    extension_name: str
    input_summary: str
    output_summary: str
    duration_ms: int
    success: bool
    created_at: datetime


class HierarchicalMemory:
    """
    Hierarchical working memory implementation.

    Three scopes:
    1. session_scope: All-time insights across tasks
    2. entry_scope: Per-task summaries
    3. runnable_scope: Tool execution outputs

    Features:
    - Semantic relevance scoring
    - Automatic summarization
    - Cross-session persistence
    - Efficient retrieval
    """

    def __init__(self, repository: "MemoryRepository"):
        self.repository = repository
        self._current_session: Optional[SessionMemory] = None
        self._entries: Dict[str, EntryMemory] = {}
        self._runnables: Dict[str, RunnableMemory] = {}

    async def load_session(self, session_id: str) -> SessionMemory:
        """Load existing session or create new one."""
        session = await self.repository.get_session(session_id)
        if not session:
            session = SessionMemory(
                session_id=session_id,
                project_id="",
                insights=[],
                patterns=[],
                decisions=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            await self.repository.save_session(session)

        self._current_session = session
        return session

    async def create_entry(self, task: str, context: Dict[str, Any]) -> str:
        """Create new entry for a task."""
        entry_id = str(uuid.uuid4())
        entry = EntryMemory(
            entry_id=entry_id,
            session_id=self._current_session.session_id if self._current_session else "",
            task=task,
            context_summary=self._summarize_context(context),
            results_summary="",
            quality_score=0.0,
            runnable_ids=[],
            created_at=datetime.utcnow(),
        )

        self._entries[entry_id] = entry
        await self.repository.save_entry(entry)
        return entry_id

    async def update_runnable(
        self,
        entry_id: str,
        extension_name: str,
        output: Dict[str, Any],
    ) -> str:
        """Record runnable execution to memory."""
        runnable_id = str(uuid.uuid4())
        runnable = RunnableMemory(
            runnable_id=runnable_id,
            entry_id=entry_id,
            extension_name=extension_name,
            input_summary="",  # Set by caller
            output_summary=self._summarize_output(output),
            duration_ms=0,  # Set by caller
            success=not output.get("error"),
            created_at=datetime.utcnow(),
        )

        self._runnables[runnable_id] = runnable

        # Link to entry
        if entry_id in self._entries:
            self._entries[entry_id].runnable_ids.append(runnable_id)

        await self.repository.save_runnable(runnable)
        return runnable_id

    async def get_relevant(
        self,
        task_context: Dict[str, Any],
        extensions: List[str],
    ) -> Dict[str, Any]:
        """Get relevant memory for current task."""
        relevant = {
            "session_insights": [],
            "related_entries": [],
            "patterns": [],
        }

        if self._current_session:
            # Get session-level insights
            relevant["session_insights"] = self._current_session.insights[-10:]
            relevant["patterns"] = self._current_session.patterns[-5:]

            # Find related entries by semantic similarity
            related = await self.repository.find_related_entries(
                session_id=self._current_session.session_id,
                task_context=task_context,
                limit=5,
            )
            relevant["related_entries"] = related

        return relevant

    async def add_insight(self, insight: Dict[str, Any]) -> None:
        """Add insight to session memory."""
        if self._current_session:
            self._current_session.insights.append({
                **insight,
                "added_at": datetime.utcnow().isoformat(),
            })
            self._current_session.updated_at = datetime.utcnow()
            await self.repository.save_session(self._current_session)

    async def add_pattern(self, pattern: Dict[str, Any]) -> None:
        """Add pattern to session memory."""
        if self._current_session:
            self._current_session.patterns.append({
                **pattern,
                "added_at": datetime.utcnow().isoformat(),
            })
            self._current_session.updated_at = datetime.utcnow()
            await self.repository.save_session(self._current_session)

    def get_state(self) -> Dict[str, Any]:
        """Get current memory state for debugging."""
        return {
            "session": self._current_session.__dict__ if self._current_session else None,
            "entries_count": len(self._entries),
            "runnables_count": len(self._runnables),
        }

    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Create summary of context for storage."""
        # Use LLM for intelligent summarization
        return str(context)[:500]

    def _summarize_output(self, output: Dict[str, Any]) -> str:
        """Create summary of output for storage."""
        return str(output)[:500]
```

---

## 6. Agent Migration Plan

### 6.1 Agent-to-Extension Mapping

| Agent | Extension Class | Capabilities | Priority |
|-------|-----------------|--------------|----------|
| **Felix** | `FelixExtension` | Architecture analysis, system design | 1 |
| **Quinn** | `QuinnExtension` | Quality analysis, code review | 1 |
| **Eliza** | `ElizaExtension` | Estimation, FP calculation | 2 |
| **Diana** | `DianaExtension` | Documentation generation | 3 |
| **Marcus** | `MarcusExtension` | Migration planning, execution | 1 |
| **Miguel** | `MiguelExtension` | Metrics collection, analysis | 2 |
| **Tessa** | `TessaExtension` | Test generation, coverage | 2 |
| **Peter** | `PeterExtension` | Product backlog, user stories | 2 |
| **Paul** | `PaulExtension` | Sprint planning, roadmap | 3 |
| **Betty** | `BettyExtension` | Business analysis, requirements | 2 |
| **Vicky** | `VickyExtension` | Validation, verification | 3 |

### 6.2 Extension Implementation Template

```python
# backend/app/confucius/extensions/felix_extension.py

from typing import Dict, Any
from .base import BaseAgentExtension, ExtensionMetadata
from ...services.agents.felix_agent_service import FelixAgentService


class FelixExtension(BaseAgentExtension):
    """
    Felix (Architect) agent as Confucius extension.

    Capabilities:
    - System architecture analysis
    - Component dependency mapping
    - Technology recommendations
    - Migration path planning
    """

    def __init__(self, felix_service: FelixAgentService):
        super().__init__(ExtensionMetadata(
            name="Felix",
            description="Architect agent for system design and analysis",
            capabilities=[
                "architecture_analysis",
                "dependency_mapping",
                "technology_recommendations",
                "migration_planning",
            ],
            domains=["architecture", "design", "migration"],
            priority=1,
            parallel_safe=True,
        ))
        self.felix_service = felix_service

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Add architecture-specific context."""
        # Get relevant architectural memories
        arch_memory = await self.get_relevant_memory(context)

        # Add Felix's system prompt
        context["system_prompt"] = self._get_felix_system_prompt()

        # Add previous architectural decisions
        if arch_memory.get("patterns"):
            context["architectural_patterns"] = arch_memory["patterns"]

        return context

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute Felix's analysis."""
        # Call existing Felix service
        result = await self.felix_service.analyze(
            task=task,
            context=context,
        )

        # Update partial for timeout handling
        self.update_partial({"analysis_started": True})

        return result

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse Felix's output into structured format."""
        return {
            "architecture": raw_output.get("architecture", {}),
            "dependencies": raw_output.get("dependencies", []),
            "recommendations": raw_output.get("recommendations", []),
            "risks": raw_output.get("risks", []),
            "raw": raw_output,
        }

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Record architectural insights to memory."""
        # Extract patterns for cross-session learning
        if executed_output.get("architecture"):
            await self._orchestrator.memory.add_pattern({
                "type": "architecture",
                "pattern": executed_output["architecture"],
                "source_task": entry_id,
            })

        return executed_output

    def _get_felix_system_prompt(self) -> str:
        return """You are Felix, the Architecture agent for MarQed.

Your responsibilities:
1. Analyze system architecture and identify patterns
2. Map component dependencies
3. Recommend technology choices
4. Plan migration paths for legacy systems

Always consider:
- Scalability and performance
- Maintainability and technical debt
- Security implications
- Integration complexity
"""
```

### 6.3 Migration Sequence

```
Week 151 Migration Order:

Day 1-2: Core agents (Felix, Quinn, Marcus)
├── Most critical for workflows
├── Highest usage
└── Test with Brown Paper workflow

Day 3: Analysis agents (Miguel, Eliza)
├── Support core agents
├── Metrics and estimation
└── Test with estimation flow

Day 4: Support agents (Diana, Tessa, Peter)
├── Documentation and testing
├── Product management
└── Test with documentation generation

Day 5: Remaining agents (Paul, Betty, Vicky)
├── Planning and validation
├── Lower priority
└── Full integration test
```

---

## 7. Extension Development

### 7.1 Extension Hooks Detail

| Hook | When Called | Purpose | Example Use |
|------|-------------|---------|-------------|
| `on_input_messages` | Before LLM call | Modify context | Add system prompt, filter data |
| `on_llm_output` | After LLM response | Parse output | Extract actions, validate format |
| `on_execute` | After parsing | Run tools | Call services, file operations |
| `on_post` | After execution | Record results | Update memory, generate artifacts |

### 7.2 Extension Communication

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTENSION COMMUNICATION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Direct Communication (via Orchestrator):                       │
│   ┌─────────┐                              ┌─────────┐          │
│   │  Felix  │ ──── shared memory ────────▶ │  Quinn  │          │
│   └─────────┘                              └─────────┘          │
│        │                                        │                │
│        └──────────┐            ┌───────────────┘                │
│                   ▼            ▼                                 │
│              ┌─────────────────────┐                            │
│              │  HierarchicalMemory │                            │
│              │  (entry_scope)      │                            │
│              └─────────────────────┘                            │
│                                                                  │
│   Event-Based Communication:                                     │
│   ┌─────────┐    event bus    ┌─────────┐                       │
│   │  Eliza  │ ───────────────▶│  Diana  │                       │
│   └─────────┘                 └─────────┘                       │
│        │                           │                             │
│        │  "estimation_complete"    │  "generate_docs"           │
│        │                           │                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Extension Testing Pattern

```python
# backend/tests/unit/confucius/extensions/test_felix_extension.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.confucius.extensions.felix_extension import FelixExtension
from app.confucius.orchestrator import ConfuciusOrchestrator


@pytest.fixture
def felix_service():
    service = MagicMock()
    service.analyze = AsyncMock(return_value={
        "architecture": {"type": "monolith"},
        "dependencies": ["db", "cache"],
        "recommendations": ["migrate to microservices"],
    })
    return service


@pytest.fixture
def felix_extension(felix_service):
    return FelixExtension(felix_service)


@pytest.fixture
def mock_orchestrator():
    orchestrator = MagicMock(spec=ConfuciusOrchestrator)
    orchestrator.memory = MagicMock()
    orchestrator.memory.get_relevant = AsyncMock(return_value={})
    orchestrator.memory.add_pattern = AsyncMock()
    return orchestrator


class TestFelixExtension:

    async def test_on_input_messages_adds_system_prompt(
        self, felix_extension, mock_orchestrator
    ):
        felix_extension.set_orchestrator(mock_orchestrator)

        context = {"code": "some code"}
        result = await felix_extension.on_input_messages("analyze", context)

        assert "system_prompt" in result
        assert "Felix" in result["system_prompt"]

    async def test_execute_calls_felix_service(
        self, felix_extension, felix_service
    ):
        result = await felix_extension.execute("analyze", {"code": "test"})

        felix_service.analyze.assert_called_once()
        assert "architecture" in result

    async def test_on_post_records_patterns(
        self, felix_extension, mock_orchestrator
    ):
        felix_extension.set_orchestrator(mock_orchestrator)

        output = {"architecture": {"type": "microservices"}}
        await felix_extension.on_post(output, "entry-123")

        mock_orchestrator.memory.add_pattern.assert_called_once()
```

---

## 8. Memory Architecture

### 8.1 Memory Scopes Deep Dive

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MEMORY ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   SESSION SCOPE (Persistent, Cross-Task)                                    │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │  Lifetime: Entire project/session                                      │ │
│   │  Content:                                                              │ │
│   │  ├── Insights: "ADO leaks often occur in batch loops"                 │ │
│   │  ├── Patterns: "FysioOne uses CreateCusCon() wrapper"                 │ │
│   │  ├── Decisions: "Use CleanupResources() helper pattern"               │ │
│   │  └── Preferences: "User prefers detailed explanations"                │ │
│   │                                                                        │ │
│   │  Compression: Summarized after 50 insights                            │ │
│   │  Retention: Permanent (database persisted)                            │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│   ENTRY SCOPE (Per-Task)                                                    │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │  Lifetime: Single task execution                                       │ │
│   │  Content:                                                              │ │
│   │  ├── Task: "Analyze stability of declaratie module"                   │ │
│   │  ├── Context Summary: "ASP files, 500 LOC, batch processing"          │ │
│   │  ├── Results Summary: "Found 12 leaks, 3 critical"                    │ │
│   │  └── Quality Score: 0.87                                              │ │
│   │                                                                        │ │
│   │  Compression: Summarized immediately after task                       │ │
│   │  Retention: 30 days (configurable)                                    │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│   RUNNABLE SCOPE (Per-Extension Call)                                       │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │  Lifetime: Single extension execution                                  │ │
│   │  Content:                                                              │ │
│   │  ├── Extension: "Quinn"                                               │ │
│   │  ├── Input Summary: "Analyze declaratie.asp for leaks"                │ │
│   │  ├── Output Summary: "Found: 3 ADO, 1 COM, 2 File"                    │ │
│   │  └── Duration: 2.3s                                                   │ │
│   │                                                                        │ │
│   │  Compression: Immediate, only key outputs retained                    │ │
│   │  Retention: 7 days                                                    │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Context Compression Strategy

```python
# backend/app/confucius/memory/compressor.py

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class CompressionResult:
    """Result of context compression."""
    original_tokens: int
    compressed_tokens: int
    reduction_percent: float
    compressed_context: Dict[str, Any]
    dropped_keys: List[str]


class ContextCompressor:
    """
    Adaptive context compression using LLM summarization.

    Strategy:
    1. Identify high-relevance content (keep verbatim)
    2. Summarize medium-relevance content
    3. Drop low-relevance content
    4. Maintain reasoning chains
    """

    def __init__(
        self,
        llm_service,
        max_summary_ratio: float = 0.3,  # 30% of original
    ):
        self.llm_service = llm_service
        self.max_summary_ratio = max_summary_ratio

    async def compress(
        self,
        context: Dict[str, Any],
        target_tokens: int,
    ) -> Dict[str, Any]:
        """
        Compress context to target token count.

        Algorithm:
        1. Score each context key by relevance
        2. Keep high-relevance keys verbatim
        3. Summarize medium-relevance keys
        4. Drop low-relevance keys
        5. Preserve reasoning chains
        """
        # Score relevance of each key
        scored = await self._score_relevance(context)

        compressed = {}
        current_tokens = 0

        # Phase 1: Keep high-relevance verbatim
        for key, (value, score) in sorted(
            scored.items(),
            key=lambda x: x[1][1],
            reverse=True
        ):
            if score >= 0.8:
                tokens = self._estimate_tokens(value)
                if current_tokens + tokens <= target_tokens * 0.6:
                    compressed[key] = value
                    current_tokens += tokens

        # Phase 2: Summarize medium-relevance
        for key, (value, score) in scored.items():
            if 0.4 <= score < 0.8 and key not in compressed:
                summary = await self._summarize(key, value)
                tokens = self._estimate_tokens(summary)
                if current_tokens + tokens <= target_tokens * 0.9:
                    compressed[f"{key}_summary"] = summary
                    current_tokens += tokens

        # Phase 3: Add reasoning chain markers
        compressed["_compression_metadata"] = {
            "original_keys": list(context.keys()),
            "kept_keys": [k for k in compressed.keys() if not k.startswith("_")],
            "dropped_keys": [k for k in context.keys() if k not in compressed],
        }

        return compressed

    async def _score_relevance(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, tuple[Any, float]]:
        """Score relevance of each context key."""
        # Use LLM to score relevance
        scores = {}
        for key, value in context.items():
            # Simple heuristics + LLM scoring
            score = await self._get_relevance_score(key, value)
            scores[key] = (value, score)
        return scores

    async def _summarize(self, key: str, value: Any) -> str:
        """Summarize a context value."""
        prompt = f"""Summarize the following {key} in 2-3 sentences,
        preserving the most important information for code analysis:

        {str(value)[:2000]}
        """
        return await self.llm_service.generate(prompt)

    def _estimate_tokens(self, value: Any) -> int:
        """Estimate token count."""
        return len(str(value)) // 4

    async def _get_relevance_score(self, key: str, value: Any) -> float:
        """Get relevance score for a context key."""
        # High relevance keys
        if key in ["task", "code", "errors", "critical_findings"]:
            return 0.95

        # Medium relevance
        if key in ["context", "history", "related"]:
            return 0.6

        # Low relevance
        if key in ["metadata", "debug", "raw"]:
            return 0.2

        # Default: use LLM scoring
        return 0.5
```

### 8.3 Note-Taking System

```python
# backend/app/confucius/memory/note_taker.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class NoteType(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    INSIGHT = "insight"
    PATTERN = "pattern"
    DECISION = "decision"


@dataclass
class Note:
    """A structured note for cross-session learning."""
    id: str
    type: NoteType
    problem: str
    solution: Optional[str]
    insights: List[str]
    context_tags: List[str]
    quality_score: float
    created_at: datetime

    def to_markdown(self) -> str:
        """Convert note to Markdown format."""
        return f"""## {self.type.value.upper()}: {self.problem[:50]}...

**Problem:** {self.problem}

**Solution:** {self.solution or "N/A"}

**Insights:**
{chr(10).join(f"- {i}" for i in self.insights)}

**Tags:** {", ".join(self.context_tags)}

**Quality Score:** {self.quality_score:.2f}

---
"""


class NoteTaker:
    """
    Cross-session learning via structured note-taking.

    Records:
    - Successful solutions (for reuse)
    - Failure cases (for avoidance)
    - Insights (for context enrichment)
    - Patterns (for recognition)
    - Decisions (for consistency)
    """

    def __init__(self, repository: "NoteRepository", llm_service):
        self.repository = repository
        self.llm_service = llm_service
        self._recent_notes: List[Note] = []

    async def record(
        self,
        task: str,
        result: Dict[str, Any],
        quality_score: float,
    ) -> Note:
        """Record a task execution as a note."""
        # Determine note type
        note_type = self._determine_type(result, quality_score)

        # Extract structured information
        extracted = await self._extract_note_content(task, result)

        note = Note(
            id=self._generate_id(),
            type=note_type,
            problem=extracted["problem"],
            solution=extracted.get("solution"),
            insights=extracted.get("insights", []),
            context_tags=extracted.get("tags", []),
            quality_score=quality_score,
            created_at=datetime.utcnow(),
        )

        await self.repository.save(note)
        self._recent_notes.append(note)

        return note

    async def retrieve_relevant(
        self,
        task: str,
        context: Dict[str, Any],
        limit: int = 5,
    ) -> List[Note]:
        """Retrieve notes relevant to current task."""
        # Extract keywords from task
        keywords = await self._extract_keywords(task, context)

        # Search by keywords and semantic similarity
        notes = await self.repository.search(
            keywords=keywords,
            limit=limit,
        )

        return notes

    def get_recent_notes(self) -> List[Dict[str, Any]]:
        """Get recently recorded notes."""
        return [
            {
                "id": n.id,
                "type": n.type.value,
                "problem": n.problem[:100],
                "quality_score": n.quality_score,
            }
            for n in self._recent_notes[-10:]
        ]

    async def _extract_note_content(
        self,
        task: str,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use LLM to extract structured note content."""
        prompt = f"""Extract a structured note from this task execution:

Task: {task}

Result: {str(result)[:2000]}

Return JSON with:
- problem: What was the problem being solved?
- solution: What solution was applied? (if successful)
- insights: List of 2-3 key insights learned
- tags: List of context tags (e.g., "ado-leaks", "asp", "batch-processing")
"""
        response = await self.llm_service.generate_json(prompt)
        return response

    def _determine_type(
        self,
        result: Dict[str, Any],
        quality_score: float,
    ) -> NoteType:
        """Determine note type from result and quality."""
        if quality_score >= 0.85:
            return NoteType.SUCCESS
        elif quality_score < 0.5:
            return NoteType.FAILURE
        elif "pattern" in str(result).lower():
            return NoteType.PATTERN
        else:
            return NoteType.INSIGHT

    async def _extract_keywords(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> List[str]:
        """Extract keywords for note retrieval."""
        # Simple extraction + LLM enhancement
        words = task.lower().split()
        keywords = [w for w in words if len(w) > 3]
        return keywords[:10]

    def _generate_id(self) -> str:
        import uuid
        return str(uuid.uuid4())
```

---

## 9. Quality Gate Integration

### 9.1 Quality Scoring Rules

```python
# backend/app/confucius/quality/rules.py

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class QualityDimension(Enum):
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    ACTIONABILITY = "actionability"
    CONSISTENCY = "consistency"


@dataclass
class QualityRule:
    """A single quality evaluation rule."""
    id: str
    dimension: QualityDimension
    description: str
    weight: float
    evaluator: callable  # async function(result) -> score


@dataclass
class QualityScore:
    """Detailed quality score breakdown."""
    overall: float
    dimensions: Dict[QualityDimension, float]
    passed: bool
    feedback: List[str]
    critical_issues: List[str]


class QualityRuleSet:
    """
    Domain-specific quality rules for MarQed.

    Domains:
    - Architecture Analysis
    - Quality Analysis
    - Stability Analysis
    - Estimation
    - Documentation
    """

    @staticmethod
    def get_architecture_rules() -> List[QualityRule]:
        return [
            QualityRule(
                id="arch_completeness",
                dimension=QualityDimension.COMPLETENESS,
                description="Architecture analysis covers all components",
                weight=0.25,
                evaluator=lambda r: 1.0 if r.get("components") else 0.0,
            ),
            QualityRule(
                id="arch_dependencies",
                dimension=QualityDimension.ACCURACY,
                description="Dependencies are correctly identified",
                weight=0.25,
                evaluator=lambda r: min(1.0, len(r.get("dependencies", [])) / 5),
            ),
            QualityRule(
                id="arch_recommendations",
                dimension=QualityDimension.ACTIONABILITY,
                description="Recommendations are actionable",
                weight=0.25,
                evaluator=lambda r: 1.0 if r.get("recommendations") else 0.0,
            ),
            QualityRule(
                id="arch_risks",
                dimension=QualityDimension.RELEVANCE,
                description="Risks are identified and prioritized",
                weight=0.25,
                evaluator=lambda r: 1.0 if r.get("risks") else 0.5,
            ),
        ]

    @staticmethod
    def get_stability_rules() -> List[QualityRule]:
        return [
            QualityRule(
                id="stab_findings",
                dimension=QualityDimension.COMPLETENESS,
                description="All leak categories analyzed",
                weight=0.3,
                evaluator=lambda r: min(1.0, len(r.get("categories_analyzed", [])) / 8),
            ),
            QualityRule(
                id="stab_severity",
                dimension=QualityDimension.ACCURACY,
                description="Severity levels correctly assigned",
                weight=0.3,
                evaluator=lambda r: 1.0 if all(
                    f.get("severity") for f in r.get("findings", [])
                ) else 0.5,
            ),
            QualityRule(
                id="stab_fixes",
                dimension=QualityDimension.ACTIONABILITY,
                description="Fix suggestions provided",
                weight=0.4,
                evaluator=lambda r: sum(
                    1 for f in r.get("findings", []) if f.get("suggested_fix")
                ) / max(1, len(r.get("findings", []))),
            ),
        ]

    @staticmethod
    def get_estimation_rules() -> List[QualityRule]:
        return [
            QualityRule(
                id="est_methodology",
                dimension=QualityDimension.ACCURACY,
                description="IFPUG/NESMA methodology followed",
                weight=0.4,
                evaluator=lambda r: 1.0 if r.get("methodology") else 0.0,
            ),
            QualityRule(
                id="est_components",
                dimension=QualityDimension.COMPLETENESS,
                description="All FP components identified",
                weight=0.3,
                evaluator=lambda r: 1.0 if all([
                    r.get("ilfs"), r.get("eifs"), r.get("eis"),
                    r.get("eos"), r.get("eqs")
                ]) else 0.5,
            ),
            QualityRule(
                id="est_productivity",
                dimension=QualityDimension.CONSISTENCY,
                description="Productivity within normal range (0.5-1.5 FP/hr)",
                weight=0.3,
                evaluator=lambda r: 1.0 if 0.5 <= r.get("productivity", 0) <= 1.5 else 0.0,
            ),
        ]
```

### 9.2 Quality Gate Evaluator

```python
# backend/app/confucius/quality/evaluator.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .rules import QualityRule, QualityScore, QualityDimension, QualityRuleSet


@dataclass
class QualityGateResult:
    """Result of quality gate evaluation."""
    score: QualityScore
    passes_threshold: bool
    feedback: List[str]
    improvement_suggestions: List[str]
    iteration_hint: Optional[str]


class QualityGateEvaluator:
    """
    Evaluates agent output against quality gates.

    Process:
    1. Select domain-specific rules
    2. Evaluate each rule
    3. Calculate weighted score
    4. Generate feedback for iteration
    """

    def __init__(self, llm_service):
        self.llm_service = llm_service
        self._rule_sets = {
            "architecture": QualityRuleSet.get_architecture_rules(),
            "stability": QualityRuleSet.get_stability_rules(),
            "estimation": QualityRuleSet.get_estimation_rules(),
        }

    async def evaluate(
        self,
        results: Dict[str, Any],
        domain: Optional[str] = None,
    ) -> QualityGateResult:
        """Evaluate results against quality gate."""
        # Auto-detect domain if not specified
        if not domain:
            domain = self._detect_domain(results)

        rules = self._rule_sets.get(domain, [])

        # Evaluate each rule
        dimension_scores: Dict[QualityDimension, List[float]] = {}
        feedback = []
        critical_issues = []

        for rule in rules:
            score = await self._evaluate_rule(rule, results)

            if rule.dimension not in dimension_scores:
                dimension_scores[rule.dimension] = []
            dimension_scores[rule.dimension].append(score * rule.weight)

            if score < 0.5:
                feedback.append(f"Low score on {rule.description}: {score:.2f}")
                if rule.weight >= 0.3:
                    critical_issues.append(rule.description)

        # Calculate overall score
        dimension_averages = {
            dim: sum(scores) / len(scores) if scores else 0
            for dim, scores in dimension_scores.items()
        }
        overall = sum(dimension_averages.values()) / len(dimension_averages) if dimension_averages else 0

        quality_score = QualityScore(
            overall=overall,
            dimensions=dimension_averages,
            passed=overall >= 0.85 and len(critical_issues) == 0,
            feedback=feedback,
            critical_issues=critical_issues,
        )

        # Generate iteration hint if needed
        iteration_hint = None
        if not quality_score.passed:
            iteration_hint = await self._generate_iteration_hint(
                results, quality_score
            )

        return QualityGateResult(
            score=quality_score,
            passes_threshold=quality_score.passed,
            feedback=feedback,
            improvement_suggestions=await self._generate_suggestions(quality_score),
            iteration_hint=iteration_hint,
        )

    async def _evaluate_rule(
        self,
        rule: QualityRule,
        results: Dict[str, Any],
    ) -> float:
        """Evaluate a single rule."""
        try:
            # Rules can be sync or async
            if asyncio.iscoroutinefunction(rule.evaluator):
                return await rule.evaluator(results)
            return rule.evaluator(results)
        except Exception:
            return 0.0

    def _detect_domain(self, results: Dict[str, Any]) -> str:
        """Auto-detect domain from results structure."""
        if "architecture" in results or "dependencies" in results:
            return "architecture"
        if "findings" in results or "leaks" in results:
            return "stability"
        if "function_points" in results or "estimation" in results:
            return "estimation"
        return "general"

    async def _generate_iteration_hint(
        self,
        results: Dict[str, Any],
        score: QualityScore,
    ) -> str:
        """Generate hint for next iteration."""
        prompt = f"""The following analysis did not pass quality gates:

Score: {score.overall:.2f}
Critical issues: {', '.join(score.critical_issues)}
Feedback: {'; '.join(score.feedback)}

Current results summary: {str(results)[:500]}

What specific improvements should be made in the next iteration?
Provide 2-3 concrete suggestions.
"""
        return await self.llm_service.generate(prompt)

    async def _generate_suggestions(
        self,
        score: QualityScore,
    ) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []

        for dim, dim_score in score.dimensions.items():
            if dim_score < 0.7:
                suggestions.append(f"Improve {dim.value}: current score {dim_score:.2f}")

        return suggestions
```

---

## 10. API Changes

### 10.1 New Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/confucius/execute` | POST | Execute task through orchestrator |
| `/api/confucius/execute/stream` | GET | SSE streaming execution |
| `/api/confucius/sessions` | GET/POST | Manage orchestrator sessions |
| `/api/confucius/sessions/{id}/memory` | GET | Get session memory state |
| `/api/confucius/extensions` | GET | List registered extensions |
| `/api/confucius/extensions/{name}/config` | GET/PUT | Extension configuration |
| `/api/confucius/quality/evaluate` | POST | Manual quality evaluation |
| `/api/confucius/quality/rules` | GET | Get quality rules |
| `/api/confucius/notes` | GET | Get cross-session notes |
| `/api/confucius/notes/search` | POST | Search notes |
| `/api/confucius/metrics` | GET | Orchestrator metrics |

### 10.2 API Specification

```python
# backend/app/api/confucius_api.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..confucius.orchestrator import ConfuciusOrchestrator, ExecutionResult
from ..confucius.memory.hierarchical import SessionMemory
from ..confucius.quality.evaluator import QualityGateResult


router = APIRouter(prefix="/api/confucius", tags=["Confucius Orchestrator"])


# ========== Request Models ==========

class ExecuteRequest(BaseModel):
    """Request to execute task through orchestrator."""
    task: str = Field(..., description="Task description")
    context: Dict[str, Any] = Field(default_factory=dict, description="Task context")
    session_id: Optional[str] = Field(None, description="Session ID for memory")
    extensions: Optional[List[str]] = Field(None, description="Specific extensions to use")
    max_iterations: int = Field(3, ge=1, le=5, description="Max quality iterations")
    quality_threshold: float = Field(0.85, ge=0.0, le=1.0, description="Quality threshold")


class SessionCreateRequest(BaseModel):
    """Request to create new session."""
    project_id: str = Field(..., description="Project ID")
    name: Optional[str] = Field(None, description="Session name")


class NoteSearchRequest(BaseModel):
    """Request to search notes."""
    keywords: List[str] = Field(..., description="Search keywords")
    note_types: Optional[List[str]] = Field(None, description="Filter by type")
    min_quality: float = Field(0.0, description="Minimum quality score")
    limit: int = Field(10, ge=1, le=100, description="Max results")


# ========== Response Models ==========

class ExecuteResponse(BaseModel):
    """Response from task execution."""
    success: bool
    output: Dict[str, Any]
    quality_score: float
    iterations_used: int
    extensions_called: List[str]
    execution_time_ms: int
    session_id: Optional[str]


class SessionResponse(BaseModel):
    """Session information."""
    session_id: str
    project_id: str
    created_at: datetime
    insights_count: int
    patterns_count: int


class ExtensionResponse(BaseModel):
    """Extension information."""
    name: str
    description: str
    capabilities: List[str]
    domains: List[str]
    enabled: bool


class MetricsResponse(BaseModel):
    """Orchestrator metrics."""
    total_executions: int
    average_quality_score: float
    average_iterations: float
    extension_usage: Dict[str, int]
    memory_usage_mb: float


# ========== Endpoints ==========

@router.post("/execute", response_model=ExecuteResponse)
async def execute_task(
    request: ExecuteRequest,
    orchestrator: ConfuciusOrchestrator = Depends(get_orchestrator),
):
    """
    Execute a task through the Confucius orchestrator.

    The orchestrator will:
    1. Route task to appropriate extensions
    2. Load relevant memory
    3. Execute with quality gates
    4. Iterate if quality threshold not met
    5. Record notes for learning
    """
    result = await orchestrator.execute(
        task=request.task,
        context=request.context,
        session_id=request.session_id,
    )

    return ExecuteResponse(
        success=result.success,
        output=result.output,
        quality_score=result.quality_score,
        iterations_used=result.iterations_used,
        extensions_called=result.extensions_called,
        execution_time_ms=result.execution_time_ms,
        session_id=request.session_id,
    )


@router.get("/execute/stream/{session_id}")
async def execute_task_stream(
    session_id: str,
    task: str,
    orchestrator: ConfuciusOrchestrator = Depends(get_orchestrator),
):
    """
    Execute task with SSE streaming for real-time updates.

    Event types:
    - state: Orchestrator state change
    - extension_start: Extension starting
    - extension_progress: Extension progress update
    - extension_complete: Extension finished
    - quality: Quality gate evaluation
    - complete: Execution complete
    """
    async def event_generator():
        async for event in orchestrator.execute_streaming(
            task=task,
            context={},
            session_id=session_id,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    project_id: Optional[str] = None,
    orchestrator: ConfuciusOrchestrator = Depends(get_orchestrator),
):
    """List orchestrator sessions."""
    sessions = await orchestrator.memory.repository.list_sessions(project_id)
    return [
        SessionResponse(
            session_id=s.session_id,
            project_id=s.project_id,
            created_at=s.created_at,
            insights_count=len(s.insights),
            patterns_count=len(s.patterns),
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    orchestrator: ConfuciusOrchestrator = Depends(get_orchestrator),
):
    """Create new orchestrator session."""
    session = await orchestrator.memory.create_session(request.project_id)
    return SessionResponse(
        session_id=session.session_id,
        project_id=session.project_id,
        created_at=session.created_at,
        insights_count=0,
        patterns_count=0,
    )


@router.get("/sessions/{session_id}/memory")
async def get_session_memory(
    session_id: str,
    orchestrator: ConfuciusOrchestrator = Depends(get_orchestrator),
):
    """Get memory state for session."""
    await orchestrator.memory.load_session(session_id)
    return orchestrator.memory.get_state()


@router.get("/extensions", response_model=List[ExtensionResponse])
async def list_extensions(
    orchestrator: ConfuciusOrchestrator = Depends(get_orchestrator),
):
    """List registered extensions."""
    return [
        ExtensionResponse(
            name=ext.metadata.name,
            description=ext.metadata.description,
            capabilities=ext.metadata.capabilities,
            domains=ext.metadata.domains,
            enabled=True,
        )
        for ext in orchestrator._extensions.values()
    ]


@router.post("/notes/search")
async def search_notes(
    request: NoteSearchRequest,
    orchestrator: ConfuciusOrchestrator = Depends(get_orchestrator),
):
    """Search cross-session notes."""
    notes = await orchestrator.note_taker.repository.search(
        keywords=request.keywords,
        note_types=request.note_types,
        min_quality=request.min_quality,
        limit=request.limit,
    )
    return notes


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    orchestrator: ConfuciusOrchestrator = Depends(get_orchestrator),
):
    """Get orchestrator metrics."""
    return await orchestrator.get_metrics()
```

---

## 11. Database Schema

### 11.1 Migration 070: Confucius Memory Tables

```python
# backend/alembic/versions/070_confucius_memory.py

"""Confucius orchestrator memory tables

Revision ID: 070_confucius_memory
Revises: 069_stability_tables
Create Date: 2026-01-XX
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = '070_confucius_memory'
down_revision = '069_stability_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Confucius Sessions
    op.create_table(
        'confucius_sessions',
        sa.Column('session_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('insights', JSONB, default=[]),
        sa.Column('patterns', JSONB, default=[]),
        sa.Column('decisions', JSONB, default=[]),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_confucius_sessions_project', 'confucius_sessions', ['project_id'])

    # Confucius Entries (per-task)
    op.create_table(
        'confucius_entries',
        sa.Column('entry_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('confucius_sessions.session_id')),
        sa.Column('task', sa.Text, nullable=False),
        sa.Column('context_summary', sa.Text),
        sa.Column('results_summary', sa.Text),
        sa.Column('quality_score', sa.Float),
        sa.Column('iterations_used', sa.Integer, default=1),
        sa.Column('extensions_called', JSONB, default=[]),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_confucius_entries_session', 'confucius_entries', ['session_id'])

    # Confucius Runnables (per-extension call)
    op.create_table(
        'confucius_runnables',
        sa.Column('runnable_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entry_id', UUID(as_uuid=True), sa.ForeignKey('confucius_entries.entry_id')),
        sa.Column('extension_name', sa.String(100), nullable=False),
        sa.Column('input_summary', sa.Text),
        sa.Column('output_summary', sa.Text),
        sa.Column('duration_ms', sa.Integer),
        sa.Column('success', sa.Boolean, default=True),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_confucius_runnables_entry', 'confucius_runnables', ['entry_id'])
    op.create_index('ix_confucius_runnables_extension', 'confucius_runnables', ['extension_name'])

    # Confucius Notes (cross-session learning)
    op.create_table(
        'confucius_notes',
        sa.Column('note_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('note_type', sa.String(50), nullable=False),  # success, failure, insight, pattern
        sa.Column('problem', sa.Text, nullable=False),
        sa.Column('solution', sa.Text),
        sa.Column('insights', JSONB, default=[]),
        sa.Column('context_tags', JSONB, default=[]),
        sa.Column('quality_score', sa.Float),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('confucius_sessions.session_id')),
        sa.Column('entry_id', UUID(as_uuid=True), sa.ForeignKey('confucius_entries.entry_id')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_confucius_notes_type', 'confucius_notes', ['note_type'])
    op.create_index('ix_confucius_notes_session', 'confucius_notes', ['session_id'])

    # Full-text search on notes
    op.execute("""
        CREATE INDEX ix_confucius_notes_search
        ON confucius_notes
        USING gin(to_tsvector('english', problem || ' ' || COALESCE(solution, '')))
    """)

    # Confucius Metrics (for analytics)
    op.create_table(
        'confucius_metrics',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('metric_date', sa.Date, nullable=False),
        sa.Column('total_executions', sa.Integer, default=0),
        sa.Column('successful_executions', sa.Integer, default=0),
        sa.Column('average_quality_score', sa.Float),
        sa.Column('average_iterations', sa.Float),
        sa.Column('extension_usage', JSONB, default={}),
        sa.Column('token_usage', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_confucius_metrics_date', 'confucius_metrics', ['metric_date'], unique=True)


def downgrade() -> None:
    op.drop_table('confucius_metrics')
    op.drop_table('confucius_notes')
    op.drop_table('confucius_runnables')
    op.drop_table('confucius_entries')
    op.drop_table('confucius_sessions')
```

### 11.2 SQLAlchemy Models

```python
# backend/app/models/confucius.py

from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class ConfuciusSession(Base):
    """Session-level memory for cross-task insights."""
    __tablename__ = 'confucius_sessions'

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255))
    insights = Column(JSONB, default=[])
    patterns = Column(JSONB, default=[])
    decisions = Column(JSONB, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    entries = relationship("ConfuciusEntry", back_populates="session")
    notes = relationship("ConfuciusNote", back_populates="session")


class ConfuciusEntry(Base):
    """Entry-level memory for per-task context."""
    __tablename__ = 'confucius_entries'

    entry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('confucius_sessions.session_id'))
    task = Column(Text, nullable=False)
    context_summary = Column(Text)
    results_summary = Column(Text)
    quality_score = Column(Float)
    iterations_used = Column(Integer, default=1)
    extensions_called = Column(JSONB, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ConfuciusSession", back_populates="entries")
    runnables = relationship("ConfuciusRunnable", back_populates="entry")
    notes = relationship("ConfuciusNote", back_populates="entry")


class ConfuciusRunnable(Base):
    """Runnable-level memory for extension execution."""
    __tablename__ = 'confucius_runnables'

    runnable_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey('confucius_entries.entry_id'))
    extension_name = Column(String(100), nullable=False, index=True)
    input_summary = Column(Text)
    output_summary = Column(Text)
    duration_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    entry = relationship("ConfuciusEntry", back_populates="runnables")


class ConfuciusNote(Base):
    """Cross-session learning notes."""
    __tablename__ = 'confucius_notes'

    note_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_type = Column(String(50), nullable=False, index=True)
    problem = Column(Text, nullable=False)
    solution = Column(Text)
    insights = Column(JSONB, default=[])
    context_tags = Column(JSONB, default=[])
    quality_score = Column(Float)
    session_id = Column(UUID(as_uuid=True), ForeignKey('confucius_sessions.session_id'))
    entry_id = Column(UUID(as_uuid=True), ForeignKey('confucius_entries.entry_id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ConfuciusSession", back_populates="notes")
    entry = relationship("ConfuciusEntry", back_populates="notes")


class ConfuciusMetrics(Base):
    """Daily metrics for orchestrator analytics."""
    __tablename__ = 'confucius_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_date = Column(Date, nullable=False, unique=True, index=True)
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    average_quality_score = Column(Float)
    average_iterations = Column(Float)
    extension_usage = Column(JSONB, default={})
    token_usage = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 12. Testing Strategy

### 12.1 Test Pyramid

```
                    ┌─────────────┐
                    │    E2E      │  10%
                    │   Tests     │  (20 tests)
                    ├─────────────┤
                    │ Integration │  20%
                    │   Tests     │  (40 tests)
                    ├─────────────┤
                    │    Unit     │  70%
                    │   Tests     │  (140 tests)
                    └─────────────┘
```

### 12.2 Test Coverage Requirements

| Component | Coverage Target | Test Focus |
|-----------|-----------------|------------|
| `ConfuciusOrchestrator` | 90% | State machine, execution flow |
| `HierarchicalMemory` | 85% | Scope management, persistence |
| `ContextCompressor` | 80% | Compression algorithms |
| `NoteTaker` | 85% | Note extraction, retrieval |
| `BaseAgentExtension` | 80% | Lifecycle hooks |
| `Agent Extensions` | 75% each | Integration with existing services |
| `QualityGateEvaluator` | 90% | Rule evaluation, scoring |
| `API Endpoints` | 85% | Request/response handling |

### 12.3 Test Categories

```python
# backend/tests/unit/confucius/test_orchestrator.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.confucius.orchestrator import (
    ConfuciusOrchestrator,
    OrchestratorConfig,
    OrchestratorState,
)


class TestOrchestratorStateManagement:
    """Test state machine transitions."""

    async def test_initial_state_is_idle(self, orchestrator):
        assert orchestrator.state == OrchestratorState.IDLE

    async def test_execute_transitions_through_states(self, orchestrator):
        states_visited = []
        original_execute = orchestrator._execute_extensions

        async def track_states(*args, **kwargs):
            states_visited.append(orchestrator.state)
            return await original_execute(*args, **kwargs)

        orchestrator._execute_extensions = track_states
        await orchestrator.execute("test task", {})

        assert OrchestratorState.PLANNING in states_visited
        assert OrchestratorState.EXECUTING in states_visited
        assert OrchestratorState.EVALUATING in states_visited


class TestOrchestratorExecution:
    """Test task execution flow."""

    async def test_routes_to_correct_extensions(self, orchestrator, mock_router):
        mock_router.route.return_value = [MagicMock(name="Felix")]

        await orchestrator.execute("analyze architecture", {})

        mock_router.route.assert_called_once()

    async def test_compresses_context_when_over_threshold(
        self, orchestrator, mock_compressor
    ):
        large_context = {"data": "x" * 500000}  # Large context

        await orchestrator.execute("test", large_context)

        mock_compressor.compress.assert_called_once()

    async def test_iterates_on_low_quality(
        self, orchestrator, mock_quality_evaluator
    ):
        mock_quality_evaluator.evaluate.side_effect = [
            MagicMock(passes_threshold=lambda t: False, score=0.5),
            MagicMock(passes_threshold=lambda t: True, score=0.9),
        ]

        result = await orchestrator.execute("test", {})

        assert result.iterations_used == 2

    async def test_fails_after_max_iterations(self, orchestrator, mock_quality_evaluator):
        mock_quality_evaluator.evaluate.return_value = MagicMock(
            passes_threshold=lambda t: False, score=0.3
        )

        result = await orchestrator.execute("test", {})

        assert not result.success
        assert result.iterations_used == orchestrator.config.max_iterations


class TestOrchestratorMemory:
    """Test memory management."""

    async def test_loads_session_memory(self, orchestrator, mock_memory):
        await orchestrator.execute("test", {}, session_id="session-123")

        mock_memory.load_session.assert_called_with("session-123")

    async def test_creates_entry_for_task(self, orchestrator, mock_memory):
        await orchestrator.execute("test task", {"key": "value"})

        mock_memory.create_entry.assert_called_once()

    async def test_updates_runnable_for_each_extension(
        self, orchestrator, mock_memory, mock_router
    ):
        mock_router.route.return_value = [
            MagicMock(name="Felix"),
            MagicMock(name="Quinn"),
        ]

        await orchestrator.execute("test", {})

        assert mock_memory.update_runnable.call_count == 2


class TestOrchestratorNoteTaking:
    """Test cross-session learning."""

    async def test_records_note_on_success(self, orchestrator, mock_note_taker):
        await orchestrator.execute("test", {})

        mock_note_taker.record.assert_called_once()

    async def test_note_includes_quality_score(
        self, orchestrator, mock_note_taker, mock_quality_evaluator
    ):
        mock_quality_evaluator.evaluate.return_value = MagicMock(
            passes_threshold=lambda t: True, score=0.92
        )

        await orchestrator.execute("test", {})

        call_kwargs = mock_note_taker.record.call_args.kwargs
        assert call_kwargs["quality_score"] == 0.92
```

### 12.4 Integration Test Example

```python
# backend/tests/integration/confucius/test_brown_paper_orchestration.py

import pytest
from app.confucius.orchestrator import ConfuciusOrchestrator
from app.confucius.extensions import FelixExtension, QuinnExtension, MiguelExtension


@pytest.mark.integration
class TestBrownPaperOrchestration:
    """Integration tests for Brown Paper workflow through orchestrator."""

    async def test_full_brown_paper_analysis(
        self, orchestrator, sample_asp_code
    ):
        """Test complete Brown Paper analysis flow."""
        result = await orchestrator.execute(
            task="Perform Brown Paper analysis on legacy ASP codebase",
            context={
                "code": sample_asp_code,
                "workflow": "brown_paper",
            },
        )

        assert result.success
        assert result.quality_score >= 0.85
        assert "Felix" in result.extensions_called
        assert "Miguel" in result.extensions_called

        # Verify output structure
        assert "architecture" in result.output
        assert "metrics" in result.output
        assert "recommendations" in result.output

    async def test_memory_reuse_across_tasks(self, orchestrator, sample_asp_code):
        """Test that memory is reused across related tasks."""
        session_id = "test-session-1"

        # First task
        result1 = await orchestrator.execute(
            task="Analyze ASP codebase architecture",
            context={"code": sample_asp_code},
            session_id=session_id,
        )

        # Second task (should reuse memory)
        result2 = await orchestrator.execute(
            task="Identify stability issues in same codebase",
            context={"code": sample_asp_code},
            session_id=session_id,
        )

        # Second task should be faster due to memory reuse
        assert result2.execution_time_ms < result1.execution_time_ms

        # Memory should contain insights from first task
        memory_state = orchestrator.memory.get_state()
        assert memory_state["entries_count"] == 2

    async def test_quality_iteration_improves_output(
        self, orchestrator, incomplete_code
    ):
        """Test that quality iteration improves output."""
        result = await orchestrator.execute(
            task="Analyze incomplete codebase",
            context={"code": incomplete_code},
        )

        # Should iterate due to incomplete analysis
        assert result.iterations_used > 1
        # Final quality should still pass
        assert result.quality_score >= 0.85
```

---

## 13. Rollout Strategy

### 13.1 Feature Flag Configuration

```python
# backend/app/confucius/config.py

from pydantic import BaseModel
from typing import Optional


class ConfuciusFeatureFlags(BaseModel):
    """Feature flags for gradual rollout."""

    # Core features
    enabled: bool = False
    use_hierarchical_memory: bool = False
    use_context_compression: bool = False
    use_note_taking: bool = False
    use_quality_gates: bool = False
    use_streaming: bool = False

    # Workflow integration
    brown_paper_orchestrated: bool = False
    migration_orchestrated: bool = False
    quality_orchestrated: bool = False
    green_paper_orchestrated: bool = False

    # Percentage rollout
    rollout_percentage: int = 0  # 0-100

    # Allowed users/projects
    allowed_project_ids: list[str] = []
    allowed_user_ids: list[str] = []


def should_use_orchestrator(
    flags: ConfuciusFeatureFlags,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> bool:
    """Determine if orchestrator should be used for this request."""
    if not flags.enabled:
        return False

    # Check allowlists
    if project_id and project_id in flags.allowed_project_ids:
        return True
    if user_id and user_id in flags.allowed_user_ids:
        return True

    # Check percentage rollout
    import random
    return random.randint(1, 100) <= flags.rollout_percentage
```

### 13.2 Rollout Schedule

| Week | Rollout % | Features | Validation |
|------|-----------|----------|------------|
| **149** | 0% | Core installed, testing only | Unit tests |
| **150** | 5% | Memory + compression for Brown Paper | Integration tests |
| **151** | 20% | All extensions active | A/B testing |
| **152** | 50% | Quality gates + streaming | Performance metrics |
| **153** | 80% | All workflows | User feedback |
| **154** | 100% | Full migration | Monitoring |

### 13.3 Rollback Procedure

```
ROLLBACK TRIGGERS:
├── Error rate > 5%
├── P95 latency > 2x baseline
├── Quality score regression > 10%
└── User complaints > threshold

ROLLBACK STEPS:
1. Set flags.enabled = False (immediate)
2. Clear orchestrator sessions (optional)
3. Investigate root cause
4. Fix and re-validate
5. Gradual re-rollout

ROLLBACK COMMAND:
$ make confucius-rollback
# Sets all feature flags to false
# Redirects traffic to legacy flow
```

---

## 14. Risk Mitigation

### 14.1 Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **SDK not available** | MEDIUM | HIGH | Build minimal orchestrator without SDK, add SDK later |
| **Performance regression** | MEDIUM | MEDIUM | Extensive load testing, feature flags |
| **Memory bloat** | LOW | MEDIUM | Aggressive compression, configurable retention |
| **Agent incompatibility** | LOW | HIGH | Comprehensive extension testing, fallback to direct calls |
| **Quality gate too strict** | MEDIUM | LOW | Configurable thresholds, override capability |
| **Learning wrong patterns** | LOW | MEDIUM | Human review of patterns, quality filtering |

### 14.2 Contingency Plans

**If SDK not available:**
```
Plan B: Build minimal orchestrator
├── Copy core patterns from paper
├── Implement hierarchical memory
├── Create extension system
├── Skip meta-agent (future)
└── Estimated extra effort: +40 hours
```

**If performance issues:**
```
Mitigation steps:
├── Disable streaming (quick win)
├── Reduce memory retention
├── Simplify compression
├── Async extension execution
└── Cache extension results
```

---

## 15. Success Metrics

### 15.1 Key Performance Indicators

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Context reduction** | 0% | 40%+ | Token count before/after compression |
| **Quality score** | N/A | 0.85+ avg | Quality gate evaluations |
| **First-pass success** | N/A | 70%+ | Tasks passing without iteration |
| **Cross-session reuse** | 0% | 30%+ | Notes retrieved per task |
| **Agent coordination** | Manual | Automatic | Workflow orchestration rate |
| **Latency (P95)** | X ms | <1.5X ms | API response times |
| **Error rate** | X% | <X% | Failed executions |

### 15.2 Dashboard Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│              CONFUCIUS ORCHESTRATOR DASHBOARD                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EXECUTIONS TODAY: 234        SUCCESS RATE: 94.2%               │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Quality Score Distribution                              │    │
│  │  ████████████████████████░░░░░░  87.3% avg               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Extension Usage                                         │    │
│  │  Felix:  ████████████  156                              │    │
│  │  Quinn:  ██████████    134                              │    │
│  │  Miguel: ████████      98                               │    │
│  │  Eliza:  ██████        72                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Memory Usage                                            │    │
│  │  Sessions: 45  |  Entries: 1,234  |  Notes: 567         │    │
│  │  Compression: 42% avg reduction                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  RECENT NOTES:                                                   │
│  ├── [SUCCESS] ADO leaks in batch loops - fixed with cleanup   │
│  ├── [PATTERN] FysioOne uses CreateCusCon() wrapper            │
│  └── [INSIGHT] VBScript case-insensitive matching required     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 16. Dependencies

### 16.1 External Dependencies

| Dependency | Version | Status | Notes |
|------------|---------|--------|-------|
| **Confucius SDK** | Latest | PENDING | `github.com/facebook/confucius` |
| `sse-starlette` | ^1.6.0 | TO INSTALL | SSE streaming |
| `tiktoken` | ^0.5.0 | EXISTS | Token counting |
| `asyncio` | stdlib | EXISTS | Async execution |

### 16.2 Internal Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Fase 21.5 (Workflow Separation) | REQUIRED | AnalysisContract interface |
| Fase 22 (FP Methodology) | RECOMMENDED | Quality scoring rules |
| Fase 23 (Context Engineering) | PARALLEL | Shared patterns |
| Existing agent services | EXISTS | Wrapped as extensions |
| LLM providers | EXISTS | Anthropic, Ollama, etc. |

### 16.3 Prerequisite Completion

```
PREREQUISITES (Must be complete before Week 149):

✅ Fase 21: Stability Analyzer (COMPLETE)
   └── Provides stability scoring for quality gates

⏳ Fase 21.5: Workflow Separation (Week 145-146)
   └── AnalysisContract for clean integration

⏳ Fase 22: FP Methodology (Week 146-147)
   └── Correct estimation for quality rules

⏳ Fase 23: Context Engineering (Week 147-148)
   └── Reference selector patterns (shared)
```

---

## 17. References

### 17.1 External References

| Reference | URL | Notes |
|-----------|-----|-------|
| **arXiv Paper** | [arxiv.org/abs/2512.10398](https://arxiv.org/abs/2512.10398) | Primary source |
| **MarkTechPost Article** | [marktechpost.com](https://www.marktechpost.com/2026/01/09/meta-and-harvard-researchers-introduce-the-confucius-code-agent-cca-a-software-engineering-agent-that-can-operate-at-large-scale-codebases/) | Overview |
| **Emergent Mind - CCA** | [emergentmind.com/topics/confucius-code-agent-cca](https://www.emergentmind.com/topics/confucius-code-agent-cca) | Technical details |
| **Emergent Mind - SDK** | [emergentmind.com/topics/confucius-sdk](https://www.emergentmind.com/topics/confucius-sdk) | SDK architecture |
| **Hugging Face Papers** | [huggingface.co/papers/2512.10398](https://huggingface.co/papers/2512.10398) | Discussion |

### 17.2 Internal References

| Document | Path |
|----------|------|
| Workflow Separation Plan | `docs/architecture/workflow-separation-plan.md` |
| Context Engineering Architecture | `docs/architecture/context-engineering-architecture.md` |
| Brown Paper Enhanced | `docs/architecture/brown-paper-enhanced.md` |
| Agent System | `.project/AGENTS.md` |
| Current Phase | `docs/roadmap/phases-current.md` |

---

## Appendix A: Module Structure

```
backend/app/confucius/
├── __init__.py
├── config.py                        # Configuration & feature flags
├── orchestrator.py                  # ConfuciusOrchestrator main class
│
├── memory/
│   ├── __init__.py
│   ├── types.py                     # Memory scope types
│   ├── hierarchical.py              # HierarchicalMemory
│   ├── compressor.py                # ContextCompressor
│   ├── note_taker.py                # NoteTaker
│   ├── repository.py                # MemoryRepository (database)
│   └── serializers.py               # Memory serialization
│
├── extensions/
│   ├── __init__.py
│   ├── base.py                      # BaseAgentExtension
│   ├── router.py                    # ExtensionRouter
│   ├── felix_extension.py           # Architect
│   ├── quinn_extension.py           # Quality
│   ├── eliza_extension.py           # Estimation
│   ├── diana_extension.py           # Documentation
│   ├── marcus_extension.py          # Migration
│   ├── miguel_extension.py          # Metrics
│   ├── tessa_extension.py           # Testing
│   ├── peter_extension.py           # Product Owner
│   ├── paul_extension.py            # Planning
│   ├── betty_extension.py           # Business
│   └── vicky_extension.py           # Validation
│
├── quality/
│   ├── __init__.py
│   ├── evaluator.py                 # QualityGateEvaluator
│   ├── iteration.py                 # IterationController
│   ├── escalation.py                # EscalationService
│   └── rules.py                     # Quality scoring rules
│
└── api/
    └── confucius_api.py             # REST API endpoints

backend/tests/
├── unit/confucius/
│   ├── test_orchestrator.py
│   ├── test_hierarchical_memory.py
│   ├── test_context_compressor.py
│   ├── test_note_taker.py
│   ├── test_quality_evaluator.py
│   └── extensions/
│       ├── test_felix_extension.py
│       └── ...
│
└── integration/confucius/
    ├── test_brown_paper_orchestration.py
    ├── test_migration_orchestration.py
    └── test_memory_persistence.py
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **AX** | Agent Experience - What the LLM sees |
| **UX** | User Experience - Transparency for humans |
| **DX** | Developer Experience - Extensibility |
| **Extension** | Agent wrapped with lifecycle hooks |
| **Entry** | Single task execution context |
| **Runnable** | Single extension execution |
| **Note** | Cross-session learning artifact |
| **Quality Gate** | Threshold-based output validation |
| **PIV Loop** | Plan-Implement-Validate iteration |

---

## Appendix C: Follow-Up Phase

### Fase 23.6: Stage-Based LLM Council Review (Week 157-162)

After CCA integration is complete, the **Stage-Based Council Review System** extends the PIV loop with automatic multi-model reviews at each development stage.

**Key Integration Points:**
- `StageReviewExtension` hooks into `on_post` lifecycle
- Automatic artifact review when stage completes
- Second round improvement if issues exceed threshold
- Performance tracking feeds back to model selection

**Reference:** [stage-based-council-review-plan.md](./stage-based-council-review-plan.md)

```python
# Integration example
class StageReviewExtension(BaseAgentExtension):
    async def on_post(self, context, result, metadata):
        if metadata.get("stage_type") in self.enabled_stages:
            review = await self.review_service.review_artifact(
                stage_type=metadata["stage_type"],
                artifact=metadata["artifact"]
            )
            if not review.approved:
                return {"should_retry": True, "improved_artifact": review.improved_artifact}
```

---

**Document Control:**
- Author: MarQed AI Team
- Reviewers: [Pending]
- Approval: [Pending]
- Next Review: Week 150
