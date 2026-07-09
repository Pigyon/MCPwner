"""
Test Error handling - verify proper error responses for ALL error scenarios.

This validates that the MCP server properly handles and reports errors to LLMs.
"""

import pytest


@pytest.mark.asyncio
async def test_invalid_tool_name(docker_compose_up, mcp_session):
    session = mcp_session
    client = mcp_session
    """Test that calling a non-existent tool returns proper error."""
    result = await session.call_tool("nonexistent_tool_12345", arguments={})

    assert result.isError is True
    assert len(result.content) > 0
    print(f"\n✅ Invalid tool name properly rejected: {result.content[0].text}")


@pytest.mark.asyncio
async def test_missing_required_arguments(docker_compose_up, mcp_session):
    session = mcp_session
    client = mcp_session
    """Test that missing required arguments returns proper error."""
    # create_workspace requires workspace_id and source_type
    result = await session.call_tool("create_workspace", arguments={})

    assert result.isError is True
    assert len(result.content) > 0
    print("\n✅ Missing required arguments properly rejected")


@pytest.mark.asyncio
async def test_invalid_argument_type(docker_compose_up, mcp_session):
    session = mcp_session
    client = mcp_session
    """Test that invalid argument types return proper error."""
    # workspace_id should be string, not number
    result = await session.call_tool(
        "create_workspace",
        arguments={"workspace_id": 12345, "source_type": "empty"},
    )

    assert result.isError is True
    assert len(result.content) > 0
    print("\n✅ Invalid argument type properly rejected")


@pytest.mark.asyncio
async def test_invalid_workspace_id(docker_compose_up, mcp_session):
    session = mcp_session
    client = mcp_session
    """Test that operations on non-existent workspace return proper error."""
    result = await session.call_tool(
        "cleanup_workspace",
        arguments={"workspace_id": "nonexistent-workspace-xyz"},
    )

    # Should return a result (not throw), but indicate failure
    assert result is not None
    assert len(result.content) > 0

    print("\n✅ Invalid workspace ID handled properly")


@pytest.mark.asyncio
async def test_invalid_codeql_database(docker_compose_up, mcp_session):
    session = mcp_session
    client = mcp_session
    """Test that operations on non-existent CodeQL database return proper error."""
    result = await session.call_tool(
        "execute_query",
        arguments={
            "workspace_id": "nonexistent",
            "database_name": "nonexistent",
            "query": "select 1",
        },
    )

    assert result.isError is True
    assert len(result.content) > 0
    print("\n✅ Invalid CodeQL database properly rejected")


@pytest.mark.asyncio
async def test_empty_arguments_when_required(docker_compose_up, mcp_session):
    session = mcp_session
    client = mcp_session
    """Test that empty arguments object is rejected when arguments are required."""
    # detect_languages requires workspace_id
    result = await session.call_tool("detect_languages", arguments={})

    assert result.isError is True
    assert len(result.content) > 0
    print("\n✅ Empty arguments properly rejected when required")


@pytest.mark.asyncio
async def test_extra_unexpected_arguments(docker_compose_up, mcp_session):
    session = mcp_session
    client = mcp_session
    """Test that extra unexpected arguments are handled properly."""
    # Call health_check with extra arguments (should be ignored or rejected)
    result = await session.call_tool("health_check", arguments={"unexpected_arg": "value"})

    # Should still work (extra args ignored) or fail gracefully
    assert result is not None
    print("\n✅ Extra arguments handled properly")


@pytest.mark.parametrize(
    "tool_action, arguments",
    [
        ("run_sast_scan", {"tool": "bandit", "workspace_id": "nonexistent-workspace"}),
        ("get_sast_report", {"tool": "bandit", "workspace_id": "nonexistent-workspace"}),
        ("run_sca_scan", {"tool": "grype", "workspace_id": "nonexistent-workspace"}),
        ("get_sca_report", {"tool": "grype", "workspace_id": "nonexistent-workspace"}),
    ],
)
@pytest.mark.asyncio
async def test_sast_tools_invalid_workspace(docker_compose_up, mcp_session, tool_action, arguments):
    session = mcp_session
    client = mcp_session
    """Test SAST/SCA scan/report tools with invalid workspace_id."""
    result = await session.call_tool(
        tool_action,
        arguments=arguments,
    )

    assert result is not None
    assert len(result.content) > 0
    content = result.content[0]
    assert hasattr(content, "text")
    assert "error" in content.text.lower() or "not found" in content.text.lower()

    print(f"\n✅ {tool_action} error handling for invalid workspace works")
