"""
MP-M-3: Semantic Zoom Service

Adjustable detail levels in code exploration.
Navigate codebase at different abstraction levels.

Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- View code at system, component, class, method, or line level
- Navigate up and down the abstraction hierarchy
- Search at specific abstraction levels
- Context-aware summaries at each level

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
from pathlib import Path
import logging
import os
import re

logger = logging.getLogger(__name__)


class ZoomLevel(Enum):
    """Levels of abstraction for viewing code."""
    SYSTEM = 1       # Entire system overview
    COMPONENT = 2    # Component/module level
    CLASS = 3        # Class/file level
    METHOD = 4       # Method/function level
    LINE = 5         # Line-by-line detail


class ContentType(Enum):
    """Type of content being viewed."""
    DIRECTORY = "directory"
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    BLOCK = "block"


@dataclass
class ZoomChild:
    """A child item at the next zoom level."""
    name: str
    path: str
    content_type: ContentType
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    summary: Optional[str] = None


@dataclass
class ZoomView:
    """A view of code at a specific zoom level."""
    id: UUID
    target_path: str
    current_level: ZoomLevel
    content_type: ContentType
    content: str
    summary: str
    children: List[ZoomChild]
    child_count: int
    parent_path: Optional[str]
    parent_level: Optional[ZoomLevel]
    line_range: Optional[Tuple[int, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class NavigationHistory:
    """History of navigation within a session."""
    view_id: UUID
    path: str
    level: ZoomLevel
    timestamp: datetime


@dataclass
class ZoomSession:
    """A zoom navigation session."""
    id: UUID
    root_path: str
    current_view_id: Optional[UUID]
    history: List[NavigationHistory]
    created_at: datetime


class SemanticZoomService:
    """
    Service for semantic zoom navigation of code.

    The "Semantic Zoom" pattern allows viewing code at different
    abstraction levels, from system overview to line-by-line detail.
    """

    def __init__(self, base_path: Optional[str] = None):
        self._base_path = base_path or os.getcwd()
        self._views: Dict[UUID, ZoomView] = {}
        self._sessions: Dict[UUID, ZoomSession] = {}

    def start_session(self, root_path: str) -> ZoomSession:
        """
        Start a new zoom navigation session.

        Args:
            root_path: Root path to start navigation from

        Returns:
            Created ZoomSession
        """
        session = ZoomSession(
            id=uuid4(),
            root_path=root_path,
            current_view_id=None,
            history=[],
            created_at=datetime.now(timezone.utc)
        )
        self._sessions[session.id] = session
        logger.info(f"Started zoom session {session.id} at {root_path}")
        return session

    def get_view(
        self,
        path: str,
        level: ZoomLevel,
        session_id: Optional[UUID] = None
    ) -> ZoomView:
        """
        Get a view of code at a specific path and zoom level.

        Args:
            path: Path to view
            level: Zoom level to use
            session_id: Optional session to track history

        Returns:
            ZoomView at the specified level
        """
        # Determine content type and parent
        content_type = self._determine_content_type(path, level)
        parent_path, parent_level = self._get_parent_info(path, level)

        # Generate content at this level
        content = self._generate_content(path, level, content_type)
        summary = self._generate_summary(path, level, content_type)
        children = self._get_children(path, level, content_type)

        view = ZoomView(
            id=uuid4(),
            target_path=path,
            current_level=level,
            content_type=content_type,
            content=content,
            summary=summary,
            children=children,
            child_count=len(children),
            parent_path=parent_path,
            parent_level=parent_level
        )

        self._views[view.id] = view

        # Update session if provided
        if session_id:
            session = self._sessions.get(session_id)
            if session:
                session.current_view_id = view.id
                session.history.append(NavigationHistory(
                    view_id=view.id,
                    path=path,
                    level=level,
                    timestamp=datetime.now(timezone.utc)
                ))

        logger.debug(f"Created view {view.id} at {path} level {level.name}")

        return view

    def zoom_in(
        self,
        view_id: UUID,
        target: str,
        session_id: Optional[UUID] = None
    ) -> ZoomView:
        """
        Zoom in to a child element.

        Args:
            view_id: Current view ID
            target: Name or path of child to zoom into
            session_id: Optional session ID

        Returns:
            New ZoomView at deeper level
        """
        current_view = self._views.get(view_id)
        if not current_view:
            raise ValueError(f"View {view_id} not found")

        # Find the target child
        target_child = None
        for child in current_view.children:
            if child.name == target or child.path == target:
                target_child = child
                break

        if not target_child:
            raise ValueError(f"Target '{target}' not found in current view")

        # Determine new zoom level
        new_level = ZoomLevel(min(current_view.current_level.value + 1, ZoomLevel.LINE.value))

        return self.get_view(target_child.path, new_level, session_id)

    def zoom_out(
        self,
        view_id: UUID,
        session_id: Optional[UUID] = None
    ) -> ZoomView:
        """
        Zoom out to parent level.

        Args:
            view_id: Current view ID
            session_id: Optional session ID

        Returns:
            New ZoomView at higher level
        """
        current_view = self._views.get(view_id)
        if not current_view:
            raise ValueError(f"View {view_id} not found")

        if not current_view.parent_path:
            raise ValueError("Already at top level")

        parent_level = current_view.parent_level or ZoomLevel(
            max(current_view.current_level.value - 1, ZoomLevel.SYSTEM.value)
        )

        return self.get_view(current_view.parent_path, parent_level, session_id)

    def get_available_levels(self, path: str) -> List[ZoomLevel]:
        """
        Get available zoom levels for a path.

        Args:
            path: Path to check

        Returns:
            List of available ZoomLevels
        """
        full_path = self._resolve_path(path)
        levels = [ZoomLevel.SYSTEM]

        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                levels.extend([ZoomLevel.COMPONENT, ZoomLevel.CLASS])
            else:
                levels.extend([
                    ZoomLevel.COMPONENT,
                    ZoomLevel.CLASS,
                    ZoomLevel.METHOD,
                    ZoomLevel.LINE
                ])

        return levels

    def search_at_level(
        self,
        query: str,
        level: ZoomLevel,
        root_path: Optional[str] = None,
        limit: int = 20
    ) -> List[ZoomView]:
        """
        Search for content at a specific zoom level.

        Args:
            query: Search query
            level: Zoom level to search at
            root_path: Optional root path to limit search
            limit: Maximum results

        Returns:
            List of matching ZoomViews
        """
        results = []
        search_root = self._resolve_path(root_path or self._base_path)

        if level == ZoomLevel.SYSTEM:
            # Search for matching directories
            for item in os.listdir(search_root):
                if query.lower() in item.lower():
                    item_path = os.path.join(search_root, item)
                    if os.path.isdir(item_path):
                        results.append(self.get_view(item_path, level))
                        if len(results) >= limit:
                            break

        elif level == ZoomLevel.COMPONENT:
            # Search for matching modules/packages
            for root, dirs, files in os.walk(search_root):
                for d in dirs:
                    if query.lower() in d.lower():
                        results.append(self.get_view(os.path.join(root, d), level))
                        if len(results) >= limit:
                            return results

        elif level in (ZoomLevel.CLASS, ZoomLevel.METHOD):
            # Search within files
            for root, dirs, files in os.walk(search_root):
                # Skip hidden and common non-code directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]

                for f in files:
                    if f.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs')):
                        file_path = os.path.join(root, f)
                        matches = self._search_in_file(file_path, query, level)
                        results.extend(matches)
                        if len(results) >= limit:
                            return results[:limit]

        return results[:limit]

    def get_context_at_level(
        self,
        path: str,
        level: ZoomLevel,
        include_siblings: bool = True
    ) -> Dict[str, Any]:
        """
        Get rich context information at a specific level.

        Args:
            path: Path to get context for
            level: Zoom level
            include_siblings: Whether to include sibling items

        Returns:
            Context dictionary with level-appropriate information
        """
        view = self.get_view(path, level)

        context = {
            "level": level.name,
            "path": path,
            "summary": view.summary,
            "child_count": view.child_count,
            "content_type": view.content_type.value
        }

        if include_siblings and view.parent_path:
            parent_view = self.get_view(view.parent_path, view.parent_level or ZoomLevel.COMPONENT)
            siblings = [c for c in parent_view.children if c.path != path]
            context["siblings"] = [{"name": s.name, "type": s.content_type.value} for s in siblings[:10]]

        if level == ZoomLevel.METHOD:
            # Add method-specific context
            context["signature"] = self._extract_signature(path)

        return context

    def _resolve_path(self, path: str) -> str:
        """Resolve a path relative to base path."""
        if os.path.isabs(path):
            return path
        return os.path.join(self._base_path, path)

    def _determine_content_type(self, path: str, level: ZoomLevel) -> ContentType:
        """Determine the content type for a path at a level."""
        full_path = self._resolve_path(path)

        if os.path.isdir(full_path):
            if level == ZoomLevel.SYSTEM:
                return ContentType.DIRECTORY
            return ContentType.DIRECTORY

        if os.path.isfile(full_path):
            if level <= ZoomLevel.CLASS:
                return ContentType.FILE
            return ContentType.FUNCTION

        # For method/function references
        if "::" in path or "." in path:
            if level == ZoomLevel.METHOD:
                return ContentType.METHOD
            return ContentType.FUNCTION

        return ContentType.FILE

    def _get_parent_info(
        self,
        path: str,
        level: ZoomLevel
    ) -> Tuple[Optional[str], Optional[ZoomLevel]]:
        """Get parent path and level."""
        if level == ZoomLevel.SYSTEM:
            return None, None

        full_path = self._resolve_path(path)

        if "::" in path:
            # Method in a class: return the file
            parent = path.split("::")[0]
            return parent, ZoomLevel.CLASS

        if os.path.isfile(full_path):
            return os.path.dirname(full_path), ZoomLevel.COMPONENT

        if os.path.isdir(full_path):
            parent = os.path.dirname(full_path)
            if parent and parent != full_path:
                parent_level = ZoomLevel(max(level.value - 1, 1))
                return parent, parent_level

        return None, None

    def _generate_content(
        self,
        path: str,
        level: ZoomLevel,
        content_type: ContentType
    ) -> str:
        """Generate content at the specified level."""
        full_path = self._resolve_path(path)

        if level == ZoomLevel.SYSTEM:
            return self._generate_system_overview(full_path)
        elif level == ZoomLevel.COMPONENT:
            return self._generate_component_overview(full_path)
        elif level == ZoomLevel.CLASS:
            return self._generate_class_overview(full_path)
        elif level == ZoomLevel.METHOD:
            return self._generate_method_overview(full_path)
        else:
            return self._generate_line_view(full_path)

    def _generate_system_overview(self, path: str) -> str:
        """Generate system-level overview."""
        if not os.path.isdir(path):
            return f"Not a directory: {path}"

        items = os.listdir(path)
        dirs = [i for i in items if os.path.isdir(os.path.join(path, i)) and not i.startswith('.')]
        files = [i for i in items if os.path.isfile(os.path.join(path, i)) and not i.startswith('.')]

        lines = [f"# System Overview: {os.path.basename(path)}", ""]

        if dirs:
            lines.append("## Components/Modules")
            for d in sorted(dirs)[:20]:
                lines.append(f"- {d}/")

        if files:
            lines.append("\n## Root Files")
            for f in sorted(files)[:10]:
                lines.append(f"- {f}")

        return "\n".join(lines)

    def _generate_component_overview(self, path: str) -> str:
        """Generate component-level overview."""
        if os.path.isdir(path):
            return self._generate_directory_overview(path)
        return self._generate_file_structure(path)

    def _generate_class_overview(self, path: str) -> str:
        """Generate class/file level overview."""
        if os.path.isdir(path):
            return self._generate_directory_overview(path)
        return self._generate_file_structure(path)

    def _generate_method_overview(self, path: str) -> str:
        """Generate method-level overview."""
        if "::" in path:
            file_path, symbol = path.split("::", 1)
            return self._extract_symbol(file_path, symbol)
        return self._generate_file_structure(path)

    def _generate_line_view(self, path: str) -> str:
        """Generate line-by-line view."""
        full_path = self._resolve_path(path)
        if os.path.isfile(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
        return f"File not found: {path}"

    def _generate_directory_overview(self, path: str) -> str:
        """Generate overview for a directory."""
        items = []
        try:
            for item in os.listdir(path):
                if item.startswith('.'):
                    continue
                full = os.path.join(path, item)
                if os.path.isdir(full):
                    items.append(f"📁 {item}/")
                else:
                    items.append(f"📄 {item}")
        except Exception as e:
            return f"Error listing directory: {e}"

        return "\n".join(sorted(items))

    def _generate_file_structure(self, path: str) -> str:
        """Generate structure overview for a file."""
        full_path = self._resolve_path(path)
        if not os.path.isfile(full_path):
            return f"File not found: {path}"

        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file: {e}"

        # Extract structure (classes, functions)
        lines = []
        lines.append(f"# {os.path.basename(path)}")
        lines.append("")

        # Find classes and functions (simplified)
        for i, line in enumerate(content.split('\n')):
            if re.match(r'^(class|def|function|fn|func)\s+\w+', line.strip()):
                lines.append(f"- Line {i+1}: {line.strip()[:60]}")

        return "\n".join(lines) if len(lines) > 2 else content[:500]

    def _generate_summary(
        self,
        path: str,
        level: ZoomLevel,
        content_type: ContentType
    ) -> str:
        """Generate a brief summary for the view."""
        full_path = self._resolve_path(path)

        if content_type == ContentType.DIRECTORY:
            if os.path.isdir(full_path):
                count = len([f for f in os.listdir(full_path) if not f.startswith('.')])
                return f"Directory with {count} items"
            return "Directory"

        if content_type == ContentType.FILE:
            if os.path.isfile(full_path):
                size = os.path.getsize(full_path)
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = sum(1 for _ in f)
                return f"File: {line_count} lines, {size} bytes"
            return "File"

        return f"{content_type.value.title()} at {level.name.lower()} level"

    def _get_children(
        self,
        path: str,
        level: ZoomLevel,
        content_type: ContentType
    ) -> List[ZoomChild]:
        """Get children at the next zoom level."""
        children = []
        full_path = self._resolve_path(path)

        if os.path.isdir(full_path):
            try:
                for item in os.listdir(full_path):
                    if item.startswith('.'):
                        continue
                    item_path = os.path.join(full_path, item)
                    item_type = ContentType.DIRECTORY if os.path.isdir(item_path) else ContentType.FILE
                    children.append(ZoomChild(
                        name=item,
                        path=item_path,
                        content_type=item_type
                    ))
            except Exception:
                pass

        elif os.path.isfile(full_path) and level < ZoomLevel.LINE:
            # Extract symbols from file
            children = self._extract_file_symbols(full_path)

        return children

    def _extract_file_symbols(self, path: str) -> List[ZoomChild]:
        """Extract symbols (classes, functions) from a file."""
        children = []

        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            return children

        current_class = None
        for i, line in enumerate(lines):
            # Match class definitions
            class_match = re.match(r'^class\s+(\w+)', line)
            if class_match:
                current_class = class_match.group(1)
                children.append(ZoomChild(
                    name=current_class,
                    path=f"{path}::{current_class}",
                    content_type=ContentType.CLASS,
                    line_start=i + 1
                ))
                continue

            # Match function/method definitions
            func_match = re.match(r'^(\s*)(def|function|fn|func)\s+(\w+)', line)
            if func_match:
                indent = len(func_match.group(1))
                func_name = func_match.group(3)

                if indent > 0 and current_class:
                    # Method
                    children.append(ZoomChild(
                        name=f"{current_class}.{func_name}",
                        path=f"{path}::{current_class}.{func_name}",
                        content_type=ContentType.METHOD,
                        line_start=i + 1
                    ))
                else:
                    # Top-level function
                    current_class = None
                    children.append(ZoomChild(
                        name=func_name,
                        path=f"{path}::{func_name}",
                        content_type=ContentType.FUNCTION,
                        line_start=i + 1
                    ))

        return children

    def _extract_symbol(self, file_path: str, symbol: str) -> str:
        """Extract a specific symbol from a file."""
        full_path = self._resolve_path(file_path)
        if not os.path.isfile(full_path):
            return f"File not found: {file_path}"

        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file: {e}"

        # Simple extraction - find the symbol and return its block
        lines = content.split('\n')
        in_symbol = False
        symbol_lines = []
        base_indent = 0

        for line in lines:
            if not in_symbol:
                if re.search(rf'\b(class|def|function|fn|func)\s+{re.escape(symbol.split(".")[-1])}\b', line):
                    in_symbol = True
                    base_indent = len(line) - len(line.lstrip())
                    symbol_lines.append(line)
            else:
                if line.strip():
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= base_indent and not line.strip().startswith('#'):
                        break
                symbol_lines.append(line)

        return "\n".join(symbol_lines) if symbol_lines else f"Symbol not found: {symbol}"

    def _extract_signature(self, path: str) -> Optional[str]:
        """Extract method/function signature."""
        if "::" not in path:
            return None

        file_path, symbol = path.split("::", 1)
        full_path = self._resolve_path(file_path)

        if not os.path.isfile(full_path):
            return None

        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if re.search(rf'\b(def|function|fn|func)\s+{re.escape(symbol.split(".")[-1])}\b', line):
                        return line.strip()
        except Exception:
            pass

        return None

    def _search_in_file(
        self,
        file_path: str,
        query: str,
        level: ZoomLevel
    ) -> List[ZoomView]:
        """Search for query in a file at the specified level."""
        results = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return results

        if query.lower() in content.lower():
            if level == ZoomLevel.CLASS:
                results.append(self.get_view(file_path, level))
            elif level == ZoomLevel.METHOD:
                # Find matching methods
                for child in self._extract_file_symbols(file_path):
                    if query.lower() in child.name.lower():
                        results.append(self.get_view(child.path, level))

        return results
