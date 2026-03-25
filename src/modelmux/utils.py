"""Shared utilities for ModelMux."""

from __future__ import annotations


def estimate_token_count(text: str) -> int:
    """Rough token estimate: ~4 characters per token for English text."""
    return max(1, len(text) // 4)


def truncate(text: str, max_length: int = 200) -> str:
    """Return text truncated to *max_length* characters with an ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_cost(amount: float) -> str:
    """Return a human-friendly dollar string for small amounts."""
    if amount < 0.01:
        return f"${amount:.6f}"
    return f"${amount:.4f}"
