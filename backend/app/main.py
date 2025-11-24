from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.api import epics, features, stories, tasks, sprints, auth, project, workflows, projects, scheduler, estimation, estimation_history, project_wizard, websocket, maintenance, ml_training, evolution, quality_dashboard, self_navigating, attribution, task_generation, continuous_learning, rollback, quality_gate_config
from app.api.week10 import green_paper_routes
from app.api.week11 import task_generation_routes
from app.database import engine
from app.models.item import Base as ItemBase
from app.models.sprint import Base as SprintBase
from app.models.user import Base as UserBase
from app.config import settings

app = FastAPI(
    title="Project Manager API",
    description="Hierarchical project management API with Sprint support",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
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
# app.include_router(maintenance.router)  # Week 15: needs scheduler dependencies
# app.include_router(ml_training.router)  # Week 16: needs ChromaDB
# app.include_router(evolution.router)  # Week 17: needs ChromaDB
# app.include_router(self_navigating.router)  # Week 19: needs ChromaDB
# app.include_router(attribution.router)  # Week 21-22: needs ChromaDB
# app.include_router(task_generation.router)  # Week 23-24: needs ChromaDB
# app.include_router(rollback.router)  # Week 25-26: needs service dependencies
app.include_router(scheduler.router)
app.include_router(green_paper_routes.router)  # Week 10: Green Paper BMAD Workflow
app.include_router(task_generation_routes.router)  # Week 11: Task Generation from Specifications
app.include_router(quality_gate_config.router)  # Week 49: Quality Gates Configuration UI
# app.include_router(websocket.router)  # Week 15: Real-time WebSocket Updates

# Mount frontend static files
frontend_path = Path("/frontend")
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

@app.get("/evolution-dashboard.html")
async def evolution_dashboard_page():
    """Serve evolution dashboard interface"""
    evolution_file = frontend_path / "evolution-dashboard.html"
    if evolution_file.exists():
        return FileResponse(str(evolution_file))
    raise HTTPException(status_code=404, detail="Evolution dashboard page not found")

@app.get("/spec-kit-wizard.html")
async def spec_kit_wizard_page():
    """Serve spec-kit wizard interface"""
    spec_kit_file = frontend_path / "spec-kit-wizard.html"
    if spec_kit_file.exists():
        return FileResponse(str(spec_kit_file))
    raise HTTPException(status_code=404, detail="Spec-kit wizard page not found")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup():
    """Create database tables and start scheduler on startup"""
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with Base
        from app.models.item import Item
        from app.models.sprint import Sprint
        from app.models.user import User
        from app.models.green_paper import GreenPaperSession, Answer, Constitution, Specification

        # Create all tables
        await conn.run_sync(ItemBase.metadata.create_all)
        await conn.run_sync(SprintBase.metadata.create_all)
        await conn.run_sync(UserBase.metadata.create_all)

        # Import and create Week 10 tables
        from app.models.green_paper import Base as GreenPaperBase
        await conn.run_sync(GreenPaperBase.metadata.create_all)

        # Import Week 11 models (they use same Base as green_paper, so tables already created)
        from app.models.task_hierarchy import Epic, Feature, Story, Task

        # Import Week 15 models for ML training data (uses same Base as green_paper)
        from app.models.estimation_history import (
            EstimationProject, FunctionPointEstimate, StoryPointEstimate, MLModelVersion
        )

    print("✅ Database tables created successfully (including Week 10-11, Week 15 ML)")

    # Start scheduler for periodic maintenance
    from app.services.scheduler_service import get_scheduler
    scheduler_instance = get_scheduler()
    scheduler_instance.start()
    print("✅ Maintenance scheduler started")

    print("✅ Database tables created successfully (including Week 10-11, Week 15-16 ML)")

    print("📚 API Documentation: http://localhost:8000/api/docs")
    print("🤖 AI Workflows: http://localhost:8000/api/workflows/work-types")
    print("📅 Scheduler API: http://localhost:8000/api/scheduler/status")
    print("🔌 WebSocket: ws://localhost:8000/ws/maintenance (real-time updates)")
    print("🧠 ML Training: http://localhost:8000/api/ml/status")

@app.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown"""
    # Stop scheduler
    from app.services.scheduler_service import get_scheduler
    scheduler_instance = get_scheduler()
    scheduler_instance.shutdown()
    print("🛑 Maintenance scheduler stopped")

    await engine.dispose()
    print("👋 Database connections closed")
