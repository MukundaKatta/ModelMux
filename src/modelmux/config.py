"""Application-level settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from modelmux.core import RoutingStrategy


@dataclass
class Settings:
    """Runtime settings for ModelMux, populated from env vars or defaults."""

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    default_strategy: RoutingStrategy = RoutingStrategy.COST_OPTIMIZED
    max_retries: int = 3
    timeout_seconds: int = 30
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> Settings:
        """Build a Settings instance from environment variables."""
        strategy_raw = os.getenv("MODELMUX_DEFAULT_STRATEGY", "cost_optimized")
        try:
            strategy = RoutingStrategy(strategy_raw)
        except ValueError:
            strategy = RoutingStrategy.COST_OPTIMIZED

        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            default_strategy=strategy,
            max_retries=int(os.getenv("MODELMUX_MAX_RETRIES", "3")),
            timeout_seconds=int(os.getenv("MODELMUX_TIMEOUT_SECONDS", "30")),
            log_level=os.getenv("MODELMUX_LOG_LEVEL", "INFO"),
        )
