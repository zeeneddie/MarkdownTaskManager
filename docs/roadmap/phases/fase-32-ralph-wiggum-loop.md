# Fase 32: Ralph Wiggum Autonomous Agent Loop

**Status:** PLANNED
**Priority:** HIGH (ROI 8.5)
**Timeline:** Week 175-180
**Effort:** 160 uur (~5 weken)
**Dependencies:** Fase 23.5 (Confucius Orchestrator), Fase 23 (Context Engineering)

---

## Executive Summary

Implementatie van de Ralph Wiggum techniek voor autonomous coding, gecombineerd met Cole Medin's PRP (Product Requirements Prompt) framework en modern Agent Harness architecture. **Cruciaal inzicht: Ralph is geen generieke loop maar 4 fundamenteel verschillende operatiemodi** (BUGFIX, CHANGES, MIGRATION, OVERNIGHT), elk met eigen prompt strategie, human-in-the-loop checkpoints, risk profiles en guardrails.

**Het Probleem dat We Oplossen:**
> "Ralph assumes a good prompt exists" - Ralph Wiggum alleen werkt niet goed zonder goede prompt engineering
> "One loop fits all" - Een bug fixen is totaal anders dan een migratie uitvoeren

**De Oplossing:**
```
WorkflowTypeResolver: Input → Detect Type → Select Config (BUGFIX|CHANGES|MIGRATION|OVERNIGHT)
                                                    ↓
PRP Framework: Research → Requirements → Blueprint → Workflow-Specific PROMPT
                                                           ↓
                                                    Ralph Loop (geconfigureerd per type)
                                                           ↓
                                                    Agent Harness (HITL checkpoints per type)
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

## Workflow-Specifieke Ralph Configuraties

> **Kernprincipe:** Ralph Wiggum is GEEN generieke loop. Het is een framework dat zich fundamenteel anders gedraagt afhankelijk van het type werkzaamheid. Een bug fixen is detectivewerk; een migratie is een chirurgische operatie op een levend systeem. De prompt engineering, human-in-the-loop checkpoints, guardrails, en risk profiles zijn per workflow type compleet verschillend.

### Vier Workflow Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RALPH WIGGUM — 4 WORKFLOW MODI                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐  │
│  │   BUGFIX       │  │   CHANGES     │  │  MIGRATION    │  │  OVERNIGHT  │  │
│  │   "Detective"  │  │   "Vakman"    │  │  "Chirurg"    │  │  "Bouwer"   │  │
│  │                │  │               │  │               │  │             │  │
│  │  Scope: NARROW │  │  Scope: MEDIUM│  │  Scope: LARGE │  │ Scope: OPEN │  │
│  │  Duur:  Uren   │  │  Duur:  Dagen │  │  Duur:  Weken │  │ Duur:  8h+  │  │
│  │  Risk:  LOW    │  │  Risk:  MEDIUM│  │  Risk:  HIGH  │  │ Risk: MEDIUM│  │
│  │  HITL:  2x     │  │  HITL:  4x    │  │  HITL:  5x+   │  │ HITL:  3-4x │  │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘  └──────┬──────┘  │
│          │                  │                  │                  │          │
│          ▼                  ▼                  ▼                  ▼          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │              WorkflowTypeResolver → WorkflowConfig                      ││
│  │  Selecteert: prompt template, HITL checkpoints, guardrails,            ││
│  │              circuit breaker limits, rollback strategy, cost limits     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│          │                                                                   │
│          ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │              Ralph Loop (geconfigureerd per workflow type)               ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### WorkflowType Enum

```python
class WorkflowType(str, Enum):
    """De 4 fundamenteel verschillende Ralph Wiggum operatiemodi."""
    BUGFIX = "bugfix"           # Detective: narrow scope, chirurgisch
    CHANGES = "changes"         # Vakman: gecontroleerde uitbreiding
    MIGRATION = "migration"     # Chirurg: gefaseerde transformatie
    OVERNIGHT = "overnight"     # Bouwer: creatieve constructie
```

---

### Dual PM Approval Gate — Kernpatroon

> **Elke significante beslissing in Ralph doorloopt twee productmanagers: eerst de PM-Agent (AI), dan de PM-Human (mens).** Dit is een approval loop die herhaalt totdat er goedkeuring of definitieve afkeuring is. Het proces kan in wachtstand staan.

#### Waarom Dual PM?

| Perspectief | PM-Agent (AI) | PM-Human (Mens) |
|-------------|---------------|-----------------|
| **Sterkte** | Objectief, regelgebaseerd, altijd beschikbaar, consistent | Contextbewust, business intuïtie, stakeholder kennis, strategisch |
| **Beoordeelt** | Technische criteria, scope-fit, sprint-fit, kwaliteitsmetrics | Business prioriteit, timing, stakeholder impact, strategische fit |
| **Snelheid** | Milliseconden | Minuten tot uren |
| **Bias** | Geen emotionele bias, wel prompt bias | Mogelijk emotionele bias, maar creatieve inzichten |

#### Gate Flow — Approval Loop

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    DUAL PM APPROVAL GATE — FLOW                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  [Werk fase compleet]                                                         │
│         │                                                                     │
│         ▼                                                                     │
│  ┌──────────────┐                                                             │
│  │  PM-Agent    │ ← Beoordeelt automatisch op basis van criteria              │
│  │  Review      │                                                             │
│  └──────┬───────┘                                                             │
│         │                                                                     │
│    ┌────┼────┐                                                                │
│    │    │    │                                                                 │
│    ▼    ▼    ▼                                                                │
│   ✅   ⚠️    ❌                                                               │
│  PASS  WARN  FAIL                                                             │
│    │    │    │                                                                 │
│    │    │    └──→ Terug naar werk met PM-Agent feedback                        │
│    │    │         (telt als retry, max 3 voor escalatie)                       │
│    │    │                                                                      │
│    ▼    ▼                                                                     │
│  ┌──────────────┐                                                             │
│  │  PM-Human    │ ← Ontvangt PM-Agent assessment + werk resultaat             │
│  │  Review      │   (WARN items worden gemarkeerd)                            │
│  └──────┬───────┘                                                             │
│         │                                                                     │
│    ┌────┼────────────┐                                                        │
│    │    │            │                                                         │
│    ▼    ▼            ▼                                                         │
│   ✅   🔄           ❌                                                        │
│  GOED  AANPASSING   AFKEURING                                                 │
│KEURD   GEVRAAGD     │                                                         │
│    │    │            ├──→ DEFINITIEF: Stop proces, archiveer met reden         │
│    │    │            ├──→ PARKEER: Pauzeer, zet op backlog voor later          │
│    │    │            └──→ TERUGSTUUR: Terug naar eerdere fase                  │
│    │    │                                                                      │
│    │    └──→ Terug naar werk met PM-Human feedback                            │
│    │         (telt als retry, max 3 voor escalatie)                            │
│    │                                                                           │
│    ▼                                                                          │
│  [Volgende fase]                                                              │
│                                                                               │
│  ════════════════════════════════════════════════════════════════════════      │
│  TIMEOUT: Als PM-Human niet reageert binnen timeout window:                   │
│  - BUGFIX P3/P4: 4 uur → reminder → 8 uur → escalatie                       │
│  - CHANGES: 24 uur → reminder → 48 uur → escalatie                           │
│  - MIGRATION: 48 uur → reminder → 72 uur → escalatie                         │
│  - OVERNIGHT: N/A (morning review is asynchroon)                              │
│                                                                               │
│  ESCALATIE: Na 3 retries of timeout → Architect + Stakeholder review          │
│  ════════════════════════════════════════════════════════════════════════      │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### Waar worden de Gates geplaatst?

Elke workflow heeft twee vaste Dual PM Gates:

| Gate | Moment | Wat wordt beoordeeld |
|------|--------|---------------------|
| **Gate 1: Na Analyse/Design** | Na de analyse/design fase, VOOR implementatie begint | Is het probleem goed begrepen? Is de aanpak juist? Past het in de strategie? |
| **Gate 2: Na Oplossing/Design Presentatie** | Na de oplossing is ontworpen/gepresenteerd, VOOR uitrol/merge | Is de voorgestelde oplossing acceptabel? Voldoet het aan kwaliteitseisen? Gaan we door? |

**Uitzondering:** BUGFIX P1/P2 (production impact) gebruikt alleen Gate 2. Gate 1 wordt vervangen door een technische review (architect) — er is geen tijd voor dubbele PM review als production down is. De PM wordt wél geïnformeerd en doet achteraf een post-mortem review.

#### Approval States

```python
class ApprovalState(str, Enum):
    """Mogelijke states van een Dual PM Gate."""
    PENDING_PM_AGENT = "pending_pm_agent"       # Wacht op PM-Agent beoordeling
    PENDING_PM_HUMAN = "pending_pm_human"       # PM-Agent akkoord, wacht op PM-Human
    REVISION_REQUESTED = "revision_requested"   # Aanpassing gevraagd, terug naar werk
    APPROVED = "approved"                       # Beide PMs akkoord
    REJECTED_DEFINITIVE = "rejected_definitive" # Definitief afgekeurd, stop
    REJECTED_PARKED = "rejected_parked"         # Geparkeerd op backlog
    REJECTED_REROUTE = "rejected_reroute"       # Teruggestuurd naar eerdere fase
    ESCALATED = "escalated"                     # Naar architect/stakeholder
    TIMED_OUT = "timed_out"                     # PM-Human timeout, wacht op escalatie


class RejectionType(str, Enum):
    """Gedifferentieerde afkeuring — niet elke afkeuring is hetzelfde."""
    DEFINITIVE = "definitive"   # Stop: fundamenteel verkeerde richting, business case vervalt
    PARK = "park"               # Pauzeer: nu niet prioriteit, later wel. Naar backlog
    REROUTE = "reroute"         # Terugstuur: analyse onvolledig, meer onderzoek nodig
```

#### PM-Agent Beoordelingscriteria per Workflow

```python
PM_AGENT_CRITERIA = {
    WorkflowType.BUGFIX: {
        "gate_1": {  # Na root cause analyse (alleen P3/P4)
            "criteria": [
                "root_cause_identified",        # Is er een concrete root cause?
                "evidence_provided",            # Is er bewijs (logs, traces)?
                "not_duplicate",                # Is dit geen bekende/duplicate bug?
                "priority_justified",           # Klopt de prioriteit?
                "impact_assessment_complete",   # Impact op gebruikers beoordeeld?
            ],
            "auto_approve_threshold": 0.8,     # 80% criteria = auto-pass naar PM-Human
        },
        "gate_2": {  # Na fix design
            "criteria": [
                "fix_is_minimal",              # Minimale code wijzigingen?
                "regression_test_written",      # Regressietest aanwezig?
                "no_side_effects_detected",     # Geen bijeffecten in impact analyse?
                "all_tests_green",              # Alle bestaande tests groen?
                "fix_matches_root_cause",       # Fix adresseert root cause, niet symptoom?
            ],
            "auto_approve_threshold": 0.9,
        }
    },
    WorkflowType.CHANGES: {
        "gate_1": {  # Na design
            "criteria": [
                "sprint_fit",                  # Past in huidige sprint?
                "scope_defined",               # Scope duidelijk afgebakend?
                "dependencies_mapped",          # Dependencies geïdentificeerd?
                "effort_estimated",             # Effort ingeschat?
                "architecture_aligned",         # Past in bestaande architectuur?
                "no_blocking_dependencies",     # Geen blokkerende dependencies?
            ],
            "auto_approve_threshold": 0.8,
        },
        "gate_2": {  # Na oplossing design
            "criteria": [
                "convention_compliance",        # Volgt bestaande conventies?
                "test_plan_present",           # Test plan aanwezig?
                "api_backward_compatible",      # API backward compatible?
                "documentation_planned",        # Documentatie gepland?
                "effort_within_estimate",       # Effort binnen schatting?
                "no_scope_creep",              # Geen scope creep?
            ],
            "auto_approve_threshold": 0.85,
        }
    },
    WorkflowType.MIGRATION: {
        "gate_1": {  # Na migratieplan
            "criteria": [
                "plan_complete",               # Alle fasen gedefinieerd?
                "risk_matrix_present",          # Risk matrix aanwezig?
                "rollback_plan_per_phase",     # Rollback per fase?
                "data_mapping_complete",        # Data mapping compleet?
                "downtime_window_defined",      # Downtime window afgesproken?
                "business_impact_assessed",     # Business impact beoordeeld?
                "parallel_run_planned",         # Strangler Fig parallel run?
            ],
            "auto_approve_threshold": 0.9,     # Hoge drempel voor migratie
        },
        "gate_2": {  # Na fase-ontwerp / voor elke fase
            "criteria": [
                "phase_rollback_tested",       # Rollback voor deze fase getest?
                "data_parity_confirmed",        # Data consistentie bevestigd?
                "performance_acceptable",       # Performance niet verslechterd?
                "monitoring_active",            # Monitoring actief?
                "previous_phase_verified",      # Vorige fase volledig geverifieerd?
                "no_anomalies_detected",        # Geen anomalieën?
            ],
            "auto_approve_threshold": 0.95,    # Zeer hoge drempel
        }
    },
    WorkflowType.OVERNIGHT: {
        "gate_1": {  # PRP review
            "criteria": [
                "prp_quality_score",           # PRP kwaliteitsscore >7/10?
                "budget_defined",              # Budget limiet gedefinieerd?
                "scope_achievable_overnight",   # Scope haalbaar in 8h?
                "success_criteria_measurable",  # Success criteria meetbaar?
                "architecture_guidelines_set",  # Architectuurrichtlijnen meegegeven?
            ],
            "auto_approve_threshold": 0.8,
        },
        "gate_2": {  # Morning review
            "criteria": [
                "quality_score_acceptable",     # Kwaliteitsscore >7/10?
                "cost_within_budget",           # Kosten binnen budget?
                "no_architectural_drift",       # Geen architectural drift?
                "tests_present_and_green",      # Tests aanwezig en groen?
                "morning_report_generated",     # Morning report compleet?
            ],
            "auto_approve_threshold": 0.85,
        }
    }
}
```

#### DualPMApprovalService

```python
class DualPMApprovalService:
    """
    Beheert het Dual PM Approval Gate patroon.

    Flow: Werk → PM-Agent review → PM-Human review → Goedkeuring/Aanpassing/Afkeuring
    Herhaalt totdat er goedkeuring of definitieve afkeuring is.
    """

    MAX_RETRIES = 3  # Na 3 rondes aanpassingen → escalatie

    def __init__(
        self,
        pm_agent: PMAgentService,
        notification_service: NotificationService,
        state_manager: ApprovalStateManager,
        config: DualPMConfig
    ):
        self.pm_agent = pm_agent
        self.notifications = notification_service
        self.state_manager = state_manager
        self.config = config

    async def request_approval(
        self,
        gate: ApprovalGate,
        workflow_type: WorkflowType,
        artifact: WorkArtifact,
        context: ExecutionContext
    ) -> ApprovalResult:
        """
        Voer het Dual PM Gate patroon uit.

        Returns ApprovalResult met status en eventuele feedback.
        """
        retry_count = 0

        while retry_count < self.MAX_RETRIES:
            # Stap 1: PM-Agent beoordeling
            self.state_manager.set_state(gate, ApprovalState.PENDING_PM_AGENT)

            agent_result = await self.pm_agent.review(
                gate=gate,
                workflow_type=workflow_type,
                artifact=artifact,
                criteria=PM_AGENT_CRITERIA[workflow_type][gate.name],
                context=context
            )

            # PM-Agent FAIL → terug naar werk zonder PM-Human te storen
            if agent_result.verdict == PMVerdict.FAIL:
                self.state_manager.set_state(gate, ApprovalState.REVISION_REQUESTED)
                self.state_manager.log_review(gate, "pm_agent", agent_result)
                return ApprovalResult(
                    state=ApprovalState.REVISION_REQUESTED,
                    feedback=agent_result.feedback,
                    source="pm_agent",
                    retry_count=retry_count
                )

            # Stap 2: PM-Human beoordeling
            self.state_manager.set_state(gate, ApprovalState.PENDING_PM_HUMAN)

            # Stuur notificatie met PM-Agent assessment
            await self.notifications.notify_pm_human(
                gate=gate,
                artifact=artifact,
                pm_agent_assessment=agent_result,
                warnings=agent_result.warnings  # WARN items gemarkeerd
            )

            # Wacht op PM-Human response (met timeout)
            human_result = await self._wait_for_human(
                gate=gate,
                timeout=self.config.timeout_per_workflow[workflow_type]
            )

            # Timeout handling
            if human_result is None:
                await self._handle_timeout(gate, workflow_type, retry_count)
                return ApprovalResult(
                    state=ApprovalState.TIMED_OUT,
                    feedback="PM-Human timeout — wacht op escalatie",
                    source="system"
                )

            # Log de review
            self.state_manager.log_review(gate, "pm_human", human_result)

            # Verwerk PM-Human beslissing
            if human_result.verdict == PMVerdict.APPROVED:
                self.state_manager.set_state(gate, ApprovalState.APPROVED)
                return ApprovalResult(
                    state=ApprovalState.APPROVED,
                    feedback=human_result.feedback,
                    conditions=human_result.conditions,  # Evt. voorwaarden bij goedkeuring
                    source="pm_human"
                )

            if human_result.verdict == PMVerdict.REJECTED:
                rejection_type = human_result.rejection_type

                if rejection_type == RejectionType.DEFINITIVE:
                    self.state_manager.set_state(gate, ApprovalState.REJECTED_DEFINITIVE)
                    return ApprovalResult(
                        state=ApprovalState.REJECTED_DEFINITIVE,
                        feedback=human_result.feedback,
                        reason=human_result.rejection_reason,
                        source="pm_human"
                    )

                if rejection_type == RejectionType.PARK:
                    self.state_manager.set_state(gate, ApprovalState.REJECTED_PARKED)
                    return ApprovalResult(
                        state=ApprovalState.REJECTED_PARKED,
                        feedback=human_result.feedback,
                        backlog_priority=human_result.backlog_priority,
                        source="pm_human"
                    )

                if rejection_type == RejectionType.REROUTE:
                    self.state_manager.set_state(gate, ApprovalState.REJECTED_REROUTE)
                    return ApprovalResult(
                        state=ApprovalState.REJECTED_REROUTE,
                        feedback=human_result.feedback,
                        reroute_to_phase=human_result.reroute_target,
                        source="pm_human"
                    )

            # AANPASSING GEVRAAGD → retry loop
            if human_result.verdict == PMVerdict.REVISION_REQUESTED:
                self.state_manager.set_state(gate, ApprovalState.REVISION_REQUESTED)
                retry_count += 1

                # Geef feedback terug aan werk-fase
                return ApprovalResult(
                    state=ApprovalState.REVISION_REQUESTED,
                    feedback=human_result.feedback,
                    source="pm_human",
                    retry_count=retry_count
                )

        # Max retries bereikt → escalatie
        return await self._escalate(gate, workflow_type, context)

    async def _handle_timeout(
        self,
        gate: ApprovalGate,
        workflow_type: WorkflowType,
        retry_count: int
    ) -> None:
        """Handle PM-Human timeout met reminder en escalatie."""
        timeout = self.config.timeout_per_workflow[workflow_type]

        # Eerste timeout → reminder
        await self.notifications.send_reminder(gate, urgency="normal")

        # Tweede timeout → escalatie
        await self.notifications.escalate_to_stakeholder(
            gate=gate,
            reason=f"PM-Human niet gereageerd binnen {timeout}",
            context_summary=self.state_manager.get_gate_history(gate)
        )

    async def _escalate(
        self,
        gate: ApprovalGate,
        workflow_type: WorkflowType,
        context: ExecutionContext
    ) -> ApprovalResult:
        """Escaleer na max retries naar Architect + Stakeholder."""
        self.state_manager.set_state(gate, ApprovalState.ESCALATED)

        await self.notifications.escalate(
            gate=gate,
            reason=f"Max retries ({self.MAX_RETRIES}) bereikt zonder goedkeuring",
            review_history=self.state_manager.get_gate_history(gate),
            recipients=["architect", "stakeholder"]
        )

        return ApprovalResult(
            state=ApprovalState.ESCALATED,
            feedback=f"Geëscaleerd na {self.MAX_RETRIES} aanpassingsrondes",
            source="system"
        )
```

#### Approval State Persistence

De approval state wordt persistent opgeslagen in de Ralph state file, zodat bij context window overflow de volledige approval history behouden blijft.

```python
class ApprovalStateManager:
    """
    Persistent opslag van approval states en review history.
    Overleeft context window resets en agent herstart.
    """

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.history: List[ApprovalRecord] = []

    def log_review(
        self,
        gate: ApprovalGate,
        reviewer: str,  # "pm_agent" of "pm_human"
        result: ReviewResult
    ) -> None:
        """Log een review voor audit trail."""
        record = ApprovalRecord(
            gate=gate.name,
            reviewer=reviewer,
            verdict=result.verdict,
            feedback=result.feedback,
            timestamp=datetime.now(timezone.utc),
            criteria_scores=result.criteria_scores,
            retry_number=len([r for r in self.history
                            if r.gate == gate.name])
        )
        self.history.append(record)
        self._persist()

    def get_gate_history(self, gate: ApprovalGate) -> List[ApprovalRecord]:
        """Haal volledige review history op voor een gate."""
        return [r for r in self.history if r.gate == gate.name]

    def _persist(self) -> None:
        """Schrijf state naar state file (atomisch)."""
        # Append to .marqed/prp-ralph.state.md onder ## Approval History
        pass


@dataclass
class ApprovalRecord:
    """Enkelvoudig approval record voor audit trail."""
    gate: str
    reviewer: str
    verdict: str
    feedback: str
    timestamp: datetime
    criteria_scores: Dict[str, float]
    retry_number: int
```

#### Timeout Configuratie per Workflow

| Workflow | Eerste Timeout (reminder) | Tweede Timeout (escalatie) | Reden |
|----------|--------------------------|---------------------------|-------|
| **BUGFIX P1/P2** | N/A | N/A | Geen Dual PM Gate, alleen tech review |
| **BUGFIX P3/P4** | 4 uur | 8 uur | Bugs zijn urgent maar niet kritisch |
| **CHANGES** | 24 uur | 48 uur | Features kunnen planmatig wachten |
| **MIGRATION** | 48 uur | 72 uur | Migraties vereisen zorgvuldige beoordeling |
| **OVERNIGHT** | N/A (asynchroon) | 12 uur na ochtend | Morning review is inherent asynchroon |

---

### WF-1: BUGFIX — "De Detective"

**Karakter:** Analytisch, forensisch, narrow focus. De agent zoekt een specifieke oorzaak en lost die chirurgisch op zonder andere code te raken.

#### Input / Output

| Aspect | Specificatie |
|--------|-------------|
| **Input** | Bug report, stack trace, reproductiestappen, error logs, gerelateerde issues |
| **Output** | Geïsoleerde fix + regressietest + root cause documentatie |
| **Scope** | NARROW — één specifiek probleem, minimale code wijzigingen |
| **Typische duur** | 1-4 Ralph iteraties (uren) |
| **Agent Chain** | Betty (analyse) → Tessa (test) → Diana (documentatie) |

#### Prompt Engineering

Het BUGFIX prompt is **forensisch** van aard:

```markdown
## Ralph BUGFIX Mode — Prompt Template

### Opdracht
Je bent een bug detective. Je taak is:
1. REPRODUCEER het probleem (bewijs dat het bestaat)
2. ISOLEER de root cause (niet het symptoom!)
3. BEWIJS de oorzaak met evidence (logs, traces, tests)
4. FIX minimaal en chirurgisch
5. BEWIJS dat de fix werkt (regressietest)

### Regels
- NOOIT meer wijzigen dan strikt nodig voor de fix
- NOOIT refactoren tijdens een bugfix
- ALTIJD een falende test schrijven VOORDAT je fixt
- ALTIJD root cause documenteren, niet alleen het symptoom

### Input
- Bug report: {bug_report}
- Stack trace: {stack_trace}
- Reproductie: {reproduction_steps}

### Succes Criteria
- [ ] Bug is gereproduceerd met een falende test
- [ ] Root cause is geïdentificeerd en gedocumenteerd
- [ ] Fix wijzigt minimaal aantal bestanden
- [ ] Regressietest bewijst dat fix werkt
- [ ] Geen andere tests falen na de fix
```

#### Dual PM Gates & Human-in-the-Loop Checkpoints

**Let op:** BUGFIX maakt onderscheid naar severity:
- **P1/P2 (production impact):** GEEN Dual PM Gate 1. Alleen technische review (architect). PM wordt geïnformeerd, niet om goedkeuring gevraagd. Gate 2 (na fix) is wél Dual PM. Post-mortem review achteraf.
- **P3/P4 (geen urgentie):** Beide Dual PM Gates actief — voorkomt werk aan low-priority bugs.

```
BUGFIX HITL Flow — P3/P4 (met Dual PM Gates):

  Bug Report ──→ [Analyse] ──→ ★ GATE 1: Na Root Cause ──→ [Fix Design] ──→ ★ GATE 2: Na Fix ──→ Merge
                    │              │                                              │
                    │              │ PM-Agent: root cause check,                  │ PM-Agent: fix minimaal?,
                    │              │           duplicate check,                   │           regressie check,
                    │              │           impact assessment                  │           all tests green
                    │              │       ↓                                      │       ↓
                    │              │ PM-Human: "Is dit de juiste                  │ PM-Human: "Fix acceptabel?
                    │              │   oorzaak? Prioriteit klopt?"                │   Geen bijeffecten?"
                    │              │       ↓                                      │       ↓
                    │              │ AANPASSING → terug naar analyse              │ AANPASSING → terug naar fix
                    │              │ AFKEURING → stop (park/definitief)           │ AFKEURING → stop
                    │              │ GOEDKEURING → door naar fix                  │ GOEDKEURING → merge
                    │
                    └─ Agent zoekt vrij (GEEN gate tijdens zoeken)


BUGFIX HITL Flow — P1/P2 (URGENT, zonder Gate 1):

  Bug Report ──→ [Analyse] ──→ Architect Review ──→ [Fix] ──→ ★ GATE 2: Na Fix ──→ Merge
                    │              │ (technisch,                        │
                    │              │  geen PM gate)                     │ Dual PM Gate
                    │              │                                    │ (PM geïnformeerd bij Gate 1)
                    │              └─ PM geïnformeerd (geen goedkeuring │
                    │                 vereist, urgentie prevaleert)     └─ Post-mortem review achteraf
```

| # | Gate | Type | PM-Agent Criteria | PM-Human Vraag | Bij Reject | Timeout |
|---|------|------|-------------------|----------------|------------|---------|
| 1 | **Na root cause** (P3/P4) | Dual PM | root_cause, evidence, duplicate, priority, impact | "Juiste oorzaak? Prioriteit klopt?" | AANPASSING/PARK/DEFINITIEF | 4h / 8h |
| 1 | **Na root cause** (P1/P2) | Architect only | N/A (technische review) | PM geïnformeerd, niet gevraagd | Architect feedback | N/A |
| 2 | **Na fix, voor merge** | Dual PM | fix_minimal, regression_test, no_side_effects, tests_green | "Fix acceptabel? Geen bijeffecten?" | AANPASSING/DEFINITIEF | 4h / 8h |

#### Workflow-Specifieke Configuratie

```python
BUGFIX_CONFIG = WorkflowConfig(
    workflow_type=WorkflowType.BUGFIX,
    max_iterations=8,
    circuit_breaker=CircuitBreakerConfig(
        max_no_progress=3,        # Streng: 3 loops zonder voortgang = stop
        max_same_error=3,
        token_limit=40_000,       # Lager: bugs zijn compact
        cost_limit=5.00           # Streng budget
    ),
    dual_pm_gates=[
        DualPMGate(
            name="gate_1",
            trigger=HITLTrigger.AFTER_ANALYSIS,
            required_severity=["P3", "P4"],  # NIET bij P1/P2
            fallback_for_urgent=ApprovalFallback(
                reviewer="architect",
                pm_informed=True,
                post_mortem_required=True
            ),
            pm_agent_criteria="bugfix.gate_1",
            timeout_reminder=timedelta(hours=4),
            timeout_escalation=timedelta(hours=8),
            max_retries=3
        ),
        DualPMGate(
            name="gate_2",
            trigger=HITLTrigger.BEFORE_MERGE,
            required_severity=["P1", "P2", "P3", "P4"],  # Altijd
            pm_agent_criteria="bugfix.gate_2",
            timeout_reminder=timedelta(hours=4),
            timeout_escalation=timedelta(hours=8),
            max_retries=3
        )
    ],
    guardrails_focus=["regressie_preventie", "minimal_change"],
    rollback_strategy=RollbackStrategy.SOFT,  # Git revert is voldoende
    completion_criteria=CompletionCriteria(
        required=["failing_test_written", "root_cause_documented", "fix_applied",
                  "all_tests_green", "dual_pm_gate_2_approved"],
        quality_threshold=0.95
    )
)
```

---

### WF-2: CHANGES — "De Vakman"

**Karakter:** Methodisch, constructief, gecontroleerd. De agent bouwt iets nieuws of breidt bestaande functionaliteit uit, maar altijd binnen de kaders van de bestaande architectuur.

#### Input / Output

| Aspect | Specificatie |
|--------|-------------|
| **Input** | Change request, feature specificatie, enhancement ticket, design document |
| **Output** | Werkende feature + unit/integration tests + documentatie updates + API changes |
| **Scope** | MEDIUM — gecontroleerde uitbreiding binnen bestaand systeem |
| **Typische duur** | 5-20 Ralph iteraties (dagen) |
| **Agent Chain** | Peter (architect) → Felix (implement) → Tessa (test) → Diana (docs) |

#### Prompt Engineering

Het CHANGES prompt is **constructief/methodisch**:

```markdown
## Ralph CHANGES Mode — Prompt Template

### Opdracht
Je bent een vakman die bestaande software uitbreidt. Je taak is:
1. BEGRIJP de bestaande architectuur en conventies
2. ONTWERP de uitbreiding passend bij het bestaande systeem
3. BOUW incrementeel — kleine, verifieerbare stappen
4. VALIDEER elke stap (types, lint, tests)
5. INTEGREER met bestaande code (geen eilandjes)

### Regels
- VOLG bestaande conventies en patronen
- BOUW incrementeel — nooit meer dan 1 component per iteratie
- VRAAG goedkeuring bij architecturale keuzes
- DOCUMENTEER nieuwe APIs en interfaces
- GEEN scope creep — alleen wat in de specificatie staat

### Input
- Feature spec: {feature_specification}
- Bestaande architectuur: {architecture_context}
- Conventies: {conventions}
- Affected modules: {impact_zone}

### Succes Criteria
- [ ] Feature werkt volgens specificatie
- [ ] Past in bestaande architectuur
- [ ] Alle nieuwe code heeft tests (>90% coverage)
- [ ] Documentatie is bijgewerkt
- [ ] Geen bestaande tests breken
- [ ] Code review checklist voldaan
```

#### Dual PM Gates & Human-in-the-Loop Checkpoints

```
CHANGES HITL Flow (met Dual PM Gates):

  Feature Spec ──→ [Design] ──→ ★ GATE 1: Design Approval ──→ [Bouw iteraties] ──→ ★ GATE 2: Solution Review ──→ Merge
                                     │                              │                       │
                                     │ PM-Agent: sprint-fit,        │                       │ PM-Agent: conventie check,
                                     │   scope, dependencies,       │                       │   test plan, API compat,
                                     │   effort, architectuur       │                       │   scope creep, effort
                                     │       ↓                      │                       │       ↓
                                     │ PM-Human: "Past in sprint?   │                       │ PM-Human: "Oplossing
                                     │   Aanpak strategisch goed?"  │                       │   acceptabel? Kwaliteit OK?"
                                     │       ↓                      │                       │       ↓
                                     │ AANPASSING → redesign        │                       │ AANPASSING → terug naar bouw
                                     │ PARK → backlog               │                       │ DEFINITIEF → stop
                                     │ GOEDKEURING → bouw           │                       │ GOEDKEURING → merge
                                     │                              │
                                     │                    ★ Scope Check (event-driven)
                                     │                         │ (alleen als scope groeit)
                                     │                         │ PM-Agent + PM-Human:
                                     │                         │ "Scope groeit — acceptabel?"
                                     │
                                     │                    ★ Architecture Decision (event-driven)
                                     │                         │ (alleen bij patroon-doorbreking)
                                     │                         │ PM-Agent + PM-Human:
                                     │                         │ "Patroon doorbreken OK?"
```

| # | Gate | Type | PM-Agent Criteria | PM-Human Vraag | Bij Reject | Timeout |
|---|------|------|-------------------|----------------|------------|---------|
| 1 | **Na design** | Dual PM | sprint_fit, scope, dependencies, effort, architecture | "Past in sprint? Aanpak strategisch goed?" | AANPASSING/PARK/DEFINITIEF | 24h / 48h |
| 2 | **Na oplossing, voor merge** | Dual PM | conventions, test_plan, api_compat, scope_creep, effort | "Oplossing acceptabel? Kwaliteit OK?" | AANPASSING/DEFINITIEF | 24h / 48h |
| — | **Bij scope-uitbreiding** | Dual PM (event) | scope_delta, effort_impact | "Scope groeit — acceptabel of apart ticket?" | Scope beperken | 24h / 48h |
| — | **Bij architecturale keuze** | Dual PM (event) | pattern_break_impact, alternative_available | "Patroon doorbreken OK?" | Alternatief zoeken | 24h / 48h |

#### Workflow-Specifieke Configuratie

```python
CHANGES_CONFIG = WorkflowConfig(
    workflow_type=WorkflowType.CHANGES,
    max_iterations=25,
    circuit_breaker=CircuitBreakerConfig(
        max_no_progress=5,        # Normaal: meer ruimte voor complexe features
        max_same_error=5,
        token_limit=80_000,
        cost_limit=15.00
    ),
    dual_pm_gates=[
        DualPMGate(
            name="gate_1",
            trigger=HITLTrigger.BEFORE_IMPLEMENTATION,
            pm_agent_criteria="changes.gate_1",
            timeout_reminder=timedelta(hours=24),
            timeout_escalation=timedelta(hours=48),
            max_retries=3
        ),
        DualPMGate(
            name="gate_2",
            trigger=HITLTrigger.BEFORE_MERGE,
            pm_agent_criteria="changes.gate_2",
            timeout_reminder=timedelta(hours=24),
            timeout_escalation=timedelta(hours=48),
            max_retries=3
        )
    ],
    event_driven_gates=[
        DualPMGate(
            name="scope_check",
            trigger=HITLTrigger.ON_SCOPE_EXPANSION,
            pm_agent_criteria="changes.scope_check",
            timeout_reminder=timedelta(hours=24),
            timeout_escalation=timedelta(hours=48),
            max_retries=2
        ),
        DualPMGate(
            name="architecture_decision",
            trigger=HITLTrigger.ON_PATTERN_BREAK,
            pm_agent_criteria="changes.architecture_check",
            timeout_reminder=timedelta(hours=24),
            timeout_escalation=timedelta(hours=48),
            max_retries=2
        )
    ],
    guardrails_focus=["conventie_naleving", "scope_bewaking", "architectuur_consistentie"],
    rollback_strategy=RollbackStrategy.SOFT,
    completion_criteria=CompletionCriteria(
        required=["feature_works", "tests_written", "docs_updated",
                  "dual_pm_gate_1_approved", "dual_pm_gate_2_approved"],
        quality_threshold=0.90
    )
)
```

---

### WF-3: MIGRATION — "De Chirurg-Ingenieur"

**Karakter:** Voorzichtig, gefaseerd, data-eerst. Dit is de meest risicovolle workflow. Dataverlies is het grootste risico en is ONHERSTELBAAR. De agent werkt in strikt gescheiden fasen met menselijke goedkeuring bij elke overgang.

#### Input / Output

| Aspect | Specificatie |
|--------|-------------|
| **Input** | Brown Paper analyse, source+target architectuur, migratieplan, Strangler Fig strategie, data mapping |
| **Output** | Gemigreerd systeem + data migratie scripts + rollback plan + verificatierapport + cutover plan |
| **Scope** | LARGE — gefaseerde transformatie, meerdere systemen, weken werk |
| **Typische duur** | 50-200 Ralph iteraties (weken, meerdere sessies) |
| **Agent Chain** | Miguel (migratie) → Peter (architect) → Felix (implement) → Quinn (kwaliteit) → Eliza (analyse) → Diana (docs) |

#### Prompt Engineering

Het MIGRATION prompt is **voorzichtig/gefaseerd**:

```markdown
## Ralph MIGRATION Mode — Prompt Template

### Opdracht
Je bent een migratie-chirurg. Je opereert op een LEVEND systeem. Je taak is:
1. ANALYSEER de huidige staat grondig (Brown Paper)
2. PLAN de migratie in discrete, omkeerbare fasen
3. BOUW elke fase met VOLLEDIGE rollback mogelijkheid
4. VERIFIEER elke fase VOORDAT je doorgaat naar de volgende
5. MIGREER data ALLEEN na expliciete menselijke goedkeuring
6. DOCUMENTEER elke stap voor audit trail

### Regels — STRIKT
- NOOIT data wijzigen zonder expliciete menselijke goedkeuring
- NOOIT twee migratiefasen tegelijk uitvoeren
- ALTIJD rollback script schrijven VOORDAT je migreert
- ALTIJD oude en nieuwe systeem parallel draaien (Strangler Fig)
- BIJ ELKE ANOMALIE: stop direct, rapporteer, wacht op instructie
- DATA IS ONVERVANGBAAR — bij twijfel: STOP

### Input
- Brown Paper analyse: {brown_paper_analysis}
- Source architectuur: {source_architecture}
- Target architectuur: {target_architecture}
- Data mapping: {data_mapping}
- Migratie strategie: {migration_strategy}

### Migratie Fasen (Strangler Fig)
1. Facade bouwen (geen data changes)
2. Nieuwe implementatie achter facade
3. Schaduw-draaien (dual-write, compare)
4. Data migratie (★ MENSELIJKE GOEDKEURING VEREIST)
5. Verkeer omleiden (gradual rollout)
6. Oude systeem uitfaseren
7. Cleanup en documentatie

### Succes Criteria per Fase
- [ ] Fase is volledig omkeerbaar (rollback getest)
- [ ] Geen data inconsistentie gedetecteerd
- [ ] Oude en nieuwe systeem geven identieke resultaten
- [ ] Performance is niet verslechterd
- [ ] Alle monitoring en alerting is actief
- [ ] Menselijke goedkeuring ontvangen voor volgende fase
```

#### Dual PM Gates & Human-in-the-Loop Checkpoints

**Migratie heeft de meest intensieve Dual PM Gate structuur.** Naast de twee vaste gates (na analyse, na oplossing design) zijn er ook herhaalde fase-gates en kritische data gates.

```
MIGRATION HITL Flow — MEEST INTENSIEF (met Dual PM Gates):

  Brown Paper ──→ [Analyse] ──→ ★ GATE 1: Migratieplan Approval ──→ [Fase 1] ──→ ★ FASE-GATE ──→ ...
  Analyse                            │                                               │
                                     │ PM-Agent: plan compleet?,                     │ PM-Agent: rollback OK?,
                                     │   risk matrix, rollback plan,                 │   data parity, performance,
                                     │   data mapping, downtime window,              │   monitoring, vorige fase OK
                                     │   business impact, parallel run               │       ↓
                                     │       ↓                                       │ PM-Human: "Fase correct
                                     │ PM-Human: "Plan compleet?                     │   afgerond? Door naar
                                     │   Business timing OK?"                        │   volgende?"
                                     │       ↓
                                     │ AANPASSING → plan herschrijven
                                     │ DEFINITIEF → stop migratie
                                     │ GOEDKEURING → start fase 1

  ... ──→ [Data Migratie Design] ──→ ★ GATE 2: Oplossing Review ──→ ★ DATA-GATE (KRITISCH) ──→ ...
                                          │                               │
                                          │ Dual PM Gate                  │ Dual PM Gate
                                          │ (standaard flow)              │ CRITICAL: kan NIET auto-approved
                                          │                               │ PM-Agent check PLUS
                                          │                               │ PM-Human MOET expliciet tekenen

  ... ──→ [Cutover voorbereiding] ──→ ★ CUTOVER-GATE ──→ [Cutover] ──→ [Cleanup]
                                          │
                                          │ Dual PM Gate (CRITICAL)
                                          │ Go/No-Go beslissing
                                          │ Beide PMs MOETEN tekenen

  ★ ANOMALIE-GATE (op elk moment):
    │ Bij anomalie → onmiddellijke stop
    │ PM-Agent detecteert + PM-Human wordt direct genotificeerd
    │ Geen retry: STOP tot expliciete herstart
```

| # | Gate | Type | PM-Agent Criteria | PM-Human Vraag | Bij Reject | Timeout |
|---|------|------|-------------------|----------------|------------|---------|
| 1 | **Na migratieplan (analyse)** | Dual PM | plan_complete, risk_matrix, rollback_plan, data_mapping, downtime, business_impact, parallel_run | "Plan compleet? Business timing OK?" | AANPASSING/PARK/DEFINITIEF | 48h / 72h |
| — | **Na elke fase** | Dual PM | phase_rollback, data_parity, performance, monitoring, previous_phase | "Fase correct? Door naar volgende?" | Herhaal fase / rollback | 48h / 72h |
| 2 | **Na oplossing design** | Dual PM | Standaard gate_2 criteria | "Data migratie aanpak acceptabel?" | AANPASSING/DEFINITIEF | 48h / 72h |
| — | **Voor data migratie** | Dual PM **CRITICAL** | Alle criteria + data_backup_verified | **"DATA MIGRATIE — onomkeerbaar. Tekenen?"** | Stop, geen data wijzigingen | 48h / 72h |
| — | **Voor cutover** | Dual PM **CRITICAL** | Alle criteria + parity_confirmed | "Go/No-Go cutover?" | Blijf op oud systeem | 48h / 72h |
| — | **Bij anomalie** | Dual PM **IMMEDIATE** | Auto-detect | "ANOMALIE — stop en evalueer" | Volledige stop | Onmiddellijk |

#### Workflow-Specifieke Configuratie

```python
MIGRATION_CONFIG = WorkflowConfig(
    workflow_type=WorkflowType.MIGRATION,
    max_iterations=200,  # Migraties duren lang
    circuit_breaker=CircuitBreakerConfig(
        max_no_progress=2,        # ZEER STRENG: 2 loops = stop
        max_same_error=2,         # Bij migratie geen ruimte voor herhaling
        token_limit=80_000,
        cost_limit=75.00          # Hoger budget, maar bewaakt
    ),
    dual_pm_gates=[
        DualPMGate(
            name="gate_1",
            trigger=HITLTrigger.BEFORE_IMPLEMENTATION,
            pm_agent_criteria="migration.gate_1",
            timeout_reminder=timedelta(hours=48),
            timeout_escalation=timedelta(hours=72),
            max_retries=3
        ),
        DualPMGate(
            name="gate_2",
            trigger=HITLTrigger.AFTER_SOLUTION_DESIGN,
            pm_agent_criteria="migration.gate_2",
            timeout_reminder=timedelta(hours=48),
            timeout_escalation=timedelta(hours=72),
            max_retries=3
        )
    ],
    phase_gates=[
        DualPMGate(
            name="phase_gate",
            trigger=HITLTrigger.AFTER_EACH_PHASE,
            pm_agent_criteria="migration.phase_gate",
            timeout_reminder=timedelta(hours=48),
            timeout_escalation=timedelta(hours=72),
            max_retries=2
        )
    ],
    critical_gates=[
        DualPMGate(
            name="data_migration_gate",
            trigger=HITLTrigger.BEFORE_DATA_MIGRATION,
            critical=True,          # Kan NIET auto-approved worden
            pm_agent_auto_approve=False,  # PM-Agent mag NIET auto-approven
            pm_agent_criteria="migration.data_gate",
            timeout_reminder=timedelta(hours=48),
            timeout_escalation=timedelta(hours=72),
            max_retries=2           # Minder retries: bij 2x afwijzing → escalatie
        ),
        DualPMGate(
            name="cutover_gate",
            trigger=HITLTrigger.BEFORE_CUTOVER,
            critical=True,
            pm_agent_auto_approve=False,
            pm_agent_criteria="migration.cutover_gate",
            timeout_reminder=timedelta(hours=48),
            timeout_escalation=timedelta(hours=72),
            max_retries=2
        )
    ],
    event_driven_gates=[
        DualPMGate(
            name="anomaly_stop",
            trigger=HITLTrigger.ON_ANOMALY,
            critical=True,
            immediate=True,         # Geen wachttijd, directe stop
            max_retries=0           # Geen retry: stop tot herstart
        )
    ],
    guardrails_focus=["data_integriteit", "rollback_beschikbaarheid", "parallel_verificatie"],
    rollback_strategy=RollbackStrategy.PHASED,  # Per-fase rollback plan
    completion_criteria=CompletionCriteria(
        required=[
            "all_phases_complete", "data_verified", "no_anomalies",
            "old_new_parity_confirmed", "cutover_approved", "rollback_tested",
            "dual_pm_gate_1_approved", "dual_pm_gate_2_approved",
            "all_phase_gates_approved", "data_migration_gate_approved",
            "cutover_gate_approved"
        ],
        quality_threshold=0.99  # Bijna perfect vereist
    )
)
```

---

### WF-4: OVERNIGHT — "De Bouwer"

**Karakter:** Creatief, autonoom, PRP-gestuurd. Dit is de "klassieke" Ralph Wiggum use case: de agent bouwt overnight een complete feature op basis van een PRP document, met minimale menselijke interactie maar strikte guardrails en cost controls.

#### Input / Output

| Aspect | Specificatie |
|--------|-------------|
| **Input** | PRP document (Product Requirements Prompt), feature specificatie, greenfield requirements |
| **Output** | Complete nieuwe feature/module + tests + docs + integratie + morning report |
| **Scope** | OPEN — creatieve constructie, scope wordt bepaald door PRP |
| **Typische duur** | 8+ uur onbeheerd (20-50 iteraties overnight) |
| **Agent Chain** | Volledig Ralph loop: InitializationAgent → PRP → RalphLoopService → alle sub-agents |

#### Prompt Engineering

Het OVERNIGHT prompt is **creatief/autonoom**:

```markdown
## Ralph OVERNIGHT Mode — Prompt Template

### Opdracht
Je werkt onbeheerd gedurende de nacht. Je bouwt een complete feature op basis van het PRP document.
1. INITIALISEER: Verzamel alle context (architectuur, conventies, dependencies)
2. PLAN: Splits het PRP in atomaire, verifieerbare taken
3. BOUW: Implementeer taak voor taak, valideer na elke stap
4. RAPPORTEER: Genereer een morning report voor menselijke review
5. STOP bij problemen: liever halverwege stoppen dan foute code opleveren

### Regels
- VOLG het PRP document als blauwdruk
- VALIDEER na ELKE taak (types, lint, tests)
- COMMIT na elke succesvolle taak (checkpoints)
- BIJ TWIJFEL: noteer in morning report, ga door met volgende taak
- COST BEWAKING: stop bij kostenlimiet
- KWALITEIT BOVEN SNELHEID: liever 60% goed dan 100% slordig

### Input
- PRP document: {prp_document}
- Project context: {initialization_context}
- Guardrails: {accumulated_guardrails}

### Morning Report Template
Bij voltooiing genereer:
- Taken voltooid vs gepland
- Kwaliteitsmetrics (test coverage, lint score)
- Kosten overzicht
- Openstaande vragen/beslissingen voor mens
- Aanbevelingen voor vervolg

### Succes Criteria
- [ ] Alle PRP taken voltooid OF duidelijk gedocumenteerd waarom niet
- [ ] Test coverage >80% voor nieuwe code
- [ ] Geen lint errors
- [ ] Types checken
- [ ] Morning report gegenereerd
- [ ] Kosten binnen budget
```

#### Dual PM Gates & Human-in-the-Loop Checkpoints

**Overnight heeft een asymmetrisch Dual PM Gate patroon:** Gate 1 (avonds, synchroon) en Gate 2 (morning review, asynchroon). Omdat de agent 's nachts onbeheerd werkt, is Gate 1 extra belangrijk — er is geen mogelijkheid tot tussentijds ingrijpen.

```
OVERNIGHT HITL Flow (met Dual PM Gates):

  PRP Document ──→ ★ GATE 1: PRP Approval (avonds, VOOR start)
                       │
                       │ PM-Agent: PRP kwaliteit, budget,
                       │   haalbaarheid, scope, architectuur
                       │       ↓
                       │ PM-Human: "PRP akkoord? Budget OK?
                       │   Scope haalbaar overnight?"
                       │       ↓
                       │ AANPASSING → PRP herschrijven (retry loop)
                       │ PARK → niet vanavond, morgen opnieuw bekijken
                       │ GOEDKEURING → start overnight
                       │
                       ▼
                  [Overnight bouwen...]
                       │
                       ├──→ ★ Cost Alert (automatisch, pauze bij limiet)
                       ├──→ ★ Circuit Breaker (automatisch, stop bij stuck)
                       │
                       ▼
                  ★ GATE 2: Morning Review ('s ochtends, asynchroon)
                       │
                       │ PM-Agent: quality score, cost vs budget,
                       │   architectural drift, tests, morning report
                       │       ↓
                       │ PM-Human: "Wat is er gebouwd?
                       │   Kwaliteit OK? Doorgaan of rollback?"
                       │       ↓
                       │ GOEDKEURING → werk accepteren, merge
                       │ AANPASSING → specifieke delen herdoen
                       │ DEFINITIEF → rollback naar checkpoint
```

| # | Gate | Type | PM-Agent Criteria | PM-Human Vraag | Bij Reject | Timeout |
|---|------|------|-------------------|----------------|------------|---------|
| 1 | **PRP Approval (avonds)** | Dual PM | prp_quality, budget, scope_overnight, criteria_measurable, arch_guidelines | "PRP + budget OK? Haalbaar overnight?" | AANPASSING/PARK | N/A (synchroon) |
| — | **Cost threshold** | Automatisch | cost_limit_reached | Melding: "Budget bereikt, gepauzeerd" | Wacht op ochtend | N/A |
| — | **Circuit breaker** | Automatisch | stuck_detected | Melding: "Agent vast, gestopt" | Wacht op ochtend | N/A |
| 2 | **Morning Review** | Dual PM | quality_score, cost_budget, arch_drift, tests, report | "Kwaliteit OK? Doorgaan of rollback?" | AANPASSING/DEFINITIEF | 12h na ochtend |

#### Workflow-Specifieke Configuratie

```python
OVERNIGHT_CONFIG = WorkflowConfig(
    workflow_type=WorkflowType.OVERNIGHT,
    max_iterations=50,
    circuit_breaker=CircuitBreakerConfig(
        max_no_progress=10,       # Soepel: meer ruimte voor creatief werk
        max_same_error=5,
        token_limit=80_000,
        cost_limit=25.00
    ),
    dual_pm_gates=[
        DualPMGate(
            name="gate_1",
            trigger=HITLTrigger.BEFORE_START,
            pm_agent_criteria="overnight.gate_1",
            synchronous=True,       # Avonds, mens is aanwezig
            timeout_reminder=None,  # Synchroon, geen timeout
            timeout_escalation=None,
            max_retries=3
        ),
        DualPMGate(
            name="gate_2",
            trigger=HITLTrigger.ON_COMPLETION_OR_MORNING,
            pm_agent_criteria="overnight.gate_2",
            synchronous=False,      # Asynchroon, morning review
            timeout_reminder=timedelta(hours=12),  # 12h na ochtend
            timeout_escalation=timedelta(hours=24),
            max_retries=2
        )
    ],
    automatic_gates=[
        AutomaticGate(
            name="cost_alert",
            trigger=HITLTrigger.ON_COST_THRESHOLD,
            action=GateAction.PAUSE,
            notification=True
        ),
        AutomaticGate(
            name="circuit_breaker",
            trigger=HITLTrigger.ON_CIRCUIT_BREAK,
            action=GateAction.STOP,
            notification=True
        )
    ],
    guardrails_focus=["architectuur_consistentie", "kwaliteit_boven_snelheid", "cost_bewaking"],
    rollback_strategy=RollbackStrategy.CHECKPOINT,  # Rollback naar laatste goede checkpoint
    completion_criteria=CompletionCriteria(
        required=["prp_tasks_addressed", "tests_written", "morning_report_generated",
                  "dual_pm_gate_1_approved", "dual_pm_gate_2_approved"],
        quality_threshold=0.85
    )
)
```

---

### Vergelijkingstabel: Alle Workflows

| Dimensie | BUGFIX | CHANGES | MIGRATION | OVERNIGHT |
|----------|--------|---------|-----------|-----------|
| **Metafoor** | Detective | Vakman | Chirurg-Ingenieur | Bouwer |
| **mq Script** | `marqed-bugfix.sh` | `marqed-changes.sh` | `marqed-migration.sh` | `marqed-overnight.sh` (nieuw) |
| **Platform Type** | BUG | NEW_FEATURE / ENHANCEMENT | BROWN_PAPER + MIGRATION | PRP-based |
| **Agent Chain** | Betty→Tessa→Diana | Peter→Felix→Tessa→Diana | Miguel→Peter→Felix→Quinn→Eliza→Diana | Alle agents via PRP |
| **Scope** | Narrow | Medium | Large | Open |
| **Typische duur** | Uren | Dagen | Weken | 8+ uur |
| **Ralph iteraties** | 1-4 | 5-20 | 50-200 | 20-50 |
| | | | | |
| **Dual PM Gates** | | | | |
| Gate 1 (na analyse) | P3/P4 only (P1/P2: architect) | Altijd | Altijd | Altijd (synchroon, avonds) |
| Gate 2 (na oplossing) | Altijd | Altijd | Altijd + fase-gates + data-gate | Asynchroon (morning review) |
| Extra gates | — | Scope check, Arch decision | Fase-gates, Data-gate, Cutover-gate, Anomalie | Cost alert, Circuit breaker |
| Critical gates | — | — | Data migratie, Cutover | — |
| PM-Agent auto-approve | Ja (threshold 0.8/0.9) | Ja (threshold 0.8/0.85) | Gate 1/2 ja; Data+Cutover NEE | Ja (threshold 0.8/0.85) |
| Timeout (reminder) | 4h | 24h | 48h | N/A / 12h |
| Timeout (escalatie) | 8h | 48h | 72h | N/A / 24h |
| Max retries per gate | 3 | 3 | 3 (gate 1/2), 2 (critical) | 3 (gate 1), 2 (gate 2) |
| | | | | |
| **Overige dimensies** | | | | |
| Kritiekste gate | Gate 2 (na fix) | Gate 1 (design) | Data migratie gate | Gate 2 (morning review) |
| Maximaal risico | Regressie | Scope creep | **Dataverlies** | Verkeerde richting |
| CircuitBreaker | Streng (3 loops) | Normaal (5 loops) | Zeer streng (2 loops) | Soepel (10 loops) |
| Cost limit | $5 | $15 | $75 | $25 |
| Token limit | 40K | 80K | 80K | 80K |
| Rollback strategie | Git revert | Git revert + cleanup | Per-fase rollback plan | Checkpoint rollback |
| Guardrails focus | Regressie preventie | Conventie naleving | Data integriteit | Architectuur consistentie |
| Quality threshold | 0.95 | 0.90 | 0.99 | 0.85 |
| Prompt karakter | Forensisch | Methodisch | Voorzichtig/gefaseerd | Creatief/autonoom |
| Afkeuring types | Definitief, Park | Definitief, Park, Reroute | Definitief, Park, Reroute | Definitief, Park |

### PM-Agent Perspectief per Workflow

| Workflow | PM-Agent Gate 1 Focus | PM-Agent Gate 2 Focus | Escalatie Triggers |
|----------|----------------------|----------------------|-------------------|
| **BUGFIX** | Root cause check, duplicate, impact, priority (P3/P4 only) | Fix minimaal?, regressie check, tests green, matches root cause | 3x retry zonder approval, P1/P2 post-mortem onvolledig |
| **CHANGES** | Sprint-fit, scope, dependencies, effort, architectuur | Conventie compliance, test plan, API compat, scope creep, effort | Scope creep >20%, blocking dependency, 3x retry |
| **MIGRATION** | Plan compleet, risk matrix, rollback, data mapping, downtime, business impact | Rollback getest, data parity, performance, monitoring, vorige fase | Data anomalie, 2x retry op critical gate, performance degradatie |
| **OVERNIGHT** | PRP kwaliteit, budget, scope overnight haalbaar, criteria meetbaar | Quality score, cost vs budget, architectural drift, tests, report | Cost overschrijding, lage kwaliteit, 2x retry morning review |

### PM-Human Perspectief per Workflow

| Workflow | PM-Human Gate 1 Vraag | PM-Human Gate 2 Vraag | Beslissingscontext |
|----------|----------------------|----------------------|-------------------|
| **BUGFIX** | "Juiste oorzaak? Prioriteit klopt? Niet duplicate?" (P3/P4) | "Fix acceptabel? Geen bijeffecten? Minimale wijziging?" | Urgentie vs grondigheid, P1/P2 gets fast-track |
| **CHANGES** | "Past in sprint? Strategisch verantwoord? Dependencies OK?" | "Oplossing goed genoeg? Kwaliteit? Scope bewaard?" | Business prioriteit, stakeholder verwachtingen |
| **MIGRATION** | "Plan compleet? Timing past bij business? Risico acceptabel?" | "Data aanpak veilig? Cutover window OK?" + per-fase goedkeuring | Data is onvervangbaar, business continuity |
| **OVERNIGHT** | "PRP goed genoeg voor onbeheerd werk? Budget vrij?" | "'s Ochtends: wat is gebouwd? Acceptabel? Doorgaan/rollback?" | Kosten-baten, kwaliteit vs snelheid |

### Architect-Agent Perspectief per Workflow

| Workflow | Architect Focus | Design Principes | Red Flags |
|----------|----------------|-------------------|-----------|
| **BUGFIX** | Impact analyse, minimal change | Single Responsibility, geen bijeffecten | Fix raakt architecturele laag, symptoombestrijding |
| **CHANGES** | Patroon consistentie, interface design | Open/Closed, DRY, bestaande conventies | Nieuw patroon doorbroken, coupling verhoogd |
| **MIGRATION** | Strangler Fig correctheid, data mapping | Parallel run, backward compatible, atomic phases | Data mapping incompleet, geen rollback, tight coupling oud↔nieuw |
| **OVERNIGHT** | Architectuur alignment, abstractie kwaliteit | SOLID, bestaande patterns, modulair | Inconsistente patronen, over-engineering, tech debt |

### WorkflowTypeResolver

```python
class WorkflowTypeResolver:
    """
    Bepaalt het juiste workflow type op basis van de input.
    Selecteert automatisch de juiste WorkflowConfig.
    """

    def resolve(self, input_data: RalphInput) -> WorkflowConfig:
        """
        Resolve workflow type from input characteristics.

        Decision logic:
        1. Explicit type specified → use that
        2. Input is bug report / has stack trace → BUGFIX
        3. Input is Brown Paper / migration plan → MIGRATION
        4. Input is PRP + overnight flag → OVERNIGHT
        5. Default → CHANGES
        """
        if input_data.explicit_type:
            return self._get_config(input_data.explicit_type)

        if self._is_bug_report(input_data):
            return self._get_config(WorkflowType.BUGFIX)

        if self._is_migration(input_data):
            return self._get_config(WorkflowType.MIGRATION)

        if self._is_overnight(input_data):
            return self._get_config(WorkflowType.OVERNIGHT)

        return self._get_config(WorkflowType.CHANGES)

    def _get_config(self, wf_type: WorkflowType) -> WorkflowConfig:
        """Get workflow-specific configuration."""
        configs = {
            WorkflowType.BUGFIX: BUGFIX_CONFIG,
            WorkflowType.CHANGES: CHANGES_CONFIG,
            WorkflowType.MIGRATION: MIGRATION_CONFIG,
            WorkflowType.OVERNIGHT: OVERNIGHT_CONFIG,
        }
        return configs[wf_type]
```

### HITLTrigger Enum

```python
class HITLTrigger(str, Enum):
    """Triggers voor Dual PM Gates en automatische checkpoints."""

    # === Dual PM Gate Triggers (universeel) ===
    BEFORE_START = "before_start"                       # Gate 1 variant: voor workflow start
    BEFORE_IMPLEMENTATION = "before_implementation"     # Gate 1: na analyse, voor implementatie
    AFTER_SOLUTION_DESIGN = "after_solution_design"     # Gate 2: na oplossing design
    BEFORE_MERGE = "before_merge"                       # Gate 2 variant: voor merge

    # === Automatische Triggers ===
    ON_COST_THRESHOLD = "on_cost_threshold"             # Budget limiet bereikt
    ON_CIRCUIT_BREAK = "on_circuit_break"               # Agent zit vast
    ON_ANOMALY = "on_anomaly"                           # Onverwacht gedrag

    # === BUGFIX-specifiek ===
    AFTER_ANALYSIS = "after_analysis"                   # Na root cause analyse

    # === CHANGES-specifiek (event-driven gates) ===
    ON_SCOPE_EXPANSION = "on_scope_expansion"           # Scope groeit
    ON_PATTERN_BREAK = "on_pattern_break"               # Agent wil patroon doorbreken

    # === MIGRATION-specifiek ===
    AFTER_EACH_PHASE = "after_each_phase"               # Na elke migratiefase
    BEFORE_DATA_MIGRATION = "before_data_migration"     # Voor data migratie (CRITICAL)
    BEFORE_CUTOVER = "before_cutover"                   # Voor cutover (CRITICAL)

    # === OVERNIGHT-specifiek ===
    ON_COMPLETION_OR_MORNING = "on_completion_or_morning"  # Asynchroon morning review


class GateAction(str, Enum):
    """Acties voor automatische gates."""
    PAUSE = "pause"       # Pauzeer tot menselijke input
    STOP = "stop"         # Volledig stoppen
    NOTIFY = "notify"     # Alleen notificatie, ga door


class PMVerdict(str, Enum):
    """Mogelijke uitspraken van een PM (agent of human)."""
    APPROVED = "approved"                 # Goedgekeurd, ga door
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"  # Goedgekeurd, maar met voorwaarden
    REVISION_REQUESTED = "revision_requested"  # Aanpassing gevraagd, retry
    REJECTED = "rejected"                 # Afgekeurd (zie RejectionType)
    FAIL = "fail"                         # PM-Agent: criteria niet gehaald
    WARN = "warn"                         # PM-Agent: criteria gehaald maar met waarschuwingen


@dataclass
class DualPMGate:
    """Configuratie voor een Dual PM Approval Gate."""
    name: str
    trigger: HITLTrigger
    pm_agent_criteria: str                              # Key in PM_AGENT_CRITERIA dict
    max_retries: int = 3
    timeout_reminder: Optional[timedelta] = None        # None = synchroon
    timeout_escalation: Optional[timedelta] = None
    critical: bool = False                              # True = kan NIET auto-approved worden
    pm_agent_auto_approve: bool = True                  # False bij critical gates
    synchronous: bool = False                           # True = mens is aanwezig
    immediate: bool = False                             # True = geen wachttijd (anomalieën)
    required_severity: Optional[List[str]] = None       # None = altijd, ["P3","P4"] = alleen die


@dataclass
class AutomaticGate:
    """Configuratie voor een automatische gate (zonder PM review)."""
    name: str
    trigger: HITLTrigger
    action: GateAction
    notification: bool = True
```

---

## Executie-Architectuur: Stateful Workflow, Stateless Executors

> **Fundamenteel inzicht:** Ralph Wiggum workflows zijn GEEN doorlopende processen. Ze zijn een reeks discrete, korte executies die worden aangedreven door een state machine. De state file is het geheugen — niet de shell, niet het LLM.

### Probleem: Drie Architectural Constraints

#### Constraint 1: Geen Persistent Shell

Een `marqed-bugfix.sh` kan niet als één doorlopend proces draaien. Op het moment dat een Dual PM Gate wordt bereikt, stopt de executie. De PM-Human reageert misschien over 4 uur, misschien over 2 dagen. Een shell proces kan niet (en moet niet) wachten.

```
❌ FOUT — wat NIET werkt:

  $ marqed-bugfix.sh --ticket=BUG-123
  [analyse loopt...]
  [root cause gevonden]
  [GATE 1: wacht op PM-Agent...]
  [PM-Agent: PASS]
  [GATE 1: wacht op PM-Human...]     ← Shell hangt hier. Uren. Dagen.
  ...                                 ← Proces kan crashen, server reboot, timeout
  [PM-Human: GOEDGEKEURD]             ← Als dit al ooit komt
  [fix loopt...]
```

#### Constraint 2: Geen LLM Context Window als Geheugen

Een LLM (Claude, GPT, etc.) heeft **geen persistent geheugen** tussen aanroepen. Elke keer dat je het LLM aanroept, begint het met een lege context window. Het "weet" niets van:

- Wat het eerder heeft geanalyseerd
- Welke root cause het had gevonden
- Wat de PM feedback was
- Welke guardrails het had geleerd
- Welke patronen het had ontdekt

**Alles** wat het LLM nodig heeft voor de huidige fase, moet **expliciet meegegeven** worden als context bij die specifieke aanroep. De state file IS het geheugen van het LLM.

```
❌ FOUT — aanname dat LLM "onthoudt":

  Aanroep 1: "Analyseer bug BUG-123"     → LLM vindt root cause, schrijft naar state
  [PM Gate... uren later...]
  Aanroep 2: "Fix de bug"                 → LLM weet NIETS meer. Wat was de root cause?
                                             Welke files waren relevant? Wat zei de PM?

✅ GOED — context wordt meegegeven:

  Aanroep 1: "Analyseer bug BUG-123"     → LLM vindt root cause, schrijft naar state
  [PM Gate... uren later...]
  Aanroep 2: context={                    → LLM krijgt ALLES wat het nodig heeft
    root_cause: "uit state file",
    pm_feedback: "uit state file",
    relevant_code: "vers uit codebase",
    guardrails: "uit guardrails.md",
    accumulated_patterns: "uit state file"
  }
  "Fix de bug op basis van deze context"
```

#### Constraint 3: Onvoorspelbare Timing

De timing van een workflow is fundamenteel onvoorspelbaar wanneer er menselijke beslissers in zitten:

| Fase | Verwachte duur | Werkelijke duur |
|------|---------------|-----------------|
| Analyse (LLM) | Seconden-minuten | Voorspelbaar |
| PM-Agent review | Milliseconden | Voorspelbaar |
| **PM-Human review** | **Onbekend** | **4 uur tot 3 dagen** |
| Fix (LLM) | Seconden-minuten | Voorspelbaar |
| **PM-Human review** | **Onbekend** | **4 uur tot 3 dagen** |

De enige manier om hier mee om te gaan: **event-driven executie met een orchestrator die de workflow voortduwt bij elke state-transitie.**

### Oplossing: Discrete Fase-Scripts + Orchestrator

#### Architectuurpatroon

```
┌──────────────────────────────────────────────────────────────────────────────┐
│           EXECUTION ARCHITECTURE: "Nudge & Execute"                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────┐                                                      │
│  │  marqed-assistent   │ ← Orchestrator / "Nudger"                           │
│  │  (event-driven)     │   Monitort state file, bepaalt volgende actie,       │
│  │                     │   roept het juiste fase-script aan                   │
│  └──────────┬──────────┘                                                      │
│             │                                                                 │
│             │ leest                                                            │
│             ▼                                                                 │
│  ┌─────────────────────┐                                                      │
│  │  .marqed/            │ ← State File = Single Source of Truth               │
│  │  prp-ralph.state.md │   Bevat: fase, status, PM feedback,                 │
│  │                     │   guardrails, context snapshots,                     │
│  │                     │   approval history, retry counts                     │
│  └──────────┬──────────┘                                                      │
│             │                                                                 │
│             │ bepaalt welk script                                              │
│             ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐      │
│  │  Fase-Scripts (klein, zelfstandig, stateless)                       │      │
│  │                                                                     │      │
│  │  marqed-wf-init.sh          → Initialiseer workflow + state file   │      │
│  │  marqed-wf-analyse.sh       → Analyse fase (LLM aanroep)          │      │
│  │  marqed-wf-pm-gate.sh       → PM-Agent beoordeling + PM-Human     │      │
│  │  marqed-wf-implement.sh     → Implementatie fase (LLM aanroep)    │      │
│  │  marqed-wf-validate.sh      → Validatie (tests, lint, typecheck)  │      │
│  │  marqed-wf-merge.sh         → Merge / afronding                   │      │
│  │  marqed-wf-rollback.sh      → Rollback naar vorige fase           │      │
│  │                                                                     │      │
│  │  Elk script:                                                        │      │
│  │  1. Leest state file                                                │      │
│  │  2. Assembleert context voor LLM (fase-specifiek!)                  │      │
│  │  3. Voert één discrete actie uit                                    │      │
│  │  4. Schrijft resultaat terug naar state file                        │      │
│  │  5. Exit                                                            │      │
│  └─────────────────────────────────────────────────────────────────────┘      │
│             │                                                                 │
│             │ na exit                                                          │
│             ▼                                                                 │
│  ┌─────────────────────┐                                                      │
│  │  marqed-assistent   │ ← Leest nieuwe state, bepaalt volgende "nudge"      │
│  │  detecteert change  │   Kan VOORUIT (volgende fase) of TERUG (retry)      │
│  │  → volgende nudge   │                                                      │
│  └─────────────────────┘                                                      │
│                                                                               │
│  ════════════════════════════════════════════════════════════════════════      │
│  TRIGGER MECHANISME:                                                          │
│  • PM-Human keurt goed via platform → webhook/event → marqed-assistent       │
│  • Timeout verstreken → cron detecteert → marqed-assistent escalatie         │
│  • Script klaar → exit code → marqed-assistent leest state → volgende        │
│  ════════════════════════════════════════════════════════════════════════      │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### Voorbeeld: BUGFIX Flow als Discrete Stappen

```
Stap 1: marqed-assistent ontvangt trigger (nieuw bug ticket)
        → roept: marqed-wf-init.sh --type=bugfix --ticket=BUG-123
        → state: { phase: "init", status: "ready" }

Stap 2: marqed-assistent leest state → phase=init, status=ready
        → roept: marqed-wf-analyse.sh
        → script assembleert context: bug report + codebase + guardrails
        → LLM analyseert, vindt root cause
        → state: { phase: "analyse", status: "complete", root_cause: "..." }

Stap 3: marqed-assistent leest state → phase=analyse, status=complete
        → roept: marqed-wf-pm-gate.sh --gate=1
        → PM-Agent beoordeelt automatisch (milliseconden)
        → PM-Agent: PASS
        → state: { phase: "gate_1", status: "pending_pm_human", pm_agent: "pass" }

       [PAUZE — uren/dagen — script is NIET actief]

Stap 4: PM-Human keurt goed via platform → event naar marqed-assistent
        → marqed-assistent schrijft approval naar state
        → state: { phase: "gate_1", status: "approved", pm_feedback: "..." }

Stap 5: marqed-assistent leest state → gate_1 approved
        → roept: marqed-wf-implement.sh
        → script assembleert context: root_cause + pm_feedback + code + guardrails
        → LLM implementeert fix
        → state: { phase: "implement", status: "complete", fix_diff: "..." }

Stap 6: marqed-assistent leest state → implement complete
        → roept: marqed-wf-validate.sh
        → runt tests, lint, typecheck (geen LLM nodig)
        → state: { phase: "validate", status: "pass" }

Stap 7: marqed-assistent leest state → validate pass
        → roept: marqed-wf-pm-gate.sh --gate=2
        → ... (zelfde patroon als stap 3-4)

Stap 8: Na gate_2 approval
        → roept: marqed-wf-merge.sh
        → state: { phase: "complete", status: "merged" }
```

**Bij AFKEURING (terug):**
```
Stap 4b: PM-Human keurt AF met feedback "root cause is symptoom, niet oorzaak"
         → state: { phase: "gate_1", status: "rejected_reroute",
                     pm_feedback: "root cause is symptoom...", retry_count: 1 }

Stap 5b: marqed-assistent leest state → rejected_reroute
         → roept: marqed-wf-analyse.sh  (TERUG naar analyse!)
         → script assembleert context: INCLUSIEF pm_feedback + vorige analyse + waarom afgekeurd
         → LLM analyseert opnieuw met die feedback
         → state: { phase: "analyse", status: "complete", root_cause: "NIEUWE analyse...",
                     retry_count: 1 }
```

### Context Assembly — Het Kritieke Stuk

> **Dit is het moeilijkste onderdeel van de architectuur.** Niet de state machine, niet de orchestratie — maar het correct samenstellen van de context die het LLM meekrijgt bij elke aanroep.

#### Waarom Context Assembly moeilijk is

1. **Token budget:** Een LLM heeft een maximum context window (bijv. 200K tokens). Je kunt niet "alles" meegeven — je moet selecteren.
2. **Relevantie per fase:** De analyse-fase heeft andere context nodig dan de fix-fase. Onnodige context is ruis die het LLM afleidt.
3. **Versheid:** Tussen twee aanroepen (uren/dagen) kan de codebase zijn veranderd door andere PRs. Context moet vers zijn.
4. **Accumulatie:** Guardrails, patronen en retry-feedback groeien per iteratie. Ze moeten mee, maar passen op een gegeven moment niet meer.

#### ContextAssemblyService

```python
class ContextAssemblyService:
    """
    Assembleert de juiste context voor elke LLM-aanroep.

    Principe: niet ALLES meegeven, maar het JUISTE meegeven.
    Elke fase heeft een eigen context-profiel.
    """

    # Context budget per fase (tokens, bij 200K window)
    CONTEXT_BUDGETS = {
        "analyse":    {"state": 5_000,  "code": 80_000, "guardrails": 3_000, "history": 2_000},
        "implement":  {"state": 8_000,  "code": 100_000,"guardrails": 5_000, "history": 5_000},
        "validate":   {"state": 2_000,  "code": 0,      "guardrails": 1_000, "history": 0},
        "pm_review":  {"state": 10_000, "code": 20_000, "guardrails": 2_000, "history": 8_000},
    }

    def assemble(
        self,
        phase: WorkflowPhase,
        state: RalphState,
        workflow_type: WorkflowType
    ) -> AssembledContext:
        """
        Assemble context for a specific phase invocation.

        Returns a structured context object ready for LLM prompt injection.
        """
        budget = self.CONTEXT_BUDGETS[phase.name]
        context = AssembledContext()

        # 1. ALTIJD: Workflow instructies + fase-specifiek prompt template
        context.add_system(self._get_prompt_template(workflow_type, phase))

        # 2. ALTIJD: Huidige state (gefilterd op relevantie voor deze fase)
        context.add_state(self._filter_state_for_phase(state, phase), budget["state"])

        # 3. ALTIJD: Guardrails (accumulated lessons, gepruned op budget)
        context.add_guardrails(
            self.guardrails_service.load(max_tokens=budget["guardrails"])
        )

        # 4. CONDITIONEEL: Codebase context (alleen als fase code nodig heeft)
        if budget["code"] > 0:
            context.add_code(
                self._get_relevant_code(state, phase, budget["code"])
            )

        # 5. CONDITIONEEL: Retry history (alleen als dit een retry is)
        if state.retry_count > 0:
            context.add_retry_context(
                previous_attempts=state.get_attempts_for_phase(phase),
                pm_feedback=state.get_pm_feedback_for_gate(phase.preceding_gate),
                rejection_reason=state.last_rejection_reason
            )

        # 6. CONDITIONEEL: Approval history (voor PM review fases)
        if phase.is_pm_gate:
            context.add_approval_history(
                state.get_approval_history(),
                budget["history"]
            )

        return context

    def _get_relevant_code(
        self,
        state: RalphState,
        phase: WorkflowPhase,
        token_budget: int
    ) -> str:
        """
        Haal relevante code op — VERS uit codebase, niet uit cache.

        Belangrijk: code kan veranderd zijn sinds vorige aanroep!
        Gebruikt file hashes om staleness te detecteren.
        """
        relevant_files = state.get_relevant_files_for_phase(phase)

        # Check of files zijn veranderd sinds vorige aanroep
        for file_path in relevant_files:
            current_hash = self._hash_file(file_path)
            stored_hash = state.get_file_hash(file_path)
            if current_hash != stored_hash:
                # File is veranderd! Neem mee als waarschuwing
                state.add_warning(f"File {file_path} changed since last invocation")

        return self._read_files_within_budget(relevant_files, token_budget)

    def _filter_state_for_phase(
        self,
        state: RalphState,
        phase: WorkflowPhase
    ) -> dict:
        """
        Filter state op wat relevant is voor deze specifieke fase.

        Analyse-fase hoeft merge-procedures niet te weten.
        Fix-fase hoeft de volledige bug report niet — alleen de root cause samenvatting.
        Merge-fase hoeft de analyse-pogingen niet.
        """
        phase_filters = {
            "analyse": ["ticket", "bug_report", "previous_analysis_attempts",
                       "pm_feedback", "codebase_patterns"],
            "implement": ["root_cause_summary", "pm_feedback", "fix_constraints",
                         "codebase_patterns", "affected_files"],
            "validate": ["expected_test_results", "validation_commands"],
            "pm_review": ["full_history", "metrics", "approval_history",
                         "quality_scores", "retry_history"],
        }
        return state.filter(phase_filters.get(phase.name, ["full"]))
```

#### Context Profiel per Fase

| Fase | State Context | Code Context | Guardrails | History | Speciale Context |
|------|--------------|-------------|------------|---------|-----------------|
| **analyse** | Ticket, bug report, vorige pogingen | Verdachte files (80K budget) | Ja (3K) | Minimaal | PM feedback (als retry) |
| **implement** | Root cause samenvatting, constraints | Relevante files (100K budget) | Ja (5K) | PM feedback | Affected files, patterns |
| **validate** | Validatie commando's | Geen | Minimaal | Geen | Expected results |
| **pm_review** | Volledige history | Diff/summary (20K) | Ja (2K) | Volledig (8K) | Approval history, metrics |
| **merge** | Fix samenvatting, approvals | Diff alleen | Geen | Approval chain | Merge checklist |

#### Versheidscontrole

```python
class FreshnessChecker:
    """
    Controleert of context nog vers/geldig is na een HITL pauze.

    Tussen twee fases (uren/dagen) kan er veel veranderd zijn:
    - Andere PRs gemerged → code conflicts
    - Dependencies geüpdate → breaking changes
    - Test suite gewijzigd → nieuwe failures
    - Configuratie aangepast → andere runtime
    """

    async def check_freshness(
        self,
        state: RalphState,
        phase: WorkflowPhase
    ) -> FreshnessResult:
        """
        Run voor ELKE LLM-aanroep na een HITL pauze.
        """
        checks = []

        # 1. Git status: zijn er commits sinds vorige fase?
        commits_since = await self._git_log_since(state.last_phase_timestamp)
        if commits_since:
            checks.append(FreshnessCheck(
                item="git_history",
                stale=True,
                detail=f"{len(commits_since)} commits since last phase",
                impact="Code context may be outdated"
            ))

        # 2. File hashes: zijn relevante files veranderd?
        changed_files = self._check_file_hashes(state.relevant_files)
        if changed_files:
            checks.append(FreshnessCheck(
                item="relevant_files",
                stale=True,
                detail=f"{len(changed_files)} relevant files changed",
                impact="Analysis/fix may need updating",
                severity="HIGH" if phase.name == "implement" else "MEDIUM"
            ))

        # 3. Dependencies: zijn er breaking changes?
        dep_changes = await self._check_dependency_changes(state.last_phase_timestamp)

        # 4. Test baseline: werken tests nog?
        if phase.name in ["implement", "validate"]:
            test_baseline = await self._run_baseline_tests()
            if not test_baseline.passed:
                checks.append(FreshnessCheck(
                    item="test_baseline",
                    stale=True,
                    detail="Tests fail BEFORE our changes — external cause",
                    impact="Cannot distinguish our failures from pre-existing",
                    severity="CRITICAL"
                ))

        return FreshnessResult(checks=checks, proceed=all(c.severity != "CRITICAL" for c in checks))
```

### Script Decompositie per Workflow Type

| Workflow | Voor Gate 1 | Gate 1 | Tussen Gates | Gate 2 | Na Gate 2 |
|----------|------------|--------|-------------|--------|-----------|
| **BUGFIX** | `wf-analyse.sh` | `wf-pm-gate.sh --gate=1` | `wf-implement.sh` → `wf-validate.sh` | `wf-pm-gate.sh --gate=2` | `wf-merge.sh` |
| **CHANGES** | `wf-design.sh` | `wf-pm-gate.sh --gate=1` | `wf-implement.sh` (herhaald) → `wf-validate.sh` | `wf-pm-gate.sh --gate=2` | `wf-merge.sh` |
| **MIGRATION** | `wf-analyse.sh` | `wf-pm-gate.sh --gate=1` | Per fase: `wf-implement.sh` → `wf-validate.sh` → `wf-pm-gate.sh --gate=phase` | `wf-pm-gate.sh --gate=2` (+ critical gates) | `wf-merge.sh` |
| **OVERNIGHT** | `wf-prp-prep.sh` | `wf-pm-gate.sh --gate=1` (synchroon, avonds) | `wf-implement.sh` (herhaald, onbeheerd) | `wf-pm-gate.sh --gate=2` (morning, asynchroon) | `wf-merge.sh` |

**Let op:** Tussen de gates draait Ralph Wiggum WEL als een doorlopende loop (meerdere iteraties `wf-implement.sh` → `wf-validate.sh`). De breaks zitten alleen bij de PM Gates. Binnen een fase is de executie continu.

### Orchestrator: marqed-assistent als State Machine Driver

```python
class MarqedAssistent:
    """
    De marqed-assistent als workflow orchestrator.

    Niet een doorlopend proces, maar een event-driven handler
    die bij elke trigger de juiste actie bepaalt en uitvoert.
    """

    # State transition table: (current_phase, event) → action
    TRANSITIONS = {
        # BUGFIX transitions
        ("init", "ready"):              Action("marqed-wf-analyse.sh"),
        ("analyse", "complete"):        Action("marqed-wf-pm-gate.sh", gate=1),
        ("gate_1", "approved"):         Action("marqed-wf-implement.sh"),
        ("gate_1", "rejected_reroute"): Action("marqed-wf-analyse.sh"),  # TERUG
        ("gate_1", "rejected_park"):    Action("marqed-wf-park.sh"),     # STOP → backlog
        ("gate_1", "rejected_definitive"): Action("marqed-wf-close.sh"), # STOP → archief
        ("implement", "complete"):      Action("marqed-wf-validate.sh"),
        ("validate", "pass"):           Action("marqed-wf-pm-gate.sh", gate=2),
        ("validate", "fail"):           Action("marqed-wf-implement.sh"), # Fix test failures
        ("gate_2", "approved"):         Action("marqed-wf-merge.sh"),
        ("gate_2", "rejected_reroute"): Action("marqed-wf-implement.sh"), # TERUG
        ("gate_2", "timeout"):          Action("marqed-wf-escalate.sh"),
        ("merge", "complete"):          Action("marqed-wf-archive.sh"),
    }

    async def handle_event(self, event: WorkflowEvent) -> None:
        """
        Event handler — aangeroepen bij:
        - Script completion (exit code)
        - PM-Human approval/rejection (platform webhook)
        - Timeout (cron detectie)
        - Cost threshold (monitoring alert)
        """
        state = self._read_state(event.workflow_id)

        # Versheidscontrole na HITL pauze
        if event.source == "pm_human":
            freshness = await self.freshness_checker.check_freshness(
                state, state.current_phase
            )
            if not freshness.proceed:
                await self._handle_stale_context(state, freshness)
                return

        # Bepaal volgende actie
        key = (state.current_phase, event.type)
        action = self.TRANSITIONS.get(key)

        if action is None:
            await self._handle_unknown_transition(state, event)
            return

        # Context assembly voor de volgende fase
        context = self.context_assembler.assemble(
            phase=action.target_phase,
            state=state,
            workflow_type=state.workflow_type
        )

        # Voer fase-script uit
        result = await self._execute_script(action, context)

        # Update state met resultaat
        state.update(result)
        self._write_state(state)

    async def _handle_stale_context(
        self,
        state: RalphState,
        freshness: FreshnessResult
    ) -> None:
        """
        Handle wanneer context niet meer vers is na HITL pauze.

        Opties:
        1. CRITICAL (tests falen voor onze changes): stop, rapporteer
        2. HIGH (relevante files veranderd): re-analyse nodig
        3. MEDIUM (andere files veranderd): waarschuwing, ga door
        """
        if freshness.has_critical:
            state.add_blocker("Pre-existing test failures detected after HITL pause")
            await self.notification_service.alert(
                "Context stale: tests fail before our changes. Manual intervention needed."
            )
        elif freshness.has_high:
            # Terug naar analyse met versheids-context
            state.add_warning("Relevant files changed during HITL pause — re-analysis needed")
            state.reroute_to_phase("analyse")
        else:
            state.add_warning(f"Minor changes detected: {freshness.summary}")
            # Ga door met waarschuwing in context
```

### Trigger Mechanismen voor de Orchestrator

| Trigger | Bron | Hoe marqed-assistent het detecteert | Actie |
|---------|------|--------------------------------------|-------|
| **Script klaar** | Fase-script exit | Exit code + state file change | Lees state, bepaal volgende stap |
| **PM-Human approval** | Platform UI | Webhook naar marqed-assistent endpoint | Update state, nudge volgende fase |
| **PM-Human rejection** | Platform UI | Webhook met feedback payload | Update state, nudge terug naar eerdere fase |
| **Timeout** | Klok | Cron job checkt state timestamps | Stuur reminder of escaleer |
| **Cost threshold** | Monitoring | Cost alert trigger | Pauzeer workflow, notificeer |
| **Anomalie** | Validatie script | Exit code + anomaly marker in state | Onmiddellijke stop, notificeer |
| **Codebase change** | Git hooks | Post-merge hook checkt actieve workflows | Versheidscontrole op relevante workflows |

### State File als Single Source of Truth

De state file `.marqed/prp-ralph.state.md` vervangt zowel het geheugen van de shell als het geheugen van het LLM. Het moet bevatten:

```markdown
# Ralph State: BUG-123 — Login timeout bij concurrent sessions

## Metadata
- **Workflow**: BUGFIX
- **Ticket**: BUG-123
- **Severity**: P3
- **Current Phase**: gate_1
- **Current Status**: pending_pm_human
- **Retry Count**: 0
- **Started**: 2026-01-28T14:30:00Z
- **Last Activity**: 2026-01-28T14:32:15Z
- **Cost So Far**: $0.85

## Context Snapshots (voor LLM context assembly)

### Root Cause Analysis (fase: analyse, iteratie 1)
- **Root Cause**: Race condition in `SessionManager.acquire()` — lock wordt niet correct
  vrijgegeven bij timeout, waardoor volgende sessie permanent blokkeert.
- **Evidence**: Stack trace toont deadlock op lijn 145 van session_manager.py
- **Affected Files**: src/services/session_manager.py (lijn 140-160), src/models/session.py
- **File Hashes**: { "session_manager.py": "abc123", "session.py": "def456" }
- **Confidence**: HIGH

### Proposed Fix
- Implementeer `try/finally` block rond lock acquisition
- Voeg timeout parameter toe aan `acquire()` methode
- Schrijf concurrent test met 10 parallelle sessies

## Approval History

### Gate 1 — PM-Agent Review (2026-01-28T14:32:00Z)
- **Verdict**: PASS (score: 0.9)
- **Criteria**: root_cause ✅, evidence ✅, not_duplicate ✅, priority ✅, impact ✅
- **Warnings**: None

### Gate 1 — PM-Human Review (PENDING)
- **Sent**: 2026-01-28T14:32:15Z
- **Timeout Reminder**: 2026-01-28T18:32:15Z
- **Timeout Escalation**: 2026-01-28T22:32:15Z

## Guardrails (accumulated)
- session_manager.py heeft geen bestaande tests → schrijf EERST tests
- Project gebruikt pytest-asyncio voor async tests

## Progress Log

### Fase: analyse — Iteratie 1 (2026-01-28T14:30:00Z → 14:31:45Z)
- **Input Context**: Bug report (450 tokens) + session_manager.py (2100 tokens)
- **Output**: Root cause gevonden, 3 files geïdentificeerd
- **Cost**: $0.35
- **Patterns Found**: Lock pattern in services/

### Fase: gate_1 — PM-Agent (2026-01-28T14:32:00Z)
- **Input Context**: State summary (800 tokens) + analysis result (1200 tokens)
- **Output**: PASS, score 0.9
- **Cost**: $0.15
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

### 3. StageApprovalWorkflow (→ DualPMApprovalService)

> **Opmerking:** Deze klasse is geëvolueerd naar het **Dual PM Approval Gate** patroon (zie sectie "Workflow-Specifieke Ralph Configuraties" hierboven). De `StageApprovalWorkflow` wordt vervangen door `DualPMApprovalService` die zowel PM-Agent als PM-Human review combineert in een approval loop met retry, timeout en escalatie mechanismen.

Dual PM approval tussen development stages met PM-Agent (AI) als eerste reviewer en PM-Human als finale beslisser.

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
| DualPMApprovalService | 10 | Dual PM Gate pattern (PM-Agent + PM-Human, approval loop, retry, timeout, escalatie) |
| ApprovalStateManager | 4 | Persistent approval state + audit trail |
| PMAgentService | 6 | PM-Agent criteria evaluation per workflow type |
| ContextAssemblyService | 10 | Fase-specifieke context assembly, token budgets, state filtering |
| FreshnessChecker | 6 | Versheidscontrole na HITL pauze (git, file hashes, test baseline) |
| MarqedAssistent Orchestrator | 8 | Event-driven state machine driver, transition table, triggers |
| Fase-scripts (6 scripts) | 12 | Discrete stateless scripts per workflow fase |
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
- [ ] DualPMApprovalService implements Dual PM Gate pattern (PM-Agent + PM-Human)
- [ ] Approval loop met retry (max 3), timeout en escalatie mechanismen
- [ ] Gedifferentieerde afkeuring: definitief / park / reroute
- [ ] Approval state persistence overleeft context window resets
- [ ] PM-Agent criteria per workflow type geconfigureerd
- [ ] Critical gates (data migratie, cutover) kunnen NIET auto-approved worden
- [ ] RollbackService enables git reset with regression testing
- [ ] MemoryCompressionService handles context handoff between runs
- [ ] MultiPhaseValidationPipeline validates 8 phases (syntax → docs)

### Execution Architecture Requirements

- [ ] Workflows draaien als discrete fase-scripts, GEEN persistent shell
- [ ] State file (.marqed/prp-ralph.state.md) is Single Source of Truth
- [ ] ContextAssemblyService assembleert fase-specifieke context per LLM-aanroep
- [ ] Context budget management per fase (analyse: 90K, implement: 118K, validate: 3K, pm_review: 42K)
- [ ] FreshnessChecker valideert context versheid na HITL pauze
- [ ] File hash tracking detecteert codebase changes tussen fases
- [ ] MarqedAssistent orchestrator event-driven met state transition table
- [ ] Trigger mechanismen: script exit, webhook (PM approval), cron (timeout), monitoring (cost)
- [ ] Forward EN backward transitions (terug naar eerdere fase bij afkeuring)
- [ ] Retry history en PM feedback wordt meegegeven als context bij re-analyse

### Quality Gates

- [ ] 80+ unit tests passing
- [ ] < 5% cost overrun vs estimates
- [ ] < 10% false completion detections
- [ ] Guardrails reduce repeat failures by 70%
- [ ] Rollback recovery time < 60 seconds
- [ ] Context compression maintains 95% essential information
- [ ] Context assembly levert >90% relevante informatie binnen token budget

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
| **Stale context na HITL pauze** | FreshnessChecker + file hash tracking + git log since |
| **LLM "vergeet" vorige fases** | ContextAssemblyService laadt relevante state per aanroep |
| **Shell timeout bij PM wachttijd** | Discrete fase-scripts, event-driven orchestrator |
| **Context budget overschrijding** | Token budgets per fase, guardrails pruning |
| **Codebase drift tussen fases** | Post-merge git hooks triggeren versheidscontrole |

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

### Related: Fase 32E — Quality Harness

Fase 32E ([fase-32e-quality-harness.md](fase-32e-quality-harness.md)) breidt het Dual PM Approval Gate patroon uit naar **micro-deliverable granulariteit** met:
- PRD decomposition naar kleinste toetsbare eenheden
- PM Acceptance Gate per micro-deliverable (onafhankelijke Claude Code review)
- QA Gate (7 assen: code quality, security, tests+coverage, performance, contracts, dependencies, dead code)
- Progressive regression (groeiende test suite per geaccepteerde deliverable)
- Sprint completion gate met full regression + traceability matrix
- Acceptance Registry (SQLite) voor tracking en rapportage

**Planning:** KW27-30 [w191-194], 120 uur, na afronding Fase 32D.

---

*Created: Week 158 (2026-01-15)*
*Updated: Week 160 (2026-01-31) — Workflow-specifieke configuraties (4 modi) + Dual PM Approval Gate patroon + Executie-Architectuur (stateful workflow, stateless executors, context assembly) toegevoegd*
*Updated: Week 162 (2026-02-01) — Fase 32E Quality Harness referentie toegevoegd*
*Author: Claude Code*
