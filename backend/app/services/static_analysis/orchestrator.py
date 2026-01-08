# backend/app/services/static_analysis/orchestrator.py
"""
Static Analysis Orchestrator - Orchestrates Cycle 0 analysis.

Coordinates all static analysis components:
- ProgramSlicer: Dependency analysis
- VariableClassifier: Domain/implementation/control classification
- BusinessRuleExtractor: IF-THEN rule detection
- NFRDetector: Non-functional requirement patterns
- ComplianceChecker: Framework compliance checks

Part of Fase 15: Hybrid Static-LLM Extraction Pipeline
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio
import logging
from uuid import uuid4

from .program_slicer import ProgramSlicer, ProgramSlice, LanguageSupport
from .variable_classifier import VariableClassifier, VariableClassificationResult
from .business_rule_extractor import BusinessRuleExtractor, RuleExtractionResult
from .nfr_detector import NFRDetector, NFRReport
from .compliance_checker import ComplianceChecker, ComplianceReport, ComplianceFramework

logger = logging.getLogger(__name__)


@dataclass
class StaticAnalysisConfig:
    """Configuration for static analysis."""
    enable_slicing: bool = True
    enable_variable_classification: bool = True
    enable_business_rules: bool = True
    enable_nfr_detection: bool = True
    enable_compliance: bool = True
    compliance_frameworks: List[str] = field(default_factory=list)
    custom_domain_terms: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=lambda: ["python"])
    max_files: int = 1000  # Maximum files to process
    include_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.js", "*.ts", "*.cs", "*.sql"])
    exclude_patterns: List[str] = field(default_factory=lambda: ["*test*", "*spec*", "node_modules/*", "__pycache__/*"])


@dataclass
class StaticAnalysisResult:
    """Complete result of Cycle 0 static analysis."""
    id: str
    project_id: int
    started_at: datetime
    completed_at: datetime

    # Component results
    slices: List[ProgramSlice] = field(default_factory=list)
    variable_classification: Optional[VariableClassificationResult] = None
    business_rules: Optional[RuleExtractionResult] = None
    nfr_report: Optional[NFRReport] = None
    compliance_report: Optional[ComplianceReport] = None

    # Summary metrics
    total_files_analyzed: int = 0
    total_lines_of_code: int = 0
    domain_coverage: float = 0.0
    nfr_coverage: float = 0.0
    compliance_score: float = 0.0

    # For LLM enrichment
    high_confidence_findings: List[Dict] = field(default_factory=list)
    low_confidence_findings: List[Dict] = field(default_factory=list)

    # Errors encountered
    errors: List[Dict] = field(default_factory=list)

    def to_llm_context(self) -> Dict[str, Any]:
        """Convert to context for LLM enrichment (Cycles 1-5)."""
        return {
            "static_analysis_summary": {
                "id": self.id,
                "files_analyzed": self.total_files_analyzed,
                "lines_of_code": self.total_lines_of_code,
                "domain_coverage": self.domain_coverage,
                "nfr_coverage": self.nfr_coverage,
                "compliance_score": self.compliance_score,
            },
            "business_rules": [
                {
                    "id": r.id,
                    "type": r.rule_type.value,
                    "condition": r.condition,
                    "action": r.action,
                    "natural_language": r.natural_language,
                    "confidence": r.confidence,
                    "source_file": r.source_file,
                    "source_lines": r.source_lines,
                }
                for r in (self.business_rules.rules if self.business_rules else [])
            ],
            "nfr_detections": [
                {
                    "id": d.id,
                    "category": d.category.value,
                    "description": d.description,
                    "confidence": d.confidence,
                    "source_file": d.source_file,
                    "compliance_relevance": d.compliance_relevance,
                }
                for d in (self.nfr_report.detections if self.nfr_report else [])
            ],
            "compliance_violations": [
                {
                    "requirement_id": v.requirement.id,
                    "framework": v.requirement.framework.value,
                    "title": v.requirement.title,
                    "violation_type": v.violation_type,
                    "file_path": v.file_path,
                    "remediation": v.remediation,
                    "severity": v.requirement.severity,
                }
                for v in (self.compliance_report.violations if self.compliance_report else [])
            ],
            "domain_variables": (
                self.variable_classification.domain_variables
                if self.variable_classification else []
            ),
            "high_confidence_findings": self.high_confidence_findings,
            "low_confidence_findings": self.low_confidence_findings,
        }

    def to_summary(self) -> Dict[str, Any]:
        """Get a summary of the analysis results."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "duration_seconds": (self.completed_at - self.started_at).total_seconds(),
            "files_analyzed": self.total_files_analyzed,
            "lines_of_code": self.total_lines_of_code,
            "business_rules_found": len(self.business_rules.rules) if self.business_rules else 0,
            "nfr_detections": len(self.nfr_report.detections) if self.nfr_report else 0,
            "compliance_violations": len(self.compliance_report.violations) if self.compliance_report else 0,
            "domain_coverage": round(self.domain_coverage, 2),
            "nfr_coverage": round(self.nfr_coverage, 2),
            "compliance_score": round(self.compliance_score, 2),
            "errors_count": len(self.errors),
        }


class StaticAnalysisOrchestrator:
    """
    Orchestrates Cycle 0: Static Analysis for all extraction tiers.

    This is the foundation layer that provides deterministic analysis
    before LLM enrichment (Cycles 1-5).
    """

    def __init__(self, db_session=None):
        """
        Initialize orchestrator.

        Args:
            db_session: Optional database session for persisting results
        """
        self.db = db_session

    async def run_analysis(self,
                           project_id: int,
                           files: Dict[str, str],
                           config: StaticAnalysisConfig) -> StaticAnalysisResult:
        """
        Run complete static analysis pipeline.

        Args:
            project_id: Project identifier
            files: Dict mapping file paths to source code content
            config: Configuration for the analysis

        Returns:
            StaticAnalysisResult with all component results
        """
        analysis_id = str(uuid4())
        started_at = datetime.utcnow()

        logger.info(f"Starting static analysis {analysis_id} for project {project_id}")
        logger.info(f"Analyzing {len(files)} files")

        result = StaticAnalysisResult(
            id=analysis_id,
            project_id=project_id,
            started_at=started_at,
            completed_at=started_at,  # Will be updated
            total_files_analyzed=len(files),
            total_lines_of_code=sum(source.count('\n') + 1 for source in files.values())
        )

        # Collect all variables for classification
        all_variables = set()

        # Initialize components
        variable_classifier = VariableClassifier(
            custom_domain_terms=config.custom_domain_terms
        )
        business_rule_extractor = BusinessRuleExtractor(
            variable_classifier=variable_classifier if config.enable_variable_classification else None
        )
        nfr_detector = NFRDetector()
        compliance_checker = ComplianceChecker()

        # Configure compliance frameworks
        if config.enable_compliance and config.compliance_frameworks:
            for fw_name in config.compliance_frameworks:
                try:
                    framework = ComplianceFramework(fw_name)
                    compliance_checker.add_framework(framework)
                except ValueError:
                    logger.warning(f"Unknown compliance framework: {fw_name}")

        # Run analyses in parallel where possible
        tasks = []

        # 1. Business rule extraction
        if config.enable_business_rules:
            tasks.append(("business_rules", business_rule_extractor.extract_all(files)))

        # 2. NFR detection
        if config.enable_nfr_detection:
            tasks.append(("nfr_report", nfr_detector.detect_all(files)))

        # 3. Compliance checking
        if config.enable_compliance and compliance_checker.active_frameworks:
            tasks.append(("compliance_report", compliance_checker.check_compliance(files)))

        # Execute parallel tasks
        task_results = {}
        for name, coro in tasks:
            try:
                task_results[name] = await coro
            except Exception as e:
                logger.error(f"Error in {name}: {e}")
                result.errors.append({
                    "component": name,
                    "error": str(e)
                })

        # Assign results
        if "business_rules" in task_results:
            result.business_rules = task_results["business_rules"]
            # Collect variables from rules
            for rule in result.business_rules.rules:
                all_variables.update(rule.variables_involved)

        if "nfr_report" in task_results:
            result.nfr_report = task_results["nfr_report"]
            result.nfr_coverage = result.nfr_report.coverage_score

        if "compliance_report" in task_results:
            result.compliance_report = task_results["compliance_report"]
            result.compliance_score = result.compliance_report.compliance_score

        # 4. Variable classification (after we've collected variables)
        if config.enable_variable_classification and all_variables:
            try:
                result.variable_classification = variable_classifier.classify_all(list(all_variables))
                result.domain_coverage = result.variable_classification.domain_coverage
            except Exception as e:
                logger.error(f"Error in variable classification: {e}")
                result.errors.append({
                    "component": "variable_classification",
                    "error": str(e)
                })

        # 5. Program slicing (optional, run if needed)
        if config.enable_slicing:
            try:
                result.slices = await self._run_slicing(files, config.languages)
            except Exception as e:
                logger.error(f"Error in program slicing: {e}")
                result.errors.append({
                    "component": "slicing",
                    "error": str(e)
                })

        # Categorize findings by confidence
        self._categorize_findings(result)

        result.completed_at = datetime.utcnow()

        logger.info(f"Completed static analysis {analysis_id}")
        logger.info(f"Found {len(result.business_rules.rules) if result.business_rules else 0} business rules")
        logger.info(f"Found {len(result.nfr_report.detections) if result.nfr_report else 0} NFR detections")
        logger.info(f"Found {len(result.compliance_report.violations) if result.compliance_report else 0} compliance violations")

        # Persist results if database session available
        if self.db:
            await self._persist_results(result)

        return result

    async def _run_slicing(self, files: Dict[str, str], languages: List[str]) -> List[ProgramSlice]:
        """Run program slicing analysis."""
        slices = []

        # Group files by language
        file_groups: Dict[LanguageSupport, List[str]] = {}
        for file_path in files.keys():
            lang = self._detect_language(file_path)
            if lang:
                file_groups.setdefault(lang, []).append(file_path)

        # Run slicer for each language
        for lang, lang_files in file_groups.items():
            try:
                slicer = ProgramSlicer(lang)
                await slicer.build_dependency_graph(lang_files)

                # Get entry points and compute slices for them
                if slicer.dependency_graph:
                    for entry_point in slicer.dependency_graph.entry_points[:10]:  # Limit
                        node = slicer.dependency_graph.nodes.get(entry_point)
                        if node and node.variables_defined:
                            for var in list(node.variables_defined)[:5]:  # Limit
                                from .program_slicer import SliceCriterion
                                criterion = SliceCriterion(
                                    file_path=node.file_path,
                                    line_number=node.line_start,
                                    variable_name=var
                                )
                                slice_result = await slicer.compute_slice(criterion)
                                slices.append(slice_result)
            except Exception as e:
                logger.warning(f"Slicing failed for {lang.value}: {e}")

        return slices

    def _detect_language(self, file_path: str) -> Optional[LanguageSupport]:
        """Detect programming language from file extension."""
        ext_map = {
            '.py': LanguageSupport.PYTHON,
            '.js': LanguageSupport.JAVASCRIPT,
            '.ts': LanguageSupport.TYPESCRIPT,
            '.cs': LanguageSupport.CSHARP,
            '.vb': LanguageSupport.VBNET,
            '.asp': LanguageSupport.ASP_CLASSIC,
            '.sql': LanguageSupport.SQL,
        }
        for ext, lang in ext_map.items():
            if file_path.lower().endswith(ext):
                return lang
        return None

    def _categorize_findings(self, result: StaticAnalysisResult):
        """Categorize findings by confidence level."""
        CONFIDENCE_THRESHOLD = 0.725  # 72.5% as specified

        # Business rules
        if result.business_rules:
            for rule in result.business_rules.rules:
                finding = {
                    "type": "business_rule",
                    "id": rule.id,
                    "rule_type": rule.rule_type.value,
                    "natural_language": rule.natural_language,
                    "confidence": rule.confidence,
                    "source_file": rule.source_file,
                }
                if rule.confidence >= CONFIDENCE_THRESHOLD:
                    result.high_confidence_findings.append(finding)
                else:
                    result.low_confidence_findings.append(finding)

        # NFR detections
        if result.nfr_report:
            for detection in result.nfr_report.detections:
                finding = {
                    "type": "nfr",
                    "id": detection.id,
                    "category": detection.category.value,
                    "description": detection.description,
                    "confidence": detection.confidence,
                    "source_file": detection.source_file,
                }
                if detection.confidence >= CONFIDENCE_THRESHOLD:
                    result.high_confidence_findings.append(finding)
                else:
                    result.low_confidence_findings.append(finding)

        # Compliance violations (always high priority)
        if result.compliance_report:
            for violation in result.compliance_report.violations:
                finding = {
                    "type": "compliance_violation",
                    "requirement_id": violation.requirement.id,
                    "framework": violation.requirement.framework.value,
                    "violation_type": violation.violation_type,
                    "severity": violation.requirement.severity,
                    "file_path": violation.file_path,
                    "confidence": 1.0,  # Compliance violations are deterministic
                }
                result.high_confidence_findings.append(finding)

    async def _persist_results(self, result: StaticAnalysisResult):
        """Persist analysis results to database."""
        # This would integrate with the database models
        # For now, just log
        logger.info(f"Persisting results for analysis {result.id}")

    def get_conflict_candidates(self, result: StaticAnalysisResult) -> List[Dict]:
        """
        Get findings that may conflict with LLM analysis.

        These are low-confidence static findings that LLM should validate,
        and high-confidence findings where LLM disagreement should trigger review.
        """
        candidates = []

        # Low confidence findings need LLM validation
        for finding in result.low_confidence_findings:
            candidates.append({
                **finding,
                "review_reason": "Low static confidence - needs LLM validation",
                "action": "validate"
            })

        # High confidence findings where LLM might disagree
        for finding in result.high_confidence_findings:
            if finding["type"] != "compliance_violation":  # Compliance is deterministic
                candidates.append({
                    **finding,
                    "review_reason": "High static confidence - flag if LLM disagrees",
                    "action": "monitor"
                })

        return candidates


# Factory function for creating orchestrator
def create_orchestrator(db_session=None) -> StaticAnalysisOrchestrator:
    """Create a new StaticAnalysisOrchestrator instance."""
    return StaticAnalysisOrchestrator(db_session)
