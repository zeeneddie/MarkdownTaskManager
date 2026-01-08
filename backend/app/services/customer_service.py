"""
Customer Service

Week 143 - Fase 28: Data Architecture Enhancement

Service layer for Customer CRUD operations and relationship management.
Customers are the top of the hierarchy: Customer -> Project -> Application
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from app.models.customer import Customer, ProjectApplication
from app.models.project import Project


class CustomerTier(str, Enum):
    """Valid customer tiers."""
    FREE = "FREE"
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    PREMIUM = "PREMIUM"


TIER_LIMITS = {
    CustomerTier.FREE: {"max_projects": 1, "max_applications": 3, "extraction_tier": "free"},
    CustomerTier.BASIC: {"max_projects": 3, "max_applications": 10, "extraction_tier": "basic"},
    CustomerTier.STANDARD: {"max_projects": 10, "max_applications": 50, "extraction_tier": "standard"},
    CustomerTier.PROFESSIONAL: {"max_projects": 50, "max_applications": 200, "extraction_tier": "professional"},
    CustomerTier.PREMIUM: {"max_projects": None, "max_applications": None, "extraction_tier": "premium"},
}


@dataclass
class CustomerStats:
    """Statistics about customers."""
    total_customers: int
    active_customers: int
    inactive_customers: int
    by_tier: Dict[str, int]


class CustomerService:
    """Service for managing customers and their relationships."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ----- CRUD Operations -----

    async def list_customers(
        self,
        skip: int = 0,
        limit: int = 100,
        tier: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Customer]:
        """List customers with optional filtering."""
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
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_customer(self, customer_id: int) -> Optional[Customer]:
        """Get a customer by ID with loaded relationships."""
        query = select(Customer).options(selectinload(Customer.projects)).where(Customer.id == customer_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_customer_by_name(self, name: str) -> Optional[Customer]:
        """Get a customer by name."""
        query = select(Customer).where(Customer.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_customer_by_external_id(self, external_id: str) -> Optional[Customer]:
        """Get a customer by external ID (CRM/ERP reference)."""
        query = select(Customer).where(Customer.external_id == external_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_customer(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        tier: str = "FREE",
        billing_email: Optional[str] = None,
        external_id: Optional[str] = None
    ) -> Customer:
        """Create a new customer."""
        # Validate tier
        self._validate_tier(tier)

        customer = Customer(
            name=name,
            display_name=display_name,
            description=description,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            tier=tier,
            billing_email=billing_email,
            external_id=external_id
        )

        self.db.add(customer)
        await self.db.commit()
        await self.db.refresh(customer)
        return customer

    async def update_customer(
        self,
        customer_id: int,
        **update_data
    ) -> Optional[Customer]:
        """Update a customer's fields."""
        customer = await self.get_customer(customer_id)
        if not customer:
            return None

        # Validate tier if updating
        if "tier" in update_data:
            self._validate_tier(update_data["tier"])

        for field, value in update_data.items():
            if value is not None and hasattr(customer, field):
                setattr(customer, field, value)

        await self.db.commit()
        await self.db.refresh(customer)
        return customer

    async def delete_customer(self, customer_id: int) -> bool:
        """Delete a customer (cascades to projects)."""
        customer = await self.get_customer(customer_id)
        if not customer:
            return False

        await self.db.delete(customer)
        await self.db.commit()
        return True

    async def deactivate_customer(self, customer_id: int) -> Optional[Customer]:
        """Soft-delete by setting is_active to False."""
        return await self.update_customer(customer_id, is_active=False)

    async def activate_customer(self, customer_id: int) -> Optional[Customer]:
        """Reactivate a deactivated customer."""
        return await self.update_customer(customer_id, is_active=True)

    # ----- Statistics -----

    async def get_stats(self) -> CustomerStats:
        """Get aggregate statistics about customers."""
        # Total customers
        total_result = await self.db.execute(select(func.count(Customer.id)))
        total = total_result.scalar() or 0

        # Active customers
        active_result = await self.db.execute(
            select(func.count(Customer.id)).where(Customer.is_active == True)
        )
        active = active_result.scalar() or 0

        # Customers by tier
        tier_result = await self.db.execute(
            select(Customer.tier, func.count(Customer.id)).group_by(Customer.tier)
        )
        by_tier = {row[0]: row[1] for row in tier_result.all()}

        return CustomerStats(
            total_customers=total,
            active_customers=active,
            inactive_customers=total - active,
            by_tier=by_tier
        )

    # ----- Project Relationships -----

    async def get_customer_projects(self, customer_id: int) -> List[Project]:
        """Get all projects for a customer."""
        query = select(Project).where(Project.customer_id == customer_id).order_by(Project.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def assign_project(self, customer_id: int, project_id: int) -> bool:
        """Assign an existing project to a customer."""
        # Verify customer exists
        customer = await self.get_customer(customer_id)
        if not customer:
            return False

        # Get project
        project_result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        if not project:
            return False

        # Check tier limits
        if not await self._check_project_limit(customer):
            raise ValueError(f"Customer has reached project limit for tier {customer.tier}")

        project.customer_id = customer_id
        await self.db.commit()
        return True

    async def unassign_project(self, customer_id: int, project_id: int) -> bool:
        """Remove a project from a customer."""
        project_result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        if not project or project.customer_id != customer_id:
            return False

        project.customer_id = None
        await self.db.commit()
        return True

    # ----- Project-Application Links -----

    async def list_project_applications(
        self,
        project_id: Optional[int] = None,
        application_id: Optional[int] = None
    ) -> List[ProjectApplication]:
        """List project-application links."""
        query = select(ProjectApplication)

        if project_id:
            query = query.where(ProjectApplication.project_id == project_id)
        if application_id:
            query = query.where(ProjectApplication.application_id == application_id)

        result = await self.db.execute(query.order_by(ProjectApplication.linked_at.desc()))
        return list(result.scalars().all())

    async def link_project_application(
        self,
        project_id: int,
        application_id: int,
        role: Optional[str] = None,
        impact_level: Optional[str] = None
    ) -> Optional[ProjectApplication]:
        """Create a link between project and application."""
        # Check for existing link
        existing = await self.db.execute(
            select(ProjectApplication).where(
                ProjectApplication.project_id == project_id,
                ProjectApplication.application_id == application_id
            )
        )
        if existing.scalar_one_or_none():
            return None  # Already exists

        link = ProjectApplication(
            project_id=project_id,
            application_id=application_id,
            role=role,
            impact_level=impact_level
        )

        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        return link

    async def unlink_project_application(self, link_id: int) -> bool:
        """Remove a project-application link."""
        query = select(ProjectApplication).where(ProjectApplication.id == link_id)
        result = await self.db.execute(query)
        link = result.scalar_one_or_none()

        if not link:
            return False

        await self.db.delete(link)
        await self.db.commit()
        return True

    # ----- Tier Management -----

    async def upgrade_tier(self, customer_id: int, new_tier: str) -> Optional[Customer]:
        """Upgrade a customer's tier."""
        self._validate_tier(new_tier)
        return await self.update_customer(customer_id, tier=new_tier)

    async def get_tier_limits(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Get tier limits for a customer."""
        customer = await self.get_customer(customer_id)
        if not customer:
            return None

        tier = CustomerTier(customer.tier)
        return TIER_LIMITS.get(tier)

    async def check_tier_compliance(self, customer_id: int) -> Dict[str, Any]:
        """Check if customer is within their tier limits."""
        customer = await self.get_customer(customer_id)
        if not customer:
            return {"error": "Customer not found"}

        limits = TIER_LIMITS.get(CustomerTier(customer.tier), {})
        projects = await self.get_customer_projects(customer_id)
        project_count = len(projects)

        # Count applications across all projects
        app_links = await self.list_project_applications()
        project_ids = {p.id for p in projects}
        app_count = len([l for l in app_links if l.project_id in project_ids])

        max_projects = limits.get("max_projects")
        max_apps = limits.get("max_applications")

        return {
            "customer_id": customer_id,
            "tier": customer.tier,
            "projects": {
                "current": project_count,
                "limit": max_projects,
                "compliant": max_projects is None or project_count <= max_projects
            },
            "applications": {
                "current": app_count,
                "limit": max_apps,
                "compliant": max_apps is None or app_count <= max_apps
            },
            "overall_compliant": (
                (max_projects is None or project_count <= max_projects) and
                (max_apps is None or app_count <= max_apps)
            )
        }

    # ----- Private Helpers -----

    def _validate_tier(self, tier: str) -> None:
        """Validate that tier is a valid CustomerTier."""
        try:
            CustomerTier(tier)
        except ValueError:
            valid = [t.value for t in CustomerTier]
            raise ValueError(f"Invalid tier '{tier}'. Must be one of: {valid}")

    async def _check_project_limit(self, customer: Customer) -> bool:
        """Check if customer can add another project."""
        limits = TIER_LIMITS.get(CustomerTier(customer.tier), {})
        max_projects = limits.get("max_projects")

        if max_projects is None:
            return True

        projects = await self.get_customer_projects(customer.id)
        return len(projects) < max_projects


# Singleton-style factory function
async def get_customer_service(db: AsyncSession) -> CustomerService:
    """Factory function for dependency injection."""
    return CustomerService(db)
