#!/usr/bin/env python3
"""
Enhanced MCP server with FastMCP 3.0.
Uses FileSystemProvider for hot reload and modular tool organization.
"""

import sys
import os
from fastmcp import FastMCP
from fastmcp.providers import FileSystemProvider
from config.config import load_config, ConfigError

# Load configuration
try:
    config = load_config("config/config.yaml")
    print(f"Configuration loaded successfully from config/config.yaml", file=sys.stderr)
except ConfigError as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    sys.exit(1)

# Initialize main server
mcp = FastMCP("MCPwner")

# Add FileSystemProviders with namespacing for each domain
# Hot reload enabled for development
print("Loading tools from filesystem...", file=sys.stderr)

# Health tools (no namespace - global)
health_provider = FileSystemProvider(
    "src/api/tools/health",
    reload=True
)
mcp.add_provider(health_provider)

# Workspace tools (with namespace)
workspace_provider = FileSystemProvider(
    "src/api/tools/workspace",
    reload=True
)
mcp.add_provider(workspace_provider, namespace="workspace")

# CodeQL tools (with namespace)
codeql_provider = FileSystemProvider(
    "src/api/tools/codeql",
    reload=True
)
mcp.add_provider(codeql_provider, namespace="codeql")

print("✓ All tools loaded with hot reload enabled", file=sys.stderr)


# ============================================================================
# TRANSPORT CONFIGURATION
# ============================================================================

def get_transport_config():
    """Determine transport configuration from environment and config file."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    
    config_data = {
        "transport": transport,
        "host": "0.0.0.0",
        "port": 13370
    }
    
    # Load from config file if available
    if transport == "sse":
        server_config = config.get("server", {})
        config_data["host"] = server_config.get("host", "0.0.0.0")
        config_data["port"] = server_config.get("port", 13370)
    
    return config_data


def run_server():
    """Run the MCP server with appropriate transport."""
    transport_config = get_transport_config()
    transport = transport_config["transport"]
    
    print(f"\nStarting MCPwner MCP server (FastMCP 3.0)...", file=sys.stderr)
    print(f"Transport: {transport}", file=sys.stderr)
    print(f"Hot reload: enabled", file=sys.stderr)
    
    if transport == "sse":
        host = transport_config["host"]
        port = transport_config["port"]
        print(f"SSE endpoint: http://{host}:{port}/sse", file=sys.stderr)
        print(f"Health check: http://{host}:{port}/health", file=sys.stderr)
        
        # Run with SSE transport
        mcp.run(transport="sse", host=host, port=port)
        
    elif transport == "stdio":
        print(f"STDIO mode: Reading from stdin, writing to stdout", file=sys.stderr)
        print(f"Compatible with: Claude Desktop, MCP CLI tools", file=sys.stderr)
        
        # Run with STDIO transport (default)
        mcp.run()
        
    else:
        print(f"ERROR: Unknown transport '{transport}'", file=sys.stderr)
        print(f"Supported transports: stdio, sse", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
