"""Tests for the ModelMux core routing engine."""

import pytest

from modelmux.core import (
    CostTracker,
    FallbackChain,
    ModelConfig,
    Router,
    RoutingStrategy,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_models() -> list[ModelConfig]:
    return [
        ModelConfig(
            name="cheap-model",
            provider="openai",
            cost_per_1k=0.0001,
            max_tokens=128000,
            quality_score=0.6,
            avg_latency_ms=200,
        ),
        ModelConfig(
            name="quality-model",
            provider="anthropic",
            cost_per_1k=0.003,
            max_tokens=200000,
            quality_score=0.95,
            avg_latency_ms=800,
        ),
        ModelConfig(
            name="fast-model",
            provider="openai",
            cost_per_1k=0.001,
            max_tokens=64000,
            quality_score=0.75,
            avg_latency_ms=100,
        ),
    ]


def _echo_call(model_name: str, prompt: str) -> str:
    """Simple stub that echoes back the prompt with the model name."""
    return f"[{model_name}] {prompt}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRouterCostOptimized:
    """Cost-optimized strategy should pick the cheapest model."""

    def test_selects_cheapest_model(self) -> None:
        router = Router(_make_models(), call_fn=_echo_call)
        resp = router.route("Hello world", strategy="cost_optimized")
        assert resp.model_name == "cheap-model"
        assert resp.text.startswith("[cheap-model]")

    def test_cost_is_recorded(self) -> None:
        router = Router(_make_models(), call_fn=_echo_call)
        router.route("Hello world", strategy="cost_optimized")
        assert router.cost_tracker.total_cost > 0
        assert router.cost_tracker.request_count == 1


class TestRouterQualityFirst:
    """Quality-first strategy should pick the highest quality model."""

    def test_selects_best_quality(self) -> None:
        router = Router(_make_models(), call_fn=_echo_call)
        resp = router.route("Explain AI", strategy="quality_first")
        assert resp.model_name == "quality-model"


class TestRouterLatencyFirst:
    """Latency-first strategy should pick the fastest model."""

    def test_selects_fastest(self) -> None:
        router = Router(_make_models(), call_fn=_echo_call)
        resp = router.route("Quick answer", strategy="latency_first")
        assert resp.model_name == "fast-model"


class TestFallback:
    """Router should fall back to the next model on failure."""

    def test_fallback_on_failure(self) -> None:
        call_count = 0

        def _fail_then_succeed(model_name: str, prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated failure")
            return f"[{model_name}] OK"

        router = Router(_make_models(), call_fn=_fail_then_succeed)
        resp = router.route("Test fallback", strategy="cost_optimized")
        assert resp.fallback_used is True
        assert resp.attempts == 2


class TestCostTracker:
    """CostTracker should accumulate costs correctly."""

    def test_budget_limit(self) -> None:
        tracker = CostTracker(budget_limit=0.01)
        tracker.record("m1", 0.005)
        assert not tracker.is_over_budget()
        tracker.record("m1", 0.006)
        assert tracker.is_over_budget()

    def test_summary(self) -> None:
        tracker = CostTracker()
        tracker.record("a", 0.001)
        tracker.record("b", 0.002)
        s = tracker.summary()
        assert s["request_count"] == 2
        assert s["total_cost"] == pytest.approx(0.003)


class TestFallbackChain:
    """FallbackChain helpers."""

    def test_next_after(self) -> None:
        models = _make_models()
        chain = FallbackChain(models)
        nxt = chain.next_after("cheap-model")
        assert nxt is not None
        assert nxt.name == "quality-model"

    def test_next_after_last_returns_none(self) -> None:
        models = _make_models()
        chain = FallbackChain(models)
        assert chain.next_after("fast-model") is None
