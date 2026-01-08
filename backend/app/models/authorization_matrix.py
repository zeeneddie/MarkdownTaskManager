"""
Authorization Matrix Models - Fase 25: Business Logic Extraction

Models for representing RBAC (Role-Based Access Control) matrices
extracted from legacy code.

Author: Claude Code (Week 139 - Fase 25)
Date: 2026-01-01
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4


class PermissionType(str, Enum):
    """Type of permission"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    REJECT = "reject"
    ADMIN = "admin"
    VIEW = "view"
    EDIT = "edit"
    MANAGE = "manage"
    EXPORT = "export"
    IMPORT = "import"


class RoleLevel(str, Enum):
    """Role hierarchy level"""
    SYSTEM = "system"     # System-wide admin
    ADMIN = "admin"       # Application admin
    MANAGER = "manager"   # Department/team manager
    POWER_USER = "power_user"
    USER = "user"         # Regular user
    GUEST = "guest"       # Limited access
    ANONYMOUS = "anonymous"


class ResourceType(str, Enum):
    """Type of protected resource"""
    PAGE = "page"
    ENDPOINT = "endpoint"
    ENTITY = "entity"
    FIELD = "field"
    ACTION = "action"
    REPORT = "report"
    MODULE = "module"
    FEATURE = "feature"


class ConflictType(str, Enum):
    """Type of authorization conflict"""
    MISSING_PERMISSION = "missing_permission"   # Action without permission check
    REDUNDANT_PERMISSION = "redundant"          # Same permission at multiple levels
    CONTRADICTORY = "contradictory"             # Conflicting allow/deny
    INCOMPLETE_COVERAGE = "incomplete"          # Resource not fully protected
    ORPHAN_ROLE = "orphan_role"                 # Role without permissions
    ORPHAN_PERMISSION = "orphan_permission"     # Permission without role


class AuthorizationMatrixOutputFormat(str, Enum):
    """Output formats for authorization matrix"""
    MARKDOWN = "markdown"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    EXCEL = "excel"


@dataclass
class ExtractedRole:
    """A role extracted from code"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    display_name: str = ""
    description: str = ""
    level: RoleLevel = RoleLevel.USER
    parent_role: Optional[str] = None  # For role hierarchy
    inherited_permissions: List[str] = field(default_factory=list)
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    source_code: Optional[str] = None
    confidence: float = 1.0


@dataclass
class ExtractedPermission:
    """A permission extracted from code"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    display_name: str = ""
    description: str = ""
    permission_type: PermissionType = PermissionType.READ
    resource_id: Optional[str] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    source_code: Optional[str] = None
    confidence: float = 1.0


@dataclass
class ExtractedResource:
    """A protected resource extracted from code"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    display_name: str = ""
    description: str = ""
    resource_type: ResourceType = ResourceType.PAGE
    path: Optional[str] = None  # URL path, file path, etc.
    parent_resource: Optional[str] = None
    required_permissions: List[str] = field(default_factory=list)
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    source_code: Optional[str] = None
    confidence: float = 1.0


@dataclass
class RolePermissionMapping:
    """Mapping of role to permission"""
    id: str = field(default_factory=lambda: str(uuid4()))
    role_id: str = ""
    permission_id: str = ""
    resource_id: Optional[str] = None  # If permission is resource-specific
    is_granted: bool = True  # True = allow, False = deny
    condition: Optional[str] = None  # Conditional access rule
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    source_code: Optional[str] = None
    confidence: float = 1.0


@dataclass
class AuthorizationConflict:
    """A detected conflict or issue in authorization"""
    id: str = field(default_factory=lambda: str(uuid4()))
    conflict_type: ConflictType = ConflictType.MISSING_PERMISSION
    severity: str = "medium"  # low, medium, high, critical
    description: str = ""
    affected_roles: List[str] = field(default_factory=list)
    affected_permissions: List[str] = field(default_factory=list)
    affected_resources: List[str] = field(default_factory=list)
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    recommendation: str = ""


@dataclass
class AuthorizationMatrixStatistics:
    """Statistics for the authorization matrix"""
    total_roles: int = 0
    total_permissions: int = 0
    total_resources: int = 0
    total_mappings: int = 0
    total_conflicts: int = 0
    coverage_percentage: float = 0.0  # How much of resources are protected
    role_hierarchy_depth: int = 0
    average_permissions_per_role: float = 0.0
    critical_conflicts: int = 0
    high_conflicts: int = 0


@dataclass
class AuthorizationMatrix:
    """Complete authorization matrix extracted from code"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    project_id: Optional[str] = None

    # Core components
    roles: List[ExtractedRole] = field(default_factory=list)
    permissions: List[ExtractedPermission] = field(default_factory=list)
    resources: List[ExtractedResource] = field(default_factory=list)
    mappings: List[RolePermissionMapping] = field(default_factory=list)

    # Analysis results
    conflicts: List[AuthorizationConflict] = field(default_factory=list)
    statistics: Optional[AuthorizationMatrixStatistics] = None

    # Metadata
    source_files: List[str] = field(default_factory=list)
    confidence: float = 1.0
    extracted_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def get_role_permissions(self, role_name: str) -> List[str]:
        """Get all permissions for a role (including inherited)"""
        role = next((r for r in self.roles if r.name == role_name), None)
        if not role:
            return []

        permissions = set()

        # Direct permissions
        for mapping in self.mappings:
            if mapping.role_id == role.id and mapping.is_granted:
                permissions.add(mapping.permission_id)

        # Inherited permissions
        if role.parent_role:
            parent_perms = self.get_role_permissions(role.parent_role)
            permissions.update(parent_perms)

        return list(permissions)

    def get_resource_roles(self, resource_name: str) -> List[str]:
        """Get all roles that can access a resource"""
        resource = next((r for r in self.resources if r.name == resource_name), None)
        if not resource:
            return []

        roles = set()
        for mapping in self.mappings:
            if mapping.resource_id == resource.id and mapping.is_granted:
                role = next((r for r in self.roles if r.id == mapping.role_id), None)
                if role:
                    roles.add(role.name)

        return list(roles)

    def check_access(self, role_name: str, permission_name: str, resource_name: Optional[str] = None) -> bool:
        """Check if role has permission (optionally for specific resource)"""
        role = next((r for r in self.roles if r.name == role_name), None)
        if not role:
            return False

        permission = next((p for p in self.permissions if p.name == permission_name), None)
        if not permission:
            return False

        resource = None
        if resource_name:
            resource = next((r for r in self.resources if r.name == resource_name), None)

        # Check mappings
        for mapping in self.mappings:
            if mapping.role_id == role.id and mapping.permission_id == permission.id:
                if resource_name is None or mapping.resource_id == resource.id:
                    return mapping.is_granted

        # Check inherited permissions
        if role.parent_role:
            return self.check_access(role.parent_role, permission_name, resource_name)

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "project_id": self.project_id,
            "roles": [
                {
                    "id": r.id,
                    "name": r.name,
                    "display_name": r.display_name,
                    "description": r.description,
                    "level": r.level.value,
                    "parent_role": r.parent_role,
                    "confidence": r.confidence
                }
                for r in self.roles
            ],
            "permissions": [
                {
                    "id": p.id,
                    "name": p.name,
                    "display_name": p.display_name,
                    "permission_type": p.permission_type.value,
                    "resource_id": p.resource_id,
                    "confidence": p.confidence
                }
                for p in self.permissions
            ],
            "resources": [
                {
                    "id": r.id,
                    "name": r.name,
                    "display_name": r.display_name,
                    "resource_type": r.resource_type.value,
                    "path": r.path,
                    "confidence": r.confidence
                }
                for r in self.resources
            ],
            "mappings": [
                {
                    "id": m.id,
                    "role_id": m.role_id,
                    "permission_id": m.permission_id,
                    "resource_id": m.resource_id,
                    "is_granted": m.is_granted,
                    "condition": m.condition
                }
                for m in self.mappings
            ],
            "conflicts": [
                {
                    "id": c.id,
                    "conflict_type": c.conflict_type.value,
                    "severity": c.severity,
                    "description": c.description,
                    "recommendation": c.recommendation
                }
                for c in self.conflicts
            ],
            "statistics": {
                "total_roles": self.statistics.total_roles,
                "total_permissions": self.statistics.total_permissions,
                "total_resources": self.statistics.total_resources,
                "coverage_percentage": self.statistics.coverage_percentage,
                "total_conflicts": self.statistics.total_conflicts
            } if self.statistics else None,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat()
        }


@dataclass
class AuthorizationExtractionResult:
    """Result of authorization matrix extraction"""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    project_id: Optional[str] = None

    matrix: Optional[AuthorizationMatrix] = None

    total_files_scanned: int = 0
    files_with_auth: int = 0
    average_confidence: float = 0.0

    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    started_at: datetime = field(default_factory=lambda: datetime.utcnow())
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
