# Stage-Based LLM Council Review System

**Document:** Architecture & Implementation Plan
**Status:** PLANNED
**Created:** Week 145 (2026-01-12)
**Priority:** HIGH
**Roadmap:** Fase 24 (Week 157-162)
**Prerequisite:** Fase 23.5 (Confucius Code Agent Integration)
**Total Effort:** 120 uur (~3-4 weken)

---

## Executive Summary

Dit document beschrijft de implementatie van een **Stage-Based LLM Council Review System** dat automatisch elke development stage (architecture, design, analysis, programming, testing, infrastructure) laat reviewen door een council van LLM modellen. Bij te veel kritieke opmerkingen wordt automatisch een second round getriggerd met een ander model voor verbetering.

### Kernprincipes

1. **Kwaliteit boven snelheid** - Machines kunnen langer draaien, kwaliteit is niet onderhandelbaar
2. **Incrementele adoptie** - Elke fase levert bruikbare functionaliteit
3. **Multi-model consensus** - Geen single point of failure in reviews
4. **Automatische verbetering** - Second round verbetert artifacts automatisch
5. **Data-driven tuning** - Thresholds en model selectie op basis van metrics

### Fasering Overview

| Fase | Focus | Deliverable | Effort |
|------|-------|-------------|--------|
| **24.1** | Foundation | StageReviewService + Issue Classification | 30 uur |
| **24.2** | Intelligence | Second Round + Auto-Improvement | 35 uur |
| **24.3** | Integration | CCA Integration + All Stages | 30 uur |
| **24.4** | Optimization | Performance Tracking + Auto-Tuning | 25 uur |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    STAGE-BASED COUNCIL REVIEW ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         CONFUCIUS ORCHESTRATOR                            │   │
│  │                     (PIV Loop Integration Point)                          │   │
│  └───────────────────────────────┬──────────────────────────────────────────┘   │
│                                  │                                               │
│                                  ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                      STAGE REVIEW COORDINATOR                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ Architecture│  │   Design    │  │  Analysis   │  │ Programming │      │   │
│  │  │   Review    │  │   Review    │  │   Review    │  │   Review    │      │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │   │
│  │         │                │                │                │              │   │
│  │  ┌──────┴────────────────┴────────────────┴────────────────┴──────┐      │   │
│  │  │                    STAGE REVIEW SERVICE                         │      │   │
│  │  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │      │   │
│  │  │  │ Issue Detector │  │ Severity       │  │ Consensus      │    │      │   │
│  │  │  │                │  │ Classifier     │  │ Calculator     │    │      │   │
│  │  │  └────────────────┘  └────────────────┘  └────────────────┘    │      │   │
│  │  └────────────────────────────┬───────────────────────────────────┘      │   │
│  └───────────────────────────────┼──────────────────────────────────────────┘   │
│                                  │                                               │
│                                  ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                      SECOND ROUND ENGINE                                  │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐              │   │
│  │  │ Threshold      │  │ Artifact       │  │ Re-Review      │              │   │
│  │  │ Evaluator      │  │ Improver       │  │ Orchestrator   │              │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘              │   │
│  └───────────────────────────────┬──────────────────────────────────────────┘   │
│                                  │                                               │
│                                  ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         LLM PROVIDER LAYER                                │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐      │   │
│  │  │ Claude │ │DeepSeek│ │  Qwen  │ │ Codex  │ │ Falcon │ │ Ollama │      │   │
│  │  │  Opus  │ │   V3   │ │ Coder  │ │        │ │  H1R   │ │ Local  │      │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘      │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Fase 24.1: Foundation (Week 157-158)

**Doel:** Werkende stage review service met issue classification
**Effort:** 30 uur
**Deliverable:** Reviews voor architecture en programming stages

### 24.1.1 Database Schema

```sql
-- Migration: 071_add_stage_review_tables.py

-- Stage Review Sessions
CREATE TABLE stage_review_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Stage identification
    stage_type VARCHAR(50) NOT NULL,  -- architecture, design, analysis, programming, testing, infrastructure
    artifact_type VARCHAR(50) NOT NULL,  -- code, document, config, schema, test
    artifact_hash VARCHAR(64) NOT NULL,  -- SHA256 of artifact for caching

    -- Context
    project_id UUID REFERENCES projects(id),
    agent_id VARCHAR(100),  -- Which agent triggered the review
    confucius_session_id UUID,  -- Link to CCA session if applicable

    -- Artifact content
    artifact_content TEXT NOT NULL,
    artifact_metadata JSONB DEFAULT '{}',

    -- Review configuration
    council_config JSONB NOT NULL,  -- Models, criteria, thresholds

    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending',  -- pending, reviewing, second_round, approved, rejected
    current_round INTEGER DEFAULT 1,
    max_rounds INTEGER DEFAULT 2,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Indexes
    CONSTRAINT valid_stage CHECK (stage_type IN (
        'architecture', 'design', 'analysis',
        'programming', 'testing', 'infrastructure'
    ))
);

CREATE INDEX idx_stage_review_sessions_stage ON stage_review_sessions(stage_type);
CREATE INDEX idx_stage_review_sessions_status ON stage_review_sessions(status);
CREATE INDEX idx_stage_review_sessions_hash ON stage_review_sessions(artifact_hash);

-- Individual Model Reviews
CREATE TABLE stage_model_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES stage_review_sessions(id) ON DELETE CASCADE,

    -- Model info
    model_name VARCHAR(100) NOT NULL,
    model_role VARCHAR(50),  -- primary, secondary, specialist
    round_number INTEGER DEFAULT 1,

    -- Review content
    review_text TEXT,
    raw_response JSONB,  -- Full LLM response

    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    response_time_ms INTEGER,

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, completed, failed, timeout
    error_message TEXT
);

CREATE INDEX idx_stage_model_reviews_session ON stage_model_reviews(session_id);

-- Detected Issues
CREATE TABLE stage_review_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES stage_review_sessions(id) ON DELETE CASCADE,
    model_review_id UUID REFERENCES stage_model_reviews(id) ON DELETE CASCADE,

    -- Issue classification
    severity VARCHAR(20) NOT NULL,  -- critical, major, minor, suggestion
    category VARCHAR(50) NOT NULL,  -- security, performance, correctness, maintainability, style

    -- Issue details
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    suggested_fix TEXT,

    -- Location reference
    line_start INTEGER,
    line_end INTEGER,
    file_path VARCHAR(500),
    code_snippet TEXT,

    -- Consensus tracking
    confirmed_by_models TEXT[],  -- Which other models flagged same issue
    consensus_score FLOAT DEFAULT 0.0,  -- 0-1, higher = more models agree

    -- Resolution
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    resolved_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_stage_review_issues_session ON stage_review_issues(session_id);
CREATE INDEX idx_stage_review_issues_severity ON stage_review_issues(severity);

-- Review Decisions
CREATE TABLE stage_review_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES stage_review_sessions(id) ON DELETE CASCADE,

    -- Decision
    decision VARCHAR(20) NOT NULL,  -- approved, rejected, needs_revision
    round_number INTEGER NOT NULL,

    -- Metrics
    total_issues INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    major_issues INTEGER DEFAULT 0,
    minor_issues INTEGER DEFAULT 0,
    suggestions INTEGER DEFAULT 0,

    -- Consensus
    consensus_level FLOAT,  -- 0-100%
    models_agreed INTEGER,
    models_total INTEGER,

    -- Reasoning
    decision_reasoning TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Improved Artifacts (Second Round)
CREATE TABLE stage_improved_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES stage_review_sessions(id) ON DELETE CASCADE,

    -- Improvement details
    original_artifact TEXT NOT NULL,
    improved_artifact TEXT NOT NULL,
    improvement_model VARCHAR(100) NOT NULL,

    -- Changes
    changes_summary TEXT,
    issues_addressed UUID[],  -- References to stage_review_issues

    -- Diff
    diff_content TEXT,
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    lines_modified INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance Metrics (for tuning)
CREATE TABLE stage_review_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES stage_review_sessions(id) ON DELETE CASCADE,

    -- Performance
    total_duration_ms INTEGER,
    round_1_duration_ms INTEGER,
    round_2_duration_ms INTEGER,
    improvement_duration_ms INTEGER,

    -- Model performance
    model_timings JSONB,  -- {"claude_opus": 2500, "deepseek": 1800, ...}
    model_issue_counts JSONB,  -- {"claude_opus": 5, "deepseek": 3, ...}

    -- Outcome
    initial_issues INTEGER,
    final_issues INTEGER,
    issues_resolved INTEGER,
    rounds_needed INTEGER,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_stage_review_metrics_session ON stage_review_metrics(session_id);
```

### 24.1.2 Data Models

```python
# backend/app/models/stage_review.py

from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class StageType(str, Enum):
    """Development stages that can be reviewed."""
    ARCHITECTURE = "architecture"
    DESIGN = "design"
    ANALYSIS = "analysis"
    PROGRAMMING = "programming"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"


class IssueSeverity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"  # Must fix, blocks approval
    MAJOR = "major"        # Should fix, counts toward threshold
    MINOR = "minor"        # Nice to fix, doesn't block
    SUGGESTION = "suggestion"  # Optional improvement


class IssueCategory(str, Enum):
    """Issue categories."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"


class ReviewStatus(str, Enum):
    """Review session status."""
    PENDING = "pending"
    REVIEWING = "reviewing"
    SECOND_ROUND = "second_round"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewDecision(str, Enum):
    """Review decision outcomes."""
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class StageReviewSession(Base):
    """Stage review session tracking."""
    __tablename__ = "stage_review_sessions"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    stage_type = Column(String(50), nullable=False)
    artifact_type = Column(String(50), nullable=False)
    artifact_hash = Column(String(64), nullable=False)

    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"))
    agent_id = Column(String(100))
    confucius_session_id = Column(PGUUID(as_uuid=True))

    artifact_content = Column(Text, nullable=False)
    artifact_metadata = Column(JSONB, default={})
    council_config = Column(JSONB, nullable=False)

    status = Column(String(20), default="pending")
    current_round = Column(Integer, default=1)
    max_rounds = Column(Integer, default=2)

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    model_reviews = relationship("StageModelReview", back_populates="session")
    issues = relationship("StageReviewIssue", back_populates="session")
    decisions = relationship("StageReviewDecision", back_populates="session")
    improved_artifacts = relationship("StageImprovedArtifact", back_populates="session")
    metrics = relationship("StageReviewMetrics", back_populates="session", uselist=False)


class StageModelReview(Base):
    """Individual model review within a session."""
    __tablename__ = "stage_model_reviews"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("stage_review_sessions.id"))

    model_name = Column(String(100), nullable=False)
    model_role = Column(String(50))
    round_number = Column(Integer, default=1)

    review_text = Column(Text)
    raw_response = Column(JSONB)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    response_time_ms = Column(Integer)

    status = Column(String(20), default="pending")
    error_message = Column(Text)

    # Relationships
    session = relationship("StageReviewSession", back_populates="model_reviews")
    issues = relationship("StageReviewIssue", back_populates="model_review")


class StageReviewIssue(Base):
    """Detected issue from a review."""
    __tablename__ = "stage_review_issues"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("stage_review_sessions.id"))
    model_review_id = Column(PGUUID(as_uuid=True), ForeignKey("stage_model_reviews.id"))

    severity = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    suggested_fix = Column(Text)

    line_start = Column(Integer)
    line_end = Column(Integer)
    file_path = Column(String(500))
    code_snippet = Column(Text)

    confirmed_by_models = Column(ARRAY(Text))
    consensus_score = Column(Float, default=0.0)

    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("StageReviewSession", back_populates="issues")
    model_review = relationship("StageModelReview", back_populates="issues")


class StageReviewDecision(Base):
    """Review decision for a round."""
    __tablename__ = "stage_review_decisions"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("stage_review_sessions.id"))

    decision = Column(String(20), nullable=False)
    round_number = Column(Integer, nullable=False)

    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    major_issues = Column(Integer, default=0)
    minor_issues = Column(Integer, default=0)
    suggestions = Column(Integer, default=0)

    consensus_level = Column(Float)
    models_agreed = Column(Integer)
    models_total = Column(Integer)

    decision_reasoning = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("StageReviewSession", back_populates="decisions")


class StageImprovedArtifact(Base):
    """Improved artifact from second round."""
    __tablename__ = "stage_improved_artifacts"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("stage_review_sessions.id"))

    original_artifact = Column(Text, nullable=False)
    improved_artifact = Column(Text, nullable=False)
    improvement_model = Column(String(100), nullable=False)

    changes_summary = Column(Text)
    issues_addressed = Column(ARRAY(PGUUID(as_uuid=True)))

    diff_content = Column(Text)
    lines_added = Column(Integer, default=0)
    lines_removed = Column(Integer, default=0)
    lines_modified = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("StageReviewSession", back_populates="improved_artifacts")


class StageReviewMetrics(Base):
    """Performance metrics for a review session."""
    __tablename__ = "stage_review_metrics"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("stage_review_sessions.id"))

    total_duration_ms = Column(Integer)
    round_1_duration_ms = Column(Integer)
    round_2_duration_ms = Column(Integer)
    improvement_duration_ms = Column(Integer)

    model_timings = Column(JSONB)
    model_issue_counts = Column(JSONB)

    initial_issues = Column(Integer)
    final_issues = Column(Integer)
    issues_resolved = Column(Integer)
    rounds_needed = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("StageReviewSession", back_populates="metrics")
```

### 24.1.3 Stage Council Configuration

```python
# backend/app/config/stage_council_config.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


@dataclass
class StageCouncilConfig:
    """Configuration for a stage-specific review council."""

    # Model selection
    primary_models: List[str]  # Models that always participate
    secondary_models: List[str] = field(default_factory=list)  # Fallback models
    specialist_model: Optional[str] = None  # For second round improvements

    # Review criteria (weighted)
    criteria: Dict[str, float] = field(default_factory=dict)  # {"security": 0.3, "correctness": 0.4, ...}

    # Thresholds
    critical_threshold: int = 0  # Max critical issues allowed
    major_threshold: int = 3  # Max major issues allowed
    consensus_minimum: float = 0.6  # Minimum consensus for approval (60%)

    # Second round settings
    enable_second_round: bool = True
    second_round_model: Optional[str] = None  # Model for improvements
    max_rounds: int = 2

    # Performance settings
    timeout_per_model_seconds: int = 120
    parallel_execution: bool = True

    # Prompt customization
    system_prompt_template: Optional[str] = None
    review_prompt_template: Optional[str] = None


# Stage-specific configurations
STAGE_COUNCIL_CONFIGS: Dict[str, StageCouncilConfig] = {

    "architecture": StageCouncilConfig(
        primary_models=["claude_opus", "deepseek_v3", "codex"],
        secondary_models=["qwen_coder"],
        specialist_model="claude_opus",  # Best for architecture improvements

        criteria={
            "scalability": 0.20,
            "security": 0.20,
            "maintainability": 0.20,
            "performance": 0.15,
            "cost_efficiency": 0.10,
            "technology_fit": 0.15
        },

        critical_threshold=0,  # No critical issues allowed
        major_threshold=2,  # Max 2 major issues
        consensus_minimum=0.7,  # 70% consensus required

        second_round_model="deepseek_v3",
        timeout_per_model_seconds=180,  # Longer for complex architecture
    ),

    "design": StageCouncilConfig(
        primary_models=["claude_sonnet", "qwen_coder", "deepseek_v3"],
        secondary_models=["codex"],
        specialist_model="qwen_coder",

        criteria={
            "patterns_usage": 0.25,
            "interface_design": 0.20,
            "extensibility": 0.20,
            "simplicity": 0.15,
            "consistency": 0.20
        },

        critical_threshold=0,
        major_threshold=3,
        consensus_minimum=0.6,

        second_round_model="claude_sonnet",
        timeout_per_model_seconds=120,
    ),

    "analysis": StageCouncilConfig(
        primary_models=["deepseek_v3", "claude_sonnet", "falcon_h1r"],
        secondary_models=["qwen_coder"],
        specialist_model="deepseek_v3",  # Best for analytical improvements

        criteria={
            "completeness": 0.25,
            "accuracy": 0.25,
            "edge_cases": 0.20,
            "assumptions": 0.15,
            "clarity": 0.15
        },

        critical_threshold=0,
        major_threshold=3,
        consensus_minimum=0.6,

        second_round_model="claude_sonnet",
        timeout_per_model_seconds=150,
    ),

    "programming": StageCouncilConfig(
        primary_models=["qwen_coder", "codex", "deepseek_v3"],
        secondary_models=["claude_sonnet", "falcon_h1r"],
        specialist_model="qwen_coder",  # Best for code improvements

        criteria={
            "correctness": 0.25,
            "security": 0.20,
            "performance": 0.15,
            "readability": 0.15,
            "error_handling": 0.15,
            "testing": 0.10
        },

        critical_threshold=0,
        major_threshold=2,  # Stricter for code
        consensus_minimum=0.6,

        second_round_model="codex",
        timeout_per_model_seconds=120,
    ),

    "testing": StageCouncilConfig(
        primary_models=["deepseek_v3", "qwen_coder", "claude_sonnet"],
        secondary_models=["codex"],
        specialist_model="qwen_coder",

        criteria={
            "coverage": 0.25,
            "edge_cases": 0.20,
            "assertions": 0.20,
            "mocking": 0.15,
            "readability": 0.10,
            "performance": 0.10
        },

        critical_threshold=0,
        major_threshold=2,
        consensus_minimum=0.6,

        second_round_model="deepseek_v3",
        timeout_per_model_seconds=120,
    ),

    "infrastructure": StageCouncilConfig(
        primary_models=["claude_opus", "deepseek_v3", "codex"],
        secondary_models=["qwen_coder"],
        specialist_model="claude_opus",  # Best for infra decisions

        criteria={
            "reliability": 0.25,
            "security": 0.25,
            "scalability": 0.20,
            "cost": 0.15,
            "maintainability": 0.15
        },

        critical_threshold=0,  # Zero tolerance for infra
        major_threshold=1,  # Very strict
        consensus_minimum=0.75,  # High consensus required

        second_round_model="deepseek_v3",
        timeout_per_model_seconds=180,
    ),
}


def get_stage_config(stage_type: str) -> StageCouncilConfig:
    """Get configuration for a specific stage."""
    if stage_type not in STAGE_COUNCIL_CONFIGS:
        raise ValueError(f"Unknown stage type: {stage_type}")
    return STAGE_COUNCIL_CONFIGS[stage_type]


def get_models_for_stage(stage_type: str) -> List[str]:
    """Get all models (primary + secondary) for a stage."""
    config = get_stage_config(stage_type)
    return config.primary_models + config.secondary_models
```

---

## Fase 24.1.4 Stage Review Service (Core)

```python
# backend/app/services/stage_review_service.py

import asyncio
import hashlib
import re
from uuid import uuid4
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.stage_review import (
    StageReviewSession, StageModelReview, StageReviewIssue,
    StageReviewDecision, StageReviewMetrics,
    StageType, IssueSeverity, IssueCategory, ReviewStatus, ReviewDecision
)
from app.config.stage_council_config import (
    get_stage_config, StageCouncilConfig, STAGE_COUNCIL_CONFIGS
)
from app.providers.registry import LLMProviderRegistry


@dataclass
class ReviewResult:
    """Result of a stage review."""
    session_id: str
    stage_type: str
    decision: ReviewDecision
    approved: bool
    issues: List[Dict]
    consensus_level: float
    rounds_completed: int
    improved_artifact: Optional[str] = None
    metrics: Optional[Dict] = None


@dataclass
class ParsedIssue:
    """Parsed issue from LLM response."""
    severity: IssueSeverity
    category: IssueCategory
    title: str
    description: str
    suggested_fix: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None


class StageReviewService:
    """
    Stage-Based LLM Council Review Service.

    Reviews development artifacts at each stage using multiple LLM models.
    Implements automatic second round with improvement when issues exceed threshold.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        llm_registry: LLMProviderRegistry
    ):
        self.db = db_session
        self.llm = llm_registry
        self.configs = STAGE_COUNCIL_CONFIGS

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    async def review_artifact(
        self,
        stage_type: str,
        artifact: str,
        artifact_type: str = "code",
        context: Optional[Dict] = None,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        force_review: bool = False
    ) -> ReviewResult:
        """
        Review an artifact for a specific development stage.

        This is the main entry point for stage-based reviews.
        Handles caching, multi-model review, consensus calculation,
        and automatic second round if needed.

        Args:
            stage_type: Development stage (architecture, design, etc.)
            artifact: The artifact content to review
            artifact_type: Type of artifact (code, document, config, etc.)
            context: Additional context for the review
            project_id: Optional project reference
            agent_id: Which agent triggered this review
            force_review: Skip cache and force new review

        Returns:
            ReviewResult with decision, issues, and metrics

        Example:
            >>> result = await service.review_artifact(
            ...     stage_type="programming",
            ...     artifact=code_content,
            ...     context={"function_name": "calculate_fp", "language": "python"}
            ... )
            >>> if result.approved:
            ...     print("Code approved!")
            ... else:
            ...     print(f"Found {len(result.issues)} issues")
        """
        # Validate stage type
        if stage_type not in self.configs:
            raise ValueError(f"Unknown stage type: {stage_type}")

        config = self.configs[stage_type]
        artifact_hash = self._compute_hash(artifact)

        # Check cache (unless forced)
        if not force_review:
            cached = await self._get_cached_review(artifact_hash)
            if cached:
                return cached

        # Create session
        session = await self._create_session(
            stage_type=stage_type,
            artifact=artifact,
            artifact_type=artifact_type,
            artifact_hash=artifact_hash,
            config=config,
            context=context,
            project_id=project_id,
            agent_id=agent_id
        )

        start_time = datetime.utcnow()

        try:
            # Round 1: Multi-model review
            round1_result = await self._execute_review_round(
                session=session,
                config=config,
                round_number=1
            )

            # Evaluate if second round needed
            needs_second_round = self._evaluate_threshold(
                issues=round1_result["issues"],
                config=config
            )

            if needs_second_round and config.enable_second_round:
                # Second round: Improve and re-review
                improved_artifact = await self._improve_artifact(
                    session=session,
                    issues=round1_result["issues"],
                    config=config
                )

                round2_result = await self._execute_review_round(
                    session=session,
                    config=config,
                    round_number=2,
                    artifact_override=improved_artifact
                )

                final_result = round2_result
                final_result["improved_artifact"] = improved_artifact
                final_result["rounds_completed"] = 2
            else:
                final_result = round1_result
                final_result["rounds_completed"] = 1

            # Calculate final decision
            decision = self._make_decision(
                issues=final_result["issues"],
                consensus=final_result["consensus_level"],
                config=config
            )

            # Save decision
            await self._save_decision(
                session=session,
                decision=decision,
                issues=final_result["issues"],
                consensus=final_result["consensus_level"],
                round_number=final_result["rounds_completed"]
            )

            # Update session status
            session.status = (
                ReviewStatus.APPROVED.value if decision == ReviewDecision.APPROVED
                else ReviewStatus.REJECTED.value
            )
            session.completed_at = datetime.utcnow()
            await self.db.commit()

            # Record metrics
            await self._record_metrics(
                session=session,
                start_time=start_time,
                final_result=final_result
            )

            return ReviewResult(
                session_id=str(session.id),
                stage_type=stage_type,
                decision=decision,
                approved=(decision == ReviewDecision.APPROVED),
                issues=final_result["issues"],
                consensus_level=final_result["consensus_level"],
                rounds_completed=final_result["rounds_completed"],
                improved_artifact=final_result.get("improved_artifact"),
                metrics=final_result.get("metrics")
            )

        except Exception as e:
            session.status = "failed"
            await self.db.commit()
            raise

    # ========================================================================
    # REVIEW EXECUTION
    # ========================================================================

    async def _execute_review_round(
        self,
        session: StageReviewSession,
        config: StageCouncilConfig,
        round_number: int,
        artifact_override: Optional[str] = None
    ) -> Dict:
        """Execute a single review round with all configured models."""

        artifact = artifact_override or session.artifact_content
        models = config.primary_models

        # Update session status
        session.status = ReviewStatus.REVIEWING.value
        session.current_round = round_number
        await self.db.commit()

        # Build prompts
        review_prompt = self._build_review_prompt(
            stage_type=session.stage_type,
            artifact=artifact,
            artifact_type=session.artifact_type,
            context=session.artifact_metadata,
            criteria=config.criteria
        )

        # Query all models in parallel
        if config.parallel_execution:
            tasks = [
                self._query_model_for_review(
                    session_id=session.id,
                    model_name=model,
                    prompt=review_prompt,
                    round_number=round_number,
                    timeout=config.timeout_per_model_seconds
                )
                for model in models
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []
            for model in models:
                result = await self._query_model_for_review(
                    session_id=session.id,
                    model_name=model,
                    prompt=review_prompt,
                    round_number=round_number,
                    timeout=config.timeout_per_model_seconds
                )
                results.append(result)

        # Process results
        successful_reviews = []
        all_issues = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Model {models[i]} failed: {result}")
                continue

            successful_reviews.append(result)
            all_issues.extend(result.get("issues", []))

        # Deduplicate and calculate consensus
        deduplicated_issues = self._deduplicate_issues(all_issues, len(successful_reviews))
        consensus_level = self._calculate_consensus(successful_reviews, deduplicated_issues)

        return {
            "reviews": successful_reviews,
            "issues": deduplicated_issues,
            "consensus_level": consensus_level,
            "models_responded": len(successful_reviews),
            "models_total": len(models)
        }

    async def _query_model_for_review(
        self,
        session_id: str,
        model_name: str,
        prompt: str,
        round_number: int,
        timeout: int
    ) -> Dict:
        """Query a single model for review."""

        # Create model review record
        model_review = StageModelReview(
            id=uuid4(),
            session_id=session_id,
            model_name=model_name,
            round_number=round_number,
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(model_review)
        await self.db.commit()

        try:
            # Query LLM
            start_time = datetime.utcnow()

            response = await asyncio.wait_for(
                self.llm.generate(
                    provider=self._get_provider_for_model(model_name),
                    model=model_name,
                    prompt=prompt,
                    max_tokens=4000
                ),
                timeout=timeout
            )

            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Parse response
            review_text = response.get("text", "")
            parsed_issues = self._parse_review_response(review_text)

            # Save issues to database
            for issue in parsed_issues:
                issue_record = StageReviewIssue(
                    id=uuid4(),
                    session_id=session_id,
                    model_review_id=model_review.id,
                    severity=issue.severity.value,
                    category=issue.category.value,
                    title=issue.title,
                    description=issue.description,
                    suggested_fix=issue.suggested_fix,
                    line_start=issue.line_start,
                    line_end=issue.line_end,
                    code_snippet=issue.code_snippet
                )
                self.db.add(issue_record)

            # Update model review
            model_review.status = "completed"
            model_review.completed_at = end_time
            model_review.response_time_ms = response_time_ms
            model_review.review_text = review_text
            model_review.raw_response = response

            await self.db.commit()

            return {
                "model": model_name,
                "issues": [self._issue_to_dict(i) for i in parsed_issues],
                "response_time_ms": response_time_ms,
                "review_text": review_text
            }

        except asyncio.TimeoutError:
            model_review.status = "timeout"
            model_review.error_message = f"Timeout after {timeout}s"
            await self.db.commit()
            raise

        except Exception as e:
            model_review.status = "failed"
            model_review.error_message = str(e)
            await self.db.commit()
            raise

    # ========================================================================
    # PROMPT ENGINEERING
    # ========================================================================

    def _build_review_prompt(
        self,
        stage_type: str,
        artifact: str,
        artifact_type: str,
        context: Optional[Dict],
        criteria: Dict[str, float]
    ) -> str:
        """Build stage-specific review prompt."""

        # Stage-specific instructions
        stage_instructions = {
            "architecture": """
ARCHITECTURE REVIEW FOCUS:
- Scalability: Can this handle 10x, 100x growth?
- Security: Are there potential vulnerabilities?
- Maintainability: Will this be easy to modify/extend?
- Performance: Any obvious bottlenecks?
- Cost: Infrastructure/operational cost implications?
- Technology Fit: Does it align with existing stack?
""",
            "design": """
DESIGN REVIEW FOCUS:
- Design Patterns: Are appropriate patterns used correctly?
- Interface Design: Are APIs/interfaces well-defined?
- Extensibility: Can new features be added easily?
- Simplicity: Is the design as simple as possible?
- Consistency: Does it follow existing conventions?
""",
            "analysis": """
ANALYSIS REVIEW FOCUS:
- Completeness: Are all aspects covered?
- Accuracy: Are conclusions correct?
- Edge Cases: Are boundary conditions considered?
- Assumptions: Are assumptions stated and valid?
- Clarity: Is the analysis easy to follow?
""",
            "programming": """
CODE REVIEW FOCUS:
- Correctness: Does the code do what it should?
- Security: Any SQL injection, XSS, or other vulnerabilities?
- Performance: Any inefficient algorithms or queries?
- Readability: Is the code easy to understand?
- Error Handling: Are errors handled gracefully?
- Testing: Is the code testable? Are tests included?
""",
            "testing": """
TEST REVIEW FOCUS:
- Coverage: Are all paths/branches tested?
- Edge Cases: Are boundary conditions tested?
- Assertions: Are assertions meaningful and specific?
- Mocking: Is mocking used appropriately?
- Readability: Are tests easy to understand?
- Performance: Will tests run in reasonable time?
""",
            "infrastructure": """
INFRASTRUCTURE REVIEW FOCUS:
- Reliability: Will this be stable in production?
- Security: Are secrets protected? Access controlled?
- Scalability: Can it handle load increases?
- Cost: Is this cost-efficient?
- Maintainability: Is it easy to operate/monitor?
"""
        }

        # Build criteria section
        criteria_text = "REVIEW CRITERIA (weighted importance):\n"
        for criterion, weight in sorted(criteria.items(), key=lambda x: -x[1]):
            criteria_text += f"- {criterion.replace('_', ' ').title()}: {int(weight * 100)}%\n"

        # Build context section
        context_text = ""
        if context:
            context_text = "\nADDITIONAL CONTEXT:\n"
            for key, value in context.items():
                context_text += f"- {key}: {value}\n"

        prompt = f"""You are an expert reviewer performing a {stage_type.upper()} review.

{stage_instructions.get(stage_type, "")}

{criteria_text}

{context_text}

ARTIFACT TO REVIEW ({artifact_type}):
```
{artifact}
```

INSTRUCTIONS:
1. Analyze the artifact against each review criterion
2. Identify any issues, categorized by severity
3. For each issue, provide specific line references if applicable
4. Suggest fixes for each issue

ISSUE SEVERITY LEVELS:
- CRITICAL: Must be fixed, blocks approval (security vulnerabilities, crashes, data loss)
- MAJOR: Should be fixed, counts toward approval threshold (bugs, performance issues)
- MINOR: Nice to fix, doesn't block approval (code style, minor improvements)
- SUGGESTION: Optional improvement ideas

FORMAT YOUR RESPONSE AS:
For each issue found, use this exact format:

[ISSUE]
SEVERITY: critical|major|minor|suggestion
CATEGORY: security|performance|correctness|maintainability|style|documentation|testing|architecture
TITLE: Brief issue title
DESCRIPTION: Detailed description of the issue
LINE: line_number (or line_start-line_end for ranges)
SUGGESTED_FIX: How to fix this issue
CODE_SNIPPET: Relevant code if applicable
[/ISSUE]

If no issues found, respond with:
[NO_ISSUES]
The artifact passes all review criteria.
[/NO_ISSUES]

End your response with:
[SUMMARY]
Total issues: X (Y critical, Z major, W minor, V suggestions)
Overall assessment: APPROVE|NEEDS_WORK|REJECT
Confidence: X%
[/SUMMARY]
"""
        return prompt

    def _parse_review_response(self, response_text: str) -> List[ParsedIssue]:
        """Parse issues from model response."""
        issues = []

        # Find all issue blocks
        issue_pattern = r'\[ISSUE\](.*?)\[/ISSUE\]'
        matches = re.findall(issue_pattern, response_text, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                issue = self._parse_single_issue(match)
                if issue:
                    issues.append(issue)
            except Exception as e:
                print(f"Failed to parse issue: {e}")
                continue

        return issues

    def _parse_single_issue(self, issue_text: str) -> Optional[ParsedIssue]:
        """Parse a single issue block."""
        def extract_field(field: str) -> Optional[str]:
            pattern = rf'{field}:\s*(.+?)(?=\n[A-Z_]+:|$)'
            match = re.search(pattern, issue_text, re.IGNORECASE | re.DOTALL)
            return match.group(1).strip() if match else None

        severity_str = extract_field("SEVERITY")
        category_str = extract_field("CATEGORY")
        title = extract_field("TITLE")
        description = extract_field("DESCRIPTION")

        if not all([severity_str, category_str, title, description]):
            return None

        # Parse severity
        try:
            severity = IssueSeverity(severity_str.lower())
        except ValueError:
            severity = IssueSeverity.MINOR

        # Parse category
        try:
            category = IssueCategory(category_str.lower())
        except ValueError:
            category = IssueCategory.CORRECTNESS

        # Parse line numbers
        line_str = extract_field("LINE")
        line_start = None
        line_end = None
        if line_str:
            if "-" in line_str:
                parts = line_str.split("-")
                line_start = int(parts[0].strip())
                line_end = int(parts[1].strip())
            else:
                try:
                    line_start = int(line_str.strip())
                except ValueError:
                    pass

        return ParsedIssue(
            severity=severity,
            category=category,
            title=title,
            description=description,
            suggested_fix=extract_field("SUGGESTED_FIX"),
            line_start=line_start,
            line_end=line_end,
            code_snippet=extract_field("CODE_SNIPPET")
        )

    # ========================================================================
    # CONSENSUS & DEDUPLICATION
    # ========================================================================

    def _deduplicate_issues(
        self,
        all_issues: List[Dict],
        num_models: int
    ) -> List[Dict]:
        """
        Deduplicate issues found by multiple models.
        Calculate consensus score for each unique issue.
        """
        if not all_issues:
            return []

        # Group similar issues
        unique_issues = {}

        for issue in all_issues:
            # Create a similarity key based on title + category
            key = f"{issue['category']}:{issue['title'][:50].lower()}"

            if key in unique_issues:
                unique_issues[key]["confirmed_by"].append(issue.get("model", "unknown"))
            else:
                unique_issues[key] = {
                    **issue,
                    "confirmed_by": [issue.get("model", "unknown")]
                }

        # Calculate consensus scores
        result = []
        for issue in unique_issues.values():
            confirmed_count = len(issue["confirmed_by"])
            issue["consensus_score"] = confirmed_count / num_models
            result.append(issue)

        # Sort by severity, then consensus
        severity_order = {"critical": 0, "major": 1, "minor": 2, "suggestion": 3}
        result.sort(key=lambda x: (
            severity_order.get(x["severity"], 4),
            -x["consensus_score"]
        ))

        return result

    def _calculate_consensus(
        self,
        reviews: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall consensus level across models."""
        if not reviews:
            return 0.0

        # Factor 1: Agreement on number of issues
        issue_counts = [len(r.get("issues", [])) for r in reviews]
        if issue_counts:
            avg_issues = sum(issue_counts) / len(issue_counts)
            variance = sum((c - avg_issues) ** 2 for c in issue_counts) / len(issue_counts)
            std_dev = variance ** 0.5
            # Lower std_dev = higher consensus
            count_consensus = max(0, 1 - (std_dev / (avg_issues + 1)))
        else:
            count_consensus = 1.0

        # Factor 2: Average issue consensus scores
        if issues:
            avg_issue_consensus = sum(i["consensus_score"] for i in issues) / len(issues)
        else:
            avg_issue_consensus = 1.0  # No issues = full consensus

        # Combined consensus
        return (count_consensus * 0.4 + avg_issue_consensus * 0.6) * 100

    # ========================================================================
    # THRESHOLD EVALUATION
    # ========================================================================

    def _evaluate_threshold(
        self,
        issues: List[Dict],
        config: StageCouncilConfig
    ) -> bool:
        """
        Evaluate if issues exceed threshold (triggers second round).

        Only counts issues with consensus >= 0.5 (at least half the models agree)
        """
        critical_count = 0
        major_count = 0

        for issue in issues:
            # Only count issues with sufficient consensus
            if issue.get("consensus_score", 0) < 0.5:
                continue

            if issue["severity"] == "critical":
                critical_count += 1
            elif issue["severity"] == "major":
                major_count += 1

        exceeds_critical = critical_count > config.critical_threshold
        exceeds_major = major_count > config.major_threshold

        return exceeds_critical or exceeds_major

    def _make_decision(
        self,
        issues: List[Dict],
        consensus: float,
        config: StageCouncilConfig
    ) -> ReviewDecision:
        """Make final decision based on issues and consensus."""

        # Count confirmed issues (consensus >= 0.5)
        confirmed_critical = sum(
            1 for i in issues
            if i["severity"] == "critical" and i.get("consensus_score", 0) >= 0.5
        )
        confirmed_major = sum(
            1 for i in issues
            if i["severity"] == "major" and i.get("consensus_score", 0) >= 0.5
        )

        # Check thresholds
        if confirmed_critical > config.critical_threshold:
            return ReviewDecision.REJECTED

        if confirmed_major > config.major_threshold:
            return ReviewDecision.NEEDS_REVISION

        if consensus < config.consensus_minimum * 100:
            return ReviewDecision.NEEDS_REVISION

        return ReviewDecision.APPROVED

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content for caching."""
        return hashlib.sha256(content.encode()).hexdigest()

    async def _get_cached_review(self, artifact_hash: str) -> Optional[ReviewResult]:
        """Check for cached review result."""
        result = await self.db.execute(
            select(StageReviewSession)
            .where(StageReviewSession.artifact_hash == artifact_hash)
            .where(StageReviewSession.status.in_(["approved", "rejected"]))
            .order_by(StageReviewSession.created_at.desc())
            .limit(1)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        # Rebuild result from session
        # ... (implementation details)
        return None  # Simplified for now

    def _get_provider_for_model(self, model_name: str) -> str:
        """Map model name to provider."""
        provider_map = {
            "claude_opus": "anthropic",
            "claude_sonnet": "anthropic",
            "deepseek_v3": "deepseek",
            "qwen_coder": "ollama",
            "codex": "openai",
            "falcon_h1r": "ollama",
        }
        return provider_map.get(model_name, "ollama")

    def _issue_to_dict(self, issue: ParsedIssue) -> Dict:
        """Convert ParsedIssue to dictionary."""
        return {
            "severity": issue.severity.value,
            "category": issue.category.value,
            "title": issue.title,
            "description": issue.description,
            "suggested_fix": issue.suggested_fix,
            "line_start": issue.line_start,
            "line_end": issue.line_end,
            "code_snippet": issue.code_snippet
        }

    async def _create_session(self, **kwargs) -> StageReviewSession:
        """Create new review session."""
        session = StageReviewSession(
            id=uuid4(),
            stage_type=kwargs["stage_type"],
            artifact_type=kwargs["artifact_type"],
            artifact_hash=kwargs["artifact_hash"],
            artifact_content=kwargs["artifact"],
            artifact_metadata=kwargs.get("context") or {},
            council_config=self._config_to_dict(kwargs["config"]),
            project_id=kwargs.get("project_id"),
            agent_id=kwargs.get("agent_id"),
            max_rounds=kwargs["config"].max_rounds,
            created_at=datetime.utcnow()
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    def _config_to_dict(self, config: StageCouncilConfig) -> Dict:
        """Convert config to serializable dict."""
        return {
            "primary_models": config.primary_models,
            "secondary_models": config.secondary_models,
            "criteria": config.criteria,
            "critical_threshold": config.critical_threshold,
            "major_threshold": config.major_threshold,
            "consensus_minimum": config.consensus_minimum
        }

    async def _save_decision(self, session, decision, issues, consensus, round_number):
        """Save review decision to database."""
        decision_record = StageReviewDecision(
            id=uuid4(),
            session_id=session.id,
            decision=decision.value,
            round_number=round_number,
            total_issues=len(issues),
            critical_issues=sum(1 for i in issues if i["severity"] == "critical"),
            major_issues=sum(1 for i in issues if i["severity"] == "major"),
            minor_issues=sum(1 for i in issues if i["severity"] == "minor"),
            suggestions=sum(1 for i in issues if i["severity"] == "suggestion"),
            consensus_level=consensus,
            models_agreed=len(set(m for i in issues for m in i.get("confirmed_by", []))),
            models_total=len(session.council_config.get("primary_models", []))
        )
        self.db.add(decision_record)
        await self.db.commit()

    async def _record_metrics(self, session, start_time, final_result):
        """Record performance metrics."""
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        metrics = StageReviewMetrics(
            id=uuid4(),
            session_id=session.id,
            total_duration_ms=duration_ms,
            rounds_needed=final_result["rounds_completed"],
            initial_issues=len(final_result.get("issues", [])),
            final_issues=len(final_result.get("issues", []))
        )
        self.db.add(metrics)
        await self.db.commit()
```

---

## Fase 24.2: Intelligence - Second Round & Auto-Improvement (Week 159-160)

**Doel:** Automatische artifact verbetering bij te veel issues
**Effort:** 35 uur
**Deliverable:** Intelligent second round met artifact improvement

### 24.2.1 Artifact Improvement Service

```python
# backend/app/services/artifact_improvement_service.py

import difflib
from uuid import uuid4
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stage_review import StageImprovedArtifact, StageReviewIssue
from app.providers.registry import LLMProviderRegistry


@dataclass
class ImprovementResult:
    """Result of artifact improvement."""
    original: str
    improved: str
    changes_summary: str
    issues_addressed: List[str]
    diff: str
    lines_added: int
    lines_removed: int
    lines_modified: int


class ArtifactImprovementService:
    """
    Service for automatically improving artifacts based on review feedback.
    Uses a specialist model to apply fixes for identified issues.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        llm_registry: LLMProviderRegistry
    ):
        self.db = db_session
        self.llm = llm_registry

    async def improve_artifact(
        self,
        original_artifact: str,
        artifact_type: str,
        issues: List[Dict],
        improvement_model: str,
        context: Optional[Dict] = None
    ) -> ImprovementResult:
        """
        Improve artifact by addressing identified issues.

        Args:
            original_artifact: The original artifact content
            artifact_type: Type of artifact (code, document, etc.)
            issues: List of issues to address
            improvement_model: Model to use for improvements
            context: Additional context

        Returns:
            ImprovementResult with improved artifact and metadata
        """
        # Prioritize issues: critical first, then major
        prioritized_issues = self._prioritize_issues(issues)

        # Build improvement prompt
        prompt = self._build_improvement_prompt(
            artifact=original_artifact,
            artifact_type=artifact_type,
            issues=prioritized_issues,
            context=context
        )

        # Query improvement model
        response = await self.llm.generate(
            provider=self._get_provider(improvement_model),
            model=improvement_model,
            prompt=prompt,
            max_tokens=8000  # Larger for full artifact
        )

        improved_artifact = self._extract_improved_artifact(response.get("text", ""))

        # Calculate diff
        diff_result = self._calculate_diff(original_artifact, improved_artifact)

        return ImprovementResult(
            original=original_artifact,
            improved=improved_artifact,
            changes_summary=self._generate_changes_summary(prioritized_issues),
            issues_addressed=[i["title"] for i in prioritized_issues],
            diff=diff_result["diff"],
            lines_added=diff_result["added"],
            lines_removed=diff_result["removed"],
            lines_modified=diff_result["modified"]
        )

    def _prioritize_issues(self, issues: List[Dict]) -> List[Dict]:
        """Prioritize issues for improvement (critical/major only)."""
        severity_order = {"critical": 0, "major": 1}

        important_issues = [
            i for i in issues
            if i["severity"] in severity_order
        ]

        return sorted(
            important_issues,
            key=lambda x: (severity_order.get(x["severity"], 99), -x.get("consensus_score", 0))
        )

    def _build_improvement_prompt(
        self,
        artifact: str,
        artifact_type: str,
        issues: List[Dict],
        context: Optional[Dict]
    ) -> str:
        """Build prompt for artifact improvement."""

        issues_text = ""
        for i, issue in enumerate(issues, 1):
            issues_text += f"""
Issue #{i}:
- Severity: {issue['severity'].upper()}
- Category: {issue['category']}
- Title: {issue['title']}
- Description: {issue['description']}
- Suggested Fix: {issue.get('suggested_fix', 'Not provided')}
- Line Reference: {issue.get('line_start', 'N/A')}
"""

        context_text = ""
        if context:
            context_text = "\nCONTEXT:\n"
            for key, value in context.items():
                context_text += f"- {key}: {value}\n"

        return f"""You are an expert {artifact_type} improver. Your task is to fix the identified issues while maintaining the artifact's original purpose and style.

ORIGINAL ARTIFACT:
```
{artifact}
```

ISSUES TO FIX:
{issues_text}
{context_text}

INSTRUCTIONS:
1. Address ALL listed issues
2. Maintain the original style and structure where possible
3. Do not introduce new functionality beyond fixing the issues
4. Preserve all existing correct functionality
5. Add comments only where they clarify the fix

IMPORTANT:
- Return the COMPLETE improved artifact
- Include ALL original content that should be preserved
- Make minimal changes - only what's needed to fix the issues

OUTPUT FORMAT:
[IMPROVED_ARTIFACT]
```
Your improved artifact here
```
[/IMPROVED_ARTIFACT]

[CHANGES_MADE]
- Brief description of each change made
[/CHANGES_MADE]
"""

    def _extract_improved_artifact(self, response: str) -> str:
        """Extract improved artifact from model response."""
        import re

        # Try to find the artifact block
        pattern = r'\[IMPROVED_ARTIFACT\]\s*```(?:\w+)?\s*(.*?)\s*```\s*\[/IMPROVED_ARTIFACT\]'
        match = re.search(pattern, response, re.DOTALL)

        if match:
            return match.group(1).strip()

        # Fallback: look for any code block
        code_pattern = r'```(?:\w+)?\s*(.*?)\s*```'
        code_match = re.search(code_pattern, response, re.DOTALL)

        if code_match:
            return code_match.group(1).strip()

        # Last resort: return entire response
        return response.strip()

    def _calculate_diff(self, original: str, improved: str) -> Dict:
        """Calculate diff statistics between original and improved."""
        original_lines = original.splitlines()
        improved_lines = improved.splitlines()

        diff = list(difflib.unified_diff(
            original_lines,
            improved_lines,
            lineterm=""
        ))

        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        # Rough estimate of modified lines
        modified = min(added, removed)
        net_added = added - modified
        net_removed = removed - modified

        return {
            "diff": "\n".join(diff),
            "added": net_added,
            "removed": net_removed,
            "modified": modified
        }

    def _generate_changes_summary(self, issues: List[Dict]) -> str:
        """Generate summary of changes made."""
        if not issues:
            return "No changes needed."

        summary_lines = ["Changes made to address:"]
        for issue in issues:
            summary_lines.append(f"- [{issue['severity'].upper()}] {issue['title']}")

        return "\n".join(summary_lines)

    def _get_provider(self, model: str) -> str:
        """Get provider for model."""
        provider_map = {
            "claude_opus": "anthropic",
            "claude_sonnet": "anthropic",
            "deepseek_v3": "deepseek",
            "qwen_coder": "ollama",
            "codex": "openai",
        }
        return provider_map.get(model, "ollama")


# Integration with StageReviewService

async def _improve_artifact(
    self,
    session: 'StageReviewSession',
    issues: List[Dict],
    config: 'StageCouncilConfig'
) -> str:
    """Improve artifact and return improved version."""

    improvement_service = ArtifactImprovementService(self.db, self.llm)

    result = await improvement_service.improve_artifact(
        original_artifact=session.artifact_content,
        artifact_type=session.artifact_type,
        issues=issues,
        improvement_model=config.second_round_model,
        context=session.artifact_metadata
    )

    # Save improved artifact
    improved_record = StageImprovedArtifact(
        id=uuid4(),
        session_id=session.id,
        original_artifact=result.original,
        improved_artifact=result.improved,
        improvement_model=config.second_round_model,
        changes_summary=result.changes_summary,
        diff_content=result.diff,
        lines_added=result.lines_added,
        lines_removed=result.lines_removed,
        lines_modified=result.lines_modified
    )
    self.db.add(improved_record)
    await self.db.commit()

    return result.improved
```

---

## Fase 24.3: Integration (Week 160-161)

**Doel:** Integratie met Confucius Orchestrator en alle development stages
**Effort:** 30 uur

### 24.3.1 Confucius Integration Extension

```python
# backend/app/extensions/stage_review_extension.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from app.extensions.base_extension import BaseAgentExtension, ExtensionContext
from app.services.stage_review_service import StageReviewService, ReviewResult


@dataclass
class StageReviewExtensionConfig:
    """Configuration for stage review extension."""
    enabled_stages: List[str]  # Which stages trigger reviews
    auto_improve: bool = True  # Automatically improve on failure
    block_on_failure: bool = True  # Block pipeline if review fails
    require_consensus: float = 0.6  # Minimum consensus for pass


class StageReviewExtension(BaseAgentExtension):
    """
    Extension that integrates stage-based reviews into the Confucius PIV loop.

    Hooks into the validation phase to automatically review artifacts
    at each development stage.
    """

    def __init__(
        self,
        review_service: StageReviewService,
        config: StageReviewExtensionConfig
    ):
        self.review_service = review_service
        self.config = config

    async def on_post(
        self,
        context: ExtensionContext,
        result: Any,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Hook called after agent execution.
        Triggers stage review if applicable.
        """
        stage_type = metadata.get("stage_type")
        artifact = metadata.get("artifact")

        if not stage_type or not artifact:
            return {"review_skipped": True, "reason": "No stage or artifact"}

        if stage_type not in self.config.enabled_stages:
            return {"review_skipped": True, "reason": f"Stage {stage_type} not enabled"}

        # Execute review
        review_result = await self.review_service.review_artifact(
            stage_type=stage_type,
            artifact=artifact,
            artifact_type=metadata.get("artifact_type", "code"),
            context=context.session_context,
            agent_id=context.agent_id
        )

        # Handle result
        if not review_result.approved and self.config.block_on_failure:
            return {
                "review_passed": False,
                "should_retry": True,
                "issues": review_result.issues,
                "improved_artifact": review_result.improved_artifact,
                "consensus": review_result.consensus_level
            }

        return {
            "review_passed": review_result.approved,
            "issues": review_result.issues,
            "consensus": review_result.consensus_level,
            "rounds_completed": review_result.rounds_completed
        }


# Registration with Confucius Orchestrator
def register_stage_review_extension(orchestrator: 'ConfuciusOrchestrator'):
    """Register stage review extension with orchestrator."""

    from app.services.stage_review_service import StageReviewService

    review_service = StageReviewService(
        db_session=orchestrator.db,
        llm_registry=orchestrator.llm_registry
    )

    extension = StageReviewExtension(
        review_service=review_service,
        config=StageReviewExtensionConfig(
            enabled_stages=[
                "architecture",
                "design",
                "programming",
                "testing",
                "infrastructure"
            ],
            auto_improve=True,
            block_on_failure=True,
            require_consensus=0.6
        )
    )

    orchestrator.register_extension(
        extension,
        stages=["architecture", "design", "programming", "testing", "infrastructure"]
    )
```

---

## Fase 24.4: Optimization (Week 161-162)

**Doel:** Performance tracking en auto-tuning
**Effort:** 25 uur

### 24.4.1 Performance Tracking Service

```python
# backend/app/services/review_performance_service.py

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.stage_review import (
    StageReviewSession, StageReviewMetrics, StageModelReview
)


@dataclass
class ModelPerformance:
    """Performance metrics for a model."""
    model_name: str
    avg_response_time_ms: float
    p95_response_time_ms: float
    timeout_rate: float
    avg_issues_found: float
    consensus_alignment: float  # How often aligned with final decision
    sessions_participated: int


@dataclass
class StagePerformance:
    """Performance metrics for a stage."""
    stage_type: str
    avg_duration_ms: float
    approval_rate: float
    avg_issues_per_review: float
    second_round_rate: float
    total_reviews: int


class ReviewPerformanceService:
    """Service for tracking and analyzing review performance."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_model_performance(
        self,
        days: int = 30
    ) -> List[ModelPerformance]:
        """Get performance metrics for all models."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Query model reviews
        result = await self.db.execute(
            select(
                StageModelReview.model_name,
                func.avg(StageModelReview.response_time_ms),
                func.percentile_cont(0.95).within_group(
                    StageModelReview.response_time_ms
                ),
                func.count().filter(StageModelReview.status == "timeout"),
                func.count()
            )
            .where(StageModelReview.started_at >= cutoff)
            .group_by(StageModelReview.model_name)
        )

        performances = []
        for row in result:
            performances.append(ModelPerformance(
                model_name=row[0],
                avg_response_time_ms=row[1] or 0,
                p95_response_time_ms=row[2] or 0,
                timeout_rate=(row[3] or 0) / (row[4] or 1),
                avg_issues_found=0,  # Calculate separately
                consensus_alignment=0,  # Calculate separately
                sessions_participated=row[4] or 0
            ))

        return performances

    async def get_stage_performance(
        self,
        days: int = 30
    ) -> List[StagePerformance]:
        """Get performance metrics per stage."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(
                StageReviewSession.stage_type,
                func.avg(StageReviewMetrics.total_duration_ms),
                func.count().filter(StageReviewSession.status == "approved"),
                func.count()
            )
            .join(StageReviewMetrics)
            .where(StageReviewSession.created_at >= cutoff)
            .group_by(StageReviewSession.stage_type)
        )

        performances = []
        for row in result:
            total = row[3] or 1
            performances.append(StagePerformance(
                stage_type=row[0],
                avg_duration_ms=row[1] or 0,
                approval_rate=(row[2] or 0) / total,
                avg_issues_per_review=0,  # Calculate separately
                second_round_rate=0,  # Calculate separately
                total_reviews=total
            ))

        return performances

    async def get_recommended_thresholds(
        self,
        stage_type: str
    ) -> Dict[str, int]:
        """
        Calculate recommended thresholds based on historical data.
        Uses statistical analysis of past reviews.
        """
        # Get historical issue counts for approved reviews
        result = await self.db.execute(
            select(
                func.percentile_cont(0.75).within_group(
                    StageReviewDecision.critical_issues
                ),
                func.percentile_cont(0.75).within_group(
                    StageReviewDecision.major_issues
                )
            )
            .join(StageReviewSession)
            .where(StageReviewSession.stage_type == stage_type)
            .where(StageReviewDecision.decision == "approved")
        )

        row = result.first()

        return {
            "critical_threshold": int(row[0]) if row and row[0] else 0,
            "major_threshold": int(row[1]) if row and row[1] else 3
        }
```

---

## API Endpoints

```python
# backend/app/api/stage_review.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from uuid import UUID

from app.services.stage_review_service import StageReviewService, ReviewResult
from app.services.review_performance_service import ReviewPerformanceService
from app.deps import get_db, get_llm_registry

router = APIRouter(prefix="/stage-review", tags=["Stage Review"])


@router.post("/review")
async def review_artifact(
    stage_type: str,
    artifact: str,
    artifact_type: str = "code",
    context: Optional[dict] = None,
    force_review: bool = False,
    db=Depends(get_db),
    llm=Depends(get_llm_registry)
) -> ReviewResult:
    """Submit artifact for stage review."""
    service = StageReviewService(db, llm)
    return await service.review_artifact(
        stage_type=stage_type,
        artifact=artifact,
        artifact_type=artifact_type,
        context=context,
        force_review=force_review
    )


@router.get("/sessions/{session_id}")
async def get_review_session(
    session_id: UUID,
    db=Depends(get_db)
):
    """Get review session details."""
    # Implementation


@router.get("/performance/models")
async def get_model_performance(
    days: int = 30,
    db=Depends(get_db)
):
    """Get model performance metrics."""
    service = ReviewPerformanceService(db)
    return await service.get_model_performance(days)


@router.get("/performance/stages")
async def get_stage_performance(
    days: int = 30,
    db=Depends(get_db)
):
    """Get stage performance metrics."""
    service = ReviewPerformanceService(db)
    return await service.get_stage_performance(days)


@router.get("/config/{stage_type}")
async def get_stage_config(stage_type: str):
    """Get configuration for a stage."""
    from app.config.stage_council_config import get_stage_config
    return get_stage_config(stage_type)
```

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/unit/services/test_stage_review_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.stage_review_service import StageReviewService, ParsedIssue
from app.models.stage_review import IssueSeverity, IssueCategory


class TestStageReviewService:
    """Unit tests for StageReviewService."""

    @pytest.fixture
    def service(self):
        db = AsyncMock()
        llm = MagicMock()
        return StageReviewService(db, llm)

    def test_parse_single_issue_valid(self, service):
        """Test parsing a valid issue block."""
        issue_text = """
SEVERITY: critical
CATEGORY: security
TITLE: SQL Injection vulnerability
DESCRIPTION: User input is directly concatenated into SQL query
LINE: 42
SUGGESTED_FIX: Use parameterized queries
CODE_SNIPPET: f"SELECT * FROM users WHERE id = {user_id}"
"""
        result = service._parse_single_issue(issue_text)

        assert result is not None
        assert result.severity == IssueSeverity.CRITICAL
        assert result.category == IssueCategory.SECURITY
        assert result.title == "SQL Injection vulnerability"
        assert result.line_start == 42

    def test_deduplicate_issues(self, service):
        """Test issue deduplication."""
        issues = [
            {"severity": "critical", "category": "security", "title": "SQL Injection"},
            {"severity": "critical", "category": "security", "title": "SQL Injection"},
            {"severity": "major", "category": "performance", "title": "N+1 Query"}
        ]

        result = service._deduplicate_issues(issues, num_models=3)

        assert len(result) == 2
        # SQL Injection should have higher consensus
        sql_issue = next(i for i in result if "SQL" in i["title"])
        assert sql_issue["consensus_score"] == 2/3

    def test_evaluate_threshold_exceeds(self, service):
        """Test threshold evaluation when exceeded."""
        from app.config.stage_council_config import StageCouncilConfig

        config = StageCouncilConfig(
            primary_models=["test"],
            critical_threshold=0,
            major_threshold=2
        )

        issues = [
            {"severity": "critical", "consensus_score": 0.6},
        ]

        result = service._evaluate_threshold(issues, config)
        assert result is True  # Should trigger second round

    def test_make_decision_approved(self, service):
        """Test decision making for approval."""
        from app.config.stage_council_config import StageCouncilConfig

        config = StageCouncilConfig(
            primary_models=["test"],
            critical_threshold=0,
            major_threshold=3,
            consensus_minimum=0.6
        )

        issues = [
            {"severity": "minor", "consensus_score": 0.8},
        ]

        result = service._make_decision(issues, consensus=75.0, config=config)
        assert result.value == "approved"
```

---

## Implementatie Timeline

| Week | Fase | Deliverables | Hours |
|------|------|--------------|-------|
| 157 | 24.1a | Database schema, models | 10 |
| 157 | 24.1b | Stage configs, prompts | 8 |
| 158 | 24.1c | Core StageReviewService | 12 |
| 159 | 24.2a | ArtifactImprovementService | 15 |
| 159 | 24.2b | Second round integration | 10 |
| 160 | 24.2c | Testing & refinement | 10 |
| 160 | 24.3a | Confucius extension | 12 |
| 161 | 24.3b | All stages integration | 10 |
| 161 | 24.3c | API endpoints | 8 |
| 162 | 24.4a | Performance tracking | 12 |
| 162 | 24.4b | Auto-tuning, documentation | 13 |
| **Total** | | | **120** |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Review Accuracy | >90% | Issues found vs post-release bugs |
| Second Round Effectiveness | >70% | Reviews passing after improvement |
| Consensus Correlation | >0.8 | Consensus vs actual quality |
| Performance | <3 min | Average review duration |
| Coverage | 100% | Stages with active reviews |

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM Hallucinations | Medium | Require consensus, line references |
| High Latency | Medium | Parallel execution, caching |
| Cost Explosion | Medium | Local models, tiered approach |
| False Positives | Low | Tunable thresholds, human override |
| Model Unavailability | Low | Fallback to secondary models |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [confucius-orchestrator-integration-plan.md](./confucius-orchestrator-integration-plan.md) | CCA Integration (prerequisite) |
| [llm-council-improvements-plan.md](./llm-council-improvements-plan.md) | Base LLM Council improvements |
| [ai-dream-team-multi-model-strategy.md](./ai-dream-team-multi-model-strategy.md) | Multi-model routing strategy |
| [phases-planned.md](../roadmap/phases-planned.md) | Project roadmap |

---

*Document Version: 1.0*
*Created: Week 145 (2026-01-12)*
*Author: Claude Opus 4.5*

| Document | Description |
|----------|-------------|
| [confucius-orchestrator-integration-plan.md](./confucius-orchestrator-integration-plan.md) | CCA Integration (prerequisite) |
| [llm-council-improvements-plan.md](./llm-council-improvements-plan.md) | Base LLM Council improvements |
| [ai-dream-team-multi-model-strategy.md](./ai-dream-team-multi-model-strategy.md) | Multi-model routing strategy |
| [phases-planned.md](../roadmap/phases-planned.md) | Project roadmap |

---

*Document continues in Part 2...*
