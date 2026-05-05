"""Thin Protocol-based abstraction for Claude calls.

Real implementation uses the `anthropic` SDK. Tests inject a mock that
satisfies the same Protocol — keeping core code free of SDK-specific knowledge.
"""

from __future__ import annotations

from typing import Protocol


class ClaudeClient(Protocol):
    """Minimal interface for the Claude completions used by core."""

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        """Return the model's response to `prompt` as a single string."""
        ...


class AnthropicClient:
    """Default Claude client wrapping the `anthropic` SDK.

    Used by the Streamlit surface (BYO-key path). Skill surfaces don't
    instantiate this directly — they let Claude's runtime invoke the skill
    and pass results into core.
    """

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-6") -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "anthropic SDK not installed; install with `pip install anthropic`"
            ) from exc
        # Resolve the key via auth module if not explicitly passed.
        # Resolution order: .env → ~/.config/ia-pptx/credentials.json → ANTHROPIC_API_KEY env var.
        if api_key is None:
            from ia_pptx.auth import load_api_key

            api_key = load_api_key()
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self._model = model

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        # The SDK's content is a list of blocks; concatenate text blocks.
        parts = []
        for block in msg.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "".join(parts)


__all__ = ["AnthropicClient", "ClaudeClient"]
