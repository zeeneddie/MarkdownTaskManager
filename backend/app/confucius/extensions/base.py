"""
Base Agent Extension for Confucius Orchestrator.

Each MarQed agent (Felix, Quinn, etc.) is wrapped as an extension
with four lifecycle hooks for modular integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
import logging

if TYPE_CHECKING:
    from ..orchestrator import ConfuciusOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class ExtensionMetadata:
    """Metadata describing an agent extension."""
    name: str
    description: str
    capabilities: List[str]
    domains: List[str]
    priority: int = 0  # Higher = more important
    parallel_safe: bool = True  # Can run in parallel with others
    timeout_seconds: int = 60
    version: str = "1.0.0"

    def matches_task(self, task: str, context: Dict[str, Any]) -> float:
        """
        Calculate match score for a task (0.0 - 1.0).

        Used by router to determine which extensions to invoke.
        """
        score = 0.0
        task_lower = task.lower()

        # Check domain match
        for domain in self.domains:
            if domain.lower() in task_lower:
                score += 0.3
                break

        # Check capability match
        for cap in self.capabilities:
            if cap.lower().replace("_", " ") in task_lower:
                score += 0.2
                break

        # Context-based matching
        if context:
            context_str = str(context).lower()
            for domain in self.domains:
                if domain.lower() in context_str:
                    score += 0.1
                    break

        return min(score, 1.0)


@dataclass
class ExtensionResult:
    """Result from extension execution."""
    extension_name: str
    success: bool
    output: Dict[str, Any]
    duration_ms: int
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extension": self.extension_name,
            "success": self.success,
            "output": self.output,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseAgentExtension(ABC):
    """
    Base class for agent extensions in the Confucius orchestrator.

    Each MarQed agent (Felix, Quinn, etc.) is wrapped as an extension
    with four lifecycle hooks:

    1. on_input_messages: Modify prompts before LLM invocation
    2. on_llm_output: Parse LLM responses into actions
    3. on_execute: Execute actions (tool calls)
    4. on_post: Record outcomes to memory/artifacts

    Example usage:
    ```python
    class FelixExtension(BaseAgentExtension):
        def __init__(self, felix_service):
            super().__init__(ExtensionMetadata(
                name="Felix",
                description="Architecture agent",
                capabilities=["architecture_analysis", "dependency_mapping"],
                domains=["architecture", "design"],
                priority=1,
            ))
            self.felix_service = felix_service

        async def execute(self, task, context):
            return await self.felix_service.analyze(task, context)
    ```
    """

    def __init__(self, metadata: ExtensionMetadata):
        self.metadata = metadata
        self._orchestrator: Optional["ConfuciusOrchestrator"] = None
        self._partial_result: Dict[str, Any] = {}
        self._execution_start: Optional[datetime] = None

    @property
    def name(self) -> str:
        """Extension name."""
        return self.metadata.name

    @property
    def priority(self) -> int:
        """Extension priority."""
        return self.metadata.priority

    def set_orchestrator(self, orchestrator: "ConfuciusOrchestrator") -> None:
        """Set reference to parent orchestrator."""
        self._orchestrator = orchestrator

    # ========== LIFECYCLE HOOKS ==========

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Hook 1: Modify context before LLM invocation.

        Override to:
        - Add agent-specific system prompts
        - Filter irrelevant context
        - Inject relevant memories
        - Add domain-specific instructions

        Args:
            task: The task description
            context: Current context dictionary

        Returns:
            Modified context dictionary
        """
        return context  # Default: no modification

    @abstractmethod
    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main execution method.

        This wraps the existing agent logic and returns raw output.
        Must be implemented by each extension.

        Args:
            task: The task to execute
            context: Context dictionary (may be modified by on_input_messages)

        Returns:
            Raw output dictionary from the agent
        """
        pass

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Hook 2: Parse LLM output into structured actions.

        Override to:
        - Extract tool calls from response
        - Parse structured data
        - Validate output format
        - Handle errors/retries

        Args:
            raw_output: Raw output from execute()

        Returns:
            Parsed/structured output
        """
        return raw_output  # Default: no modification

    async def on_execute(
        self,
        parsed_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Hook 3: Execute actions from parsed output.

        Override to:
        - Execute tool calls
        - Run code analysis
        - Call external services
        - Perform file operations

        Args:
            parsed_output: Output from on_llm_output()

        Returns:
            Output with tool execution results
        """
        return parsed_output  # Default: no tool execution

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """
        Hook 4: Post-processing and memory recording.

        Override to:
        - Record to memory scopes
        - Generate artifacts
        - Update metrics
        - Trigger notifications

        Args:
            executed_output: Output from on_execute()
            entry_id: ID of the current entry for memory linking

        Returns:
            Final output (may include additional metadata)
        """
        return executed_output  # Default: no post-processing

    # ========== UTILITY METHODS ==========

    def get_partial(self) -> Dict[str, Any]:
        """Get partial result (for timeout scenarios)."""
        return self._partial_result

    def update_partial(self, update: Dict[str, Any]) -> None:
        """Update partial result during execution."""
        self._partial_result.update(update)

    def clear_partial(self) -> None:
        """Clear partial result."""
        self._partial_result = {}

    async def get_relevant_memory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant memory from orchestrator."""
        if self._orchestrator:
            relevant = await self._orchestrator.memory.get_relevant(
                task_context=context,
                extensions=[self.name],
            )
            return relevant.to_context() if hasattr(relevant, 'to_context') else relevant
        return {}

    def matches_task(self, task: str, context: Dict[str, Any]) -> float:
        """Calculate how well this extension matches the given task."""
        return self.metadata.matches_task(task, context)

    def start_execution(self) -> None:
        """Mark start of execution (for timing)."""
        self._execution_start = datetime.utcnow()
        self.clear_partial()

    def get_execution_duration_ms(self) -> int:
        """Get execution duration in milliseconds."""
        if self._execution_start:
            delta = datetime.utcnow() - self._execution_start
            return int(delta.total_seconds() * 1000)
        return 0

    async def run_full_lifecycle(
        self,
        task: str,
        context: Dict[str, Any],
        entry_id: str,
    ) -> ExtensionResult:
        """
        Run the full extension lifecycle.

        Executes all four hooks in sequence:
        1. on_input_messages
        2. execute
        3. on_llm_output
        4. on_execute
        5. on_post

        Args:
            task: Task description
            context: Context dictionary
            entry_id: Entry ID for memory linking

        Returns:
            ExtensionResult with output and metadata
        """
        self.start_execution()

        try:
            # Hook 1: Prepare input
            modified_context = await self.on_input_messages(task, context)

            # Main execution
            raw_output = await self.execute(task, modified_context)
            self.update_partial({"raw_complete": True})

            # Hook 2: Parse output
            parsed_output = await self.on_llm_output(raw_output)

            # Hook 3: Execute tools
            executed_output = await self.on_execute(parsed_output)

            # Hook 4: Post-processing
            final_output = await self.on_post(executed_output, entry_id)

            return ExtensionResult(
                extension_name=self.name,
                success=True,
                output=final_output,
                duration_ms=self.get_execution_duration_ms(),
            )

        except Exception as e:
            logger.error(f"Extension {self.name} failed: {e}")
            return ExtensionResult(
                extension_name=self.name,
                success=False,
                output=self.get_partial(),
                duration_ms=self.get_execution_duration_ms(),
                error=str(e),
            )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, priority={self.priority})>"
