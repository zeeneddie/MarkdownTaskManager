# 📅 UPDATED PLAN: Week 11-12 - Progressive Elaboration Implementation

**Status**: 📅 PLANNED (starts Dec 30, 2025)
**New Feature**: Progressive Elaboration Workflow (grof naar fijnmazig)
**Integration**: BMAD + Spec-Kit + Backlog Import

---

## 🎯 OVERVIEW WEEK 11-12

### Wat is er toegevoegd?
**Progressive Elaboration Workflow** - Van grof naar fijnmazig met continue gebruikersvalidatie:

```
Roadmap → Fasenplan → Fase Detail → Week Detail → Epics → Features/Stories/Tasks
   ↓          ↓            ↓              ↓           ↓              ↓
 Validatie  Validatie   Validatie     Validatie   Validatie     Validatie
```

**Plus voor bestaande projecten**:
- Backlog import (CSV/JSON/Markdown)
- Bugfix lijst import (Jira/GitHub/CSV)
- AI classificatie (Epic/Feature/Story/Task)
- Merge met quality scan results

---

## 📅 WEEK 11 (Dec 30-Jan 5): BROWN_PAPER + Backlog Import

**Nieuwjaarsweek - Reduced Capacity**

### Doelen (aangepast)
1. ✅ BROWN_PAPER workflow (brownfield) - **OORSPRONKELIJK**
2. 🆕 Backlog import functionality - **NIEUW**
3. 🆕 Bug list import functionality - **NIEUW**
4. 🆕 AI classificatie engine - **NIEUW**

### Target: ~2,200 lines (was 1,800 - +400 voor import features)

---

### Monday-Tuesday (Days 1-2) - 16h
**Focus**: BROWN_PAPER Workflow + Quality Scan Integration

#### Oorspronkelijk Plan (blijft staan)
**Task 1**: Quality Scan Automation (6h)
- [ ] Integrate 7 quality gates into brown-paper flow
- [ ] Pre-populate brown-paper form with scan results
- [ ] Tech debt detection
- [ ] Security vulnerability mapping
- [ ] Code smell categorization

**Task 2**: BMAD Brown-Paper Facilitator (6h)
- [ ] Create brown-paper session interface (if UI)
- [ ] 7 structured questions (vs 6 for green-paper):
  1. Current Architecture
  2. Technical Debt Assessment
  3. Security Concerns
  4. What to Preserve
  5. What to Improve
  6. Migration Strategy
  7. Risks & Dependencies

**Task 3**: Integration Tests (4h)
- [ ] E2E test: Quality scan → Brown-paper → Spec-Kit
- [ ] Validation tests

**Deliverable**: Brown-paper workflow operational

---

### Wednesday (Day 3) - 8h
**Focus**: 🆕 Backlog Import Infrastructure

#### NEW: Import Endpoints

**Task 1**: Backlog Import API (4h)
**File**: `backend/app/api/import.py`

```python
@router.post("/api/projects/{project_id}/import/backlog")
async def import_backlog(
    project_id: int,
    file: UploadFile,
    format: str,  # csv, json, markdown
    mapping: dict  # column name mapping
):
    """
    Import existing backlog from various formats

    Supports:
    - CSV (comma-separated)
    - JSON (array of objects)
    - Markdown (checklist format)

    Returns classified items (Epics, Features, Stories, Tasks)
    """
    # 1. Parse file based on format
    items = await parse_backlog_file(file, format, mapping)

    # 2. AI Classification (Felix agent)
    classified = await classify_backlog_items(items)

    # 3. Store in database + ChromaDB
    await store_backlog(project_id, classified)

    # 4. Return for user validation
    return {
        "total_items": len(items),
        "epics": classified["epics"],
        "features": classified["features"],
        "stories": classified["stories"],
        "tasks": classified["tasks"],
        "validation_needed": True
    }
```

**Task 2**: File Parsers (4h)
**File**: `backend/app/services/import_service.py`

```python
async def parse_csv_backlog(file: UploadFile, mapping: dict):
    """Parse CSV backlog file"""
    # pandas or csv.DictReader

async def parse_json_backlog(file: UploadFile):
    """Parse JSON backlog file"""

async def parse_markdown_backlog(file: UploadFile):
    """Parse Markdown checklist backlog"""
    # - [ ] Epic 1: User Management
    # - [ ] Feature 1.1: Registration
```

**Deliverable**: Backlog import working for 3 formats

---

### Thursday (Day 4) - 8h
**Focus**: 🆕 Bug List Import + AI Classification

**Task 1**: Bug Import API (3h)
**File**: `backend/app/api/import.py` (extend)

```python
@router.post("/api/projects/{project_id}/import/bugs")
async def import_bugs(
    project_id: int,
    file: UploadFile,
    format: str,  # jira, github, csv
    mapping: dict
):
    """
    Import bug tracker exports

    Supports:
    - Jira export (JSON/CSV)
    - GitHub Issues export (JSON)
    - Generic CSV

    Returns prioritized bug list
    """
    # 1. Parse bugs
    bugs = await parse_bug_file(file, format, mapping)

    # 2. AI Analysis (Betty + Quinn)
    analyzed = await analyze_bugs(bugs)

    # 3. Prioritize (Critical → High → Medium → Low)
    prioritized = await prioritize_bugs(analyzed)

    # 4. Convert to work items (Stories/Tasks)
    work_items = await bugs_to_work_items(prioritized)

    return {
        "total_bugs": len(bugs),
        "critical": prioritized["critical"],
        "high": prioritized["high"],
        "medium": prioritized["medium"],
        "low": prioritized["low"],
        "work_items_created": len(work_items)
    }
```

**Task 2**: AI Classification Engine (5h)
**File**: `backend/agents/commands/classifyBacklogCommand.ts`

```typescript
// Felix agent classifies backlog items
interface BacklogItem {
  title: string;
  description: string;
  priority?: string;
  status?: string;
}

interface ClassifiedItem {
  original: BacklogItem;
  type: 'epic' | 'feature' | 'story' | 'task';
  confidence: number;
  reasoning: string;
  suggested_story_points: number;  // TBD - for Planning Poker
}

async function classifyBacklogItems(
  items: BacklogItem[]
): Promise<ClassifiedItem[]> {
  // Use Felix (Feature Architect) to analyze each item

  // Rules:
  // - Large scope, multiple features → Epic
  // - Medium scope, user-facing capability → Feature
  // - Small scope, single user flow → Story
  // - Technical task, no user value → Task

  // Consider:
  // - Title length and complexity
  // - Description detail level
  // - Existing priority
  // - Dependencies mentioned
}
```

**Deliverable**: Bug import + AI classification operational

---

### Friday (Day 5) - 8h
**Focus**: Testing, Documentation, Integration

**Task 1**: E2E Tests (4h)
```python
def test_import_csv_backlog():
    """Test CSV backlog import and classification"""

def test_import_jira_bugs():
    """Test Jira bug import and prioritization"""

def test_merge_backlog_and_bugs():
    """Test merging imported backlog with bug list"""

def test_brownfield_complete_flow():
    """Test: Quality scan → Brown-paper → Import backlog → Import bugs → Merged backlog"""
```

**Task 2**: Documentation (2h)
- Update BMAD_INTEGRATION_GUIDE.md (brown-paper flow)
- Update PROGRESSIVE_ELABORATION_WORKFLOW.md (import section)
- Create WEEK_11_SUMMARY.md

**Task 3**: Integration with Week 10 (2h)
- Verify GREEN_PAPER + BROWN_PAPER both work
- Test greenfield vs brownfield flows
- Ensure ChromaDB storage consistent

**Deliverable**: Week 11 complete, tested, documented

---

## 📅 WEEK 12 (Jan 6-12): Progressive Elaboration Implementation

**Doel**: Implementeer complete 7-stappen verfijning workflow

### Target: ~2,400 lines (was 1,800 - +600 voor Progressive Elaboration)

---

### Monday (Day 1) - 8h
**Focus**: Stap 1-2 Implementation (Roadmap + Fasenplan)

**Task 1**: Roadmap Generator (4h)
**File**: `backend/agents/commands/generateRoadmapCommand.ts`

```typescript
// Paul (Project Lead) generates 40-week roadmap from BMAD session
interface RoadmapInput {
  bmad_session_id: string;
  total_weeks: number;
  key_milestones: string[];
  project_type: 'greenfield' | 'brownfield';
}

interface RoadmapOutput {
  phases: Phase[];  // 9 phases
  milestones: Milestone[];  // Major milestones
  risks: Risk[];
  dependencies: Dependency[];
  timeline: TimelineEntry[];
}

async function generateRoadmap(input: RoadmapInput): Promise<RoadmapOutput> {
  // Use Paul agent to analyze BMAD session
  // Extract key components from green/brown-paper
  // Generate phase breakdown (Fase 1-9)
  // Identify major milestones
  // Map risks from BMAD
}
```

**Task 2**: Fasenplan Generator (4h)
**File**: `backend/agents/commands/generateFasenplanCommand.ts`

```typescript
// Paul generates detailed phase plan
interface FasenplanInput {
  roadmap: RoadmapOutput;
  roadmap_validated: boolean;  // User confirmation
}

interface FasenplanOutput {
  phases: DetailedPhase[];  // Each phase with week breakdown
  effort_distribution: EffortDistribution;
  dependencies: PhaseDependency[];
}

async function generateFasenplan(input: FasenplanInput): Promise<FasenplanOutput> {
  // For each phase in roadmap
  // Break down into weeks
  // Estimate effort per week
  // Identify dependencies between phases
}
```

**Deliverable**: Roadmap + Fasenplan generators working

---

### Tuesday (Day 2) - 8h
**Focus**: Stap 3-4 Implementation (Fase Detail + Week Detail)

**Task 1**: Fase Detail Planner (4h)
**File**: `backend/agents/commands/generateFaseDetailCommand.ts`

```typescript
// Felix + Paul generate week-by-week breakdown per fase
interface FaseDetailInput {
  fase: DetailedPhase;
  fasenplan_validated: boolean;
}

interface FaseDetailOutput {
  weeks: WeekPlan[];  // Day-by-day for each week
  deliverables: Deliverable[];
  validation_checkpoints: ValidationCheckpoint[];
}
```

**Task 2**: Week Detail Planner (4h)
**File**: `backend/agents/commands/generateWeekDetailCommand.ts`

```typescript
// Felix generates hour-level planning
interface WeekDetailInput {
  week: WeekPlan;
  fase_detail_validated: boolean;
}

interface WeekDetailOutput {
  days: DayPlan[];  // Hour-by-hour schedule
  tasks: Task[];
  subtasks: Subtask[];
}
```

**Deliverable**: Fase + Week planners working

---

### Wednesday (Day 3) - 8h
**Focus**: Stap 5-6 Implementation (Epics + WBS)

**Task 1**: Epic Generator (4h)
**File**: `backend/agents/commands/generateEpicsCommand.ts`

```typescript
// Felix + Peter generate High Level Design
interface EpicGeneratorInput {
  specification: SpecificationResult;  // From Spec-Kit
  week_planning_validated: boolean;
}

interface EpicGeneratorOutput {
  epics: Epic[];  // High-level business capabilities
  acceptance_criteria: AcceptanceCriteria[];
  user_personas: UserPersona[];
}
```

**Task 2**: WBS Generator (4h)
**File**: `backend/agents/commands/generateWBSCommand.ts`

```typescript
// Felix + Tessa generate complete Work Breakdown Structure
interface WBSInput {
  epics: Epic[];
  epics_validated: boolean;
}

interface WBSOutput {
  features: Feature[];  // Per epic
  stories: UserStory[];  // Per feature
  tasks: Task[];  // Per story
  actions: Action[];  // Per task (micro-level)
}
```

**Deliverable**: Epic + WBS generators working

---

### Thursday (Day 4) - 8h
**Focus**: Stap 7 + API Integration

**Task 1**: Planning Poker Support (3h)
**File**: `backend/agents/commands/planningPokerSupportCommand.ts`

```typescript
// Eliza provides story point suggestions (team still decides)
interface PlanningPokerInput {
  story: UserStory;
  historical_data: HistoricalEstimate[];  // From ChromaDB
}

interface PlanningPokerOutput {
  suggested_points: number;  // Fibonacci
  confidence: number;  // 0-100%
  similar_stories: UserStory[];  // From past projects
  reasoning: string;
}
```

**Task 2**: Progressive Elaboration API Endpoints (5h)
**File**: `backend/app/api/progressive_elaboration.py`

```python
# 7 endpoints for 7 steps
@router.post("/api/projects/{id}/progressive-elaboration/roadmap")
@router.post("/api/projects/{id}/progressive-elaboration/fasenplan")
@router.post("/api/projects/{id}/progressive-elaboration/fase-detail/{fase_id}")
@router.post("/api/projects/{id}/progressive-elaboration/week-detail/{week_id}")
@router.post("/api/projects/{id}/progressive-elaboration/epics")
@router.post("/api/projects/{id}/progressive-elaboration/wbs")
@router.post("/api/projects/{id}/progressive-elaboration/planning-poker")

# Plus validation endpoints
@router.put("/api/projects/{id}/progressive-elaboration/validate/{step}")
```

**Deliverable**: Complete API for Progressive Elaboration

---

### Friday (Day 5) - 8h
**Focus**: E2E Testing + Documentation + Integration

**Task 1**: E2E Tests (4h)
```python
def test_progressive_elaboration_greenfield():
    """
    Test complete flow:
    1. Create greenfield project
    2. Green-paper session
    3. Generate roadmap → validate
    4. Generate fasenplan → validate
    5. Generate fase detail → validate
    6. Generate week detail → validate
    7. Generate epics → validate
    8. Generate WBS → validate
    9. Planning poker → finalize
    """

def test_progressive_elaboration_brownfield():
    """
    Test brownfield flow with:
    - Quality scan
    - Brown-paper session
    - Import existing backlog
    - Import bug list
    - Merge & prioritize
    - Progressive elaboration from step 5 (epics)
    """

def test_validation_checkpoints():
    """Test user can reject at any step and refine"""
```

**Task 2**: Documentation (3h)
- Create WEEK_12_SUMMARY.md
- Update PROJECT_STATUS_SUMMARY.md (Fase 3 complete!)
- Update PROGRESSIVE_ELABORATION_WORKFLOW.md (status: implemented)
- Update BMAD_INTEGRATION_GUIDE.md (complete integration)

**Task 3**: Fase 3 Retrospective (1h)
- Review Weeks 10-12 achievements
- Identify learnings
- Plan improvements for Fase 4

**Deliverable**: Fase 3 COMPLETE ✅

---

## 📊 UPDATED METRICS

### Week 11 Targets
| Metric | Original | Updated | Reason |
|--------|----------|---------|--------|
| Lines | 1,800 | 2,200 | +400 for import features |
| Features | 1 (Brown-paper) | 4 | +Backlog +Bugs +Classification |
| Endpoints | 2 | 6 | +Import APIs |

### Week 12 Targets
| Metric | Original | Updated | Reason |
|--------|----------|---------|--------|
| Lines | 1,800 | 2,400 | +600 for 7-step workflow |
| Features | 1 (Estimation) | 7 | 7 Progressive Elaboration steps |
| Endpoints | 3 | 10 | 7 steps + 3 validation |

### Fase 3 Total (Weeks 9-12)
| Metric | Original Plan | Actual/Expected |
|--------|---------------|-----------------|
| Weeks | 4 | 4 ✅ |
| Total Lines | 7,200 | ~10,269 (+42%) |
| Major Features | 4 | 12 (+200%) |
| API Endpoints | 8 | 26 (+225%) |

**Achievement**: Massive overdelivery expected (consistent with Weeks 8-9 pattern)

---

## 🎯 SUCCESS CRITERIA (UPDATED)

### Week 11
- ✅ Brown-paper workflow operational
- ✅ CSV backlog import working
- ✅ JSON backlog import working
- ✅ Markdown backlog import working
- ✅ Jira bug import working
- ✅ GitHub bug import working
- ✅ AI classification ≥80% accuracy
- ✅ E2E test: Brownfield complete flow
- ✅ 0 TypeScript errors
- ✅ All tests passing

### Week 12
- ✅ 7-step Progressive Elaboration workflow complete
- ✅ Roadmap generator working
- ✅ Fasenplan generator working
- ✅ Fase detail planner working
- ✅ Week detail planner working
- ✅ Epic generator working
- ✅ WBS generator working
- ✅ Planning Poker support working
- ✅ Validation checkpoints functional
- ✅ E2E test: Greenfield + Brownfield full flows
- ✅ Integration with BMAD + Spec-Kit seamless
- ✅ 0 TypeScript errors
- ✅ All tests passing
- ✅ Documentation complete

---

## 🔗 INTEGRATION OVERVIEW

```
┌──────────────────────────────────────────────────────────────┐
│                    COMPLETE PROJECT INTAKE                    │
└──────────────────────────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
         GREENFIELD                    BROWNFIELD
              │                             │
              ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │  Green-Paper    │          │  Quality Scan   │
     │  (Week 10)      │          │  (5-15 min)     │
     └────────┬────────┘          └────────┬────────┘
              │                             │
              │                             ▼
              │                    ┌─────────────────┐
              │                    │  Brown-Paper    │
              │                    │  (Week 11)      │
              │                    │  +              │
              │                    │  Import Backlog │
              │                    │  Import Bugs    │
              │                    └────────┬────────┘
              │                             │
              └──────────────┬──────────────┘
                             ▼
              ┌──────────────────────────────┐
              │  Progressive Elaboration     │
              │  (Week 12)                   │
              │                              │
              │  Step 1: Roadmap             │
              │     ↓ Validate ✓             │
              │  Step 2: Fasenplan           │
              │     ↓ Validate ✓             │
              │  Step 3: Fase Detail         │
              │     ↓ Validate ✓             │
              │  Step 4: Week Detail         │
              │     ↓ Validate ✓             │
              │  Step 5: Epics (HLD)         │
              │     ↓ Validate ✓             │
              │  Step 6: WBS (LLD)           │
              │     ↓ Validate ✓             │
              │  Step 7: Planning Poker      │
              │     ↓ Finalize ✓             │
              └──────────────┬───────────────┘
                             ▼
              ┌──────────────────────────────┐
              │  Spec-Kit Workflow           │
              │  (Week 8 - reuse)            │
              │                              │
              │  Constitution → Spec → Tasks │
              └──────────────┬───────────────┘
                             ▼
              ┌──────────────────────────────┐
              │  5 Files Generated           │
              │  + ChromaDB Storage          │
              └──────────────┬───────────────┘
                             ▼
              ┌──────────────────────────────┐
              │  Project Status: ACTIVE      │
              │  Ready for Sprint Execution  │
              └──────────────────────────────┘
```

---

## 📚 DELIVERABLES SUMMARY

### Week 11 Deliverables
1. Brown-paper workflow (TypeScript + Python)
2. Backlog import service (3 formats)
3. Bug import service (3 formats)
4. AI classification engine
5. E2E tests (brownfield flow)
6. Documentation (WEEK_11_SUMMARY.md, guides updated)

### Week 12 Deliverables
1. Roadmap generator
2. Fasenplan generator
3. Fase detail planner
4. Week detail planner
5. Epic generator (HLD)
6. WBS generator (LLD)
7. Planning Poker support
8. Progressive Elaboration API (10 endpoints)
9. Validation system
10. E2E tests (complete flows)
11. Documentation (WEEK_12_SUMMARY.md, Fase 3 retro)

---

## 🚀 NEXT PHASE PREVIEW

### Fase 4 (Weeks 13-16): UI + Estimation
With Progressive Elaboration complete, Week 14's Spec-Kit Wizard will be enhanced:

**Original Week 14 Plan**:
- Spec-Kit Wizard (Constitution → Spec → Tasks)

**Updated Week 14 Plan**:
- Spec-Kit Wizard WITH Progressive Elaboration:
  - Step-by-step wizard (7 steps)
  - Validation checkpoints visible
  - Real-time refinement
  - Progress indicator
  - Can go back/forward between steps
  - "Skip to final" option for experienced users

**Result**: Complete project intake via UI! 🎉

---

**Status**: 📅 READY FOR WEEK 11 (starts Dec 30)
**Next Action**: Start BROWN_PAPER workflow + Backlog import
**Impact**: Project intake becomes 10x more powerful with Progressive Elaboration!

---

**Last Updated**: 2025-11-18
**Author**: Eddie + Claude Code
**Version**: 2.0 (with Progressive Elaboration)
