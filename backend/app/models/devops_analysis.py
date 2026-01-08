# backend/app/models/devops_analysis.py
"""
Database models for GitHub/DevOps Analysis - Week 97-98 (Fase 14).

Provides repository intelligence for improved extraction and project assessment.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.database import Base


class RepositoryPlatform(str, Enum):
    """Supported repository platforms."""
    GITHUB = "github"
    AZURE_DEVOPS = "azure_devops"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class AnalysisDepth(str, Enum):
    """Analysis depth levels."""
    QUICK = "quick"  # Basic metrics only
    STANDARD = "standard"  # + hot spots, PR analysis
    FULL = "full"  # + contributor analysis, CI/CD


class RepositoryAnalysis(Base):
    """Repository analysis session."""
    __tablename__ = "repository_analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Repository info
    platform = Column(SQLEnum(RepositoryPlatform), nullable=False)
    repository_url = Column(String(500), nullable=False)
    repository_name = Column(String(200), nullable=False)
    default_branch = Column(String(100), default="main")

    # Analysis configuration
    analysis_depth = Column(SQLEnum(AnalysisDepth), default=AnalysisDepth.STANDARD)
    include_forks = Column(Boolean, default=False)
    max_commits = Column(Integer, default=1000)
    max_prs = Column(Integer, default=500)

    # Analysis results summary
    total_commits = Column(Integer, default=0)
    total_prs = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    total_contributors = Column(Integer, default=0)

    # Metrics
    avg_pr_review_time_hours = Column(Float, nullable=True)
    avg_pr_size_lines = Column(Float, nullable=True)
    merge_conflict_rate = Column(Float, nullable=True)  # 0.0-1.0
    test_coverage_percent = Column(Float, nullable=True)
    build_success_rate = Column(Float, nullable=True)  # 0.0-1.0

    # Status
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    hot_spots = relationship("HotSpot", back_populates="analysis", cascade="all, delete-orphan")
    contributors = relationship("ContributorAnalysis", back_populates="analysis", cascade="all, delete-orphan")
    pr_patterns = relationship("PRPattern", back_populates="analysis", cascade="all, delete-orphan")
    ci_pipelines = relationship("CIPipelineAnalysis", back_populates="analysis", cascade="all, delete-orphan")


class HotSpot(Base):
    """Code hot spots - files with high change frequency."""
    __tablename__ = "hot_spots"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("repository_analyses.id"), nullable=False)

    # File info
    file_path = Column(String(500), nullable=False)
    file_extension = Column(String(20), nullable=True)

    # Metrics
    change_count = Column(Integer, default=0)  # Number of commits touching this file
    lines_changed_total = Column(Integer, default=0)
    distinct_authors = Column(Integer, default=0)

    # Scores (0.0-1.0)
    change_frequency_score = Column(Float, default=0.0)
    complexity_score = Column(Float, nullable=True)  # Based on churn
    risk_score = Column(Float, default=0.0)  # Combined metric

    # Context
    last_modified = Column(DateTime, nullable=True)
    associated_bugs = Column(Integer, default=0)  # Linked bug fixes

    # Relationship
    analysis = relationship("RepositoryAnalysis", back_populates="hot_spots")


class ContributorAnalysis(Base):
    """Contributor analysis for knowledge silo detection."""
    __tablename__ = "contributor_analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("repository_analyses.id"), nullable=False)

    # Contributor info
    contributor_id = Column(String(100), nullable=False)  # GitHub/Azure ID
    contributor_name = Column(String(200), nullable=True)
    contributor_email = Column(String(200), nullable=True)

    # Activity metrics
    total_commits = Column(Integer, default=0)
    total_prs = Column(Integer, default=0)
    total_reviews = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_removed = Column(Integer, default=0)

    # Focus areas
    primary_directories = Column(JSON, default=list)  # Top 5 directories
    primary_file_types = Column(JSON, default=list)  # Top 5 file extensions

    # Knowledge silo indicators
    bus_factor_contribution = Column(Float, default=0.0)  # 0.0-1.0
    is_sole_maintainer_files = Column(Integer, default=0)  # Files only this person touched

    # Activity period
    first_commit_date = Column(DateTime, nullable=True)
    last_commit_date = Column(DateTime, nullable=True)

    # Relationship
    analysis = relationship("RepositoryAnalysis", back_populates="contributors")


class PRPattern(Base):
    """Pull request patterns and review analysis."""
    __tablename__ = "pr_patterns"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("repository_analyses.id"), nullable=False)

    # PR info
    pr_number = Column(Integer, nullable=False)
    pr_title = Column(String(500), nullable=True)
    pr_state = Column(String(50), nullable=True)  # open, closed, merged

    # Size metrics
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    changed_files = Column(Integer, default=0)

    # Review metrics
    review_count = Column(Integer, default=0)
    approval_count = Column(Integer, default=0)
    change_request_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)

    # Time metrics (in hours)
    time_to_first_review = Column(Float, nullable=True)
    time_to_merge = Column(Float, nullable=True)

    # Patterns detected
    had_merge_conflicts = Column(Boolean, default=False)
    had_ci_failures = Column(Boolean, default=False)
    required_rework = Column(Boolean, default=False)  # Changes requested then updated

    # Timestamps
    created_at = Column(DateTime, nullable=True)
    merged_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Relationship
    analysis = relationship("RepositoryAnalysis", back_populates="pr_patterns")


class CIPipelineAnalysis(Base):
    """CI/CD pipeline analysis."""
    __tablename__ = "ci_pipeline_analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("repository_analyses.id"), nullable=False)

    # Pipeline info
    pipeline_name = Column(String(200), nullable=False)
    pipeline_type = Column(String(50), nullable=True)  # build, test, deploy, etc.

    # Run statistics
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)

    # Time metrics (in minutes)
    avg_duration_minutes = Column(Float, nullable=True)
    p95_duration_minutes = Column(Float, nullable=True)

    # Quality metrics
    success_rate = Column(Float, default=0.0)  # 0.0-1.0
    flaky_test_count = Column(Integer, default=0)

    # Configuration
    triggers = Column(JSON, default=list)  # push, pr, schedule, etc.
    stages = Column(JSON, default=list)  # Pipeline stages

    # Recent runs sample
    recent_runs = Column(JSON, default=list)  # Last 10 runs summary

    # Relationship
    analysis = relationship("RepositoryAnalysis", back_populates="ci_pipelines")


class IssueCorrelation(Base):
    """Issue/bug correlation with code."""
    __tablename__ = "issue_correlations"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("repository_analyses.id"), nullable=False)

    # Issue info
    issue_number = Column(Integer, nullable=False)
    issue_title = Column(String(500), nullable=True)
    issue_type = Column(String(50), nullable=True)  # bug, feature, enhancement, etc.
    issue_state = Column(String(50), nullable=True)  # open, closed

    # Labels/tags
    labels = Column(JSON, default=list)
    priority = Column(String(50), nullable=True)

    # Correlation
    linked_pr_numbers = Column(JSON, default=list)
    affected_files = Column(JSON, default=list)  # Files mentioned or changed in linked PRs

    # Backlog integration
    suggested_epic = Column(String(200), nullable=True)
    suggested_work_type = Column(String(50), nullable=True)  # bug, feature, maintenance
    confidence_score = Column(Float, default=0.5)  # 0.0-1.0

    # Timestamps
    created_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)


class RepositoryInsight(Base):
    """High-level repository insights and recommendations."""
    __tablename__ = "repository_insights"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("repository_analyses.id"), nullable=False)

    # Insight categorization
    insight_type = Column(String(50), nullable=False)  # risk, opportunity, recommendation
    category = Column(String(50), nullable=False)  # code_quality, team, process, ci_cd

    # Content
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Severity/importance (0.0-1.0)
    severity = Column(Float, default=0.5)

    # Evidence
    evidence = Column(JSON, default=dict)  # Supporting data
    affected_files = Column(JSON, default=list)

    # Recommendations
    recommendations = Column(JSON, default=list)  # Action items

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
