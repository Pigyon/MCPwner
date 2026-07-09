#!/usr/bin/env python3
"""
Supports STDIO and SSE transports with namespaced tools.
"""

import logging
import os
import sys

from fastmcp import FastMCP

# Load configuration first
try:
    from config.config import load_config
    from config.logging import setup_logging
    from config.transport import get_transport_config

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "config.yaml",
    )
    config = load_config(config_path)

    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)

    logger.info(f"Configuration loaded successfully from {config_path}")
except Exception as e:
    logging.basicConfig(level=logging.ERROR)
    logging.error(f"Configuration error: {e}")
    sys.exit(1)

# Initialize main server
mcp = FastMCP("MCPwner")

# Register tools using main API router
logger.info("Loading tools...")
try:
    import config.tools as tools_module
    from config.health import update_healthy_tools

    # CRITICAL IMPORT ORDER GUARD:
    # update_healthy_tools() MUST be executed before api.router and its tool modules
    # are imported. The tool discovery process dynamically resolves and captures
    # HEALTHY_TOOLS state at module-load time, so the global registry must be pruned first.
    update_healthy_tools()

    if not tools_module.HEALTHY_TOOLS:
        logger.warning("=================================================================")
        logger.warning(" ZERO TOOLS DETECTED: No tool containers are running/healthy!")
        logger.warning(" If you did not configure your .env file, Docker Compose will")
        logger.warning(" not start any tools by default. Please copy .env.example to")
        logger.warning(" .env and set COMPOSE_PROFILES to enable tools.")
        logger.warning("=================================================================")
except Exception as e:
    logger.error(f"Failed to probe health: {e}")

try:
    from api.router import router as api_router

    # Register all tools from the router
    logger.info("Registering tools from api_router...")
    api_router.register_tools(mcp)
    logger.info("All tools loaded")
except Exception:
    logger.exception("Tool loading failed")
    # Don't exit, try to run anyway so we can see logs


def run_server():
    """Run the MCP server with appropriate transport."""
    transport_config = get_transport_config(config)
    transport = transport_config["transport"]

    logger.info("Starting MCPwner MCP server...")
    logger.info(f"Transport: {transport}")

    if transport == "sse":
        host = transport_config["host"]
        port = transport_config["port"]
        logger.info(f"SSE endpoint: http://{host}:{port}/sse")
        logger.info(f"Health check: http://{host}:{port}/health")

        # Run with SSE transport
        mcp.run(transport="sse", host=host, port=port)

    elif transport == "stdio":
        logger.info("STDIO mode: Reading from stdin, writing to stdout")
        logger.info("Compatible with: Claude Desktop, MCP CLI tools")

        # Run with STDIO transport (default)
        mcp.run()

    else:
        logger.error(f"ERROR: Unknown transport '{transport}'")
        logger.error("Supported transports: stdio, sse")
        sys.exit(1)


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        sys.exit(0)
    except Exception:
        logger.exception("Fatal error occurred")
        sys.exit(1)
