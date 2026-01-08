"""
IFPUG Function Point Calculator

Implements the International Function Point Users Group (IFPUG)
Counting Practices Manual (CPM) 4.3.1 methodology for software size estimation.

References:
- IFPUG CPM 4.3.1 (January 2010)
- ISO/IEC 20926:2003

Author: Claude Code (Week 13 Day 4)
Date: 2025-11-19
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Data Models
# ============================================================================

class ComponentInput(BaseModel):
    """Input for a single function point component (ILF, EIF, EI, EO, or EQ)"""
    name: str = Field(..., description="Component name (e.g., 'User Database', 'Login Form')")
    description: Optional[str] = Field(None, description="Optional description of the component")

    # For ILF/EIF (data functions)
    rets: Optional[int] = Field(None, description="Record Element Types (logical subgroups)")

    # For all components
    dets: int = Field(..., description="Data Element Types (unique user-recognizable fields)", gt=0)

    # For EI/EO/EQ (transactional functions)
    ftrs: Optional[int] = Field(None, description="File Types Referenced (ILFs/EIFs accessed)")

    @field_validator('rets')
    @classmethod
    def validate_rets(cls, v):
        if v is not None and v < 1:
            raise ValueError("RETs must be >= 1 if provided")
        return v

    @field_validator('ftrs')
    @classmethod
    def validate_ftrs(cls, v):
        if v is not None and v < 0:
            raise ValueError("FTRs must be >= 0 if provided")
        return v


class ComponentResult(BaseModel):
    """Result for a single component calculation"""
    name: str
    complexity: Literal["Low", "Average", "High"]
    function_points: int
    details: Dict[str, Any]


class FunctionPointRequest(BaseModel):
    """Complete function point calculation request"""
    project_name: str = Field(..., description="Name of the project being estimated")

    # Data functions
    ilfs: List[ComponentInput] = Field(default_factory=list, description="Internal Logical Files")
    eifs: List[ComponentInput] = Field(default_factory=list, description="External Interface Files")

    # Transactional functions
    eis: List[ComponentInput] = Field(default_factory=list, description="External Inputs")
    eos: List[ComponentInput] = Field(default_factory=list, description="External Outputs")
    eqs: List[ComponentInput] = Field(default_factory=list, description="External Queries")

    # VAF (optional)
    use_vaf: bool = Field(False, description="Whether to apply Value Adjustment Factor")
    gsc_ratings: Optional[List[int]] = Field(
        None,
        description="14 General System Characteristics ratings (0-5 each)"
    )

    @model_validator(mode='after')
    def validate_gsc_ratings(self):
        if self.use_vaf and self.gsc_ratings is None:
            raise ValueError("gsc_ratings required when use_vaf=True")
        if self.gsc_ratings is not None:
            if len(self.gsc_ratings) != 14:
                raise ValueError("gsc_ratings must contain exactly 14 values")
            if any(rating < 0 or rating > 5 for rating in self.gsc_ratings):
                raise ValueError("Each GSC rating must be between 0 and 5")
        return self


class FunctionPointResponse(BaseModel):
    """Complete function point calculation response"""
    project_name: str

    # Component results
    ilf_results: List[ComponentResult]
    eif_results: List[ComponentResult]
    ei_results: List[ComponentResult]
    eo_results: List[ComponentResult]
    eq_results: List[ComponentResult]

    # Component totals
    total_ilf_fp: int
    total_eif_fp: int
    total_ei_fp: int
    total_eo_fp: int
    total_eq_fp: int

    # Final calculations
    unadjusted_fp: int  # UFP
    vaf: float  # Value Adjustment Factor
    adjusted_fp: float  # AFP = UFP × VAF

    # Summary
    summary: Dict[str, Any]


# ============================================================================
# ILF Calculator (Internal Logical Files)
# ============================================================================

class ILFCalculator:
    """
    Calculates function points for Internal Logical Files (ILF).

    ILF: User-identifiable groups of logically related data that:
    - Reside entirely within the application boundary
    - Are maintained through External Inputs

    Complexity Matrix (RETs × DETs):
        RETs/DETs    1-19 DETs    20-50 DETs    51+ DETs
        1 RET        Low (7)      Low (7)       Average (10)
        2-5 RETs     Low (7)      Average (10)  High (15)
        6+ RETs      Average (10) High (15)     High (15)
    """

    WEIGHTS = {
        "Low": 7,
        "Average": 10,
        "High": 15
    }

    @staticmethod
    def determine_complexity(rets: int, dets: int) -> str:
        """Determine ILF complexity based on RETs and DETs"""
        if rets == 1:
            if dets <= 50:
                return "Low"
            else:
                return "Average"
        elif 2 <= rets <= 5:
            if dets <= 19:
                return "Low"
            elif dets <= 50:
                return "Average"
            else:
                return "High"
        else:  # rets >= 6
            if dets <= 19:
                return "Average"
            else:
                return "High"

    @classmethod
    def calculate(cls, component: ComponentInput) -> ComponentResult:
        """Calculate function points for an ILF component"""
        if component.rets is None:
            raise ValueError(f"ILF '{component.name}' requires RETs")

        complexity = cls.determine_complexity(component.rets, component.dets)
        fp = cls.WEIGHTS[complexity]

        return ComponentResult(
            name=component.name,
            complexity=complexity,
            function_points=fp,
            details={
                "type": "ILF",
                "rets": component.rets,
                "dets": component.dets,
                "description": component.description,
                "reasoning": f"{component.rets} RETs × {component.dets} DETs → {complexity} complexity"
            }
        )


# ============================================================================
# EIF Calculator (External Interface Files)
# ============================================================================

class EIFCalculator:
    """
    Calculates function points for External Interface Files (EIF).

    EIF: User-identifiable groups of logically related data that:
    - Are used for reference purposes only (read-only)
    - Reside entirely outside the application boundary
    - Are maintained by another application

    Complexity Matrix (RETs × DETs):
        RETs/DETs    1-19 DETs    20-50 DETs    51+ DETs
        1 RET        Low (5)      Low (5)       Average (7)
        2-5 RETs     Low (5)      Average (7)   High (10)
        6+ RETs      Average (7)  High (10)     High (10)
    """

    WEIGHTS = {
        "Low": 5,
        "Average": 7,
        "High": 10
    }

    @staticmethod
    def determine_complexity(rets: int, dets: int) -> str:
        """Determine EIF complexity based on RETs and DETs"""
        if rets == 1:
            if dets <= 50:
                return "Low"
            else:
                return "Average"
        elif 2 <= rets <= 5:
            if dets <= 19:
                return "Low"
            elif dets <= 50:
                return "Average"
            else:
                return "High"
        else:  # rets >= 6
            if dets <= 19:
                return "Average"
            else:
                return "High"

    @classmethod
    def calculate(cls, component: ComponentInput) -> ComponentResult:
        """Calculate function points for an EIF component"""
        if component.rets is None:
            raise ValueError(f"EIF '{component.name}' requires RETs")

        complexity = cls.determine_complexity(component.rets, component.dets)
        fp = cls.WEIGHTS[complexity]

        return ComponentResult(
            name=component.name,
            complexity=complexity,
            function_points=fp,
            details={
                "type": "EIF",
                "rets": component.rets,
                "dets": component.dets,
                "description": component.description,
                "reasoning": f"{component.rets} RETs × {component.dets} DETs → {complexity} complexity"
            }
        )


# ============================================================================
# EI Calculator (External Inputs)
# ============================================================================

class EICalculator:
    """
    Calculates function points for External Inputs (EI).

    EI: Elementary process that:
    - Processes data or control information coming from outside the boundary
    - Maintains one or more ILFs
    - Can alter system behavior

    Complexity Matrix (FTRs × DETs):
        FTRs/DETs    1-4 DETs     5-15 DETs     16+ DETs
        0-1 FTR      Low (3)      Low (3)       Average (4)
        2 FTRs       Low (3)      Average (4)   High (6)
        3+ FTRs      Average (4)  High (6)      High (6)
    """

    WEIGHTS = {
        "Low": 3,
        "Average": 4,
        "High": 6
    }

    @staticmethod
    def determine_complexity(ftrs: int, dets: int) -> str:
        """Determine EI complexity based on FTRs and DETs"""
        if ftrs <= 1:
            if dets <= 15:
                return "Low"
            else:
                return "Average"
        elif ftrs == 2:
            if dets <= 4:
                return "Low"
            elif dets <= 15:
                return "Average"
            else:
                return "High"
        else:  # ftrs >= 3
            if dets <= 4:
                return "Average"
            else:
                return "High"

    @classmethod
    def calculate(cls, component: ComponentInput) -> ComponentResult:
        """Calculate function points for an EI component"""
        if component.ftrs is None:
            raise ValueError(f"EI '{component.name}' requires FTRs")

        complexity = cls.determine_complexity(component.ftrs, component.dets)
        fp = cls.WEIGHTS[complexity]

        return ComponentResult(
            name=component.name,
            complexity=complexity,
            function_points=fp,
            details={
                "type": "EI",
                "ftrs": component.ftrs,
                "dets": component.dets,
                "description": component.description,
                "reasoning": f"{component.ftrs} FTRs × {component.dets} DETs → {complexity} complexity"
            }
        )


# ============================================================================
# EO Calculator (External Outputs)
# ============================================================================

class EOCalculator:
    """
    Calculates function points for External Outputs (EO).

    EO: Elementary process that:
    - Sends derived (calculated/processed) data outside the boundary
    - Includes data formatting/calculation logic
    - May update one or more ILFs

    Complexity Matrix (FTRs × DETs):
        FTRs/DETs    1-5 DETs     6-19 DETs     20+ DETs
        0-1 FTR      Low (4)      Low (4)       Average (5)
        2-3 FTRs     Low (4)      Average (5)   High (7)
        4+ FTRs      Average (5)  High (7)      High (7)
    """

    WEIGHTS = {
        "Low": 4,
        "Average": 5,
        "High": 7
    }

    @staticmethod
    def determine_complexity(ftrs: int, dets: int) -> str:
        """Determine EO complexity based on FTRs and DETs"""
        if ftrs <= 1:
            if dets <= 19:
                return "Low"
            else:
                return "Average"
        elif ftrs <= 3:
            if dets <= 5:
                return "Low"
            elif dets <= 19:
                return "Average"
            else:
                return "High"
        else:  # ftrs >= 4
            if dets <= 5:
                return "Average"
            else:
                return "High"

    @classmethod
    def calculate(cls, component: ComponentInput) -> ComponentResult:
        """Calculate function points for an EO component"""
        if component.ftrs is None:
            raise ValueError(f"EO '{component.name}' requires FTRs")

        complexity = cls.determine_complexity(component.ftrs, component.dets)
        fp = cls.WEIGHTS[complexity]

        return ComponentResult(
            name=component.name,
            complexity=complexity,
            function_points=fp,
            details={
                "type": "EO",
                "ftrs": component.ftrs,
                "dets": component.dets,
                "description": component.description,
                "reasoning": f"{component.ftrs} FTRs × {component.dets} DETs → {complexity} complexity"
            }
        )


# ============================================================================
# EQ Calculator (External Queries)
# ============================================================================

class EQCalculator:
    """
    Calculates function points for External Queries (EQ).

    EQ: Elementary process that:
    - Sends non-derived data outside the boundary
    - Retrieves data without calculation/processing
    - Does NOT update ILFs
    - Has both input and output components

    Complexity Matrix (FTRs × DETs):
        FTRs/DETs    1-5 DETs     6-19 DETs     20+ DETs
        0-1 FTR      Low (3)      Low (3)       Average (4)
        2-3 FTRs     Low (3)      Average (4)   High (6)
        4+ FTRs      Average (4)  High (6)      High (6)
    """

    WEIGHTS = {
        "Low": 3,
        "Average": 4,
        "High": 6
    }

    @staticmethod
    def determine_complexity(ftrs: int, dets: int) -> str:
        """Determine EQ complexity based on FTRs and DETs"""
        if ftrs <= 1:
            if dets <= 19:
                return "Low"
            else:
                return "Average"
        elif ftrs <= 3:
            if dets <= 5:
                return "Low"
            elif dets <= 19:
                return "Average"
            else:
                return "High"
        else:  # ftrs >= 4
            if dets <= 5:
                return "Average"
            else:
                return "High"

    @classmethod
    def calculate(cls, component: ComponentInput) -> ComponentResult:
        """Calculate function points for an EQ component"""
        if component.ftrs is None:
            raise ValueError(f"EQ '{component.name}' requires FTRs")

        complexity = cls.determine_complexity(component.ftrs, component.dets)
        fp = cls.WEIGHTS[complexity]

        return ComponentResult(
            name=component.name,
            complexity=complexity,
            function_points=fp,
            details={
                "type": "EQ",
                "ftrs": component.ftrs,
                "dets": component.dets,
                "description": component.description,
                "reasoning": f"{component.ftrs} FTRs × {component.dets} DETs → {complexity} complexity"
            }
        )


# ============================================================================
# VAF Calculator (Value Adjustment Factor)
# ============================================================================

class VAFCalculator:
    """
    Calculates Value Adjustment Factor (VAF) based on 14 General System Characteristics.

    VAF Formula: VAF = 0.65 + (TDI × 0.01)
    Where TDI = Total Degree of Influence (sum of 14 GSC ratings)

    GSC Rating Scale (0-5):
    - 0: Not present or no influence
    - 1: Incidental influence
    - 2: Moderate influence
    - 3: Average influence
    - 4: Significant influence
    - 5: Strong influence throughout

    The 14 GSCs:
    1. Data communications
    2. Distributed data processing
    3. Performance
    4. Heavily used configuration
    5. Transaction rate
    6. On-line data entry
    7. End-user efficiency
    8. On-line update
    9. Complex processing
    10. Reusability
    11. Installation ease
    12. Operational ease
    13. Multiple sites
    14. Facilitate change

    Note: VAF is optional in CPM 4.3.1 (moved to appendix)
    """

    GSC_NAMES = [
        "Data communications",
        "Distributed data processing",
        "Performance",
        "Heavily used configuration",
        "Transaction rate",
        "On-line data entry",
        "End-user efficiency",
        "On-line update",
        "Complex processing",
        "Reusability",
        "Installation ease",
        "Operational ease",
        "Multiple sites",
        "Facilitate change"
    ]

    @staticmethod
    def validate_gsc_ratings(ratings: List[int]) -> None:
        """Validate GSC ratings"""
        if len(ratings) != 14:
            raise ValueError(f"Expected 14 GSC ratings, got {len(ratings)}")

        for i, rating in enumerate(ratings):
            if not (0 <= rating <= 5):
                raise ValueError(
                    f"GSC rating {i+1} ({VAFCalculator.GSC_NAMES[i]}) must be 0-5, got {rating}"
                )

    @staticmethod
    def calculate_tdi(ratings: List[int]) -> int:
        """Calculate Total Degree of Influence (TDI)"""
        VAFCalculator.validate_gsc_ratings(ratings)
        return sum(ratings)

    @staticmethod
    def calculate_vaf(ratings: List[int]) -> float:
        """Calculate Value Adjustment Factor (VAF)"""
        tdi = VAFCalculator.calculate_tdi(ratings)
        vaf = 0.65 + (tdi * 0.01)
        return round(vaf, 2)

    @staticmethod
    def get_gsc_breakdown(ratings: List[int]) -> Dict[str, Any]:
        """Get detailed breakdown of GSC ratings"""
        VAFCalculator.validate_gsc_ratings(ratings)

        breakdown = []
        for i, (name, rating) in enumerate(zip(VAFCalculator.GSC_NAMES, ratings)):
            breakdown.append({
                "number": i + 1,
                "name": name,
                "rating": rating
            })

        tdi = sum(ratings)
        vaf = 0.65 + (tdi * 0.01)

        return {
            "gsc_breakdown": breakdown,
            "tdi": tdi,
            "vaf": round(vaf, 2),
            "vaf_range": "0.65 to 1.35",
            "impact": "Multiplier on unadjusted function points"
        }


# ============================================================================
# Main Function Point Calculator
# ============================================================================

class FunctionPointCalculator:
    """
    Main calculator that orchestrates all component calculations
    and produces the final function point count.

    Process:
    1. Calculate all components (ILF, EIF, EI, EO, EQ)
    2. Sum to get Unadjusted Function Points (UFP)
    3. Calculate Value Adjustment Factor (VAF) if requested
    4. Calculate Adjusted Function Points (AFP) = UFP × VAF
    """

    def __init__(self, request: FunctionPointRequest):
        self.request = request
        self.ilf_results: List[ComponentResult] = []
        self.eif_results: List[ComponentResult] = []
        self.ei_results: List[ComponentResult] = []
        self.eo_results: List[ComponentResult] = []
        self.eq_results: List[ComponentResult] = []

    def calculate_all_components(self) -> None:
        """Calculate function points for all components"""
        # ILFs
        for ilf in self.request.ilfs:
            result = ILFCalculator.calculate(ilf)
            self.ilf_results.append(result)

        # EIFs
        for eif in self.request.eifs:
            result = EIFCalculator.calculate(eif)
            self.eif_results.append(result)

        # EIs
        for ei in self.request.eis:
            result = EICalculator.calculate(ei)
            self.ei_results.append(result)

        # EOs
        for eo in self.request.eos:
            result = EOCalculator.calculate(eo)
            self.eo_results.append(result)

        # EQs
        for eq in self.request.eqs:
            result = EQCalculator.calculate(eq)
            self.eq_results.append(result)

    def calculate_unadjusted_fp(self) -> int:
        """Calculate Unadjusted Function Points (UFP)"""
        total_ilf = sum(r.function_points for r in self.ilf_results)
        total_eif = sum(r.function_points for r in self.eif_results)
        total_ei = sum(r.function_points for r in self.ei_results)
        total_eo = sum(r.function_points for r in self.eo_results)
        total_eq = sum(r.function_points for r in self.eq_results)

        return total_ilf + total_eif + total_ei + total_eo + total_eq

    def calculate_vaf(self) -> float:
        """Calculate Value Adjustment Factor (VAF)"""
        if not self.request.use_vaf:
            return 1.0

        if self.request.gsc_ratings is None:
            raise ValueError("GSC ratings required when use_vaf=True")

        return VAFCalculator.calculate_vaf(self.request.gsc_ratings)

    def calculate_adjusted_fp(self, ufp: int, vaf: float) -> float:
        """Calculate Adjusted Function Points (AFP)"""
        return round(ufp * vaf, 2)

    def generate_summary(self, ufp: int, vaf: float, afp: float) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_components = (
            len(self.ilf_results) + len(self.eif_results) +
            len(self.ei_results) + len(self.eo_results) + len(self.eq_results)
        )

        summary = {
            "total_components": total_components,
            "data_functions": len(self.ilf_results) + len(self.eif_results),
            "transactional_functions": len(self.ei_results) + len(self.eo_results) + len(self.eq_results),
            "component_counts": {
                "ilfs": len(self.ilf_results),
                "eifs": len(self.eif_results),
                "eis": len(self.ei_results),
                "eos": len(self.eo_results),
                "eqs": len(self.eq_results)
            },
            "calculation": {
                "unadjusted_fp": ufp,
                "vaf": vaf,
                "vaf_applied": self.request.use_vaf,
                "adjusted_fp": afp
            },
            "complexity_distribution": self._get_complexity_distribution(),
            "estimation_guidance": self._get_estimation_guidance(afp)
        }

        if self.request.use_vaf and self.request.gsc_ratings:
            summary["vaf_breakdown"] = VAFCalculator.get_gsc_breakdown(self.request.gsc_ratings)

        return summary

    def _get_complexity_distribution(self) -> Dict[str, int]:
        """Get distribution of complexities across all components"""
        all_results = (
            self.ilf_results + self.eif_results +
            self.ei_results + self.eo_results + self.eq_results
        )

        return {
            "low": sum(1 for r in all_results if r.complexity == "Low"),
            "average": sum(1 for r in all_results if r.complexity == "Average"),
            "high": sum(1 for r in all_results if r.complexity == "High")
        }

    def _get_estimation_guidance(self, afp: float) -> Dict[str, Any]:
        """Provide estimation guidance based on function points"""
        # Industry benchmarks (approximate)
        # Simple CRUD: ~10 FP/person-day
        # Average web app: ~8 FP/person-day
        # Complex enterprise: ~5 FP/person-day

        if afp < 50:
            category = "Small"
            person_days_range = f"{afp/10:.1f} - {afp/8:.1f}"
            complexity_note = "Simple CRUD application"
        elif afp < 200:
            category = "Medium"
            person_days_range = f"{afp/8:.1f} - {afp/5:.1f}"
            complexity_note = "Standard web/mobile application"
        elif afp < 500:
            category = "Large"
            person_days_range = f"{afp/5:.1f} - {afp/3:.1f}"
            complexity_note = "Complex business application"
        else:
            category = "Enterprise"
            person_days_range = f"{afp/3:.1f} - {afp/2:.1f}"
            complexity_note = "Enterprise-scale system"

        return {
            "project_size": category,
            "estimated_person_days": person_days_range,
            "complexity_note": complexity_note,
            "disclaimer": "Estimates vary by language, framework, team experience, and domain complexity"
        }

    def calculate(self) -> FunctionPointResponse:
        """Main calculation method - orchestrates entire process"""
        # Step 1: Calculate all components
        self.calculate_all_components()

        # Step 2: Calculate totals
        total_ilf_fp = sum(r.function_points for r in self.ilf_results)
        total_eif_fp = sum(r.function_points for r in self.eif_results)
        total_ei_fp = sum(r.function_points for r in self.ei_results)
        total_eo_fp = sum(r.function_points for r in self.eo_results)
        total_eq_fp = sum(r.function_points for r in self.eq_results)

        # Step 3: Calculate UFP
        ufp = self.calculate_unadjusted_fp()

        # Step 4: Calculate VAF
        vaf = self.calculate_vaf()

        # Step 5: Calculate AFP
        afp = self.calculate_adjusted_fp(ufp, vaf)

        # Step 6: Generate summary
        summary = self.generate_summary(ufp, vaf, afp)

        return FunctionPointResponse(
            project_name=self.request.project_name,
            ilf_results=self.ilf_results,
            eif_results=self.eif_results,
            ei_results=self.ei_results,
            eo_results=self.eo_results,
            eq_results=self.eq_results,
            total_ilf_fp=total_ilf_fp,
            total_eif_fp=total_eif_fp,
            total_ei_fp=total_ei_fp,
            total_eo_fp=total_eo_fp,
            total_eq_fp=total_eq_fp,
            unadjusted_fp=ufp,
            vaf=vaf,
            adjusted_fp=afp,
            summary=summary
        )
