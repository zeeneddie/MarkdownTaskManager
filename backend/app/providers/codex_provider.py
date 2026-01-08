"""
Codex Provider - OpenAI Codex CLI Integration

Wraps the Codex CLI for complex code analysis and generation tasks.
Uses: gpt-5-codex, gpt-5, gpt-5.1-codex-max models via CLI.
"""

import asyncio
import time
import shutil
from typing import Literal, Optional

from .base import LLMProvider, LLMRequest, LLMResponse, ProviderConfig


ReasoningEffort = Literal["low", "medium", "high"]
SandboxMode = Literal["read-only", "workspace-write", "danger-full-access"]


class CodexProvider(LLMProvider):
    """
    Codex CLI provider for complex code tasks.

    Uses the `codex exec` command to leverage OpenAI's Codex models
    for tasks requiring deep code understanding.

    Benefits:
    - Superior code analysis capabilities
    - Multi-file understanding
    - Architecture-level reasoning
    - Refactoring suggestions

    Models:
    - gpt-5-codex - Standard Codex model
    - gpt-5 - GPT-5 base
    - gpt-5.1-codex-max - Latest Codex (recommended)

    Reasoning Efforts:
    - low: Quick responses, less thinking
    - medium: Balanced (default)
    - high: Deep analysis, more thorough
    """

    SUPPORTED_MODELS = [
        "gpt-5-codex",
        "gpt-5",
        "gpt-5.1-codex-max",
        "o3",
        "o4-mini",
    ]

    def __init__(
        self,
        model: str = "gpt-5.1-codex-max",
        reasoning_effort: ReasoningEffort = "medium",
        sandbox_mode: SandboxMode = "read-only",
        working_dir: Optional[str] = None
    ):
        self.reasoning_effort = reasoning_effort
        self.sandbox_mode = sandbox_mode
        self.working_dir = working_dir

        # Estimate costs (actual costs depend on OpenAI pricing)
        cost_map = {
            "gpt-5-codex": (10.0, 30.0),
            "gpt-5": (10.0, 30.0),
            "gpt-5.1-codex-max": (15.0, 60.0),
            "o3": (20.0, 80.0),
            "o4-mini": (5.0, 15.0),
        }
        costs = cost_map.get(model, (15.0, 60.0))

        self.config = ProviderConfig(
            name="codex",
            tier="deep",
            model=model,
            cost_input_per_m=costs[0],
            cost_output_per_m=costs[1],
            is_local=False,
            is_active=True,
            extras={
                "reasoning_effort": reasoning_effort,
                "sandbox_mode": sandbox_mode,
            }
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response using Codex CLI.

        Executes: codex exec --sandbox {mode} --skip-git-repo-check "{prompt}"
        """
        start_time = time.time()

        # Check if codex CLI is available
        if not shutil.which("codex"):
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="codex",
                success=False,
                error="Codex CLI not found. Install with: npm install -g @openai/codex"
            )

        try:
            # Build command
            cmd = [
                "codex", "exec",
                "-m", self.config.model,
                "--config", f'model_reasoning_effort="{self.reasoning_effort}"',
                "--sandbox", self.sandbox_mode,
                "--skip-git-repo-check",
            ]

            if self.working_dir:
                cmd.extend(["-C", self.working_dir])

            # Add the prompt
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
                    model=self.config.model,
                    provider="codex",
                    success=False,
                    error=f"Codex timeout after {request.timeout}s"
                )

            duration_ms = int((time.time() - start_time) * 1000)

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                return LLMResponse(
                    content="",
                    model=self.config.model,
                    provider="codex",
                    duration_ms=duration_ms,
                    success=False,
                    error=f"Codex exit code {process.returncode}: {error_msg}"
                )

            content = stdout.decode("utf-8", errors="replace").strip()

            # Estimate tokens (rough: ~4 chars per token)
            token_input = len(request.prompt) // 4
            token_output = len(content) // 4
            cost_cents = self.calculate_cost(token_input, token_output)

            return LLMResponse(
                content=content,
                model=self.config.model,
                provider="codex",
                token_input=token_input,
                token_output=token_output,
                duration_ms=duration_ms,
                cost_cents=cost_cents,
                success=True,
                raw={
                    "reasoning_effort": self.reasoning_effort,
                    "sandbox_mode": self.sandbox_mode,
                    "exit_code": process.returncode,
                }
            )

        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="codex",
                success=False,
                error=f"Codex error: {str(e)}"
            )

    async def healthcheck(self) -> bool:
        """Check if Codex CLI is available and configured."""
        if not shutil.which("codex"):
            return False

        try:
            process = await asyncio.create_subprocess_exec(
                "codex", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(
                process.communicate(),
                timeout=5
            )
            return process.returncode == 0 and b"codex" in stdout.lower()
        except Exception:
            return False

    def supports_model(self, model: str) -> bool:
        """Check if model is supported by Codex."""
        return model in self.SUPPORTED_MODELS

    def set_reasoning_effort(self, effort: ReasoningEffort) -> None:
        """Change reasoning effort level."""
        self.reasoning_effort = effort
        self.config.extras["reasoning_effort"] = effort

    def set_sandbox_mode(self, mode: SandboxMode) -> None:
        """Change sandbox mode."""
        self.sandbox_mode = mode
        self.config.extras["sandbox_mode"] = mode
