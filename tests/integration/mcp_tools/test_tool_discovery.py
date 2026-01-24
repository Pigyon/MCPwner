"""
Test Tool discovery - verify ALL tools are exposed via MCP protocol.

This test ensures that LLMs can discover all available tools.
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
async def test_all_tools_discoverable(docker_compose_up):
    """Test that ALL expected tools are discoverable via MCP protocol."""
    async with create_mcp_client() as session:
        # List all available tools
        tools_result = await session.list_tools()
        tools = tools_result.tools

        # Extract tool names
        tool_names = [tool.name for tool in tools]

        print(f"\n📋 Discovered {len(tool_names)} tools:")
        for name in sorted(tool_names):
            print(f"  - {name}")

        # Complete list of ALL expected tools based on routers
        expected_tools = [
            # Health tools (no prefix)
            "health_check",
            "list_tools",
            # Workspace tools (workspace_ prefix)
            "workspace_create_workspace",
            "workspace_list_workspaces",
            "workspace_cleanup_workspace",
            # CodeQL tools (codeql_ prefix)
            "codeql_detect_languages",
            "codeql_create_codeql_database",
            "codeql_list_databases",
            "codeql_execute_query",
            "codeql_list_query_packs",
            "codeql_extract_code_context",
            "codeql_get_function_context",
            "codeql_get_callers",
            "codeql_get_callees",
            "codeql_search_functions",
            "codeql_list_functions",
            # SAST tools (no prefix)
            "sast_list_tools",
        ]

        # Verify ALL expected tools are present
        missing_tools = []
        for expected_tool in expected_tools:
            if expected_tool not in tool_names:
                missing_tools.append(expected_tool)

        # Verify no tools are missing
        assert len(missing_tools) == 0, f"Missing tools: {missing_tools}"

        # Verify no unexpected tools
        unexpected_tools = [t for t in tool_names if t not in expected_tools]
        if unexpected_tools:
            print(f"\n⚠️  Unexpected tools found: {unexpected_tools}")

        print(f"\n✅ All {len(expected_tools)} expected tools are discoverable")
        print(f"   Total tools: {len(tool_names)}")


@pytest.mark.asyncio
async def test_tool_metadata(docker_compose_up):
    """Test that all tools have proper metadata (name, description, schema)."""
    async with create_mcp_client() as session:
        # List all available tools
        tools_result = await session.list_tools()
        tools = tools_result.tools

        print(f"\n🔍 Validating metadata for {len(tools)} tools:")

        for tool in tools:
            # Verify each tool has required metadata
            assert tool.name, "Tool missing name"
            assert tool.description, f"Tool '{tool.name}' missing description"
            assert tool.inputSchema, f"Tool '{tool.name}' missing input schema"

            print(f"  ✓ {tool.name}")

        print("\n✅ All tools have proper metadata")
