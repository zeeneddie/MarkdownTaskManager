# Week 10 Implementation Plan: BMAD Green-Paper Workflow

**Target Dates**: December 23-29, 2025 (Christmas Week - Adjusted)
**Status**: Pre-work Complete ✅ | Ready for Implementation
**Branch**: `week-10-green-paper-workflow`
**Capacity**: 5 working days (avoiding Christmas holidays)

---

## 🎯 WEEK OBJECTIVES

Implement the **BMAD Green-Paper Workflow** for greenfield project creation:

1. ✅ **6-Question BMAD Session Interface** - Capture strategic project information
2. ✅ **Constitution → Specification Pipeline (Spec-Kit)** - Progressive elaboration
3. ✅ **Progressive Validation Checkpoints** - User reviews at each stage
4. ✅ **Peter + Felix Integration** - AI agents generate deliverables
5. ✅ **100% Local AI Execution** - All LLM calls via Ollama
6. ✅ **ChromaDB Semantic Search** - Find similar projects

---

## 📋 PRE-WORK STATUS (COMPLETED ✅)

### Files Created (8 total, ~3,500 lines):
- ✅ `app/api/week10/API_CONTRACTS.md` - 7 endpoints fully specified
- ✅ `app/api/week10/green_paper_routes.py` - FastAPI handlers (7 endpoints)
- ✅ `app/api/week10/README.md` - Implementation guide
- ✅ `app/services/week10/green_paper_service.py` - Business logic (15 methods)
- ✅ `agents/workflows/week10/greenPaperWorkflow.ts` - KaibanJS workflow (2 agents, 3 tasks)
- ✅ `agents/templates/week10/green_paper_template.md` - BMAD template + Peter's prompt
- ✅ `tests/api/week10/test_green_paper_api.py` - API tests (10 classes, 40+ cases)
- ✅ `tests/workflows/week10/test_green_paper_workflow.py` - Workflow tests (15 classes, 60+ cases)

### Directories Created (6):
- ✅ `app/api/week10/` (with __init__.py)
- ✅ `app/services/week10/` (with __init__.py)
- ✅ `agents/workflows/week10/`
- ✅ `agents/templates/week10/`
- ✅ `tests/api/week10/` (with __init__.py)
- ✅ `tests/workflows/week10/` (with __init__.py)

### Environment Setup:
- ✅ Python venv exists
- ✅ ML dependencies installed (chromadb, sentence-transformers, torch, transformers, numpy)
- 🔄 Docker services building (PostgreSQL, ChromaDB, Backend API)
- ✅ Ollama models ready (6/6: mistral, deepseek-r1, qwen2.5:7b, qwen2.5-coder:7b, codellama, llama3.2)

---

## 📅 DAY-BY-DAY IMPLEMENTATION PLAN

### 🗓️ MONDAY, DEC 23 (Day 1): Database Models + Migration

**Focus**: Create database schema for green-paper workflow

#### Morning (4h): Database Models
- [ ] Create `app/models/green_paper.py` with 4 models (2h)
  - `GreenPaperSession` - Session tracking with 6 answers
  - `Answer` - Individual question answers
  - `Constitution` - Generated constitutions (JSON + Markdown)
  - `Specification` - Generated specifications (JSON + Markdown)
- [ ] Add relationships and foreign keys (1h)
  - Session → Project (many-to-one)
  - Answer → Session (many-to-one)
  - Constitution → Session (one-to-one)
  - Specification → Constitution (one-to-one)
- [ ] Add validation constraints (1h)
  - Status enums (draft, in_progress, completed, approved, rejected)
  - Timestamps (created_at, updated_at, completed_at)
  - Metadata JSON fields

#### Afternoon (4h): Alembic Migration
- [ ] Create migration: `003_add_green_paper_tables.py` (1h)
  - Add 4 new tables
  - Add indexes on foreign keys
  - Add check constraints for status enums
- [ ] Test migration forward and backward (1h)
  ```bash
  alembic upgrade head
  alembic downgrade -1
  alembic upgrade head
  ```
- [ ] Verify database schema (1h)
  ```bash
  psql -h localhost -p 5433 -U user -d taskmanager
  \dt green_paper*
  \d green_paper_sessions
  ```
- [ ] Update model imports in `__init__.py` files (1h)

**Deliverables**:
- ✅ 4 database models defined
- ✅ Alembic migration tested
- ✅ Database schema verified

**Test Command**:
```bash
pytest tests/models/test_green_paper_models.py -v
```

---

### 🗓️ TUESDAY, DEC 24 (Day 2): Service Implementation (Part 1)

**Focus**: Implement core service methods

#### Morning (4h): Session Management
- [ ] Implement `start_session()` (2h)
  - Verify project exists and status = draft
  - Check no active session exists
  - Create session record
  - Return session + 6 BMAD questions
- [ ] Implement `get_session()` (1h)
  - Retrieve session with all answers
  - Calculate progress percentage
  - Return completion status
- [ ] Implement `get_questions()` - **Already done** ✅ (0h)

#### Afternoon (4h): Answer Management
- [ ] Implement `submit_answer()` (2h)
  - Validate question_number (1-6)
  - Validate answer length against max_length
  - Check required vs optional (Q1-4 required, Q5-6 optional)
  - Create or update answer record
  - Update session progress
  - Return progress information
- [ ] Implement `validate_answer()` - **Already done** ✅ (0h)
- [ ] Implement `check_session_complete()` (1h)
  - Verify Q1-4 all answered
  - Return true if ready for constitution generation
- [ ] Implement `calculate_progress()` (1h)
  - Count answered questions
  - Calculate percentage (0-100%)
  - Return detailed progress object

**Deliverables**:
- ✅ Session creation working
- ✅ Answer submission with validation
- ✅ Progress tracking accurate

**Test Command**:
```bash
pytest tests/api/week10/test_green_paper_api.py::TestGreenPaperSessionCreation -v
pytest tests/api/week10/test_green_paper_api.py::TestAnswerSubmission -v
```

---

### 🗓️ WEDNESDAY, DEC 25 (Day 3): Christmas - No Work

**Status**: Holiday - Team off

---

### 🗓️ THURSDAY, DEC 26 (Day 4): Service Implementation (Part 2) + Agent Workflow

**Focus**: Constitution generation + Peter integration

#### Morning (4h): Constitution Generation Service
- [ ] Implement `generate_constitution()` (3h)
  - Verify session complete (Q1-4 answered)
  - Retrieve all 6 answers
  - Format answers using `_format_answers_for_peter()`
  - Trigger green-paper workflow (KaibanJS)
  - Create constitution record (status: draft)
  - Return task_id and workflow info
- [ ] Implement `_format_answers_for_peter()` (1h)
  - Use template from `green_paper_template.md`
  - Inject 6 BMAD answers
  - Format for Peter's prompt

#### Afternoon (4h): Agent Workflow Implementation
- [ ] Complete `executeGreenPaperWorkflow()` in TypeScript (2h)
  - Set workflow inputs (6 BMAD answers)
  - Execute KaibanJS workflow
  - Return constitution JSON + Markdown
- [ ] Test Peter constitution generation (1h)
  - Create test session with sample answers
  - Trigger workflow
  - Verify constitution structure (7 sections)
  - Verify word count (1000-1500)
- [ ] Test Diana documentation formatting (1h)
  - Verify Markdown output
  - Verify executive summary

**Deliverables**:
- ✅ Constitution generation working
- ✅ Peter agent generates 1000-1500 word constitutions
- ✅ Diana agent formats documentation

**Test Command**:
```bash
pytest tests/workflows/week10/test_green_paper_workflow.py::TestPeterConstitutionGeneration -v
pytest tests/workflows/week10/test_green_paper_workflow.py::TestDianaDocumentation -v
```

---

### 🗓️ FRIDAY, DEC 27 (Day 5): API Integration + ChromaDB

**Focus**: Wire up API endpoints + semantic search

#### Morning (4h): API Endpoint Implementation
- [ ] Implement all 7 endpoint handlers (3h)
  - POST `/api/projects/{id}/green-paper/start` ✅ (boilerplate done)
  - POST `/api/projects/{id}/green-paper/{sid}/answer` ✅ (boilerplate done)
  - GET `/api/projects/{id}/green-paper/{sid}` ✅ (boilerplate done)
  - POST `/api/projects/{id}/green-paper/{sid}/generate-constitution` ✅ (boilerplate done)
  - GET `/api/projects/{id}/constitution` ✅ (boilerplate done)
  - POST `/api/projects/{id}/constitution/{cid}/review` ✅ (boilerplate done)
  - POST `/api/projects/{id}/specification/generate` ✅ (boilerplate done)
- [ ] Register router in `app/main.py` (1h)
  ```python
  from app.api.week10.green_paper_routes import router as green_paper_router
  app.include_router(green_paper_router)
  ```

#### Afternoon (4h): ChromaDB Integration
- [ ] Implement `store_constitution_embeddings()` (2h)
  - Extract text from constitution sections
  - Generate embeddings with sentence-transformers
  - Store in ChromaDB collection 'constitutions'
  - Store metadata (project_id, constitution_id, sections)
- [ ] Implement `search_similar_projects()` (1h)
  - Generate embedding for query
  - Search ChromaDB for top 5 similar constitutions
  - Return project info + similarity scores
- [ ] Test ChromaDB integration (1h)
  - Store test constitution
  - Search for similar
  - Verify results

**Deliverables**:
- ✅ All 7 API endpoints operational
- ✅ ChromaDB storing constitutions
- ✅ Semantic search working

**Test Command**:
```bash
curl -X POST http://localhost:8000/api/projects/{id}/green-paper/start
pytest tests/workflows/week10/test_green_paper_workflow.py::TestChromeDBIntegration -v
```

---

### 🗓️ SATURDAY, DEC 28 (Day 6): Testing + Documentation

**Focus**: Complete test coverage + documentation

#### Morning (4h): Testing
- [ ] Run all API tests (1h)
  - 10 test classes for API endpoints
  - 40+ test cases
  - Fix any failures
- [ ] Run all workflow tests (1h)
  - 15 test classes for workflows
  - 60+ test cases
  - Fix any failures
- [ ] Run E2E test (2h)
  - Complete flow: BMAD → Constitution → Review → Approve
  - Verify all database records created
  - Verify ChromaDB storage
  - Verify Ollama calls succeeded

#### Afternoon (4h): Documentation
- [ ] Update `PROJECT_STATUS_SUMMARY.md` (1h)
  - Mark Week 10 as complete
  - Update achievement percentage
  - Add Week 10 deliverables
- [ ] Update `app/api/week10/README.md` (1h)
  - Add actual implementation notes
  - Document known issues
  - Add usage examples with curl commands
- [ ] Create `WEEK_10_COMPLETE.md` (1h)
  - Summary of all deliverables
  - Test results (100+ tests passing)
  - Performance metrics (constitution generation time)
  - Next steps (Week 11)
- [ ] Update `ROADMAP.md` (1h)
  - Mark Week 10 as complete
  - Update Fase 3 progress

**Deliverables**:
- ✅ 100+ tests passing
- ✅ Complete documentation
- ✅ Ready for demo

**Test Command**:
```bash
pytest tests/api/week10/ -v --cov=app/api/week10 --cov=app/services/week10
pytest tests/workflows/week10/ -v
```

---

## 📊 SUCCESS METRICS

### Week 10 Completion Criteria:

**Backend**:
- ✅ 4 database models with migration
- ✅ 15 service methods implemented
- ✅ 7 API endpoints operational
- ✅ ChromaDB integration working

**Agents**:
- ✅ Peter generates 1000-1500 word constitutions
- ✅ Diana formats Markdown documentation
- ✅ 100% local AI execution (Ollama only)
- ✅ Constitution generation < 5 minutes

**Testing**:
- ✅ 100+ test cases passing
- ✅ E2E test: BMAD → Constitution complete
- ✅ API test coverage > 80%
- ✅ Workflow test coverage > 80%

**User Experience**:
- ✅ 6-question BMAD interface working
- ✅ Progressive validation (user reviews constitution)
- ✅ Semantic search finds similar projects
- ✅ Complete workflow < 30 minutes (user + AI time)

---

## 🔧 TECHNICAL STACK

**Backend**:
- FastAPI 0.104.1
- PostgreSQL 15
- asyncpg 0.29.0
- SQLAlchemy 2.0.23

**AI/ML**:
- Ollama (local LLM inference)
- Peter (deepseek-r1:latest) - Constitution generation
- Diana (mistral:latest) - Documentation
- ChromaDB 1.3.5 - Vector database
- sentence-transformers 5.1.2 - Embeddings (all-MiniLM-L6-v2)
- torch 2.9.1 - ML framework

**Agents**:
- KaibanJS - Workflow orchestration
- 2 agents active (Peter, Diana)
- 3 tasks sequential (Analyze → Generate → Format)

**Testing**:
- pytest 7.4.3
- pytest-asyncio 0.21.1
- pytest-cov 4.1.0

---

## 🚨 RISKS & MITIGATION

### Risk 1: Christmas Week Low Availability
**Impact**: Reduced working days (5 instead of 7)
**Mitigation**: Pre-work completed ahead of time (all boilerplate ready)

### Risk 2: First-Time ChromaDB Integration
**Impact**: Unknown complexity, could take longer
**Mitigation**: Allocate full Friday afternoon, have fallback (skip semantic search)

### Risk 3: Large Torch Package (~900MB)
**Impact**: Docker build slow, potential timeouts
**Mitigation**: Already installed in venv ✅, Docker caching will help

### Risk 4: Peter Constitution Quality
**Impact**: Generated constitutions may need iteration
**Mitigation**:
- Clear template with examples
- Max 3 regeneration attempts
- User can provide detailed feedback

---

## 📈 WEEK 10 DELIVERABLES SUMMARY

**Code**:
- 4 database models (~200 lines)
- 1 Alembic migration (~100 lines)
- 15 service methods (~800 lines)
- 7 API endpoints (already ~380 lines boilerplate)
- 1 KaibanJS workflow (already ~336 lines)
- **Total New Code**: ~1,400 lines

**Tests**:
- 100+ test cases
- E2E workflow test
- ChromaDB integration tests

**Documentation**:
- API contracts (already done ✅)
- Implementation guide (already done ✅)
- BMAD template (already done ✅)
- Week 10 completion summary

**Infrastructure**:
- Docker services (PostgreSQL, ChromaDB, API)
- Python venv with ML dependencies

---

## 🔄 NEXT STEPS (After Week 10)

### Week 11: Felix Specification Generation
- Felix receives approved constitutions
- Generates High-Level Design (HLD) specifications
- API contracts, data models, architecture diagrams
- User validation checkpoint

### Week 12: Task Generation + Sprint Planning
- Felix generates task hierarchy (Epics → Features → Stories)
- Paul creates sprint plans (2-week sprints)
- Resource allocation and capacity planning
- Complete Spec-Kit pipeline end-to-end

### Week 13+: UI Development
- `green-paper-wizard.html` - BMAD session UI
- `constitution-viewer.html` - Review and approve
- `spec-kit-dashboard.html` - Complete pipeline monitoring

---

## 📞 SUPPORT & ESCALATION

### Development Team
- **Lead**: Eddie
- **AI Assistant**: Claude Code
- **Agents**: Peter (Product Owner), Diana (Documentation)

### Critical Issues
- **Blocking Issues**: Escalate immediately via Slack
- **Docker Build Failures**: Check logs, retry with `--no-cache`
- **Ollama Connection**: Verify `ollama serve` running
- **ChromaDB Issues**: Check port 8001 accessibility

### Help Resources
- ARCHITECTURE.md - System architecture
- AGENTS.md - Agent specifications
- API_CONTRACTS.md - API documentation
- KaibanJS docs - Agent workflow framework

---

## ✅ CHECKLIST

### Pre-Implementation (Monday Morning)
- [ ] Docker services verified (PostgreSQL, ChromaDB, API)
- [ ] Ollama models verified (deepseek-r1, mistral)
- [ ] Python venv activated
- [ ] Git branch verified: `week-10-green-paper-workflow`
- [ ] All pre-work files present (8 files)

### During Implementation
- [ ] Day 1: Database models + migration ✅
- [ ] Day 2: Service implementation (Part 1) ✅
- [ ] Day 3: Christmas - Off
- [ ] Day 4: Service implementation (Part 2) + Workflow ✅
- [ ] Day 5: API integration + ChromaDB ✅
- [ ] Day 6: Testing + Documentation ✅

### Post-Implementation (Saturday Evening)
- [ ] All 100+ tests passing
- [ ] E2E test successful
- [ ] Documentation updated
- [ ] Demo prepared
- [ ] WEEK_10_COMPLETE.md created
- [ ] Ready for Week 11

---

**Created**: 2025-11-18
**Last Updated**: 2025-11-18
**Status**: ✅ Ready for Implementation (Pre-work Complete)
**Next Review**: Monday Dec 23, 2025 (Week 10 Start)
