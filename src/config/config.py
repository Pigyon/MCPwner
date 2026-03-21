"""Configuration management for MCPwner."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml

# Mapping from environment variable names to config paths (section, key)
_SERVICE_URL_ENV_VARS = {
    "CODEQL_SERVICE_URL": ("codeql", "service_url"),
    "LINGUIST_SERVICE_URL": ("linguist", "service_url"),
    "SEMGREP_SERVICE_URL": ("semgrep", "service_url"),
    "BANDIT_SERVICE_URL": ("bandit", "service_url"),
    "GOSEC_SERVICE_URL": ("gosec", "service_url"),
    "BRAKEMAN_SERVICE_URL": ("brakeman", "service_url"),
    "PMD_SERVICE_URL": ("pmd", "service_url"),
    "PSALM_SERVICE_URL": ("psalm", "service_url"),
    "OSV_SCANNER_SERVICE_URL": ("osv_scanner", "service_url"),
    "GRYPE_SERVICE_URL": ("grype", "service_url"),
    "SYFT_SERVICE_URL": ("syft", "service_url"),
    "RETIREJS_SERVICE_URL": ("retirejs", "service_url"),
    "SUBFINDER_SERVICE_URL": ("reconnaissance", "subfinder", "service_url"),
}


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
    """Override service URLs from environment variables if set."""
    for env_var, path_tuple in _SERVICE_URL_ENV_VARS.items():
        value = os.environ.get(env_var)
        if value:
            # Handle nested paths (e.g., reconnaissance.subfinder.service_url)
            if len(path_tuple) == 2:
                section, key = path_tuple
                if section not in config:
                    config[section] = {}
                config[section][key] = value
            elif len(path_tuple) == 3:
                section, subsection, key = path_tuple
                if section not in config:
                    config[section] = {}
                if subsection not in config[section]:
                    config[section][subsection] = {}
                config[section][subsection][key] = value


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
    _validate_positive_int(server, "port", "server")
    _validate_string(server, "host", "server")

    # Validate workspace settings
    workspace = config["workspace"]
    _validate_positive_int(workspace, "max_workspaces", "workspace")
    _validate_non_negative_int(workspace, "auto_cleanup_seconds", "workspace")

    # Validate resource limits
    resources = config["resources"]
    _validate_positive_int(resources, "max_disk_mb", "resources")
    _validate_positive_int(resources, "max_memory_mb", "resources")
    _validate_positive_int(resources, "max_cpu_cores", "resources")

    # Validate logging settings
    logging = config["logging"]
    _validate_string(logging, "level", "logging")
    _validate_string(logging, "file", "logging")

    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if logging["level"] not in valid_log_levels:
        raise ConfigError(f"Invalid log level: {logging['level']}. Must be one of {valid_log_levels}")


def _validate_positive_int(section: Dict[str, Any], key: str, section_name: str) -> None:
    """Validate that a value is a positive integer."""
    if key not in section:
        raise ConfigError(f"Missing required key '{key}' in section '{section_name}'")

    value = section[key]
    if not isinstance(value, int) or value <= 0:
        raise ConfigError(f"'{section_name}.{key}' must be a positive integer, got: {value}")


def _validate_non_negative_int(section: Dict[str, Any], key: str, section_name: str) -> None:
    """Validate that a value is a non-negative integer."""
    if key not in section:
        raise ConfigError(f"Missing required key '{key}' in section '{section_name}'")

    value = section[key]
    if not isinstance(value, int) or value < 0:
        raise ConfigError(f"'{section_name}.{key}' must be a non-negative integer, got: {value}")


def _validate_string(section: Dict[str, Any], key: str, section_name: str) -> None:
    """Validate that a value is a non-empty string."""
    if key not in section:
        raise ConfigError(f"Missing required key '{key}' in section '{section_name}'")

    value = section[key]
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{section_name}.{key}' must be a non-empty string, got: {value}")


def _validate_bool(section: Dict[str, Any], key: str, section_name: str) -> None:
    """Validate that a value is a boolean."""
    if key not in section:
        raise ConfigError(f"Missing required key '{key}' in section '{section_name}'")

    value = section[key]
    if not isinstance(value, bool):
        raise ConfigError(f"'{section_name}.{key}' must be a boolean, got: {value}")


def _validate_list(section: Dict[str, Any], key: str, section_name: str) -> None:
    """Validate that a value is a list."""
    if key not in section:
        raise ConfigError(f"Missing required key '{key}' in section '{section_name}'")

    value = section[key]
    if not isinstance(value, list):
        raise ConfigError(f"'{section_name}.{key}' must be a list, got: {value}")
