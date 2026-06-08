# Vulture whitelist for intentionally unused code
# This prevents false positives for public interfaces and framework-driven attributes.

# Repository / model methods (public interface, used dynamically or reserved)
is_github_clone

# Service methods (public interface, invoked via MCP tools)
detect_languages_detailed
is_language_supported
delete_workspace
cleanup_old_workspaces

# Pydantic model config (used by Pydantic internally)
Config
from_attributes
status  # Model field
