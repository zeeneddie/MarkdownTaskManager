"""
Agent Service - Python ↔ TypeScript Bridge

This service handles communication between the FastAPI backend (Python)
and the KaibanJS agent system (TypeScript/Node.js).
"""
import json
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.schemas.workflow import (
    WorkflowRequest,
    WorkflowResult,
    WorkTypeInfo,
    AgentInfo,
    AgentResult,
    WorkType,
    SpecKitWorkflowRequest,
    SpecKitWorkflowResult,
    GeneratedFile,
    TechnicalContext
)

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service for executing AI agent workflows via TypeScript subprocess
    """

    def __init__(self):
        # Path to the agents directory
        self.agents_dir = Path(__file__).parent.parent.parent / "agents"
        self.node_binary = "npx"

        # Cache for work type configurations
        self._work_type_cache: Optional[List[WorkTypeInfo]] = None
        self._agent_cache: Optional[List[AgentInfo]] = None

        logger.info(f"AgentService initialized with agents_dir: {self.agents_dir}")

    async def execute_workflow(
        self,
        request: WorkflowRequest,
        timeout: int = 1800
    ) -> WorkflowResult:
        """
        Execute a workflow by calling the TypeScript agent system

        Args:
            request: The workflow request
            timeout: Suggested maximum execution time in seconds (default: 30 minutes)
                    Note: This is a soft limit - execution will log a warning but continue

        Returns:
            WorkflowResult with execution details

        Raises:
            RuntimeError: If workflow execution fails
        """
        start_time = datetime.now()

        try:
            # Prepare the request payload
            payload = {
                "description": request.description,
                "context": request.context or {},
                "priority": request.priority
            }

            # Call the TypeScript workflow executor
            result = await self._call_typescript_workflow(payload, timeout)

            # Parse the result
            execution_time = (datetime.now() - start_time).total_seconds()

            return WorkflowResult(
                work_type=result.get("workType", "NEW_FEATURE"),
                status=result.get("status", "success"),
                agents_executed=self._parse_agent_results(result.get("agentsExecuted", [])),
                total_execution_time=execution_time,
                result=result.get("result", {}),
                error=result.get("error"),
                timestamp=start_time
            )

        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}", exc_info=True)
            execution_time = (datetime.now() - start_time).total_seconds()
            return WorkflowResult(
                work_type="NEW_FEATURE",
                status="failed",
                agents_executed=[],
                total_execution_time=execution_time,
                result={},
                error=str(e),
                timestamp=start_time
            )

    async def _call_typescript_workflow(
        self,
        payload: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Call the TypeScript workflow executor via subprocess

        Args:
            payload: Request payload to send to TypeScript
            timeout: Execution timeout in seconds

        Returns:
            Parsed JSON result from TypeScript

        Raises:
            RuntimeError: If TypeScript execution fails
        """
        # Create a temporary file with the request payload
        input_json = json.dumps(payload)

        # Execute the TypeScript workflow
        # Using ts-node to run the workflow executor directly
        cmd = [
            self.node_binary,
            "ts-node",
            str(self.agents_dir / "execute-workflow.ts")
        ]

        logger.info(f"Executing TypeScript workflow: {cmd}")
        logger.debug(f"Payload: {input_json}")

        # Run subprocess asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.agents_dir)
        )

        # Send input and wait for completion (no timeout - let user decide when to stop)
        # We'll monitor execution time and log warnings, but never kill the process
        start_exec = datetime.now()

        # Create a task for the communication
        comm_task = asyncio.create_task(process.communicate(input=input_json.encode()))

        # Monitor progress without enforcing timeout
        warning_intervals = [300, 600, 1200, 1800]  # 5, 10, 20, 30 minutes
        last_warning_time = 0

        while not comm_task.done():
            elapsed = (datetime.now() - start_exec).total_seconds()

            # Check if we should log a warning
            for interval in warning_intervals:
                if elapsed >= interval and last_warning_time < interval:
                    logger.warning(
                        f"⏰ Workflow still running after {int(elapsed/60)} minutes. "
                        f"This is just a notification - execution continues. "
                        f"User decides when to stop."
                    )
                    last_warning_time = interval
                    break

            # Wait a bit before checking again
            try:
                await asyncio.wait_for(asyncio.shield(comm_task), timeout=10)
                break  # Task completed
            except asyncio.TimeoutError:
                continue  # Keep waiting

        # Get the results
        stdout, stderr = await comm_task

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"TypeScript workflow failed: {error_msg}")
            raise RuntimeError(f"Workflow execution failed: {error_msg}")

        # Parse the JSON output
        output = stdout.decode()
        logger.debug(f"TypeScript output: {output}")

        return json.loads(output)

    def _parse_agent_results(self, agents: List[Dict]) -> List[AgentResult]:
        """Parse agent execution results from TypeScript output"""
        results = []
        for agent in agents:
            results.append(AgentResult(
                agent_name=agent.get("name", "Unknown"),
                agent_role=agent.get("role", "Unknown"),
                output=agent.get("output", {}),
                execution_time=agent.get("executionTime", 0.0),
                status=agent.get("status", "success")
            ))
        return results

    async def get_work_types(self) -> List[WorkTypeInfo]:
        """
        Get all available work types and their configurations

        Returns:
            List of work type information
        """
        if self._work_type_cache is not None:
            return self._work_type_cache

        # Call TypeScript to get work type configurations
        cmd = [
            self.node_binary,
            "ts-node",
            "-e",
            "import('./routers/workTypeRouter').then(m => console.log(JSON.stringify(m.WORK_TYPE_TEAMS)))"
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.agents_dir)
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30
            )

            if process.returncode != 0:
                logger.error(f"Failed to get work types: {stderr.decode()}")
                return self._get_default_work_types()

            # Parse the output
            work_types_data = json.loads(stdout.decode())

            # Convert to WorkTypeInfo objects
            work_types = []
            for work_type, config in work_types_data.items():
                work_types.append(WorkTypeInfo(
                    name=work_type,
                    description=self._get_work_type_description(work_type),
                    agents=[agent.get("name", "") for agent in config.get("agents", [])],
                    process=config.get("process", "sequential"),
                    workflow=config.get("workflow", "unknown")
                ))

            self._work_type_cache = work_types
            return work_types

        except Exception as e:
            logger.error(f"Error getting work types: {str(e)}", exc_info=True)
            return self._get_default_work_types()

    def _get_default_work_types(self) -> List[WorkTypeInfo]:
        """Return default work type configurations (fallback)"""
        return [
            WorkTypeInfo(
                name="PROJECT_DEFINITION",
                description="Complete new project definition from business case to implementation plan",
                agents=["Peter", "Felix", "Peter", "Eliza", "Paul", "Diana"],
                process="sequential",
                workflow="project_setup_pipeline"
            ),
            WorkTypeInfo(
                name="NEW_FEATURE",
                description="New feature development from concept to implementation plan",
                agents=["Felix", "Eliza", "Tessa", "Quinn", "Diana"],
                process="sequential",
                workflow="spec_kit_pipeline"
            ),
            WorkTypeInfo(
                name="MAINTENANCE",
                description="Code maintenance, refactoring, and dependency updates",
                agents=["Marcus", "Quinn", "Tessa", "Eliza"],
                process="sequential",
                workflow="maintenance_pipeline"
            ),
            WorkTypeInfo(
                name="BUG",
                description="Bug investigation, fixing, and verification",
                agents=["Betty", "Tessa", "Diana"],
                process="sequential",
                workflow="bug_fix_pipeline"
            ),
            WorkTypeInfo(
                name="QUALITY_AUDIT",
                description="Code quality and security audit",
                agents=["Quinn", "Betty", "Marcus", "Diana"],
                process="parallel",
                workflow="quality_audit"
            ),
            WorkTypeInfo(
                name="ENHANCEMENT",
                description="Improvements to existing features",
                agents=["Felix", "Marcus", "Quinn", "Tessa"],
                process="sequential",
                workflow="enhancement_pipeline"
            ),
            WorkTypeInfo(
                name="MIGRATION",
                description="Technology migration and platform upgrades",
                agents=["Miguel", "Marcus", "Tessa", "Diana"],
                process="sequential",
                workflow="migration_pipeline"
            ),
            WorkTypeInfo(
                name="QUALITY_IMPROVEMENT",
                description="Technical debt reduction and code quality improvement",
                agents=["Marcus", "Quinn", "Tessa", "Diana"],
                process="sequential",
                workflow="quality_improvement"
            ),
            WorkTypeInfo(
                name="TESTING",
                description="Test coverage improvement and test automation",
                agents=["Tessa", "Quinn", "Diana"],
                process="sequential",
                workflow="testing_pipeline"
            )
        ]

    def _get_work_type_description(self, work_type: str) -> str:
        """Get description for a work type"""
        descriptions = {
            "PROJECT_DEFINITION": "Complete new project definition from business case to implementation plan",
            "NEW_FEATURE": "New feature development from concept to implementation plan",
            "MAINTENANCE": "Code maintenance, refactoring, and dependency updates",
            "BUG": "Bug investigation, fixing, and verification",
            "QUALITY_AUDIT": "Code quality and security audit",
            "ENHANCEMENT": "Improvements to existing features",
            "MIGRATION": "Technology migration and platform upgrades",
            "QUALITY_IMPROVEMENT": "Technical debt reduction and code quality improvement",
            "TESTING": "Test coverage improvement and test automation"
        }
        return descriptions.get(work_type, "Unknown work type")

    async def get_agents(self) -> List[AgentInfo]:
        """
        Get all available agents and their status

        Returns:
            List of agent information
        """
        if self._agent_cache is not None:
            return self._agent_cache

        # For now, return static agent info
        # TODO: Query TypeScript for actual agent status
        agents = [
            AgentInfo(
                name="Felix",
                role="Feature Architect",
                description="Spec Kit specialist who transforms ideas into structured epics",
                tools=["spec_kit_constitution", "epic_creator", "feasibility_checker", "story_breakdown", "dependency_analyzer", "acceptance_criteria_builder"],
                status="ready"
            ),
            AgentInfo(
                name="Marcus",
                role="Maintenance Specialist",
                description="Code health guardian for refactoring and dependency management",
                tools=["dependency_updater", "refactor_analyzer", "code_smell_detector", "security_scanner", "performance_profiler", "documentation_updater"],
                status="ready"
            ),
            AgentInfo(
                name="Quinn",
                role="Quality Inspector",
                description="Quality assurance expert ensuring code standards and best practices",
                tools=["code_review", "security_audit", "performance_audit", "accessibility_checker", "best_practices_validator", "complexity_analyzer"],
                status="ready"
            ),
            AgentInfo(
                name="Betty",
                role="Bug Hunter",
                description="Root cause analyst and bug fixing specialist",
                tools=["bug_analyzer", "stack_trace_parser", "test_case_generator", "fix_validator", "regression_checker", "error_pattern_matcher"],
                status="ready"
            ),
            AgentInfo(
                name="Eliza",
                role="Estimation Engine",
                description="Effort estimation and resource planning expert",
                tools=["complexity_estimator", "resource_calculator", "timeline_projector", "risk_assessor", "velocity_tracker", "burndown_predictor"],
                status="ready"
            ),
            AgentInfo(
                name="Tessa",
                role="Test Engineer",
                description="Test strategy and automation specialist",
                tools=["test_strategy_planner", "unit_test_generator", "integration_test_designer", "e2e_test_planner", "coverage_analyzer", "test_data_generator"],
                status="ready"
            ),
            AgentInfo(
                name="Miguel",
                role="Migration Architect",
                description="Technology migration and upgrade planning expert",
                tools=["compatibility_checker", "migration_planner", "risk_analyzer", "rollback_strategist", "data_migrator", "version_validator"],
                status="ready"
            ),
            AgentInfo(
                name="Diana",
                role="Documentation Writer",
                description="Technical documentation and knowledge management specialist",
                tools=["api_doc_generator", "readme_writer", "changelog_creator", "tutorial_builder", "diagram_creator", "knowledge_base_updater"],
                status="ready"
            ),
            AgentInfo(
                name="Peter",
                role="Product Owner",
                description="Product vision and business case specialist who translates business needs into project requirements",
                tools=["business_case_analyzer", "stakeholder_interviewer", "scope_definer", "success_metrics_creator", "roadmap_visualizer", "epic_breakdown"],
                status="ready"
            ),
            AgentInfo(
                name="Paul",
                role="Project Lead",
                description="Project planning and resource management expert who creates sprints and manages delivery",
                tools=["project_planner", "resource_allocator", "risk_analyzer", "sprint_designer", "gantt_creator", "milestone_tracker"],
                status="ready"
            )
        ]

        self._agent_cache = agents
        return agents

    async def execute_spec_kit_workflow(
        self,
        request: SpecKitWorkflowRequest,
        timeout: int = 3600
    ) -> SpecKitWorkflowResult:
        """
        Execute complete Spec-Kit workflow (Constitution → Specification → Tasks)

        Args:
            request: The Spec-Kit workflow request
            timeout: Suggested maximum execution time in seconds (default: 60 minutes)

        Returns:
            SpecKitWorkflowResult with all generated files

        Raises:
            RuntimeError: If workflow execution fails
        """
        start_time = datetime.now()

        try:
            # Prepare the request payload
            payload = {
                "command": "spec-kit",
                "businessCase": request.business_case,
                "stakeholders": request.stakeholders,
                "constraints": request.constraints,
                "successCriteria": request.success_criteria,
                "technicalContext": self._prepare_technical_context(request.technical_context),
                "projectPath": request.project_path,
                "projectName": request.project_name
            }

            # Call the TypeScript spec-kit workflow
            result = await self._call_typescript_spec_kit(payload, timeout)

            # Parse the result
            execution_time = (datetime.now() - start_time).total_seconds()

            files = [
                GeneratedFile(
                    filename=f.get("filename", ""),
                    content=f.get("content", ""),
                    path=f.get("path")
                )
                for f in result.get("files", [])
            ]

            # Write files to disk if project_path was provided
            if request.project_path and files:
                await self._write_files_to_disk(files, request.project_path)

            return SpecKitWorkflowResult(
                success=result.get("success", True),
                constitution=result.get("constitution", {}),
                specification=result.get("specification", {}),
                tasks=result.get("tasks", {}),
                files=files,
                summary=result.get("summary", {}),
                total_execution_time=execution_time,
                error=result.get("error")
            )

        except Exception as e:
            logger.error(f"Spec-Kit workflow error: {str(e)}", exc_info=True)
            execution_time = (datetime.now() - start_time).total_seconds()
            return SpecKitWorkflowResult(
                success=False,
                constitution={},
                specification={},
                tasks={},
                files=[],
                summary={},
                total_execution_time=execution_time,
                error=str(e)
            )

    async def execute_constitution(
        self,
        request: SpecKitWorkflowRequest
    ) -> Dict[str, Any]:
        """
        Execute only the Constitution stage

        Args:
            request: The Spec-Kit workflow request

        Returns:
            Constitution result dictionary
        """
        try:
            payload = {
                "command": "constitution",
                "businessCase": request.business_case,
                "stakeholders": request.stakeholders,
                "constraints": request.constraints,
                "successCriteria": request.success_criteria,
                "technicalContext": self._prepare_technical_context(request.technical_context)
            }

            result = await self._call_typescript_spec_kit(payload, 600)
            return result.get("constitution", {})

        except Exception as e:
            logger.error(f"Constitution error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Constitution generation failed: {str(e)}")

    async def execute_specification(
        self,
        request: SpecKitWorkflowRequest,
        constitution: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute only the Specification stage

        Args:
            request: The Spec-Kit workflow request
            constitution: Optional constitution result from previous stage

        Returns:
            Specification result dictionary
        """
        try:
            payload = {
                "command": "specification",
                "businessCase": request.business_case,
                "stakeholders": request.stakeholders,
                "constraints": request.constraints,
                "successCriteria": request.success_criteria,
                "technicalContext": self._prepare_technical_context(request.technical_context),
                "constitution": constitution
            }

            result = await self._call_typescript_spec_kit(payload, 600)
            return result.get("specification", {})

        except Exception as e:
            logger.error(f"Specification error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Specification generation failed: {str(e)}")

    async def execute_tasks(
        self,
        request: SpecKitWorkflowRequest,
        specification: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute only the Tasks stage

        Args:
            request: The Spec-Kit workflow request
            specification: Optional specification result from previous stage

        Returns:
            Tasks result dictionary
        """
        try:
            payload = {
                "command": "tasks",
                "businessCase": request.business_case,
                "stakeholders": request.stakeholders,
                "constraints": request.constraints,
                "successCriteria": request.success_criteria,
                "technicalContext": self._prepare_technical_context(request.technical_context),
                "specification": specification
            }

            result = await self._call_typescript_spec_kit(payload, 600)
            return result.get("tasks", {})

        except Exception as e:
            logger.error(f"Tasks error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Tasks generation failed: {str(e)}")

    def _prepare_technical_context(self, context: Optional[TechnicalContext]) -> Dict[str, Any]:
        """Prepare technical context for TypeScript payload"""
        if context is None:
            return {}

        return {
            "existingSystems": context.existing_systems or [],
            "technologies": context.technologies or [],
            "teamSize": context.team_size,
            "timeline": context.timeline
        }

    async def _call_typescript_spec_kit(
        self,
        payload: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Call the TypeScript Spec-Kit executor via subprocess

        Args:
            payload: Request payload to send to TypeScript
            timeout: Execution timeout in seconds

        Returns:
            Parsed JSON result from TypeScript

        Raises:
            RuntimeError: If TypeScript execution fails
        """
        input_json = json.dumps(payload)

        # Execute the TypeScript spec-kit executor
        cmd = [
            self.node_binary,
            "ts-node",
            str(self.agents_dir / "execute-spec-kit.ts")  # New executor file
        ]

        logger.info(f"Executing Spec-Kit command: {payload.get('command')}")
        logger.debug(f"Payload: {input_json}")

        # Run subprocess asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.agents_dir)
        )

        # Send input and wait for completion
        start_exec = datetime.now()
        comm_task = asyncio.create_task(process.communicate(input=input_json.encode()))

        # Monitor progress (similar to regular workflow)
        warning_intervals = [300, 600, 1200, 1800]
        last_warning_time = 0

        while not comm_task.done():
            elapsed = (datetime.now() - start_exec).total_seconds()

            for interval in warning_intervals:
                if elapsed >= interval and last_warning_time < interval:
                    logger.warning(
                        f"⏰ Spec-Kit still running after {int(elapsed/60)} minutes. "
                        f"Command: {payload.get('command')}"
                    )
                    last_warning_time = interval
                    break

            try:
                await asyncio.wait_for(asyncio.shield(comm_task), timeout=10)
                break
            except asyncio.TimeoutError:
                continue

        # Get the results
        stdout, stderr = await comm_task

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Spec-Kit execution failed: {error_msg}")
            raise RuntimeError(f"Spec-Kit execution failed: {error_msg}")

        # Parse the JSON output
        output = stdout.decode()
        logger.debug(f"Spec-Kit output: {output[:500]}...")

        return json.loads(output)

    async def _write_files_to_disk(
        self,
        files: List[GeneratedFile],
        base_path: str
    ) -> None:
        """
        Write generated files to disk

        Args:
            files: List of generated files with content
            base_path: Base directory path for file creation

        This method:
        1. Creates the base directory if it doesn't exist
        2. Creates subdirectories as needed
        3. Writes each file to disk
        4. Logs the creation of each file
        """
        try:
            # Resolve base path (relative to project root or absolute)
            if not base_path.startswith('/'):
                # Relative path - make it relative to project root
                project_root = Path(__file__).parent.parent.parent.parent
                full_base_path = project_root / base_path
            else:
                full_base_path = Path(base_path)

            # Create base directory
            full_base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Ensured directory exists: {full_base_path}")

            # Write each file
            for file in files:
                # Get the file path (remove base path if it's already in the file.path)
                file_path_str = file.path
                if file_path_str.startswith(base_path):
                    # File path already includes base path
                    full_file_path = Path(file_path_str)
                else:
                    # Append to base path
                    full_file_path = full_base_path / Path(file_path_str).name

                # Create parent directory if needed
                full_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write the file
                full_file_path.write_text(file.content, encoding='utf-8')
                logger.info(f"✓ Wrote file: {full_file_path} ({len(file.content)} bytes)")

            logger.info(f"✓ Successfully wrote {len(files)} files to {full_base_path}")

        except Exception as e:
            logger.error(f"Error writing files to disk: {str(e)}", exc_info=True)
            # Don't raise - file writing is optional, workflow can still succeed

    # ========== Week 11: Task Generation Methods ==========

    async def generate_epics_from_specification(
        self,
        specification: Dict[str, Any],
        project_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call Felix agent to break down specification into epics.

        Args:
            specification: The HLD specification data
            project_id: Project identifier
            options: Generation options (max_epics, focus_areas, etc.)

        Returns:
            Dict with generated epics structure
        """
        try:
            payload = {
                "command": "generate-epics",
                "specification": specification,
                "projectId": project_id,
                "options": options or {}
            }

            result = await self._call_typescript_felix(payload, 300)
            return result

        except Exception as e:
            logger.error(f"Epic generation error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Epic generation failed: {str(e)}")

    async def generate_features_from_epic(
        self,
        epic: Dict[str, Any],
        specification_context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call Felix agent to break down epic into features.

        Args:
            epic: The epic data
            specification_context: Optional specification context
            options: Generation options

        Returns:
            Dict with generated features structure
        """
        try:
            payload = {
                "command": "generate-features",
                "epic": epic,
                "specificationContext": specification_context or {},
                "options": options or {}
            }

            result = await self._call_typescript_felix(payload, 300)
            return result

        except Exception as e:
            logger.error(f"Feature generation error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Feature generation failed: {str(e)}")

    async def generate_stories_from_feature(
        self,
        feature: Dict[str, Any],
        epic_context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call Felix agent to create user stories from feature.

        Args:
            feature: The feature data
            epic_context: Optional epic context
            options: Generation options

        Returns:
            Dict with generated stories structure
        """
        try:
            payload = {
                "command": "generate-stories",
                "feature": feature,
                "epicContext": epic_context or {},
                "options": options or {}
            }

            result = await self._call_typescript_felix(payload, 300)
            return result

        except Exception as e:
            logger.error(f"Story generation error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Story generation failed: {str(e)}")

    async def generate_tasks_from_story(
        self,
        story: Dict[str, Any],
        feature_context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call Felix agent to break down story into technical tasks.

        Args:
            story: The story data
            feature_context: Optional feature context
            options: Generation options

        Returns:
            Dict with generated tasks structure
        """
        try:
            payload = {
                "command": "generate-tasks",
                "story": story,
                "featureContext": feature_context or {},
                "options": options or {}
            }

            result = await self._call_typescript_felix(payload, 300)
            return result

        except Exception as e:
            logger.error(f"Task generation error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Task generation failed: {str(e)}")

    async def _call_typescript_felix(
        self,
        payload: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Call the TypeScript Felix task generation executor via subprocess.

        Args:
            payload: Request payload to send to TypeScript
            timeout: Execution timeout in seconds

        Returns:
            Parsed JSON result from TypeScript

        Raises:
            RuntimeError: If TypeScript execution fails
        """
        input_json = json.dumps(payload)

        # Execute the TypeScript Felix executor using npx
        cmd = [
            "npx",
            "ts-node",
            str(self.agents_dir / "execute-felix-task-generation.ts")
        ]

        logger.info(f"Executing Felix command: {payload.get('command')}")
        logger.debug(f"Payload: {input_json[:200]}...")

        start_exec = datetime.now()

        # Run subprocess asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.agents_dir)
        )

        # Communicate with the subprocess
        comm_task = asyncio.create_task(process.communicate(input=input_json.encode()))

        # Monitor progress
        warning_intervals = [60, 120, 240]
        last_warning_time = 0

        while not comm_task.done():
            elapsed = (datetime.now() - start_exec).total_seconds()

            for interval in warning_intervals:
                if elapsed >= interval and last_warning_time < interval:
                    logger.warning(
                        f"⏰ Felix task generation still running after {int(elapsed)} seconds. "
                        f"Command: {payload.get('command')}"
                    )
                    last_warning_time = interval
                    break

            try:
                await asyncio.wait_for(asyncio.shield(comm_task), timeout=10)
                break
            except asyncio.TimeoutError:
                continue

        # Get the results
        stdout, stderr = await comm_task

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Felix execution failed: {error_msg}")
            raise RuntimeError(f"Felix execution failed: {error_msg}")

        # Parse the JSON output
        output = stdout.decode()
        logger.debug(f"Felix output: {output[:500]}...")

        return json.loads(output)
            # Files are still available in the response

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get workflow execution statistics

        Returns:
            Statistics dictionary
        """
        # TODO: Implement actual statistics tracking
        # For now, return mock statistics
        return {
            "total_workflows_executed": 0,
            "workflows_by_type": {},
            "average_execution_time": 0.0,
            "success_rate": 0.0
        }


# Singleton instance
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """Get or create the AgentService singleton"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
