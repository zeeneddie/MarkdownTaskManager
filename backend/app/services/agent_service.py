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
from app.services.standards_loader_service import get_standards_loader

# Optional knowledge services (Week 62)
try:
    from app.services.unified_knowledge_service import UnifiedKnowledgeService, QueryType
    from app.services.knowledge_graph_service import KnowledgeGraphService
    KNOWLEDGE_SERVICES_AVAILABLE = True
except ImportError:
    KNOWLEDGE_SERVICES_AVAILABLE = False

# Graph workflow integration (Week 88)
try:
    from app.services.graph_workflow_integration_service import GraphWorkflowIntegrationService
    from app.models.graph_workflow import WORKFLOW_GRAPH_INTEGRATIONS
    GRAPH_INTEGRATION_AVAILABLE = True
except ImportError:
    GRAPH_INTEGRATION_AVAILABLE = False

# CCPM Worktree integration (Week 89)
try:
    from app.services.ccpm_workflow_integration_service import (
        CCPMWorkflowIntegrationService,
        SUPPORTED_WORKFLOW_TYPES as CCPM_WORKFLOW_TYPES
    )
    CCPM_INTEGRATION_AVAILABLE = True
except ImportError:
    CCPM_INTEGRATION_AVAILABLE = False
    CCPM_WORKFLOW_TYPES = []

# Agent Orchestration integration (Week 107-110)
try:
    from app.services.orchestration import (
        CrossContextMemoryService, MemoryScope,
        HypothesizeService, Hypothesis,
        StateIndicatorService, ProcessState,
        AntiPatternDetector, AntiPatternType, AnalysisResult,
        RefactorGuardService, ChangeScope, ChangeCheckResult,
    )
    ORCHESTRATION_AVAILABLE = True
except ImportError:
    ORCHESTRATION_AVAILABLE = False
    # Define placeholder types for type hints when not available
    MemoryScope = None  # type: ignore
    ProcessState = None  # type: ignore
    ChangeScope = None  # type: ignore

# Week 111: Missing Patterns integration (Check Alignment, Active Partner, Chunking)
try:
    from app.services.orchestration import (
        CheckAlignmentService, AlignmentLevel, DriftType, AlignmentCheck,
        ActivePartnerService, DecisionType, CollaborationMode, HandoffReason,
        ChunkingService, ChunkStrategy, ChunkingConfig,
    )
    WEEK_111_PATTERNS_AVAILABLE = True
except ImportError:
    WEEK_111_PATTERNS_AVAILABLE = False
    CheckAlignmentService = None  # type: ignore
    ActivePartnerService = None  # type: ignore
    ChunkingService = None  # type: ignore
    AlignmentLevel = None  # type: ignore
    DecisionType = None  # type: ignore
    ChunkStrategy = None  # type: ignore

# Week 116: Phase 5 - Business Rule Workflow Integration
try:
    from app.services.orchestration import (
        BusinessRuleWorkflowIntegration,
        RuleExtractionContext,
        WorkflowIntegrationResult,
        is_rule_integrated_workflow,
        RULE_INTEGRATED_WORKFLOWS,
    )
    RULE_INTEGRATION_AVAILABLE = True
except ImportError:
    RULE_INTEGRATION_AVAILABLE = False
    BusinessRuleWorkflowIntegration = None  # type: ignore
    is_rule_integrated_workflow = lambda x: False  # type: ignore
    RULE_INTEGRATED_WORKFLOWS = frozenset()  # type: ignore

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service for executing AI agent workflows via TypeScript subprocess
    """

    def __init__(self):
        # Path to the agents directory (at project root level)
        self.agents_dir = Path(__file__).parent.parent.parent.parent / "agents"
        self.node_binary = "npx"

        # Cache for work type configurations
        self._work_type_cache: Optional[List[WorkTypeInfo]] = None
        self._agent_cache: Optional[List[AgentInfo]] = None

        # Initialize Agent Orchestration services (Week 107-110)
        self._init_orchestration_services()

        logger.info(f"AgentService initialized with agents_dir: {self.agents_dir}")

    def _init_orchestration_services(self) -> None:
        """Initialize Agent Orchestration services (Week 107-111, 116)"""
        if not ORCHESTRATION_AVAILABLE:
            logger.warning("Orchestration services not available - running in basic mode")
            self._memory_service = None
            self._hypothesize_service = None
            self._state_service = None
            self._antipattern_detector = None
            self._refactor_guard = None
            self._alignment_service = None
            self._partner_service = None
            self._chunking_service = None
            self._rule_integration_service = None
            return

        try:
            # Week 107-110: Core Orchestration Services
            # Cross-Context Memory - persistent state between sessions
            self._memory_service = CrossContextMemoryService()

            # Hypothesize - verbalize expectations before execution
            self._hypothesize_service = HypothesizeService()

            # State Indicator - track workflow progress
            self._state_service = StateIndicatorService()

            # Anti-Pattern Detector - quality gates (9 patterns)
            self._antipattern_detector = AntiPatternDetector()

            # Refactor Guard - protect against scope creep
            self._refactor_guard = RefactorGuardService()

            logger.info("Orchestration services initialized (Week 107-110)")
        except Exception as e:
            logger.error(f"Failed to initialize orchestration services: {e}")
            self._memory_service = None
            self._hypothesize_service = None
            self._state_service = None
            self._antipattern_detector = None
            self._refactor_guard = None

        # Week 111: Missing Patterns (Check Alignment, Active Partner, Chunking)
        self._init_week_111_patterns()

        # Week 116: Phase 5 - Business Rule Workflow Integration
        self._init_rule_integration_service()

    def _init_week_111_patterns(self) -> None:
        """Initialize Week 111 Missing Patterns services"""
        if not WEEK_111_PATTERNS_AVAILABLE:
            logger.warning("Week 111 patterns not available - alignment/partner/chunking disabled")
            self._alignment_service = None
            self._partner_service = None
            self._chunking_service = None
            return

        try:
            # Check Alignment - verify actions align with stated goals
            self._alignment_service = CheckAlignmentService()

            # Active Partner - human-AI collaboration and decision points
            self._partner_service = ActivePartnerService()

            # Chunking - decompose large tasks into manageable pieces
            self._chunking_service = ChunkingService()

            logger.info("Week 111 Missing Patterns initialized (Alignment, Partner, Chunking)")
        except Exception as e:
            logger.error(f"Failed to initialize Week 111 patterns: {e}")
            self._alignment_service = None
            self._partner_service = None
            self._chunking_service = None

    def _init_rule_integration_service(self) -> None:
        """Initialize Week 116 Business Rule Workflow Integration service"""
        if not RULE_INTEGRATION_AVAILABLE:
            logger.warning("Rule integration not available - running without business rule extraction")
            self._rule_integration_service = None
            return

        try:
            self._rule_integration_service = BusinessRuleWorkflowIntegration()
            logger.info("Week 116 Business Rule Workflow Integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize rule integration service: {e}")
            self._rule_integration_service = None

    async def _get_rule_context(
        self,
        work_type: str,
        source_path: Optional[str],
        project_id: Optional[int],
        tier: str = "STANDARD",
    ) -> Optional[Dict[str, Any]]:
        """
        Get business rule extraction context for a workflow.

        Week 116: Phase 5 - Business Rule Workflow Integration

        Args:
            work_type: The workflow type (BROWN_PAPER, MIGRATION, BACKLOG_GENERATION)
            source_path: Path to source code for extraction
            project_id: Optional project ID
            tier: Extraction tier (FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM)

        Returns:
            Rule context dict with entities, workflows, and agent-specific context
        """
        if not self._rule_integration_service or not source_path:
            return None

        if not is_rule_integrated_workflow(work_type):
            return None

        try:
            result = await self._rule_integration_service.extract_for_workflow(
                workflow_type=work_type,
                source_path=source_path,
                project_id=project_id,
                tier=tier,
                enable_llm=True,
            )

            if result.success and result.extraction_context:
                logger.info(
                    f"Rule extraction for {work_type}: "
                    f"{result.extraction_context.total_rules} rules, "
                    f"{len(result.extraction_context.entities)} entities"
                )
                return {
                    "extraction_summary": {
                        "total_rules": result.extraction_context.total_rules,
                        "entities": len(result.extraction_context.entities),
                        "workflows": len(result.extraction_context.workflows),
                        "tier": tier,
                    },
                    "agent_contexts": result.agent_contexts,
                    "entities": result.extraction_context.entities[:15],
                    "detected_workflows": result.extraction_context.workflows[:10],
                    "detected_languages": result.extraction_context.detected_languages,
                    "database_patterns": result.extraction_context.database_patterns,
                }

            return None

        except Exception as e:
            logger.warning(f"Rule extraction failed for {work_type}: {e}")
            return None

    async def execute_workflow(
        self,
        request: WorkflowRequest,
        timeout: int = 1800,
        project_id: Optional[int] = None,
        db_session = None
    ) -> WorkflowResult:
        """
        Execute a workflow by calling the TypeScript agent system

        Args:
            request: The workflow request
            timeout: Suggested maximum execution time in seconds (default: 30 minutes)
                    Note: This is a soft limit - execution will log a warning but continue
            project_id: Optional project ID for knowledge context (Week 62)
            db_session: Optional database session for knowledge services

        Returns:
            WorkflowResult with execution details

        Raises:
            RuntimeError: If workflow execution fails
        """
        start_time = datetime.now()
        workflow_session_id = f"{request.work_type}_{start_time.isoformat()}"

        try:
            # ========== PRE-WORKFLOW HOOKS (Week 107-111) ==========
            hook_context = await self._pre_workflow_hooks(
                request=request,
                session_id=workflow_session_id,
                project_id=project_id
            )

            # Load standards for this workflow type
            standards_content = self._get_standards_for_workflow(request.work_type)

            # Prepare the request payload with standards injected
            context = request.context or {}
            if standards_content:
                context["coding_standards"] = standards_content

            # Load knowledge context for primary agent (Week 62)
            if project_id and db_session:
                primary_agent = self._get_primary_agent_for_workflow(request.work_type)
                if primary_agent:
                    knowledge_context = self._get_knowledge_context(
                        agent_name=primary_agent,
                        project_id=project_id,
                        task_description=request.description,
                        db_session=db_session
                    )
                    if knowledge_context:
                        context["knowledge_context"] = knowledge_context
                        logger.info(f"Injected knowledge context for {primary_agent}")

            # Load graph analysis context (Week 88)
            if project_id and db_session and GRAPH_INTEGRATION_AVAILABLE:
                graph_context = await self._get_graph_context(
                    work_type=request.work_type,
                    project_id=project_id,
                    context=context,
                    db_session=db_session
                )
                if graph_context:
                    context["graph_analysis"] = graph_context
                    logger.info(f"Injected graph analysis for {request.work_type}")

            # Load CCPM worktree context (Week 89)
            if project_id and db_session and CCPM_INTEGRATION_AVAILABLE:
                primary_agent = self._get_primary_agent_for_workflow(request.work_type)
                if primary_agent and request.work_type in CCPM_WORKFLOW_TYPES:
                    context = await self._get_worktree_context(
                        work_type=request.work_type,
                        project_id=project_id,
                        agent_id=primary_agent,
                        context=context,
                        db_session=db_session
                    )
                    if context.get("worktree"):
                        logger.info(f"Injected worktree context for {request.work_type}")

            # Week 116: Load business rule context for rule-integrated workflows
            if request.work_type and is_rule_integrated_workflow(request.work_type):
                source_path = context.get("source_path") or context.get("app_root_path")
                tier = context.get("extraction_tier", "STANDARD")
                if source_path:
                    rule_context = await self._get_rule_context(
                        work_type=request.work_type,
                        source_path=source_path,
                        project_id=project_id,
                        tier=tier,
                    )
                    if rule_context:
                        context["business_rule_context"] = rule_context
                        # Inject agent-specific contexts
                        primary_agent = self._get_primary_agent_for_workflow(request.work_type)
                        if primary_agent and primary_agent in rule_context.get("agent_contexts", {}):
                            context["agent_rule_context"] = rule_context["agent_contexts"][primary_agent]
                        logger.info(f"Injected business rule context for {request.work_type}")

            payload = {
                "description": request.description,
                "context": context,
                "priority": request.priority,
                "work_type": request.work_type if hasattr(request, 'work_type') else None
            }

            # Call the TypeScript workflow executor
            result = await self._call_typescript_workflow(payload, timeout)

            # Parse the result
            execution_time = (datetime.now() - start_time).total_seconds()

            # ========== POST-WORKFLOW HOOKS (Week 107-110) ==========
            workflow_result = WorkflowResult(
                work_type=result.get("workType", "NEW_FEATURE"),
                status=result.get("status", "success"),
                agents_executed=self._parse_agent_results(result.get("agentsExecuted", [])),
                total_execution_time=execution_time,
                result=result.get("result", {}),
                error=result.get("error"),
                timestamp=start_time
            )

            # Run post-workflow analysis (Week 107-111)
            await self._post_workflow_hooks(
                request=request,
                result=workflow_result,
                session_id=workflow_session_id,
                project_id=project_id,
                hook_context=hook_context
            )

            return workflow_result

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

    def _get_standards_for_workflow(self, work_type: Optional[str]) -> Optional[str]:
        """
        Get coding standards for a specific workflow type.

        Standards are loaded from .standards/ folder and injected into agent context.
        This implements the Agent OS "standards-as-files" concept (Week 59).

        Args:
            work_type: The workflow type (e.g., "NEW_FEATURE", "BUG")

        Returns:
            Concatenated standards content or None if no work_type specified
        """
        if not work_type:
            return None

        try:
            loader = get_standards_loader()
            standards = loader.get_standards_for_workflow(work_type)
            if standards:
                logger.debug(f"Loaded standards for workflow {work_type}: {len(standards)} chars")
            return standards if standards else None
        except Exception as e:
            logger.warning(f"Failed to load standards for {work_type}: {e}")
            return None

    def _get_knowledge_context(
        self,
        agent_name: str,
        project_id: Optional[int],
        task_description: Optional[str],
        db_session = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get knowledge context for a specific agent.

        Knowledge is sourced from CodeWiki, CodeRAG, and Knowledge Graph.
        This implements Week 62 Code Understanding integration.

        Args:
            agent_name: The agent name (felix, miguel, quinn, diana, etc.)
            project_id: Optional project ID for project-specific knowledge
            task_description: Optional task description for relevance filtering
            db_session: Database session for service initialization

        Returns:
            Knowledge context dict or None if services unavailable
        """
        if not KNOWLEDGE_SERVICES_AVAILABLE or not project_id or not db_session:
            return None

        try:
            # Get unified knowledge context
            knowledge_service = UnifiedKnowledgeService(db_session)
            context = knowledge_service.get_agent_context(
                agent_name=agent_name,
                project_id=project_id,
                task_description=task_description
            )

            # Add agent-specific knowledge based on role
            agent_lower = agent_name.lower()

            if agent_lower == "felix":
                # Felix needs architecture overview
                arch = knowledge_service.get_architecture_context(project_id)
                context["architecture"] = arch

            elif agent_lower == "miguel":
                # Miguel needs dependency analysis
                deps = knowledge_service.get_dependency_context(project_id)
                context["dependencies"] = deps

            elif agent_lower in ("quinn", "tessa"):
                # Quinn/Tessa need quality insights - use knowledge graph if available
                try:
                    from app.api.knowledge_graph import _graph_services
                    if project_id in _graph_services:
                        graph = _graph_services[project_id]
                        context["quality_insights"] = graph.get_quality_insights()
                except Exception:
                    pass

            elif agent_lower == "vicky":
                # Week 94-95: Vicky needs design context (tokens, specs, sample data)
                try:
                    from app.services.design_os_service import (
                        DesignTokenService,
                        ApplicationShellService,
                        UISpecificationService
                    )
                    # Get existing design tokens if available
                    token_service = DesignTokenService(None)  # Will need DB session
                    context["design_context"] = {
                        "has_tokens": False,
                        "has_shell": False,
                        "available_presets": list(token_service.get_presets().keys()) if hasattr(token_service, 'get_presets') else [],
                        "tier": "STANDARD"  # Default tier
                    }
                except Exception:
                    pass

            logger.debug(f"Loaded knowledge context for {agent_name}: {len(str(context))} chars")
            return context

        except Exception as e:
            logger.warning(f"Failed to load knowledge for {agent_name}: {e}")
            return None

    async def _get_graph_context(
        self,
        work_type: Optional[str],
        project_id: int,
        context: Dict[str, Any],
        db_session = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get graph analysis context for a workflow.

        Runs appropriate graph analyses based on workflow type.
        This implements Week 88 Graph Workflow Integration.

        Args:
            work_type: The workflow type (NEW_FEATURE, BUG, MAINTENANCE, etc.)
            project_id: Project ID for the analysis
            context: Current workflow context (may contain changes, entity_id, etc.)
            db_session: Database session for service initialization

        Returns:
            Graph analysis context dict or None if unavailable
        """
        if not GRAPH_INTEGRATION_AVAILABLE or not project_id or not db_session:
            return None

        if not work_type:
            return None

        # Check if this workflow type has graph integrations
        integrations = WORKFLOW_GRAPH_INTEGRATIONS.get(work_type, [])
        if not integrations:
            return None

        try:
            import uuid
            service = GraphWorkflowIntegrationService(db_session)
            session_id = str(uuid.uuid4())

            # Run all relevant graph analyses for this workflow
            result = await service.run_workflow_integrations(
                workflow_type=work_type,
                project_id=project_id,
                session_id=session_id,
                context=context
            )

            if result and result.get("results"):
                logger.debug(
                    f"Graph analysis for {work_type}: "
                    f"{len(result.get('integrations_run', []))} analyses run"
                )
                return result

            return None

        except Exception as e:
            logger.warning(f"Failed to load graph context for {work_type}: {e}")
            return None

    async def _get_worktree_context(
        self,
        work_type: Optional[str],
        project_id: int,
        agent_id: str,
        context: Dict[str, Any],
        db_session = None
    ) -> Dict[str, Any]:
        """
        Get CCPM worktree context for a workflow.

        Creates or retrieves isolated worktree for agent parallel development.
        This implements Week 89 CCPM Worktree Integration.

        Args:
            work_type: The workflow type (GREEN_PAPER, BROWN_PAPER, MIGRATION, NEW_FEATURE, BUG)
            project_id: Project ID for the worktree
            agent_id: Agent executing the workflow
            context: Current workflow context
            db_session: Database session for service initialization

        Returns:
            Enhanced context with worktree info
        """
        if not CCPM_INTEGRATION_AVAILABLE or not project_id or not db_session:
            return context

        if not work_type or work_type not in CCPM_WORKFLOW_TYPES:
            return context

        try:
            service = CCPMWorkflowIntegrationService(db_session)

            # Inject worktree context into workflow context
            enhanced_context = await service.inject_worktree_context(
                workflow_type=work_type,
                project_id=project_id,
                agent_id=agent_id,
                context=context
            )

            if enhanced_context.get("worktree"):
                logger.debug(
                    f"Worktree for {work_type}/{agent_id}: "
                    f"{enhanced_context['worktree'].get('branch')}"
                )

            return enhanced_context

        except Exception as e:
            logger.warning(f"Failed to load worktree context for {work_type}: {e}")
            return context

    def _get_primary_agent_for_workflow(self, work_type: Optional[str]) -> Optional[str]:
        """
        Get the primary agent for a workflow type.

        This determines which agent's knowledge context to load.

        Args:
            work_type: The workflow type

        Returns:
            Primary agent name or None
        """
        if not work_type:
            return None

        # Map work types to primary agents
        agent_map = {
            "NEW_FEATURE": "felix",      # Felix: Feature Architect
            "GREEN_PAPER": "peter",      # Peter: Product Owner (leads discovery)
            "BROWN_PAPER": "miguel",     # Miguel: Migration Architect
            "BUG": "betty",              # Betty: Bug Hunter
            "MAINTENANCE": "marcus",     # Marcus: Maintenance Specialist
            "MIGRATION": "miguel",       # Miguel: Migration Architect
            "QUALITY_AUDIT": "quinn",    # Quinn: Quality Inspector
            "QUALITY_IMPROVEMENT": "quinn",
            "TESTING": "tessa",          # Tessa: Test Engineer
            "ENHANCEMENT": "felix",
            "PROJECT_DEFINITION": "peter",
            "BACKLOG_GENERATION": "peter",  # Week 116: Peter leads backlog generation from code
        }

        return agent_map.get(work_type.upper())

    # ========== ORCHESTRATION HOOKS (Week 107-110) ==========

    async def _pre_workflow_hooks(
        self,
        request: WorkflowRequest,
        session_id: str,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Pre-workflow orchestration hooks (Week 107-111).

        Executes before workflow starts:
        1. Load cross-context memory (previous session state)
        2. Create hypothesis (verbalize expectations)
        3. Set initial state indicator
        4. Check refactor guard (scope protection)
        5. Week 111: Check alignment with stated goal
        6. Week 111: Chunk large descriptions if needed
        7. Week 111: Initialize collaboration session

        Args:
            request: The workflow request
            session_id: Unique session identifier
            project_id: Optional project ID

        Returns:
            Hook context dict with alignment session, chunking info, etc.
        """
        hook_context: Dict[str, Any] = {}

        if not ORCHESTRATION_AVAILABLE:
            return hook_context

        try:
            # 1. Load previous session memory if available
            if self._memory_service and project_id:
                try:
                    previous_state = self._memory_service.load_state(
                        scope=MemoryScope.PROJECT,
                        scope_id=str(project_id)
                    )
                    if previous_state:
                        logger.debug(f"Loaded {len(previous_state)} memory entries for project {project_id}")
                except Exception as e:
                    logger.warning(f"Failed to load memory state: {e}")

            # 2. Create hypothesis (Gregor Riegler pattern: verbalize before execute)
            if self._hypothesize_service:
                try:
                    hypothesis = self._hypothesize_service.create_hypothesis(
                        task_description=request.description,
                        work_type=request.work_type,
                        context=request.context or {}
                    )
                    logger.info(f"Hypothesis created: {hypothesis.expected_outcome[:100]}...")
                except Exception as e:
                    logger.warning(f"Failed to create hypothesis: {e}")

            # 3. Set initial workflow state
            if self._state_service:
                try:
                    self._state_service.set_state(
                        session_id=session_id,
                        state=ProcessState.PENDING,
                        metadata={
                            "work_type": request.work_type,
                            "project_id": project_id,
                            "started_at": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to set initial state: {e}")

            # 4. Check refactor guard (scope protection)
            if self._refactor_guard and request.context:
                try:
                    scope = ChangeScope(
                        intended_changes=request.context.get("intended_changes", []),
                        affected_files=request.context.get("affected_files", [])
                    )
                    check = self._refactor_guard.check_scope(scope)
                    if not check.allowed:
                        logger.warning(f"Refactor guard warning: {check.reason}")
                except Exception as e:
                    logger.warning(f"Failed to check refactor guard: {e}")

            # ========== WEEK 111: Missing Patterns ==========

            # 5. Check Alignment - create session and verify initial alignment
            if self._alignment_service and WEEK_111_PATTERNS_AVAILABLE:
                try:
                    # Extract goal from request - use description as the goal
                    goal = request.description or "Execute workflow"
                    sub_goals = request.context.get("sub_goals", []) if request.context else []

                    # Create alignment tracking session
                    alignment_session = self._alignment_service.create_session(
                        goal=goal,
                        sub_goals=sub_goals
                    )
                    hook_context["alignment_session_id"] = str(alignment_session.id)

                    # Initial alignment check for the workflow itself
                    initial_action = f"Execute {request.work_type} workflow"
                    alignment_check = self._alignment_service.check_action_alignment(
                        goal=goal,
                        proposed_action=initial_action,
                        context={"work_type": request.work_type, "project_id": project_id}
                    )

                    if not alignment_check.is_aligned:
                        logger.warning(
                            f"Alignment concern: {alignment_check.reasoning}. "
                            f"Suggestions: {alignment_check.suggestions}"
                        )
                    hook_context["initial_alignment"] = {
                        "score": alignment_check.alignment_score,
                        "level": alignment_check.level.value,
                        "is_aligned": alignment_check.is_aligned
                    }
                    logger.debug(f"Alignment session created: {alignment_session.id}")
                except Exception as e:
                    logger.warning(f"Failed to create alignment session: {e}")

            # 6. Chunking - decompose large descriptions for better processing
            if self._chunking_service and WEEK_111_PATTERNS_AVAILABLE:
                try:
                    description = request.description or ""
                    # Only chunk if description is large (>2000 chars)
                    if len(description) > 2000:
                        chunk_session = self._chunking_service.chunk_text(
                            text=description,
                            strategy=ChunkStrategy.SECTION,  # Use section-based for descriptions
                            config=ChunkingConfig(max_size=1500, overlap=100)
                        )
                        hook_context["chunk_session_id"] = str(chunk_session.id)
                        hook_context["total_chunks"] = chunk_session.total_chunks
                        logger.info(f"Description chunked into {chunk_session.total_chunks} parts")
                except Exception as e:
                    logger.warning(f"Failed to chunk description: {e}")

            # 7. Active Partner - initialize collaboration session for complex workflows
            if self._partner_service and WEEK_111_PATTERNS_AVAILABLE:
                try:
                    # Complex workflows that may need human decision points
                    complex_workflows = {"GREEN_PAPER", "BROWN_PAPER", "MIGRATION", "PROJECT_DEFINITION"}
                    if request.work_type in complex_workflows:
                        collab_session = self._partner_service.start_session(
                            task_id=session_id,
                            task_description=request.description or "Complex workflow",
                            mode=CollaborationMode.AI_ASSISTED  # AI leads, human available
                        )
                        hook_context["collaboration_session_id"] = str(collab_session.id)
                        logger.debug(f"Collaboration session created for {request.work_type}")
                except Exception as e:
                    logger.warning(f"Failed to create collaboration session: {e}")

        except Exception as e:
            logger.error(f"Pre-workflow hooks failed: {e}")
            # Don't fail the workflow, just log the error

        return hook_context

    async def _post_workflow_hooks(
        self,
        request: WorkflowRequest,
        result: WorkflowResult,
        session_id: str,
        project_id: Optional[int] = None,
        hook_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Post-workflow orchestration hooks (Week 107-111).

        Executes after workflow completes:
        1. Run anti-pattern detection (9 quality gates)
        2. Update state indicator
        3. Save cross-context memory
        4. Validate hypothesis outcome
        5. Week 111: Analyze alignment drift
        6. Week 111: Generate collaboration report
        7. Week 111: Record final action in alignment session

        Args:
            request: The original workflow request
            result: The workflow execution result
            session_id: Unique session identifier
            project_id: Optional project ID
            hook_context: Context from pre-workflow hooks (alignment/chunking/collab sessions)
        """
        hook_context = hook_context or {}

        if not ORCHESTRATION_AVAILABLE:
            return

        try:
            # 1. Run anti-pattern detection (9 patterns from Gregor Riegler)
            if self._antipattern_detector and result.result:
                try:
                    analysis = self._antipattern_detector.analyze(
                        work_type=request.work_type,
                        description=request.description,
                        result=result.result,
                        context=request.context or {}
                    )
                    if analysis.detected_patterns:
                        for pattern in analysis.detected_patterns:
                            logger.warning(
                                f"Anti-pattern detected: {pattern.pattern_type.value} "
                                f"(severity: {pattern.severity}, confidence: {pattern.confidence:.2f})"
                            )
                        # Store in result metadata for quality gate integration
                        result.result["_antipattern_analysis"] = {
                            "patterns_detected": len(analysis.detected_patterns),
                            "patterns": [
                                {
                                    "type": p.pattern_type.value,
                                    "severity": p.severity,
                                    "confidence": p.confidence,
                                    "description": p.description
                                }
                                for p in analysis.detected_patterns
                            ]
                        }
                except Exception as e:
                    logger.warning(f"Anti-pattern detection failed: {e}")

            # 2. Update state to completed
            if self._state_service:
                try:
                    final_state = ProcessState.COMPLETED if result.status == "success" else ProcessState.FAILED
                    self._state_service.transition(
                        session_id=session_id,
                        to_state=final_state,
                        metadata={
                            "completed_at": datetime.now().isoformat(),
                            "execution_time": result.total_execution_time,
                            "agents_count": len(result.agents_executed)
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to update state: {e}")

            # 3. Save session memory for future reference
            if self._memory_service and project_id:
                try:
                    self._memory_service.save_state(
                        scope=MemoryScope.PROJECT,
                        scope_id=str(project_id),
                        key=f"workflow_{session_id}",
                        value={
                            "work_type": request.work_type,
                            "status": result.status,
                            "execution_time": result.total_execution_time,
                            "agents_executed": [a.agent_name for a in result.agents_executed],
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to save memory state: {e}")

            # 4. Validate hypothesis if created
            if self._hypothesize_service:
                try:
                    validation = self._hypothesize_service.validate(
                        session_id=session_id,
                        actual_outcome=result.result,
                        status=result.status
                    )
                    if validation and not validation.matched:
                        logger.info(f"Hypothesis mismatch: expected vs actual outcome differs")
                except Exception as e:
                    logger.warning(f"Failed to validate hypothesis: {e}")

            # ========== WEEK 111: Missing Patterns Post-Processing ==========

            # 5. Analyze alignment drift for the session
            if self._alignment_service and WEEK_111_PATTERNS_AVAILABLE:
                try:
                    alignment_session_id = hook_context.get("alignment_session_id")
                    if alignment_session_id:
                        from uuid import UUID
                        session_uuid = UUID(alignment_session_id)

                        # Record final workflow completion as an action
                        final_action = f"Completed {request.work_type} workflow with status: {result.status}"
                        self._alignment_service.record_action(
                            session_id=session_uuid,
                            action=final_action,
                            context={
                                "status": result.status,
                                "execution_time": result.total_execution_time,
                                "agents_executed": len(result.agents_executed)
                            }
                        )

                        # Analyze drift for the session
                        drift_report = self._alignment_service.analyze_drift(session_uuid)
                        if drift_report.drift_severity > 0.3:
                            logger.warning(
                                f"Goal drift detected: severity={drift_report.drift_severity:.2f}, "
                                f"types={[d.value for d in drift_report.drift_types]}"
                            )
                            result.result["_alignment_analysis"] = {
                                "average_alignment": drift_report.average_alignment,
                                "drift_severity": drift_report.drift_severity,
                                "drift_types": [d.value for d in drift_report.drift_types],
                                "recommendations": drift_report.recommendations
                            }
                        else:
                            logger.debug(f"Alignment check passed: avg={drift_report.average_alignment:.2f}")
                except Exception as e:
                    logger.warning(f"Failed to analyze alignment drift: {e}")

            # 6. Generate collaboration report if session was created
            if self._partner_service and WEEK_111_PATTERNS_AVAILABLE:
                try:
                    collab_session_id = hook_context.get("collaboration_session_id")
                    if collab_session_id:
                        from uuid import UUID
                        collab_uuid = UUID(collab_session_id)

                        # Generate collaboration report
                        collab_report = self._partner_service.generate_report(collab_uuid)
                        if collab_report:
                            result.result["_collaboration_report"] = {
                                "total_decisions": collab_report.total_decisions,
                                "human_decisions": collab_report.human_decisions,
                                "ai_decisions": collab_report.ai_decisions,
                                "collaboration_score": collab_report.collaboration_score,
                                "handoff_count": collab_report.handoff_count,
                                "recommendations": collab_report.recommendations
                            }
                            logger.debug(
                                f"Collaboration report: {collab_report.total_decisions} decisions, "
                                f"score={collab_report.collaboration_score:.2f}"
                            )
                except Exception as e:
                    logger.warning(f"Failed to generate collaboration report: {e}")

            # 7. Store chunk processing status if chunking was used
            if self._chunking_service and WEEK_111_PATTERNS_AVAILABLE:
                try:
                    chunk_session_id = hook_context.get("chunk_session_id")
                    if chunk_session_id:
                        from uuid import UUID
                        chunk_uuid = UUID(chunk_session_id)
                        chunk_session = self._chunking_service.get_session(chunk_uuid)
                        if chunk_session:
                            result.result["_chunking_info"] = {
                                "total_chunks": chunk_session.total_chunks,
                                "processed_chunks": chunk_session.processed_chunks,
                                "progress_percentage": (chunk_session.processed_chunks / chunk_session.total_chunks * 100)
                                    if chunk_session.total_chunks > 0 else 0
                            }
                except Exception as e:
                    logger.warning(f"Failed to record chunking status: {e}")

        except Exception as e:
            logger.error(f"Post-workflow hooks failed: {e}")
            # Don't fail the workflow, just log the error

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
        """Return default work type configurations (fallback)

        Week 94-95: Added Vicky (Visual Designer) to design-first workflows.
        Vicky is positioned between Peter/Felix and the implementation agents.
        """
        return [
            WorkTypeInfo(
                name="PROJECT_DEFINITION",
                description="Complete new project definition from business case to implementation plan",
                agents=["Peter", "Vicky", "Felix", "Eliza", "Paul", "Diana"],  # Week 94: Vicky added
                process="sequential",
                workflow="project_setup_pipeline"
            ),
            WorkTypeInfo(
                name="GREEN_PAPER",
                description="Greenfield project discovery and specification",
                agents=["Peter", "Vicky", "Felix", "Tessa", "Diana"],  # Week 94: Vicky added
                process="sequential",
                workflow="green_paper_pipeline"
            ),
            WorkTypeInfo(
                name="BROWN_PAPER",
                description="Legacy system analysis and migration planning",
                agents=["Miguel", "Peter", "Vicky", "Felix", "Tessa", "Diana"],  # Week 94: Vicky added
                process="sequential",
                workflow="brown_paper_pipeline"
            ),
            WorkTypeInfo(
                name="NEW_FEATURE",
                description="New feature development from concept to implementation plan",
                agents=["Peter", "Vicky", "Felix", "Tessa", "Diana"],  # Week 94: Vicky added
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
                agents=["Felix", "Vicky", "Tessa", "Diana"],  # Week 94: Vicky added
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
            ),
            # Week 116: Phase 5 - Backlog Generation from Code
            WorkTypeInfo(
                name="BACKLOG_GENERATION",
                description="Generate epics, features, and stories from legacy code analysis",
                agents=["Peter", "Felix", "Paul"],
                process="sequential",
                workflow="backlog_generation_pipeline"
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
            "TESTING": "Test coverage improvement and test automation",
            "BACKLOG_GENERATION": "Generate epics, features, and stories from legacy code analysis",
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
            ),
            # Week 94-95: Vicky - Visual Designer (Design OS Integration)
            AgentInfo(
                name="Vicky",
                role="Visual Designer",
                description="Design-first workflow specialist creating design tokens, wireframes, UI specs, and sample data",
                tools=["design_token_generator", "wireframe_creator", "ui_spec_builder", "sample_data_generator", "shell_configurator", "implementation_prompt_builder"],
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
