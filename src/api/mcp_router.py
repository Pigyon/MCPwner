"""MCPRouter wrapper for organizing tools into namespaced routers."""

import asyncio
import functools
import inspect
import logging
from typing import Callable, List, Optional

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
    Router for organizing MCP tools with optional prefix.

    This class provides a way to group related tools together and optionally
    namespace them with a prefix.
    """

    def __init__(self, prefix: Optional[str] = None):
        """
        Initialize router with optional prefix.

        Args:
            prefix: Optional prefix for tool names (e.g., "codeql")
        """
        self.prefix = prefix
        self._tools: List[Callable] = []
        self._routers: List["MCPRouter"] = []

    def tool(self, name: Optional[str] = None):
        """
        Decorator to register a tool function.

        Args:
            name: Optional explicit name for the tool (ignored in this version)

        Returns:
            Decorator function
        """

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
        logger.info(f"Registering {len(self._tools)} tools for prefix '{self.prefix}'")
        for tool_func in self._tools:
            # Use prefixed name if prefix is set, otherwise use the function name as-is
            name = f"{self.prefix}_{tool_func.__name__}" if self.prefix else tool_func.__name__
            logger.debug(f"  Registering tool: {name}")
            try:
                mcp.tool(name=name)(_ensure_async(tool_func))
            except Exception as e:
                logger.error(f"  ERROR registering tool {name}: {e}")

        # Register included routers' tools
        for router in self._routers:
            router.register_tools(mcp)
