"""
ImprovementPlannerService - Convert SWOT Weaknesses to Improvement Backlog

Week 77: Creates prioritized, actionable improvement items from analysis.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class ImprovementCategory(Enum):
    """Categories for improvements."""
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    DATABASE = "database"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"


class ImprovementType(Enum):
    """Types of improvements."""
    QUICK_WIN = "quick_win"  # Low effort, high impact
    STRATEGIC = "strategic"  # High effort, high impact
    TECHNICAL_DEBT = "technical_debt"  # Medium effort, medium impact
    SECURITY_FIX = "security_fix"  # Any security improvement
    MODERNIZATION = "modernization"  # Architecture changes
    OPTIMIZATION = "optimization"  # Performance improvements


class ImpactLevel(Enum):
    """Impact levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ImprovementItem:
    """Single improvement item in the backlog."""
    id: str
    title: str
    description: str
    category: ImprovementCategory
    item_type: ImprovementType

    # Source
    source_weakness: str
    affected_files: List[str] = field(default_factory=list)
    affected_sps: List[str] = field(default_factory=list)

    # Prioritization
    priority: int = 3  # 1-5, 1 is highest
    business_impact: ImpactLevel = ImpactLevel.MEDIUM
    effort_days: float = 5.0
    risk_if_not_done: ImpactLevel = ImpactLevel.MEDIUM

    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)

    # Implementation
    implementation_notes: str = ""
    code_examples: List[Dict[str, str]] = field(default_factory=list)
    references: List[str] = field(default_factory=list)

    # Tracking
    status: str = "identified"  # identified, planned, in_progress, completed, deferred

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "item_type": self.item_type.value,
            "source_weakness": self.source_weakness,
            "affected_files": self.affected_files,
            "affected_sps": self.affected_sps,
            "priority": self.priority,
            "business_impact": self.business_impact.value,
            "effort_days": self.effort_days,
            "risk_if_not_done": self.risk_if_not_done.value,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "implementation_notes": self.implementation_notes,
            "code_examples": self.code_examples,
            "references": self.references,
            "status": self.status,
        }


@dataclass
class PlanningConstraints:
    """Constraints for improvement planning."""
    max_effort_days: Optional[float] = None
    max_items: Optional[int] = None
    focus_categories: List[ImprovementCategory] = field(default_factory=list)
    exclude_types: List[ImprovementType] = field(default_factory=list)
    team_size: int = 1


@dataclass
class ImprovementPlan:
    """Complete improvement plan."""
    items: List[ImprovementItem] = field(default_factory=list)
    quick_wins: List[ImprovementItem] = field(default_factory=list)
    strategic_items: List[ImprovementItem] = field(default_factory=list)
    technical_debt: List[ImprovementItem] = field(default_factory=list)

    # Summary
    total_effort_days: float = 0
    by_category: Dict[str, List[ImprovementItem]] = field(default_factory=dict)
    by_priority: Dict[int, List[ImprovementItem]] = field(default_factory=dict)

    # Phasing recommendation
    phases: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "quick_wins": [item.to_dict() for item in self.quick_wins],
            "strategic_items": [item.to_dict() for item in self.strategic_items],
            "technical_debt": [item.to_dict() for item in self.technical_debt],
            "summary": {
                "total_items": len(self.items),
                "total_effort_days": self.total_effort_days,
                "quick_wins_count": len(self.quick_wins),
                "strategic_count": len(self.strategic_items),
            },
            "by_category": {
                cat: [item.to_dict() for item in items]
                for cat, items in self.by_category.items()
            },
            "by_priority": {
                str(pri): [item.to_dict() for item in items]
                for pri, items in self.by_priority.items()
            },
            "phases": self.phases,
        }


class ImprovementPlannerService:
    """
    Convert SWOT weaknesses to prioritized improvement backlog.
    """

    # Implementation templates for common improvements
    IMPLEMENTATION_TEMPLATES = {
        "SQL_INJECTION": {
            "notes": "Replace string concatenation with parameterized queries",
            "examples": [
                {
                    "before": "sql = \"SELECT * FROM users WHERE id = \" & userId",
                    "after": "cmd.Parameters.Add(\"@userId\", SqlDbType.Int).Value = userId",
                },
            ],
            "references": [
                "https://owasp.org/www-community/attacks/SQL_Injection",
                "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
            ],
        },
        "XSS": {
            "notes": "Encode all user input before output",
            "examples": [
                {
                    "before": "Response.Write(Request.Form(\"name\"))",
                    "after": "Response.Write(Server.HTMLEncode(Request.Form(\"name\")))",
                },
            ],
            "references": [
                "https://owasp.org/www-community/attacks/xss/",
            ],
        },
        "LEGACY_TECH": {
            "notes": "Plan migration to modern framework in phases",
            "examples": [],
            "references": [
                "https://docs.microsoft.com/en-us/aspnet/core/migration/proper-to-2x/",
            ],
        },
        "HIGH_COMPLEXITY": {
            "notes": "Refactor complex procedures into smaller, focused units",
            "examples": [
                {
                    "pattern": "Extract method for each logical block",
                    "benefit": "Improved testability and maintainability",
                },
            ],
            "references": [
                "https://refactoring.guru/refactoring/techniques",
            ],
        },
        "ERROR_HANDLING": {
            "notes": "Implement proper error handling with logging",
            "examples": [
                {
                    "before": "On Error Resume Next",
                    "after": "On Error Resume Next\n' ... risky code ...\nIf Err.Number <> 0 Then\n    ' Log error\n    ' Handle appropriately\n    Err.Clear\nEnd If",
                },
            ],
            "references": [],
        },
        "VENDOR_SPECIFIC": {
            "notes": "Replace vendor-specific SQL with portable alternatives",
            "examples": [
                {
                    "sql_server": "ISNULL(column, 'default')",
                    "portable": "COALESCE(column, 'default')",
                },
                {
                    "sql_server": "TOP 10",
                    "portable": "FETCH FIRST 10 ROWS ONLY",
                },
            ],
            "references": [],
        },
        "PERFORMANCE": {
            "notes": "Optimize queries and consider caching",
            "examples": [
                {
                    "issue": "SELECT * FROM large_table",
                    "fix": "SELECT only_needed_columns FROM large_table WHERE condition",
                },
            ],
            "references": [],
        },
    }

    def __init__(self):
        self.plan = ImprovementPlan()

    async def create_improvement_plan(
        self,
        swot_matrix: Dict[str, Any],
        constraints: Optional[PlanningConstraints] = None
    ) -> ImprovementPlan:
        """
        Create improvement plan from SWOT matrix.

        Args:
            swot_matrix: SWOT analysis results
            constraints: Optional planning constraints

        Returns:
            ImprovementPlan with prioritized items
        """
        self.plan = ImprovementPlan()
        constraints = constraints or PlanningConstraints()

        # Extract weaknesses
        weaknesses = swot_matrix.get("matrix", {}).get("weaknesses", [])
        prioritized = swot_matrix.get("prioritization", {}).get("prioritized_weaknesses", [])

        # Create improvement items from prioritized weaknesses
        for pw in prioritized:
            weakness = pw.get("weakness", {})
            item = self._create_improvement_item(weakness, pw)

            # Apply constraints
            if constraints.focus_categories:
                if item.category not in constraints.focus_categories:
                    continue

            if constraints.exclude_types:
                if item.item_type in constraints.exclude_types:
                    continue

            self.plan.items.append(item)

        # If no prioritized weaknesses, create from raw weaknesses
        if not self.plan.items:
            for weakness in weaknesses:
                item = self._create_improvement_item(weakness)
                self.plan.items.append(item)

        # Categorize items
        self._categorize_items()

        # Build dependency graph
        self._build_dependencies()

        # Apply max constraints
        if constraints.max_items:
            self.plan.items = self.plan.items[:constraints.max_items]

        if constraints.max_effort_days:
            self._filter_by_effort(constraints.max_effort_days)

        # Calculate totals
        self.plan.total_effort_days = sum(item.effort_days for item in self.plan.items)

        # Create phases
        self._create_phases(constraints.team_size)

        return self.plan

    def _create_improvement_item(
        self,
        weakness: Dict[str, Any],
        prioritized: Optional[Dict[str, Any]] = None
    ) -> ImprovementItem:
        """Create improvement item from weakness."""
        title = weakness.get("title", "Unknown Improvement")
        category_str = weakness.get("category", "maintainability")
        impact_str = weakness.get("impact", "medium")

        # Map to enums
        try:
            category = ImprovementCategory(category_str)
        except ValueError:
            category = ImprovementCategory.MAINTAINABILITY

        try:
            impact = ImpactLevel(impact_str)
        except ValueError:
            impact = ImpactLevel.MEDIUM

        # Determine item type
        item_type = self._determine_item_type(title, category, prioritized)

        # Get effort and priority from prioritized data
        if prioritized:
            effort = prioritized.get("effort_days", 5)
            priority = prioritized.get("priority", 3)
            risk = ImpactLevel(prioritized.get("risk_if_not_done", "medium"))
        else:
            effort = self._estimate_effort(category, impact)
            priority = self._calculate_priority(impact, effort)
            risk = impact

        # Get implementation template
        template_key = self._get_template_key(title)
        template = self.IMPLEMENTATION_TEMPLATES.get(template_key, {})

        return ImprovementItem(
            id=str(uuid4()),
            title=f"Fix: {title}",
            description=self._generate_description(weakness),
            category=category,
            item_type=item_type,
            source_weakness=title,
            affected_files=weakness.get("affected_components", []),
            affected_sps=[],  # Will be populated for DB issues
            priority=priority,
            business_impact=impact,
            effort_days=effort,
            risk_if_not_done=risk,
            implementation_notes=template.get("notes", ""),
            code_examples=template.get("examples", []),
            references=template.get("references", []),
        )

    def _determine_item_type(
        self,
        title: str,
        category: ImprovementCategory,
        prioritized: Optional[Dict[str, Any]]
    ) -> ImprovementType:
        """Determine the type of improvement."""
        title_lower = title.lower()

        # Security fixes
        if category == ImprovementCategory.SECURITY:
            return ImprovementType.SECURITY_FIX

        # Quick wins
        if prioritized and prioritized.get("quick_win", False):
            return ImprovementType.QUICK_WIN

        # Modernization
        if "legacy" in title_lower or "obsolete" in title_lower or "moderniz" in title_lower:
            return ImprovementType.MODERNIZATION

        # Performance
        if category == ImprovementCategory.PERFORMANCE:
            return ImprovementType.OPTIMIZATION

        # High priority = strategic
        if prioritized and prioritized.get("priority", 5) <= 2:
            return ImprovementType.STRATEGIC

        # Default to technical debt
        return ImprovementType.TECHNICAL_DEBT

    def _get_template_key(self, title: str) -> str:
        """Get template key from weakness title."""
        title_lower = title.lower()

        if "sql injection" in title_lower:
            return "SQL_INJECTION"
        elif "xss" in title_lower:
            return "XSS"
        elif "legacy" in title_lower:
            return "LEGACY_TECH"
        elif "complexity" in title_lower:
            return "HIGH_COMPLEXITY"
        elif "error" in title_lower:
            return "ERROR_HANDLING"
        elif "vendor" in title_lower:
            return "VENDOR_SPECIFIC"
        elif "performance" in title_lower:
            return "PERFORMANCE"

        return ""

    def _generate_description(self, weakness: Dict[str, Any]) -> str:
        """Generate improvement description."""
        title = weakness.get("title", "")
        description = weakness.get("description", "")
        evidence = weakness.get("evidence", [])

        parts = [description]

        if evidence:
            parts.append("\n\nEvidence:")
            for e in evidence[:3]:
                parts.append(f"- {e}")

        return "\n".join(parts)

    def _estimate_effort(self, category: ImprovementCategory, impact: ImpactLevel) -> float:
        """Estimate effort in days."""
        base_effort = {
            ImprovementCategory.SECURITY: 5,
            ImprovementCategory.ARCHITECTURE: 20,
            ImprovementCategory.DATABASE: 10,
            ImprovementCategory.PERFORMANCE: 5,
            ImprovementCategory.MAINTAINABILITY: 8,
            ImprovementCategory.TESTING: 10,
            ImprovementCategory.DOCUMENTATION: 3,
            ImprovementCategory.INFRASTRUCTURE: 5,
        }

        impact_multiplier = {
            ImpactLevel.CRITICAL: 2.0,
            ImpactLevel.HIGH: 1.5,
            ImpactLevel.MEDIUM: 1.0,
            ImpactLevel.LOW: 0.5,
        }

        return base_effort.get(category, 5) * impact_multiplier.get(impact, 1.0)

    def _calculate_priority(self, impact: ImpactLevel, effort: float) -> int:
        """Calculate priority 1-5."""
        impact_score = {
            ImpactLevel.CRITICAL: 4,
            ImpactLevel.HIGH: 3,
            ImpactLevel.MEDIUM: 2,
            ImpactLevel.LOW: 1,
        }.get(impact, 2)

        roi = impact_score / (effort / 5)

        if roi >= 3:
            return 1
        elif roi >= 2:
            return 2
        elif roi >= 1:
            return 3
        elif roi >= 0.5:
            return 4
        else:
            return 5

    def _categorize_items(self) -> None:
        """Categorize items by type and priority."""
        # By type
        self.plan.quick_wins = [
            item for item in self.plan.items
            if item.item_type == ImprovementType.QUICK_WIN
        ]

        self.plan.strategic_items = [
            item for item in self.plan.items
            if item.item_type == ImprovementType.STRATEGIC
        ]

        self.plan.technical_debt = [
            item for item in self.plan.items
            if item.item_type == ImprovementType.TECHNICAL_DEBT
        ]

        # By category
        for item in self.plan.items:
            cat = item.category.value
            if cat not in self.plan.by_category:
                self.plan.by_category[cat] = []
            self.plan.by_category[cat].append(item)

        # By priority
        for item in self.plan.items:
            if item.priority not in self.plan.by_priority:
                self.plan.by_priority[item.priority] = []
            self.plan.by_priority[item.priority].append(item)

    def _build_dependencies(self) -> None:
        """Build dependency relationships between items."""
        # Security fixes should come before other improvements
        security_ids = [
            item.id for item in self.plan.items
            if item.item_type == ImprovementType.SECURITY_FIX
        ]

        # Architecture changes should come before optimizations
        arch_ids = [
            item.id for item in self.plan.items
            if item.category == ImprovementCategory.ARCHITECTURE
        ]

        for item in self.plan.items:
            # Non-security items depend on security fixes
            if item.item_type != ImprovementType.SECURITY_FIX:
                # Only add critical security as dependency
                critical_security = [
                    i.id for i in self.plan.items
                    if i.item_type == ImprovementType.SECURITY_FIX
                    and i.business_impact == ImpactLevel.CRITICAL
                ]
                item.depends_on.extend(critical_security[:2])  # Limit dependencies

            # Optimizations depend on architecture changes
            if item.item_type == ImprovementType.OPTIMIZATION:
                item.depends_on.extend(arch_ids[:2])

    def _filter_by_effort(self, max_effort: float) -> None:
        """Filter items to fit within effort budget."""
        # Sort by priority and ROI
        sorted_items = sorted(
            self.plan.items,
            key=lambda x: (x.priority, x.effort_days / max(1, x.priority))
        )

        filtered = []
        total_effort = 0

        for item in sorted_items:
            if total_effort + item.effort_days <= max_effort:
                filtered.append(item)
                total_effort += item.effort_days

        self.plan.items = filtered

    def _create_phases(self, team_size: int) -> None:
        """Create implementation phases."""
        # Phase 1: Security fixes and quick wins
        phase1_items = [
            item for item in self.plan.items
            if item.item_type == ImprovementType.SECURITY_FIX
            or item.item_type == ImprovementType.QUICK_WIN
        ]
        phase1_effort = sum(item.effort_days for item in phase1_items)

        # Phase 2: Strategic improvements
        phase2_items = [
            item for item in self.plan.items
            if item.item_type == ImprovementType.STRATEGIC
        ]
        phase2_effort = sum(item.effort_days for item in phase2_items)

        # Phase 3: Technical debt and optimizations
        phase3_items = [
            item for item in self.plan.items
            if item.item_type in [ImprovementType.TECHNICAL_DEBT, ImprovementType.OPTIMIZATION]
        ]
        phase3_effort = sum(item.effort_days for item in phase3_items)

        # Phase 4: Remaining items
        phase4_items = [
            item for item in self.plan.items
            if item not in phase1_items and item not in phase2_items and item not in phase3_items
        ]
        phase4_effort = sum(item.effort_days for item in phase4_items)

        self.plan.phases = [
            {
                "phase": 1,
                "name": "Security & Quick Wins",
                "description": "Address critical security issues and implement quick wins",
                "items": [item.id for item in phase1_items],
                "item_count": len(phase1_items),
                "effort_days": phase1_effort,
                "duration_weeks": max(1, round(phase1_effort / (team_size * 5))),
            },
            {
                "phase": 2,
                "name": "Strategic Improvements",
                "description": "Implement high-impact strategic improvements",
                "items": [item.id for item in phase2_items],
                "item_count": len(phase2_items),
                "effort_days": phase2_effort,
                "duration_weeks": max(1, round(phase2_effort / (team_size * 5))),
            },
            {
                "phase": 3,
                "name": "Technical Debt & Optimization",
                "description": "Reduce technical debt and optimize performance",
                "items": [item.id for item in phase3_items],
                "item_count": len(phase3_items),
                "effort_days": phase3_effort,
                "duration_weeks": max(1, round(phase3_effort / (team_size * 5))),
            },
        ]

        if phase4_items:
            self.plan.phases.append({
                "phase": 4,
                "name": "Remaining Improvements",
                "description": "Address remaining improvement items",
                "items": [item.id for item in phase4_items],
                "item_count": len(phase4_items),
                "effort_days": phase4_effort,
                "duration_weeks": max(1, round(phase4_effort / (team_size * 5))),
            })

    async def get_quick_wins(self, plan: ImprovementPlan, max_items: int = 5) -> List[ImprovementItem]:
        """Get top quick wins from plan."""
        quick_wins = sorted(
            plan.quick_wins,
            key=lambda x: (x.priority, -x.business_impact.value == "critical")
        )
        return quick_wins[:max_items]

    async def get_critical_security_fixes(self, plan: ImprovementPlan) -> List[ImprovementItem]:
        """Get critical security fixes that need immediate attention."""
        return [
            item for item in plan.items
            if item.item_type == ImprovementType.SECURITY_FIX
            and item.business_impact in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]
        ]

    async def export_to_jira_format(self, plan: ImprovementPlan) -> List[Dict[str, Any]]:
        """Export plan items in Jira-compatible format."""
        return [
            {
                "summary": item.title,
                "description": item.description,
                "issueType": "Improvement",
                "priority": self._map_priority_to_jira(item.priority),
                "labels": [item.category.value, item.item_type.value],
                "storyPoints": self._effort_to_story_points(item.effort_days),
                "customFields": {
                    "businessImpact": item.business_impact.value,
                    "riskIfNotDone": item.risk_if_not_done.value,
                },
            }
            for item in plan.items
        ]

    def _map_priority_to_jira(self, priority: int) -> str:
        """Map priority 1-5 to Jira priority."""
        mapping = {
            1: "Highest",
            2: "High",
            3: "Medium",
            4: "Low",
            5: "Lowest",
        }
        return mapping.get(priority, "Medium")

    def _effort_to_story_points(self, effort_days: float) -> int:
        """Convert effort days to story points."""
        if effort_days <= 1:
            return 1
        elif effort_days <= 2:
            return 2
        elif effort_days <= 3:
            return 3
        elif effort_days <= 5:
            return 5
        elif effort_days <= 8:
            return 8
        elif effort_days <= 13:
            return 13
        else:
            return 21
