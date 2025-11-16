"""
FastAPI Integration Example - How to use sync engine in API endpoints

This demonstrates how to integrate the sync engine into your FastAPI application.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
from typing import Optional, List

# Assuming these imports from your app
# from app.database import get_db
# from app.config import settings

from sync_engine import SyncEngine, sync_markdown_to_db, sync_db_to_markdown
from file_watcher import MarkdownFileWatcher

# Create router
router = APIRouter(prefix="/api/sync", tags=["sync"])

# Global file watcher instance
file_watcher: Optional[MarkdownFileWatcher] = None


# Dependency to get project root
def get_project_root() -> Path:
    """Get project root directory"""
    return Path("/home/eddie/Projects/MarkdownTaskManager")


@router.post("/markdown-to-db")
async def sync_markdown_to_database(
    project_root: Path = Depends(get_project_root),
    # db: AsyncSession = Depends(get_db)  # Uncomment when database is configured
):
    """
    Sync markdown files to database.

    Parses all markdown files and updates database records.

    Returns:
        Sync statistics
    """
    try:
        # TODO: Uncomment when database is configured
        # stats = await sync_markdown_to_db(project_root, db)

        # Placeholder response
        stats = {
            "status": "success",
            "message": "Sync engine ready - waiting for database models",
            "epics_created": 0,
            "epics_updated": 0,
            "note": "Complete database implementation to enable sync"
        }

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/db-to-markdown")
async def sync_database_to_markdown(
    epic_ids: Optional[List[str]] = None,
    project_root: Path = Depends(get_project_root),
    # db: AsyncSession = Depends(get_db)  # Uncomment when database is configured
):
    """
    Sync database to markdown files.

    Queries database and generates/updates markdown files.

    Args:
        epic_ids: Optional list of epic IDs to sync. If None, sync all.

    Returns:
        Sync statistics
    """
    try:
        # TODO: Uncomment when database is configured
        # stats = await sync_db_to_markdown(project_root, db, epic_ids)

        # Placeholder response
        stats = {
            "status": "success",
            "message": "Sync engine ready - waiting for database models",
            "epics_generated": 0,
            "note": "Complete database implementation to enable sync"
        }

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/watcher/start")
async def start_file_watcher(
    project_root: Path = Depends(get_project_root),
    # db: AsyncSession = Depends(get_db)  # Uncomment when database is configured
):
    """
    Start file watcher for automatic synchronization.

    Monitors markdown directory for changes and automatically syncs to database.
    """
    global file_watcher

    if file_watcher and file_watcher.is_running():
        return {
            "status": "already_running",
            "message": "File watcher is already running"
        }

    try:
        # Define sync callback
        async def sync_callback():
            """Callback to sync markdown to database when files change"""
            # TODO: Uncomment when database is configured
            # await sync_markdown_to_db(project_root, db)
            print("File change detected - sync triggered")

        # Create and start watcher
        file_watcher = MarkdownFileWatcher(
            project_root,
            sync_callback,
            debounce_seconds=2.0
        )
        file_watcher.start()

        return {
            "status": "started",
            "message": "File watcher started",
            "watching": str(project_root / "Projecten" / "MarkdownTaskManager")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start watcher: {str(e)}")


@router.post("/watcher/stop")
async def stop_file_watcher():
    """
    Stop file watcher.

    Stops monitoring markdown directory for changes.
    """
    global file_watcher

    if not file_watcher or not file_watcher.is_running():
        return {
            "status": "not_running",
            "message": "File watcher is not running"
        }

    try:
        file_watcher.stop()
        file_watcher = None

        return {
            "status": "stopped",
            "message": "File watcher stopped"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop watcher: {str(e)}")


@router.get("/watcher/status")
async def get_watcher_status():
    """
    Get file watcher status.

    Returns:
        Current status of file watcher
    """
    global file_watcher

    is_running = file_watcher is not None and file_watcher.is_running()

    return {
        "status": "running" if is_running else "stopped",
        "watching": str(file_watcher.markdown_dir) if file_watcher else None
    }


# Application startup/shutdown handlers

async def startup_handler():
    """
    Call this in your FastAPI app startup event to auto-start file watcher.

    Example:
        @app.on_event("startup")
        async def startup():
            await startup_handler()
    """
    # Optionally auto-start file watcher on application startup
    # await start_file_watcher()
    pass


async def shutdown_handler():
    """
    Call this in your FastAPI app shutdown event to stop file watcher.

    Example:
        @app.on_event("shutdown")
        async def shutdown():
            await shutdown_handler()
    """
    global file_watcher

    if file_watcher and file_watcher.is_running():
        file_watcher.stop()


# Example: Add to main.py
"""
from fastapi import FastAPI
from app.sync.api_integration_example import router, startup_handler, shutdown_handler

app = FastAPI()

# Include sync router
app.include_router(router)

# Add startup/shutdown handlers
@app.on_event("startup")
async def startup():
    await startup_handler()

@app.on_event("shutdown")
async def shutdown():
    await shutdown_handler()
"""
