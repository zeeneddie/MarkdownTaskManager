"""
Customer API Endpoints

Week 143 - Fase 28: Data Architecture Enhancement

CRUD operations for Customer entities.
Customers are the top of the hierarchy: Customer -> Project -> Application
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime

from app.database import get_db
from app.models.customer import Customer, ProjectApplication
from app.models.project import Project

router = APIRouter(prefix="/api/customers", tags=["customers"])


# ----- Pydantic Schemas -----

class CustomerCreate(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    tier: str = "FREE"
    billing_email: Optional[str] = None
    external_id: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    tier: Optional[str] = None
    billing_email: Optional[str] = None
    external_id: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    id: int
    name: str
    display_name: Optional[str]
    description: Optional[str]
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    tier: str
    billing_email: Optional[str]
    external_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    project_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProjectApplicationCreate(BaseModel):
    project_id: int
    application_id: int
    role: Optional[str] = None
    impact_level: Optional[str] = None


class ProjectApplicationResponse(BaseModel):
    id: int
    project_id: int
    application_id: int
    role: Optional[str]
    impact_level: Optional[str]
    linked_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- Customer CRUD Endpoints -----

@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tier: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all customers with optional filtering."""
    query = select(Customer).options(selectinload(Customer.projects))

    if tier:
        query = query.where(Customer.tier == tier)
    if is_active is not None:
        query = query.where(Customer.is_active == is_active)
    if search:
        query = query.where(
            Customer.name.ilike(f"%{search}%") |
            Customer.display_name.ilike(f"%{search}%") |
            Customer.contact_email.ilike(f"%{search}%")
        )

    query = query.order_by(Customer.name).offset(skip).limit(limit)
    result = await db.execute(query)
    customers = result.scalars().all()

    return [
        CustomerResponse(
            id=c.id,
            name=c.name,
            display_name=c.display_name,
            description=c.description,
            contact_name=c.contact_name,
            contact_email=c.contact_email,
            contact_phone=c.contact_phone,
            tier=c.tier,
            billing_email=c.billing_email,
            external_id=c.external_id,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
            project_count=len(c.projects) if c.projects else 0
        )
        for c in customers
    ]


# ----- Project-Application Link Endpoints -----
# NOTE: These must be defined BEFORE /{customer_id} routes to avoid path conflicts

@router.get("/project-applications")
async def list_project_applications(
    project_id: Optional[int] = None,
    application_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """List project-application links with optional filtering."""
    query = select(ProjectApplication)

    if project_id:
        query = query.where(ProjectApplication.project_id == project_id)
    if application_id:
        query = query.where(ProjectApplication.application_id == application_id)

    result = await db.execute(query.order_by(ProjectApplication.linked_at.desc()))
    links = result.scalars().all()

    return [
        ProjectApplicationResponse(
            id=link.id,
            project_id=link.project_id,
            application_id=link.application_id,
            role=link.role,
            impact_level=link.impact_level,
            linked_at=link.linked_at
        )
        for link in links
    ]


@router.post("/project-applications", response_model=ProjectApplicationResponse, status_code=201)
async def link_project_application(data: ProjectApplicationCreate, db: AsyncSession = Depends(get_db)):
    """Create a link between a project and an application."""
    # Verify project exists
    project_result = await db.execute(select(Project).where(Project.id == data.project_id))
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Project {data.project_id} not found")

    # Check for existing link
    existing = await db.execute(
        select(ProjectApplication).where(
            ProjectApplication.project_id == data.project_id,
            ProjectApplication.application_id == data.application_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Link between project {data.project_id} and application {data.application_id} already exists"
        )

    link = ProjectApplication(
        project_id=data.project_id,
        application_id=data.application_id,
        role=data.role,
        impact_level=data.impact_level
    )

    db.add(link)
    await db.commit()
    await db.refresh(link)

    return ProjectApplicationResponse(
        id=link.id,
        project_id=link.project_id,
        application_id=link.application_id,
        role=link.role,
        impact_level=link.impact_level,
        linked_at=link.linked_at
    )


@router.delete("/project-applications/{link_id}")
async def unlink_project_application(link_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a project-application link."""
    query = select(ProjectApplication).where(ProjectApplication.id == link_id)
    result = await db.execute(query)
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(status_code=404, detail=f"Project-Application link {link_id} not found")

    await db.delete(link)
    await db.commit()

    return {"message": f"Project-Application link {link_id} deleted successfully"}


# ----- Customer Stats Endpoint -----

@router.get("/stats")
async def get_customer_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregate statistics about customers."""
    # Total customers
    total_result = await db.execute(select(func.count(Customer.id)))
    total = total_result.scalar() or 0

    # Active customers
    active_result = await db.execute(
        select(func.count(Customer.id)).where(Customer.is_active == True)
    )
    active = active_result.scalar() or 0

    # Customers by tier
    tier_result = await db.execute(
        select(Customer.tier, func.count(Customer.id))
        .group_by(Customer.tier)
    )
    by_tier = {row[0]: row[1] for row in tier_result.all()}

    return {
        "total_customers": total,
        "active_customers": active,
        "inactive_customers": total - active,
        "by_tier": by_tier
    }


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific customer by ID."""
    query = select(Customer).options(selectinload(Customer.projects)).where(Customer.id == customer_id)
    result = await db.execute(query)
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    return CustomerResponse(
        id=customer.id,
        name=customer.name,
        display_name=customer.display_name,
        description=customer.description,
        contact_name=customer.contact_name,
        contact_email=customer.contact_email,
        contact_phone=customer.contact_phone,
        tier=customer.tier,
        billing_email=customer.billing_email,
        external_id=customer.external_id,
        is_active=customer.is_active,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        project_count=len(customer.projects) if customer.projects else 0
    )


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(data: CustomerCreate, db: AsyncSession = Depends(get_db)):
    """Create a new customer."""
    # Check for duplicate name
    existing = await db.execute(select(Customer).where(Customer.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Customer with name '{data.name}' already exists")

    # Validate tier
    valid_tiers = ["FREE", "BASIC", "STANDARD", "PROFESSIONAL", "PREMIUM"]
    if data.tier not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}")

    customer = Customer(
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        tier=data.tier,
        billing_email=data.billing_email,
        external_id=data.external_id
    )

    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    return CustomerResponse(
        id=customer.id,
        name=customer.name,
        display_name=customer.display_name,
        description=customer.description,
        contact_name=customer.contact_name,
        contact_email=customer.contact_email,
        contact_phone=customer.contact_phone,
        tier=customer.tier,
        billing_email=customer.billing_email,
        external_id=customer.external_id,
        is_active=customer.is_active,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        project_count=0
    )


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: int, data: CustomerUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing customer."""
    query = select(Customer).options(selectinload(Customer.projects)).where(Customer.id == customer_id)
    result = await db.execute(query)
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    # Check for duplicate name if updating name
    if data.name and data.name != customer.name:
        existing = await db.execute(select(Customer).where(Customer.name == data.name))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Customer with name '{data.name}' already exists")

    # Validate tier if updating
    if data.tier:
        valid_tiers = ["FREE", "BASIC", "STANDARD", "PROFESSIONAL", "PREMIUM"]
        if data.tier not in valid_tiers:
            raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}")

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)

    return CustomerResponse(
        id=customer.id,
        name=customer.name,
        display_name=customer.display_name,
        description=customer.description,
        contact_name=customer.contact_name,
        contact_email=customer.contact_email,
        contact_phone=customer.contact_phone,
        tier=customer.tier,
        billing_email=customer.billing_email,
        external_id=customer.external_id,
        is_active=customer.is_active,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        project_count=len(customer.projects) if customer.projects else 0
    )


@router.delete("/{customer_id}")
async def delete_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a customer. This will also cascade delete associated projects."""
    query = select(Customer).where(Customer.id == customer_id)
    result = await db.execute(query)
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    await db.delete(customer)
    await db.commit()

    return {"message": f"Customer {customer_id} deleted successfully"}


# ----- Customer Projects Endpoints -----

@router.get("/{customer_id}/projects")
async def get_customer_projects(customer_id: int, db: AsyncSession = Depends(get_db)):
    """Get all projects for a customer."""
    # Verify customer exists
    customer_result = await db.execute(select(Customer).where(Customer.id == customer_id))
    if not customer_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    query = select(Project).where(Project.customer_id == customer_id).order_by(Project.name)
    result = await db.execute(query)
    projects = result.scalars().all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "project_type": p.project_type,
            "project_status": p.project_status,
            "extraction_tier": p.extraction_tier,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in projects
    ]


@router.post("/{customer_id}/projects/{project_id}")
async def assign_project_to_customer(
    customer_id: int,
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Assign an existing project to a customer."""
    # Verify customer exists
    customer_result = await db.execute(select(Customer).where(Customer.id == customer_id))
    if not customer_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    # Get project
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Update project's customer_id
    project.customer_id = customer_id
    await db.commit()

    return {"message": f"Project {project_id} assigned to customer {customer_id}"}


@router.delete("/{customer_id}/projects/{project_id}")
async def unassign_project_from_customer(
    customer_id: int,
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Remove a project from a customer (sets customer_id to NULL)."""
    # Get project
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    if project.customer_id != customer_id:
        raise HTTPException(status_code=400, detail=f"Project {project_id} is not assigned to customer {customer_id}")

    project.customer_id = None
    await db.commit()

    return {"message": f"Project {project_id} unassigned from customer {customer_id}"}
