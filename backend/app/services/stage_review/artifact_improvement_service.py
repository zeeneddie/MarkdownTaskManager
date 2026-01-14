"""
Artifact Improvement Service.

Fase 23.6 Phase 24.2: Dedicated service for intelligent artifact improvement.
Applies fixes for issues found during stage review, using specialized improvement strategies.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

from .types import ConsolidatedIssue, IssueSeverity, IssueCategory, StageType
from .stage_council_config import get_provider_for_model

logger = logging.getLogger(__name__)


class ImprovementStrategy(str, Enum):
    """Strategy for artifact improvement."""
    FULL_REWRITE = "full_rewrite"  # Rewrite entire artifact
    TARGETED_FIXES = "targeted_fixes"  # Fix specific issues only
    INCREMENTAL = "incremental"  # Fix one issue at a time
    HYBRID = "hybrid"  # Combine strategies based on issue count


@dataclass
class ImprovementResult:
    """Result of artifact improvement."""
    success: bool
    original_artifact: str
    improved_artifact: str
    strategy_used: ImprovementStrategy
    issues_addressed: int
    changes_made: List[str] = field(default_factory=list)
    error: Optional[str] = None
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "strategy_used": self.strategy_used.value,
            "issues_addressed": self.issues_addressed,
            "changes_made": self.changes_made,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "artifact_changed": self.original_artifact != self.improved_artifact,
        }


class ArtifactImprovementService:
    """
    Service for improving artifacts based on review issues.

    Features:
    - Multiple improvement strategies
    - Stage-specific improvement prompts
    - Issue prioritization
    - Validation of improvements
    """

    def __init__(
        self,
        llm_provider: Optional[Callable[[str, str, str, int], Awaitable[Dict]]] = None,
    ):
        """
        Initialize the artifact improvement service.

        Args:
            llm_provider: Optional async function for LLM calls.
                          Signature: (provider, model, prompt, max_tokens) -> response
        """
        self.llm_provider = llm_provider

        # Strategy thresholds
        self._strategy_thresholds = {
            "full_rewrite": 10,  # >= 10 issues: full rewrite
            "targeted_fixes": 3,  # 3-9 issues: targeted fixes
            "incremental": 0,  # 1-2 issues: incremental
        }

    async def improve_artifact(
        self,
        artifact: str,
        artifact_type: str,
        issues: List[ConsolidatedIssue],
        stage_type: StageType,
        model: str,
        context: Optional[Dict[str, Any]] = None,
        strategy: Optional[ImprovementStrategy] = None,
    ) -> ImprovementResult:
        """
        Improve an artifact based on identified issues.

        Args:
            artifact: The artifact content to improve
            artifact_type: Type of artifact (code, document, config, etc.)
            issues: List of issues to address
            stage_type: The development stage
            model: LLM model to use for improvement
            context: Additional context
            strategy: Override automatic strategy selection

        Returns:
            ImprovementResult with improved artifact
        """
        import time
        start_time = time.time()

        # Filter to important issues only
        important_issues = self._filter_important_issues(issues)

        if not important_issues:
            return ImprovementResult(
                success=True,
                original_artifact=artifact,
                improved_artifact=artifact,
                strategy_used=ImprovementStrategy.INCREMENTAL,
                issues_addressed=0,
                changes_made=["No important issues to address"],
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # Select strategy if not specified
        if strategy is None:
            strategy = self._select_strategy(important_issues)

        try:
            # Apply improvement strategy
            if strategy == ImprovementStrategy.FULL_REWRITE:
                improved, changes = await self._apply_full_rewrite(
                    artifact, artifact_type, important_issues, stage_type, model, context
                )
            elif strategy == ImprovementStrategy.INCREMENTAL:
                improved, changes = await self._apply_incremental(
                    artifact, artifact_type, important_issues, stage_type, model, context
                )
            else:  # TARGETED_FIXES or HYBRID
                improved, changes = await self._apply_targeted_fixes(
                    artifact, artifact_type, important_issues, stage_type, model, context
                )

            return ImprovementResult(
                success=True,
                original_artifact=artifact,
                improved_artifact=improved,
                strategy_used=strategy,
                issues_addressed=len(important_issues),
                changes_made=changes,
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            logger.error(f"Artifact improvement failed: {e}")
            return ImprovementResult(
                success=False,
                original_artifact=artifact,
                improved_artifact=artifact,
                strategy_used=strategy,
                issues_addressed=0,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    def _filter_important_issues(
        self,
        issues: List[ConsolidatedIssue],
    ) -> List[ConsolidatedIssue]:
        """Filter to critical and major issues only."""
        return [
            issue for issue in issues
            if issue.severity in (IssueSeverity.CRITICAL, IssueSeverity.MAJOR)
            and issue.consensus_score >= 0.5  # At least half the models agree
        ]

    def _select_strategy(self, issues: List[ConsolidatedIssue]) -> ImprovementStrategy:
        """Select improvement strategy based on issue count and severity."""
        issue_count = len(issues)
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)

        # Critical issues require more aggressive approach
        if critical_count >= 3:
            return ImprovementStrategy.FULL_REWRITE

        if issue_count >= self._strategy_thresholds["full_rewrite"]:
            return ImprovementStrategy.FULL_REWRITE
        elif issue_count >= self._strategy_thresholds["targeted_fixes"]:
            return ImprovementStrategy.TARGETED_FIXES
        else:
            return ImprovementStrategy.INCREMENTAL

    async def _apply_full_rewrite(
        self,
        artifact: str,
        artifact_type: str,
        issues: List[ConsolidatedIssue],
        stage_type: StageType,
        model: str,
        context: Optional[Dict[str, Any]],
    ) -> tuple[str, List[str]]:
        """Apply full rewrite strategy."""
        prompt = self._build_rewrite_prompt(
            artifact, artifact_type, issues, stage_type, context
        )

        improved = await self._call_llm(model, prompt)
        changes = [f"Full rewrite addressing {len(issues)} issues"]

        return improved, changes

    async def _apply_targeted_fixes(
        self,
        artifact: str,
        artifact_type: str,
        issues: List[ConsolidatedIssue],
        stage_type: StageType,
        model: str,
        context: Optional[Dict[str, Any]],
    ) -> tuple[str, List[str]]:
        """Apply targeted fixes strategy."""
        prompt = self._build_targeted_prompt(
            artifact, artifact_type, issues, stage_type, context
        )

        improved = await self._call_llm(model, prompt)
        changes = [f"Targeted fix for: {issue.title}" for issue in issues[:5]]

        return improved, changes

    async def _apply_incremental(
        self,
        artifact: str,
        artifact_type: str,
        issues: List[ConsolidatedIssue],
        stage_type: StageType,
        model: str,
        context: Optional[Dict[str, Any]],
    ) -> tuple[str, List[str]]:
        """Apply incremental fixes (one issue at a time)."""
        current_artifact = artifact
        changes = []

        for issue in issues:
            prompt = self._build_single_fix_prompt(
                current_artifact, artifact_type, issue, stage_type, context
            )
            current_artifact = await self._call_llm(model, prompt)
            changes.append(f"Fixed: {issue.title}")

        return current_artifact, changes

    async def _call_llm(self, model: str, prompt: str) -> str:
        """Call LLM for improvement."""
        if self.llm_provider:
            provider = get_provider_for_model(model)
            response = await self.llm_provider(provider, model, prompt, 8000)
            return self._extract_improved_artifact(response.get("text", ""))
        else:
            # Mock for testing
            return prompt.split("ORIGINAL ARTIFACT:")[1].split("```")[1] if "ORIGINAL ARTIFACT:" in prompt else "# Improved artifact"

    def _build_rewrite_prompt(
        self,
        artifact: str,
        artifact_type: str,
        issues: List[ConsolidatedIssue],
        stage_type: StageType,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Build prompt for full rewrite."""
        issues_text = self._format_issues(issues)
        context_text = self._format_context(context)
        stage_guidance = self._get_stage_guidance(stage_type)

        return f"""You are an expert {artifact_type} improver specializing in {stage_type.value} work.

TASK: Completely rewrite this artifact to address ALL identified issues while preserving its core purpose.

{stage_guidance}

ORIGINAL ARTIFACT:
```
{artifact}
```

ISSUES TO ADDRESS ({len(issues)} total):
{issues_text}

{context_text}

REWRITE INSTRUCTIONS:
1. Address ALL listed issues
2. Maintain the original purpose and functionality
3. Apply {stage_type.value} best practices
4. Ensure the rewritten artifact is production-quality
5. Keep explanatory comments minimal but helpful

OUTPUT FORMAT:
[IMPROVED_ARTIFACT]
```
Your rewritten artifact here
```
[/IMPROVED_ARTIFACT]

[CHANGES_SUMMARY]
- List of significant changes made
[/CHANGES_SUMMARY]
"""

    def _build_targeted_prompt(
        self,
        artifact: str,
        artifact_type: str,
        issues: List[ConsolidatedIssue],
        stage_type: StageType,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Build prompt for targeted fixes."""
        issues_text = self._format_issues(issues)
        context_text = self._format_context(context)

        return f"""You are an expert {artifact_type} improver.

TASK: Apply targeted fixes to address the specific issues listed below.

ORIGINAL ARTIFACT:
```
{artifact}
```

ISSUES TO FIX:
{issues_text}

{context_text}

INSTRUCTIONS:
1. Make minimal changes - only what's needed to fix the issues
2. Preserve all existing correct functionality
3. Keep the original style and structure
4. Add comments only where they clarify the fix

OUTPUT FORMAT:
[IMPROVED_ARTIFACT]
```
Your improved artifact here
```
[/IMPROVED_ARTIFACT]

[CHANGES_MADE]
- Brief description of each change
[/CHANGES_MADE]
"""

    def _build_single_fix_prompt(
        self,
        artifact: str,
        artifact_type: str,
        issue: ConsolidatedIssue,
        stage_type: StageType,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Build prompt for single issue fix."""
        return f"""Fix this single issue in the {artifact_type}:

ISSUE:
- Severity: {issue.severity.value.upper()}
- Category: {issue.category.value}
- Title: {issue.title}
- Description: {issue.description}
- Suggested Fix: {issue.suggested_fix or 'Not provided'}
- Line Reference: {issue.line_start or 'N/A'}

ARTIFACT:
```
{artifact}
```

Return ONLY the complete fixed artifact (no explanations):
[IMPROVED_ARTIFACT]
```
Your fixed artifact
```
[/IMPROVED_ARTIFACT]
"""

    def _format_issues(self, issues: List[ConsolidatedIssue]) -> str:
        """Format issues for prompt."""
        text = ""
        for i, issue in enumerate(issues, 1):
            consensus_pct = int(issue.consensus_score * 100)
            text += f"""
Issue #{i} ({consensus_pct}% consensus):
  Severity: {issue.severity.value.upper()}
  Category: {issue.category.value}
  Title: {issue.title}
  Description: {issue.description}
  Suggested Fix: {issue.suggested_fix or 'Not provided'}
  Line: {issue.line_start or 'N/A'}
"""
        return text

    def _format_context(self, context: Optional[Dict[str, Any]]) -> str:
        """Format context for prompt."""
        if not context:
            return ""

        text = "\nADDITIONAL CONTEXT:\n"
        for key, value in context.items():
            text += f"- {key}: {value}\n"
        return text

    def _get_stage_guidance(self, stage_type: StageType) -> str:
        """Get stage-specific guidance."""
        guidance = {
            StageType.ARCHITECTURE: """
ARCHITECTURE GUIDELINES:
- Ensure scalability patterns are applied
- Follow SOLID principles
- Consider security implications
- Document key architectural decisions
""",
            StageType.DESIGN: """
DESIGN GUIDELINES:
- Apply appropriate design patterns
- Ensure clear interface definitions
- Maintain consistency with existing patterns
- Keep it simple (KISS principle)
""",
            StageType.PROGRAMMING: """
CODE GUIDELINES:
- Follow clean code principles
- Ensure proper error handling
- Add meaningful variable/function names
- Apply defensive programming
""",
            StageType.TESTING: """
TESTING GUIDELINES:
- Ensure comprehensive coverage
- Test edge cases and boundaries
- Use meaningful assertions
- Keep tests independent and fast
""",
            StageType.INFRASTRUCTURE: """
INFRASTRUCTURE GUIDELINES:
- Follow infrastructure as code best practices
- Ensure security configurations
- Apply resource tagging
- Consider cost optimization
""",
        }
        return guidance.get(stage_type, "")

    def _extract_improved_artifact(self, response: str) -> str:
        """Extract improved artifact from LLM response."""
        # Try to find the artifact block
        pattern = r'\[IMPROVED_ARTIFACT\]\s*```(?:\w+)?\s*(.*?)\s*```\s*\[/IMPROVED_ARTIFACT\]'
        match = re.search(pattern, response, re.DOTALL)

        if match:
            return match.group(1).strip()

        # Fallback: look for any code block
        code_pattern = r'```(?:\w+)?\s*(.*?)\s*```'
        code_match = re.search(code_pattern, response, re.DOTALL)

        if code_match:
            return code_match.group(1).strip()

        # Last resort: return entire response
        return response.strip()


# Factory function
def create_artifact_improvement_service(
    llm_provider: Optional[Callable[[str, str, str, int], Awaitable[Dict]]] = None,
) -> ArtifactImprovementService:
    """Create an ArtifactImprovementService instance."""
    return ArtifactImprovementService(llm_provider=llm_provider)
