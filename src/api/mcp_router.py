"""MCPRouter wrapper for organizing tools into namespaced routers."""

import logging
from typing import Callable, List, Optional

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


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
                mcp.tool(name=name)(tool_func)
            except Exception as e:
                logger.error(f"  ERROR registering tool {name}: {e}")

        # Register included routers' tools
        for router in self._routers:
            router.register_tools(mcp)
