"""MCPRouter wrapper for organizing tools into namespaced routers."""

from typing import Callable, Optional, List
from fastmcp import FastMCP


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
        self._routers: List['MCPRouter'] = []
    
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
    
    def include_router(self, router: 'MCPRouter'):
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
        for tool_func in self._tools:
            # Apply prefix if set
            if self.prefix:
                # Store original name
                original_name = tool_func.__name__
                # Create wrapper with prefixed name
                tool_func.__name__ = f"{self.prefix}_{original_name}"
            
            mcp.tool()(tool_func)
        
        # Register included routers' tools
        for router in self._routers:
            router.register_tools(mcp)
