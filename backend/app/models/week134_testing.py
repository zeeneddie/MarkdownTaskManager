"""
Week 134-135: Testing Excellence Models (Fase 23)

SQLAlchemy models and dataclasses for advanced testing strategies:
- Characterization Tests (Golden Master pattern)
- Visual Regression Testing (screenshot comparison)
- Dual-Run Comparison (parallel execution)
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


# ============================================================================
# Enums
# ============================================================================

class TestType(str, Enum):
    """Types of testing excellence tests."""
    CHARACTERIZATION = "characterization"
    VISUAL_REGRESSION = "visual_regression"
    DUAL_RUN = "dual_run"
    GOLDEN_MASTER = "golden_master"


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RECORDING = "recording"
    RUNNING = "running"
    COMPARING = "comparing"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    BASELINE_UPDATED = "baseline_updated"


class ComparisonResult(str, Enum):
    """Result of comparison operations."""
    MATCH = "match"
    MISMATCH = "mismatch"
    NEW_BASELINE = "new_baseline"
    IGNORED = "ignored"
    ERROR = "error"


class DiffType(str, Enum):
    """Types of differences detected."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    TYPE_CHANGE = "type_change"
    ORDER_CHANGE = "order_change"
    VISUAL = "visual"


class ScreenshotTool(str, Enum):
    """Screenshot capture tools."""
    PLAYWRIGHT = "playwright"
    PUPPETEER = "puppeteer"
    SELENIUM = "selenium"
    CYPRESS = "cypress"
    PERCY = "percy"
    CHROMATIC = "chromatic"


class OutputFormat(str, Enum):
    """Output data formats for comparison."""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    HTML = "html"
    TEXT = "text"
    BINARY = "binary"
    DATABASE = "database"


class ConfidenceLevel(str, Enum):
    """Confidence level for test results."""
    HIGH = "high"         # >95% confidence
    MEDIUM = "medium"     # 70-95% confidence
    LOW = "low"           # <70% confidence


# ============================================================================
# SQLAlchemy Models
# ============================================================================

class CharacterizationTestModel(Base):
    """Golden Master / Characterization test session."""
    __tablename__ = "characterization_tests"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(String(255), nullable=False, index=True)
    migration_session_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    name = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)

    # Test Configuration
    legacy_system_path = Column(String(1024), nullable=False)
    new_system_path = Column(String(1024), nullable=True)
    test_endpoint = Column(String(512), nullable=True)
    input_format = Column(String(50), default="json")
    output_format = Column(String(50), default="json")

    # Baseline (Golden Master)
    baseline_recorded = Column(Boolean, default=False)
    baseline_recorded_at = Column(DateTime, nullable=True)
    baseline_data = Column(JSONB, nullable=True)
    baseline_hash = Column(String(64), nullable=True)

    # Test Execution
    status = Column(String(50), default="pending")
    last_run_at = Column(DateTime, nullable=True)
    last_result = Column(String(50), nullable=True)
    run_count = Column(Integer, default=0)
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)

    # Results
    current_output = Column(JSONB, nullable=True)
    current_output_hash = Column(String(64), nullable=True)
    differences = Column(JSONB, nullable=True)
    diff_count = Column(Integer, default=0)
    match_percentage = Column(Float, default=0.0)

    # Metadata
    input_scenarios = Column(JSONB, nullable=True)  # List of test inputs
    ignored_fields = Column(JSONB, nullable=True)   # Fields to ignore in comparison
    tolerance_rules = Column(JSONB, nullable=True)  # Numeric tolerance, date formats
    tags = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    __table_args__ = (
        Index("ix_characterization_tests_status", "status"),
        Index("ix_characterization_tests_name", "name"),
    )


class CharacterizationTestRunModel(Base):
    """Individual run of a characterization test."""
    __tablename__ = "characterization_test_runs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    test_id = Column(PGUUID(as_uuid=True), ForeignKey("characterization_tests.id", ondelete="CASCADE"), nullable=False, index=True)

    # Input
    input_data = Column(JSONB, nullable=True)
    input_scenario = Column(String(255), nullable=True)

    # Legacy Output
    legacy_output = Column(JSONB, nullable=True)
    legacy_output_hash = Column(String(64), nullable=True)
    legacy_duration_ms = Column(Integer, default=0)
    legacy_error = Column(Text, nullable=True)

    # New System Output
    new_output = Column(JSONB, nullable=True)
    new_output_hash = Column(String(64), nullable=True)
    new_duration_ms = Column(Integer, default=0)
    new_error = Column(Text, nullable=True)

    # Comparison
    result = Column(String(50), nullable=False)
    differences = Column(JSONB, nullable=True)
    diff_count = Column(Integer, default=0)
    match_percentage = Column(Float, default=100.0)

    # Metadata
    executed_at = Column(DateTime, default=lambda: datetime.utcnow())
    duration_ms = Column(Integer, default=0)


class VisualRegressionTestModel(Base):
    """Visual regression test session."""
    __tablename__ = "visual_regression_tests"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(String(255), nullable=False, index=True)
    migration_session_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    name = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    legacy_url = Column(String(1024), nullable=False)
    new_url = Column(String(1024), nullable=True)
    screenshot_tool = Column(String(50), default="playwright")
    viewport_width = Column(Integer, default=1920)
    viewport_height = Column(Integer, default=1080)
    device_scale_factor = Column(Float, default=1.0)

    # Capture Settings
    wait_for_selector = Column(String(512), nullable=True)
    wait_timeout_ms = Column(Integer, default=5000)
    hide_selectors = Column(JSONB, nullable=True)  # Elements to hide
    mask_selectors = Column(JSONB, nullable=True)  # Elements to mask
    scroll_to_bottom = Column(Boolean, default=False)
    full_page = Column(Boolean, default=True)

    # Baseline
    baseline_screenshot_path = Column(String(1024), nullable=True)
    baseline_captured_at = Column(DateTime, nullable=True)
    baseline_thumbnail_path = Column(String(1024), nullable=True)

    # Test Execution
    status = Column(String(50), default="pending")
    last_run_at = Column(DateTime, nullable=True)
    last_result = Column(String(50), nullable=True)
    run_count = Column(Integer, default=0)
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)

    # Results
    current_screenshot_path = Column(String(1024), nullable=True)
    diff_screenshot_path = Column(String(1024), nullable=True)
    diff_percentage = Column(Float, default=0.0)
    diff_pixels = Column(Integer, default=0)
    threshold = Column(Float, default=0.01)  # 1% default threshold

    # Pages to test
    pages = Column(JSONB, nullable=True)  # List of page configs
    tags = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    __table_args__ = (
        Index("ix_visual_regression_tests_status", "status"),
    )


class VisualRegressionRunModel(Base):
    """Individual run of a visual regression test."""
    __tablename__ = "visual_regression_runs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    test_id = Column(PGUUID(as_uuid=True), ForeignKey("visual_regression_tests.id", ondelete="CASCADE"), nullable=False, index=True)
    page_url = Column(String(1024), nullable=False)
    page_name = Column(String(255), nullable=True)

    # Screenshots
    baseline_path = Column(String(1024), nullable=True)
    actual_path = Column(String(1024), nullable=True)
    diff_path = Column(String(1024), nullable=True)

    # Comparison
    result = Column(String(50), nullable=False)
    diff_percentage = Column(Float, default=0.0)
    diff_pixels = Column(Integer, default=0)
    total_pixels = Column(Integer, default=0)
    threshold_used = Column(Float, default=0.01)

    # Regions with differences
    diff_regions = Column(JSONB, nullable=True)  # [{x, y, width, height}]

    # Metadata
    viewport = Column(JSONB, nullable=True)
    executed_at = Column(DateTime, default=lambda: datetime.utcnow())
    duration_ms = Column(Integer, default=0)
    error = Column(Text, nullable=True)


class DualRunComparisonModel(Base):
    """Dual-run comparison session for parallel execution."""
    __tablename__ = "dual_run_comparisons"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(String(255), nullable=False, index=True)
    migration_session_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    name = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)

    # Systems Configuration
    legacy_system = Column(JSONB, nullable=False)  # {url, type, config}
    new_system = Column(JSONB, nullable=False)     # {url, type, config}

    # Traffic Configuration
    traffic_split = Column(Float, default=0.0)  # % to new system
    shadow_mode = Column(Boolean, default=True)  # Run both, return legacy
    comparison_mode = Column(String(50), default="full")  # full, sample, key_fields

    # Comparison Settings
    compare_response_body = Column(Boolean, default=True)
    compare_response_code = Column(Boolean, default=True)
    compare_response_time = Column(Boolean, default=True)
    time_tolerance_ms = Column(Integer, default=100)
    ignored_fields = Column(JSONB, nullable=True)
    field_mappings = Column(JSONB, nullable=True)  # Field name transformations

    # Execution Status
    status = Column(String(50), default="pending")
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False)

    # Statistics
    total_requests = Column(Integer, default=0)
    matched_requests = Column(Integer, default=0)
    mismatched_requests = Column(Integer, default=0)
    error_requests = Column(Integer, default=0)
    match_percentage = Column(Float, default=0.0)
    avg_legacy_time_ms = Column(Float, default=0.0)
    avg_new_time_ms = Column(Float, default=0.0)
    performance_improvement = Column(Float, default=0.0)

    # Detailed Results
    mismatch_summary = Column(JSONB, nullable=True)
    error_summary = Column(JSONB, nullable=True)

    tags = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    __table_args__ = (
        Index("ix_dual_run_comparisons_status", "status"),
        Index("ix_dual_run_comparisons_is_active", "is_active"),
    )


class DualRunRequestModel(Base):
    """Individual request in a dual-run comparison."""
    __tablename__ = "dual_run_requests"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    comparison_id = Column(PGUUID(as_uuid=True), ForeignKey("dual_run_comparisons.id", ondelete="CASCADE"), nullable=False, index=True)

    # Request Details
    request_method = Column(String(10), nullable=False)
    request_path = Column(String(1024), nullable=False)
    request_headers = Column(JSONB, nullable=True)
    request_body = Column(JSONB, nullable=True)

    # Legacy Response
    legacy_status_code = Column(Integer, nullable=True)
    legacy_response_body = Column(JSONB, nullable=True)
    legacy_response_time_ms = Column(Integer, default=0)
    legacy_error = Column(Text, nullable=True)

    # New System Response
    new_status_code = Column(Integer, nullable=True)
    new_response_body = Column(JSONB, nullable=True)
    new_response_time_ms = Column(Integer, default=0)
    new_error = Column(Text, nullable=True)

    # Comparison Result
    result = Column(String(50), nullable=False)
    differences = Column(JSONB, nullable=True)
    diff_count = Column(Integer, default=0)

    # Metadata
    executed_at = Column(DateTime, default=lambda: datetime.utcnow())
    correlation_id = Column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_dual_run_requests_result", "result"),
        Index("ix_dual_run_requests_executed_at", "executed_at"),
    )


class TestingExcellenceSummaryModel(Base):
    """Summary of testing excellence for a migration."""
    __tablename__ = "testing_excellence_summaries"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(String(255), nullable=False, index=True)
    migration_session_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)

    # Characterization Tests
    char_test_count = Column(Integer, default=0)
    char_test_passed = Column(Integer, default=0)
    char_test_failed = Column(Integer, default=0)
    char_test_coverage = Column(Float, default=0.0)

    # Visual Regression
    visual_test_count = Column(Integer, default=0)
    visual_test_passed = Column(Integer, default=0)
    visual_test_failed = Column(Integer, default=0)
    visual_pages_covered = Column(Integer, default=0)

    # Dual-Run
    dual_run_total = Column(Integer, default=0)
    dual_run_matched = Column(Integer, default=0)
    dual_run_mismatched = Column(Integer, default=0)
    dual_run_match_rate = Column(Float, default=0.0)

    # Overall Confidence
    overall_confidence = Column(String(20), default="low")
    confidence_score = Column(Float, default=0.0)
    migration_ready = Column(Boolean, default=False)

    # Recommendations
    recommendations = Column(JSONB, nullable=True)
    blocking_issues = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())


# ============================================================================
# Dataclasses for Service Layer
# ============================================================================

@dataclass
class TestInput:
    """Input scenario for characterization test."""
    name: str
    data: Dict[str, Any]
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class FieldDifference:
    """Difference in a specific field."""
    field_path: str
    diff_type: DiffType
    expected_value: Any
    actual_value: Any
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_path": self.field_path,
            "diff_type": self.diff_type.value if isinstance(self.diff_type, Enum) else self.diff_type,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "message": self.message,
        }


@dataclass
class CharacterizationTestResult:
    """Result of a characterization test run."""
    test_id: str
    test_name: str
    result: ComparisonResult
    input_scenario: Optional[str] = None
    legacy_output: Optional[Dict[str, Any]] = None
    new_output: Optional[Dict[str, Any]] = None
    differences: List[FieldDifference] = field(default_factory=list)
    diff_count: int = 0
    match_percentage: float = 100.0
    legacy_duration_ms: int = 0
    new_duration_ms: int = 0
    error: Optional[str] = None
    executed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "result": self.result.value if isinstance(self.result, Enum) else self.result,
            "input_scenario": self.input_scenario,
            "legacy_output": self.legacy_output,
            "new_output": self.new_output,
            "differences": [d.to_dict() for d in self.differences],
            "diff_count": self.diff_count,
            "match_percentage": self.match_percentage,
            "legacy_duration_ms": self.legacy_duration_ms,
            "new_duration_ms": self.new_duration_ms,
            "error": self.error,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


@dataclass
class DiffRegion:
    """Region with visual differences."""
    x: int
    y: int
    width: int
    height: int
    diff_pixels: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "diff_pixels": self.diff_pixels,
        }


@dataclass
class VisualRegressionResult:
    """Result of a visual regression test run."""
    test_id: str
    test_name: str
    page_url: str
    result: ComparisonResult
    baseline_path: Optional[str] = None
    actual_path: Optional[str] = None
    diff_path: Optional[str] = None
    diff_percentage: float = 0.0
    diff_pixels: int = 0
    total_pixels: int = 0
    threshold: float = 0.01
    diff_regions: List[DiffRegion] = field(default_factory=list)
    viewport_width: int = 1920
    viewport_height: int = 1080
    error: Optional[str] = None
    executed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "page_url": self.page_url,
            "result": self.result.value if isinstance(self.result, Enum) else self.result,
            "baseline_path": self.baseline_path,
            "actual_path": self.actual_path,
            "diff_path": self.diff_path,
            "diff_percentage": self.diff_percentage,
            "diff_pixels": self.diff_pixels,
            "total_pixels": self.total_pixels,
            "threshold": self.threshold,
            "diff_regions": [r.to_dict() for r in self.diff_regions],
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "error": self.error,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


@dataclass
class DualRunResult:
    """Result of a dual-run comparison request."""
    comparison_id: str
    request_path: str
    request_method: str
    result: ComparisonResult
    legacy_status_code: Optional[int] = None
    new_status_code: Optional[int] = None
    legacy_response_time_ms: int = 0
    new_response_time_ms: int = 0
    differences: List[FieldDifference] = field(default_factory=list)
    diff_count: int = 0
    legacy_error: Optional[str] = None
    new_error: Optional[str] = None
    correlation_id: Optional[str] = None
    executed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "request_path": self.request_path,
            "request_method": self.request_method,
            "result": self.result.value if isinstance(self.result, Enum) else self.result,
            "legacy_status_code": self.legacy_status_code,
            "new_status_code": self.new_status_code,
            "legacy_response_time_ms": self.legacy_response_time_ms,
            "new_response_time_ms": self.new_response_time_ms,
            "differences": [d.to_dict() for d in self.differences],
            "diff_count": self.diff_count,
            "legacy_error": self.legacy_error,
            "new_error": self.new_error,
            "correlation_id": self.correlation_id,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


@dataclass
class TestingExcellenceSummary:
    """Summary of all testing excellence results."""
    project_id: str
    migration_session_id: Optional[str] = None

    # Characterization
    char_test_count: int = 0
    char_test_passed: int = 0
    char_test_failed: int = 0
    char_test_coverage: float = 0.0

    # Visual Regression
    visual_test_count: int = 0
    visual_test_passed: int = 0
    visual_test_failed: int = 0
    visual_pages_covered: int = 0

    # Dual-Run
    dual_run_total: int = 0
    dual_run_matched: int = 0
    dual_run_mismatched: int = 0
    dual_run_match_rate: float = 0.0

    # Overall
    overall_confidence: ConfidenceLevel = ConfidenceLevel.LOW
    confidence_score: float = 0.0
    migration_ready: bool = False
    recommendations: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "migration_session_id": self.migration_session_id,
            "characterization": {
                "test_count": self.char_test_count,
                "passed": self.char_test_passed,
                "failed": self.char_test_failed,
                "coverage": self.char_test_coverage,
            },
            "visual_regression": {
                "test_count": self.visual_test_count,
                "passed": self.visual_test_passed,
                "failed": self.visual_test_failed,
                "pages_covered": self.visual_pages_covered,
            },
            "dual_run": {
                "total": self.dual_run_total,
                "matched": self.dual_run_matched,
                "mismatched": self.dual_run_mismatched,
                "match_rate": self.dual_run_match_rate,
            },
            "overall": {
                "confidence": self.overall_confidence.value if isinstance(self.overall_confidence, Enum) else self.overall_confidence,
                "confidence_score": self.confidence_score,
                "migration_ready": self.migration_ready,
            },
            "recommendations": self.recommendations,
            "blocking_issues": self.blocking_issues,
        }


# ============================================================================
# Confidence Calculation
# ============================================================================

def calculate_confidence(summary: TestingExcellenceSummary) -> tuple[ConfidenceLevel, float]:
    """Calculate overall confidence based on test results."""
    scores = []

    # Characterization tests weight: 40%
    if summary.char_test_count > 0:
        char_score = (summary.char_test_passed / summary.char_test_count) * 100
        scores.append(char_score * 0.4)

    # Visual regression weight: 30%
    if summary.visual_test_count > 0:
        visual_score = (summary.visual_test_passed / summary.visual_test_count) * 100
        scores.append(visual_score * 0.3)

    # Dual-run weight: 30%
    if summary.dual_run_total > 0:
        dual_score = summary.dual_run_match_rate
        scores.append(dual_score * 0.3)

    if not scores:
        return ConfidenceLevel.LOW, 0.0

    total_score = sum(scores)

    if total_score >= 95:
        return ConfidenceLevel.HIGH, total_score
    elif total_score >= 70:
        return ConfidenceLevel.MEDIUM, total_score
    else:
        return ConfidenceLevel.LOW, total_score
