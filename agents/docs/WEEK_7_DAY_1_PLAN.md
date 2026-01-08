# Week 7 Day 1: Spec-Kit Integration - Planning

**Date:** 15 november 2025
**Status:** IN PROGRESS
**Focus:** Spec-Kit Integration voor NEW_FEATURE workflow (Capability #1)

---

## Executive Summary

Week 7 focust op de integratie van **GitHub Spec Kit** in MarkdownTaskManager om de NEW_FEATURE workflow te automatiseren. Spec Kit biedt een structured approach voor spec-driven development die perfect align met onze Feature Architect agent (Felix).

**Key Integration:**
- Spec Kit's 5-phase workflow → Felix's NEW_FEATURE implementation
- CLI tool `specify` → TypeScript wrapper
- Automatic Epic → Feature → Story → Task breakdown
- Specification-first development (spec as source of truth)

---

## Spec Kit Overview

### Repository
- **Source:** https://github.com/github/spec-kit (Official GitHub tool)
- **Cloned to:** ~/Projects/spec-kit
- **CLI Tool:** `specify` (Python-based, uv installable)
- **Supported AI Agents:** Claude Code, GitHub Copilot, Gemini CLI, Cursor, +10 others

### Core Philosophy

> **"Code is no longer king - specifications are executable"**

Spec-Driven Development flips traditional software development:
- Specifications become **executable** (not just documentation)
- Code is **generated output** that serves the spec
- Explicit **checkpoints** for review and refinement at each phase

---

## Spec Kit 5-Phase Workflow

### Phase 1: `/speckit.constitution`
**Purpose:** Establish project principles and development guidelines

**Input:** High-level project governance requirements
**Output:** `.speckit/constitution.md` with:
- Code quality standards
- Testing requirements
- User experience principles
- Performance requirements
- Security guidelines

**Example:**
```bash
/speckit.constitution Create principles focused on code quality,
testing standards, user experience consistency, and performance requirements
```

**Mapping to MarkdownTaskManager:**
- This becomes **Project Definition** phase
- Stored in project metadata
- Used by all agents as guardrails

---

### Phase 2: `/speckit.specify`
**Purpose:** Define WHAT to build and WHY (not HOW)

**Input:** Feature description (user-focused, tech-agnostic)
**Output:** `.speckit/specifications/FEATURE_NAME.md` with:
- User scenarios
- Feature requirements
- Acceptance criteria
- Edge cases
- Non-functional requirements

**Example:**
```bash
/speckit.specify Build an application that can help me organize my photos
in separate photo albums. Albums are grouped by date and can be re-organized
by dragging and dropping on the main page. Albums are never in other nested
albums. Within each album, photos are previewed in a tile-like interface.
```

**Mapping to MarkdownTaskManager:**
- Creates **Epic** in our hierarchy
- Felix (Feature Architect) analyzes specification
- Eliza (Estimation Engine) calculates Function Points

---

### Phase 3: `/speckit.plan`
**Purpose:** Define HOW to build (tech stack + architecture)

**Input:** Technology choices, architecture decisions, constraints
**Output:** `.speckit/plans/FEATURE_NAME.md` with:
- Tech stack selection
- Architecture patterns
- Third-party library choices
- Data storage decisions
- API design
- Folder structure

**Example:**
```bash
/speckit.plan The application uses Vite with minimal number of libraries.
Use vanilla HTML, CSS, and JavaScript as much as possible. Images are not
uploaded anywhere and metadata is stored in a local SQLite database.
```

**Mapping to MarkdownTaskManager:**
- Breaks Epic into **Features**
- Each major component becomes a Feature
- Felix documents technical approach
- Quinn (Quality Inspector) reviews architecture

---

### Phase 4: `/speckit.tasks`
**Purpose:** Create actionable task list from implementation plan

**Input:** Plan from Phase 3
**Output:** `.speckit/tasks/FEATURE_NAME.md` with:
- Ordered task list
- Task descriptions
- Dependencies between tasks
- Acceptance criteria per task

**Example:**
```bash
/speckit.tasks
```

**Mapping to MarkdownTaskManager:**
- Creates **Stories** from Features
- Creates **Tasks** from Stories
- Eliza estimates Story Points per task
- Task dependencies mapped
- Sprint assignment suggested

---

### Phase 5: `/speckit.implement`
**Purpose:** Execute all tasks and build the feature

**Input:** Task list from Phase 4
**Output:** Working implementation with:
- Generated code
- Tests (if in constitution)
- Documentation
- Deployment configuration

**Example:**
```bash
/speckit.implement
```

**Mapping to MarkdownTaskManager:**
- Execution phase (not planning)
- KaibanJS orchestration kicks in
- Multiple agents collaborate:
  - Felix: Code generation
  - Tessa: Test generation
  - Quinn: Quality review
  - Diana: Documentation

---

## Integration Architecture

### Current State
```
MarkdownTaskManager
├── Backend (FastAPI) ✅
│   ├── 52 API endpoints
│   ├── PostgreSQL database
│   └── Alembic migrations
├── Agents Layer (KaibanJS) ✅
│   ├── 10 specialized agents
│   ├── Work type router
│   └── Workflow orchestration
└── Frontend (HTML/CSS/JS) ✅
    ├── Project viewer
    ├── Sprint planning
    └── Interactive dashboard
```

### Week 7 Addition: Spec Kit Integration

```
MarkdownTaskManager + Spec Kit
│
├── Spec Kit CLI (Python)
│   ├── specify init <project>
│   ├── specify check (tool validation)
│   └── Shell scripts (bash/powershell)
│
├── MarkdownTaskManager Integration Layer (NEW)
│   ├── TypeScript Wrapper (specKitRunner.ts)
│   │   ├── spawn('specify', [...args])
│   │   ├── Parse .speckit/ outputs
│   │   └── Return structured data
│   │
│   ├── Felix Agent Enhancement (configs/agents.ts)
│   │   ├── NEW_FEATURE workflow uses Spec Kit
│   │   ├── Phase 1-4: Planning
│   │   └── Phase 5: Hand off to execution agents
│   │
│   └── API Endpoints (app/main.py)
│       ├── POST /api/workflows/new-feature (initiate)
│       ├── GET /api/workflows/{id}/spec (get specification)
│       ├── GET /api/workflows/{id}/plan (get plan)
│       └── GET /api/workflows/{id}/tasks (get task list)
│
└── Database Extension (NEW)
    ├── Table: specifications (spec content)
    ├── Table: plans (technical plans)
    └── Table: spec_tasks (task breakdown before Epic creation)
```

---

## Week 7 Implementation Roadmap

### Day 1 (Today): Analysis & Planning
**Goals:**
- ✅ Clone spec-kit repository
- ✅ Analyze Spec Kit workflow
- ✅ Document 5-phase process
- 🔄 Create integration architecture plan
- 🔄 Define Felix enhancement strategy

**Deliverables:**
- WEEK_7_DAY_1_PLAN.md (this document)
- Integration architecture diagram
- Felix enhancement specification

---

### Day 2: CLI Installation & Testing
**Goals:**
- Install `specify` CLI tool
- Test all 5 phases manually
- Validate output formats
- Document CLI behavior

**Tasks:**
- [ ] `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
- [ ] Create test project: `specify init test-feature`
- [ ] Run all commands: constitution → specify → plan → tasks → implement
- [ ] Analyze generated `.speckit/` folder structure
- [ ] Document output schemas

**Deliverables:**
- Installed specify CLI
- Test project with all phases completed
- Output schema documentation

---

### Day 3: TypeScript Wrapper
**Goals:**
- Create specKitRunner.ts wrapper
- Implement CLI command execution
- Parse .speckit/ outputs
- Return structured JSON

**Tasks:**
- [ ] Create `backend/agents/integrations/specKitRunner.ts`
- [ ] Implement `runConstitution(projectPath, prompt)`
- [ ] Implement `runSpecify(projectPath, featureName, description)`
- [ ] Implement `runPlan(projectPath, featureName, techStack)`
- [ ] Implement `runTasks(projectPath, featureName)`
- [ ] Implement `runImplement(projectPath, featureName)` (optional - execution phase)
- [ ] Add file parsing utilities (read .speckit/*.md files)
- [ ] Create unit tests

**Deliverables:**
- specKitRunner.ts (300+ lines)
- Unit tests
- Integration test

---

### Day 4: Felix Agent Enhancement
**Goals:**
- Enhance Felix to use Spec Kit
- Create NEW_FEATURE workflow
- Integrate with KaibanJS
- Test agent coordination

**Tasks:**
- [ ] Update `backend/agents/configs/agents.ts` - Felix configuration
- [ ] Create new workflow: `backend/agents/workflows/newFeatureWorkflow.ts`
- [ ] Implement 4-phase planning loop:
  1. Constitution phase
  2. Specification phase
  3. Planning phase
  4. Task breakdown phase
- [ ] Add Epic/Feature/Story/Task creation after Phase 4
- [ ] Add Eliza (Estimation Engine) integration
- [ ] Test workflow with sample feature

**Deliverables:**
- Enhanced Felix agent
- NEW_FEATURE workflow (200+ lines)
- Integration with estimation

---

### Day 5: API Endpoints & Testing
**Goals:**
- Create FastAPI endpoints
- Database migrations for specs
- End-to-end testing
- Documentation

**Tasks:**
- [ ] Create database migration: `003_add_specifications.py`
  - Table: specifications
  - Table: plans
  - Table: spec_tasks
- [ ] Create API endpoints:
  - POST /api/workflows/new-feature
  - GET /api/workflows/{id}/spec
  - GET /api/workflows/{id}/plan
  - GET /api/workflows/{id}/tasks
- [ ] Create E2E test: full NEW_FEATURE flow
- [ ] Update API documentation (Swagger)
- [ ] Create WEEK_7_COMPLETE.md

**Deliverables:**
- 4 new API endpoints
- Database migrations
- E2E tests passing
- Week 7 completion documentation

---

## Felix Agent - NEW_FEATURE Workflow Design

### Current Felix Configuration
```typescript
const felix: Agent = {
  name: 'Felix',
  role: 'Feature Architect',
  goal: 'Design and specify new features with complete breakdown',
  backstory: 'Expert software architect with experience in feature design...',
  tools: [] // Currently empty
};
```

### Enhanced Felix with Spec Kit
```typescript
const felix: Agent = {
  name: 'Felix',
  role: 'Feature Architect',
  goal: 'Design features using spec-driven development methodology',
  backstory: `Expert software architect specializing in specification-first
    development. Uses GitHub Spec Kit to ensure features are thoroughly
    planned before implementation. Creates executable specifications that
    generate working code.`,
  tools: [
    specKitRunner.runConstitution,
    specKitRunner.runSpecify,
    specKitRunner.runPlan,
    specKitRunner.runTasks,
    elizaEstimator.calculateFunctionPoints,
    elizaEstimator.calculateStoryPoints
  ],
  workflow: 'NEW_FEATURE' // Links to newFeatureWorkflow.ts
};
```

### NEW_FEATURE Workflow Steps

```typescript
// backend/agents/workflows/newFeatureWorkflow.ts

export interface NewFeatureWorkflow {
  phase1: ConstitutionPhase;
  phase2: SpecificationPhase;
  phase3: PlanningPhase;
  phase4: TaskBreakdownPhase;
  phase5: EstimationPhase;
  phase6: EpicCreationPhase;
}

// Phase 1: Constitution (if new project)
async function constitutionPhase(input: WorkflowInput) {
  const result = await specKitRunner.runConstitution(
    input.projectPath,
    input.principles || DEFAULT_PRINCIPLES
  );

  return {
    constitution: result.content,
    path: result.filePath
  };
}

// Phase 2: Specification
async function specificationPhase(input: WorkflowInput) {
  const result = await specKitRunner.runSpecify(
    input.projectPath,
    input.featureName,
    input.description
  );

  // Parse specification output
  const spec = parseSpecification(result.content);

  return {
    epic: {
      title: input.featureName,
      description: spec.summary,
      acceptanceCriteria: spec.acceptanceCriteria,
      userScenarios: spec.scenarios
    },
    specPath: result.filePath
  };
}

// Phase 3: Planning
async function planningPhase(input: WorkflowInput) {
  const result = await specKitRunner.runPlan(
    input.projectPath,
    input.featureName,
    input.techStack || DEFAULT_TECH_STACK
  );

  // Parse plan output
  const plan = parsePlan(result.content);

  return {
    features: plan.components.map(component => ({
      title: component.name,
      description: component.purpose,
      technicalApproach: component.implementation
    })),
    planPath: result.filePath
  };
}

// Phase 4: Task Breakdown
async function taskBreakdownPhase(input: WorkflowInput) {
  const result = await specKitRunner.runTasks(
    input.projectPath,
    input.featureName
  );

  // Parse tasks output
  const taskList = parseTasks(result.content);

  return {
    stories: groupTasksIntoStories(taskList),
    tasks: taskList.map(task => ({
      title: task.title,
      description: task.description,
      dependencies: task.dependencies,
      acceptanceCriteria: task.acceptance
    })),
    tasksPath: result.filePath
  };
}

// Phase 5: Estimation (NEW - MarkdownTaskManager addition)
async function estimationPhase(workflow: WorkflowOutput) {
  // Epic level: Function Points
  const epicFP = await elizaEstimator.calculateFunctionPoints({
    specification: workflow.epic.description,
    components: workflow.features.length
  });

  // Feature level: Function Points
  const featureFP = await Promise.all(
    workflow.features.map(feature =>
      elizaEstimator.calculateFunctionPoints({
        specification: feature.description,
        approach: feature.technicalApproach
      })
    )
  );

  // Story level: Story Points
  const storyPoints = await Promise.all(
    workflow.stories.map(story =>
      elizaEstimator.calculateStoryPoints({
        tasks: story.tasks,
        complexity: story.complexity
      })
    )
  );

  return {
    epic: {
      ...workflow.epic,
      functionPoints: epicFP,
      tshirtSize: mapFPToTshirt(epicFP)
    },
    features: workflow.features.map((feature, idx) => ({
      ...feature,
      functionPoints: featureFP[idx]
    })),
    stories: workflow.stories.map((story, idx) => ({
      ...story,
      storyPoints: storyPoints[idx]
    }))
  };
}

// Phase 6: Epic Creation (Database persistence)
async function epicCreationPhase(workflow: WorkflowOutput) {
  // Create Epic in database
  const epic = await createEpic({
    title: workflow.epic.title,
    description: workflow.epic.description,
    functionPoints: workflow.epic.functionPoints,
    tshirtSize: workflow.epic.tshirtSize,
    specificationPath: workflow.specPath,
    planPath: workflow.planPath,
    tasksPath: workflow.tasksPath
  });

  // Create Features
  for (const feature of workflow.features) {
    const dbFeature = await createFeature({
      epicId: epic.id,
      title: feature.title,
      description: feature.description,
      functionPoints: feature.functionPoints
    });

    // Create Stories within Feature
    const featureStories = workflow.stories.filter(
      story => story.featureName === feature.title
    );

    for (const story of featureStories) {
      const dbStory = await createStory({
        featureId: dbFeature.id,
        title: story.title,
        description: story.description,
        storyPoints: story.storyPoints
      });

      // Create Tasks within Story
      for (const task of story.tasks) {
        await createTask({
          storyId: dbStory.id,
          title: task.title,
          description: task.description,
          acceptanceCriteria: task.acceptanceCriteria
        });
      }
    }
  }

  return epic;
}
```

---

## Success Criteria

### Week 7 Success Metrics

**Functional:**
- ✅ Spec Kit CLI installed and working
- ✅ TypeScript wrapper functional
- ✅ Felix agent uses Spec Kit for NEW_FEATURE
- ✅ Full workflow: description → Epic → Features → Stories → Tasks
- ✅ Estimation integrated (FP + SP)
- ✅ Database persistence working

**Quality:**
- ✅ TypeScript compilation: 0 errors
- ✅ Unit tests passing (specKitRunner)
- ✅ Integration test passing (E2E NEW_FEATURE)
- ✅ API endpoints functional (4 endpoints)

**Documentation:**
- ✅ Spec Kit integration guide
- ✅ Felix workflow documentation
- ✅ API documentation (Swagger)
- ✅ Week 7 completion report

---

## Risks & Mitigations

### Risk 1: Spec Kit CLI Dependency
**Risk:** Requires Python + uv tool chain
**Probability:** Low
**Impact:** Medium
**Mitigation:**
- Install specify CLI in project venv
- Test on multiple machines
- Document installation process clearly

### Risk 2: Output Parsing Complexity
**Risk:** .speckit/*.md files may have variable formats
**Probability:** Medium
**Impact:** Medium
**Mitigation:**
- Create robust parsing functions
- Use regex + markdown parsers
- Add validation and error handling
- Test with multiple feature types

### Risk 3: AI Agent Compatibility
**Risk:** Spec Kit designed for Claude Code/Copilot - may behave differently with our local Ollama models
**Probability:** Medium
**Impact:** High
**Mitigation:**
- Test with our local models first
- May need to adjust prompts
- Consider using cloud model (Claude) for Felix only
- Document model-specific behavior

### Risk 4: Integration Complexity
**Risk:** Multiple moving parts (CLI → TS → Agents → DB)
**Probability:** Low
**Impact:** High
**Mitigation:**
- Test each component individually
- Build integration incrementally
- Create comprehensive E2E test
- Daily check-ins with progress

---

## Next Steps (Day 1 - Today)

1. ✅ Complete this planning document
2. 🔄 Design Felix enhancement specification
3. ⏳ Create integration architecture diagram
4. ⏳ Document Day 1 completion

**Tomorrow (Day 2):**
- Install specify CLI
- Create test project
- Run all 5 phases
- Document outputs

---

**Document Owner:** Week 7 Integration Team
**Status:** IN PROGRESS - Day 1
**Next Review:** Day 2 (after CLI testing)
