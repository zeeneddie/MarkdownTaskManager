"""
Process File Standard Service

Week 108 - AO-M-3: Standard format for process files with navigation links.

Based on Gregor Riegler's Augmented Coding Pattern Language:
- Standardized process file format (markdown-based)
- Navigation links between steps (HATEOAG integration)
- Conditional steps and loops
- Checkpoints and recovery points
- Variables and context passing

Process File Format:
```markdown
# Process: Feature Development

## Metadata
- **ID**: process-feature-001
- **Version**: 1.0
- **Author**: Felix
- **Created**: 2024-12-24

## Context Variables
- `feature_name`: string (required)
- `priority`: enum[low, medium, high] (default: medium)
- `has_tests`: boolean (default: true)

## Steps

### [step:analyze] Analyze Requirements
**Checkpoint**: true

Analyze the feature requirements and create user stories.

**Expected Output**: User stories in markdown format

**Actions**:
- Read requirements document
- Identify acceptance criteria
- Create user stories

**Navigation**:
- [Next: Design](#step:design) when analysis complete
- [Skip: Implementation](#step:implement) when design exists

### [step:design] Design Solution
...
```

Example usage:
    service = ProcessFileService()

    # Parse a process file
    process = service.parse_file("./processes/feature_development.md")

    # Validate the process
    errors = service.validate(process)

    # Generate a process file from template
    content = service.generate(
        name="Bug Fix",
        steps=[...],
        variables=[...]
    )

    # Execute process with HATEOAG integration
    executor = service.create_executor(process)
    await executor.run(context={"feature_name": "user-auth"})
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Set, Tuple
from pathlib import Path
import json
import re
import uuid


class StepType(Enum):
    """Type of process step."""
    ACTION = "action"
    DECISION = "decision"
    LOOP = "loop"
    PARALLEL = "parallel"
    CHECKPOINT = "checkpoint"
    WAIT = "wait"
    CALL = "call"  # Call another process


class VariableType(Enum):
    """Type of context variable."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ENUM = "enum"
    ANY = "any"


class NavigationType(Enum):
    """Type of navigation link."""
    NEXT = "next"
    SKIP = "skip"
    BACK = "back"
    BRANCH = "branch"
    ERROR = "error"
    END = "end"
    CALL = "call"
    LOOP = "loop"


@dataclass
class VariableDefinition:
    """Definition of a context variable."""
    name: str
    var_type: VariableType
    required: bool = True
    default: Any = None
    description: str = ""
    enum_values: List[str] = field(default_factory=list)
    validation_pattern: Optional[str] = None

    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate a value against this definition."""
        if value is None:
            if self.required and self.default is None:
                return False, f"Required variable '{self.name}' is missing"
            return True, None

        if self.var_type == VariableType.STRING:
            if not isinstance(value, str):
                return False, f"Variable '{self.name}' must be a string"
            if self.validation_pattern:
                if not re.match(self.validation_pattern, value):
                    return False, f"Variable '{self.name}' does not match pattern"

        elif self.var_type == VariableType.INTEGER:
            if not isinstance(value, int):
                return False, f"Variable '{self.name}' must be an integer"

        elif self.var_type == VariableType.FLOAT:
            if not isinstance(value, (int, float)):
                return False, f"Variable '{self.name}' must be a number"

        elif self.var_type == VariableType.BOOLEAN:
            if not isinstance(value, bool):
                return False, f"Variable '{self.name}' must be a boolean"

        elif self.var_type == VariableType.LIST:
            if not isinstance(value, list):
                return False, f"Variable '{self.name}' must be a list"

        elif self.var_type == VariableType.DICT:
            if not isinstance(value, dict):
                return False, f"Variable '{self.name}' must be a dictionary"

        elif self.var_type == VariableType.ENUM:
            if value not in self.enum_values:
                return False, f"Variable '{self.name}' must be one of {self.enum_values}"

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.var_type.value,
            "required": self.required,
            "default": self.default,
            "description": self.description,
            "enum_values": self.enum_values if self.var_type == VariableType.ENUM else None,
            "validation_pattern": self.validation_pattern
        }


@dataclass
class NavigationLink:
    """Link to another step or process."""
    nav_type: NavigationType
    target: str  # Step ID or process ID
    label: str
    condition: Optional[str] = None  # Condition expression
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.nav_type.value,
            "target": self.target,
            "label": self.label,
            "condition": self.condition,
            "description": self.description
        }

    def to_markdown(self) -> str:
        """Generate markdown link."""
        anchor = f"#step:{self.target}" if self.nav_type != NavigationType.CALL else self.target
        condition_text = f" when {self.condition}" if self.condition else ""
        return f"- [{self.nav_type.value.capitalize()}: {self.label}]({anchor}){condition_text}"


@dataclass
class ProcessAction:
    """An action within a step."""
    description: str
    tool: Optional[str] = None
    tool_args: Dict[str, Any] = field(default_factory=dict)
    output_variable: Optional[str] = None
    required: bool = True


@dataclass
class ProcessStep:
    """A step in the process."""
    id: str
    title: str
    step_type: StepType
    description: str
    actions: List[ProcessAction]
    navigation: List[NavigationLink]
    is_checkpoint: bool = False
    expected_output: Optional[str] = None
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    conditions: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.step_type.value,
            "description": self.description,
            "actions": [
                {
                    "description": a.description,
                    "tool": a.tool,
                    "tool_args": a.tool_args,
                    "output_variable": a.output_variable,
                    "required": a.required
                }
                for a in self.actions
            ],
            "navigation": [n.to_dict() for n in self.navigation],
            "is_checkpoint": self.is_checkpoint,
            "expected_output": self.expected_output,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "conditions": self.conditions,
            "metadata": self.metadata
        }

    def to_markdown(self) -> str:
        """Generate markdown for this step."""
        lines = [
            f"### [step:{self.id}] {self.title}"
        ]

        if self.is_checkpoint:
            lines.append("**Checkpoint**: true")
        lines.append("")

        if self.description:
            lines.append(self.description)
            lines.append("")

        if self.expected_output:
            lines.append(f"**Expected Output**: {self.expected_output}")
            lines.append("")

        if self.actions:
            lines.append("**Actions**:")
            for action in self.actions:
                tool_info = f" (tool: {action.tool})" if action.tool else ""
                lines.append(f"- {action.description}{tool_info}")
            lines.append("")

        if self.navigation:
            lines.append("**Navigation**:")
            for nav in self.navigation:
                lines.append(nav.to_markdown())
            lines.append("")

        return "\n".join(lines)


@dataclass
class ProcessMetadata:
    """Metadata for a process definition."""
    id: str
    name: str
    version: str
    description: str
    author: str
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    requires: List[str] = field(default_factory=list)  # Required processes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "category": self.category,
            "requires": self.requires
        }


@dataclass
class ProcessDefinition:
    """Complete process definition."""
    metadata: ProcessMetadata
    variables: List[VariableDefinition]
    steps: List[ProcessStep]
    entry_step: str
    exit_steps: List[str] = field(default_factory=list)

    def get_step(self, step_id: str) -> Optional[ProcessStep]:
        """Get step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_step_ids(self) -> List[str]:
        """Get all step IDs."""
        return [step.id for step in self.steps]

    def validate_navigation(self) -> List[str]:
        """Validate all navigation links point to valid targets."""
        errors = []
        step_ids = set(self.get_step_ids())

        for step in self.steps:
            for nav in step.navigation:
                if nav.nav_type == NavigationType.END:
                    continue
                if nav.nav_type == NavigationType.CALL:
                    continue  # External process, can't validate here
                if nav.target not in step_ids:
                    errors.append(f"Step '{step.id}' has invalid navigation target '{nav.target}'")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "variables": [v.to_dict() for v in self.variables],
            "steps": [s.to_dict() for s in self.steps],
            "entry_step": self.entry_step,
            "exit_steps": self.exit_steps
        }

    def to_markdown(self) -> str:
        """Generate markdown process file."""
        lines = [
            f"# Process: {self.metadata.name}",
            "",
            self.metadata.description if self.metadata.description else "",
            "",
            "## Metadata",
            "",
            f"- **ID**: {self.metadata.id}",
            f"- **Version**: {self.metadata.version}",
            f"- **Author**: {self.metadata.author}",
            f"- **Created**: {self.metadata.created_at.strftime('%Y-%m-%d')}",
            f"- **Updated**: {self.metadata.updated_at.strftime('%Y-%m-%d')}",
        ]

        if self.metadata.tags:
            lines.append(f"- **Tags**: {', '.join(self.metadata.tags)}")
        if self.metadata.category:
            lines.append(f"- **Category**: {self.metadata.category}")
        if self.metadata.requires:
            lines.append(f"- **Requires**: {', '.join(self.metadata.requires)}")

        lines.extend(["", "## Context Variables", ""])

        if self.variables:
            for var in self.variables:
                req = "(required)" if var.required else f"(default: {var.default})"
                type_info = var.var_type.value
                if var.var_type == VariableType.ENUM:
                    type_info = f"enum[{', '.join(var.enum_values)}]"
                lines.append(f"- `{var.name}`: {type_info} {req}")
                if var.description:
                    lines.append(f"  - {var.description}")
        else:
            lines.append("*No variables defined*")

        lines.extend(["", "## Steps", ""])

        for step in self.steps:
            lines.append(step.to_markdown())

        return "\n".join(lines)


class ProcessFileParser:
    """Parser for markdown process files."""

    STEP_PATTERN = re.compile(r"###\s*\[step:([^\]]+)\]\s*(.*)")
    METADATA_PATTERN = re.compile(r"-\s*\*\*([^*]+)\*\*:\s*(.*)")
    VARIABLE_PATTERN = re.compile(r"-\s*`([^`]+)`:\s*(\S+)\s*\(([^)]+)\)")
    NAV_PATTERN = re.compile(r"-\s*\[([^:]+):\s*([^\]]+)\]\(([^)]+)\)(?:\s*when\s*(.+))?")
    ACTION_PATTERN = re.compile(r"-\s*(.+?)(?:\s*\(tool:\s*([^)]+)\))?$")

    def parse(self, content: str) -> ProcessDefinition:
        """Parse markdown content into ProcessDefinition."""
        lines = content.split("\n")

        # Parse title
        title = ""
        for line in lines:
            if line.startswith("# Process:"):
                title = line.replace("# Process:", "").strip()
                break

        # Parse metadata section
        metadata = self._parse_metadata(lines, title)

        # Parse variables section
        variables = self._parse_variables(lines)

        # Parse steps
        steps = self._parse_steps(lines)

        # Determine entry and exit steps
        entry_step = steps[0].id if steps else ""
        exit_steps = [s.id for s in steps if any(n.nav_type == NavigationType.END for n in s.navigation)]

        return ProcessDefinition(
            metadata=metadata,
            variables=variables,
            steps=steps,
            entry_step=entry_step,
            exit_steps=exit_steps if exit_steps else [steps[-1].id] if steps else []
        )

    def _parse_metadata(self, lines: List[str], title: str) -> ProcessMetadata:
        """Parse metadata section."""
        in_metadata = False
        metadata_dict: Dict[str, str] = {}

        for line in lines:
            if "## Metadata" in line:
                in_metadata = True
                continue
            if in_metadata and line.startswith("## "):
                break
            if in_metadata:
                match = self.METADATA_PATTERN.match(line.strip())
                if match:
                    key = match.group(1).lower().replace(" ", "_")
                    value = match.group(2).strip()
                    metadata_dict[key] = value

        now = datetime.now()
        return ProcessMetadata(
            id=metadata_dict.get("id", str(uuid.uuid4())),
            name=title,
            version=metadata_dict.get("version", "1.0"),
            description=metadata_dict.get("description", ""),
            author=metadata_dict.get("author", "unknown"),
            created_at=datetime.fromisoformat(metadata_dict["created"]) if "created" in metadata_dict else now,
            updated_at=datetime.fromisoformat(metadata_dict["updated"]) if "updated" in metadata_dict else now,
            tags=metadata_dict.get("tags", "").split(", ") if metadata_dict.get("tags") else [],
            category=metadata_dict.get("category", "general"),
            requires=metadata_dict.get("requires", "").split(", ") if metadata_dict.get("requires") else []
        )

    def _parse_variables(self, lines: List[str]) -> List[VariableDefinition]:
        """Parse variables section."""
        in_variables = False
        variables = []

        for line in lines:
            if "## Context Variables" in line:
                in_variables = True
                continue
            if in_variables and line.startswith("## "):
                break
            if in_variables:
                match = self.VARIABLE_PATTERN.match(line.strip())
                if match:
                    name = match.group(1)
                    type_str = match.group(2)
                    modifier = match.group(3)

                    # Parse type
                    var_type = VariableType.STRING
                    enum_values = []

                    if type_str.startswith("enum["):
                        var_type = VariableType.ENUM
                        enum_str = type_str[5:-1]
                        enum_values = [v.strip() for v in enum_str.split(",")]
                    elif type_str in ["string", "integer", "float", "boolean", "list", "dict", "any"]:
                        var_type = VariableType(type_str)

                    # Parse modifier
                    required = "required" in modifier
                    default = None
                    if "default:" in modifier:
                        default_match = re.search(r"default:\s*(\S+)", modifier)
                        if default_match:
                            default = default_match.group(1)

                    variables.append(VariableDefinition(
                        name=name,
                        var_type=var_type,
                        required=required,
                        default=default,
                        enum_values=enum_values
                    ))

        return variables

    def _parse_steps(self, lines: List[str]) -> List[ProcessStep]:
        """Parse steps section."""
        steps = []
        current_step = None
        current_section = None

        for i, line in enumerate(lines):
            # Check for step header
            step_match = self.STEP_PATTERN.match(line)
            if step_match:
                if current_step:
                    steps.append(current_step)

                step_id = step_match.group(1)
                title = step_match.group(2).strip()

                current_step = ProcessStep(
                    id=step_id,
                    title=title,
                    step_type=StepType.ACTION,
                    description="",
                    actions=[],
                    navigation=[]
                )
                current_section = None
                continue

            if current_step is None:
                continue

            # Check for checkpoint marker
            if "**Checkpoint**: true" in line:
                current_step.is_checkpoint = True
                continue

            # Check for expected output
            if line.startswith("**Expected Output**:"):
                current_step.expected_output = line.replace("**Expected Output**:", "").strip()
                continue

            # Check for section headers
            if line.startswith("**Actions**:"):
                current_section = "actions"
                continue
            elif line.startswith("**Navigation**:"):
                current_section = "navigation"
                continue

            # Parse content based on section
            if current_section == "actions":
                action_match = self.ACTION_PATTERN.match(line.strip())
                if action_match:
                    current_step.actions.append(ProcessAction(
                        description=action_match.group(1).strip(),
                        tool=action_match.group(2).strip() if action_match.group(2) else None
                    ))

            elif current_section == "navigation":
                nav_match = self.NAV_PATTERN.match(line.strip())
                if nav_match:
                    nav_type_str = nav_match.group(1).lower()
                    label = nav_match.group(2).strip()
                    target = nav_match.group(3).strip()
                    condition = nav_match.group(4).strip() if nav_match.group(4) else None

                    # Parse target
                    if target.startswith("#step:"):
                        target = target[6:]

                    # Map navigation type
                    nav_type = NavigationType.NEXT
                    if nav_type_str == "skip":
                        nav_type = NavigationType.SKIP
                    elif nav_type_str == "back":
                        nav_type = NavigationType.BACK
                    elif nav_type_str == "branch":
                        nav_type = NavigationType.BRANCH
                    elif nav_type_str == "error":
                        nav_type = NavigationType.ERROR
                    elif nav_type_str == "end":
                        nav_type = NavigationType.END
                    elif nav_type_str == "call":
                        nav_type = NavigationType.CALL
                    elif nav_type_str == "loop":
                        nav_type = NavigationType.LOOP

                    current_step.navigation.append(NavigationLink(
                        nav_type=nav_type,
                        target=target,
                        label=label,
                        condition=condition
                    ))

            elif current_section is None and line.strip() and not line.startswith("**"):
                # Description content
                if current_step.description:
                    current_step.description += "\n" + line.strip()
                else:
                    current_step.description = line.strip()

        if current_step:
            steps.append(current_step)

        return steps


class ProcessFileService:
    """
    Service for managing process files.

    Provides:
    - Process file parsing and validation
    - Process generation from templates
    - Process registry and lookup
    - Integration with HATEOAG navigation
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(".agent_memory/processes")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.parser = ProcessFileParser()
        self.processes: Dict[str, ProcessDefinition] = {}
        self._load_processes()

    def _load_processes(self) -> None:
        """Load all processes from storage."""
        for file_path in self.storage_path.glob("*.md"):
            try:
                content = file_path.read_text()
                process = self.parser.parse(content)
                self.processes[process.metadata.id] = process
            except Exception:
                pass

        for file_path in self.storage_path.glob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                process = self._process_from_dict(data)
                self.processes[process.metadata.id] = process
            except Exception:
                pass

    def _process_from_dict(self, data: Dict[str, Any]) -> ProcessDefinition:
        """Reconstruct process from dictionary."""
        meta = data["metadata"]
        metadata = ProcessMetadata(
            id=meta["id"],
            name=meta["name"],
            version=meta["version"],
            description=meta.get("description", ""),
            author=meta["author"],
            created_at=datetime.fromisoformat(meta["created_at"]),
            updated_at=datetime.fromisoformat(meta["updated_at"]),
            tags=meta.get("tags", []),
            category=meta.get("category", "general"),
            requires=meta.get("requires", [])
        )

        variables = [
            VariableDefinition(
                name=v["name"],
                var_type=VariableType(v["type"]),
                required=v.get("required", True),
                default=v.get("default"),
                description=v.get("description", ""),
                enum_values=v.get("enum_values", []),
                validation_pattern=v.get("validation_pattern")
            )
            for v in data.get("variables", [])
        ]

        steps = []
        for s in data.get("steps", []):
            actions = [
                ProcessAction(
                    description=a["description"],
                    tool=a.get("tool"),
                    tool_args=a.get("tool_args", {}),
                    output_variable=a.get("output_variable"),
                    required=a.get("required", True)
                )
                for a in s.get("actions", [])
            ]

            navigation = [
                NavigationLink(
                    nav_type=NavigationType(n["type"]),
                    target=n["target"],
                    label=n["label"],
                    condition=n.get("condition"),
                    description=n.get("description", "")
                )
                for n in s.get("navigation", [])
            ]

            steps.append(ProcessStep(
                id=s["id"],
                title=s["title"],
                step_type=StepType(s.get("type", "action")),
                description=s.get("description", ""),
                actions=actions,
                navigation=navigation,
                is_checkpoint=s.get("is_checkpoint", False),
                expected_output=s.get("expected_output"),
                timeout_seconds=s.get("timeout_seconds"),
                retry_count=s.get("retry_count", 0),
                conditions=s.get("conditions", {}),
                metadata=s.get("metadata", {})
            ))

        return ProcessDefinition(
            metadata=metadata,
            variables=variables,
            steps=steps,
            entry_step=data.get("entry_step", steps[0].id if steps else ""),
            exit_steps=data.get("exit_steps", [])
        )

    def parse_file(self, file_path: str) -> ProcessDefinition:
        """Parse a process file from disk."""
        path = Path(file_path)
        content = path.read_text()

        if path.suffix == ".json":
            data = json.loads(content)
            return self._process_from_dict(data)

        return self.parser.parse(content)

    def parse_content(self, content: str) -> ProcessDefinition:
        """Parse process from string content."""
        return self.parser.parse(content)

    def validate(self, process: ProcessDefinition) -> List[str]:
        """
        Validate a process definition.

        Returns list of error messages.
        """
        errors = []

        # Validate metadata
        if not process.metadata.id:
            errors.append("Process ID is required")
        if not process.metadata.name:
            errors.append("Process name is required")

        # Validate steps
        if not process.steps:
            errors.append("Process must have at least one step")

        # Validate entry step exists
        if process.entry_step and not process.get_step(process.entry_step):
            errors.append(f"Entry step '{process.entry_step}' does not exist")

        # Validate exit steps exist
        for exit_step in process.exit_steps:
            if not process.get_step(exit_step):
                errors.append(f"Exit step '{exit_step}' does not exist")

        # Validate navigation
        errors.extend(process.validate_navigation())

        # Check for unreachable steps
        reachable = self._find_reachable_steps(process)
        all_steps = set(process.get_step_ids())
        unreachable = all_steps - reachable
        for step_id in unreachable:
            errors.append(f"Step '{step_id}' is unreachable from entry step")

        return errors

    def _find_reachable_steps(self, process: ProcessDefinition) -> Set[str]:
        """Find all steps reachable from entry step."""
        reachable = set()
        to_visit = [process.entry_step] if process.entry_step else []

        while to_visit:
            step_id = to_visit.pop()
            if step_id in reachable:
                continue
            reachable.add(step_id)

            step = process.get_step(step_id)
            if step:
                for nav in step.navigation:
                    if nav.nav_type not in [NavigationType.END, NavigationType.CALL]:
                        if nav.target not in reachable:
                            to_visit.append(nav.target)

        return reachable

    def save(self, process: ProcessDefinition, format: str = "markdown") -> Path:
        """
        Save a process definition.

        Args:
            process: Process to save
            format: "markdown" or "json"

        Returns:
            Path to saved file
        """
        if format == "json":
            file_path = self.storage_path / f"{process.metadata.id}.json"
            file_path.write_text(json.dumps(process.to_dict(), indent=2, default=str))
        else:
            file_path = self.storage_path / f"{process.metadata.id}.md"
            file_path.write_text(process.to_markdown())

        self.processes[process.metadata.id] = process
        return file_path

    def get(self, process_id: str) -> Optional[ProcessDefinition]:
        """Get process by ID."""
        return self.processes.get(process_id)

    def get_by_name(self, name: str) -> Optional[ProcessDefinition]:
        """Get process by name."""
        for process in self.processes.values():
            if process.metadata.name == name:
                return process
        return None

    def list_processes(self, category: Optional[str] = None) -> List[ProcessDefinition]:
        """List all processes, optionally filtered by category."""
        processes = list(self.processes.values())
        if category:
            processes = [p for p in processes if p.metadata.category == category]
        return processes

    def delete(self, process_id: str) -> bool:
        """Delete a process."""
        if process_id in self.processes:
            del self.processes[process_id]

            for ext in [".md", ".json"]:
                file_path = self.storage_path / f"{process_id}{ext}"
                if file_path.exists():
                    file_path.unlink()

            return True
        return False

    def generate(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        variables: Optional[List[Dict[str, Any]]] = None,
        description: str = "",
        author: str = "system",
        category: str = "general",
        tags: Optional[List[str]] = None
    ) -> ProcessDefinition:
        """
        Generate a new process definition.

        Args:
            name: Process name
            steps: List of step definitions
            variables: Optional list of variable definitions
            description: Process description
            author: Process author
            category: Process category
            tags: Optional tags

        Returns:
            Generated ProcessDefinition
        """
        now = datetime.now()

        # Parse variables
        parsed_variables = []
        for v in (variables or []):
            var_type = VariableType(v.get("type", "string"))
            parsed_variables.append(VariableDefinition(
                name=v["name"],
                var_type=var_type,
                required=v.get("required", True),
                default=v.get("default"),
                description=v.get("description", ""),
                enum_values=v.get("enum_values", []),
                validation_pattern=v.get("validation_pattern")
            ))

        # Parse steps
        parsed_steps = []
        for s in steps:
            actions = [
                ProcessAction(
                    description=a["description"],
                    tool=a.get("tool"),
                    tool_args=a.get("tool_args", {}),
                    output_variable=a.get("output_variable"),
                    required=a.get("required", True)
                )
                for a in s.get("actions", [])
            ]

            navigation = [
                NavigationLink(
                    nav_type=NavigationType(n.get("type", "next")),
                    target=n["target"],
                    label=n["label"],
                    condition=n.get("condition")
                )
                for n in s.get("navigation", [])
            ]

            parsed_steps.append(ProcessStep(
                id=s["id"],
                title=s["title"],
                step_type=StepType(s.get("type", "action")),
                description=s.get("description", ""),
                actions=actions,
                navigation=navigation,
                is_checkpoint=s.get("is_checkpoint", False),
                expected_output=s.get("expected_output"),
                timeout_seconds=s.get("timeout_seconds"),
                retry_count=s.get("retry_count", 0)
            ))

        # Create metadata
        metadata = ProcessMetadata(
            id=str(uuid.uuid4()),
            name=name,
            version="1.0",
            description=description,
            author=author,
            created_at=now,
            updated_at=now,
            tags=tags or [],
            category=category
        )

        # Determine entry and exit steps
        entry_step = parsed_steps[0].id if parsed_steps else ""
        exit_steps = [
            s.id for s in parsed_steps
            if any(n.nav_type == NavigationType.END for n in s.navigation)
        ]
        if not exit_steps and parsed_steps:
            exit_steps = [parsed_steps[-1].id]

        return ProcessDefinition(
            metadata=metadata,
            variables=parsed_variables,
            steps=parsed_steps,
            entry_step=entry_step,
            exit_steps=exit_steps
        )

    def create_from_template(self, template_name: str, **kwargs: Any) -> ProcessDefinition:
        """
        Create a process from a predefined template.

        Available templates:
        - feature_development
        - bug_fix
        - code_review
        - migration
        """
        templates = {
            "feature_development": self._template_feature_development,
            "bug_fix": self._template_bug_fix,
            "code_review": self._template_code_review,
            "migration": self._template_migration
        }

        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")

        return templates[template_name](**kwargs)

    def _template_feature_development(self, feature_name: str = "Feature", **kwargs: Any) -> ProcessDefinition:
        """Feature development process template."""
        return self.generate(
            name=f"Feature: {feature_name}",
            description="Standard feature development workflow",
            author="Felix",
            category="development",
            tags=["feature", "development"],
            variables=[
                {"name": "feature_name", "type": "string", "required": True},
                {"name": "priority", "type": "enum", "enum_values": ["low", "medium", "high"], "default": "medium"},
                {"name": "has_tests", "type": "boolean", "default": True}
            ],
            steps=[
                {
                    "id": "analyze",
                    "title": "Analyze Requirements",
                    "is_checkpoint": True,
                    "description": "Analyze feature requirements and create user stories",
                    "expected_output": "User stories in markdown format",
                    "actions": [
                        {"description": "Read requirements document"},
                        {"description": "Identify acceptance criteria"},
                        {"description": "Create user stories", "tool": "create_stories"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "design", "label": "Design", "condition": "analysis complete"},
                        {"type": "skip", "target": "implement", "label": "Implementation", "condition": "design exists"}
                    ]
                },
                {
                    "id": "design",
                    "title": "Design Solution",
                    "is_checkpoint": True,
                    "description": "Design the technical solution",
                    "actions": [
                        {"description": "Create architecture diagram"},
                        {"description": "Define API contracts"},
                        {"description": "Review with team"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "implement", "label": "Implementation"},
                        {"type": "back", "target": "analyze", "label": "Re-analyze", "condition": "requirements unclear"}
                    ]
                },
                {
                    "id": "implement",
                    "title": "Implement Feature",
                    "description": "Implement the feature code",
                    "actions": [
                        {"description": "Write implementation code", "tool": "write_code"},
                        {"description": "Write unit tests", "tool": "write_tests"},
                        {"description": "Run tests", "tool": "run_tests"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "review", "label": "Code Review", "condition": "tests pass"},
                        {"type": "loop", "target": "implement", "label": "Fix", "condition": "tests fail"}
                    ]
                },
                {
                    "id": "review",
                    "title": "Code Review",
                    "description": "Review code changes",
                    "actions": [
                        {"description": "Submit pull request", "tool": "create_pr"},
                        {"description": "Address feedback"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "done", "label": "Complete", "condition": "approved"},
                        {"type": "back", "target": "implement", "label": "Revise", "condition": "changes requested"}
                    ]
                },
                {
                    "id": "done",
                    "title": "Complete",
                    "description": "Feature implementation complete",
                    "actions": [
                        {"description": "Merge pull request"},
                        {"description": "Update documentation"}
                    ],
                    "navigation": [
                        {"type": "end", "target": "", "label": "Done"}
                    ]
                }
            ]
        )

    def _template_bug_fix(self, bug_id: str = "BUG-001", **kwargs: Any) -> ProcessDefinition:
        """Bug fix process template."""
        return self.generate(
            name=f"Bug Fix: {bug_id}",
            description="Standard bug investigation and fix workflow",
            author="Betty",
            category="bugfix",
            tags=["bug", "fix"],
            variables=[
                {"name": "bug_id", "type": "string", "required": True},
                {"name": "severity", "type": "enum", "enum_values": ["critical", "high", "medium", "low"]}
            ],
            steps=[
                {
                    "id": "investigate",
                    "title": "Investigate Bug",
                    "is_checkpoint": True,
                    "description": "Investigate and reproduce the bug",
                    "actions": [
                        {"description": "Read bug report"},
                        {"description": "Reproduce the issue"},
                        {"description": "Identify root cause"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "fix", "label": "Fix", "condition": "root cause found"},
                        {"type": "end", "target": "", "label": "Cannot Reproduce", "condition": "not reproducible"}
                    ]
                },
                {
                    "id": "fix",
                    "title": "Implement Fix",
                    "description": "Implement the bug fix",
                    "actions": [
                        {"description": "Write fix", "tool": "write_code"},
                        {"description": "Add regression test", "tool": "write_tests"},
                        {"description": "Verify fix"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "verify", "label": "Verify"},
                        {"type": "back", "target": "investigate", "label": "Re-investigate", "condition": "fix incomplete"}
                    ]
                },
                {
                    "id": "verify",
                    "title": "Verify Fix",
                    "description": "Verify the bug is fixed",
                    "actions": [
                        {"description": "Run regression tests", "tool": "run_tests"},
                        {"description": "Manual verification"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "done", "label": "Complete", "condition": "verified"},
                        {"type": "back", "target": "fix", "label": "Revise Fix", "condition": "still broken"}
                    ]
                },
                {
                    "id": "done",
                    "title": "Complete",
                    "description": "Bug fix complete",
                    "actions": [
                        {"description": "Close bug ticket"},
                        {"description": "Update release notes"}
                    ],
                    "navigation": [
                        {"type": "end", "target": "", "label": "Done"}
                    ]
                }
            ]
        )

    def _template_code_review(self, pr_id: str = "PR-001", **kwargs: Any) -> ProcessDefinition:
        """Code review process template."""
        return self.generate(
            name=f"Code Review: {pr_id}",
            description="Standard code review workflow",
            author="Quinn",
            category="review",
            tags=["review", "quality"],
            variables=[
                {"name": "pr_id", "type": "string", "required": True},
                {"name": "review_depth", "type": "enum", "enum_values": ["quick", "standard", "thorough"], "default": "standard"}
            ],
            steps=[
                {
                    "id": "overview",
                    "title": "Review Overview",
                    "description": "Get overview of changes",
                    "actions": [
                        {"description": "Read PR description"},
                        {"description": "Check file list"},
                        {"description": "Verify tests pass"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "code_review", "label": "Review Code"}
                    ]
                },
                {
                    "id": "code_review",
                    "title": "Code Review",
                    "is_checkpoint": True,
                    "description": "Review code changes in detail",
                    "actions": [
                        {"description": "Check code style"},
                        {"description": "Verify logic correctness"},
                        {"description": "Check security issues"},
                        {"description": "Add comments"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "decision", "label": "Make Decision"}
                    ]
                },
                {
                    "id": "decision",
                    "title": "Review Decision",
                    "description": "Make review decision",
                    "actions": [
                        {"description": "Summarize findings"},
                        {"description": "Submit review"}
                    ],
                    "navigation": [
                        {"type": "end", "target": "", "label": "Approve", "condition": "no issues"},
                        {"type": "end", "target": "", "label": "Request Changes", "condition": "issues found"}
                    ]
                }
            ]
        )

    def _template_migration(self, source: str = "legacy", target: str = "new", **kwargs: Any) -> ProcessDefinition:
        """Migration process template."""
        return self.generate(
            name=f"Migration: {source} to {target}",
            description="Standard migration workflow",
            author="Miguel",
            category="migration",
            tags=["migration"],
            variables=[
                {"name": "source_system", "type": "string", "required": True},
                {"name": "target_system", "type": "string", "required": True},
                {"name": "rollback_plan", "type": "boolean", "default": True}
            ],
            steps=[
                {
                    "id": "analyze",
                    "title": "Analyze Source",
                    "is_checkpoint": True,
                    "description": "Analyze source system",
                    "actions": [
                        {"description": "Inventory source assets"},
                        {"description": "Identify dependencies"},
                        {"description": "Document data schema"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "plan", "label": "Plan Migration"}
                    ]
                },
                {
                    "id": "plan",
                    "title": "Plan Migration",
                    "is_checkpoint": True,
                    "description": "Create migration plan",
                    "actions": [
                        {"description": "Design target architecture"},
                        {"description": "Create migration scripts"},
                        {"description": "Plan rollback procedure"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "test", "label": "Test Migration"}
                    ]
                },
                {
                    "id": "test",
                    "title": "Test Migration",
                    "description": "Test migration in staging",
                    "actions": [
                        {"description": "Run migration scripts"},
                        {"description": "Verify data integrity"},
                        {"description": "Performance testing"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "execute", "label": "Execute", "condition": "tests pass"},
                        {"type": "back", "target": "plan", "label": "Revise Plan", "condition": "issues found"}
                    ]
                },
                {
                    "id": "execute",
                    "title": "Execute Migration",
                    "is_checkpoint": True,
                    "description": "Execute production migration",
                    "actions": [
                        {"description": "Run production migration"},
                        {"description": "Monitor for errors"},
                        {"description": "Validate results"}
                    ],
                    "navigation": [
                        {"type": "next", "target": "done", "label": "Complete", "condition": "successful"},
                        {"type": "error", "target": "rollback", "label": "Rollback", "condition": "failed"}
                    ]
                },
                {
                    "id": "rollback",
                    "title": "Rollback",
                    "description": "Rollback migration",
                    "actions": [
                        {"description": "Execute rollback procedure"},
                        {"description": "Verify system state"},
                        {"description": "Document issues"}
                    ],
                    "navigation": [
                        {"type": "back", "target": "plan", "label": "Revise Plan"}
                    ]
                },
                {
                    "id": "done",
                    "title": "Complete",
                    "description": "Migration complete",
                    "actions": [
                        {"description": "Decommission source system"},
                        {"description": "Update documentation"},
                        {"description": "Final sign-off"}
                    ],
                    "navigation": [
                        {"type": "end", "target": "", "label": "Done"}
                    ]
                }
            ]
        )
