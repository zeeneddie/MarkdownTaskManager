"""
Project Agent Configuration Models

Week 58: Dynamic agent mapping per project for different tech stacks.

Features:
- Project-specific lane-to-agent mappings
- Tag-to-agent customization
- Stack templates (IoT, Mobile, Security, etc.)
- Specialist agent support per project
"""
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TechStack(str, Enum):
    """Supported tech stack templates."""
    PYTHON_FASTAPI = "python_fastapi"
    PYTHON_DJANGO = "python_django"
    JAVASCRIPT_NODE = "javascript_node"
    JAVASCRIPT_REACT = "javascript_react"
    TYPESCRIPT_FULLSTACK = "typescript_fullstack"
    GO_MICROSERVICES = "go_microservices"
    RUST_SYSTEMS = "rust_systems"
    IOT_EMBEDDED = "iot_embedded"
    MOBILE_REACT_NATIVE = "mobile_react_native"
    MOBILE_FLUTTER = "mobile_flutter"
    SECURITY_FOCUSED = "security_focused"
    LEGACY_MIGRATION = "legacy_migration"
    CUSTOM = "custom"


# ============================================================================
# STACK TEMPLATES - Default agent mappings per tech stack
# ============================================================================

STACK_TEMPLATES: Dict[str, Dict[str, Any]] = {
    TechStack.PYTHON_FASTAPI: {
        "description": "Python FastAPI backend with modern async patterns",
        "lane_agents": {
            "analysis": ["Quinn", "Eliza"],
            "build": [],  # Hybrid selection
            "test": ["Tessa"],
            "in_review": ["Quinn"],
        },
        "tag_mappings": {
            "fastapi": "BackendDev_py",
            "sqlalchemy": "BackendDev_py",
            "async": "BackendDev_py",
            "pydantic": "BackendDev_py",
            "api": "BackendDev_py",
            "frontend": "FrontendDev",
            "security": "SecurityAudit_py",
        },
        "specialist_agents": ["BackendDev_py", "SecurityAudit_py", "Tester_py"],
        "model_preferences": {
            "BackendDev_py": "qwen2.5-coder:7b",
            "SecurityAudit_py": "deepseek-r1:latest",
        },
    },
    TechStack.IOT_EMBEDDED: {
        "description": "IoT and embedded systems development",
        "lane_agents": {
            "analysis": ["Quinn", "Eliza", "IoTArchitect"],
            "build": [],
            "test": ["Tessa", "HardwareTester"],
            "in_review": ["Quinn", "SecurityAudit"],
        },
        "tag_mappings": {
            "embedded": "EmbeddedDev",
            "firmware": "EmbeddedDev",
            "mqtt": "IoTBackend",
            "sensor": "EmbeddedDev",
            "protocol": "IoTArchitect",
            "security": "IoTSecurityAudit",
            "ota": "IoTBackend",
        },
        "specialist_agents": ["EmbeddedDev", "IoTArchitect", "IoTBackend", "IoTSecurityAudit", "HardwareTester"],
        "model_preferences": {
            "EmbeddedDev": "codellama:latest",
            "IoTArchitect": "qwen2.5-coder:7b",
        },
        "extra_dod_criteria": {
            "build": [
                {"name": "firmware_compiles", "description": "Firmware compiles without errors", "required": True},
                {"name": "memory_footprint_ok", "description": "Memory usage within limits", "required": True},
            ],
            "test": [
                {"name": "hardware_simulation_pass", "description": "Hardware simulation tests pass", "required": False},
            ],
        },
    },
    TechStack.MOBILE_REACT_NATIVE: {
        "description": "React Native cross-platform mobile development",
        "lane_agents": {
            "analysis": ["Quinn", "Eliza", "MobileArchitect"],
            "build": [],
            "test": ["Tessa", "MobileTester"],
            "in_review": ["Quinn", "MobileReviewer"],
        },
        "tag_mappings": {
            "ios": "iOSDev",
            "android": "AndroidDev",
            "react-native": "MobileDev_RN",
            "navigation": "MobileDev_RN",
            "native-module": "NativeModuleDev",
            "ui": "MobileUIDev",
            "performance": "MobilePerformance",
        },
        "specialist_agents": ["MobileDev_RN", "iOSDev", "AndroidDev", "NativeModuleDev", "MobileUIDev", "MobileTester"],
        "model_preferences": {
            "MobileDev_RN": "qwen2.5-coder:7b",
        },
        "extra_dod_criteria": {
            "build": [
                {"name": "ios_build_success", "description": "iOS build succeeds", "required": True},
                {"name": "android_build_success", "description": "Android build succeeds", "required": True},
            ],
            "test": [
                {"name": "device_tests_pass", "description": "Device/emulator tests pass", "required": True},
            ],
        },
    },
    TechStack.SECURITY_FOCUSED: {
        "description": "High-security applications with strict validation",
        "lane_agents": {
            "analysis": ["Quinn", "Eliza", "ThreatModeler"],
            "build": [],
            "test": ["Tessa", "PenTester"],
            "in_review": ["SecurityAudit", "ComplianceChecker"],
        },
        "tag_mappings": {
            "auth": "AuthSpecialist",
            "crypto": "CryptoSpecialist",
            "api": "SecureAPIDev",
            "data": "DataSecurityDev",
            "compliance": "ComplianceChecker",
            "audit": "SecurityAudit",
        },
        "specialist_agents": ["SecurityAudit", "PenTester", "ThreatModeler", "AuthSpecialist", "CryptoSpecialist"],
        "model_preferences": {
            "SecurityAudit": "claude/opus",  # Use Opus for critical security reviews
            "PenTester": "deepseek-r1:latest",
        },
        "extra_dod_criteria": {
            "build": [
                {"name": "no_secrets_exposed", "description": "No secrets in code", "required": True},
                {"name": "owasp_scan_pass", "description": "OWASP scan passes", "required": True},
            ],
            "in_review": [
                {"name": "security_review_complete", "description": "Security review completed", "required": True},
                {"name": "penetration_test_pass", "description": "Penetration tests pass", "required": False},
            ],
        },
        "blocking_quality_checks": ["sql-injection", "xss", "csrf", "secrets-exposure", "insecure-crypto"],
    },
    TechStack.LEGACY_MIGRATION: {
        "description": "Legacy system migration with careful validation",
        "lane_agents": {
            "analysis": ["Quinn", "Eliza", "Miguel"],
            "build": [],
            "test": ["Tessa", "RegressionTester"],
            "in_review": ["Quinn", "MigrationValidator"],
        },
        "tag_mappings": {
            "migration": "Miguel",
            "legacy": "LegacyCodeAnalyst",
            "database": "DatabaseMigration",
            "data": "DataMigration",
            "api": "APIBridge",
        },
        "specialist_agents": ["Miguel", "LegacyCodeAnalyst", "DatabaseMigration", "DataMigration", "RegressionTester"],
        "extra_dod_criteria": {
            "test": [
                {"name": "regression_tests_pass", "description": "All regression tests pass", "required": True},
                {"name": "data_integrity_verified", "description": "Data integrity verified", "required": True},
            ],
            "in_review": [
                {"name": "rollback_plan_exists", "description": "Rollback plan documented", "required": True},
            ],
        },
    },
}


class ProjectAgentConfig(Base):
    """
    Project-level agent configuration.

    Each project can have custom lane-to-agent mappings, tag mappings,
    and specialist agents based on its tech stack and requirements.
    """
    __tablename__ = "project_agent_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(Integer, nullable=True, index=True)  # Links to external project
    project_name = Column(String(200), nullable=False)
    tech_stack = Column(String(50), nullable=False, default="custom")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Custom lane-to-agent mapping (overrides template)
    lane_agents = Column(JSONB, nullable=True)  # {"analysis": ["Quinn", "Eliza"], ...}

    # Custom tag-to-agent mapping (merged with template)
    tag_mappings = Column(JSONB, nullable=True)  # {"frontend": "FrontendDev", ...}

    # Custom item type defaults
    item_type_agents = Column(JSONB, nullable=True)  # {"bug": "Betty", "task": "BackendDev"}

    # Specialist agents available for this project
    specialist_agents = Column(ARRAY(String), nullable=True)

    # Model preferences per agent
    model_preferences = Column(JSONB, nullable=True)  # {"agent_name": "model_id"}

    # Extra DoD criteria per lane (merged with defaults)
    extra_dod_criteria = Column(JSONB, nullable=True)

    # Quality gate checks that block this project
    blocking_quality_checks = Column(ARRAY(String), nullable=True)

    # Quality gate config reference (links to QualityGateConfig)
    quality_gate_config_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)

    # Relationships
    lane_configs = relationship("ProjectLaneConfig", back_populates="project_config", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "project_name": self.project_name,
            "tech_stack": self.tech_stack,
            "description": self.description,
            "is_active": self.is_active,
            "lane_agents": self.lane_agents,
            "tag_mappings": self.tag_mappings,
            "item_type_agents": self.item_type_agents,
            "specialist_agents": self.specialist_agents,
            "model_preferences": self.model_preferences,
            "extra_dod_criteria": self.extra_dod_criteria,
            "blocking_quality_checks": self.blocking_quality_checks,
            "quality_gate_config_id": str(self.quality_gate_config_id) if self.quality_gate_config_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_effective_lane_agents(self, lane: str) -> List[str]:
        """Get effective agents for a lane, merging template with custom config."""
        template = STACK_TEMPLATES.get(self.tech_stack, {})
        template_agents = template.get("lane_agents", {}).get(lane, [])

        if self.lane_agents and lane in self.lane_agents:
            return self.lane_agents[lane]
        return template_agents

    def get_effective_tag_mappings(self) -> Dict[str, str]:
        """Get effective tag mappings, merging template with custom config."""
        template = STACK_TEMPLATES.get(self.tech_stack, {})
        mappings = template.get("tag_mappings", {}).copy()

        if self.tag_mappings:
            mappings.update(self.tag_mappings)
        return mappings

    def get_effective_specialist_agents(self) -> List[str]:
        """Get all specialist agents available for this project."""
        template = STACK_TEMPLATES.get(self.tech_stack, {})
        agents = set(template.get("specialist_agents", []))

        if self.specialist_agents:
            agents.update(self.specialist_agents)
        return list(agents)


class ProjectLaneConfig(Base):
    """
    Per-lane configuration for a project.

    Allows fine-grained control over each lane's behavior:
    - Custom DoD criteria
    - Quality gate integration
    - Agent preferences
    """
    __tablename__ = "project_lane_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_config_id = Column(UUID(as_uuid=True), ForeignKey("project_agent_configs.id", ondelete="CASCADE"), nullable=False)
    lane = Column(String(30), nullable=False, index=True)

    # Lane-specific settings
    enabled = Column(Boolean, default=True)
    automatic_agent_trigger = Column(Boolean, default=True)  # Auto-trigger agents on entry

    # Custom agents for this lane (overrides project-level)
    custom_agents = Column(ARRAY(String), nullable=True)

    # DoD criteria for this lane
    dod_criteria = Column(JSONB, nullable=True)  # List of DoDCriterion dicts
    dod_min_pass_percentage = Column(Float, default=100.0)

    # Quality gate settings
    quality_gate_enabled = Column(Boolean, default=True)
    quality_gate_blocking = Column(Boolean, default=False)  # Block if gate fails
    quality_checks = Column(ARRAY(String), nullable=True)  # Specific checks to run

    # Retry settings
    max_retries = Column(Integer, default=3)
    escalate_on_max_retries = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship
    project_config = relationship("ProjectAgentConfig", back_populates="lane_configs")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "project_config_id": str(self.project_config_id),
            "lane": self.lane,
            "enabled": self.enabled,
            "automatic_agent_trigger": self.automatic_agent_trigger,
            "custom_agents": self.custom_agents,
            "dod_criteria": self.dod_criteria,
            "dod_min_pass_percentage": self.dod_min_pass_percentage,
            "quality_gate_enabled": self.quality_gate_enabled,
            "quality_gate_blocking": self.quality_gate_blocking,
            "quality_checks": self.quality_checks,
            "max_retries": self.max_retries,
            "escalate_on_max_retries": self.escalate_on_max_retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
