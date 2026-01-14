"""
Vicky Extension - Visual Designer/Validator Specialist.

Wraps design and validation services for Confucius orchestrator integration.
Handles UI/UX design, design tokens, and visual validation.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


class VickyExtension(BaseAgentExtension):
    """
    Vicky - Visual Designer/Validator Agent Extension.

    Capabilities:
    - UI specification creation
    - Design token generation
    - Application shell configuration
    - Sample data generation
    - Visual validation
    - Responsive design verification

    Position in workflow: Between Peter (Product) and Felix (Architecture).
    """

    def __init__(self):
        """Initialize Vicky extension."""
        super().__init__(
            ExtensionMetadata(
                name="Vicky",
                description="Visual Designer - UI specs, design tokens, validation",
                capabilities=[
                    "ui_specification",
                    "design_token_generation",
                    "application_shell",
                    "sample_data_generation",
                    "visual_validation",
                    "responsive_verification",
                    "wireframe_generation",
                    "style_guide_creation",
                ],
                domains=[
                    "design",
                    "ui",
                    "ux",
                    "visual",
                    "tokens",
                    "wireframe",
                    "responsive",
                    "style",
                ],
                priority=5,
                parallel_safe=True,
                timeout_seconds=90,
                version="1.0.0",
            )
        )
        self._vicky_service = None

    def _get_vicky_service(self):
        """Lazy load Vicky service."""
        if self._vicky_service is None:
            try:
                from app.services.design_os_service import VickyAgentService
                # Note: VickyAgentService requires a db session
                # We'll handle this at runtime
                self._vicky_service = None  # Will be set per request
            except ImportError as e:
                logger.warning(f"Could not import VickyAgentService: {e}")
        return self._vicky_service

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for Vicky design work."""
        modified = context.copy()

        # Determine design activity
        activity = self._determine_activity(task)
        modified["vicky_activity"] = activity

        # Set tier if not specified
        if "tier" not in modified:
            modified["tier"] = "STANDARD"

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute design activities."""
        activity = context.get("vicky_activity", "general")

        try:
            if activity == "ui_spec":
                result = await self._create_ui_spec(context)
            elif activity == "design_tokens":
                result = await self._generate_design_tokens(context)
            elif activity == "application_shell":
                result = await self._create_application_shell(context)
            elif activity == "sample_data":
                result = await self._generate_sample_data(context)
            elif activity == "validation":
                result = await self._validate_design(context)
            else:
                result = await self._general_design_work(task, context)

            self.update_partial({
                "design_complete": True,
                "activity": activity,
            })

            return {
                "success": True,
                "activity": activity,
                "result": result,
                "agent": "Vicky",
            }

        except Exception as e:
            logger.error(f"Vicky design work failed: {e}")
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
        """Parse Vicky output into structured format."""
        if not raw_output.get("success"):
            return raw_output

        result = raw_output.get("result", {})
        parsed = raw_output.copy()

        parsed["ui_specs"] = result.get("ui_specs", [])
        parsed["design_tokens"] = result.get("design_tokens", {})
        parsed["shell_config"] = result.get("shell_config", {})
        parsed["validation_results"] = result.get("validation_results", [])

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Post-processing: Record design artifacts."""
        if executed_output.get("success"):
            spec_count = len(executed_output.get("ui_specs", []))
            token_count = len(executed_output.get("design_tokens", {}))

            executed_output["vicky_summary"] = {
                "ui_specs_created": spec_count,
                "design_tokens_generated": token_count,
                "activity": executed_output.get("activity"),
                "tier": executed_output.get("result", {}).get("tier", "STANDARD"),
                "entry_id": entry_id,
            }

            logger.info(
                f"Vicky completed: {spec_count} specs, "
                f"{token_count} design tokens"
            )

        return executed_output

    def _determine_activity(self, task: str) -> str:
        """Determine design activity from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["ui spec", "specification", "screen"]):
            return "ui_spec"
        elif any(kw in task_lower for kw in ["token", "color", "typography", "spacing"]):
            return "design_tokens"
        elif any(kw in task_lower for kw in ["shell", "layout", "navigation"]):
            return "application_shell"
        elif any(kw in task_lower for kw in ["sample data", "mock", "test data"]):
            return "sample_data"
        elif any(kw in task_lower for kw in ["validate", "check", "verify"]):
            return "validation"
        else:
            return "general"

    async def _create_ui_spec(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create UI specification."""
        return {
            "ui_specs": [],
            "tier": context.get("tier", "STANDARD"),
            "sections": [],
        }

    async def _generate_design_tokens(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate design tokens."""
        preset = context.get("preset", "minimal")
        return {
            "design_tokens": {
                "colors": {},
                "typography": {},
                "spacing": {},
                "shadows": {},
                "borders": {},
            },
            "preset": preset,
            "tier": context.get("tier", "STANDARD"),
        }

    async def _create_application_shell(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create application shell configuration."""
        tier = context.get("tier", "STANDARD")
        if tier not in ["PROFESSIONAL", "PREMIUM"]:
            return {
                "shell_config": {},
                "status": "skipped",
                "message": "Application shell requires PROFESSIONAL tier or higher",
            }

        return {
            "shell_config": {
                "type": "sidebar",
                "navigation": [],
                "header": {},
                "footer": {},
            },
            "tier": tier,
        }

    async def _generate_sample_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sample data."""
        tier = context.get("tier", "STANDARD")
        if tier == "FREE":
            return {
                "sample_data": [],
                "status": "skipped",
                "message": "Sample data requires BASIC tier or higher",
            }

        return {
            "sample_data": [],
            "entities_generated": 0,
            "tier": tier,
        }

    async def _validate_design(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate design."""
        return {
            "validation_results": [],
            "is_valid": True,
            "issues": [],
            "suggestions": [],
        }

    async def _general_design_work(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute general design work."""
        return {
            "ui_specs": [],
            "design_tokens": {},
            "tier": context.get("tier", "STANDARD"),
        }
