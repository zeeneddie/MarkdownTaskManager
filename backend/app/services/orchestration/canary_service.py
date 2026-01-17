"""
MP-QW-5: Canary in the Code Mine Service

Detect code quality issues from AI struggles.
When AI has difficulty with code, it's often a signal of underlying quality problems.

Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- Track AI struggle signals
- Map struggles to code quality indicators
- Generate refactoring recommendations
- Prioritize technical debt

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of AI struggle signals."""
    DUPLICATE_LOGIC_MISSED = "duplicate_logic_missed"
    CONTEXT_LIMIT_HIT = "context_limit_hit"
    FLAWED_TEST_REASONING = "flawed_test_reasoning"
    COMPLEX_CONDITIONAL = "complex_conditional"
    HIDDEN_COUPLING = "hidden_coupling"
    INCONSISTENT_NAMING = "inconsistent_naming"
    UNCLEAR_RESPONSIBILITY = "unclear_responsibility"
    MISSING_ABSTRACTION = "missing_abstraction"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    MAGIC_VALUES = "magic_values"


class SeverityLevel(Enum):
    """Severity of the code quality issue."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RefactoringType(Enum):
    """Type of refactoring recommended."""
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    MOVE_METHOD = "move_method"
    RENAME = "rename"
    INTRODUCE_PARAMETER_OBJECT = "introduce_parameter_object"
    REPLACE_CONDITIONAL_WITH_POLYMORPHISM = "replace_conditional_with_polymorphism"
    REMOVE_DUPLICATION = "remove_duplication"
    SIMPLIFY_CONDITIONAL = "simplify_conditional"
    INTRODUCE_CONSTANT = "introduce_constant"
    BREAK_DEPENDENCY = "break_dependency"


@dataclass
class CanarySignal:
    """A signal indicating AI struggle with code."""
    id: UUID
    code_path: str
    signal_type: SignalType
    severity: SeverityLevel
    description: str
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    acknowledged: bool
    recommendation: str
    context: Dict[str, Any] = field(default_factory=dict)
    related_paths: List[str] = field(default_factory=list)


@dataclass
class RefactoringCandidate:
    """A candidate for refactoring based on signals."""
    id: UUID
    code_path: str
    refactoring_type: RefactoringType
    priority: int  # 1-10, higher = more urgent
    effort_estimate: str  # "small", "medium", "large"
    signals: List[UUID]  # Signal IDs that led to this candidate
    description: str
    suggested_approach: str
    created_at: datetime
    completed: bool = False


@dataclass
class CodeHealthReport:
    """Health report for a code area."""
    path: str
    signal_count: int
    severity_breakdown: Dict[SeverityLevel, int]
    top_issues: List[SignalType]
    health_score: float  # 0-100
    trend: str  # "improving", "stable", "degrading"
    recommendations: List[RefactoringCandidate]


class CanaryService:
    """
    Service for detecting code quality issues from AI struggles.

    The "Canary in the Code Mine" pattern recognizes that when AI
    struggles with code, it's often revealing underlying quality issues
    that affect human developers too.
    """

    # Severity mappings for signal types
    SIGNAL_SEVERITY = {
        SignalType.DUPLICATE_LOGIC_MISSED: SeverityLevel.MEDIUM,
        SignalType.CONTEXT_LIMIT_HIT: SeverityLevel.HIGH,
        SignalType.FLAWED_TEST_REASONING: SeverityLevel.HIGH,
        SignalType.COMPLEX_CONDITIONAL: SeverityLevel.MEDIUM,
        SignalType.HIDDEN_COUPLING: SeverityLevel.HIGH,
        SignalType.INCONSISTENT_NAMING: SeverityLevel.LOW,
        SignalType.UNCLEAR_RESPONSIBILITY: SeverityLevel.MEDIUM,
        SignalType.MISSING_ABSTRACTION: SeverityLevel.MEDIUM,
        SignalType.CIRCULAR_DEPENDENCY: SeverityLevel.CRITICAL,
        SignalType.MAGIC_VALUES: SeverityLevel.LOW,
    }

    # Recommended refactorings for each signal type
    SIGNAL_REFACTORINGS = {
        SignalType.DUPLICATE_LOGIC_MISSED: RefactoringType.REMOVE_DUPLICATION,
        SignalType.CONTEXT_LIMIT_HIT: RefactoringType.EXTRACT_CLASS,
        SignalType.FLAWED_TEST_REASONING: RefactoringType.EXTRACT_METHOD,
        SignalType.COMPLEX_CONDITIONAL: RefactoringType.SIMPLIFY_CONDITIONAL,
        SignalType.HIDDEN_COUPLING: RefactoringType.BREAK_DEPENDENCY,
        SignalType.INCONSISTENT_NAMING: RefactoringType.RENAME,
        SignalType.UNCLEAR_RESPONSIBILITY: RefactoringType.MOVE_METHOD,
        SignalType.MISSING_ABSTRACTION: RefactoringType.EXTRACT_CLASS,
        SignalType.CIRCULAR_DEPENDENCY: RefactoringType.BREAK_DEPENDENCY,
        SignalType.MAGIC_VALUES: RefactoringType.INTRODUCE_CONSTANT,
    }

    def __init__(self):
        self._signals: Dict[UUID, CanarySignal] = {}
        self._path_signals: Dict[str, List[UUID]] = {}  # path -> signal IDs
        self._candidates: Dict[UUID, RefactoringCandidate] = {}

    def report_signal(
        self,
        code_path: str,
        signal_type: SignalType,
        description: str,
        context: Optional[Dict[str, Any]] = None,
        related_paths: Optional[List[str]] = None,
        severity_override: Optional[SeverityLevel] = None
    ) -> CanarySignal:
        """
        Report an AI struggle signal.

        Args:
            code_path: Path to the code that caused the struggle
            signal_type: Type of struggle signal
            description: Human-readable description of the issue
            context: Additional context about the struggle
            related_paths: Other paths related to this issue
            severity_override: Override the default severity

        Returns:
            Created or updated CanarySignal
        """
        now = datetime.now(timezone.utc)

        # Check for existing signal of same type at same path
        existing = self._find_existing_signal(code_path, signal_type)
        if existing:
            # Update existing signal
            existing.occurrences += 1
            existing.last_seen = now
            if context:
                existing.context.update(context)
            if related_paths:
                existing.related_paths.extend(p for p in related_paths if p not in existing.related_paths)

            # Escalate severity if recurring
            if existing.occurrences >= 3 and existing.severity != SeverityLevel.CRITICAL:
                existing.severity = self._escalate_severity(existing.severity)

            logger.info(f"Updated canary signal {existing.id}: {signal_type.value} at {code_path} (occurrence #{existing.occurrences})")
            return existing

        # Create new signal
        severity = severity_override or self.SIGNAL_SEVERITY.get(signal_type, SeverityLevel.MEDIUM)
        recommendation = self._generate_recommendation(signal_type, code_path)

        signal = CanarySignal(
            id=uuid4(),
            code_path=code_path,
            signal_type=signal_type,
            severity=severity,
            description=description,
            occurrences=1,
            first_seen=now,
            last_seen=now,
            acknowledged=False,
            recommendation=recommendation,
            context=context or {},
            related_paths=related_paths or [],
        )

        self._signals[signal.id] = signal

        if code_path not in self._path_signals:
            self._path_signals[code_path] = []
        self._path_signals[code_path].append(signal.id)

        # Create refactoring candidate if severe enough
        if severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
            self._create_refactoring_candidate(signal)

        logger.info(f"Created canary signal {signal.id}: {signal_type.value} at {code_path} ({severity.value})")
        return signal

    def get_signals_for_path(self, code_path: str, include_related: bool = True) -> List[CanarySignal]:
        """Get all signals for a code path."""
        signals = []

        # Direct signals
        signal_ids = self._path_signals.get(code_path, [])
        signals.extend(self._signals[sid] for sid in signal_ids if sid in self._signals)

        # Related signals (if requested)
        if include_related:
            for signal in self._signals.values():
                if code_path in signal.related_paths and signal not in signals:
                    signals.append(signal)

        return sorted(signals, key=lambda s: s.severity.value, reverse=True)

    def get_all_signals(
        self,
        severity: Optional[SeverityLevel] = None,
        signal_type: Optional[SignalType] = None,
        include_acknowledged: bool = False
    ) -> List[CanarySignal]:
        """Get all signals with optional filtering."""
        signals = list(self._signals.values())

        if severity:
            signals = [s for s in signals if s.severity == severity]

        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]

        if not include_acknowledged:
            signals = [s for s in signals if not s.acknowledged]

        return sorted(signals, key=lambda s: (s.severity.value, -s.occurrences), reverse=True)

    def get_refactoring_candidates(
        self,
        min_priority: int = 1,
        include_completed: bool = False
    ) -> List[RefactoringCandidate]:
        """Get refactoring candidates sorted by priority."""
        candidates = list(self._candidates.values())

        if not include_completed:
            candidates = [c for c in candidates if not c.completed]

        candidates = [c for c in candidates if c.priority >= min_priority]

        return sorted(candidates, key=lambda c: c.priority, reverse=True)

    def acknowledge_signal(self, signal_id: UUID, notes: Optional[str] = None) -> CanarySignal:
        """Acknowledge a signal (mark as reviewed)."""
        signal = self._signals.get(signal_id)
        if not signal:
            raise ValueError(f"Signal {signal_id} not found")

        signal.acknowledged = True
        if notes:
            signal.context["acknowledgment_notes"] = notes

        logger.info(f"Acknowledged canary signal {signal_id}")
        return signal

    def complete_refactoring(self, candidate_id: UUID, success: bool = True) -> RefactoringCandidate:
        """Mark a refactoring candidate as completed."""
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            raise ValueError(f"Refactoring candidate {candidate_id} not found")

        candidate.completed = True

        # Acknowledge related signals
        for signal_id in candidate.signals:
            if signal_id in self._signals:
                self._signals[signal_id].acknowledged = True

        logger.info(f"Completed refactoring candidate {candidate_id} (success: {success})")
        return candidate

    def get_health_report(self, path: str) -> CodeHealthReport:
        """Generate a health report for a code path."""
        signals = self.get_signals_for_path(path)

        severity_breakdown = {level: 0 for level in SeverityLevel}
        for signal in signals:
            severity_breakdown[signal.severity] += 1

        # Calculate health score (100 = perfect, 0 = terrible)
        health_score = 100.0
        health_score -= severity_breakdown[SeverityLevel.CRITICAL] * 25
        health_score -= severity_breakdown[SeverityLevel.HIGH] * 15
        health_score -= severity_breakdown[SeverityLevel.MEDIUM] * 8
        health_score -= severity_breakdown[SeverityLevel.LOW] * 3
        health_score = max(0.0, min(100.0, health_score))

        # Count signal types
        type_counts: Dict[SignalType, int] = {}
        for signal in signals:
            type_counts[signal.signal_type] = type_counts.get(signal.signal_type, 0) + signal.occurrences
        top_issues = sorted(type_counts.keys(), key=lambda t: type_counts[t], reverse=True)[:5]

        # Get recommendations
        recommendations = [
            c for c in self._candidates.values()
            if c.code_path == path and not c.completed
        ]

        # Determine trend (simplified - would need historical data for real trend)
        trend = "stable"
        recent_signals = [s for s in signals if (datetime.now(timezone.utc) - s.last_seen).days < 7]
        if len(recent_signals) > len(signals) * 0.5:
            trend = "degrading"
        elif len(recent_signals) < len(signals) * 0.2:
            trend = "improving"

        return CodeHealthReport(
            path=path,
            signal_count=len(signals),
            severity_breakdown=severity_breakdown,
            top_issues=top_issues,
            health_score=health_score,
            trend=trend,
            recommendations=recommendations,
        )

    def get_hotspots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the code paths with the most quality issues."""
        path_scores: Dict[str, Dict[str, Any]] = {}

        for signal in self._signals.values():
            if signal.code_path not in path_scores:
                path_scores[signal.code_path] = {
                    "path": signal.code_path,
                    "signal_count": 0,
                    "total_occurrences": 0,
                    "critical_count": 0,
                    "high_count": 0,
                    "score": 0,
                }

            ps = path_scores[signal.code_path]
            ps["signal_count"] += 1
            ps["total_occurrences"] += signal.occurrences
            if signal.severity == SeverityLevel.CRITICAL:
                ps["critical_count"] += 1
            elif signal.severity == SeverityLevel.HIGH:
                ps["high_count"] += 1

            # Calculate weighted score
            ps["score"] = (
                ps["critical_count"] * 100 +
                ps["high_count"] * 50 +
                ps["signal_count"] * 10 +
                ps["total_occurrences"] * 5
            )

        hotspots = sorted(path_scores.values(), key=lambda p: p["score"], reverse=True)
        return hotspots[:limit]

    def _find_existing_signal(self, code_path: str, signal_type: SignalType) -> Optional[CanarySignal]:
        """Find existing signal of same type at same path."""
        signal_ids = self._path_signals.get(code_path, [])
        for sid in signal_ids:
            signal = self._signals.get(sid)
            if signal and signal.signal_type == signal_type and not signal.acknowledged:
                return signal
        return None

    def _escalate_severity(self, current: SeverityLevel) -> SeverityLevel:
        """Escalate severity level."""
        escalation = {
            SeverityLevel.LOW: SeverityLevel.MEDIUM,
            SeverityLevel.MEDIUM: SeverityLevel.HIGH,
            SeverityLevel.HIGH: SeverityLevel.CRITICAL,
            SeverityLevel.CRITICAL: SeverityLevel.CRITICAL,
        }
        return escalation[current]

    def _generate_recommendation(self, signal_type: SignalType, code_path: str) -> str:
        """Generate a recommendation based on signal type."""
        recommendations = {
            SignalType.DUPLICATE_LOGIC_MISSED: f"Extract duplicated logic into a shared function/class",
            SignalType.CONTEXT_LIMIT_HIT: f"Consider splitting {code_path} into smaller, focused modules",
            SignalType.FLAWED_TEST_REASONING: f"Simplify the code to make test behavior more predictable",
            SignalType.COMPLEX_CONDITIONAL: f"Refactor complex conditionals using guard clauses or polymorphism",
            SignalType.HIDDEN_COUPLING: f"Make dependencies explicit and consider dependency injection",
            SignalType.INCONSISTENT_NAMING: f"Establish naming conventions and apply them consistently",
            SignalType.UNCLEAR_RESPONSIBILITY: f"Apply Single Responsibility Principle - split the class/function",
            SignalType.MISSING_ABSTRACTION: f"Introduce an abstraction to reduce complexity",
            SignalType.CIRCULAR_DEPENDENCY: f"Break circular dependency by introducing an interface or event",
            SignalType.MAGIC_VALUES: f"Replace magic values with named constants",
        }
        return recommendations.get(signal_type, "Review and refactor the problematic code")

    def _create_refactoring_candidate(self, signal: CanarySignal) -> RefactoringCandidate:
        """Create a refactoring candidate from a signal."""
        refactoring_type = self.SIGNAL_REFACTORINGS.get(
            signal.signal_type,
            RefactoringType.EXTRACT_METHOD
        )

        # Calculate priority (1-10)
        priority = 5
        if signal.severity == SeverityLevel.CRITICAL:
            priority = 10
        elif signal.severity == SeverityLevel.HIGH:
            priority = 8
        priority = min(10, priority + (signal.occurrences - 1))

        # Estimate effort
        effort = "medium"
        if refactoring_type in (RefactoringType.RENAME, RefactoringType.INTRODUCE_CONSTANT):
            effort = "small"
        elif refactoring_type in (RefactoringType.EXTRACT_CLASS, RefactoringType.BREAK_DEPENDENCY):
            effort = "large"

        candidate = RefactoringCandidate(
            id=uuid4(),
            code_path=signal.code_path,
            refactoring_type=refactoring_type,
            priority=priority,
            effort_estimate=effort,
            signals=[signal.id],
            description=f"{refactoring_type.value} to address {signal.signal_type.value}",
            suggested_approach=signal.recommendation,
            created_at=datetime.now(timezone.utc),
        )

        self._candidates[candidate.id] = candidate
        return candidate
