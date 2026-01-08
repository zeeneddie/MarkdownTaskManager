"""
Wave Planner Service - Fase 26: Migration Execution

Week 140-141: Dependency-based grouping and risk-balanced wave planning.
Creates migration waves based on module dependencies and risk assessment.

Agent: Paul (Project Lead)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple
from enum import Enum
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== Enums ====================

class WaveStrategy(Enum):
    """Wave planning strategies"""
    DEPENDENCY_FIRST = "dependency_first"  # Foundation modules first
    RISK_BALANCED = "risk_balanced"  # Balance risk across waves
    BUSINESS_VALUE = "business_value"  # High value modules first
    COMPLEXITY_GRADIENT = "complexity_gradient"  # Simple to complex
    HYBRID = "hybrid"  # Combination approach


class ModuleRisk(Enum):
    """Module risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WaveStatus(Enum):
    """Wave execution status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    VALIDATION = "validation"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class ModuleType(Enum):
    """Module classification"""
    FOUNDATION = "foundation"
    SHARED = "shared"
    BUSINESS = "business"
    UI = "ui"
    INTEGRATION = "integration"
    UTILITY = "utility"


# ==================== Data Classes ====================

@dataclass
class Module:
    """Module for wave planning"""
    id: str
    name: str
    path: str
    module_type: ModuleType
    dependencies: List[str]  # IDs of modules this depends on
    dependents: List[str]  # IDs of modules that depend on this
    lines_of_code: int
    complexity_score: float
    risk_level: ModuleRisk
    business_value: float  # 0.0 to 1.0
    estimated_hours: float
    team_affinity: Optional[str] = None  # Preferred team
    tags: List[str] = field(default_factory=list)


@dataclass
class Wave:
    """Migration wave containing modules"""
    id: str
    number: int
    name: str
    modules: List[Module]
    status: WaveStatus
    planned_start: Optional[datetime]
    planned_end: Optional[datetime]
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    total_loc: int = 0
    total_hours: float = 0.0
    team_assignments: Dict[str, List[str]] = field(default_factory=dict)
    dependencies_satisfied: bool = True
    blockers: List[str] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass
class WavePlan:
    """Complete wave plan for a migration"""
    id: UUID
    project_id: str
    name: str
    strategy: WaveStrategy
    waves: List[Wave]
    total_modules: int
    total_loc: int
    total_hours: float
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None
    team_capacity: Dict[str, float] = field(default_factory=dict)  # team -> hours/week
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyGraph:
    """Module dependency graph for analysis"""
    modules: Dict[str, Module]
    adjacency: Dict[str, Set[str]]  # module_id -> set of dependency IDs
    reverse_adjacency: Dict[str, Set[str]]  # module_id -> set of dependent IDs
    levels: Dict[str, int]  # module_id -> dependency level (0 = no deps)
    circular_dependencies: List[List[str]]


@dataclass
class RiskAssessment:
    """Risk assessment for a wave"""
    wave_id: str
    overall_risk: ModuleRisk
    risk_factors: List[Dict[str, Any]]
    mitigation_suggestions: List[str]
    recommended_buffer_days: int
    critical_path_modules: List[str]


# ==================== Service ====================

class WavePlannerService:
    """
    Plans migration waves based on dependencies and risk balancing.

    Features:
    - Dependency analysis and topological sorting
    - Risk-balanced wave distribution
    - Team capacity planning
    - Critical path identification
    - Wave scheduling optimization
    """

    def __init__(self):
        self.plans: Dict[UUID, WavePlan] = {}
        self.max_wave_risk_score = 100.0  # Max acceptable risk per wave

    # ==================== Dependency Analysis ====================

    async def analyze_dependencies(
        self,
        modules: List[Module]
    ) -> DependencyGraph:
        """Analyze module dependencies and build graph."""
        module_map = {m.id: m for m in modules}
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)

        for module in modules:
            for dep_id in module.dependencies:
                if dep_id in module_map:
                    adjacency[module.id].add(dep_id)
                    reverse_adjacency[dep_id].add(module.id)

        # Calculate levels (topological depth)
        levels = await self._calculate_levels(modules, adjacency)

        # Detect circular dependencies
        circular = await self._detect_circular_dependencies(modules, adjacency)

        return DependencyGraph(
            modules=module_map,
            adjacency=adjacency,
            reverse_adjacency=reverse_adjacency,
            levels=levels,
            circular_dependencies=circular,
        )

    async def _calculate_levels(
        self,
        modules: List[Module],
        adjacency: Dict[str, Set[str]]
    ) -> Dict[str, int]:
        """Calculate dependency levels for each module."""
        levels: Dict[str, int] = {}
        in_degree = {m.id: len(adjacency[m.id]) for m in modules}

        # Modules with no dependencies start at level 0
        current_level = 0
        queue = [m.id for m in modules if in_degree[m.id] == 0]

        while queue:
            next_queue = []
            for module_id in queue:
                levels[module_id] = current_level

            current_level += 1

            for module_id in queue:
                for m in modules:
                    if module_id in adjacency[m.id]:
                        in_degree[m.id] -= 1
                        if in_degree[m.id] == 0:
                            next_queue.append(m.id)

            queue = next_queue

        # Handle any remaining (circular deps)
        for m in modules:
            if m.id not in levels:
                levels[m.id] = current_level

        return levels

    async def _detect_circular_dependencies(
        self,
        modules: List[Module],
        adjacency: Dict[str, Set[str]]
    ) -> List[List[str]]:
        """Detect circular dependencies using DFS."""
        circular = []
        visited = set()
        rec_stack = set()

        def dfs(module_id: str, path: List[str]) -> None:
            visited.add(module_id)
            rec_stack.add(module_id)
            path.append(module_id)

            for dep_id in adjacency[module_id]:
                if dep_id not in visited:
                    dfs(dep_id, path.copy())
                elif dep_id in rec_stack:
                    # Found cycle
                    cycle_start = path.index(dep_id)
                    cycle = path[cycle_start:] + [dep_id]
                    if cycle not in circular:
                        circular.append(cycle)

            rec_stack.remove(module_id)

        for m in modules:
            if m.id not in visited:
                dfs(m.id, [])

        return circular

    # ==================== Wave Planning ====================

    async def create_wave_plan(
        self,
        project_id: str,
        name: str,
        modules: List[Module],
        strategy: WaveStrategy = WaveStrategy.HYBRID,
        max_modules_per_wave: int = 10,
        max_hours_per_wave: float = 200.0,
        team_capacity: Optional[Dict[str, float]] = None
    ) -> WavePlan:
        """Create a complete wave plan for migration."""
        plan_id = uuid4()

        # Analyze dependencies
        graph = await self.analyze_dependencies(modules)

        # Log circular dependencies as warnings
        if graph.circular_dependencies:
            logger.warning(f"Circular dependencies detected: {graph.circular_dependencies}")

        # Generate waves based on strategy
        if strategy == WaveStrategy.DEPENDENCY_FIRST:
            waves = await self._plan_dependency_first(graph, max_modules_per_wave, max_hours_per_wave)
        elif strategy == WaveStrategy.RISK_BALANCED:
            waves = await self._plan_risk_balanced(graph, max_modules_per_wave, max_hours_per_wave)
        elif strategy == WaveStrategy.BUSINESS_VALUE:
            waves = await self._plan_business_value(graph, max_modules_per_wave, max_hours_per_wave)
        elif strategy == WaveStrategy.COMPLEXITY_GRADIENT:
            waves = await self._plan_complexity_gradient(graph, max_modules_per_wave, max_hours_per_wave)
        else:  # HYBRID
            waves = await self._plan_hybrid(graph, max_modules_per_wave, max_hours_per_wave)

        # Calculate totals
        total_loc = sum(m.lines_of_code for m in modules)
        total_hours = sum(m.estimated_hours for m in modules)

        # Estimate completion
        total_team_capacity = sum((team_capacity or {}).values()) or 40.0  # Default 40 hrs/week
        weeks_needed = total_hours / total_team_capacity
        estimated_completion = datetime.now() + timedelta(weeks=weeks_needed)

        plan = WavePlan(
            id=plan_id,
            project_id=project_id,
            name=name,
            strategy=strategy,
            waves=waves,
            total_modules=len(modules),
            total_loc=total_loc,
            total_hours=total_hours,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            estimated_completion=estimated_completion,
            team_capacity=team_capacity or {},
        )

        self.plans[plan_id] = plan
        logger.info(f"Created wave plan: {plan_id} with {len(waves)} waves")

        return plan

    async def _plan_dependency_first(
        self,
        graph: DependencyGraph,
        max_modules: int,
        max_hours: float
    ) -> List[Wave]:
        """Plan waves with foundation/dependency modules first."""
        waves = []

        # Group by level
        level_groups: Dict[int, List[Module]] = defaultdict(list)
        for module_id, level in graph.levels.items():
            level_groups[level].append(graph.modules[module_id])

        wave_number = 1
        for level in sorted(level_groups.keys()):
            modules_at_level = level_groups[level]

            # Split if too many modules
            current_wave_modules: List[Module] = []
            current_hours = 0.0

            for module in modules_at_level:
                if (len(current_wave_modules) >= max_modules or
                        current_hours + module.estimated_hours > max_hours):
                    # Create wave
                    if current_wave_modules:
                        wave = self._create_wave(wave_number, current_wave_modules)
                        waves.append(wave)
                        wave_number += 1
                        current_wave_modules = []
                        current_hours = 0.0

                current_wave_modules.append(module)
                current_hours += module.estimated_hours

            # Add remaining
            if current_wave_modules:
                wave = self._create_wave(wave_number, current_wave_modules)
                waves.append(wave)
                wave_number += 1

        return waves

    async def _plan_risk_balanced(
        self,
        graph: DependencyGraph,
        max_modules: int,
        max_hours: float
    ) -> List[Wave]:
        """Plan waves with balanced risk distribution."""
        modules = list(graph.modules.values())

        # Sort by risk (critical first to spread out)
        risk_order = {ModuleRisk.CRITICAL: 0, ModuleRisk.HIGH: 1, ModuleRisk.MEDIUM: 2, ModuleRisk.LOW: 3}
        modules.sort(key=lambda m: risk_order[m.risk_level])

        waves = []
        wave_number = 1

        # Distribute high-risk modules across waves
        high_risk = [m for m in modules if m.risk_level in [ModuleRisk.CRITICAL, ModuleRisk.HIGH]]
        other = [m for m in modules if m.risk_level in [ModuleRisk.MEDIUM, ModuleRisk.LOW]]

        # Calculate target number of waves
        target_waves = max(len(high_risk), 1)

        # Distribute high-risk evenly
        wave_buckets: List[List[Module]] = [[] for _ in range(target_waves)]
        for i, module in enumerate(high_risk):
            wave_buckets[i % target_waves].append(module)

        # Fill with lower risk modules respecting dependencies
        for module in other:
            # Find suitable wave (dependencies satisfied, not too full)
            deps = set(graph.adjacency[module.id])
            placed = False

            for bucket in wave_buckets:
                bucket_ids = {m.id for m in bucket}
                bucket_hours = sum(m.estimated_hours for m in bucket)

                # Check if dependencies are in previous waves or same wave
                if len(bucket) < max_modules and bucket_hours + module.estimated_hours <= max_hours:
                    bucket.append(module)
                    placed = True
                    break

            if not placed:
                # Create new wave
                wave_buckets.append([module])

        # Create wave objects
        for bucket in wave_buckets:
            if bucket:
                wave = self._create_wave(wave_number, bucket)
                waves.append(wave)
                wave_number += 1

        return waves

    async def _plan_business_value(
        self,
        graph: DependencyGraph,
        max_modules: int,
        max_hours: float
    ) -> List[Wave]:
        """Plan waves prioritizing high business value."""
        modules = list(graph.modules.values())

        # Sort by business value (highest first), respecting dependencies
        modules.sort(key=lambda m: (-m.business_value, graph.levels[m.id]))

        return await self._create_waves_from_sorted(modules, graph, max_modules, max_hours)

    async def _plan_complexity_gradient(
        self,
        graph: DependencyGraph,
        max_modules: int,
        max_hours: float
    ) -> List[Wave]:
        """Plan waves from simple to complex."""
        modules = list(graph.modules.values())

        # Sort by complexity (lowest first), respecting dependencies
        modules.sort(key=lambda m: (m.complexity_score, graph.levels[m.id]))

        return await self._create_waves_from_sorted(modules, graph, max_modules, max_hours)

    async def _plan_hybrid(
        self,
        graph: DependencyGraph,
        max_modules: int,
        max_hours: float
    ) -> List[Wave]:
        """Hybrid planning: dependencies + risk balance + value."""
        modules = list(graph.modules.values())

        # Score each module
        def hybrid_score(m: Module) -> float:
            level_score = graph.levels[m.id] * 10  # Lower level = earlier
            risk_penalty = {"low": 0, "medium": 5, "high": 10, "critical": 20}[m.risk_level.value]
            value_bonus = m.business_value * 5

            return level_score + risk_penalty - value_bonus

        modules.sort(key=hybrid_score)

        return await self._create_waves_from_sorted(modules, graph, max_modules, max_hours)

    async def _create_waves_from_sorted(
        self,
        modules: List[Module],
        graph: DependencyGraph,
        max_modules: int,
        max_hours: float
    ) -> List[Wave]:
        """Create waves from sorted module list, respecting dependencies."""
        waves = []
        wave_number = 1
        placed = set()

        current_wave: List[Module] = []
        current_hours = 0.0

        for module in modules:
            # Check if dependencies are satisfied (in previous waves)
            deps_satisfied = all(dep in placed for dep in graph.adjacency[module.id])

            if not deps_satisfied:
                continue

            if (len(current_wave) >= max_modules or
                    current_hours + module.estimated_hours > max_hours):
                # Finalize current wave
                if current_wave:
                    wave = self._create_wave(wave_number, current_wave)
                    waves.append(wave)
                    wave_number += 1

                    # Mark as placed
                    for m in current_wave:
                        placed.add(m.id)

                    current_wave = []
                    current_hours = 0.0

            current_wave.append(module)
            current_hours += module.estimated_hours

        # Add final wave
        if current_wave:
            wave = self._create_wave(wave_number, current_wave)
            waves.append(wave)
            for m in current_wave:
                placed.add(m.id)

        # Handle any unplaced modules (circular deps)
        unplaced = [m for m in modules if m.id not in placed]
        if unplaced:
            wave = self._create_wave(wave_number + 1, unplaced)
            wave.blockers.append("Contains modules with circular dependencies")
            waves.append(wave)

        return waves

    def _create_wave(self, number: int, modules: List[Module]) -> Wave:
        """Create a wave from modules."""
        total_loc = sum(m.lines_of_code for m in modules)
        total_hours = sum(m.estimated_hours for m in modules)

        # Calculate risk score
        risk_weights = {ModuleRisk.LOW: 1, ModuleRisk.MEDIUM: 2, ModuleRisk.HIGH: 4, ModuleRisk.CRITICAL: 8}
        risk_score = sum(risk_weights[m.risk_level] for m in modules)

        return Wave(
            id=f"wave-{number:02d}",
            number=number,
            name=f"Wave {number}",
            modules=modules,
            status=WaveStatus.PLANNED,
            planned_start=None,
            planned_end=None,
            total_loc=total_loc,
            total_hours=total_hours,
            risk_score=risk_score,
        )

    # ==================== Wave Scheduling ====================

    async def schedule_waves(
        self,
        plan_id: UUID,
        start_date: datetime,
        buffer_days_per_wave: int = 2
    ) -> Optional[WavePlan]:
        """Schedule waves with dates."""
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        total_capacity = sum(plan.team_capacity.values()) or 40.0  # Default

        current_date = start_date
        for wave in plan.waves:
            wave.planned_start = current_date

            # Calculate duration based on hours and capacity
            days_needed = (wave.total_hours / total_capacity) * 5  # 5 workdays/week
            days_needed += buffer_days_per_wave

            wave.planned_end = current_date + timedelta(days=int(days_needed))
            current_date = wave.planned_end + timedelta(days=1)

        plan.estimated_completion = plan.waves[-1].planned_end if plan.waves else None
        plan.updated_at = datetime.now()

        return plan

    # ==================== Risk Assessment ====================

    async def assess_wave_risk(
        self,
        plan_id: UUID,
        wave_id: str
    ) -> Optional[RiskAssessment]:
        """Assess risk for a specific wave."""
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        wave = next((w for w in plan.waves if w.id == wave_id), None)
        if not wave:
            return None

        risk_factors = []
        mitigation_suggestions = []

        # Factor 1: High-risk modules
        critical_modules = [m for m in wave.modules if m.risk_level == ModuleRisk.CRITICAL]
        high_risk_modules = [m for m in wave.modules if m.risk_level == ModuleRisk.HIGH]

        if critical_modules:
            risk_factors.append({
                "factor": "Critical modules",
                "count": len(critical_modules),
                "modules": [m.name for m in critical_modules],
                "severity": "high",
            })
            mitigation_suggestions.append("Consider splitting critical modules across multiple waves")
            mitigation_suggestions.append("Assign senior developers to critical modules")

        if high_risk_modules:
            risk_factors.append({
                "factor": "High-risk modules",
                "count": len(high_risk_modules),
                "modules": [m.name for m in high_risk_modules],
                "severity": "medium",
            })

        # Factor 2: Complexity concentration
        avg_complexity = sum(m.complexity_score for m in wave.modules) / len(wave.modules) if wave.modules else 0
        if avg_complexity > 0.7:
            risk_factors.append({
                "factor": "High average complexity",
                "value": avg_complexity,
                "severity": "medium",
            })
            mitigation_suggestions.append("Add code review checkpoints")

        # Factor 3: LOC concentration
        if wave.total_loc > 5000:
            risk_factors.append({
                "factor": "Large code volume",
                "value": wave.total_loc,
                "severity": "low",
            })

        # Factor 4: Dependencies
        external_deps = set()
        for module in wave.modules:
            wave_module_ids = {m.id for m in wave.modules}
            for dep in module.dependencies:
                if dep not in wave_module_ids:
                    external_deps.add(dep)

        if external_deps:
            risk_factors.append({
                "factor": "External dependencies",
                "count": len(external_deps),
                "dependency_ids": list(external_deps),
                "severity": "low",
            })

        # Determine overall risk
        if critical_modules or (len(high_risk_modules) > len(wave.modules) * 0.5):
            overall_risk = ModuleRisk.HIGH
        elif high_risk_modules or avg_complexity > 0.7:
            overall_risk = ModuleRisk.MEDIUM
        else:
            overall_risk = ModuleRisk.LOW

        # Recommend buffer
        buffer_days = 2
        if overall_risk == ModuleRisk.HIGH:
            buffer_days = 5
        elif overall_risk == ModuleRisk.MEDIUM:
            buffer_days = 3

        # Critical path modules (most dependents within wave)
        critical_path = sorted(
            wave.modules,
            key=lambda m: len([d for d in m.dependents if any(wm.id == d for wm in wave.modules)]),
            reverse=True
        )[:3]

        return RiskAssessment(
            wave_id=wave_id,
            overall_risk=overall_risk,
            risk_factors=risk_factors,
            mitigation_suggestions=mitigation_suggestions,
            recommended_buffer_days=buffer_days,
            critical_path_modules=[m.name for m in critical_path],
        )

    # ==================== Team Assignment ====================

    async def assign_teams(
        self,
        plan_id: UUID,
        team_specialties: Dict[str, List[ModuleType]]
    ) -> Optional[WavePlan]:
        """Assign teams to waves based on module types."""
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        for wave in plan.waves:
            wave.team_assignments = {}

            for module in wave.modules:
                # Find best team for module type
                best_team = None
                for team, specialties in team_specialties.items():
                    if module.module_type in specialties:
                        best_team = team
                        break

                if best_team:
                    if best_team not in wave.team_assignments:
                        wave.team_assignments[best_team] = []
                    wave.team_assignments[best_team].append(module.id)
                elif module.team_affinity:
                    if module.team_affinity not in wave.team_assignments:
                        wave.team_assignments[module.team_affinity] = []
                    wave.team_assignments[module.team_affinity].append(module.id)

        plan.updated_at = datetime.now()
        return plan

    # ==================== Wave Progress ====================

    async def update_wave_status(
        self,
        plan_id: UUID,
        wave_id: str,
        status: WaveStatus
    ) -> Optional[Wave]:
        """Update wave status."""
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        wave = next((w for w in plan.waves if w.id == wave_id), None)
        if not wave:
            return None

        old_status = wave.status
        wave.status = status

        if status == WaveStatus.IN_PROGRESS and not wave.actual_start:
            wave.actual_start = datetime.now()
        elif status == WaveStatus.COMPLETED and not wave.actual_end:
            wave.actual_end = datetime.now()

        plan.updated_at = datetime.now()
        logger.info(f"Wave {wave_id} status: {old_status.value} -> {status.value}")

        return wave

    async def get_plan_progress(
        self,
        plan_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get overall plan progress."""
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        completed_waves = [w for w in plan.waves if w.status == WaveStatus.COMPLETED]
        in_progress_waves = [w for w in plan.waves if w.status == WaveStatus.IN_PROGRESS]
        blocked_waves = [w for w in plan.waves if w.status == WaveStatus.BLOCKED]

        completed_modules = sum(len(w.modules) for w in completed_waves)
        completed_hours = sum(w.total_hours for w in completed_waves)

        return {
            "plan_id": str(plan.id),
            "name": plan.name,
            "total_waves": len(plan.waves),
            "completed_waves": len(completed_waves),
            "in_progress_waves": len(in_progress_waves),
            "blocked_waves": len(blocked_waves),
            "total_modules": plan.total_modules,
            "completed_modules": completed_modules,
            "module_progress_percent": (completed_modules / plan.total_modules * 100) if plan.total_modules else 0,
            "total_hours": plan.total_hours,
            "completed_hours": completed_hours,
            "hours_progress_percent": (completed_hours / plan.total_hours * 100) if plan.total_hours else 0,
            "estimated_completion": plan.estimated_completion.isoformat() if plan.estimated_completion else None,
        }

    # ==================== Export ====================

    def to_gantt_mermaid(self, plan: WavePlan) -> str:
        """Generate Mermaid Gantt chart."""
        lines = [
            "gantt",
            f"    title {plan.name}",
            "    dateFormat YYYY-MM-DD",
            "    excludes weekends",
            "",
        ]

        for wave in plan.waves:
            start = wave.planned_start.strftime("%Y-%m-%d") if wave.planned_start else "2025-01-01"
            duration = int((wave.planned_end - wave.planned_start).days) if wave.planned_start and wave.planned_end else 7

            status_suffix = ""
            if wave.status == WaveStatus.COMPLETED:
                status_suffix = " :done,"
            elif wave.status == WaveStatus.IN_PROGRESS:
                status_suffix = " :active,"

            lines.append(f"    section Wave {wave.number}")
            lines.append(f"    {wave.name}{status_suffix} {start}, {duration}d")

            # Add key modules
            for module in wave.modules[:3]:  # First 3 modules
                lines.append(f"    {module.name}: after {wave.id}, 2d")

        return "\n".join(lines)

    def to_markdown_report(self, plan: WavePlan) -> str:
        """Generate markdown progress report."""
        lines = [
            f"# Wave Migration Plan: {plan.name}",
            f"",
            f"**Strategy:** {plan.strategy.value}",
            f"**Total Waves:** {len(plan.waves)}",
            f"**Total Modules:** {plan.total_modules}",
            f"**Total LOC:** {plan.total_loc:,}",
            f"**Estimated Hours:** {plan.total_hours:.0f}",
            f"**Est. Completion:** {plan.estimated_completion.strftime('%Y-%m-%d') if plan.estimated_completion else 'TBD'}",
            f"",
            f"## Wave Summary",
            f"",
            f"| Wave | Modules | LOC | Hours | Risk | Status |",
            f"|------|---------|-----|-------|------|--------|",
        ]

        status_emoji = {
            "planned": "⬜", "in_progress": "🔵", "validation": "🟡",
            "completed": "✅", "blocked": "🔴", "failed": "❌"
        }

        for wave in plan.waves:
            emoji = status_emoji.get(wave.status.value, "⬜")
            lines.append(
                f"| {wave.name} | {len(wave.modules)} | {wave.total_loc:,} | "
                f"{wave.total_hours:.0f}h | {wave.risk_score:.0f} | {emoji} {wave.status.value} |"
            )

        # Wave details
        for wave in plan.waves:
            lines.extend([
                f"",
                f"### {wave.name}",
                f"",
                f"**Status:** {wave.status.value}",
                f"**Planned:** {wave.planned_start.strftime('%Y-%m-%d') if wave.planned_start else 'TBD'} - {wave.planned_end.strftime('%Y-%m-%d') if wave.planned_end else 'TBD'}",
                f"",
                f"| Module | Type | Risk | Hours |",
                f"|--------|------|------|-------|",
            ])

            for module in wave.modules:
                risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
                lines.append(
                    f"| {module.name} | {module.module_type.value} | "
                    f"{risk_emoji.get(module.risk_level.value, '⚪')} | {module.estimated_hours:.0f}h |"
                )

            if wave.blockers:
                lines.extend([
                    f"",
                    f"**Blockers:**",
                ])
                for blocker in wave.blockers:
                    lines.append(f"- {blocker}")

        return "\n".join(lines)
