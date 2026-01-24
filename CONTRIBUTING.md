# Contributing to MCPwner

## Development Setup

### Initial Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r config/requirements.txt
   pip install -r tests/integration/requirements.txt
   ```

3. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Pre-commit Hooks

This project uses pre-commit to maintain code quality and run tests. The hooks are configured in `.pre-commit-config.yaml`.

**First time setup:**
```bash
pip install pre-commit
pre-commit install
```

**What runs on every commit:**
- **Ruff linter**: Checks code quality, simplifies patterns, enforces best practices
- **Ruff formatter**: Auto-formats Python code
- **Vulture**: Detects unused/dead code
- **JSON/YAML validation**: Ensures config files are valid
- **Git quality checks**: Detects merge conflicts, blocks large files, fixes whitespace

**What runs on push:**
- **Integration tests**: Full test suite (configured with `stages: [manual, pre-push]`)

**Manual runs:**
```bash
# Run all hooks on all files
pre-commit run --all-files

# Run only tests (pre-push stage)
pre-commit run --hook-stage push --all-files

# Run specific hook
pre-commit run ruff-check --all-files
```

**Bypass in emergencies:**
```bash
git commit --no-verify  # Skip commit hooks
git push --no-verify    # Skip push hooks
```

**Note:** Pre-commit automatically downloads and manages all tools (ruff, vulture, etc.) - you don't need to install them separately.

### Running Tests Manually

```bash
# Run all integration tests
python -m pytest tests/integration/

# Run specific test file
python -m pytest tests/integration/mcp_tools/test_tool_execution.py

# Run with verbose output
python -m pytest tests/integration/ -v
```
