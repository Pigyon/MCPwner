"""
Test Tool discovery - verify ALL tools are exposed via MCP protocol.

This test ensures that LLMs can discover all available tools.
"""

import pytest

from tests.integration.mcp_tools.conftest import create_mcp_client


@pytest.mark.asyncio
async def test_all_tools_discoverable(docker_compose_up):
    """Test that ALL expected tools are discoverable via MCP protocol."""
    async with create_mcp_client() as session:
        tools_result = await session.list_tools()
        tools = tools_result.tools

        tool_names = [tool.name for tool in tools]

        print(f"\n📋 Discovered {len(tool_names)} tools:")
        for name in sorted(tool_names):
            print(f"  - {name}")

        expected_tools = {
            "health_check",
            "health_list_tools",
            "create_workspace",
            "list_workspaces",
            "cleanup_workspace",
        }

        # Dynamically build expectations based on healthy tools registry
        from config.tools import HEALTHY_TOOLS, tools_for_category

        if "linguist" in HEALTHY_TOOLS:
            expected_tools.add("detect_languages")

        if "codeql" in HEALTHY_TOOLS:
            expected_tools.update(
                ["create_codeql_database", "list_databases", "execute_query", "list_query_packs"]
            )

        categories = ["sast", "sca", "secrets", "reconnaissance", "utilities", "fuzzing", "dast", "iac"]
        for category in categories:
            if tools_for_category(category):
                expected_tools.update(
                    [f"{category}_list_tools", f"run_{category}_scan", f"get_{category}_report"]
                )
                if category == "reconnaissance":
                    expected_tools.add("run_reconnaissance_chain")

        missing_tools = []
        for expected_tool in expected_tools:
            if expected_tool not in tool_names:
                missing_tools.append(expected_tool)

        assert len(missing_tools) == 0, f"Missing tools: {missing_tools}"

        unexpected_tools = [t for t in tool_names if t not in expected_tools]
        if unexpected_tools:
            print(f"\n⚠️  Unexpected tools found: {unexpected_tools}")

        print(f"\n✅ All {len(expected_tools)} expected tools are discoverable")
        print(f"   Total tools: {len(tool_names)}")


@pytest.mark.asyncio
async def test_tool_metadata(docker_compose_up):
    """Test that all tools have proper metadata (name, description, schema)."""
    async with create_mcp_client() as session:
        tools_result = await session.list_tools()
        tools = tools_result.tools

        print(f"\n🔍 Validating metadata for {len(tools)} tools:")

        for tool in tools:
            assert tool.name, "Tool missing name"
            assert tool.description, f"Tool '{tool.name}' missing description"
            assert tool.inputSchema, f"Tool '{tool.name}' missing input schema"

            print(f"  ✓ {tool.name}")

        print("\n✅ All tools have proper metadata")
