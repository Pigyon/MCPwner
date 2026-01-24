#!/usr/bin/env python3
"""
Supports STDIO and SSE transports with namespaced tools.
"""

import sys
from fastmcp import FastMCP
from config.config import load_config, ConfigError
from config.transport import get_transport_config
from api.router import router as api_router

# Load configuration
try:
    config = load_config("config/config.yaml")
    print(f"Configuration loaded successfully from config/config.yaml", file=sys.stderr)
except ConfigError as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    sys.exit(1)

# Initialize main server
mcp = FastMCP("MCPwner")

# Register tools using main API router
print("Loading tools...", file=sys.stderr)

# Register all tools from the router
api_router.register_tools(mcp)

print("✓ All tools loaded", file=sys.stderr)


def run_server():
    """Run the MCP server with appropriate transport."""
    transport_config = get_transport_config(config)
    transport = transport_config["transport"]
    
    print(f"\nStarting MCPwner MCP server...", file=sys.stderr)
    print(f"Transport: {transport}", file=sys.stderr)
    
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
