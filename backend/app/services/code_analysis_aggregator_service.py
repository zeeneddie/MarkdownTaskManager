"""
Code Analysis Aggregator Service - Week 83

Unified code analysis combining:
- StackDetectionService: Technology stack detection
- DependencyGraphService: Module dependency analysis
- CodeWikiService: Documentation and structure analysis

This service provides the foundation for the Deep Extraction Pipeline,
gathering all structural data before LLM analysis begins.

Integration Points:
- Input: Repository path, project configuration
- Output: AggregatedAnalysis for DeepExtractionService
- Tier: Runs locally (no LLM costs), provides input for tier-aware LLM analysis
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import asyncio
import logging
import time
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.stack_detection_service import (
    StackDetectionService,
    ScanResult,
    StackDetection,
    ComplexityMetrics,
)
from app.services.dependency_graph_service import (
    DependencyGraphService,
    DependencyGraphResult,
    DependencyMetrics,
    CircularDependency,
    OutputFormat,
)
from app.services.codewiki_service import CodeWikiService
from app.models.codewiki import CodeWikiAnalysis, CodeWikiModule

logger = logging.getLogger(__name__)


@dataclass
class TechnologyProfile:
    """Summary of detected technology stack."""
    primary_stack: Optional[str] = None
    secondary_stacks: List[str] = field(default_factory=list)
    database_type: Optional[str] = None
    languages: Dict[str, int] = field(default_factory=dict)  # lang -> file_count
    frameworks: List[str] = field(default_factory=list)
    total_files: int = 0
    total_loc: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_stack": self.primary_stack,
            "secondary_stacks": self.secondary_stacks,
            "database_type": self.database_type,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "total_files": self.total_files,
            "total_loc": self.total_loc,
        }


@dataclass
class DependencyProfile:
    """Summary of dependency graph analysis."""
    module_count: int = 0
    edge_count: int = 0
    circular_dependencies: int = 0
    entry_points: List[str] = field(default_factory=list)
    hub_modules: List[str] = field(default_factory=list)  # Highly connected
    external_dependencies: int = 0
    internal_dependencies: int = 0
    instability_avg: float = 0.0
    coupling_score: float = 0.0  # 0-1, higher = more coupled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_count": self.module_count,
            "edge_count": self.edge_count,
            "circular_dependencies": self.circular_dependencies,
            "entry_points": self.entry_points[:10],  # Limit for storage
            "hub_modules": self.hub_modules[:10],
            "external_dependencies": self.external_dependencies,
            "internal_dependencies": self.internal_dependencies,
            "instability_avg": round(self.instability_avg, 3),
            "coupling_score": round(self.coupling_score, 3),
        }


@dataclass
class DocumentationProfile:
    """Summary of code documentation and structure."""
    module_count: int = 0
    documented_ratio: float = 0.0  # 0-1
    diagram_count: int = 0
    top_modules: List[Dict[str, Any]] = field(default_factory=list)
    architecture_detected: bool = False
    readme_exists: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_count": self.module_count,
            "documented_ratio": round(self.documented_ratio, 3),
            "diagram_count": self.diagram_count,
            "top_modules": self.top_modules[:10],
            "architecture_detected": self.architecture_detected,
            "readme_exists": self.readme_exists,
        }


@dataclass
class ComplexityProfile:
    """Code complexity summary."""
    avg_cyclomatic: float = 0.0
    max_cyclomatic: float = 0.0
    total_functions: int = 0
    high_complexity_count: int = 0  # Functions with CC > 10
    complexity_rating: str = "unknown"  # low/medium/high/critical

    def to_dict(self) -> Dict[str, Any]:
        return {
            "avg_cyclomatic": round(self.avg_cyclomatic, 2),
            "max_cyclomatic": self.max_cyclomatic,
            "total_functions": self.total_functions,
            "high_complexity_count": self.high_complexity_count,
            "complexity_rating": self.complexity_rating,
        }


@dataclass
class AggregatedAnalysis:
    """
    Complete aggregated analysis result.

    This is the input for DeepExtractionService's LLM analysis.
    """
    project_id: int
    repository_path: str
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: int = 0

    # Analysis profiles
    technology: TechnologyProfile = field(default_factory=TechnologyProfile)
    dependencies: DependencyProfile = field(default_factory=DependencyProfile)
    documentation: DocumentationProfile = field(default_factory=DocumentationProfile)
    complexity: ComplexityProfile = field(default_factory=ComplexityProfile)

    # Raw results for detailed access
    stack_scan_result: Optional[ScanResult] = None
    dependency_graph_result: Optional[DependencyGraphResult] = None
    codewiki_analysis_id: Optional[int] = None

    # Status
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_successful(self) -> bool:
        """Check if analysis completed without critical errors."""
        return len(self.errors) == 0

    @property
    def analysis_score(self) -> float:
        """
        Overall analysis quality score 0-100.

        Based on:
        - How much data was extracted
        - Code quality indicators
        - Documentation coverage
        """
        score = 0.0

        # Tech detection (20 points)
        if self.technology.primary_stack:
            score += 15
        if self.technology.database_type:
            score += 5

        # Dependency analysis (25 points)
        if self.dependencies.module_count > 0:
            score += 15
        if self.dependencies.circular_dependencies == 0:
            score += 10
        elif self.dependencies.circular_dependencies < 5:
            score += 5

        # Documentation (25 points)
        score += self.documentation.documented_ratio * 20
        if self.documentation.readme_exists:
            score += 5

        # Complexity (30 points)
        if self.complexity.complexity_rating == "low":
            score += 30
        elif self.complexity.complexity_rating == "medium":
            score += 20
        elif self.complexity.complexity_rating == "high":
            score += 10
        # critical = 0 points

        return min(100, score)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "project_id": self.project_id,
            "repository_path": self.repository_path,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "technology": self.technology.to_dict(),
            "dependencies": self.dependencies.to_dict(),
            "documentation": self.documentation.to_dict(),
            "complexity": self.complexity.to_dict(),
            "analysis_score": round(self.analysis_score, 1),
            "is_successful": self.is_successful,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def to_llm_context(self) -> str:
        """
        Generate concise context string for LLM analysis.

        This is optimized for token efficiency while providing
        essential information for LLM-based code analysis.
        """
        lines = [
            f"## Code Analysis Summary",
            f"Repository: {self.repository_path}",
            f"",
            f"### Technology Stack",
            f"- Primary: {self.technology.primary_stack or 'Unknown'}",
        ]

        if self.technology.secondary_stacks:
            lines.append(f"- Secondary: {', '.join(self.technology.secondary_stacks[:5])}")

        if self.technology.database_type:
            lines.append(f"- Database: {self.technology.database_type}")

        lines.extend([
            f"- Files: {self.technology.total_files:,}",
            f"- Lines of Code: {self.technology.total_loc:,}",
            f"",
            f"### Dependencies",
            f"- Modules: {self.dependencies.module_count}",
            f"- Internal deps: {self.dependencies.internal_dependencies}",
            f"- External deps: {self.dependencies.external_dependencies}",
            f"- Circular deps: {self.dependencies.circular_dependencies}",
            f"- Coupling: {'High' if self.dependencies.coupling_score > 0.7 else 'Medium' if self.dependencies.coupling_score > 0.4 else 'Low'}",
        ])

        if self.dependencies.hub_modules:
            lines.append(f"- Hub modules: {', '.join(self.dependencies.hub_modules[:5])}")

        lines.extend([
            f"",
            f"### Complexity",
            f"- Rating: {self.complexity.complexity_rating.upper()}",
            f"- Avg cyclomatic: {self.complexity.avg_cyclomatic:.1f}",
            f"- Functions: {self.complexity.total_functions}",
            f"- High complexity: {self.complexity.high_complexity_count}",
            f"",
            f"### Documentation",
            f"- Coverage: {self.documentation.documented_ratio*100:.0f}%",
            f"- Has README: {'Yes' if self.documentation.readme_exists else 'No'}",
            f"- Diagrams: {self.documentation.diagram_count}",
        ])

        return "\n".join(lines)


class CodeAnalysisAggregatorService:
    """
    Aggregates multiple code analysis services into a unified result.

    This service runs locally (no LLM costs) and provides the foundation
    for the Deep Extraction Pipeline's tier-aware LLM analysis.

    Usage:
        service = CodeAnalysisAggregatorService(db)
        result = await service.analyze(
            project_id=1,
            repository_path="/opt/projects/legacy-app"
        )

        # Use result for LLM analysis
        llm_context = result.to_llm_context()
    """

    def __init__(self, db: Session):
        """Initialize aggregator with database session."""
        self.db = db
        # StackDetectionService is created on-demand with repo_path
        self.dependency_service = DependencyGraphService()
        self.codewiki_service = CodeWikiService(db)

    async def analyze(
        self,
        project_id: int,
        repository_path: str,
        branch: str = "main",
        include_codewiki: bool = True,
        timeout_seconds: int = 300,
    ) -> AggregatedAnalysis:
        """
        Run complete aggregated analysis on a repository.

        Args:
            project_id: Project ID for association
            repository_path: Path to repository
            branch: Git branch (for CodeWiki)
            include_codewiki: Whether to run CodeWiki analysis (slower)
            timeout_seconds: Maximum analysis time

        Returns:
            AggregatedAnalysis with all results
        """
        start_time = time.time()
        result = AggregatedAnalysis(
            project_id=project_id,
            repository_path=repository_path,
        )

        # Validate path exists
        if not Path(repository_path).exists():
            result.errors.append(f"Repository path not found: {repository_path}")
            return result

        try:
            # Run analyses - can be parallelized
            tasks = [
                self._analyze_stack(repository_path, result),
                self._analyze_dependencies(repository_path, result),
            ]

            if include_codewiki:
                tasks.append(self._analyze_codewiki(project_id, repository_path, branch, result))

            # Run with timeout
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout_seconds
            )

        except asyncio.TimeoutError:
            result.errors.append(f"Analysis timed out after {timeout_seconds}s")
        except Exception as e:
            logger.exception("Unexpected error in aggregated analysis")
            result.errors.append(f"Analysis error: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Aggregated analysis complete: project={project_id}, "
            f"duration={result.duration_ms}ms, score={result.analysis_score:.1f}, "
            f"errors={len(result.errors)}"
        )

        return result

    async def _analyze_stack(
        self,
        repository_path: str,
        result: AggregatedAnalysis
    ) -> None:
        """Run stack detection analysis."""
        try:
            stack_service = StackDetectionService(repository_path)
            scan = stack_service.scan()
            result.stack_scan_result = scan

            # Extract technology profile
            result.technology = TechnologyProfile(
                primary_stack=scan.primary_stack,
                secondary_stacks=scan.secondary_stacks,
                database_type=scan.database_type,
                languages=self._extract_languages(scan),
                frameworks=list(scan.stack_detections.keys()),
                total_files=scan.total_files,
                total_loc=scan.total_loc,
            )

            # Extract complexity profile
            if scan.complexity:
                result.complexity = self._build_complexity_profile(scan.complexity)

        except Exception as e:
            logger.warning(f"Stack detection failed: {e}")
            result.warnings.append(f"Stack detection partial: {str(e)}")

    async def _analyze_dependencies(
        self,
        repository_path: str,
        result: AggregatedAnalysis
    ) -> None:
        """Run dependency graph analysis."""
        try:
            dep_result = self.dependency_service.analyze_directory(repository_path)
            result.dependency_graph_result = dep_result

            metrics = dep_result.metrics
            result.dependencies = DependencyProfile(
                module_count=metrics.total_modules,
                edge_count=metrics.total_edges,
                circular_dependencies=metrics.circular_dependencies,
                entry_points=metrics.entry_points,
                hub_modules=metrics.hub_modules,
                external_dependencies=metrics.external_dependencies,
                internal_dependencies=metrics.internal_dependencies,
                instability_avg=metrics.instability_avg,
                coupling_score=self._calculate_coupling_score(metrics),
            )

        except Exception as e:
            logger.warning(f"Dependency analysis failed: {e}")
            result.warnings.append(f"Dependency analysis partial: {str(e)}")

    async def _analyze_codewiki(
        self,
        project_id: int,
        repository_path: str,
        branch: str,
        result: AggregatedAnalysis
    ) -> None:
        """Run CodeWiki documentation analysis."""
        try:
            analysis = self.codewiki_service.create_analysis(
                project_id=project_id,
                repository_path=repository_path,
                branch=branch,
            )
            result.codewiki_analysis_id = analysis.id

            # Check for README
            readme_exists = any(
                (Path(repository_path) / f).exists()
                for f in ["README.md", "README.rst", "README.txt", "README"]
            )

            # Build documentation profile
            result.documentation = DocumentationProfile(
                module_count=0,  # Will be updated after full analysis
                documented_ratio=0.0,
                diagram_count=0,
                top_modules=[],
                architecture_detected=False,
                readme_exists=readme_exists,
            )

        except Exception as e:
            logger.warning(f"CodeWiki analysis failed: {e}")
            result.warnings.append(f"Documentation analysis partial: {str(e)}")

    def _extract_languages(self, scan: ScanResult) -> Dict[str, int]:
        """Extract language counts from scan result."""
        return dict(scan.file_inventory) if scan.file_inventory else {}

    def _build_complexity_profile(self, metrics: ComplexityMetrics) -> ComplexityProfile:
        """Build complexity profile from Lizard metrics."""
        # Determine rating based on cyclomatic complexity
        if metrics.avg_cyclomatic <= 5:
            rating = "low"
        elif metrics.avg_cyclomatic <= 10:
            rating = "medium"
        elif metrics.avg_cyclomatic <= 20:
            rating = "high"
        else:
            rating = "critical"

        return ComplexityProfile(
            avg_cyclomatic=metrics.avg_cyclomatic,
            max_cyclomatic=metrics.max_cyclomatic,
            total_functions=metrics.total_functions,
            high_complexity_count=metrics.high_complexity_count,
            complexity_rating=rating,
        )

    def _calculate_coupling_score(self, metrics: DependencyMetrics) -> float:
        """
        Calculate overall coupling score 0-1.

        Based on:
        - Afferent/efferent coupling ratios
        - Circular dependencies
        - Hub module concentration
        """
        if metrics.total_modules == 0:
            return 0.0

        # Base score from coupling averages
        base = (metrics.afferent_coupling_avg + metrics.efferent_coupling_avg) / 20.0

        # Penalty for circular dependencies
        circular_penalty = min(metrics.circular_dependencies * 0.1, 0.3)

        # Penalty for hub concentration
        hub_ratio = len(metrics.hub_modules) / metrics.total_modules
        hub_penalty = min(hub_ratio * 0.5, 0.2)

        score = min(1.0, base + circular_penalty + hub_penalty)
        return score

    async def get_analysis_summary(
        self,
        project_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent analysis summary for a project.

        Args:
            project_id: Project ID

        Returns:
            Summary dict or None if no analysis exists
        """
        # Query latest CodeWiki analysis for this project
        analysis = (
            self.db.query(CodeWikiAnalysis)
            .filter(CodeWikiAnalysis.project_id == project_id)
            .order_by(CodeWikiAnalysis.created_at.desc())
            .first()
        )

        if not analysis:
            return None

        return {
            "project_id": project_id,
            "analysis_id": analysis.id,
            "repository_path": analysis.repository_path,
            "languages": analysis.languages_detected,
            "status": analysis.status.value if analysis.status else "unknown",
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        }


def get_aggregator_service(db: Session) -> CodeAnalysisAggregatorService:
    """Factory function for CodeAnalysisAggregatorService."""
    return CodeAnalysisAggregatorService(db)
