"""
Extraction LLM Adapter - Week 83

Unified LLM interface for the Deep Extraction Pipeline.
Supports parallel execution, cost tracking, and multiple providers.

Providers:
- Ollama (local): qwen2.5-coder, deepseek-r1, codellama
- Groq: llama-3.1-8b, qwen3-32b
- Alibaba: qwen-turbo, qwen-plus
- Google: gemini-2.0-flash-lite, gemini-2.5-flash, gemini-2.5-pro
- OpenAI: gpt-5.2
- Anthropic: claude-opus-4.5
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import aiohttp

from app.config import settings
from app.services.tier_provider_selector import (
    TierProviderSelector,
    LLMCallResult,
    PROVIDER_COSTS,
)


logger = logging.getLogger(__name__)


# ============================================================================
# EXTRACTION PROMPTS
# ============================================================================

class ExtractionPrompts:
    """Prompts for different analysis types in Cycle 1."""

    SYSTEM_BASE = """You are an expert software analyst. Analyze the provided codebase and extract structured information.
Your output MUST be valid JSON matching the specified schema. Do not include any text outside the JSON object."""

    @staticmethod
    def get_architecture_prompt(code_summary: str, file_list: List[str]) -> str:
        """Prompt for architecture analysis (system structure, patterns)."""
        return f"""Analyze the following codebase for ARCHITECTURE patterns.

## Code Summary
{code_summary}

## Files ({len(file_list)} total)
{chr(10).join(file_list[:50])}
{"... and more" if len(file_list) > 50 else ""}

## Task
Extract:
1. High-level system architecture (layers, modules, services)
2. Design patterns used (MVC, Repository, Factory, etc.)
3. Major components and their responsibilities
4. Integration points and external dependencies

## Output Schema
Return JSON:
{{
    "epics": [
        {{
            "title": "Epic title",
            "description": "What this epic covers",
            "business_value": "Why this matters",
            "estimated_complexity": "low|medium|high",
            "features": ["Feature 1", "Feature 2"]
        }}
    ],
    "architecture_notes": {{
        "patterns": ["Pattern 1", "Pattern 2"],
        "layers": ["Layer 1", "Layer 2"],
        "key_components": ["Component 1", "Component 2"]
    }}
}}"""

    @staticmethod
    def get_business_logic_prompt(code_summary: str, file_list: List[str]) -> str:
        """Prompt for business logic analysis (use cases, workflows)."""
        return f"""Analyze the following codebase for BUSINESS LOGIC and user workflows.

## Code Summary
{code_summary}

## Files ({len(file_list)} total)
{chr(10).join(file_list[:50])}

## Task
Extract:
1. User-facing features and capabilities
2. Business workflows and processes
3. User roles and permissions
4. Core use cases

## Output Schema
Return JSON:
{{
    "features": [
        {{
            "title": "Feature title",
            "description": "What this feature does",
            "user_type": "Who uses this",
            "stories": [
                {{
                    "title": "As a [user], I want [goal] so that [benefit]",
                    "acceptance_criteria": ["Criterion 1", "Criterion 2"],
                    "estimated_points": 3
                }}
            ]
        }}
    ],
    "business_rules": ["Rule 1", "Rule 2"],
    "user_workflows": ["Workflow 1", "Workflow 2"]
}}"""

    @staticmethod
    def get_security_prompt(code_summary: str, file_list: List[str]) -> str:
        """Prompt for security analysis (vulnerabilities, risks)."""
        return f"""Analyze the following codebase for SECURITY concerns.

## Code Summary
{code_summary}

## Files ({len(file_list)} total)
{chr(10).join(file_list[:50])}

## Task
Extract:
1. Authentication and authorization mechanisms
2. Data validation and sanitization
3. Potential security vulnerabilities
4. Security-related technical tasks

## Output Schema
Return JSON:
{{
    "security_features": [
        {{
            "title": "Security feature",
            "description": "What it protects",
            "implementation_status": "implemented|partial|missing"
        }}
    ],
    "tasks": [
        {{
            "title": "Security task",
            "description": "What needs to be done",
            "task_type": "security",
            "priority": "critical|high|medium|low",
            "estimated_hours": 4
        }}
    ],
    "vulnerabilities": ["Potential issue 1", "Potential issue 2"],
    "recommendations": ["Recommendation 1", "Recommendation 2"]
}}"""

    @staticmethod
    def get_code_structure_prompt(code_summary: str, file_list: List[str]) -> str:
        """Prompt for code structure analysis (files, dependencies)."""
        return f"""Analyze the following codebase for CODE STRUCTURE and technical tasks.

## Code Summary
{code_summary}

## Files ({len(file_list)} total)
{chr(10).join(file_list[:50])}

## Task
Extract:
1. File organization and module structure
2. Dependencies and imports
3. Technical debt and refactoring needs
4. Testing requirements

## Output Schema
Return JSON:
{{
    "tasks": [
        {{
            "title": "Technical task",
            "description": "What needs to be done",
            "task_type": "backend|frontend|database|testing|devops",
            "estimated_hours": 2,
            "files_affected": ["file1.py", "file2.py"]
        }}
    ],
    "technical_debt": [
        {{
            "issue": "Debt description",
            "impact": "low|medium|high",
            "effort_to_fix": "low|medium|high"
        }}
    ],
    "dependencies": ["Dependency 1", "Dependency 2"],
    "test_coverage_gaps": ["Gap 1", "Gap 2"]
}}"""

    @staticmethod
    def get_synthesis_prompt(
        accepted_items: List[Dict[str, Any]],
        tier: str,
        project_info: Dict[str, Any],
    ) -> str:
        """
        Prompt for Cycle 5 final synthesis (PREMIUM tier uses Claude Opus).

        Generates:
        - Validated Epic→Feature→Story→Task hierarchy
        - Confidence explanations per item
        - Function point estimates per Story/Task
        """
        items_json = json.dumps(accepted_items, indent=2, default=str)

        return f"""You are performing FINAL SYNTHESIS for a code extraction analysis.

## Project Information
- Name: {project_info.get('name', 'Unknown')}
- Tier: {tier}
- Total Files: {project_info.get('total_files', 0)}
- Source Path: {project_info.get('source_path', 'Unknown')}

## Accepted Items from Multi-LLM Analysis
The following items were extracted by multiple LLMs and validated:

{items_json}

## Your Task

Create a FINAL, VALIDATED hierarchy with the following requirements:

### 1. Hierarchy Structure
Organize all items into a proper Epic → Feature → Story → Task structure.
- Each Epic should contain related Features
- Each Feature should contain User Stories
- Each Story should have Technical Tasks

### 2. Confidence Explanations
For EACH Epic and Feature, provide a confidence_explanation that includes:
- How many LLMs agreed on this item
- What evidence supports its inclusion
- Any caveats or uncertainties

### 3. Function Point Estimates
For EACH Story and Task, provide function_points estimate using IFPUG methodology:
- Stories: 5-20 FP typical range
- Tasks: 1-8 FP typical range
- Include brief rationale

### 4. Acceptance Criteria
Ensure each Story has clear acceptance criteria.

## Output Schema
Return JSON:
{{
    "synthesis_metadata": {{
        "tier": "{tier}",
        "synthesized_at": "ISO timestamp",
        "total_confidence": 0.0-1.0,
        "synthesis_notes": "Any important observations"
    }},
    "epics": [
        {{
            "id": "EPIC-001",
            "title": "Epic Title",
            "description": "What this epic covers",
            "business_value": "Why this matters",
            "confidence_score": 0.85,
            "confidence_explanation": "8/10 LLMs identified this epic. Strong evidence from auth modules...",
            "total_function_points": 150,
            "features": [
                {{
                    "id": "FEAT-001",
                    "title": "Feature Title",
                    "description": "Feature description",
                    "confidence_score": 0.82,
                    "confidence_explanation": "Identified by 6/10 LLMs based on...",
                    "stories": [
                        {{
                            "id": "STORY-001",
                            "title": "As a [user], I want [goal] so that [benefit]",
                            "acceptance_criteria": ["AC1", "AC2"],
                            "function_points": 8,
                            "fp_rationale": "1 EI (login form) + 1 EO (user profile) = 8 FP",
                            "story_points": 5,
                            "tasks": [
                                {{
                                    "id": "TASK-001",
                                    "title": "Implement login endpoint",
                                    "task_type": "backend",
                                    "function_points": 3,
                                    "estimated_hours": 4
                                }}
                            ]
                        }}
                    ]
                }}
            ]
        }}
    ],
    "summary": {{
        "total_epics": 0,
        "total_features": 0,
        "total_stories": 0,
        "total_tasks": 0,
        "total_function_points": 0,
        "avg_confidence": 0.0
    }}
}}

IMPORTANT: Return ONLY valid JSON. No markdown, no explanation text outside JSON."""

    @staticmethod
    def get_enrichment_prompt(original_analysis: Dict[str, Any], analysis_type: str) -> str:
        """Prompt for Cycle 2 cross-enrichment."""
        return f"""Review the following {analysis_type} analysis and suggest improvements.

## Original Analysis
{json.dumps(original_analysis, indent=2)}

## Task
1. Identify any MISSING items that should be added
2. Suggest MODIFICATIONS to improve existing items
3. Flag any items that seem INCORRECT or inconsistent

## Output Schema
Return JSON:
{{
    "additions": [
        {{
            "item_type": "epic|feature|story|task",
            "item": {{...}}  // Full item definition
        }}
    ],
    "modifications": [
        {{
            "original_title": "Title of item to modify",
            "suggested_changes": {{
                "field": "new_value"
            }},
            "reasoning": "Why this change"
        }}
    ],
    "concerns": [
        {{
            "item_title": "Title of concerning item",
            "concern": "What's wrong",
            "suggestion": "How to fix"
        }}
    ],
    "confidence_adjustments": {{
        "item_title": 0.85  // Adjusted confidence score
    }}
}}"""


# ============================================================================
# LLM ADAPTER
# ============================================================================

class ExtractionLLMAdapter:
    """
    Unified adapter for calling LLMs in the Deep Extraction Pipeline.

    Supports:
    - Multiple providers (Ollama, Groq, Google, OpenAI, Anthropic)
    - Parallel execution
    - Automatic retry with fallback
    - Cost tracking
    - JSON response parsing

    Usage:
        adapter = ExtractionLLMAdapter(selector)

        # Single call
        result = await adapter.call_llm(
            provider_id="ollama/qwen2.5-coder:7b",
            prompt="Analyze this code...",
            system="You are a code analyst."
        )

        # Parallel calls
        results = await adapter.call_llms_parallel([
            ("ollama/qwen2.5-coder:7b", prompt1, "architecture"),
            ("ollama/deepseek-r1", prompt2, "business_logic"),
        ])
    """

    def __init__(self, selector: TierProviderSelector):
        self.selector = selector
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    # =========================================================================
    # PROVIDER CALLS
    # =========================================================================

    async def call_ollama(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        timeout: int = 300,
    ) -> LLMCallResult:
        """Call Ollama local provider."""
        start_time = time.time()
        provider_id = f"ollama/{model}"

        try:
            session = await self._get_session()
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
            }
            if system:
                payload["system"] = system

            async with session.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                latency_ms = int((time.time() - start_time) * 1000)

                if resp.status != 200:
                    error_text = await resp.text()
                    self.selector.update_health(provider_id, False, latency_ms, error_text)
                    return LLMCallResult(
                        provider_id=provider_id,
                        model=model,
                        content="",
                        latency_ms=latency_ms,
                        success=False,
                        error=f"Ollama error {resp.status}: {error_text}"
                    )

                data = await resp.json()
                tokens_in = data.get("prompt_eval_count", 0)
                tokens_out = data.get("eval_count", 0)

                result = LLMCallResult(
                    provider_id=provider_id,
                    model=model,
                    content=data.get("response", ""),
                    tokens_input=tokens_in,
                    tokens_output=tokens_out,
                    latency_ms=latency_ms,
                    cost_usd=0.0,  # Ollama is free
                    success=True,
                    raw_response=data,
                )

                self.selector.update_health(provider_id, True, latency_ms)
                self.selector.track_call(result)
                return result

        except asyncio.TimeoutError:
            latency_ms = int((time.time() - start_time) * 1000)
            self.selector.update_health(provider_id, False, latency_ms, "Timeout")
            return LLMCallResult(
                provider_id=provider_id,
                model=model,
                content="",
                latency_ms=latency_ms,
                success=False,
                error=f"Timeout after {timeout}s"
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            self.selector.update_health(provider_id, False, latency_ms, str(e))
            return LLMCallResult(
                provider_id=provider_id,
                model=model,
                content="",
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            )

    async def call_groq(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        timeout: int = 60,
    ) -> LLMCallResult:
        """Call Groq API (fast inference)."""
        start_time = time.time()
        provider_id = f"groq/{model}"

        # TODO: Implement actual Groq API call
        # For now, return placeholder indicating not implemented
        return LLMCallResult(
            provider_id=provider_id,
            model=model,
            content="",
            latency_ms=0,
            success=False,
            error="Groq provider not yet implemented - requires GROQ_API_KEY"
        )

    async def call_google(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        timeout: int = 120,
    ) -> LLMCallResult:
        """Call Google Gemini API."""
        start_time = time.time()
        provider_id = f"google/{model}"

        # TODO: Implement actual Google API call
        return LLMCallResult(
            provider_id=provider_id,
            model=model,
            content="",
            latency_ms=0,
            success=False,
            error="Google provider not yet implemented - requires GOOGLE_API_KEY"
        )

    async def call_openai(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        timeout: int = 180,
    ) -> LLMCallResult:
        """Call OpenAI API."""
        start_time = time.time()
        provider_id = f"openai/{model}"

        # TODO: Implement actual OpenAI API call
        return LLMCallResult(
            provider_id=provider_id,
            model=model,
            content="",
            latency_ms=0,
            success=False,
            error="OpenAI provider not yet implemented - requires OPENAI_API_KEY"
        )

    async def call_anthropic(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        timeout: int = 180,
    ) -> LLMCallResult:
        """
        Call Anthropic Claude via CLI.

        Uses the `claude` CLI with --print mode for non-interactive responses.
        Supports: haiku, sonnet, opus

        Model mapping:
        - claude-haiku-3.5 → haiku
        - claude-sonnet-4 → sonnet
        - claude-opus-4.5 → opus
        """
        import shutil
        import subprocess

        start_time = time.time()
        provider_id = f"anthropic/{model}"

        # Map model names to CLI model flags
        model_mapping = {
            "claude-haiku-3.5": "haiku",
            "claude-sonnet-4": "sonnet",
            "claude-opus-4.5": "opus",
            "haiku": "haiku",
            "sonnet": "sonnet",
            "opus": "opus",
        }

        cli_model = model_mapping.get(model, "sonnet")

        # Check if claude CLI is available
        if not shutil.which("claude"):
            latency_ms = int((time.time() - start_time) * 1000)
            return LLMCallResult(
                provider_id=provider_id,
                model=model,
                content="",
                latency_ms=latency_ms,
                success=False,
                error="Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )

        try:
            # Build command
            cmd = ["claude", "--print", "--model", cli_model]
            if system:
                cmd.extend(["--system-prompt", system])

            # Run claude CLI
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=prompt.encode()),
                timeout=timeout
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else f"Exit code {process.returncode}"
                self.selector.update_health(provider_id, False, latency_ms, error_msg)
                return LLMCallResult(
                    provider_id=provider_id,
                    model=model,
                    content="",
                    latency_ms=latency_ms,
                    success=False,
                    error=f"Claude CLI error: {error_msg}"
                )

            content = stdout.decode()

            # Estimate token usage (rough approximation)
            tokens_input = len(prompt.split()) * 1.3  # ~1.3 tokens per word
            tokens_output = len(content.split()) * 1.3

            # Calculate cost based on model
            cost_per_m = {
                "haiku": (1.0, 5.0),
                "sonnet": (3.0, 15.0),
                "opus": (15.0, 75.0),
            }
            input_rate, output_rate = cost_per_m.get(cli_model, (3.0, 15.0))
            cost_usd = (tokens_input / 1_000_000 * input_rate) + (tokens_output / 1_000_000 * output_rate)

            result = LLMCallResult(
                provider_id=provider_id,
                model=model,
                content=content,
                tokens_input=int(tokens_input),
                tokens_output=int(tokens_output),
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                success=True,
            )

            self.selector.update_health(provider_id, True, latency_ms)
            self.selector.track_call(result)
            return result

        except asyncio.TimeoutError:
            latency_ms = int((time.time() - start_time) * 1000)
            self.selector.update_health(provider_id, False, latency_ms, "Timeout")
            return LLMCallResult(
                provider_id=provider_id,
                model=model,
                content="",
                latency_ms=latency_ms,
                success=False,
                error=f"Timeout after {timeout}s"
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            self.selector.update_health(provider_id, False, latency_ms, str(e))
            return LLMCallResult(
                provider_id=provider_id,
                model=model,
                content="",
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            )

    async def call_alibaba(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        timeout: int = 120,
    ) -> LLMCallResult:
        """Call Alibaba Qwen API."""
        start_time = time.time()
        provider_id = f"alibaba/{model}"

        # TODO: Implement actual Alibaba API call
        return LLMCallResult(
            provider_id=provider_id,
            model=model,
            content="",
            latency_ms=0,
            success=False,
            error="Alibaba provider not yet implemented - requires ALIBABA_API_KEY"
        )

    # =========================================================================
    # UNIFIED CALL INTERFACE
    # =========================================================================

    async def call_llm(
        self,
        provider_id: str,
        prompt: str,
        system: Optional[str] = None,
        timeout: int = 300,
    ) -> LLMCallResult:
        """
        Call an LLM provider by provider_id.

        Args:
            provider_id: Full provider ID (e.g., "ollama/qwen2.5-coder:7b")
            prompt: The prompt to send
            system: Optional system message
            timeout: Timeout in seconds

        Returns:
            LLMCallResult with response and metadata
        """
        if "/" not in provider_id:
            return LLMCallResult(
                provider_id=provider_id,
                model=provider_id,
                content="",
                success=False,
                error=f"Invalid provider_id format: {provider_id}"
            )

        provider, model = provider_id.split("/", 1)

        provider_methods = {
            "ollama": self.call_ollama,
            "groq": self.call_groq,
            "google": self.call_google,
            "openai": self.call_openai,
            "anthropic": self.call_anthropic,
            "alibaba": self.call_alibaba,
        }

        method = provider_methods.get(provider)
        if not method:
            return LLMCallResult(
                provider_id=provider_id,
                model=model,
                content="",
                success=False,
                error=f"Unknown provider: {provider}"
            )

        return await method(model, prompt, system, timeout)

    async def call_llms_parallel(
        self,
        calls: List[Tuple[str, str, str]],  # (provider_id, prompt, analysis_type)
        system: Optional[str] = None,
        timeout: int = 300,
    ) -> List[Tuple[str, LLMCallResult]]:
        """
        Call multiple LLMs in parallel.

        Args:
            calls: List of (provider_id, prompt, analysis_type) tuples
            system: Shared system message
            timeout: Timeout per call

        Returns:
            List of (analysis_type, LLMCallResult) tuples
        """
        async def make_call(provider_id: str, prompt: str, analysis_type: str):
            result = await self.call_llm(provider_id, prompt, system, timeout)
            return (analysis_type, result)

        tasks = [
            make_call(provider_id, prompt, analysis_type)
            for provider_id, prompt, analysis_type in calls
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                provider_id, _, analysis_type = calls[i]
                final_results.append((
                    analysis_type,
                    LLMCallResult(
                        provider_id=provider_id,
                        model=provider_id.split("/")[1] if "/" in provider_id else provider_id,
                        content="",
                        success=False,
                        error=str(result)
                    )
                ))
            else:
                final_results.append(result)

        return final_results

    # =========================================================================
    # JSON PARSING
    # =========================================================================

    def parse_json_response(self, content: str) -> Tuple[bool, Any]:
        """
        Parse JSON from LLM response.

        Handles:
        - Clean JSON
        - JSON wrapped in markdown code blocks
        - JSON with trailing text

        Returns:
            (success, parsed_data or error_message)
        """
        if not content:
            return False, "Empty response"

        # Try direct parse first
        try:
            return True, json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code blocks
        import re
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    return True, json.loads(match)
                except json.JSONDecodeError:
                    continue

        return False, f"Could not parse JSON from response: {content[:200]}..."

    # =========================================================================
    # EXTRACTION HELPERS
    # =========================================================================

    async def run_analysis(
        self,
        provider_id: str,
        analysis_type: str,
        code_summary: str,
        file_list: List[str],
    ) -> Tuple[LLMCallResult, Optional[Dict[str, Any]]]:
        """
        Run a specific analysis type on code.

        Args:
            provider_id: LLM provider to use
            analysis_type: Type of analysis (architecture, business_logic, security, code_structure)
            code_summary: Summary of the codebase
            file_list: List of files in the codebase

        Returns:
            (LLMCallResult, parsed_data or None)
        """
        # Get appropriate prompt
        prompt_methods = {
            "architecture": ExtractionPrompts.get_architecture_prompt,
            "business_logic": ExtractionPrompts.get_business_logic_prompt,
            "security": ExtractionPrompts.get_security_prompt,
            "code_structure": ExtractionPrompts.get_code_structure_prompt,
        }

        prompt_method = prompt_methods.get(analysis_type)
        if not prompt_method:
            return LLMCallResult(
                provider_id=provider_id,
                model="",
                content="",
                success=False,
                error=f"Unknown analysis type: {analysis_type}"
            ), None

        prompt = prompt_method(code_summary, file_list)

        # Call LLM
        result = await self.call_llm(
            provider_id=provider_id,
            prompt=prompt,
            system=ExtractionPrompts.SYSTEM_BASE,
        )

        if not result.success:
            return result, None

        # Parse response
        success, parsed = self.parse_json_response(result.content)
        if not success:
            logger.warning(f"Failed to parse JSON from {provider_id}: {parsed}")
            return result, None

        return result, parsed

    async def run_enrichment(
        self,
        reviewer_provider_id: str,
        original_analysis: Dict[str, Any],
        original_analysis_type: str,
    ) -> Tuple[LLMCallResult, Optional[Dict[str, Any]]]:
        """
        Run cross-enrichment on an existing analysis.

        Args:
            reviewer_provider_id: LLM to do the review
            original_analysis: The analysis to review
            original_analysis_type: Type of the original analysis

        Returns:
            (LLMCallResult, parsed_enrichment or None)
        """
        prompt = ExtractionPrompts.get_enrichment_prompt(
            original_analysis,
            original_analysis_type
        )

        result = await self.call_llm(
            provider_id=reviewer_provider_id,
            prompt=prompt,
            system=ExtractionPrompts.SYSTEM_BASE,
        )

        if not result.success:
            return result, None

        success, parsed = self.parse_json_response(result.content)
        if not success:
            logger.warning(f"Failed to parse enrichment JSON from {reviewer_provider_id}")
            return result, None

        return result, parsed

    async def run_synthesis(
        self,
        provider_id: str,
        accepted_items: List[Dict[str, Any]],
        tier: str,
        project_info: Dict[str, Any],
        timeout: int = 300,
    ) -> Tuple[LLMCallResult, Optional[Dict[str, Any]]]:
        """
        Run final synthesis on accepted items (Cycle 5).

        For PREMIUM tier, uses Claude Opus for best reasoning.
        For other tiers, uses the best available LLM.

        Args:
            provider_id: LLM to use for synthesis
            accepted_items: List of accepted consensus items
            tier: Extraction tier (FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM)
            project_info: Project metadata

        Returns:
            (LLMCallResult, parsed_synthesis or None)
        """
        prompt = ExtractionPrompts.get_synthesis_prompt(
            accepted_items,
            tier,
            project_info
        )

        system = """You are an expert software architect performing final synthesis of a multi-LLM code analysis.
Your task is to create a validated, hierarchical backlog structure with confidence explanations and function point estimates.
Return ONLY valid JSON. No markdown wrapping, no explanation text outside the JSON object."""

        result = await self.call_llm(
            provider_id=provider_id,
            prompt=prompt,
            system=system,
            timeout=timeout,
        )

        if not result.success:
            logger.warning(f"Synthesis failed with {provider_id}: {result.error}")
            return result, None

        success, parsed = self.parse_json_response(result.content)
        if not success:
            logger.warning(f"Failed to parse synthesis JSON from {provider_id}: {parsed}")
            return result, None

        logger.info(f"Synthesis completed with {provider_id}")
        return result, parsed


# ============================================================================
# FACTORY
# ============================================================================

def create_extraction_adapter(selector: TierProviderSelector) -> ExtractionLLMAdapter:
    """Create an extraction adapter with the given selector."""
    return ExtractionLLMAdapter(selector)
