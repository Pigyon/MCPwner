"""Transport configuration for MCP server."""

import os
from typing import Any, Dict


def get_transport_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine transport configuration from environment and config file.

    Args:
        config: Loaded configuration dictionary

    Returns:
        Dictionary with transport, host, and port
    """
    # Get transport from environment or config
    transport = os.environ.get("MCP_TRANSPORT")
    if transport:
        transport = transport.lower()
    else:
        transport = config.get("transport", {}).get("type", "stdio").lower()

    # Get server settings from config
    server_config = config.get("server", {})

    return {
        "transport": transport,
        "host": server_config.get("host", "0.0.0.0"),
        "port": server_config.get("port", 13370),
    }
