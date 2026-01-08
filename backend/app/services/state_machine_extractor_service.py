"""
State Machine Extractor Service - Fase 25: Business Logic Extraction

Extracts state machine patterns from legacy code and outputs to
Mermaid, XState, and other formats.

Detects patterns:
1. Enum-based states (Status = Pending | Approved | Rejected)
2. String-based states (strStatus = "Active")
3. State design pattern (classes per state)
4. Nested switch/select on status field
5. VB.NET Select Case patterns

Author: Claude Code (Week 138 - Fase 25)
Date: 2026-01-01
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class StatePatternType(str, Enum):
    """Type of state machine pattern detected"""
    ENUM_BASED = "enum_based"
    STRING_BASED = "string_based"
    CLASS_BASED = "class_based"
    SWITCH_CASE = "switch_case"
    IF_ELSE_CHAIN = "if_else_chain"
    STATUS_FIELD = "status_field"


class StateMachineOutputFormat(str, Enum):
    """Output formats for state machines"""
    MERMAID = "mermaid"
    XSTATE = "xstate"
    PLANTUML = "plantuml"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class ExtractedState:
    """A state extracted from code"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    original_value: str = ""  # Original enum/string value
    description: str = ""
    is_initial: bool = False
    is_final: bool = False
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedTransition:
    """A transition extracted from code"""
    id: str = field(default_factory=lambda: str(uuid4()))
    from_state: str = ""
    to_state: str = ""
    trigger: str = ""  # Event/action name
    guard: Optional[str] = None  # Condition
    action: Optional[str] = None  # Side effect
    description: str = ""
    source_file: Optional[str] = None
    source_line_start: Optional[int] = None
    source_line_end: Optional[int] = None
    source_code: Optional[str] = None
    confidence: float = 1.0


@dataclass
class ExtractedStateMachineStatistics:
    """Statistics for an extracted state machine"""
    total_states: int = 0
    total_transitions: int = 0
    has_initial_state: bool = False
    has_final_states: bool = False
    is_deterministic: bool = True
    reachable_states: int = 0
    unreachable_states: int = 0
    dead_end_states: int = 0


@dataclass
class ExtractedStateMachine:
    """A complete state machine extracted from code"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    pattern_type: StatePatternType = StatePatternType.STATUS_FIELD

    # Core structure
    states: List[ExtractedState] = field(default_factory=list)
    transitions: List[ExtractedTransition] = field(default_factory=list)
    initial_state: Optional[str] = None

    # Source tracking
    status_variable: Optional[str] = None
    source_file: Optional[str] = None
    source_class: Optional[str] = None
    source_line_start: Optional[int] = None
    source_line_end: Optional[int] = None

    # Metadata
    domain: Optional[str] = None
    entity: Optional[str] = None
    statistics: Optional[ExtractedStateMachineStatistics] = None
    confidence: float = 1.0
    extracted_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def get_state_names(self) -> List[str]:
        """Get list of state names"""
        return [s.name for s in self.states]

    def to_mermaid(self) -> str:
        """Generate Mermaid state diagram"""
        lines = ["stateDiagram-v2"]

        # Initial state
        if self.initial_state:
            lines.append(f"    [*] --> {self.initial_state}")

        # Transitions
        for trans in self.transitions:
            label = trans.trigger or ""
            if trans.guard:
                label += f" [{trans.guard}]"
            if trans.action:
                label += f" / {trans.action}"

            if label:
                lines.append(f"    {trans.from_state} --> {trans.to_state}: {label}")
            else:
                lines.append(f"    {trans.from_state} --> {trans.to_state}")

        # Final states
        for state in self.states:
            if state.is_final:
                lines.append(f"    {state.name} --> [*]")

        # Add state descriptions as notes
        for state in self.states:
            if state.description:
                lines.append(f"    note right of {state.name}: {state.description}")

        return "\n".join(lines)

    def to_xstate(self) -> Dict[str, Any]:
        """Generate XState v5 JSON format"""
        states_dict: Dict[str, Any] = {}

        for state in self.states:
            state_def: Dict[str, Any] = {}

            # Add metadata
            if state.description:
                state_def["meta"] = {"description": state.description}

            # Mark final states
            if state.is_final:
                state_def["type"] = "final"

            # Find transitions from this state
            state_transitions = [t for t in self.transitions if t.from_state == state.name]

            if state_transitions:
                on_dict: Dict[str, Any] = {}
                for trans in state_transitions:
                    trans_def: Dict[str, Any] = {"target": trans.to_state}

                    if trans.guard:
                        trans_def["guard"] = trans.guard

                    if trans.action:
                        trans_def["actions"] = [trans.action]

                    trigger = trans.trigger or "next"
                    if trigger in on_dict:
                        # Multiple transitions for same trigger
                        existing = on_dict[trigger]
                        if isinstance(existing, list):
                            existing.append(trans_def)
                        else:
                            on_dict[trigger] = [existing, trans_def]
                    else:
                        on_dict[trigger] = trans_def

                state_def["on"] = on_dict

            states_dict[state.name] = state_def

        return {
            "id": self.name,
            "initial": self.initial_state,
            "states": states_dict,
            "context": {},
            "meta": {
                "source_file": self.source_file,
                "pattern_type": self.pattern_type.value,
                "confidence": self.confidence
            }
        }

    def to_plantuml(self) -> str:
        """Generate PlantUML state diagram"""
        lines = ["@startuml", f"title {self.name}"]

        if self.initial_state:
            lines.append(f"[*] --> {self.initial_state}")

        for trans in self.transitions:
            label = trans.trigger or ""
            if trans.guard:
                label += f" [{trans.guard}]"

            if label:
                lines.append(f"{trans.from_state} --> {trans.to_state} : {label}")
            else:
                lines.append(f"{trans.from_state} --> {trans.to_state}")

        for state in self.states:
            if state.is_final:
                lines.append(f"{state.name} --> [*]")

        lines.append("@enduml")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "pattern_type": self.pattern_type.value,
            "states": [
                {
                    "id": s.id,
                    "name": s.name,
                    "original_value": s.original_value,
                    "description": s.description,
                    "is_initial": s.is_initial,
                    "is_final": s.is_final
                }
                for s in self.states
            ],
            "transitions": [
                {
                    "id": t.id,
                    "from_state": t.from_state,
                    "to_state": t.to_state,
                    "trigger": t.trigger,
                    "guard": t.guard,
                    "action": t.action,
                    "confidence": t.confidence
                }
                for t in self.transitions
            ],
            "initial_state": self.initial_state,
            "status_variable": self.status_variable,
            "source_file": self.source_file,
            "statistics": {
                "total_states": self.statistics.total_states,
                "total_transitions": self.statistics.total_transitions,
                "is_deterministic": self.statistics.is_deterministic
            } if self.statistics else None,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat()
        }


@dataclass
class StateMachineExtractionResult:
    """Result of state machine extraction"""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    project_id: Optional[str] = None

    machines: List[ExtractedStateMachine] = field(default_factory=list)

    total_files_scanned: int = 0
    files_with_machines: int = 0
    total_machines_extracted: int = 0
    average_confidence: float = 0.0

    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    started_at: datetime = field(default_factory=lambda: datetime.utcnow())
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0


class StateMachineExtractorService:
    """
    Service for extracting state machines from legacy code.

    Detects various state machine patterns in VB.NET, C#, Python,
    and JavaScript code.
    """

    # Patterns for status/state enum detection
    ENUM_PATTERNS = {
        "vbnet": [
            r"(?:Public\s+)?Enum\s+(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*(.*?)End\s+Enum",
            r"(?:Public\s+)?Enum\s+(\w+)\s*(.*?(?:Pending|Active|Completed|Approved|Rejected).*?)End\s+Enum",
        ],
        "csharp": [
            r"(?:public\s+)?enum\s+(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*\{(.*?)\}",
            r"(?:public\s+)?enum\s+(\w+)\s*\{(.*?(?:Pending|Active|Completed|Approved|Rejected).*?)\}",
        ],
        "python": [
            r"class\s+(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*\(\s*(?:str,\s*)?Enum\s*\)\s*:\s*(.*?)(?=\nclass|\n\n|\Z)",
        ],
        "javascript": [
            r"(?:const|let|var)\s+(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*=\s*\{(.*?)\}",
        ],
    }

    # Patterns for status field detection
    STATUS_FIELD_PATTERNS = {
        "vbnet": [
            r"(?:Private|Public|Protected)\s+(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s+As\s+(\w+)",
            r"(\w+)\.(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*=\s*[\"']?(\w+)[\"']?",
        ],
        "csharp": [
            r"(?:private|public|protected)\s+(\w+)\s+(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*\{",
            r"(\w+)\.(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*=\s*[\"']?(\w+)[\"']?",
        ],
        "python": [
            r"self\.(\w*status\w*|\w*state\w*)\s*=\s*[\"']?(\w+)[\"']?",
            r"(\w+)\.(\w*status\w*|\w*state\w*)\s*=\s*[\"']?(\w+)[\"']?",
        ],
    }

    # Patterns for transition detection
    TRANSITION_PATTERNS = {
        "vbnet": [
            # Select Case strStatus
            r"Select\s+Case\s+(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*(.*?)End\s+Select",
            # If status = X Then status = Y
            r"If\s+(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*=\s*[\"']?(\w+)[\"']?\s+Then\s*\n[^E]*?(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*=\s*[\"']?(\w+)[\"']?",
        ],
        "csharp": [
            # switch(status)
            r"switch\s*\(\s*(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*\)\s*\{(.*?)\}",
            # if (status == X) { status = Y; }
            r"if\s*\(\s*(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*==\s*[\"']?(\w+)[\"']?\s*\)\s*\{[^}]*?(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*=\s*[\"']?(\w+)[\"']?",
        ],
        "python": [
            # if self.status == X: self.status = Y
            r"if\s+self\.(\w*status\w*|\w*state\w*)\s*==\s*[\"']?(\w+)[\"']?\s*:\s*\n[^\n]*?self\.(\w*status\w*|\w*state\w*)\s*=\s*[\"']?(\w+)[\"']?",
            # match self.status:
            r"match\s+self\.(\w*status\w*|\w*state\w*)\s*:\s*(.*?)(?=\ndef|\nclass|\Z)",
        ],
    }

    # Common status field names
    COMMON_STATUS_FIELDS = [
        "status", "state", "phase", "stage", "workflow_status", "process_status",
        "strStatus", "intStatus", "objStatus", "Status", "State",
        "ProcessState", "WorkflowState", "OrderStatus", "TaskStatus",
    ]

    # Common initial states
    INITIAL_STATE_KEYWORDS = [
        "new", "initial", "created", "pending", "draft", "open", "start",
        "init", "begin", "queued", "backlog", "todo", "waiting"
    ]

    # Common final states
    FINAL_STATE_KEYWORDS = [
        "done", "completed", "finished", "closed", "final", "end",
        "cancelled", "canceled", "archived", "deleted", "terminated"
    ]

    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize the service"""
        self.db = db
        self._sessions: Dict[str, StateMachineExtractionResult] = {}

    async def create_session(
        self,
        project_id: Optional[str] = None,
        name: str = "State Machine Extraction"
    ) -> str:
        """Create a new extraction session"""
        session_id = str(uuid4())
        result = StateMachineExtractionResult(
            session_id=session_id,
            project_id=project_id,
            started_at=datetime.utcnow()
        )
        self._sessions[session_id] = result
        logger.info(f"Created state machine extraction session: {session_id}")
        return session_id

    async def get_session(self, session_id: str) -> Optional[StateMachineExtractionResult]:
        """Get an extraction session"""
        return self._sessions.get(session_id)

    async def extract_from_files(
        self,
        session_id: str,
        files: Dict[str, str],
        language: str = "vbnet"
    ) -> StateMachineExtractionResult:
        """
        Extract state machines from source files.

        Args:
            session_id: The extraction session ID
            files: Dict mapping file paths to file contents
            language: Programming language

        Returns:
            StateMachineExtractionResult with extracted machines
        """
        result = self._sessions.get(session_id)
        if not result:
            result = StateMachineExtractionResult(session_id=session_id)
            self._sessions[session_id] = result

        result.total_files_scanned = len(files)

        for file_path, content in files.items():
            try:
                machines = await self._extract_from_file(content, file_path, language)
                if machines:
                    result.files_with_machines += 1
                    result.machines.extend(machines)
                    result.total_machines_extracted += len(machines)
            except Exception as e:
                logger.error(f"Error extracting from {file_path}: {e}")
                result.errors.append(f"{file_path}: {str(e)}")

        # Calculate average confidence
        if result.machines:
            result.average_confidence = sum(
                m.confidence for m in result.machines
            ) / len(result.machines)

        result.completed_at = datetime.utcnow()
        result.duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()

        return result

    async def _extract_from_file(
        self,
        content: str,
        file_path: str,
        language: str
    ) -> List[ExtractedStateMachine]:
        """Extract state machines from a single file"""
        machines = []

        # 1. Find enum-based state definitions
        enum_machines = await self._extract_enum_based(content, file_path, language)
        machines.extend(enum_machines)

        # 2. Find switch/select case patterns
        switch_machines = await self._extract_switch_based(content, file_path, language)
        machines.extend(switch_machines)

        # 3. Find status field assignments
        field_machines = await self._extract_field_based(content, file_path, language)
        machines.extend(field_machines)

        # Deduplicate machines with similar names
        machines = self._deduplicate_machines(machines)

        return machines

    async def _extract_enum_based(
        self,
        content: str,
        file_path: str,
        language: str
    ) -> List[ExtractedStateMachine]:
        """Extract state machines from enum definitions"""
        machines = []
        patterns = self.ENUM_PATTERNS.get(language, [])

        for pattern in patterns:
            try:
                for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                    enum_name = match.group(1)
                    enum_body = match.group(2)

                    states = self._parse_enum_values(enum_body, language)
                    if len(states) < 2:
                        continue

                    machine = ExtractedStateMachine(
                        name=enum_name,
                        description=f"State machine from enum {enum_name}",
                        pattern_type=StatePatternType.ENUM_BASED,
                        source_file=file_path,
                        source_line_start=content[:match.start()].count('\n') + 1,
                        source_line_end=content[:match.end()].count('\n') + 1,
                        confidence=0.9
                    )

                    # Create states
                    for i, state_name in enumerate(states):
                        state = ExtractedState(
                            name=state_name,
                            original_value=state_name,
                            is_initial=self._is_initial_state(state_name),
                            is_final=self._is_final_state(state_name),
                            source_file=file_path
                        )
                        if state.is_initial:
                            machine.initial_state = state_name
                        machine.states.append(state)

                    # Look for transitions in the file
                    transitions = await self._find_transitions_for_states(
                        content, file_path, enum_name, [s.name for s in machine.states], language
                    )
                    machine.transitions = transitions

                    machine.statistics = self._calculate_statistics(machine)
                    machines.append(machine)

            except re.error as e:
                logger.warning(f"Regex error: {e}")

        return machines

    async def _extract_switch_based(
        self,
        content: str,
        file_path: str,
        language: str
    ) -> List[ExtractedStateMachine]:
        """Extract state machines from switch/select case statements"""
        machines = []
        patterns = self.TRANSITION_PATTERNS.get(language, [])

        if not patterns:
            return machines

        try:
            # Look for Select Case / switch on status fields
            switch_pattern = patterns[0] if patterns else None
            if not switch_pattern:
                return machines

            for match in re.finditer(switch_pattern, content, re.DOTALL | re.IGNORECASE):
                status_var = match.group(1)
                switch_body = match.group(2)

                # Extract cases as states and transitions
                states, transitions = self._parse_switch_cases(
                    switch_body, status_var, file_path, language
                )

                if len(states) < 2:
                    continue

                machine = ExtractedStateMachine(
                    name=f"{status_var}_workflow",
                    description=f"State machine from switch on {status_var}",
                    pattern_type=StatePatternType.SWITCH_CASE,
                    status_variable=status_var,
                    source_file=file_path,
                    source_line_start=content[:match.start()].count('\n') + 1,
                    source_line_end=content[:match.end()].count('\n') + 1,
                    confidence=0.85
                )

                machine.states = states
                machine.transitions = transitions

                # Try to identify initial state
                for state in states:
                    if state.is_initial:
                        machine.initial_state = state.name
                        break

                machine.statistics = self._calculate_statistics(machine)
                machines.append(machine)

        except re.error as e:
            logger.warning(f"Regex error: {e}")

        return machines

    async def _extract_field_based(
        self,
        content: str,
        file_path: str,
        language: str
    ) -> List[ExtractedStateMachine]:
        """Extract state machines from status field assignments"""
        machines = []
        patterns = self.STATUS_FIELD_PATTERNS.get(language, [])

        # Find all status field assignments
        assignments: Dict[str, Set[str]] = {}  # field -> set of values

        for pattern in patterns:
            try:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    groups = match.groups()
                    if len(groups) >= 3:
                        field_name = groups[1] if len(groups) > 1 else groups[0]
                        value = groups[2] if len(groups) > 2 else groups[1]

                        if field_name not in assignments:
                            assignments[field_name] = set()
                        assignments[field_name].add(value)
            except re.error:
                continue

        # Create machines for fields with multiple values
        for field_name, values in assignments.items():
            if len(values) < 2:
                continue

            machine = ExtractedStateMachine(
                name=f"{field_name}_workflow",
                description=f"State machine inferred from {field_name} assignments",
                pattern_type=StatePatternType.STATUS_FIELD,
                status_variable=field_name,
                source_file=file_path,
                confidence=0.7
            )

            for value in values:
                state = ExtractedState(
                    name=value,
                    original_value=value,
                    is_initial=self._is_initial_state(value),
                    is_final=self._is_final_state(value),
                    source_file=file_path
                )
                if state.is_initial and not machine.initial_state:
                    machine.initial_state = value
                machine.states.append(state)

            machine.statistics = self._calculate_statistics(machine)
            machines.append(machine)

        return machines

    def _parse_enum_values(self, enum_body: str, language: str) -> List[str]:
        """Parse enum values from enum body"""
        values = []

        if language == "vbnet":
            # VB.NET: Value = 0 or just Value
            for match in re.finditer(r"^\s*(\w+)\s*(?:=\s*\d+)?", enum_body, re.MULTILINE):
                value = match.group(1).strip()
                if value and not value.startswith("'"):
                    values.append(value)
        elif language == "csharp":
            # C#: Value = 0, or just Value
            for match in re.finditer(r"(\w+)\s*(?:=\s*\d+)?", enum_body):
                value = match.group(1).strip()
                if value:
                    values.append(value)
        elif language == "python":
            # Python: VALUE = "value" or VALUE = auto()
            for match in re.finditer(r"^\s*(\w+)\s*=", enum_body, re.MULTILINE):
                value = match.group(1).strip()
                if value and not value.startswith("#"):
                    values.append(value)
        elif language == "javascript":
            # JS: KEY: "value" or KEY: 0
            for match in re.finditer(r"(\w+)\s*:", enum_body):
                value = match.group(1).strip()
                if value:
                    values.append(value)

        return values

    def _parse_switch_cases(
        self,
        switch_body: str,
        status_var: str,
        file_path: str,
        language: str
    ) -> Tuple[List[ExtractedState], List[ExtractedTransition]]:
        """Parse switch/select case body into states and transitions"""
        states: List[ExtractedState] = []
        transitions: List[ExtractedTransition] = []
        seen_states: Set[str] = set()

        if language == "vbnet":
            case_pattern = r"Case\s+[\"']?(\w+)[\"']?\s*(.*?)(?=Case|End\s+Select)"
            assign_pattern = r"(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*=\s*[\"']?(\w+)[\"']?"
        else:  # csharp, javascript
            case_pattern = r"case\s+[\"']?(\w+)[\"']?\s*:(.*?)(?=case|default|break|\})"
            assign_pattern = r"(\w*[Ss]tatus\w*|\w*[Ss]tate\w*)\s*=\s*[\"']?(\w+)[\"']?"

        for case_match in re.finditer(case_pattern, switch_body, re.DOTALL | re.IGNORECASE):
            from_state = case_match.group(1)
            case_body = case_match.group(2)

            if from_state not in seen_states:
                seen_states.add(from_state)
                states.append(ExtractedState(
                    name=from_state,
                    original_value=from_state,
                    is_initial=self._is_initial_state(from_state),
                    is_final=self._is_final_state(from_state),
                    source_file=file_path
                ))

            # Find assignments in case body
            for assign_match in re.finditer(assign_pattern, case_body, re.IGNORECASE):
                to_state = assign_match.group(2)

                if to_state not in seen_states:
                    seen_states.add(to_state)
                    states.append(ExtractedState(
                        name=to_state,
                        original_value=to_state,
                        is_initial=self._is_initial_state(to_state),
                        is_final=self._is_final_state(to_state),
                        source_file=file_path
                    ))

                transitions.append(ExtractedTransition(
                    from_state=from_state,
                    to_state=to_state,
                    trigger=f"on_{from_state.lower()}_to_{to_state.lower()}",
                    source_file=file_path,
                    source_code=case_body.strip()[:100],
                    confidence=0.85
                ))

        return states, transitions

    async def _find_transitions_for_states(
        self,
        content: str,
        file_path: str,
        enum_name: str,
        state_names: List[str],
        language: str
    ) -> List[ExtractedTransition]:
        """Find transitions between known states in file content"""
        transitions = []

        # Build pattern to find state assignments
        state_pattern = "|".join(re.escape(s) for s in state_names)

        if language == "vbnet":
            # Pattern: status = State1 after checking status = State2
            assign_patterns = [
                rf"If\s+\w+\s*=\s*({enum_name}\.)?({state_pattern})\s+Then[^E]*?(\w+)\s*=\s*({enum_name}\.)?({state_pattern})",
            ]
        else:
            assign_patterns = [
                rf"if\s*\(\s*\w+\s*==\s*({enum_name}\.)?({state_pattern})\s*\)[^}}]*?(\w+)\s*=\s*({enum_name}\.)?({state_pattern})",
            ]

        for pattern in assign_patterns:
            try:
                for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                    groups = match.groups()
                    from_state = groups[1] if len(groups) > 1 else None
                    to_state = groups[-1] if groups else None

                    if from_state and to_state and from_state != to_state:
                        transitions.append(ExtractedTransition(
                            from_state=from_state,
                            to_state=to_state,
                            trigger=f"transition_{from_state}_to_{to_state}",
                            source_file=file_path,
                            source_line_start=content[:match.start()].count('\n') + 1,
                            source_code=match.group(0)[:100],
                            confidence=0.8
                        ))
            except re.error:
                continue

        return transitions

    def _is_initial_state(self, state_name: str) -> bool:
        """Check if state name suggests initial state"""
        return any(
            kw in state_name.lower()
            for kw in self.INITIAL_STATE_KEYWORDS
        )

    def _is_final_state(self, state_name: str) -> bool:
        """Check if state name suggests final state"""
        return any(
            kw in state_name.lower()
            for kw in self.FINAL_STATE_KEYWORDS
        )

    def _calculate_statistics(
        self,
        machine: ExtractedStateMachine
    ) -> ExtractedStateMachineStatistics:
        """Calculate statistics for a state machine"""
        stats = ExtractedStateMachineStatistics(
            total_states=len(machine.states),
            total_transitions=len(machine.transitions),
            has_initial_state=machine.initial_state is not None,
            has_final_states=any(s.is_final for s in machine.states)
        )

        # Check determinism (no duplicate from_state + trigger)
        seen_triggers: Set[Tuple[str, str]] = set()
        for trans in machine.transitions:
            key = (trans.from_state, trans.trigger)
            if key in seen_triggers:
                stats.is_deterministic = False
                break
            seen_triggers.add(key)

        # Calculate reachability
        if machine.initial_state:
            reachable = self._find_reachable_states(machine)
            stats.reachable_states = len(reachable)
            stats.unreachable_states = stats.total_states - len(reachable)

        # Find dead ends
        states_with_outgoing = {t.from_state for t in machine.transitions}
        final_states = {s.name for s in machine.states if s.is_final}
        dead_ends = set(s.name for s in machine.states) - states_with_outgoing - final_states
        stats.dead_end_states = len(dead_ends)

        return stats

    def _find_reachable_states(self, machine: ExtractedStateMachine) -> Set[str]:
        """Find all states reachable from initial state"""
        if not machine.initial_state:
            return set()

        reachable: Set[str] = {machine.initial_state}
        queue = [machine.initial_state]

        while queue:
            current = queue.pop(0)
            for trans in machine.transitions:
                if trans.from_state == current and trans.to_state not in reachable:
                    reachable.add(trans.to_state)
                    queue.append(trans.to_state)

        return reachable

    def _deduplicate_machines(
        self,
        machines: List[ExtractedStateMachine]
    ) -> List[ExtractedStateMachine]:
        """Remove duplicate machines with similar states"""
        if len(machines) <= 1:
            return machines

        unique: List[ExtractedStateMachine] = []
        seen_state_sets: List[Set[str]] = []

        for machine in machines:
            state_set = set(s.name for s in machine.states)

            # Check for overlap with existing machines
            is_duplicate = False
            for existing_set in seen_state_sets:
                overlap = len(state_set & existing_set) / max(len(state_set), len(existing_set), 1)
                if overlap > 0.8:  # 80% overlap threshold
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(machine)
                seen_state_sets.append(state_set)

        return unique

    # Export methods

    async def export_to_format(
        self,
        machine: ExtractedStateMachine,
        format: StateMachineOutputFormat
    ) -> str:
        """Export a state machine to specified format"""
        if format == StateMachineOutputFormat.MERMAID:
            return machine.to_mermaid()
        elif format == StateMachineOutputFormat.XSTATE:
            import json
            return json.dumps(machine.to_xstate(), indent=2)
        elif format == StateMachineOutputFormat.PLANTUML:
            return machine.to_plantuml()
        elif format == StateMachineOutputFormat.JSON:
            import json
            return json.dumps(machine.to_dict(), indent=2)
        elif format == StateMachineOutputFormat.MARKDOWN:
            return await self._export_to_markdown(machine)
        else:
            raise ValueError(f"Unknown format: {format}")

    async def _export_to_markdown(self, machine: ExtractedStateMachine) -> str:
        """Export to Markdown documentation"""
        lines = [
            f"# State Machine: {machine.name}",
            "",
            f"**Description:** {machine.description}",
            f"**Pattern Type:** {machine.pattern_type.value}",
            f"**Source:** {machine.source_file}",
            f"**Confidence:** {machine.confidence:.0%}",
            "",
            "## States",
            "",
            "| State | Initial | Final | Description |",
            "|-------|---------|-------|-------------|",
        ]

        for state in machine.states:
            initial = "✓" if state.is_initial else ""
            final = "✓" if state.is_final else ""
            lines.append(f"| {state.name} | {initial} | {final} | {state.description} |")

        lines.extend([
            "",
            "## Transitions",
            "",
            "| From | To | Trigger | Guard |",
            "|------|-----|---------|-------|",
        ])

        for trans in machine.transitions:
            guard = trans.guard or "-"
            lines.append(f"| {trans.from_state} | {trans.to_state} | {trans.trigger} | {guard} |")

        lines.extend([
            "",
            "## Diagram (Mermaid)",
            "",
            "```mermaid",
            machine.to_mermaid(),
            "```"
        ])

        return "\n".join(lines)

    async def export_session(
        self,
        session_id: str,
        format: StateMachineOutputFormat = StateMachineOutputFormat.MERMAID
    ) -> str:
        """Export all machines from a session"""
        result = self._sessions.get(session_id)
        if not result:
            raise ValueError(f"Session {session_id} not found")

        outputs = []
        for machine in result.machines:
            output = await self.export_to_format(machine, format)
            outputs.append(output)

        separator = "\n\n---\n\n"
        return separator.join(outputs)
