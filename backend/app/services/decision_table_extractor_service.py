"""
Decision Table Extractor Service - Fase 25: Business Logic Extraction

Extracts decision tables from nested IF-THEN-ELSE logic in legacy code
and converts them to DMN (Decision Model and Notation) format.

Features:
- Pattern detection for nested conditionals
- Condition matrix building
- DMN XML export
- Markdown table export
- JSON export
- Integration with existing BusinessRule extraction

Author: Claude Code (Week 138 - Fase 25)
Date: 2026-01-01
"""

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decision_table import (
    ActionEntry,
    ConditionEntry,
    ConditionOperator,
    DecisionRule,
    DecisionTable,
    DecisionTableExtractionResult,
    DecisionTableOutputFormat,
    DecisionTableStatistics,
    HitPolicy,
    InputColumn,
    OutputColumn,
)

logger = logging.getLogger(__name__)


@dataclass
class ConditionalPattern:
    """A detected conditional pattern in code"""
    pattern_type: str  # "if_else", "switch", "select_case", "ternary"
    condition: str
    branches: List[Dict[str, Any]] = field(default_factory=list)
    source_code: str = ""
    source_file: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    nesting_level: int = 0


class DecisionTableExtractorService:
    """
    Service for extracting decision tables from legacy code.

    Converts nested IF-THEN-ELSE, Select Case, and switch statements
    into structured decision tables in DMN format.
    """

    # Patterns for detecting conditional structures
    IF_ELSE_PATTERNS = {
        "vbnet": [
            r"If\s+(.+?)\s+Then\s*\n(.*?)(?:ElseIf\s+(.+?)\s+Then\s*\n(.*?))*(?:Else\s*\n(.*?))?End\s+If",
            r"IIf\s*\(\s*(.+?)\s*,\s*(.+?)\s*,\s*(.+?)\s*\)",
        ],
        "csharp": [
            r"if\s*\(\s*(.+?)\s*\)\s*\{(.*?)\}(?:\s*else\s+if\s*\(\s*(.+?)\s*\)\s*\{(.*?)\})*(?:\s*else\s*\{(.*?)\})?",
            r"(.+?)\s*\?\s*(.+?)\s*:\s*(.+?)",  # Ternary
        ],
        "python": [
            r"if\s+(.+?):\s*\n(.*?)(?:elif\s+(.+?):\s*\n(.*?))*(?:else:\s*\n(.*?))?",
            r"(.+?)\s+if\s+(.+?)\s+else\s+(.+?)",  # Ternary
        ],
        "javascript": [
            r"if\s*\(\s*(.+?)\s*\)\s*\{(.*?)\}(?:\s*else\s+if\s*\(\s*(.+?)\s*\)\s*\{(.*?)\})*(?:\s*else\s*\{(.*?)\})?",
            r"(.+?)\s*\?\s*(.+?)\s*:\s*(.+?)",
        ],
    }

    SWITCH_PATTERNS = {
        "vbnet": r"Select\s+Case\s+(.+?)\s*\n(.*?)End\s+Select",
        "csharp": r"switch\s*\(\s*(.+?)\s*\)\s*\{(.*?)\}",
        "javascript": r"switch\s*\(\s*(.+?)\s*\)\s*\{(.*?)\}",
        "python": r"match\s+(.+?):\s*\n(.*?)(?=\n\S|\Z)",  # Python 3.10+
    }

    CASE_PATTERNS = {
        "vbnet": r"Case\s+(.+?)\s*\n(.*?)(?=Case|End\s+Select)",
        "csharp": r"case\s+(.+?):\s*(.*?)(?=case|default|break|\})",
        "javascript": r"case\s+(.+?):\s*(.*?)(?=case|default|break|\})",
        "python": r"case\s+(.+?):\s*(.*?)(?=case|\Z)",
    }

    # Operator mapping from code to DMN
    OPERATOR_MAPPING = {
        "==": ConditionOperator.EQUALS,
        "=": ConditionOperator.EQUALS,
        "!=": ConditionOperator.NOT_EQUALS,
        "<>": ConditionOperator.NOT_EQUALS,
        ">": ConditionOperator.GREATER_THAN,
        ">=": ConditionOperator.GREATER_THAN_OR_EQUALS,
        "<": ConditionOperator.LESS_THAN,
        "<=": ConditionOperator.LESS_THAN_OR_EQUALS,
        "in": ConditionOperator.IN,
        "not in": ConditionOperator.NOT_IN,
        "Is Nothing": ConditionOperator.IS_NULL,
        "IsNot Nothing": ConditionOperator.IS_NOT_NULL,
        "is None": ConditionOperator.IS_NULL,
        "is not None": ConditionOperator.IS_NOT_NULL,
        "=== null": ConditionOperator.IS_NULL,
        "!== null": ConditionOperator.IS_NOT_NULL,
    }

    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize the service"""
        self.db = db
        self._sessions: Dict[str, DecisionTableExtractionResult] = {}

    async def create_session(
        self,
        project_id: Optional[str] = None,
        name: str = "Decision Table Extraction"
    ) -> str:
        """Create a new extraction session"""
        session_id = str(uuid4())
        result = DecisionTableExtractionResult(
            session_id=session_id,
            project_id=project_id,
            started_at=datetime.utcnow()
        )
        self._sessions[session_id] = result
        logger.info(f"Created decision table extraction session: {session_id}")
        return session_id

    async def get_session(self, session_id: str) -> Optional[DecisionTableExtractionResult]:
        """Get an extraction session by ID"""
        return self._sessions.get(session_id)

    async def extract_from_files(
        self,
        session_id: str,
        files: Dict[str, str],
        language: str = "vbnet",
        min_nesting: int = 2
    ) -> DecisionTableExtractionResult:
        """
        Extract decision tables from source files.

        Args:
            session_id: The extraction session ID
            files: Dict mapping file paths to file contents
            language: Programming language of the files
            min_nesting: Minimum nesting level to consider as decision table

        Returns:
            DecisionTableExtractionResult with extracted tables
        """
        result = self._sessions.get(session_id)
        if not result:
            result = DecisionTableExtractionResult(session_id=session_id)
            self._sessions[session_id] = result

        result.total_files_scanned = len(files)

        for file_path, content in files.items():
            try:
                tables = await self._extract_from_file(
                    content, file_path, language, min_nesting
                )
                if tables:
                    result.files_with_tables += 1
                    result.tables.extend(tables)
                    result.total_tables_extracted += len(tables)
                    for table in tables:
                        result.total_rules_extracted += len(table.rules)
            except Exception as e:
                logger.error(f"Error extracting from {file_path}: {e}")
                result.errors.append(f"{file_path}: {str(e)}")

        # Calculate average confidence
        if result.tables:
            result.average_confidence = sum(
                t.confidence for t in result.tables
            ) / len(result.tables)

        result.completed_at = datetime.utcnow()
        result.duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()

        logger.info(
            f"Extraction complete: {result.total_tables_extracted} tables, "
            f"{result.total_rules_extracted} rules"
        )
        return result

    async def _extract_from_file(
        self,
        content: str,
        file_path: str,
        language: str,
        min_nesting: int
    ) -> List[DecisionTable]:
        """Extract decision tables from a single file"""
        tables = []

        # Find nested conditionals
        patterns = await self._detect_conditional_patterns(
            content, language, file_path
        )

        # Filter by nesting level
        complex_patterns = [
            p for p in patterns if p.nesting_level >= min_nesting
        ]

        for pattern in complex_patterns:
            table = await self._build_decision_table(pattern, file_path)
            if table and len(table.rules) > 0:
                tables.append(table)

        # Also look for switch/select case statements
        switch_tables = await self._extract_switch_tables(
            content, file_path, language
        )
        tables.extend(switch_tables)

        return tables

    async def _detect_conditional_patterns(
        self,
        content: str,
        language: str,
        file_path: str
    ) -> List[ConditionalPattern]:
        """Detect conditional patterns in code"""
        patterns = []
        lang_patterns = self.IF_ELSE_PATTERNS.get(language, [])

        for regex in lang_patterns:
            try:
                for match in re.finditer(regex, content, re.DOTALL | re.IGNORECASE):
                    pattern = ConditionalPattern(
                        pattern_type="if_else",
                        condition=match.group(1) if match.group(1) else "",
                        source_code=match.group(0),
                        source_file=file_path,
                        line_start=content[:match.start()].count('\n') + 1,
                        line_end=content[:match.end()].count('\n') + 1,
                        nesting_level=self._count_nesting(match.group(0), language)
                    )

                    # Parse branches
                    pattern.branches = self._parse_if_branches(
                        match.group(0), language
                    )
                    patterns.append(pattern)
            except re.error as e:
                logger.warning(f"Regex error for pattern {regex}: {e}")

        return patterns

    def _count_nesting(self, code: str, language: str) -> int:
        """Count the nesting level of conditionals"""
        if language == "vbnet":
            return code.lower().count("if ") + code.lower().count("elseif ")
        elif language in ["csharp", "javascript"]:
            return code.count("if") + code.count("else if")
        elif language == "python":
            return code.count("if ") + code.count("elif ")
        return 1

    def _parse_if_branches(
        self,
        code: str,
        language: str
    ) -> List[Dict[str, Any]]:
        """Parse if/else branches into structured format"""
        branches = []

        if language == "vbnet":
            # Parse VB.NET If...ElseIf...Else...End If
            if_match = re.search(r"If\s+(.+?)\s+Then", code, re.IGNORECASE)
            if if_match:
                branches.append({
                    "condition": if_match.group(1).strip(),
                    "type": "if"
                })

            for elseif_match in re.finditer(
                r"ElseIf\s+(.+?)\s+Then", code, re.IGNORECASE
            ):
                branches.append({
                    "condition": elseif_match.group(1).strip(),
                    "type": "elseif"
                })

            if re.search(r"\bElse\b(?!\s*If)", code, re.IGNORECASE):
                branches.append({"condition": "default", "type": "else"})

        elif language in ["csharp", "javascript"]:
            # Parse C#/JS if...else if...else
            if_match = re.search(r"if\s*\(\s*(.+?)\s*\)", code)
            if if_match:
                branches.append({
                    "condition": if_match.group(1).strip(),
                    "type": "if"
                })

            for elseif_match in re.finditer(r"else\s+if\s*\(\s*(.+?)\s*\)", code):
                branches.append({
                    "condition": elseif_match.group(1).strip(),
                    "type": "elseif"
                })

            if re.search(r"\belse\s*\{", code):
                branches.append({"condition": "default", "type": "else"})

        elif language == "python":
            # Parse Python if...elif...else
            if_match = re.search(r"if\s+(.+?):", code)
            if if_match:
                branches.append({
                    "condition": if_match.group(1).strip(),
                    "type": "if"
                })

            for elif_match in re.finditer(r"elif\s+(.+?):", code):
                branches.append({
                    "condition": elif_match.group(1).strip(),
                    "type": "elif"
                })

            if re.search(r"\belse:", code):
                branches.append({"condition": "default", "type": "else"})

        return branches

    async def _build_decision_table(
        self,
        pattern: ConditionalPattern,
        file_path: str
    ) -> Optional[DecisionTable]:
        """Build a decision table from a conditional pattern"""
        if not pattern.branches:
            return None

        table = DecisionTable(
            name=self._generate_table_name(pattern, file_path),
            description=f"Decision table extracted from {file_path}",
            source_file=file_path,
            source_line_start=pattern.line_start,
            source_line_end=pattern.line_end,
            original_code=pattern.source_code,
            hit_policy=HitPolicy.FIRST  # Default to first-match
        )

        # Extract input columns from conditions
        variables = self._extract_variables_from_conditions(pattern.branches)
        for var_name in variables:
            input_col = InputColumn(
                name=self._normalize_variable_name(var_name),
                label=self._humanize_variable_name(var_name),
                source_variable=var_name,
                source_file=file_path
            )
            table.inputs.append(input_col)

        # Create output column (generic "result" for now)
        output_col = OutputColumn(
            name="result",
            label="Result",
            source_file=file_path
        )
        table.outputs.append(output_col)

        # Create rules from branches
        rule_num = 1
        for branch in pattern.branches:
            rule = DecisionRule(
                rule_number=rule_num,
                annotation=branch.get("condition", ""),
                source_file=file_path,
                confidence=0.8 if branch["type"] != "else" else 0.9
            )

            # Parse condition into entries
            if branch["condition"] != "default":
                condition_entries = self._parse_condition_string(
                    branch["condition"], table.inputs
                )
                rule.conditions = condition_entries
            else:
                # Default/else branch - match any
                for inp in table.inputs:
                    rule.conditions.append(ConditionEntry(
                        column_id=inp.id,
                        operator=ConditionOperator.ANY,
                        expression="-"
                    ))

            # Add action entry
            rule.actions.append(ActionEntry(
                column_id=output_col.id,
                value=f"branch_{rule_num}",
                expression=branch.get("condition", "default")
            ))

            table.rules.append(rule)
            rule_num += 1

        # Calculate statistics
        table.statistics = self._calculate_statistics(table)
        table.confidence = self._calculate_confidence(table)

        return table

    def _extract_variables_from_conditions(
        self,
        branches: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract variable names from condition strings"""
        variables = set()
        var_pattern = r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b"

        # Common keywords to exclude
        keywords = {
            "if", "else", "elseif", "elif", "then", "end", "and", "or", "not",
            "true", "false", "null", "none", "nothing", "is", "isnot",
            "andalso", "orelse", "like", "typeof", "instanceof"
        }

        for branch in branches:
            condition = branch.get("condition", "")
            if condition == "default":
                continue

            for match in re.finditer(var_pattern, condition):
                var = match.group(1)
                if var.lower() not in keywords and not var.isdigit():
                    variables.add(var)

        return sorted(list(variables))

    def _normalize_variable_name(self, name: str) -> str:
        """Normalize variable name to snake_case"""
        # Remove common prefixes
        prefixes = ["str", "int", "bln", "dbl", "obj", "dt", "arr"]
        result = name
        for prefix in prefixes:
            if result.lower().startswith(prefix) and len(result) > len(prefix):
                result = result[len(prefix):]
                break

        # Convert to snake_case
        result = re.sub(r'([A-Z])', r'_\1', result).lower()
        result = re.sub(r'^_', '', result)
        result = re.sub(r'__+', '_', result)
        return result

    def _humanize_variable_name(self, name: str) -> str:
        """Convert variable name to human-readable label"""
        normalized = self._normalize_variable_name(name)
        return normalized.replace("_", " ").title()

    def _parse_condition_string(
        self,
        condition: str,
        inputs: List[InputColumn]
    ) -> List[ConditionEntry]:
        """Parse a condition string into condition entries"""
        entries = []

        # Split by AND/OR (simplified parsing)
        parts = re.split(r'\s+(?:And|AndAlso|Or|OrElse|&&|\|\|)\s+', condition, flags=re.IGNORECASE)

        for part in parts:
            entry = self._parse_single_condition(part.strip(), inputs)
            if entry:
                entries.append(entry)

        return entries

    def _parse_single_condition(
        self,
        condition: str,
        inputs: List[InputColumn]
    ) -> Optional[ConditionEntry]:
        """Parse a single condition into a ConditionEntry"""
        # Try to match common comparison patterns
        comparison_pattern = r"(.+?)\s*(==|!=|<>|>=|<=|>|<|=)\s*(.+)"
        match = re.match(comparison_pattern, condition.strip())

        if match:
            left = match.group(1).strip()
            operator_str = match.group(2).strip()
            right = match.group(3).strip()

            # Find matching input column
            column_id = None
            for inp in inputs:
                if inp.source_variable and inp.source_variable.lower() == left.lower():
                    column_id = inp.id
                    break

            if not column_id and inputs:
                column_id = inputs[0].id  # Default to first input

            operator = self.OPERATOR_MAPPING.get(operator_str, ConditionOperator.EQUALS)

            return ConditionEntry(
                column_id=column_id or "",
                operator=operator,
                value=right.strip('"\''),
                expression=condition
            )

        return None

    async def _extract_switch_tables(
        self,
        content: str,
        file_path: str,
        language: str
    ) -> List[DecisionTable]:
        """Extract decision tables from switch/select case statements"""
        tables = []
        switch_pattern = self.SWITCH_PATTERNS.get(language)
        case_pattern = self.CASE_PATTERNS.get(language)

        if not switch_pattern or not case_pattern:
            return tables

        try:
            for switch_match in re.finditer(switch_pattern, content, re.DOTALL | re.IGNORECASE):
                switch_var = switch_match.group(1).strip()
                switch_body = switch_match.group(2)

                table = DecisionTable(
                    name=f"Switch_{self._normalize_variable_name(switch_var)}",
                    description=f"Switch statement on {switch_var}",
                    source_file=file_path,
                    source_line_start=content[:switch_match.start()].count('\n') + 1,
                    source_line_end=content[:switch_match.end()].count('\n') + 1,
                    original_code=switch_match.group(0),
                    hit_policy=HitPolicy.UNIQUE
                )

                # Create input column for switch variable
                input_col = InputColumn(
                    name=self._normalize_variable_name(switch_var),
                    label=self._humanize_variable_name(switch_var),
                    source_variable=switch_var,
                    source_file=file_path
                )
                table.inputs.append(input_col)

                # Create output column
                output_col = OutputColumn(
                    name="action",
                    label="Action",
                    source_file=file_path
                )
                table.outputs.append(output_col)

                # Parse case statements
                rule_num = 1
                for case_match in re.finditer(case_pattern, switch_body, re.DOTALL | re.IGNORECASE):
                    case_value = case_match.group(1).strip()

                    rule = DecisionRule(
                        rule_number=rule_num,
                        annotation=f"Case {case_value}",
                        source_file=file_path,
                        confidence=0.9
                    )

                    rule.conditions.append(ConditionEntry(
                        column_id=input_col.id,
                        operator=ConditionOperator.EQUALS,
                        value=case_value.strip('"\''),
                        expression=case_value
                    ))

                    rule.actions.append(ActionEntry(
                        column_id=output_col.id,
                        value=f"case_{rule_num}",
                        expression=case_value
                    ))

                    table.rules.append(rule)
                    rule_num += 1

                if table.rules:
                    table.statistics = self._calculate_statistics(table)
                    table.confidence = self._calculate_confidence(table)
                    tables.append(table)

        except re.error as e:
            logger.warning(f"Regex error parsing switch statements: {e}")

        return tables

    def _generate_table_name(
        self,
        pattern: ConditionalPattern,
        file_path: str
    ) -> str:
        """Generate a meaningful name for the decision table"""
        # Try to extract meaningful name from condition
        if pattern.condition:
            # Get first variable in condition
            var_match = re.search(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", pattern.condition)
            if var_match:
                return f"Decision_{self._normalize_variable_name(var_match.group(1))}"

        # Fall back to file name + line number
        import os
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        return f"Decision_{base_name}_{pattern.line_start}"

    def _calculate_statistics(self, table: DecisionTable) -> DecisionTableStatistics:
        """Calculate statistics for a decision table"""
        stats = DecisionTableStatistics(
            total_rules=len(table.rules),
            total_inputs=len(table.inputs),
            total_outputs=len(table.outputs),
        )

        # Count unique conditions
        unique_conditions = set()
        for rule in table.rules:
            for cond in rule.conditions:
                unique_conditions.add((cond.column_id, cond.operator, str(cond.value)))
        stats.unique_conditions = len(unique_conditions)

        # Calculate complexity score
        stats.complexity_score = stats.total_rules * stats.total_inputs

        # Check for default rule (else branch)
        stats.has_default_rule = any(
            any(c.operator == ConditionOperator.ANY for c in rule.conditions)
            for rule in table.rules
        )

        return stats

    def _calculate_confidence(self, table: DecisionTable) -> float:
        """Calculate overall confidence for a decision table"""
        if not table.rules:
            return 0.0

        rule_confidences = [r.confidence for r in table.rules]
        avg_confidence = sum(rule_confidences) / len(rule_confidences)

        # Boost confidence if we have good structure
        if table.statistics:
            if table.statistics.has_default_rule:
                avg_confidence = min(1.0, avg_confidence + 0.05)
            if table.statistics.total_rules >= 3:
                avg_confidence = min(1.0, avg_confidence + 0.05)

        return round(avg_confidence, 2)

    # Export Methods

    async def export_to_dmn_xml(self, table: DecisionTable) -> str:
        """Export decision table to DMN 1.3 XML format"""
        # Create DMN namespace
        ns = "https://www.omg.org/spec/DMN/20191111/MODEL/"

        definitions = ET.Element("definitions", {
            "xmlns": ns,
            "id": f"definitions_{table.id}",
            "name": table.name,
            "namespace": "http://decision-tables.example.com"
        })

        # Decision element
        decision = ET.SubElement(definitions, "decision", {
            "id": f"decision_{table.id}",
            "name": table.name
        })

        # Decision table
        decision_table = ET.SubElement(decision, "decisionTable", {
            "id": f"dt_{table.id}",
            "hitPolicy": table.hit_policy.value
        })

        # Inputs
        for inp in table.inputs:
            input_elem = ET.SubElement(decision_table, "input", {
                "id": f"input_{inp.id}",
                "label": inp.label
            })
            input_expr = ET.SubElement(input_elem, "inputExpression", {
                "id": f"expr_{inp.id}",
                "typeRef": inp.type_ref
            })
            text = ET.SubElement(input_expr, "text")
            text.text = inp.name

        # Outputs
        for out in table.outputs:
            output_elem = ET.SubElement(decision_table, "output", {
                "id": f"output_{out.id}",
                "label": out.label,
                "name": out.name,
                "typeRef": out.type_ref
            })

        # Rules
        for rule in table.rules:
            rule_elem = ET.SubElement(decision_table, "rule", {
                "id": f"rule_{rule.id}"
            })

            # Input entries
            for cond in rule.conditions:
                input_entry = ET.SubElement(rule_elem, "inputEntry", {
                    "id": f"entry_{cond.column_id}_{rule.id}"
                })
                text = ET.SubElement(input_entry, "text")
                if cond.operator == ConditionOperator.ANY:
                    text.text = "-"
                elif cond.operator == ConditionOperator.EQUALS:
                    text.text = f'"{cond.value}"' if isinstance(cond.value, str) else str(cond.value)
                else:
                    text.text = f"{cond.operator.value} {cond.value}"

            # Output entries
            for action in rule.actions:
                output_entry = ET.SubElement(rule_elem, "outputEntry", {
                    "id": f"action_{action.column_id}_{rule.id}"
                })
                text = ET.SubElement(output_entry, "text")
                text.text = str(action.value)

            # Annotation
            if rule.annotation:
                annotation = ET.SubElement(rule_elem, "annotationEntry")
                text = ET.SubElement(annotation, "text")
                text.text = rule.annotation

        return ET.tostring(definitions, encoding="unicode", xml_declaration=True)

    async def export_to_markdown(self, table: DecisionTable) -> str:
        """Export decision table to Markdown format"""
        lines = []

        # Header
        lines.append(f"# Decision Table: {table.name}")
        lines.append("")
        lines.append(f"**Description:** {table.description}")
        lines.append(f"**Hit Policy:** {table.hit_policy.name}")
        lines.append(f"**Source:** {table.source_file}:{table.source_line_start}-{table.source_line_end}")
        lines.append("")

        # Build table header
        headers = ["#"]
        for inp in table.inputs:
            headers.append(inp.label or inp.name)
        for out in table.outputs:
            headers.append(out.label or out.name)
        headers.append("Annotation")

        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["---"] * len(headers)) + "|")

        # Build table rows
        for rule in table.rules:
            row = [str(rule.rule_number)]

            # Conditions
            cond_map = {c.column_id: c for c in rule.conditions}
            for inp in table.inputs:
                cond = cond_map.get(inp.id)
                if cond:
                    if cond.operator == ConditionOperator.ANY:
                        row.append("-")
                    elif cond.operator == ConditionOperator.EQUALS:
                        row.append(str(cond.value))
                    else:
                        row.append(f"{cond.operator.value} {cond.value}")
                else:
                    row.append("-")

            # Actions
            action_map = {a.column_id: a for a in rule.actions}
            for out in table.outputs:
                action = action_map.get(out.id)
                row.append(str(action.value) if action else "-")

            # Annotation
            row.append(rule.annotation or "")

            lines.append("| " + " | ".join(row) + " |")

        # Statistics
        if table.statistics:
            lines.append("")
            lines.append("## Statistics")
            lines.append("")
            lines.append(f"- Total Rules: {table.statistics.total_rules}")
            lines.append(f"- Total Inputs: {table.statistics.total_inputs}")
            lines.append(f"- Total Outputs: {table.statistics.total_outputs}")
            lines.append(f"- Complexity Score: {table.statistics.complexity_score}")
            lines.append(f"- Has Default Rule: {'Yes' if table.statistics.has_default_rule else 'No'}")

        return "\n".join(lines)

    async def export_to_json(self, table: DecisionTable) -> Dict[str, Any]:
        """Export decision table to JSON format"""
        return table.to_dict()

    async def export_tables(
        self,
        session_id: str,
        format: DecisionTableOutputFormat = DecisionTableOutputFormat.MARKDOWN
    ) -> str:
        """Export all tables from a session"""
        result = self._sessions.get(session_id)
        if not result:
            raise ValueError(f"Session {session_id} not found")

        outputs = []

        for table in result.tables:
            if format == DecisionTableOutputFormat.DMN_XML:
                outputs.append(await self.export_to_dmn_xml(table))
            elif format == DecisionTableOutputFormat.MARKDOWN:
                outputs.append(await self.export_to_markdown(table))
            elif format == DecisionTableOutputFormat.DMN_JSON:
                import json
                outputs.append(json.dumps(await self.export_to_json(table), indent=2))

        separator = "\n\n---\n\n" if format == DecisionTableOutputFormat.MARKDOWN else "\n"
        return separator.join(outputs)
