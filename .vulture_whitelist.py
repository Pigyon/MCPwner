# Vulture whitelist for intentionally unused code
# This prevents false positives for public interfaces and framework-driven attributes.

# Pydantic model config (used by Pydantic internally)
Config
from_attributes
status  # Model field

# Framework-driven / used outside src/ (linguist container imports git_utils)
handlers
__doc__
init_git
config_git
commit_git
