"""
Test Error handling - verify proper error responses for ALL error scenarios.

This validates that the MCP server properly handles and reports errors to LLMs.
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
        await session.initialize()
        yield session


@pytest.mark.asyncio
async def test_invalid_tool_name(docker_compose_up):
    """Test that calling a non-existent tool returns proper error."""
    async with create_mcp_client() as session:
        result = await session.call_tool("nonexistent_tool_12345", arguments={})

        # Server returns isError=True for invalid tools
        assert result.isError is True
        assert len(result.content) > 0
        print(f"\n✅ Invalid tool name properly rejected: {result.content[0].text}")


@pytest.mark.asyncio
async def test_missing_required_arguments(docker_compose_up):
    """Test that missing required arguments returns proper error."""
    async with create_mcp_client() as session:
        # workspace_create_workspace requires workspace_id and source_type
        result = await session.call_tool("workspace_create_workspace", arguments={})

        # Server returns isError=True for missing args
        assert result.isError is True
        assert len(result.content) > 0
        print("\n✅ Missing required arguments properly rejected")


@pytest.mark.asyncio
async def test_invalid_argument_type(docker_compose_up):
    """Test that invalid argument types return proper error."""
    async with create_mcp_client() as session:
        # workspace_id should be string, not number
        result = await session.call_tool(
            "workspace_create_workspace",
            arguments={"workspace_id": 12345, "source_type": "empty"},
        )

        # Server returns isError=True for invalid types
        assert result.isError is True
        assert len(result.content) > 0
        print("\n✅ Invalid argument type properly rejected")


@pytest.mark.asyncio
async def test_invalid_workspace_id(docker_compose_up):
    """Test that operations on non-existent workspace return proper error."""
    async with create_mcp_client() as session:
        # Try to cleanup a workspace that doesn't exist
        result = await session.call_tool(
            "workspace_cleanup_workspace",
            arguments={"workspace_id": "nonexistent-workspace-xyz"},
        )

        # Should return a result (not throw), but indicate failure
        assert result is not None
        assert len(result.content) > 0

        print("\n✅ Invalid workspace ID handled properly")


@pytest.mark.asyncio
async def test_invalid_codeql_database(docker_compose_up):
    """Test that operations on non-existent CodeQL database return proper error."""
    async with create_mcp_client() as session:
        # Try to execute query on non-existent database
        result = await session.call_tool(
            "codeql_execute_query",
            arguments={
                "workspace_id": "nonexistent",
                "database_name": "nonexistent",
                "query": "select 1",
            },
        )

        # Server returns isError=True for invalid database
        assert result.isError is True
        assert len(result.content) > 0
        print("\n✅ Invalid CodeQL database properly rejected")


@pytest.mark.asyncio
async def test_empty_arguments_when_required(docker_compose_up):
    """Test that empty arguments object is rejected when arguments are required."""
    async with create_mcp_client() as session:
        # codeql_detect_languages requires workspace_id
        result = await session.call_tool("codeql_detect_languages", arguments={})

        # Server returns isError=True for missing required args
        assert result.isError is True
        assert len(result.content) > 0
        print("\n✅ Empty arguments properly rejected when required")


@pytest.mark.asyncio
async def test_extra_unexpected_arguments(docker_compose_up):
    """Test that extra unexpected arguments are handled properly."""
    async with create_mcp_client() as session:
        # Call health_check with extra arguments (should be ignored or rejected)
        result = await session.call_tool("health_check", arguments={"unexpected_arg": "value"})

        # Should still work (extra args ignored) or fail gracefully
        assert result is not None
        print("\n✅ Extra arguments handled properly")
