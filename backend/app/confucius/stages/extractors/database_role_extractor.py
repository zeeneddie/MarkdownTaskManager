"""
Database Role Extractor.

Extracts user roles and permissions from database schemas and queries.
"""

import re
from typing import Dict, Any, List
from .base import BaseJourneyExtractor


class DatabaseRoleExtractor(BaseJourneyExtractor):
    """
    Extract user roles and permissions from database artifacts.

    Analyzes:
    - SQL schema files for user/role tables
    - Stored procedures for role checks
    - Entity Framework models
    - Database migrations
    """

    def __init__(self):
        """Initialize extractor."""
        super().__init__()
        self.supported_extensions = [".sql", ".cs", ".py"]

    def supports_stack(self, tech_stack: List[str]) -> bool:
        """Check if this extractor supports the given tech stack."""
        # This extractor works with most stacks that use databases
        db_identifiers = [
            "sql", "mssql", "mysql", "postgresql", "postgres",
            "oracle", "sqlite", "ef", "entity framework",
            "dapper", "sqlalchemy", "prisma", "sequelize"
        ]
        return any(
            t.lower() in db_identifiers
            for t in tech_stack
        )

    async def extract(
        self,
        files: List[Dict[str, Any]],
        code_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract role data from database artifacts."""
        result = self._get_empty_result()

        # Extract from SQL files
        sql_files = self._find_files_by_extension(files, [".sql"])
        for f in sql_files:
            self._extract_from_sql(f, result)

        # Extract from Entity Framework models
        cs_files = self._find_files_by_extension(files, [".cs"])
        for f in cs_files:
            if any(keyword in f.get("path", "").lower() for keyword in [
                "model", "entity", "migration", "context"
            ]):
                self._extract_from_ef_model(f, result)

        # Extract from Python ORM models
        py_files = self._find_files_by_extension(files, [".py"])
        for f in py_files:
            if "model" in f.get("path", "").lower():
                self._extract_from_python_model(f, result)

        return result

    def _extract_from_sql(
        self,
        file: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract from SQL schema/scripts."""
        content = file.get("content", "")
        path = file.get("path", "")

        if not content:
            return

        # Extract from CREATE TABLE for Users/Roles
        self._extract_from_user_tables(content, path, result)

        # Extract from stored procedures
        self._extract_from_stored_procs(content, path, result)

        # Extract from INSERT statements (seed data)
        self._extract_from_insert_statements(content, path, result)

    def _extract_from_user_tables(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract role information from user/role table definitions."""
        # Look for role-related tables
        table_patterns = [
            r'CREATE\s+TABLE\s+(?:\[?dbo\]?\.)?\[?(\w*Role\w*)\]?\s*\(',
            r'CREATE\s+TABLE\s+(?:\[?dbo\]?\.)?\[?(\w*User\w*)\]?\s*\(',
            r'CREATE\s+TABLE\s+(?:\[?dbo\]?\.)?\[?(\w*Permission\w*)\]?\s*\(',
        ]

        for pattern in table_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for table_name in matches:
                # This is a role-related table, look for role values
                self._extract_roles_from_table_definition(
                    content, table_name, path, result
                )

        # Extract from CHECK constraints with role values
        check_pattern = r"CHECK\s*\(\s*\[?Role\]?\s+IN\s*\(([^)]+)\)"
        matches = re.findall(check_pattern, content, re.IGNORECASE)
        for match in matches:
            roles = re.findall(r"'(\w+)'", match)
            for role in roles:
                self._add_role(role, path, "check_constraint", result)

    def _extract_roles_from_table_definition(
        self,
        content: str,
        table_name: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract role values from table definition area."""
        # Find the CREATE TABLE block
        table_pattern = rf'CREATE\s+TABLE[^;]+{table_name}[^;]+;'
        table_match = re.search(table_pattern, content, re.IGNORECASE | re.DOTALL)

        if table_match:
            table_content = table_match.group(0)

            # Look for ENUM-like definitions
            enum_pattern = r"IN\s*\(([^)]+)\)"
            enum_matches = re.findall(enum_pattern, table_content, re.IGNORECASE)
            for match in enum_matches:
                roles = re.findall(r"'(\w+)'", match)
                for role in roles:
                    self._add_role(role, path, "table_enum", result)

    def _extract_from_stored_procs(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract role checks from stored procedures."""
        # Look for role parameters and checks
        role_check_patterns = [
            # @Role parameter
            r'@Role\s+(?:NVARCHAR|VARCHAR|INT)[^,)]+',
            # WHERE Role = @Role
            r"WHERE[^;]*Role\s*=\s*'(\w+)'",
            # IF @Role = 'Admin'
            r"IF\s+@Role\s*=\s*'(\w+)'",
            # Role IN ('Admin', 'User')
            r"Role\s+IN\s*\(([^)]+)\)",
        ]

        for pattern in role_check_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if "'" in match:
                    # Extract role names from IN clause
                    roles = re.findall(r"'(\w+)'", match)
                    for role in roles:
                        self._add_role(role, path, "stored_proc", result)
                elif match and not match.startswith("@"):
                    self._add_role(match, path, "stored_proc", result)

    def _extract_from_insert_statements(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract role values from INSERT seed data."""
        # Look for role inserts
        insert_patterns = [
            # INSERT INTO Roles VALUES (1, 'Admin')
            r"INSERT\s+INTO\s+(?:\[?dbo\]?\.)?\[?\w*Role\w*\]?\s*(?:\([^)]+\))?\s*VALUES\s*\([^)]*'(\w+)'",
            # INSERT INTO UserRoles
            r"INSERT\s+INTO\s+(?:\[?dbo\]?\.)?\[?\w*UserRole\w*\]?",
        ]

        for pattern in insert_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match:
                    self._add_role(match, path, "seed_data", result)

    def _extract_from_ef_model(
        self,
        file: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract from Entity Framework models."""
        content = file.get("content", "")
        path = file.get("path", "")

        if not content:
            return

        # Look for role-related classes
        role_class_patterns = [
            r'class\s+(\w*Role\w*)\s*(?::\s*\w+)?',
            r'class\s+(\w*User\w*)\s*(?::\s*\w+)?',
            r'enum\s+(\w*Role\w*)',
        ]

        for pattern in role_class_patterns:
            matches = re.findall(pattern, content)
            for class_name in matches:
                # Look for enum values
                if "enum" in pattern:
                    self._extract_enum_values(content, class_name, path, result)

        # Look for role property definitions
        property_patterns = [
            # public string Role { get; set; }
            r'public\s+string\s+(Role|UserRole|RoleName)\s*{',
            # public RoleType Role { get; set; }
            r'public\s+(\w*Role\w*Type?)\s+Role\s*{',
        ]

        for pattern in property_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # This file has role-related properties
                # Try to find seed data or enum values
                self._extract_seed_data_from_ef(content, path, result)

    def _extract_enum_values(
        self,
        content: str,
        enum_name: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract values from enum definition."""
        enum_pattern = rf'enum\s+{enum_name}\s*{{([^}}]+)}}'
        match = re.search(enum_pattern, content, re.DOTALL)

        if match:
            enum_body = match.group(1)
            # Extract enum members
            members = re.findall(r'\b(\w+)\s*(?:=|,|$)', enum_body)
            for member in members:
                if member and not member.isdigit():
                    self._add_role(member, path, "enum", result)

    def _extract_seed_data_from_ef(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract seed data from Entity Framework configurations."""
        # Look for HasData calls
        seed_patterns = [
            r'\.HasData\s*\([^)]*Role\s*=\s*"(\w+)"',
            r'\.HasData\s*\([^)]*new\s*{\s*[^}]*Role\s*=\s*"(\w+)"',
            r'new\s+\w*Role\w*\s*{[^}]*Name\s*=\s*"(\w+)"',
        ]

        for pattern in seed_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for role in matches:
                self._add_role(role, path, "ef_seed", result)

    def _extract_from_python_model(
        self,
        file: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract from Python ORM models (SQLAlchemy, Django, etc.)."""
        content = file.get("content", "")
        path = file.get("path", "")

        if not content:
            return

        # Look for role-related models
        model_patterns = [
            # class Role(Model):
            r'class\s+(\w*Role\w*)\s*\(',
            # role = Column(Enum('admin', 'user'))
            r"Column\s*\(\s*Enum\s*\(([^)]+)\)",
            # ROLE_CHOICES = [('admin', 'Admin')]
            r"ROLE_CHOICES\s*=\s*\[([^\]]+)\]",
            # role = models.CharField(choices=...)
            r"choices\s*=\s*\[([^\]]+)\]",
        ]

        for pattern in model_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if "'" in match or '"' in match:
                    # Extract string values
                    roles = re.findall(r"['\"](\w+)['\"]", match)
                    for role in roles:
                        self._add_role(role, path, "python_model", result)

    def _add_role(
        self,
        role: str,
        source: str,
        check_type: str,
        result: Dict[str, Any],
    ):
        """Add role to result if not already present."""
        role = self._normalize_role_name(role)
        if not role:
            return

        # Skip common non-role words
        skip_words = {
            "ID", "NAME", "TYPE", "VALUE", "TABLE", "COLUMN",
            "NULL", "NOT", "VARCHAR", "INT", "BIT", "DATETIME"
        }
        if role in skip_words:
            return

        # Add to roles list
        existing_roles = [r.get("name", "").upper() for r in result["roles"]]
        if role not in existing_roles:
            result["roles"].append({
                "name": role,
                "source": source,
                "check_type": check_type,
            })

        # Add auth check
        result["auth_checks"].append({
            "role": role,
            "file": source,
            "type": check_type,
        })
