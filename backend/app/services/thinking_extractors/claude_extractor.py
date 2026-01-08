"""
Claude Thinking Extractor - Native thinking block extraction

Week 61: CCTrace Integration

Claude CLI provides native `thinking` blocks with:
- Content: The actual reasoning
- Signature: Cryptographic signature for verification
- Type: "thinking" block type in content array
"""

from typing import Dict, Any, List
from app.services.thinking_extractors.base import BaseThinkingExtractor, ThinkingBlockData


class ClaudeThinkingExtractor(BaseThinkingExtractor):
    """
    Extract native thinking blocks from Claude CLI responses.

    Claude's extended thinking feature provides structured thinking
    blocks that can be directly extracted from the response JSON.

    Response format (Claude CLI with extended thinking):
    {
        "content": [
            {
                "type": "thinking",
                "thinking": "Let me analyze this step by step...",
                "signature": "abc123..."  # Optional cryptographic signature
            },
            {
                "type": "text",
                "text": "Based on my analysis..."
            }
        ],
        "model": "claude-3-opus-...",
        "usage": {
            "input_tokens": 100,
            "output_tokens": 200,
            "cache_creation_input_tokens": 50,
            "cache_read_input_tokens": 25
        }
    }
    """

    @property
    def provider_name(self) -> str:
        return "claude"

    def can_extract(self, response_data: Dict[str, Any]) -> bool:
        """
        Check if response contains Claude thinking blocks.

        Args:
            response_data: Raw Claude CLI response

        Returns:
            True if thinking blocks are present
        """
        if not response_data:
            return False

        content = response_data.get("content", [])
        if not isinstance(content, list):
            return False

        return any(
            block.get("type") == "thinking"
            for block in content
            if isinstance(block, dict)
        )

    def extract(self, response_data: Dict[str, Any]) -> List[ThinkingBlockData]:
        """
        Extract native thinking blocks from Claude response.

        Args:
            response_data: Raw Claude CLI response

        Returns:
            List of ThinkingBlockData with content, signature, and hash
        """
        blocks = []

        if not response_data:
            return blocks

        content = response_data.get("content", [])
        if not isinstance(content, list):
            return blocks

        for i, block in enumerate(content):
            if not isinstance(block, dict):
                continue

            if block.get("type") == "thinking":
                thinking_content = block.get("thinking", "")

                if not thinking_content:
                    continue

                blocks.append(ThinkingBlockData(
                    block_type="thinking",
                    content=thinking_content,
                    token_count=self._estimate_tokens(thinking_content),
                    sequence_number=i,
                    signature=block.get("signature"),  # Claude provides this
                    content_hash=self._create_content_hash(thinking_content),
                    extra_data={
                        "original_index": i,
                        "has_signature": block.get("signature") is not None
                    }
                ))

        return blocks

    def extract_token_cache_info(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract token cache information from Claude response.

        Args:
            response_data: Raw Claude CLI response

        Returns:
            Dict with cache_creation and cache_read token counts
        """
        usage = response_data.get("usage", {})
        return {
            "cache_creation": usage.get("cache_creation_input_tokens", 0),
            "cache_read": usage.get("cache_read_input_tokens", 0),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
        }
