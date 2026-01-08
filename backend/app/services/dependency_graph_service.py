"""
Dependency Graph Generator Service - Module Dependency Visualization

Week 67 Day 10: Multi-language dependency analysis and graph generation

Provides:
- Cross-language import/dependency extraction
- Circular dependency detection
- Coupling/cohesion metrics
- Multiple output formats (Mermaid, DOT, JSON, D3.js)
- Module clustering analysis
"""

import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Set, Tuple
from enum import Enum
from datetime import datetime
from collections import defaultdict
import json


class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    CSHARP = "csharp"
    JAVA = "java"
    PHP = "php"
    RUBY = "ruby"
    RUST = "rust"
    VB_NET = "vb.net"
    ASP_CLASSIC = "asp_classic"  # Classic ASP (VBScript/JScript)
    ASPX = "aspx"  # ASP.NET WebForms
    UNKNOWN = "unknown"


class OutputFormat(Enum):
    """Graph output formats"""
    MERMAID = "mermaid"
    DOT = "dot"  # GraphViz
    JSON = "json"
    D3 = "d3"  # D3.js compatible
    ADJACENCY = "adjacency"  # Adjacency matrix


@dataclass
class DependencyEdge:
    """Single dependency relationship"""
    source: str  # Source module/file
    target: str  # Target module/file
    import_type: str  # "import", "from_import", "require", "using", etc.
    line_number: int
    is_external: bool  # External package vs internal module
    import_statement: str  # Original import statement


@dataclass
class ModuleNode:
    """Module/file in the dependency graph"""
    name: str
    file_path: str
    language: Language
    imports: List[DependencyEdge] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)
    lines_of_code: int = 0
    is_entry_point: bool = False  # No incoming edges from internal modules


@dataclass
class CircularDependency:
    """Detected circular dependency"""
    cycle: List[str]  # List of modules in the cycle
    cycle_length: int


@dataclass
class DependencyMetrics:
    """Dependency analysis metrics"""
    total_modules: int
    total_edges: int
    external_dependencies: int
    internal_dependencies: int
    circular_dependencies: int
    average_imports_per_module: float
    max_imports: int
    max_imported_by: int
    afferent_coupling_avg: float  # Ca - incoming dependencies
    efferent_coupling_avg: float  # Ce - outgoing dependencies
    instability_avg: float  # I = Ce / (Ca + Ce)
    entry_points: List[str]
    hub_modules: List[str]  # Highly connected modules


@dataclass
class DependencyGraphResult:
    """Complete dependency graph analysis result"""
    project_path: str
    languages_detected: List[Language]
    modules: Dict[str, ModuleNode]
    edges: List[DependencyEdge]
    circular_dependencies: List[CircularDependency]
    metrics: DependencyMetrics
    clusters: Dict[str, List[str]]  # Directory-based clustering
    analysis_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "languages_detected": [l.value for l in self.languages_detected],
            "module_count": len(self.modules),
            "edge_count": len(self.edges),
            "modules": {
                name: {
                    "file_path": m.file_path,
                    "language": m.language.value,
                    "imports_count": len(m.imports),
                    "imported_by_count": len(m.imported_by),
                    "lines_of_code": m.lines_of_code,
                    "is_entry_point": m.is_entry_point
                }
                for name, m in self.modules.items()
            },
            "circular_dependencies": [
                {"cycle": cd.cycle, "length": cd.cycle_length}
                for cd in self.circular_dependencies
            ],
            "metrics": {
                "total_modules": self.metrics.total_modules,
                "total_edges": self.metrics.total_edges,
                "external_dependencies": self.metrics.external_dependencies,
                "internal_dependencies": self.metrics.internal_dependencies,
                "circular_dependencies": self.metrics.circular_dependencies,
                "average_imports_per_module": round(self.metrics.average_imports_per_module, 2),
                "max_imports": self.metrics.max_imports,
                "max_imported_by": self.metrics.max_imported_by,
                "afferent_coupling_avg": round(self.metrics.afferent_coupling_avg, 2),
                "efferent_coupling_avg": round(self.metrics.efferent_coupling_avg, 2),
                "instability_avg": round(self.metrics.instability_avg, 2),
                "entry_points": self.metrics.entry_points,
                "hub_modules": self.metrics.hub_modules
            },
            "clusters": self.clusters,
            "analysis_timestamp": self.analysis_timestamp
        }


# Language detection by file extension
LANGUAGE_EXTENSIONS: Dict[str, Language] = {
    ".py": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".go": Language.GO,
    ".cs": Language.CSHARP,
    ".java": Language.JAVA,
    ".php": Language.PHP,
    ".rb": Language.RUBY,
    ".rs": Language.RUST,
    ".vb": Language.VB_NET,
    ".asp": Language.ASP_CLASSIC,
    ".asa": Language.ASP_CLASSIC,  # Global.asa
    ".inc": Language.ASP_CLASSIC,  # Include files
    ".aspx": Language.ASPX,
}

# Import patterns by language
IMPORT_PATTERNS: Dict[Language, List[Tuple[str, str]]] = {
    Language.PYTHON: [
        (r"^import\s+(\S+)", "import"),
        (r"^from\s+(\S+)\s+import", "from_import"),
    ],
    Language.JAVASCRIPT: [
        (r"import\s+.*\s+from\s+['\"](.+?)['\"]", "es6_import"),
        (r"import\s+['\"](.+?)['\"]", "es6_import_side_effect"),
        (r"require\s*\(\s*['\"](.+?)['\"]\s*\)", "commonjs_require"),
        (r"import\s*\(\s*['\"](.+?)['\"]\s*\)", "dynamic_import"),
    ],
    Language.TYPESCRIPT: [
        (r"import\s+.*\s+from\s+['\"](.+?)['\"]", "es6_import"),
        (r"import\s+['\"](.+?)['\"]", "es6_import_side_effect"),
        (r"import\s+type\s+.*\s+from\s+['\"](.+?)['\"]", "type_import"),
        (r"require\s*\(\s*['\"](.+?)['\"]\s*\)", "commonjs_require"),
    ],
    Language.GO: [
        (r'import\s+"(.+?)"', "single_import"),
        (r'^\s+"(.+?)"', "grouped_import"),  # Inside import block
    ],
    Language.CSHARP: [
        (r"^using\s+([\w\.]+)\s*;", "using"),
        (r"^using\s+static\s+([\w\.]+)\s*;", "using_static"),
    ],
    Language.JAVA: [
        (r"^import\s+([\w\.]+)\s*;", "import"),
        (r"^import\s+static\s+([\w\.]+)\s*;", "static_import"),
    ],
    Language.PHP: [
        (r"use\s+([\w\\]+)", "use"),
        (r"require(?:_once)?\s*['\"](.+?)['\"]", "require"),
        (r"include(?:_once)?\s*['\"](.+?)['\"]", "include"),
    ],
    Language.RUBY: [
        (r"require\s+['\"](.+?)['\"]", "require"),
        (r"require_relative\s+['\"](.+?)['\"]", "require_relative"),
        (r"load\s+['\"](.+?)['\"]", "load"),
    ],
    Language.RUST: [
        (r"use\s+([\w:]+)", "use"),
        (r"extern\s+crate\s+(\w+)", "extern_crate"),
        (r"mod\s+(\w+)\s*;", "mod"),
    ],
    Language.VB_NET: [
        (r"^Imports\s+([\w\.]+)", "imports"),
    ],
    Language.ASP_CLASSIC: [
        # SSI includes - file (relative path)
        (r'<!--\s*#include\s+file\s*=\s*"([^"]+)"', "ssi_include_file"),
        # SSI includes - virtual (from web root)
        (r'<!--\s*#include\s+virtual\s*=\s*"([^"]+)"', "ssi_include_virtual"),
        # Server.Execute - server-side execution
        (r'Server\.Execute\s*\(\s*"([^"]+)"', "server_execute"),
        # Server.Transfer - server-side transfer
        (r'Server\.Transfer\s*\(\s*"([^"]+)"', "server_transfer"),
        # Response.Redirect - navigation dependency
        (r'Response\.Redirect\s*\(\s*"([^"]+\.asp[^"]*)"', "redirect"),
        # CreateObject for components
        (r'Server\.CreateObject\s*\(\s*"([^"]+)"', "com_component"),
    ],
    Language.ASPX: [
        # Page directive inherits
        (r'<%@\s*Page[^>]*Inherits\s*=\s*"([^"]+)"', "page_inherits"),
        # Control directive
        (r'<%@\s*Control[^>]*Inherits\s*=\s*"([^"]+)"', "control_inherits"),
        # Register directive for user controls
        (r'<%@\s*Register[^>]*Src\s*=\s*"([^"]+)"', "register_src"),
        # Master page reference
        (r'<%@\s*Page[^>]*MasterPageFile\s*=\s*"([^"]+)"', "master_page"),
        # Code-behind
        (r'<%@\s*Page[^>]*CodeBehind\s*=\s*"([^"]+)"', "code_behind"),
        (r'<%@\s*Page[^>]*CodeFile\s*=\s*"([^"]+)"', "code_file"),
    ],
}

# External package indicators by language
EXTERNAL_INDICATORS: Dict[Language, List[str]] = {
    Language.PYTHON: [".", "/"],  # If starts with . it's relative
    Language.JAVASCRIPT: [".", "/", "@"],  # @ for scoped packages
    Language.TYPESCRIPT: [".", "/", "@"],
    Language.GO: ["github.com", "golang.org", "google.golang.org"],
    Language.CSHARP: ["System", "Microsoft", "Newtonsoft"],
    Language.JAVA: ["java.", "javax.", "org.", "com."],
    Language.PHP: [],
    Language.RUBY: [],
    Language.RUST: ["std", "crate"],
    Language.VB_NET: ["System", "Microsoft"],
    Language.ASP_CLASSIC: ["ADODB.", "Scripting.", "MSXML", "CDO.", "WScript."],  # COM components
    Language.ASPX: ["System", "Microsoft"],
}


class DependencyGraphService:
    """Service for generating dependency graphs from codebases"""

    def __init__(self):
        pass

    def analyze_directory(
        self,
        directory: str,
        exclude_patterns: Optional[List[str]] = None,
        include_external: bool = True,
        max_depth: Optional[int] = None
    ) -> DependencyGraphResult:
        """
        Analyze directory and build dependency graph

        Args:
            directory: Root directory to analyze
            exclude_patterns: Glob patterns to exclude (e.g., ["**/node_modules/**"])
            include_external: Include external package dependencies
            max_depth: Maximum directory depth to analyze

        Returns:
            DependencyGraphResult with complete analysis
        """
        if exclude_patterns is None:
            exclude_patterns = [
                "**/node_modules/**",
                "**/.venv/**",
                "**/venv/**",
                "**/__pycache__/**",
                "**/dist/**",
                "**/build/**",
                "**/.git/**",
                "**/vendor/**",
            ]

        path = Path(directory)
        if not path.exists():
            return self._empty_result(directory, "Directory does not exist")

        # Collect source files
        source_files = self._collect_source_files(path, exclude_patterns, max_depth)

        if not source_files:
            return self._empty_result(directory, "No source files found")

        # Build modules and extract imports
        modules: Dict[str, ModuleNode] = {}
        edges: List[DependencyEdge] = []
        languages_detected: Set[Language] = set()

        for file_path in source_files:
            module = self._analyze_file(file_path, path, include_external)
            if module:
                modules[module.name] = module
                edges.extend(module.imports)
                languages_detected.add(module.language)

        # Build reverse dependencies (imported_by)
        self._build_reverse_dependencies(modules, edges)

        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies(modules)

        # Calculate metrics
        metrics = self._calculate_metrics(modules, edges, circular_deps)

        # Create clusters based on directory structure
        clusters = self._create_clusters(modules)

        return DependencyGraphResult(
            project_path=str(directory),
            languages_detected=list(languages_detected),
            modules=modules,
            edges=edges,
            circular_dependencies=circular_deps,
            metrics=metrics,
            clusters=clusters
        )

    def _collect_source_files(
        self,
        root: Path,
        exclude_patterns: List[str],
        max_depth: Optional[int]
    ) -> List[Path]:
        """Collect all source files"""
        files = []

        for ext in LANGUAGE_EXTENSIONS.keys():
            for file_path in root.rglob(f"*{ext}"):
                # Check depth
                if max_depth is not None:
                    rel_path = file_path.relative_to(root)
                    if len(rel_path.parts) > max_depth:
                        continue

                # Check exclusions
                rel_str = str(file_path.relative_to(root))
                excluded = False
                for pattern in exclude_patterns:
                    # Simple glob matching
                    pattern_parts = pattern.replace("**", ".*").replace("*", "[^/]*")
                    if re.match(pattern_parts, rel_str):
                        excluded = True
                        break

                if not excluded:
                    files.append(file_path)

        return files

    def _analyze_file(
        self,
        file_path: Path,
        root: Path,
        include_external: bool
    ) -> Optional[ModuleNode]:
        """Analyze a single file for imports"""
        ext = file_path.suffix.lower()
        language = LANGUAGE_EXTENSIONS.get(ext, Language.UNKNOWN)

        if language == Language.UNKNOWN:
            return None

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        lines = content.splitlines()
        rel_path = file_path.relative_to(root)
        module_name = self._path_to_module_name(rel_path, language)

        imports = []
        patterns = IMPORT_PATTERNS.get(language, [])
        external_indicators = EXTERNAL_INDICATORS.get(language, [])

        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith(("#", "//", "/*", "*")):
                continue

            for pattern, import_type in patterns:
                match = re.search(pattern, line_stripped, re.IGNORECASE)
                if match:
                    target = match.group(1)

                    # Normalize ASP include paths to module names
                    if language in [Language.ASP_CLASSIC, Language.ASPX]:
                        target = self._normalize_asp_include_path(
                            target, rel_path, import_type
                        )

                    # Determine if external
                    is_external = self._is_external_import(
                        target, language, external_indicators
                    )

                    if not include_external and is_external:
                        continue

                    imports.append(DependencyEdge(
                        source=module_name,
                        target=target,
                        import_type=import_type,
                        line_number=i,
                        is_external=is_external,
                        import_statement=line_stripped
                    ))

        return ModuleNode(
            name=module_name,
            file_path=str(rel_path),
            language=language,
            imports=imports,
            lines_of_code=len(lines)
        )

    def _normalize_asp_include_path(
        self,
        target: str,
        source_rel_path: Path,
        import_type: str
    ) -> str:
        """
        Normalize ASP include paths to module names.

        Converts:
          '../Includes/Footer.asp' -> 'Includes/Footer'
          'Procedures/Security.asp' -> 'Procedures/Security'
          '/Includes/HeaderMenu.asp' -> 'Includes/HeaderMenu'
        """
        # Remove leading/trailing whitespace
        target = target.strip()

        # Handle virtual paths (from web root)
        if import_type == "ssi_include_virtual" or target.startswith("/"):
            target = target.lstrip("/")
        else:
            # Resolve relative paths
            if target.startswith("../") or target.startswith("..\\"):
                # Get source directory
                source_dir = source_rel_path.parent
                # Resolve relative path
                try:
                    resolved = (source_dir / target).resolve()
                    # Convert back to relative string (best effort)
                    target_path = Path(target)
                    # Normalize by removing .. components
                    parts = []
                    for part in str(source_dir / target).split("/"):
                        if part == "..":
                            if parts:
                                parts.pop()
                        elif part and part != ".":
                            parts.append(part)
                    target = "/".join(parts)
                except Exception:
                    pass

        # Remove file extension to get module name
        for ext in [".asp", ".asa", ".inc", ".aspx", ".ascx"]:
            if target.lower().endswith(ext):
                target = target[:-len(ext)]
                break

        # Normalize path separators
        target = target.replace("\\", "/")

        return target

    def _path_to_module_name(self, rel_path: Path, language: Language) -> str:
        """Convert file path to module name"""
        parts = list(rel_path.parts)

        # Remove file extension
        if parts:
            parts[-1] = rel_path.stem

        # Language-specific module naming
        if language == Language.PYTHON:
            return ".".join(parts)
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return "/".join(parts)
        elif language == Language.GO:
            return "/".join(parts)
        elif language == Language.JAVA:
            return ".".join(parts)
        elif language == Language.CSHARP:
            return ".".join(parts)
        else:
            return "/".join(parts)

    def _is_external_import(
        self,
        target: str,
        language: Language,
        indicators: List[str]
    ) -> bool:
        """Determine if import is external"""
        if language == Language.PYTHON:
            # Relative imports start with .
            return not target.startswith(".")
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            # Local imports start with . or /
            return not (target.startswith(".") or target.startswith("/"))
        elif language == Language.GO:
            # Standard library and external packages have known prefixes
            for indicator in indicators:
                if indicator in target:
                    return True
            return False
        elif language in [Language.JAVA, Language.CSHARP, Language.VB_NET, Language.ASPX]:
            # Check for standard library prefixes
            for indicator in indicators:
                if target.startswith(indicator):
                    return True
            return False
        elif language == Language.ASP_CLASSIC:
            # COM components are external (ADODB, Scripting, etc.)
            for indicator in indicators:
                if indicator in target:
                    return True
            # File paths (.asp, .inc) are internal
            if target.endswith((".asp", ".asa", ".inc")):
                return False
            # Relative paths are internal
            if target.startswith("..") or target.startswith("/"):
                return False
            return False  # Default to internal for ASP includes
        else:
            return True  # Default to external

    def _build_reverse_dependencies(
        self,
        modules: Dict[str, ModuleNode],
        edges: List[DependencyEdge]
    ):
        """Build imported_by relationships"""
        for edge in edges:
            if edge.target in modules:
                modules[edge.target].imported_by.append(edge.source)

        # Mark entry points (modules not imported by any internal module)
        for name, module in modules.items():
            internal_importers = [
                imp for imp in module.imported_by if imp in modules
            ]
            module.is_entry_point = len(internal_importers) == 0

    def _detect_circular_dependencies(
        self,
        modules: Dict[str, ModuleNode]
    ) -> List[CircularDependency]:
        """Detect circular dependencies using DFS"""
        circular_deps = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            if node in modules:
                for edge in modules[node].imports:
                    target = edge.target
                    if target not in modules:
                        continue  # External dependency

                    if target not in visited:
                        dfs(target)
                    elif target in rec_stack:
                        # Found cycle
                        cycle_start = path.index(target)
                        cycle = path[cycle_start:] + [target]
                        circular_deps.append(CircularDependency(
                            cycle=cycle,
                            cycle_length=len(cycle) - 1
                        ))

            path.pop()
            rec_stack.remove(node)

        for module_name in modules:
            if module_name not in visited:
                dfs(module_name)

        return circular_deps

    def _calculate_metrics(
        self,
        modules: Dict[str, ModuleNode],
        edges: List[DependencyEdge],
        circular_deps: List[CircularDependency]
    ) -> DependencyMetrics:
        """Calculate dependency metrics"""
        total_modules = len(modules)
        total_edges = len(edges)

        external_deps = sum(1 for e in edges if e.is_external)
        internal_deps = total_edges - external_deps

        # Calculate per-module metrics
        imports_counts = [len(m.imports) for m in modules.values()]
        imported_by_counts = [len(m.imported_by) for m in modules.values()]

        avg_imports = sum(imports_counts) / total_modules if total_modules > 0 else 0
        max_imports = max(imports_counts) if imports_counts else 0
        max_imported_by = max(imported_by_counts) if imported_by_counts else 0

        # Coupling metrics
        afferent_couplings = []  # Ca - incoming
        efferent_couplings = []  # Ce - outgoing
        instabilities = []

        for module in modules.values():
            ca = len([imp for imp in module.imported_by if imp in modules])
            ce = len([imp for imp in module.imports if imp.target in modules])
            afferent_couplings.append(ca)
            efferent_couplings.append(ce)

            # Instability I = Ce / (Ca + Ce)
            total_coupling = ca + ce
            if total_coupling > 0:
                instabilities.append(ce / total_coupling)
            else:
                instabilities.append(0.0)

        ca_avg = sum(afferent_couplings) / total_modules if total_modules > 0 else 0
        ce_avg = sum(efferent_couplings) / total_modules if total_modules > 0 else 0
        instability_avg = sum(instabilities) / total_modules if total_modules > 0 else 0

        # Entry points
        entry_points = [
            name for name, m in modules.items()
            if m.is_entry_point
        ][:10]  # Top 10

        # Hub modules (high connectivity)
        hub_threshold = avg_imports * 2
        hub_modules = [
            name for name, m in modules.items()
            if len(m.imports) + len(m.imported_by) > hub_threshold * 2
        ][:10]  # Top 10

        return DependencyMetrics(
            total_modules=total_modules,
            total_edges=total_edges,
            external_dependencies=external_deps,
            internal_dependencies=internal_deps,
            circular_dependencies=len(circular_deps),
            average_imports_per_module=avg_imports,
            max_imports=max_imports,
            max_imported_by=max_imported_by,
            afferent_coupling_avg=ca_avg,
            efferent_coupling_avg=ce_avg,
            instability_avg=instability_avg,
            entry_points=entry_points,
            hub_modules=hub_modules
        )

    def _create_clusters(
        self,
        modules: Dict[str, ModuleNode]
    ) -> Dict[str, List[str]]:
        """Create clusters based on directory structure"""
        clusters: Dict[str, List[str]] = defaultdict(list)

        for name, module in modules.items():
            path = Path(module.file_path)
            if len(path.parts) > 1:
                cluster = path.parts[0]
            else:
                cluster = "root"
            clusters[cluster].append(name)

        return dict(clusters)

    def export_mermaid(
        self,
        result: DependencyGraphResult,
        max_nodes: int = 50,
        include_external: bool = False
    ) -> str:
        """Export graph as Mermaid diagram"""
        lines = ["graph TD"]

        # Filter modules
        modules_to_show = list(result.modules.keys())[:max_nodes]

        # Add nodes
        for module_name in modules_to_show:
            module = result.modules[module_name]
            node_id = self._sanitize_mermaid_id(module_name)
            label = module_name.split("/")[-1].split(".")[-1]

            if module.is_entry_point:
                lines.append(f"    {node_id}[[\"{label}\"]]")  # Stadium shape
            else:
                lines.append(f"    {node_id}[\"{label}\"]")

        # Add edges
        for edge in result.edges:
            if edge.source not in modules_to_show:
                continue
            if not include_external and edge.is_external:
                continue
            if edge.target not in modules_to_show and not include_external:
                continue

            source_id = self._sanitize_mermaid_id(edge.source)
            target_id = self._sanitize_mermaid_id(edge.target)
            lines.append(f"    {source_id} --> {target_id}")

        return "\n".join(lines)

    def export_dot(
        self,
        result: DependencyGraphResult,
        max_nodes: int = 100,
        include_external: bool = False
    ) -> str:
        """Export graph as GraphViz DOT format"""
        lines = [
            "digraph dependencies {",
            "    rankdir=LR;",
            "    node [shape=box];",
        ]

        modules_to_show = list(result.modules.keys())[:max_nodes]

        # Add nodes with colors by cluster
        cluster_colors = ["#e6f3ff", "#fff2e6", "#e6ffe6", "#ffe6e6", "#f0e6ff"]
        cluster_list = list(result.clusters.keys())

        for cluster_idx, (cluster, members) in enumerate(result.clusters.items()):
            color = cluster_colors[cluster_idx % len(cluster_colors)]
            lines.append(f"    subgraph cluster_{cluster_idx} {{")
            lines.append(f'        label="{cluster}";')
            lines.append(f'        style=filled;')
            lines.append(f'        color="{color}";')

            for module_name in members:
                if module_name in modules_to_show:
                    node_id = self._sanitize_dot_id(module_name)
                    label = module_name.split("/")[-1].split(".")[-1]
                    lines.append(f'        {node_id} [label="{label}"];')

            lines.append("    }")

        # Add edges
        for edge in result.edges:
            if edge.source not in modules_to_show:
                continue
            if not include_external and edge.is_external:
                continue

            source_id = self._sanitize_dot_id(edge.source)
            target_id = self._sanitize_dot_id(edge.target)
            lines.append(f"    {source_id} -> {target_id};")

        lines.append("}")
        return "\n".join(lines)

    def export_d3(
        self,
        result: DependencyGraphResult,
        max_nodes: int = 100
    ) -> Dict[str, Any]:
        """Export graph as D3.js force-directed graph format"""
        modules_to_show = set(list(result.modules.keys())[:max_nodes])

        nodes = []
        node_index: Dict[str, int] = {}

        for idx, (name, module) in enumerate(result.modules.items()):
            if name not in modules_to_show:
                continue

            node_index[name] = len(nodes)
            nodes.append({
                "id": name,
                "label": name.split("/")[-1].split(".")[-1],
                "group": list(result.clusters.keys()).index(
                    next(
                        (c for c, m in result.clusters.items() if name in m),
                        list(result.clusters.keys())[0] if result.clusters else "root"
                    )
                ) if result.clusters else 0,
                "size": module.lines_of_code / 100,  # Scale by LOC
                "imports": len(module.imports),
                "imported_by": len(module.imported_by),
                "is_entry_point": module.is_entry_point
            })

        links = []
        for edge in result.edges:
            if edge.source not in modules_to_show:
                continue
            if edge.target not in node_index:
                continue

            links.append({
                "source": node_index[edge.source],
                "target": node_index[edge.target],
                "type": edge.import_type,
                "is_external": edge.is_external
            })

        return {
            "nodes": nodes,
            "links": links
        }

    def _sanitize_mermaid_id(self, name: str) -> str:
        """Sanitize name for Mermaid node ID"""
        return re.sub(r"[^a-zA-Z0-9]", "_", name)

    def _sanitize_dot_id(self, name: str) -> str:
        """Sanitize name for DOT node ID"""
        return '"' + name.replace('"', '\\"') + '"'

    def _empty_result(
        self,
        directory: str,
        message: str
    ) -> DependencyGraphResult:
        """Create empty result with message"""
        return DependencyGraphResult(
            project_path=directory,
            languages_detected=[],
            modules={},
            edges=[],
            circular_dependencies=[],
            metrics=DependencyMetrics(
                total_modules=0,
                total_edges=0,
                external_dependencies=0,
                internal_dependencies=0,
                circular_dependencies=0,
                average_imports_per_module=0,
                max_imports=0,
                max_imported_by=0,
                afferent_coupling_avg=0,
                efferent_coupling_avg=0,
                instability_avg=0,
                entry_points=[],
                hub_modules=[]
            ),
            clusters={"_info": [message]}
        )

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "supported_languages": [l.value for l in Language if l != Language.UNKNOWN],
            "output_formats": [f.value for f in OutputFormat],
            "features": [
                "Cross-language import extraction",
                "Circular dependency detection",
                "Coupling/cohesion metrics",
                "Directory-based clustering",
                "Multiple export formats"
            ]
        }
