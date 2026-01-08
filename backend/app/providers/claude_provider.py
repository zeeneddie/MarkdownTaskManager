"""
Claude Provider - Anthropic Claude CLI Integration

Wraps the Claude CLI for high-quality code generation and analysis.
Supports: Haiku (fast), Sonnet (balanced), Opus (deep reasoning).
"""

import asyncio
import time
import shutil
import json
from typing import Literal, Optional

from .base import LLMProvider, LLMRequest, LLMResponse, ProviderConfig


ClaudeModel = Literal["haiku", "sonnet", "opus"]


class ClaudeProvider(LLMProvider):
    """
    Claude CLI provider for balanced AI tasks.

    Uses the `claude` CLI with --print mode for non-interactive responses.
    Supports model selection via --model flag.

    Models & Pricing (per million tokens):
    - haiku: Fast, cheap ($1 input / $5 output)
    - sonnet: Balanced ($3 input / $15 output)
    - opus: Deep reasoning ($15 input / $75 output)

    Use Cases:
    - haiku: Quick fixes, scaffolding, bulk generation
    - sonnet: Daily coding, standard tasks, code review
    - opus: Architecture decisions, complex debugging, security

    Note: Requires Claude CLI installed and authenticated.
    Install: npm install -g @anthropic-ai/claude-code
    Auth: claude login
    """

    SUPPORTED_MODELS = ["haiku", "sonnet", "opus"]

    # Pricing per million tokens (USD)
    MODEL_PRICING = {
        "haiku": {"input": 1.0, "output": 5.0, "tier": "fast"},
        "sonnet": {"input": 3.0, "output": 15.0, "tier": "balanced"},
        "opus": {"input": 15.0, "output": 75.0, "tier": "deep"},
    }

    def __init__(
        self,
        model: ClaudeModel = "sonnet",
        working_dir: Optional[str] = None,
        system_prompt: Optional[str] = None,
        output_format: Literal["text", "json"] = "text",
    ):
        self.model = model
        self.working_dir = working_dir
        self.system_prompt = system_prompt
        self.output_format = output_format

        pricing = self.MODEL_PRICING.get(model, self.MODEL_PRICING["sonnet"])

        self.config = ProviderConfig(
            name="claude",
            tier=pricing["tier"],
            model=model,
            cost_input_per_m=pricing["input"],
            cost_output_per_m=pricing["output"],
            is_local=False,
            is_active=True,
            extras={
                "output_format": output_format,
                "system_prompt": system_prompt,
            }
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response using Claude CLI.

        Executes: claude --print --model {model} "{prompt}"
        """
        start_time = time.time()

        # Check if claude CLI is available
        if not shutil.which("claude"):
            return LLMResponse(
                content="",
                model=self.model,
                provider="claude",
                success=False,
                error="Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )

        try:
            # Build command
            cmd = [
                "claude",
                "--print",
                "--model", self.model,
                "--output-format", self.output_format,
            ]

            # Add system prompt if provided
            effective_system = request.system or self.system_prompt
            if effective_system:
                cmd.extend(["--system-prompt", effective_system])

            # Add working directory if specified
            if self.working_dir:
                cmd.extend(["--add-dir", self.working_dir])

            # Add the prompt as argument
            cmd.append(request.prompt)

            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=request.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return LLMResponse(
                    content="",
                    model=self.model,
                    provider="claude",
                    success=False,
                    error=f"Claude timeout after {request.timeout}s"
                )

            duration_ms = int((time.time() - start_time) * 1000)

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                return LLMResponse(
                    content="",
                    model=self.model,
                    provider="claude",
                    duration_ms=duration_ms,
                    success=False,
                    error=f"Claude exit code {process.returncode}: {error_msg}"
                )

            content = stdout.decode("utf-8", errors="replace").strip()

            # Parse JSON output if requested
            raw_data = {}
            if self.output_format == "json":
                try:
                    raw_data = json.loads(content)
                    # Extract actual content from JSON response
                    if isinstance(raw_data, dict) and "result" in raw_data:
                        content = raw_data.get("result", content)
                except json.JSONDecodeError:
                    pass  # Keep content as-is if not valid JSON

            # Estimate tokens (rough: ~4 chars per token)
            token_input = len(request.prompt) // 4
            token_output = len(content) // 4
            cost_cents = self.calculate_cost(token_input, token_output)

            return LLMResponse(
                content=content,
                model=self.model,
                provider="claude",
                token_input=token_input,
                token_output=token_output,
                duration_ms=duration_ms,
                cost_cents=cost_cents,
                success=True,
                raw=raw_data if raw_data else {"exit_code": process.returncode}
            )

        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                provider="claude",
                success=False,
                error=f"Claude error: {str(e)}"
            )

    async def healthcheck(self) -> bool:
        """Check if Claude CLI is available and authenticated."""
        if not shutil.which("claude"):
            return False

        try:
            process = await asyncio.create_subprocess_exec(
                "claude", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(
                process.communicate(),
                timeout=5
            )
            return process.returncode == 0
        except Exception:
            return False

    def supports_model(self, model: str) -> bool:
        """Check if model is supported by Claude CLI."""
        return model in self.SUPPORTED_MODELS

    def set_model(self, model: ClaudeModel) -> None:
        """Change the model."""
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}. Use: {self.SUPPORTED_MODELS}")

        self.model = model
        pricing = self.MODEL_PRICING[model]
        self.config.model = model
        self.config.tier = pricing["tier"]
        self.config.cost_input_per_m = pricing["input"]
        self.config.cost_output_per_m = pricing["output"]

    @classmethod
    def haiku(cls, **kwargs) -> "ClaudeProvider":
        """Create a Haiku provider (fast, cheap)."""
        return cls(model="haiku", **kwargs)

    @classmethod
    def sonnet(cls, **kwargs) -> "ClaudeProvider":
        """Create a Sonnet provider (balanced)."""
        return cls(model="sonnet", **kwargs)

    @classmethod
    def opus(cls, **kwargs) -> "ClaudeProvider":
        """Create an Opus provider (deep reasoning)."""
        return cls(model="opus", **kwargs)
