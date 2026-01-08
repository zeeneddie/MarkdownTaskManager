# Include File Resolver
# Resolves and loads include files for cross-file analysis in Classic ASP
#
# Features:
# - Resolves #include directives (virtual and file)
# - Builds include dependency graph
# - Detects circular includes
# - Caches loaded files for performance
# - Provides merged file content for analysis
#
# Week 144 Implementation

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import re
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class IncludeDirective:
    """Represents a single include directive."""
    line_number: int
    include_type: str  # 'virtual' or 'file'
    path: str
    resolved_path: Optional[str] = None
    exists: bool = False


@dataclass
class IncludeGraph:
    """Represents the include dependency graph."""
    root_file: str
    includes: Dict[str, List[str]] = field(default_factory=dict)  # file -> list of included files
    reverse_includes: Dict[str, List[str]] = field(default_factory=dict)  # file -> files that include it
    circular_refs: List[Tuple[str, str]] = field(default_factory=list)
    all_files: Set[str] = field(default_factory=set)

    def add_include(self, parent: str, child: str) -> bool:
        """
        Add an include relationship. Returns False if circular.
        """
        # Check for circular reference
        if self._would_create_cycle(parent, child):
            self.circular_refs.append((parent, child))
            return False

        # Add to graph
        if parent not in self.includes:
            self.includes[parent] = []
        self.includes[parent].append(child)

        if child not in self.reverse_includes:
            self.reverse_includes[child] = []
        self.reverse_includes[child].append(parent)

        self.all_files.add(parent)
        self.all_files.add(child)
        return True

    def _would_create_cycle(self, parent: str, child: str) -> bool:
        """Check if adding parent->child would create a cycle."""
        if parent == child:
            return True

        # DFS to check if child can reach parent
        visited = set()
        stack = [child]

        while stack:
            current = stack.pop()
            if current == parent:
                return True
            if current in visited:
                continue
            visited.add(current)

            # Add all files that current includes
            if current in self.includes:
                stack.extend(self.includes[current])

        return False

    def get_all_includes(self, file_path: str) -> Set[str]:
        """Get all files included by file_path (recursive)."""
        result = set()
        stack = [file_path]
        visited = set()

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            if current in self.includes:
                for included in self.includes[current]:
                    result.add(included)
                    stack.append(included)

        return result

    def get_include_order(self, file_path: str) -> List[str]:
        """Get files in dependency order (included files first)."""
        result = []
        visited = set()

        def dfs(file: str):
            if file in visited:
                return
            visited.add(file)

            # Visit dependencies first
            if file in self.includes:
                for dep in self.includes[file]:
                    dfs(dep)

            result.append(file)

        dfs(file_path)
        return result


@dataclass
class ResolvedFile:
    """Represents a resolved and loaded file."""
    original_path: str
    resolved_path: str
    content: str
    includes: List[IncludeDirective] = field(default_factory=list)
    line_count: int = 0

    @property
    def exists(self) -> bool:
        return len(self.content) > 0


@dataclass
class MergedContent:
    """Represents merged content from multiple files."""
    root_file: str
    content: str
    line_mapping: Dict[int, Tuple[str, int]] = field(default_factory=dict)  # merged_line -> (file, original_line)
    included_files: List[str] = field(default_factory=list)
    total_lines: int = 0


class IncludeResolver:
    """
    Resolves and loads include files for Classic ASP analysis.

    Handles:
    - <!--#include virtual="/path/to/file.inc"-->
    - <!--#include file="relative/path.inc"-->

    Features:
    - Caches loaded files for performance
    - Builds include dependency graph
    - Detects circular includes
    - Provides merged content for analysis
    """

    # Include directive patterns
    INCLUDE_VIRTUAL_PATTERN = r'<!--\s*#include\s+virtual\s*=\s*["\']([^"\']+)["\']\s*-->'
    INCLUDE_FILE_PATTERN = r'<!--\s*#include\s+file\s*=\s*["\']([^"\']+)["\']\s*-->'

    def __init__(self, web_root: Optional[str] = None):
        """
        Initialize the resolver.

        Args:
            web_root: The web root directory for virtual includes.
                      If not provided, will try to detect from file paths.
        """
        self.web_root = web_root
        self._file_cache: Dict[str, ResolvedFile] = {}
        self._include_graph: Optional[IncludeGraph] = None

        # Compile patterns
        self._virtual_pattern = re.compile(self.INCLUDE_VIRTUAL_PATTERN, re.IGNORECASE)
        self._file_pattern = re.compile(self.INCLUDE_FILE_PATTERN, re.IGNORECASE)

    def set_web_root(self, web_root: str) -> None:
        """Set the web root directory."""
        self.web_root = os.path.abspath(web_root)

    def detect_web_root(self, file_path: str) -> Optional[str]:
        """
        Try to detect web root from common directory patterns.

        Looks for:
        - wwwroot
        - htdocs
        - public_html
        - web
        - www
        """
        path = Path(file_path).absolute()

        # Walk up the directory tree
        for parent in path.parents:
            if parent.name.lower() in ['wwwroot', 'htdocs', 'public_html', 'web', 'www']:
                return str(parent)

            # Check for common IIS/Apache config files
            if (parent / 'web.config').exists() or (parent / '.htaccess').exists():
                return str(parent)

        return None

    def find_includes(self, content: str) -> List[IncludeDirective]:
        """
        Find all include directives in content.

        Args:
            content: File content to search

        Returns:
            List of IncludeDirective objects
        """
        includes = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Check for virtual include
            match = self._virtual_pattern.search(line)
            if match:
                includes.append(IncludeDirective(
                    line_number=line_num,
                    include_type='virtual',
                    path=match.group(1),
                ))
                continue

            # Check for file include
            match = self._file_pattern.search(line)
            if match:
                includes.append(IncludeDirective(
                    line_number=line_num,
                    include_type='file',
                    path=match.group(1),
                ))

        return includes

    def resolve_include_path(
        self,
        include: IncludeDirective,
        parent_file: str
    ) -> Optional[str]:
        """
        Resolve an include directive to an absolute file path.

        Args:
            include: The include directive
            parent_file: The file containing the include

        Returns:
            Absolute path to the included file, or None if not resolvable
        """
        if include.include_type == 'virtual':
            return self._resolve_virtual(include.path, parent_file)
        else:
            return self._resolve_file(include.path, parent_file)

    def _resolve_virtual(self, path: str, parent_file: str) -> Optional[str]:
        """Resolve a virtual include path."""
        # Try explicit web root first
        if self.web_root:
            resolved = os.path.join(self.web_root, path.lstrip('/'))
            if os.path.exists(resolved):
                return os.path.abspath(resolved)

        # Try to detect web root
        detected_root = self.detect_web_root(parent_file)
        if detected_root:
            resolved = os.path.join(detected_root, path.lstrip('/'))
            if os.path.exists(resolved):
                return os.path.abspath(resolved)

        # Try parent directories
        parent_dir = Path(parent_file).parent
        for _ in range(10):  # Max 10 levels up
            resolved = parent_dir / path.lstrip('/')
            if resolved.exists():
                return str(resolved.absolute())
            parent_dir = parent_dir.parent
            if parent_dir == parent_dir.parent:  # Reached root
                break

        return None

    def _resolve_file(self, path: str, parent_file: str) -> Optional[str]:
        """Resolve a file include path (relative to parent)."""
        parent_dir = Path(parent_file).parent
        resolved = parent_dir / path

        if resolved.exists():
            return str(resolved.absolute())

        # Try without leading ./
        if path.startswith('./'):
            resolved = parent_dir / path[2:]
            if resolved.exists():
                return str(resolved.absolute())

        return None

    def load_file(self, file_path: str) -> ResolvedFile:
        """
        Load a file and find its includes.

        Args:
            file_path: Path to the file

        Returns:
            ResolvedFile object
        """
        abs_path = os.path.abspath(file_path)

        # Check cache
        if abs_path in self._file_cache:
            return self._file_cache[abs_path]

        # Load file
        content = ""
        try:
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except (IOError, OSError) as e:
            logger.warning(f"Could not load file {abs_path}: {e}")

        # Find includes
        includes = self.find_includes(content) if content else []

        # Resolve include paths
        for inc in includes:
            resolved = self.resolve_include_path(inc, abs_path)
            if resolved:
                inc.resolved_path = resolved
                inc.exists = os.path.exists(resolved)

        result = ResolvedFile(
            original_path=file_path,
            resolved_path=abs_path,
            content=content,
            includes=includes,
            line_count=len(content.split('\n')) if content else 0,
        )

        self._file_cache[abs_path] = result
        return result

    def build_include_graph(self, root_file: str) -> IncludeGraph:
        """
        Build the complete include dependency graph starting from root_file.

        Args:
            root_file: The root file to start from

        Returns:
            IncludeGraph representing all dependencies
        """
        graph = IncludeGraph(root_file=os.path.abspath(root_file))
        visited: Set[str] = set()
        stack = [os.path.abspath(root_file)]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            graph.all_files.add(current)

            # Load and analyze file
            resolved = self.load_file(current)

            for include in resolved.includes:
                if include.resolved_path and include.exists:
                    # Add to graph (will detect circular refs)
                    if graph.add_include(current, include.resolved_path):
                        stack.append(include.resolved_path)

        self._include_graph = graph
        return graph

    def get_merged_content(
        self,
        root_file: str,
        max_depth: int = 10
    ) -> MergedContent:
        """
        Get merged content from root file and all includes.

        The merged content can be used for analysis that needs to see
        the complete code including all includes.

        Args:
            root_file: The root file to start from
            max_depth: Maximum include depth (prevents infinite loops)

        Returns:
            MergedContent with all includes merged in order
        """
        # Build graph if not already built
        graph = self.build_include_graph(root_file)

        # Get files in dependency order
        ordered_files = graph.get_include_order(os.path.abspath(root_file))

        # Merge content
        merged_lines = []
        line_mapping: Dict[int, Tuple[str, int]] = {}
        included_files = []

        current_merged_line = 1

        for file_path in ordered_files:
            resolved = self.load_file(file_path)
            if not resolved.content:
                continue

            included_files.append(file_path)
            file_lines = resolved.content.split('\n')

            for original_line_num, line in enumerate(file_lines, 1):
                # Skip include directives in merged output
                if self._virtual_pattern.search(line) or self._file_pattern.search(line):
                    # Add a comment instead
                    merged_lines.append(f"' [INCLUDED: {line.strip()}]")
                else:
                    merged_lines.append(line)

                line_mapping[current_merged_line] = (file_path, original_line_num)
                current_merged_line += 1

        return MergedContent(
            root_file=root_file,
            content='\n'.join(merged_lines),
            line_mapping=line_mapping,
            included_files=included_files,
            total_lines=len(merged_lines),
        )

    def get_original_location(
        self,
        merged_line: int,
        merged_content: MergedContent
    ) -> Optional[Tuple[str, int]]:
        """
        Map a merged content line back to original file and line.

        Args:
            merged_line: Line number in merged content
            merged_content: The MergedContent object

        Returns:
            Tuple of (file_path, original_line) or None
        """
        return merged_content.line_mapping.get(merged_line)

    def get_files_that_include(self, file_path: str) -> List[str]:
        """
        Get all files that include the given file.

        Args:
            file_path: Path to the file

        Returns:
            List of files that include this file
        """
        if not self._include_graph:
            return []

        abs_path = os.path.abspath(file_path)
        return self._include_graph.reverse_includes.get(abs_path, [])

    def get_include_depth(self, file_path: str) -> int:
        """
        Get the maximum depth of includes from this file.

        Args:
            file_path: Path to the file

        Returns:
            Maximum include depth (0 if no includes)
        """
        if not self._include_graph:
            return 0

        abs_path = os.path.abspath(file_path)

        def get_depth(path: str, visited: Set[str]) -> int:
            if path in visited:
                return 0
            visited.add(path)

            includes = self._include_graph.includes.get(path, [])
            if not includes:
                return 0

            return 1 + max(get_depth(inc, visited) for inc in includes)

        return get_depth(abs_path, set())

    def clear_cache(self) -> None:
        """Clear the file cache."""
        self._file_cache.clear()
        self._include_graph = None

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_files": len(self._file_cache),
            "total_lines_cached": sum(f.line_count for f in self._file_cache.values()),
        }
