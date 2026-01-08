"""
Codex Thinking Extractor - Pseudo-thinking tag extraction

Week 61: CCTrace Integration

Codex CLI (OpenAI) doesn't provide native thinking blocks,
but we can extract reasoning from `<thinking>` tags in output
when models are prompted to use them.
"""

import re
from typing import Dict, Any, List
from app.services.thinking_extractors.base import BaseThinkingExtractor, ThinkingBlockData


class CodexThinkingExtractor(BaseThinkingExtractor):
    """
    Extract pseudo-thinking from Codex CLI responses.

    Codex doesn't have native thinking blocks, but we can:
    1. Use prompts that encourage `<thinking>` tag usage
    2. Parse these tags from the response
    3. Differentiate between thinking and final answer

    Response format (Codex CLI):
    {
        "id": "chatcmpl-...",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "<thinking>Let me analyze...</thinking>\\n\\nBased on..."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 200,
            "total_tokens": 300
        }
    }
    """

    # Regex patterns for thinking extraction
    THINKING_PATTERN = re.compile(
        r'<thinking>(.*?)</thinking>',
        re.DOTALL | re.IGNORECASE
    )
    REASONING_PATTERN = re.compile(
        r'<reasoning>(.*?)</reasoning>',
        re.DOTALL | re.IGNORECASE
    )
    ANALYSIS_PATTERN = re.compile(
        r'<analysis>(.*?)</analysis>',
        re.DOTALL | re.IGNORECASE
    )

    @property
    def provider_name(self) -> str:
        return "codex"

    def can_extract(self, response_data: Dict[str, Any]) -> bool:
        """
        Check if response contains extractable thinking tags.

        Args:
            response_data: Raw Codex CLI response

        Returns:
            True if thinking-like tags are present
        """
        content = self._get_content(response_data)
        if not content:
            return False

        # Check for any thinking-like tags
        return bool(
            self.THINKING_PATTERN.search(content) or
            self.REASONING_PATTERN.search(content) or
            self.ANALYSIS_PATTERN.search(content)
        )

    def extract(self, response_data: Dict[str, Any]) -> List[ThinkingBlockData]:
        """
        Extract thinking blocks from tagged content.

        Args:
            response_data: Raw Codex CLI response

        Returns:
            List of ThinkingBlockData from tags
        """
        blocks = []
        content = self._get_content(response_data)

        if not content:
            return blocks

        sequence = 0

        # Extract <thinking> tags
        for match in self.THINKING_PATTERN.finditer(content):
            thinking_content = match.group(1).strip()
            if thinking_content:
                blocks.append(ThinkingBlockData(
                    block_type="thinking",
                    content=thinking_content,
                    token_count=self._estimate_tokens(thinking_content),
                    sequence_number=sequence,
                    content_hash=self._create_content_hash(thinking_content),
                    extra_data={
                        "tag": "thinking",
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    }
                ))
                sequence += 1

        # Extract <reasoning> tags
        for match in self.REASONING_PATTERN.finditer(content):
            reasoning_content = match.group(1).strip()
            if reasoning_content:
                blocks.append(ThinkingBlockData(
                    block_type="reasoning",
                    content=reasoning_content,
                    token_count=self._estimate_tokens(reasoning_content),
                    sequence_number=sequence,
                    content_hash=self._create_content_hash(reasoning_content),
                    extra_data={
                        "tag": "reasoning",
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    }
                ))
                sequence += 1

        # Extract <analysis> tags
        for match in self.ANALYSIS_PATTERN.finditer(content):
            analysis_content = match.group(1).strip()
            if analysis_content:
                blocks.append(ThinkingBlockData(
                    block_type="reasoning",  # Treat as reasoning
                    content=analysis_content,
                    token_count=self._estimate_tokens(analysis_content),
                    sequence_number=sequence,
                    content_hash=self._create_content_hash(analysis_content),
                    extra_data={
                        "tag": "analysis",
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    }
                ))
                sequence += 1

        return blocks

    def _get_content(self, response_data: Dict[str, Any]) -> str:
        """
        Extract content string from Codex response structure.

        Handles both:
        - Standard OpenAI format: choices[0].message.content
        - Direct content format: content field
        """
        if not response_data:
            return ""

        # Try direct content
        if "content" in response_data and isinstance(response_data["content"], str):
            return response_data["content"]

        # Try OpenAI format
        choices = response_data.get("choices", [])
        if choices and isinstance(choices, list):
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message", {})
                if isinstance(message, dict):
                    return message.get("content", "")

        # Try text field (some formats)
        return response_data.get("text", "")

    def extract_token_info(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract token usage information from Codex response.

        Args:
            response_data: Raw Codex CLI response

        Returns:
            Dict with token counts
        """
        usage = response_data.get("usage", {})
        return {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
