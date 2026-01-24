"""Configuration management for MCPwner."""

from pathlib import Path
from typing import Any, Dict

import yaml


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

    return config


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
        "timeouts",
        "rate_limits",
        "security",
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
    _validate_string(workspace, "base_path", "workspace")

    # Validate resource limits
    resources = config["resources"]
    _validate_positive_int(resources, "max_disk_mb", "resources")
    _validate_positive_int(resources, "max_memory_mb", "resources")
    _validate_positive_int(resources, "max_cpu_cores", "resources")

    # Validate timeouts
    timeouts = config["timeouts"]
    _validate_positive_int(timeouts, "database_creation", "timeouts")
    _validate_positive_int(timeouts, "query_execution", "timeouts")
    _validate_positive_int(timeouts, "workspace_creation", "timeouts")

    # Validate rate limits
    rate_limits = config["rate_limits"]
    _validate_positive_int(rate_limits, "queries_per_minute", "rate_limits")
    _validate_positive_int(rate_limits, "databases_per_hour", "rate_limits")

    # Validate security settings
    security = config["security"]
    _validate_bool(security, "allow_custom_queries", "security")
    _validate_list(security, "allowed_source_types", "security")
    _validate_non_negative_int(security, "github_rate_limit", "security")

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
