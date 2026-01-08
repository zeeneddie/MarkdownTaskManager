# backend/app/services/orchestration/business_rule_workflow_integration.py
"""
Business Rule Workflow Integration - Phase 5 Agent Integration

Integrates hybrid business rule extraction with AI agent workflows.

Week 116: Track 2 - Phase 5 Agent & Workflow Integration (16 hours)

Features:
- BROWN_PAPER workflow hook for Miguel agent
- MIGRATION workflow hook for Miguel agent
- BACKLOG_GENERATION integration for Peter agent
- Agent context enrichment with extracted rules

Pipeline Flow:
1. Workflow starts (BROWN_PAPER, MIGRATION, or BACKLOG_GENERATION)
2. TierOrchestrator extracts business rules from source code
3. RuleCorrelationService detects entities and workflows
4. Context is prepared for the primary agent (Miguel or Peter)
5. Agent receives enriched context for intelligent analysis
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


# Workflow types that support business rule integration
RULE_INTEGRATED_WORKFLOWS = frozenset([
    "BROWN_PAPER",
    "MIGRATION",
    "BACKLOG_GENERATION",
    "QUALITY_AUDIT",
])


@dataclass
class RuleExtractionContext:
    """Context from business rule extraction for agent consumption."""
    # Summary statistics
    total_rules: int = 0
    high_confidence_rules: int = 0
    average_confidence: float = 0.0

    # Extracted entities
    entities: List[Dict[str, Any]] = field(default_factory=list)

    # Detected workflows (CRUD patterns)
    workflows: List[Dict[str, Any]] = field(default_factory=list)

    # Rules by type
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    authorization_rules: List[Dict[str, Any]] = field(default_factory=list)
    business_logic_rules: List[Dict[str, Any]] = field(default_factory=list)
    data_access_rules: List[Dict[str, Any]] = field(default_factory=list)

    # Technology insights
    detected_languages: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)
    database_patterns: List[str] = field(default_factory=list)

    # Relationships
    rule_relationships: List[Dict[str, Any]] = field(default_factory=list)

    # Extraction metadata
    extraction_tier: str = "STANDARD"
    extraction_time_ms: int = 0
    extraction_cost_cents: float = 0.0
    synthesis_result: Optional[Dict[str, Any]] = None

    # Errors and warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_agent_context(self, agent_name: str) -> Dict[str, Any]:
        """
        Convert to agent-specific context format.

        Args:
            agent_name: Name of the agent (miguel, peter, felix, etc.)

        Returns:
            Agent-specific context dict
        """
        base_context = {
            "rule_extraction": {
                "summary": {
                    "total_rules": self.total_rules,
                    "high_confidence_rules": self.high_confidence_rules,
                    "average_confidence": round(self.average_confidence, 2),
                    "tier": self.extraction_tier,
                },
                "entities": self.entities[:20],  # Top 20 entities
                "workflows": self.workflows[:10],  # Top 10 workflows
            }
        }

        agent_lower = agent_name.lower()

        if agent_lower == "miguel":
            # Miguel: Migration Architect - needs tech stack insights
            return {
                **base_context,
                "migration_context": {
                    "detected_languages": self.detected_languages,
                    "detected_frameworks": self.detected_frameworks,
                    "database_patterns": self.database_patterns,
                    "data_access_rules_count": len(self.data_access_rules),
                    "complexity_indicators": {
                        "entity_count": len(self.entities),
                        "workflow_count": len(self.workflows),
                        "rule_relationship_count": len(self.rule_relationships),
                    },
                },
                "legacy_analysis": {
                    "authorization_patterns": [
                        r["description"] for r in self.authorization_rules[:5]
                    ],
                    "validation_patterns": [
                        r["description"] for r in self.validation_rules[:5]
                    ],
                    "business_rules_sample": [
                        {"condition": r.get("condition", ""), "action": r.get("action", "")}
                        for r in self.business_logic_rules[:10]
                    ],
                },
            }

        elif agent_lower == "peter":
            # Peter: Product Owner - needs user story material
            return {
                **base_context,
                "story_generation": {
                    "entities_for_epics": [
                        {
                            "name": e.get("name", ""),
                            "crud_coverage": e.get("crud_coverage", ""),
                            "rule_count": e.get("rule_count", 0),
                            "suggested_epic": f"Manage {e.get('name', 'Entity')}",
                        }
                        for e in self.entities[:15]
                    ],
                    "workflows_for_features": [
                        {
                            "name": w.get("name", ""),
                            "workflow_type": w.get("workflow_type", ""),
                            "operations": w.get("operations", []),
                            "total_rules": w.get("total_rules", 0),
                        }
                        for w in self.workflows[:10]
                    ],
                    "validation_requirements": [
                        {"description": r.get("description", ""), "source": r.get("source_file", "")}
                        for r in self.validation_rules[:10]
                    ],
                    "authorization_requirements": [
                        {"description": r.get("description", ""), "pattern": r.get("auth_pattern", "")}
                        for r in self.authorization_rules[:10]
                    ],
                },
                "priority_indicators": {
                    "high_rule_count_entities": [
                        e.get("name", "") for e in self.entities
                        if e.get("rule_count", 0) > 5
                    ][:5],
                    "complex_workflows": [
                        w.get("name", "") for w in self.workflows
                        if w.get("total_rules", 0) > 3
                    ][:5],
                },
            }

        elif agent_lower == "felix":
            # Felix: Feature Architect - needs technical architecture
            return {
                **base_context,
                "architecture_context": {
                    "detected_patterns": {
                        "languages": self.detected_languages,
                        "frameworks": self.detected_frameworks,
                        "database": self.database_patterns,
                    },
                    "module_boundaries": [
                        {
                            "entity": e.get("name", ""),
                            "files": e.get("files_referenced", [])[:3],
                            "rule_count": e.get("rule_count", 0),
                        }
                        for e in self.entities[:10]
                    ],
                    "integration_points": [
                        {
                            "workflow": w.get("name", ""),
                            "files": w.get("source_files", [])[:3],
                            "auth_pattern": w.get("auth_pattern", ""),
                        }
                        for w in self.workflows[:10]
                    ],
                },
                "technical_debt_indicators": {
                    "rules_without_workflow": self.total_rules - sum(
                        w.get("total_rules", 0) for w in self.workflows
                    ),
                    "low_confidence_rules": self.total_rules - self.high_confidence_rules,
                },
            }

        elif agent_lower == "quinn":
            # Quinn: Quality Inspector - needs quality insights
            return {
                **base_context,
                "quality_context": {
                    "validation_coverage": {
                        "total_validation_rules": len(self.validation_rules),
                        "entities_with_validation": len([
                            e for e in self.entities
                            if any("validation" in str(r).lower() for r in self.validation_rules)
                        ]),
                    },
                    "authorization_coverage": {
                        "total_auth_rules": len(self.authorization_rules),
                        "workflows_with_auth": len([
                            w for w in self.workflows
                            if w.get("auth_rules", [])
                        ]),
                    },
                    "rule_quality": {
                        "average_confidence": round(self.average_confidence, 2),
                        "high_confidence_percentage": round(
                            self.high_confidence_rules / self.total_rules * 100, 1
                        ) if self.total_rules > 0 else 0,
                    },
                },
            }

        # Default: return base context
        return base_context


@dataclass
class WorkflowIntegrationResult:
    """Result of business rule workflow integration."""
    success: bool
    workflow_type: str
    extraction_context: Optional[RuleExtractionContext] = None
    agent_contexts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    processing_time_ms: int = 0
    errors: List[str] = field(default_factory=list)


class BusinessRuleWorkflowIntegration:
    """
    Integrates business rule extraction with AI agent workflows.

    This service:
    1. Detects when a workflow needs rule extraction
    2. Runs the TierOrchestrator to extract rules
    3. Correlates rules into entities and workflows
    4. Prepares agent-specific context
    5. Injects context into the workflow
    """

    def __init__(self, db_session=None):
        """
        Initialize the integration service.

        Args:
            db_session: Optional database session for persistence
        """
        self.db_session = db_session
        self._extraction_cache: Dict[str, RuleExtractionContext] = {}

    def supports_workflow(self, workflow_type: str) -> bool:
        """
        Check if a workflow type supports business rule integration.

        Args:
            workflow_type: The workflow type (e.g., "BROWN_PAPER")

        Returns:
            True if workflow supports rule integration
        """
        return workflow_type.upper() in RULE_INTEGRATED_WORKFLOWS

    async def extract_for_workflow(
        self,
        workflow_type: str,
        source_path: str,
        project_id: Optional[int] = None,
        tier: str = "STANDARD",
        enable_llm: bool = True,
    ) -> WorkflowIntegrationResult:
        """
        Extract business rules for a workflow and prepare agent contexts.

        Args:
            workflow_type: The workflow type
            source_path: Path to source code (file or directory)
            project_id: Optional project ID
            tier: Extraction tier (FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM)
            enable_llm: Whether to use LLM features

        Returns:
            WorkflowIntegrationResult with extraction context
        """
        start_time = datetime.now()
        errors: List[str] = []

        if not self.supports_workflow(workflow_type):
            return WorkflowIntegrationResult(
                success=False,
                workflow_type=workflow_type,
                errors=[f"Workflow {workflow_type} does not support rule integration"],
            )

        # Check cache first
        cache_key = f"{workflow_type}:{source_path}:{project_id}:{tier}"
        if cache_key in self._extraction_cache:
            cached = self._extraction_cache[cache_key]
            logger.info(f"Using cached extraction for {cache_key}")
            return WorkflowIntegrationResult(
                success=True,
                workflow_type=workflow_type,
                extraction_context=cached,
                agent_contexts=self._prepare_all_agent_contexts(cached, workflow_type),
                processing_time_ms=0,
            )

        try:
            # Import services (lazy to avoid circular imports)
            from app.services.static_analysis.tier_orchestrator import (
                TierOrchestrator,
                ExtractionTier,
            )
            from app.services.static_analysis.rule_correlation_service import (
                RuleCorrelationService,
            )

            # Map tier string to enum
            tier_map = {
                "FREE": ExtractionTier.FREE,
                "BASIC": ExtractionTier.BASIC,
                "STANDARD": ExtractionTier.STANDARD,
                "PROFESSIONAL": ExtractionTier.PROFESSIONAL,
                "PREMIUM": ExtractionTier.PREMIUM,
            }
            extraction_tier = tier_map.get(tier.upper(), ExtractionTier.STANDARD)

            # Run extraction
            orchestrator = TierOrchestrator(
                extraction_tier=extraction_tier,
                project_id=project_id,
            )

            path = Path(source_path)
            if path.is_file():
                extraction_result = await orchestrator.extract_from_file(
                    str(path), enable_llm
                )
            else:
                extraction_result = await orchestrator.extract_from_directory(
                    str(path), enable_llm=enable_llm
                )

            # Run correlation
            correlation_service = RuleCorrelationService(project_id=project_id)
            correlation_result = correlation_service.correlate(extraction_result.rules)

            # Build extraction context
            context = self._build_extraction_context(
                extraction_result,
                correlation_result,
                tier,
            )

            # Cache the result
            self._extraction_cache[cache_key] = context

            # Prepare agent-specific contexts
            agent_contexts = self._prepare_all_agent_contexts(context, workflow_type)

            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.info(
                f"Rule extraction for {workflow_type}: "
                f"{context.total_rules} rules, {len(context.entities)} entities, "
                f"{len(context.workflows)} workflows in {processing_time}ms"
            )

            return WorkflowIntegrationResult(
                success=True,
                workflow_type=workflow_type,
                extraction_context=context,
                agent_contexts=agent_contexts,
                processing_time_ms=processing_time,
            )

        except ImportError as e:
            error_msg = f"Missing dependency for rule extraction: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        except Exception as e:
            error_msg = f"Rule extraction failed: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return WorkflowIntegrationResult(
            success=False,
            workflow_type=workflow_type,
            processing_time_ms=processing_time,
            errors=errors,
        )

    def _build_extraction_context(
        self,
        extraction_result,
        correlation_result,
        tier: str,
    ) -> RuleExtractionContext:
        """
        Build RuleExtractionContext from extraction and correlation results.

        Args:
            extraction_result: OrchestrationResult from TierOrchestrator
            correlation_result: CorrelationResult from RuleCorrelationService
            tier: Extraction tier string

        Returns:
            RuleExtractionContext for agent consumption
        """
        # Categorize rules by type
        validation_rules = []
        authorization_rules = []
        business_logic_rules = []
        data_access_rules = []

        detected_languages = set()
        detected_frameworks = set()
        database_patterns = set()

        for rule in extraction_result.rules:
            rule_dict = {
                "id": rule.id,
                "description": rule.description,
                "condition": rule.condition,
                "action": rule.action,
                "confidence": rule.confidence,
                "source_file": rule.source_file,
            }

            # Categorize by rule type
            rule_type = rule.rule_type.value if hasattr(rule.rule_type, 'value') else str(rule.rule_type)

            if "validation" in rule_type.lower():
                validation_rules.append(rule_dict)
            elif "authorization" in rule_type.lower() or "permission" in rule_type.lower():
                authorization_rules.append(rule_dict)
            elif "data" in rule_type.lower() or "access" in rule_type.lower():
                data_access_rules.append(rule_dict)
            else:
                business_logic_rules.append(rule_dict)

            # Detect technology from source files
            if rule.source_file:
                ext = Path(rule.source_file).suffix.lower()
                lang_map = {
                    ".py": "Python",
                    ".js": "JavaScript",
                    ".ts": "TypeScript",
                    ".cs": "C#",
                    ".vb": "VB.NET",
                    ".asp": "Classic ASP",
                    ".aspx": "ASP.NET",
                    ".sql": "SQL",
                    ".java": "Java",
                    ".php": "PHP",
                }
                if ext in lang_map:
                    detected_languages.add(lang_map[ext])

            # Detect database patterns
            code = rule.code_snippet or ""
            if "SELECT" in code.upper() or "INSERT" in code.upper():
                if "ORACLE" in code.upper() or "NVL(" in code.upper():
                    database_patterns.add("Oracle PL/SQL")
                elif "ISNULL(" in code.upper() or "@@" in code:
                    database_patterns.add("Microsoft SQL Server")
                else:
                    database_patterns.add("SQL")

        # Convert entities
        entities = [
            {
                "id": e.id,
                "name": e.name,
                "entity_type": e.entity_type,
                "rule_count": e.rule_count,
                "crud_coverage": e.crud_coverage,
                "files_referenced": e.files_referenced[:5],
                "has_create": e.has_create,
                "has_read": e.has_read,
                "has_update": e.has_update,
                "has_delete": e.has_delete,
            }
            for e in correlation_result.entities
        ]

        # Convert workflows
        workflows = [
            {
                "id": w.id,
                "name": w.name,
                "workflow_type": w.workflow_type.value if hasattr(w.workflow_type, 'value') else str(w.workflow_type),
                "primary_entity": w.primary_entity,
                "operations": [op.value if hasattr(op, 'value') else str(op) for op in w.operations],
                "total_rules": w.total_rules,
                "auth_pattern": w.auth_pattern,
                "source_files": w.source_files[:5],
                "confidence": w.confidence,
            }
            for w in correlation_result.workflows
        ]

        # Convert relationships
        relationships = [
            {
                "source": r.source_rule_id,
                "target": r.target_rule_id,
                "type": r.relationship_type,
                "confidence": r.confidence,
            }
            for r in correlation_result.relationships[:50]  # Limit to 50
        ]

        return RuleExtractionContext(
            total_rules=extraction_result.metrics.total_rules,
            high_confidence_rules=extraction_result.metrics.high_confidence_rules,
            average_confidence=extraction_result.metrics.average_confidence,
            entities=entities,
            workflows=workflows,
            validation_rules=validation_rules,
            authorization_rules=authorization_rules,
            business_logic_rules=business_logic_rules,
            data_access_rules=data_access_rules,
            detected_languages=list(detected_languages),
            detected_frameworks=list(detected_frameworks),
            database_patterns=list(database_patterns),
            rule_relationships=relationships,
            extraction_tier=tier,
            extraction_time_ms=extraction_result.metrics.total_ms,
            extraction_cost_cents=extraction_result.metrics.total_cost_cents,
            synthesis_result=extraction_result.synthesis_result,
            errors=extraction_result.errors,
            warnings=extraction_result.warnings,
        )

    def _prepare_all_agent_contexts(
        self,
        context: RuleExtractionContext,
        workflow_type: str,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Prepare contexts for all agents involved in a workflow.

        Args:
            context: The extraction context
            workflow_type: The workflow type

        Returns:
            Dict mapping agent names to their contexts
        """
        # Define agents per workflow type
        workflow_agents = {
            "BROWN_PAPER": ["miguel", "peter", "felix"],
            "MIGRATION": ["miguel", "felix", "marcus"],
            "BACKLOG_GENERATION": ["peter", "felix", "paul"],
            "QUALITY_AUDIT": ["quinn", "betty", "marcus"],
        }

        agents = workflow_agents.get(workflow_type.upper(), ["felix"])

        return {
            agent: context.to_agent_context(agent)
            for agent in agents
        }

    def get_agent_context(
        self,
        agent_name: str,
        workflow_type: str,
        source_path: str,
        project_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached agent context for a specific agent.

        Args:
            agent_name: Agent name (miguel, peter, felix, etc.)
            workflow_type: Workflow type
            source_path: Source path used for extraction
            project_id: Optional project ID

        Returns:
            Agent context dict or None if not cached
        """
        # Check multiple tier possibilities
        for tier in ["STANDARD", "PROFESSIONAL", "PREMIUM", "BASIC", "FREE"]:
            cache_key = f"{workflow_type}:{source_path}:{project_id}:{tier}"
            if cache_key in self._extraction_cache:
                return self._extraction_cache[cache_key].to_agent_context(agent_name)

        return None

    def clear_cache(self, project_id: Optional[int] = None):
        """
        Clear extraction cache.

        Args:
            project_id: If provided, only clear cache for this project
        """
        if project_id is None:
            self._extraction_cache.clear()
        else:
            keys_to_remove = [
                k for k in self._extraction_cache.keys()
                if f":{project_id}:" in k
            ]
            for key in keys_to_remove:
                del self._extraction_cache[key]


# Convenience functions

async def get_rule_context_for_agent(
    agent_name: str,
    source_path: str,
    workflow_type: str = "BROWN_PAPER",
    project_id: Optional[int] = None,
    tier: str = "STANDARD",
) -> Optional[Dict[str, Any]]:
    """
    Get business rule context for a specific agent.

    Args:
        agent_name: Agent name (miguel, peter, felix, etc.)
        source_path: Path to source code
        workflow_type: Workflow type
        project_id: Optional project ID
        tier: Extraction tier

    Returns:
        Agent context dict or None if extraction fails
    """
    service = BusinessRuleWorkflowIntegration()
    result = await service.extract_for_workflow(
        workflow_type=workflow_type,
        source_path=source_path,
        project_id=project_id,
        tier=tier,
    )

    if result.success and result.extraction_context:
        return result.extraction_context.to_agent_context(agent_name)

    return None


def is_rule_integrated_workflow(workflow_type: str) -> bool:
    """Check if a workflow type supports rule integration."""
    return workflow_type.upper() in RULE_INTEGRATED_WORKFLOWS
