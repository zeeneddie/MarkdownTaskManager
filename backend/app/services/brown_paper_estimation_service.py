"""
Brown Paper Estimation Service

Integrates IFPUG Function Point Analysis with Brown Paper workflow.
Provides automatic FP calculation for existing code with confidence scoring.
"""

import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Complexity(Enum):
    """IFPUG complexity levels."""
    LOW = "Low"
    AVERAGE = "Average"
    HIGH = "High"


class ComponentType(Enum):
    """IFPUG component types."""
    ILF = "ILF"  # Internal Logical File
    EIF = "EIF"  # External Interface File
    EI = "EI"    # External Input
    EO = "EO"    # External Output
    EQ = "EQ"    # External Inquiry


@dataclass
class FPComponent:
    """A single Function Point component."""
    name: str
    component_type: ComponentType
    complexity: Complexity
    description: str = ""
    source_file: str = ""
    source_line: int = 0
    confidence: float = 0.8  # 0.0 - 1.0

    @property
    def fp_value(self) -> int:
        """Calculate FP value based on type and complexity."""
        return FP_VALUES[self.component_type][self.complexity]


# IFPUG CPM 4.3.1 FP value tables
FP_VALUES = {
    ComponentType.ILF: {Complexity.LOW: 7, Complexity.AVERAGE: 10, Complexity.HIGH: 15},
    ComponentType.EIF: {Complexity.LOW: 5, Complexity.AVERAGE: 7, Complexity.HIGH: 10},
    ComponentType.EI: {Complexity.LOW: 3, Complexity.AVERAGE: 4, Complexity.HIGH: 6},
    ComponentType.EO: {Complexity.LOW: 4, Complexity.AVERAGE: 5, Complexity.HIGH: 7},
    ComponentType.EQ: {Complexity.LOW: 3, Complexity.AVERAGE: 4, Complexity.HIGH: 6},
}


@dataclass
class GSCScores:
    """General System Characteristics for VAF calculation."""
    data_communications: int = 0
    distributed_data: int = 0
    performance: int = 0
    heavily_used_config: int = 0
    transaction_rate: int = 0
    online_data_entry: int = 0
    end_user_efficiency: int = 0
    online_update: int = 0
    complex_processing: int = 0
    reusability: int = 0
    installation_ease: int = 0
    operational_ease: int = 0
    multiple_sites: int = 0
    facilitate_change: int = 0

    @property
    def total(self) -> int:
        """Sum of all GSC scores."""
        return (
            self.data_communications +
            self.distributed_data +
            self.performance +
            self.heavily_used_config +
            self.transaction_rate +
            self.online_data_entry +
            self.end_user_efficiency +
            self.online_update +
            self.complex_processing +
            self.reusability +
            self.installation_ease +
            self.operational_ease +
            self.multiple_sites +
            self.facilitate_change
        )

    @property
    def vaf(self) -> float:
        """Calculate Value Adjustment Factor."""
        return 0.65 + (self.total * 0.01)


@dataclass
class FPAnalysisResult:
    """Result of Function Point analysis."""
    components: List[FPComponent] = field(default_factory=list)
    gsc_scores: GSCScores = field(default_factory=GSCScores)
    confidence_score: float = 0.0
    low_confidence_items: List[Dict[str, Any]] = field(default_factory=list)
    analysis_timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total_ufp(self) -> int:
        """Unadjusted Function Points."""
        return sum(c.fp_value for c in self.components)

    @property
    def vaf(self) -> float:
        """Value Adjustment Factor."""
        return self.gsc_scores.vaf

    @property
    def total_afp(self) -> int:
        """Adjusted Function Points."""
        return round(self.total_ufp * self.vaf)

    @property
    def estimated_sp(self) -> int:
        """Estimated Story Points (conservative ratio for legacy code)."""
        return round(self.total_afp * 0.19)

    def by_type(self) -> Dict[ComponentType, List[FPComponent]]:
        """Group components by type."""
        result = {ct: [] for ct in ComponentType}
        for comp in self.components:
            result[comp.component_type].append(comp)
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "total_ufp": self.total_ufp,
            "vaf": round(self.vaf, 2),
            "total_afp": self.total_afp,
            "estimated_sp": self.estimated_sp,
            "confidence_score": round(self.confidence_score * 100, 1),
            "component_count": len(self.components),
            "by_type": {
                ct.value: {
                    "count": len(comps),
                    "fp": sum(c.fp_value for c in comps),
                    "items": [
                        {
                            "name": c.name,
                            "complexity": c.complexity.value,
                            "fp": c.fp_value,
                            "confidence": round(c.confidence * 100, 1),
                        }
                        for c in comps
                    ],
                }
                for ct, comps in self.by_type().items()
            },
            "low_confidence_items": self.low_confidence_items,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
        }


class BrownPaperEstimationService:
    """
    Service for automatic Function Point estimation from existing code.

    Uses pattern-based analysis to identify IFPUG components and estimate
    complexity based on code structure.
    """

    # Pattern detection configuration
    PATTERNS = {
        # ILF patterns - data stores maintained by the application
        "ILF": [
            (r"class\s+(\w+).*\(.*Base\)", "ORM Model"),
            (r"CREATE\s+TABLE\s+(\w+)", "Database Table"),
            (r"@dataclass\s+class\s+(\w+)", "Data Class"),
            (r"class\s+(\w+)Model\b", "Model Class"),
        ],
        # EIF patterns - external data sources
        "EIF": [
            (r"\.soap\.", "SOAP Service"),
            (r"WebClient|HttpClient|requests\.", "HTTP Client"),
            (r"\.ws\.|WebService|_soap_", "Web Service"),
            (r"External.*Interface|Provider", "External Interface"),
        ],
        # EI patterns - external inputs
        "EI": [
            (r"@(app\.|router\.)(post|put|delete|patch)", "API Mutation"),
            (r"Request\.(Form|Files|QueryString)", "Form Input"),
            (r"def\s+handle_|def\s+process_", "Input Handler"),
            (r"\.insert|\.update|\.delete", "CRUD Operation"),
        ],
        # EO patterns - external outputs with calculations
        "EO": [
            (r"Response\.Write|return.*render|export", "Output Response"),
            (r"Report|Export|Generate.*PDF", "Report Generation"),
            (r"\.xls|\.xlsx|\.csv|\.pdf", "File Export"),
            (r"aggregate|calculate|sum\(|avg\(", "Calculated Output"),
        ],
        # EQ patterns - simple queries
        "EQ": [
            (r"@(app\.|router\.)get", "API Query"),
            (r"\.find\(|\.get\(|\.select\(", "Data Query"),
            (r"SELECT.*FROM", "SQL Query"),
            (r"def\s+get_|def\s+list_|def\s+search_", "Query Method"),
        ],
    }

    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        "high": [
            r"for.*for",  # Nested loops
            r"switch.*case.*case.*case.*case",  # Many cases
            r"if.*else.*if.*else.*if",  # Nested conditions
            r"try.*catch.*try",  # Nested error handling
            r"JOIN.*JOIN.*JOIN",  # Multiple joins
        ],
        "low": [
            r"simple|basic|default",  # Simple naming
            r"\.Length|\.Count|\.Size",  # Simple operations
        ],
    }

    def __init__(self, fp_to_sp_ratio: float = 0.19, confidence_threshold: float = 0.7):
        """
        Initialize the estimation service.

        Args:
            fp_to_sp_ratio: Conversion ratio from FP to SP (default: conservative)
            confidence_threshold: Threshold for flagging low-confidence items
        """
        self.fp_to_sp_ratio = fp_to_sp_ratio
        self.confidence_threshold = confidence_threshold

    def analyze_file(self, file_path: Path) -> List[FPComponent]:
        """
        Analyze a single file for FP components.

        Args:
            file_path: Path to the source file

        Returns:
            List of detected FP components
        """
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return []

        components = []

        for comp_type_str, patterns in self.PATTERNS.items():
            comp_type = ComponentType[comp_type_str]

            for pattern, description in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)

                for match in matches:
                    # Extract component name
                    if match.groups():
                        name = match.group(1)
                    else:
                        name = match.group(0)[:50]

                    # Determine complexity
                    complexity = self._determine_complexity(content, match)

                    # Calculate confidence
                    confidence = self._calculate_confidence(content, match, comp_type)

                    # Get line number
                    line_num = content[:match.start()].count('\n') + 1

                    components.append(FPComponent(
                        name=name,
                        component_type=comp_type,
                        complexity=complexity,
                        description=description,
                        source_file=str(file_path),
                        source_line=line_num,
                        confidence=confidence,
                    ))

        return self._deduplicate_components(components)

    def analyze_directory(
        self,
        directory: Path,
        extensions: List[str] = None,
        recursive: bool = True,
    ) -> FPAnalysisResult:
        """
        Analyze all files in a directory.

        Args:
            directory: Directory path to analyze
            extensions: File extensions to include (default: common code files)
            recursive: Whether to include subdirectories

        Returns:
            Complete FP analysis result
        """
        if extensions is None:
            extensions = ['.py', '.vb', '.cs', '.java', '.ts', '.js', '.aspx', '.ashx']

        all_components = []

        pattern = "**/*" if recursive else "*"
        for ext in extensions:
            for file_path in directory.glob(f"{pattern}{ext}"):
                components = self.analyze_file(file_path)
                all_components.extend(components)

        # Deduplicate across files
        all_components = self._deduplicate_components(all_components)

        # Calculate overall confidence
        if all_components:
            avg_confidence = sum(c.confidence for c in all_components) / len(all_components)
        else:
            avg_confidence = 0.0

        # Identify low-confidence items
        low_confidence = [
            {
                "name": c.name,
                "type": c.component_type.value,
                "confidence": round(c.confidence * 100, 1),
                "file": c.source_file,
                "line": c.source_line,
            }
            for c in all_components
            if c.confidence < self.confidence_threshold
        ]

        # Estimate GSC scores based on detected patterns
        gsc_scores = self._estimate_gsc_scores(all_components)

        return FPAnalysisResult(
            components=all_components,
            gsc_scores=gsc_scores,
            confidence_score=avg_confidence,
            low_confidence_items=low_confidence,
        )

    def _determine_complexity(self, content: str, match: re.Match) -> Complexity:
        """Determine complexity based on surrounding code."""
        # Get context around the match (100 chars before and after)
        start = max(0, match.start() - 200)
        end = min(len(content), match.end() + 200)
        context = content[start:end]

        # Check for high complexity indicators
        for pattern in self.COMPLEXITY_INDICATORS["high"]:
            if re.search(pattern, context, re.IGNORECASE):
                return Complexity.HIGH

        # Check for low complexity indicators
        for pattern in self.COMPLEXITY_INDICATORS["low"]:
            if re.search(pattern, context, re.IGNORECASE):
                return Complexity.LOW

        return Complexity.AVERAGE

    def _calculate_confidence(
        self,
        content: str,
        match: re.Match,
        comp_type: ComponentType,
    ) -> float:
        """Calculate confidence score for a component detection."""
        confidence = 0.7  # Base confidence

        # Increase confidence for clear patterns
        if comp_type == ComponentType.ILF and "CREATE TABLE" in content:
            confidence += 0.2
        if comp_type == ComponentType.EIF and ("SOAP" in content or "WebService" in content):
            confidence += 0.15
        if comp_type == ComponentType.EI and "@app.post" in content.lower():
            confidence += 0.2

        # Decrease confidence for ambiguous patterns
        if "test" in match.group(0).lower():
            confidence -= 0.3
        if "mock" in match.group(0).lower():
            confidence -= 0.3
        if "example" in match.group(0).lower():
            confidence -= 0.2

        # Check for documentation
        start = max(0, match.start() - 200)
        context_before = content[start:match.start()]
        if '"""' in context_before or "'''" in context_before or "///" in context_before:
            confidence += 0.1  # Better documented code

        return max(0.1, min(1.0, confidence))

    def _deduplicate_components(self, components: List[FPComponent]) -> List[FPComponent]:
        """Remove duplicate components based on name and type."""
        seen = set()
        unique = []

        for comp in components:
            key = (comp.name.lower(), comp.component_type)
            if key not in seen:
                seen.add(key)
                unique.append(comp)

        return unique

    def _estimate_gsc_scores(self, components: List[FPComponent]) -> GSCScores:
        """Estimate GSC scores based on detected components."""
        gsc = GSCScores()

        # Count EIF for data communications
        eif_count = sum(1 for c in components if c.component_type == ComponentType.EIF)
        gsc.data_communications = min(5, eif_count)

        # Check for distributed processing
        if eif_count > 3:
            gsc.distributed_data = 2

        # Check for transaction volume
        ei_count = sum(1 for c in components if c.component_type == ComponentType.EI)
        gsc.transaction_rate = min(5, ei_count // 3)

        # Check for online updates
        if ei_count > 0:
            gsc.online_update = min(3, ei_count // 2)

        # Check for complex processing (high complexity components)
        high_complexity = sum(1 for c in components if c.complexity == Complexity.HIGH)
        gsc.complex_processing = min(5, high_complexity)

        return gsc

    def estimate_for_epic(
        self,
        epic_path: Path,
        include_breakdown: bool = True,
    ) -> Dict[str, Any]:
        """
        Estimate FP/SP for an entire epic based on code paths.

        Args:
            epic_path: Path to epic source code
            include_breakdown: Whether to include per-feature breakdown

        Returns:
            Dictionary with FP/SP estimates and breakdown
        """
        result = self.analyze_directory(epic_path)

        output = {
            "epic_path": str(epic_path),
            "total_function_points": result.total_afp,
            "total_story_points": result.estimated_sp,
            "confidence_score": round(result.confidence_score * 100, 1),
            "vaf": round(result.vaf, 2),
            "summary": {
                "components": len(result.components),
                "by_type": {
                    ct.value: len(comps)
                    for ct, comps in result.by_type().items()
                },
            },
        }

        if include_breakdown:
            output["breakdown"] = result.to_dict()

        if result.low_confidence_items:
            output["requires_review"] = True
            output["low_confidence_count"] = len(result.low_confidence_items)

        return output


# Singleton instance
_service: Optional[BrownPaperEstimationService] = None


def get_brown_paper_estimation_service() -> BrownPaperEstimationService:
    """Get the global brown paper estimation service instance."""
    global _service
    if _service is None:
        _service = BrownPaperEstimationService()
    return _service
