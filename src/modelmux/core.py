"""Core routing engine for ModelMux."""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from modelmux.utils import estimate_token_count

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Available strategies for selecting a model."""

    COST_OPTIMIZED = "cost_optimized"
    QUALITY_FIRST = "quality_first"
    LATENCY_FIRST = "latency_first"
    ROUND_ROBIN = "round_robin"


@dataclass
class ModelConfig:
    """Configuration for a single LLM model endpoint."""

    name: str
    provider: str
    cost_per_1k: float
    max_tokens: int
    priority: int = 0
    avg_latency_ms: float = 500.0
    quality_score: float = 0.8
    is_available: bool = True
    tags: list[str] = field(default_factory=list)

    def estimated_cost(self, token_count: int) -> float:
        """Return estimated cost for a given token count."""
        return (token_count / 1000) * self.cost_per_1k


@dataclass
class ModelResponse:
    """Structured response returned by the router."""

    text: str
    model_name: str
    provider: str
    token_count: int
    cost: float
    latency_ms: float
    fallback_used: bool = False
    attempts: int = 1


class CostTracker:
    """Tracks cumulative cost across all routed requests."""

    def __init__(self, budget_limit: float | None = None) -> None:
        self._total_cost: float = 0.0
        self._request_count: int = 0
        self._cost_by_model: dict[str, float] = {}
        self.budget_limit = budget_limit

    @property
    def total_cost(self) -> float:
        return self._total_cost

    @property
    def request_count(self) -> int:
        return self._request_count

    def record(self, model_name: str, cost: float) -> None:
        """Record cost for a single request."""
        self._total_cost += cost
        self._request_count += 1
        self._cost_by_model[model_name] = self._cost_by_model.get(model_name, 0.0) + cost

    def cost_for_model(self, model_name: str) -> float:
        """Return cumulative cost for a specific model."""
        return self._cost_by_model.get(model_name, 0.0)

    def is_over_budget(self) -> bool:
        """Check if the total spend has exceeded the budget limit."""
        if self.budget_limit is None:
            return False
        return self._total_cost >= self.budget_limit

    def summary(self) -> dict[str, Any]:
        """Return a summary dict of cost data."""
        return {
            "total_cost": round(self._total_cost, 6),
            "request_count": self._request_count,
            "cost_by_model": {k: round(v, 6) for k, v in self._cost_by_model.items()},
            "budget_limit": self.budget_limit,
            "over_budget": self.is_over_budget(),
        }


class FallbackChain:
    """Manages an ordered sequence of models to try on failure."""

    def __init__(self, models: list[ModelConfig]) -> None:
        self._models = list(models)

    @property
    def models(self) -> list[ModelConfig]:
        return list(self._models)

    def available_models(self) -> list[ModelConfig]:
        """Return only models that are currently available."""
        return [m for m in self._models if m.is_available]

    def next_after(self, current_name: str) -> ModelConfig | None:
        """Return the next available model after the given one, or None."""
        found = False
        for m in self._models:
            if found and m.is_available:
                return m
            if m.name == current_name:
                found = True
        return None


class Router:
    """Main routing engine that selects and calls models."""

    def __init__(
        self,
        models: list[ModelConfig],
        cost_tracker: CostTracker | None = None,
        max_retries: int = 3,
        call_fn: Callable[[str, str], str] | None = None,
    ) -> None:
        if not models:
            raise ValueError("At least one ModelConfig must be provided")
        self._models = list(models)
        self._cost_tracker = cost_tracker or CostTracker()
        self._max_retries = max_retries
        self._round_robin_idx = 0
        self._call_fn = call_fn or self._default_call

    # -- public API ----------------------------------------------------------

    @property
    def cost_tracker(self) -> CostTracker:
        return self._cost_tracker

    def route(
        self,
        prompt: str,
        strategy: str | RoutingStrategy = RoutingStrategy.COST_OPTIMIZED,
        max_cost: float | None = None,
    ) -> ModelResponse:
        """Route a prompt to the best model according to *strategy*.

        Tries models in order determined by strategy, falling back on failure
        up to ``max_retries`` times.
        """
        if isinstance(strategy, str):
            strategy = RoutingStrategy(strategy)

        candidates = self._rank_models(strategy, prompt, max_cost)
        if not candidates:
            raise RuntimeError("No available models match the given constraints")

        chain = FallbackChain(candidates)
        token_count = estimate_token_count(prompt)
        attempts = 0

        for model in chain.available_models():
            if attempts >= self._max_retries:
                break
            attempts += 1
            try:
                start = time.perf_counter()
                text = self._call_fn(model.name, prompt)
                latency_ms = (time.perf_counter() - start) * 1000
                cost = model.estimated_cost(token_count)
                self._cost_tracker.record(model.name, cost)
                return ModelResponse(
                    text=text,
                    model_name=model.name,
                    provider=model.provider,
                    token_count=token_count,
                    cost=cost,
                    latency_ms=round(latency_ms, 2),
                    fallback_used=attempts > 1,
                    attempts=attempts,
                )
            except Exception as exc:
                logger.warning("Model %s failed: %s", model.name, exc)
                continue

        raise RuntimeError(
            f"All models failed after {attempts} attempt(s)"
        )

    # -- ranking helpers -----------------------------------------------------

    def _rank_models(
        self,
        strategy: RoutingStrategy,
        prompt: str,
        max_cost: float | None,
    ) -> list[ModelConfig]:
        available = [m for m in self._models if m.is_available]
        token_count = estimate_token_count(prompt)

        if max_cost is not None:
            available = [
                m for m in available if m.estimated_cost(token_count) <= max_cost
            ]

        if strategy == RoutingStrategy.COST_OPTIMIZED:
            return sorted(available, key=lambda m: m.cost_per_1k)
        elif strategy == RoutingStrategy.QUALITY_FIRST:
            return sorted(available, key=lambda m: m.quality_score, reverse=True)
        elif strategy == RoutingStrategy.LATENCY_FIRST:
            return sorted(available, key=lambda m: m.avg_latency_ms)
        elif strategy == RoutingStrategy.ROUND_ROBIN:
            if not available:
                return []
            idx = self._round_robin_idx % len(available)
            self._round_robin_idx += 1
            return available[idx:] + available[:idx]
        else:
            return available

    # -- default stub --------------------------------------------------------

    @staticmethod
    def _default_call(model_name: str, prompt: str) -> str:  # pragma: no cover
        """Placeholder call function — override with a real provider client."""
        raise NotImplementedError(
            f"No call_fn configured. Provide a callable to route to {model_name}."
        )
