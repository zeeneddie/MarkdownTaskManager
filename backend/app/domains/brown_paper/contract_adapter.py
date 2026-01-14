# Brown Paper Contract Adapter
# Converts Brown Paper session data to AnalysisContract
#
# This adapter is THE key component that breaks the coupling between
# Brown Paper and Migration. It creates a standard AnalysisContract
# that Migration can consume without knowing about Brown Paper internals.
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 (Week 145-146)

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import logging

from ...contracts import (
    AnalysisContract,
    AnalysisSourceType,
    ProjectInfo,
    DomainSummary,
    ModuleSummary,
    EpicSummary,
    FeatureSummary,
    BusinessRuleSummary,
    StabilityInfo,
    StabilityCategorySummary,
    StabilityFindingSummary,
)
from ...models.brown_paper import (
    BrownPaperSession,
    BrownPaperAnalysis,
    BrownPaperConstitution,
    BrownPaperEpic,
)

logger = logging.getLogger(__name__)


class BrownPaperContractAdapter:
    """
    Adapter that converts Brown Paper output to AnalysisContract.

    Usage:
        adapter = BrownPaperContractAdapter()
        contract = adapter.to_contract(session, analysis, stability_result)

    The contract can then be:
    1. Stored in analysis_contracts table
    2. Passed to Migration service
    3. Used for Quality gate evaluation
    """

    def to_contract(
        self,
        session: BrownPaperSession,
        analysis: Optional[BrownPaperAnalysis] = None,
        constitution: Optional[BrownPaperConstitution] = None,
        stability_result: Optional[Dict[str, Any]] = None,
    ) -> AnalysisContract:
        """
        Convert Brown Paper session to AnalysisContract.

        Args:
            session: Brown Paper session with basic info
            analysis: Optional detailed analysis with modules and domains
            constitution: Optional constitution with epics
            stability_result: Optional stability analysis result

        Returns:
            AnalysisContract ready for storage or consumption
        """
        logger.info(f"Converting Brown Paper session {session.id} to AnalysisContract")

        # Create project info
        project = self._extract_project_info(session, analysis)

        # Extract domains
        domains = self._extract_domains(analysis)

        # Extract modules
        modules = self._extract_modules(analysis)

        # Extract epics
        epics = self._extract_epics(constitution)

        # Extract stability info
        stability = self._extract_stability_info(stability_result)

        # Create contract
        contract = AnalysisContract(
            analysis_id=str(uuid.uuid4()),
            source_type=AnalysisSourceType.BROWN_PAPER,
            source_id=str(session.id),
            project=project,
            domains=domains,
            modules=modules,
            stability=stability,
            epics=epics,
            business_rules=[],  # Brown Paper doesn't extract business rules yet
            created_at=datetime.now(timezone.utc),
            version="1.0",
        )

        logger.info(
            f"Created AnalysisContract {contract.analysis_id} with "
            f"{len(domains)} domains, {len(modules)} modules, {len(epics)} epics"
        )

        return contract

    def _extract_project_info(
        self,
        session: BrownPaperSession,
        analysis: Optional[BrownPaperAnalysis],
    ) -> ProjectInfo:
        """Extract project info from session and analysis."""
        lines_of_code = 0
        total_files = 0
        framework = ""
        primary_language = ""

        if analysis and analysis.modules:
            # Calculate totals from modules
            for module in analysis.modules:
                if isinstance(module, dict):
                    lines_of_code += module.get("lines_of_code", 0)
                    total_files += 1

            # Detect primary language from patterns
            if analysis.primary_patterns:
                for pattern in analysis.primary_patterns:
                    if isinstance(pattern, str):
                        if "fastapi" in pattern.lower():
                            framework = "FastAPI"
                            primary_language = "Python"
                        elif "django" in pattern.lower():
                            framework = "Django"
                            primary_language = "Python"
                        elif "asp" in pattern.lower():
                            framework = "Classic ASP"
                            primary_language = "VBScript"

        return ProjectInfo(
            name=session.application_name or "Unknown",
            path=session.root_path or "",
            description="",
            repository_url="",
            primary_language=primary_language,
            framework=framework,
            lines_of_code=lines_of_code,
            total_files=total_files or session.modules_count or 0,
        )

    def _extract_domains(
        self,
        analysis: Optional[BrownPaperAnalysis],
    ) -> List[DomainSummary]:
        """Extract domain summaries from analysis."""
        if not analysis or not analysis.domains:
            return []

        domains = []
        for domain_data in analysis.domains:
            if not isinstance(domain_data, dict):
                continue

            domain = DomainSummary(
                name=domain_data.get("name", "Unknown"),
                description=domain_data.get("description", ""),
                entities=domain_data.get("entities", []),
                use_cases=domain_data.get("use_cases", []),
                modules=domain_data.get("modules", []),
                estimated_complexity=domain_data.get("complexity", "medium"),
                estimated_fp=domain_data.get("estimated_fp", 0.0),
            )
            domains.append(domain)

        return domains

    def _extract_modules(
        self,
        analysis: Optional[BrownPaperAnalysis],
    ) -> List[ModuleSummary]:
        """Extract module summaries from analysis."""
        if not analysis or not analysis.modules:
            return []

        modules = []
        for module_data in analysis.modules:
            if not isinstance(module_data, dict):
                continue

            module = ModuleSummary(
                name=module_data.get("name", ""),
                path=module_data.get("path", ""),
                module_type=module_data.get("type", module_data.get("module_type", "")),
                complexity=module_data.get("complexity", "medium"),
                lines_of_code=module_data.get("lines_of_code", 0),
                classes=module_data.get("classes_count", len(module_data.get("classes", []))),
                functions=module_data.get("functions_count", len(module_data.get("functions", []))),
                dependencies=module_data.get("dependencies", []),
                domain=module_data.get("domain", ""),
            )
            modules.append(module)

        return modules

    def _extract_epics(
        self,
        constitution: Optional[BrownPaperConstitution],
    ) -> List[EpicSummary]:
        """Extract epic summaries from constitution."""
        if not constitution or not constitution.epics:
            return []

        epics = []
        for epic in constitution.epics:
            if not isinstance(epic, BrownPaperEpic):
                continue

            features = []
            if epic.features:
                for i, feature_data in enumerate(epic.features):
                    if isinstance(feature_data, dict):
                        feature = FeatureSummary(
                            feature_id=feature_data.get("id", f"FEAT-{i+1:03d}"),
                            title=feature_data.get("title", feature_data.get("name", "")),
                            description=feature_data.get("description", ""),
                            estimated_sp=feature_data.get("story_points", feature_data.get("points", 0)),
                            priority=feature_data.get("priority", "medium"),
                        )
                        features.append(feature)

            epic_summary = EpicSummary(
                epic_id=epic.epic_number or f"EPIC-{epic.id}",
                title=epic.name or "",
                description=epic.description or "",
                domain=epic.source_domain or "",
                estimated_fp=0.0,  # Can be calculated from features
                estimated_weeks=0.0,  # Can be calculated from complexity
                features=features,
                priority=self._map_priority(epic.priority),
                complexity=epic.complexity or "medium",
            )
            epics.append(epic_summary)

        return epics

    def _extract_stability_info(
        self,
        stability_result: Optional[Dict[str, Any]],
    ) -> StabilityInfo:
        """Extract stability info from stability analysis result."""
        if not stability_result:
            return StabilityInfo.empty()

        # Extract category summaries
        categories = {}
        categories_data = stability_result.get("categories", {})
        for cat_name, cat_data in categories_data.items():
            if isinstance(cat_data, dict):
                categories[cat_name] = StabilityCategorySummary(
                    category=cat_name,
                    issues_found=cat_data.get("issues_found", 0),
                    critical_count=cat_data.get("critical_count", 0),
                    high_count=cat_data.get("high_count", 0),
                    medium_count=cat_data.get("medium_count", 0),
                    low_count=cat_data.get("low_count", 0),
                )

        # Extract top findings (limit to 10 for contract size)
        top_findings = []
        all_findings = stability_result.get("all_findings", stability_result.get("findings", []))
        for finding_data in all_findings[:10]:
            if isinstance(finding_data, dict):
                finding = StabilityFindingSummary(
                    file_path=finding_data.get("file_path", ""),
                    line_number=finding_data.get("line_number", 0),
                    category=finding_data.get("category", ""),
                    severity=finding_data.get("severity", "LOW"),
                    description=finding_data.get("description", ""),
                    suggested_fix=finding_data.get("suggested_fix", ""),
                    confidence=finding_data.get("confidence", 1.0),
                )
                top_findings.append(finding)

        return StabilityInfo(
            overall_score=stability_result.get("overall_score", 100),
            overall_risk=stability_result.get("overall_risk", "LOW"),
            total_findings=stability_result.get("total_findings", 0),
            critical_count=stability_result.get("critical_count", 0),
            high_count=stability_result.get("high_count", 0),
            categories=categories,
            top_findings=top_findings,
            files_scanned=stability_result.get("total_files_scanned", 0),
            languages_analyzed=stability_result.get("languages_analyzed", []),
            scan_timestamp=datetime.now(timezone.utc),
        )

    def _map_priority(self, priority: Optional[int]) -> str:
        """Map numeric priority to string."""
        if priority is None:
            return "medium"
        if priority <= 1:
            return "critical"
        if priority <= 2:
            return "high"
        if priority <= 3:
            return "medium"
        return "low"

    # === Convenience Methods ===

    def from_session_with_relations(
        self,
        session: BrownPaperSession,
    ) -> AnalysisContract:
        """
        Create contract from session using its relationships.
        Assumes session has analysis and constitution loaded.
        """
        return self.to_contract(
            session=session,
            analysis=session.analysis if hasattr(session, "analysis") else None,
            constitution=session.constitution if hasattr(session, "constitution") else None,
        )

    def create_minimal_contract(
        self,
        session_id: str,
        project_name: str,
        project_path: str,
    ) -> AnalysisContract:
        """
        Create a minimal contract with just basic info.
        Useful for quick contract creation without full analysis.
        """
        return AnalysisContract.create_new(
            source_type=AnalysisSourceType.BROWN_PAPER,
            project_name=project_name,
            project_path=project_path,
            source_id=session_id,
        )
