"""
Project Profile Model - Centralized Agent Configuration

Defines project size and focus areas that influence ALL agent behavior
throughout the entire project lifecycle.

Usage:
    profile = ProjectProfile(
        size=ProjectSize.SMALL,
        focus_areas={
            FocusArea.SECURITY: StrictnessLevel.HIGH,
            FocusArea.USABILITY: StrictnessLevel.HIGH,
            FocusArea.SCALABILITY: StrictnessLevel.LOW
        }
    )

    # Get agent-specific config
    quinn_config = profile.get_agent_config("quinn")
"""

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


class ProjectSize(str, Enum):
    """Project size determines base agent strictness levels."""
    HOBBY = "hobby"           # Personal project, 1-2 devs, <100 users
    SMALL = "small"           # Small team, 2-5 devs, <1000 users
    MEDIUM = "medium"         # Medium team, 5-15 devs, <10K users
    LARGE = "large"           # Large team, 15-50 devs, <100K users
    ENTERPRISE = "enterprise" # Enterprise, 50+ devs, 100K+ users


class FocusArea(str, Enum):
    """Areas where extra attention can be configured."""
    SECURITY = "security"           # Auth, encryption, OWASP
    PERFORMANCE = "performance"     # Speed, latency, throughput
    SCALABILITY = "scalability"     # Growth, load handling
    USABILITY = "usability"         # UX, accessibility, simplicity
    RELIABILITY = "reliability"     # Uptime, error handling, recovery
    MAINTAINABILITY = "maintainability"  # Code quality, docs, tests
    COMPLIANCE = "compliance"       # GDPR, HIPAA, SOC2, etc.
    COST = "cost"                   # Budget optimization


class StrictnessLevel(str, Enum):
    """How strict agents should be on a focus area."""
    IGNORE = "ignore"     # Don't evaluate this aspect
    RELAXED = "relaxed"   # Minimal checks, advisory only
    NORMAL = "normal"     # Standard evaluation
    STRICT = "strict"     # Thorough evaluation, block on issues
    CRITICAL = "critical" # Maximum scrutiny, mandatory compliance


@dataclass
class AgentConfig:
    """Configuration for a single agent based on project profile."""
    agent_name: str

    # Thresholds (adjusted per project size)
    min_quality_score: float = 6.0
    critical_issue_threshold: int = 3

    # Focus area strictness (adjusted per focus)
    strictness_by_area: Dict[FocusArea, StrictnessLevel] = field(default_factory=dict)

    # Review criteria weights (0.0 - 1.0)
    criteria_weights: Dict[str, float] = field(default_factory=dict)

    # Prompt modifiers
    context_instructions: str = ""

    def get_strictness(self, area: FocusArea) -> StrictnessLevel:
        """Get strictness level for a focus area."""
        return self.strictness_by_area.get(area, StrictnessLevel.NORMAL)

    def should_evaluate(self, area: FocusArea) -> bool:
        """Check if this area should be evaluated."""
        return self.get_strictness(area) != StrictnessLevel.IGNORE


@dataclass
class ProjectProfile:
    """
    Central configuration that influences all agent behavior.

    Set once at project creation, used throughout project lifecycle.
    """
    # Core settings
    size: ProjectSize
    focus_areas: Dict[FocusArea, StrictnessLevel] = field(default_factory=dict)

    # Project metadata
    project_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Budget/resource constraints
    budget_type: str = "volunteer"  # volunteer, startup, corporate, enterprise
    team_size: int = 1
    expected_users: int = 50
    timeline_weeks: int = 16

    def __post_init__(self):
        """Set default focus areas based on size if not provided."""
        if not self.focus_areas:
            self.focus_areas = self._default_focus_for_size()

    def _default_focus_for_size(self) -> Dict[FocusArea, StrictnessLevel]:
        """Get default focus area strictness based on project size."""
        defaults = {
            ProjectSize.HOBBY: {
                FocusArea.SECURITY: StrictnessLevel.RELAXED,
                FocusArea.PERFORMANCE: StrictnessLevel.IGNORE,
                FocusArea.SCALABILITY: StrictnessLevel.IGNORE,
                FocusArea.USABILITY: StrictnessLevel.NORMAL,
                FocusArea.RELIABILITY: StrictnessLevel.RELAXED,
                FocusArea.MAINTAINABILITY: StrictnessLevel.RELAXED,
                FocusArea.COMPLIANCE: StrictnessLevel.IGNORE,
                FocusArea.COST: StrictnessLevel.IGNORE,
            },
            ProjectSize.SMALL: {
                FocusArea.SECURITY: StrictnessLevel.NORMAL,
                FocusArea.PERFORMANCE: StrictnessLevel.RELAXED,
                FocusArea.SCALABILITY: StrictnessLevel.RELAXED,
                FocusArea.USABILITY: StrictnessLevel.NORMAL,
                FocusArea.RELIABILITY: StrictnessLevel.NORMAL,
                FocusArea.MAINTAINABILITY: StrictnessLevel.NORMAL,
                FocusArea.COMPLIANCE: StrictnessLevel.RELAXED,
                FocusArea.COST: StrictnessLevel.RELAXED,
            },
            ProjectSize.MEDIUM: {
                FocusArea.SECURITY: StrictnessLevel.STRICT,
                FocusArea.PERFORMANCE: StrictnessLevel.NORMAL,
                FocusArea.SCALABILITY: StrictnessLevel.NORMAL,
                FocusArea.USABILITY: StrictnessLevel.NORMAL,
                FocusArea.RELIABILITY: StrictnessLevel.STRICT,
                FocusArea.MAINTAINABILITY: StrictnessLevel.STRICT,
                FocusArea.COMPLIANCE: StrictnessLevel.NORMAL,
                FocusArea.COST: StrictnessLevel.NORMAL,
            },
            ProjectSize.LARGE: {
                FocusArea.SECURITY: StrictnessLevel.STRICT,
                FocusArea.PERFORMANCE: StrictnessLevel.STRICT,
                FocusArea.SCALABILITY: StrictnessLevel.STRICT,
                FocusArea.USABILITY: StrictnessLevel.NORMAL,
                FocusArea.RELIABILITY: StrictnessLevel.STRICT,
                FocusArea.MAINTAINABILITY: StrictnessLevel.STRICT,
                FocusArea.COMPLIANCE: StrictnessLevel.STRICT,
                FocusArea.COST: StrictnessLevel.NORMAL,
            },
            ProjectSize.ENTERPRISE: {
                FocusArea.SECURITY: StrictnessLevel.CRITICAL,
                FocusArea.PERFORMANCE: StrictnessLevel.STRICT,
                FocusArea.SCALABILITY: StrictnessLevel.CRITICAL,
                FocusArea.USABILITY: StrictnessLevel.NORMAL,
                FocusArea.RELIABILITY: StrictnessLevel.CRITICAL,
                FocusArea.MAINTAINABILITY: StrictnessLevel.STRICT,
                FocusArea.COMPLIANCE: StrictnessLevel.CRITICAL,
                FocusArea.COST: StrictnessLevel.STRICT,
            },
        }
        return defaults.get(self.size, defaults[ProjectSize.MEDIUM])

    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """
        Generate agent-specific configuration based on project profile.

        Args:
            agent_name: Name of agent (quinn, felix, eliza, tessa, etc.)

        Returns:
            AgentConfig with adjusted thresholds and strictness
        """
        # Base thresholds per size
        size_thresholds = {
            ProjectSize.HOBBY: {"min_score": 4.0, "critical_threshold": 5},
            ProjectSize.SMALL: {"min_score": 5.0, "critical_threshold": 4},
            ProjectSize.MEDIUM: {"min_score": 6.0, "critical_threshold": 3},
            ProjectSize.LARGE: {"min_score": 7.0, "critical_threshold": 2},
            ProjectSize.ENTERPRISE: {"min_score": 8.0, "critical_threshold": 1},
        }

        base = size_thresholds.get(self.size, size_thresholds[ProjectSize.MEDIUM])

        # Generate context instructions for prompts
        context = self._generate_context_instructions()

        return AgentConfig(
            agent_name=agent_name,
            min_quality_score=base["min_score"],
            critical_issue_threshold=base["critical_threshold"],
            strictness_by_area=self.focus_areas.copy(),
            criteria_weights=self._get_criteria_weights(agent_name),
            context_instructions=context
        )

    def _generate_context_instructions(self) -> str:
        """Generate prompt context based on project profile."""
        lines = [
            f"PROJECT SIZE: {self.size.value.upper()}",
            f"Team: {self.team_size} developers",
            f"Expected Users: {self.expected_users}",
            f"Budget: {self.budget_type}",
            f"Timeline: {self.timeline_weeks} weeks",
            "",
            "FOCUS AREA PRIORITIES:",
        ]

        # Sort by strictness (most strict first)
        strictness_order = {
            StrictnessLevel.CRITICAL: 0,
            StrictnessLevel.STRICT: 1,
            StrictnessLevel.NORMAL: 2,
            StrictnessLevel.RELAXED: 3,
            StrictnessLevel.IGNORE: 4,
        }

        sorted_areas = sorted(
            self.focus_areas.items(),
            key=lambda x: strictness_order.get(x[1], 2)
        )

        for area, strictness in sorted_areas:
            if strictness != StrictnessLevel.IGNORE:
                emoji = {
                    StrictnessLevel.CRITICAL: "🔴",
                    StrictnessLevel.STRICT: "🟠",
                    StrictnessLevel.NORMAL: "🟡",
                    StrictnessLevel.RELAXED: "🟢",
                }.get(strictness, "⚪")
                lines.append(f"  {emoji} {area.value}: {strictness.value}")

        lines.extend([
            "",
            "SCORING GUIDANCE:",
            f"- For {self.size.value} projects, be proportionate in your evaluation",
            f"- Focus areas marked STRICT/CRITICAL require thorough review",
            f"- Areas marked RELAXED/IGNORE need minimal attention",
            f"- Consider the {self.budget_type} budget and {self.team_size}-person team",
        ])

        return "\n".join(lines)

    def _get_criteria_weights(self, agent_name: str) -> Dict[str, float]:
        """Get criteria weights for specific agent."""
        # Map focus areas to review criteria
        area_to_criteria = {
            FocusArea.SECURITY: ["authentication", "encryption", "input_validation"],
            FocusArea.PERFORMANCE: ["response_time", "throughput", "caching"],
            FocusArea.SCALABILITY: ["horizontal_scaling", "load_handling", "data_volume"],
            FocusArea.USABILITY: ["user_experience", "accessibility", "simplicity"],
            FocusArea.RELIABILITY: ["uptime", "error_handling", "disaster_recovery"],
            FocusArea.MAINTAINABILITY: ["code_quality", "documentation", "test_coverage"],
            FocusArea.COMPLIANCE: ["gdpr", "data_protection", "audit_trails"],
            FocusArea.COST: ["infrastructure", "licensing", "operational"],
        }

        strictness_to_weight = {
            StrictnessLevel.CRITICAL: 1.0,
            StrictnessLevel.STRICT: 0.8,
            StrictnessLevel.NORMAL: 0.5,
            StrictnessLevel.RELAXED: 0.2,
            StrictnessLevel.IGNORE: 0.0,
        }

        weights = {}
        for area, strictness in self.focus_areas.items():
            weight = strictness_to_weight.get(strictness, 0.5)
            for criteria in area_to_criteria.get(area, []):
                weights[criteria] = weight

        return weights

    def to_dict(self) -> dict:
        """Convert to dictionary for storage/API."""
        return {
            "size": self.size.value,
            "focus_areas": {
                area.value: level.value
                for area, level in self.focus_areas.items()
            },
            "project_id": self.project_id,
            "budget_type": self.budget_type,
            "team_size": self.team_size,
            "expected_users": self.expected_users,
            "timeline_weeks": self.timeline_weeks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectProfile":
        """Create from dictionary."""
        focus_areas = {}
        if "focus_areas" in data:
            for area_str, level_str in data["focus_areas"].items():
                focus_areas[FocusArea(area_str)] = StrictnessLevel(level_str)

        return cls(
            size=ProjectSize(data["size"]),
            focus_areas=focus_areas,
            project_id=data.get("project_id"),
            budget_type=data.get("budget_type", "volunteer"),
            team_size=data.get("team_size", 1),
            expected_users=data.get("expected_users", 50),
            timeline_weeks=data.get("timeline_weeks", 16),
        )


# ============================================================================
# PRESET PROFILES
# ============================================================================

def get_preset_profile(preset_name: str) -> ProjectProfile:
    """Get a preset project profile."""
    presets = {
        "hobby": ProjectProfile(
            size=ProjectSize.HOBBY,
            budget_type="volunteer",
            team_size=1,
            expected_users=10,
            timeline_weeks=0,  # No deadline
        ),
        "club_app": ProjectProfile(
            size=ProjectSize.SMALL,
            focus_areas={
                FocusArea.USABILITY: StrictnessLevel.STRICT,
                FocusArea.SECURITY: StrictnessLevel.NORMAL,
                FocusArea.PERFORMANCE: StrictnessLevel.RELAXED,
                FocusArea.SCALABILITY: StrictnessLevel.RELAXED,
                FocusArea.RELIABILITY: StrictnessLevel.NORMAL,
                FocusArea.MAINTAINABILITY: StrictnessLevel.NORMAL,
                FocusArea.COMPLIANCE: StrictnessLevel.NORMAL,  # GDPR
                FocusArea.COST: StrictnessLevel.IGNORE,
            },
            budget_type="volunteer",
            team_size=2,
            expected_users=100,
            timeline_weeks=16,
        ),
        "startup_mvp": ProjectProfile(
            size=ProjectSize.SMALL,
            focus_areas={
                FocusArea.USABILITY: StrictnessLevel.STRICT,
                FocusArea.SECURITY: StrictnessLevel.NORMAL,
                FocusArea.PERFORMANCE: StrictnessLevel.NORMAL,
                FocusArea.SCALABILITY: StrictnessLevel.NORMAL,
                FocusArea.RELIABILITY: StrictnessLevel.NORMAL,
                FocusArea.MAINTAINABILITY: StrictnessLevel.RELAXED,
                FocusArea.COMPLIANCE: StrictnessLevel.RELAXED,
                FocusArea.COST: StrictnessLevel.STRICT,
            },
            budget_type="startup",
            team_size=3,
            expected_users=1000,
            timeline_weeks=8,
        ),
        "saas_product": ProjectProfile(
            size=ProjectSize.MEDIUM,
            focus_areas={
                FocusArea.SECURITY: StrictnessLevel.STRICT,
                FocusArea.PERFORMANCE: StrictnessLevel.STRICT,
                FocusArea.SCALABILITY: StrictnessLevel.STRICT,
                FocusArea.USABILITY: StrictnessLevel.NORMAL,
                FocusArea.RELIABILITY: StrictnessLevel.STRICT,
                FocusArea.MAINTAINABILITY: StrictnessLevel.STRICT,
                FocusArea.COMPLIANCE: StrictnessLevel.STRICT,
                FocusArea.COST: StrictnessLevel.NORMAL,
            },
            budget_type="corporate",
            team_size=10,
            expected_users=10000,
            timeline_weeks=24,
        ),
        "fintech": ProjectProfile(
            size=ProjectSize.LARGE,
            focus_areas={
                FocusArea.SECURITY: StrictnessLevel.CRITICAL,
                FocusArea.COMPLIANCE: StrictnessLevel.CRITICAL,
                FocusArea.RELIABILITY: StrictnessLevel.CRITICAL,
                FocusArea.PERFORMANCE: StrictnessLevel.STRICT,
                FocusArea.SCALABILITY: StrictnessLevel.STRICT,
                FocusArea.MAINTAINABILITY: StrictnessLevel.STRICT,
                FocusArea.USABILITY: StrictnessLevel.NORMAL,
                FocusArea.COST: StrictnessLevel.NORMAL,
            },
            budget_type="enterprise",
            team_size=25,
            expected_users=50000,
            timeline_weeks=52,
        ),
        "healthcare": ProjectProfile(
            size=ProjectSize.ENTERPRISE,
            focus_areas={
                FocusArea.SECURITY: StrictnessLevel.CRITICAL,
                FocusArea.COMPLIANCE: StrictnessLevel.CRITICAL,  # HIPAA
                FocusArea.RELIABILITY: StrictnessLevel.CRITICAL,
                FocusArea.USABILITY: StrictnessLevel.STRICT,
                FocusArea.PERFORMANCE: StrictnessLevel.STRICT,
                FocusArea.SCALABILITY: StrictnessLevel.STRICT,
                FocusArea.MAINTAINABILITY: StrictnessLevel.STRICT,
                FocusArea.COST: StrictnessLevel.NORMAL,
            },
            budget_type="enterprise",
            team_size=50,
            expected_users=100000,
            timeline_weeks=78,
        ),
    }

    return presets.get(preset_name, presets["club_app"])


# Convenience for klaverjas
KLAVERJAS_PROFILE = get_preset_profile("club_app")
