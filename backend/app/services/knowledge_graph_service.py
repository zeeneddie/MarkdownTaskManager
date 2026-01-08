"""
Knowledge Graph Service - Code Entity Relationships

Week 62 Day 3: Archon-style Knowledge Graph Integration

Provides:
- Code entity graph (classes, functions, imports)
- Dependency relationships
- Cross-file references
- Agent-optimized context queries

Future integration: Archon OS MCP Server (coleam00/Archon)
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import ast
import os
from pathlib import Path
import json

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Types of code entities."""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    CONSTANT = "constant"


class RelationType(str, Enum):
    """Types of relationships between entities."""
    IMPORTS = "imports"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    USES = "uses"
    DEFINES = "defines"
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"


@dataclass
class CodeEntity:
    """A code entity (class, function, module, etc.)."""
    id: str
    name: str
    entity_type: EntityType
    file_path: str
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityRelation:
    """A relationship between two code entities."""
    source_id: str
    target_id: str
    relation_type: RelationType
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraphService:
    """
    Knowledge Graph for code understanding.

    Builds a graph of code entities and their relationships.
    Optimized for agent context queries.
    """

    def __init__(self, db: Session):
        """Initialize knowledge graph service."""
        self.db = db
        self._entities: Dict[str, CodeEntity] = {}
        self._relations: List[EntityRelation] = []
        self._file_entities: Dict[str, List[str]] = {}  # file_path -> entity_ids

    def build_graph(
        self,
        repo_path: str,
        project_id: int,
        languages: List[str] = None
    ) -> Dict[str, Any]:
        """
        Build knowledge graph for a repository.

        Args:
            repo_path: Path to repository
            project_id: Project ID
            languages: Languages to analyze (default: ["python"])

        Returns:
            Graph statistics
        """
        languages = languages or ["python"]
        repo = Path(repo_path)

        if not repo.exists():
            return {"error": f"Repository not found: {repo_path}"}

        # Clear existing graph
        self._entities = {}
        self._relations = []
        self._file_entities = {}

        # Analyze files
        for lang in languages:
            if lang == "python":
                self._analyze_python_files(repo)
            # Future: Add support for other languages

        # Build cross-file relationships
        self._build_import_relationships()

        return {
            "project_id": project_id,
            "repo_path": str(repo_path),
            "entities": len(self._entities),
            "relations": len(self._relations),
            "files_analyzed": len(self._file_entities),
            "entity_types": self._count_entity_types(),
            "relation_types": self._count_relation_types(),
        }

    def _analyze_python_files(self, repo: Path) -> None:
        """Analyze Python files in repository."""
        for py_file in repo.rglob("*.py"):
            # Skip common directories
            if any(skip in str(py_file) for skip in [
                "__pycache__", ".venv", "venv", "node_modules", ".git",
                "migrations", "alembic/versions"
            ]):
                continue

            try:
                self._analyze_python_file(py_file)
            except Exception as e:
                logger.warning(f"Failed to analyze {py_file}: {e}")

    def _analyze_python_file(self, file_path: Path) -> None:
        """Analyze a single Python file."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return

        rel_path = str(file_path)
        self._file_entities[rel_path] = []

        # Create module entity
        module_id = f"module:{rel_path}"
        module_entity = CodeEntity(
            id=module_id,
            name=file_path.stem,
            entity_type=EntityType.MODULE,
            file_path=rel_path,
            start_line=1,
            end_line=len(content.splitlines()),
            docstring=ast.get_docstring(tree),
            metadata={"imports": [], "classes": [], "functions": []}
        )
        self._entities[module_id] = module_entity
        self._file_entities[rel_path].append(module_id)

        # Analyze top-level nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self._handle_import(node, module_id, rel_path)
            elif isinstance(node, ast.ImportFrom):
                self._handle_import_from(node, module_id, rel_path)
            elif isinstance(node, ast.ClassDef):
                self._handle_class(node, module_id, rel_path)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Only top-level functions (not methods)
                if self._is_top_level(node, tree):
                    self._handle_function(node, module_id, rel_path)

    def _is_top_level(self, node: ast.AST, tree: ast.Module) -> bool:
        """Check if node is at module level."""
        return node in tree.body

    def _handle_import(
        self,
        node: ast.Import,
        module_id: str,
        file_path: str
    ) -> None:
        """Handle import statement."""
        for alias in node.names:
            import_name = alias.asname or alias.name
            import_id = f"import:{file_path}:{import_name}"

            entity = CodeEntity(
                id=import_id,
                name=import_name,
                entity_type=EntityType.IMPORT,
                file_path=file_path,
                start_line=node.lineno,
                end_line=node.lineno,
                metadata={"module": alias.name, "alias": alias.asname}
            )
            self._entities[import_id] = entity
            self._file_entities[file_path].append(import_id)

            # Create relationship
            self._relations.append(EntityRelation(
                source_id=module_id,
                target_id=import_id,
                relation_type=RelationType.IMPORTS
            ))

    def _handle_import_from(
        self,
        node: ast.ImportFrom,
        module_id: str,
        file_path: str
    ) -> None:
        """Handle from ... import statement."""
        module = node.module or ""

        for alias in node.names:
            import_name = alias.asname or alias.name
            import_id = f"import:{file_path}:{module}.{alias.name}"

            entity = CodeEntity(
                id=import_id,
                name=import_name,
                entity_type=EntityType.IMPORT,
                file_path=file_path,
                start_line=node.lineno,
                end_line=node.lineno,
                metadata={
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname,
                    "level": node.level  # Relative import level
                }
            )
            self._entities[import_id] = entity
            self._file_entities[file_path].append(import_id)

            # Create relationship
            self._relations.append(EntityRelation(
                source_id=module_id,
                target_id=import_id,
                relation_type=RelationType.IMPORTS
            ))

    def _handle_class(
        self,
        node: ast.ClassDef,
        module_id: str,
        file_path: str
    ) -> None:
        """Handle class definition."""
        class_id = f"class:{file_path}:{node.name}"

        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{self._get_attr_name(base)}")

        entity = CodeEntity(
            id=class_id,
            name=node.name,
            entity_type=EntityType.CLASS,
            file_path=file_path,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            metadata={
                "bases": bases,
                "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                "methods": []
            }
        )
        self._entities[class_id] = entity
        self._file_entities[file_path].append(class_id)

        # Create contains relationship
        self._relations.append(EntityRelation(
            source_id=module_id,
            target_id=class_id,
            relation_type=RelationType.CONTAINS
        ))

        # Create extends relationships
        for base in bases:
            self._relations.append(EntityRelation(
                source_id=class_id,
                target_id=f"class_ref:{base}",
                relation_type=RelationType.EXTENDS
            ))

        # Handle methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._handle_method(item, class_id, file_path)

    def _handle_function(
        self,
        node: ast.FunctionDef,
        module_id: str,
        file_path: str
    ) -> None:
        """Handle function definition."""
        func_id = f"function:{file_path}:{node.name}"

        entity = CodeEntity(
            id=func_id,
            name=node.name,
            entity_type=EntityType.FUNCTION,
            file_path=file_path,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            metadata={
                "args": [arg.arg for arg in node.args.args],
                "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                "is_async": isinstance(node, ast.AsyncFunctionDef)
            }
        )
        self._entities[func_id] = entity
        self._file_entities[file_path].append(func_id)

        # Create contains relationship
        self._relations.append(EntityRelation(
            source_id=module_id,
            target_id=func_id,
            relation_type=RelationType.CONTAINS
        ))

    def _handle_method(
        self,
        node: ast.FunctionDef,
        class_id: str,
        file_path: str
    ) -> None:
        """Handle method definition."""
        class_name = class_id.split(":")[-1]
        method_id = f"method:{file_path}:{class_name}.{node.name}"

        entity = CodeEntity(
            id=method_id,
            name=node.name,
            entity_type=EntityType.METHOD,
            file_path=file_path,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            metadata={
                "class": class_name,
                "args": [arg.arg for arg in node.args.args],
                "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "is_property": any(
                    self._get_decorator_name(d) == "property"
                    for d in node.decorator_list
                ),
                "is_classmethod": any(
                    self._get_decorator_name(d) == "classmethod"
                    for d in node.decorator_list
                ),
                "is_staticmethod": any(
                    self._get_decorator_name(d) == "staticmethod"
                    for d in node.decorator_list
                )
            }
        )
        self._entities[method_id] = entity
        self._file_entities[file_path].append(method_id)

        # Create contains relationship
        self._relations.append(EntityRelation(
            source_id=class_id,
            target_id=method_id,
            relation_type=RelationType.CONTAINS
        ))

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Get decorator name."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return self._get_attr_name(decorator)
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return "unknown"

    def _get_attr_name(self, attr: ast.Attribute) -> str:
        """Get full attribute name."""
        parts = []
        node = attr
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))

    def _build_import_relationships(self) -> None:
        """Build cross-file import relationships."""
        # Map module names to entity IDs
        module_map: Dict[str, str] = {}
        for entity_id, entity in self._entities.items():
            if entity.entity_type == EntityType.MODULE:
                # Map both full path and stem
                module_map[entity.name] = entity_id
                # Also map dotted path
                path = Path(entity.file_path)
                parts = path.parts
                if parts:
                    dotted = ".".join(parts[:-1] + (path.stem,))
                    module_map[dotted] = entity_id

    def _count_entity_types(self) -> Dict[str, int]:
        """Count entities by type."""
        counts = {}
        for entity in self._entities.values():
            entity_type = entity.entity_type.value
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts

    def _count_relation_types(self) -> Dict[str, int]:
        """Count relations by type."""
        counts = {}
        for relation in self._relations:
            rel_type = relation.relation_type.value
            counts[rel_type] = counts.get(rel_type, 0) + 1
        return counts

    # ============ Query Methods ============

    def get_entity(self, entity_id: str) -> Optional[CodeEntity]:
        """Get entity by ID."""
        return self._entities.get(entity_id)

    def get_entities_by_type(self, entity_type: EntityType) -> List[CodeEntity]:
        """Get all entities of a type."""
        return [e for e in self._entities.values() if e.entity_type == entity_type]

    def get_entities_in_file(self, file_path: str) -> List[CodeEntity]:
        """Get all entities in a file."""
        entity_ids = self._file_entities.get(file_path, [])
        return [self._entities[eid] for eid in entity_ids if eid in self._entities]

    def get_relations_for_entity(
        self,
        entity_id: str,
        direction: str = "both"
    ) -> List[EntityRelation]:
        """
        Get relations for an entity.

        Args:
            entity_id: Entity ID
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of relations
        """
        relations = []
        for rel in self._relations:
            if direction in ("both", "outgoing") and rel.source_id == entity_id:
                relations.append(rel)
            if direction in ("both", "incoming") and rel.target_id == entity_id:
                relations.append(rel)
        return relations

    def find_classes(self, pattern: str = None) -> List[CodeEntity]:
        """Find classes, optionally matching a pattern."""
        classes = self.get_entities_by_type(EntityType.CLASS)
        if pattern:
            pattern_lower = pattern.lower()
            classes = [c for c in classes if pattern_lower in c.name.lower()]
        return classes

    def find_functions(self, pattern: str = None) -> List[CodeEntity]:
        """Find functions, optionally matching a pattern."""
        functions = self.get_entities_by_type(EntityType.FUNCTION)
        if pattern:
            pattern_lower = pattern.lower()
            functions = [f for f in functions if pattern_lower in f.name.lower()]
        return functions

    def get_class_hierarchy(self, class_name: str) -> Dict[str, Any]:
        """Get class inheritance hierarchy."""
        # Find the class
        classes = self.find_classes(class_name)
        if not classes:
            return {"error": f"Class not found: {class_name}"}

        class_entity = classes[0]

        # Get base classes
        bases = class_entity.metadata.get("bases", [])

        # Get methods
        methods = []
        for rel in self.get_relations_for_entity(class_entity.id, "outgoing"):
            if rel.relation_type == RelationType.CONTAINS:
                target = self.get_entity(rel.target_id)
                if target and target.entity_type == EntityType.METHOD:
                    methods.append({
                        "name": target.name,
                        "line": target.start_line,
                        "docstring": target.docstring,
                        **target.metadata
                    })

        return {
            "name": class_entity.name,
            "file": class_entity.file_path,
            "line": class_entity.start_line,
            "docstring": class_entity.docstring,
            "bases": bases,
            "methods": methods,
            "metadata": class_entity.metadata
        }

    def get_module_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Get dependencies for a module."""
        entities = self.get_entities_in_file(file_path)

        imports = []
        for entity in entities:
            if entity.entity_type == EntityType.IMPORT:
                imports.append({
                    "name": entity.name,
                    "module": entity.metadata.get("module"),
                    "alias": entity.metadata.get("alias"),
                    "level": entity.metadata.get("level", 0)
                })

        # Separate internal vs external
        internal = [i for i in imports if i.get("level", 0) > 0 or
                    (i.get("module", "").startswith("app.") if i.get("module") else False)]
        external = [i for i in imports if i not in internal]

        return {
            "file": file_path,
            "total_imports": len(imports),
            "internal_imports": internal,
            "external_imports": external
        }

    # ============ Agent Context Methods ============

    def get_architecture_summary(self) -> Dict[str, Any]:
        """Get architecture summary for Felix (Feature Architect)."""
        modules = self.get_entities_by_type(EntityType.MODULE)
        classes = self.get_entities_by_type(EntityType.CLASS)
        functions = self.get_entities_by_type(EntityType.FUNCTION)

        # Group by directory
        dir_structure = {}
        for module in modules:
            path = Path(module.file_path)
            dir_name = str(path.parent) if path.parent != Path(".") else "root"
            if dir_name not in dir_structure:
                dir_structure[dir_name] = {"modules": 0, "classes": 0, "functions": 0}
            dir_structure[dir_name]["modules"] += 1

        for cls in classes:
            path = Path(cls.file_path)
            dir_name = str(path.parent) if path.parent != Path(".") else "root"
            if dir_name in dir_structure:
                dir_structure[dir_name]["classes"] += 1

        for func in functions:
            path = Path(func.file_path)
            dir_name = str(path.parent) if path.parent != Path(".") else "root"
            if dir_name in dir_structure:
                dir_structure[dir_name]["functions"] += 1

        return {
            "summary": {
                "total_modules": len(modules),
                "total_classes": len(classes),
                "total_functions": len(functions),
                "total_relations": len(self._relations),
            },
            "directory_structure": dir_structure,
            "main_classes": [
                {"name": c.name, "file": c.file_path, "docstring": c.docstring}
                for c in classes[:20]  # Top 20 classes
            ]
        }

    def get_dependency_graph(self) -> Dict[str, Any]:
        """Get dependency graph for Miguel (Migration Architect)."""
        modules = self.get_entities_by_type(EntityType.MODULE)

        # Collect all external dependencies
        external_deps = set()
        module_deps = {}

        for module in modules:
            deps = self.get_module_dependencies(module.file_path)
            module_deps[module.name] = {
                "internal": len(deps["internal_imports"]),
                "external": len(deps["external_imports"])
            }
            for ext in deps["external_imports"]:
                if ext.get("module"):
                    external_deps.add(ext["module"].split(".")[0])

        return {
            "external_dependencies": sorted(external_deps),
            "total_external": len(external_deps),
            "module_dependency_counts": module_deps,
            "most_dependent_modules": sorted(
                module_deps.items(),
                key=lambda x: x[1]["external"],
                reverse=True
            )[:10]
        }

    def get_quality_insights(self) -> Dict[str, Any]:
        """Get quality insights for Quinn (Quality Inspector)."""
        classes = self.get_entities_by_type(EntityType.CLASS)
        functions = self.get_entities_by_type(EntityType.FUNCTION)
        methods = self.get_entities_by_type(EntityType.METHOD)

        # Check for missing docstrings
        undocumented_classes = [c for c in classes if not c.docstring]
        undocumented_functions = [f for f in functions if not f.docstring]
        undocumented_methods = [m for m in methods if not m.docstring
                               and not m.name.startswith("_")]

        # Check for large classes (many methods)
        large_classes = []
        for cls in classes:
            method_count = len([
                r for r in self._relations
                if r.source_id == cls.id and r.relation_type == RelationType.CONTAINS
            ])
            if method_count > 10:
                large_classes.append({"name": cls.name, "methods": method_count})

        return {
            "documentation": {
                "undocumented_classes": len(undocumented_classes),
                "undocumented_functions": len(undocumented_functions),
                "undocumented_public_methods": len(undocumented_methods),
                "documentation_coverage": round(
                    (1 - (len(undocumented_classes) + len(undocumented_functions)) /
                     max(len(classes) + len(functions), 1)) * 100, 2
                )
            },
            "complexity": {
                "large_classes": large_classes,
                "total_classes": len(classes),
                "total_functions": len(functions),
                "total_methods": len(methods)
            },
            "recommendations": self._generate_quality_recommendations(
                undocumented_classes, undocumented_functions, large_classes
            )
        }

    def _generate_quality_recommendations(
        self,
        undocumented_classes: List[CodeEntity],
        undocumented_functions: List[CodeEntity],
        large_classes: List[Dict]
    ) -> List[str]:
        """Generate quality recommendations."""
        recommendations = []

        if undocumented_classes:
            recommendations.append(
                f"Add docstrings to {len(undocumented_classes)} classes: "
                f"{', '.join(c.name for c in undocumented_classes[:5])}"
            )

        if undocumented_functions:
            recommendations.append(
                f"Add docstrings to {len(undocumented_functions)} functions: "
                f"{', '.join(f.name for f in undocumented_functions[:5])}"
            )

        for cls in large_classes[:3]:
            recommendations.append(
                f"Consider splitting class '{cls['name']}' ({cls['methods']} methods)"
            )

        return recommendations

    def export_graph(self, format: str = "json") -> str:
        """Export graph to JSON format."""
        data = {
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.entity_type.value,
                    "file": e.file_path,
                    "start_line": e.start_line,
                    "end_line": e.end_line,
                    "docstring": e.docstring,
                    "metadata": e.metadata
                }
                for e in self._entities.values()
            ],
            "relations": [
                {
                    "source": r.source_id,
                    "target": r.target_id,
                    "type": r.relation_type.value,
                    "metadata": r.metadata
                }
                for r in self._relations
            ],
            "statistics": {
                "entities": len(self._entities),
                "relations": len(self._relations),
                "files": len(self._file_entities),
                "entity_types": self._count_entity_types(),
                "relation_types": self._count_relation_types()
            },
            "generated_at": datetime.utcnow().isoformat()
        }

        return json.dumps(data, indent=2, default=str)


# Singleton instance
_knowledge_graph_service: Optional[KnowledgeGraphService] = None


def get_knowledge_graph_service(db: Session = None) -> KnowledgeGraphService:
    """Get knowledge graph service singleton."""
    global _knowledge_graph_service
    if _knowledge_graph_service is None and db is not None:
        _knowledge_graph_service = KnowledgeGraphService(db)
    return _knowledge_graph_service
