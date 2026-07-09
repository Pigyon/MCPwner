"""Configuration management for MCPwner."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml

from config.tools import TOOL_REGISTRY


def _env_var_name(tool_name: str) -> str:
    """Map a tool name to its service-URL env var (e.g. osv-scanner -> OSV_SCANNER_SERVICE_URL)."""
    return tool_name.upper().replace("-", "_") + "_SERVICE_URL"


# Mapping from environment variable names to config paths. Derived from the tool
# registry so every tool gets a consistent <NAME>_SERVICE_URL override, plus the
# bespoke CodeQL/Linguist services that live outside the registry.
_SERVICE_URL_ENV_VARS: Dict[str, tuple] = {
    "CODEQL_SERVICE_URL": ("codeql", "service_url"),
    "LINGUIST_SERVICE_URL": ("linguist", "service_url"),
}
for _name, _spec in TOOL_REGISTRY.items():
    _SERVICE_URL_ENV_VARS[_env_var_name(_name)] = (*_spec.config_path, "service_url")


class ConfigError(Exception):
    """Raised when configuration is invalid."""

    pass


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load and validate configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary with validated configuration

    Raises:
        ConfigError: If configuration is invalid or missing
    """
    path = Path(config_path)

    if not path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in configuration file: {e}")

    if config is None:
        raise ConfigError("Configuration file is empty")

    # Validate required sections
    _validate_config(config)

    # Apply environment variable overrides for service URLs
    _apply_env_overrides(config)

    return config


def _apply_env_overrides(config: Dict[str, Any]) -> None:
    """Override service URLs from environment variables if set.

    Walks each mapping's path (any depth, e.g. reconnaissance.subfinder.service_url),
    creating intermediate dicts as needed.
    """
    for env_var, path in _SERVICE_URL_ENV_VARS.items():
        value = os.environ.get(env_var)
        if not value:
            continue
        node = config
        for key in path[:-1]:
            node = node.setdefault(key, {})
        node[path[-1]] = value


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration structure and values.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigError: If configuration is invalid
    """
    required_sections = [
        "server",
        "workspace",
        "resources",
        "logging",
    ]

    for section in required_sections:
        if section not in config:
            raise ConfigError(f"Missing required configuration section: {section}")

    # Validate server settings
    server = config["server"]
    _validate_int(server, "port", "server", 1)
    _validate_string(server, "host", "server")

    # Validate workspace settings
    workspace = config["workspace"]
    _validate_int(workspace, "max_workspaces", "workspace", 1)
    _validate_int(workspace, "auto_cleanup_seconds", "workspace", 0)

    # Validate resource limits
    resources = config["resources"]
    _validate_int(resources, "max_disk_mb", "resources", 1)
    _validate_int(resources, "max_memory_mb", "resources", 1)
    _validate_int(resources, "max_cpu_cores", "resources", 1)

    # Validate logging settings
    logging = config["logging"]
    _validate_string(logging, "level", "logging")
    _validate_string(logging, "file", "logging")

    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if logging["level"] not in valid_log_levels:
        raise ConfigError(f"Invalid log level: {logging['level']}. Must be one of {valid_log_levels}")


def _validate_int(section: Dict[str, Any], key: str, section_name: str, min_val: int) -> None:
    """Validate that a value is an integer >= min_val."""
    if key not in section:
        raise ConfigError(f"Missing required key '{key}' in section '{section_name}'")

    value = section[key]
    if not isinstance(value, int) or value < min_val:
        raise ConfigError(f"'{section_name}.{key}' must be an integer >= {min_val}, got: {value}")


def _validate_string(section: Dict[str, Any], key: str, section_name: str) -> None:
    """Validate that a value is a non-empty string."""
    if key not in section:
        raise ConfigError(f"Missing required key '{key}' in section '{section_name}'")

    value = section[key]
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{section_name}.{key}' must be a non-empty string, got: {value}")
