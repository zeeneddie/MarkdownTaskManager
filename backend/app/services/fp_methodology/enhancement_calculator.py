# Enhancement FP Calculator
# IFPUG CPM 4.3.1 Enhancement Function Point counting
#
# For maintenance, bug fixes, and enhancement work:
# - ADD: New functions added
# - CHNG: Functions changed (count AFTER change)
# - DEL: Functions deleted (40% of original FP)
# - CFP: Conversion functions (one-time data migration)
#
# Formula: EFP = ADD + CHNG + CFP + DEL
#
# Architecture: docs/roadmap/phases/fase-22-fp-methodology.md
# Phase: Fase 22 (Week 146-147)

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Type of change in enhancement project."""
    ADD = "add"       # New function added
    CHANGE = "change"  # Existing function modified
    DELETE = "delete"  # Function removed
    CONVERSION = "conversion"  # One-time data migration


class Complexity(Enum):
    """IFPUG complexity levels."""
    LOW = "low"
    AVERAGE = "average"
    HIGH = "high"


class ComponentType(Enum):
    """IFPUG component types for transactions."""
    EI = "EI"  # External Input
    EO = "EO"  # External Output
    EQ = "EQ"  # External Inquiry


# IFPUG FP values for transactions
TRANSACTION_FP_VALUES = {
    ComponentType.EI: {Complexity.LOW: 3, Complexity.AVERAGE: 4, Complexity.HIGH: 6},
    ComponentType.EO: {Complexity.LOW: 4, Complexity.AVERAGE: 5, Complexity.HIGH: 7},
    ComponentType.EQ: {Complexity.LOW: 3, Complexity.AVERAGE: 4, Complexity.HIGH: 6},
}

# Delete FP ratio (40% of original FP per IFPUG)
DELETE_FP_RATIO = 0.40


@dataclass
class EnhancementComponent:
    """A component in an enhancement project."""
    name: str
    change_type: ChangeType
    component_type: ComponentType = ComponentType.EI
    complexity: Complexity = Complexity.AVERAGE
    description: str = ""
    dets: int = 0  # Data Element Types
    ftrs: int = 0  # File Types Referenced
    original_fp: int = 0  # For DELETE: original FP value

    @property
    def fp_value(self) -> float:
        """Calculate FP value based on change type."""
        if self.change_type == ChangeType.DELETE:
            # Deleted functions count at 40% of original value
            if self.original_fp > 0:
                return self.original_fp * DELETE_FP_RATIO
            # If no original FP provided, use average complexity
            base_fp = TRANSACTION_FP_VALUES[self.component_type][Complexity.AVERAGE]
            return base_fp * DELETE_FP_RATIO

        # ADD, CHANGE, CONVERSION use normal FP values
        return TRANSACTION_FP_VALUES[self.component_type][self.complexity]


@dataclass
class EnhancementFPResult:
    """Result of Enhancement FP calculation."""
    added: List[EnhancementComponent] = field(default_factory=list)
    changed: List[EnhancementComponent] = field(default_factory=list)
    deleted: List[EnhancementComponent] = field(default_factory=list)
    conversion: List[EnhancementComponent] = field(default_factory=list)

    # Optional VAF (deprecated but supported)
    use_vaf: bool = False
    vaf: float = 1.0

    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def add_fp(self) -> float:
        """Total FP for added functions."""
        return sum(c.fp_value for c in self.added)

    @property
    def change_fp(self) -> float:
        """Total FP for changed functions."""
        return sum(c.fp_value for c in self.changed)

    @property
    def delete_fp(self) -> float:
        """Total FP for deleted functions (40% of original)."""
        return sum(c.fp_value for c in self.deleted)

    @property
    def conversion_fp(self) -> float:
        """Total FP for conversion functions."""
        return sum(c.fp_value for c in self.conversion)

    @property
    def total_ufp(self) -> float:
        """Unadjusted Enhancement Function Points."""
        return self.add_fp + self.change_fp + self.delete_fp + self.conversion_fp

    @property
    def total_efp(self) -> float:
        """
        Enhancement Function Points.

        Formula: EFP = (ADD + CHNG + DEL + CFP) × VAF
        Note: VAF is deprecated in CPM 4.3.1, default to 1.0
        """
        if self.use_vaf:
            logger.warning(
                "VAF is deprecated in IFPUG CPM 4.3.1. "
                "Report UFP only; VAF should be in appendix."
            )
            return round(self.total_ufp * self.vaf, 1)
        return round(self.total_ufp, 1)

    @property
    def component_count(self) -> int:
        """Total number of components."""
        return (
            len(self.added) +
            len(self.changed) +
            len(self.deleted) +
            len(self.conversion)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "add_fp": round(self.add_fp, 1),
            "change_fp": round(self.change_fp, 1),
            "delete_fp": round(self.delete_fp, 1),
            "conversion_fp": round(self.conversion_fp, 1),
            "total_ufp": round(self.total_ufp, 1),
            "total_efp": self.total_efp,
            "use_vaf": self.use_vaf,
            "vaf": self.vaf if self.use_vaf else None,
            "component_count": self.component_count,
            "breakdown": {
                "added": len(self.added),
                "changed": len(self.changed),
                "deleted": len(self.deleted),
                "conversion": len(self.conversion),
            },
            "calculated_at": self.calculated_at.isoformat(),
        }


class EnhancementFPCalculator:
    """
    Calculate Enhancement Function Points for maintenance/fix work.

    IFPUG Enhancement FP counting rules:
    - ADD: Count FP of new functions (standard FP values)
    - CHNG: Count FP of changed functions AFTER change
    - DEL: Count 40% of original FP for deleted functions
    - CFP: Count FP of one-time conversion functions

    Usage:
        calculator = EnhancementFPCalculator()

        result = calculator.calculate(
            added=[
                {"name": "CleanupResources()", "type": "EI", "complexity": "low"},
                {"name": "SafeEnd()", "type": "EI", "complexity": "low"},
            ],
            changed=[
                {"name": "Declaratie_verzenden", "type": "EI", "complexity": "average"},
            ],
            deleted=[],
        )

        print(f"Enhancement FP: {result.total_efp}")
    """

    def calculate(
        self,
        added: Optional[List[Dict[str, Any]]] = None,
        changed: Optional[List[Dict[str, Any]]] = None,
        deleted: Optional[List[Dict[str, Any]]] = None,
        conversion: Optional[List[Dict[str, Any]]] = None,
        use_vaf: bool = False,
        vaf: float = 1.0,
    ) -> EnhancementFPResult:
        """
        Calculate Enhancement Function Points.

        Args:
            added: List of new functions (dicts with name, type, complexity)
            changed: List of changed functions (count AFTER change)
            deleted: List of deleted functions (include original_fp if known)
            conversion: List of one-time conversion functions
            use_vaf: Whether to apply VAF (deprecated)
            vaf: Value Adjustment Factor (0.65-1.35)

        Returns:
            EnhancementFPResult with FP breakdown
        """
        result = EnhancementFPResult(use_vaf=use_vaf, vaf=vaf)

        # Process added components
        if added:
            for comp_data in added:
                component = self._create_component(comp_data, ChangeType.ADD)
                result.added.append(component)

        # Process changed components
        if changed:
            for comp_data in changed:
                component = self._create_component(comp_data, ChangeType.CHANGE)
                result.changed.append(component)

        # Process deleted components
        if deleted:
            for comp_data in deleted:
                component = self._create_component(comp_data, ChangeType.DELETE)
                result.deleted.append(component)

        # Process conversion components
        if conversion:
            for comp_data in conversion:
                component = self._create_component(comp_data, ChangeType.CONVERSION)
                result.conversion.append(component)

        logger.info(
            f"Enhancement FP calculated: ADD={result.add_fp}, "
            f"CHNG={result.change_fp}, DEL={result.delete_fp}, "
            f"CFP={result.conversion_fp}, Total={result.total_efp}"
        )

        return result

    def _create_component(
        self,
        data: Dict[str, Any],
        change_type: ChangeType,
    ) -> EnhancementComponent:
        """Create EnhancementComponent from dict data."""
        # Parse component type
        comp_type_str = data.get("type", "EI").upper()
        try:
            comp_type = ComponentType(comp_type_str)
        except ValueError:
            comp_type = ComponentType.EI
            logger.warning(f"Unknown component type '{comp_type_str}', defaulting to EI")

        # Parse complexity
        complexity_str = data.get("complexity", "average").lower()
        try:
            complexity = Complexity(complexity_str)
        except ValueError:
            complexity = Complexity.AVERAGE
            logger.warning(f"Unknown complexity '{complexity_str}', defaulting to average")

        return EnhancementComponent(
            name=data.get("name", "Unknown"),
            change_type=change_type,
            component_type=comp_type,
            complexity=complexity,
            description=data.get("description", ""),
            dets=data.get("dets", 0),
            ftrs=data.get("ftrs", 0),
            original_fp=data.get("original_fp", 0),
        )

    def estimate_productivity(
        self,
        efp: float,
        hours: float,
    ) -> Dict[str, Any]:
        """
        Estimate productivity and validate against industry norms.

        Args:
            efp: Enhancement Function Points
            hours: Actual hours spent

        Returns:
            Productivity analysis with industry comparison
        """
        if hours <= 0:
            return {"error": "Hours must be positive"}

        fp_per_hour = efp / hours

        # Industry norms for productivity (FP per hour)
        PRODUCTIVITY_NORMS = {
            "low": {"min": 0.1, "max": 0.3, "description": "Complex legacy maintenance"},
            "normal": {"min": 0.3, "max": 0.8, "description": "Typical maintenance work"},
            "high": {"min": 0.8, "max": 1.5, "description": "Well-understood codebase"},
            "anomaly": {"min": 1.5, "max": float('inf'), "description": "Possible methodology error"},
        }

        # Determine productivity category
        category = "anomaly"
        for cat, norms in PRODUCTIVITY_NORMS.items():
            if norms["min"] <= fp_per_hour < norms["max"]:
                category = cat
                break

        return {
            "efp": efp,
            "hours": hours,
            "fp_per_hour": round(fp_per_hour, 2),
            "category": category,
            "description": PRODUCTIVITY_NORMS[category]["description"],
            "is_anomaly": category == "anomaly",
            "expected_range": f"{PRODUCTIVITY_NORMS['normal']['min']}-{PRODUCTIVITY_NORMS['normal']['max']} FP/hour",
            "recommendation": (
                "Verify FP calculation methodology - productivity is unusually high"
                if category == "anomaly"
                else "Productivity within expected range"
            ),
        }
