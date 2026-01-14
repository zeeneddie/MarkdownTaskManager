"""
Stage Council Configuration.

Fase 23.6 Phase 24.1: Stage-specific configurations for LLM council reviews.
Defines which models review each stage and the criteria/thresholds.
"""

from typing import Dict, List
from .types import StageCouncilConfig, StageType


# =============================================================================
# STAGE-SPECIFIC CONFIGURATIONS
# =============================================================================


STAGE_COUNCIL_CONFIGS: Dict[str, StageCouncilConfig] = {

    StageType.ARCHITECTURE.value: StageCouncilConfig(
        primary_models=["claude_opus", "deepseek_v3", "codex"],
        secondary_models=["qwen_coder"],
        specialist_model="claude_opus",  # Best for architecture improvements

        criteria={
            "scalability": 0.20,
            "security": 0.20,
            "maintainability": 0.20,
            "performance": 0.15,
            "cost_efficiency": 0.10,
            "technology_fit": 0.15,
        },

        critical_threshold=0,  # No critical issues allowed
        major_threshold=2,     # Max 2 major issues
        consensus_minimum=0.7, # 70% consensus required

        second_round_model="deepseek_v3",
        timeout_per_model_seconds=180,  # Longer for complex architecture
    ),

    StageType.DESIGN.value: StageCouncilConfig(
        primary_models=["claude_sonnet", "qwen_coder", "deepseek_v3"],
        secondary_models=["codex"],
        specialist_model="qwen_coder",

        criteria={
            "patterns_usage": 0.25,
            "interface_design": 0.20,
            "extensibility": 0.20,
            "simplicity": 0.15,
            "consistency": 0.20,
        },

        critical_threshold=0,
        major_threshold=3,
        consensus_minimum=0.6,

        second_round_model="claude_sonnet",
        timeout_per_model_seconds=120,
    ),

    StageType.ANALYSIS.value: StageCouncilConfig(
        primary_models=["deepseek_v3", "claude_sonnet", "falcon_h1r"],
        secondary_models=["qwen_coder"],
        specialist_model="deepseek_v3",  # Best for analytical improvements

        criteria={
            "completeness": 0.25,
            "accuracy": 0.25,
            "edge_cases": 0.20,
            "assumptions": 0.15,
            "clarity": 0.15,
        },

        critical_threshold=0,
        major_threshold=3,
        consensus_minimum=0.6,

        second_round_model="claude_sonnet",
        timeout_per_model_seconds=150,
    ),

    StageType.PROGRAMMING.value: StageCouncilConfig(
        primary_models=["qwen_coder", "codex", "deepseek_v3"],
        secondary_models=["claude_sonnet", "falcon_h1r"],
        specialist_model="qwen_coder",  # Best for code improvements

        criteria={
            "correctness": 0.25,
            "security": 0.20,
            "performance": 0.15,
            "readability": 0.15,
            "error_handling": 0.15,
            "testing": 0.10,
        },

        critical_threshold=0,
        major_threshold=2,  # Stricter for code
        consensus_minimum=0.6,

        second_round_model="codex",
        timeout_per_model_seconds=120,
    ),

    StageType.TESTING.value: StageCouncilConfig(
        primary_models=["deepseek_v3", "qwen_coder", "claude_sonnet"],
        secondary_models=["codex"],
        specialist_model="qwen_coder",

        criteria={
            "coverage": 0.25,
            "edge_cases": 0.20,
            "assertions": 0.20,
            "mocking": 0.15,
            "readability": 0.10,
            "performance": 0.10,
        },

        critical_threshold=0,
        major_threshold=2,
        consensus_minimum=0.6,

        second_round_model="deepseek_v3",
        timeout_per_model_seconds=120,
    ),

    StageType.INFRASTRUCTURE.value: StageCouncilConfig(
        primary_models=["claude_opus", "deepseek_v3", "codex"],
        secondary_models=["qwen_coder"],
        specialist_model="claude_opus",  # Best for infra decisions

        criteria={
            "reliability": 0.25,
            "security": 0.25,
            "scalability": 0.20,
            "cost": 0.15,
            "maintainability": 0.15,
        },

        critical_threshold=0,  # Zero tolerance for infra
        major_threshold=1,     # Very strict
        consensus_minimum=0.75,  # High consensus required

        second_round_model="deepseek_v3",
        timeout_per_model_seconds=180,
    ),
}


# =============================================================================
# MODEL PROVIDER MAPPING
# =============================================================================


MODEL_PROVIDER_MAP: Dict[str, str] = {
    "claude_opus": "anthropic",
    "claude_sonnet": "anthropic",
    "deepseek_v3": "deepseek",
    "qwen_coder": "ollama",
    "codex": "openai",
    "falcon_h1r": "ollama",
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_stage_config(stage_type: str) -> StageCouncilConfig:
    """
    Get configuration for a specific stage.

    Args:
        stage_type: The development stage type

    Returns:
        StageCouncilConfig for the stage

    Raises:
        ValueError: If stage type is unknown
    """
    if stage_type not in STAGE_COUNCIL_CONFIGS:
        raise ValueError(f"Unknown stage type: {stage_type}")
    return STAGE_COUNCIL_CONFIGS[stage_type]


def get_models_for_stage(stage_type: str) -> List[str]:
    """
    Get all models (primary + secondary) for a stage.

    Args:
        stage_type: The development stage type

    Returns:
        List of model names
    """
    config = get_stage_config(stage_type)
    return config.primary_models + config.secondary_models


def get_provider_for_model(model_name: str) -> str:
    """
    Get the provider for a model.

    Args:
        model_name: Name of the model

    Returns:
        Provider name (defaults to 'ollama' if unknown)
    """
    return MODEL_PROVIDER_MAP.get(model_name, "ollama")


def get_all_stage_types() -> List[str]:
    """Get all available stage types."""
    return list(STAGE_COUNCIL_CONFIGS.keys())


def get_default_config() -> StageCouncilConfig:
    """
    Get a default configuration for unknown stages.

    Returns a conservative config with generic models.
    """
    return StageCouncilConfig(
        primary_models=["claude_sonnet", "deepseek_v3"],
        secondary_models=["qwen_coder"],
        specialist_model="claude_sonnet",
        criteria={
            "correctness": 0.30,
            "quality": 0.25,
            "security": 0.25,
            "maintainability": 0.20,
        },
        critical_threshold=0,
        major_threshold=3,
        consensus_minimum=0.6,
        timeout_per_model_seconds=120,
    )
