# backend/app/services/static_analysis/tier_orchestrator.py
"""
Tier-Aware Extraction Orchestrator - Coordinates hybrid business rule extraction.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline (Phase 2.5)

Features:
- Coordinates Tier 1 (AST), Tier 2 (Regex), and Tier 3 (LLM) extraction
- Customer tier-aware provider selection
- Automatic confidence boosting via LLM validation
- Premium synthesis for high-value projects

Pipeline Flow:
1. Static Extraction (AST/Regex) - Always runs
2. LLM Classification (BASIC+) - Validates ambiguous rules
3. LLM Extraction (STANDARD+) - Extracts from comments/messages
4. Multi-LLM Validation (PROFESSIONAL+) - Cross-validation
5. Premium Synthesis (PREMIUM) - Final Claude Opus review
"""

import logging
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

from .extraction_models import (
    BusinessRule,
    RuleType,
    ExtractionTier,
    ExtractionMethod,
    Language,
    ExtractionResult,
    MultiFileExtractionResult,
)
from .extractor_factory import ExtractorFactory
from .llm_classifier import LLMRuleClassifier
from .llm_extractor import LLMRuleExtractor
from .multi_llm_validator import MultiLLMValidator, PremiumSynthesizer

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationMetrics:
    """Metrics from the orchestration process."""
    # Extraction counts
    static_rules_extracted: int = 0
    llm_rules_extracted: int = 0
    total_rules: int = 0

    # Validation counts
    rules_classified: int = 0
    rules_confirmed: int = 0
    rules_rejected: int = 0

    # Multi-LLM validation
    multi_llm_validated: int = 0
    consensus_reached: int = 0

    # Premium synthesis
    premium_synthesis_performed: bool = False

    # Performance
    static_extraction_ms: int = 0
    llm_classification_ms: int = 0
    llm_extraction_ms: int = 0
    multi_llm_validation_ms: int = 0
    premium_synthesis_ms: int = 0
    total_ms: int = 0

    # Cost
    total_tokens: int = 0
    total_cost_cents: float = 0.0

    # Quality
    average_confidence: float = 0.0
    high_confidence_rules: int = 0  # Rules with confidence > 0.8


@dataclass
class OrchestrationResult:
    """Result of the orchestrated extraction."""
    rules: List[BusinessRule]
    metrics: OrchestrationMetrics
    tier_used: ExtractionTier
    project_id: Optional[int] = None
    base_path: str = ""
    synthesis_result: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class TierOrchestrator:
    """
    Orchestrates the hybrid business rule extraction pipeline.

    Coordinates:
    - Static extraction (always)
    - LLM classification (BASIC+)
    - LLM extraction (STANDARD+)
    - Multi-LLM validation (PROFESSIONAL+)
    - Premium synthesis (PREMIUM)
    """

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.STANDARD,
        project_id: Optional[int] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            extraction_tier: Customer tier determining LLM access
            project_id: Optional project ID for tracking
        """
        self.extraction_tier = extraction_tier
        self.project_id = project_id

        # Create components
        self.factory = ExtractorFactory(
            extraction_tier=extraction_tier,
            project_id=project_id,
        )
        self.classifier = LLMRuleClassifier(extraction_tier=extraction_tier)
        self.extractor = LLMRuleExtractor(extraction_tier=extraction_tier)
        self.validator = MultiLLMValidator(extraction_tier=extraction_tier)
        self.synthesizer = PremiumSynthesizer()

    async def extract_from_file(
        self,
        file_path: str,
        enable_llm: bool = True,
    ) -> OrchestrationResult:
        """
        Extract business rules from a single file using full pipeline.

        Args:
            file_path: Path to the file
            enable_llm: Whether to use LLM features (if tier allows)

        Returns:
            OrchestrationResult with all extracted rules
        """
        start_time = time.time()
        metrics = OrchestrationMetrics()
        all_rules: List[BusinessRule] = []
        errors: List[str] = []
        warnings: List[str] = []

        # Detect language
        language = self.factory.detect_language(file_path)
        if not language:
            return OrchestrationResult(
                rules=[],
                metrics=metrics,
                tier_used=self.extraction_tier,
                base_path=file_path,
                errors=[f"Unsupported file type: {file_path}"],
            )

        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                source_code = f.read()
        except Exception as e:
            return OrchestrationResult(
                rules=[],
                metrics=metrics,
                tier_used=self.extraction_tier,
                base_path=file_path,
                errors=[f"Failed to read file: {e}"],
            )

        # Step 1: Static Extraction (always runs)
        static_start = time.time()
        try:
            static_result = await self.factory.extract_from_file(file_path)
            if static_result:
                all_rules.extend(static_result.business_rules)
                metrics.static_rules_extracted = len(static_result.business_rules)
        except Exception as e:
            errors.append(f"Static extraction failed: {e}")
            logger.error(f"Static extraction failed for {file_path}: {e}")

        metrics.static_extraction_ms = int((time.time() - static_start) * 1000)

        # Step 2: LLM Classification (BASIC+)
        if enable_llm and self.extraction_tier != ExtractionTier.FREE:
            classification_start = time.time()
            try:
                low_confidence = [r for r in all_rules if r.confidence < 0.75]
                if low_confidence:
                    classifications = await self.classifier.classify_batch(
                        low_confidence,
                        confidence_threshold=0.75,
                        max_rules=30,
                    )
                    metrics.rules_classified = len(classifications)
                    metrics.rules_confirmed = sum(
                        1 for _, c in classifications
                        if c.is_business_rule
                    )
                    metrics.rules_rejected = sum(
                        1 for _, c in classifications
                        if not c.is_business_rule
                    )

                    # Remove rejected rules
                    all_rules = self.classifier.filter_rejected_rules(
                        all_rules,
                        classifications,
                    )
            except Exception as e:
                warnings.append(f"LLM classification failed: {e}")
                logger.warning(f"LLM classification failed: {e}")

            metrics.llm_classification_ms = int((time.time() - classification_start) * 1000)

        # Step 3: LLM Extraction from comments/messages (STANDARD+)
        if (enable_llm and
            self.extraction_tier in [
                ExtractionTier.STANDARD,
                ExtractionTier.PROFESSIONAL,
                ExtractionTier.PREMIUM,
            ]):
            extraction_start = time.time()
            try:
                # Extract from comments
                comment_result = await self.extractor.extract_rules_from_comments(
                    source_code,
                    language,
                    file_path,
                )

                # Extract from user messages
                message_result = await self.extractor.extract_rules_from_messages(
                    source_code,
                    language,
                    file_path,
                )

                # Convert to BusinessRules
                llm_extracted = comment_result.rules + message_result.rules
                if llm_extracted:
                    llm_rules = self.extractor.convert_to_business_rules(
                        llm_extracted,
                        file_path,
                        language,
                        id_prefix=f"BR-LLM-{Path(file_path).stem}",
                    )
                    all_rules.extend(llm_rules)
                    metrics.llm_rules_extracted = len(llm_rules)

                    # Track costs
                    metrics.total_tokens += (
                        comment_result.tokens_used + message_result.tokens_used
                    )
                    metrics.total_cost_cents += (
                        comment_result.cost_cents + message_result.cost_cents
                    )

            except Exception as e:
                warnings.append(f"LLM extraction failed: {e}")
                logger.warning(f"LLM extraction failed: {e}")

            metrics.llm_extraction_ms = int((time.time() - extraction_start) * 1000)

        # Step 4: Multi-LLM Validation (PROFESSIONAL+)
        if (enable_llm and
            self.extraction_tier in [
                ExtractionTier.PROFESSIONAL,
                ExtractionTier.PREMIUM,
            ]):
            validation_start = time.time()
            try:
                # Validate remaining low-confidence rules
                candidates = [r for r in all_rules if 0.6 < r.confidence < 0.8]
                if candidates:
                    validations = await self.validator.validate_batch(
                        candidates,
                        confidence_threshold=0.8,
                        max_rules=15,
                    )
                    metrics.multi_llm_validated = len(validations)
                    metrics.consensus_reached = sum(
                        1 for _, c in validations if c.consensus_reached
                    )

                    # Track costs from validation
                    for _, consensus in validations:
                        metrics.total_tokens += consensus.total_tokens
                        metrics.total_cost_cents += consensus.total_cost_cents

            except Exception as e:
                warnings.append(f"Multi-LLM validation failed: {e}")
                logger.warning(f"Multi-LLM validation failed: {e}")

            metrics.multi_llm_validation_ms = int((time.time() - validation_start) * 1000)

        # Step 5: Premium Synthesis (PREMIUM only)
        synthesis_result = None
        if enable_llm and self.extraction_tier == ExtractionTier.PREMIUM:
            synthesis_start = time.time()
            try:
                synthesis_result = await self.synthesizer.synthesize(
                    all_rules,
                    project_name=f"Project {self.project_id or 'Unknown'}",
                )
                metrics.premium_synthesis_performed = True

                if "tokens_used" in synthesis_result:
                    metrics.total_tokens += synthesis_result["tokens_used"]
                if "cost_cents" in synthesis_result:
                    metrics.total_cost_cents += synthesis_result["cost_cents"]

            except Exception as e:
                warnings.append(f"Premium synthesis failed: {e}")
                logger.warning(f"Premium synthesis failed: {e}")

            metrics.premium_synthesis_ms = int((time.time() - synthesis_start) * 1000)

        # Calculate final metrics
        metrics.total_rules = len(all_rules)
        metrics.total_ms = int((time.time() - start_time) * 1000)

        if all_rules:
            confidences = [r.confidence for r in all_rules]
            metrics.average_confidence = sum(confidences) / len(confidences)
            metrics.high_confidence_rules = sum(1 for c in confidences if c >= 0.8)

        return OrchestrationResult(
            rules=all_rules,
            metrics=metrics,
            tier_used=self.extraction_tier,
            project_id=self.project_id,
            base_path=file_path,
            synthesis_result=synthesis_result,
            errors=errors,
            warnings=warnings,
        )

    async def extract_from_directory(
        self,
        directory: str,
        recursive: bool = True,
        languages: Optional[List[Language]] = None,
        enable_llm: bool = True,
    ) -> OrchestrationResult:
        """
        Extract business rules from all files in a directory.

        Args:
            directory: Directory path
            recursive: Scan subdirectories
            languages: Optional language filter
            enable_llm: Whether to use LLM features

        Returns:
            Aggregated OrchestrationResult
        """
        start_time = time.time()
        all_rules: List[BusinessRule] = []
        aggregated_metrics = OrchestrationMetrics()
        all_errors: List[str] = []
        all_warnings: List[str] = []

        path = Path(directory)
        if not path.exists():
            return OrchestrationResult(
                rules=[],
                metrics=aggregated_metrics,
                tier_used=self.extraction_tier,
                base_path=directory,
                errors=[f"Directory not found: {directory}"],
            )

        # Find all supported files
        pattern = '**/*' if recursive else '*'
        supported_extensions = self.factory.get_supported_extensions()

        files_to_process = []
        for file_path in path.glob(pattern):
            if not file_path.is_file():
                continue

            # Check extension
            file_lower = str(file_path).lower()
            for ext in supported_extensions:
                if file_lower.endswith(ext):
                    # Filter by language if specified
                    if languages:
                        lang = self.factory.detect_language(str(file_path))
                        if lang and lang in languages:
                            files_to_process.append(str(file_path))
                    else:
                        files_to_process.append(str(file_path))
                    break

        logger.info(
            f"Processing {len(files_to_process)} files with tier {self.extraction_tier.value}"
        )

        # Process each file
        for file_path in files_to_process:
            try:
                result = await self.extract_from_file(file_path, enable_llm)
                all_rules.extend(result.rules)
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)

                # Aggregate metrics
                aggregated_metrics.static_rules_extracted += result.metrics.static_rules_extracted
                aggregated_metrics.llm_rules_extracted += result.metrics.llm_rules_extracted
                aggregated_metrics.rules_classified += result.metrics.rules_classified
                aggregated_metrics.rules_confirmed += result.metrics.rules_confirmed
                aggregated_metrics.rules_rejected += result.metrics.rules_rejected
                aggregated_metrics.multi_llm_validated += result.metrics.multi_llm_validated
                aggregated_metrics.consensus_reached += result.metrics.consensus_reached
                aggregated_metrics.total_tokens += result.metrics.total_tokens
                aggregated_metrics.total_cost_cents += result.metrics.total_cost_cents
                aggregated_metrics.static_extraction_ms += result.metrics.static_extraction_ms
                aggregated_metrics.llm_classification_ms += result.metrics.llm_classification_ms
                aggregated_metrics.llm_extraction_ms += result.metrics.llm_extraction_ms
                aggregated_metrics.multi_llm_validation_ms += result.metrics.multi_llm_validation_ms

            except Exception as e:
                all_errors.append(f"Failed to process {file_path}: {e}")
                logger.error(f"Failed to process {file_path}: {e}")

        # Final metrics
        aggregated_metrics.total_rules = len(all_rules)
        aggregated_metrics.total_ms = int((time.time() - start_time) * 1000)

        if all_rules:
            confidences = [r.confidence for r in all_rules]
            aggregated_metrics.average_confidence = sum(confidences) / len(confidences)
            aggregated_metrics.high_confidence_rules = sum(
                1 for c in confidences if c >= 0.8
            )

        # Optional: Premium synthesis for directory results
        synthesis_result = None
        if (enable_llm and
            self.extraction_tier == ExtractionTier.PREMIUM and
            len(all_rules) > 0):
            try:
                synthesis_result = await self.synthesizer.synthesize(
                    all_rules,
                    project_name=f"Project {self.project_id or 'Unknown'}",
                )
                aggregated_metrics.premium_synthesis_performed = True
            except Exception as e:
                all_warnings.append(f"Premium synthesis failed: {e}")

        logger.info(
            f"Extraction complete: {aggregated_metrics.total_rules} rules, "
            f"avg confidence {aggregated_metrics.average_confidence:.1%}, "
            f"cost ${aggregated_metrics.total_cost_cents/100:.2f}"
        )

        return OrchestrationResult(
            rules=all_rules,
            metrics=aggregated_metrics,
            tier_used=self.extraction_tier,
            project_id=self.project_id,
            base_path=directory,
            synthesis_result=synthesis_result,
            errors=all_errors,
            warnings=all_warnings,
        )


# Convenience function
async def extract_with_orchestration(
    path: str,
    tier: ExtractionTier = ExtractionTier.STANDARD,
    project_id: Optional[int] = None,
    enable_llm: bool = True,
) -> OrchestrationResult:
    """
    Extract business rules using full orchestrated pipeline.

    Args:
        path: File or directory path
        tier: Customer extraction tier
        project_id: Optional project ID
        enable_llm: Whether to enable LLM features

    Returns:
        OrchestrationResult
    """
    orchestrator = TierOrchestrator(
        extraction_tier=tier,
        project_id=project_id,
    )

    p = Path(path)
    if p.is_file():
        return await orchestrator.extract_from_file(str(p), enable_llm)
    else:
        return await orchestrator.extract_from_directory(str(p), enable_llm=enable_llm)
