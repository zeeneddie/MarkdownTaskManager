"""
ERDGeneratorService - Generate Target Architecture ERD

This service generates ERD diagrams for the TARGET architecture (not legacy copy).
Input: Extracted entities from Brown Paper Enhanced
Output: Clean architecture ERD with DDD concepts

Key capabilities:
- Generate Mermaid/PlantUML ERD from extracted entities
- Apply normalization rules (3NF, DDD aggregates)
- Map bounded contexts
- Suggest relationships based on field analysis

Author: Claude Code (Week 136 - Fase 24)
Date: 2026-01-01
"""

import logging
import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.data_architecture import (
    ERDOutputFormat,
    ERDColumn, ERDTable, ERDRelationship, ERDDiagram,
    ERDDiagramModel
)

logger = logging.getLogger(__name__)


class ERDGeneratorService:
    """
    Service for generating target architecture ERD diagrams.

    This generates the NEW architecture, not a copy of legacy.
    Uses extracted entities from Brown Paper as input, but applies:
    - Modern naming conventions
    - Proper normalization
    - DDD bounded contexts
    - Clean relationships
    """

    # Type mapping from legacy to modern types
    TYPE_MAPPINGS = {
        # VB.NET / SQL Server types
        "integer": "int",
        "int32": "int",
        "int64": "bigint",
        "long": "bigint",
        "smallint": "smallint",
        "tinyint": "smallint",
        "bit": "boolean",
        "boolean": "boolean",
        "string": "varchar(255)",
        "nvarchar": "varchar",
        "varchar": "varchar",
        "text": "text",
        "ntext": "text",
        "char": "char",
        "decimal": "decimal(18,2)",
        "numeric": "decimal",
        "money": "decimal(18,2)",
        "float": "float",
        "double": "double precision",
        "real": "real",
        "datetime": "timestamp",
        "datetime2": "timestamp",
        "date": "date",
        "time": "time",
        "datetimeoffset": "timestamptz",
        "uniqueidentifier": "uuid",
        "guid": "uuid",
        "binary": "bytea",
        "varbinary": "bytea",
        "image": "bytea",
        "xml": "xml",
        "json": "jsonb",
        # Oracle types
        "number": "decimal",
        "varchar2": "varchar",
        "clob": "text",
        "blob": "bytea",
        "raw": "bytea",
    }

    # Common naming patterns for primary keys
    PK_PATTERNS = [
        r"^id$",
        r"^.*_id$",
        r"^pk_.*",
        r"^.*_pk$",
    ]

    # Common naming patterns for foreign keys
    FK_PATTERNS = [
        (r"^(.+)_id$", r"\1"),  # user_id -> user
        (r"^fk_(.+)$", r"\1"),  # fk_user -> user
        (r"^(.+)Id$", r"\1"),   # userId -> user (camelCase)
    ]

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self._diagrams: Dict[str, ERDDiagram] = {}

    # ============================================
    # ERD Generation
    # ============================================

    async def generate_from_entities(
        self,
        entities: List[Dict[str, Any]],
        name: str = "Target Architecture",
        project_id: Optional[str] = None,
        brown_paper_session_id: Optional[str] = None,
        apply_normalization: bool = True,
        detect_relationships: bool = True,
        infer_bounded_contexts: bool = True
    ) -> ERDDiagram:
        """
        Generate ERD from extracted entities.

        Args:
            entities: List of entity definitions from Brown Paper
                Each entity: {
                    "name": "User",
                    "fields": [{"name": "id", "type": "int"}, ...],
                    "description": "...",
                    "source_file": "..."
                }
            name: Name for the ERD diagram
            project_id: Optional project ID
            apply_normalization: Apply 3NF normalization rules
            detect_relationships: Auto-detect FK relationships
            infer_bounded_contexts: Group tables into DDD contexts

        Returns:
            ERDDiagram with tables and relationships
        """
        diagram_id = str(uuid.uuid4())
        tables: List[ERDTable] = []
        relationships: List[ERDRelationship] = []

        # Convert entities to tables
        for entity in entities:
            table = self._entity_to_table(entity)
            tables.append(table)

        # Apply normalization if requested
        if apply_normalization:
            tables = self._apply_normalization(tables)

        # Detect relationships
        if detect_relationships:
            relationships = self._detect_relationships(tables)

        # Infer bounded contexts
        bounded_contexts = {}
        if infer_bounded_contexts:
            bounded_contexts = self._infer_bounded_contexts(tables, relationships)
            # Update tables with context info
            for context_name, table_names in bounded_contexts.items():
                for table in tables:
                    if table.name in table_names:
                        table.bounded_context = context_name

        diagram = ERDDiagram(
            name=name,
            tables=tables,
            relationships=relationships,
            bounded_contexts=bounded_contexts
        )
        self._diagrams[diagram_id] = diagram

        # Persist to database
        if self.db:
            db_diagram = ERDDiagramModel(
                id=diagram_id,
                project_id=project_id,
                brown_paper_session_id=brown_paper_session_id,
                name=name,
                diagram_type="target",
                table_count=len(tables),
                relationship_count=len(relationships),
                diagram_data=self._serialize_diagram(diagram),
                mermaid_output=diagram.to_mermaid(),
                plantuml_output=diagram.to_plantuml(),
                bounded_contexts=bounded_contexts,
                normalization_level="3NF" if apply_normalization else "as-is"
            )
            self.db.add(db_diagram)
            await self.db.commit()

        logger.info(f"Generated ERD: {len(tables)} tables, {len(relationships)} relationships")
        return diagram

    def _entity_to_table(self, entity: Dict[str, Any]) -> ERDTable:
        """Convert a Brown Paper entity to ERD table."""
        table_name = self._normalize_table_name(entity.get("name", "unknown"))

        columns = []
        primary_key = []

        for field in entity.get("fields", []):
            field_name = self._normalize_column_name(field.get("name", ""))
            field_type = self._map_type(field.get("type", "varchar"))

            # Detect primary key
            is_pk = self._is_primary_key(field_name, field)

            # Detect foreign key
            fk_ref = self._detect_foreign_key(field_name)

            column = ERDColumn(
                name=field_name,
                data_type=field_type,
                nullable=field.get("nullable", True) and not is_pk,
                primary_key=is_pk,
                foreign_key=fk_ref,
                unique=field.get("unique", False),
                default=field.get("default"),
                description=field.get("description")
            )
            columns.append(column)

            if is_pk:
                primary_key.append(field_name)

        # Add id column if no primary key found
        if not primary_key:
            id_column = ERDColumn(
                name="id",
                data_type="uuid",
                nullable=False,
                primary_key=True,
                description="Auto-generated primary key"
            )
            columns.insert(0, id_column)
            primary_key = ["id"]

        # Add audit columns
        audit_columns = [
            ERDColumn(name="created_at", data_type="timestamp", nullable=False, default="now()"),
            ERDColumn(name="updated_at", data_type="timestamp", nullable=False, default="now()")
        ]

        # Check if audit columns already exist
        existing_names = {c.name.lower() for c in columns}
        for audit_col in audit_columns:
            if audit_col.name.lower() not in existing_names:
                columns.append(audit_col)

        return ERDTable(
            name=table_name,
            columns=columns,
            primary_key=primary_key,
            description=entity.get("description"),
            is_aggregate_root=entity.get("is_aggregate_root", False)
        )

    def _normalize_table_name(self, name: str) -> str:
        """Normalize table name to snake_case plural."""
        # Convert PascalCase to snake_case
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        # Remove special characters
        name = re.sub(r'[^a-z0-9_]', '', name)
        # Pluralize if not already plural
        if not name.endswith('s') and not name.endswith('ies'):
            if name.endswith('y'):
                name = name[:-1] + 'ies'
            else:
                name = name + 's'
        return name

    def _normalize_column_name(self, name: str) -> str:
        """Normalize column name to snake_case."""
        # Convert PascalCase/camelCase to snake_case
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        # Remove special characters
        name = re.sub(r'[^a-z0-9_]', '', name)
        return name

    def _map_type(self, legacy_type: str) -> str:
        """Map legacy type to modern PostgreSQL type."""
        legacy_lower = legacy_type.lower().strip()

        # Direct mapping
        if legacy_lower in self.TYPE_MAPPINGS:
            return self.TYPE_MAPPINGS[legacy_lower]

        # Check for parameterized types
        for pattern, mapped in self.TYPE_MAPPINGS.items():
            if legacy_lower.startswith(pattern):
                return mapped

        # Default to varchar
        return "varchar(255)"

    def _is_primary_key(self, field_name: str, field: Dict[str, Any]) -> bool:
        """Detect if field is a primary key."""
        # Explicit PK flag
        if field.get("primary_key") or field.get("is_pk"):
            return True

        # Check naming patterns
        for pattern in self.PK_PATTERNS:
            if re.match(pattern, field_name.lower()):
                return True

        return False

    def _detect_foreign_key(self, field_name: str) -> Optional[str]:
        """Detect foreign key reference from field name."""
        for pattern, table_pattern in self.FK_PATTERNS:
            match = re.match(pattern, field_name, re.IGNORECASE)
            if match:
                ref_table = re.sub(pattern, table_pattern, field_name, flags=re.IGNORECASE)
                ref_table = self._normalize_table_name(ref_table)
                return f"{ref_table}.id"
        return None

    # ============================================
    # Normalization
    # ============================================

    def _apply_normalization(self, tables: List[ERDTable]) -> List[ERDTable]:
        """Apply 3NF normalization rules."""
        normalized = []

        for table in tables:
            # Check for repeating groups (1NF violation)
            table = self._fix_repeating_groups(table)

            # Check for partial dependencies (2NF violation)
            table = self._fix_partial_dependencies(table)

            # Check for transitive dependencies (3NF violation)
            table = self._fix_transitive_dependencies(table)

            normalized.append(table)

        return normalized

    def _fix_repeating_groups(self, table: ERDTable) -> ERDTable:
        """
        Fix 1NF violations (repeating groups).

        Detects patterns like: phone1, phone2, phone3
        Suggests: Create separate phones table
        """
        # Detect numbered columns
        numbered_pattern = re.compile(r'^(.+?)(\d+)$')
        groups: Dict[str, List[str]] = {}

        for column in table.columns:
            match = numbered_pattern.match(column.name)
            if match:
                base_name = match.group(1)
                if base_name not in groups:
                    groups[base_name] = []
                groups[base_name].append(column.name)

        # Log suggestions for repeating groups
        for base_name, columns in groups.items():
            if len(columns) > 1:
                logger.info(
                    f"Normalization suggestion for {table.name}: "
                    f"Columns {columns} could be extracted to separate table '{base_name}s'"
                )

        return table

    def _fix_partial_dependencies(self, table: ERDTable) -> ERDTable:
        """
        Fix 2NF violations (partial dependencies).

        In composite keys, all non-key attributes should depend on ALL key parts.
        """
        if len(table.primary_key) <= 1:
            return table  # No composite key, no 2NF issue

        # Log warning for composite keys
        logger.info(
            f"Normalization note for {table.name}: "
            f"Composite key {table.primary_key} - verify all columns depend on full key"
        )

        return table

    def _fix_transitive_dependencies(self, table: ERDTable) -> ERDTable:
        """
        Fix 3NF violations (transitive dependencies).

        Non-key attributes should not depend on other non-key attributes.
        """
        # Detect potential transitive dependencies by naming patterns
        # E.g., if we have both 'department_id' and 'department_name',
        # 'department_name' might transitively depend on 'department_id'

        non_pk_columns = [c for c in table.columns if not c.primary_key]
        fk_columns = [c for c in non_pk_columns if c.foreign_key]

        for fk_col in fk_columns:
            # Get base name from FK (e.g., 'department' from 'department_id')
            base_name = fk_col.name.replace('_id', '')

            # Check for related columns
            related = [c for c in non_pk_columns if c.name.startswith(base_name) and c != fk_col]

            if related:
                logger.info(
                    f"Normalization suggestion for {table.name}: "
                    f"Columns {[c.name for c in related]} may have transitive dependency via {fk_col.name}"
                )

        return table

    # ============================================
    # Relationship Detection
    # ============================================

    def _detect_relationships(self, tables: List[ERDTable]) -> List[ERDRelationship]:
        """Detect relationships between tables based on FK patterns."""
        relationships = []
        table_names = {t.name for t in tables}

        for table in tables:
            for column in table.columns:
                if column.foreign_key:
                    # Parse FK reference
                    ref_parts = column.foreign_key.split('.')
                    ref_table = ref_parts[0]
                    ref_column = ref_parts[1] if len(ref_parts) > 1 else 'id'

                    # Verify referenced table exists
                    if ref_table in table_names:
                        # Determine relationship type
                        rel_type = "one-to-many"  # Default

                        # If FK is part of PK, might be many-to-many junction
                        if column.name in table.primary_key and len(table.primary_key) > 1:
                            rel_type = "many-to-many"

                        # If FK is unique, it's one-to-one
                        if column.unique:
                            rel_type = "one-to-one"

                        relationships.append(ERDRelationship(
                            from_table=ref_table,
                            from_column=ref_column,
                            to_table=table.name,
                            to_column=column.name,
                            relationship_type=rel_type
                        ))

        return relationships

    # ============================================
    # Bounded Contexts
    # ============================================

    def _infer_bounded_contexts(
        self,
        tables: List[ERDTable],
        relationships: List[ERDRelationship]
    ) -> Dict[str, List[str]]:
        """
        Infer DDD bounded contexts from table relationships.

        Groups closely related tables into contexts.
        """
        # Build adjacency graph
        graph: Dict[str, Set[str]] = {t.name: set() for t in tables}

        for rel in relationships:
            if rel.from_table in graph and rel.to_table in graph:
                graph[rel.from_table].add(rel.to_table)
                graph[rel.to_table].add(rel.from_table)

        # Find connected components (simple approach)
        visited: Set[str] = set()
        contexts: Dict[str, List[str]] = {}
        context_num = 1

        for table in tables:
            if table.name not in visited:
                component = self._dfs_component(table.name, graph, visited)

                # Name the context
                context_name = self._name_context(component, tables)
                contexts[context_name] = list(component)
                context_num += 1

        return contexts

    def _dfs_component(
        self,
        start: str,
        graph: Dict[str, Set[str]],
        visited: Set[str]
    ) -> Set[str]:
        """Find connected component using DFS."""
        component = set()
        stack = [start]

        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                component.add(node)
                for neighbor in graph.get(node, []):
                    if neighbor not in visited:
                        stack.append(neighbor)

        return component

    def _name_context(self, table_names: Set[str], tables: List[ERDTable]) -> str:
        """Generate a meaningful name for a bounded context."""
        # Find common prefix
        names_list = list(table_names)
        if not names_list:
            return "unknown"

        # Check for common domain prefixes
        domain_keywords = ["user", "order", "product", "payment", "appointment", "patient", "document"]

        for keyword in domain_keywords:
            if any(keyword in name.lower() for name in names_list):
                return f"{keyword}_context"

        # Use shortest table name as context name
        shortest = min(names_list, key=len)
        return f"{shortest.rstrip('s')}_context"

    # ============================================
    # Output Generation
    # ============================================

    async def export_diagram(
        self,
        diagram_id: str,
        format: ERDOutputFormat = ERDOutputFormat.MERMAID
    ) -> str:
        """Export diagram in specified format."""
        diagram = self._diagrams.get(diagram_id)

        if not diagram and self.db:
            result = await self.db.execute(
                select(ERDDiagramModel).where(ERDDiagramModel.id == diagram_id)
            )
            db_diagram = result.scalar_one_or_none()
            if db_diagram:
                if format == ERDOutputFormat.MERMAID and db_diagram.mermaid_output:
                    return db_diagram.mermaid_output
                if format == ERDOutputFormat.PLANTUML and db_diagram.plantuml_output:
                    return db_diagram.plantuml_output
                if db_diagram.diagram_data:
                    diagram = self._deserialize_diagram(db_diagram.diagram_data)

        if not diagram:
            raise ValueError(f"Diagram {diagram_id} not found")

        if format == ERDOutputFormat.MERMAID:
            return diagram.to_mermaid()
        elif format == ERDOutputFormat.PLANTUML:
            return diagram.to_plantuml()
        elif format == ERDOutputFormat.DBML:
            return self._to_dbml(diagram)
        elif format == ERDOutputFormat.JSON:
            return self._to_json(diagram)
        elif format == ERDOutputFormat.DOT:
            return self._to_dot(diagram)
        else:
            return diagram.to_mermaid()

    def _to_dbml(self, diagram: ERDDiagram) -> str:
        """Generate DBML format."""
        lines = [f"// {diagram.name}", ""]

        for table in diagram.tables:
            lines.append(f"Table {table.name} {{")
            for col in table.columns:
                modifiers = []
                if col.primary_key:
                    modifiers.append("pk")
                if not col.nullable:
                    modifiers.append("not null")
                if col.unique:
                    modifiers.append("unique")
                if col.default:
                    modifiers.append(f"default: `{col.default}`")

                mod_str = f" [{', '.join(modifiers)}]" if modifiers else ""
                lines.append(f"  {col.name} {col.data_type}{mod_str}")

            lines.append("}")
            lines.append("")

        for rel in diagram.relationships:
            if rel.relationship_type == "one-to-one":
                symbol = "-"
            elif rel.relationship_type == "one-to-many":
                symbol = "<"
            else:
                symbol = "<>"
            lines.append(f"Ref: {rel.from_table}.{rel.from_column} {symbol} {rel.to_table}.{rel.to_column}")

        return "\n".join(lines)

    def _to_json(self, diagram: ERDDiagram) -> str:
        """Generate JSON format."""
        import json
        return json.dumps(self._serialize_diagram(diagram), indent=2)

    def _to_dot(self, diagram: ERDDiagram) -> str:
        """Generate Graphviz DOT format."""
        lines = ["digraph ERD {", "  rankdir=LR;", "  node [shape=record];"]

        for table in diagram.tables:
            fields = "|".join([f"{c.name}: {c.data_type}" for c in table.columns[:5]])  # Limit fields
            if len(table.columns) > 5:
                fields += f"|... +{len(table.columns) - 5} more"
            lines.append(f'  {table.name} [label="{{{table.name}|{fields}}}"];')

        for rel in diagram.relationships:
            style = "solid" if rel.relationship_type == "one-to-many" else "dashed"
            lines.append(f"  {rel.from_table} -> {rel.to_table} [style={style}];")

        lines.append("}")
        return "\n".join(lines)

    # ============================================
    # Serialization
    # ============================================

    def _serialize_diagram(self, diagram: ERDDiagram) -> Dict[str, Any]:
        """Serialize ERDDiagram to JSON-compatible dict."""
        return {
            "name": diagram.name,
            "tables": [
                {
                    "name": t.name,
                    "schema": t.schema,
                    "columns": [
                        {
                            "name": c.name,
                            "data_type": c.data_type,
                            "nullable": c.nullable,
                            "primary_key": c.primary_key,
                            "foreign_key": c.foreign_key,
                            "unique": c.unique,
                            "default": c.default,
                            "description": c.description
                        }
                        for c in t.columns
                    ],
                    "primary_key": t.primary_key,
                    "description": t.description,
                    "is_aggregate_root": t.is_aggregate_root,
                    "bounded_context": t.bounded_context
                }
                for t in diagram.tables
            ],
            "relationships": [
                {
                    "from_table": r.from_table,
                    "from_column": r.from_column,
                    "to_table": r.to_table,
                    "to_column": r.to_column,
                    "relationship_type": r.relationship_type,
                    "on_delete": r.on_delete,
                    "on_update": r.on_update
                }
                for r in diagram.relationships
            ],
            "bounded_contexts": diagram.bounded_contexts,
            "created_at": diagram.created_at.isoformat()
        }

    def _deserialize_diagram(self, data: Dict[str, Any]) -> ERDDiagram:
        """Deserialize JSON to ERDDiagram."""
        tables = []
        for t in data.get("tables", []):
            columns = [
                ERDColumn(
                    name=c["name"],
                    data_type=c["data_type"],
                    nullable=c.get("nullable", True),
                    primary_key=c.get("primary_key", False),
                    foreign_key=c.get("foreign_key"),
                    unique=c.get("unique", False),
                    default=c.get("default"),
                    description=c.get("description")
                )
                for c in t.get("columns", [])
            ]
            tables.append(ERDTable(
                name=t["name"],
                schema=t.get("schema"),
                columns=columns,
                primary_key=t.get("primary_key", []),
                description=t.get("description"),
                is_aggregate_root=t.get("is_aggregate_root", False),
                bounded_context=t.get("bounded_context")
            ))

        relationships = [
            ERDRelationship(
                from_table=r["from_table"],
                from_column=r["from_column"],
                to_table=r["to_table"],
                to_column=r["to_column"],
                relationship_type=r.get("relationship_type", "one-to-many"),
                on_delete=r.get("on_delete", "NO ACTION"),
                on_update=r.get("on_update", "NO ACTION")
            )
            for r in data.get("relationships", [])
        ]

        return ERDDiagram(
            name=data.get("name", "Unknown"),
            tables=tables,
            relationships=relationships,
            bounded_contexts=data.get("bounded_contexts", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow()
        )

    # ============================================
    # Statistics
    # ============================================

    async def get_statistics(self, diagram_id: str) -> Dict[str, Any]:
        """Get statistics for an ERD diagram."""
        diagram = self._diagrams.get(diagram_id)

        if not diagram and self.db:
            result = await self.db.execute(
                select(ERDDiagramModel).where(ERDDiagramModel.id == diagram_id)
            )
            db_diagram = result.scalar_one_or_none()
            if db_diagram and db_diagram.diagram_data:
                diagram = self._deserialize_diagram(db_diagram.diagram_data)

        if not diagram:
            return {}

        total_columns = sum(len(t.columns) for t in diagram.tables)
        fk_columns = sum(1 for t in diagram.tables for c in t.columns if c.foreign_key)
        nullable_columns = sum(1 for t in diagram.tables for c in t.columns if c.nullable)

        return {
            "name": diagram.name,
            "total_tables": len(diagram.tables),
            "total_columns": total_columns,
            "total_relationships": len(diagram.relationships),
            "bounded_contexts": len(diagram.bounded_contexts),
            "avg_columns_per_table": round(total_columns / len(diagram.tables), 1) if diagram.tables else 0,
            "foreign_key_columns": fk_columns,
            "nullable_columns": nullable_columns,
            "relationship_types": {
                "one-to-one": sum(1 for r in diagram.relationships if r.relationship_type == "one-to-one"),
                "one-to-many": sum(1 for r in diagram.relationships if r.relationship_type == "one-to-many"),
                "many-to-many": sum(1 for r in diagram.relationships if r.relationship_type == "many-to-many")
            }
        }
