"""
Project API - Endpoints for project visualization
"""

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Optional
import sys

# Add sync module to path
sys.path.append(str(Path(__file__).parent.parent / "sync"))

from app.sync.parser import MultiFileProjectParser

router = APIRouter(prefix="/api/project", tags=["project"])

# Project root path
PROJECT_ROOT = Path("/home/eddie/Projects/MarkdownTaskManager")


@router.get("/")
async def get_project(
    project_name: Optional[str] = Query("MarkdownTaskManager", description="Project folder name")
):
    """
    Get full project structure (epics, features, stories, tasks).

    Returns parsed markdown project data.
    """
    try:
        parser = MultiFileProjectParser(PROJECT_ROOT, project_name)

        project_data = parser.parse_project()

        # Convert datetime to string for JSON serialization
        if "parse_time" in project_data:
            project_data["parse_time"] = str(project_data["parse_time"])

        return {
            "status": "success",
            "data": project_data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse project: {str(e)}"
        )


@router.get("/epics")
async def get_epics(
    project_name: Optional[str] = Query("MarkdownTaskManager", description="Project folder name")
):
    """Get all epics"""
    try:
        parser = MultiFileProjectParser(PROJECT_ROOT, project_name)

        project_data = parser.parse_project()

        return {
            "status": "success",
            "data": project_data["epics"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get epics: {str(e)}"
        )


@router.get("/epic/{epic_id}")
async def get_epic(
    epic_id: str,
    project_name: Optional[str] = Query("MarkdownTaskManager", description="Project folder name")
):
    """Get single epic by ID"""
    try:
        parser = MultiFileProjectParser(PROJECT_ROOT, project_name)

        epic_dir = PROJECT_ROOT / "Projecten" / project_name / epic_id

        if not epic_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Epic {epic_id} not found"
            )

        epic_data = parser.parse_epic(epic_dir)

        return {
            "status": "success",
            "data": epic_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get epic: {str(e)}"
        )


@router.get("/stats")
async def get_project_stats(
    project_name: Optional[str] = Query("MarkdownTaskManager", description="Project folder name")
):
    """Get project statistics"""
    try:
        parser = MultiFileProjectParser(PROJECT_ROOT, project_name)

        project_data = parser.parse_project()

        # Calculate stats
        total_sp = sum(epic.get("sp_total", 0) for epic in project_data["epics"])
        completed_sp = sum(epic.get("sp_completed", 0) for epic in project_data["epics"])

        stats = {
            "epics_count": len(project_data["epics"]),
            "features_count": len(project_data["features"]),
            "stories_count": len(project_data["stories"]),
            "tasks_count": len(project_data["tasks"]),
            "total_story_points": total_sp,
            "completed_story_points": completed_sp,
            "progress_percentage": round((completed_sp / total_sp * 100) if total_sp > 0 else 0, 1)
        }

        return {
            "status": "success",
            "data": stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
