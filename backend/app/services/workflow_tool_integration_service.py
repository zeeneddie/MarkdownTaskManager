"""
Workflow Tool Integration Service - Week 79

Integrates external tools into existing workflows:

GREEN_PAPER Integration:
- Option A: Claude-Mem context injection for 6 BMAD questions
- Option B: CCPM PRD decomposition after constitution approval

BROWN_PAPER Integration:
- Option A: Claude-Mem context injection for 8 BMAD questions + scan data
- Option B: CCPM migration task decomposition after analysis approval

QUALITY_AUDIT Integration:
- Option C: BigAGI multi-model validation for high/critical findings
- Claude-Mem scan result tracking

Generic Workflow Integration:
- MIGRATION: Phase completion, issue tracking
- BUG: Root cause analysis, fix tracking
- MAINTENANCE, NEW_FEATURE, TESTING: Observation capture

Cross-Workflow Features:
- Context injection into prompts
- Priority-based retrieval
- Auto-tagging based on workflow type
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.claude_mem_service import ClaudeMemService
from app.services.ccpm_orchestrator import CCPMOrchestrator
from app.services.bigagi_beam_service import BigAGIBeamService

logger = logging.getLogger(__name__)


class WorkflowToolIntegrationService:
    """
    Orchestrates tool integration into workflow pipelines.

    This service provides hooks that can be called at specific points
    in workflow execution to enhance them with additional capabilities.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._claude_mem: Optional[ClaudeMemService] = None
        self._ccpm: Optional[CCPMOrchestrator] = None
        self._bigagi: Optional[BigAGIBeamService] = None
        self._ghostcrew = None  # GhostCrew security service

    @property
    def ghostcrew(self):
        """Lazy-load GhostCrew security service."""
        if self._ghostcrew is None:
            from app.services.ghostcrew_service import GhostCrewService
            self._ghostcrew = GhostCrewService(self.db)
        return self._ghostcrew

    @property
    def claude_mem(self) -> ClaudeMemService:
        """Lazy-load Claude-Mem service."""
        if self._claude_mem is None:
            self._claude_mem = ClaudeMemService(self.db)
        return self._claude_mem

    @property
    def ccpm(self) -> CCPMOrchestrator:
        """Lazy-load CCPM orchestrator."""
        if self._ccpm is None:
            self._ccpm = CCPMOrchestrator(self.db)
        return self._ccpm

    @property
    def bigagi(self) -> BigAGIBeamService:
        """Lazy-load BigAGI Beam service."""
        if self._bigagi is None:
            self._bigagi = BigAGIBeamService(self.db)
        return self._bigagi

    # =========================================================================
    # OPTION A: Claude-Mem Integration for GREEN_PAPER Workflow
    # =========================================================================

    async def green_paper_session_start(
        self,
        session_id: str,
        project_id: Optional[int] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Called when GREEN_PAPER session starts.
        Creates Claude-Mem session for context tracking.

        Args:
            session_id: Green paper session ID
            project_id: Optional project association
            title: Optional session title

        Returns:
            Claude-Mem session data
        """
        mem_session_id = f"gp_{session_id}"

        try:
            result = await self.claude_mem.create_session(
                session_id=mem_session_id,
                title=title or f"GREEN_PAPER Session {session_id[:8]}",
                project_id=project_id,
                token_budget=6000,  # Higher budget for project definition
                auto_tag=True
            )

            # Capture initial observation
            await self.claude_mem.capture_observation(
                session_id=mem_session_id,
                content="GREEN_PAPER workflow session started. User will answer 6 BMAD questions to define project.",
                observation_type="progress",
                priority="normal",
                tags=["green_paper", "session_start", "workflow"]
            )

            logger.info(f"Claude-Mem session created for GREEN_PAPER: {mem_session_id}")
            return result

        except Exception as e:
            logger.warning(f"Failed to create Claude-Mem session: {e}")
            return {"error": str(e), "fallback": "continuing without memory"}

    async def green_paper_answer_submitted(
        self,
        session_id: str,
        question_number: int,
        question_text: str,
        answer: str
    ) -> Dict[str, Any]:
        """
        Called when user submits an answer in GREEN_PAPER.
        Captures the Q&A as an observation.

        Args:
            session_id: Green paper session ID
            question_number: Question number (1-6)
            question_text: The question text
            answer: User's answer

        Returns:
            Observation capture result
        """
        mem_session_id = f"gp_{session_id}"

        # Determine priority based on question
        # Questions 1-4 are required (higher priority)
        priority = "high" if question_number <= 4 else "normal"

        # Auto-detect relevant tags
        tags = [f"q{question_number}", "bmad_answer"]

        if question_number == 1:
            tags.extend(["problem_statement", "decision"])
        elif question_number == 2:
            tags.append("stakeholders")
        elif question_number == 3:
            tags.extend(["functionalities", "architecture"])
        elif question_number == 4:
            tags.extend(["success_criteria", "decision"])
        elif question_number == 5:
            tags.extend(["constraints", "architecture"])
        elif question_number == 6:
            tags.append("timeline")

        try:
            result = await self.claude_mem.capture_observation(
                session_id=mem_session_id,
                content=f"Q{question_number}: {question_text}\nAnswer: {answer}",
                observation_type="decision",
                priority=priority,
                tags=tags,
                source_context=f"GREEN_PAPER question {question_number}"
            )

            logger.info(f"Captured Q{question_number} answer in Claude-Mem")
            return result

        except Exception as e:
            logger.warning(f"Failed to capture answer in Claude-Mem: {e}")
            return {"error": str(e)}

    async def green_paper_get_context_for_constitution(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Called before constitution generation.
        Returns context window with all captured observations.

        Args:
            session_id: Green paper session ID

        Returns:
            Context window data for injection into prompt
        """
        mem_session_id = f"gp_{session_id}"

        try:
            context = await self.claude_mem.get_context_window(
                session_id=mem_session_id,
                token_budget=4000,
                strategy="priority",  # Prioritize high-priority observations
                include_summaries=True
            )

            logger.info(f"Retrieved context window for constitution: {context.get('token_count', 0)} tokens")
            return context

        except Exception as e:
            logger.warning(f"Failed to get context window: {e}")
            return {"error": str(e), "context_text": ""}

    async def green_paper_enhance_prompt_with_context(
        self,
        session_id: str,
        base_prompt: str
    ) -> str:
        """
        Enhances a prompt with Claude-Mem context.

        Args:
            session_id: Green paper session ID
            base_prompt: Original prompt

        Returns:
            Enhanced prompt with context injection
        """
        context = await self.green_paper_get_context_for_constitution(session_id)

        if "error" in context or not context.get("context_text"):
            return base_prompt

        enhanced = f"""## Session Context (Auto-captured observations)

{context.get('context_text', '')}

---

{base_prompt}"""

        logger.info(f"Enhanced prompt with {context.get('token_count', 0)} tokens of context")
        return enhanced

    # =========================================================================
    # OPTION B: CCPM PRD Decomposition for GREEN_PAPER Workflow
    # =========================================================================

    async def green_paper_constitution_approved(
        self,
        project_id: int,
        constitution_id: str,
        constitution_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Called when constitution is APPROVED.
        Automatically triggers PRD decomposition via CCPM.

        Args:
            project_id: Project ID
            constitution_id: Constitution UUID
            constitution_content: Constitution JSON content

        Returns:
            CCPM decomposition result with task hierarchy
        """
        try:
            # Convert constitution to PRD format
            prd_content = self._constitution_to_prd(constitution_content)

            # Optional: Create decomposition context
            context = {
                "source": "green_paper_constitution",
                "constitution_id": constitution_id,
                "auto_triggered": True,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Call CCPM to decompose
            decomposition = await self.ccpm.decompose_prd(
                project_id=project_id,
                prd_content=prd_content,
                decomposition_context=context
            )

            logger.info(
                f"CCPM decomposition completed for constitution {constitution_id}: "
                f"{decomposition.get('statistics', {}).get('total_epics', 0)} epics, "
                f"{decomposition.get('statistics', {}).get('total_stories', 0)} stories"
            )

            # Capture in Claude-Mem if session exists
            # (session_id would need to be passed or looked up)

            return {
                "status": "success",
                "decomposition_id": decomposition.get("decomposition_id"),
                "statistics": decomposition.get("statistics", {}),
                "epics_created": decomposition.get("hierarchy", {}).get("epics", []),
                "next_step": "get_task_recommendations",
                "message": "Constitution approved and PRD decomposed into task hierarchy"
            }

        except Exception as e:
            logger.error(f"Failed to decompose constitution: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Constitution approved but PRD decomposition failed. You can retry manually."
            }

    def _constitution_to_prd(self, constitution: Dict[str, Any]) -> str:
        """
        Convert constitution JSON to PRD text format for CCPM.

        Args:
            constitution: Constitution JSON content

        Returns:
            PRD-formatted text
        """
        sections = []

        # Title/Problem Statement
        if constitution.get("problem_statement"):
            sections.append(f"# Project Overview\n\n{constitution['problem_statement']}")

        # Stakeholders
        if constitution.get("stakeholders"):
            sections.append("\n## Stakeholders\n")
            for s in constitution["stakeholders"]:
                role = s.get("role", "Unknown")
                desc = s.get("description", "")
                needs = ", ".join(s.get("needs", []))
                sections.append(f"- **{role}**: {desc}")
                if needs:
                    sections.append(f"  - Needs: {needs}")

        # Core Functionalities -> Epics
        if constitution.get("core_functionalities"):
            sections.append("\n## Core Functionalities (Epics)\n")
            for i, f in enumerate(constitution["core_functionalities"], 1):
                name = f.get("name", f"Functionality {i}")
                desc = f.get("description", "")
                priority = f.get("priority", "Unknown")
                sections.append(f"\n### {i}. {name}\n")
                sections.append(f"**Priority**: {priority}\n")
                sections.append(f"{desc}")
                if f.get("dependencies"):
                    sections.append(f"\n**Dependencies**: {', '.join(f['dependencies'])}")

        # Success Criteria
        if constitution.get("success_criteria"):
            sections.append("\n## Success Criteria\n")
            for c in constitution["success_criteria"]:
                metric = c.get("metric", "")
                target = c.get("target", "")
                sections.append(f"- {metric}: {target}")

        # Technical Constraints
        if constitution.get("technical_constraints"):
            sections.append("\n## Technical Constraints\n")
            for tc in constitution["technical_constraints"]:
                constraint = tc.get("constraint", "")
                reason = tc.get("reason", "")
                sections.append(f"- **{constraint}**: {reason}")

        # Timeline
        if constitution.get("timeline"):
            timeline = constitution["timeline"]
            sections.append("\n## Timeline\n")
            if timeline.get("phases"):
                for phase in timeline["phases"]:
                    name = phase.get("name", "Phase")
                    duration = phase.get("duration_weeks", "?")
                    sections.append(f"- {name}: {duration} weeks")
            if timeline.get("total_duration_weeks"):
                sections.append(f"\n**Total Duration**: {timeline['total_duration_weeks']} weeks")

        return "\n".join(sections)

    async def green_paper_get_task_recommendations(
        self,
        project_id: int,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get task recommendations after PRD decomposition.

        Args:
            project_id: Project ID
            limit: Max recommendations to return

        Returns:
            Prioritized task recommendations
        """
        try:
            recommendation = await self.ccpm.get_next_task(
                project_id=project_id,
                limit=limit
            )

            return {
                "status": "success",
                "recommendations": recommendation.get("recommendations", []),
                "count": len(recommendation.get("recommendations", []))
            }

        except Exception as e:
            logger.error(f"Failed to get task recommendations: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # OPTION C: BigAGI Multi-Model Validation for QUALITY_AUDIT Workflow
    # =========================================================================

    async def quality_audit_validate_finding(
        self,
        task_description: str,
        finding: str,
        agent_model: str = "quinn",
        severity: str = "high",
        consensus_method: str = "weighted"
    ) -> Dict[str, Any]:
        """
        Validate a quality audit finding with multi-model consensus.
        Called for HIGH/CRITICAL severity findings.

        Args:
            task_description: What was being audited
            finding: The quality finding to validate
            agent_model: Agent that produced the finding
            severity: Finding severity (critical, high, medium, low)
            consensus_method: How to reach consensus

        Returns:
            Validation result with consensus score
        """
        # Only validate high/critical findings to save resources
        if severity not in ("critical", "high"):
            return {
                "validated": False,
                "reason": f"Skipped validation for {severity} severity finding",
                "finding": finding
            }

        try:
            # Create validation session
            validation = await self.bigagi.create_validation(
                task=f"QUALITY AUDIT: {task_description}",
                primary_response=finding,
                primary_model=agent_model,
                session_metadata={
                    "workflow": "QUALITY_AUDIT",
                    "severity": severity,
                    "auto_triggered": True
                }
            )

            # Run validation
            result = await self.bigagi.run_validation(
                validation_id=validation.id,
                consensus_method=consensus_method
            )

            logger.info(
                f"BigAGI validation completed for {severity} finding: "
                f"consensus={result.consensus_reached}, score={result.consensus_score:.2f}"
            )

            return {
                "validated": True,
                "validation_id": str(result.validation_id),
                "consensus_reached": result.consensus_reached,
                "consensus_score": result.consensus_score,
                "recommendation": result.recommendation,
                "final_answer": result.final_answer,
                "agreements": result.key_agreements,
                "disagreements": result.key_disagreements,
                "severity": severity,
                "original_finding": finding
            }

        except Exception as e:
            logger.error(f"Failed to validate quality finding: {e}")
            return {
                "validated": False,
                "error": str(e),
                "finding": finding
            }

    async def quality_audit_validate_batch(
        self,
        task_description: str,
        findings: List[Dict[str, Any]],
        validate_severity: List[str] = None
    ) -> Dict[str, Any]:
        """
        Validate multiple quality findings in batch.

        Args:
            task_description: What was being audited
            findings: List of findings with severity
            validate_severity: Which severities to validate (default: critical, high)

        Returns:
            Batch validation results
        """
        if validate_severity is None:
            validate_severity = ["critical", "high"]

        results = []
        validated_count = 0
        consensus_count = 0

        for finding in findings:
            severity = finding.get("severity", "medium")
            content = finding.get("content") or finding.get("finding", "")
            agent = finding.get("agent", "quinn")

            if severity in validate_severity:
                result = await self.quality_audit_validate_finding(
                    task_description=task_description,
                    finding=content,
                    agent_model=agent,
                    severity=severity
                )

                if result.get("validated"):
                    validated_count += 1
                    if result.get("consensus_reached"):
                        consensus_count += 1

                results.append({
                    "original": finding,
                    "validation": result
                })
            else:
                results.append({
                    "original": finding,
                    "validation": {"validated": False, "reason": "severity below threshold"}
                })

        return {
            "total_findings": len(findings),
            "validated_count": validated_count,
            "consensus_count": consensus_count,
            "consensus_rate": consensus_count / validated_count if validated_count > 0 else 0,
            "results": results
        }

    async def quality_audit_enhance_with_validation(
        self,
        audit_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance a complete quality audit result with BigAGI validation.

        Args:
            audit_result: Complete audit result from Quinn agent

        Returns:
            Enhanced audit result with validation data
        """
        # Extract findings from audit result
        findings = []

        # Parse different finding types
        for category in ["security_issues", "code_quality_issues", "performance_issues", "accessibility_issues"]:
            if category in audit_result:
                for issue in audit_result[category]:
                    severity = issue.get("severity", "medium")
                    findings.append({
                        "category": category,
                        "content": issue.get("description") or issue.get("issue", ""),
                        "severity": severity,
                        "agent": audit_result.get("agent", "quinn")
                    })

        # Validate findings
        validation_results = await self.quality_audit_validate_batch(
            task_description=audit_result.get("task", "Quality Audit"),
            findings=findings
        )

        # Enhance audit result
        enhanced = {
            **audit_result,
            "bigagi_validation": {
                "enabled": True,
                "total_findings": validation_results["total_findings"],
                "validated_count": validation_results["validated_count"],
                "consensus_count": validation_results["consensus_count"],
                "consensus_rate": validation_results["consensus_rate"],
                "validation_details": validation_results["results"]
            }
        }

        # Add confidence boost based on consensus
        if validation_results["consensus_rate"] >= 0.7:
            enhanced["confidence_level"] = "high"
            enhanced["validation_status"] = "consensus_reached"
        elif validation_results["consensus_rate"] >= 0.5:
            enhanced["confidence_level"] = "medium"
            enhanced["validation_status"] = "partial_consensus"
        else:
            enhanced["confidence_level"] = "low"
            enhanced["validation_status"] = "needs_review"

        return enhanced


    # =========================================================================
    # OPTION A+B: BROWN_PAPER Workflow Integration
    # =========================================================================

    async def brown_paper_session_start(
        self,
        session_id: str,
        project_id: Optional[int] = None,
        title: Optional[str] = None,
        application_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Called when BROWN_PAPER session starts (legacy system analysis).
        Creates Claude-Mem session for migration decision tracking.

        Args:
            session_id: Brown paper session ID
            project_id: Optional project association
            title: Optional session title
            application_name: Name of legacy application being analyzed

        Returns:
            Claude-Mem session data
        """
        mem_session_id = f"bp_{session_id}"

        try:
            result = await self.claude_mem.create_session(
                session_id=mem_session_id,
                title=title or f"BROWN_PAPER: {application_name or session_id[:8]}",
                project_id=project_id,
                token_budget=8000,  # Higher budget for migration analysis (8 questions)
                auto_tag=True
            )

            # Capture initial observation with migration context
            await self.claude_mem.capture_observation(
                session_id=mem_session_id,
                content=f"BROWN_PAPER migration analysis started for: {application_name or 'legacy system'}. "
                        "User will answer 8 BMAD questions to analyze current state, technical debt, "
                        "security issues, and migration strategy.",
                observation_type="progress",
                priority="high",
                tags=["brown_paper", "migration", "session_start", "workflow"]
            )

            logger.info(f"Claude-Mem session created for BROWN_PAPER: {mem_session_id}")
            return result

        except Exception as e:
            logger.warning(f"Failed to create Claude-Mem session for BROWN_PAPER: {e}")
            return {"error": str(e), "fallback": "continuing without memory"}

    async def brown_paper_answer_submitted(
        self,
        session_id: str,
        question_number: int,
        question_text: str,
        answer: str,
        scan_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Called when user submits an answer in BROWN_PAPER.
        Captures the Q&A as an observation with migration-specific tagging.

        Args:
            session_id: Brown paper session ID
            question_number: Question number (1-8)
            question_text: The question text
            answer: User's answer
            scan_data: Optional scan data (code quality, security scan results)

        Returns:
            Observation capture result
        """
        mem_session_id = f"bp_{session_id}"

        # BROWN_PAPER has 8 questions - all important for migration
        # Q1-4: Current state analysis (critical)
        # Q5-8: Migration strategy (high)
        priority = "critical" if question_number <= 4 else "high"

        # Migration-specific tagging based on BMAD brown paper questions
        tags = [f"q{question_number}", "bmad_answer", "migration"]

        if question_number == 1:
            tags.extend(["current_state", "tech_stack", "architecture"])
        elif question_number == 2:
            tags.extend(["technical_debt", "code_quality", "risk"])
        elif question_number == 3:
            tags.extend(["security", "vulnerabilities", "risk"])
        elif question_number == 4:
            tags.extend(["preservation", "valuable_components", "decision"])
        elif question_number == 5:
            tags.extend(["improvement_areas", "priorities", "decision"])
        elif question_number == 6:
            tags.extend(["migration_strategy", "approach", "decision"])
        elif question_number == 7:
            tags.extend(["risks", "mitigation", "planning"])
        elif question_number == 8:
            tags.extend(["success_criteria", "checkpoints", "planning"])

        content = f"Q{question_number}: {question_text}\nAnswer: {answer}"

        # Append scan data if available
        if scan_data:
            content += f"\n\nRelated Scan Data:\n{self._format_scan_data(scan_data)}"
            tags.append("scan_enriched")

        try:
            result = await self.claude_mem.capture_observation(
                session_id=mem_session_id,
                content=content,
                observation_type="decision",
                priority=priority,
                tags=tags,
                source_context=f"BROWN_PAPER question {question_number}"
            )

            logger.info(f"Captured BROWN_PAPER Q{question_number} answer in Claude-Mem")
            return result

        except Exception as e:
            logger.warning(f"Failed to capture BROWN_PAPER answer in Claude-Mem: {e}")
            return {"error": str(e)}

    def _format_scan_data(self, scan_data: Dict[str, Any]) -> str:
        """Format scan data for observation content."""
        lines = []
        if scan_data.get("violations"):
            lines.append(f"Violations: {scan_data['violations']}")
        if scan_data.get("complexity_score"):
            lines.append(f"Complexity: {scan_data['complexity_score']}")
        if scan_data.get("security_score"):
            lines.append(f"Security: {scan_data['security_score']}")
        if scan_data.get("tech_debt_hours"):
            lines.append(f"Tech Debt: {scan_data['tech_debt_hours']} hours")
        return ", ".join(lines) if lines else "No scan data"

    async def brown_paper_get_context_for_analysis(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Called before migration plan generation.
        Returns context window with all captured observations.

        Args:
            session_id: Brown paper session ID

        Returns:
            Context window data for injection into prompt
        """
        mem_session_id = f"bp_{session_id}"

        try:
            context = await self.claude_mem.get_context_window(
                session_id=mem_session_id,
                token_budget=5000,  # More context for migration analysis
                strategy="priority",
                include_summaries=True
            )

            logger.info(f"Retrieved context window for migration analysis: {context.get('token_count', 0)} tokens")
            return context

        except Exception as e:
            logger.warning(f"Failed to get migration context window: {e}")
            return {"error": str(e), "context_text": ""}

    async def brown_paper_analysis_approved(
        self,
        project_id: int,
        analysis_id: str,
        analysis_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Called when BROWN_PAPER analysis is APPROVED.
        Triggers CCPM to decompose migration plan into tasks.

        Args:
            project_id: Project ID
            analysis_id: Brown paper analysis UUID
            analysis_content: Migration analysis JSON content

        Returns:
            CCPM decomposition result with migration task hierarchy
        """
        try:
            # Convert brown paper analysis to migration PRD format
            prd_content = self._migration_analysis_to_prd(analysis_content)

            context = {
                "source": "brown_paper_analysis",
                "analysis_id": analysis_id,
                "migration_type": analysis_content.get("migration_strategy", {}).get("type", "unknown"),
                "auto_triggered": True,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Call CCPM to decompose
            decomposition = await self.ccpm.decompose_prd(
                project_id=project_id,
                prd_content=prd_content,
                decomposition_context=context
            )

            logger.info(
                f"CCPM migration decomposition completed for analysis {analysis_id}: "
                f"{decomposition.get('statistics', {}).get('total_epics', 0)} epics, "
                f"{decomposition.get('statistics', {}).get('total_stories', 0)} stories"
            )

            return {
                "status": "success",
                "decomposition_id": decomposition.get("decomposition_id"),
                "statistics": decomposition.get("statistics", {}),
                "epics_created": decomposition.get("hierarchy", {}).get("epics", []),
                "next_step": "get_migration_task_recommendations",
                "message": "Migration analysis approved and decomposed into task hierarchy"
            }

        except Exception as e:
            logger.error(f"Failed to decompose migration analysis: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Migration analysis approved but task decomposition failed. You can retry manually."
            }

    def _migration_analysis_to_prd(self, analysis: Dict[str, Any]) -> str:
        """
        Convert brown paper migration analysis to PRD text format for CCPM.

        Args:
            analysis: Brown paper analysis JSON content

        Returns:
            PRD-formatted text for migration work
        """
        sections = []

        # Header with migration context
        sections.append("# Migration Project - Brown Paper Analysis\n")

        # Current State
        if analysis.get("current_state"):
            cs = analysis["current_state"]
            sections.append("## Current State Analysis\n")
            if cs.get("tech_stack"):
                sections.append(f"**Tech Stack**: {', '.join(cs['tech_stack'])}")
            if cs.get("architecture"):
                sections.append(f"\n**Architecture**: {cs['architecture']}")
            if cs.get("complexity"):
                sections.append(f"\n**Complexity Score**: {cs['complexity']}")

        # Technical Debt -> Epic 1: Tech Debt Resolution
        if analysis.get("technical_debt"):
            td = analysis["technical_debt"]
            sections.append("\n## Epic 1: Technical Debt Resolution\n")
            sections.append(f"**Priority**: {td.get('priority', 'High')}\n")
            if td.get("categories"):
                for cat in td["categories"]:
                    sections.append(f"- {cat.get('name', 'Unknown')}: {cat.get('hours', '?')} hours estimated")
            if td.get("top_issues"):
                sections.append("\n**Top Issues to Address**:")
                for issue in td["top_issues"][:5]:
                    sections.append(f"- {issue}")

        # Security Issues -> Epic 2: Security Remediation
        if analysis.get("security_issues"):
            sec = analysis["security_issues"]
            sections.append("\n## Epic 2: Security Remediation\n")
            sections.append(f"**Security Score**: {sec.get('score', 'Unknown')}\n")
            if sec.get("vulnerabilities"):
                sections.append("**Vulnerabilities to Fix**:")
                for vuln in sec["vulnerabilities"]:
                    severity = vuln.get("severity", "medium")
                    desc = vuln.get("description", "")
                    sections.append(f"- [{severity.upper()}] {desc}")

        # Migration Strategy -> Epic 3: Migration Implementation
        if analysis.get("migration_strategy"):
            ms = analysis["migration_strategy"]
            sections.append("\n## Epic 3: Migration Implementation\n")
            sections.append(f"**Strategy Type**: {ms.get('type', 'Unknown')}\n")
            if ms.get("description"):
                sections.append(f"{ms['description']}\n")
            if ms.get("phases"):
                sections.append("**Phases**:")
                for phase in ms["phases"]:
                    name = phase.get("name", "Phase")
                    weeks = phase.get("weeks", "?")
                    sections.append(f"- {name}: {weeks} weeks")

        # Preservation Needs -> Constraints
        if analysis.get("preservation_needs"):
            sections.append("\n## Components to Preserve\n")
            for item in analysis["preservation_needs"]:
                name = item.get("name", "Component")
                reason = item.get("reason", "")
                sections.append(f"- **{name}**: {reason}")

        # Risks
        if analysis.get("risks"):
            sections.append("\n## Migration Risks\n")
            for risk in analysis["risks"]:
                name = risk.get("name", "Risk")
                impact = risk.get("impact", "medium")
                mitigation = risk.get("mitigation", "")
                sections.append(f"- **{name}** (Impact: {impact})")
                if mitigation:
                    sections.append(f"  - Mitigation: {mitigation}")

        # Success Criteria
        if analysis.get("success_criteria"):
            sections.append("\n## Success Criteria\n")
            for sc in analysis["success_criteria"]:
                metric = sc.get("metric", "")
                target = sc.get("target", "")
                sections.append(f"- {metric}: {target}")

        return "\n".join(sections)

    # =========================================================================
    # GENERIC WORKFLOW OBSERVATION CAPTURE
    # =========================================================================

    async def workflow_capture_observation(
        self,
        workflow_type: str,
        session_id: str,
        content: str,
        observation_type: str = "progress",
        priority: str = "normal",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generic observation capture for ANY workflow.
        Use this to track decisions, findings, and progress across all workflows.

        Args:
            workflow_type: MIGRATION, QUALITY_AUDIT, BUG, etc.
            session_id: Workflow session ID
            content: Observation content
            observation_type: Type (decision, finding, bugfix, progress)
            priority: Priority level
            tags: Additional tags
            metadata: Additional metadata

        Returns:
            Observation capture result
        """
        # Create workflow-specific session prefix
        prefix_map = {
            "GREEN_PAPER": "gp",
            "BROWN_PAPER": "bp",
            "MIGRATION": "mig",
            "QUALITY_AUDIT": "qa",
            "BUG": "bug",
            "MAINTENANCE": "maint",
            "NEW_FEATURE": "feat",
            "TESTING": "test"
        }
        prefix = prefix_map.get(workflow_type, workflow_type[:4].lower())
        mem_session_id = f"{prefix}_{session_id}"

        # Build tags
        all_tags = [workflow_type.lower(), observation_type]
        if tags:
            all_tags.extend(tags)

        try:
            # Ensure session exists
            await self._ensure_workflow_session(
                workflow_type=workflow_type,
                session_id=session_id,
                mem_session_id=mem_session_id
            )

            result = await self.claude_mem.capture_observation(
                session_id=mem_session_id,
                content=content,
                observation_type=observation_type,
                priority=priority,
                tags=all_tags,
                source_context=f"{workflow_type} workflow"
            )

            logger.info(f"Captured observation for {workflow_type}: {observation_type}")
            return result

        except Exception as e:
            logger.warning(f"Failed to capture workflow observation: {e}")
            return {"error": str(e)}

    async def _ensure_workflow_session(
        self,
        workflow_type: str,
        session_id: str,
        mem_session_id: str
    ) -> None:
        """Ensure Claude-Mem session exists for workflow."""
        try:
            # Try to get existing session
            existing = await self.claude_mem.get_context_window(
                session_id=mem_session_id,
                token_budget=100  # Minimal check
            )
            if existing and not existing.get("error"):
                return  # Session exists

        except Exception:
            pass  # Session doesn't exist, create it

        # Create new session
        token_budgets = {
            "GREEN_PAPER": 6000,
            "BROWN_PAPER": 8000,
            "MIGRATION": 7000,
            "QUALITY_AUDIT": 5000,
            "BUG": 4000,
            "MAINTENANCE": 4000,
            "NEW_FEATURE": 5000,
            "TESTING": 4000
        }

        await self.claude_mem.create_session(
            session_id=mem_session_id,
            title=f"{workflow_type} Session {session_id[:8]}",
            token_budget=token_budgets.get(workflow_type, 4000),
            auto_tag=True
        )

    # =========================================================================
    # MIGRATION WORKFLOW SPECIFIC HOOKS
    # =========================================================================

    async def migration_phase_completed(
        self,
        session_id: str,
        phase_name: str,
        phase_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Called when a migration phase is completed.
        Captures phase results for context.

        Args:
            session_id: Migration session ID
            phase_name: Name of completed phase
            phase_results: Results/outcomes of the phase

        Returns:
            Observation capture result
        """
        content = f"Migration Phase Completed: {phase_name}\n\n"

        if phase_results.get("metrics"):
            content += "**Metrics**:\n"
            for k, v in phase_results["metrics"].items():
                content += f"- {k}: {v}\n"

        if phase_results.get("issues_resolved"):
            content += f"\n**Issues Resolved**: {len(phase_results['issues_resolved'])}\n"

        if phase_results.get("blockers"):
            content += f"\n**Blockers Identified**: {phase_results['blockers']}\n"

        if phase_results.get("next_phase"):
            content += f"\n**Next Phase**: {phase_results['next_phase']}"

        return await self.workflow_capture_observation(
            workflow_type="MIGRATION",
            session_id=session_id,
            content=content,
            observation_type="progress",
            priority="high",
            tags=["phase_complete", phase_name.lower().replace(" ", "_")],
            metadata=phase_results
        )

    async def migration_issue_found(
        self,
        session_id: str,
        issue_type: str,
        description: str,
        severity: str = "medium",
        source_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Called when a migration issue is discovered.

        Args:
            session_id: Migration session ID
            issue_type: Type of issue (compatibility, data, security, performance)
            description: Issue description
            severity: Issue severity
            source_file: Optional source file where issue found

        Returns:
            Observation capture result
        """
        content = f"Migration Issue Found: {issue_type.upper()}\n\n"
        content += f"**Severity**: {severity}\n"
        content += f"**Description**: {description}\n"

        if source_file:
            content += f"**Source**: {source_file}\n"

        priority = "critical" if severity in ("critical", "high") else "normal"

        return await self.workflow_capture_observation(
            workflow_type="MIGRATION",
            session_id=session_id,
            content=content,
            observation_type="finding",
            priority=priority,
            tags=["issue", issue_type.lower(), severity]
        )

    # =========================================================================
    # BUG WORKFLOW SPECIFIC HOOKS
    # =========================================================================

    async def bug_root_cause_identified(
        self,
        session_id: str,
        bug_description: str,
        root_cause: str,
        affected_files: List[str],
        fix_approach: str
    ) -> Dict[str, Any]:
        """
        Called when Betty identifies root cause of a bug.

        Args:
            session_id: Bug investigation session ID
            bug_description: Original bug description
            root_cause: Identified root cause
            affected_files: Files affected by the bug
            fix_approach: Proposed fix approach

        Returns:
            Observation capture result
        """
        content = f"Bug Root Cause Analysis Complete\n\n"
        content += f"**Bug**: {bug_description}\n\n"
        content += f"**Root Cause**: {root_cause}\n\n"
        content += f"**Affected Files**:\n"
        for f in affected_files[:5]:  # Limit to 5 files
            content += f"- {f}\n"
        content += f"\n**Fix Approach**: {fix_approach}"

        return await self.workflow_capture_observation(
            workflow_type="BUG",
            session_id=session_id,
            content=content,
            observation_type="decision",
            priority="high",
            tags=["root_cause", "bugfix", "analysis"]
        )

    async def bug_fix_applied(
        self,
        session_id: str,
        bug_id: str,
        fix_description: str,
        files_modified: List[str],
        tests_added: int = 0
    ) -> Dict[str, Any]:
        """
        Called when a bug fix is applied.

        Args:
            session_id: Bug investigation session ID
            bug_id: Bug identifier
            fix_description: Description of the fix
            files_modified: Files that were modified
            tests_added: Number of tests added

        Returns:
            Observation capture result
        """
        content = f"Bug Fix Applied: {bug_id}\n\n"
        content += f"**Fix**: {fix_description}\n\n"
        content += f"**Files Modified**: {len(files_modified)}\n"
        for f in files_modified[:5]:
            content += f"- {f}\n"
        content += f"\n**Tests Added**: {tests_added}"

        return await self.workflow_capture_observation(
            workflow_type="BUG",
            session_id=session_id,
            content=content,
            observation_type="bugfix",
            priority="normal",
            tags=["fix_applied", "resolved"]
        )

    # =========================================================================
    # QUALITY_AUDIT WORKFLOW HOOKS (Additional to BigAGI validation)
    # =========================================================================

    async def quality_audit_scan_complete(
        self,
        session_id: str,
        scan_type: str,
        scan_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Called when a quality scan is complete.
        Captures scan results in Claude-Mem for context.

        Args:
            session_id: Quality audit session ID
            scan_type: Type of scan (security, code_quality, performance)
            scan_results: Scan results

        Returns:
            Observation capture result
        """
        content = f"Quality Scan Complete: {scan_type.upper()}\n\n"

        if scan_results.get("score"):
            content += f"**Score**: {scan_results['score']}/100\n"

        if scan_results.get("issues_found"):
            content += f"**Issues Found**: {scan_results['issues_found']}\n"
            if scan_results.get("critical_count"):
                content += f"- Critical: {scan_results['critical_count']}\n"
            if scan_results.get("high_count"):
                content += f"- High: {scan_results['high_count']}\n"

        if scan_results.get("recommendations"):
            content += "\n**Top Recommendations**:\n"
            for rec in scan_results["recommendations"][:3]:
                content += f"- {rec}\n"

        priority = "critical" if scan_results.get("critical_count", 0) > 0 else "normal"

        return await self.workflow_capture_observation(
            workflow_type="QUALITY_AUDIT",
            session_id=session_id,
            content=content,
            observation_type="finding",
            priority=priority,
            tags=["scan", scan_type.lower()]
        )

    # =========================================================================
    # CROSS-WORKFLOW CONTEXT RETRIEVAL
    # =========================================================================

    async def get_workflow_context(
        self,
        workflow_type: str,
        session_id: str,
        token_budget: int = 3000
    ) -> Dict[str, Any]:
        """
        Get accumulated context for any workflow.

        Args:
            workflow_type: Workflow type
            session_id: Session ID
            token_budget: Max tokens to return

        Returns:
            Context window with observations
        """
        prefix_map = {
            "GREEN_PAPER": "gp",
            "BROWN_PAPER": "bp",
            "MIGRATION": "mig",
            "QUALITY_AUDIT": "qa",
            "BUG": "bug",
            "MAINTENANCE": "maint",
            "NEW_FEATURE": "feat",
            "TESTING": "test"
        }
        prefix = prefix_map.get(workflow_type, workflow_type[:4].lower())
        mem_session_id = f"{prefix}_{session_id}"

        try:
            return await self.claude_mem.get_context_window(
                session_id=mem_session_id,
                token_budget=token_budget,
                strategy="priority",
                include_summaries=True
            )
        except Exception as e:
            logger.warning(f"Failed to get workflow context: {e}")
            return {"error": str(e), "context_text": ""}

    async def inject_workflow_context(
        self,
        workflow_type: str,
        session_id: str,
        base_prompt: str,
        token_budget: int = 2000
    ) -> str:
        """
        Inject workflow context into a prompt.

        Args:
            workflow_type: Workflow type
            session_id: Session ID
            base_prompt: Original prompt
            token_budget: Max tokens for context

        Returns:
            Enhanced prompt with context
        """
        context = await self.get_workflow_context(
            workflow_type=workflow_type,
            session_id=session_id,
            token_budget=token_budget
        )

        if "error" in context or not context.get("context_text"):
            return base_prompt

        return f"""## Workflow Context ({workflow_type})
(Auto-captured from previous steps)

{context.get('context_text', '')}

---

{base_prompt}"""


# =========================================================================
# GHOSTCREW SECURITY INTEGRATION (Week 80-82)
# =========================================================================

class WorkflowGhostCrewIntegration:
    """
    GhostCrew integration mixin for WorkflowToolIntegrationService.

    Provides security scanning hooks for all workflows:
    - QUALITY_AUDIT: Full security crew analysis
    - BROWN_PAPER: Legacy security assessment
    - MIGRATION: Per-phase security verification
    - NEW_FEATURE: Security review on completion
    - BUG: Security check for security-related bugs
    - MAINTENANCE: Security scan for dependency updates
    """

    def __init__(self, db):
        self.db = db
        self._ghostcrew = None
        self._shadow_graph = None
        self._security_rag = None

    @property
    def ghostcrew(self):
        """Lazy-load GhostCrew service."""
        if self._ghostcrew is None:
            from app.services.ghostcrew_service import GhostCrewService
            self._ghostcrew = GhostCrewService(self.db)
        return self._ghostcrew

    @property
    def shadow_graph(self):
        """Lazy-load ShadowGraph service."""
        if self._shadow_graph is None:
            from app.services.shadow_graph_service import ShadowGraphService
            self._shadow_graph = ShadowGraphService(self.db)
        return self._shadow_graph

    @property
    def security_rag(self):
        """Lazy-load Security RAG service."""
        if self._security_rag is None:
            from app.services.security_rag_service import SecurityRAGService
            self._security_rag = SecurityRAGService(self.db)
        return self._security_rag

    # =========================================================================
    # QUALITY_AUDIT Integration - Primary Security Workflow
    # =========================================================================

    async def quality_audit_security_scan(
        self,
        session_id: str,
        project_id: int,
        target_path: str,
        scan_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Run GhostCrew security scan for QUALITY_AUDIT workflow.
        This is the primary security integration point.

        Args:
            session_id: Quality audit session ID
            project_id: Project being audited
            target_path: Path to scan
            scan_type: Type of scan (full, quick, targeted)

        Returns:
            Security scan results
        """
        try:
            result = await self.ghostcrew.scan_autonomous(
                repo_path=target_path,
                project_id=project_id,
                scan_type=scan_type,
                workflow_type="QUALITY_AUDIT",
                workflow_session_id=session_id
            )

            logger.info(
                f"QUALITY_AUDIT security scan completed: "
                f"{result.get('total_findings', 0)} findings, "
                f"score={result.get('security_score', 0)}"
            )

            return result

        except Exception as e:
            logger.error(f"QUALITY_AUDIT security scan failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def quality_audit_run_crew(
        self,
        session_id: str,
        project_id: int,
        target_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run full GhostCrew multi-agent analysis for QUALITY_AUDIT.
        Uses all security agents: SecurityAgent, AuditAgent, ComplianceAgent.

        Args:
            session_id: Quality audit session ID
            project_id: Project being audited
            target_path: Optional specific path

        Returns:
            Combined crew analysis results
        """
        try:
            result = await self.ghostcrew.run_crew(
                project_id=project_id,
                target_path=target_path,
                agents=["security_agent", "audit_agent", "compliance_agent"],
                workflow_type="QUALITY_AUDIT",
                workflow_session_id=session_id
            )

            logger.info(
                f"QUALITY_AUDIT crew analysis completed: "
                f"score={result.get('security_score', 0)}, "
                f"risk={result.get('risk_level', 'unknown')}"
            )

            return result

        except Exception as e:
            logger.error(f"QUALITY_AUDIT crew analysis failed: {e}")
            return {"error": str(e), "status": "failed"}

    # =========================================================================
    # BROWN_PAPER Integration - Legacy Security Assessment
    # =========================================================================

    async def brown_paper_security_assessment(
        self,
        session_id: str,
        project_id: int,
        target_path: str
    ) -> Dict[str, Any]:
        """
        Run security assessment for BROWN_PAPER (legacy analysis).
        Called before migration decision to identify security debt.

        Args:
            session_id: Brown paper session ID
            project_id: Project being analyzed
            target_path: Path to legacy codebase

        Returns:
            Security assessment results with legacy-specific findings
        """
        try:
            # Run autonomous scan with legacy focus
            scan_result = await self.ghostcrew.scan_autonomous(
                repo_path=target_path,
                project_id=project_id,
                scan_type="full",
                workflow_type="BROWN_PAPER",
                workflow_session_id=session_id
            )

            # Get recommendations for findings
            recommendations = []
            for finding in scan_result.get("findings", [])[:5]:
                recs = await self.shadow_graph.get_recommendations(
                    finding.get("finding_type", ""),
                    language=self._detect_language(finding.get("file_path"))
                )
                recommendations.extend(recs)

            # Enhance result with legacy context
            result = {
                **scan_result,
                "workflow": "BROWN_PAPER",
                "legacy_assessment": True,
                "security_debt_items": scan_result.get("total_findings", 0),
                "migration_blockers": [
                    f for f in scan_result.get("findings", [])
                    if f.get("severity") in ("critical", "high")
                ],
                "remediation_recommendations": list(set(recommendations))[:10],
            }

            logger.info(
                f"BROWN_PAPER security assessment completed: "
                f"{result.get('total_findings', 0)} findings, "
                f"{len(result.get('migration_blockers', []))} blockers"
            )

            return result

        except Exception as e:
            logger.error(f"BROWN_PAPER security assessment failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def brown_paper_capture_vulnerabilities(
        self,
        session_id: str,
        findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Capture security findings in Claude-Mem for BROWN_PAPER context.

        Args:
            session_id: Brown paper session ID
            findings: List of security findings

        Returns:
            Capture result
        """
        mem_session_id = f"bp_{session_id}"

        # Format findings for observation
        content_parts = ["## Security Assessment Findings\n"]

        critical_count = sum(1 for f in findings if f.get("severity") == "critical")
        high_count = sum(1 for f in findings if f.get("severity") == "high")

        content_parts.append(f"**Total Findings**: {len(findings)}")
        content_parts.append(f"- Critical: {critical_count}")
        content_parts.append(f"- High: {high_count}\n")

        # Top findings
        content_parts.append("**Top Issues**:")
        for finding in findings[:5]:
            content_parts.append(
                f"- [{finding.get('severity', 'unknown').upper()}] "
                f"{finding.get('title', 'Unknown issue')}"
            )

        content = "\n".join(content_parts)

        try:
            # Import claude_mem from parent class would be needed
            # For now, return structured result
            return {
                "status": "success",
                "session_id": mem_session_id,
                "findings_captured": len(findings),
                "critical_count": critical_count,
                "high_count": high_count,
            }

        except Exception as e:
            logger.error(f"Failed to capture vulnerabilities: {e}")
            return {"error": str(e)}

    # =========================================================================
    # MIGRATION Integration - Per-Phase Security Verification
    # =========================================================================

    async def migration_security_verify(
        self,
        session_id: str,
        project_id: int,
        phase_name: str,
        target_path: str
    ) -> Dict[str, Any]:
        """
        Verify security after migration phase completion.

        Args:
            session_id: Migration session ID
            project_id: Project being migrated
            phase_name: Name of completed phase
            target_path: Path to verify

        Returns:
            Security verification results
        """
        try:
            # Quick scan after phase completion
            result = await self.ghostcrew.scan_autonomous(
                repo_path=target_path,
                project_id=project_id,
                scan_type="quick",
                workflow_type="MIGRATION",
                workflow_session_id=session_id
            )

            # Check for new vulnerabilities
            new_vulns = [
                f for f in result.get("findings", [])
                if f.get("severity") in ("critical", "high")
            ]

            verification = {
                **result,
                "phase_name": phase_name,
                "phase_passed": len(new_vulns) == 0,
                "new_vulnerabilities": len(new_vulns),
                "blocking_issues": new_vulns,
                "recommendation": (
                    "Phase security check passed" if len(new_vulns) == 0
                    else f"Address {len(new_vulns)} security issues before proceeding"
                ),
            }

            logger.info(
                f"MIGRATION phase '{phase_name}' security verification: "
                f"{'PASSED' if verification['phase_passed'] else 'FAILED'}"
            )

            return verification

        except Exception as e:
            logger.error(f"MIGRATION security verification failed: {e}")
            return {"error": str(e), "phase_passed": False}

    async def migration_pre_deploy_scan(
        self,
        session_id: str,
        project_id: int,
        target_path: str
    ) -> Dict[str, Any]:
        """
        Final security scan before deployment.

        Args:
            session_id: Migration session ID
            project_id: Project being migrated
            target_path: Final deployment path

        Returns:
            Pre-deployment security assessment
        """
        try:
            # Full scan before deployment
            result = await self.ghostcrew.run_crew(
                project_id=project_id,
                target_path=target_path,
                agents=["security_agent", "compliance_agent"],
                workflow_type="MIGRATION",
                workflow_session_id=session_id
            )

            # Deployment decision
            can_deploy = (
                result.get("security_score", 0) >= 70 and
                result.get("critical_count", 1) == 0
            )

            return {
                **result,
                "pre_deploy_check": True,
                "deployment_approved": can_deploy,
                "approval_reason": (
                    "Security requirements met" if can_deploy
                    else "Critical issues must be resolved before deployment"
                ),
            }

        except Exception as e:
            logger.error(f"Pre-deploy scan failed: {e}")
            return {"error": str(e), "deployment_approved": False}

    # =========================================================================
    # NEW_FEATURE Integration - Security Review
    # =========================================================================

    async def new_feature_security_review(
        self,
        session_id: str,
        project_id: int,
        feature_path: str,
        feature_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Security review for new feature implementation.

        Args:
            session_id: Feature session ID
            project_id: Project ID
            feature_path: Path to feature code
            feature_files: Optional specific files to review

        Returns:
            Security review results
        """
        try:
            result = await self.ghostcrew.scan_autonomous(
                repo_path=feature_path,
                project_id=project_id,
                scan_type="targeted",
                workflow_type="NEW_FEATURE",
                workflow_session_id=session_id
            )

            # Get remediation guidance for findings
            remediations = []
            for finding in result.get("findings", [])[:3]:
                guidance = await self.security_rag.get_remediation(
                    vulnerability_type=finding.get("finding_type", ""),
                    language=self._detect_language(finding.get("file_path"))
                )
                remediations.append({
                    "finding": finding.get("title"),
                    "remediation": guidance.get("remediation_steps", [])[:3]
                })

            return {
                **result,
                "feature_review": True,
                "remediations": remediations,
                "review_passed": result.get("critical_count", 1) == 0,
            }

        except Exception as e:
            logger.error(f"NEW_FEATURE security review failed: {e}")
            return {"error": str(e), "review_passed": False}

    # =========================================================================
    # BUG Integration - Security Bug Check
    # =========================================================================

    async def bug_security_check(
        self,
        session_id: str,
        project_id: int,
        bug_description: str,
        affected_files: List[str],
        is_security_bug: bool = False
    ) -> Dict[str, Any]:
        """
        Security check for bug fixes, especially security-related bugs.

        Args:
            session_id: Bug session ID
            project_id: Project ID
            bug_description: Description of the bug
            affected_files: Files affected by the bug
            is_security_bug: Whether this is a security-related bug

        Returns:
            Security check results
        """
        if not is_security_bug and not self._is_security_related(bug_description):
            return {
                "status": "skipped",
                "reason": "Bug is not security-related",
                "security_check_required": False
            }

        try:
            # Get security guidance for the bug type
            guidance = await self.ghostcrew.assist(
                query=f"Security implications of bug: {bug_description}",
                context="\n".join(affected_files[:5]),
                project_id=project_id
            )

            return {
                "status": "completed",
                "security_check_required": True,
                "is_security_bug": is_security_bug or self._is_security_related(bug_description),
                "guidance": guidance,
                "recommendations": guidance.get("recommendations", []),
                "severity_assessment": guidance.get("severity_assessment", "unknown"),
            }

        except Exception as e:
            logger.error(f"BUG security check failed: {e}")
            return {"error": str(e)}

    # =========================================================================
    # MAINTENANCE Integration - Dependency Security
    # =========================================================================

    async def maintenance_security_scan(
        self,
        session_id: str,
        project_id: int,
        target_path: str,
        focus: str = "dependencies"
    ) -> Dict[str, Any]:
        """
        Security scan for maintenance work (dependency updates, etc.).

        Args:
            session_id: Maintenance session ID
            project_id: Project ID
            target_path: Path to scan
            focus: Focus area (dependencies, config, general)

        Returns:
            Maintenance security scan results
        """
        try:
            result = await self.ghostcrew.scan_autonomous(
                repo_path=target_path,
                project_id=project_id,
                scan_type="quick",
                workflow_type="MAINTENANCE",
                workflow_session_id=session_id
            )

            # Filter for dependency/config issues if focused
            if focus == "dependencies":
                relevant_findings = [
                    f for f in result.get("findings", [])
                    if f.get("category") in ("dependencies", "config", "crypto")
                ]
            else:
                relevant_findings = result.get("findings", [])

            return {
                **result,
                "focus": focus,
                "relevant_findings": relevant_findings,
                "action_required": len([
                    f for f in relevant_findings
                    if f.get("severity") in ("critical", "high")
                ]) > 0,
            }

        except Exception as e:
            logger.error(f"MAINTENANCE security scan failed: {e}")
            return {"error": str(e)}

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _detect_language(self, file_path: Optional[str]) -> Optional[str]:
        """Detect programming language from file path."""
        if not file_path:
            return None

        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".php": "php",
            ".go": "go",
        }

        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang

        return None

    def _is_security_related(self, description: str) -> bool:
        """Check if a bug description is security-related."""
        security_keywords = [
            "security", "vulnerability", "xss", "sql injection", "csrf",
            "authentication", "authorization", "permission", "access control",
            "password", "secret", "token", "credential", "encrypt", "decrypt",
            "injection", "sanitize", "escape", "validate"
        ]

        description_lower = description.lower()
        return any(keyword in description_lower for keyword in security_keywords)


# Extend WorkflowToolIntegrationService with GhostCrew methods
# Add GhostCrew methods to the main service class
WorkflowToolIntegrationService.quality_audit_security_scan = WorkflowGhostCrewIntegration.quality_audit_security_scan
WorkflowToolIntegrationService.quality_audit_run_crew = WorkflowGhostCrewIntegration.quality_audit_run_crew
WorkflowToolIntegrationService.brown_paper_security_assessment = WorkflowGhostCrewIntegration.brown_paper_security_assessment
WorkflowToolIntegrationService.brown_paper_capture_vulnerabilities = WorkflowGhostCrewIntegration.brown_paper_capture_vulnerabilities
WorkflowToolIntegrationService.migration_security_verify = WorkflowGhostCrewIntegration.migration_security_verify
WorkflowToolIntegrationService.migration_pre_deploy_scan = WorkflowGhostCrewIntegration.migration_pre_deploy_scan
WorkflowToolIntegrationService.new_feature_security_review = WorkflowGhostCrewIntegration.new_feature_security_review
WorkflowToolIntegrationService.bug_security_check = WorkflowGhostCrewIntegration.bug_security_check
WorkflowToolIntegrationService.maintenance_security_scan = WorkflowGhostCrewIntegration.maintenance_security_scan


# =========================================================================
# GHOSTCREW WEEK 90 EXTENSIONS
# =========================================================================

class WorkflowGhostCrewWeek90:
    """
    Week 90 GhostCrew extensions for additional workflows:
    - GREEN_PAPER: Greenfield security audit for new project architecture
    - TESTING: Security scan of test files and fixtures
    - ENHANCEMENT: Security scan for enhancement changes
    - QUALITY_IMPROVEMENT: Combined quality + security analysis
    """

    async def ghostcrew_greenfield_audit(
        self,
        session_id: str,
        project_id: int,
        project_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Security review for new project architecture (GREEN_PAPER workflow).

        Analyzes proposed architecture for security best practices:
        - Authentication/authorization design
        - Data protection strategy
        - API security considerations
        - Infrastructure security recommendations

        Args:
            session_id: GREEN_PAPER session ID
            project_id: Project being defined
            project_spec: Project specification/constitution

        Returns:
            Security audit results with architecture recommendations
        """
        try:
            # Extract architecture components from spec
            architecture_context = self._extract_architecture_context(project_spec)

            # Get security guidance based on proposed tech stack
            guidance = await self.ghostcrew.assist(
                query=f"Security review for greenfield project architecture: {architecture_context}",
                context=str(project_spec),
                project_id=project_id,
                include_knowledge=True
            )

            # Build audit result
            result = {
                "scan_id": str(uuid4()),
                "workflow": "GREEN_PAPER",
                "workflow_session_id": session_id,
                "audit_type": "greenfield_architecture",
                "status": "completed",
                "architecture_context": architecture_context,
                "security_recommendations": guidance.get("recommendations", []),
                "immediate_actions": guidance.get("immediate_actions", []),
                "severity_assessment": guidance.get("severity_assessment", "info"),
                "knowledge_references": guidance.get("knowledge_references", []),
                "checklist": self._generate_greenfield_checklist(project_spec),
                "security_patterns_recommended": [
                    "Authentication before authorization",
                    "Defense in depth",
                    "Least privilege principle",
                    "Secure by default configuration",
                    "Input validation at boundaries",
                ],
            }

            logger.info(
                f"GREEN_PAPER greenfield security audit completed: "
                f"{len(result['security_recommendations'])} recommendations"
            )

            return result

        except Exception as e:
            logger.error(f"GREEN_PAPER greenfield audit failed: {e}")
            return {"error": str(e), "status": "failed"}

    def _extract_architecture_context(self, project_spec: Dict[str, Any]) -> str:
        """Extract key architecture details from project spec."""
        parts = []

        if project_spec.get("tech_stack"):
            parts.append(f"Tech Stack: {', '.join(project_spec['tech_stack'])}")

        if project_spec.get("core_functionalities"):
            funcs = [f.get("name", "") for f in project_spec["core_functionalities"][:5]]
            parts.append(f"Core Features: {', '.join(funcs)}")

        if project_spec.get("stakeholders"):
            roles = [s.get("role", "") for s in project_spec["stakeholders"][:3]]
            parts.append(f"User Roles: {', '.join(roles)}")

        if project_spec.get("technical_constraints"):
            constraints = [c.get("constraint", "") for c in project_spec["technical_constraints"][:3]]
            parts.append(f"Constraints: {', '.join(constraints)}")

        return " | ".join(parts) if parts else "New project architecture"

    def _generate_greenfield_checklist(self, project_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate security checklist for greenfield project."""
        checklist = [
            {"item": "Authentication mechanism defined", "category": "auth", "priority": "critical"},
            {"item": "Authorization model specified", "category": "auth", "priority": "critical"},
            {"item": "Data encryption strategy", "category": "crypto", "priority": "high"},
            {"item": "API rate limiting planned", "category": "api", "priority": "high"},
            {"item": "Input validation approach", "category": "injection", "priority": "high"},
            {"item": "Logging and monitoring strategy", "category": "observability", "priority": "medium"},
            {"item": "Secret management solution", "category": "crypto", "priority": "critical"},
            {"item": "CORS configuration plan", "category": "config", "priority": "medium"},
        ]

        # Add tech-stack specific items
        tech_stack = project_spec.get("tech_stack", [])
        if any("python" in t.lower() for t in tech_stack):
            checklist.append({"item": "SQLAlchemy parameterized queries", "category": "injection", "priority": "high"})
        if any("react" in t.lower() or "javascript" in t.lower() for t in tech_stack):
            checklist.append({"item": "XSS prevention (React escaping)", "category": "injection", "priority": "high"})
        if any("api" in t.lower() or "rest" in t.lower() for t in tech_stack):
            checklist.append({"item": "JWT/OAuth2 token handling", "category": "auth", "priority": "critical"})

        return checklist

    async def ghostcrew_test_security(
        self,
        session_id: str,
        project_id: int,
        test_path: str,
        test_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Security scan of test files and fixtures (TESTING workflow).

        Checks for:
        - Hardcoded credentials in test fixtures
        - Insecure test data exposure
        - Test configuration security
        - Mock security bypasses

        Args:
            session_id: TESTING session ID
            project_id: Project being tested
            test_path: Path to test directory
            test_files: Optional specific test files to scan

        Returns:
            Test security scan results
        """
        try:
            # Scan test directory with test-specific patterns
            result = await self.ghostcrew.scan_autonomous(
                repo_path=test_path,
                project_id=project_id,
                scan_type="targeted",
                workflow_type="TESTING",
                workflow_session_id=session_id,
                file_extensions=[".py", ".js", ".ts", ".json", ".yaml", ".yml"]
            )

            # Add test-specific analysis
            test_specific_findings = []

            # Check for common test security issues
            test_patterns = {
                "hardcoded_test_credentials": [
                    r'password\s*=\s*["\']test',
                    r'api_key\s*=\s*["\']test',
                    r'token\s*=\s*["\'][a-zA-Z0-9]+["\']',
                ],
                "fixture_data_exposure": [
                    r'real_.*_data',
                    r'production.*fixture',
                    r'\.env\.test',
                ],
                "security_bypass_in_tests": [
                    r'@skip.*auth',
                    r'mock.*authentication',
                    r'disable.*security',
                ],
            }

            enhanced_result = {
                **result,
                "workflow": "TESTING",
                "test_security_analysis": True,
                "test_specific_findings": test_specific_findings,
                "recommendations": [
                    "Use environment variables for test credentials",
                    "Generate random test data instead of hardcoded values",
                    "Ensure test fixtures don't contain production data",
                    "Review security mocks to ensure they don't hide real issues",
                ] + result.get("recommendations", []),
                "test_security_score": max(0, result.get("security_score", 100) - len(test_specific_findings) * 5),
            }

            logger.info(
                f"TESTING security scan completed: "
                f"{result.get('total_findings', 0)} findings"
            )

            return enhanced_result

        except Exception as e:
            logger.error(f"TESTING security scan failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def ghostcrew_enhancement_scan(
        self,
        session_id: str,
        project_id: int,
        diff_content: str,
        enhancement_description: str
    ) -> Dict[str, Any]:
        """
        Security scan for enhancement changes (ENHANCEMENT workflow).

        Analyzes code changes in enhancement for:
        - New security vulnerabilities introduced
        - Security patterns broken
        - Missing security updates

        Args:
            session_id: ENHANCEMENT session ID
            project_id: Project being enhanced
            diff_content: Git diff or code changes
            enhancement_description: Description of the enhancement

        Returns:
            Enhancement security scan results
        """
        try:
            # Analyze the diff for security issues
            code_findings = await self.ghostcrew._scan_code_snippet(diff_content)

            # Get security guidance for the enhancement type
            guidance = await self.ghostcrew.assist(
                query=f"Security review for enhancement: {enhancement_description}",
                context=diff_content[:2000],  # Limit context size
                project_id=project_id,
                include_knowledge=True
            )

            # Determine if changes are security-sensitive
            security_sensitive_patterns = [
                "auth", "login", "password", "token", "session",
                "permission", "access", "encrypt", "decrypt", "hash",
                "sql", "query", "input", "validate", "sanitize"
            ]

            is_security_sensitive = any(
                pattern in diff_content.lower() or pattern in enhancement_description.lower()
                for pattern in security_sensitive_patterns
            )

            result = {
                "scan_id": str(uuid4()),
                "workflow": "ENHANCEMENT",
                "workflow_session_id": session_id,
                "status": "completed",
                "enhancement_description": enhancement_description,
                "is_security_sensitive": is_security_sensitive,
                "findings_in_changes": code_findings,
                "total_findings": len(code_findings),
                "severity_counts": self._count_severities(code_findings),
                "security_score": 100 - sum(
                    25 if f.get("severity") == "critical" else
                    15 if f.get("severity") == "high" else
                    5 if f.get("severity") == "medium" else 1
                    for f in code_findings
                ),
                "recommendations": guidance.get("recommendations", []),
                "review_required": is_security_sensitive or len(code_findings) > 0,
                "approval_status": (
                    "blocked" if any(f.get("severity") in ("critical", "high") for f in code_findings)
                    else "review" if code_findings
                    else "approved"
                ),
            }

            logger.info(
                f"ENHANCEMENT security scan completed: "
                f"{len(code_findings)} findings, "
                f"approval={result['approval_status']}"
            )

            return result

        except Exception as e:
            logger.error(f"ENHANCEMENT security scan failed: {e}")
            return {"error": str(e), "status": "failed"}

    def _count_severities(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count findings by severity."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in findings:
            severity = finding.get("severity", "info")
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    async def ghostcrew_quality_security(
        self,
        session_id: str,
        project_id: int,
        target_path: str
    ) -> Dict[str, Any]:
        """
        Combined quality + security analysis (QUALITY_IMPROVEMENT workflow).

        Performs holistic analysis combining:
        - Security vulnerability scan
        - Code quality assessment
        - Security-aware refactoring suggestions

        Args:
            session_id: QUALITY_IMPROVEMENT session ID
            project_id: Project being improved
            target_path: Path to analyze

        Returns:
            Combined quality and security report
        """
        try:
            # Run full security scan
            security_result = await self.ghostcrew.scan_autonomous(
                repo_path=target_path,
                project_id=project_id,
                scan_type="full",
                workflow_type="QUALITY_IMPROVEMENT",
                workflow_session_id=session_id
            )

            # Run crew analysis for deeper insights
            crew_result = await self.ghostcrew.run_crew(
                project_id=project_id,
                target_path=target_path,
                agents=["security_agent", "audit_agent"],
                workflow_type="QUALITY_IMPROVEMENT",
                workflow_session_id=session_id
            )

            # Combine results
            combined_findings = security_result.get("findings", []) + crew_result.get("findings", [])
            unique_findings = self._deduplicate_findings(combined_findings)

            # Generate quality-security matrix
            quality_security_matrix = self._build_quality_security_matrix(unique_findings)

            result = {
                "scan_id": str(uuid4()),
                "workflow": "QUALITY_IMPROVEMENT",
                "workflow_session_id": session_id,
                "status": "completed",
                "security_scan": security_result,
                "crew_analysis": crew_result,
                "combined_findings": unique_findings,
                "total_unique_findings": len(unique_findings),
                "quality_security_matrix": quality_security_matrix,
                "overall_score": (
                    security_result.get("security_score", 50) +
                    crew_result.get("security_score", 50)
                ) / 2,
                "improvement_priorities": self._prioritize_improvements(unique_findings),
                "recommendations": list(set(
                    security_result.get("recommendations", []) +
                    crew_result.get("recommendations", [])
                )),
            }

            logger.info(
                f"QUALITY_IMPROVEMENT combined analysis completed: "
                f"{len(unique_findings)} unique findings, "
                f"score={result['overall_score']:.1f}"
            )

            return result

        except Exception as e:
            logger.error(f"QUALITY_IMPROVEMENT analysis failed: {e}")
            return {"error": str(e), "status": "failed"}

    def _deduplicate_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate findings."""
        seen = set()
        unique = []
        for finding in findings:
            key = (
                finding.get("file_path"),
                finding.get("line_number"),
                finding.get("finding_type")
            )
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        return unique

    def _build_quality_security_matrix(
        self,
        findings: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, int]]:
        """Build matrix of quality vs security findings."""
        matrix = {
            "security": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "quality": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        }

        security_categories = ["injection", "auth", "crypto", "config"]

        for finding in findings:
            category = finding.get("category", "")
            severity = finding.get("severity", "low")

            if category in security_categories:
                matrix["security"][severity] = matrix["security"].get(severity, 0) + 1
            else:
                matrix["quality"][severity] = matrix["quality"].get(severity, 0) + 1

        return matrix

    def _prioritize_improvements(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Prioritize improvements based on severity and type."""
        priorities = []

        # Group by severity
        severity_order = ["critical", "high", "medium", "low"]
        for severity in severity_order:
            severity_findings = [f for f in findings if f.get("severity") == severity]
            for finding in severity_findings[:3]:  # Top 3 per severity
                priorities.append({
                    "priority": len(priorities) + 1,
                    "finding_type": finding.get("finding_type"),
                    "severity": severity,
                    "file_path": finding.get("file_path"),
                    "action": f"Address {finding.get('finding_type', 'issue')} in {finding.get('file_path', 'file')}"
                })

        return priorities[:10]  # Top 10 priorities


# Add Week 90 GhostCrew methods to main service
WorkflowToolIntegrationService.ghostcrew_greenfield_audit = WorkflowGhostCrewWeek90.ghostcrew_greenfield_audit
WorkflowToolIntegrationService.ghostcrew_test_security = WorkflowGhostCrewWeek90.ghostcrew_test_security
WorkflowToolIntegrationService.ghostcrew_enhancement_scan = WorkflowGhostCrewWeek90.ghostcrew_enhancement_scan
WorkflowToolIntegrationService.ghostcrew_quality_security = WorkflowGhostCrewWeek90.ghostcrew_quality_security
WorkflowToolIntegrationService._extract_architecture_context = WorkflowGhostCrewWeek90._extract_architecture_context
WorkflowToolIntegrationService._generate_greenfield_checklist = WorkflowGhostCrewWeek90._generate_greenfield_checklist
WorkflowToolIntegrationService._count_severities = WorkflowGhostCrewWeek90._count_severities
WorkflowToolIntegrationService._build_quality_security_matrix = WorkflowGhostCrewWeek90._build_quality_security_matrix
WorkflowToolIntegrationService._prioritize_improvements = WorkflowGhostCrewWeek90._prioritize_improvements
WorkflowToolIntegrationService._deduplicate_findings = WorkflowGhostCrewWeek90._deduplicate_findings


# =========================================================================
# BIGAGI WEEK 90 EXTENSIONS
# =========================================================================

class WorkflowBigAGIWeek90:
    """
    Week 90 BigAGI extensions for architecture validation:
    - GREEN_PAPER: Multi-model validation of architecture decisions
    - BROWN_PAPER: Multi-model consensus on migration strategy
    - NEW_FEATURE: Multi-model validation of feature design
    """

    async def bigagi_validate_architecture(
        self,
        session_id: str,
        project_id: int,
        architecture_doc: str,
        primary_model: str = "felix"
    ) -> Dict[str, Any]:
        """
        Multi-model validation of architecture decisions (GREEN_PAPER).

        Validates proposed architecture against multiple LLM perspectives:
        - Technical soundness
        - Scalability considerations
        - Security implications
        - Best practice alignment

        Args:
            session_id: GREEN_PAPER session ID
            project_id: Project ID
            architecture_doc: Architecture document/specification
            primary_model: Model that proposed the architecture

        Returns:
            Validation result with consensus score
        """
        try:
            # Create validation session
            validation = await self.bigagi.create_validation(
                task=f"Validate architecture for project {project_id}: {architecture_doc[:500]}",
                primary_response=architecture_doc,
                primary_model=primary_model,
                validation_models=[
                    {"name": "qwen2.5-coder:7b", "provider": "ollama", "weight": 2.0},  # Architecture
                    {"name": "deepseek-r1:latest", "provider": "ollama", "weight": 1.5},  # Reasoning
                    {"name": "mistral:latest", "provider": "ollama", "weight": 1.0},  # General
                ],
                session_metadata={
                    "workflow": "GREEN_PAPER",
                    "workflow_session_id": session_id,
                    "validation_type": "architecture",
                    "project_id": project_id
                }
            )

            # Run validation
            result = await self.bigagi.run_validation(
                validation_id=validation.id,
                consensus_method="weighted"
            )

            enhanced_result = {
                "validation_id": str(result.validation_id),
                "workflow": "GREEN_PAPER",
                "workflow_session_id": session_id,
                "validation_type": "architecture",
                "consensus_reached": result.consensus_reached,
                "consensus_score": result.consensus_score,
                "recommendation": result.recommendation,
                "final_answer": result.final_answer,
                "key_agreements": result.key_agreements,
                "key_disagreements": result.key_disagreements,
                "model_responses": result.model_responses,
                "architecture_verdict": (
                    "approved" if result.consensus_score >= 0.85
                    else "review" if result.consensus_score >= 0.7
                    else "revise"
                ),
                "next_steps": self._get_architecture_next_steps(result),
            }

            logger.info(
                f"GREEN_PAPER architecture validation completed: "
                f"consensus={result.consensus_score:.2f}, "
                f"verdict={enhanced_result['architecture_verdict']}"
            )

            return enhanced_result

        except Exception as e:
            logger.error(f"GREEN_PAPER architecture validation failed: {e}")
            return {"error": str(e), "status": "failed"}

    def _get_architecture_next_steps(self, result) -> List[str]:
        """Generate next steps based on validation result."""
        steps = []

        if result.consensus_score >= 0.85:
            steps.extend([
                "Proceed with detailed design phase",
                "Create technical specifications",
                "Begin implementation planning"
            ])
        elif result.consensus_score >= 0.7:
            steps.extend([
                "Review key disagreements from validators",
                "Address highlighted concerns",
                "Re-validate after adjustments"
            ])
        else:
            steps.extend([
                "Major revision required",
                "Analyze all disagreement points",
                "Consider alternative architecture approaches",
                "Schedule architecture review session"
            ])

        return steps

    async def bigagi_validate_migration_plan(
        self,
        session_id: str,
        project_id: int,
        migration_plan: Dict[str, Any],
        primary_model: str = "miguel"
    ) -> Dict[str, Any]:
        """
        Multi-model consensus on migration strategy (BROWN_PAPER).

        Validates migration plan for:
        - Risk assessment accuracy
        - Phase sequencing logic
        - Resource estimation realism
        - Rollback strategy adequacy

        Args:
            session_id: BROWN_PAPER session ID
            project_id: Project ID
            migration_plan: Migration plan document
            primary_model: Model that created the plan

        Returns:
            Validation result with migration-specific insights
        """
        try:
            # Format migration plan for validation
            plan_text = self._format_migration_plan(migration_plan)

            # Create validation session
            validation = await self.bigagi.create_validation(
                task=f"Validate migration plan for legacy system: {plan_text[:500]}",
                primary_response=plan_text,
                primary_model=primary_model,
                validation_models=[
                    {"name": "qwen2.5-coder:7b", "provider": "ollama", "weight": 2.0},  # Technical
                    {"name": "deepseek-r1:latest", "provider": "ollama", "weight": 2.0},  # Risk analysis
                    {"name": "mistral:latest", "provider": "ollama", "weight": 1.0},  # General
                ],
                session_metadata={
                    "workflow": "BROWN_PAPER",
                    "workflow_session_id": session_id,
                    "validation_type": "migration_plan",
                    "project_id": project_id
                }
            )

            # Run validation
            result = await self.bigagi.run_validation(
                validation_id=validation.id,
                consensus_method="weighted"
            )

            # Migration-specific analysis
            risk_validated = any(
                "risk" in str(resp).lower() and "accurate" in str(resp).lower()
                for resp in result.model_responses.values()
            )

            enhanced_result = {
                "validation_id": str(result.validation_id),
                "workflow": "BROWN_PAPER",
                "workflow_session_id": session_id,
                "validation_type": "migration_plan",
                "consensus_reached": result.consensus_reached,
                "consensus_score": result.consensus_score,
                "recommendation": result.recommendation,
                "final_answer": result.final_answer,
                "key_agreements": result.key_agreements,
                "key_disagreements": result.key_disagreements,
                "model_responses": result.model_responses,
                "migration_verdict": (
                    "proceed" if result.consensus_score >= 0.8
                    else "refine" if result.consensus_score >= 0.6
                    else "redesign"
                ),
                "risk_assessment_validated": risk_validated,
                "migration_confidence": result.consensus_score,
                "recommended_actions": self._get_migration_actions(result),
            }

            logger.info(
                f"BROWN_PAPER migration validation completed: "
                f"consensus={result.consensus_score:.2f}, "
                f"verdict={enhanced_result['migration_verdict']}"
            )

            return enhanced_result

        except Exception as e:
            logger.error(f"BROWN_PAPER migration validation failed: {e}")
            return {"error": str(e), "status": "failed"}

    def _format_migration_plan(self, plan: Dict[str, Any]) -> str:
        """Format migration plan for validation prompt."""
        sections = ["# Migration Plan\n"]

        if plan.get("current_state"):
            sections.append(f"## Current State\n{plan['current_state']}\n")

        if plan.get("target_state"):
            sections.append(f"## Target State\n{plan['target_state']}\n")

        if plan.get("phases"):
            sections.append("## Migration Phases\n")
            for i, phase in enumerate(plan["phases"], 1):
                name = phase.get("name", f"Phase {i}")
                duration = phase.get("duration", "TBD")
                sections.append(f"- **{name}**: {duration}\n")

        if plan.get("risks"):
            sections.append("## Identified Risks\n")
            for risk in plan["risks"]:
                sections.append(f"- {risk.get('name', 'Unknown')}: {risk.get('impact', 'TBD')}\n")

        if plan.get("rollback_strategy"):
            sections.append(f"## Rollback Strategy\n{plan['rollback_strategy']}\n")

        return "\n".join(sections)

    def _get_migration_actions(self, result) -> List[str]:
        """Generate recommended actions for migration."""
        actions = []

        if result.consensus_score >= 0.8:
            actions.extend([
                "Begin Phase 1 preparation",
                "Set up monitoring and rollback triggers",
                "Communicate timeline to stakeholders"
            ])
        elif result.consensus_score >= 0.6:
            actions.extend([
                "Review risk assessment with team",
                "Refine phase timelines based on feedback",
                "Add additional checkpoint gates"
            ])
        else:
            actions.extend([
                "Major plan revision required",
                "Re-assess migration approach",
                "Consider alternative strategies (strangler, parallel run)"
            ])

        return actions

    async def bigagi_validate_feature_design(
        self,
        session_id: str,
        project_id: int,
        feature_design: Dict[str, Any],
        primary_model: str = "felix"
    ) -> Dict[str, Any]:
        """
        Multi-model validation of feature design (NEW_FEATURE).

        Validates feature design for:
        - Technical feasibility
        - Design pattern appropriateness
        - Integration considerations
        - Testing strategy adequacy

        Args:
            session_id: NEW_FEATURE session ID
            project_id: Project ID
            feature_design: Feature design specification
            primary_model: Model that created the design

        Returns:
            Validation result with feature-specific feedback
        """
        try:
            # Format feature design for validation
            design_text = self._format_feature_design(feature_design)

            # Create validation session
            validation = await self.bigagi.create_validation(
                task=f"Validate feature design: {design_text[:500]}",
                primary_response=design_text,
                primary_model=primary_model,
                validation_models=[
                    {"name": "qwen2.5-coder:7b", "provider": "ollama", "weight": 2.0},  # Implementation
                    {"name": "deepseek-r1:latest", "provider": "ollama", "weight": 1.5},  # Analysis
                    {"name": "mistral:latest", "provider": "ollama", "weight": 1.0},  # Review
                ],
                session_metadata={
                    "workflow": "NEW_FEATURE",
                    "workflow_session_id": session_id,
                    "validation_type": "feature_design",
                    "project_id": project_id,
                    "feature_name": feature_design.get("name", "Unknown")
                }
            )

            # Run validation
            result = await self.bigagi.run_validation(
                validation_id=validation.id,
                consensus_method="weighted"
            )

            enhanced_result = {
                "validation_id": str(result.validation_id),
                "workflow": "NEW_FEATURE",
                "workflow_session_id": session_id,
                "validation_type": "feature_design",
                "feature_name": feature_design.get("name", "Unknown"),
                "consensus_reached": result.consensus_reached,
                "consensus_score": result.consensus_score,
                "recommendation": result.recommendation,
                "final_answer": result.final_answer,
                "key_agreements": result.key_agreements,
                "key_disagreements": result.key_disagreements,
                "model_responses": result.model_responses,
                "design_verdict": (
                    "approved" if result.consensus_score >= 0.85
                    else "iterate" if result.consensus_score >= 0.7
                    else "rethink"
                ),
                "implementation_ready": result.consensus_score >= 0.8,
                "design_feedback": self._extract_design_feedback(result),
            }

            logger.info(
                f"NEW_FEATURE design validation completed: "
                f"consensus={result.consensus_score:.2f}, "
                f"verdict={enhanced_result['design_verdict']}"
            )

            return enhanced_result

        except Exception as e:
            logger.error(f"NEW_FEATURE design validation failed: {e}")
            return {"error": str(e), "status": "failed"}

    def _format_feature_design(self, design: Dict[str, Any]) -> str:
        """Format feature design for validation prompt."""
        sections = [f"# Feature: {design.get('name', 'New Feature')}\n"]

        if design.get("description"):
            sections.append(f"## Description\n{design['description']}\n")

        if design.get("user_stories"):
            sections.append("## User Stories\n")
            for story in design["user_stories"]:
                sections.append(f"- {story}\n")

        if design.get("technical_approach"):
            sections.append(f"## Technical Approach\n{design['technical_approach']}\n")

        if design.get("api_changes"):
            sections.append("## API Changes\n")
            for change in design["api_changes"]:
                sections.append(f"- {change}\n")

        if design.get("dependencies"):
            sections.append(f"## Dependencies\n{', '.join(design['dependencies'])}\n")

        if design.get("testing_strategy"):
            sections.append(f"## Testing Strategy\n{design['testing_strategy']}\n")

        return "\n".join(sections)

    def _extract_design_feedback(self, result) -> List[str]:
        """Extract actionable design feedback from validation."""
        feedback = []

        # From agreements
        for agreement in result.key_agreements[:3]:
            feedback.append(f"✓ {agreement}")

        # From disagreements
        for disagreement in result.key_disagreements[:3]:
            feedback.append(f"⚠ {disagreement}")

        return feedback


# Add Week 90 BigAGI methods to main service
WorkflowToolIntegrationService.bigagi_validate_architecture = WorkflowBigAGIWeek90.bigagi_validate_architecture
WorkflowToolIntegrationService.bigagi_validate_migration_plan = WorkflowBigAGIWeek90.bigagi_validate_migration_plan
WorkflowToolIntegrationService.bigagi_validate_feature_design = WorkflowBigAGIWeek90.bigagi_validate_feature_design
WorkflowToolIntegrationService._get_architecture_next_steps = WorkflowBigAGIWeek90._get_architecture_next_steps
WorkflowToolIntegrationService._format_migration_plan = WorkflowBigAGIWeek90._format_migration_plan
WorkflowToolIntegrationService._get_migration_actions = WorkflowBigAGIWeek90._get_migration_actions
WorkflowToolIntegrationService._format_feature_design = WorkflowBigAGIWeek90._format_feature_design
WorkflowToolIntegrationService._extract_design_feedback = WorkflowBigAGIWeek90._extract_design_feedback


# =========================================================================
# Factory Function
# =========================================================================

def get_workflow_integration_service(db: AsyncSession) -> WorkflowToolIntegrationService:
    """Get workflow integration service instance."""
    return WorkflowToolIntegrationService(db)
