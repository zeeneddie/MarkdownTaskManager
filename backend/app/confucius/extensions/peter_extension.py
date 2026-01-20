"""
Peter Extension - Product Owner Specialist.

Wraps product management services for Confucius orchestrator integration.
Handles requirements, user stories, backlog management, and prioritization.

Week 158: Fixed to use local Ollama LLM instead of returning empty stubs.
"""

from typing import Dict, Any, Optional, List
import logging
import json

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


class PeterExtension(BaseAgentExtension):
    """
    Peter - Product Owner Agent Extension.

    Capabilities:
    - Requirements gathering and analysis
    - User story generation
    - Backlog management
    - Feature prioritization
    - Stakeholder communication
    - Acceptance criteria definition

    Position in workflow: First agent in project initiation.
    """

    def __init__(self):
        """Initialize Peter extension."""
        super().__init__(
            ExtensionMetadata(
                name="Peter",
                description="Product Owner - Requirements, stories, prioritization",
                capabilities=[
                    "requirements_analysis",
                    "user_story_generation",
                    "backlog_management",
                    "feature_prioritization",
                    "acceptance_criteria",
                    "stakeholder_analysis",
                    "constitution_generation",
                    "epic_creation",
                ],
                domains=[
                    "product",
                    "requirements",
                    "stories",
                    "backlog",
                    "prioritization",
                    "features",
                    "epics",
                ],
                priority=8,  # High - starts workflows
                parallel_safe=True,
                timeout_seconds=90,
                version="1.0.0",
            )
        )

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for Peter product work."""
        modified = context.copy()

        # Determine product activity
        activity = self._determine_activity(task)
        modified["peter_activity"] = activity

        # Set prioritization method if not specified
        if "prioritization_method" not in modified:
            modified["prioritization_method"] = "MoSCoW"

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute product owner activities."""
        activity = context.get("peter_activity", "general")

        try:
            if activity == "requirements":
                result = await self._analyze_requirements(context)
            elif activity == "stories":
                result = await self._generate_stories(context)
            elif activity == "backlog":
                result = await self._manage_backlog(context)
            elif activity == "prioritization":
                result = await self._prioritize_features(context)
            elif activity == "constitution":
                result = await self._generate_constitution(context)
            else:
                result = await self._general_product_work(task, context)

            self.update_partial({
                "product_work_complete": True,
                "activity": activity,
            })

            return {
                "success": True,
                "activity": activity,
                "result": result,
                "agent": "Peter",
            }

        except Exception as e:
            logger.error(f"Peter product work failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "activity": activity,
                "partial_result": self.get_partial(),
            }

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse Peter output into structured format."""
        if not raw_output.get("success"):
            return raw_output

        result = raw_output.get("result", {})
        parsed = raw_output.copy()

        parsed["requirements"] = result.get("requirements", [])
        parsed["user_stories"] = result.get("user_stories", [])
        parsed["backlog_items"] = result.get("backlog_items", [])
        parsed["priorities"] = result.get("priorities", {})

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Post-processing: Record product artifacts."""
        if executed_output.get("success"):
            req_count = len(executed_output.get("requirements", []))
            story_count = len(executed_output.get("user_stories", []))
            backlog_count = len(executed_output.get("backlog_items", []))

            executed_output["peter_summary"] = {
                "requirements_count": req_count,
                "stories_count": story_count,
                "backlog_items_count": backlog_count,
                "activity": executed_output.get("activity"),
                "entry_id": entry_id,
            }

            logger.info(
                f"Peter completed: {req_count} requirements, "
                f"{story_count} stories, {backlog_count} backlog items"
            )

        return executed_output

    def _determine_activity(self, task: str) -> str:
        """Determine product activity from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["requirement", "need", "want"]):
            return "requirements"
        elif any(kw in task_lower for kw in ["story", "user story", "as a"]):
            return "stories"
        elif any(kw in task_lower for kw in ["backlog", "items", "manage"]):
            return "backlog"
        elif any(kw in task_lower for kw in ["priorit", "rank", "order", "moscow"]):
            return "prioritization"
        elif any(kw in task_lower for kw in ["constitution", "vision", "charter"]):
            return "constitution"
        else:
            return "general"

    async def _analyze_requirements(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and document requirements using LLM."""
        code_analysis = context.get("code_analysis", {})
        domains = context.get("domains", [])

        prompt = f"""Analyze the following code context and extract software requirements.

## Code Analysis Context
{json.dumps(code_analysis, indent=2, default=str)[:8000]}

## Business Domains
{json.dumps(domains, indent=2, default=str)[:2000]}

## Task
Extract requirements from this codebase. Identify:
1. Functional requirements (what the system does)
2. Non-functional requirements (performance, security, usability)
3. Technical constraints

## Output Schema
Return JSON:
{{
    "requirements": [
        {{"id": "REQ-001", "title": "...", "description": "...", "type": "functional|non_functional", "priority": "high|medium|low"}}
    ],
    "functional": ["Functional requirement 1", "..."],
    "non_functional": ["Non-functional requirement 1", "..."],
    "constraints": ["Constraint 1", "..."]
}}"""

        result = await self.call_llm(prompt)
        return result if result else {
            "requirements": [],
            "functional": [],
            "non_functional": [],
            "constraints": [],
        }

    async def _generate_stories(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate user stories using LLM."""
        domains = context.get("domains", [])
        code_analysis = context.get("code_analysis", {})

        prompt = f"""Generate user stories from the following code analysis and business domains.

## Business Domains
{json.dumps(domains, indent=2, default=str)[:4000]}

## Code Analysis
{json.dumps(code_analysis, indent=2, default=str)[:6000]}

## Task
Create user stories in the format: "As a [user type], I want [goal] so that [benefit]"
Group stories into epics by business domain.

## Output Schema
Return JSON:
{{
    "epics": [
        {{
            "id": "EPIC-001",
            "title": "...",
            "description": "...",
            "domain": "...",
            "stories": ["US-001", "US-002"]
        }}
    ],
    "user_stories": [
        {{
            "id": "US-001",
            "title": "As a [user], I want [goal] so that [benefit]",
            "epic_id": "EPIC-001",
            "acceptance_criteria": ["Given...", "When...", "Then..."],
            "estimated_points": 3
        }}
    ],
    "acceptance_criteria": ["AC-1: ...", "AC-2: ..."]
}}"""

        result = await self.call_llm(prompt)
        return result if result else {
            "user_stories": [],
            "epics": [],
            "acceptance_criteria": [],
        }

    async def _manage_backlog(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage product backlog using LLM."""
        stories = context.get("stories", [])
        epics = context.get("epics", [])

        prompt = f"""Organize the following items into a prioritized product backlog.

## Epics
{json.dumps(epics, indent=2, default=str)[:4000]}

## Stories
{json.dumps(stories, indent=2, default=str)[:6000]}

## Task
Create a prioritized backlog with:
1. Items ordered by business value
2. Dependencies identified
3. Sprint readiness assessment

## Output Schema
Return JSON:
{{
    "backlog_items": [
        {{
            "id": "...",
            "title": "...",
            "priority": 1,
            "status": "ready|blocked|needs_refinement",
            "dependencies": [],
            "estimated_points": 3
        }}
    ],
    "total_items": 10,
    "ready_for_sprint": 5
}}"""

        result = await self.call_llm(prompt)
        return result if result else {
            "backlog_items": [],
            "total_items": 0,
            "ready_for_sprint": 0,
        }

    async def _prioritize_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prioritize features using LLM and specified method."""
        method = context.get("prioritization_method", "MoSCoW")
        features = context.get("features", [])
        stories = context.get("stories", [])

        prompt = f"""Prioritize the following features using the {method} method.

## Features/Stories
{json.dumps(features + stories, indent=2, default=str)[:8000]}

## Task
Apply {method} prioritization:
- Must Have: Critical for MVP
- Should Have: Important but not critical
- Could Have: Nice to have
- Won't Have: Out of scope for now

## Output Schema
Return JSON:
{{
    "priorities": {{
        "must_have": ["Feature 1", "Feature 2"],
        "should_have": ["Feature 3"],
        "could_have": ["Feature 4"],
        "wont_have": ["Feature 5"]
    }},
    "method": "{method}",
    "ranked_items": [
        {{"id": "...", "title": "...", "priority": "must_have", "rank": 1, "rationale": "..."}}
    ]
}}"""

        result = await self.call_llm(prompt)
        return result if result else {
            "priorities": {},
            "method": method,
            "ranked_items": [],
        }

    async def _generate_constitution(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate project constitution using LLM."""
        project_info = context.get("project_info", {})
        domains = context.get("domains", [])

        prompt = f"""Generate a project constitution based on the following context.

## Project Information
{json.dumps(project_info, indent=2, default=str)[:4000]}

## Business Domains
{json.dumps(domains, indent=2, default=str)[:4000]}

## Task
Create a project constitution defining:
1. Vision: The aspirational future state
2. Mission: How we'll achieve the vision
3. Objectives: Measurable goals
4. Success criteria: How we'll know we succeeded
5. Stakeholders: Who is involved

## Output Schema
Return JSON:
{{
    "constitution": {{
        "vision": "...",
        "mission": "...",
        "objectives": ["Objective 1", "Objective 2"],
        "success_criteria": ["Criterion 1", "Criterion 2"],
        "stakeholders": [
            {{"role": "...", "responsibilities": "...", "interest": "high|medium|low"}}
        ]
    }}
}}"""

        result = await self.call_llm(prompt)
        return result if result else {
            "constitution": {
                "vision": "",
                "mission": "",
                "objectives": [],
                "success_criteria": [],
                "stakeholders": [],
            },
        }

    async def _general_product_work(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute general product owner work using LLM."""
        prompt = f"""As a Product Owner, analyze and respond to the following task.

## Task
{task}

## Context
{json.dumps(context, indent=2, default=str)[:8000]}

## Output Schema
Return JSON with relevant product artifacts:
{{
    "requirements": [],
    "user_stories": [],
    "backlog_items": [],
    "recommendations": [],
    "analysis": "..."
}}"""

        result = await self.call_llm(prompt)
        return result if result else {
            "requirements": [],
            "user_stories": [],
            "backlog_items": [],
        }
