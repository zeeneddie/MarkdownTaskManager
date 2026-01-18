# Fase 44: AI Code Complaints Strategy

**Status:** PLANNED
**Priority:** CRITICAL (ROI 9.0)
**Timeline:** Week 185-192
**Effort:** 200 uur (~6-7 weken)

---

## Executive Summary

Research reveals AI-generated code has **1.7x more problems** than human code, with 51% containing security vulnerabilities and 76% of developers not trusting AI output. This fase leverages MarQed's agent ecosystem (Felix, Vicky, Quinn, Marcus) to systematically address these complaints and build demonstrably superior software.

---

## Part 1: Research Findings - Common AI Code Complaints

### Sources
- [CodeRabbit State of AI vs Human Code Report](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report)
- [IEEE Spectrum: AI Coding Degrades](https://spectrum.ieee.org/ai-coding-degrades)
- [Qodo: State of AI Code Quality 2025](https://www.qodo.ai/reports/state-of-ai-code-quality/)
- [vFunction: Vibe Coding Architecture Problems](https://vfunction.com/blog/vibe-coding-architecture-ai-agents/)
- [Palo Alto Networks: AI Security Debt](https://www.paloaltonetworks.com/blog/cloud-security/ai-security-debt/)

### 6 Complaint Categories

| Category | Key Finding | Impact |
|----------|-------------|--------|
| **1. Quality & Correctness** | 1.7x more major issues, 1.75x more logic errors | 76% developers don't trust AI output |
| **2. Security Vulnerabilities** | 51% contains vulnerabilities, 36% SQL injection rate | 1.57x more security findings |
| **3. Architecture Problems** | "Vibe coding" destroys architecture at scale | Dependencies become mess, systems don't scale |
| **4. Technical Debt** | 80-90% refactor avoidance, 2x naming inconsistencies | "Spaghetti code" - tangled structure |
| **5. Context & Understanding** | AI misses context, no business logic understanding | Developers don't understand merged code |
| **6. Productivity Paradox** | 17% individual gain BUT 30% higher failure rates | 23.5% more incidents per PR |

---

## Part 2: MarQed Agent Attack Strategy

### Agent Assignments by Complaint Category

```
COMPLAINT 1: Quality & Correctness
├── Quinn (Quality Inspector) - PRIMARY
│   └── SIG-TOP-10, SOLID, GRASP compliance checks
├── Felix (Architect) - Architecture alignment scoring
├── Marcus (Maintenance) - Complexity analysis
└── LLM Council - 6-model consensus validation

COMPLAINT 2: Security Vulnerabilities
├── Quinn (Quality Inspector) - PRIMARY
│   └── OWASP validation, CVE scanning
├── Security Scanner (21 detectors)
│   ├── injection_detector.py - SQLi, XSS, CMDi
│   ├── auth_logic_detector.py - CWE-862, 863, 287
│   ├── secret_scanner.py - Credential exposure
│   └── 18 more specialized detectors
└── Felix - Privilege escalation review

COMPLAINT 3: Architecture Problems
├── Felix (Feature Architect) - PRIMARY
│   └── ADR generation, trade-off analysis, alignment scoring
├── Vicky (Design Agent) - Design consistency
│   └── Design tokens, UI specs, wireframes
└── Anti-Pattern Detector - 9 Gregor Riegler patterns

COMPLAINT 4: Technical Debt
├── Marcus (Maintenance) - PRIMARY
│   └── Refactor analysis, code smell detection
├── Quinn - Duplication detection (<=3% threshold)
└── Clean Code Compliance - YAGNI, KISS, meaningful names

COMPLAINT 5: Context & Understanding
├── Felix - Context preservation, ADR tracking
├── Diana (Documentation) - Technical specs, API docs
└── Peter (Product Owner) - Business logic validation

COMPLAINT 6: Productivity Paradox
├── Quinn - Pre-merge validation
├── Tessa (Test Engineer) - Coverage validation (>=80%)
├── Multi-Stage Quality Gates - 7 validation stages
└── Blocking Rules - Critical issues block merge
```

---

## Part 3: Preventive Measures (Before Code Generation)

### 3.1 Quality Gates (qualityGateService.ts)

```typescript
// Minimum thresholds to pass
minimumScore: 80%
blockOnCritical: true
blockOnCoverageDecrease: true

// Compliance checks
sigTop10Compliance: >= 80%
solidCompliance: >= 85%
graspCompliance: >= 80%
cleanCodeCompliance: >= 85%
```

### 3.2 LLM Council Consensus (llm_council_service.py)

```python
# 6 models with weighted voting
models = [
    ("deepseek-r1", 2.0),      # Chairman
    ("qwen2.5-coder", 1.5),    # Technical
    ("codellama", 1.5),        # Implementation
    ("mistral", 1.0),          # General
    ("llama3.2", 1.0),         # Fast check
    ("qwen2.5", 1.0)           # Verification
]
consensus_threshold = 0.70  # 70% agreement required
high_confidence_threshold = 0.80
```

### 3.3 Anti-Pattern Detection (antipattern_detector.py)

| Pattern | ID | Threshold | Prevents |
|---------|-----|-----------|----------|
| Overspecification | AP-1 | 0.40 | Over-detailed requirements |
| Premature Genericization | AP-2 | 0.45 | Over-engineering |
| Gold-plating | AP-4 | 0.45 | Unnecessary features |
| Feature Creep | AP-6 | 0.40 | Scope expansion |
| Analysis Paralysis | AP-7 | 0.50 | Decision delays |
| Perfectionism | AP-9 | 0.45 | Endless refinement |

---

## Part 3.5: Guardrails System (Core Defense Layer)

Guardrails vormen de **kern van de defensieve strategie** tegen AI code complaints. Ze werken op 4 niveaus:

### 3.5.1 Bestaande Guardrails Infrastructuur

MarQed heeft al een stevige guardrails basis:

| Component | Status | Locatie | Functie |
|-----------|--------|---------|---------|
| **MarQedConstraintManager** | ✅ LIVE | `backend/app/harness/adapters/constraint_manager.py` | Per-agent action constraints, forbidden patterns |
| **ConstraintManagerProtocol** | ✅ LIVE | `backend/app/harness/core/protocols.py` | Abstract interface (BLOCK/WARN/AUDIT/APPROVE) |
| **SafetyGuardrails (TS)** | ✅ LIVE | `agents/types/Evolution.ts` | Approval rules, rollback triggers |
| **PluginRegistry** | ✅ LIVE | `backend/app/harness/core/registry.py` | Hot-swap guardrails adapters |
| **RollbackService** | ✅ LIVE | `backend/app/services/rollback_service.py` | Snapshots, rollback, approval workflow |
| **GuardrailsService** | 📋 FASE 32 | `.marqed/guardrails.md` | Cross-context learning |

### 3.5.2 Bestaande Agent Constraints

```python
# Uit constraint_manager.py - Per-agent permission matrix
DEFAULT_CONSTRAINTS = {
    "agents": {
        "quinn": {
            "allowed_actions": ["file_read", "code_generate", "security"],
            "denied_actions": ["file_write", "file_delete", "code_execute", "database_write"],
            "requires_approval": [],
        },
        "felix": {
            "allowed_actions": ["file_read", "file_write", "code_generate", "api_internal"],
            "denied_actions": ["file_delete", "code_execute", "database_write"],
            "requires_approval": ["api_external"],
        },
        "marcus": {
            "allowed_actions": ["file_read", "file_write", "code_generate", "database_read"],
            "denied_actions": ["file_delete", "code_execute"],
            "requires_approval": ["database_write"],
        },
        # ... tessa, diana, miguel, peter, etc.
    },
    "global": {
        "forbidden_patterns": [
            r"DROP\s+DATABASE",
            r"rm\s+-rf\s+/",
            r"FORMAT\s+C:",
            r"sudo\s+rm",
        ],
        "forbidden_file_extensions": [".exe", ".dll", ".so", ".dylib", ".sys"]
    }
}
```

### 3.5.3 Nieuwe Guardrails voor AI Code Complaints

| Guardrail Type | Target Complaint | Functie | Implementatie |
|----------------|------------------|---------|---------------|
| **CodeGenGuardrails** | Quality & Correctness | Block low-quality AI code patterns | Extend ConstraintManager |
| **SecurityGuardrails** | Security Vulnerabilities | Real-time security pattern blocking | Integrate 21 detectors |
| **ArchitectureGuardrails** | Architecture Problems | Prevent architecture violations | ADR compliance checks |
| **DebtGuardrails** | Technical Debt | Block code smell patterns | Clean code rules |
| **ContextGuardrails** | Context & Understanding | Ensure context preservation | ADR/doc requirements |
| **LLMOutputGuardrails** | All categories | Validate LLM responses pre-use | Output validation |

### 3.5.4 CodeGenGuardrails (Nieuw)

Specifieke guardrails voor AI-gegenereerde code:

```python
class CodeGenGuardrails:
    """
    Guardrails specifiek voor AI code generatie.
    Blokkeert bekende AI code anti-patterns.
    """

    AI_CODE_ANTIPATTERNS = {
        "excessive_comments": {
            "pattern": r"(#|//)\s*.{100,}",  # Over-commented code
            "severity": "WARN",
            "message": "AI tends to over-comment - review necessity"
        },
        "placeholder_code": {
            "pattern": r"TODO|FIXME|pass\s*#|\.\.\.(?!,)",
            "severity": "BLOCK",
            "message": "Incomplete placeholder code detected"
        },
        "hallucinated_imports": {
            "pattern": r"from\s+(?!app\.|backend\.|agents\.)\w+_nonexistent",
            "severity": "BLOCK",
            "message": "Potentially hallucinated import"
        },
        "magic_numbers": {
            "pattern": r"(?<!['\"])\b(?!0|1|2|10|100|1000)\d{2,}\b(?!['\"])",
            "severity": "WARN",
            "message": "Magic number - consider named constant"
        },
        "deep_nesting": {
            "pattern": r"(\s{16,}|\t{4,})(if|for|while|try)",
            "severity": "WARN",
            "message": "Deep nesting (>4 levels) - refactor recommended"
        },
        "long_functions": {
            "check": "line_count > 60",
            "severity": "WARN",
            "message": "Function exceeds SIG recommendation (60 lines)"
        },
        "high_complexity": {
            "check": "cyclomatic_complexity > 10",
            "severity": "BLOCK",
            "message": "Cyclomatic complexity too high (>10)"
        }
    }

    async def validate_generated_code(
        self,
        code: str,
        language: str,
        context: dict
    ) -> GuardrailResult:
        """Validate AI-generated code against guardrails."""
```

### 3.5.5 SecurityGuardrails (Nieuw)

Real-time security pattern blocking tijdens generatie:

```python
class SecurityGuardrails:
    """
    Real-time security guardrails.
    Integreert met 21 security detectors.
    """

    CRITICAL_SECURITY_PATTERNS = {
        "sql_injection": {
            "pattern": r"f['\"].*SELECT.*{.*}|\.format\(.*\).*SELECT",
            "cwe": "CWE-89",
            "severity": "BLOCK",
            "fix_hint": "Use parameterized queries"
        },
        "command_injection": {
            "pattern": r"os\.system\(|subprocess\.(?!run).*shell=True",
            "cwe": "CWE-78",
            "severity": "BLOCK",
            "fix_hint": "Use subprocess.run with list args"
        },
        "path_traversal": {
            "pattern": r"\.\./|\.\.\\\\",
            "cwe": "CWE-22",
            "severity": "BLOCK",
            "fix_hint": "Use os.path.realpath and validate"
        },
        "hardcoded_secrets": {
            "pattern": r"(?i)(password|secret|api_key|token)\s*=\s*['\"][^'\"]{8,}['\"]",
            "cwe": "CWE-798",
            "severity": "BLOCK",
            "fix_hint": "Use environment variables"
        },
        "eval_usage": {
            "pattern": r"\beval\s*\(|\bexec\s*\(",
            "cwe": "CWE-95",
            "severity": "BLOCK",
            "fix_hint": "Avoid eval/exec - use safe alternatives"
        }
    }

    async def validate_security(
        self,
        code: str,
        run_full_scan: bool = False
    ) -> GuardrailResult:
        """Fast security validation with optional deep scan."""
```

### 3.5.6 ArchitectureGuardrails (Nieuw)

Voorkom "vibe coding" architecture degradatie:

```python
class ArchitectureGuardrails:
    """
    Architecture compliance guardrails.
    Prevent architecture violations tijdens code gen.
    """

    ARCHITECTURE_RULES = {
        "layer_violation": {
            "check": "imports_cross_layer_boundary",
            "severity": "WARN",
            "message": "Cross-layer import detected"
        },
        "circular_dependency": {
            "check": "creates_circular_import",
            "severity": "BLOCK",
            "message": "Circular dependency would be created"
        },
        "god_class": {
            "check": "class_method_count > 20 or class_loc > 500",
            "severity": "WARN",
            "message": "Class too large - consider splitting"
        },
        "missing_interface": {
            "check": "external_dependency_without_interface",
            "severity": "WARN",
            "message": "External dependency should use interface"
        },
        "adr_compliance": {
            "check": "violates_adr_decision",
            "severity": "BLOCK",
            "message": "Code violates ADR decision"
        }
    }
```

### 3.5.7 Guardrails Pipeline Integratie

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GUARDRAILS PIPELINE                             │
│                                                                      │
│  INPUT: Code Generation Request                                      │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────┐                                                │
│  │ PRE-GENERATION  │  ConstraintManager.check_action()              │
│  │ GUARDRAILS      │  - Agent permissions                           │
│  │                 │  - Action type validation                       │
│  └────────┬────────┘                                                │
│           │ PASS                                                     │
│           ▼                                                            │
│  ┌─────────────────┐                                                │
│  │ CONTEXT         │  ContextGuardrails.validate()                  │
│  │ GUARDRAILS      │  - ADR requirements check                       │
│  │                 │  - Context completeness                         │
│  └────────┬────────┘                                                │
│           │ PASS                                                     │
│           ▼                                                            │
│  ╔═════════════════╗                                                │
│  ║ CODE GENERATION ║  LLM generates code                            │
│  ╚════════╤════════╝                                                │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────┐                                                │
│  │ POST-GENERATION │  CodeGenGuardrails.validate()                  │
│  │ GUARDRAILS      │  - AI anti-patterns                            │
│  │                 │  - Code quality checks                          │
│  └────────┬────────┘                                                │
│           │ PASS                                                     │
│           ▼                                                            │
│  ┌─────────────────┐                                                │
│  │ SECURITY        │  SecurityGuardrails.validate()                 │
│  │ GUARDRAILS      │  - Critical patterns (instant)                  │
│  │                 │  - Full scan (optional)                         │
│  └────────┬────────┘                                                │
│           │ PASS                                                     │
│           ▼                                                            │
│  ┌─────────────────┐                                                │
│  │ ARCHITECTURE    │  ArchitectureGuardrails.validate()             │
│  │ GUARDRAILS      │  - Layer violations                             │
│  │                 │  - ADR compliance                               │
│  └────────┬────────┘                                                │
│           │ PASS                                                     │
│           ▼                                                            │
│  ┌─────────────────┐                                                │
│  │ DEBT            │  DebtGuardrails.validate()                     │
│  │ GUARDRAILS      │  - Clean code rules                             │
│  │                 │  - Duplication check                            │
│  └────────┬────────┘                                                │
│           │ PASS                                                     │
│           ▼                                                            │
│  OUTPUT: Validated Code (or BLOCK with feedback)                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.5.8 Guardrails Severity Levels

| Level | Action | Use Case |
|-------|--------|----------|
| **BLOCK** | Reject code, require fix | Critical security, architecture violations |
| **WARN** | Accept with warning | Minor issues, recommendations |
| **AUDIT** | Log for review | Tracking, compliance |
| **APPROVE** | Require human approval | High-risk changes |

### 3.5.9 Guardrails Files te Implementeren

| File | Prioriteit | Beschrijving |
|------|------------|--------------|
| `backend/app/services/guardrails/code_gen_guardrails.py` | HIGH | AI code anti-pattern detection |
| `backend/app/services/guardrails/security_guardrails.py` | HIGH | Real-time security pattern blocking |
| `backend/app/services/guardrails/architecture_guardrails.py` | MEDIUM | Layer/ADR compliance |
| `backend/app/services/guardrails/debt_guardrails.py` | MEDIUM | Clean code enforcement |
| `backend/app/services/guardrails/context_guardrails.py` | MEDIUM | Context/ADR requirements |
| `backend/app/services/guardrails/guardrails_pipeline.py` | HIGH | Pipeline orchestration |
| `backend/app/services/guardrails/__init__.py` | HIGH | Module exports |

### 3.5.10 Guardrails Integration met Bestaande Services

```python
# Integration pattern
class AIComplaintGuardrailsOrchestrator:
    """
    Central guardrails orchestrator for AI code complaints strategy.
    Integrates all guardrail types into single validation pipeline.
    """

    def __init__(self):
        # Bestaande services
        self.constraint_manager = MarQedConstraintManager()
        self.security_scanner = SecurityScanOrchestrator()
        self.quality_gate = QualityGateService()

        # Nieuwe guardrails
        self.code_gen_guardrails = CodeGenGuardrails()
        self.security_guardrails = SecurityGuardrails()
        self.architecture_guardrails = ArchitectureGuardrails()
        self.debt_guardrails = DebtGuardrails()
        self.context_guardrails = ContextGuardrails()

    async def validate_generated_code(
        self,
        code: str,
        agent_id: str,
        context: dict,
        options: ValidationOptions
    ) -> ValidationResult:
        """
        Full guardrails pipeline execution.
        Returns ValidationResult with pass/fail and detailed feedback.
        """
```

---

## Part 4: Detective Controls (During/After Generation)

### 4.1 Security Scanner Suite (21+ Detectors)

| Detector | CWE Coverage | Blocks |
|----------|--------------|--------|
| injection_detector | CWE-89, 78, 79, 90, 943 | CRITICAL |
| auth_logic_detector | CWE-862, 863, 287, 306 | CRITICAL |
| secret_scanner | CWE-798 | CRITICAL |
| crypto_error_detector | CWE-326, 327, 328 | HIGH |
| memory_safety_detector | CWE-787, 416, 125, 119 | CRITICAL |
| concurrency_error_detector | CWE-362, 367, 833 | HIGH |
| web_security_detector | CWE-1321, 1236 | HIGH |
| path_security_detector | CWE-22, 427, 428 | HIGH |
| control_flow_detector | Logic errors | MEDIUM |
| boolean_logic_detector | Boolean errors | MEDIUM |

### 4.2 SIG-TOP-10 Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Unit Size | < 60 lines | Per function/method |
| Cyclomatic Complexity | <= 10 | Per unit |
| Code Duplication | <= 3% | Codebase-wide |
| Interface Size | < 4 parameters | Per function |
| Module Coupling | Loose | Dependency analysis |
| Component Balance | No module > 10% | Size distribution |

### 4.3 Test Strategy Enforcement

```typescript
testStrategy: {
    unitTests: required,
    integrationTests: required,
    e2eTests: optional,
    coverageTarget: 80%,
    patterns: {
        aaaPattern: true,      // Arrange-Act-Assert
        firstPrinciples: true, // F.I.R.S.T
        testPyramid: true      // Unit > Integration > E2E
    }
}
```

---

## Part 5: Corrective Actions (When Issues Found)

### 5.1 Automated Retry with Feedback

```typescript
// Exponential backoff
maxRetries: 3
backoffTime: 2^(attempt-1) * 1000ms

// Feedback generation
feedbackForRetry = generateRetryFeedback(failedChecks)
suggestedFixes = getSuggestedFixes(issues)
```

### 5.2 Escalation Path

```
Attempt 1 → Retry with specific feedback
Attempt 2 → Retry with enhanced context
Attempt 3 → Escalate to human review
```

### 5.3 Security Fix Generation

```python
@dataclass
class SuggestedFix:
    description: str           # What to fix
    replacement_text: str      # Safe code
    diff: str                  # Before/after
    confidence: float          # Fix reliability
```

---

## Part 6: Integrated Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MARQED SUPERIOR SOFTWARE PIPELINE                │
│                                                                      │
│  PHASE 1: REQUIREMENTS                                               │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────────┐         │
│  │ Peter   │──►│ Felix   │──►│ Vicky   │──►│ LLM Council │         │
│  │ Business│   │ Arch    │   │ Design  │   │ Consensus   │         │
│  │ Context │   │ ADRs    │   │ Tokens  │   │ (6 models)  │         │
│  └─────────┘   └─────────┘   └─────────┘   └─────────────┘         │
│                                                     │                │
│  PHASE 2: PRE-IMPLEMENTATION GATES                  ▼                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ ✓ SIG Compliance   ✓ SOLID Check   ✓ Anti-Pattern Scan     │   │
│  │ ✓ Security Patterns ✓ Context Injection ✓ ADR Reference    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                     │                │
│  PHASE 3: GENERATION + VALIDATION                   ▼                │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────────┐         │
│  │ Code    │──►│ Quinn   │──►│ Tessa   │──►│ Security    │         │
│  │ Generate│   │ Quality │   │ Tests   │   │ Scanner     │         │
│  │         │   │ Check   │   │ 80%+    │   │ 21 Detectors│         │
│  └─────────┘   └─────────┘   └─────────┘   └─────────────┘         │
│                                                     │                │
│  PHASE 4: MERGE GATE (ALL MUST PASS)               ▼                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ □ Quality Score >= 80%       □ No CRITICAL security         │   │
│  │ □ Test Coverage >= 80%       □ Documentation complete       │   │
│  │ □ LLM Council approved       □ Anti-patterns clear          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                     │                │
│  PHASE 5: POST-MERGE                                ▼                │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐                           │
│  │ Diana   │   │ Marcus  │   │ Monitor │                           │
│  │ Docs    │   │ Debt    │   │ Metrics │                           │
│  │ Generate│   │ Track   │   │ Track   │                           │
│  └─────────┘   └─────────┘   └─────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 7: Success Metrics & KPIs

### Target: Outperform Industry AI Code by 3x

| Metric | Industry AI | MarQed Target | Measurement |
|--------|-------------|---------------|-------------|
| Major Issues/100 LOC | 1.7x human | **< 0.5x human** | Quinn quality scan |
| Security Finding Rate | 51% | **< 10%** | Security scanner |
| SQL Injection Rate | 36% | **< 1%** | injection_detector |
| Architecture Alignment | Unknown | **>= 85%** | Felix alignment score |
| Code Duplication | High | **<= 3%** | SIG duplication check |
| Test Coverage | Variable | **>= 80%** | Coverage reports |
| Incident Rate per PR | 23.5% | **< 5%** | Incident tracking |
| Change Failure Rate | 30% | **< 10%** | Deployment tracking |
| First-Pass Quality Gate | Low | **>= 90%** | Quality gate logs |

---

## Part 8: Implementation Components

### Existing Files to Leverage

| Component | File Path | Status |
|-----------|-----------|--------|
| Quality Gates | `agents/services/qualityGateService.ts` | ✅ EXISTS |
| Security Scanner | `backend/app/services/security_scanner/orchestrator.py` | ✅ EXISTS |
| Anti-Pattern Detection | `backend/app/services/orchestration/antipattern_detector.py` | ✅ EXISTS |
| LLM Council | `backend/app/services/llm_council_service.py` | ✅ EXISTS |
| Agent Service | `backend/app/services/agent_service.py` | ✅ EXISTS |
| Stack Agent Factory | `backend/app/services/stack_agent_factory.py` | ✅ EXISTS |
| New Feature Workflow | `agents/workflows/newFeatureWorkflow.ts` | ✅ EXISTS |
| Confucius Quality Rules | `backend/app/confucius/quality/rules.py` | ✅ EXISTS |

### New Components to Build

| Component | Purpose | File Path | Priority |
|-----------|---------|-----------|----------|
| AIComplaintDashboard | Track metrics vs industry baselines | `backend/app/services/ai_complaint_dashboard_service.py` | HIGH |
| ContextPreservationService | ADR tracking across generations | `backend/app/services/context_preservation_service.py` | HIGH |
| RealTimeQualityFeedback | During-generation validation | `backend/app/services/realtime_quality_feedback_service.py` | MEDIUM |
| AutomatedFixGenerator | Security vulnerability auto-fixes | `backend/app/services/automated_fix_generator_service.py` | MEDIUM |
| LearningSystem | Track patterns causing issues | `backend/app/services/learning_system_service.py` | LOW |

### API Endpoints to Create

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai-complaints/dashboard` | GET | Get current metrics vs baselines |
| `/api/ai-complaints/metrics/{project_id}` | GET | Get project-specific metrics |
| `/api/ai-complaints/compare` | POST | Compare against industry baselines |
| `/api/context/adrs` | GET | List all ADRs for a project |
| `/api/context/adrs/{adr_id}` | GET | Get specific ADR details |
| `/api/context/preserve` | POST | Preserve context for generation |
| `/api/quality/realtime` | WebSocket | Real-time quality feedback stream |
| `/api/fixes/suggest` | POST | Get suggested fixes for issues |
| `/api/learning/patterns` | GET | Get learned issue patterns |

---

## Part 9: Verification Plan

### Test the Strategy

1. **Generate test code** through MarQed pipeline
2. **Compare metrics** against research baselines:
   - CodeRabbit: 1.7x issues → Target < 0.5x
   - Security: 51% vulnerable → Target < 10%
   - Incidents: 23.5% per PR → Target < 5%
3. **Run full security scan** with 21 detectors
4. **Validate quality gates** pass rate >= 90%
5. **Review architecture alignment** score >= 85%

### Commands to Verify

```bash
# Run quality gate validation
cd backend && python -m pytest tests/unit/quality/ -v

# Run security scanner
python -m pytest tests/unit/security_scanner/ -v

# Run anti-pattern detection
python -m pytest tests/unit/orchestration/test_antipattern_detector.py -v

# Run LLM council tests
python -m pytest tests/unit/services/test_llm_council_service.py -v
```

---

## Part 10: Implementation Schedule

### Week 185-186: Foundation + Guardrails Core
- [ ] AIComplaintDashboard service (baseline metrics, comparison logic)
- [ ] Database models for metrics storage
- [ ] API endpoints for dashboard
- [ ] **GuardrailsPipeline orchestrator** (central coordination)
- [ ] **CodeGenGuardrails** (AI code anti-pattern detection)
- [ ] **SecurityGuardrails** (real-time security blocking)

### Week 187-188: Context Preservation + Architecture Guardrails
- [ ] ContextPreservationService (ADR tracking)
- [ ] Integration with Felix architect agent
- [ ] Context injection into code generation
- [ ] **ArchitectureGuardrails** (layer/ADR compliance)
- [ ] **ContextGuardrails** (context requirements validation)

### Week 189-190: Real-time Feedback + Debt Guardrails
- [ ] RealTimeQualityFeedback service
- [ ] WebSocket integration
- [ ] Integration with quality gates
- [ ] **DebtGuardrails** (clean code enforcement)
- [ ] **LLMOutputGuardrails** (LLM response validation)

### Week 191: Automated Fixes + Guardrails Integration
- [ ] AutomatedFixGenerator service
- [ ] Fix confidence scoring
- [ ] Integration with security scanner
- [ ] **Guardrails ↔ Security Scanner integration**
- [ ] **Guardrails ↔ Quality Gate integration**

### Week 192: Learning & Full Pipeline
- [ ] LearningSystem service
- [ ] **Guardrails learning feedback loop**
- [ ] Full pipeline integration
- [ ] Documentation and testing
- [ ] **Unit tests for all guardrails (target: 95% coverage)**

---

## Conclusion

MarQed can build **demonstrably superior software** by:

1. **Preventing** complaints through pre-implementation quality gates
2. **Guarding** with 6-layer guardrails pipeline (CodeGen, Security, Architecture, Debt, Context, LLM)
3. **Detecting** issues with 21+ security detectors and 9 anti-patterns
4. **Correcting** problems via automated retry with feedback
5. **Measuring** success against documented industry baselines

The **Guardrails System** forms the core defense layer, building on existing infrastructure:
- `MarQedConstraintManager` - Per-agent permissions (✅ LIVE)
- `ConstraintManagerProtocol` - Abstract interface (✅ LIVE)
- `SafetyGuardrails` - Rollback triggers (✅ LIVE)
- `GuardrailsService` - Cross-context learning (📋 FASE 32)

The agent ecosystem (Felix, Vicky, Quinn, Marcus, Tessa, Diana) provides specialized expertise at each stage, while the LLM Council ensures consensus-driven decisions.

**Expected Outcome**: 3x improvement over industry AI code metrics.

---

*Generated: Week 158 (2026-01-18)*
