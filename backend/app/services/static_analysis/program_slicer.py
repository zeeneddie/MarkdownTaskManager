# backend/app/services/static_analysis/program_slicer.py
"""
Program Slicer - Backward/forward slicing for dependency analysis.

Implements IEEE 852482 (Huang et al. 1996) program slicing algorithm
for multi-language dependency analysis.

Part of Fase 15: Hybrid Static-LLM Extraction Pipeline
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
import ast
import re
import logging

logger = logging.getLogger(__name__)


class SliceDirection(Enum):
    """Direction for program slicing."""
    BACKWARD = "backward"  # Data dependencies leading TO variable
    FORWARD = "forward"    # Data dependencies FROM variable
    BOTH = "both"


class LanguageSupport(Enum):
    """Supported programming languages for slicing."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    CSHARP = "csharp"
    VBNET = "vbnet"
    ASP_CLASSIC = "asp_classic"
    SQL = "sql"


@dataclass
class SliceCriterion:
    """IEEE 852482: Slice criterion = (statement, variable)"""
    file_path: str
    line_number: int
    variable_name: str
    direction: SliceDirection = SliceDirection.BACKWARD


@dataclass
class ProgramSlice:
    """Result of slicing operation."""
    criterion: SliceCriterion
    statements: List[int]  # Line numbers in slice
    variables: Set[str]    # Variables in slice
    functions_involved: Set[str]
    files_involved: Set[str]
    slice_size: int
    complexity_score: float  # 0.0 - 1.0


@dataclass
class DependencyNode:
    """Node in the dependency graph representing a code element."""
    id: str
    file_path: str
    line_start: int
    line_end: int
    node_type: str  # function, class, module, statement
    name: str
    variables_defined: Set[str] = field(default_factory=set)
    variables_used: Set[str] = field(default_factory=set)


@dataclass
class DependencyEdge:
    """Edge in the dependency graph representing a dependency."""
    source_id: str
    target_id: str
    edge_type: str  # data_flow, control_flow, call


@dataclass
class DependencyGraph:
    """Control and data flow graph."""
    nodes: Dict[str, DependencyNode]
    edges: List[DependencyEdge]
    entry_points: List[str]
    exit_points: List[str]


class ProgramSlicer:
    """
    Multi-language program slicer for dependency analysis.

    Implements:
    - Backward slicing: Find all code affecting a variable
    - Forward slicing: Find all code affected by a variable
    - Inter-procedural analysis: Cross-function dependencies
    """

    LANGUAGE_PARSERS = {
        LanguageSupport.PYTHON: "_parse_python",
        LanguageSupport.JAVASCRIPT: "_parse_javascript",
        LanguageSupport.TYPESCRIPT: "_parse_typescript",
        LanguageSupport.CSHARP: "_parse_csharp",
        LanguageSupport.SQL: "_parse_sql",
    }

    def __init__(self, language: LanguageSupport):
        self.language = language
        self.dependency_graph: Optional[DependencyGraph] = None

    async def build_dependency_graph(self, source_files: List[str]) -> DependencyGraph:
        """Build control and data flow graph from source files."""
        parser_method = self.LANGUAGE_PARSERS.get(self.language)
        if not parser_method:
            raise ValueError(f"Unsupported language: {self.language}")

        nodes = {}
        edges = []

        for file_path in source_files:
            try:
                file_nodes, file_edges = await getattr(self, parser_method)(file_path)
                nodes.update(file_nodes)
                edges.extend(file_edges)
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
                continue

        # Build inter-procedural edges
        edges.extend(self._build_call_edges(nodes))

        self.dependency_graph = DependencyGraph(
            nodes=nodes,
            edges=edges,
            entry_points=self._find_entry_points(nodes),
            exit_points=self._find_exit_points(nodes)
        )
        return self.dependency_graph

    async def compute_slice(self, criterion: SliceCriterion) -> ProgramSlice:
        """Compute program slice for given criterion."""
        if not self.dependency_graph:
            raise ValueError("Dependency graph not built. Call build_dependency_graph first.")

        if criterion.direction == SliceDirection.BACKWARD:
            return await self._backward_slice(criterion)
        elif criterion.direction == SliceDirection.FORWARD:
            return await self._forward_slice(criterion)
        else:
            backward = await self._backward_slice(criterion)
            forward = await self._forward_slice(criterion)
            return self._merge_slices(backward, forward)

    async def _backward_slice(self, criterion: SliceCriterion) -> ProgramSlice:
        """Find all statements that affect the criterion variable."""
        affected_statements = set()
        affected_variables = {criterion.variable_name}
        functions_involved = set()
        files_involved = {criterion.file_path}

        worklist = [(criterion.file_path, criterion.line_number, criterion.variable_name)]
        visited = set()

        while worklist:
            file_path, line, var = worklist.pop()
            if (file_path, line, var) in visited:
                continue
            visited.add((file_path, line, var))

            # Find node containing this line
            node = self._find_node_at_line(file_path, line)
            if not node:
                continue

            affected_statements.add(line)
            functions_involved.add(node.name)

            # Find definitions of var that reach this point
            for edge in self.dependency_graph.edges:
                if edge.target_id == node.id and edge.edge_type == "data_flow":
                    source_node = self.dependency_graph.nodes.get(edge.source_id)
                    if source_node and var in source_node.variables_defined:
                        # Add source to worklist with its used variables
                        for used_var in source_node.variables_used:
                            worklist.append((source_node.file_path, source_node.line_start, used_var))
                        files_involved.add(source_node.file_path)
                        affected_variables.update(source_node.variables_used)

        return ProgramSlice(
            criterion=criterion,
            statements=sorted(affected_statements),
            variables=affected_variables,
            functions_involved=functions_involved,
            files_involved=files_involved,
            slice_size=len(affected_statements),
            complexity_score=self._calculate_complexity(affected_statements, functions_involved)
        )

    async def _forward_slice(self, criterion: SliceCriterion) -> ProgramSlice:
        """Find all statements affected by the criterion variable."""
        affected_statements = set()
        affected_variables = {criterion.variable_name}
        functions_involved = set()
        files_involved = {criterion.file_path}

        worklist = [(criterion.file_path, criterion.line_number, criterion.variable_name)]
        visited = set()

        while worklist:
            file_path, line, var = worklist.pop()
            if (file_path, line, var) in visited:
                continue
            visited.add((file_path, line, var))

            # Find node containing this line
            node = self._find_node_at_line(file_path, line)
            if not node:
                continue

            affected_statements.add(line)
            functions_involved.add(node.name)

            # Find usages of var that flow from this point
            for edge in self.dependency_graph.edges:
                if edge.source_id == node.id and edge.edge_type == "data_flow":
                    target_node = self.dependency_graph.nodes.get(edge.target_id)
                    if target_node and var in target_node.variables_used:
                        # Add target to worklist with its defined variables
                        for defined_var in target_node.variables_defined:
                            worklist.append((target_node.file_path, target_node.line_start, defined_var))
                        files_involved.add(target_node.file_path)
                        affected_variables.update(target_node.variables_defined)

        return ProgramSlice(
            criterion=criterion,
            statements=sorted(affected_statements),
            variables=affected_variables,
            functions_involved=functions_involved,
            files_involved=files_involved,
            slice_size=len(affected_statements),
            complexity_score=self._calculate_complexity(affected_statements, functions_involved)
        )

    def _merge_slices(self, backward: ProgramSlice, forward: ProgramSlice) -> ProgramSlice:
        """Merge backward and forward slices."""
        statements = set(backward.statements) | set(forward.statements)
        variables = backward.variables | forward.variables
        functions = backward.functions_involved | forward.functions_involved
        files = backward.files_involved | forward.files_involved

        return ProgramSlice(
            criterion=backward.criterion,
            statements=sorted(statements),
            variables=variables,
            functions_involved=functions,
            files_involved=files,
            slice_size=len(statements),
            complexity_score=self._calculate_complexity(statements, functions)
        )

    def _find_node_at_line(self, file_path: str, line: int) -> Optional[DependencyNode]:
        """Find the node containing the given line."""
        for node in self.dependency_graph.nodes.values():
            if node.file_path == file_path and node.line_start <= line <= node.line_end:
                return node
        return None

    def _calculate_complexity(self, statements: Set[int], functions: Set[str]) -> float:
        """Calculate slice complexity score (0.0 - 1.0)."""
        # Higher complexity = more statements, more functions
        stmt_factor = min(len(statements) / 100, 1.0)
        func_factor = min(len(functions) / 10, 1.0)
        return (stmt_factor + func_factor) / 2

    async def _parse_python(self, file_path: str) -> Tuple[Dict[str, DependencyNode], List[DependencyEdge]]:
        """Parse Python source file into dependency graph nodes/edges."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except (IOError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return {}, []

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return {}, []

        nodes = {}
        edges = []

        # Parse module-level elements
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                node_id = f"{file_path}:{node.name}"
                dep_node = DependencyNode(
                    id=node_id,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    node_type="function",
                    name=node.name,
                    variables_defined=self._extract_assignments(node),
                    variables_used=self._extract_references(node)
                )
                nodes[node_id] = dep_node

            elif isinstance(node, ast.AsyncFunctionDef):
                node_id = f"{file_path}:async_{node.name}"
                dep_node = DependencyNode(
                    id=node_id,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    node_type="async_function",
                    name=node.name,
                    variables_defined=self._extract_assignments(node),
                    variables_used=self._extract_references(node)
                )
                nodes[node_id] = dep_node

            elif isinstance(node, ast.ClassDef):
                class_node_id = f"{file_path}:{node.name}"
                class_dep_node = DependencyNode(
                    id=class_node_id,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    node_type="class",
                    name=node.name,
                    variables_defined=set(),
                    variables_used=set()
                )
                nodes[class_node_id] = class_dep_node

                # Parse class methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = f"{file_path}:{node.name}.{item.name}"
                        method_node = DependencyNode(
                            id=method_id,
                            file_path=file_path,
                            line_start=item.lineno,
                            line_end=item.end_lineno or item.lineno,
                            node_type="method",
                            name=f"{node.name}.{item.name}",
                            variables_defined=self._extract_assignments(item),
                            variables_used=self._extract_references(item)
                        )
                        nodes[method_id] = method_node

        # Build data flow edges within file
        edges.extend(self._build_data_flow_edges(nodes, file_path))

        return nodes, edges

    async def _parse_javascript(self, file_path: str) -> Tuple[Dict[str, DependencyNode], List[DependencyEdge]]:
        """Parse JavaScript/TypeScript source file into dependency graph nodes/edges."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except (IOError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return {}, []

        nodes = {}
        edges = []

        # Regex patterns for JavaScript/TypeScript
        function_pattern = r'(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))'
        class_pattern = r'class\s+(\w+)'
        method_pattern = r'(\w+)\s*\([^)]*\)\s*\{'

        line_num = 0
        for line in source.split('\n'):
            line_num += 1

            # Find functions
            func_match = re.search(function_pattern, line)
            if func_match:
                func_name = func_match.group(1) or func_match.group(2)
                if func_name:
                    node_id = f"{file_path}:{func_name}"
                    nodes[node_id] = DependencyNode(
                        id=node_id,
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        node_type="function",
                        name=func_name,
                        variables_defined=self._extract_js_assignments(line),
                        variables_used=self._extract_js_references(line)
                    )

            # Find classes
            class_match = re.search(class_pattern, line)
            if class_match:
                class_name = class_match.group(1)
                node_id = f"{file_path}:{class_name}"
                nodes[node_id] = DependencyNode(
                    id=node_id,
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    node_type="class",
                    name=class_name,
                    variables_defined=set(),
                    variables_used=set()
                )

        return nodes, edges

    async def _parse_typescript(self, file_path: str) -> Tuple[Dict[str, DependencyNode], List[DependencyEdge]]:
        """Parse TypeScript - uses JavaScript parser with type annotations."""
        return await self._parse_javascript(file_path)

    async def _parse_csharp(self, file_path: str) -> Tuple[Dict[str, DependencyNode], List[DependencyEdge]]:
        """Parse C# source file into dependency graph nodes/edges."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except (IOError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return {}, []

        nodes = {}
        edges = []

        # Regex patterns for C#
        class_pattern = r'(?:public|private|internal|protected)?\s*(?:static\s+)?class\s+(\w+)'
        method_pattern = r'(?:public|private|internal|protected)?\s*(?:static\s+)?(?:async\s+)?(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\('
        property_pattern = r'(?:public|private|internal|protected)?\s*(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\{\s*get'

        line_num = 0
        current_class = None

        for line in source.split('\n'):
            line_num += 1

            # Find classes
            class_match = re.search(class_pattern, line)
            if class_match:
                current_class = class_match.group(1)
                node_id = f"{file_path}:{current_class}"
                nodes[node_id] = DependencyNode(
                    id=node_id,
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    node_type="class",
                    name=current_class,
                    variables_defined=set(),
                    variables_used=set()
                )

            # Find methods
            method_match = re.search(method_pattern, line)
            if method_match and current_class:
                method_name = method_match.group(1)
                if method_name not in ('if', 'while', 'for', 'switch', 'catch'):
                    node_id = f"{file_path}:{current_class}.{method_name}"
                    nodes[node_id] = DependencyNode(
                        id=node_id,
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        node_type="method",
                        name=f"{current_class}.{method_name}",
                        variables_defined=self._extract_csharp_assignments(line),
                        variables_used=self._extract_csharp_references(line)
                    )

        return nodes, edges

    async def _parse_sql(self, file_path: str) -> Tuple[Dict[str, DependencyNode], List[DependencyEdge]]:
        """Parse SQL source file into dependency graph nodes/edges."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except (IOError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return {}, []

        nodes = {}
        edges = []

        # Regex patterns for SQL
        proc_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+(\w+)'
        func_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(\w+)'
        table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)'

        line_num = 0
        for line in source.split('\n'):
            line_num += 1
            upper_line = line.upper()

            # Find stored procedures
            proc_match = re.search(proc_pattern, upper_line, re.IGNORECASE)
            if proc_match:
                proc_name = proc_match.group(1)
                node_id = f"{file_path}:PROCEDURE.{proc_name}"
                nodes[node_id] = DependencyNode(
                    id=node_id,
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    node_type="procedure",
                    name=proc_name,
                    variables_defined=set(),
                    variables_used=set()
                )

            # Find functions
            func_match = re.search(func_pattern, upper_line, re.IGNORECASE)
            if func_match:
                func_name = func_match.group(1)
                node_id = f"{file_path}:FUNCTION.{func_name}"
                nodes[node_id] = DependencyNode(
                    id=node_id,
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    node_type="function",
                    name=func_name,
                    variables_defined=set(),
                    variables_used=set()
                )

            # Find tables
            table_match = re.search(table_pattern, upper_line, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(1)
                node_id = f"{file_path}:TABLE.{table_name}"
                nodes[node_id] = DependencyNode(
                    id=node_id,
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    node_type="table",
                    name=table_name,
                    variables_defined=set(),
                    variables_used=set()
                )

        return nodes, edges

    def _extract_assignments(self, node: ast.AST) -> Set[str]:
        """Extract all variable assignments in a Python AST node."""
        assignments = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        assignments.add(target.id)
            elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                assignments.add(child.target.id)
            elif isinstance(child, ast.AugAssign) and isinstance(child.target, ast.Name):
                assignments.add(child.target.id)
        return assignments

    def _extract_references(self, node: ast.AST) -> Set[str]:
        """Extract all variable references in a Python AST node."""
        references = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                references.add(child.id)
        return references

    def _extract_js_assignments(self, line: str) -> Set[str]:
        """Extract variable assignments from JavaScript line."""
        assignments = set()
        # Match: const/let/var x = ...
        pattern = r'(?:const|let|var)\s+(\w+)\s*='
        matches = re.findall(pattern, line)
        assignments.update(matches)
        return assignments

    def _extract_js_references(self, line: str) -> Set[str]:
        """Extract variable references from JavaScript line."""
        references = set()
        # Match: identifiers that look like variable references
        pattern = r'\b([a-z_]\w*)\b'
        matches = re.findall(pattern, line, re.IGNORECASE)
        # Filter out keywords
        keywords = {'const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while', 'class', 'new', 'this', 'true', 'false', 'null', 'undefined'}
        references.update(m for m in matches if m.lower() not in keywords)
        return references

    def _extract_csharp_assignments(self, line: str) -> Set[str]:
        """Extract variable assignments from C# line."""
        assignments = set()
        # Match: Type varName = ...
        pattern = r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*='
        matches = re.findall(pattern, line)
        assignments.update(matches)
        return assignments

    def _extract_csharp_references(self, line: str) -> Set[str]:
        """Extract variable references from C# line."""
        references = set()
        # Match: identifiers
        pattern = r'\b([a-z_]\w*)\b'
        matches = re.findall(pattern, line, re.IGNORECASE)
        # Filter out keywords
        keywords = {'public', 'private', 'protected', 'internal', 'static', 'void', 'class', 'interface', 'if', 'else', 'for', 'foreach', 'while', 'return', 'new', 'null', 'true', 'false', 'var', 'using', 'namespace'}
        references.update(m for m in matches if m.lower() not in keywords)
        return references

    def _build_data_flow_edges(self, nodes: Dict[str, DependencyNode], file_path: str) -> List[DependencyEdge]:
        """Build data flow edges between nodes in the same file."""
        edges = []
        node_list = [n for n in nodes.values() if n.file_path == file_path]

        for i, source in enumerate(node_list):
            for j, target in enumerate(node_list):
                if i >= j:
                    continue
                # Check if source defines variables that target uses
                shared_vars = source.variables_defined & target.variables_used
                if shared_vars:
                    edges.append(DependencyEdge(
                        source_id=source.id,
                        target_id=target.id,
                        edge_type="data_flow"
                    ))

        return edges

    def _build_call_edges(self, nodes: Dict[str, DependencyNode]) -> List[DependencyEdge]:
        """Build call edges between functions."""
        edges = []
        function_names = {n.name.split('.')[-1]: n.id for n in nodes.values() if n.node_type in ('function', 'method')}

        for node in nodes.values():
            for var in node.variables_used:
                if var in function_names and function_names[var] != node.id:
                    edges.append(DependencyEdge(
                        source_id=node.id,
                        target_id=function_names[var],
                        edge_type="call"
                    ))

        return edges

    def _find_entry_points(self, nodes: Dict[str, DependencyNode]) -> List[str]:
        """Find entry point nodes (e.g., main functions, API endpoints)."""
        entry_patterns = ['main', '__main__', 'app', 'handler', 'endpoint', 'route', 'view', 'api']
        return [nid for nid, node in nodes.items()
                if any(p in node.name.lower() for p in entry_patterns)]

    def _find_exit_points(self, nodes: Dict[str, DependencyNode]) -> List[str]:
        """Find exit point nodes (e.g., return statements, outputs)."""
        return [nid for nid, node in nodes.items()
                if 'return' in node.name.lower() or 'output' in node.name.lower() or 'response' in node.name.lower()]
