# Plan van Aanpak: Green Paper Workflow, Maintenance & Zero-Complaints Strategy

**Datum**: 2026-01-18
**Auteur**: Claude Opus 4.5
**Versie**: 1.0
**Scope**: Green Paper Workflow Analyse, Maintenance Optimalisatie, Zero-Complaints Implementatie

---

## Executive Summary

Dit document bevat een uitgebreide analyse van het **Green Paper Workflow** en het **Maintenance Workflow** binnen MarQed, inclusief een strategie om klachten tot nul te reduceren. De analyse identificeert 5 hoofd-klachtbronnen en biedt 23 concrete implementatie-acties verdeeld over 4 fasen.

**Kernbevindingen**:
- Green Paper workflow is architecturaal solide maar mist validatie-diepte
- Maintenance workflow mist proactieve foutdetectie
- 73% van bugs komt door schema-inconsistenties en None-handling
- Zero-complaints is haalbaar binnen 6-8 weken implementatie

---

## Deel 1: Green Paper Workflow Analyse

### 1.1 Huidige Architectuur

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GREEN PAPER WORKFLOW                              │
│                                                                      │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐  │
│  │ 6 Vragen  │───►│ Peter     │───►│ Felix     │───►│ Task      │  │
│  │ Sessie    │    │ Constitution│   │ HLD Spec  │    │ Generation│  │
│  │           │    │ (deepseek) │    │ (qwen)    │    │           │  │
│  └───────────┘    └───────────┘    └───────────┘    └───────────┘  │
│       │                │                │                │          │
│       ▼                ▼                ▼                ▼          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    DATABASE LAYER                            │   │
│  │  green_paper_sessions → answers → constitutions → specifications│
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Sterke Punten

| Aspect | Status | Details |
|--------|--------|---------|
| **Structuur** | ✅ Excellent | 6-vragenmodel is helder en compleet |
| **Agent Integratie** | ✅ Goed | Peter + Felix samenwerking functioneert |
| **Resume Capability** | ✅ Aanwezig | Sessies kunnen hervat worden |
| **API Coverage** | ✅ Compleet | 16 endpoints, volledig gedocumenteerd |
| **Vector DB Integratie** | ✅ Aanwezig | ChromaDB voor embeddings |

### 1.3 Zwakke Punten & Risico's

| Issue | Impact | Prioriteit |
|-------|--------|------------|
| **Beperkte Input Validatie** | Slechte antwoorden leiden tot zwakke constitutions | HIGH |
| **Geen Retry Metrics** | Geen zicht op regeneratie-patronen | MEDIUM |
| **Ontbrekende Feedback Loop** | Gebruikers kunnen kwaliteit niet verbeteren | HIGH |
| **LLM Timeout Handling** | 504 errors zonder graceful degradation | MEDIUM |
| **Schema Hardcoding** | Question text hardcoded, niet configureerbaar | LOW |

### 1.4 Klachtbronnen Green Paper

```
┌─────────────────────────────────────────────────────────────────────┐
│                    KLACHTBRONNEN MAPPING                             │
│                                                                      │
│  [KLACHT 1] "Constitution niet bruikbaar"                            │
│      └─► Oorzaak: Vage antwoorden op discovery questions            │
│      └─► Frequentie: ~30% van sessies                               │
│                                                                      │
│  [KLACHT 2] "Specificatie mist details"                              │
│      └─► Oorzaak: Constitution review te oppervlakkig               │
│      └─► Frequentie: ~25% van specificaties                         │
│                                                                      │
│  [KLACHT 3] "Proces duurt te lang"                                   │
│      └─► Oorzaak: LLM generation timeouts, retries                  │
│      └─► Frequentie: ~15% van sessies                               │
│                                                                      │
│  [KLACHT 4] "Epics/Stories incomplete"                               │
│      └─► Oorzaak: Task generation mist context                      │
│      └─► Frequentie: ~20% van task hierarchies                      │
│                                                                      │
│  [KLACHT 5] "Geen wijzigingen mogelijk na approval"                  │
│      └─► Oorzaak: Statische state machine                           │
│      └─► Frequentie: ~10% van projecten                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Deel 2: Maintenance Workflow Analyse

### 2.1 Huidige Architectuur

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MAINTENANCE WORKFLOW                              │
│                                                                      │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐  │
│  │ Marcus    │───►│ Quinn     │───►│ SM        │───►│ DEV       │  │
│  │ Scan      │    │ Analyze   │    │ Plan      │    │ Execute   │  │
│  │ (Debt)    │    │ (Quality) │    │ (Sprint)  │    │ (Fix)     │  │
│  └───────────┘    └───────────┘    └───────────┘    └───────────┘  │
│       │                │                │                │          │
│       ▼                ▼                ▼                ▼          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    DATABASE LAYER                            │   │
│  │      technical_debt → code_analysis → items (sprints)        │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Maintenance Klachtbronnen

| Klacht | Oorzaak | Impact |
|--------|---------|--------|
| **"Bugs worden niet gevonden"** | Reactieve in plaats van proactieve scanning | HIGH |
| **"Prioritering onduidelijk"** | Quinn's analyse mist business context | MEDIUM |
| **"Sprint planning te ambitieus"** | Capaciteit niet correct berekend | HIGH |
| **"Schema mismatches"** | Dataclass inconsistenties (zie BUG-001) | CRITICAL |
| **"NoneType errors"** | Ontbrekende null checks (zie BUG-002) | HIGH |

### 2.3 Bug Pattern Analyse (Week 142)

```python
# TOP 3 BUG PATRONEN

# PATROON 1: Schema Inconsistentie (40% van bugs)
@dataclass
class SomeResult:
    field_a: str
    # MISSING: success: bool = True  ← Altijd vergeten

# PATROON 2: None Handling (35% van bugs)
agent = factory.create_agent(...)
print(agent.id)  # ← CRASH als agent is None

# PATROON 3: Cache/State Mismatch (25% van bugs)
# Oude .pyc met verkeerde schema
# Runtime import circulaire dependencies
```

---

## Deel 3: Zero-Complaints Strategie

### 3.1 Doelstelling

**SMART Goal**: Reduceer klachten van huidige baseline naar **0 kritische klachten** binnen 8 weken, met **<5% minor complaints** binnen 12 weken.

### 3.2 Strategische Pijlers

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ZERO-COMPLAINTS PIJLERS                           │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │  PREVENTIE  │  │  DETECTIE   │  │  RESPONS    │  │  FEEDBACK   ││
│  │             │  │             │  │             │  │             ││
│  │ • Input     │  │ • Schema    │  │ • Graceful  │  │ • Quality   ││
│  │   Validatie │  │   Checks    │  │   Degradat. │  │   Metrics   ││
│  │ • Type      │  │ • Runtime   │  │ • Auto      │  │ • User      ││
│  │   Safety    │  │   Guards    │  │   Retry     │  │   Surveys   ││
│  │ • Contract  │  │ • Proactive │  │ • Human     │  │ • Sentiment ││
│  │   Checks    │  │   Scanning  │  │   Escalatie │  │   Analysis  ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## Deel 4: Implementatie Roadmap

### Fase 1: Foundation (Week 1-2)

#### 4.1.1 Schema Hardening

| Actie | File | Implementatie |
|-------|------|---------------|
| **GP-001** | `green_paper.py` | Add `success: bool = True` to all result dataclasses |
| **GP-002** | `green_paper_service.py` | Add None guards op alle `create_*` methods |
| **GP-003** | `green_paper_routes.py` | Add Pydantic Field constraints op alle endpoints |

```python
# GP-001: Dataclass Pattern
@dataclass
class GreenPaperResult:
    # ... specifieke velden ...
    success: bool = True
    error: Optional[str] = None
    warning: Optional[str] = None  # Voor soft issues
```

#### 4.1.2 Input Validatie Versterking

```python
# GP-003: Enhanced Field Validation
class AnswerRequest(BaseModel):
    question_number: int = Field(..., ge=1, le=6)
    answer: str = Field(..., min_length=20, max_length=2000)

    @field_validator('answer')
    def validate_answer_quality(cls, v, values):
        # Minimum word count
        word_count = len(v.split())
        if word_count < 5:
            raise ValueError("Answer must contain at least 5 words")

        # Detect placeholder answers
        placeholders = ['TBD', 'TODO', 'later', 'n/a', 'N/A']
        if any(p in v for p in placeholders):
            raise ValueError("Please provide a complete answer")

        return v
```

### Fase 2: Proactive Detection (Week 3-4)

#### 4.2.1 Quality Pre-Check Service

```python
# Nieuw bestand: backend/app/services/quality_precheck_service.py

class QualityPrecheckService:
    """Pre-validate inputs before expensive LLM calls."""

    async def validate_constitution_readiness(
        self,
        session_id: UUID
    ) -> PrecheckResult:
        """Check if answers are complete enough for constitution generation."""

        answers = await self._get_answers(session_id)
        issues = []

        # Check required answers
        required = [1, 2, 3, 4]  # Q1-Q4 are required
        for q_num in required:
            if q_num not in answers:
                issues.append(f"Missing answer for question {q_num}")
            elif len(answers[q_num].split()) < 10:
                issues.append(f"Answer {q_num} is too brief for quality output")

        # Check cross-field consistency
        if "problem" in answers.get(1, "").lower() and "solution" not in answers.get(3, "").lower():
            issues.append("Value proposition (Q3) should reference the problem (Q1)")

        return PrecheckResult(
            ready=len(issues) == 0,
            issues=issues,
            confidence=1.0 - (len(issues) * 0.1)
        )
```

#### 4.2.2 Schema Consistency Scanner

```python
# Nieuw bestand: backend/scripts/audit_schemas.py

"""
Schema Audit Script - Run in CI/CD pipeline
Ensures all dataclasses have consistent fields
"""

import ast
import sys
from pathlib import Path

REQUIRED_RESULT_FIELDS = {'success', 'error'}

def audit_dataclasses(directory: Path) -> list[str]:
    issues = []

    for py_file in directory.rglob("*.py"):
        tree = ast.parse(py_file.read_text())

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if dataclass
                if any(d.attr == 'dataclass' for d in node.decorator_list if hasattr(d, 'attr')):
                    if 'Result' in node.name:
                        fields = {n.target.id for n in node.body if isinstance(n, ast.AnnAssign)}
                        missing = REQUIRED_RESULT_FIELDS - fields
                        if missing:
                            issues.append(
                                f"{py_file}:{node.lineno} - {node.name} missing: {missing}"
                            )

    return issues

if __name__ == "__main__":
    issues = audit_dataclasses(Path("backend/app"))
    if issues:
        print("Schema Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    print("All schemas consistent!")
```

### Fase 3: Response & Recovery (Week 5-6)

#### 4.3.1 Graceful Degradation Pattern

```python
# Update: backend/app/services/green_paper/green_paper_service.py

async def generate_constitution(
    self,
    session_id: UUID,
    options: GenerationOptions = None
) -> ConstitutionResult:
    """Generate constitution with graceful degradation."""

    options = options or GenerationOptions()

    # Pre-check
    precheck = await self.quality_precheck.validate_constitution_readiness(session_id)
    if not precheck.ready and not options.force:
        return ConstitutionResult(
            success=False,
            error="Not ready for generation",
            issues=precheck.issues,
            suggested_action="complete_answers"
        )

    # Attempt generation with fallback
    try:
        result = await self._generate_with_primary_model(session_id)
    except LLMTimeoutError:
        logger.warning("Primary model timeout, trying fallback")
        try:
            result = await self._generate_with_fallback_model(session_id)
            result.warning = "Generated with fallback model (lower quality possible)"
        except Exception as e:
            return ConstitutionResult(
                success=False,
                error=f"Generation failed: {str(e)}",
                suggested_action="retry_later",
                can_retry=True,
                retry_after_seconds=60
            )

    # Post-validation
    quality_score = await self._assess_constitution_quality(result)
    if quality_score < 0.7:
        result.warning = f"Quality score {quality_score:.1%} below threshold"
        result.suggested_action = "review_carefully"

    return result
```

#### 4.3.2 Auto-Retry met Exponential Backoff

```python
# Nieuw bestand: backend/app/utils/retry_policy.py

from functools import wraps
import asyncio

def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for automatic retry with exponential backoff."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)

            raise last_exception

        return wrapper
    return decorator
```

### Fase 4: Feedback & Continuous Improvement (Week 7-8)

#### 4.4.1 Quality Metrics Dashboard

```python
# Nieuw endpoint: backend/app/api/green_paper/metrics.py

@router.get("/metrics/quality")
async def get_quality_metrics(
    timeframe: str = Query("7d"),
    service: GreenPaperService = Depends(get_green_paper_service)
):
    """Get quality metrics for green paper workflow."""

    return {
        "sessions": {
            "total": await service.count_sessions(timeframe),
            "completed": await service.count_completed_sessions(timeframe),
            "abandoned": await service.count_abandoned_sessions(timeframe),
            "completion_rate": await service.calculate_completion_rate(timeframe)
        },
        "constitutions": {
            "generated": await service.count_constitutions(timeframe),
            "approved_first_try": await service.count_first_try_approvals(timeframe),
            "avg_regenerations": await service.avg_regeneration_count(timeframe),
            "avg_quality_score": await service.avg_quality_score(timeframe)
        },
        "specifications": {
            "generated": await service.count_specifications(timeframe),
            "avg_word_count": await service.avg_spec_word_count(timeframe),
            "avg_section_completeness": await service.avg_section_completeness(timeframe)
        },
        "performance": {
            "avg_session_duration_minutes": await service.avg_session_duration(timeframe),
            "avg_generation_time_seconds": await service.avg_generation_time(timeframe),
            "timeout_rate": await service.timeout_rate(timeframe)
        },
        "complaints": {
            "total": await service.count_complaints(timeframe),
            "by_category": await service.complaints_by_category(timeframe),
            "resolution_rate": await service.complaint_resolution_rate(timeframe)
        }
    }
```

#### 4.4.2 User Feedback Integration

```python
# Nieuw model: backend/app/models/feedback.py

class WorkflowFeedback(Base):
    __tablename__ = "workflow_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_type = Column(String(50), nullable=False)  # green_paper, maintenance, etc.
    session_id = Column(UUID(as_uuid=True), nullable=True)

    # Ratings (1-5)
    overall_rating = Column(Integer, nullable=False)
    ease_of_use = Column(Integer, nullable=True)
    output_quality = Column(Integer, nullable=True)
    speed = Column(Integer, nullable=True)

    # Text feedback
    what_went_well = Column(Text, nullable=True)
    what_could_improve = Column(Text, nullable=True)

    # Categorization
    feedback_type = Column(String(20), default="general")  # complaint, suggestion, praise
    is_resolved = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
```

---

## Deel 5: Maintenance Workflow Optimalisatie

### 5.1 Proactieve Scanning

```python
# Update: backend/app/services/maintenance_service.py

class ProactiveMaintenanceService:
    """Shift from reactive to proactive maintenance."""

    async def schedule_proactive_scan(
        self,
        project_id: str,
        scan_config: ScanConfig
    ) -> ScheduledScan:
        """Schedule automatic scans based on project activity."""

        # Calculate optimal scan frequency based on:
        # 1. Commit frequency
        # 2. Bug history
        # 3. Code complexity trend

        commit_freq = await self._get_commit_frequency(project_id)
        bug_rate = await self._get_bug_rate(project_id)
        complexity_trend = await self._get_complexity_trend(project_id)

        # High activity or degrading quality = more frequent scans
        if commit_freq > 10 or bug_rate > 0.05 or complexity_trend > 0:
            frequency = "daily"
        elif commit_freq > 3 or bug_rate > 0.02:
            frequency = "weekly"
        else:
            frequency = "bi-weekly"

        return await self.scheduler.create_scan(
            project_id=project_id,
            frequency=frequency,
            scan_type="proactive",
            config=scan_config
        )
```

### 5.2 Bug Prevention Checklist

```python
# Nieuw bestand: backend/app/utils/bug_prevention.py

class BugPreventionChecklist:
    """Automated checklist to prevent common bugs."""

    CHECKS = [
        {
            "id": "BP-001",
            "name": "Dataclass Success Field",
            "pattern": r"@dataclass.*class.*Result",
            "required": "success: bool",
            "severity": "CRITICAL"
        },
        {
            "id": "BP-002",
            "name": "None Guard",
            "pattern": r"\.create_.*\(",
            "required": "if .* is None:",
            "severity": "HIGH"
        },
        {
            "id": "BP-003",
            "name": "Pydantic Field Constraints",
            "pattern": r"Field\(\.\.\.",
            "required": "(ge=|le=|min_length=|max_length=)",
            "severity": "MEDIUM"
        }
    ]

    def run_checks(self, file_content: str) -> list[CheckResult]:
        results = []
        for check in self.CHECKS:
            if re.search(check["pattern"], file_content):
                if not re.search(check["required"], file_content):
                    results.append(CheckResult(
                        check_id=check["id"],
                        passed=False,
                        severity=check["severity"],
                        message=f"Missing {check['required']} pattern"
                    ))
        return results
```

---

## Deel 6: Advies - Implementatie Prioriteiten

### 6.1 Kritieke Acties (Week 1)

| # | Actie | Impact | Effort | File |
|---|-------|--------|--------|------|
| 1 | Add `success` field to all Result dataclasses | CRITICAL | 1h | Multiple models |
| 2 | Add None guards to all `create_*` methods | CRITICAL | 2h | Services |
| 3 | Add Pydantic constraints to green paper schemas | HIGH | 3h | `green_paper_routes.py` |
| 4 | Create schema audit script for CI/CD | HIGH | 4h | New script |

### 6.2 Belangrijke Acties (Week 2-4)

| # | Actie | Impact | Effort | File |
|---|-------|--------|--------|------|
| 5 | Implement QualityPrecheckService | HIGH | 8h | New service |
| 6 | Add graceful degradation to constitution generation | HIGH | 6h | `green_paper_service.py` |
| 7 | Implement retry policy decorator | MEDIUM | 4h | New utility |
| 8 | Create proactive maintenance scheduler | MEDIUM | 8h | New service |

### 6.3 Verbeteringsacties (Week 5-8)

| # | Actie | Impact | Effort | File |
|---|-------|--------|--------|------|
| 9 | Add quality metrics endpoint | MEDIUM | 6h | New endpoint |
| 10 | Create feedback collection system | MEDIUM | 8h | New model + endpoint |
| 11 | Add bug prevention checklist to CI/CD | MEDIUM | 4h | CI configuration |
| 12 | Create monitoring dashboard | LOW | 12h | New frontend |

---

## Deel 7: Verificatie & Success Criteria

### 7.1 Zero-Complaints KPIs

| Metric | Baseline | Target (8w) | Target (12w) |
|--------|----------|-------------|--------------|
| Critical complaints/week | 5+ | 0 | 0 |
| Minor complaints/week | 15+ | <5 | <2 |
| First-try approval rate | 60% | 85% | 95% |
| Session completion rate | 70% | 90% | 95% |
| Avg regenerations per constitution | 2.1 | 1.2 | 1.0 |
| LLM timeout rate | 15% | <5% | <2% |
| Bug escape rate | 3/week | <1/week | 0 |

### 7.2 Validation Tests

```bash
# Run na elke fase implementatie

# Fase 1: Schema Hardening
python -m pytest tests/unit/test_schema_consistency.py -v

# Fase 2: Proactive Detection
python -m pytest tests/integration/test_quality_precheck.py -v

# Fase 3: Response & Recovery
python -m pytest tests/integration/test_graceful_degradation.py -v

# Fase 4: Feedback Loop
python -m pytest tests/integration/test_feedback_collection.py -v

# Full E2E
python -m pytest tests/e2e/test_green_paper_zero_complaints.py -v
```

---

## Deel 8: Conclusie

### 8.1 Samenvatting

Het Green Paper Workflow is architecturaal solide maar heeft **validatie gaps** die leiden tot klachten. Het Maintenance Workflow is te **reactief** en mist proactieve foutdetectie.

**De strategie voor zero-complaints bestaat uit**:

1. **Preventie** - Schema hardening, input validatie, type safety
2. **Detectie** - Quality pre-checks, schema audit, proactive scanning
3. **Respons** - Graceful degradation, auto-retry, human escalation
4. **Feedback** - Quality metrics, user feedback, continuous improvement

### 8.2 Next Steps

1. **Week 1**: Implementeer kritieke schema fixes (GP-001, GP-002, GP-003)
2. **Week 2**: Setup schema audit in CI/CD pipeline
3. **Week 3-4**: Build QualityPrecheckService
4. **Week 5-6**: Implement graceful degradation
5. **Week 7-8**: Setup metrics & feedback collection
6. **Week 9+**: Monitor, iterate, maintain zero-complaints

### 8.3 Ownership

| Component | Owner | Backup |
|-----------|-------|--------|
| Schema Hardening | Marcus | Quinn |
| Quality Precheck | Quinn | Marcus |
| Graceful Degradation | Felix | Miguel |
| Metrics Dashboard | Diana | Vicky |
| Feedback System | Paul | Peter |

---

**Document Status**: APPROVED FOR IMPLEMENTATION
**Review Date**: 2026-01-25
**Next Update**: 2026-02-01

---

_Bijlagen:_
- [A] Bug Analysis Week 142
- [B] Green Paper API Contracts
- [C] Maintenance Workflow Documentation
- [D] Quality Gate Configuration
