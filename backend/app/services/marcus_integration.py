"""
Marcus Agent Integration Service

Integrates Marcus (Maintenance Specialist Agent) with the scheduler service.
Marcus handles:
- Code maintenance & tech debt analysis
- Dependency updates & security patches
- Refactoring recommendations
- Code health monitoring

Uses Ollama qwen2.5-coder:7b for local LLM processing.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum
import asyncio
import logging
import json
import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

class MaintenanceScope(str, Enum):
    """Scope of maintenance scan"""
    FULL_CODEBASE = "full_codebase"
    MODULE = "module"
    SPECIFIC_FILES = "specific_files"


class FocusArea(str, Enum):
    """Focus areas for maintenance"""
    DEPENDENCIES = "dependencies"
    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    TECH_DEBT = "tech_debt"
    TESTING = "testing"


class Urgency(str, Enum):
    """Urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Marcus agent configuration
MARCUS_CONFIG = {
    "name": "Marcus",
    "role": "Maintenance Specialist",
    "llm": "qwen2.5-coder:7b",
    "ollama_url": "http://localhost:11434/api/generate",
    "specialties": [
        "refactoring",
        "dependency_updates",
        "code_health",
        "tech_debt_reduction"
    ]
}

# System prompts for different maintenance tasks
MAINTENANCE_PROMPTS = {
    "dependencies": """You are Marcus, a Maintenance Specialist AI agent.
Analyze the following dependency information and provide recommendations:
- Identify outdated packages
- Flag security vulnerabilities
- Suggest update priorities
- Note breaking changes to watch for

Respond with JSON format:
{
    "findings": [{"package": str, "current": str, "latest": str, "severity": str, "recommendation": str}],
    "summary": str,
    "priority_updates": [str]
}""",

    "security": """You are Marcus, a Maintenance Specialist AI agent.
Analyze the following code for security issues:
- Identify potential vulnerabilities (OWASP Top 10)
- Check for hardcoded secrets
- Review authentication/authorization patterns
- Flag unsafe data handling

Respond with JSON format:
{
    "findings": [{"type": str, "severity": str, "location": str, "description": str, "recommendation": str}],
    "risk_score": float,
    "immediate_actions": [str]
}""",

    "code_quality": """You are Marcus, a Maintenance Specialist AI agent.
Analyze the following code for quality issues:
- Code smells and anti-patterns
- Complexity metrics
- DRY violations
- Naming conventions
- Documentation gaps

Respond with JSON format:
{
    "findings": [{"type": str, "severity": str, "location": str, "description": str, "fix_suggestion": str}],
    "quality_score": float,
    "refactoring_suggestions": [str]
}""",

    "tech_debt": """You are Marcus, a Maintenance Specialist AI agent.
Analyze the following for technical debt:
- Legacy patterns that need updating
- Missing tests
- Deprecated API usage
- Architecture issues
- Documentation debt

Respond with JSON format:
{
    "findings": [{"category": str, "severity": str, "effort": str, "impact": str, "description": str}],
    "total_debt_score": float,
    "prioritized_items": [str]
}"""
}


# ============================================================================
# MARCUS AGENT CLASS
# ============================================================================

class MarcusAgent:
    """
    Marcus - Maintenance Specialist Agent

    Integrates with Ollama for local LLM processing and the scheduler
    for automated maintenance scans.
    """

    def __init__(self, ollama_url: Optional[str] = None):
        """
        Initialize Marcus agent.

        Args:
            ollama_url: URL for Ollama API (default: localhost:11434)
        """
        self.config = MARCUS_CONFIG
        self.ollama_url = ollama_url or MARCUS_CONFIG["ollama_url"]
        self.is_available = False
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=120.0)
        return self._http_client

    async def check_availability(self) -> bool:
        """
        Check if Marcus (Ollama with qwen2.5-coder:7b) is available.

        Returns:
            True if available, False otherwise
        """
        try:
            client = await self._get_client()
            response = await client.get(
                "http://localhost:11434/api/tags",
                timeout=5.0
            )

            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]

                # Check if our model is available
                self.is_available = any(
                    "qwen2.5-coder" in m for m in models
                )

                if self.is_available:
                    logger.info("Marcus agent available (qwen2.5-coder found)")
                else:
                    logger.warning("Marcus agent unavailable (qwen2.5-coder not found)")

                return self.is_available

        except Exception as e:
            logger.error(f"Failed to check Marcus availability: {e}")
            self.is_available = False

        return False

    async def analyze(
        self,
        focus_area: FocusArea,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run Marcus analysis on content.

        Args:
            focus_area: Area to focus analysis on
            content: Content to analyze (code, dependencies, etc.)
            context: Additional context

        Returns:
            Analysis results
        """
        if not self.is_available:
            await self.check_availability()

        if not self.is_available:
            return {
                "success": False,
                "error": "Marcus agent not available (Ollama/qwen2.5-coder not running)"
            }

        # Get appropriate prompt
        system_prompt = MAINTENANCE_PROMPTS.get(
            focus_area.value,
            MAINTENANCE_PROMPTS["code_quality"]
        )

        # Build full prompt
        full_prompt = f"{system_prompt}\n\nContent to analyze:\n```\n{content}\n```"

        if context:
            full_prompt += f"\n\nAdditional context:\n{json.dumps(context, indent=2)}"

        try:
            client = await self._get_client()

            response = await client.post(
                self.ollama_url,
                json={
                    "model": self.config["llm"],
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Lower for more consistent analysis
                        "num_predict": 2000
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")

                # Try to parse JSON response
                try:
                    # Find JSON in response
                    start = response_text.find("{")
                    end = response_text.rfind("}") + 1
                    if start >= 0 and end > start:
                        json_str = response_text[start:end]
                        result = json.loads(json_str)
                        return {
                            "success": True,
                            "focus_area": focus_area.value,
                            "analysis": result,
                            "raw_response": response_text,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                except json.JSONDecodeError:
                    pass

                # Return raw response if JSON parsing fails
                return {
                    "success": True,
                    "focus_area": focus_area.value,
                    "analysis": {"raw": response_text},
                    "raw_response": response_text,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

            else:
                return {
                    "success": False,
                    "error": f"Ollama returned status {response.status_code}"
                }

        except Exception as e:
            logger.error(f"Marcus analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def run_maintenance_scan(
        self,
        scope: MaintenanceScope,
        focus_areas: List[FocusArea],
        urgency: Urgency,
        target_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a full maintenance scan.

        Args:
            scope: Scope of the scan
            focus_areas: Areas to analyze
            urgency: Priority level
            target_path: Optional specific path to scan

        Returns:
            Comprehensive scan results
        """
        scan_id = f"marcus_scan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now(timezone.utc)

        logger.info(f"Starting maintenance scan {scan_id} with scope {scope.value}")

        results = {
            "scan_id": scan_id,
            "scope": scope.value,
            "focus_areas": [f.value for f in focus_areas],
            "urgency": urgency.value,
            "target_path": target_path,
            "start_time": start_time.isoformat(),
            "findings": [],
            "summary": {},
            "status": "in_progress"
        }

        # Check availability first
        if not await self.check_availability():
            results["status"] = "failed"
            results["error"] = "Marcus agent not available"
            results["end_time"] = datetime.now(timezone.utc).isoformat()
            return results

        # Run analysis for each focus area
        all_findings = []
        for area in focus_areas:
            logger.info(f"Analyzing {area.value}...")

            # In a real implementation, this would read actual files
            # For now, we'll use a placeholder that would be replaced
            # with actual file content from the repository
            sample_content = self._get_sample_content(area, target_path)

            analysis = await self.analyze(
                focus_area=area,
                content=sample_content,
                context={
                    "scope": scope.value,
                    "urgency": urgency.value,
                    "target_path": target_path
                }
            )

            if analysis.get("success"):
                findings = analysis.get("analysis", {}).get("findings", [])
                all_findings.extend([
                    {**f, "focus_area": area.value}
                    for f in findings
                ])

                results["summary"][area.value] = {
                    "findings_count": len(findings),
                    "analysis": analysis.get("analysis", {})
                }
            else:
                results["summary"][area.value] = {
                    "error": analysis.get("error")
                }

        # Compile final results
        results["findings"] = all_findings
        results["status"] = "completed"
        results["end_time"] = datetime.now(timezone.utc).isoformat()
        results["duration_seconds"] = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()
        results["total_findings"] = len(all_findings)

        # Generate priority recommendations
        results["priority_actions"] = self._prioritize_findings(
            all_findings, urgency
        )

        logger.info(
            f"Scan {scan_id} completed with {len(all_findings)} findings"
        )

        return results

    def _get_sample_content(
        self,
        area: FocusArea,
        target_path: Optional[str]
    ) -> str:
        """
        Get content to analyze for a focus area.

        In production, this would read actual files from the codebase.
        """
        # This is a placeholder - in real implementation,
        # would use file system access to read actual code
        samples = {
            FocusArea.DEPENDENCIES: """
# requirements.txt
fastapi==0.68.0
pydantic==1.8.2
sqlalchemy==1.4.22
httpx==0.18.2
uvicorn==0.14.0
""",
            FocusArea.SECURITY: """
# Example code for security analysis
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection risk
    return db.execute(query)

API_KEY = "sk-1234567890"  # Hardcoded secret
""",
            FocusArea.CODE_QUALITY: """
# Example code for quality analysis
def process_data(data):
    result = []
    for item in data:
        if item['type'] == 'A':
            result.append({'value': item['value'] * 2})
        elif item['type'] == 'B':
            result.append({'value': item['value'] * 3})
        elif item['type'] == 'C':
            result.append({'value': item['value'] * 4})
    return result
""",
            FocusArea.TECH_DEBT: """
# TODO: Refactor this legacy code
# FIXME: This is a temporary workaround
# HACK: Quick fix for deadline
def legacy_function():
    pass  # Needs implementation
"""
        }

        return samples.get(area, "# No content available for analysis")

    def _prioritize_findings(
        self,
        findings: List[Dict[str, Any]],
        urgency: Urgency
    ) -> List[str]:
        """
        Prioritize findings based on severity and urgency.
        """
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        sorted_findings = sorted(
            findings,
            key=lambda f: severity_order.get(
                f.get("severity", "low").lower(), 4
            )
        )

        # Get top priority items based on urgency
        limit = {
            Urgency.CRITICAL: 10,
            Urgency.HIGH: 7,
            Urgency.MEDIUM: 5,
            Urgency.LOW: 3
        }.get(urgency, 5)

        return [
            f.get("description", f.get("recommendation", "Unknown finding"))
            for f in sorted_findings[:limit]
        ]

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_marcus_instance: Optional[MarcusAgent] = None


def get_marcus_agent() -> MarcusAgent:
    """Get or create Marcus agent singleton."""
    global _marcus_instance
    if _marcus_instance is None:
        _marcus_instance = MarcusAgent()
    return _marcus_instance


# ============================================================================
# SCHEDULER INTEGRATION FUNCTIONS
# ============================================================================

async def run_scheduled_maintenance(
    scope: str,
    focus_areas: List[str],
    urgency: str
) -> Dict[str, Any]:
    """
    Entry point for scheduled maintenance scans.

    Called by scheduler_service when a maintenance job runs.

    Args:
        scope: Scope string
        focus_areas: List of focus area strings
        urgency: Urgency string

    Returns:
        Scan results
    """
    marcus = get_marcus_agent()

    # Convert strings to enums
    scope_enum = MaintenanceScope(scope)
    focus_enum = [FocusArea(f) for f in focus_areas]
    urgency_enum = Urgency(urgency)

    # Broadcast scan started event
    try:
        from app.api.websocket import broadcast_scan_started
        await broadcast_scan_started(
            scan_id=f"scheduled_{datetime.now(timezone.utc).isoformat()}",
            scope=scope,
            focus_areas=focus_areas
        )
    except ImportError:
        pass

    # Run the scan
    results = await marcus.run_maintenance_scan(
        scope=scope_enum,
        focus_areas=focus_enum,
        urgency=urgency_enum
    )

    # Broadcast completion
    try:
        from app.api.websocket import broadcast_scan_completed
        await broadcast_scan_completed(
            scan_id=results.get("scan_id", ""),
            findings_count=results.get("total_findings", 0),
            tasks_created=0,  # Tasks would be created in a full implementation
            duration_seconds=results.get("duration_seconds", 0)
        )
    except ImportError:
        pass

    return results


async def check_marcus_status() -> Dict[str, Any]:
    """
    Check Marcus agent status.

    Returns:
        Status information
    """
    marcus = get_marcus_agent()
    is_available = await marcus.check_availability()

    return {
        "agent": marcus.config["name"],
        "role": marcus.config["role"],
        "llm": marcus.config["llm"],
        "available": is_available,
        "specialties": marcus.config["specialties"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
