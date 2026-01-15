# Fase 32: Ralph Wiggum Autonomous Agent Loop

**Status:** PLANNED
**Priority:** HIGH (ROI 8.5)
**Timeline:** Week 175-180
**Effort:** 160 uur (~5 weken)
**Dependencies:** Fase 23.5 (Confucius Orchestrator), Fase 23 (Context Engineering)

---

## Executive Summary

Implementatie van de Ralph Wiggum techniek voor autonomous overnight coding, gecombineerd met Cole Medin's PRP (Product Requirements Prompt) framework en modern Agent Harness architecture.

**Het Probleem dat We Oplossen:**
> "Ralph assumes a good prompt exists" - Ralph Wiggum alleen werkt niet goed zonder goede prompt engineering

**De Oplossing:**
```
PRP Framework: Research → Requirements → Blueprint → Engineered PROMPT
                                                           ↓
                                                    Ralph Loop Executes
                                                           ↓
                                                    Agent Harness Manages
```

---

## Architecture Overview

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: PRP FRAMEWORK                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Research   │→ │Requirements │→ │  Blueprint  │→ PROMPT.md  │
│  │  (Codebase) │  │  (Success)  │  │  (Plan)     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 2: RALPH LOOP                          │
│                                                                 │
│  while (!complete && iterations < max) {                        │
│      inject(guardrails + progress)                              │
│      result = execute(PROMPT.md)                                │
│      commit(changes)                                            │
│      evaluate(completion_criteria)                              │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 LAYER 3: AGENT HARNESS                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Human-in-   │ │ Filesystem   │ │ Tool Call    │            │
│  │ Loop Control│ │ Access Mgmt  │ │ Orchestration│            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Sub-agent   │ │ Prompt       │ │ Lifecycle    │            │
│  │ Coordination│ │ Presets      │ │ Hooks        │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: PRP Framework (Wirasm/PRPs-agentic-eng)

Gebaseerd op: [github.com/Wirasm/PRPs-agentic-eng](https://github.com/Wirasm/PRPs-agentic-eng)

### PRP Workflow (3 Commands)

```
/prp-prd  →  PRD Document met Implementation Phases
     ↓
/prp-plan →  Detailed Implementation Plan (.plan.md)
     ↓
/prp-implement → Execute with validation loops
     ↓
/prp-ralph → Autonomous loop until complete
```

### PRPPlanService (prp-plan)

Genereert een `.plan.md` file via 6 fases:

| Phase | Focus | Output |
|-------|-------|--------|
| 0 | Input type detection | Feature description ready |
| 1 | Parse requirements | Problem statement |
| 2 | **Explore codebase** | Pattern table met file:line refs |
| 3 | External docs research | Library references |
| 4 | UX transformation | ASCII diagrams |
| 5 | Architecture analysis | Design rationale |
| 6 | Plan generation | Executable roadmap |

**Task Structure (Atomic, Verifiable):**
```markdown
- [ ] Task 1: CREATE `src/features/new/models.ts`
  - ACTION: What to create/modify
  - IMPLEMENT: Specific details
  - MIRROR: `src/existing/models.ts:45-60` (pattern source)
  - IMPORTS: Required dependencies
  - GOTCHA: Known pitfall + prevention
  - VALIDATE: `npm run typecheck` (executable command)
```

### PRPImplementService (prp-implement)

Voert plan uit met validation loops:

1. **Environment Detection** - Package manager, branch verification
2. **Task Execution** - Sequential, pattern-mirroring
3. **Immediate Validation** - Type-check after EVERY change
4. **Progress Tracking** - Log completion status

**Core Rule:** "Never accumulate broken state - fix before moving on"

### Data Models

```python
@dataclass
class PRPDocument:
    """Product Requirements Prompt document."""
    feature_name: str
    initial_request: str

    # Research phase
    codebase_patterns: List[CodePattern]
    similar_implementations: List[str]
    conventions: List[Convention]
    api_docs: List[APIReference]

    # Requirements phase
    success_criteria: List[SuccessCriterion]
    edge_cases: List[EdgeCase]
    test_requirements: List[TestRequirement]

    # Blueprint phase
    implementation_steps: List[ImplementationStep]
    validation_gates: List[ValidationGate]
    dependencies: List[Dependency]
    confidence_score: float  # 1-10

    # Output
    engineered_prompt: str


@dataclass
class SuccessCriterion:
    """Machine-verifiable success condition."""
    id: str
    description: str
    verification_type: VerificationType  # TEST, BUILD, LINT, MANUAL
    verification_command: Optional[str]
    expected_result: str
```

### Integration with Existing Services

| MarQed Service | PRP Integration |
|---------------|-----------------|
| `CodeRAGService` | Research phase - semantic search |
| `DependencyGraphService` | Identify affected modules |
| `PatternMatcherService` | Find similar implementations |
| `ContextOptimizer` | Token-efficient prompt building |
| `ValidationPipelineService` | Success verification |

---

## Layer 2: Ralph Loop (prp-ralph)

Gebaseerd op Wirasm's implementatie met 4 fases.

### Four-Phase Architecture

```
PHASE 1: PARSE
├── Validate input (.plan.md or .prd.md)
├── Extract max iterations (default: 20)
├── Verify file existence
└── If PRD: identify next executable phase

PHASE 2: SETUP
├── Create state file: .marqed/prp-ralph.state.md
├── Establish archive: .marqed/PRPs/ralph-archives/
└── Display activation message

PHASE 3: EXECUTE (Loop)
├── Read context from state file
├── Identify incomplete tasks from plan
├── Implement changes
├── Run ALL validations (type-check, lint, test, build)
├── Update plan with completion status
├── Append iteration notes to progress log
└── Consolidate discovered patterns

PHASE 4: COMPLETION CHECK
├── Confirm all validations pass
├── Generate implementation report
├── Archive complete run with learnings
├── Update CLAUDE.md with permanent patterns
└── Output: <promise>COMPLETE</promise>
```

### RalphLoopService

```python
class RalphLoopService:
    """
    Autonomous execution loop with state file persistence.

    Based on: Wirasm/PRPs-agentic-eng
    State file: .marqed/prp-ralph.state.md
    """

    STATE_FILE = ".marqed/prp-ralph.state.md"
    ARCHIVE_DIR = ".marqed/PRPs/ralph-archives/"

    async def execute(
        self,
        plan_path: Path,
        max_iterations: int = 20
    ) -> RalphResult:
        """Execute Ralph loop until completion or max iterations."""

        # PHASE 1: PARSE
        plan = self._parse_plan(plan_path)

        # PHASE 2: SETUP
        state = self._create_state_file(plan, max_iterations)

        iteration = 0
        while iteration < max_iterations:
            # PHASE 3: EXECUTE
            # 3.1 Read context
            context = self._build_context(state, plan)

            # 3.2 Identify incomplete tasks
            tasks = self._get_incomplete_tasks(plan)
            if not tasks:
                break

            # 3.3 Implement next task
            result = await self.agent.implement(tasks[0], context)

            # 3.4 Run ALL validations
            validations = await self._run_validations(plan.validation_commands)

            # 3.5 Update plan
            if validations.all_passed:
                self._mark_task_complete(plan, tasks[0])

            # 3.6 Append to progress log
            self._append_progress_log(state, iteration, result, validations)

            # 3.7 Extract patterns
            if result.patterns_discovered:
                self._consolidate_patterns(state, result.patterns_discovered)

            # PHASE 4: COMPLETION CHECK
            if self._is_complete(plan, validations):
                return self._finalize(state, plan, iteration)

            iteration += 1

        return RalphResult(status=RalphStatus.MAX_ITERATIONS)
```

### State File Structure

```markdown
# Ralph State: {feature-name}

## Metadata
- **Iteration**: 3/20
- **Plan File**: .marqed/PRPs/plans/add-user-auth.plan.md
- **Started**: 2026-01-15T10:30:00Z

## Codebase Patterns (Shared Across Iterations)
### Pattern: Database Model
- Source: `src/models/user.py:15-45`
- Usage: All new models should follow this structure

### Pattern: API Route
- Source: `src/routes/users.py:10-35`
- Usage: FastAPI route with dependency injection

## Progress Log

### Iteration 1 (2026-01-15T10:31:00Z)
- **Completed**: Task 1 (CREATE models.py)
- **Validations**: ✅ typecheck, ✅ lint, ❌ test (missing fixture)
- **Patterns Found**: Database model pattern
- **Next**: Fix test fixture, continue Task 2

### Iteration 2 (2026-01-15T10:35:00Z)
- **Completed**: Fixed test fixture, Task 2 (CREATE routes.py)
- **Validations**: ✅ typecheck, ✅ lint, ✅ test
- **Blockers**: None
```

### GuardrailsService

File-based lesson learning across context windows.

```python
class GuardrailsService:
    """
    Manages .marqed/guardrails.md for cross-context learning.

    Guardrails accumulate as the agent learns from failures.
    Each new iteration reads guardrails first.
    """

    GUARDRAILS_PATH = ".marqed/guardrails.md"

    def add_lesson(
        self,
        category: str,
        lesson: str,
        source_error: Optional[str] = None
    ) -> None:
        """Add a learned lesson to guardrails."""

    def load(self) -> str:
        """Load all guardrails for context injection."""

    def prune(self, max_tokens: int = 2000) -> None:
        """Keep guardrails under token limit."""
```

### ArchiveService

Bewaart voltooide runs voor learning.

```python
class ArchiveService:
    """
    Archives completed Ralph runs for future learning.

    Archive structure:
    .marqed/PRPs/ralph-archives/
    └── 2026-01-15_add-user-auth/
        ├── state.md (final state)
        ├── plan.md (completed plan)
        ├── learnings.md (extracted insights)
        └── report.md (implementation report)
    """

    def archive(
        self,
        state: RalphState,
        plan: Plan,
        learnings: List[Learning]
    ) -> ArchiveResult:
        """Archive completed run with all artifacts."""

    def extract_learnings(
        self,
        state: RalphState
    ) -> Tuple[List[Learning], List[PermanentPattern]]:
        """
        Extract two types of learnings:
        - Iteration-specific: Goes to archive
        - Permanent patterns: Goes to CLAUDE.md
        """
```

### CompletionDetector

Dual-gate exit logic.

```python
class CompletionDetector:
    """
    Determines when Ralph loop should exit.

    Uses dual-gate logic:
    1. Completion indicators >= threshold (heuristic)
    2. Explicit EXIT_SIGNAL in output
    """

    def check(
        self,
        result: AgentResult,
        prp: PRPDocument
    ) -> CompletionResult:
        # Gate 1: Success criteria from PRP
        criteria_met = self._check_criteria(result, prp.success_criteria)

        # Gate 2: Explicit exit signal
        exit_signal = self._find_exit_signal(result.output)

        # Gate 3: Test verification
        tests_pass = self._verify_tests(prp.test_requirements)

        return CompletionResult(
            is_complete=criteria_met >= 0.9 and tests_pass,
            exit_signal=exit_signal,
            criteria_met=criteria_met,
            tests_passed=tests_pass
        )
```

### CourseCorrectionService

Detecteert dead-ends en past de aanpak aan (gebaseerd op prp-debug).

```python
class CourseCorrectionService:
    """
    Course correction when Ralph hits obstacles.

    Mechanisms:
    1. Dead-end detection: Backtrack when stuck
    2. Hypothesis rejection: Document why approach failed
    3. Alternative exploration: Pivot to next theory
    4. Root cause analysis: 5 Whys methodology
    """

    async def analyze_failure(
        self,
        iteration: int,
        failure: FailureResult,
        context: ExecutionContext
    ) -> CorrectionResult:
        """
        Analyze failure and determine correction.

        Uses 5 Whys methodology:
        - Every 'because' MUST have evidence
        - Stop when you hit code you can change
        """
        # Build causation chain
        chain = await self._build_causation_chain(failure)

        # Validate chain
        if not self._validate_chain(chain):
            # Pivot to alternative theory
            return CorrectionResult(
                action=CorrectionAction.PIVOT,
                alternative=self._get_next_theory(failure)
            )

        # Generate fix specification
        return CorrectionResult(
            action=CorrectionAction.FIX,
            root_cause=chain.root_cause,
            fix_spec=self._generate_fix_spec(chain)
        )

    def _validate_chain(self, chain: CausationChain) -> bool:
        """
        Apply 3 validation filters:
        1. Causation: Does chain logically flow?
        2. Necessity: Would symptoms disappear without root cause?
        3. Sufficiency: Are co-factors required?
        """
        return (
            chain.is_logical and
            chain.is_necessary and
            chain.is_sufficient
        )
```

### CircuitBreaker

Prevents runaway loops and excessive costs.

```python
class CircuitBreaker:
    """
    Stops Ralph loop when:
    - No progress for N iterations
    - Same error repeats M times
    - Token/cost limit reached
    - Context pollution detected
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.max_no_progress = config.max_no_progress  # default: 3
        self.max_same_error = config.max_same_error    # default: 5
        self.token_limit = config.token_limit          # default: 80K
        self.cost_limit = config.cost_limit            # default: $50
```

---

## Layer 3: Agent Harness Architecture

Gebaseerd op het "2026 is Agent Harnesses" paradigma.

### HumanInLoopController

```python
class HumanInLoopController:
    """
    Pauses execution at critical decision points.

    Critical points:
    - Destructive operations (delete, overwrite)
    - External API calls
    - Database migrations
    - Security-sensitive changes
    """

    async def check_approval(
        self,
        action: AgentAction,
        context: ExecutionContext
    ) -> ApprovalResult:
        if action.risk_level > RiskLevel.MEDIUM:
            return await self._request_human_approval(action)
        return ApprovalResult(approved=True)
```

### FilesystemAccessManager

```python
class FilesystemAccessManager:
    """
    Controls what filesystem operations the agent can perform.

    Based on Claude Code's security model.
    """

    def __init__(self, config: FilesystemConfig):
        self.allowed_paths = config.allowed_paths
        self.denied_paths = config.denied_paths  # system files, secrets
        self.allowed_operations = config.operations

    def validate(self, operation: FileOperation) -> bool:
        # Never touch system files
        if self._is_system_path(operation.path):
            return False
        # Check allowed paths
        return self._is_allowed(operation)
```

### SubAgentCoordinator

```python
class SubAgentCoordinator:
    """
    Coordinates specialized sub-agents for complex tasks.

    Agent types:
    - ResearchAgent: Gathers context
    - ImplementAgent: Writes code
    - TestAgent: Validates changes
    - ReviewAgent: Quality checks
    """

    async def coordinate(
        self,
        task: Task,
        agents: List[SubAgent]
    ) -> CoordinationResult:
        # Sequential or parallel based on dependencies
        results = {}
        for agent in self._order_by_dependencies(agents):
            results[agent.name] = await agent.execute(
                task,
                context=results
            )
        return self._merge_results(results)
```

### LifecycleHooks

```python
class LifecycleHooks:
    """
    Manages Ralph loop lifecycle events.

    Hooks:
    - on_start: Initialize context
    - on_iteration_start: Inject guardrails
    - on_iteration_end: Commit, update progress
    - on_error: Log, learn, retry
    - on_complete: Cleanup, report
    """

    async def on_iteration_end(
        self,
        iteration: int,
        result: IterationResult
    ) -> None:
        # Commit changes
        await self.git.commit(
            message=f"Ralph iteration {iteration}: {result.summary}"
        )
        # Update progress file
        self.progress.append(iteration, result)
        # Check for lessons
        if result.has_failure:
            self.guardrails.add_lesson(
                category=result.failure_category,
                lesson=result.lesson_learned
            )
```

---

## Production Harness Requirements (Cole Medin)

Gebaseerd op Cole Medin's "What production harnesses need" uit zijn YouTube video.

### Gap Analysis

| Requirement | Huidige Status | Actie Nodig |
|-------------|----------------|-------------|
| 1. Initialization agent | PRP Research fase | Expliciet `InitializationAgent` toevoegen |
| 2. Structured progress tracking | ProgressTracker basic | Uitbreiden met gedetailleerde metrics |
| 3. Human approval between stages | Alleen high-risk ops | Stage-based approval workflow |
| 4. Error recovery and rollback | CourseCorrectionService | `RollbackService` met git reset |
| 5. Memory compression | GuardrailsService | `MemoryCompressionService` |
| 6. Multi-phase validation | CompletionDetector | `MultiPhaseValidationPipeline` |

### 1. InitializationAgent

Context gathering vóór werk begint - niet alleen file listing, maar semantisch begrip.

```python
class InitializationAgent:
    """
    Gathers complete context before any work starts.

    Goes beyond file listing:
    - Analyzes codebase architecture
    - Identifies conventions and patterns
    - Maps dependencies and impact zones
    - Loads relevant documentation
    - Builds semantic understanding
    """

    async def initialize(
        self,
        project_path: Path,
        task: PRPDocument
    ) -> InitializationContext:
        """
        Gather all context needed for task execution.

        Returns:
            InitializationContext with:
            - Architecture summary
            - Relevant patterns discovered
            - Dependency graph (affected modules)
            - Convention rules extracted
            - Similar implementations found
        """
        # 1. Analyze architecture
        arch = await self.code_rag.analyze_architecture(project_path)

        # 2. Find similar implementations
        similar = await self.pattern_matcher.find_similar(
            task.feature_name,
            task.initial_request
        )

        # 3. Map impact zone
        impact = await self.dependency_graph.get_impact_zone(
            task.target_files
        )

        # 4. Extract conventions
        conventions = await self.convention_extractor.extract(
            project_path,
            task.target_language
        )

        # 5. Load relevant docs
        docs = await self.doc_loader.load_relevant(
            task.feature_name,
            max_tokens=10000
        )

        return InitializationContext(
            architecture=arch,
            similar_implementations=similar,
            impact_zone=impact,
            conventions=conventions,
            relevant_docs=docs,
            estimated_complexity=self._estimate_complexity(arch, impact)
        )


@dataclass
class InitializationContext:
    """Complete context for task execution."""
    architecture: ArchitectureSummary
    similar_implementations: List[SimilarCode]
    impact_zone: ImpactZone
    conventions: List[Convention]
    relevant_docs: List[DocumentChunk]
    estimated_complexity: ComplexityEstimate

    def to_prompt_context(self) -> str:
        """Convert to prompt-injectable context."""
        return f"""
## Project Context (Auto-gathered)

### Architecture
{self.architecture.summary}

### Conventions to Follow
{self._format_conventions()}

### Similar Implementations (Reference)
{self._format_similar()}

### Impact Analysis
Files affected: {len(self.impact_zone.files)}
Modules affected: {len(self.impact_zone.modules)}
Risk level: {self.impact_zone.risk_level}
"""
```

### 2. StructuredProgressTracker

Niet alleen "files changed" maar gedetailleerde voortgang.

```python
class StructuredProgressTracker:
    """
    Tracks progress with rich metrics, not just file changes.

    Metrics tracked:
    - Task completion percentage
    - Quality score trend
    - Time per task
    - Blockers encountered
    - Rollbacks needed
    - Validation pass rate
    """

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.metrics: List[IterationMetrics] = []

    def record_iteration(
        self,
        iteration: int,
        result: IterationResult
    ) -> None:
        """Record comprehensive iteration metrics."""
        metrics = IterationMetrics(
            iteration=iteration,
            timestamp=datetime.now(timezone.utc),

            # Task progress
            tasks_completed=result.tasks_completed,
            tasks_remaining=result.tasks_remaining,
            completion_percentage=self._calc_percentage(result),

            # Quality metrics
            quality_score=result.quality_score,
            quality_delta=self._calc_quality_delta(result),

            # Validation results
            validations_run=len(result.validations),
            validations_passed=sum(1 for v in result.validations if v.passed),
            validation_pass_rate=self._calc_pass_rate(result.validations),

            # Effort metrics
            duration_seconds=result.duration_seconds,
            tokens_used=result.tokens_used,
            cost_usd=result.cost_usd,

            # Issues
            blockers=result.blockers,
            rollbacks_needed=result.rollbacks_needed,
            lessons_learned=result.lessons_learned
        )

        self.metrics.append(metrics)
        self._persist_state()

    def get_progress_summary(self) -> ProgressSummary:
        """Get current progress summary for dashboard."""
        if not self.metrics:
            return ProgressSummary.empty()

        latest = self.metrics[-1]
        return ProgressSummary(
            current_iteration=latest.iteration,
            completion_percentage=latest.completion_percentage,
            quality_trend=self._calculate_trend(),
            estimated_remaining_iterations=self._estimate_remaining(),
            total_cost=sum(m.cost_usd for m in self.metrics),
            total_duration=sum(m.duration_seconds for m in self.metrics),
            blocker_count=sum(len(m.blockers) for m in self.metrics),
            rollback_count=sum(m.rollbacks_needed for m in self.metrics)
        )


@dataclass
class IterationMetrics:
    """Comprehensive metrics for a single iteration."""
    iteration: int
    timestamp: datetime

    # Progress
    tasks_completed: int
    tasks_remaining: int
    completion_percentage: float

    # Quality
    quality_score: float
    quality_delta: float

    # Validations
    validations_run: int
    validations_passed: int
    validation_pass_rate: float

    # Effort
    duration_seconds: float
    tokens_used: int
    cost_usd: float

    # Issues
    blockers: List[Blocker]
    rollbacks_needed: int
    lessons_learned: List[str]
```

### 3. StageApprovalWorkflow

Human approval tussen development stages, niet alleen voor high-risk operations.

```python
class StageApprovalWorkflow:
    """
    Requires human approval between development stages.

    Stages requiring approval:
    1. After initialization (before first code change)
    2. After major refactoring
    3. Before database migrations
    4. After completing feature (before merge)
    5. When estimated cost exceeds threshold
    """

    def __init__(self, config: ApprovalConfig):
        self.approval_required_stages = config.stages
        self.cost_threshold = config.cost_threshold
        self.auto_approve_low_risk = config.auto_approve_low_risk

    async def check_stage_approval(
        self,
        stage: DevelopmentStage,
        context: ExecutionContext
    ) -> ApprovalResult:
        """
        Check if human approval is needed for this stage transition.
        """
        # Always require approval for configured stages
        if stage.name in self.approval_required_stages:
            return await self._request_approval(
                stage=stage,
                reason=f"Stage '{stage.name}' requires human approval",
                context=context
            )

        # Check cost threshold
        if context.total_cost > self.cost_threshold:
            return await self._request_approval(
                stage=stage,
                reason=f"Cost ${context.total_cost:.2f} exceeds threshold ${self.cost_threshold:.2f}",
                context=context
            )

        # Check for high-impact changes
        if stage.has_database_changes:
            return await self._request_approval(
                stage=stage,
                reason="Stage includes database schema changes",
                context=context
            )

        # Auto-approve low-risk stages if configured
        if self.auto_approve_low_risk and stage.risk_level == RiskLevel.LOW:
            return ApprovalResult(approved=True, auto_approved=True)

        return ApprovalResult(approved=True)

    async def _request_approval(
        self,
        stage: DevelopmentStage,
        reason: str,
        context: ExecutionContext
    ) -> ApprovalResult:
        """Request human approval via configured channel."""
        # Generate approval request
        request = ApprovalRequest(
            stage=stage.name,
            reason=reason,
            summary=context.get_progress_summary(),
            changes_preview=context.get_pending_changes(),
            risk_assessment=stage.risk_assessment,
            estimated_remaining_cost=context.estimate_remaining_cost()
        )

        # Wait for human response
        response = await self.approval_channel.request(request)

        return ApprovalResult(
            approved=response.approved,
            approver=response.user,
            feedback=response.feedback,
            conditions=response.conditions
        )
```

### 4. RollbackService

Explicit rollback met git reset en regression test runs.

```python
class RollbackService:
    """
    Handles error recovery with git rollback and regression testing.

    Rollback strategies:
    1. Soft rollback - revert last commit, keep changes staged
    2. Hard rollback - reset to last known good state
    3. Selective rollback - cherry-pick specific commits
    """

    def __init__(self, repo_path: Path):
        self.repo = git.Repo(repo_path)
        self.checkpoints: List[Checkpoint] = []

    def create_checkpoint(
        self,
        name: str,
        iteration: int
    ) -> Checkpoint:
        """Create a rollback checkpoint at current state."""
        checkpoint = Checkpoint(
            name=name,
            iteration=iteration,
            commit_sha=self.repo.head.commit.hexsha,
            timestamp=datetime.now(timezone.utc),
            test_status=self._run_quick_tests()
        )
        self.checkpoints.append(checkpoint)
        return checkpoint

    async def rollback(
        self,
        to_checkpoint: Optional[Checkpoint] = None,
        strategy: RollbackStrategy = RollbackStrategy.SOFT
    ) -> RollbackResult:
        """
        Rollback to checkpoint or last known good state.
        """
        target = to_checkpoint or self._get_last_good_checkpoint()

        if not target:
            return RollbackResult(
                success=False,
                error="No valid checkpoint found for rollback"
            )

        # Execute rollback based on strategy
        if strategy == RollbackStrategy.SOFT:
            self.repo.git.reset("--soft", target.commit_sha)
        elif strategy == RollbackStrategy.HARD:
            self.repo.git.reset("--hard", target.commit_sha)
        elif strategy == RollbackStrategy.SELECTIVE:
            # Revert specific commits since checkpoint
            commits_to_revert = self._get_commits_since(target.commit_sha)
            for commit in reversed(commits_to_revert):
                self.repo.git.revert(commit.hexsha, "--no-commit")
            self.repo.index.commit(f"Revert to checkpoint: {target.name}")

        # Run regression tests
        regression_result = await self._run_regression_tests()

        return RollbackResult(
            success=True,
            target_checkpoint=target,
            commits_reverted=len(self._get_commits_since(target.commit_sha)),
            regression_tests=regression_result
        )

    async def _run_regression_tests(self) -> RegressionTestResult:
        """Run regression tests after rollback."""
        # Run full test suite
        test_result = await self.test_runner.run_all()

        # Compare with baseline
        baseline = self._get_baseline_metrics()
        regression = self._detect_regression(test_result, baseline)

        return RegressionTestResult(
            tests_run=test_result.total,
            tests_passed=test_result.passed,
            tests_failed=test_result.failed,
            has_regression=regression is not None,
            regression_details=regression
        )


@dataclass
class Checkpoint:
    """Rollback checkpoint."""
    name: str
    iteration: int
    commit_sha: str
    timestamp: datetime
    test_status: TestStatus

    @property
    def is_valid(self) -> bool:
        return self.test_status == TestStatus.ALL_PASSED
```

### 5. MemoryCompressionService

Context handoff tussen agent runs met intelligente compressie.

```python
class MemoryCompressionService:
    """
    Compresses and transfers memory between agent context windows.

    Problem: Context windows fill up, agent loses context.
    Solution: Compress learnings, handoff essential state.
    """

    def __init__(self, max_context_tokens: int = 80000):
        self.max_context_tokens = max_context_tokens
        self.compression_threshold = 0.7  # Compress at 70% capacity

    async def compress_and_handoff(
        self,
        current_context: ExecutionContext,
        state_file: Path
    ) -> HandoffPackage:
        """
        Compress current context and prepare handoff package.

        Compression strategy:
        1. Keep: Critical decisions, active blockers, guardrails
        2. Summarize: Completed work, pattern discoveries
        3. Discard: Verbose logs, redundant context
        """
        # Calculate current token usage
        current_tokens = self._count_tokens(current_context)

        if current_tokens < self.max_context_tokens * self.compression_threshold:
            # No compression needed yet
            return None

        # Extract essential state
        essential = EssentialState(
            # Critical - never compress
            active_task=current_context.current_task,
            blockers=current_context.active_blockers,
            guardrails=current_context.guardrails,

            # Important - compress but keep
            completed_tasks=self._summarize_completed(current_context),
            patterns_discovered=self._extract_key_patterns(current_context),
            validation_status=current_context.validation_summary,

            # Metadata
            iteration=current_context.iteration,
            checkpoint=current_context.last_checkpoint
        )

        # Create compressed summary
        compressed = await self._create_summary(
            current_context,
            max_tokens=5000
        )

        # Write handoff package
        handoff = HandoffPackage(
            essential_state=essential,
            compressed_summary=compressed,
            continuation_prompt=self._generate_continuation_prompt(essential)
        )

        # Persist to state file
        self._write_handoff(state_file, handoff)

        return handoff

    def _generate_continuation_prompt(
        self,
        state: EssentialState
    ) -> str:
        """Generate prompt for next context window."""
        return f"""
## Context Handoff - Iteration {state.iteration}

You are continuing a Ralph Wiggum autonomous coding session.
Previous context was compressed due to token limits.

### Current Task
{state.active_task.description}

### Active Blockers
{self._format_blockers(state.blockers)}

### Guardrails (MUST FOLLOW)
{state.guardrails}

### Completed Work Summary
{state.completed_tasks}

### Key Patterns Discovered
{self._format_patterns(state.patterns_discovered)}

### Validation Status
{state.validation_status}

Continue from where previous context left off.
Checkpoint available at: {state.checkpoint.commit_sha}
"""


@dataclass
class HandoffPackage:
    """Package for context handoff between agent runs."""
    essential_state: EssentialState
    compressed_summary: str
    continuation_prompt: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_total_tokens(self) -> int:
        """Get total token count of handoff package."""
        pass
```

### 6. MultiPhaseValidationPipeline

Clear multi-phase validation - niet alleen "tests pass".

```python
class MultiPhaseValidationPipeline:
    """
    Multi-phase validation beyond just "tests pass".

    Validation Phases:
    1. Syntax - Does code parse?
    2. Types - Does type checking pass?
    3. Lint - Does code follow style?
    4. Unit Tests - Do unit tests pass?
    5. Integration - Do integration tests pass?
    6. Security - Any security issues?
    7. Performance - Any performance regressions?
    8. Documentation - Is code documented?
    """

    def __init__(self, config: ValidationConfig):
        self.phases = [
            SyntaxValidationPhase(),
            TypeCheckPhase(config.type_checker),
            LintPhase(config.linter),
            UnitTestPhase(config.test_runner),
            IntegrationTestPhase(config.integration_config),
            SecurityPhase(config.security_scanner),
            PerformancePhase(config.perf_config),
            DocumentationPhase(config.doc_checker)
        ]

    async def validate(
        self,
        changes: List[FileChange]
    ) -> ValidationPipelineResult:
        """
        Run all validation phases.

        Stops at first failure unless continue_on_failure is set.
        """
        results: List[PhaseResult] = []
        overall_passed = True

        for phase in self.phases:
            # Skip phases not relevant to these changes
            if not phase.is_relevant(changes):
                results.append(PhaseResult(
                    phase=phase.name,
                    status=PhaseStatus.SKIPPED,
                    reason="Not relevant to changed files"
                ))
                continue

            # Run phase
            result = await phase.run(changes)
            results.append(result)

            # Track overall status
            if result.status == PhaseStatus.FAILED:
                overall_passed = False

                # Stop if phase is blocking
                if phase.is_blocking:
                    break

        return ValidationPipelineResult(
            passed=overall_passed,
            phases=results,
            summary=self._generate_summary(results),
            recommendations=self._generate_recommendations(results)
        )

    def _generate_summary(
        self,
        results: List[PhaseResult]
    ) -> str:
        """Generate human-readable summary."""
        passed = sum(1 for r in results if r.status == PhaseStatus.PASSED)
        failed = sum(1 for r in results if r.status == PhaseStatus.FAILED)
        skipped = sum(1 for r in results if r.status == PhaseStatus.SKIPPED)

        return f"""
Validation Summary: {'PASSED' if failed == 0 else 'FAILED'}
├── Passed:  {passed}/{len(results)}
├── Failed:  {failed}/{len(results)}
└── Skipped: {skipped}/{len(results)}

{self._format_failures(results)}
"""


@dataclass
class ValidationPipelineResult:
    """Complete validation pipeline result."""
    passed: bool
    phases: List[PhaseResult]
    summary: str
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "phases": [p.to_dict() for p in self.phases],
            "summary": self.summary,
            "recommendations": self.recommendations
        }
```

---

## Integration with MarQed Platform

### Existing Services Used

| Service | Usage |
|---------|-------|
| `ConfuciusOrchestrator` | Workflow stage management |
| `ContextOptimizer` | Token-efficient context building |
| `QualityGateEvaluator` | Success verification |
| `CrossContextMemoryService` | State persistence |
| `ExperienceStoreService` | Pattern learning |
| `ValidationPipelineService` | Code validation |
| `AgentValidationLoopService` | Quality iteration (already exists!) |

### New API Endpoints

```
POST /api/ralph/start
  Body: { prp_document, config }
  Returns: { ralph_id, status }

GET /api/ralph/status/{ralph_id}
  Returns: { iteration, progress, cost, estimated_remaining }

POST /api/ralph/stop/{ralph_id}
  Returns: { final_status, iterations_completed }

GET /api/ralph/guardrails/{project_id}
  Returns: { lessons: [...] }

POST /api/ralph/prp/generate
  Body: { feature_request, project_id }
  Returns: { prp_document }

POST /api/ralph/prp/execute
  Body: { prp_id, config }
  Returns: { ralph_id }
```

---

## Implementation Plan

### Week 1: PRP Framework (32 uur)

| Task | Hours | Description |
|------|-------|-------------|
| PRPDocument models | 4 | Data classes, enums |
| PRPGeneratorService | 12 | Research, requirements, blueprint |
| CodebaseAnalyzer | 8 | Pattern detection, convention mining |
| API endpoints | 4 | /api/ralph/prp/* |
| Unit tests | 4 | 20+ tests |

### Week 2: Ralph Loop Core (32 uur)

| Task | Hours | Description |
|------|-------|-------------|
| RalphLoopService | 10 | Core execution loop |
| GuardrailsService | 6 | File-based lessons |
| CourseCorrectionService | 6 | 5 Whys methodology |
| CompletionDetector | 4 | Dual-gate exit logic |
| CircuitBreaker | 4 | Safety mechanisms |
| Unit tests | 2 | 15+ tests |

### Week 3: Production Harness Components (40 uur)

| Task | Hours | Description |
|------|-------|-------------|
| InitializationAgent | 6 | Context gathering, semantic understanding |
| StructuredProgressTracker | 6 | Rich metrics beyond file changes |
| StageApprovalWorkflow | 6 | Human approval between stages |
| RollbackService | 8 | Git reset, regression testing |
| MemoryCompressionService | 8 | Context handoff, compression |
| MultiPhaseValidationPipeline | 6 | 8-phase validation beyond "tests pass" |

### Week 4: Agent Harness & Integration (32 uur)

| Task | Hours | Description |
|------|-------|-------------|
| HumanInLoopController | 4 | Approval workflow |
| FilesystemAccessManager | 4 | Security controls |
| SubAgentCoordinator | 6 | Multi-agent orchestration |
| LifecycleHooks | 4 | Event management |
| Confucius integration | 8 | Workflow embedding |
| Cost tracking | 4 | Token/API usage |
| Unit tests | 2 | 15+ tests |

### Week 5: Dashboard & Testing (24 uur)

| Task | Hours | Description |
|------|-------|-------------|
| Dashboard UI | 10 | Progress visualization, approvals |
| E2E tests | 6 | Full workflow tests |
| Performance tuning | 4 | Large repo optimization |
| Documentation | 4 | API docs, examples |

---

## Success Criteria

### Functional Requirements

- [ ] PRP generation produces machine-verifiable prompts
- [ ] Ralph loop executes autonomously for 50+ iterations
- [ ] Guardrails accumulate and prevent repeat failures
- [ ] Circuit breaker stops runaway loops
- [ ] Human approval required for high-risk operations
- [ ] Progress visible in real-time dashboard

### Production Harness Requirements (Cole Medin)

- [ ] InitializationAgent gathers semantic context before work starts
- [ ] StructuredProgressTracker tracks beyond "files changed" (quality, cost, blockers)
- [ ] StageApprovalWorkflow pauses for human approval between stages
- [ ] RollbackService enables git reset with regression testing
- [ ] MemoryCompressionService handles context handoff between runs
- [ ] MultiPhaseValidationPipeline validates 8 phases (syntax → docs)

### Quality Gates

- [ ] 80+ unit tests passing
- [ ] < 5% cost overrun vs estimates
- [ ] < 10% false completion detections
- [ ] Guardrails reduce repeat failures by 70%
- [ ] Rollback recovery time < 60 seconds
- [ ] Context compression maintains 95% essential information

### Performance Metrics

| Metric | Target |
|--------|--------|
| Iteration latency | < 60s average |
| Token efficiency | 80K token rotation |
| Cost per feature | < $25 average |
| Overnight runtime | 8+ hours stable |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Runaway costs | Hard cost limits, circuit breaker |
| Infinite loops | Max iterations, stuck detection |
| Context pollution | Token rotation at 80K |
| Quality degradation | Quality gates per iteration |
| Security issues | Filesystem access control |

---

## References

### Core Implementation
- [Wirasm/PRPs-agentic-eng](https://github.com/Wirasm/PRPs-agentic-eng) - PRP Framework met prp-ralph, prp-plan, prp-implement
- [Ralph Wiggum - Geoffrey Huntley](https://ghuntley.com/ralph/) - Originele concept
- [ralph-claude-code GitHub](https://github.com/frankbria/ralph-claude-code) - Community implementatie

### Best Practices
- [11 Tips for AI Coding with Ralph Wiggum](https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum)
- [Cole Medin's Context Engineering](https://github.com/coleam00/context-engineering-intro) - PRP Framework basis

### Agent Harness Architecture
- [2025 Was Agents, 2026 Is Agent Harnesses](https://aakashgupta.medium.com/2025-was-agents-2026-is-agent-harnesses-heres-why-that-changes-everything-073e9877655e)
- [Agent Harness Importance 2026](https://www.philschmid.de/agent-harness-2026)

---

*Created: Week 158 (2026-01-15)*
*Author: Claude Code*
