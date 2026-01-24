"""
Test Tool execution - test calling ALL tools via MCP protocol.

This validates that LLMs can successfully execute all available tools.
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
            "BANDIT_SERVICE_URL": "http://localhost:8083",
            "GOSEC_SERVICE_URL": "http://localhost:8084",
        },
    )

    async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        yield session


@pytest.mark.asyncio
async def test_health_check_tool(docker_compose_up):
    """Test executing health_check tool."""
    async with create_mcp_client() as session:
        result = await session.call_tool("health_check", arguments={})

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ health_check executed successfully")


@pytest.mark.asyncio
async def test_list_tools_tool(docker_compose_up):
    """Test executing list_tools tool."""
    async with create_mcp_client() as session:
        result = await session.call_tool("list_tools", arguments={})

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ list_tools executed successfully")


@pytest.mark.asyncio
async def test_workspace_list_workspaces_tool(docker_compose_up):
    """Test executing workspace_list_workspaces tool."""
    async with create_mcp_client() as session:
        result = await session.call_tool("workspace_list_workspaces", arguments={})

        assert result is not None
        assert result.isError is False
        # Empty list is valid - no workspaces created yet
        assert result.content is not None

        print("\n✅ workspace_list_workspaces executed successfully")


@pytest.mark.asyncio
async def test_codeql_list_databases_tool(docker_compose_up):
    """Test executing codeql_list_databases tool."""
    async with create_mcp_client() as session:
        result = await session.call_tool("codeql_list_databases", arguments={})

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ codeql_list_databases executed successfully")


@pytest.mark.asyncio
async def test_codeql_list_query_packs_tool(docker_compose_up):
    """Test executing codeql_list_query_packs tool."""
    async with create_mcp_client() as session:
        result = await session.call_tool("codeql_list_query_packs", arguments={})

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ codeql_list_query_packs executed successfully")


@pytest.mark.asyncio
async def test_sast_list_tools_tool(docker_compose_up):
    """Test executing sast_list_tools tool."""
    async with create_mcp_client() as session:
        result = await session.call_tool("sast_list_tools", arguments={})

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ sast_list_tools executed successfully")


@pytest.mark.asyncio
async def test_workspace_create_workspace_tool(docker_compose_up):
    """Test executing workspace_create_workspace tool with valid arguments."""
    async with create_mcp_client() as session:
        result = await session.call_tool(
            "workspace_create_workspace",
            arguments={"workspace_id": "test-workspace-mcp", "source_type": "empty"},
        )

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ workspace_create_workspace executed successfully")

        # Cleanup
        await session.call_tool(
            "workspace_cleanup_workspace",
            arguments={"workspace_id": "test-workspace-mcp"},
        )


@pytest.mark.asyncio
async def test_workspace_cleanup_workspace_tool(docker_compose_up):
    """Test executing workspace_cleanup_workspace tool."""
    async with create_mcp_client() as session:
        # Create a workspace first
        await session.call_tool(
            "workspace_create_workspace",
            arguments={"workspace_id": "test-cleanup-mcp", "source_type": "empty"},
        )

        # Now cleanup
        result = await session.call_tool(
            "workspace_cleanup_workspace",
            arguments={"workspace_id": "test-cleanup-mcp"},
        )

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ workspace_cleanup_workspace executed successfully")
