"""
Project management API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.security import get_current_user, get_current_tenant, TokenData
from ..models.project import Project, ProjectRepository, ProjectStatus, ProjectType

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class ProjectCreate(BaseModel):
    """Create a new project."""

    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    project_type: ProjectType = ProjectType.BROWNFIELD
    tech_stack: List[str] = []


class ProjectUpdate(BaseModel):
    """Update project."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    tech_stack: Optional[List[str]] = None


class ProjectResponse(BaseModel):
    """Project response."""

    id: str
    name: str
    code: Optional[str]
    description: Optional[str]
    status: ProjectStatus
    project_type: ProjectType
    total_fp_estimated: float
    total_fp_consumed: float
    completion_percentage: float
    stories_total: int
    stories_completed: int
    tech_stack: List[str]

    class Config:
        from_attributes = True


class RepositoryCreate(BaseModel):
    """Add repository to project."""

    name: str
    url: Optional[str] = None
    clone_path: Optional[str] = None
    default_branch: str = "main"


class RepositoryResponse(BaseModel):
    """Repository response."""

    id: str
    name: str
    url: Optional[str]
    repository_type: str
    default_branch: str
    last_analyzed_at: Optional[str]
    total_files: int
    total_loc: int
    languages: dict

    class Config:
        from_attributes = True


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List all projects in current tenant."""
    result = await db.execute(
        select(Project)
        .where(Project.tenant_id == tenant_id)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()

    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get project details."""
    result = await db.execute(
        select(Project)
        .where(
            Project.id == project_id,
            Project.tenant_id == tenant_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return ProjectResponse.model_validate(project)


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreate,
    tenant_id: str = Depends(get_current_tenant),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    project = Project(
        tenant_id=tenant_id,
        name=request.name,
        code=request.code,
        description=request.description,
        project_type=request.project_type,
        tech_stack=request.tech_stack,
        status=ProjectStatus.DRAFT,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update project."""
    result = await db.execute(
        select(Project)
        .where(
            Project.id == project_id,
            Project.tenant_id == tenant_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    tenant_id: str = Depends(get_current_tenant),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project."""
    # Verify admin role
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    result = await db.execute(
        select(Project)
        .where(
            Project.id == project_id,
            Project.tenant_id == tenant_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    await db.delete(project)
    await db.commit()

    return {"message": "Project deleted"}


# =============================================================================
# REPOSITORY ENDPOINTS
# =============================================================================


@router.get("/{project_id}/repositories", response_model=List[RepositoryResponse])
async def list_repositories(
    project_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List repositories in a project."""
    result = await db.execute(
        select(ProjectRepository)
        .where(
            ProjectRepository.project_id == project_id,
            ProjectRepository.tenant_id == tenant_id,
        )
    )
    repos = result.scalars().all()

    return [
        RepositoryResponse(
            id=r.id,
            name=r.name,
            url=r.url,
            repository_type=r.repository_type,
            default_branch=r.default_branch,
            last_analyzed_at=r.last_analyzed_at.isoformat() if r.last_analyzed_at else None,
            total_files=r.total_files,
            total_loc=r.total_loc,
            languages=r.languages,
        )
        for r in repos
    ]


@router.post("/{project_id}/repositories", response_model=RepositoryResponse)
async def add_repository(
    project_id: str,
    request: RepositoryCreate,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Add a repository to a project."""
    # Verify project exists
    result = await db.execute(
        select(Project)
        .where(
            Project.id == project_id,
            Project.tenant_id == tenant_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    repo = ProjectRepository(
        tenant_id=tenant_id,
        project_id=project_id,
        name=request.name,
        url=request.url,
        clone_path=request.clone_path,
        default_branch=request.default_branch,
    )

    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    return RepositoryResponse(
        id=repo.id,
        name=repo.name,
        url=repo.url,
        repository_type=repo.repository_type,
        default_branch=repo.default_branch,
        last_analyzed_at=None,
        total_files=repo.total_files,
        total_loc=repo.total_loc,
        languages=repo.languages,
    )
