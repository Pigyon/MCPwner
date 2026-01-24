"""Integration tests for Psalm MCP tools."""

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
            "BANDIT_SERVICE_URL": "http://localhost:8083",
            "GOSEC_SERVICE_URL": "http://localhost:8084",
            "BRAKEMAN_SERVICE_URL": "http://localhost:8085",
            "PMD_SERVICE_URL": "http://localhost:8086",
            "PSALM_SERVICE_URL": "http://localhost:8087",
        },
    )

    async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        yield session


@pytest.mark.asyncio
async def test_sast_psalm_scan_invalid_workspace(docker_compose_up):
    """Test sast_psalm_scan with invalid workspace_id."""
    async with create_mcp_client() as session:
        result = await session.call_tool(
            "sast_psalm_scan",
            arguments={"workspace_id": "nonexistent-workspace"},
        )

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")
        # Should return error for nonexistent workspace
        assert (
            "error" in content.text.lower()
            or "not found" in content.text.lower()
            or "unknown" in content.text.lower()
        )

        print("\n✅ sast_psalm_scan error handling for invalid workspace works")


@pytest.mark.asyncio
async def test_sast_psalm_get_report_invalid_workspace(docker_compose_up):
    """Test sast_psalm_get_report with invalid workspace_id."""
    async with create_mcp_client() as session:
        result = await session.call_tool(
            "sast_psalm_get_report",
            arguments={"workspace_id": "nonexistent-workspace"},
        )

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")
        # Should return error for nonexistent workspace
        assert (
            "error" in content.text.lower()
            or "not found" in content.text.lower()
            or "unknown" in content.text.lower()
        )

        print("\n✅ sast_psalm_get_report error handling for invalid workspace works")
