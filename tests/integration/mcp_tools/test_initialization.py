"""
Test MCP server initialization and handshake.

Validates that the MCP server properly initializes and responds to the handshake.
"""

import os
import sys
from contextlib import asynccontextmanager

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def create_mcp_client():
    """Create an MCP client connected to the server via stdio."""
    # Get the mcpwner root directory (two levels up from this test file)
    test_dir = os.path.dirname(os.path.abspath(__file__))
    mcpwner_root = os.path.abspath(os.path.join(test_dir, "..", "..", ".."))
    src_dir = os.path.join(mcpwner_root, "src")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "server"],
        cwd=src_dir,
        env={
            "MCP_TRANSPORT": "stdio",
            "CODEQL_SERVICE_URL": "http://localhost:8080",
            "LINGUIST_SERVICE_URL": "http://localhost:8081",
            "SEMGREP_SERVICE_URL": "http://localhost:8082",
        },
    )

    async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
        result = await session.initialize()
        yield session, result


@pytest.mark.asyncio
async def test_mcp_initialization(docker_compose_up):
    """Test MCP server initialization and handshake."""
    async with create_mcp_client() as (session, result):
        # Verify session is initialized
        assert session is not None

        # Verify initialization result
        assert result is not None
        assert result.serverInfo is not None
        assert result.serverInfo.name == "MCPwner"

        print("\n✅ MCP server initialized successfully")
        print(f"   Server name: {result.serverInfo.name}")
        print(f"   Protocol version: {result.protocolVersion}")
