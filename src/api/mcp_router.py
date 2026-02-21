"""MCPRouter wrapper for organizing tools into namespaced routers."""

from typing import Callable, List, Optional
import sys
import logging

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

    def tool(self):
        """
        Decorator to register a tool function.

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
        # Register own tools
        logger.info(f"Registering {len(self._tools)} tools for prefix '{self.prefix}'")
        for tool_func in self._tools:
            original_name = tool_func.__name__
            
            # Apply prefix if set
            names_to_register = []
            if self.prefix:
                name_snake = f"{self.prefix}_{original_name}"
                name_kebab = name_snake.replace("_", "-")
                
                names_to_register.extend([name_snake, name_kebab])
            
            # ALWAYS register original name and its kebab variant
            names_to_register.append(original_name)
            names_to_register.append(original_name.replace("_", "-"))
            
            # Remove duplicates
            names_to_register = list(set(names_to_register))

            for name in names_to_register:
                logger.debug(f"  Registering tool: {name}")
                try:
                    # Use the name argument to force the name
                    mcp.tool(name=name)(tool_func)
                except Exception as e:
                    logger.error(f"  ERROR registering tool {name}: {e}")

        # Register included routers' tools
        for router in self._routers:
            router.register_tools(mcp)
