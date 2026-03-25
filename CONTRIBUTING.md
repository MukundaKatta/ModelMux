# Contributing to ModelMux

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/MukundaKatta/ModelMux.git
cd ModelMux

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
make install
```

## Running Tests

```bash
make test
```

## Code Quality

Before submitting a PR, please run:

```bash
make lint       # ruff linter
make typecheck  # mypy strict mode
make fmt        # auto-format with ruff
```

## Pull Request Process

1. Fork the repository and create a feature branch from `main`.
2. Write tests for any new functionality.
3. Ensure all checks pass (`make all`).
4. Open a PR with a clear description of the change.
5. A maintainer will review and merge.

## Code Style

- We use **ruff** for linting and formatting.
- Type hints are required on all public functions.
- Keep functions small and focused.

## Reporting Issues

Open a GitHub issue with:
- A clear title and description.
- Steps to reproduce (if a bug).
- Expected vs actual behavior.
