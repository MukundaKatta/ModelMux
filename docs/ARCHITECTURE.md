# ModelMux Architecture

## Overview

ModelMux is structured around a central `Router` that accepts prompts and delegates them to the optimal LLM model based on a pluggable `RoutingStrategy`.

## Components

### Router
The entry point for all requests. It:
1. Accepts a prompt and a routing strategy.
2. Ranks available models using the chosen strategy.
3. Calls the top-ranked model via a configurable `call_fn`.
4. On failure, walks the `FallbackChain` to try the next model.
5. Records cost via `CostTracker` on success.

### ModelConfig
A dataclass describing a single model endpoint: name, provider, cost, latency, quality score, and availability flag.

### RoutingStrategy
An enum of supported strategies:
- **cost_optimized** — sort by lowest `cost_per_1k`.
- **quality_first** — sort by highest `quality_score`.
- **latency_first** — sort by lowest `avg_latency_ms`.
- **round_robin** — rotate through available models.

### FallbackChain
An ordered list of `ModelConfig` entries. When the primary model fails, the chain provides the next available model to try.

### CostTracker
Accumulates per-model and total spend. Supports an optional `budget_limit` that the caller can check to stop routing when the budget is exhausted.

### Settings (config.py)
Loads runtime configuration from environment variables (API keys, default strategy, timeouts).

## Data Flow

```
User prompt
    |
    v
Router.route(prompt, strategy)
    |
    v
_rank_models(strategy) -> ordered list
    |
    v
for model in candidates:
    call_fn(model.name, prompt)
        |-- success --> record cost, return ModelResponse
        |-- failure --> try next model in FallbackChain
```

## Extension Points

- **call_fn**: Inject any callable `(model_name, prompt) -> str` to integrate real provider SDKs.
- **RoutingStrategy**: Add new enum members and corresponding ranking logic in `_rank_models`.
- **CostTracker**: Subclass or replace to persist cost data to a database.
