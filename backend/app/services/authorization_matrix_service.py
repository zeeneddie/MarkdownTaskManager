"""
Authorization Matrix Service - Fase 25: Business Logic Extraction

Extracts RBAC (Role-Based Access Control) patterns from legacy code
and generates authorization matrices.

Features:
- Role extraction from code patterns
- Permission detection from checks
- Resource protection mapping
- Role hierarchy inference
- Conflict detection
- Multiple export formats

Author: Claude Code (Week 139 - Fase 25)
Date: 2026-01-01
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.authorization_matrix import (
    AuthorizationConflict,
    AuthorizationExtractionResult,
    AuthorizationMatrix,
    AuthorizationMatrixOutputFormat,
    AuthorizationMatrixStatistics,
    ConflictType,
    ExtractedPermission,
    ExtractedResource,
    ExtractedRole,
    PermissionType,
    ResourceType,
    RoleLevel,
    RolePermissionMapping,
)

logger = logging.getLogger(__name__)


class AuthorizationMatrixService:
    """
    Service for extracting authorization matrices from legacy code.

    Detects RBAC patterns in VB.NET, C#, Python, JavaScript, and other
    languages to build complete authorization matrices.
    """

    # Extended AUTH_PATTERNS for comprehensive detection
    AUTH_PATTERNS = {
        "vbnet": [
            # Permission checks
            r"\bintCan(Add|Edit|View|Delete|Approve|Reject|Manage|Export)\b",
            r"\bblnHas(Right|Permission|Access|Role)\b",
            r"\bCheck(Rights?|Permissions?|Access)\s*\(",
            r"\bValidate(User|Access|Permission)\s*\(",
            r"\bIs(Admin|Manager|User|Guest|Authorized)\b",
            r"\bHas(Permission|Access|Right)\s*\(",
            # Role checks
            r"\bUser\.Role\s*=\s*[\"']?(\w+)[\"']?",
            r"\bstrUserRole\s*=\s*[\"']?(\w+)[\"']?",
            r"\bintUserLevel\s*[><=]+\s*(\d+)",
            r"\bUser\.IsInRole\s*\(\s*[\"'](\w+)[\"']\s*\)",
        ],
        "csharp": [
            # Attributes
            r"\[Authorize\s*\]",
            r"\[Authorize\s*\(\s*Roles\s*=\s*[\"'](.+?)[\"']\s*\)\]",
            r"\[Authorize\s*\(\s*Policy\s*=\s*[\"'](.+?)[\"']\s*\)\]",
            r"\[AllowAnonymous\s*\]",
            # Method checks
            r"User\.IsInRole\s*\(\s*[\"'](\w+)[\"']\s*\)",
            r"User\.HasClaim\s*\(",
            r"ClaimsPrincipal",
            r"\.RequireRole\s*\(\s*[\"'](\w+)[\"']\s*\)",
            r"\.RequireClaim\s*\(",
            # Policy
            r"policy\.RequireRole\s*\(\s*[\"'](\w+)[\"']\s*\)",
            r"AddPolicy\s*\(\s*[\"'](\w+)[\"']\s*,",
        ],
        "python": [
            # Decorators
            r"@login_required",
            r"@permission_required\s*\(\s*[\"'](.+?)[\"']\s*\)",
            r"@user_passes_test\s*\(",
            r"@staff_member_required",
            r"@superuser_required",
            # Django
            r"\.has_perm\s*\(\s*[\"'](.+?)[\"']\s*\)",
            r"\.has_perms\s*\(",
            r"user\.is_staff",
            r"user\.is_superuser",
            r"user\.groups\.filter\s*\(",
            # Flask
            r"@roles_required\s*\(\s*[\"'](.+?)[\"']\s*\)",
            r"@roles_accepted\s*\(",
            r"current_user\.has_role\s*\(",
        ],
        "javascript": [
            # Express/Node
            r"req\.user\.role\s*===?\s*[\"'](\w+)[\"']",
            r"passport\.authenticate\s*\(",
            r"isAuthenticated\s*\(",
            r"checkRole\s*\(\s*[\"'](\w+)[\"']\s*\)",
            # Guards
            r"@UseGuards\s*\(",
            r"@Roles\s*\(\s*[\"'](.+?)[\"']\s*\)",
            r"CanActivate",
            # JWT
            r"jwt\.verify\s*\(",
            r"req\.user\.permissions",
        ],
    }

    # Role name patterns
    ROLE_PATTERNS = {
        "vbnet": [
            r"(?:Public\s+)?Enum\s+(\w*[Rr]ole\w*)\s*(.*?)End\s+Enum",
            r"Const\s+ROLE_(\w+)\s*=",
            r"Case\s+[\"']?(Admin|Manager|User|Guest|Viewer|Editor)[\"']?",
        ],
        "csharp": [
            r"(?:public\s+)?enum\s+(\w*[Rr]ole\w*)\s*\{(.*?)\}",
            r"const\s+string\s+(\w*Role\w*)\s*=\s*[\"'](\w+)[\"']",
            r"public\s+static\s+readonly\s+string\s+(\w*Role\w*)",
        ],
        "python": [
            r"class\s+(\w*[Rr]ole\w*)\s*\(.*?Enum.*?\)\s*:",
            r"ROLE_(\w+)\s*=\s*[\"'](\w+)[\"']",
            r"(\w+)\s*=\s*[\"'](admin|manager|user|guest|viewer|editor)[\"']",
        ],
        "javascript": [
            r"(?:const|let|var)\s+(\w*[Rr]oles?\w*)\s*=\s*\{(.*?)\}",
            r"ROLE_(\w+)\s*[:=]\s*[\"'](\w+)[\"']",
            r"enum\s+(\w*[Rr]ole\w*)\s*\{(.*?)\}",
        ],
    }

    # Permission name patterns
    PERMISSION_PATTERNS = {
        "vbnet": [
            r"(?:Public\s+)?Enum\s+(\w*[Pp]ermission\w*)\s*(.*?)End\s+Enum",
            r"Const\s+PERM_(\w+)\s*=",
            r"intCan(\w+)",
        ],
        "csharp": [
            r"(?:public\s+)?enum\s+(\w*[Pp]ermission\w*)\s*\{(.*?)\}",
            r"const\s+string\s+(\w*Permission\w*)\s*=",
            r"Can(\w+)\s*\(\)",
        ],
        "python": [
            r"class\s+(\w*[Pp]ermission\w*)\s*\(.*?Enum.*?\)\s*:",
            r"PERMISSION_(\w+)\s*=",
            r"can_(\w+)",
        ],
        "javascript": [
            r"(?:const|let|var)\s+(\w*[Pp]ermissions?\w*)\s*=\s*\{(.*?)\}",
            r"PERMISSION_(\w+)\s*[:=]",
            r"can(\w+)\s*\(",
        ],
    }

    # Resource/endpoint patterns
    RESOURCE_PATTERNS = {
        "vbnet": [
            r"\.aspx[\"']?\s*,?\s*[\"']?(\w+)[\"']?",  # ASPX pages
            r"Protected\s+Sub\s+Page_Load",  # Protected pages
            r"<location\s+path\s*=\s*[\"'](.+?)[\"']",  # Web.config
        ],
        "csharp": [
            r"\[HttpGet\s*\(\s*[\"'](.+?)[\"']\s*\)\]",
            r"\[HttpPost\s*\(\s*[\"'](.+?)[\"']\s*\)\]",
            r"\[Route\s*\(\s*[\"'](.+?)[\"']\s*\)\]",
            r"MapGet\s*\(\s*[\"'](.+?)[\"']",
            r"MapPost\s*\(\s*[\"'](.+?)[\"']",
        ],
        "python": [
            r"@app\.route\s*\(\s*[\"'](.+?)[\"']",
            r"path\s*\(\s*[\"'](.+?)[\"']",
            r"url\s*\(\s*r?[\"'](.+?)[\"']",
        ],
        "javascript": [
            r"router\.get\s*\(\s*[\"'](.+?)[\"']",
            r"router\.post\s*\(\s*[\"'](.+?)[\"']",
            r"app\.get\s*\(\s*[\"'](.+?)[\"']",
            r"app\.post\s*\(\s*[\"'](.+?)[\"']",
        ],
    }

    # Common role names mapped to levels
    ROLE_LEVEL_MAPPING = {
        "admin": RoleLevel.ADMIN,
        "administrator": RoleLevel.ADMIN,
        "sysadmin": RoleLevel.SYSTEM,
        "superuser": RoleLevel.SYSTEM,
        "manager": RoleLevel.MANAGER,
        "supervisor": RoleLevel.MANAGER,
        "poweruser": RoleLevel.POWER_USER,
        "user": RoleLevel.USER,
        "member": RoleLevel.USER,
        "viewer": RoleLevel.USER,
        "guest": RoleLevel.GUEST,
        "anonymous": RoleLevel.ANONYMOUS,
    }

    # Permission type mapping
    PERMISSION_TYPE_MAPPING = {
        "create": PermissionType.CREATE,
        "add": PermissionType.CREATE,
        "new": PermissionType.CREATE,
        "insert": PermissionType.CREATE,
        "read": PermissionType.READ,
        "view": PermissionType.VIEW,
        "get": PermissionType.READ,
        "list": PermissionType.READ,
        "update": PermissionType.UPDATE,
        "edit": PermissionType.EDIT,
        "modify": PermissionType.UPDATE,
        "delete": PermissionType.DELETE,
        "remove": PermissionType.DELETE,
        "execute": PermissionType.EXECUTE,
        "run": PermissionType.EXECUTE,
        "approve": PermissionType.APPROVE,
        "reject": PermissionType.REJECT,
        "manage": PermissionType.MANAGE,
        "admin": PermissionType.ADMIN,
        "export": PermissionType.EXPORT,
        "import": PermissionType.IMPORT,
    }

    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize the service"""
        self.db = db
        self._sessions: Dict[str, AuthorizationExtractionResult] = {}

    async def create_session(
        self,
        project_id: Optional[str] = None,
        name: str = "Authorization Matrix Extraction"
    ) -> str:
        """Create a new extraction session"""
        session_id = str(uuid4())
        result = AuthorizationExtractionResult(
            session_id=session_id,
            project_id=project_id,
            started_at=datetime.now(timezone.utc)
        )
        self._sessions[session_id] = result
        logger.info(f"Created authorization extraction session: {session_id}")
        return session_id

    async def get_session(self, session_id: str) -> Optional[AuthorizationExtractionResult]:
        """Get an extraction session"""
        return self._sessions.get(session_id)

    async def extract_from_files(
        self,
        session_id: str,
        files: Dict[str, str],
        language: str = "vbnet"
    ) -> AuthorizationExtractionResult:
        """
        Extract authorization matrix from source files.

        Args:
            session_id: The extraction session ID
            files: Dict mapping file paths to file contents
            language: Programming language

        Returns:
            AuthorizationExtractionResult with extracted matrix
        """
        result = self._sessions.get(session_id)
        if not result:
            result = AuthorizationExtractionResult(session_id=session_id)
            self._sessions[session_id] = result

        result.total_files_scanned = len(files)

        # Initialize matrix
        matrix = AuthorizationMatrix(
            name=f"Authorization Matrix - {session_id[:8]}",
            description="Extracted from legacy code analysis",
            source_files=list(files.keys())
        )

        # Extract from each file
        for file_path, content in files.items():
            try:
                has_auth = await self._extract_from_file(
                    matrix, content, file_path, language
                )
                if has_auth:
                    result.files_with_auth += 1
            except Exception as e:
                logger.error(f"Error extracting from {file_path}: {e}")
                result.errors.append(f"{file_path}: {str(e)}")

        # Post-process and analyze
        await self._infer_role_hierarchy(matrix)
        await self._detect_conflicts(matrix)
        matrix.statistics = self._calculate_statistics(matrix)
        matrix.confidence = self._calculate_confidence(matrix)

        result.matrix = matrix
        result.average_confidence = matrix.confidence

        result.completed_at = datetime.now(timezone.utc)
        result.duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()

        return result

    async def _extract_from_file(
        self,
        matrix: AuthorizationMatrix,
        content: str,
        file_path: str,
        language: str
    ) -> bool:
        """Extract authorization patterns from a single file"""
        has_auth = False

        # Extract roles
        roles = await self._extract_roles(content, file_path, language)
        for role in roles:
            if not any(r.name == role.name for r in matrix.roles):
                matrix.roles.append(role)
                has_auth = True

        # Extract permissions
        permissions = await self._extract_permissions(content, file_path, language)
        for perm in permissions:
            if not any(p.name == perm.name for p in matrix.permissions):
                matrix.permissions.append(perm)
                has_auth = True

        # Extract resources
        resources = await self._extract_resources(content, file_path, language)
        for res in resources:
            if not any(r.name == res.name for r in matrix.resources):
                matrix.resources.append(res)
                has_auth = True

        # Extract mappings from auth checks
        mappings = await self._extract_mappings(
            content, file_path, language, matrix
        )
        matrix.mappings.extend(mappings)
        if mappings:
            has_auth = True

        return has_auth

    async def _extract_roles(
        self,
        content: str,
        file_path: str,
        language: str
    ) -> List[ExtractedRole]:
        """Extract role definitions from code"""
        roles = []
        patterns = self.ROLE_PATTERNS.get(language, [])

        for pattern in patterns:
            try:
                for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                    groups = match.groups()

                    if len(groups) >= 1:
                        role_name = groups[0]

                        # Parse enum body if available
                        if len(groups) >= 2 and groups[1]:
                            enum_body = groups[1]
                            enum_roles = self._parse_enum_values(enum_body, language)
                            for enum_role in enum_roles:
                                role = ExtractedRole(
                                    name=enum_role,
                                    display_name=self._humanize_name(enum_role),
                                    level=self._infer_role_level(enum_role),
                                    source_file=file_path,
                                    source_line=content[:match.start()].count('\n') + 1,
                                    confidence=0.9
                                )
                                roles.append(role)
                        else:
                            role = ExtractedRole(
                                name=role_name,
                                display_name=self._humanize_name(role_name),
                                level=self._infer_role_level(role_name),
                                source_file=file_path,
                                source_line=content[:match.start()].count('\n') + 1,
                                confidence=0.85
                            )
                            roles.append(role)
            except re.error:
                continue

        # Also extract roles from auth checks
        auth_patterns = self.AUTH_PATTERNS.get(language, [])
        for pattern in auth_patterns:
            try:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    groups = match.groups()
                    for group in groups:
                        if group and self._looks_like_role(group):
                            role = ExtractedRole(
                                name=group,
                                display_name=self._humanize_name(group),
                                level=self._infer_role_level(group),
                                source_file=file_path,
                                source_line=content[:match.start()].count('\n') + 1,
                                confidence=0.7
                            )
                            if not any(r.name == role.name for r in roles):
                                roles.append(role)
            except re.error:
                continue

        return roles

    async def _extract_permissions(
        self,
        content: str,
        file_path: str,
        language: str
    ) -> List[ExtractedPermission]:
        """Extract permission definitions from code"""
        permissions = []
        patterns = self.PERMISSION_PATTERNS.get(language, [])

        for pattern in patterns:
            try:
                for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                    groups = match.groups()

                    if len(groups) >= 1:
                        perm_name = groups[0]

                        if len(groups) >= 2 and groups[1]:
                            # Enum body
                            enum_body = groups[1]
                            enum_perms = self._parse_enum_values(enum_body, language)
                            for enum_perm in enum_perms:
                                perm = ExtractedPermission(
                                    name=enum_perm,
                                    display_name=self._humanize_name(enum_perm),
                                    permission_type=self._infer_permission_type(enum_perm),
                                    source_file=file_path,
                                    source_line=content[:match.start()].count('\n') + 1,
                                    confidence=0.9
                                )
                                permissions.append(perm)
                        else:
                            perm = ExtractedPermission(
                                name=perm_name,
                                display_name=self._humanize_name(perm_name),
                                permission_type=self._infer_permission_type(perm_name),
                                source_file=file_path,
                                source_line=content[:match.start()].count('\n') + 1,
                                confidence=0.85
                            )
                            permissions.append(perm)
            except re.error:
                continue

        return permissions

    async def _extract_resources(
        self,
        content: str,
        file_path: str,
        language: str
    ) -> List[ExtractedResource]:
        """Extract protected resources from code"""
        resources = []
        patterns = self.RESOURCE_PATTERNS.get(language, [])

        for pattern in patterns:
            try:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    groups = match.groups()

                    for group in groups:
                        if group:
                            resource = ExtractedResource(
                                name=self._normalize_resource_name(group),
                                display_name=group,
                                resource_type=self._infer_resource_type(group, file_path),
                                path=group,
                                source_file=file_path,
                                source_line=content[:match.start()].count('\n') + 1,
                                confidence=0.8
                            )
                            if not any(r.name == resource.name for r in resources):
                                resources.append(resource)
            except re.error:
                continue

        return resources

    async def _extract_mappings(
        self,
        content: str,
        file_path: str,
        language: str,
        matrix: AuthorizationMatrix
    ) -> List[RolePermissionMapping]:
        """Extract role-permission mappings from auth checks"""
        mappings = []
        auth_patterns = self.AUTH_PATTERNS.get(language, [])

        for pattern in auth_patterns:
            try:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    matched_text = match.group(0)
                    groups = match.groups()

                    # Try to identify role and permission from context
                    role_id = None
                    permission_id = None
                    resource_id = None

                    for group in groups:
                        if group:
                            # Check if it's a role
                            role = next(
                                (r for r in matrix.roles if r.name.lower() == group.lower()),
                                None
                            )
                            if role:
                                role_id = role.id
                                continue

                            # Check if it's a permission
                            perm = next(
                                (p for p in matrix.permissions if group.lower() in p.name.lower()),
                                None
                            )
                            if perm:
                                permission_id = perm.id
                                continue

                    # Infer from pattern type
                    if "Can" in matched_text or "Has" in matched_text:
                        # Permission check
                        perm_name = self._extract_permission_from_check(matched_text)
                        if perm_name:
                            perm = next(
                                (p for p in matrix.permissions if p.name == perm_name),
                                None
                            )
                            if not perm:
                                perm = ExtractedPermission(
                                    name=perm_name,
                                    display_name=self._humanize_name(perm_name),
                                    permission_type=self._infer_permission_type(perm_name),
                                    source_file=file_path,
                                    confidence=0.75
                                )
                                matrix.permissions.append(perm)
                            permission_id = perm.id

                    if role_id and permission_id:
                        mapping = RolePermissionMapping(
                            role_id=role_id,
                            permission_id=permission_id,
                            resource_id=resource_id,
                            is_granted=True,
                            source_file=file_path,
                            source_line=content[:match.start()].count('\n') + 1,
                            source_code=matched_text[:100],
                            confidence=0.8
                        )
                        mappings.append(mapping)

            except re.error:
                continue

        return mappings

    async def _infer_role_hierarchy(self, matrix: AuthorizationMatrix):
        """Infer role hierarchy from role levels"""
        # Sort roles by level
        level_order = [
            RoleLevel.SYSTEM,
            RoleLevel.ADMIN,
            RoleLevel.MANAGER,
            RoleLevel.POWER_USER,
            RoleLevel.USER,
            RoleLevel.GUEST,
            RoleLevel.ANONYMOUS,
        ]

        sorted_roles = sorted(
            matrix.roles,
            key=lambda r: level_order.index(r.level) if r.level in level_order else 999
        )

        # Assign parent roles
        prev_role = None
        for role in sorted_roles:
            if prev_role and prev_role.level != role.level:
                role.parent_role = prev_role.name
                # Inherit permissions from parent
                role.inherited_permissions = matrix.get_role_permissions(prev_role.name)
            prev_role = role

    async def _detect_conflicts(self, matrix: AuthorizationMatrix):
        """Detect authorization conflicts and issues"""
        conflicts = []

        # Check for orphan roles (no permissions)
        for role in matrix.roles:
            perms = [m for m in matrix.mappings if m.role_id == role.id]
            if not perms and not role.parent_role:
                conflicts.append(AuthorizationConflict(
                    conflict_type=ConflictType.ORPHAN_ROLE,
                    severity="low",
                    description=f"Role '{role.name}' has no direct permissions",
                    affected_roles=[role.name],
                    recommendation="Assign permissions or remove unused role"
                ))

        # Check for orphan permissions (not assigned to any role)
        for perm in matrix.permissions:
            mappings = [m for m in matrix.mappings if m.permission_id == perm.id]
            if not mappings:
                conflicts.append(AuthorizationConflict(
                    conflict_type=ConflictType.ORPHAN_PERMISSION,
                    severity="medium",
                    description=f"Permission '{perm.name}' is not assigned to any role",
                    affected_permissions=[perm.name],
                    recommendation="Assign to appropriate roles or remove"
                ))

        # Check for resources without protection
        protected_resources = {m.resource_id for m in matrix.mappings if m.resource_id}
        for resource in matrix.resources:
            if resource.id not in protected_resources:
                conflicts.append(AuthorizationConflict(
                    conflict_type=ConflictType.INCOMPLETE_COVERAGE,
                    severity="high",
                    description=f"Resource '{resource.name}' has no authorization rules",
                    affected_resources=[resource.name],
                    recommendation="Add authorization checks"
                ))

        matrix.conflicts = conflicts

    def _calculate_statistics(
        self,
        matrix: AuthorizationMatrix
    ) -> AuthorizationMatrixStatistics:
        """Calculate statistics for the authorization matrix"""
        stats = AuthorizationMatrixStatistics(
            total_roles=len(matrix.roles),
            total_permissions=len(matrix.permissions),
            total_resources=len(matrix.resources),
            total_mappings=len(matrix.mappings),
            total_conflicts=len(matrix.conflicts)
        )

        # Coverage percentage
        if matrix.resources:
            protected = len({m.resource_id for m in matrix.mappings if m.resource_id})
            stats.coverage_percentage = protected / len(matrix.resources) * 100

        # Role hierarchy depth
        max_depth = 0
        for role in matrix.roles:
            depth = 0
            current = role
            while current.parent_role:
                depth += 1
                current = next(
                    (r for r in matrix.roles if r.name == current.parent_role),
                    None
                )
                if not current:
                    break
            max_depth = max(max_depth, depth)
        stats.role_hierarchy_depth = max_depth

        # Average permissions per role
        if matrix.roles:
            total_perms = sum(
                len([m for m in matrix.mappings if m.role_id == r.id])
                for r in matrix.roles
            )
            stats.average_permissions_per_role = total_perms / len(matrix.roles)

        # Conflict severity counts
        stats.critical_conflicts = len([c for c in matrix.conflicts if c.severity == "critical"])
        stats.high_conflicts = len([c for c in matrix.conflicts if c.severity == "high"])

        return stats

    def _calculate_confidence(self, matrix: AuthorizationMatrix) -> float:
        """Calculate overall confidence score"""
        if not matrix.roles and not matrix.permissions:
            return 0.0

        scores = []
        scores.extend(r.confidence for r in matrix.roles)
        scores.extend(p.confidence for p in matrix.permissions)
        scores.extend(m.confidence for m in matrix.mappings)

        if not scores:
            return 0.5

        return sum(scores) / len(scores)

    # Helper methods

    def _parse_enum_values(self, enum_body: str, language: str) -> List[str]:
        """Parse enum values"""
        values = []

        if language == "vbnet":
            for match in re.finditer(r"^\s*(\w+)\s*(?:=\s*\d+)?", enum_body, re.MULTILINE):
                val = match.group(1).strip()
                if val:
                    values.append(val)
        elif language in ["csharp", "javascript"]:
            for match in re.finditer(r"(\w+)\s*(?:=\s*\d+)?[,\}]?", enum_body):
                val = match.group(1).strip()
                if val:
                    values.append(val)
        elif language == "python":
            for match in re.finditer(r"^\s*(\w+)\s*=", enum_body, re.MULTILINE):
                val = match.group(1).strip()
                if val:
                    values.append(val)

        return values

    def _humanize_name(self, name: str) -> str:
        """Convert code name to human-readable"""
        # Remove common prefixes
        prefixes = ["str", "int", "bln", "Can", "Has", "Is"]
        result = name
        for prefix in prefixes:
            if result.startswith(prefix) and len(result) > len(prefix):
                result = result[len(prefix):]
                break

        # Convert to title case with spaces
        result = re.sub(r'([A-Z])', r' \1', result)
        result = re.sub(r'_+', ' ', result)
        return result.strip().title()

    def _infer_role_level(self, role_name: str) -> RoleLevel:
        """Infer role level from name"""
        name_lower = role_name.lower()
        for keyword, level in self.ROLE_LEVEL_MAPPING.items():
            if keyword in name_lower:
                return level
        return RoleLevel.USER

    def _infer_permission_type(self, perm_name: str) -> PermissionType:
        """Infer permission type from name"""
        name_lower = perm_name.lower()
        for keyword, ptype in self.PERMISSION_TYPE_MAPPING.items():
            if keyword in name_lower:
                return ptype
        return PermissionType.READ

    def _infer_resource_type(self, name: str, file_path: str) -> ResourceType:
        """Infer resource type from name and file"""
        name_lower = name.lower()

        if ".aspx" in name_lower or ".html" in name_lower:
            return ResourceType.PAGE
        elif "/api/" in name_lower or "endpoint" in name_lower:
            return ResourceType.ENDPOINT
        elif file_path and "controller" in file_path.lower():
            return ResourceType.ACTION
        else:
            return ResourceType.FEATURE

    def _normalize_resource_name(self, name: str) -> str:
        """Normalize resource name"""
        # Remove leading/trailing slashes
        result = name.strip("/")
        # Replace special chars
        result = re.sub(r"[^a-zA-Z0-9_]", "_", result)
        return result.lower()

    def _looks_like_role(self, name: str) -> bool:
        """Check if name looks like a role"""
        role_keywords = ["admin", "manager", "user", "guest", "viewer", "editor", "role"]
        return any(kw in name.lower() for kw in role_keywords)

    def _extract_permission_from_check(self, check_text: str) -> Optional[str]:
        """Extract permission name from auth check"""
        # intCanAdd -> Add
        match = re.search(r"Can(\w+)", check_text, re.IGNORECASE)
        if match:
            return match.group(1)

        # HasPermission("xyz") -> xyz
        match = re.search(r"Has(?:Permission|Right)\s*\(\s*[\"'](\w+)[\"']", check_text, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    # Export methods

    async def export_to_markdown(self, matrix: AuthorizationMatrix) -> str:
        """Export authorization matrix to Markdown"""
        lines = [
            f"# Authorization Matrix: {matrix.name}",
            "",
            f"**Description:** {matrix.description}",
            f"**Confidence:** {matrix.confidence:.0%}",
            "",
            "## Roles",
            "",
            "| Role | Level | Parent | Description |",
            "|------|-------|--------|-------------|",
        ]

        for role in matrix.roles:
            parent = role.parent_role or "-"
            lines.append(f"| {role.name} | {role.level.value} | {parent} | {role.description} |")

        lines.extend([
            "",
            "## Permissions",
            "",
            "| Permission | Type | Description |",
            "|------------|------|-------------|",
        ])

        for perm in matrix.permissions:
            lines.append(f"| {perm.name} | {perm.permission_type.value} | {perm.description} |")

        lines.extend([
            "",
            "## Authorization Matrix",
            "",
        ])

        # Build matrix table
        if matrix.roles and matrix.permissions:
            # Header row
            header = "| Role |"
            for perm in matrix.permissions[:10]:  # Limit columns
                header += f" {perm.name[:15]} |"
            lines.append(header)

            # Separator
            sep = "|------|"
            for _ in matrix.permissions[:10]:
                sep += "---|"
            lines.append(sep)

            # Data rows
            for role in matrix.roles:
                row = f"| {role.name} |"
                for perm in matrix.permissions[:10]:
                    has_perm = any(
                        m.role_id == role.id and m.permission_id == perm.id and m.is_granted
                        for m in matrix.mappings
                    )
                    row += " ✓ |" if has_perm else " - |"
                lines.append(row)

        # Conflicts
        if matrix.conflicts:
            lines.extend([
                "",
                "## Conflicts & Issues",
                "",
                "| Type | Severity | Description | Recommendation |",
                "|------|----------|-------------|----------------|",
            ])

            for conflict in matrix.conflicts:
                lines.append(
                    f"| {conflict.conflict_type.value} | {conflict.severity} | "
                    f"{conflict.description} | {conflict.recommendation} |"
                )

        return "\n".join(lines)

    async def export_to_csv(self, matrix: AuthorizationMatrix) -> str:
        """Export authorization matrix to CSV"""
        lines = []

        # Header
        header = ["Role"]
        for perm in matrix.permissions:
            header.append(perm.name)
        lines.append(",".join(header))

        # Data rows
        for role in matrix.roles:
            row = [role.name]
            for perm in matrix.permissions:
                has_perm = any(
                    m.role_id == role.id and m.permission_id == perm.id and m.is_granted
                    for m in matrix.mappings
                )
                row.append("1" if has_perm else "0")
            lines.append(",".join(row))

        return "\n".join(lines)

    async def export_to_format(
        self,
        matrix: AuthorizationMatrix,
        format: AuthorizationMatrixOutputFormat
    ) -> str:
        """Export matrix to specified format"""
        if format == AuthorizationMatrixOutputFormat.MARKDOWN:
            return await self.export_to_markdown(matrix)
        elif format == AuthorizationMatrixOutputFormat.CSV:
            return await self.export_to_csv(matrix)
        elif format == AuthorizationMatrixOutputFormat.JSON:
            import json
            return json.dumps(matrix.to_dict(), indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def export_session(
        self,
        session_id: str,
        format: AuthorizationMatrixOutputFormat = AuthorizationMatrixOutputFormat.MARKDOWN
    ) -> str:
        """Export the matrix from a session"""
        result = self._sessions.get(session_id)
        if not result or not result.matrix:
            raise ValueError(f"Session {session_id} not found or has no matrix")

        return await self.export_to_format(result.matrix, format)
