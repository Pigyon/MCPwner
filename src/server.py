#!/usr/bin/env python3
"""
Supports STDIO transport with namespaced tools.
"""

import logging
import os
import sys

from fastmcp import FastMCP

try:
    from config.config import load_config
    from config.logging import setup_logging

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "config.yaml",
    )
    config = load_config(config_path)

    setup_logging(config)
    logger = logging.getLogger(__name__)

    logger.info(f"Configuration loaded successfully from {config_path}")
except Exception as e:
    logging.basicConfig(level=logging.ERROR)
    logging.error(f"Configuration error: {e}")
    sys.exit(1)

mcp = FastMCP("MCPwner")

logger.info("Loading tools...")
try:
    import config.tools as tools_module
    from config.health import update_healthy_tools

    # update_healthy_tools() must run before api.router import: HEALTHY_TOOLS is
    # captured at module-load time during tool discovery.
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

    logger.info("Registering tools from api_router...")
    api_router.register_tools(mcp)
    logger.info("All tools loaded")
except Exception:
    logger.exception("Tool loading failed")
    # Don't exit, try to run anyway so we can see logs


def run_server():
    """Run the MCP server."""
    logger.info("Starting MCPwner MCP server in STDIO mode...")
    logger.info("Reading from stdin, writing to stdout")
    logger.info("Compatible with: Claude Desktop, MCP CLI tools")

    mcp.run()


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        sys.exit(0)
    except Exception:
        logger.exception("Fatal error occurred")
        sys.exit(1)
