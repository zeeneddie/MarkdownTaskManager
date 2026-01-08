"""
Ollama Thinking Extractor - Chain-of-Thought forcing with tag extraction

Week 61: CCTrace Integration

Ollama models don't have native thinking blocks, but we can:
1. Force Chain-of-Thought (CoT) via prompt templates
2. Parse `<thinking>` tags from the response
3. Extract step-by-step reasoning

This extractor also provides the CoT forcing prompt template
to be injected into requests.
"""

import re
from typing import Dict, Any, List, Optional
from app.services.thinking_extractors.base import BaseThinkingExtractor, ThinkingBlockData


class OllamaThinkingExtractor(BaseThinkingExtractor):
    """
    Extract Chain-of-Thought reasoning from Ollama responses.

    Works by:
    1. Providing COT_FORCING_PROMPT to prepend to system prompts
    2. Parsing `<thinking>` tags from model output
    3. Separating thinking from final answer

    Response format (Ollama):
    {
        "model": "qwen2.5-coder:7b",
        "response": "<thinking>Step 1: ...</thinking>\\n\\nFinal answer: ...",
        "done": true,
        "context": [...],
        "total_duration": 1234567890,
        "load_duration": 123456,
        "prompt_eval_count": 50,
        "prompt_eval_duration": 123456789,
        "eval_count": 100,
        "eval_duration": 987654321
    }

    OR streaming format:
    {
        "model": "...",
        "message": {
            "role": "assistant",
            "content": "..."
        },
        "done": true
    }
    """

    # CoT forcing prompt template to inject
    COT_FORCING_PROMPT = """Before answering, think through this step by step inside <thinking> tags.
Then provide your final answer outside the tags.

Example format:
<thinking>
Step 1: First, I'll analyze...
Step 2: Then, I'll consider...
Step 3: Finally, I'll conclude...
</thinking>

Based on my analysis, [your answer here]

"""

    # Alternative CoT prompt (more structured)
    COT_STRUCTURED_PROMPT = """You must reason through problems step-by-step using the following format:

<thinking>
1. Understanding: What is being asked?
2. Analysis: What are the key factors?
3. Approach: How should I solve this?
4. Execution: Implementing the solution
5. Verification: Is the solution correct?
</thinking>

[Your final answer here]

"""

    # Regex patterns
    THINKING_PATTERN = re.compile(
        r'<thinking>(.*?)</thinking>',
        re.DOTALL | re.IGNORECASE
    )
    STEP_PATTERN = re.compile(
        r'(?:Step\s*\d+[:.]\s*|^\d+[.)]\s*)(.*?)(?=(?:Step\s*\d+[:.]\s*|\d+[.)]\s*|$))',
        re.MULTILINE | re.DOTALL
    )

    @property
    def provider_name(self) -> str:
        return "ollama"

    @classmethod
    def get_cot_prompt(cls, structured: bool = False) -> str:
        """
        Get the CoT forcing prompt to inject into requests.

        Args:
            structured: Use more structured 5-step format

        Returns:
            Prompt string to prepend to system message
        """
        return cls.COT_STRUCTURED_PROMPT if structured else cls.COT_FORCING_PROMPT

    def can_extract(self, response_data: Dict[str, Any]) -> bool:
        """
        Check if response contains extractable thinking tags.

        Args:
            response_data: Raw Ollama response

        Returns:
            True if thinking-like content is present
        """
        content = self._get_content(response_data)
        if not content:
            return False

        return bool(self.THINKING_PATTERN.search(content))

    def extract(self, response_data: Dict[str, Any]) -> List[ThinkingBlockData]:
        """
        Extract thinking blocks from Ollama response.

        Args:
            response_data: Raw Ollama response

        Returns:
            List of ThinkingBlockData with CoT reasoning
        """
        blocks = []
        content = self._get_content(response_data)

        if not content:
            return blocks

        sequence = 0

        # Extract <thinking> tags
        for match in self.THINKING_PATTERN.finditer(content):
            thinking_content = match.group(1).strip()
            if not thinking_content:
                continue

            # Try to extract individual steps for richer analysis
            steps = self._extract_steps(thinking_content)

            blocks.append(ThinkingBlockData(
                block_type="cot",  # Chain of Thought
                content=thinking_content,
                token_count=self._estimate_tokens(thinking_content),
                sequence_number=sequence,
                content_hash=self._create_content_hash(thinking_content),
                extra_data={
                    "tag": "thinking",
                    "step_count": len(steps),
                    "steps": steps[:10],  # Limit stored steps
                    "model": response_data.get("model", "unknown"),
                    "start_pos": match.start(),
                    "end_pos": match.end()
                }
            ))
            sequence += 1

        return blocks

    def _get_content(self, response_data: Dict[str, Any]) -> str:
        """
        Extract content string from Ollama response structure.

        Handles both:
        - Non-streaming: response field
        - Streaming: message.content field
        """
        if not response_data:
            return ""

        # Try response field (non-streaming)
        if "response" in response_data:
            return response_data["response"]

        # Try message.content (streaming/chat)
        message = response_data.get("message", {})
        if isinstance(message, dict):
            return message.get("content", "")

        # Try direct content
        return response_data.get("content", "")

    def _extract_steps(self, thinking_content: str) -> List[str]:
        """
        Extract individual reasoning steps from thinking content.

        Args:
            thinking_content: The raw thinking text

        Returns:
            List of step descriptions
        """
        steps = []

        # Try numbered steps pattern
        lines = thinking_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Match "Step N:", "1.", "1)", etc.
            step_match = re.match(
                r'^(?:Step\s*(\d+)[:.]\s*|(\d+)[.)]\s*)(.*)',
                line,
                re.IGNORECASE
            )
            if step_match:
                step_content = step_match.group(3).strip()
                if step_content:
                    steps.append(step_content)
            elif line.startswith('-') or line.startswith('*'):
                # Bullet points
                step_content = line[1:].strip()
                if step_content:
                    steps.append(step_content)

        return steps

    def extract_timing_info(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract timing and token information from Ollama response.

        Args:
            response_data: Raw Ollama response

        Returns:
            Dict with timing and token metrics
        """
        return {
            "prompt_tokens": response_data.get("prompt_eval_count", 0),
            "completion_tokens": response_data.get("eval_count", 0),
            "total_duration_ns": response_data.get("total_duration", 0),
            "load_duration_ns": response_data.get("load_duration", 0),
            "prompt_eval_duration_ns": response_data.get("prompt_eval_duration", 0),
            "eval_duration_ns": response_data.get("eval_duration", 0),
            "model": response_data.get("model", "unknown"),
        }
