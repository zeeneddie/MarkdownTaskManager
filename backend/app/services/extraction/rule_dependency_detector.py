"""
Rule Dependency Detector - Week 105
BR-M-2: Inter-Rule Dependency Detection

Analyzes relationships between business rules to detect:
- Direct dependencies (rule A requires rule B)
- Conflicts (rule A contradicts rule B)
- Hierarchies (rule A is a specialization of rule B)
- Temporal dependencies (rule A must execute before rule B)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
from datetime import datetime
import re
from collections import defaultdict

# Import from semantic_rule_analyzer
from .semantic_rule_analyzer import ExtractedRule, RuleCategory


class DependencyType(Enum):
    """Types of rule dependencies."""
    REQUIRES = "requires"           # Rule A needs rule B to function
    CONFLICTS = "conflicts"         # Rule A contradicts rule B
    SPECIALIZES = "specializes"     # Rule A is a more specific version of B
    PRECEDES = "precedes"           # Rule A must run before rule B
    TRIGGERS = "triggers"           # Rule A activates rule B
    OVERRIDES = "overrides"         # Rule A supersedes rule B
    SHARES_ENTITY = "shares_entity" # Both rules operate on same entity
    SHARES_STATE = "shares_state"   # Both rules affect same state


class ConflictSeverity(Enum):
    """Severity levels for rule conflicts."""
    CRITICAL = "critical"   # Rules directly contradict
    HIGH = "high"           # Potential logic conflict
    MEDIUM = "medium"       # Overlapping conditions
    LOW = "low"             # Minor inconsistency


@dataclass
class RuleDependency:
    """A dependency relationship between two rules."""
    source_rule_id: str
    target_rule_id: str
    dependency_type: DependencyType
    confidence: float  # 0.0 to 1.0
    reason: str
    shared_elements: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_rule_id": self.source_rule_id,
            "target_rule_id": self.target_rule_id,
            "dependency_type": self.dependency_type.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "shared_elements": self.shared_elements,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class RuleConflict:
    """A conflict between two rules."""
    rule_a_id: str
    rule_b_id: str
    severity: ConflictSeverity
    conflict_type: str
    description: str
    resolution_suggestion: Optional[str] = None
    affected_entities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_a_id": self.rule_a_id,
            "rule_b_id": self.rule_b_id,
            "severity": self.severity.value,
            "conflict_type": self.conflict_type,
            "description": self.description,
            "resolution_suggestion": self.resolution_suggestion,
            "affected_entities": self.affected_entities
        }


@dataclass
class RuleGraph:
    """Graph representation of rule dependencies."""
    rules: Dict[str, ExtractedRule]
    dependencies: List[RuleDependency]
    conflicts: List[RuleConflict]

    def get_dependencies_for(self, rule_id: str) -> List[RuleDependency]:
        """Get all dependencies where rule_id is the source."""
        return [d for d in self.dependencies if d.source_rule_id == rule_id]

    def get_dependents_of(self, rule_id: str) -> List[RuleDependency]:
        """Get all rules that depend on rule_id."""
        return [d for d in self.dependencies if d.target_rule_id == rule_id]

    def get_conflicts_for(self, rule_id: str) -> List[RuleConflict]:
        """Get all conflicts involving rule_id."""
        return [
            c for c in self.conflicts
            if c.rule_a_id == rule_id or c.rule_b_id == rule_id
        ]

    def get_rule_clusters(self) -> List[Set[str]]:
        """Find clusters of related rules."""
        # Build adjacency list
        adj: Dict[str, Set[str]] = defaultdict(set)
        for dep in self.dependencies:
            adj[dep.source_rule_id].add(dep.target_rule_id)
            adj[dep.target_rule_id].add(dep.source_rule_id)

        # Find connected components
        visited: Set[str] = set()
        clusters: List[Set[str]] = []

        for rule_id in self.rules:
            if rule_id not in visited:
                cluster: Set[str] = set()
                self._dfs(rule_id, adj, visited, cluster)
                if cluster:
                    clusters.append(cluster)

        return clusters

    def _dfs(
        self,
        node: str,
        adj: Dict[str, Set[str]],
        visited: Set[str],
        cluster: Set[str]
    ):
        """Depth-first search for cluster detection."""
        visited.add(node)
        cluster.add(node)
        for neighbor in adj.get(node, set()):
            if neighbor not in visited:
                self._dfs(neighbor, adj, visited, cluster)


class RuleDependencyDetector:
    """
    Detects dependencies and conflicts between business rules.

    Analysis methods:
    1. Entity-based: Rules operating on same entities
    2. State-based: Rules affecting same state variables
    3. Condition-based: Rules with overlapping conditions
    4. Temporal: Execution order dependencies
    5. Semantic: Meaning-based relationships
    """

    def __init__(self):
        self._analyzed_pairs: Set[Tuple[str, str]] = set()

    def analyze(self, rules: List[ExtractedRule]) -> RuleGraph:
        """
        Analyze a set of rules for dependencies and conflicts.

        Args:
            rules: List of extracted business rules

        Returns:
            RuleGraph containing all detected relationships
        """
        rules_dict = {r.id: r for r in rules}
        dependencies = []
        conflicts = []

        # Compare each pair of rules
        for i, rule_a in enumerate(rules):
            for rule_b in rules[i + 1:]:
                pair_deps, pair_conflicts = self._analyze_pair(rule_a, rule_b)
                dependencies.extend(pair_deps)
                conflicts.extend(pair_conflicts)

        return RuleGraph(
            rules=rules_dict,
            dependencies=dependencies,
            conflicts=conflicts
        )

    def _analyze_pair(
        self,
        rule_a: ExtractedRule,
        rule_b: ExtractedRule
    ) -> Tuple[List[RuleDependency], List[RuleConflict]]:
        """Analyze a pair of rules for relationships."""
        dependencies = []
        conflicts = []

        # Check for shared entities
        shared_entities = set(rule_a.entities) & set(rule_b.entities)
        if shared_entities:
            dep = self._detect_entity_dependency(rule_a, rule_b, shared_entities)
            if dep:
                dependencies.append(dep)

        # Check for state dependencies
        state_dep = self._detect_state_dependency(rule_a, rule_b)
        if state_dep:
            dependencies.append(state_dep)

        # Check for condition overlap
        overlap_dep = self._detect_condition_overlap(rule_a, rule_b)
        if overlap_dep:
            dependencies.append(overlap_dep)

        # Check for conflicts
        conflict = self._detect_conflict(rule_a, rule_b)
        if conflict:
            conflicts.append(conflict)

        # Check for specialization
        special_dep = self._detect_specialization(rule_a, rule_b)
        if special_dep:
            dependencies.append(special_dep)

        return dependencies, conflicts

    def _detect_entity_dependency(
        self,
        rule_a: ExtractedRule,
        rule_b: ExtractedRule,
        shared_entities: Set[str]
    ) -> Optional[RuleDependency]:
        """Detect dependency based on shared entities."""
        if not shared_entities:
            return None

        # Determine dependency direction based on category hierarchy
        category_order = {
            RuleCategory.VALIDATION: 1,
            RuleCategory.AUTHORIZATION: 2,
            RuleCategory.CONSTRAINT: 3,
            RuleCategory.CALCULATION: 4,
            RuleCategory.WORKFLOW: 5,
            RuleCategory.TRANSFORMATION: 6,
            RuleCategory.NOTIFICATION: 7,
        }

        order_a = category_order.get(rule_a.category, 99)
        order_b = category_order.get(rule_b.category, 99)

        if order_a < order_b:
            source, target = rule_a, rule_b
            dep_type = DependencyType.PRECEDES
        elif order_a > order_b:
            source, target = rule_b, rule_a
            dep_type = DependencyType.PRECEDES
        else:
            source, target = rule_a, rule_b
            dep_type = DependencyType.SHARES_ENTITY

        return RuleDependency(
            source_rule_id=source.id,
            target_rule_id=target.id,
            dependency_type=dep_type,
            confidence=0.7,
            reason=f"Both rules operate on: {', '.join(shared_entities)}",
            shared_elements=list(shared_entities)
        )

    def _detect_state_dependency(
        self,
        rule_a: ExtractedRule,
        rule_b: ExtractedRule
    ) -> Optional[RuleDependency]:
        """Detect dependency based on shared state variables."""
        # Look for state variables in code snippets
        state_pattern = r'(?:self\.)?(?:status|state|is_\w+|has_\w+|can_\w+)\s*='

        states_a = set(re.findall(state_pattern, rule_a.code_snippet))
        states_b = set(re.findall(state_pattern, rule_b.code_snippet))

        shared_states = states_a & states_b
        if not shared_states:
            return None

        return RuleDependency(
            source_rule_id=rule_a.id,
            target_rule_id=rule_b.id,
            dependency_type=DependencyType.SHARES_STATE,
            confidence=0.8,
            reason=f"Both rules modify state variables: {', '.join(shared_states)}",
            shared_elements=list(shared_states)
        )

    def _detect_condition_overlap(
        self,
        rule_a: ExtractedRule,
        rule_b: ExtractedRule
    ) -> Optional[RuleDependency]:
        """Detect overlap in rule conditions."""
        if not rule_a.conditions or not rule_b.conditions:
            return None

        # Simple overlap detection based on variable names
        vars_a = set()
        vars_b = set()

        for cond in rule_a.conditions:
            vars_a.update(re.findall(r'\b(\w+)\b', cond))

        for cond in rule_b.conditions:
            vars_b.update(re.findall(r'\b(\w+)\b', cond))

        # Filter common words
        common_words = {'if', 'and', 'or', 'not', 'is', 'in', 'True', 'False', 'None'}
        vars_a -= common_words
        vars_b -= common_words

        shared_vars = vars_a & vars_b
        overlap_ratio = len(shared_vars) / max(len(vars_a | vars_b), 1)

        if overlap_ratio < 0.3:
            return None

        return RuleDependency(
            source_rule_id=rule_a.id,
            target_rule_id=rule_b.id,
            dependency_type=DependencyType.REQUIRES,
            confidence=overlap_ratio,
            reason=f"Conditions share variables: {', '.join(list(shared_vars)[:5])}",
            shared_elements=list(shared_vars)
        )

    def _detect_conflict(
        self,
        rule_a: ExtractedRule,
        rule_b: ExtractedRule
    ) -> Optional[RuleConflict]:
        """Detect potential conflicts between rules."""
        # Check for opposite validation outcomes
        if rule_a.category == RuleCategory.VALIDATION and rule_b.category == RuleCategory.VALIDATION:
            conflict = self._check_validation_conflict(rule_a, rule_b)
            if conflict:
                return conflict

        # Check for contradictory authorization
        if rule_a.category == RuleCategory.AUTHORIZATION and rule_b.category == RuleCategory.AUTHORIZATION:
            conflict = self._check_auth_conflict(rule_a, rule_b)
            if conflict:
                return conflict

        return None

    def _check_validation_conflict(
        self,
        rule_a: ExtractedRule,
        rule_b: ExtractedRule
    ) -> Optional[RuleConflict]:
        """Check for validation rule conflicts."""
        # Look for opposite conditions on same variable
        for cond_a in rule_a.conditions:
            for cond_b in rule_b.conditions:
                # Check for > vs < conflicts
                var_match_a = re.search(r'(\w+)\s*(>|<|>=|<=|==|!=)', cond_a)
                var_match_b = re.search(r'(\w+)\s*(>|<|>=|<=|==|!=)', cond_b)

                if var_match_a and var_match_b:
                    var_a, op_a = var_match_a.groups()
                    var_b, op_b = var_match_b.groups()

                    if var_a == var_b and self._are_conflicting_ops(op_a, op_b):
                        return RuleConflict(
                            rule_a_id=rule_a.id,
                            rule_b_id=rule_b.id,
                            severity=ConflictSeverity.HIGH,
                            conflict_type="contradictory_condition",
                            description=f"Rules have contradictory conditions on '{var_a}'",
                            resolution_suggestion="Review and consolidate validation logic",
                            affected_entities=[var_a]
                        )

        return None

    def _check_auth_conflict(
        self,
        rule_a: ExtractedRule,
        rule_b: ExtractedRule
    ) -> Optional[RuleConflict]:
        """Check for authorization rule conflicts."""
        shared = set(rule_a.entities) & set(rule_b.entities)
        if not shared:
            return None

        # Look for allow vs deny patterns
        allow_patterns = ['allow', 'grant', 'permit', 'can_', 'has_permission']
        deny_patterns = ['deny', 'revoke', 'forbid', 'cannot', 'no_permission']

        a_allows = any(p in rule_a.code_snippet.lower() for p in allow_patterns)
        a_denies = any(p in rule_a.code_snippet.lower() for p in deny_patterns)
        b_allows = any(p in rule_b.code_snippet.lower() for p in allow_patterns)
        b_denies = any(p in rule_b.code_snippet.lower() for p in deny_patterns)

        if (a_allows and b_denies) or (a_denies and b_allows):
            return RuleConflict(
                rule_a_id=rule_a.id,
                rule_b_id=rule_b.id,
                severity=ConflictSeverity.CRITICAL,
                conflict_type="authorization_conflict",
                description=f"Conflicting authorization rules for {shared}",
                resolution_suggestion="Establish clear authorization hierarchy",
                affected_entities=list(shared)
            )

        return None

    def _are_conflicting_ops(self, op_a: str, op_b: str) -> bool:
        """Check if two comparison operators conflict."""
        conflicts = {
            ('>',  '<'),
            ('>', '=='),
            ('<', '=='),
            ('>=', '<'),
            ('<=', '>'),
            ('==', '!='),
        }
        return (op_a, op_b) in conflicts or (op_b, op_a) in conflicts

    def _detect_specialization(
        self,
        rule_a: ExtractedRule,
        rule_b: ExtractedRule
    ) -> Optional[RuleDependency]:
        """Detect if one rule is a specialization of another."""
        if rule_a.category != rule_b.category:
            return None

        # Check if one rule's entities are a subset of another's
        entities_a = set(rule_a.entities)
        entities_b = set(rule_b.entities)

        if entities_a < entities_b:
            return RuleDependency(
                source_rule_id=rule_a.id,
                target_rule_id=rule_b.id,
                dependency_type=DependencyType.SPECIALIZES,
                confidence=0.6,
                reason=f"Rule A operates on subset of entities",
                shared_elements=list(entities_a)
            )
        elif entities_b < entities_a:
            return RuleDependency(
                source_rule_id=rule_b.id,
                target_rule_id=rule_a.id,
                dependency_type=DependencyType.SPECIALIZES,
                confidence=0.6,
                reason=f"Rule B operates on subset of entities",
                shared_elements=list(entities_b)
            )

        return None

    def get_execution_order(self, graph: RuleGraph) -> List[str]:
        """
        Determine optimal execution order for rules.

        Uses topological sort based on PRECEDES dependencies.
        """
        # Build dependency graph
        in_degree: Dict[str, int] = {rid: 0 for rid in graph.rules}
        adj: Dict[str, List[str]] = defaultdict(list)

        for dep in graph.dependencies:
            if dep.dependency_type == DependencyType.PRECEDES:
                adj[dep.source_rule_id].append(dep.target_rule_id)
                in_degree[dep.target_rule_id] += 1

        # Kahn's algorithm for topological sort
        queue = [rid for rid, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            rule_id = queue.pop(0)
            order.append(rule_id)

            for neighbor in adj[rule_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Handle cycles by adding remaining rules
        remaining = [rid for rid in graph.rules if rid not in order]
        order.extend(remaining)

        return order

    def export_graph(self, graph: RuleGraph, format: str = "json") -> str:
        """Export rule graph to specified format."""
        import json

        if format == "json":
            return json.dumps({
                "rules": {rid: r.to_dict() for rid, r in graph.rules.items()},
                "dependencies": [d.to_dict() for d in graph.dependencies],
                "conflicts": [c.to_dict() for c in graph.conflicts],
                "clusters": [list(c) for c in graph.get_rule_clusters()],
                "execution_order": self.get_execution_order(graph)
            }, indent=2, default=str)

        elif format == "mermaid":
            return self._to_mermaid(graph)

        elif format == "dot":
            return self._to_dot(graph)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def _to_mermaid(self, graph: RuleGraph) -> str:
        """Export as Mermaid diagram."""
        lines = ["graph TD"]

        # Add nodes with categories
        for rid, rule in graph.rules.items():
            label = f"{rid}[{rule.name}]"
            lines.append(f"    {label}")

        # Add dependency edges
        for dep in graph.dependencies:
            arrow = self._get_mermaid_arrow(dep.dependency_type)
            lines.append(f"    {dep.source_rule_id} {arrow} {dep.target_rule_id}")

        # Add conflict edges (dashed red)
        for conf in graph.conflicts:
            lines.append(f"    {conf.rule_a_id} -.-> |conflict| {conf.rule_b_id}")

        return '\n'.join(lines)

    def _get_mermaid_arrow(self, dep_type: DependencyType) -> str:
        """Get Mermaid arrow for dependency type."""
        arrows = {
            DependencyType.REQUIRES: "-->",
            DependencyType.PRECEDES: "-->",
            DependencyType.TRIGGERS: "==>",
            DependencyType.SPECIALIZES: "-.->",
            DependencyType.SHARES_ENTITY: "---",
            DependencyType.SHARES_STATE: "---",
            DependencyType.OVERRIDES: "-->|overrides|",
            DependencyType.CONFLICTS: "x--x",
        }
        return arrows.get(dep_type, "-->")

    def _to_dot(self, graph: RuleGraph) -> str:
        """Export as DOT (Graphviz) format."""
        lines = ["digraph RuleDependencies {"]
        lines.append("    rankdir=TB;")
        lines.append("    node [shape=box];")

        # Add nodes
        for rid, rule in graph.rules.items():
            color = self._get_category_color(rule.category)
            lines.append(f'    "{rid}" [label="{rule.name}" fillcolor="{color}" style="filled"];')

        # Add edges
        for dep in graph.dependencies:
            style = "solid" if dep.dependency_type == DependencyType.REQUIRES else "dashed"
            lines.append(f'    "{dep.source_rule_id}" -> "{dep.target_rule_id}" [style="{style}"];')

        # Add conflict edges
        for conf in graph.conflicts:
            lines.append(f'    "{conf.rule_a_id}" -> "{conf.rule_b_id}" [color="red" style="dashed"];')

        lines.append("}")
        return '\n'.join(lines)

    def _get_category_color(self, category: RuleCategory) -> str:
        """Get color for rule category."""
        colors = {
            RuleCategory.VALIDATION: "#90EE90",     # Light green
            RuleCategory.AUTHORIZATION: "#FFB6C1",  # Light pink
            RuleCategory.CALCULATION: "#87CEEB",    # Sky blue
            RuleCategory.WORKFLOW: "#DDA0DD",       # Plum
            RuleCategory.CONSTRAINT: "#F0E68C",     # Khaki
            RuleCategory.COMPLIANCE: "#FFA07A",     # Light salmon
        }
        return colors.get(category, "#FFFFFF")
