from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.api import epics, features, stories, tasks, sprints, auth, project, workflows, projects, scheduler, estimation, estimation_history, project_wizard, websocket, maintenance, ml_training, evolution, quality_dashboard, self_navigating, attribution, task_generation, continuous_learning, rollback, quality_gate_config, quality_gate_evaluation, agent_validation, ab_testing, llm_council, evolution_dashboard, spec_review, observability, council_human_review, stack_agents, project_registration, application_registry, test_organization, brown_paper, fp_estimation, hci_crs_knowledge, kanban, standards, spec_shaping, quick_spec, improve_skills, spec_verification, cctrace, codewiki, knowledge, knowledge_graph, security, rl_training, migration_analyzer, migration_security, migration_estimation, migration_architecture, migration_report, project_workflows, workflow_dashboard, mcp_proxy, anytool, memmachine, code_graph, claude_mem, layered_analysis, playwriter, bigagi, ccpm, ghostcrew, deep_extraction, graph_workflow, debt_categorization, code_analysis, hierarchical_extraction, rerun_upgrade, portal_features, portal_roadmap, harness, design, static_analysis, devops_analysis, orchestration, traceability, hybrid_extraction, requirements, portal_boost, portal_engagement, causality, metrics, migration_enhanced, week131_research, week132_dead_code, week134_testing, week131_transformation, data_architecture, migration_execution, decision_tables, state_machine_extraction, authorization_matrix, api_inventory, customers, codecharta, token_context, project_intake, stability
from app.api.week10 import green_paper_routes
from app.api.week11 import task_generation_routes
from app.database import engine
from app.models.item import Base as ItemBase
from app.models.sprint import Base as SprintBase
from app.models.user import Base as UserBase
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # === STARTUP ===
    # NOTE: Table creation is handled by Alembic migrations in docker-entrypoint.sh
    # DO NOT use create_all() here - it conflicts with migration versioning
    print("✅ Database tables managed by Alembic migrations")

    # Start scheduler for periodic maintenance
    from app.services.scheduler_service import get_scheduler
    scheduler_instance = get_scheduler()
    scheduler_instance.start()
    print("✅ Maintenance scheduler started")

    # Initialize Agent Harness Framework (Week 91-93)
    try:
        from app.harness import registry, ModuleType
        from app.harness.adapters import (
            MarQedConstraintManager,
            MarQedContextManager,
            MarQedToolRegistry,
            MarQedVersionTracker,
        )

        # Register and mount default adapters
        registry.register_adapter("marqed", MarQedConstraintManager, ModuleType.CONSTRAINTS, {"version": "1.0"})
        registry.register_adapter("marqed", MarQedContextManager, ModuleType.CONTEXT, {"version": "1.0"})
        registry.register_adapter("marqed", MarQedToolRegistry, ModuleType.TOOLS, {"version": "1.0"})
        registry.register_adapter("marqed", MarQedVersionTracker, ModuleType.VERSIONING, {"version": "1.0"})

        registry.mount(ModuleType.CONSTRAINTS, "marqed")
        registry.mount(ModuleType.CONTEXT, "marqed")

        # Mount tools with constraint manager integration
        constraint_mgr = registry.get(ModuleType.CONSTRAINTS)
        registry.mount(ModuleType.TOOLS, "marqed", {"constraint_manager": constraint_mgr})

        # Mount version tracker
        registry.mount(ModuleType.VERSIONING, "marqed")

        print("✅ Agent Harness Framework initialized (Constraints + Context + Tools + Versioning)")
    except Exception as e:
        print(f"⚠️ Agent Harness initialization failed: {e}")

    print("✅ Database tables created successfully (including Week 10-11, Week 15-16 ML)")
    print("📚 API Documentation: http://localhost:8000/api/docs")
    print("🤖 AI Workflows: http://localhost:8000/api/workflows/work-types")
    print("📅 Scheduler API: http://localhost:8000/api/scheduler/status")
    print("🔌 WebSocket: ws://localhost:8000/ws/maintenance (real-time updates)")
    print("🧠 ML Training: http://localhost:8000/api/ml/status")

    yield  # Application runs here

    # === SHUTDOWN ===
    # Stop scheduler
    from app.services.scheduler_service import get_scheduler
    scheduler_instance = get_scheduler()
    scheduler_instance.shutdown()
    print("🛑 Maintenance scheduler stopped")

    await engine.dispose()
    print("👋 Database connections closed")


app = FastAPI(
    title="Project Manager API",
    description="Hierarchical project management API with Sprint support",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS middleware - use wildcard for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(project.router)
app.include_router(epics.router, prefix="/api")
app.include_router(features.router, prefix="/api")
app.include_router(stories.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(sprints.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
# Active routers (Week 48 - OpenAPI schema bugs fixed)
app.include_router(estimation.router, prefix="/api")  # Week 13: Function Point Calculator
app.include_router(estimation_history.router, prefix="/api")  # Week 15: ML Training Data Collection
app.include_router(project_wizard.router)  # Week 15: Project Wizard
app.include_router(quality_dashboard.router)  # Week 18: OpenAPI + DB column mapping FIXED
app.include_router(continuous_learning.router)  # Week 25-26: Continuous Learning (not in OpenAPI docs)
# Disabled routers (require additional services)
app.include_router(maintenance.router)  # Week 15: Marcus maintenance agent
app.include_router(ml_training.router)  # Week 16: ML training pipeline
app.include_router(evolution.router)  # Week 17: Agent evolution system
# app.include_router(self_navigating.router)  # Week 19: needs ChromaDB (no tests)
app.include_router(attribution.router)  # Week 21-22: Attribution tracking
# app.include_router(task_generation.router)  # Week 23-24: needs ChromaDB (no tests)
# app.include_router(rollback.router)  # Week 25-26: needs service dependencies (no tests)
app.include_router(scheduler.router)
app.include_router(green_paper_routes.router)  # Week 10: Green Paper BMAD Workflow
app.include_router(task_generation_routes.router)  # Week 11: Task Generation from Specifications
app.include_router(quality_gate_config.router)  # Week 49: Quality Gates Configuration UI
app.include_router(quality_gate_evaluation.router)  # Week 50: Quality Gate Evaluation API
app.include_router(agent_validation.router)  # Week 50: Agent Validation Loop API
app.include_router(ab_testing.router)  # Week 51: A/B Testing for Agent Evolution
app.include_router(llm_council.router)  # Week 52: LLM Council Multi-Model Decision Making
app.include_router(evolution_dashboard.router)  # Week 53: Evolution Dashboard - Real-time Agent Performance
app.include_router(spec_review.router)  # Week 53: Quinn/Felix Spec Review (Option B+)
app.include_router(observability.router, prefix="/api")  # Week 54: Observability System
app.include_router(council_human_review.router)  # Week 55: Human-in-the-Loop Council
app.include_router(stack_agents.router)  # Week 56: Stack Agent Factory & Templates
app.include_router(project_registration.router, prefix="/api")  # Week 56: Unified Project Registration
app.include_router(application_registry.router, prefix="/api")  # Week 57: Multi-Project Application Registry
app.include_router(test_organization.router, prefix="/api")  # Week 57: Test Organization for Projects
app.include_router(brown_paper.router)  # Week 57: Brown Paper Reverse Engineering Workflow
app.include_router(fp_estimation.router)  # Week 57: Function Point Estimation API
app.include_router(hci_crs_knowledge.router)  # Week 57: HCI-CRS Project Knowledge API (RAG)
app.include_router(kanban.router)  # Week 58: Kanban Dashboard with 6 Lanes
app.include_router(standards.router)  # Week 59: Standards Loader Service (Agent OS)
app.include_router(spec_shaping.router)  # Week 59: Spec Shaping Loop (Agent OS)
app.include_router(quick_spec.router)  # Week 60: Quick Spec Templates
app.include_router(improve_skills.router)  # Week 60: Agent Skill Improvement (/improve-skills)
app.include_router(spec_verification.router)  # Week 60: Spec Verification (Agent OS - 4 concepts)
app.include_router(cctrace.router, prefix="/api")  # Week 61: CCTrace Observability & Cost Management
app.include_router(codewiki.router, prefix="/api")  # Week 62: CodeWiki Repository Documentation
app.include_router(knowledge.router, prefix="/api")  # Week 62: Unified Knowledge API (CodeWiki + CodeRAG)
app.include_router(knowledge_graph.router, prefix="/api")  # Week 62: Local Knowledge Graph (AST-based)
app.include_router(security.router)  # Week 63: CyberStrike Security Scanning
app.include_router(rl_training.router)  # Week 64: ART Reinforcement Learning Training
app.include_router(migration_analyzer.router)  # Week 65: MigrationAnalyzer Multi-Agent System
app.include_router(migration_security.router)  # Week 68: Quinn Security Integration for Legacy Migration
app.include_router(migration_estimation.router)  # Week 68: Eliza FP Estimation for Migration Projects
app.include_router(migration_architecture.router)  # Week 68: Felix Architecture Recommendations
app.include_router(migration_report.router)  # Week 68: Diana Report Generation (Markdown output)
app.include_router(project_workflows.router)  # Week 69: Gestandaardiseerde Project Workflows (3 workflows)
app.include_router(workflow_dashboard.router, prefix="/api")  # Week 69: Workflow Monitoring Dashboard
app.include_router(mcp_proxy.router)  # Week 71: MCP Proxy Token Optimization
app.include_router(anytool.router)  # Week 72: AnyTool Universal Tool Calling
app.include_router(memmachine.router)  # Week 73: MemMachine Agent Memory
app.include_router(code_graph.router)  # Week 75: Graph Persistence for Code Understanding
app.include_router(claude_mem.router)  # Week 76: Claude-Mem Session Memory
app.include_router(layered_analysis.router)  # Week 77: 4-Layer Analysis Pipeline (VBScript/SP/SWOT/Improvements)
app.include_router(playwriter.router)  # Week 78: Playwriter Browser Automation
app.include_router(bigagi.router)  # Week 78: BigAGI Beam Multi-Model Validation
app.include_router(ccpm.router)  # Week 79: CCPM Git Worktrees, GitHub Issues, PRD Decomposition
app.include_router(ghostcrew.router)  # Week 80-82: GhostCrew Security Multi-Agent System
app.include_router(deep_extraction.router)  # Week 81-87: Deep Extraction Pipeline (Multi-LLM Code Analysis)
app.include_router(graph_workflow.router, prefix="/api")  # Week 88: Graph-Workflow Integration (Tool-Workflow bindings)
app.include_router(debt_categorization.router, prefix="/api")  # Week 80+: Debt Categorization (Issues per Epic/Feature/Story)
app.include_router(code_analysis.router, prefix="/api")  # Week 83: Code Analysis Aggregator (Potpie, Stack, Dependencies)
app.include_router(hierarchical_extraction.router, prefix="/api")  # Week 84: Hierarchical Story Extraction (Few-shot templates)
app.include_router(rerun_upgrade.router, prefix="/api")  # Week 85: Re-Run Upgrade & Delta Tracking
app.include_router(portal_features.router)  # Week 88: Portal Feature Request API (Customer Portal Integration)
app.include_router(portal_roadmap.router)  # Week 90: Portal Roadmap API (Analysis Queue, Releases, Public Roadmaps)
app.include_router(harness.router)  # Week 91: Agent Harness Framework (Constraints, Context, Tools, Versioning)
app.include_router(design.router)  # Week 94-95: Design OS (Vicky Agent, Design Tokens, UI Specs, Wireframes)
app.include_router(static_analysis.router)  # Week 97-98: Static Analysis (Fase 15 - Hybrid Static-LLM Pipeline)
app.include_router(devops_analysis.router)  # Week 97-98: DevOps Analysis (Fase 14 - GitHub/Azure DevOps Intelligence)
app.include_router(orchestration.router)  # Week 107-110: Agent Orchestration (HATEOAG, Memory, Anti-Patterns)
app.include_router(traceability.router)  # Week 113: Traceability (Business Rules ↔ Epic/Feature/Story)
app.include_router(hybrid_extraction.router, prefix="/api")  # Week 111-114: Hybrid Business Rule Extraction (5-stage LLM pipeline)
app.include_router(requirements.router)  # Week 117: rmtoo Requirements Management (Sync, Export, Traceability)
app.include_router(portal_boost.router)  # Week 118: Client Portal 2.0 Phase 2 (Priority Boost, Impact Preview, Duplicates)
app.include_router(portal_engagement.router)  # Week 119-120: Client Portal 2.0 Phase 3 (Feedback, Gamification, Dashboard)
app.include_router(causality.router)  # Week 123: CiRA Causality Detection (BERT-based cause-effect analysis)
app.include_router(metrics.router, prefix="/api")  # Week 126: Metrics Layer (HCI Quality Scanners - Complexity, Coupling, Balance, Duplication)
app.include_router(migration_enhanced.router)  # Week 130: Migration Enhanced (7-Phase Execution Workflow)
app.include_router(week131_research.router)  # Week 131: Research Services (Background Jobs, Load Estimation, Documentation Rules)
app.include_router(week131_transformation.router)  # Week 131: Transformation Services (Code + DB Migration)
app.include_router(week132_dead_code.router)  # Week 132-133: Dead Code & Runtime Analysis (Fase 22)
app.include_router(week134_testing.router)  # Week 134-135: Testing Excellence (Golden Master, Visual Regression, Dual-Run)
app.include_router(data_architecture.router)  # Week 136-137: Data Architecture (Fase 24 - Lineage, ERD, Journey Comparison)
app.include_router(decision_tables.router)  # Week 138-139: Decision Tables (Fase 25 - Business Logic Extraction)
app.include_router(state_machine_extraction.router)  # Week 138-139: State Machines (Fase 25 - Business Logic Extraction)
app.include_router(authorization_matrix.router)  # Week 138-139: Authorization Matrix (Fase 25 - RBAC Extraction)
app.include_router(migration_execution.router)  # Week 140-141: Migration Execution (Fase 26 - Strangler Fig, Library Mapper, Wave Planner, UI Extraction)
app.include_router(api_inventory.router)  # Week 140-141: API Inventory (Fase 26 - Endpoint Extraction, External API Detection)
app.include_router(customers.router)  # Week 143: Customer Hierarchy (Fase 28 - Data Architecture Enhancement)
app.include_router(codecharta.router)  # Week 145: CodeCharta 3D Visualization Export (Fase 28 - Data Architecture Enhancement)
app.include_router(token_context.router)  # Week 143: Token-Optimized Context (Vector DB Context within Token Budgets)
app.include_router(project_intake.router)  # Week 145: Project Intake Wizard (Brown Paper, Green Paper, Migration)
app.include_router(stability.router)  # Week 143-146: ASP Stability Analyzer (Fase 21 - Resource Leak Detection)
app.include_router(websocket.router)  # Week 15: Real-time WebSocket Updates

# Mount frontend static files
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
async def root():
    """Serve frontend or API info"""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        return FileResponse(str(frontend_file))
    return {
        "message": "Project Manager API v2.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc"
    }

@app.get("/index.html")
async def index_html():
    """Serve index.html directly"""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        return FileResponse(str(frontend_file))
    raise HTTPException(status_code=404, detail="Index page not found")

@app.get("/sprint-planning.html")
async def sprint_planning():
    """Serve sprint planning interface"""
    sprint_planning_file = frontend_path / "sprint-planning.html"
    if sprint_planning_file.exists():
        return FileResponse(str(sprint_planning_file))
    raise HTTPException(status_code=404, detail="Sprint planning page not found")

@app.get("/agent-dashboard.html")
async def agent_dashboard():
    """Serve agent dashboard interface"""
    agent_dashboard_file = frontend_path / "agent-dashboard.html"
    if agent_dashboard_file.exists():
        return FileResponse(str(agent_dashboard_file))
    raise HTTPException(status_code=404, detail="Agent dashboard page not found")

@app.get("/quality-dashboard.html")
async def quality_dashboard():
    """Serve quality dashboard interface"""
    quality_dashboard_file = frontend_path / "quality-dashboard.html"
    if quality_dashboard_file.exists():
        return FileResponse(str(quality_dashboard_file))
    raise HTTPException(status_code=404, detail="Quality dashboard page not found")

@app.get("/quality-gates-config.html")
async def quality_gates_config():
    """Serve quality gates configuration interface"""
    config_file = frontend_path / "quality-gates-config.html"
    if config_file.exists():
        return FileResponse(str(config_file))
    raise HTTPException(status_code=404, detail="Quality gates config page not found")

@app.get("/project-wizard.html")
async def project_wizard_page():
    """Serve project wizard interface"""
    project_wizard_file = frontend_path / "project-wizard.html"
    if project_wizard_file.exists():
        return FileResponse(str(project_wizard_file))
    raise HTTPException(status_code=404, detail="Project wizard page not found")

@app.get("/maintenance-scheduler.html")
async def maintenance_scheduler_page():
    """Serve maintenance scheduler interface"""
    maintenance_file = frontend_path / "maintenance-scheduler.html"
    if maintenance_file.exists():
        return FileResponse(str(maintenance_file))
    raise HTTPException(status_code=404, detail="Maintenance scheduler page not found")

@app.get("/estimation-dashboard.html")
async def estimation_dashboard_page():
    """Serve estimation dashboard interface"""
    estimation_file = frontend_path / "estimation-dashboard.html"
    if estimation_file.exists():
        return FileResponse(str(estimation_file))
    raise HTTPException(status_code=404, detail="Estimation dashboard page not found")

@app.get("/technical-debt-dashboard.html")
async def technical_debt_dashboard_page():
    """Serve technical debt dashboard interface"""
    debt_file = frontend_path / "technical-debt-dashboard.html"
    if debt_file.exists():
        return FileResponse(str(debt_file))
    raise HTTPException(status_code=404, detail="Technical debt dashboard page not found")

@app.get("/weak-spots-dashboard.html")
async def weak_spots_dashboard_page():
    """Serve weak spots dashboard interface"""
    weak_spots_file = frontend_path / "weak-spots-dashboard.html"
    if weak_spots_file.exists():
        return FileResponse(str(weak_spots_file))
    raise HTTPException(status_code=404, detail="Weak spots dashboard page not found")

@app.get("/evolution-dashboard.html")
async def evolution_dashboard_page():
    """Serve evolution dashboard interface"""
    evolution_file = frontend_path / "evolution-dashboard.html"
    if evolution_file.exists():
        return FileResponse(str(evolution_file))
    raise HTTPException(status_code=404, detail="Evolution dashboard page not found")

@app.get("/human-review-dashboard.html")
async def human_review_dashboard_page():
    """Serve human review dashboard interface (Week 85)"""
    human_review_file = frontend_path / "human-review-dashboard.html"
    if human_review_file.exists():
        return FileResponse(str(human_review_file))
    raise HTTPException(status_code=404, detail="Human review dashboard page not found")

@app.get("/spec-kit-wizard.html")
async def spec_kit_wizard_page():
    """Serve spec-kit wizard interface"""
    spec_kit_file = frontend_path / "spec-kit-wizard.html"
    if spec_kit_file.exists():
        return FileResponse(str(spec_kit_file))
    raise HTTPException(status_code=404, detail="Spec-kit wizard page not found")

@app.get("/llm-council-dashboard.html")
async def llm_council_dashboard_page():
    """Serve LLM council dashboard interface"""
    council_file = frontend_path / "llm-council-dashboard.html"
    if council_file.exists():
        return FileResponse(str(council_file))
    raise HTTPException(status_code=404, detail="LLM council dashboard page not found")

@app.get("/council-human-review.html")
async def council_human_review_page():
    """Serve Council Human Review interface (Week 55)"""
    review_file = frontend_path / "council-human-review.html"
    if review_file.exists():
        return FileResponse(str(review_file))
    raise HTTPException(status_code=404, detail="Council human review page not found")

@app.get("/observability-dashboard.html")
async def observability_dashboard_page():
    """Serve Observability Dashboard interface (Week 54)"""
    obs_file = frontend_path / "observability-dashboard.html"
    if obs_file.exists():
        return FileResponse(str(obs_file))
    raise HTTPException(status_code=404, detail="Observability dashboard page not found")

@app.get("/project-intake.html")
async def project_intake_page():
    """Serve Project Intake interface (Week 57)"""
    intake_file = frontend_path / "project-intake.html"
    if intake_file.exists():
        return FileResponse(str(intake_file))
    raise HTTPException(status_code=404, detail="Project intake page not found")

@app.get("/applications.html")
async def applications_page():
    """Serve Applications overview (Week 57)"""
    apps_file = frontend_path / "applications.html"
    if apps_file.exists():
        return FileResponse(str(apps_file))
    raise HTTPException(status_code=404, detail="Applications page not found")

@app.get("/kanban-dashboard.html")
async def kanban_dashboard_page():
    """Serve Kanban Dashboard (Week 58)"""
    kanban_file = frontend_path / "kanban-dashboard.html"
    if kanban_file.exists():
        return FileResponse(str(kanban_file))
    raise HTTPException(status_code=404, detail="Kanban dashboard page not found")

@app.get("/standards-browser.html")
async def standards_browser_page():
    """Serve Standards Browser (Week 59 - Agent OS)"""
    standards_file = frontend_path / "standards-browser.html"
    if standards_file.exists():
        return FileResponse(str(standards_file))
    raise HTTPException(status_code=404, detail="Standards browser page not found")

@app.get("/codewiki-dashboard.html")
async def codewiki_dashboard_page():
    """Serve CodeWiki Dashboard (Week 62)"""
    codewiki_file = frontend_path / "codewiki-dashboard.html"
    if codewiki_file.exists():
        return FileResponse(str(codewiki_file))
    raise HTTPException(status_code=404, detail="CodeWiki dashboard page not found")

@app.get("/security-dashboard.html")
async def security_dashboard_page():
    """Serve Security Dashboard (Week 63 - CyberStrike)"""
    security_file = frontend_path / "security-dashboard.html"
    if security_file.exists():
        return FileResponse(str(security_file))
    raise HTTPException(status_code=404, detail="Security dashboard page not found")

@app.get("/migration-analyzer.html")
async def migration_analyzer_page():
    """Serve Migration Analyzer Dashboard (Week 70)"""
    migration_file = frontend_path / "migration-analyzer.html"
    if migration_file.exists():
        return FileResponse(str(migration_file))
    raise HTTPException(status_code=404, detail="Migration analyzer page not found")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


# NOTE: Startup and shutdown logic moved to lifespan context manager (line 17)
