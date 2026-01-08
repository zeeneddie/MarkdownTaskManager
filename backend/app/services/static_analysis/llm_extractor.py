# backend/app/services/static_analysis/llm_extractor.py
"""
LLM Rule Extractor - Extracts business rules from comments and natural language.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline (Phase 2.5)

Features:
- Extracts rules from code comments (VBScript, SQL, VB.NET)
- Detects rules from MsgBox/alert text with business meaning
- Identifies authorization messages and user prompts
- Creates structured BusinessRule from unstructured text

Use Cases:
1. Comment Extraction - `' Check if user has permission` → authorization rule
2. MsgBox Analysis - MsgBox "U heeft geen rechten" → authorization rule
3. SQL Comments - -- Validate date range → scheduling rule
"""

import logging
import json
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from .extraction_models import (
    BusinessRule,
    RuleType,
    ExtractionTier,
    ExtractionMethod,
    Language,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractedRule:
    """A rule extracted by LLM from comments/text."""
    rule_type: RuleType
    condition: str
    action: str
    natural_language: str
    confidence: float
    source_text: str          # Original comment/text
    line_number: int
    variables: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)


@dataclass
class LLMExtractionResult:
    """Result of LLM-based rule extraction."""
    rules: List[ExtractedRule]
    provider_used: str
    tokens_used: int = 0
    cost_cents: float = 0.0
    success: bool = True
    error: Optional[str] = None


# Tier to provider mapping for extraction
TIER_EXTRACTION_PROVIDERS: Dict[ExtractionTier, List[str]] = {
    ExtractionTier.FREE: [],
    ExtractionTier.BASIC: ["ollama"],
    ExtractionTier.STANDARD: ["ollama", "groq", "gemini"],
    ExtractionTier.PROFESSIONAL: ["ollama", "groq", "gemini", "openai"],
    ExtractionTier.PREMIUM: ["ollama", "groq", "gemini", "openai", "anthropic"],
}


# Prompt for extracting rules from comments
COMMENT_EXTRACTION_PROMPT = """You are an expert at extracting business rules from code comments.

Analyze the following code comments and extract any business rules they describe.

LANGUAGE: {language}
FILE: {source_file}

COMMENTS TO ANALYZE:
{comments}

For each business rule found, provide:
- rule_type: validation|authorization|scheduling|workflow|branching|threshold|data_access|state_management|error_handling|navigation|calculation|constraint|derivation
- condition: The IF/WHEN condition
- action: The THEN/result action
- natural_language: Clear business description
- confidence: 0.0-1.0 how certain this is a business rule
- line_number: Which line this came from
- variables: Any variable names mentioned
- entities: Any business entities (Client, Afspraak, Order, etc.)

Respond in JSON:
{{
    "rules": [
        {{
            "rule_type": "authorization",
            "condition": "User does not have permission",
            "action": "Deny access",
            "natural_language": "User must have VIEW permission to see agenda",
            "confidence": 0.85,
            "line_number": 123,
            "variables": ["intCanView", "tablePermissions"],
            "entities": ["User", "Agenda"]
        }}
    ]
}}

Only respond with the JSON, no other text. If no rules found, return {{"rules": []}}."""


# Prompt for extracting rules from user messages (MsgBox, alert, etc.)
MESSAGE_EXTRACTION_PROMPT = """You are an expert at extracting business rules from user-facing messages in code.

Analyze the following user messages (MsgBox, Response.Write, alert, etc.) and extract any business rules they reveal.

LANGUAGE: {language}
FILE: {source_file}

MESSAGES TO ANALYZE:
{messages}

Messages often reveal business rules through:
- Error messages: "U heeft geen rechten" → authorization rule
- Validation messages: "Datum moet in de toekomst liggen" → validation rule
- Confirmation prompts: "Wilt u de afspraak verwijderen?" → workflow rule

For each business rule found, provide:
- rule_type: validation|authorization|scheduling|workflow|data_access|error_handling
- condition: What triggers this message
- action: What the message indicates happens
- natural_language: Clear business description (translate Dutch if needed)
- confidence: 0.0-1.0 certainty
- line_number: Source line
- variables: Variables in the message
- entities: Business entities mentioned

Respond in JSON:
{{
    "rules": [
        {{
            "rule_type": "authorization",
            "condition": "User lacks required permission",
            "action": "Display 'No rights to modify' message and deny action",
            "natural_language": "User must have EDIT permission to modify records",
            "confidence": 0.80,
            "line_number": 456,
            "variables": [],
            "entities": ["User"]
        }}
    ]
}}

Only respond with JSON. If no rules found, return {{"rules": []}}."""


class LLMRuleExtractor:
    """
    Extracts business rules from comments and user messages using LLM.

    Provides:
    - Comment-based rule extraction
    - Message/MsgBox analysis
    - Natural language to structured rule conversion
    - Multi-language support
    """

    # Patterns to find comments in different languages
    COMMENT_PATTERNS: Dict[Language, List[str]] = {
        Language.VBNET: [
            r"'(.+)$",                          # VB comment
            r"'''(.+)$",                        # Doc comment
            r"REM\s+(.+)$",                     # Old style
        ],
        Language.CLASSIC_ASP: [
            r"'(.+)$",                          # VBScript comment
            r"<%--(.+?)--%>",                   # ASP comment
        ],
        Language.TSQL: [
            r"--(.+)$",                         # Single line
            r"/\*(.+?)\*/",                     # Multi-line
        ],
        Language.PLSQL: [
            r"--(.+)$",                         # Single line
            r"/\*(.+?)\*/",                     # Multi-line
        ],
    }

    # Patterns to find user messages
    MESSAGE_PATTERNS: Dict[Language, List[str]] = {
        Language.VBNET: [
            r'MsgBox\s*\(\s*["\'](.+?)["\']\s*[,)]',   # MsgBox("text")
            r'MsgBox\s+["\'](.+?)["\']',               # MsgBox "text" (no parens)
            r'MessageBox\.Show\s*\(\s*["\'](.+?)["\']\s*[,)]',
        ],
        Language.CLASSIC_ASP: [
            r'MsgBox\s*\(\s*["\'](.+?)["\']\s*[,)]',   # MsgBox("text")
            r'MsgBox\s+["\'](.+?)["\']',               # MsgBox "text" (no parens)
            r'Response\.Write\s*\(\s*["\'](.+?)["\']\s*\)',
            r'alert\s*\(\s*["\'](.+?)["\']\s*\)',
        ],
        Language.TSQL: [
            r'RAISERROR\s*\(\s*["\'](.+?)["\']\s*,',
            r'PRINT\s+["\'](.+?)["\']\s*',
        ],
        Language.PLSQL: [
            r'RAISE_APPLICATION_ERROR\s*\([^,]+,\s*["\'](.+?)["\']\)',
            r'DBMS_OUTPUT\.PUT_LINE\s*\(\s*["\'](.+?)["\']\)',
        ],
    }

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.STANDARD,
    ):
        """
        Initialize the extractor.

        Args:
            extraction_tier: Customer tier determining LLM access
        """
        self.extraction_tier = extraction_tier
        self._registry = None

    def _get_registry(self):
        """Lazy load provider registry."""
        if self._registry is None:
            try:
                from app.providers.registry import get_registry
                self._registry = get_registry()
            except ImportError:
                logger.warning("Provider registry not available")
        return self._registry

    def get_available_providers(self) -> List[str]:
        """Get available providers for current tier."""
        return TIER_EXTRACTION_PROVIDERS.get(self.extraction_tier, [])

    def extract_comments(
        self,
        source_code: str,
        language: Language,
    ) -> List[Dict[str, Any]]:
        """
        Extract comments from source code.

        Args:
            source_code: The source code to analyze
            language: Programming language

        Returns:
            List of {text: str, line: int} dicts
        """
        comments = []
        patterns = self.COMMENT_PATTERNS.get(language, [])

        for line_num, line in enumerate(source_code.split('\n'), 1):
            for pattern in patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    text = match.strip()
                    if text and len(text) > 5:  # Skip trivial comments
                        comments.append({
                            "text": text,
                            "line": line_num,
                        })

        return comments

    def extract_messages(
        self,
        source_code: str,
        language: Language,
    ) -> List[Dict[str, Any]]:
        """
        Extract user messages from source code.

        Args:
            source_code: The source code to analyze
            language: Programming language

        Returns:
            List of {text: str, line: int} dicts
        """
        messages = []
        patterns = self.MESSAGE_PATTERNS.get(language, [])

        for line_num, line in enumerate(source_code.split('\n'), 1):
            for pattern in patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    text = match.strip()
                    if text and len(text) > 3:
                        messages.append({
                            "text": text,
                            "line": line_num,
                        })

        return messages

    async def extract_rules_from_comments(
        self,
        source_code: str,
        language: Language,
        source_file: str,
    ) -> LLMExtractionResult:
        """
        Extract business rules from code comments using LLM.

        Args:
            source_code: Source code containing comments
            language: Programming language
            source_file: File path for context

        Returns:
            LLMExtractionResult with extracted rules
        """
        # Extract comments first
        comments = self.extract_comments(source_code, language)

        if not comments:
            return LLMExtractionResult(
                rules=[],
                provider_used="none",
                success=True,
            )

        # Format comments for prompt
        comments_text = "\n".join([
            f"Line {c['line']}: {c['text']}"
            for c in comments
        ])

        return await self._extract_with_llm(
            prompt_template=COMMENT_EXTRACTION_PROMPT,
            content=comments_text,
            language=language,
            source_file=source_file,
            source_items=comments,
        )

    async def extract_rules_from_messages(
        self,
        source_code: str,
        language: Language,
        source_file: str,
    ) -> LLMExtractionResult:
        """
        Extract business rules from user messages using LLM.

        Args:
            source_code: Source code containing messages
            language: Programming language
            source_file: File path for context

        Returns:
            LLMExtractionResult with extracted rules
        """
        # Extract messages first
        messages = self.extract_messages(source_code, language)

        if not messages:
            return LLMExtractionResult(
                rules=[],
                provider_used="none",
                success=True,
            )

        # Format messages for prompt
        messages_text = "\n".join([
            f"Line {m['line']}: {m['text']}"
            for m in messages
        ])

        return await self._extract_with_llm(
            prompt_template=MESSAGE_EXTRACTION_PROMPT,
            content=messages_text,
            language=language,
            source_file=source_file,
            source_items=messages,
        )

    async def _extract_with_llm(
        self,
        prompt_template: str,
        content: str,
        language: Language,
        source_file: str,
        source_items: List[Dict],
    ) -> LLMExtractionResult:
        """Internal method to call LLM for extraction."""
        providers = self.get_available_providers()
        if not providers:
            logger.debug(f"No LLM providers for tier {self.extraction_tier.value}")
            return LLMExtractionResult(
                rules=[],
                provider_used="none",
                success=True,
            )

        registry = self._get_registry()
        if not registry:
            return LLMExtractionResult(
                rules=[],
                provider_used="none",
                success=False,
                error="Provider registry not available",
            )

        # Select provider (prefer Gemini for NL understanding if available)
        if "gemini" in providers:
            provider_name = "gemini"
        elif "groq" in providers:
            provider_name = "groq"
        else:
            provider_name = providers[0]

        provider = registry.get_provider(provider_name)
        if not provider:
            return LLMExtractionResult(
                rules=[],
                provider_used=provider_name,
                success=False,
                error=f"Provider {provider_name} not available",
            )

        # Build prompt
        if "comments" in prompt_template.lower():
            prompt = prompt_template.format(
                language=language.value,
                source_file=source_file,
                comments=content,
            )
        else:
            prompt = prompt_template.format(
                language=language.value,
                source_file=source_file,
                messages=content,
            )

        try:
            from app.providers.base import LLMRequest

            request = LLMRequest(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.2,
            )

            response = await provider.generate(request)

            if not response.success:
                return LLMExtractionResult(
                    rules=[],
                    provider_used=provider_name,
                    tokens_used=response.token_input + response.token_output,
                    cost_cents=response.cost_cents,
                    success=False,
                    error=response.error,
                )

            # Parse response
            rules = self._parse_extraction_response(
                response.content,
                source_items,
            )

            return LLMExtractionResult(
                rules=rules,
                provider_used=provider_name,
                tokens_used=response.token_input + response.token_output,
                cost_cents=response.cost_cents,
                success=True,
            )

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return LLMExtractionResult(
                rules=[],
                provider_used=provider_name,
                success=False,
                error=str(e),
            )

    def _parse_extraction_response(
        self,
        content: str,
        source_items: List[Dict],
    ) -> List[ExtractedRule]:
        """Parse LLM response into ExtractedRule objects."""
        try:
            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                return []

            data = json.loads(json_match.group())
            raw_rules = data.get("rules", [])

            rules = []
            for raw in raw_rules:
                try:
                    rule_type = RuleType(raw.get("rule_type", "validation"))
                except ValueError:
                    rule_type = RuleType.VALIDATION

                line_num = raw.get("line_number", 0)

                # Find source text from line number
                source_text = ""
                for item in source_items:
                    if item["line"] == line_num:
                        source_text = item["text"]
                        break

                rules.append(ExtractedRule(
                    rule_type=rule_type,
                    condition=raw.get("condition", ""),
                    action=raw.get("action", ""),
                    natural_language=raw.get("natural_language", ""),
                    confidence=float(raw.get("confidence", 0.7)),
                    source_text=source_text,
                    line_number=line_num,
                    variables=raw.get("variables", []),
                    entities=raw.get("entities", []),
                ))

            return rules

        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM extraction response as JSON")
            return []

    def convert_to_business_rules(
        self,
        extracted_rules: List[ExtractedRule],
        source_file: str,
        language: Language,
        id_prefix: str = "BR-LLM",
    ) -> List[BusinessRule]:
        """
        Convert ExtractedRules to BusinessRule objects.

        Args:
            extracted_rules: Rules from LLM extraction
            source_file: Source file path
            language: Programming language
            id_prefix: Prefix for rule IDs

        Returns:
            List of BusinessRule objects
        """
        business_rules = []

        for i, ext in enumerate(extracted_rules, 1):
            br = BusinessRule(
                id=f"{id_prefix}-{i:03d}",
                rule_type=ext.rule_type,
                condition=ext.condition,
                action=ext.action,
                source_file=source_file,
                source_lines=(ext.line_number, ext.line_number),
                confidence=ext.confidence,
                natural_language=ext.natural_language,
                variables_involved=ext.variables,
                related_entities=ext.entities,
                language=language,
                extraction_method=ExtractionMethod.LLM,
                code_snippet=ext.source_text,
            )
            business_rules.append(br)

        return business_rules


# Convenience function
async def extract_rules_from_source(
    source_code: str,
    language: Language,
    source_file: str,
    tier: ExtractionTier = ExtractionTier.STANDARD,
) -> List[BusinessRule]:
    """
    Extract business rules from source code using LLM.

    Args:
        source_code: Source code to analyze
        language: Programming language
        source_file: File path
        tier: Customer extraction tier

    Returns:
        List of BusinessRule objects
    """
    extractor = LLMRuleExtractor(extraction_tier=tier)

    # Extract from both comments and messages
    comment_result = await extractor.extract_rules_from_comments(
        source_code, language, source_file
    )
    message_result = await extractor.extract_rules_from_messages(
        source_code, language, source_file
    )

    all_extracted = comment_result.rules + message_result.rules

    return extractor.convert_to_business_rules(
        all_extracted,
        source_file,
        language,
    )
