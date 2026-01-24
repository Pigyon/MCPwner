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
   pre-commit install --hook-type pre-push
   ```

### Pre-commit Hooks

This project uses pre-commit to run tests before every push. The hooks are configured in `.pre-commit-config.yaml` and the test runner script is in `tests/hooks/run-tests.py`.

**First time setup:**
```bash
pip install pre-commit
pre-commit install --hook-type pre-push
```

**What it does:**
- Runs all integration tests before `git push`
- Blocks the push if tests fail
- Works cross-platform (Linux, macOS, Windows)
- Automatically detects your Python interpreter (python/python3/py)

**Manual test run:**
```bash
pre-commit run --hook-stage push --all-files
```

**Bypass in emergencies:**
```bash
git push --no-verify
```

### Running Tests Manually

```bash
# Run all integration tests
python -m pytest tests/integration/

# Run specific test file
python -m pytest tests/integration/mcp_tools/test_tool_execution.py

# Run with verbose output
python -m pytest tests/integration/ -v
```
