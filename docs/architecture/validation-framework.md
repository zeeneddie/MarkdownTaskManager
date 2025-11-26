# Validation Framework Architecture

**Status:** Week 17-26 (Planned)
**Bron:** github.com/zeeneddie/context-engineering-intro
**Impact:** Transformeert code generatie van "hopelijk werkend" naar "gegarandeerd werkend"
**Strategie:** Parallel implementatie met AgentEvolver (0 extra weken)

---

## Design Filosofie

> **"Als /validate slaagt, moet de gebruiker 100% vertrouwen hebben dat de applicatie correct werkt in productie."**

**Kernprincipes:**
1. **Iteratie tot Succes** - Agents fixen automatisch tot validatie slaagt
2. **Early Failure** - Stop vroeg bij kritieke fouten
3. **Comprehensive Coverage** - 5 fasen dekken alle aspecten
4. **Configurable per Workflow** - Elk workflow type heeft eigen validatie regels

---

## High-Level Architectuur

```
+---------------------------------------------------------------------+
|                     VALIDATION FRAMEWORK                             |
|                                                                      |
|  +---------------------------------------------------------------+  |
|  |                    5-PHASE VALIDATION PIPELINE                 |  |
|  |                                                                |  |
|  |  +--------+ +--------+ +--------+ +--------+ +--------+        |  |
|  |  | PHASE 1|>| PHASE 2|>| PHASE 3|>| PHASE 4|>| PHASE 5|        |  |
|  |  |LINTING | | TYPE   | | STYLE  | | UNIT   | | E2E    |        |  |
|  |  |        | | CHECK  | | CHECK  | | TESTS  | | TESTS  |        |  |
|  |  |ruff    | |mypy    | |black   | |pytest  | |API+DB  |        |  |
|  |  |eslint  | |tsc     | |prettier| |jest    | |curl    |        |  |
|  |  +--------+ +--------+ +--------+ +--------+ +--------+        |  |
|  +---------------------------------------------------------------+  |
|                                |                                     |
|  +---------------------------------------------------------------+  |
|  |                    ITERATION LOOP                              |  |
|  |                                                                |  |
|  |   Generate Code -> Validate -> Failed? -> Fix -> Repeat        |  |
|  |        ^                        |                              |  |
|  |        +------------------------+                              |  |
|  |                        (max 3 iterations)                      |  |
|  +---------------------------------------------------------------+  |
|                                |                                     |
|  +---------------------------------------------------------------+  |
|  |                    WORKFLOW INTEGRATION                        |  |
|  |                                                                |  |
|  |  NEW_FEATURE -> Level 1-3    |  MAINTENANCE -> Level 1-2       |  |
|  |  BUG -> Level 2-3 (regr.)    |  QUALITY_AUDIT -> Level 1 only  |  |
|  |  ENHANCEMENT -> Level 1-3    |  MIGRATION -> Level 3 (E2E)     |  |
|  |  QUALITY_IMPROVEMENT -> 1-2  |  TESTING -> Level 2 (meta)      |  |
|  |  PROJECT_DEFINITION -> 1     |                                 |  |
|  +---------------------------------------------------------------+  |
+---------------------------------------------------------------------+
```

---

## Kern Modules

### 1. ValidationService (Python Backend)

**Locatie:** `backend/app/services/validation_service.py`

```python
class ValidationService:
    """5-Phase Validation Pipeline"""

    async def run_full_validation(
        self,
        project_path: str,
        phases: List[ValidationPhase] = None,
        config: ValidationConfig = None
    ) -> ValidationResult:
        """Run all or selected validation phases"""

        results = ValidationResult()

        for phase in phases or ValidationPhase.all():
            phase_result = await self._run_phase(phase, project_path)
            results.add(phase, phase_result)

            if config.stop_on_first_failure and not phase_result.passed:
                return results

        return results

    async def iterate_until_valid(
        self,
        code: str,
        context: WorkflowContext,
        max_iterations: int = 3
    ) -> Tuple[str, ValidationResult]:
        """Iterate on code until validation passes"""

        for i in range(max_iterations):
            result = await self.run_full_validation(code)

            if result.all_passed:
                return code, result

            # Request fix from agent
            code = await self._request_fix(code, result.errors, context)

        raise ValidationMaxIterationsExceeded(max_iterations, result)
```

### 2. ValidationLoop (TypeScript Agents)

**Locatie:** `backend/agents/lib/validationLoop.ts`

```typescript
interface ValidationLoop {
  // Configuration
  maxIterations: number;        // Default: 3
  phases: ValidationPhase[];    // Which phases to run?
  stopOnFirstFailure: boolean;  // Early exit?

  // Core loop
  async validateAndIterate(
    code: string,
    context: WorkflowContext
  ): Promise<ValidatedCode>;

  // Per-phase executors
  async runLinting(code: string): Promise<LintResult>;
  async runTypeCheck(code: string): Promise<TypeCheckResult>;
  async runStyleCheck(code: string): Promise<StyleResult>;
  async runUnitTests(code: string): Promise<TestResult>;
  async runE2ETests(code: string): Promise<E2EResult>;

  // Fix request (to LLM)
  async requestFix(
    code: string,
    errors: ValidationError[]
  ): Promise<string>;
}
```

---

## Data Models

### ValidationResult

```python
class ValidationResult(BaseModel):
    id: UUID
    workflow_id: Optional[UUID]
    phases_executed: List[ValidationPhase]
    results: Dict[ValidationPhase, PhaseResult]
    all_passed: bool
    iteration_count: int
    total_duration_ms: int
    created_at: datetime

class PhaseResult(BaseModel):
    phase: ValidationPhase
    passed: bool
    duration_ms: int
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    metrics: Dict[str, Any]  # coverage, etc.
```

### ValidationConfig (Per Workflow)

```python
class ValidationConfig(BaseModel):
    workflow_type: WorkType
    phases: List[ValidationPhase]
    max_iterations: int = 3
    stop_on_first_failure: bool = True
    required_coverage: float = 0.80
    regression_test_required: bool = False
    report_only: bool = False  # For QUALITY_AUDIT
```

---

## Per-Workflow Validation Rules

| Workflow | Phases | Max Iter | Coverage | Special |
|----------|--------|----------|----------|---------|
| **NEW_FEATURE** | 1-5 (all) | 3 | 80% | - |
| **MAINTENANCE** | 1-2, 4 | 2 | 70% | - |
| **BUG** | 1, 4-5 | 3 | - | Regression test required |
| **QUALITY_AUDIT** | 1-3 | 1 | - | Report only |
| **ENHANCEMENT** | 1-5 | 3 | 80% | - |
| **MIGRATION** | 5 only | 2 | - | E2E critical |
| **QUALITY_IMPROVEMENT** | 1-2, 4 | 2 | 75% | - |
| **TESTING** | 4 | 1 | - | Meta-validation |
| **PROJECT_DEFINITION** | 1 | 1 | - | Template validation |

---

## Integration met AgentEvolver

**Perfecte Synergie!** Validation Framework integreert naadloos met AgentEvolver:

```typescript
interface ValidationExperience extends ExperienceRecord {
  // Inherited from ExperienceRecord
  agent_id: string;
  workflow_type: WorkType;

  // Validation-specific
  validation_attempts: number;
  failed_phases: ValidationPhase[];
  fix_strategies_used: FixStrategy[];
  final_result: 'SUCCESS' | 'MAX_ITERATIONS' | 'MANUAL';

  // Learning
  lessons_learned: string[];
  common_error_patterns: ErrorPattern[];
}
```

**How they work together:**

| AgentEvolver | Validation Framework |
|--------------|---------------------|
| Self-Questioning | Generate validation test cases |
| Self-Navigating | Learn from validation successes |
| Self-Attributing | Track which validations fail |

---

## API Endpoints

| Endpoint | Method | Beschrijving |
|----------|--------|-------------|
| `/api/validation/run` | POST | Run validation pipeline |
| `/api/validation/phases` | GET | List available phases |
| `/api/validation/history` | GET | Validation history |
| `/api/validation/iterate` | POST | Run with iteration loop |
| `/api/validation/config` | GET | Get workflow config |
| `/api/validation/config` | PUT | Update workflow config |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| First-Time Success | >80% | Code passes first try |
| Iteration Success | >95% | Code passes within 3 iterations |
| Unit Test Coverage | >80% | pytest/jest coverage |
| E2E Coverage | >70% | Integration test coverage |
| Validation Time | <5 min | Full pipeline execution |

---

**Related Documents:**
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [Self-Evolution Layer](./self-evolution.md) - Agent learning integration
- [Quality Gates System](./quality-gates.md) - Quality validation rules
