"""
Documentation Rule Extractor Service - Week 131

Extracts business rules from markdown documentation files and correlates
them with code-extracted rules.

Extraction patterns:
- Rule prefixes: Rule:, Business Rule:, Regel:, BR-
- Numbered lists: 1. IF x THEN y, 2. When x => y
- Markdown tables: | Condition | Action |
- RFC 2119 keywords: MUST, SHALL, SHOULD, MAY

Agent: Peter (Product Owner)
"""
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
import logging

from app.models.week131_research import (
    DocumentationRule,
    DocumentationExtractionResult,
    RuleType,
)

logger = logging.getLogger(__name__)


# Rule prefix patterns (multilingual)
RULE_PREFIX_PATTERNS = [
    # English
    (r'(?:Business\s+)?Rule\s*[:：]\s*(.+)', 0.9),
    (r'BR[-\s]?(\d+)\s*[:：]\s*(.+)', 0.95),
    (r'Requirement\s*[:：]\s*(.+)', 0.85),
    (r'Constraint\s*[:：]\s*(.+)', 0.85),
    (r'Policy\s*[:：]\s*(.+)', 0.8),
    # Dutch
    (r'(?:Bedrijfs)?Regel\s*[:：]\s*(.+)', 0.9),
    (r'Vereiste\s*[:：]\s*(.+)', 0.85),
    (r'Beperking\s*[:：]\s*(.+)', 0.85),
    (r'Beleid\s*[:：]\s*(.+)', 0.8),
    # German
    (r'(?:Geschäfts)?Regel\s*[:：]\s*(.+)', 0.9),
    (r'Anforderung\s*[:：]\s*(.+)', 0.85),
]

# RFC 2119 keywords and their implications
RFC_2119_KEYWORDS = {
    'MUST': (RuleType.VALIDATION, 1.0),
    'MUST NOT': (RuleType.VALIDATION, 1.0),
    'SHALL': (RuleType.VALIDATION, 0.95),
    'SHALL NOT': (RuleType.VALIDATION, 0.95),
    'SHOULD': (RuleType.RECOMMENDATION, 0.8),
    'SHOULD NOT': (RuleType.RECOMMENDATION, 0.8),
    'MAY': (RuleType.OPTIONAL, 0.6),
    'REQUIRED': (RuleType.VALIDATION, 0.9),
    'RECOMMENDED': (RuleType.RECOMMENDATION, 0.75),
    'OPTIONAL': (RuleType.OPTIONAL, 0.5),
    # Dutch equivalents
    'MOET': (RuleType.VALIDATION, 0.95),
    'MAG': (RuleType.OPTIONAL, 0.6),
    'KAN': (RuleType.OPTIONAL, 0.5),
    'VERPLICHT': (RuleType.VALIDATION, 0.9),
}

# Conditional patterns for IF-THEN rules
CONDITIONAL_PATTERNS = [
    # English patterns
    (r'IF\s+(.+?)\s+THEN\s+(.+?)(?:\.|$)', RuleType.CONDITION),
    (r'WHEN\s+(.+?)\s+(?:THEN\s+)?(.+?)(?:\.|$)', RuleType.CONDITION),
    (r'UNLESS\s+(.+?)\s*[,]\s*(.+?)(?:\.|$)', RuleType.CONDITION),
    (r'(?:IN CASE|IN CASE OF)\s+(.+?)\s*[,]\s*(.+?)(?:\.|$)', RuleType.CONDITION),
    # Dutch patterns
    (r'ALS\s+(.+?)\s+DAN\s+(.+?)(?:\.|$)', RuleType.CONDITION),
    (r'WANNEER\s+(.+?)\s+(?:DAN\s+)?(.+?)(?:\.|$)', RuleType.CONDITION),
    (r'INDIEN\s+(.+?)\s*[,]\s*(.+?)(?:\.|$)', RuleType.CONDITION),
    (r'TENZIJ\s+(.+?)\s*[,]\s*(.+?)(?:\.|$)', RuleType.CONDITION),
    # Symbol patterns
    (r'(.+?)\s*=>\s*(.+?)(?:\.|$)', RuleType.CONDITION),
    (r'(.+?)\s*->\s*(.+?)(?:\.|$)', RuleType.CONDITION),
]

# Rule type indicators
RULE_TYPE_PATTERNS = {
    RuleType.VALIDATION: [
        r'valid', r'validat', r'check', r'verify', r'ensure',
        r'controleer', r'valideer',
    ],
    RuleType.AUTHORIZATION: [
        r'authoriz', r'access', r'permission', r'role', r'right',
        r'autorisatie', r'toegang', r'rechten', r'rol',
    ],
    RuleType.CALCULATION: [
        r'calculat', r'compute', r'formula', r'sum', r'total', r'percentage',
        r'bereken', r'formule', r'som', r'totaal',
    ],
    RuleType.CONSTRAINT: [
        r'must be', r'cannot', r'limit', r'restrict', r'maximum', r'minimum',
        r'moet zijn', r'kan niet', r'limiet', r'beperking',
    ],
    RuleType.DEFAULT: [
        r'default', r'initially', r'by default',
        r'standaard', r'initieel',
    ],
    RuleType.WORKFLOW: [
        r'workflow', r'process', r'step', r'stage', r'state',
        r'werkstroom', r'proces', r'stap', r'fase',
    ],
    RuleType.NOTIFICATION: [
        r'notify', r'alert', r'email', r'message', r'send',
        r'notificatie', r'melding', r'bericht', r'verstuur',
    ],
}


class DocumentationRuleExtractorService:
    """
    Extracts business rules from documentation files (markdown, text, etc.)
    and correlates them with rules extracted from code.
    """

    def __init__(self):
        self._rule_counter = 0
        self._current_section = ""

    def extract_from_directory(
        self,
        path: Path,
        code_rules: Optional[List[Dict[str, Any]]] = None,
        include_extensions: Optional[List[str]] = None,
    ) -> DocumentationExtractionResult:
        """
        Extract rules from all documentation files in a directory.

        Args:
            path: Directory path to scan
            code_rules: Optional list of rules extracted from code for correlation
            include_extensions: File extensions to include (default: .md, .txt, .rst)

        Returns:
            DocumentationExtractionResult with extracted rules
        """
        start_time = time.time()
        self._rule_counter = 0
        errors: List[str] = []

        if not path.exists():
            return DocumentationExtractionResult(
                success=False,
                errors=[f"Path does not exist: {path}"],
            )

        if include_extensions is None:
            include_extensions = ['.md', '.txt', '.rst', '.adoc', '.doc']

        # Collect documentation files
        doc_files = []
        for ext in include_extensions:
            doc_files.extend(path.rglob(f'*{ext}'))

        # Also check common documentation locations
        doc_dirs = ['docs', 'doc', 'documentation', 'specifications', 'specs']
        for doc_dir in doc_dirs:
            for ext in include_extensions:
                doc_files.extend(path.rglob(f'{doc_dir}/**/*{ext}'))

        # Deduplicate
        doc_files = list(set(doc_files))

        all_rules: List[DocumentationRule] = []

        for doc_file in doc_files:
            try:
                content = self._read_file_safe(doc_file)
                if content:
                    rules = self._extract_from_file(doc_file, content)
                    all_rules.extend(rules)
            except Exception as e:
                errors.append(f"Error processing {doc_file}: {e}")

        # Correlate with code rules if provided
        if code_rules:
            for rule in all_rules:
                related, conflicts = self._correlate_with_code_rules(rule, code_rules)
                rule.related_code_rules = related
                rule.conflicts = conflicts

        # Calculate statistics
        by_type = {}
        by_confidence = {'high': 0, 'medium': 0, 'low': 0}

        for rule in all_rules:
            rt = rule.rule_type.value if isinstance(rule.rule_type, RuleType) else str(rule.rule_type)
            by_type[rt] = by_type.get(rt, 0) + 1

            if rule.confidence >= 0.8:
                by_confidence['high'] += 1
            elif rule.confidence >= 0.5:
                by_confidence['medium'] += 1
            else:
                by_confidence['low'] += 1

        duration_ms = int((time.time() - start_time) * 1000)

        # Calculate additional statistics
        code_rule_matches = sum(len(r.related_code_rules) for r in all_rules)
        conflicts_detected = sum(1 for r in all_rules if r.conflicts)

        return DocumentationExtractionResult(
            success=True,
            rules=all_rules,
            files_processed=[str(f) for f in doc_files],
            rules_by_type=by_type,
            code_rule_matches=code_rule_matches,
            conflicts_detected=conflicts_detected,
            duration_ms=duration_ms,
            errors=errors,
        )

    def _read_file_safe(self, file_path: Path) -> Optional[str]:
        """Read file content safely."""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue
        return None

    def _generate_rule_id(self) -> str:
        """Generate unique documentation rule ID."""
        self._rule_counter += 1
        return f"DOC-BR-{self._rule_counter:03d}"

    def _extract_from_file(
        self,
        file_path: Path,
        content: str,
    ) -> List[DocumentationRule]:
        """Extract rules from a single documentation file."""
        rules: List[DocumentationRule] = []

        # Parse markdown structure for section tracking
        sections = self._parse_sections(content)

        # Extract using different patterns
        rules.extend(self._extract_rule_prefixes(content, file_path, sections))
        rules.extend(self._extract_rfc2119_rules(content, file_path, sections))
        rules.extend(self._extract_conditional_rules(content, file_path, sections))
        rules.extend(self._extract_numbered_list_rules(content, file_path, sections))
        rules.extend(self._extract_table_rules(content, file_path, sections))

        # Deduplicate rules by content similarity
        rules = self._deduplicate_rules(rules)

        return rules

    def _parse_sections(self, content: str) -> Dict[int, str]:
        """Parse markdown headings to track section context."""
        sections = {}
        current_section = ""
        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Match markdown headings
            heading_match = re.match(r'^(#{1,6})\s+(.+)', line)
            if heading_match:
                level = len(heading_match.group(1))
                heading = heading_match.group(2).strip()
                if level <= 2:
                    current_section = heading
                else:
                    current_section = f"{current_section} > {heading}"

            sections[i + 1] = current_section

        return sections

    def _get_section_for_line(self, line_num: int, sections: Dict[int, str]) -> str:
        """Get the section heading for a given line number."""
        for ln in range(line_num, 0, -1):
            if ln in sections and sections[ln]:
                return sections[ln]
        return ""

    def _extract_rule_prefixes(
        self,
        content: str,
        file_path: Path,
        sections: Dict[int, str],
    ) -> List[DocumentationRule]:
        """Extract rules that start with explicit rule prefixes."""
        rules = []

        for pattern, confidence in RULE_PREFIX_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1

                # Handle BR-xxx pattern with separate ID
                if 'BR[-\\s]?' in pattern:
                    rule_num = match.group(1)
                    rule_text = match.group(2).strip()
                    rule_id = f"DOC-BR-{rule_num}"
                else:
                    rule_text = match.group(1).strip()
                    rule_id = self._generate_rule_id()

                # Parse condition and action
                condition, action = self._parse_rule_parts(rule_text)
                rule_type = self._infer_rule_type(rule_text)

                rule = DocumentationRule(
                    rule_id=rule_id,
                    rule_type=rule_type,
                    condition=condition,
                    action=action,
                    natural_language=rule_text,
                    source_file=str(file_path),
                    source_section=self._get_section_for_line(line_num, sections),
                    source_line=line_num,
                    extraction_pattern='rule_prefix',
                    confidence=confidence,
                )
                rules.append(rule)

        return rules

    def _extract_rfc2119_rules(
        self,
        content: str,
        file_path: Path,
        sections: Dict[int, str],
    ) -> List[DocumentationRule]:
        """Extract rules containing RFC 2119 keywords."""
        rules = []

        for keyword, (rule_type, base_confidence) in RFC_2119_KEYWORDS.items():
            # Match sentences containing the keyword
            pattern = rf'([^.]*\b{re.escape(keyword)}\b[^.]*\.)'

            for match in re.finditer(pattern, content, re.IGNORECASE):
                sentence = match.group(1).strip()
                line_num = content[:match.start()].count('\n') + 1

                # Adjust confidence based on context
                confidence = base_confidence
                if self._get_section_for_line(line_num, sections):
                    confidence = min(1.0, confidence + 0.05)

                condition, action = self._parse_rule_parts(sentence)

                rule = DocumentationRule(
                    rule_id=self._generate_rule_id(),
                    rule_type=rule_type,
                    condition=condition,
                    action=action,
                    natural_language=sentence,
                    source_file=str(file_path),
                    source_section=self._get_section_for_line(line_num, sections),
                    source_line=line_num,
                    extraction_pattern='rfc2119',
                    confidence=confidence,
                )
                rules.append(rule)

        return rules

    def _extract_conditional_rules(
        self,
        content: str,
        file_path: Path,
        sections: Dict[int, str],
    ) -> List[DocumentationRule]:
        """Extract IF-THEN and similar conditional rules."""
        rules = []

        for pattern, rule_type in CONDITIONAL_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1

                condition = match.group(1).strip()
                action = match.group(2).strip()
                full_text = match.group(0).strip()

                # Higher confidence for explicit IF-THEN patterns
                confidence = 0.85

                rule = DocumentationRule(
                    rule_id=self._generate_rule_id(),
                    rule_type=rule_type,
                    condition=condition,
                    action=action,
                    natural_language=full_text,
                    source_file=str(file_path),
                    source_section=self._get_section_for_line(line_num, sections),
                    source_line=line_num,
                    extraction_pattern='conditional',
                    confidence=confidence,
                )
                rules.append(rule)

        return rules

    def _extract_numbered_list_rules(
        self,
        content: str,
        file_path: Path,
        sections: Dict[int, str],
    ) -> List[DocumentationRule]:
        """Extract rules from numbered lists."""
        rules = []

        # Match numbered list items
        list_pattern = r'^[\s]*(\d+)[.\)]\s+(.+)$'

        for match in re.finditer(list_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            list_text = match.group(2).strip()

            # Only extract if it looks like a rule
            if not self._looks_like_rule(list_text):
                continue

            condition, action = self._parse_rule_parts(list_text)
            rule_type = self._infer_rule_type(list_text)

            # Lower confidence for numbered lists
            confidence = 0.6

            # Boost confidence if in a "rules" section
            section = self._get_section_for_line(line_num, sections)
            if section and any(kw in section.lower() for kw in ['rule', 'regel', 'requirement', 'vereiste']):
                confidence = 0.8

            rule = DocumentationRule(
                rule_id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=condition,
                action=action,
                natural_language=list_text,
                source_file=str(file_path),
                source_section=section,
                source_line=line_num,
                extraction_pattern='numbered_list',
                confidence=confidence,
            )
            rules.append(rule)

        return rules

    def _extract_table_rules(
        self,
        content: str,
        file_path: Path,
        sections: Dict[int, str],
    ) -> List[DocumentationRule]:
        """Extract rules from markdown tables."""
        rules = []

        # Find markdown tables
        table_pattern = r'\|(.+)\|[\r\n]+\|[-:\s|]+\|[\r\n]+((?:\|.+\|[\r\n]?)+)'

        for match in re.finditer(table_pattern, content):
            line_num = content[:match.start()].count('\n') + 1

            # Parse header
            header = [h.strip() for h in match.group(1).split('|') if h.strip()]

            # Check if this looks like a rules table
            is_rules_table = any(
                kw in ' '.join(header).lower()
                for kw in ['condition', 'action', 'rule', 'requirement', 'voorwaarde', 'actie', 'regel']
            )

            if not is_rules_table:
                continue

            # Find condition and action columns
            condition_col = None
            action_col = None
            for i, h in enumerate(header):
                h_lower = h.lower()
                if any(kw in h_lower for kw in ['condition', 'if', 'when', 'voorwaarde', 'als', 'wanneer']):
                    condition_col = i
                if any(kw in h_lower for kw in ['action', 'then', 'result', 'actie', 'dan', 'resultaat']):
                    action_col = i

            if condition_col is None or action_col is None:
                continue

            # Parse rows
            rows = match.group(2).strip().split('\n')
            for row in rows:
                cells = [c.strip() for c in row.split('|') if c.strip()]
                if len(cells) > max(condition_col, action_col):
                    condition = cells[condition_col]
                    action = cells[action_col]

                    rule = DocumentationRule(
                        rule_id=self._generate_rule_id(),
                        rule_type=RuleType.CONDITION,
                        condition=condition,
                        action=action,
                        natural_language=f"IF {condition} THEN {action}",
                        source_file=str(file_path),
                        source_section=self._get_section_for_line(line_num, sections),
                        source_line=line_num,
                        extraction_pattern='table',
                        confidence=0.85,
                    )
                    rules.append(rule)

        return rules

    def _looks_like_rule(self, text: str) -> bool:
        """Check if text looks like a business rule."""
        text_lower = text.lower()

        # Must have reasonable length
        if len(text) < 10 or len(text) > 500:
            return False

        # Check for rule indicators
        rule_indicators = [
            'must', 'shall', 'should', 'may', 'cannot', 'can not',
            'if', 'when', 'unless', 'only',
            'required', 'allowed', 'forbidden', 'prohibited',
            'valid', 'invalid', 'check', 'verify',
            'moet', 'mag', 'kan', 'alleen', 'verplicht',
            'geldig', 'ongeldig', 'controleer',
        ]

        return any(indicator in text_lower for indicator in rule_indicators)

    def _parse_rule_parts(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse a rule text into condition and action parts."""
        # Try to find IF-THEN structure
        if_then = re.search(r'(?:IF|WHEN|ALS|WANNEER|INDIEN)\s+(.+?)\s+(?:THEN|DAN)\s+(.+)', text, re.IGNORECASE)
        if if_then:
            return if_then.group(1).strip(), if_then.group(2).strip()

        # Try arrow notation
        arrow = re.search(r'(.+?)\s*(?:=>|->)\s*(.+)', text)
        if arrow:
            return arrow.group(1).strip(), arrow.group(2).strip()

        # No clear structure - return full text as action
        return None, text

    def _infer_rule_type(self, text: str) -> RuleType:
        """Infer the rule type from the text content."""
        text_lower = text.lower()

        # Check each rule type's patterns
        for rule_type, patterns in RULE_TYPE_PATTERNS.items():
            if any(pattern in text_lower for pattern in patterns):
                return rule_type

        # Default to VALIDATION for MUST/SHALL, CONDITION for IF/WHEN
        if any(kw in text.upper() for kw in ['MUST', 'SHALL', 'REQUIRED', 'MOET', 'VERPLICHT']):
            return RuleType.VALIDATION
        if any(kw in text.upper() for kw in ['IF', 'WHEN', 'ALS', 'WANNEER']):
            return RuleType.CONDITION

        return RuleType.GENERAL

    def _deduplicate_rules(self, rules: List[DocumentationRule]) -> List[DocumentationRule]:
        """Remove duplicate rules based on content similarity."""
        unique_rules = []
        seen_texts: Set[str] = set()

        for rule in rules:
            # Normalize text for comparison
            normalized = rule.natural_language.lower().strip()
            normalized = re.sub(r'\s+', ' ', normalized)

            if normalized not in seen_texts:
                seen_texts.add(normalized)
                unique_rules.append(rule)
            else:
                # Keep the one with higher confidence
                for i, existing in enumerate(unique_rules):
                    existing_norm = re.sub(r'\s+', ' ', existing.natural_language.lower().strip())
                    if existing_norm == normalized and rule.confidence > existing.confidence:
                        unique_rules[i] = rule
                        break

        return unique_rules

    def _correlate_with_code_rules(
        self,
        doc_rule: DocumentationRule,
        code_rules: List[Dict[str, Any]],
    ) -> Tuple[List[str], List[str]]:
        """
        Correlate a documentation rule with code-extracted rules.

        Returns:
            Tuple of (related_rule_ids, conflict_ids)
        """
        related = []
        conflicts = []

        doc_text = doc_rule.natural_language.lower()
        doc_condition = (doc_rule.condition or "").lower()
        doc_action = (doc_rule.action or "").lower()

        for code_rule in code_rules:
            code_id = code_rule.get('rule_id', code_rule.get('id', ''))
            code_text = code_rule.get('natural_language', code_rule.get('description', '')).lower()
            code_condition = code_rule.get('condition', '').lower()
            code_action = code_rule.get('action', '').lower()

            # Calculate similarity
            text_similarity = self._calculate_similarity(doc_text, code_text)
            condition_similarity = self._calculate_similarity(doc_condition, code_condition) if doc_condition and code_condition else 0
            action_similarity = self._calculate_similarity(doc_action, code_action) if doc_action and code_action else 0

            # Determine relationship
            if text_similarity > 0.7 or (condition_similarity > 0.6 and action_similarity > 0.6):
                related.append(code_id)
            elif condition_similarity > 0.6 and action_similarity < 0.3:
                # Same condition but different action = potential conflict
                conflicts.append(code_id)

        return related, conflicts

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple word overlap similarity."""
        if not text1 or not text2:
            return 0.0

        words1 = set(re.findall(r'\w+', text1))
        words2 = set(re.findall(r'\w+', text2))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def detect_conflicts(
        self,
        rules: List[DocumentationRule],
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts between documentation rules themselves.

        Returns list of conflict descriptions.
        """
        conflicts = []

        for i, rule1 in enumerate(rules):
            for rule2 in rules[i+1:]:
                # Check for same condition but different action
                if rule1.condition and rule2.condition:
                    cond_sim = self._calculate_similarity(
                        rule1.condition.lower(),
                        rule2.condition.lower()
                    )
                    if cond_sim > 0.7:
                        action_sim = self._calculate_similarity(
                            (rule1.action or "").lower(),
                            (rule2.action or "").lower()
                        )
                        if action_sim < 0.3:
                            conflicts.append({
                                'rule1_id': rule1.rule_id,
                                'rule2_id': rule2.rule_id,
                                'conflict_type': 'contradicting_actions',
                                'description': f"Rules have similar conditions but different actions",
                                'rule1_source': f"{rule1.source_file}:{rule1.source_line}",
                                'rule2_source': f"{rule2.source_file}:{rule2.source_line}",
                            })

        return conflicts
