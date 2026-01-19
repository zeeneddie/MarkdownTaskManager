"""
LLM Streaming API - Fase 24.5

Server-Sent Events (SSE) endpoints for streaming LLM responses.

Features:
- Real-time streaming of LLM responses
- Circuit breaker status and management
- Provider health monitoring

Author: Claude Code (Week 158 - Fase 24.5)
Date: 2026-01-19
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import json

from app.services.extraction_llm_adapter import ExtractionLLMAdapter
from app.services.llm_resilience import (
    circuit_breaker_registry,
    StreamChunk,
)


router = APIRouter(prefix="/api/v1/llm", tags=["llm-streaming"])


# =============================================================================
# STREAMING ENDPOINTS
# =============================================================================


@router.get("/stream")
async def stream_llm_response(
    provider_id: str = Query(..., description="Provider ID (e.g., 'ollama/qwen2.5-coder:7b')"),
    prompt: str = Query(..., description="The prompt to send"),
    system: Optional[str] = Query(None, description="Optional system message"),
    timeout: int = Query(300, ge=10, le=600, description="Timeout in seconds"),
):
    """
    Stream LLM response using Server-Sent Events (SSE).

    Fase 24.5: Real-time streaming reduces perceived latency.

    Connect using EventSource in JavaScript:
    ```javascript
    const source = new EventSource('/api/v1/llm/stream?provider_id=ollama/qwen2.5-coder:7b&prompt=Hello');
    source.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.content);
        if (data.type === 'done') source.close();
    };
    ```

    Events:
        - type: "chunk" - Partial response content
        - type: "done" - Stream complete with metadata
        - type: "error" - Error occurred

    Returns:
        text/event-stream with SSE formatted data
    """
    adapter = ExtractionLLMAdapter()

    async def generate_sse():
        try:
            async for chunk in adapter.call_llm_streaming(
                provider_id=provider_id,
                prompt=prompt,
                system=system,
                timeout=timeout,
            ):
                yield chunk.to_sse()

        except Exception as e:
            error_chunk = StreamChunk(
                content="",
                is_final=True,
                metadata={"error": str(e)},
            )
            yield error_chunk.to_sse()

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/generate")
async def generate_with_stream_option(
    provider_id: str = Query(..., description="Provider ID"),
    prompt: str = Query(..., description="The prompt to send"),
    system: Optional[str] = Query(None, description="Optional system message"),
    timeout: int = Query(300, ge=10, le=600, description="Timeout in seconds"),
    stream: bool = Query(False, description="Enable streaming response"),
):
    """
    Generate LLM response with optional streaming.

    If stream=True, returns SSE stream.
    If stream=False (default), returns complete response as JSON.

    Returns:
        JSON response or text/event-stream depending on stream parameter
    """
    adapter = ExtractionLLMAdapter()

    if stream:
        async def generate_sse():
            try:
                async for chunk in adapter.call_llm_streaming(
                    provider_id=provider_id,
                    prompt=prompt,
                    system=system,
                    timeout=timeout,
                ):
                    yield chunk.to_sse()
            except Exception as e:
                error_chunk = StreamChunk(
                    content="",
                    is_final=True,
                    metadata={"error": str(e)},
                )
                yield error_chunk.to_sse()

        return StreamingResponse(
            generate_sse(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming: wait for complete response
    result = await adapter.call_llm(
        provider_id=provider_id,
        prompt=prompt,
        system=system,
        timeout=timeout,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "provider_id": result.provider_id,
        "model": result.model,
        "content": result.content,
        "tokens_input": result.tokens_input,
        "tokens_output": result.tokens_output,
        "latency_ms": result.latency_ms,
        "cost_usd": result.cost_usd,
    }


# =============================================================================
# CIRCUIT BREAKER ENDPOINTS
# =============================================================================


@router.get("/providers/health")
async def get_provider_health():
    """
    Get health status and circuit breaker state for all providers.

    Fase 24.5: Circuit breaker monitoring for operational visibility.

    Returns:
        Dict mapping provider IDs to their circuit breaker states

    States:
        - closed: Normal operation, requests pass through
        - open: Failing fast, requests rejected (provider unhealthy)
        - half_open: Testing recovery, limited requests allowed
    """
    states = circuit_breaker_registry.get_all_states()

    return {
        "providers": states,
        "total_providers": len(states),
        "healthy_count": sum(
            1 for s in states.values()
            if s.get("state") == "closed"
        ),
        "unhealthy_count": sum(
            1 for s in states.values()
            if s.get("state") == "open"
        ),
        "recovering_count": sum(
            1 for s in states.values()
            if s.get("state") == "half_open"
        ),
    }


@router.get("/providers/{provider}/health")
async def get_single_provider_health(provider: str):
    """
    Get health status for a specific provider.

    Args:
        provider: Provider name (e.g., "ollama", "anthropic")

    Returns:
        Circuit breaker state for the provider
    """
    breaker = await circuit_breaker_registry.get_breaker(provider)
    return breaker.to_dict()


@router.post("/providers/{provider}/reset")
async def reset_provider_circuit_breaker(provider: str):
    """
    Manually reset circuit breaker for a provider.

    Use this to force a provider back to healthy state after
    resolving issues.

    Args:
        provider: Provider name to reset

    Returns:
        Updated circuit breaker state
    """
    breaker = await circuit_breaker_registry.get_breaker(provider)
    await breaker.reset()

    return {
        "message": f"Circuit breaker reset for {provider}",
        "state": breaker.to_dict(),
    }


@router.post("/providers/reset-all")
async def reset_all_circuit_breakers():
    """
    Reset all circuit breakers.

    Use with caution - this will allow traffic to all providers
    regardless of their actual health.

    Returns:
        Summary of reset operations
    """
    await circuit_breaker_registry.reset_all()
    states = circuit_breaker_registry.get_all_states()

    return {
        "message": "All circuit breakers reset",
        "providers_reset": len(states),
        "states": states,
    }


# =============================================================================
# STREAMING ANALYSIS ENDPOINT
# =============================================================================


@router.get("/analysis/{analysis_id}/stream")
async def stream_analysis_result(
    analysis_id: str,
    timeout: int = Query(300, ge=10, le=600),
):
    """
    Stream results of an ongoing analysis.

    This endpoint connects to an analysis job and streams its results
    as they become available.

    Args:
        analysis_id: ID of the analysis to stream
        timeout: Maximum time to wait for results

    Note:
        This is a placeholder for integration with the analysis pipeline.
        Currently returns an error as no analysis storage is implemented.
    """
    # TODO: Integrate with analysis pipeline storage
    # This would look up the analysis by ID and stream its results
    raise HTTPException(
        status_code=501,
        detail={
            "error": "Analysis streaming not yet implemented",
            "analysis_id": analysis_id,
            "hint": "Use /api/v1/llm/stream for direct LLM streaming",
        },
    )
