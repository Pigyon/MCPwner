# Vulture whitelist for intentionally unused code
# This prevents false positives for API endpoints, fixtures, and public interfaces

# API tool functions (called dynamically by FastAPI)
sast_semgrep_get_report
sast_semgrep_scan

# Repository methods (public interface, may be used later)
get_by_id
clear
get_statistics
is_github_clone

# Service methods (public interface)
detect_languages_detailed
is_language_supported
delete_workspace
cleanup_old_workspaces

# Dependency injection functions (may be used in future endpoints)
get_bandit_service
get_gosec_service
get_brakeman_service
get_pmd_service
get_psalm_service
reset_dependencies

# Pydantic model Config classes (used by Pydantic internally)
Config
json_encoders
from_attributes
status  # Model field

# SQLite connection attributes (used by sqlite3 internally)
row_factory
