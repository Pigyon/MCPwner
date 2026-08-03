# Contributing to MCPwner

Thanks for your interest in improving MCPwner. This guide covers the local setup, the code
standards enforced on commit, and how to add a new tool.

## Getting started

1. Fork and clone the repository.
2. Bring up the fleet you need for testing (see [docs/quickstart.md](docs/quickstart.md)):
   ```bash
   cp .env.example .env          # pick COMPOSE_PROFILES
   cp config/config.yaml.example config/config.yaml
   docker compose up -d --build
   ```
3. For running the Python test suite and linters locally, create a virtualenv and install the
   server requirements:
   ```bash
   python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Code style and linting

**`ruff.toml` is the source of truth.** Before finishing any Python change, run:

```bash
ruff format <changed-files>
ruff check --fix <changed-files>
```

or repo-wide when touching many files: `ruff format .` then `ruff check --fix .`.

- Line length **105**, **double quotes**, 4-space indent.
- Imports sorted by ruff/isort: stdlib → third-party → first-party (`src`).
- Enabled rule sets: `E, W, F, I, SIM, RET, C4, S` (S = Bandit security). Respect the ignores
  already in `ruff.toml` - don't "fix" suppressed rules (e.g. subprocess in Docker services,
  `0.0.0.0` binds, `assert` in tests).
- No unused imports or dead public functions in `src/` - **vulture runs on commit and blocks if
  it finds dead code** (add genuinely-intentional exceptions to `.vulture_whitelist.py`).

### Comments

Comment on **why**, not **what**. Explain intent, hidden constraints, or non-obvious edge cases -
not what the code already says. Keep comments to 1-2 lines, and don't write changelog- or
history-style comments describing past states or changes.

## Pre-commit hooks

The repo ships a `.pre-commit-config.yaml` running ruff (format check + lint) and vulture. Install
it once so checks run automatically:

```bash
pip install pre-commit
pre-commit install
```

The hooks **verify** formatting rather than reforming - apply fixes with `ruff format` /
`ruff check --fix` (or editor format-on-save) before committing.

## Tests

Unit tests live under `tests/`. Run them with pytest:

```bash
pytest tests/unit
```

Add or update tests for any behavior change to the server (`src/`).

## Commits and pull requests

- Use short, imperative commit subjects with a type prefix (`fix:`, `feat:`, `docs:`, `chore:`).
- The [pull request template](.github/PULL_REQUEST_TEMPLATE.md) asks for a summary, the problem,
  and how you verified the change - fill it in. Concrete verification (commands run, output,
  builds that now pass) gets PRs merged faster.
- Keep PRs focused; unrelated changes belong in separate PRs.

## Adding a new tool

See [docs/adding-a-tool.md](docs/adding-a-tool.md) for the full walkthrough - a tool container, a
compose service, a registry entry, a config URL, and a discovery-list entry.

## Security

Please report vulnerabilities per [SECURITY.md](SECURITY.md) rather than opening a public issue.
