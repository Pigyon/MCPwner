# Contributing to MCPwner

## Development Setup

### Initial Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r tests/integration/requirements.txt
   ```

3. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Pre-commit Hooks

This project uses pre-commit to maintain code quality. The hooks are configured in `.pre-commit-config.yaml`.

**First time setup:**
```bash
pip install pre-commit ruff vulture
pre-commit install
```

**What runs on every commit (STRICT - blocks if issues found):**
- **Ruff formatter**: Auto-formats Python code
- **Ruff linter**: Checks code quality, auto-fixes simple issues
- **Vulture**: Detects unused/dead code (min-confidence=80, BLOCKS commit)

**Editor integration (VSCode/Kiro):**
- Ruff runs automatically on file save
- Install the Ruff extension for real-time feedback
- See `.vscode/settings.json` for configuration

**Manual runs:**
```bash
# Run all commit hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run vulture --all-files

# Format code manually
ruff format .

# Lint code manually
ruff check --fix .

# Check for dead code manually
vulture src/ .vulture_whitelist.py --min-confidence=80
```

**If vulture blocks your commit:**
1. Review the reported dead code - is it actually unused?
2. If truly dead: Delete it
3. If intentional (API methods, fixtures, etc.): Add to `.vulture_whitelist.py`

**Bypass in emergencies (not recommended):**
```bash
git commit --no-verify  # Skip commit hooks
```

**Note:** Pre-commit automatically downloads and manages hook environments - you don't need to install tools globally except for editor integration.

### Running Tests Manually

```bash
# Run all integration tests
python -m pytest tests/integration/

# Run specific test file
python -m pytest tests/integration/mcp_tools/test_tool_execution.py

# Run with verbose output
python -m pytest tests/integration/ -v
```
