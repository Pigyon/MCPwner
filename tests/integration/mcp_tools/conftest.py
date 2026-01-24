"""Shared fixtures for MCP tool tests."""

import sys
import os
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def create_mcp_client():
    """
    Create an MCP client connected to the server via stdio.
    
    This is a shared helper that can be used across all MCP tests.
    Uses sys.executable to ensure cross-platform compatibility.
    """
    # Get the mcpwner root directory (two levels up from this file)
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
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session
