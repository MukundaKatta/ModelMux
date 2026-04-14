# ModelMux — Multi-Model Router. Intelligent multi-model routing and fallback for LLM apps

Multi-Model Router. Intelligent multi-model routing and fallback for LLM apps. ModelMux gives you a focused, inspectable implementation of that idea.

## Why ModelMux

ModelMux exists to make this workflow practical. Multi-model router. intelligent multi-model routing and fallback for llm apps. It favours a small, inspectable surface over sprawling configuration.

## Features

- `RoutingStrategy` — exported from `src/modelmux/core.py`
- `ModelConfig` — exported from `src/modelmux/core.py`
- `ModelResponse` — exported from `src/modelmux/core.py`
- Included test suite
- Dedicated documentation folder

## Tech Stack

- **Runtime:** Python

## How It Works

The codebase is organised into `docs/`, `src/`, `tests/`. The primary entry points are `src/modelmux/core.py`, `src/modelmux/__init__.py`. `src/modelmux/core.py` exposes `RoutingStrategy`, `ModelConfig`, `ModelResponse` — the core types that drive the behaviour.

## Getting Started

```bash
pip install -e .
```

## Usage

```python
from modelmux.core import RoutingStrategy

instance = RoutingStrategy()
# See the source for the full API
```

## Project Structure

```
ModelMux/
├── .env.example
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── README.md
├── docs/
├── pyproject.toml
├── src/
├── tests/
```
