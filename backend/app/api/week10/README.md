# Week 10: BMAD Green-Paper Workflow

**Target Start Date**: December 23, 2025 (5 weeks from now)
**Status**: Pre-work Complete ✅
**Branch**: `week-10-green-paper-workflow`

---

## 📋 Objectives

Implement the **BMAD Green-Paper Workflow** for greenfield project creation:

1. ✅ 6-Question BMAD Session Interface
2. ✅ Constitution → Specification Pipeline (Spec-Kit)
3. ✅ Progressive Validation Checkpoints
4. ✅ Integration with Peter (Product Owner) and Felix (Feature Architect)
5. ⏳ E2E Testing + Documentation

---

## 🎯 What We Deliver

### Core Features

1. **BMAD Session Interface**
   - 6 strategic questions for greenfield projects
   - Answer validation and progress tracking
   - Session state management

2. **Constitution Generation**
   - Peter (Product Owner) analyzes BMAD answers
   - Generates comprehensive project constitution
   - Structured output: Problem, Stakeholders, Functions, Criteria, Constraints, Timeline, Risks

3. **User Validation Checkpoint**
   - Review and approve/reject constitution
   - Request changes with specific feedback
   - Regeneration with user feedback (max 3 attempts)

4. **Specification Generation**
   - Felix (Feature Architect) receives approved constitution
   - Generates High-Level Design (HLD) specification
   - API contracts, data models, architecture

5. **ChromaDB Integration**
   - Store constitutions for semantic search
   - Find similar projects
   - 384-dimensional embeddings (all-MiniLM-L6-v2)

---

## 📁 Deliverables (Pre-work Complete)

### 1. API Contracts ✅
**File**: `API_CONTRACTS.md`

**7 Endpoints**:
- `POST /api/projects/{id}/green-paper/start` - Start session
- `POST /api/projects/{id}/green-paper/{sid}/answer` - Submit answer
- `GET /api/projects/{id}/green-paper/{sid}` - Get session status
- `POST /api/projects/{id}/green-paper/{sid}/generate-constitution` - Generate constitution
- `GET /api/projects/{id}/constitution` - Get constitution (JSON or Markdown)
- `POST /api/projects/{id}/constitution/{cid}/review` - Approve/reject
- `POST /api/projects/{id}/specification/generate` - Generate specification

**Data Models**:
- GreenPaperSession
- Answer
- Constitution
- ConstitutionReview
- Specification

**Validation Rules**:
- Project must be in `draft` status
- Only one active session per project
- Questions 1-4 required, 5-6 optional
- Sequential answer submission

### 2. Test Skeletons ✅
**Files**:
- `tests/api/week10/test_green_paper_api.py` - API endpoint tests (10 test classes)
- `tests/workflows/week10/test_green_paper_workflow.py` - Workflow integration tests (15 test classes)

**Coverage**:
- Session creation and management
- Answer submission and validation
- Constitution generation (Peter agent)
- Specification generation (Felix agent)
- User validation and review
- Agent collaboration
- ChromaDB integration
- Ollama local AI integration
- Performance and error handling

### 3. BMAD Template ✅
**File**: `agents/templates/week10/green_paper_template.md`

**Contents**:
- The 6 Strategic Questions (detailed guidance for each)
- User guidance with examples (✅ good / ❌ bad)
- Peter's Constitution Generation Prompt
- Constitution Template Structure (JSON)
- User Review Guidance
- Progressive Validation Checkpoint
- Best Practices

### 4. Service Layer ✅
**File**: `app/services/week10/green_paper_service.py`

**Class**: `GreenPaperService`

**Methods**:
- Session Management: `start_session()`, `get_session()`, `get_questions()`
- Answer Management: `submit_answer()`, `validate_answer()`
- Constitution: `generate_constitution()`, `get_constitution()`, `review_constitution()`
- Specification: `generate_specification()`
- ChromaDB: `store_constitution_embeddings()`, `search_similar_projects()`
- Helpers: `check_session_complete()`, `calculate_progress()`, `get_session_statistics()`

**Custom Exceptions**:
- `GreenPaperValidationError`
- `IncompleteSessionError`
- `InvalidStatusError`

### 5. API Routes ✅
**File**: `app/api/week10/green_paper_routes.py`

**FastAPI Router**: `/api/projects`

**Request Models** (Pydantic):
- `StartSessionRequest`
- `SubmitAnswerRequest`
- `GenerateConstitutionRequest`
- `ReviewConstitutionRequest`
- `GenerateSpecificationRequest`

**Features**:
- Request validation
- Error handling (400, 404, 422, 500)
- Async/await support
- Dependency injection
- OpenAPI documentation

### 6. Agent Workflow ✅
**File**: `agents/workflows/week10/greenPaperWorkflow.ts`

**Workflow**: Green-Paper Constitution Generation

**Agents**:
- Peter (Product Owner) - `deepseek-r1:latest`
- Diana (Documentation Writer) - `mistral:latest`

**Tasks**:
1. Analyze BMAD Answers (Peter)
2. Generate Constitution (Peter)
3. Format Documentation (Diana)

**Functions**:
- `executeGreenPaperWorkflow()` - Run workflow with BMAD answers
- `handleConstitutionValidation()` - Process user review

---

## 🏗️ Folder Structure

```
app/
├── api/
│   └── week10/
│       ├── __init__.py
│       ├── green_paper_routes.py      # FastAPI endpoints
│       ├── API_CONTRACTS.md           # API specification
│       └── README.md                  # This file
└── services/
    └── week10/
        ├── __init__.py
        └── green_paper_service.py     # Business logic

agents/
├── workflows/
│   └── week10/
│       └── greenPaperWorkflow.ts      # KaibanJS workflow
└── templates/
    └── week10/
        └── green_paper_template.md    # BMAD template

tests/
├── api/
│   └── week10/
│       ├── __init__.py
│       └── test_green_paper_api.py    # API tests
└── workflows/
    └── week10/
        ├── __init__.py
        └── test_green_paper_workflow.py  # Workflow tests
```

---

## 🔄 Workflow Sequence

### User Journey

```
1. User creates project (draft status)
   ↓
2. User starts green-paper session
   GET 6 BMAD questions
   ↓
3. User answers questions 1-6
   (1-4 required, 5-6 optional)
   Progress tracked: 0% → 16% → 33% → 50% → 67% → 83% → 100%
   ↓
4. User triggers constitution generation
   Peter (Product Owner) analyzes answers
   ↓
5. Peter generates constitution
   ~3-5 minutes (local AI)
   Output: 1000-1500 word structured document
   ↓
6. User reviews constitution
   Option A: APPROVE → Proceed to step 7
   Option B: REJECT → Peter regenerates (max 3 attempts) → Back to step 6
   ↓
7. User triggers specification generation
   Felix (Feature Architect) receives approved constitution
   ↓
8. Felix generates HLD specification
   ~5-10 minutes (local AI)
   Output: API contracts, data models, architecture
   ↓
9. User reviews specification
   Option A: APPROVE → Proceed to task generation
   Option B: REJECT → Felix regenerates → Back to step 9
   ↓
10. Felix generates tasks
    Epics → Features → User Stories
    ↓
11. Paul (Project Lead) creates sprint plan
    2-week sprints with capacity planning
```

### Agent Collaboration

```
Peter (Product Owner)
  ├─ Receives: 6 BMAD answers
  ├─ Analyzes: Problem, stakeholders, functions, criteria
  ├─ Generates: Project Constitution
  └─ Collaborates with: Diana (documentation)

Diana (Documentation Writer)
  ├─ Receives: Constitution from Peter
  ├─ Formats: Markdown documentation
  └─ Outputs: Full + Executive Summary

Felix (Feature Architect)
  ├─ Receives: Approved Constitution
  ├─ Generates: HLD Specification
  ├─ Creates: Epics, Features, Stories
  └─ Collaborates with: Diana, Paul

Paul (Project Lead)
  ├─ Receives: Tasks from Felix
  ├─ Creates: Sprint Plan
  └─ Outputs: Resource allocation, timeline
```

---

## 🔧 Implementation Checklist

### Week 10 Implementation Tasks

- [ ] **Database Models** (Day 1-2)
  - [ ] Create `GreenPaperSession` model
  - [ ] Create `Answer` model
  - [ ] Create `Constitution` model
  - [ ] Create `Specification` model
  - [ ] Create Alembic migration: `003_add_green_paper_tables.py`

- [ ] **Service Implementation** (Day 2-4)
  - [ ] Implement `start_session()`
  - [ ] Implement `submit_answer()` with validation
  - [ ] Implement `generate_constitution()` with Peter integration
  - [ ] Implement `review_constitution()`
  - [ ] Implement `generate_specification()` with Felix integration
  - [ ] Implement ChromaDB integration

- [ ] **API Implementation** (Day 3-4)
  - [ ] Wire up all 7 endpoints
  - [ ] Add to main FastAPI app
  - [ ] Test with Postman/curl

- [ ] **Agent Workflow** (Day 4-5)
  - [ ] Implement Peter constitution generation
  - [ ] Implement Diana documentation formatting
  - [ ] Add retry mechanism (max 3)
  - [ ] Add quality gates integration
  - [ ] Test with sample BMAD answers

- [ ] **Testing** (Day 5-6)
  - [ ] Implement all API test cases
  - [ ] Implement all workflow test cases
  - [ ] Run E2E test: Complete BMAD → Tasks flow
  - [ ] Verify ChromaDB storage
  - [ ] Verify Ollama local execution

- [ ] **Documentation** (Day 6)
  - [ ] Update main README
  - [ ] Create user guide for BMAD session
  - [ ] Document API with examples
  - [ ] Create demo video/screenshots

- [ ] **Optional Enhancements**
  - [ ] Add rate limiting middleware
  - [ ] Add webhook support for async events
  - [ ] Create frontend UI for BMAD session
  - [ ] Add analytics/metrics tracking

---

## 🧪 Testing Strategy

### Unit Tests
- Service methods (validation, logic)
- Answer validation rules
- Constitution generation logic

### Integration Tests
- API endpoints with database
- Agent workflow with Ollama
- ChromaDB storage and retrieval

### E2E Tests
1. Complete BMAD session (6 questions)
2. Constitution generation
3. User review (approve/reject)
4. Specification generation
5. Task generation

### Performance Tests
- Complete workflow < 30 minutes
- API response times < 2 seconds
- Concurrent session handling (10+)

---

## 🚀 Quick Start (After Implementation)

### 1. Start Services

```bash
# Terminal 1: Start Ollama (if not running)
ollama serve

# Terminal 2: Start Docker services
cd backend
docker-compose up -d

# Terminal 3: Start FastAPI
uvicorn app.main:app --reload
```

### 2. Create Project and Start Session

```bash
# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Greenfield Project",
    "status": "draft"
  }'

# Start green-paper session
curl -X POST http://localhost:8000/api/projects/{project_id}/green-paper/start \
  -H "Content-Type: application/json" \
  -d '{"session_type": "green-paper"}'
```

### 3. Submit Answers

```bash
# Answer question 1
curl -X POST http://localhost:8000/api/projects/{project_id}/green-paper/{session_id}/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question_number": 1,
    "answer": "This project solves the problem of..."
  }'

# Repeat for questions 2-6
```

### 4. Generate Constitution

```bash
curl -X POST http://localhost:8000/api/projects/{project_id}/green-paper/{session_id}/generate-constitution
```

---

## 📊 Success Metrics

- ✅ 6-question BMAD interface implemented
- ✅ Peter generates 1000-1500 word constitution
- ✅ Felix generates HLD specification
- ✅ Complete workflow < 30 minutes
- ✅ 100% local AI execution (no cloud APIs)
- ✅ All API tests passing (100+ test cases)
- ✅ E2E test: BMAD → Tasks workflow succeeds

---

## 🔗 Related Documentation

- **Project Status**: `/PROJECT_STATUS_SUMMARY.md`
- **Architecture**: `/ARCHITECTURE.md`
- **Roadmap**: `/ROADMAP.md` (Week 10 details)
- **Agents**: `/AGENTS.md` (Peter & Felix specifications)
- **Environment**: `/WEEK_10_ENVIRONMENT_STATUS.md`

---

**Last Updated**: 2025-11-18
**Status**: Pre-work Complete ✅ - Ready for Implementation
**Next Milestone**: Week 10 Implementation (December 23, 2025)
