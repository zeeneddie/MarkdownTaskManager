"""
MP-M-4: Instruction Sandwich Service

Counter recency bias with structured instruction repetition.
Ensures critical instructions are reinforced throughout conversations.

Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- Sandwich pattern: instructions at start and end
- Periodic reminders during conversation
- Adaptive repetition based on compliance
- Instruction compliance tracking

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class RepetitionStrategy(Enum):
    """Strategy for repeating instructions."""
    SANDWICH = "sandwich"        # Start + End
    PERIODIC = "periodic"        # Every N messages
    ADAPTIVE = "adaptive"        # Based on compliance
    ESCALATING = "escalating"    # Increase frequency on violations
    DECAY = "decay"              # Decrease over time if compliant


class InstructionPriority(Enum):
    """Priority level of instructions."""
    CRITICAL = "critical"    # Must always be followed
    HIGH = "high"           # Important, remind frequently
    MEDIUM = "medium"       # Standard reminders
    LOW = "low"             # Occasional reminders


class ReminderPosition(Enum):
    """Position for reminder insertion."""
    START = "start"          # At the beginning
    MIDDLE = "middle"        # In the middle of response
    END = "end"             # At the end
    CONTEXT = "context"      # In context window


@dataclass
class Instruction:
    """A single instruction to be tracked."""
    id: UUID
    index: int               # Position in the set
    content: str             # The instruction text
    priority: InstructionPriority
    short_form: Optional[str] = None  # Brief reminder form
    keyword: Optional[str] = None     # Trigger keyword
    compliance_count: int = 0
    violation_count: int = 0


@dataclass
class Reminder:
    """Configuration for when to show reminders."""
    instruction_index: int
    position: ReminderPosition
    frequency: int           # Every N messages
    last_shown: Optional[datetime] = None
    show_count: int = 0


@dataclass
class InstructionSet:
    """A set of related instructions."""
    id: UUID
    name: str
    description: str
    instructions: List[Instruction]
    reminders: List[Reminder]
    strategy: RepetitionStrategy
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SandwichContext:
    """Context for instruction sandwich in a session."""
    session_id: UUID
    instruction_set_id: UUID
    message_count: int
    compliance_score: float
    pending_reminders: List[str]
    last_reminder_at: Optional[datetime]
    violation_streak: int
    created_at: datetime


@dataclass
class ComplianceEvent:
    """Record of instruction compliance."""
    instruction_id: UUID
    instruction_index: int
    complied: bool
    timestamp: datetime
    context: Optional[str] = None


class InstructionSandwichService:
    """
    Service for managing instruction repetition and reminders.

    The "Instruction Sandwich" pattern places critical instructions
    at both the start and end of prompts to counter recency bias,
    and uses periodic reminders to maintain focus.
    """

    # Default reminder frequencies by priority
    DEFAULT_FREQUENCIES = {
        InstructionPriority.CRITICAL: 3,   # Every 3 messages
        InstructionPriority.HIGH: 5,       # Every 5 messages
        InstructionPriority.MEDIUM: 10,    # Every 10 messages
        InstructionPriority.LOW: 20,       # Every 20 messages
    }

    def __init__(self):
        self._instruction_sets: Dict[UUID, InstructionSet] = {}
        self._contexts: Dict[UUID, SandwichContext] = {}  # session_id -> context
        self._compliance_history: Dict[UUID, List[ComplianceEvent]] = {}  # set_id -> events

    def create_instruction_set(
        self,
        name: str,
        instructions: List[str],
        strategy: RepetitionStrategy = RepetitionStrategy.SANDWICH,
        description: str = "",
        priorities: Optional[List[InstructionPriority]] = None,
        short_forms: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> InstructionSet:
        """
        Create a new instruction set.

        Args:
            name: Name for the instruction set
            instructions: List of instruction texts
            strategy: Repetition strategy to use
            description: Description of the instruction set
            priorities: Priority for each instruction (defaults to MEDIUM)
            short_forms: Short reminder forms for each instruction
            keywords: Trigger keywords for each instruction
            metadata: Additional metadata

        Returns:
            Created InstructionSet
        """
        instruction_objs = []
        reminders = []

        for i, text in enumerate(instructions):
            priority = priorities[i] if priorities and i < len(priorities) else InstructionPriority.MEDIUM
            short_form = short_forms[i] if short_forms and i < len(short_forms) else None
            keyword = keywords[i] if keywords and i < len(keywords) else None

            instruction = Instruction(
                id=uuid4(),
                index=i,
                content=text,
                priority=priority,
                short_form=short_form,
                keyword=keyword
            )
            instruction_objs.append(instruction)

            # Create default reminders based on priority
            frequency = self.DEFAULT_FREQUENCIES.get(priority, 10)
            reminders.append(Reminder(
                instruction_index=i,
                position=ReminderPosition.END,
                frequency=frequency
            ))

        instruction_set = InstructionSet(
            id=uuid4(),
            name=name,
            description=description,
            instructions=instruction_objs,
            reminders=reminders,
            strategy=strategy,
            created_at=datetime.now(timezone.utc),
            metadata=metadata or {}
        )

        self._instruction_sets[instruction_set.id] = instruction_set
        self._compliance_history[instruction_set.id] = []

        logger.info(f"Created instruction set '{name}' with {len(instructions)} instructions")

        return instruction_set

    def start_session(
        self,
        session_id: UUID,
        instruction_set_id: UUID
    ) -> SandwichContext:
        """
        Start a new session with instruction tracking.

        Args:
            session_id: Session identifier
            instruction_set_id: Instruction set to use

        Returns:
            SandwichContext for the session
        """
        if instruction_set_id not in self._instruction_sets:
            raise ValueError(f"Instruction set {instruction_set_id} not found")

        context = SandwichContext(
            session_id=session_id,
            instruction_set_id=instruction_set_id,
            message_count=0,
            compliance_score=100.0,
            pending_reminders=[],
            last_reminder_at=None,
            violation_streak=0,
            created_at=datetime.now(timezone.utc)
        )

        self._contexts[session_id] = context

        logger.info(f"Started instruction session {session_id}")

        return context

    def get_preamble(self, set_id: UUID) -> str:
        """
        Get instructions for the start of a conversation.

        Args:
            set_id: Instruction set ID

        Returns:
            Formatted preamble with instructions
        """
        instruction_set = self._instruction_sets.get(set_id)
        if not instruction_set:
            raise ValueError(f"Instruction set {set_id} not found")

        lines = ["## Ground Rules", ""]

        for instruction in instruction_set.instructions:
            priority_marker = {
                InstructionPriority.CRITICAL: "🔴",
                InstructionPriority.HIGH: "🟠",
                InstructionPriority.MEDIUM: "🟡",
                InstructionPriority.LOW: "⚪",
            }.get(instruction.priority, "")

            lines.append(f"{priority_marker} {instruction.index + 1}. {instruction.content}")

        lines.append("")
        lines.append("---")

        return "\n".join(lines)

    def get_reminders(
        self,
        session_id: UUID,
        message_count: Optional[int] = None
    ) -> List[str]:
        """
        Get reminders that should be shown at this point.

        Args:
            session_id: Session ID
            message_count: Current message count (auto-increments if not provided)

        Returns:
            List of reminder texts
        """
        context = self._contexts.get(session_id)
        if not context:
            return []

        instruction_set = self._instruction_sets.get(context.instruction_set_id)
        if not instruction_set:
            return []

        if message_count is not None:
            context.message_count = message_count
        else:
            context.message_count += 1

        reminders = []

        for reminder in instruction_set.reminders:
            # Check if this reminder is due
            if context.message_count % reminder.frequency == 0:
                instruction = instruction_set.instructions[reminder.instruction_index]

                # Use short form if available
                text = instruction.short_form or instruction.content
                reminders.append(text)

                reminder.show_count += 1
                reminder.last_shown = datetime.now(timezone.utc)

        # Adaptive: add more reminders if compliance is low
        if instruction_set.strategy == RepetitionStrategy.ADAPTIVE:
            if context.compliance_score < 70:
                # Add critical instruction reminders
                for instruction in instruction_set.instructions:
                    if instruction.priority == InstructionPriority.CRITICAL:
                        reminder_text = f"⚠️ Remember: {instruction.short_form or instruction.content}"
                        if reminder_text not in reminders:
                            reminders.append(reminder_text)

        # Escalating: increase frequency on violations
        if instruction_set.strategy == RepetitionStrategy.ESCALATING:
            if context.violation_streak > 2:
                for instruction in instruction_set.instructions:
                    if instruction.violation_count > instruction.compliance_count:
                        reminder_text = f"📍 {instruction.short_form or instruction.content}"
                        if reminder_text not in reminders:
                            reminders.append(reminder_text)

        context.pending_reminders = reminders
        context.last_reminder_at = datetime.now(timezone.utc) if reminders else context.last_reminder_at

        return reminders

    def get_closing(self, set_id: UUID) -> str:
        """
        Get instructions for the end of a conversation/response.

        Args:
            set_id: Instruction set ID

        Returns:
            Formatted closing with key reminders
        """
        instruction_set = self._instruction_sets.get(set_id)
        if not instruction_set:
            raise ValueError(f"Instruction set {set_id} not found")

        # Get critical and high priority instructions for closing
        critical = [i for i in instruction_set.instructions
                   if i.priority in (InstructionPriority.CRITICAL, InstructionPriority.HIGH)]

        if not critical:
            return ""

        lines = ["---", "## Key Reminders", ""]

        for instruction in critical:
            text = instruction.short_form or instruction.content
            lines.append(f"- {text}")

        return "\n".join(lines)

    def track_compliance(
        self,
        session_id: UUID,
        instruction_index: int,
        complied: bool,
        context: Optional[str] = None
    ) -> float:
        """
        Track compliance with an instruction.

        Args:
            session_id: Session ID
            instruction_index: Index of the instruction
            complied: Whether the instruction was followed
            context: Optional context about the compliance check

        Returns:
            Updated compliance score
        """
        session_context = self._contexts.get(session_id)
        if not session_context:
            raise ValueError(f"Session {session_id} not found")

        instruction_set = self._instruction_sets.get(session_context.instruction_set_id)
        if not instruction_set:
            raise ValueError("Instruction set not found")

        if instruction_index >= len(instruction_set.instructions):
            raise ValueError(f"Invalid instruction index: {instruction_index}")

        instruction = instruction_set.instructions[instruction_index]

        # Update instruction counts
        if complied:
            instruction.compliance_count += 1
            session_context.violation_streak = 0
        else:
            instruction.violation_count += 1
            session_context.violation_streak += 1

        # Record event
        event = ComplianceEvent(
            instruction_id=instruction.id,
            instruction_index=instruction_index,
            complied=complied,
            timestamp=datetime.now(timezone.utc),
            context=context
        )
        self._compliance_history[instruction_set.id].append(event)

        # Recalculate compliance score
        session_context.compliance_score = self._calculate_compliance_score(instruction_set)

        logger.debug(f"Tracked compliance for instruction {instruction_index}: {complied}, score: {session_context.compliance_score:.1f}")

        return session_context.compliance_score

    def get_sandwich_context(self, session_id: UUID) -> Optional[SandwichContext]:
        """Get the current context for a session."""
        return self._contexts.get(session_id)

    def get_instruction_set(self, set_id: UUID) -> Optional[InstructionSet]:
        """Get an instruction set by ID."""
        return self._instruction_sets.get(set_id)

    def get_compliance_report(self, set_id: UUID) -> Dict[str, Any]:
        """
        Get a compliance report for an instruction set.

        Args:
            set_id: Instruction set ID

        Returns:
            Report with compliance statistics
        """
        instruction_set = self._instruction_sets.get(set_id)
        if not instruction_set:
            raise ValueError(f"Instruction set {set_id} not found")

        history = self._compliance_history.get(set_id, [])

        total_checks = len(history)
        compliant = len([e for e in history if e.complied])

        instruction_stats = []
        for instruction in instruction_set.instructions:
            total = instruction.compliance_count + instruction.violation_count
            rate = (instruction.compliance_count / total * 100) if total > 0 else 100.0
            instruction_stats.append({
                "index": instruction.index,
                "content": instruction.content[:50] + "..." if len(instruction.content) > 50 else instruction.content,
                "priority": instruction.priority.value,
                "compliance_count": instruction.compliance_count,
                "violation_count": instruction.violation_count,
                "compliance_rate": rate
            })

        return {
            "set_id": str(set_id),
            "set_name": instruction_set.name,
            "total_checks": total_checks,
            "compliant_count": compliant,
            "overall_compliance_rate": (compliant / total_checks * 100) if total_checks > 0 else 100.0,
            "instruction_stats": instruction_stats,
            "strategy": instruction_set.strategy.value
        }

    def update_reminder_frequency(
        self,
        set_id: UUID,
        instruction_index: int,
        frequency: int
    ) -> Reminder:
        """
        Update the reminder frequency for an instruction.

        Args:
            set_id: Instruction set ID
            instruction_index: Index of the instruction
            frequency: New frequency (every N messages)

        Returns:
            Updated Reminder
        """
        instruction_set = self._instruction_sets.get(set_id)
        if not instruction_set:
            raise ValueError(f"Instruction set {set_id} not found")

        for reminder in instruction_set.reminders:
            if reminder.instruction_index == instruction_index:
                reminder.frequency = frequency
                logger.info(f"Updated reminder frequency for instruction {instruction_index} to {frequency}")
                return reminder

        raise ValueError(f"Reminder for instruction {instruction_index} not found")

    def add_instruction(
        self,
        set_id: UUID,
        content: str,
        priority: InstructionPriority = InstructionPriority.MEDIUM,
        short_form: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Instruction:
        """
        Add a new instruction to an existing set.

        Args:
            set_id: Instruction set ID
            content: Instruction text
            priority: Priority level
            short_form: Short reminder form
            keyword: Trigger keyword

        Returns:
            Created Instruction
        """
        instruction_set = self._instruction_sets.get(set_id)
        if not instruction_set:
            raise ValueError(f"Instruction set {set_id} not found")

        index = len(instruction_set.instructions)

        instruction = Instruction(
            id=uuid4(),
            index=index,
            content=content,
            priority=priority,
            short_form=short_form,
            keyword=keyword
        )

        instruction_set.instructions.append(instruction)

        # Add default reminder
        frequency = self.DEFAULT_FREQUENCIES.get(priority, 10)
        instruction_set.reminders.append(Reminder(
            instruction_index=index,
            position=ReminderPosition.END,
            frequency=frequency
        ))

        logger.info(f"Added instruction {index} to set {set_id}")

        return instruction

    def _calculate_compliance_score(self, instruction_set: InstructionSet) -> float:
        """Calculate overall compliance score for an instruction set."""
        total_weight = 0.0
        weighted_compliance = 0.0

        weights = {
            InstructionPriority.CRITICAL: 4.0,
            InstructionPriority.HIGH: 2.0,
            InstructionPriority.MEDIUM: 1.0,
            InstructionPriority.LOW: 0.5,
        }

        for instruction in instruction_set.instructions:
            weight = weights.get(instruction.priority, 1.0)
            total = instruction.compliance_count + instruction.violation_count

            if total > 0:
                compliance_rate = instruction.compliance_count / total
                weighted_compliance += compliance_rate * weight

            total_weight += weight

        if total_weight == 0:
            return 100.0

        return (weighted_compliance / total_weight) * 100

    def get_triggered_instructions(
        self,
        set_id: UUID,
        text: str
    ) -> List[Instruction]:
        """
        Get instructions triggered by keywords in text.

        Args:
            set_id: Instruction set ID
            text: Text to check for keywords

        Returns:
            List of triggered Instructions
        """
        instruction_set = self._instruction_sets.get(set_id)
        if not instruction_set:
            return []

        triggered = []
        text_lower = text.lower()

        for instruction in instruction_set.instructions:
            if instruction.keyword and instruction.keyword.lower() in text_lower:
                triggered.append(instruction)

        return triggered
