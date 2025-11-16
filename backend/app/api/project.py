"""
Project API - Endpoints for project visualization
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import sys

# Add sync module to path
sys.path.append(str(Path(__file__).parent.parent / "sync"))

from app.sync.parser import MultiFileProjectParser

router = APIRouter(prefix="/api/project", tags=["project"])


@router.get("/")
async def get_project():
    """
    Get full project structure (epics, features, stories, tasks).

    Returns parsed markdown project data.
    """
    try:
        project_root = Path("/home/eddie/Projects/MarkdownTaskManager")
        parser = MultiFileProjectParser(project_root)

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
async def get_epics():
    """Get all epics"""
    try:
        project_root = Path("/home/eddie/Projects/MarkdownTaskManager")
        parser = MultiFileProjectParser(project_root)

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
async def get_epic(epic_id: str):
    """Get single epic by ID"""
    try:
        project_root = Path("/home/eddie/Projects/MarkdownTaskManager")
        parser = MultiFileProjectParser(project_root)

        epic_dir = project_root / "Projecten" / "MarkdownTaskManager" / epic_id

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
async def get_project_stats():
    """Get project statistics"""
    try:
        project_root = Path("/home/eddie/Projects/MarkdownTaskManager")
        parser = MultiFileProjectParser(project_root)

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
