"""MCPRouter wrapper for organizing tools into namespaced routers."""

import asyncio
import functools
import inspect
import logging
from typing import Callable, List

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def _ensure_async(func: Callable) -> Callable:
    """Wrap a synchronous tool function so it runs in a worker thread.

    FastMCP 2.x invokes synchronous tool functions directly on the asyncio
    event loop. Because our tool functions perform blocking I/O (e.g. a
    ``requests.post`` to a scanner container that can take ~50s), running them
    on the loop freezes the entire MCP server: while one scan blocks, every
    other request — including the IDE's ``tools/list`` and keepalive pings —
    is stalled, and the client eventually declares the connection dead.

    Offloading sync functions to a thread keeps the event loop responsive so
    the MCP SDK's per-request concurrency actually works. ``functools.wraps``
    preserves the original signature/annotations, so FastMCP still derives the
    correct input schema (``inspect.signature`` follows ``__wrapped__``).
    """
    if inspect.iscoroutinefunction(func):
        return func

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


class MCPRouter:
    """
    Router for grouping related MCP tools.

    Tools are registered with the FastMCP instance under their function name
    (the project's naming convention bakes any namespace into the function name,
    e.g. ``run_sast_scan`` / ``sast_list_tools``).
    """

    def __init__(self):
        self._tools: List[Callable] = []
        self._routers: List["MCPRouter"] = []

    def tool(self):
        """Decorator to register a tool function under its own name."""

        def decorator(func: Callable) -> Callable:
            self._tools.append(func)
            return func

        return decorator

    def include_router(self, router: "MCPRouter"):
        """
        Include another router's tools.

        Args:
            router: MCPRouter instance to include
        """
        self._routers.append(router)

    def register_tools(self, mcp: FastMCP):
        """
        Register all tools with the FastMCP instance.

        Args:
            mcp: FastMCP instance
        """
        logger.info(f"Registering {len(self._tools)} tools")
        for tool_func in self._tools:
            name = tool_func.__name__
            logger.debug(f"  Registering tool: {name}")
            try:
                mcp.tool(name=name)(_ensure_async(tool_func))
            except Exception as e:
                logger.error(f"  ERROR registering tool {name}: {e}")

        # Register included routers' tools
        for router in self._routers:
            router.register_tools(mcp)
