# backend/app/services/static_analysis/rule_correlation_service.py
"""
Rule Correlation Service - Detects workflows, entities, and rule relationships.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline - Phase 3

Features:
- CRUD workflow detection (Create, Read, Update, Delete patterns)
- Entity extraction from table names, class names, variables
- Rule relationship detection (guards, validates, triggers)
- Workflow grouping and confidence scoring
"""

import re
import logging
import time
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from .extraction_models import (
    BusinessRule,
    RuleType,
    CRUDOperation,
    WorkflowType,
    Entity,
    Workflow,
    RuleRelationship,
    CorrelationResult,
)

logger = logging.getLogger(__name__)


class RuleCorrelationService:
    """
    Service for correlating business rules into workflows and entities.

    Provides:
    - CRUD operation detection from rule patterns
    - Entity extraction from code patterns (tables, classes, variables)
    - Workflow grouping based on shared entities
    - Relationship detection between rules
    """

    # Patterns for CRUD operation detection
    CRUD_PATTERNS: Dict[CRUDOperation, List[re.Pattern]] = {
        CRUDOperation.CREATE: [
            re.compile(r'\bINSERT\s+INTO\b', re.IGNORECASE),
            re.compile(r'\b(Add|Create|New|Insert)\w*\b', re.IGNORECASE),
            re.compile(r'\bintCanAdd\b', re.IGNORECASE),
            re.compile(r'\.Add\(', re.IGNORECASE),
            re.compile(r'\.Create\(', re.IGNORECASE),
            re.compile(r'POST\s+/api/', re.IGNORECASE),
        ],
        CRUDOperation.READ: [
            re.compile(r'\bSELECT\b.*\bFROM\b', re.IGNORECASE),
            re.compile(r'\b(Get|Read|View|List|Find|Fetch|Load)\w*\b', re.IGNORECASE),
            re.compile(r'\bintCanView\b', re.IGNORECASE),
            re.compile(r'\.Get\(', re.IGNORECASE),
            re.compile(r'\.Find\(', re.IGNORECASE),
            re.compile(r'GET\s+/api/', re.IGNORECASE),
        ],
        CRUDOperation.UPDATE: [
            re.compile(r'\bUPDATE\b.*\bSET\b', re.IGNORECASE),
            re.compile(r'\b(Edit|Update|Modify|Save|Change)\w*\b', re.IGNORECASE),
            re.compile(r'\bintCanEdit\b', re.IGNORECASE),
            re.compile(r'\.Update\(', re.IGNORECASE),
            re.compile(r'\.Save\(', re.IGNORECASE),
            re.compile(r'PUT\s+/api/', re.IGNORECASE),
            re.compile(r'PATCH\s+/api/', re.IGNORECASE),
        ],
        CRUDOperation.DELETE: [
            re.compile(r'\bDELETE\s+FROM\b', re.IGNORECASE),
            re.compile(r'\b(Delete|Remove|Destroy|Drop)\w*\b', re.IGNORECASE),
            re.compile(r'\bintCanDelete\b', re.IGNORECASE),
            re.compile(r'\.Delete\(', re.IGNORECASE),
            re.compile(r'\.Remove\(', re.IGNORECASE),
            re.compile(r'DELETE\s+/api/', re.IGNORECASE),
        ],
        CRUDOperation.COPY: [
            re.compile(r'\b(Copy|Clone|Duplicate)\w*\b', re.IGNORECASE),
            re.compile(r'\bKopieer\b', re.IGNORECASE),  # Dutch
        ],
        CRUDOperation.SEARCH: [
            re.compile(r'\bSELECT\b.*\bWHERE\b', re.IGNORECASE),
            re.compile(r'\b(Search|Filter|Query)\w*\b', re.IGNORECASE),
            re.compile(r'\.Where\(', re.IGNORECASE),
            re.compile(r'\.filter\(', re.IGNORECASE),
        ],
        CRUDOperation.EXPORT: [
            re.compile(r'\b(Export|Download|Generate\s*Report)\w*\b', re.IGNORECASE),
            re.compile(r'\.(xlsx|csv|pdf|xls)\b', re.IGNORECASE),
        ],
        CRUDOperation.IMPORT: [
            re.compile(r'\b(Import|Upload|Load\s*File)\w*\b', re.IGNORECASE),
        ],
    }

    # Patterns for entity extraction
    ENTITY_PATTERNS: List[Tuple[re.Pattern, str]] = [
        # Database table patterns
        (re.compile(r'\b(?:ta|tbl|tb)([A-Z][a-zA-Z0-9]+)\b'), 'table'),
        (re.compile(r'\bFROM\s+(\w+)\b', re.IGNORECASE), 'table'),
        (re.compile(r'\bINSERT\s+INTO\s+(\w+)\b', re.IGNORECASE), 'table'),
        (re.compile(r'\bUPDATE\s+(\w+)\s+SET\b', re.IGNORECASE), 'table'),
        (re.compile(r'\bDELETE\s+FROM\s+(\w+)\b', re.IGNORECASE), 'table'),
        (re.compile(r'\bJOIN\s+(\w+)\b', re.IGNORECASE), 'table'),
        # Class/Service patterns
        (re.compile(r'\b(\w+)Service\b'), 'class'),
        (re.compile(r'\b(\w+)Repository\b'), 'class'),
        (re.compile(r'\b(\w+)Controller\b'), 'class'),
        (re.compile(r'\b(\w+)Manager\b'), 'class'),
        # Variable ID patterns
        (re.compile(r'\bint([A-Z][a-zA-Z0-9]+)ID\b'), 'variable'),
        (re.compile(r'\blng([A-Z][a-zA-Z0-9]+)ID\b'), 'variable'),
        (re.compile(r'\b(\w+)_id\b', re.IGNORECASE), 'variable'),
    ]

    # Authorization pattern detection - Extended for Fase 25
    AUTH_PATTERNS: List[re.Pattern] = [
        # VB.NET patterns
        re.compile(r'\bintCan(Add|Edit|View|Delete|Approve|Reject|Manage|Export)\b', re.IGNORECASE),
        re.compile(r'\bCan(Add|Edit|View|Delete|Approve|Reject|Manage)\b'),
        re.compile(r'\bblnHas(Right|Permission|Access|Role)\b', re.IGNORECASE),
        re.compile(r'\bCheck(Rights?|Permissions?|Access)\b', re.IGNORECASE),
        re.compile(r'\bValidate(User|Access|Permission)\b', re.IGNORECASE),
        re.compile(r'\bIs(Admin|Manager|User|Guest|Authorized|Authenticated)\b', re.IGNORECASE),
        re.compile(r'\bhas(Permission|Access|Role|Right)\b', re.IGNORECASE),
        # C# patterns
        re.compile(r'\[Authorize\b', re.IGNORECASE),
        re.compile(r'\[Authorize\s*\(\s*Roles\s*=', re.IGNORECASE),
        re.compile(r'\[Authorize\s*\(\s*Policy\s*=', re.IGNORECASE),
        re.compile(r'\[AllowAnonymous\b', re.IGNORECASE),
        re.compile(r'User\.IsInRole\b', re.IGNORECASE),
        re.compile(r'User\.HasClaim\b', re.IGNORECASE),
        re.compile(r'ClaimsPrincipal\b', re.IGNORECASE),
        re.compile(r'\.RequireRole\b', re.IGNORECASE),
        re.compile(r'\.RequireClaim\b', re.IGNORECASE),
        re.compile(r'AddPolicy\b', re.IGNORECASE),
        # Python/Django patterns
        re.compile(r'@login_required\b'),
        re.compile(r'@permission_required\b'),
        re.compile(r'@user_passes_test\b'),
        re.compile(r'@staff_member_required\b'),
        re.compile(r'@superuser_required\b'),
        re.compile(r'\.has_perm\b', re.IGNORECASE),
        re.compile(r'\.has_perms\b', re.IGNORECASE),
        re.compile(r'user\.is_staff\b', re.IGNORECASE),
        re.compile(r'user\.is_superuser\b', re.IGNORECASE),
        re.compile(r'user\.groups\.filter\b', re.IGNORECASE),
        # Flask patterns
        re.compile(r'flask_login\.login_required\b', re.IGNORECASE),
        re.compile(r'current_user\.is_authenticated\b', re.IGNORECASE),
        # JavaScript/Node patterns
        re.compile(r'@UseGuards\b', re.IGNORECASE),
        re.compile(r'@Roles\b', re.IGNORECASE),
        re.compile(r'req\.user\.role\b', re.IGNORECASE),
        re.compile(r'req\.user\.permissions\b', re.IGNORECASE),
        re.compile(r'passport\.authenticate\b', re.IGNORECASE),
        re.compile(r'isAuthenticated\b', re.IGNORECASE),
        re.compile(r'requireAuth\b', re.IGNORECASE),
        re.compile(r'checkPermission\b', re.IGNORECASE),
        # Java/Spring patterns
        re.compile(r'@PreAuthorize\b'),
        re.compile(r'@PostAuthorize\b'),
        re.compile(r'@Secured\b'),
        re.compile(r'@RolesAllowed\b'),
        re.compile(r'hasRole\b', re.IGNORECASE),
        re.compile(r'hasAuthority\b', re.IGNORECASE),
        re.compile(r'hasPermission\b', re.IGNORECASE),
        # Generic patterns
        re.compile(r'\brequire_permission\b', re.IGNORECASE),
        re.compile(r'\bauthorize\b', re.IGNORECASE),
        re.compile(r'\bauthenticate\b', re.IGNORECASE),
        re.compile(r'\baccess_control\b', re.IGNORECASE),
        re.compile(r'\brbac\b', re.IGNORECASE),
        re.compile(r'\bpermissions?\[', re.IGNORECASE),
        re.compile(r'\broles?\[', re.IGNORECASE),
    ]

    # Entity name normalization
    TABLE_PREFIXES = ['ta', 'tbl', 'tb', 't_']
    SUFFIX_REMOVALS = ['Service', 'Repository', 'Controller', 'Manager', 'Handler']

    def __init__(self, project_id: Optional[int] = None):
        """
        Initialize the correlation service.

        Args:
            project_id: Optional project ID for tracking
        """
        self.project_id = project_id
        self._entity_counter = 0
        self._workflow_counter = 0

    def correlate(self, rules: List[BusinessRule]) -> CorrelationResult:
        """
        Perform full correlation analysis on a list of business rules.

        Args:
            rules: List of extracted business rules

        Returns:
            CorrelationResult with entities, workflows, and relationships
        """
        start_time = time.time()
        result = CorrelationResult(project_id=self.project_id)
        result.total_rules_analyzed = len(rules)

        if not rules:
            return result

        try:
            # Step 1: Detect CRUD operations for each rule
            rule_operations = self._detect_crud_operations(rules)

            # Step 2: Extract entities from rules
            entities = self._extract_entities(rules)
            result.entities = list(entities.values())

            # Step 3: Link rules to entities
            self._link_rules_to_entities(rules, entities)

            # Step 4: Detect workflows based on entities and operations
            workflows = self._detect_workflows(rules, entities, rule_operations)
            result.workflows = workflows

            # Step 5: Detect relationships between rules
            relationships = self._detect_relationships(rules, entities)
            result.relationships = relationships

            # Calculate statistics
            correlated_rule_ids: Set[str] = set()
            for workflow in workflows:
                correlated_rule_ids.update(workflow.rule_ids)
            result.rules_correlated = len(correlated_rule_ids)
            result.rules_orphaned = len(rules) - result.rules_correlated

        except Exception as e:
            logger.error(f"Correlation error: {e}")
            result.errors.append(str(e))

        result.correlation_time_ms = int((time.time() - start_time) * 1000)
        result.__post_init__()  # Recalculate statistics

        logger.info(
            f"Correlation complete: {result.entities_detected} entities, "
            f"{result.workflows_detected} workflows, "
            f"{result.relationships_detected} relationships in {result.correlation_time_ms}ms"
        )

        return result

    def _detect_crud_operations(
        self, rules: List[BusinessRule]
    ) -> Dict[str, List[CRUDOperation]]:
        """
        Detect CRUD operations for each rule.

        Args:
            rules: List of business rules

        Returns:
            Dict mapping rule IDs to detected CRUD operations
        """
        rule_operations: Dict[str, List[CRUDOperation]] = {}

        for rule in rules:
            operations = []
            # Combine condition, action, and code snippet for analysis
            text = f"{rule.condition} {rule.action} {rule.code_snippet or ''}"

            for operation, patterns in self.CRUD_PATTERNS.items():
                for pattern in patterns:
                    if pattern.search(text):
                        if operation not in operations:
                            operations.append(operation)
                        break

            # Also check rule type hints
            if rule.rule_type == RuleType.DATA_ACCESS:
                # Default to READ if no specific operation detected
                if not operations:
                    operations.append(CRUDOperation.READ)

            rule_operations[rule.id] = operations

            # Update rule's workflow context based on detected operations
            if operations:
                rule.workflow_context = operations[0].value

        return rule_operations

    def _extract_entities(self, rules: List[BusinessRule]) -> Dict[str, Entity]:
        """
        Extract domain entities from business rules.

        Args:
            rules: List of business rules

        Returns:
            Dict mapping normalized entity names to Entity objects
        """
        entities: Dict[str, Entity] = {}
        entity_originals: Dict[str, Set[str]] = defaultdict(set)

        for rule in rules:
            # Combine all text sources
            text = f"{rule.condition} {rule.action} {rule.code_snippet or ''}"

            for pattern, source_type in self.ENTITY_PATTERNS:
                for match in pattern.finditer(text):
                    original_name = match.group(1)
                    normalized = self._normalize_entity_name(original_name)

                    if normalized and len(normalized) >= 2:
                        entity_originals[normalized].add(original_name)

                        if normalized not in entities:
                            self._entity_counter += 1
                            entities[normalized] = Entity(
                                id=f"ENT-{self._entity_counter:03d}",
                                name=normalized,
                                original_names=[],
                                entity_type=source_type,
                            )

            # Also check related_entities field
            for entity_name in rule.related_entities:
                normalized = self._normalize_entity_name(entity_name)
                if normalized and normalized not in entities:
                    self._entity_counter += 1
                    entities[normalized] = Entity(
                        id=f"ENT-{self._entity_counter:03d}",
                        name=normalized,
                        original_names=[entity_name],
                        entity_type="domain",
                    )

        # Update original names
        for name, entity in entities.items():
            entity.original_names = list(entity_originals.get(name, set()))

        return entities

    def _normalize_entity_name(self, name: str) -> str:
        """
        Normalize an entity name by removing prefixes/suffixes.

        Args:
            name: Raw entity name

        Returns:
            Normalized entity name
        """
        if not name:
            return ""

        normalized = name

        # Remove table prefixes
        for prefix in self.TABLE_PREFIXES:
            if normalized.lower().startswith(prefix):
                normalized = normalized[len(prefix):]
                break

        # Remove common suffixes
        for suffix in self.SUFFIX_REMOVALS:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
                break

        # Ensure first letter is uppercase
        if normalized:
            normalized = normalized[0].upper() + normalized[1:]

        return normalized

    def _link_rules_to_entities(
        self, rules: List[BusinessRule], entities: Dict[str, Entity]
    ):
        """
        Link rules to their associated entities.

        Args:
            rules: List of business rules
            entities: Dict of extracted entities
        """
        for rule in rules:
            text = f"{rule.condition} {rule.action} {rule.code_snippet or ''}"
            text_lower = text.lower()

            for entity_name, entity in entities.items():
                # Check if entity or its original names appear in rule
                found = entity_name.lower() in text_lower

                if not found:
                    for original in entity.original_names:
                        if original.lower() in text_lower:
                            found = True
                            break

                if found:
                    if rule.id not in entity.rule_ids:
                        entity.rule_ids.append(rule.id)
                        entity.rule_count += 1

                    if rule.source_file not in entity.files_referenced:
                        entity.files_referenced.append(rule.source_file)

                    # Update CRUD coverage
                    if rule.workflow_context:
                        ctx = rule.workflow_context.lower()
                        if ctx == 'create':
                            entity.has_create = True
                        elif ctx == 'read':
                            entity.has_read = True
                        elif ctx == 'update':
                            entity.has_update = True
                        elif ctx == 'delete':
                            entity.has_delete = True

    def _detect_workflows(
        self,
        rules: List[BusinessRule],
        entities: Dict[str, Entity],
        rule_operations: Dict[str, List[CRUDOperation]],
    ) -> List[Workflow]:
        """
        Detect workflows based on entities and CRUD operations.

        Args:
            rules: List of business rules
            entities: Dict of extracted entities
            rule_operations: Dict of rule ID to CRUD operations

        Returns:
            List of detected workflows
        """
        workflows: List[Workflow] = []
        rules_by_id = {r.id: r for r in rules}

        # Create a workflow for each entity with sufficient rules
        for entity_name, entity in entities.items():
            if entity.rule_count < 2:
                continue  # Skip entities with too few rules

            self._workflow_counter += 1
            workflow = Workflow(
                id=f"WF-{self._workflow_counter:03d}",
                name=f"{entity_name} Management",
                workflow_type=WorkflowType.CRUD,
                primary_entity=entity_name,
            )

            # Collect operations and rules
            operations_set: Set[CRUDOperation] = set()
            rules_by_op: Dict[str, List[str]] = defaultdict(list)

            for rule_id in entity.rule_ids:
                rule = rules_by_id.get(rule_id)
                if not rule:
                    continue

                workflow.rule_ids.append(rule_id)

                # Get operations for this rule
                ops = rule_operations.get(rule_id, [])
                for op in ops:
                    operations_set.add(op)
                    rules_by_op[op.value].append(rule_id)

                # Categorize by rule type
                if rule.rule_type == RuleType.AUTHORIZATION:
                    workflow.auth_rules.append(rule_id)
                elif rule.rule_type == RuleType.VALIDATION:
                    workflow.validation_rules.append(rule_id)

                # Track source files
                if rule.source_file not in workflow.source_files:
                    workflow.source_files.append(rule.source_file)

            workflow.operations = list(operations_set)
            workflow.rules_by_operation = dict(rules_by_op)
            workflow.total_rules = len(workflow.rule_ids)

            # Detect authorization pattern
            workflow.auth_pattern = self._detect_auth_pattern(
                [rules_by_id[rid] for rid in workflow.auth_rules if rid in rules_by_id]
            )

            # Calculate confidence based on CRUD coverage
            crud_count = sum([
                entity.has_create,
                entity.has_read,
                entity.has_update,
                entity.has_delete
            ])
            workflow.confidence = min(0.95, 0.5 + (crud_count * 0.1) + (workflow.total_rules * 0.02))

            workflows.append(workflow)

        # Detect state machine workflows
        state_workflows = self._detect_state_machine_workflows(rules)
        workflows.extend(state_workflows)

        return workflows

    def _detect_auth_pattern(self, auth_rules: List[BusinessRule]) -> Optional[str]:
        """
        Detect the authorization pattern from auth rules.

        Args:
            auth_rules: List of authorization rules

        Returns:
            Detected auth pattern or None
        """
        patterns_found: Dict[str, int] = defaultdict(int)

        for rule in auth_rules:
            text = f"{rule.condition} {rule.action}"
            for pattern in self.AUTH_PATTERNS:
                matches = pattern.findall(text)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match else ""
                    patterns_found[match] += 1

        if patterns_found:
            # Return most common pattern
            most_common = max(patterns_found.items(), key=lambda x: x[1])
            return f"intCan{most_common[0]}" if most_common[0] else None

        return None

    def _detect_state_machine_workflows(
        self, rules: List[BusinessRule]
    ) -> List[Workflow]:
        """
        Detect state machine workflows from rules.

        Args:
            rules: List of business rules

        Returns:
            List of state machine workflows
        """
        workflows: List[Workflow] = []
        state_patterns = [
            re.compile(r'\b(status|state|fase|phase)\s*[=:]\s*["\']?(\w+)', re.IGNORECASE),
            re.compile(r'\bSet\s*(Status|State)\s*=\s*["\']?(\w+)', re.IGNORECASE),
            re.compile(r'\b(\w+)\s*->\s*(\w+)\b'),  # State transitions
        ]

        state_rules: Dict[str, List[str]] = defaultdict(list)

        for rule in rules:
            if rule.rule_type in [RuleType.WORKFLOW, RuleType.STATE_MANAGEMENT]:
                text = f"{rule.condition} {rule.action}"
                for pattern in state_patterns:
                    matches = pattern.findall(text)
                    for match in matches:
                        if isinstance(match, tuple) and len(match) >= 2:
                            state_key = match[0].lower()
                            state_rules[state_key].append(rule.id)

        # Create workflows for state machines with multiple states
        for state_key, rule_ids in state_rules.items():
            if len(rule_ids) >= 2:
                self._workflow_counter += 1
                workflow = Workflow(
                    id=f"WF-{self._workflow_counter:03d}",
                    name=f"{state_key.title()} State Machine",
                    workflow_type=WorkflowType.STATE_MACHINE,
                    rule_ids=list(set(rule_ids)),
                    total_rules=len(set(rule_ids)),
                    confidence=0.75,
                )
                workflows.append(workflow)

        return workflows

    def _detect_relationships(
        self,
        rules: List[BusinessRule],
        entities: Dict[str, Entity],
    ) -> List[RuleRelationship]:
        """
        Detect relationships between business rules.

        Args:
            rules: List of business rules
            entities: Dict of extracted entities

        Returns:
            List of rule relationships
        """
        relationships: List[RuleRelationship] = []
        rules_by_id = {r.id: r for r in rules}

        # Group rules by source file and function for proximity analysis
        rules_by_context: Dict[str, List[BusinessRule]] = defaultdict(list)
        for rule in rules:
            context_key = f"{rule.source_file}:{rule.parent_function or 'global'}"
            rules_by_context[context_key].append(rule)

        # Detect guards relationships (auth rules guarding data access)
        for rule in rules:
            if rule.rule_type == RuleType.AUTHORIZATION:
                # Find data access rules in same context
                context_key = f"{rule.source_file}:{rule.parent_function or 'global'}"
                for other in rules_by_context.get(context_key, []):
                    if other.id != rule.id and other.rule_type == RuleType.DATA_ACCESS:
                        # Auth rule likely guards data access
                        rel = RuleRelationship(
                            source_rule_id=rule.id,
                            target_rule_id=other.id,
                            relationship_type="guards",
                            confidence=0.8,
                            description=f"Authorization check guards data access",
                        )
                        relationships.append(rel)

        # Detect validates relationships (validation before data operations)
        for rule in rules:
            if rule.rule_type == RuleType.VALIDATION:
                context_key = f"{rule.source_file}:{rule.parent_function or 'global'}"
                for other in rules_by_context.get(context_key, []):
                    if other.id != rule.id and other.rule_type == RuleType.DATA_ACCESS:
                        if rule.source_lines[0] < other.source_lines[0]:
                            rel = RuleRelationship(
                                source_rule_id=rule.id,
                                target_rule_id=other.id,
                                relationship_type="validates",
                                confidence=0.75,
                                description="Validation precedes data operation",
                            )
                            relationships.append(rel)

        # Detect shares_entity relationships
        for entity_name, entity in entities.items():
            if len(entity.rule_ids) > 1:
                # Rules sharing the same entity are related
                for i, rule_id_1 in enumerate(entity.rule_ids):
                    for rule_id_2 in entity.rule_ids[i + 1:]:
                        rel = RuleRelationship(
                            source_rule_id=rule_id_1,
                            target_rule_id=rule_id_2,
                            relationship_type="shares_entity",
                            confidence=0.9,
                            description=f"Both rules operate on {entity_name}",
                        )
                        relationships.append(rel)

        return relationships

    def get_workflow_summary(self, result: CorrelationResult) -> Dict:
        """
        Generate a summary of detected workflows.

        Args:
            result: Correlation result

        Returns:
            Summary dict for dashboard display
        """
        return {
            "total_entities": result.entities_detected,
            "total_workflows": result.workflows_detected,
            "total_relationships": result.relationships_detected,
            "coverage": {
                "rules_in_workflows": result.rules_correlated,
                "orphaned_rules": result.rules_orphaned,
                "coverage_percent": (
                    result.rules_correlated / result.total_rules_analyzed * 100
                    if result.total_rules_analyzed > 0 else 0
                ),
            },
            "entities_by_crud_coverage": self._summarize_crud_coverage(result.entities),
            "workflows_by_type": self._summarize_workflow_types(result.workflows),
        }

    def _summarize_crud_coverage(self, entities: List[Entity]) -> Dict[str, int]:
        """Summarize entities by their CRUD coverage."""
        coverage_counts: Dict[str, int] = defaultdict(int)
        for entity in entities:
            coverage_counts[entity.crud_coverage] += 1
        return dict(coverage_counts)

    def _summarize_workflow_types(self, workflows: List[Workflow]) -> Dict[str, int]:
        """Summarize workflows by type."""
        type_counts: Dict[str, int] = defaultdict(int)
        for workflow in workflows:
            type_counts[workflow.workflow_type.value] += 1
        return dict(type_counts)

    def generate_decision_tables(
        self, rules: List[BusinessRule]
    ) -> List[Dict]:
        """
        Generate decision tables from BRANCHING rules.

        Groups related conditional rules into decision table format
        suitable for DMN (Decision Model and Notation) or markdown tables.

        Args:
            rules: List of business rules

        Returns:
            List of decision tables with inputs, outputs, and rules
        """
        decision_tables: List[Dict] = []
        branching_rules = [r for r in rules if r.rule_type == RuleType.BRANCHING]

        # Group by parent function/context
        rules_by_context: Dict[str, List[BusinessRule]] = defaultdict(list)
        for rule in branching_rules:
            context = rule.parent_function or rule.parent_class or "global"
            rules_by_context[context].append(rule)

        for context, context_rules in rules_by_context.items():
            if len(context_rules) < 2:
                continue

            # Extract unique conditions and actions
            conditions = set()
            actions = set()
            for rule in context_rules:
                conditions.add(rule.condition)
                actions.add(rule.action)

            # Build decision table
            table_id = f"DT-{len(decision_tables) + 1:03d}"
            decision_table = {
                "id": table_id,
                "name": f"Decision Table: {context}",
                "context": context,
                "input_columns": list(conditions),
                "output_columns": list(actions),
                "rules": [
                    {
                        "rule_id": rule.id,
                        "condition": rule.condition,
                        "action": rule.action,
                        "confidence": rule.confidence,
                        "source_file": rule.source_file,
                    }
                    for rule in context_rules
                ],
                "total_rules": len(context_rules),
                "dmn_xml": self._to_dmn_xml(table_id, context, context_rules),
                "markdown": self._to_decision_markdown(context, context_rules),
            }
            decision_tables.append(decision_table)

        return decision_tables

    def _to_dmn_xml(
        self, table_id: str, context: str, rules: List[BusinessRule]
    ) -> str:
        """Generate simplified DMN XML for decision table."""
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/">',
            f'  <decision id="{table_id}" name="{context}">',
            '    <decisionTable>',
        ]

        # Add inputs
        xml_lines.append('      <input>')
        xml_lines.append('        <inputExpression typeRef="string">')
        xml_lines.append('          <text>condition</text>')
        xml_lines.append('        </inputExpression>')
        xml_lines.append('      </input>')

        # Add outputs
        xml_lines.append('      <output name="action" typeRef="string"/>')

        # Add rules
        for i, rule in enumerate(rules):
            condition_escaped = rule.condition.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            action_escaped = rule.action.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            xml_lines.append(f'      <rule id="rule_{i + 1}">')
            xml_lines.append(f'        <inputEntry><text>{condition_escaped}</text></inputEntry>')
            xml_lines.append(f'        <outputEntry><text>{action_escaped}</text></outputEntry>')
            xml_lines.append('      </rule>')

        xml_lines.extend([
            '    </decisionTable>',
            '  </decision>',
            '</definitions>',
        ])

        return '\n'.join(xml_lines)

    def _to_decision_markdown(
        self, context: str, rules: List[BusinessRule]
    ) -> str:
        """Generate markdown table for decision table."""
        lines = [
            f"## Decision Table: {context}",
            "",
            "| # | Condition | Action | Confidence |",
            "|---|-----------|--------|------------|",
        ]

        for i, rule in enumerate(rules):
            condition = rule.condition[:50] + "..." if len(rule.condition) > 50 else rule.condition
            action = rule.action[:50] + "..." if len(rule.action) > 50 else rule.action
            lines.append(f"| {i + 1} | {condition} | {action} | {rule.confidence:.0%} |")

        return '\n'.join(lines)

    def generate_authorization_matrix(
        self, rules: List[BusinessRule]
    ) -> Dict:
        """
        Generate authorization matrix from AUTHORIZATION rules.

        Creates a Role-Permission-Resource matrix from detected auth rules.

        Args:
            rules: List of business rules

        Returns:
            Authorization matrix with roles, permissions, and resources
        """
        auth_rules = [r for r in rules if r.rule_type == RuleType.AUTHORIZATION]

        # Extract roles, permissions, and resources
        roles: Set[str] = set()
        permissions: Set[str] = set()
        resources: Set[str] = set()
        role_permissions: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))

        # Role patterns
        role_patterns = [
            re.compile(r'\b(admin|administrator|user|manager|viewer|editor|operator|superuser)\b', re.IGNORECASE),
            re.compile(r'\brole\s*[=:]\s*["\']?(\w+)', re.IGNORECASE),
            re.compile(r'\b(intCan|has|is)\s*(\w+)', re.IGNORECASE),
        ]

        # Permission patterns
        permission_patterns = [
            re.compile(r'\b(can|may|allow|permit|grant)\s*(\w+)', re.IGNORECASE),
            re.compile(r'\b(read|write|create|update|delete|view|edit|add|remove)\b', re.IGNORECASE),
        ]

        # Resource patterns
        resource_patterns = [
            re.compile(r'\b(tbl|table|entity|model)\s*_?(\w+)', re.IGNORECASE),
            re.compile(r'/api/(\w+)', re.IGNORECASE),
        ]

        for rule in auth_rules:
            text = f"{rule.condition} {rule.action}"

            # Extract roles
            for pattern in role_patterns:
                for match in pattern.findall(text):
                    role = match[1] if isinstance(match, tuple) else match
                    if role.lower() not in ['and', 'or', 'not', 'the', 'can', 'has', 'is']:
                        roles.add(role.lower())

            # Extract permissions
            for pattern in permission_patterns:
                for match in pattern.findall(text):
                    perm = match[1] if isinstance(match, tuple) else match
                    if perm.lower() not in ['and', 'or', 'not', 'the']:
                        permissions.add(perm.lower())

            # Extract resources
            for pattern in resource_patterns:
                for match in pattern.findall(text):
                    resource = match[1] if isinstance(match, tuple) else match
                    resources.add(resource.lower())

            # Build role-permission-resource mapping
            for entity in rule.related_entities:
                resources.add(entity.lower())

            # Simple heuristic: associate first found role with permissions
            found_roles = [r for r in roles if r in text.lower()]
            found_perms = [p for p in permissions if p in text.lower()]
            found_resources = [res for res in resources if res in text.lower()]

            for role in found_roles or ["unknown"]:
                for perm in found_perms or ["access"]:
                    for resource in found_resources or ["system"]:
                        role_permissions[role][resource].add(perm)

        # Build matrix
        matrix: Dict[str, Dict[str, List[str]]] = {}
        for role, resource_perms in role_permissions.items():
            matrix[role] = {
                resource: sorted(list(perms))
                for resource, perms in resource_perms.items()
            }

        return {
            "id": "AUTH-MATRIX-001",
            "name": "Authorization Matrix",
            "roles": sorted(list(roles)) if roles else ["admin", "user"],
            "permissions": sorted(list(permissions)) if permissions else ["read", "write"],
            "resources": sorted(list(resources)) if resources else ["system"],
            "matrix": matrix,
            "total_rules": len(auth_rules),
            "markdown": self._to_auth_matrix_markdown(matrix, sorted(list(roles)), sorted(list(resources))),
        }

    def _to_auth_matrix_markdown(
        self,
        matrix: Dict[str, Dict[str, List[str]]],
        roles: List[str],
        resources: List[str]
    ) -> str:
        """Generate markdown table for authorization matrix."""
        if not roles:
            roles = ["(none)"]
        if not resources:
            resources = ["(none)"]

        lines = [
            "## Authorization Matrix",
            "",
            "| Role | " + " | ".join(resources) + " |",
            "|------|" + "|".join(["------" for _ in resources]) + "|",
        ]

        for role in roles:
            row = [role]
            for resource in resources:
                perms = matrix.get(role, {}).get(resource, [])
                row.append(", ".join(perms) if perms else "-")
            lines.append("| " + " | ".join(row) + " |")

        return '\n'.join(lines)
