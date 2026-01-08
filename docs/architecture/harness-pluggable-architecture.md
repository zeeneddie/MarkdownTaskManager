# Pluggable Agent Harness Architecture

**Version:** 1.0
**Date:** 2025-12-18
**Status:** Design Specification

---

## Executive Summary

Deze architectuur definieert een **plug-and-play harness framework** voor AI agents, ontworpen voor:
- Modulaire componenten die onafhankelijk vervangen kunnen worden
- Toekomstige integratie met open-source tooling
- Backward compatibility met bestaande MarQed services
- Configuration-driven behavior

---

## Architectuur Overzicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AGENT HARNESS FRAMEWORK                              │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      HARNESS CORE (Orchestrator)                      │   │
│  │                                                                       │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │   │  Constraint │  │   Context   │  │    Tool     │  │  Version   │  │   │
│  │   │   Manager   │  │   Manager   │  │  Registry   │  │  Tracker   │  │   │
│  │   │  (Module 1) │  │  (Module 2) │  │  (Module 3) │  │ (Module 4) │  │   │
│  │   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │   │
│  │          │                │                │               │          │   │
│  │   ┌──────▼────────────────▼────────────────▼───────────────▼──────┐  │   │
│  │   │                    PLUGIN REGISTRY                            │  │   │
│  │   │  register() | get() | list() | swap() | health_check()       │  │   │
│  │   └───────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                         INTEGRATION LAYER                              │  │
│  │                                                                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │  │
│  │  │ AgentSvc   │  │ KanbanSvc  │  │ ClaudeMem  │  │ Observability  │   │  │
│  │  │ (existing) │  │ (existing) │  │ (existing) │  │   (existing)   │   │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     OPEN SOURCE ADAPTERS (Future)                      │ │
│  │                                                                        │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │ │
│  │  │ LangChain│  │ CrewAI   │  │ AutoGen  │  │ KaibanJS │  │  Dify   │  │ │
│  │  │ Adapter  │  │ Adapter  │  │ Adapter  │  │ Adapter  │  │ Adapter │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Module 1: Agent Constraints Manager

### Purpose
Definieert en enforced wat agents **niet mogen doen**.

### Protocol Interface

```python
from typing import Protocol, List, Dict, Any, Optional
from enum import Enum

class ConstraintSeverity(str, Enum):
    BLOCK = "block"        # Voorkom actie volledig
    WARN = "warn"          # Log warning, sta toe
    AUDIT = "audit"        # Log voor review, sta toe
    APPROVE = "approve"    # Vereist human approval

class ConstraintResult:
    allowed: bool
    severity: ConstraintSeverity
    reason: Optional[str]
    requires_approval: bool
    audit_id: Optional[str]

class ConstraintManagerProtocol(Protocol):
    """
    Abstract interface voor Agent Constraint Management.

    Implementaties kunnen zijn:
    - MarQed native (deze repo)
    - LangChain GuardrailsAdapter
    - NeMo Guardrails Adapter
    - Custom enterprise rules
    """

    async def check_action(
        self,
        agent_id: str,
        action_type: str,
        action_params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ConstraintResult:
        """Check of een actie is toegestaan."""
        ...

    async def get_constraints(
        self,
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """Haal alle constraints op voor een agent."""
        ...

    async def add_constraint(
        self,
        agent_id: str,
        constraint: Dict[str, Any]
    ) -> bool:
        """Voeg een constraint toe."""
        ...

    async def validate_output(
        self,
        agent_id: str,
        output: str,
        output_type: str
    ) -> ConstraintResult:
        """Valideer agent output tegen constraints."""
        ...
```

### Default Implementation

```python
# backend/app/harness/constraints/default.py

class DefaultConstraintManager:
    """
    Native MarQed constraint manager.
    Configuration-driven via YAML/JSON.
    """

    def __init__(self, config_path: str = "config/constraints.yaml"):
        self.config = self._load_config(config_path)
        self._compiled_rules = {}

    # ... implementation
```

### Configuration Schema

```yaml
# config/constraints.yaml
version: "1.0"
global_constraints:
  max_iterations: 10
  max_token_output: 8000
  forbidden_patterns:
    - "DROP TABLE"
    - "rm -rf"
    - "sudo"

agents:
  felix:
    role: "Feature Architect"
    can_do:
      - "file_read"
      - "code_generate"
      - "api_design"
    cannot_do:
      - "file_delete"
      - "db_write_production"
      - "external_api_without_approval"
    requires_approval:
      - "schema_migration"
      - "security_config_change"
    output_constraints:
      max_code_lines: 500
      forbidden_imports: ["os.system", "subprocess.call"]

  quinn:
    role: "Quality Inspector"
    can_do:
      - "file_read"
      - "security_scan"
      - "quality_report"
    cannot_do:
      - "file_write"
      - "code_execute"
```

---

## Module 2: Structured Context Manager

### Purpose
Beheert 3-laags context: **System** (static) → **Task** (dynamic) → **Memory** (compressed).

### Protocol Interface

```python
from typing import Protocol, Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ContextLayer:
    """Een laag in de context stack."""
    name: str
    content: Dict[str, Any]
    token_count: int
    priority: int  # Hogere priority = behouden bij truncatie
    ttl_seconds: Optional[int] = None  # None = permanent
    created_at: datetime = None

@dataclass
class ResolvedContext:
    """Opgeloste context voor een agent call."""
    system: str          # Gerenderde system prompt
    task: str            # Huidige taak context
    memory: str          # Compressed history
    total_tokens: int
    layers_used: List[str]
    truncated: bool

class ContextManagerProtocol(Protocol):
    """
    Abstract interface voor Structured Context Management.

    Implementaties kunnen zijn:
    - MarQed native (uitbreiding Claude-Mem)
    - LangChain Memory Adapter
    - Mem0 Adapter
    - MemGPT Adapter
    """

    async def set_system_context(
        self,
        agent_id: str,
        context: Dict[str, Any]
    ) -> None:
        """Set static system context (rol, regels, ethiek)."""
        ...

    async def set_task_context(
        self,
        session_id: str,
        context: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set dynamic task context."""
        ...

    async def add_memory(
        self,
        session_id: str,
        observation: str,
        tags: Optional[List[str]] = None,
        priority: int = 5
    ) -> str:
        """Voeg observatie toe aan memory layer."""
        ...

    async def resolve_context(
        self,
        agent_id: str,
        session_id: str,
        token_budget: int = 4000
    ) -> ResolvedContext:
        """
        Resolve alle context lagen naar een agent-ready format.
        Past binnen token budget via prioritized truncation.
        """
        ...

    async def compress_memory(
        self,
        session_id: str,
        compression_ratio: float = 0.1
    ) -> int:
        """Compress older memories. Returns tokens saved."""
        ...
```

### Default Implementation

```python
# backend/app/harness/context/default.py

class DefaultContextManager:
    """
    Native MarQed context manager.
    Extends existing ClaudeMemService.
    """

    def __init__(
        self,
        db: AsyncSession,
        claude_mem_service: ClaudeMemService
    ):
        self.db = db
        self.mem = claude_mem_service
        self._system_contexts: Dict[str, ContextLayer] = {}

    async def resolve_context(
        self,
        agent_id: str,
        session_id: str,
        token_budget: int = 4000
    ) -> ResolvedContext:
        """
        Resolution order:
        1. System context (altijd eerst, niet trunceerbaar)
        2. Task context (huidige taak)
        3. Memory (compressed history, trunceerbaar)
        """
        # ... implementation
```

### Configuration Schema

```yaml
# config/context.yaml
version: "1.0"

system_contexts:
  felix:
    role: "Feature Architect"
    mission: |
      Je bent Felix, de Feature Architect agent.
      Je ontwerpt systemen, API's en breekt werk op in taken.
    rules:
      - "Volg altijd de project architectuur conventies"
      - "Genereer geen code zonder specificatie"
      - "Vraag om verduidelijking bij ambiguïteit"
    ethics:
      - "Geen security vulnerabilities introduceren"
      - "Privacy-by-design principes volgen"

  quinn:
    role: "Quality Inspector"
    mission: |
      Je bent Quinn, de Quality Inspector agent.
      Je reviewt code, voert security audits uit en bewaakt kwaliteit.
    rules:
      - "Rapporteer alle gevonden issues"
      - "Prioriteer security boven functionaliteit"

defaults:
  token_budget: 4000
  compression_ratio: 0.1
  memory_ttl_hours: 24
  task_ttl_minutes: 60
```

---

## Module 3: Tool Permission Registry

### Purpose
Registry van beschikbare tools met agent-specifieke permissies.

### Protocol Interface

```python
from typing import Protocol, Dict, Any, List, Optional, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass

class ToolCategory(str, Enum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    CODE_EXECUTE = "code_execute"
    API_INTERNAL = "api_internal"
    API_EXTERNAL = "api_external"
    DATABASE = "database"
    SECURITY = "security"

@dataclass
class ToolDefinition:
    """Definitie van een tool."""
    name: str
    category: ToolCategory
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable[..., Awaitable[Any]]
    requires_approval: bool = False
    rate_limit: Optional[int] = None  # calls per minute
    sandbox_required: bool = False

@dataclass
class ToolCallRequest:
    """Request om een tool aan te roepen."""
    tool_name: str
    agent_id: str
    session_id: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

@dataclass
class ToolCallResult:
    """Resultaat van een tool call."""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: int = 0
    tokens_used: int = 0
    audit_id: Optional[str] = None

class ToolRegistryProtocol(Protocol):
    """
    Abstract interface voor Tool Permission Registry.

    Implementaties kunnen zijn:
    - MarQed native
    - LangChain Tools Adapter
    - OpenAI Function Calling Adapter
    - MCP (Model Context Protocol) Adapter
    """

    def register_tool(
        self,
        tool: ToolDefinition
    ) -> bool:
        """Registreer een nieuwe tool."""
        ...

    def get_tools_for_agent(
        self,
        agent_id: str
    ) -> List[ToolDefinition]:
        """Haal alle toegestane tools op voor een agent."""
        ...

    async def can_use_tool(
        self,
        agent_id: str,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check of agent een tool mag gebruiken."""
        ...

    async def execute_tool(
        self,
        request: ToolCallRequest
    ) -> ToolCallResult:
        """
        Voer een tool uit met permission checks.
        Integreert met ConstraintManager.
        """
        ...

    def get_tool_schema(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Genereer OpenAI-compatible function schema
        voor alle toegestane tools van een agent.
        """
        ...
```

### Default Implementation

```python
# backend/app/harness/tools/default.py

class DefaultToolRegistry:
    """
    Native MarQed tool registry.
    Configuration-driven permissions.
    """

    def __init__(
        self,
        constraint_manager: ConstraintManagerProtocol,
        config_path: str = "config/tools.yaml"
    ):
        self.constraints = constraint_manager
        self.config = self._load_config(config_path)
        self._tools: Dict[str, ToolDefinition] = {}
        self._agent_permissions: Dict[str, List[str]] = {}

    async def execute_tool(
        self,
        request: ToolCallRequest
    ) -> ToolCallResult:
        """Execute with full permission pipeline."""

        # 1. Check constraint manager
        constraint_check = await self.constraints.check_action(
            agent_id=request.agent_id,
            action_type="tool_call",
            action_params={
                "tool": request.tool_name,
                "params": request.parameters
            }
        )

        if not constraint_check.allowed:
            return ToolCallResult(
                success=False,
                result=None,
                error=f"Blocked by constraint: {constraint_check.reason}"
            )

        # 2. Check rate limits
        # 3. Execute in sandbox if required
        # 4. Log to observability
        # ...
```

### Configuration Schema

```yaml
# config/tools.yaml
version: "1.0"

tools:
  file_read:
    category: file_read
    description: "Read file contents"
    parameters:
      path: { type: "string", required: true }
      encoding: { type: "string", default: "utf-8" }
    handler: "app.harness.tools.handlers.file_read"
    rate_limit: 100  # per minute

  code_execute:
    category: code_execute
    description: "Execute code in sandbox"
    parameters:
      code: { type: "string", required: true }
      language: { type: "string", enum: ["python", "javascript"] }
      timeout_seconds: { type: "integer", default: 30 }
    handler: "app.harness.tools.handlers.code_execute"
    sandbox_required: true
    requires_approval: true

  security_scan:
    category: security
    description: "Run security vulnerability scan"
    parameters:
      target_path: { type: "string", required: true }
      scan_type: { type: "string", enum: ["quick", "full"] }
    handler: "app.harness.tools.handlers.security_scan"

agent_permissions:
  felix:
    allowed: ["file_read", "code_generate", "api_design"]
    denied: ["file_delete", "code_execute", "db_write"]
    requires_approval: ["schema_migration"]

  quinn:
    allowed: ["file_read", "security_scan", "quality_check"]
    denied: ["file_write", "code_execute"]

  tessa:
    allowed: ["file_read", "code_execute", "test_run"]
    sandbox_only: ["code_execute"]
```

---

## Module 4: Context Version Tracker

### Purpose
Track elke context state voor reproduceerbaarheid en audit.

### Protocol Interface

```python
from typing import Protocol, Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import hashlib

@dataclass
class ContextSnapshot:
    """Immutable snapshot van context op een moment."""
    version_id: str           # Unique identifier
    content_hash: str         # SHA256 van content
    agent_id: str
    session_id: str
    timestamp: datetime
    layers: Dict[str, Any]    # system, task, memory
    token_count: int
    parent_version: Optional[str] = None  # Voor history chain

@dataclass
class ContextDiff:
    """Verschil tussen twee context versies."""
    from_version: str
    to_version: str
    added: Dict[str, Any]
    removed: Dict[str, Any]
    modified: Dict[str, Any]
    token_delta: int

class ContextVersionTrackerProtocol(Protocol):
    """
    Abstract interface voor Context Version Tracking.

    Implementaties kunnen zijn:
    - MarQed native (PostgreSQL based)
    - Git-based versioning
    - IPFS content-addressed storage
    - MLflow Tracking Adapter
    """

    async def snapshot(
        self,
        agent_id: str,
        session_id: str,
        context: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextSnapshot:
        """Maak een immutable snapshot van huidige context."""
        ...

    async def get_snapshot(
        self,
        version_id: str
    ) -> Optional[ContextSnapshot]:
        """Haal een specifieke snapshot op."""
        ...

    async def get_history(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[ContextSnapshot]:
        """Haal snapshot history op voor een sessie."""
        ...

    async def diff(
        self,
        from_version: str,
        to_version: str
    ) -> ContextDiff:
        """Bereken verschil tussen twee versies."""
        ...

    async def restore(
        self,
        version_id: str
    ) -> Dict[str, Any]:
        """Restore context naar een specifieke versie."""
        ...

    async def link_to_action(
        self,
        version_id: str,
        action_id: str
    ) -> None:
        """Link context snapshot aan een agent action (observability)."""
        ...
```

### Default Implementation

```python
# backend/app/harness/versioning/default.py

class DefaultContextVersionTracker:
    """
    Native MarQed version tracker.
    PostgreSQL-based with content-addressed hashing.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def _compute_hash(self, content: Dict[str, Any]) -> str:
        """Content-addressed hash voor deduplicatie."""
        serialized = json.dumps(content, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    async def snapshot(
        self,
        agent_id: str,
        session_id: str,
        context: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextSnapshot:
        """Create immutable snapshot."""

        content_hash = self._compute_hash(context)

        # Check for existing identical snapshot (dedup)
        existing = await self._find_by_hash(content_hash)
        if existing:
            return existing

        # Create new snapshot
        snapshot = ContextSnapshot(
            version_id=str(uuid4()),
            content_hash=content_hash,
            agent_id=agent_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            layers=context,
            token_count=self._count_tokens(context)
        )

        # Store in database
        # ...

        return snapshot
```

### Database Schema

```sql
-- Migration: add_context_versioning_tables.py

CREATE TABLE context_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id VARCHAR(64) UNIQUE NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    parent_version VARCHAR(64),
    layers JSONB NOT NULL,
    token_count INTEGER NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes for fast lookup
    CONSTRAINT fk_parent FOREIGN KEY (parent_version)
        REFERENCES context_snapshots(version_id)
);

CREATE INDEX idx_snapshots_session ON context_snapshots(session_id);
CREATE INDEX idx_snapshots_hash ON context_snapshots(content_hash);
CREATE INDEX idx_snapshots_agent ON context_snapshots(agent_id);

-- Link table for action ↔ context
CREATE TABLE action_context_links (
    action_id UUID NOT NULL,
    context_version_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    PRIMARY KEY (action_id, context_version_id),
    CONSTRAINT fk_context FOREIGN KEY (context_version_id)
        REFERENCES context_snapshots(version_id)
);
```

---

## Plugin Registry (Core Orchestrator)

### Purpose
Centraal registry voor plug-and-play mounting van modules.

```python
# backend/app/harness/core/registry.py

from typing import Dict, Type, Optional, Any
from enum import Enum
import importlib
import logging

logger = logging.getLogger(__name__)


class ModuleType(str, Enum):
    CONSTRAINTS = "constraints"
    CONTEXT = "context"
    TOOLS = "tools"
    VERSIONING = "versioning"


class PluginRegistry:
    """
    Central registry for harness modules.
    Supports hot-swapping and multiple implementations.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._modules: Dict[ModuleType, Any] = {}
            cls._instance._adapters: Dict[str, Type] = {}
        return cls._instance

    def register_adapter(
        self,
        name: str,
        adapter_class: Type,
        module_type: ModuleType
    ) -> None:
        """
        Register an adapter implementation.

        Example:
            registry.register_adapter(
                "langchain_guardrails",
                LangChainGuardrailsAdapter,
                ModuleType.CONSTRAINTS
            )
        """
        key = f"{module_type.value}:{name}"
        self._adapters[key] = adapter_class
        logger.info(f"Registered adapter: {key}")

    def mount(
        self,
        module_type: ModuleType,
        adapter_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Mount an adapter as the active module.

        Example:
            registry.mount(
                ModuleType.CONSTRAINTS,
                "langchain_guardrails",
                {"model": "gpt-4"}
            )
        """
        key = f"{module_type.value}:{adapter_name}"

        if key not in self._adapters:
            raise ValueError(f"Unknown adapter: {key}")

        adapter_class = self._adapters[key]
        instance = adapter_class(**(config or {}))

        self._modules[module_type] = instance
        logger.info(f"Mounted {adapter_name} for {module_type.value}")

        return instance

    def get(self, module_type: ModuleType) -> Any:
        """Get the currently mounted module."""
        if module_type not in self._modules:
            raise ValueError(f"No module mounted for {module_type.value}")
        return self._modules[module_type]

    def swap(
        self,
        module_type: ModuleType,
        adapter_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Hot-swap a module at runtime."""
        old = self._modules.get(module_type)
        if old and hasattr(old, 'cleanup'):
            old.cleanup()

        return self.mount(module_type, adapter_name, config)

    def health_check(self) -> Dict[str, bool]:
        """Check health of all mounted modules."""
        results = {}
        for module_type, module in self._modules.items():
            try:
                if hasattr(module, 'health_check'):
                    results[module_type.value] = module.health_check()
                else:
                    results[module_type.value] = True
            except Exception as e:
                logger.error(f"Health check failed for {module_type}: {e}")
                results[module_type.value] = False
        return results


# Global singleton
registry = PluginRegistry()
```

---

## Open Source Adapters (Future)

### Adapter Interface Pattern

```python
# backend/app/harness/adapters/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAdapter(ABC):
    """Base class for all external adapters."""

    @abstractmethod
    def __init__(self, **config):
        """Initialize with configuration."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if adapter is healthy."""
        pass

    def cleanup(self) -> None:
        """Cleanup resources on unmount."""
        pass


# Example: LangChain Guardrails Adapter
class LangChainGuardrailsAdapter(BaseAdapter, ConstraintManagerProtocol):
    """
    Adapter for LangChain Guardrails.

    pip install langchain-guardrails
    """

    def __init__(self, model: str = "gpt-4", **config):
        from langchain_guardrails import GuardrailsClient
        self.client = GuardrailsClient(model=model)
        self.config = config

    async def check_action(
        self,
        agent_id: str,
        action_type: str,
        action_params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ConstraintResult:
        """Delegate to LangChain Guardrails."""
        # ... adaptation logic


# Example: Mem0 Adapter
class Mem0ContextAdapter(BaseAdapter, ContextManagerProtocol):
    """
    Adapter for Mem0 memory management.

    pip install mem0ai
    """

    def __init__(self, api_key: str, **config):
        from mem0 import MemoryClient
        self.client = MemoryClient(api_key=api_key)

    # ... implement ContextManagerProtocol methods


# Example: MCP Tools Adapter
class MCPToolsAdapter(BaseAdapter, ToolRegistryProtocol):
    """
    Adapter for Model Context Protocol tools.

    pip install mcp-sdk
    """

    def __init__(self, server_url: str, **config):
        from mcp import MCPClient
        self.client = MCPClient(server_url)

    # ... implement ToolRegistryProtocol methods
```

---

## Configuration-Driven Initialization

### Main Configuration File

```yaml
# config/harness.yaml
version: "1.0"

# Module selection
modules:
  constraints:
    adapter: "default"  # or "langchain_guardrails", "nemo_guardrails"
    config:
      config_path: "config/constraints.yaml"

  context:
    adapter: "default"  # or "mem0", "memgpt"
    config:
      token_budget: 4000
      compression_ratio: 0.1

  tools:
    adapter: "default"  # or "langchain_tools", "mcp"
    config:
      config_path: "config/tools.yaml"
      sandbox_enabled: true

  versioning:
    adapter: "default"  # or "git", "mlflow"
    config:
      dedup_enabled: true
      retention_days: 90

# Integration settings
integrations:
  observability:
    enabled: true
    link_context_to_actions: true

  claude_mem:
    enabled: true
    extend_with_structured_context: true
```

### Initialization Code

```python
# backend/app/harness/init.py

from app.harness.core.registry import registry, ModuleType
from app.harness.constraints.default import DefaultConstraintManager
from app.harness.context.default import DefaultContextManager
from app.harness.tools.default import DefaultToolRegistry
from app.harness.versioning.default import DefaultContextVersionTracker
import yaml


def init_harness(config_path: str = "config/harness.yaml"):
    """
    Initialize harness with configuration.
    Called at application startup.
    """
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Register built-in adapters
    registry.register_adapter("default", DefaultConstraintManager, ModuleType.CONSTRAINTS)
    registry.register_adapter("default", DefaultContextManager, ModuleType.CONTEXT)
    registry.register_adapter("default", DefaultToolRegistry, ModuleType.TOOLS)
    registry.register_adapter("default", DefaultContextVersionTracker, ModuleType.VERSIONING)

    # Mount configured adapters
    for module_name, module_config in config["modules"].items():
        module_type = ModuleType(module_name)
        adapter = module_config.get("adapter", "default")
        adapter_config = module_config.get("config", {})

        registry.mount(module_type, adapter, adapter_config)

    return registry


# Usage in main.py
from app.harness.init import init_harness

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize harness
    harness = init_harness()
    app.state.harness = harness

    yield

    # Cleanup
    for module in harness._modules.values():
        if hasattr(module, 'cleanup'):
            module.cleanup()
```

---

## Integration with Existing Services

### Agent Service Integration

```python
# backend/app/services/agent_service.py (updated)

from app.harness.core.registry import registry, ModuleType


class AgentService:
    """Updated to use harness modules."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.constraints = registry.get(ModuleType.CONSTRAINTS)
        self.context = registry.get(ModuleType.CONTEXT)
        self.tools = registry.get(ModuleType.TOOLS)
        self.versioning = registry.get(ModuleType.VERSIONING)

    async def execute_agent_action(
        self,
        agent_id: str,
        session_id: str,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent action through harness pipeline."""

        # 1. Check constraints
        constraint_result = await self.constraints.check_action(
            agent_id=agent_id,
            action_type=action["type"],
            action_params=action.get("params", {})
        )

        if not constraint_result.allowed:
            return {"error": constraint_result.reason, "blocked": True}

        # 2. Resolve context
        context = await self.context.resolve_context(
            agent_id=agent_id,
            session_id=session_id,
            token_budget=4000
        )

        # 3. Snapshot context for audit
        snapshot = await self.versioning.snapshot(
            agent_id=agent_id,
            session_id=session_id,
            context=context.__dict__
        )

        # 4. Execute with tools
        if action["type"] == "tool_call":
            result = await self.tools.execute_tool(
                ToolCallRequest(
                    tool_name=action["tool"],
                    agent_id=agent_id,
                    session_id=session_id,
                    parameters=action.get("params", {}),
                    context=context.__dict__
                )
            )
        else:
            result = await self._execute_llm_call(agent_id, action, context)

        # 5. Link context to action (observability)
        await self.versioning.link_to_action(
            version_id=snapshot.version_id,
            action_id=result.get("action_id")
        )

        return result
```

---

## API Endpoints

```python
# backend/app/api/harness.py

from fastapi import APIRouter, Depends, HTTPException
from app.harness.core.registry import registry, ModuleType

router = APIRouter(prefix="/api/harness", tags=["harness"])


@router.get("/health")
async def health_check():
    """Check health of all harness modules."""
    return {"status": "ok", "modules": registry.health_check()}


@router.get("/modules")
async def list_modules():
    """List all mounted modules."""
    return {
        "modules": {
            mt.value: type(registry._modules.get(mt)).__name__
            for mt in ModuleType
            if mt in registry._modules
        }
    }


@router.post("/modules/{module_type}/swap")
async def swap_module(
    module_type: ModuleType,
    adapter_name: str,
    config: Dict[str, Any] = {}
):
    """Hot-swap a module at runtime."""
    try:
        registry.swap(module_type, adapter_name, config)
        return {"status": "swapped", "module": module_type.value, "adapter": adapter_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/constraints/{agent_id}")
async def get_agent_constraints(agent_id: str):
    """Get constraints for an agent."""
    constraints = registry.get(ModuleType.CONSTRAINTS)
    return await constraints.get_constraints(agent_id)


@router.get("/tools/{agent_id}")
async def get_agent_tools(agent_id: str):
    """Get available tools for an agent."""
    tools = registry.get(ModuleType.TOOLS)
    tool_list = tools.get_tools_for_agent(agent_id)
    return {"agent_id": agent_id, "tools": [t.name for t in tool_list]}


@router.get("/context/{session_id}/history")
async def get_context_history(session_id: str, limit: int = 100):
    """Get context version history for a session."""
    versioning = registry.get(ModuleType.VERSIONING)
    history = await versioning.get_history(session_id, limit)
    return {"session_id": session_id, "snapshots": history}
```

---

## Directory Structure

```
backend/app/harness/
├── __init__.py
├── init.py                    # Initialization & startup
├── core/
│   ├── __init__.py
│   ├── registry.py            # Plugin registry (singleton)
│   └── protocols.py           # All Protocol definitions
├── constraints/
│   ├── __init__.py
│   ├── default.py             # Native implementation
│   └── schemas.py             # Pydantic models
├── context/
│   ├── __init__.py
│   ├── default.py             # Native implementation
│   └── schemas.py
├── tools/
│   ├── __init__.py
│   ├── default.py             # Native implementation
│   ├── handlers/              # Tool handler implementations
│   │   ├── file_ops.py
│   │   ├── code_execute.py
│   │   └── security.py
│   └── schemas.py
├── versioning/
│   ├── __init__.py
│   ├── default.py             # Native implementation
│   └── schemas.py
└── adapters/
    ├── __init__.py
    ├── base.py                # BaseAdapter class
    ├── langchain_guardrails.py
    ├── mem0.py
    ├── mcp.py
    └── nemo_guardrails.py

config/
├── harness.yaml               # Main harness config
├── constraints.yaml           # Agent constraints
├── tools.yaml                 # Tool definitions & permissions
└── context.yaml               # Context layer configs
```

---

## Migration Path

### Phase 1: Foundation (Week 1)
1. Create directory structure
2. Implement Protocol interfaces
3. Implement PluginRegistry
4. Write database migration for context_snapshots

### Phase 2: Default Implementations (Week 2)
1. DefaultConstraintManager
2. DefaultContextManager (extend ClaudeMemService)
3. DefaultToolRegistry
4. DefaultContextVersionTracker

### Phase 3: Integration (Week 3)
1. Update AgentService to use harness
2. Add API endpoints
3. Update KanbanAgentService
4. Add observability integration

### Phase 4: Adapters (Future)
1. LangChain Guardrails adapter
2. Mem0 adapter
3. MCP tools adapter
4. Community contributions

---

## Benefits

| Aspect | Benefit |
|--------|---------|
| **Modularity** | Elk component onafhankelijk vervangbaar |
| **Open Source Ready** | Protocol interfaces voor community adapters |
| **Configuration-Driven** | Geen code changes voor configuratie |
| **Hot-Swappable** | Runtime module switching |
| **Backward Compatible** | Bestaande services blijven werken |
| **Audit Trail** | Context versioning voor compliance |
| **Testable** | Mock adapters voor unit tests |

---

## Related Documents

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [AGENTS.md](../../AGENTS.md)
- [provider-registry.md](provider-registry.md)
- [observability-layer.md](observability-layer.md)
