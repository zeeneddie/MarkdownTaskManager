"""
User Journey Extraction Stage.

Stage for extracting end-user workflows, personas, and screen flows
from legacy code or specifications.

Used by:
- Brown Paper workflow (bottom-up extraction from code)
- Migration workflow (enrichment with 8 questions)
- Green Paper workflow (top-down definition)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from ..models.user_journey import (
    Persona,
    PersonaType,
    UserJourney,
    JourneyStep,
    ScreenInfo,
    ScreenFlow,
    ErrorPath,
    JourneyComplexity,
    InteractionType,
    RolePermissionMatrix,
    UserJourneyExtractionResult,
)
from ..workflows.base import WorkflowContext, StageResult, WorkflowStatus

logger = logging.getLogger(__name__)


class UserJourneyExtractionStage:
    """
    Stage for extracting user journeys from code or specifications.

    Extraction Sources:
    1. UI Components (ASPX, Razor, React, etc.)
    2. Authorization/Role checks
    3. Navigation/Routing
    4. Form handlers & validators
    5. Database user/role tables
    6. API endpoints

    Agents:
    - Vicky: UI/UX analysis, screen flows
    - Peter: Business journeys, persona goals

    Modes:
    - BOTTOM_UP: Extract from code (Brown Paper)
    - TOP_DOWN: Define from specification (Green Paper)
    - HYBRID: Combine code extraction with enrichment (Migration)
    """

    def __init__(self):
        """Initialize stage."""
        self.extractors = []
        self._init_extractors()

    def _init_extractors(self):
        """Initialize tech-stack specific extractors."""
        try:
            from .extractors import (
                AspNetExtractor,
                AspClassicExtractor,
                DatabaseRoleExtractor,
            )

            self.extractors = [
                AspNetExtractor(),
                AspClassicExtractor(),
                DatabaseRoleExtractor(),
            ]
        except ImportError as e:
            logger.warning(f"Could not load all extractors: {e}")
            self.extractors = []

    async def execute(
        self,
        context: WorkflowContext,
        enrichment: Optional[Dict[str, Any]] = None,
    ) -> StageResult:
        """
        Execute user journey extraction.

        Args:
            context: Workflow context with code_analysis and domain data
            enrichment: Optional enrichment data (Migration 8 questions)

        Returns:
            StageResult with UserJourneyExtractionResult
        """
        started_at = datetime.now(timezone.utc)

        try:
            # Get input data
            code_analysis = context.shared_data.get("code_understanding_result", {})
            domains = context.shared_data.get("domain_extraction_result", {})
            tech_stack = context.shared_data.get("tech_stack", [])

            # Auto-detect tech stack if not provided
            if not tech_stack:
                tech_stack = self._detect_tech_stack(code_analysis)

            # Step 1: Extract raw data from code
            raw_extraction = await self._extract_from_code(
                code_analysis, tech_stack
            )

            # Step 2: Use Vicky for UI/UX analysis (if available)
            vicky_result = await self._analyze_with_vicky(
                raw_extraction, context
            )

            # Step 3: Use Peter for business journey definition (if available)
            peter_result = await self._define_with_peter(
                raw_extraction, vicky_result, domains, context
            )

            # Step 4: Apply enrichment (Migration)
            if enrichment:
                peter_result = self._apply_enrichment(peter_result, enrichment)

            # Step 5: Build final result
            result = self._build_result(
                raw_extraction, vicky_result, peter_result
            )

            # Store in context
            context.shared_data["user_journey_extraction_result"] = result.to_dict()

            return StageResult(
                stage_name="user_journey_extraction",
                status=WorkflowStatus.COMPLETED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                agent_results={
                    "raw_extraction": self._summarize_raw_extraction(raw_extraction),
                    "vicky_analysis": vicky_result,
                    "peter_journeys": self._summarize_peter_result(peter_result),
                    "final_result": result.to_dict(),
                },
                quality_score=result.extraction_confidence,
                passed_quality_gate=result.extraction_confidence >= 0.7,
            )

        except Exception as e:
            logger.exception(f"User journey extraction failed: {e}")
            return StageResult(
                stage_name="user_journey_extraction",
                status=WorkflowStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error=str(e),
            )

    def _detect_tech_stack(self, code_analysis: Dict[str, Any]) -> List[str]:
        """Detect tech stack from code analysis."""
        tech_stack = []
        files = code_analysis.get("files", [])

        # Check file extensions
        extensions = set()
        for f in files:
            path = f.get("path", "").lower()
            if "." in path:
                ext = "." + path.rsplit(".", 1)[-1]
                extensions.add(ext)

        # Map extensions to tech stack
        ext_mapping = {
            ".cs": "aspnet",
            ".aspx": "aspnet",
            ".cshtml": "aspnet",
            ".razor": "aspnet",
            ".asp": "asp",
            ".inc": "asp",
            ".jsx": "react",
            ".tsx": "react",
            ".vue": "vue",
            ".py": "python",
            ".sql": "sql",
        }

        for ext in extensions:
            if ext in ext_mapping:
                tech = ext_mapping[ext]
                if tech not in tech_stack:
                    tech_stack.append(tech)

        return tech_stack or ["generic"]

    async def _extract_from_code(
        self,
        code_analysis: Dict[str, Any],
        tech_stack: List[str],
    ) -> Dict[str, Any]:
        """
        Extract raw user journey data from code analysis.

        Analyzes:
        - Authorization attributes/decorators
        - UI component structure
        - Form handlers
        - Navigation/routing
        - Session management
        """
        raw_data = {
            "roles": [],
            "screens": [],
            "forms": [],
            "navigation": [],
            "auth_checks": [],
            "api_endpoints": [],
            "event_handlers": [],
        }

        files = code_analysis.get("files", [])

        for extractor in self.extractors:
            try:
                if extractor.supports_stack(tech_stack):
                    extracted = await extractor.extract(files, code_analysis)

                    # Merge results
                    for key in raw_data:
                        if key in extracted:
                            raw_data[key].extend(extracted[key])
            except Exception as e:
                logger.warning(f"Extractor {extractor.name} failed: {e}")

        # Deduplicate
        for key in raw_data:
            if isinstance(raw_data[key], list):
                raw_data[key] = self._deduplicate(raw_data[key])

        return raw_data

    async def _analyze_with_vicky(
        self,
        raw_extraction: Dict[str, Any],
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Vicky analyzes UI/UX patterns and screen flows.

        Returns synthesized screen flows and UX insights.
        """
        result = {
            "personas_from_ui": [],
            "screen_flows": [],
            "ux_patterns": [],
            "accessibility_notes": [],
        }

        try:
            # Try to get Vicky extension via router
            router = getattr(context, "router", None)
            if router:
                from ..extensions import WorkflowRouter
                if isinstance(router, WorkflowRouter):
                    extensions = await router.get_extensions_for_agents(["Vicky"])
                    vicky = extensions[0] if extensions else None

                    if vicky:
                        vicky_result = await vicky.run_full_lifecycle(
                            task="Analyze UI patterns and extract user personas and screen flows",
                            context={
                                "screens": raw_extraction.get("screens", []),
                                "forms": raw_extraction.get("forms", []),
                                "navigation": raw_extraction.get("navigation", []),
                                "roles": raw_extraction.get("roles", []),
                                "vicky_activity": "journey_mapping",
                                "tier": "PROFESSIONAL",
                            },
                            entry_id=f"{context.workflow_id}-vicky-journey",
                        )

                        if vicky_result.success:
                            result["personas_from_ui"] = vicky_result.output.get("personas", [])
                            result["screen_flows"] = vicky_result.output.get("screen_flows", [])
                            result["ux_patterns"] = vicky_result.output.get("patterns", [])
                            return result

        except Exception as e:
            logger.warning(f"Vicky analysis failed: {e}")

        # Fallback: Generate basic screen flows from navigation
        result["screen_flows"] = self._generate_basic_screen_flows(raw_extraction)
        result["personas_from_ui"] = self._infer_personas_from_roles(raw_extraction)

        return result

    async def _define_with_peter(
        self,
        raw_extraction: Dict[str, Any],
        vicky_result: Dict[str, Any],
        domains: Dict[str, Any],
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Peter defines business journeys per persona.

        Returns structured personas and journeys.
        """
        result = {
            "personas": [],
            "journeys": [],
            "business_processes": [],
        }

        try:
            # Try to get Peter extension via router
            router = getattr(context, "router", None)
            if router:
                from ..extensions import WorkflowRouter
                if isinstance(router, WorkflowRouter):
                    extensions = await router.get_extensions_for_agents(["Peter"])
                    peter = extensions[0] if extensions else None

                    if peter:
                        peter_result = await peter.run_full_lifecycle(
                            task="Define user journeys for each persona based on domains and UI analysis",
                            context={
                                "domains": domains.get("domains", []),
                                "business_capabilities": domains.get("business_capabilities", []),
                                "personas_from_ui": vicky_result.get("personas_from_ui", []),
                                "screen_flows": vicky_result.get("screen_flows", []),
                                "roles": raw_extraction.get("roles", []),
                                "api_endpoints": raw_extraction.get("api_endpoints", []),
                                "activity": "user_journeys",
                            },
                            entry_id=f"{context.workflow_id}-peter-journey",
                        )

                        if peter_result.success:
                            result["personas"] = peter_result.output.get("personas", [])
                            result["journeys"] = peter_result.output.get("journeys", [])
                            result["business_processes"] = peter_result.output.get(
                                "business_processes", []
                            )
                            return result

        except Exception as e:
            logger.warning(f"Peter journey definition failed: {e}")

        # Fallback: Generate basic journeys from extracted data
        result["personas"] = self._generate_basic_personas(raw_extraction, vicky_result)
        result["journeys"] = self._generate_basic_journeys(raw_extraction, vicky_result, result["personas"])

        return result

    def _apply_enrichment(
        self,
        peter_result: Dict[str, Any],
        enrichment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enrich journeys with Migration 8-questions context.

        Enrichment sources:
        - Q5: Why migrate? → Journey improvement priorities
        - Q6: Stakeholders? → Persona business impact
        - Q7: Success criteria? → Journey success metrics
        - Q8: Timeline? → Journey migration priority
        """
        answers = enrichment.get("answers", {})

        # Enrich personas with stakeholder info
        enriched_personas = []
        for persona in peter_result.get("personas", []):
            enriched = {**persona}

            # Match stakeholder to persona
            stakeholders = answers.get("q6_stakeholders", "") or answers.get("stakeholders", "")
            persona_name = persona.get("name", "").lower()
            if persona_name and persona_name in stakeholders.lower():
                enriched["stakeholder_notes"] = stakeholders
                enriched["business_impact"] = "high"

            enriched_personas.append(enriched)

        # Enrich journeys with migration context
        enriched_journeys = []
        for journey in peter_result.get("journeys", []):
            enriched = {**journey}

            # Add migration drivers from Q5
            problem = answers.get("q5_problem_statement", "") or answers.get("problem_statement", "")
            if problem:
                enriched["migration_notes"] = problem

            # Add success criteria from Q7
            success = answers.get("q7_success_criteria", "") or answers.get("success_criteria", "")
            if success:
                enriched["success_criteria"] = enriched.get("success_criteria", [])
                if isinstance(enriched["success_criteria"], list):
                    enriched["success_criteria"].append(f"Migration: {success}")

            # Calculate priority based on Q8 timeline
            timeline = answers.get("q8_timeline", "") or answers.get("timeline", "")
            if timeline:
                timeline_lower = timeline.lower()
                if "critical" in timeline_lower or "urgent" in timeline_lower:
                    enriched["migration_priority"] = "must_have"
                elif "important" in timeline_lower:
                    enriched["migration_priority"] = "should_have"
                else:
                    enriched["migration_priority"] = "nice_to_have"

            # Add target improvements from migration goals
            migration_goals = answers.get("migration_goals", "") or answers.get("q4_goals", "")
            if migration_goals:
                enriched["target_improvements"] = enriched.get("target_improvements", [])
                if isinstance(enriched["target_improvements"], list):
                    if isinstance(migration_goals, list):
                        enriched["target_improvements"].extend(migration_goals)
                    else:
                        enriched["target_improvements"].append(migration_goals)

            enriched_journeys.append(enriched)

        return {
            **peter_result,
            "personas": enriched_personas,
            "journeys": enriched_journeys,
        }

    def _build_result(
        self,
        raw_extraction: Dict[str, Any],
        vicky_result: Dict[str, Any],
        peter_result: Dict[str, Any],
    ) -> UserJourneyExtractionResult:
        """Build final UserJourneyExtractionResult."""

        # Build personas
        personas = [
            self._dict_to_persona(p)
            for p in peter_result.get("personas", [])
        ]

        # Build journeys
        journeys = [
            self._dict_to_journey(j)
            for j in peter_result.get("journeys", [])
        ]

        # Build screens
        screens = [
            self._dict_to_screen(s)
            for s in raw_extraction.get("screens", [])
        ]

        # Build screen flows
        screen_flows = [
            self._dict_to_screen_flow(f)
            for f in vicky_result.get("screen_flows", [])
        ]

        # Build role matrix
        role_matrix = self._build_role_matrix(
            raw_extraction.get("roles", []),
            raw_extraction.get("auth_checks", []),
            screens,
        )

        # Calculate statistics
        total_steps = sum(len(j.steps) for j in journeys)

        # Calculate confidence
        confidence = self._calculate_confidence(
            personas, journeys, screens, raw_extraction
        )

        # Identify gaps
        gaps = self._identify_gaps(personas, journeys, screens, raw_extraction)

        return UserJourneyExtractionResult(
            personas=personas,
            journeys=journeys,
            screens=screens,
            screen_flows=screen_flows,
            role_matrix=role_matrix,
            total_personas=len(personas),
            total_journeys=len(journeys),
            total_screens=len(screens),
            total_steps=total_steps,
            extraction_confidence=confidence,
            coverage_percentage=self._calculate_coverage(raw_extraction),
            gaps=gaps,
        )

    def _dict_to_persona(self, data: Dict[str, Any]) -> Persona:
        """Convert dict to Persona dataclass."""
        persona_type = data.get("type", "customer")
        if isinstance(persona_type, str):
            try:
                persona_type = PersonaType(persona_type.lower())
            except ValueError:
                persona_type = PersonaType.CUSTOMER

        return Persona(
            id=data.get("id", f"persona_{self._safe_hash(data.get('name', 'unknown'))}"),
            name=data.get("name", "Unknown"),
            type=persona_type,
            role_code=data.get("role_code", data.get("role", "USER")),
            goals=data.get("goals", []),
            pain_points=data.get("pain_points", []),
            technical_proficiency=data.get("technical_proficiency", "medium"),
            usage_frequency=data.get("usage_frequency", "daily"),
            permissions=data.get("permissions", []),
            accessible_screens=data.get("accessible_screens", []),
            accessible_features=data.get("accessible_features", []),
            evidence=data.get("evidence", []),
            confidence=data.get("confidence", 0.7),
            stakeholder_notes=data.get("stakeholder_notes"),
            business_impact=data.get("business_impact"),
        )

    def _dict_to_journey(self, data: Dict[str, Any]) -> UserJourney:
        """Convert dict to UserJourney dataclass."""
        steps = [
            self._dict_to_step(s, i)
            for i, s in enumerate(data.get("steps", []))
        ]

        error_paths = [
            self._dict_to_error_path(e)
            for e in data.get("error_paths", [])
        ]

        complexity = data.get("complexity", "moderate")
        if isinstance(complexity, str):
            try:
                complexity = JourneyComplexity(complexity.lower())
            except ValueError:
                complexity = JourneyComplexity.MODERATE

        return UserJourney(
            id=data.get("id", f"journey_{self._safe_hash(data.get('name', 'unknown'))}"),
            name=data.get("name", "Unknown Journey"),
            description=data.get("description", ""),
            persona_id=data.get("persona_id", ""),
            persona_name=data.get("persona_name", ""),
            complexity=complexity,
            business_value=data.get("business_value", "medium"),
            frequency=data.get("frequency", "unknown"),
            trigger=data.get("trigger", ""),
            trigger_type=data.get("trigger_type", "user_initiated"),
            preconditions=data.get("preconditions", []),
            steps=steps,
            happy_path=data.get("happy_path", [s.id for s in steps]),
            error_paths=error_paths,
            alternative_paths=data.get("alternative_paths", []),
            screens_involved=data.get("screens_involved", []),
            success_criteria=data.get("success_criteria", []),
            outcome=data.get("outcome", ""),
            estimated_duration_minutes=data.get("estimated_duration_minutes", 5),
            sla_minutes=data.get("sla_minutes"),
            required_integrations=data.get("required_integrations", []),
            required_permissions=data.get("required_permissions", []),
            migration_priority=data.get("migration_priority"),
            migration_notes=data.get("migration_notes"),
            target_improvements=data.get("target_improvements", []),
            evidence=data.get("evidence", []),
            confidence=data.get("confidence", 0.7),
        )

    def _dict_to_step(self, data: Dict[str, Any], sequence: int) -> JourneyStep:
        """Convert dict to JourneyStep dataclass."""
        interaction_type = data.get("interaction_type", "view")
        if isinstance(interaction_type, str):
            try:
                interaction_type = InteractionType(interaction_type.lower())
            except ValueError:
                interaction_type = InteractionType.VIEW

        return JourneyStep(
            id=data.get("id", f"step_{sequence}"),
            sequence=sequence,
            action=data.get("action", ""),
            interaction_type=interaction_type,
            actor=data.get("actor", "user"),
            screen_id=data.get("screen_id", ""),
            screen_name=data.get("screen_name", data.get("screen", "")),
            system_action=data.get("system_action"),
            api_calls=data.get("api_calls", []),
            database_operations=data.get("database_operations", []),
            validations=data.get("validations", []),
            business_rules=data.get("business_rules", []),
            next_steps=data.get("next_steps", []),
            conditions=data.get("conditions", {}),
            estimated_duration_seconds=data.get("estimated_duration_seconds", 30),
            code_references=data.get("code_references", []),
        )

    def _dict_to_error_path(self, data: Dict[str, Any]) -> ErrorPath:
        """Convert dict to ErrorPath dataclass."""
        return ErrorPath(
            id=data.get("id", f"error_{self._safe_hash(data.get('trigger_condition', 'unknown'))}"),
            trigger_step_id=data.get("trigger_step_id", ""),
            trigger_condition=data.get("trigger_condition", ""),
            error_type=data.get("error_type", "validation"),
            error_screen_id=data.get("error_screen_id"),
            error_message=data.get("error_message", ""),
            recovery_options=data.get("recovery_options", []),
            can_retry=data.get("can_retry", True),
            data_rollback_required=data.get("data_rollback_required", False),
            notification_required=data.get("notification_required", False),
        )

    def _dict_to_screen(self, data: Dict[str, Any]) -> ScreenInfo:
        """Convert dict to ScreenInfo dataclass."""
        return ScreenInfo(
            id=data.get("id", f"screen_{self._safe_hash(data.get('name', 'unknown'))}"),
            name=data.get("name", "Unknown"),
            display_name=data.get("display_name", data.get("name", "")),
            file_path=data.get("file_path", ""),
            screen_type=data.get("screen_type", "form"),
            requires_auth=data.get("requires_auth", True),
            allowed_roles=data.get("allowed_roles", []),
            forms=data.get("forms", []),
            buttons=data.get("buttons", []),
            data_displays=data.get("data_displays", []),
            navigation_links=data.get("navigation_links", []),
            data_sources=data.get("data_sources", []),
            input_fields=data.get("input_fields", []),
            validations=data.get("validations", []),
            evidence=data.get("evidence", []),
        )

    def _dict_to_screen_flow(self, data: Dict[str, Any]) -> ScreenFlow:
        """Convert dict to ScreenFlow dataclass."""
        return ScreenFlow(
            id=data.get("id", f"flow_{self._safe_hash(data.get('name', 'unknown'))}"),
            name=data.get("name", "Unknown Flow"),
            screens=data.get("screens", []),
            transitions=data.get("transitions", []),
            flow_type=data.get("flow_type", "linear"),
            entry_points=data.get("entry_points", []),
            exit_points=data.get("exit_points", []),
            personas=data.get("personas", []),
        )

    def _build_role_matrix(
        self,
        roles: List[Dict],
        auth_checks: List[Dict],
        screens: List[ScreenInfo],
    ) -> RolePermissionMatrix:
        """Build role-permission matrix from extracted data."""
        role_names = list(set(r.get("name", "") for r in roles if r.get("name")))

        # Extract permissions from auth checks
        permissions = list(set(
            a.get("permission", "")
            for a in auth_checks
            if a.get("permission")
        ))

        # Build matrix
        matrix = {}
        screen_access = {}
        feature_access = {}

        for role in role_names:
            matrix[role] = []
            screen_access[role] = []
            feature_access[role] = []

            # Find permissions for this role
            for check in auth_checks:
                if check.get("role") == role:
                    if check.get("permission"):
                        matrix[role].append(check["permission"])
                    if check.get("screen"):
                        screen_access[role].append(check["screen"])
                    if check.get("feature"):
                        feature_access[role].append(check["feature"])

            # Add screens that allow this role
            for screen in screens:
                if role in screen.allowed_roles:
                    if screen.id not in screen_access[role]:
                        screen_access[role].append(screen.id)

        return RolePermissionMatrix(
            roles=role_names,
            permissions=permissions,
            matrix=matrix,
            screen_access=screen_access,
            feature_access=feature_access,
            evidence=[],
        )

    def _calculate_confidence(
        self,
        personas: List[Persona],
        journeys: List[UserJourney],
        screens: List[ScreenInfo],
        raw_extraction: Dict[str, Any],
    ) -> float:
        """Calculate overall extraction confidence."""
        scores = []

        # Persona confidence
        if personas:
            persona_conf = sum(p.confidence for p in personas) / len(personas)
            scores.append(persona_conf)
        else:
            scores.append(0.0)

        # Journey confidence
        if journeys:
            journey_conf = sum(j.confidence for j in journeys) / len(journeys)
            scores.append(journey_conf)
        else:
            scores.append(0.0)

        # Data completeness
        completeness = 0.0
        if raw_extraction.get("roles"):
            completeness += 0.2
        if raw_extraction.get("screens"):
            completeness += 0.2
        if raw_extraction.get("navigation"):
            completeness += 0.2
        if raw_extraction.get("auth_checks"):
            completeness += 0.2
        if raw_extraction.get("api_endpoints"):
            completeness += 0.2
        scores.append(completeness)

        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_coverage(self, raw_extraction: Dict[str, Any]) -> float:
        """Calculate code coverage percentage."""
        total_items = sum(
            len(v) for v in raw_extraction.values()
            if isinstance(v, list)
        )
        return min(100.0, total_items / 10 * 100)  # Simplified

    def _identify_gaps(
        self,
        personas: List[Persona],
        journeys: List[UserJourney],
        screens: List[ScreenInfo],
        raw_extraction: Dict[str, Any],
    ) -> List[str]:
        """Identify gaps in extracted data."""
        gaps = []

        # Check for personas without journeys
        persona_ids = {p.id for p in personas}
        journey_persona_ids = {j.persona_id for j in journeys}
        orphan_personas = persona_ids - journey_persona_ids
        if orphan_personas:
            gaps.append(f"Personas without journeys: {len(orphan_personas)}")

        # Check for screens without roles
        screens_without_roles = [s for s in screens if not s.allowed_roles]
        if screens_without_roles:
            gaps.append(f"Screens without role assignment: {len(screens_without_roles)}")

        # Check for journeys without steps
        journeys_without_steps = [j for j in journeys if not j.steps]
        if journeys_without_steps:
            gaps.append(f"Journeys without steps: {len(journeys_without_steps)}")

        # Check for missing role definitions
        roles_in_checks = {c.get("role", "") for c in raw_extraction.get("auth_checks", [])}
        defined_roles = {r.get("name", "") for r in raw_extraction.get("roles", [])}
        undefined_roles = roles_in_checks - defined_roles - {""}
        if undefined_roles:
            gaps.append(f"Roles used but not defined: {', '.join(undefined_roles)}")

        return gaps

    def _deduplicate(self, items: List[Dict]) -> List[Dict]:
        """Remove duplicates from list of dicts."""
        seen = set()
        result = []
        for item in items:
            key = item.get("id") or item.get("name") or str(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    def _safe_hash(self, value: str) -> str:
        """Generate safe hash string for IDs."""
        return str(abs(hash(value)))[:12]

    # Fallback generation methods

    def _generate_basic_screen_flows(
        self,
        raw_extraction: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate basic screen flows from navigation data."""
        flows = []
        navigation = raw_extraction.get("navigation", [])

        # Group by source
        by_source: Dict[str, List[str]] = {}
        for nav in navigation:
            source = nav.get("from", "")
            target = nav.get("to", "")
            if source and target:
                if source not in by_source:
                    by_source[source] = []
                if target not in by_source[source]:
                    by_source[source].append(target)

        # Create flows from connected screens
        flow_idx = 0
        processed = set()
        for source, targets in by_source.items():
            if source not in processed:
                flow_screens = [source] + targets
                flows.append({
                    "id": f"flow_{flow_idx}",
                    "name": f"Flow from {source.split('/')[-1]}",
                    "screens": flow_screens,
                    "flow_type": "linear" if len(targets) == 1 else "branching",
                    "entry_points": [source],
                    "exit_points": [t for t in targets if t not in by_source],
                })
                processed.add(source)
                flow_idx += 1

        return flows

    def _infer_personas_from_roles(
        self,
        raw_extraction: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Infer personas from extracted roles."""
        personas = []
        roles = raw_extraction.get("roles", [])

        role_persona_mapping = {
            "ADMIN": ("Administrator", PersonaType.ADMINISTRATOR),
            "ADMINISTRATOR": ("Administrator", PersonaType.ADMINISTRATOR),
            "USER": ("Standard User", PersonaType.CUSTOMER),
            "CUSTOMER": ("Customer", PersonaType.CUSTOMER),
            "EMPLOYEE": ("Employee", PersonaType.EMPLOYEE),
            "MANAGER": ("Manager", PersonaType.EMPLOYEE),
            "PARTNER": ("Partner", PersonaType.PARTNER),
            "GUEST": ("Guest", PersonaType.GUEST),
            "ANONYMOUS": ("Anonymous User", PersonaType.GUEST),
        }

        for role in roles:
            role_name = role.get("name", "").upper()
            if role_name in role_persona_mapping:
                name, persona_type = role_persona_mapping[role_name]
            else:
                name = role.get("name", "Unknown").title()
                persona_type = PersonaType.CUSTOMER

            personas.append({
                "id": f"persona_{self._safe_hash(role_name)}",
                "name": name,
                "type": persona_type.value,
                "role_code": role_name,
                "confidence": 0.6,
            })

        return personas

    def _generate_basic_personas(
        self,
        raw_extraction: Dict[str, Any],
        vicky_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate basic personas from roles and UI analysis."""
        # Start with UI-inferred personas
        personas = vicky_result.get("personas_from_ui", [])

        # Add any missing roles
        existing_roles = {p.get("role_code", "").upper() for p in personas}
        for role in raw_extraction.get("roles", []):
            role_name = role.get("name", "").upper()
            if role_name and role_name not in existing_roles:
                personas.append({
                    "id": f"persona_{self._safe_hash(role_name)}",
                    "name": role_name.title().replace("_", " "),
                    "type": "customer",
                    "role_code": role_name,
                    "confidence": 0.5,
                })
                existing_roles.add(role_name)

        return personas

    def _generate_basic_journeys(
        self,
        raw_extraction: Dict[str, Any],
        vicky_result: Dict[str, Any],
        personas: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate basic journeys from screen flows."""
        journeys = []
        screen_flows = vicky_result.get("screen_flows", [])

        for i, flow in enumerate(screen_flows):
            # Use first persona or default
            persona = personas[0] if personas else {"id": "default", "name": "User"}

            journey = {
                "id": f"journey_{i}",
                "name": flow.get("name", f"Journey {i + 1}"),
                "description": f"User flow through {len(flow.get('screens', []))} screens",
                "persona_id": persona.get("id"),
                "persona_name": persona.get("name"),
                "complexity": "moderate",
                "screens_involved": flow.get("screens", []),
                "steps": [
                    {
                        "id": f"step_{j}",
                        "action": f"Navigate to {screen.split('/')[-1] if '/' in screen else screen}",
                        "interaction_type": "navigate",
                        "screen_id": screen,
                        "screen_name": screen.split("/")[-1] if "/" in screen else screen,
                    }
                    for j, screen in enumerate(flow.get("screens", []))
                ],
                "confidence": 0.5,
            }
            journeys.append(journey)

        return journeys

    def _summarize_raw_extraction(self, raw_extraction: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize raw extraction for stage result."""
        return {
            "roles_count": len(raw_extraction.get("roles", [])),
            "screens_count": len(raw_extraction.get("screens", [])),
            "navigation_count": len(raw_extraction.get("navigation", [])),
            "auth_checks_count": len(raw_extraction.get("auth_checks", [])),
            "api_endpoints_count": len(raw_extraction.get("api_endpoints", [])),
        }

    def _summarize_peter_result(self, peter_result: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize Peter result for stage result."""
        return {
            "personas_count": len(peter_result.get("personas", [])),
            "journeys_count": len(peter_result.get("journeys", [])),
            "business_processes_count": len(peter_result.get("business_processes", [])),
        }
