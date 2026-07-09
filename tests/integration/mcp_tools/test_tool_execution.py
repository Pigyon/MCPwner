"""
Test Tool execution - test calling ALL tools via MCP protocol.

This validates that LLMs can successfully execute all available tools.
"""

import json

import pytest

from tests.integration.mcp_tools.conftest import create_mcp_client


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
    """Test executing health_list_tools tool."""
    async with create_mcp_client() as session:
        result = await session.call_tool("health_list_tools", arguments={})

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ health_list_tools executed successfully")


@pytest.mark.asyncio
async def test_workspace_list_workspaces_tool(docker_compose_up):
    """Test executing list_workspaces tool."""
    async with create_mcp_client() as session:
        result = await session.call_tool("list_workspaces", arguments={})

        assert result is not None
        assert result.isError is False
        # Empty list is valid - no workspaces created yet
        assert result.content is not None

        print("\n✅ list_workspaces executed successfully")


@pytest.mark.asyncio
async def test_codeql_list_databases_tool(docker_compose_up):
    """Test executing list_databases tool."""
    async with create_mcp_client() as session:
        result = await session.call_tool("list_databases", arguments={})

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ list_databases executed successfully")


@pytest.mark.asyncio
async def test_codeql_list_query_packs_tool(docker_compose_up):
    """Test executing list_query_packs tool."""
    async with create_mcp_client() as session:
        result = await session.call_tool("list_query_packs", arguments={})

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ list_query_packs executed successfully")


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
    """Test executing create_workspace tool with valid arguments."""
    async with create_mcp_client() as session:
        result = await session.call_tool(
            "create_workspace",
            arguments={"workspace_id": "test-workspace-mcp", "source_type": "empty"},
        )

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ create_workspace executed successfully")

        # Cleanup
        await session.call_tool(
            "cleanup_workspace",
            arguments={"workspace_id": "test-workspace-mcp"},
        )


@pytest.mark.asyncio
async def test_workspace_cleanup_workspace_tool(docker_compose_up):
    """Test executing cleanup_workspace tool."""
    async with create_mcp_client() as session:
        # Create a workspace first
        await session.call_tool(
            "create_workspace",
            arguments={"workspace_id": "test-cleanup-mcp", "source_type": "empty"},
        )

        # Now cleanup
        result = await session.call_tool(
            "cleanup_workspace",
            arguments={"workspace_id": "test-cleanup-mcp"},
        )

        assert result is not None
        assert len(result.content) > 0
        content = result.content[0]
        assert hasattr(content, "text")

        print("\n✅ cleanup_workspace executed successfully")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_name",
    [
        "sast_list_tools",
        "sca_list_tools",
        "secrets_list_tools",
        "reconnaissance_list_tools",
        "utilities_list_tools",
        "fuzzing_list_tools",
        "iac_list_tools",
        "dast_list_tools",
    ],
)
async def test_list_tools(docker_compose_up, tool_name):
    """Test all *_list_tools tools."""
    async with create_mcp_client() as client:
        result = await client.call_tool(tool_name, {})
        assert result.isError is False
        assert result.content
        data = json.loads(result.content[0].text)
        assert data["status"] == "success"
        assert "tools" in data
