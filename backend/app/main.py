from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.api import epics, features, stories, tasks, sprints, auth, project, workflows, projects, scheduler
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
app.include_router(scheduler.router)

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

@app.get("/sprint-planning.html")
async def sprint_planning():
    """Serve sprint planning interface"""
    sprint_planning_file = frontend_path / "sprint-planning.html"
    if sprint_planning_file.exists():
        return FileResponse(str(sprint_planning_file))
    raise HTTPException(status_code=404, detail="Sprint planning page not found")

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

        # Create all tables
        await conn.run_sync(ItemBase.metadata.create_all)
        await conn.run_sync(SprintBase.metadata.create_all)
        await conn.run_sync(UserBase.metadata.create_all)

    print("✅ Database tables created successfully")

    # Start scheduler for periodic maintenance
    from app.services.scheduler_service import get_scheduler
    scheduler_instance = get_scheduler()
    scheduler_instance.start()
    print("✅ Maintenance scheduler started")

    print("📚 API Documentation: http://localhost:8000/api/docs")
    print("🤖 AI Workflows: http://localhost:8000/api/workflows/work-types")
    print("📅 Scheduler API: http://localhost:8000/api/scheduler/status")

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
