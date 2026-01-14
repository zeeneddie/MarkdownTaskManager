"""
Context Optimizer for Token-Efficient Agent Execution.

Combines reference selection with context building to minimize
token usage while maintaining task-relevant information.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .reference_selector import (
    ReferenceSelector,
    ReferenceMatch,
    Reference,
    create_reference_selector,
)
from .reference_registry import (
    ReferenceRegistry,
    create_reference_registry,
)

logger = logging.getLogger(__name__)


@dataclass
class OptimizedContext:
    """Result of context optimization."""
    task: str
    original_context: Dict[str, Any]
    selected_references: List[ReferenceMatch]
    reference_content: Dict[str, str]
    token_estimate: int
    token_savings: int
    optimization_ratio: float
    agent_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def get_enriched_context(self) -> Dict[str, Any]:
        """
        Get context enriched with reference content.

        Returns:
            Context dictionary with references added
        """
        ctx = self.original_context.copy()
        ctx["_references"] = {
            ref_id: content
            for ref_id, content in self.reference_content.items()
        }
        ctx["_reference_metadata"] = [
            m.to_dict() for m in self.selected_references
        ]
        ctx["_token_estimate"] = self.token_estimate
        return ctx

    def get_combined_reference_content(self) -> str:
        """Get all reference content combined."""
        parts = []
        for match in self.selected_references:
            content = self.reference_content.get(match.reference.id, "")
            if content:
                parts.append(f"# {match.reference.name}\n\n{content}")
        return "\n\n---\n\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task": self.task[:100],
            "agent_name": self.agent_name,
            "references_selected": len(self.selected_references),
            "reference_ids": [m.reference.id for m in self.selected_references],
            "token_estimate": self.token_estimate,
            "token_savings": self.token_savings,
            "optimization_ratio": round(self.optimization_ratio, 2),
            "created_at": self.created_at.isoformat(),
        }


class ContextOptimizer:
    """
    Optimizes context for token-efficient agent execution.

    Combines reference selection with content loading to build
    optimal context for each task, reducing token usage by 60-80%.

    Example:
    ```python
    optimizer = ContextOptimizer()

    result = optimizer.optimize(
        task="Analyze ASP code for connection leaks",
        context={"domain": "stability"},
        agent_name="Miguel",
    )

    # Use enriched context with agent
    enriched = result.get_enriched_context()
    ```
    """

    # Estimated tokens for full context without optimization
    FULL_CONTEXT_ESTIMATE = 25000

    def __init__(
        self,
        selector: Optional[ReferenceSelector] = None,
        registry: Optional[ReferenceRegistry] = None,
        max_references: int = 3,
        max_tokens: int = 8000,
    ):
        """
        Initialize optimizer.

        Args:
            selector: Reference selector (created if None)
            registry: Reference registry (created if None)
            max_references: Maximum references to include
            max_tokens: Maximum tokens for references
        """
        self._selector = selector or create_reference_selector()
        self._registry = registry or create_reference_registry(auto_load=False)
        self._max_references = max_references
        self._max_tokens = max_tokens

    def optimize(
        self,
        task: str,
        context: Dict[str, Any],
        agent_name: Optional[str] = None,
        required_references: Optional[List[str]] = None,
    ) -> OptimizedContext:
        """
        Optimize context for a task.

        Args:
            task: Task description
            context: Original task context
            agent_name: Name of executing agent
            required_references: Reference IDs that must be included

        Returns:
            OptimizedContext with selected references
        """
        required_references = required_references or []

        # Select relevant references
        if agent_name:
            matches = self._selector.select_for_agent(
                agent_name=agent_name,
                task=task,
                context=context,
            )
        else:
            matches = self._selector.select(
                task=task,
                context=context,
                max_references=self._max_references,
            )

        # Add required references if not already included
        for ref_id in required_references:
            if not any(m.reference.id == ref_id for m in matches):
                ref = self._selector.get_reference(ref_id)
                if ref:
                    matches.append(ReferenceMatch(
                        reference=ref,
                        score=1.0,
                        matched_keywords=[],
                        reason="Required reference",
                    ))

        # Filter by token budget
        matches = self._filter_by_tokens(matches)

        # Load reference content
        reference_content = self._load_content(matches)

        # Calculate token estimate
        token_estimate = sum(
            m.reference.token_estimate for m in matches
        )
        token_savings = self.FULL_CONTEXT_ESTIMATE - token_estimate
        optimization_ratio = token_savings / self.FULL_CONTEXT_ESTIMATE

        logger.info(
            f"Context optimized: {len(matches)} refs, "
            f"{token_estimate} tokens, {optimization_ratio:.1%} savings"
        )

        return OptimizedContext(
            task=task,
            original_context=context,
            selected_references=matches,
            reference_content=reference_content,
            token_estimate=token_estimate,
            token_savings=token_savings,
            optimization_ratio=optimization_ratio,
            agent_name=agent_name,
        )

    def optimize_for_workflow(
        self,
        workflow_type: str,
        stages: List[str],
        context: Dict[str, Any],
    ) -> Dict[str, OptimizedContext]:
        """
        Optimize context for a workflow with multiple stages.

        Args:
            workflow_type: Type of workflow (brown_paper, migration, etc.)
            stages: List of stage names
            context: Workflow context

        Returns:
            Dictionary of stage -> OptimizedContext
        """
        # Stage-to-reference mappings
        WORKFLOW_REFERENCES = {
            "brown_paper": {
                "code_understanding": ["asp-vbscript", "stability-analysis"],
                "domain_extraction": ["python-best-practices"],
                "estimation": ["fp-methodology"],
            },
            "migration": {
                "technical_analysis": ["asp-vbscript", "security-patterns"],
                "generate_specification": ["fastapi-conventions"],
                "quality_review": ["testing-patterns"],
            },
            "green_paper": {
                "requirements_constitution": ["python-best-practices"],
                "architecture_design": ["fastapi-conventions", "sqlalchemy-patterns"],
                "quality_review": ["testing-patterns", "security-patterns"],
            },
            "quality": {
                "scan_execution": ["stability-analysis", "security-patterns"],
                "quality_review": ["testing-patterns"],
            },
        }

        stage_refs = WORKFLOW_REFERENCES.get(workflow_type, {})
        results = {}

        for stage in stages:
            required = stage_refs.get(stage, [])
            results[stage] = self.optimize(
                task=f"Execute {stage} stage for {workflow_type}",
                context={**context, "stage": stage, "workflow": workflow_type},
                required_references=required,
            )

        return results

    def get_reference_summary(self) -> Dict[str, Any]:
        """Get summary of available references."""
        refs = self._selector.list_references()
        return {
            "total_references": len(refs),
            "total_estimated_tokens": sum(r.token_estimate for r in refs),
            "by_category": self._group_by_category(refs),
            "max_references_per_task": self._max_references,
            "max_tokens_per_task": self._max_tokens,
        }

    def _filter_by_tokens(
        self,
        matches: List[ReferenceMatch],
    ) -> List[ReferenceMatch]:
        """Filter matches to stay within token budget."""
        filtered = []
        total_tokens = 0

        for match in matches:
            if total_tokens + match.reference.token_estimate <= self._max_tokens:
                filtered.append(match)
                total_tokens += match.reference.token_estimate
            else:
                logger.debug(
                    f"Skipping {match.reference.id} due to token budget "
                    f"({total_tokens}/{self._max_tokens})"
                )

        return filtered

    def _load_content(
        self,
        matches: List[ReferenceMatch],
    ) -> Dict[str, str]:
        """Load content for matched references."""
        content = {}
        for match in matches:
            ref_content = self._registry.get_content(match.reference.id)
            if ref_content:
                content[match.reference.id] = ref_content
            else:
                # Generate placeholder content if not loaded
                content[match.reference.id] = self._generate_placeholder(
                    match.reference
                )
        return content

    def _generate_placeholder(self, ref: Reference) -> str:
        """Generate placeholder content for unloaded reference."""
        return f"""# {ref.name}

## Overview
{ref.description}

## Keywords
{', '.join(ref.keywords[:10])}

## Category
{ref.category.value}

*Note: Full reference content not loaded. Create file at {ref.path}*
"""

    def _group_by_category(
        self,
        refs: List[Reference],
    ) -> Dict[str, int]:
        """Group references by category."""
        groups: Dict[str, int] = {}
        for ref in refs:
            cat = ref.category.value
            groups[cat] = groups.get(cat, 0) + 1
        return groups


def create_context_optimizer(
    max_references: int = 3,
    max_tokens: int = 8000,
) -> ContextOptimizer:
    """
    Factory function to create context optimizer.

    Args:
        max_references: Maximum references per task
        max_tokens: Maximum tokens for references

    Returns:
        Configured ContextOptimizer
    """
    return ContextOptimizer(
        max_references=max_references,
        max_tokens=max_tokens,
    )
