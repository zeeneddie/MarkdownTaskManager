"""
Stage Review Service.

Fase 23.6 Phase 24.1: Core service for stage-based LLM council reviews.
Orchestrates multi-model reviews with consensus calculation and threshold evaluation.
"""

import asyncio
import hashlib
import re
import logging
from uuid import uuid4
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Awaitable

from .types import (
    StageType,
    IssueSeverity,
    IssueCategory,
    ReviewStatus,
    ReviewDecision,
    ModelRole,
    ParsedIssue,
    ModelReviewResult,
    ConsolidatedIssue,
    ReviewRoundResult,
    ReviewResult,
    StageCouncilConfig,
)
from .stage_council_config import (
    get_stage_config,
    get_provider_for_model,
    STAGE_COUNCIL_CONFIGS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# STAGE REVIEW SERVICE
# =============================================================================


class StageReviewService:
    """
    Stage-Based LLM Council Review Service.

    Reviews development artifacts at each stage using multiple LLM models.
    Implements automatic second round with improvement when issues exceed threshold.
    """

    def __init__(
        self,
        llm_provider: Optional[Callable[[str, str, str, int], Awaitable[Dict]]] = None,
    ):
        """
        Initialize the stage review service.

        Args:
            llm_provider: Optional async function for LLM calls.
                          Signature: (provider, model, prompt, max_tokens) -> response
                          If None, uses mock responses for testing.
        """
        self.llm_provider = llm_provider
        self.configs = STAGE_COUNCIL_CONFIGS
        self._review_cache: Dict[str, ReviewResult] = {}

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    async def review_artifact(
        self,
        stage_type: str,
        artifact: str,
        artifact_type: str = "code",
        context: Optional[Dict[str, Any]] = None,
        force_review: bool = False,
    ) -> ReviewResult:
        """
        Review an artifact for a specific development stage.

        This is the main entry point for stage-based reviews.
        Handles caching, multi-model review, consensus calculation,
        and automatic second round if needed.

        Args:
            stage_type: Development stage (architecture, design, etc.)
            artifact: The artifact content to review
            artifact_type: Type of artifact (code, document, config, etc.)
            context: Additional context for the review
            force_review: Skip cache and force new review

        Returns:
            ReviewResult with decision, issues, and metrics

        Raises:
            ValueError: If stage_type is unknown

        Example:
            >>> result = await service.review_artifact(
            ...     stage_type="programming",
            ...     artifact=code_content,
            ...     context={"function_name": "calculate_fp", "language": "python"}
            ... )
            >>> if result.approved:
            ...     print("Code approved!")
            ... else:
            ...     print(f"Found {len(result.issues)} issues")
        """
        # Validate stage type
        if stage_type not in self.configs:
            raise ValueError(f"Unknown stage type: {stage_type}")

        config = self.configs[stage_type]
        artifact_hash = self._compute_hash(artifact)
        session_id = str(uuid4())

        # Check cache (unless forced)
        if not force_review and artifact_hash in self._review_cache:
            logger.info(f"Returning cached review for hash {artifact_hash[:8]}")
            return self._review_cache[artifact_hash]

        logger.info(f"Starting {stage_type} review for session {session_id}")
        start_time = datetime.utcnow()

        # Round 1: Multi-model review
        round1_result = await self._execute_review_round(
            session_id=session_id,
            stage_type=stage_type,
            artifact=artifact,
            artifact_type=artifact_type,
            context=context or {},
            config=config,
            round_number=1,
        )

        # Evaluate if second round needed
        needs_second_round = self._evaluate_threshold(
            issues=round1_result.consolidated_issues,
            config=config,
        )

        final_issues = round1_result.consolidated_issues
        rounds_completed = 1
        improved_artifact: Optional[str] = None

        if needs_second_round and config.enable_second_round:
            logger.info(f"Threshold exceeded, starting second round for {session_id}")

            # Second round: Improve and re-review
            improved_artifact = await self._improve_artifact(
                artifact=artifact,
                artifact_type=artifact_type,
                issues=round1_result.consolidated_issues,
                config=config,
                context=context,
            )

            round2_result = await self._execute_review_round(
                session_id=session_id,
                stage_type=stage_type,
                artifact=improved_artifact,
                artifact_type=artifact_type,
                context=context or {},
                config=config,
                round_number=2,
            )

            final_issues = round2_result.consolidated_issues
            rounds_completed = 2

        # Calculate final decision
        final_consensus = (
            round1_result.consensus_level if rounds_completed == 1
            else round2_result.consensus_level
        )

        decision = self._make_decision(
            issues=final_issues,
            consensus=final_consensus,
            config=config,
        )

        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        result = ReviewResult(
            session_id=session_id,
            stage_type=StageType(stage_type),
            decision=decision,
            approved=(decision == ReviewDecision.APPROVED),
            issues=final_issues,
            consensus_level=final_consensus,
            rounds_completed=rounds_completed,
            improved_artifact=improved_artifact,
            metrics={
                "duration_ms": duration_ms,
                "round1_issues": len(round1_result.consolidated_issues),
                "final_issues": len(final_issues),
            },
            created_at=datetime.utcnow(),
        )

        # Cache result
        self._review_cache[artifact_hash] = result

        logger.info(
            f"Review {session_id} completed: {decision.value}, "
            f"{len(final_issues)} issues, {rounds_completed} rounds"
        )

        return result

    # ========================================================================
    # REVIEW EXECUTION
    # ========================================================================

    async def _execute_review_round(
        self,
        session_id: str,
        stage_type: str,
        artifact: str,
        artifact_type: str,
        context: Dict[str, Any],
        config: StageCouncilConfig,
        round_number: int,
    ) -> ReviewRoundResult:
        """Execute a single review round with all configured models."""

        models = config.primary_models

        # Build review prompt
        review_prompt = self._build_review_prompt(
            stage_type=stage_type,
            artifact=artifact,
            artifact_type=artifact_type,
            context=context,
            criteria=config.criteria,
        )

        # Query all models
        if config.parallel_execution and self.llm_provider:
            tasks = [
                self._query_model_for_review(
                    model_name=model,
                    prompt=review_prompt,
                    timeout=config.timeout_per_model_seconds,
                )
                for model in models
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []
            for model in models:
                try:
                    result = await self._query_model_for_review(
                        model_name=model,
                        prompt=review_prompt,
                        timeout=config.timeout_per_model_seconds,
                    )
                    results.append(result)
                except Exception as e:
                    results.append(e)

        # Process results
        successful_reviews: List[ModelReviewResult] = []
        all_parsed_issues: List[ParsedIssue] = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Model {models[i]} failed: {result}")
                continue

            successful_reviews.append(result)
            for issue in result.issues:
                issue.model_name = result.model_name
                all_parsed_issues.append(issue)

        # Consolidate and calculate consensus
        consolidated_issues = self._consolidate_issues(
            all_parsed_issues,
            len(successful_reviews),
        )
        consensus_level = self._calculate_consensus(
            successful_reviews,
            consolidated_issues,
        )

        return ReviewRoundResult(
            round_number=round_number,
            model_reviews=successful_reviews,
            consolidated_issues=consolidated_issues,
            consensus_level=consensus_level,
            models_responded=len(successful_reviews),
            models_total=len(models),
        )

    async def _query_model_for_review(
        self,
        model_name: str,
        prompt: str,
        timeout: int,
    ) -> ModelReviewResult:
        """Query a single model for review."""

        start_time = datetime.utcnow()

        try:
            if self.llm_provider:
                provider = get_provider_for_model(model_name)
                response = await asyncio.wait_for(
                    self.llm_provider(provider, model_name, prompt, 4000),
                    timeout=timeout,
                )
                review_text = response.get("text", "")
            else:
                # Mock response for testing
                review_text = self._generate_mock_review(model_name)

            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Parse issues from response
            parsed_issues = self._parse_review_response(review_text)

            return ModelReviewResult(
                model_name=model_name,
                model_role=ModelRole.PRIMARY,
                issues=parsed_issues,
                review_text=review_text,
                response_time_ms=response_time_ms,
                status="completed",
            )

        except asyncio.TimeoutError:
            return ModelReviewResult(
                model_name=model_name,
                model_role=ModelRole.PRIMARY,
                issues=[],
                review_text="",
                response_time_ms=timeout * 1000,
                status="timeout",
                error_message=f"Timeout after {timeout}s",
            )

        except Exception as e:
            return ModelReviewResult(
                model_name=model_name,
                model_role=ModelRole.PRIMARY,
                issues=[],
                review_text="",
                response_time_ms=0,
                status="failed",
                error_message=str(e),
            )

    # ========================================================================
    # PROMPT ENGINEERING
    # ========================================================================

    def _build_review_prompt(
        self,
        stage_type: str,
        artifact: str,
        artifact_type: str,
        context: Dict[str, Any],
        criteria: Dict[str, float],
    ) -> str:
        """Build stage-specific review prompt."""

        # Stage-specific instructions
        stage_instructions = {
            "architecture": """
ARCHITECTURE REVIEW FOCUS:
- Scalability: Can this handle 10x, 100x growth?
- Security: Are there potential vulnerabilities?
- Maintainability: Will this be easy to modify/extend?
- Performance: Any obvious bottlenecks?
- Cost: Infrastructure/operational cost implications?
- Technology Fit: Does it align with existing stack?
""",
            "design": """
DESIGN REVIEW FOCUS:
- Design Patterns: Are appropriate patterns used correctly?
- Interface Design: Are APIs/interfaces well-defined?
- Extensibility: Can new features be added easily?
- Simplicity: Is the design as simple as possible?
- Consistency: Does it follow existing conventions?
""",
            "analysis": """
ANALYSIS REVIEW FOCUS:
- Completeness: Are all aspects covered?
- Accuracy: Are conclusions correct?
- Edge Cases: Are boundary conditions considered?
- Assumptions: Are assumptions stated and valid?
- Clarity: Is the analysis easy to follow?
""",
            "programming": """
CODE REVIEW FOCUS:
- Correctness: Does the code do what it should?
- Security: Any SQL injection, XSS, or other vulnerabilities?
- Performance: Any inefficient algorithms or queries?
- Readability: Is the code easy to understand?
- Error Handling: Are errors handled gracefully?
- Testing: Is the code testable? Are tests included?
""",
            "testing": """
TEST REVIEW FOCUS:
- Coverage: Are all paths/branches tested?
- Edge Cases: Are boundary conditions tested?
- Assertions: Are assertions meaningful and specific?
- Mocking: Is mocking used appropriately?
- Readability: Are tests easy to understand?
- Performance: Will tests run in reasonable time?
""",
            "infrastructure": """
INFRASTRUCTURE REVIEW FOCUS:
- Reliability: Will this be stable in production?
- Security: Are secrets protected? Access controlled?
- Scalability: Can it handle load increases?
- Cost: Is this cost-efficient?
- Maintainability: Is it easy to operate/monitor?
""",
        }

        # Build criteria section
        criteria_text = "REVIEW CRITERIA (weighted importance):\n"
        for criterion, weight in sorted(criteria.items(), key=lambda x: -x[1]):
            criteria_text += f"- {criterion.replace('_', ' ').title()}: {int(weight * 100)}%\n"

        # Build context section
        context_text = ""
        if context:
            context_text = "\nADDITIONAL CONTEXT:\n"
            for key, value in context.items():
                context_text += f"- {key}: {value}\n"

        prompt = f"""You are an expert reviewer performing a {stage_type.upper()} review.

{stage_instructions.get(stage_type, "")}

{criteria_text}

{context_text}

ARTIFACT TO REVIEW ({artifact_type}):
```
{artifact}
```

INSTRUCTIONS:
1. Analyze the artifact against each review criterion
2. Identify any issues, categorized by severity
3. For each issue, provide specific line references if applicable
4. Suggest fixes for each issue

ISSUE SEVERITY LEVELS:
- CRITICAL: Must be fixed, blocks approval (security vulnerabilities, crashes, data loss)
- MAJOR: Should be fixed, counts toward approval threshold (bugs, performance issues)
- MINOR: Nice to fix, doesn't block approval (code style, minor improvements)
- SUGGESTION: Optional improvement ideas

FORMAT YOUR RESPONSE AS:
For each issue found, use this exact format:

[ISSUE]
SEVERITY: critical|major|minor|suggestion
CATEGORY: security|performance|correctness|maintainability|style|documentation|testing|architecture
TITLE: Brief issue title
DESCRIPTION: Detailed description of the issue
LINE: line_number (or line_start-line_end for ranges)
SUGGESTED_FIX: How to fix this issue
CODE_SNIPPET: Relevant code if applicable
[/ISSUE]

If no issues found, respond with:
[NO_ISSUES]
The artifact passes all review criteria.
[/NO_ISSUES]

End your response with:
[SUMMARY]
Total issues: X (Y critical, Z major, W minor, V suggestions)
Overall assessment: APPROVE|NEEDS_WORK|REJECT
Confidence: X%
[/SUMMARY]
"""
        return prompt

    def _parse_review_response(self, response_text: str) -> List[ParsedIssue]:
        """Parse issues from model response."""
        issues = []

        # Find all issue blocks
        issue_pattern = r'\[ISSUE\](.*?)\[/ISSUE\]'
        matches = re.findall(issue_pattern, response_text, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                issue = self._parse_single_issue(match)
                if issue:
                    issues.append(issue)
            except Exception as e:
                logger.warning(f"Failed to parse issue: {e}")
                continue

        return issues

    def _parse_single_issue(self, issue_text: str) -> Optional[ParsedIssue]:
        """Parse a single issue block."""

        def extract_field(field: str) -> Optional[str]:
            pattern = rf'{field}:\s*(.+?)(?=\n[A-Z_]+:|$)'
            match = re.search(pattern, issue_text, re.IGNORECASE | re.DOTALL)
            return match.group(1).strip() if match else None

        severity_str = extract_field("SEVERITY")
        category_str = extract_field("CATEGORY")
        title = extract_field("TITLE")
        description = extract_field("DESCRIPTION")

        if not all([severity_str, category_str, title, description]):
            return None

        # Parse severity
        try:
            severity = IssueSeverity(severity_str.lower())
        except ValueError:
            severity = IssueSeverity.MINOR

        # Parse category
        try:
            category = IssueCategory(category_str.lower())
        except ValueError:
            category = IssueCategory.CORRECTNESS

        # Parse line numbers
        line_str = extract_field("LINE")
        line_start = None
        line_end = None
        if line_str:
            if "-" in line_str:
                parts = line_str.split("-")
                try:
                    line_start = int(parts[0].strip())
                    line_end = int(parts[1].strip())
                except ValueError:
                    pass
            else:
                try:
                    line_start = int(line_str.strip())
                except ValueError:
                    pass

        return ParsedIssue(
            severity=severity,
            category=category,
            title=title,
            description=description,
            suggested_fix=extract_field("SUGGESTED_FIX"),
            line_start=line_start,
            line_end=line_end,
            code_snippet=extract_field("CODE_SNIPPET"),
        )

    # ========================================================================
    # CONSENSUS & CONSOLIDATION
    # ========================================================================

    def _consolidate_issues(
        self,
        all_issues: List[ParsedIssue],
        num_models: int,
    ) -> List[ConsolidatedIssue]:
        """
        Consolidate issues found by multiple models.
        Calculate consensus score for each unique issue.
        """
        if not all_issues:
            return []

        # Group similar issues
        unique_issues: Dict[str, Dict[str, Any]] = {}

        for issue in all_issues:
            # Create a similarity key based on title + category
            key = f"{issue.category.value}:{issue.title[:50].lower()}"

            if key in unique_issues:
                unique_issues[key]["confirmed_by"].append(issue.model_name or "unknown")
            else:
                unique_issues[key] = {
                    "issue": issue,
                    "confirmed_by": [issue.model_name or "unknown"],
                }

        # Create consolidated issues
        result = []
        for data in unique_issues.values():
            issue = data["issue"]
            confirmed_by = list(set(data["confirmed_by"]))  # Dedupe
            consensus_score = len(confirmed_by) / num_models if num_models > 0 else 0

            result.append(ConsolidatedIssue(
                severity=issue.severity,
                category=issue.category,
                title=issue.title,
                description=issue.description,
                suggested_fix=issue.suggested_fix,
                line_start=issue.line_start,
                line_end=issue.line_end,
                code_snippet=issue.code_snippet,
                confirmed_by_models=confirmed_by,
                consensus_score=consensus_score,
            ))

        # Sort by severity, then consensus
        severity_order = {"critical": 0, "major": 1, "minor": 2, "suggestion": 3}
        result.sort(key=lambda x: (
            severity_order.get(x.severity.value, 4),
            -x.consensus_score,
        ))

        return result

    def _calculate_consensus(
        self,
        reviews: List[ModelReviewResult],
        issues: List[ConsolidatedIssue],
    ) -> float:
        """Calculate overall consensus level across models."""
        if not reviews:
            return 0.0

        # Factor 1: Agreement on number of issues
        issue_counts = [len(r.issues) for r in reviews]
        if issue_counts:
            avg_issues = sum(issue_counts) / len(issue_counts)
            if avg_issues > 0:
                variance = sum((c - avg_issues) ** 2 for c in issue_counts) / len(issue_counts)
                std_dev = variance ** 0.5
                # Lower std_dev = higher consensus
                count_consensus = max(0, 1 - (std_dev / (avg_issues + 1)))
            else:
                count_consensus = 1.0
        else:
            count_consensus = 1.0

        # Factor 2: Average issue consensus scores
        if issues:
            avg_issue_consensus = sum(i.consensus_score for i in issues) / len(issues)
        else:
            avg_issue_consensus = 1.0  # No issues = full consensus

        # Combined consensus (as percentage)
        return (count_consensus * 0.4 + avg_issue_consensus * 0.6) * 100

    # ========================================================================
    # THRESHOLD EVALUATION & DECISION
    # ========================================================================

    def _evaluate_threshold(
        self,
        issues: List[ConsolidatedIssue],
        config: StageCouncilConfig,
    ) -> bool:
        """
        Evaluate if issues exceed threshold (triggers second round).

        Only counts issues with consensus >= 0.5 (at least half the models agree).
        """
        critical_count = 0
        major_count = 0

        for issue in issues:
            # Only count issues with sufficient consensus
            if issue.consensus_score < 0.5:
                continue

            if issue.severity == IssueSeverity.CRITICAL:
                critical_count += 1
            elif issue.severity == IssueSeverity.MAJOR:
                major_count += 1

        exceeds_critical = critical_count > config.critical_threshold
        exceeds_major = major_count > config.major_threshold

        return exceeds_critical or exceeds_major

    def _make_decision(
        self,
        issues: List[ConsolidatedIssue],
        consensus: float,
        config: StageCouncilConfig,
    ) -> ReviewDecision:
        """Make final decision based on issues and consensus."""

        # Count confirmed issues (consensus >= 0.5)
        confirmed_critical = sum(
            1 for i in issues
            if i.severity == IssueSeverity.CRITICAL and i.consensus_score >= 0.5
        )
        confirmed_major = sum(
            1 for i in issues
            if i.severity == IssueSeverity.MAJOR and i.consensus_score >= 0.5
        )

        # Check thresholds
        if confirmed_critical > config.critical_threshold:
            return ReviewDecision.REJECTED

        if confirmed_major > config.major_threshold:
            return ReviewDecision.NEEDS_REVISION

        if consensus < config.consensus_minimum * 100:
            return ReviewDecision.NEEDS_REVISION

        return ReviewDecision.APPROVED

    # ========================================================================
    # IMPROVEMENT (SECOND ROUND)
    # ========================================================================

    async def _improve_artifact(
        self,
        artifact: str,
        artifact_type: str,
        issues: List[ConsolidatedIssue],
        config: StageCouncilConfig,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Improve artifact based on identified issues."""

        # Filter to critical and major issues only
        important_issues = [
            i for i in issues
            if i.severity in (IssueSeverity.CRITICAL, IssueSeverity.MAJOR)
        ]

        if not important_issues:
            return artifact

        # Build improvement prompt
        prompt = self._build_improvement_prompt(
            artifact=artifact,
            artifact_type=artifact_type,
            issues=important_issues,
            context=context,
        )

        if self.llm_provider:
            model = config.second_round_model or config.primary_models[0]
            provider = get_provider_for_model(model)
            response = await self.llm_provider(provider, model, prompt, 8000)
            improved = self._extract_improved_artifact(response.get("text", ""))
        else:
            # Mock improvement for testing
            improved = artifact + "\n# Improvements applied"

        return improved

    def _build_improvement_prompt(
        self,
        artifact: str,
        artifact_type: str,
        issues: List[ConsolidatedIssue],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Build prompt for artifact improvement."""

        issues_text = ""
        for i, issue in enumerate(issues, 1):
            issues_text += f"""
Issue #{i}:
- Severity: {issue.severity.value.upper()}
- Category: {issue.category.value}
- Title: {issue.title}
- Description: {issue.description}
- Suggested Fix: {issue.suggested_fix or 'Not provided'}
- Line Reference: {issue.line_start or 'N/A'}
"""

        context_text = ""
        if context:
            context_text = "\nCONTEXT:\n"
            for key, value in context.items():
                context_text += f"- {key}: {value}\n"

        return f"""You are an expert {artifact_type} improver. Your task is to fix the identified issues while maintaining the artifact's original purpose and style.

ORIGINAL ARTIFACT:
```
{artifact}
```

ISSUES TO FIX:
{issues_text}
{context_text}

INSTRUCTIONS:
1. Address ALL listed issues
2. Maintain the original style and structure where possible
3. Do not introduce new functionality beyond fixing the issues
4. Preserve all existing correct functionality
5. Add comments only where they clarify the fix

IMPORTANT:
- Return the COMPLETE improved artifact
- Include ALL original content that should be preserved
- Make minimal changes - only what's needed to fix the issues

OUTPUT FORMAT:
[IMPROVED_ARTIFACT]
```
Your improved artifact here
```
[/IMPROVED_ARTIFACT]

[CHANGES_MADE]
- Brief description of each change made
[/CHANGES_MADE]
"""

    def _extract_improved_artifact(self, response: str) -> str:
        """Extract improved artifact from model response."""

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

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content for caching."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _generate_mock_review(self, model_name: str) -> str:
        """Generate mock review response for testing."""
        return f"""[ISSUE]
SEVERITY: minor
CATEGORY: style
TITLE: Code formatting inconsistency
DESCRIPTION: Some lines exceed the recommended line length
LINE: 15
SUGGESTED_FIX: Break long lines into multiple lines
CODE_SNIPPET: def very_long_function_name(parameter1, parameter2, parameter3):
[/ISSUE]

[SUMMARY]
Total issues: 1 (0 critical, 0 major, 1 minor, 0 suggestions)
Overall assessment: APPROVE
Confidence: 85%
[/SUMMARY]
"""

    def clear_cache(self) -> None:
        """Clear the review cache."""
        self._review_cache.clear()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_stage_review_service(
    llm_provider: Optional[Callable[[str, str, str, int], Awaitable[Dict]]] = None,
) -> StageReviewService:
    """
    Factory function to create a StageReviewService.

    Args:
        llm_provider: Optional async function for LLM calls

    Returns:
        Configured StageReviewService
    """
    return StageReviewService(llm_provider=llm_provider)
