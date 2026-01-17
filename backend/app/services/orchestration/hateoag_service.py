"""
HATEOAG Navigation Framework - Week 107 (AO-QW-1)

Hypertext as Engine of Agent Guidance - Meta-framework for agent navigation.

Based on Gregor Riegler's Augmented Coding Pattern Language:
https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html

Key Principles:
1. Agents navigate via linked processes, documentation, and code
2. Process files contain links to next steps
3. State is tracked via Cross-Context Memory
4. Starter Symbols provide visual feedback on progress

Features:
- Process file parsing and link extraction
- Navigation state tracking
- Hyperlink-based workflow execution
- Cycle detection and max depth limits
- Checkpoint recovery support
"""

import re
import json
import hashlib
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set, Callable


class LinkType(str, Enum):
    """Types of navigation links in process files."""
    NEXT_STEP = "next_step"           # Sequential next action
    BRANCH = "branch"                  # Conditional branch
    REFERENCE = "reference"            # Documentation reference
    TOOL = "tool"                      # MCP tool invocation
    PROCESS = "process"                # Sub-process call
    CHECKPOINT = "checkpoint"          # Savepoint for recovery
    LOOP_START = "loop_start"          # Beginning of iterative section
    LOOP_END = "loop_end"              # End of iterative section
    ERROR_HANDLER = "error_handler"    # Error recovery path
    GOAL = "goal"                      # Target outcome


class NodeStatus(str, Enum):
    """Status of a process node."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class NavigationLink:
    """
    A navigable link within a process file.

    Links enable agents to move between process nodes,
    reference documentation, or invoke tools.
    """
    id: str
    link_type: LinkType
    target: str                         # Target path, URL, or tool name
    label: str                          # Human-readable description
    condition: Optional[str] = None     # Condition for conditional links
    priority: int = 0                   # Higher = more important
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches_condition(self, context: Dict[str, Any]) -> bool:
        """Check if this link's condition is satisfied."""
        if not self.condition:
            return True
        try:
            # Safe evaluation of simple conditions
            return self._evaluate_condition(context)
        except Exception:
            return False

    def _evaluate_condition(self, context: Dict[str, Any]) -> bool:
        """Safely evaluate condition against context."""
        # Simple key=value or key!=value conditions
        if "==" in self.condition:
            key, value = self.condition.split("==", 1)
            return str(context.get(key.strip())) == value.strip().strip("'\"")
        if "!=" in self.condition:
            key, value = self.condition.split("!=", 1)
            return str(context.get(key.strip())) != value.strip().strip("'\"")
        if self.condition.startswith("not "):
            key = self.condition[4:].strip()
            return not context.get(key)
        # Boolean check
        return bool(context.get(self.condition))


@dataclass
class ProcessNode:
    """
    A node in the navigation graph representing a process step.

    Each node contains:
    - Unique identifier
    - Description of what happens at this node
    - Outgoing links to other nodes
    - Status tracking
    - Execution metadata
    """
    id: str
    name: str
    description: str
    links: List[NavigationLink] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    execution_count: int = 0
    error_message: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    checkpoint_data: Optional[Dict[str, Any]] = None

    def get_available_links(self, context: Dict[str, Any]) -> List[NavigationLink]:
        """Get links whose conditions are satisfied."""
        available = [link for link in self.links if link.matches_condition(context)]
        return sorted(available, key=lambda x: -x.priority)

    def get_next_step(self, context: Dict[str, Any]) -> Optional[NavigationLink]:
        """Get the primary next step link."""
        next_links = [
            link for link in self.get_available_links(context)
            if link.link_type == LinkType.NEXT_STEP
        ]
        return next_links[0] if next_links else None

    def mark_started(self) -> None:
        """Mark node as in progress."""
        self.status = NodeStatus.IN_PROGRESS
        self.entry_time = datetime.now(timezone.utc)
        self.execution_count += 1

    def mark_completed(self, output: Optional[Dict[str, Any]] = None) -> None:
        """Mark node as completed."""
        self.status = NodeStatus.COMPLETED
        self.exit_time = datetime.now(timezone.utc)
        self.output = output

    def mark_failed(self, error: str) -> None:
        """Mark node as failed."""
        self.status = NodeStatus.FAILED
        self.exit_time = datetime.now(timezone.utc)
        self.error_message = error


@dataclass
class NavigationState:
    """
    Current state of agent navigation through a process.

    Tracks:
    - Current position in the process graph
    - History of visited nodes
    - Active context variables
    - Checkpoint for recovery
    """
    process_id: str
    current_node_id: str
    visited_nodes: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    checkpoints: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    iteration_counts: Dict[str, int] = field(default_factory=dict)
    max_iterations: int = 10
    max_depth: int = 50

    def visit(self, node_id: str) -> bool:
        """
        Record visiting a node.

        Returns False if max depth exceeded.
        """
        if len(self.visited_nodes) >= self.max_depth:
            return False
        self.visited_nodes.append(node_id)
        self.current_node_id = node_id
        return True

    def get_iteration_count(self, loop_id: str) -> int:
        """Get current iteration count for a loop."""
        return self.iteration_counts.get(loop_id, 0)

    def increment_iteration(self, loop_id: str) -> int:
        """Increment and return iteration count for a loop."""
        count = self.iteration_counts.get(loop_id, 0) + 1
        self.iteration_counts[loop_id] = count
        return count

    def create_checkpoint(self, checkpoint_id: str) -> None:
        """Save current state as a checkpoint."""
        self.checkpoints[checkpoint_id] = {
            "current_node_id": self.current_node_id,
            "visited_nodes": self.visited_nodes.copy(),
            "context": self.context.copy(),
            "iteration_counts": self.iteration_counts.copy(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore state from a checkpoint."""
        if checkpoint_id not in self.checkpoints:
            return False
        checkpoint = self.checkpoints[checkpoint_id]
        self.current_node_id = checkpoint["current_node_id"]
        self.visited_nodes = checkpoint["visited_nodes"].copy()
        self.context = checkpoint["context"].copy()
        self.iteration_counts = checkpoint["iteration_counts"].copy()
        return True


class ProcessFileParser:
    """
    Parser for HATEOAG process files in Markdown format.

    Process files use a structured format with:
    - YAML frontmatter for metadata
    - Markdown sections for steps
    - Special link syntax for navigation
    """

    LINK_PATTERN = re.compile(
        r'\[(?P<label>[^\]]+)\]\((?P<target>[^\)]+)\)'
        r'(?:\s*\{(?P<attrs>[^\}]+)\})?'
    )

    NODE_PATTERN = re.compile(
        r'^##\s+(?P<id>\S+):\s+(?P<name>.+)$',
        re.MULTILINE
    )

    def parse_file(self, content: str) -> Dict[str, ProcessNode]:
        """Parse a process file and extract nodes with links."""
        nodes: Dict[str, ProcessNode] = {}

        # Split into sections by ## headers
        sections = re.split(r'\n(?=##\s+)', content)

        for section in sections:
            node = self._parse_section(section)
            if node:
                nodes[node.id] = node

        return nodes

    def _parse_section(self, section: str) -> Optional[ProcessNode]:
        """Parse a single section into a ProcessNode."""
        lines = section.strip().split('\n')
        if not lines:
            return None

        # Parse header
        header_match = self.NODE_PATTERN.match(lines[0])
        if not header_match:
            return None

        node_id = header_match.group('id')
        name = header_match.group('name')

        # Parse body
        body_lines = lines[1:]
        description_lines = []
        links = []

        for line in body_lines:
            # Check for links
            for match in self.LINK_PATTERN.finditer(line):
                link = self._parse_link(match)
                if link:
                    links.append(link)

            # Collect description (non-link lines)
            if not self.LINK_PATTERN.search(line):
                description_lines.append(line)

        return ProcessNode(
            id=node_id,
            name=name,
            description='\n'.join(description_lines).strip(),
            links=links
        )

    def _parse_link(self, match: re.Match) -> Optional[NavigationLink]:
        """Parse a link match into a NavigationLink."""
        label = match.group('label')
        target = match.group('target')
        attrs_str = match.group('attrs') or ''

        # Parse attributes
        attrs = {}
        for attr in attrs_str.split(','):
            if '=' in attr:
                key, value = attr.split('=', 1)
                attrs[key.strip()] = value.strip().strip('"\'')

        # Determine link type from target or attributes
        link_type = self._determine_link_type(target, attrs)

        return NavigationLink(
            id=hashlib.md5(f"{label}:{target}".encode()).hexdigest()[:8],
            link_type=link_type,
            target=target,
            label=label,
            condition=attrs.get('condition'),
            priority=int(attrs.get('priority', 0)),
            metadata=attrs
        )

    def _determine_link_type(self, target: str, attrs: Dict[str, str]) -> LinkType:
        """Determine link type from target and attributes."""
        if 'type' in attrs:
            return LinkType(attrs['type'])

        if target.startswith('mcp://') or target.startswith('tool://'):
            return LinkType.TOOL
        if target.startswith('process://'):
            return LinkType.PROCESS
        if target.startswith('#checkpoint:'):
            return LinkType.CHECKPOINT
        if target.startswith('#loop-start:'):
            return LinkType.LOOP_START
        if target.startswith('#loop-end:'):
            return LinkType.LOOP_END
        if target.startswith('#error:'):
            return LinkType.ERROR_HANDLER
        if 'condition' in attrs:
            return LinkType.BRANCH
        if target.endswith('.md') or target.startswith('http'):
            return LinkType.REFERENCE

        return LinkType.NEXT_STEP


class HATEOAGService:
    """
    HATEOAG Navigation Framework Service.

    Provides:
    - Process file loading and parsing
    - Navigation state management
    - Link traversal with cycle detection
    - Checkpoint creation and recovery
    - Progress visualization

    Usage:
        service = HATEOAGService()

        # Load a process
        process = service.load_process("workflows/green_paper.md")

        # Start navigation
        state = service.start_navigation(process.id)

        # Navigate
        while not service.is_complete(state):
            node = service.get_current_node(state)
            next_link = node.get_next_step(state.context)
            if next_link:
                service.navigate(state, next_link.target)
    """

    def __init__(
        self,
        process_dir: Optional[Path] = None,
        max_iterations: int = 10,
        max_depth: int = 50,
    ):
        """
        Initialize HATEOAG service.

        Args:
            process_dir: Directory containing process files
            max_iterations: Maximum loop iterations (prevent infinite loops)
            max_depth: Maximum navigation depth (prevent deep recursion)
        """
        self.process_dir = process_dir or Path("processes")
        self.max_iterations = max_iterations
        self.max_depth = max_depth
        self.parser = ProcessFileParser()

        # In-memory storage
        self._processes: Dict[str, Dict[str, ProcessNode]] = {}
        self._states: Dict[str, NavigationState] = {}
        self._hooks: Dict[str, List[Callable]] = {
            "on_node_enter": [],
            "on_node_exit": [],
            "on_checkpoint": [],
            "on_error": [],
        }

    # === Process Management ===

    def load_process(self, file_path: str) -> Dict[str, ProcessNode]:
        """
        Load and parse a process file.

        Args:
            file_path: Path to process file (relative to process_dir)

        Returns:
            Dictionary of process nodes keyed by node ID
        """
        full_path = self.process_dir / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"Process file not found: {full_path}")

        content = full_path.read_text(encoding='utf-8')
        nodes = self.parser.parse_file(content)

        process_id = file_path.replace('/', '_').replace('.md', '')
        self._processes[process_id] = nodes

        return nodes

    def load_process_from_string(self, process_id: str, content: str) -> Dict[str, ProcessNode]:
        """
        Load a process from string content.

        Args:
            process_id: Unique identifier for this process
            content: Markdown content of the process file

        Returns:
            Dictionary of process nodes
        """
        nodes = self.parser.parse_file(content)
        self._processes[process_id] = nodes
        return nodes

    def get_process(self, process_id: str) -> Optional[Dict[str, ProcessNode]]:
        """Get a loaded process by ID."""
        return self._processes.get(process_id)

    def list_processes(self) -> List[str]:
        """List all loaded process IDs."""
        return list(self._processes.keys())

    # === Navigation State Management ===

    def start_navigation(
        self,
        process_id: str,
        start_node_id: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> NavigationState:
        """
        Start navigating a process.

        Args:
            process_id: ID of the process to navigate
            start_node_id: Optional starting node (defaults to first node)
            initial_context: Initial context variables

        Returns:
            Navigation state for tracking progress
        """
        process = self._processes.get(process_id)
        if not process:
            raise ValueError(f"Process not found: {process_id}")

        # Determine start node
        if start_node_id and start_node_id in process:
            start_id = start_node_id
        else:
            # Use first node
            start_id = next(iter(process.keys()))

        # Create state
        state = NavigationState(
            process_id=process_id,
            current_node_id=start_id,
            context=initial_context or {},
            max_iterations=self.max_iterations,
            max_depth=self.max_depth,
        )

        # Store state
        state_id = f"{process_id}_{datetime.now(timezone.utc).timestamp()}"
        self._states[state_id] = state

        # Mark start node
        state.visit(start_id)
        process[start_id].mark_started()

        # Fire hooks
        self._fire_hook("on_node_enter", state, process[start_id])

        return state

    def get_current_node(self, state: NavigationState) -> Optional[ProcessNode]:
        """Get the current node in navigation."""
        process = self._processes.get(state.process_id)
        if not process:
            return None
        return process.get(state.current_node_id)

    def navigate(
        self,
        state: NavigationState,
        target: str,
        output: Optional[Dict[str, Any]] = None,
    ) -> Optional[ProcessNode]:
        """
        Navigate to a target node.

        Args:
            state: Current navigation state
            target: Target node ID or path
            output: Output from current node (passed to next node)

        Returns:
            The new current node, or None if navigation failed
        """
        process = self._processes.get(state.process_id)
        if not process:
            return None

        # Get current node
        current = process.get(state.current_node_id)
        if current:
            current.mark_completed(output)
            self._fire_hook("on_node_exit", state, current)

            # Store output in context
            if output:
                state.context[f"{current.id}_output"] = output

        # Parse target
        target_id = self._resolve_target(target, state)

        # Check for cycles / depth limit
        if not state.visit(target_id):
            self._fire_hook("on_error", state, None, "Max depth exceeded")
            return None

        # Get target node
        target_node = process.get(target_id)
        if not target_node:
            self._fire_hook("on_error", state, None, f"Target not found: {target_id}")
            return None

        # Mark target as started
        target_node.mark_started()
        self._fire_hook("on_node_enter", state, target_node)

        return target_node

    def navigate_next(
        self,
        state: NavigationState,
        output: Optional[Dict[str, Any]] = None,
    ) -> Optional[ProcessNode]:
        """
        Navigate to the next step automatically.

        Uses the first available NEXT_STEP link from current node.

        Args:
            state: Current navigation state
            output: Output from current node

        Returns:
            The new current node, or None if no next step
        """
        current = self.get_current_node(state)
        if not current:
            return None

        next_link = current.get_next_step(state.context)
        if not next_link:
            return None

        return self.navigate(state, next_link.target, output)

    def _resolve_target(self, target: str, state: NavigationState) -> str:
        """Resolve a target string to a node ID."""
        # Handle special targets
        if target.startswith('#'):
            # Internal reference
            return target[1:]
        if target.startswith('process://'):
            # Cross-process reference (not fully implemented yet)
            return target.split('/')[-1]

        # Direct node ID
        return target

    # === Checkpoint Management ===

    def create_checkpoint(
        self,
        state: NavigationState,
        checkpoint_id: str,
    ) -> None:
        """
        Create a checkpoint for state recovery.

        Args:
            state: Navigation state to checkpoint
            checkpoint_id: Unique identifier for this checkpoint
        """
        state.create_checkpoint(checkpoint_id)

        # Also store node checkpoint data
        current = self.get_current_node(state)
        if current:
            current.checkpoint_data = {
                "state_context": state.context.copy(),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        self._fire_hook("on_checkpoint", state, current, checkpoint_id)

    def restore_checkpoint(
        self,
        state: NavigationState,
        checkpoint_id: str,
    ) -> bool:
        """
        Restore state from a checkpoint.

        Args:
            state: Navigation state to restore
            checkpoint_id: Checkpoint to restore from

        Returns:
            True if restore successful
        """
        return state.restore_checkpoint(checkpoint_id)

    # === Loop Handling ===

    def enter_loop(
        self,
        state: NavigationState,
        loop_id: str,
    ) -> int:
        """
        Enter a loop and get current iteration.

        Args:
            state: Navigation state
            loop_id: Unique identifier for the loop

        Returns:
            Current iteration number (1-based)
        """
        return state.increment_iteration(loop_id)

    def should_continue_loop(
        self,
        state: NavigationState,
        loop_id: str,
    ) -> bool:
        """
        Check if loop should continue.

        Args:
            state: Navigation state
            loop_id: Loop identifier

        Returns:
            True if iterations < max_iterations
        """
        count = state.get_iteration_count(loop_id)
        return count < state.max_iterations

    # === Progress & Status ===

    def is_complete(self, state: NavigationState) -> bool:
        """Check if navigation is complete (no more next steps)."""
        current = self.get_current_node(state)
        if not current:
            return True

        # Complete if current node has no outgoing links
        available = current.get_available_links(state.context)
        return len(available) == 0

    def get_progress(self, state: NavigationState) -> Dict[str, Any]:
        """
        Get navigation progress summary.

        Returns:
            Progress information including:
            - visited_count: Number of nodes visited
            - total_nodes: Total nodes in process
            - completion_percent: Estimated completion
            - current_node: Current node info
            - checkpoints: Available checkpoints
        """
        process = self._processes.get(state.process_id)
        if not process:
            return {"error": "Process not found"}

        visited_unique = set(state.visited_nodes)
        total = len(process)

        return {
            "process_id": state.process_id,
            "visited_count": len(visited_unique),
            "total_nodes": total,
            "completion_percent": (len(visited_unique) / total * 100) if total else 0,
            "current_node": {
                "id": state.current_node_id,
                "name": process[state.current_node_id].name if state.current_node_id in process else None,
            },
            "depth": len(state.visited_nodes),
            "checkpoints": list(state.checkpoints.keys()),
            "iteration_counts": state.iteration_counts.copy(),
            "started_at": state.started_at.isoformat(),
        }

    def get_visual_progress(self, state: NavigationState) -> str:
        """
        Get visual progress indicator with emoji markers.

        Returns:
            Formatted string with state indicators
        """
        process = self._processes.get(state.process_id)
        if not process:
            return "Process not found"

        lines = []
        lines.append(f"CURRENT_STATE: {state.current_node_id}")

        completed = [
            nid for nid, node in process.items()
            if node.status == NodeStatus.COMPLETED
        ]
        lines.append(f"COMPLETED: {completed}")

        pending = [
            nid for nid, node in process.items()
            if node.status == NodeStatus.PENDING
        ]
        lines.append(f"PENDING: {pending}")

        if state.iteration_counts:
            for loop_id, count in state.iteration_counts.items():
                lines.append(f"ITERATION ({loop_id}): {count}/{state.max_iterations}")

        return '\n'.join(lines)

    # === Hook System ===

    def register_hook(
        self,
        event: str,
        callback: Callable,
    ) -> None:
        """
        Register a callback for navigation events.

        Events:
        - on_node_enter: Called when entering a node
        - on_node_exit: Called when leaving a node
        - on_checkpoint: Called when checkpoint created
        - on_error: Called on navigation error
        """
        if event in self._hooks:
            self._hooks[event].append(callback)

    def _fire_hook(
        self,
        event: str,
        state: NavigationState,
        node: Optional[ProcessNode],
        *args,
    ) -> None:
        """Fire all callbacks for an event."""
        for callback in self._hooks.get(event, []):
            try:
                callback(state, node, *args)
            except Exception:
                pass  # Don't let hook errors break navigation

    # === Serialization ===

    def export_state(self, state: NavigationState) -> Dict[str, Any]:
        """Export navigation state to JSON-serializable dict."""
        return {
            "process_id": state.process_id,
            "current_node_id": state.current_node_id,
            "visited_nodes": state.visited_nodes,
            "context": state.context,
            "checkpoints": state.checkpoints,
            "started_at": state.started_at.isoformat(),
            "iteration_counts": state.iteration_counts,
        }

    def import_state(self, data: Dict[str, Any]) -> NavigationState:
        """Import navigation state from dict."""
        state = NavigationState(
            process_id=data["process_id"],
            current_node_id=data["current_node_id"],
            visited_nodes=data.get("visited_nodes", []),
            context=data.get("context", {}),
            checkpoints=data.get("checkpoints", {}),
            iteration_counts=data.get("iteration_counts", {}),
            max_iterations=self.max_iterations,
            max_depth=self.max_depth,
        )

        if "started_at" in data:
            state.started_at = datetime.fromisoformat(data["started_at"])

        return state


# Convenience function for quick process creation
def create_simple_process(
    steps: List[Dict[str, str]],
    process_id: str = "simple_process",
) -> Dict[str, ProcessNode]:
    """
    Create a simple linear process from a list of steps.

    Args:
        steps: List of dicts with 'id', 'name', 'description'
        process_id: Process identifier

    Returns:
        Dictionary of ProcessNodes

    Example:
        process = create_simple_process([
            {"id": "step1", "name": "Initialize", "description": "Set up project"},
            {"id": "step2", "name": "Analyze", "description": "Analyze requirements"},
            {"id": "step3", "name": "Complete", "description": "Finalize"},
        ])
    """
    nodes: Dict[str, ProcessNode] = {}

    for i, step in enumerate(steps):
        links = []

        # Add link to next step if not last
        if i < len(steps) - 1:
            next_step = steps[i + 1]
            links.append(NavigationLink(
                id=f"link_{step['id']}_to_{next_step['id']}",
                link_type=LinkType.NEXT_STEP,
                target=next_step['id'],
                label=f"Continue to {next_step['name']}",
            ))

        nodes[step['id']] = ProcessNode(
            id=step['id'],
            name=step['name'],
            description=step.get('description', ''),
            links=links,
        )

    return nodes
