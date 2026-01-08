# Tool-Workflow Integration Proposal

**Datum**: Week 79 (December 2025)
**Doel**: Bestaande tools integreren in workflows voor betere analyse, migratie, verbeterplannen en maintenance

---

## Executive Summary

Dit document beschrijft hoe de 8 nieuwe services (Week 75-79) geïntegreerd kunnen worden in de 11 bestaande workflows om ze te versterken en uit te breiden.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    TOOL-WORKFLOW INTEGRATION MATRIX                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  TOOLS (Week 75-79)              WORKFLOWS (11)                            │
│  ┌─────────────────────┐         ┌─────────────────────┐                  │
│  │ Week 75: CodeGraph  │─────────│ GREEN_PAPER         │ Architecture     │
│  │ Week 76: Claude-Mem │─────────│ BROWN_PAPER         │ Context          │
│  │ Week 77: Layered    │─────────│ MIGRATION           │ Analysis         │
│  │ Week 78: BigAGI     │─────────│ QUALITY_*           │ Validation       │
│  │ Week 78: Playwriter │─────────│ TESTING             │ Automation       │
│  │ Week 79: Worktrees  │─────────│ NEW_FEATURE         │ Parallel Dev     │
│  │ Week 79: GitHub     │─────────│ BUG/MAINTENANCE     │ Sync             │
│  │ Week 79: CCPM       │─────────│ PROJECT_DEFINITION  │ PRD → Tasks      │
│  └─────────────────────┘         └─────────────────────┘                  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Workflow Integraties per Tool

### 1.1 CodeGraph (Week 75) → Impact Analysis

**Doel**: Code-afhankelijkheden begrijpen voordat wijzigingen worden gemaakt.

| Workflow | Integratie | Voordeel |
|----------|------------|----------|
| **NEW_FEATURE** | Felix analyseert impact vooraf | Scope-creep voorkomen |
| **MIGRATION** | Miguel identificeert dependencies | Veiligere migraties |
| **MAINTENANCE** | Marcus vindt gerelateerde code | Complete refactoring |
| **BUG** | Betty trace root cause | Snellere debugging |

```python
# Integratie in NEW_FEATURE workflow
async def new_feature_workflow(description: str, project_id: int):
    # Stap 1: Impact analysis VOORDAT Felix begint
    impact = await code_graph_service.analyze_impact(
        project_id=project_id,
        change_type="feature",
        affected_modules=["api", "models"]
    )

    # Stap 2: Felix ontwerpt met impact-kennis
    if impact.high_risk_modules:
        design = await felix.design_with_constraints(
            description=description,
            avoid_modules=impact.high_risk_modules,
            coupling_metrics=impact.coupling_scores
        )

    # Stap 3: Quinn valideert impact
    validation = await quinn.validate_impact(
        proposed_changes=design.changes,
        impact_analysis=impact
    )
```

---

### 1.2 Claude-Mem (Week 76) → Contextual Memory

**Doel**: Agent-context behouden over sessies heen.

| Workflow | Integratie | Voordeel |
|----------|------------|----------|
| **ALLE WORKFLOWS** | Start met context injection | 95% minder token-gebruik |
| **PROJECT_DEFINITION** | Peter onthoudt eerdere beslissingen | Consistentie |
| **QUALITY_AUDIT** | Quinn onthoudt eerdere issues | Patroonherkenning |
| **TESTING** | Tessa onthoudt test-strategie | Consistente coverage |

```python
# Integratie: Context injection bij elke workflow
async def start_workflow(workflow_type: str, session_id: str, project_id: int):
    # Haal relevante context op
    context = await claude_mem_service.get_context_window(
        session_id=session_id,
        token_budget=4000,
        tags=[workflow_type, f"project:{project_id}"]
    )

    # Inject in agent prompt
    enhanced_prompt = f"""
    ## Relevante Context (uit vorige sessies)
    {context.compressed_observations}

    ## Eerdere Beslissingen
    {context.decisions}

    ## Huidige Taak
    {task_description}
    """

    # Na workflow: observaties opslaan
    async def on_agent_decision(agent: str, decision: str):
        await claude_mem_service.capture_observation(
            session_id=session_id,
            content=f"[{agent}] {decision}",
            tags=["decision", agent, workflow_type]
        )
```

---

### 1.3 Layered Analysis (Week 77) → Deep Code Understanding

**Doel**: Legacy code systematisch analyseren.

| Workflow | Integratie | Voordeel |
|----------|------------|----------|
| **BROWN_PAPER** | 4-laags analyse van legacy | Complete inzicht |
| **MIGRATION** | VBScript/SP analyse | Accurate scoping |
| **QUALITY_AUDIT** | SWOT per module | Prioritering |
| **MAINTENANCE** | Improvement items | Actionable backlog |

```python
# BROWN_PAPER workflow met Layered Analysis
async def brown_paper_workflow(repo_url: str, project_id: int):
    # Stap 1: Start 4-layer analysis
    session = await layered_analysis_service.create_session(
        project_id=project_id,
        repo_url=repo_url
    )

    # Stap 2: Layer 1 - VBScript inventarisatie
    vbscript_results = await layered_analysis_service.analyze_vbscript(
        session_id=session.id
    )

    # Stap 3: Layer 2 - Stored Procedures
    sp_results = await layered_analysis_service.analyze_stored_procedures(
        session_id=session.id
    )

    # Stap 4: Layer 3 - SWOT per component
    swot_results = await layered_analysis_service.create_swot(
        session_id=session.id,
        components=vbscript_results.components + sp_results.procedures
    )

    # Stap 5: Layer 4 - Verbeteringen genereren
    improvements = await layered_analysis_service.generate_improvements(
        session_id=session.id,
        swot=swot_results
    )

    # Stap 6: Miguel ontvangt complete analyse
    migration_plan = await miguel.create_migration_plan(
        vbscript_analysis=vbscript_results,
        sp_analysis=sp_results,
        swot=swot_results,
        improvements=improvements
    )
```

---

### 1.4 BigAGI Beam (Week 78) → Multi-Model Validation

**Doel**: Kritische beslissingen valideren met meerdere LLMs.

| Workflow | Integratie | Voordeel |
|----------|------------|----------|
| **QUALITY_AUDIT** | Quinn's review valideren | Hogere betrouwbaarheid |
| **QUALITY_IMPROVEMENT** | Voorgestelde fixes valideren | Minder regressies |
| **PROJECT_DEFINITION** | Architecture decisions valideren | Betere keuzes |
| **ENHANCEMENT** | Felix's design valideren | Robuustere features |

```python
# QUALITY_AUDIT met BigAGI validatie
async def quality_audit_workflow(project_id: int, scope: str):
    # Stap 1: Quinn doet eerste review
    quinn_review = await quinn.review_code(
        project_id=project_id,
        scope=scope
    )

    # Stap 2: Valideer kritische findings met BigAGI
    if quinn_review.severity == "critical":
        validation = await bigagi_service.run_validation(
            task=f"Review security finding: {quinn_review.finding}",
            primary_response=quinn_review.recommendation,
            primary_model="claude-sonnet",
            validation_models=[
                {"name": "deepseek-r1", "provider": "ollama", "weight": 1.2},
                {"name": "qwen2.5-coder", "provider": "ollama", "weight": 1.0},
            ],
            consensus_method="weighted"
        )

        # Stap 3: Neem beslissing op basis van consensus
        if validation.consensus_reached and validation.consensus_score > 0.85:
            # High confidence - automatisch actie
            await create_fix_task(quinn_review.finding, validation.final_answer)
        elif validation.consensus_score > 0.70:
            # Medium confidence - human review
            await create_review_task(quinn_review.finding, validation)
        else:
            # Low confidence - re-analyse nodig
            await schedule_re_analysis(quinn_review.finding)
```

---

### 1.5 Playwriter (Week 78) → Browser Automation

**Doel**: E2E tests automatiseren en UI-validatie.

| Workflow | Integratie | Voordeel |
|----------|------------|----------|
| **TESTING** | Tessa genereert E2E tests | Betere coverage |
| **BUG** | Betty reproduceert bugs | Visueel bewijs |
| **NEW_FEATURE** | Feature demo genereren | Stakeholder validatie |
| **QUALITY_AUDIT** | UI security tests | OWASP compliance |

```python
# TESTING workflow met Playwriter
async def testing_workflow(feature_id: int, test_type: str):
    # Stap 1: Tessa genereert test scenario's
    test_scenarios = await tessa.generate_test_scenarios(
        feature_id=feature_id,
        coverage_targets=["happy_path", "edge_cases", "error_handling"]
    )

    # Stap 2: Converteer naar Playwriter code
    for scenario in test_scenarios:
        playwright_code = await tessa.generate_playwright_code(scenario)

        # Stap 3: Execute via Playwriter
        result = await playwriter_service.execute(
            code=playwright_code,
            session_name=f"test-{feature_id}-{scenario.name}"
        )

        # Stap 4: Capture screenshot bij failure
        if not result.success:
            screenshot = await playwriter_service.screenshot()
            await create_bug_report(
                scenario=scenario,
                result=result,
                screenshot=screenshot
            )

    # Stap 5: Genereer test report
    report = await diana.generate_test_report(test_scenarios)
```

---

### 1.6 Git Worktrees (Week 79) → Parallel Development

**Doel**: Meerdere agents tegelijk aan dezelfde codebase laten werken.

| Workflow | Integratie | Voordeel |
|----------|------------|----------|
| **NEW_FEATURE** | Felix + Tessa parallel | 2x sneller |
| **MAINTENANCE** | Marcus + Quinn parallel | Complete audit |
| **MIGRATION** | Miguel + Betty parallel | Migration + testing |
| **BUG** | Betty + Tessa parallel | Fix + test tegelijk |

```python
# NEW_FEATURE met parallel worktrees
async def new_feature_parallel_workflow(feature_spec: str, project_id: int):
    # Stap 1: Maak worktrees voor beide agents
    felix_worktree = await worktree_service.create_worktree(
        agent_id="felix",
        base_branch="develop",
        project_id=project_id
    )

    tessa_worktree = await worktree_service.create_worktree(
        agent_id="tessa",
        base_branch="develop",
        project_id=project_id
    )

    # Stap 2: Parallel werk
    async with asyncio.TaskGroup() as tg:
        # Felix implementeert feature
        felix_task = tg.create_task(
            felix.implement_feature(
                spec=feature_spec,
                worktree=felix_worktree
            )
        )

        # Tessa schrijft tests (parallel!)
        tessa_task = tg.create_task(
            tessa.write_tests(
                spec=feature_spec,
                worktree=tessa_worktree
            )
        )

    # Stap 3: Merge Felix's werk eerst
    await worktree_service.merge_worktree(
        worktree_id=felix_worktree.id,
        target_branch="develop"
    )

    # Stap 4: Sync Tessa's worktree en valideer
    await worktree_service.sync_with_base(tessa_worktree.id)
    await tessa.validate_tests(worktree=tessa_worktree)

    # Stap 5: Merge tests
    await worktree_service.merge_worktree(
        worktree_id=tessa_worktree.id,
        target_branch="develop"
    )
```

---

### 1.7 GitHub Issues (Week 79) → External Sync

**Doel**: Bidirectionele sync tussen lokale taken en GitHub.

| Workflow | Integratie | Voordeel |
|----------|------------|----------|
| **BUG** | Auto-create GitHub issue | Transparency |
| **PROJECT_DEFINITION** | Epics → GitHub milestones | Planning sync |
| **MAINTENANCE** | Tech debt → issues | Backlog visibility |
| **ALL** | Progress tracking | Stakeholder updates |

```python
# BUG workflow met GitHub sync
async def bug_workflow(bug_report: str, project_id: int, github_repo: str):
    # Stap 1: Betty analyseert bug
    analysis = await betty.analyze_bug(bug_report)

    # Stap 2: Maak lokale taak
    local_task = await create_bug_task(
        title=analysis.title,
        description=analysis.root_cause,
        severity=analysis.severity
    )

    # Stap 3: Sync naar GitHub
    github_issue = await github_service.create_issue_from_task(
        task_id=local_task.id,
        task_type="bug",
        title=local_task.title,
        body=f"""
## Bug Report
{bug_report}

## Root Cause Analysis (Betty)
{analysis.root_cause}

## Proposed Fix
{analysis.proposed_fix}

## Affected Components
{', '.join(analysis.affected_components)}
        """,
        repo=github_repo,
        labels=["bug", analysis.severity]
    )

    # Stap 4: Link terug
    await local_task.update(github_url=github_issue.url)

    # Stap 5: Monitor voor updates
    await github_service.enable_sync_watching(
        repo=github_repo,
        issue_number=github_issue.number
    )
```

---

### 1.8 CCPM Orchestrator (Week 79) → PRD Decomposition

**Doel**: PRD's automatisch omzetten naar Epics → Features → Stories → Tasks.

| Workflow | Integratie | Voordeel |
|----------|------------|----------|
| **GREEN_PAPER** | PRD → complete breakdown | Snelle start |
| **PROJECT_DEFINITION** | Automatische schatting | Accurate planning |
| **NEW_FEATURE** | Feature → stories | Gedetailleerde specs |
| **ENHANCEMENT** | Enhancement → tasks | Granular tracking |

```python
# GREEN_PAPER workflow met CCPM
async def green_paper_workflow(prd_content: str, project_id: int):
    # Stap 1: Beantwoord 6 BMAD vragen
    bmad_answers = await peter.answer_bmad_questions(prd_content)

    # Stap 2: Decompose PRD
    decomposition = await ccpm_orchestrator.decompose_prd(
        title=bmad_answers.project_name,
        prd_content=prd_content,
        project_id=project_id,
        agent="peter"
    )

    # Stap 3: Genereer recommendations
    await ccpm_orchestrator.create_recommendations_from_decomposition(
        decomposition_id=decomposition.id
    )

    # Stap 4: Paul plant sprints
    sprint_plan = await paul.create_sprint_plan(
        epics=decomposition.epics,
        stories=decomposition.stories,
        total_story_points=decomposition.total_story_points
    )

    # Stap 5: Sync naar GitHub (optioneel)
    for epic in decomposition.epics:
        await github_service.create_issue_from_task(
            task_id=epic["id"],
            task_type="epic",
            title=epic["title"],
            body=epic["description"],
            repo=project.github_repo,
            labels=["epic"]
        )

    return {
        "decomposition": decomposition,
        "sprint_plan": sprint_plan,
        "next_task": await ccpm_orchestrator.get_next_task(project_id)
    }
```

---

## 2. Complete Workflow Integratie Matrix

| Workflow | CodeGraph | Claude-Mem | Layered | BigAGI | Playwriter | Worktrees | GitHub | CCPM |
|----------|-----------|------------|---------|--------|------------|-----------|--------|------|
| **GREEN_PAPER** | ⚪ | 🟢 | ⚪ | 🟢 | ⚪ | ⚪ | 🟢 | 🟢 |
| **BROWN_PAPER** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | ⚪ | 🟢 | 🟢 |
| **NEW_FEATURE** | 🟢 | 🟢 | ⚪ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| **BUG** | 🟢 | 🟢 | ⚪ | ⚪ | 🟢 | 🟢 | 🟢 | ⚪ |
| **MAINTENANCE** | 🟢 | 🟢 | ⚪ | ⚪ | ⚪ | 🟢 | 🟢 | ⚪ |
| **MIGRATION** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | 🟢 | 🟢 | 🟢 |
| **QUALITY_AUDIT** | 🟢 | 🟢 | ⚪ | 🟢 | 🟢 | ⚪ | 🟢 | ⚪ |
| **QUALITY_IMPROVEMENT** | 🟢 | 🟢 | ⚪ | 🟢 | ⚪ | 🟢 | 🟢 | ⚪ |
| **TESTING** | ⚪ | 🟢 | ⚪ | ⚪ | 🟢 | 🟢 | ⚪ | ⚪ |
| **ENHANCEMENT** | 🟢 | 🟢 | ⚪ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| **PROJECT_DEFINITION** | ⚪ | 🟢 | ⚪ | 🟢 | ⚪ | ⚪ | 🟢 | 🟢 |

**Legenda**: 🟢 = Primaire integratie, ⚪ = Optionele integratie

---

## 3. Implementatie Prioriteit

### Fase 1: Context & Memory (1-2 weken)
```
1. Claude-Mem integratie in ALLE workflows
   - Start elke workflow met context_window
   - Sla observaties op na elke agent beslissing
   - Implementeer progressive disclosure

2. CodeGraph integratie in MAINTENANCE
   - Impact analysis voor refactoring
   - Dependency tracking
```

### Fase 2: Validation & Quality (1-2 weken)
```
3. BigAGI integratie in QUALITY_* workflows
   - Multi-model validation voor critical findings
   - Consensus-based decision making

4. Playwriter integratie in TESTING
   - E2E test automation
   - Visual regression testing
```

### Fase 3: Parallel & External (1-2 weken)
```
5. Git Worktrees voor parallel development
   - NEW_FEATURE: Felix + Tessa parallel
   - BUG: Betty + Tessa parallel

6. GitHub sync voor externe visibility
   - Alle workflows met GitHub integration
   - Bidirectional sync
```

### Fase 4: PRD & Planning (1 week)
```
7. CCPM voor PRD decomposition
   - GREEN_PAPER met automatische breakdown
   - Task recommendations
```

---

## 4. Verwachte Verbeteringen

| Metriek | Huidige Situatie | Na Integratie | Verbetering |
|---------|------------------|---------------|-------------|
| **Context overhead** | 20K+ tokens per sessie | 4K tokens | 80% reductie |
| **Agent throughput** | 1 agent per taak | 2-3 agents parallel | 2-3x sneller |
| **Decision confidence** | Enkele LLM | Multi-model consensus | +40% accuracy |
| **Test coverage** | Handmatig | Geautomatiseerd | +60% coverage |
| **Stakeholder visibility** | Intern alleen | GitHub sync | 100% transparant |
| **PRD → Tasks** | Handmatig (dagen) | Automatisch (minuten) | 99% sneller |

---

## 5. Volgende Stappen

1. **Week 80**: Implementeer Claude-Mem in alle workflows
2. **Week 81**: BigAGI validatie voor QUALITY workflows
3. **Week 82**: Playwriter voor TESTING workflow
4. **Week 83**: Git Worktrees voor parallel development
5. **Week 84**: CCPM + GitHub sync voor GREEN_PAPER

---

**Auteur**: AI Agent Platform Team
**Status**: Proposal - Awaiting Approval
**Impact**: 11 workflows versterkt met 8 nieuwe tools
