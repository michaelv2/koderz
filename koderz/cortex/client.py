"""MCP client for connecting to claude-cortex-core server."""

import asyncio
from typing import Optional, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class CortexClient:
    """Client for interacting with claude-cortex-core MCP server."""

    def __init__(self, cortex_path: str):
        """Initialize Cortex MCP client.

        Args:
            cortex_path: Path to cortex-core dist/index.js
        """
        self.server_params = StdioServerParameters(
            command="node",
            args=[cortex_path]
        )

    async def remember(
        self,
        title: str,
        content: str,
        category: str = "custom",
        tags: Optional[list[str]] = None,
        importance: str = "medium",
        metadata: Optional[dict] = None
    ) -> dict:
        """Store a memory via MCP remember tool.

        Args:
            title: Memory title
            content: Memory content
            category: Memory category
            tags: List of tags
            importance: Importance level (low/medium/high)
            metadata: Additional metadata dictionary

        Returns:
            Result from remember tool
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                params = {
                    "title": title,
                    "content": content,
                    "category": category,
                    "importance": importance
                }

                if tags:
                    params["tags"] = ",".join(tags)

                if metadata:
                    params["metadata"] = metadata

                result = await session.call_tool("remember", params)
                return result

    async def recall(
        self,
        query: str,
        tags: Optional[list[str]] = None,
        category: Optional[str] = None,
        limit: int = 10,
        mode: str = "balanced"
    ) -> list[dict]:
        """Query memories via MCP recall tool.

        Args:
            query: Search query
            tags: Filter by tags
            category: Filter by category
            limit: Maximum results
            mode: Search mode (balanced/recent/important)

        Returns:
            List of matching memories
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                params = {
                    "query": query,
                    "limit": limit,
                    "mode": mode
                }

                if tags:
                    params["tags"] = ",".join(tags)

                if category:
                    params["category"] = category

                result = await session.call_tool("recall", params)

                # Parse the result - MCP returns content with memories
                if hasattr(result, 'content') and len(result.content) > 0:
                    # The recall tool returns formatted text, we need to parse it
                    # For now, return raw result
                    return result.content
                return []

    async def start_session(self, context: Optional[str] = None) -> dict:
        """Start a new session.

        Args:
            context: Optional session context

        Returns:
            Session start result
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                params = {}
                if context:
                    params["context"] = context

                result = await session.call_tool("start_session", params)
                return result

    async def end_session(self) -> dict:
        """End current session and trigger consolidation.

        Returns:
            Session end result
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("end_session", {})
                return result

    async def consolidate(self, dry_run: bool = False) -> dict:
        """Manually trigger memory consolidation.

        Args:
            dry_run: If True, show what would happen without making changes

        Returns:
            Consolidation result
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("consolidate", {"dryRun": dry_run})
                return result

    async def get_stats(self) -> dict:
        """Get memory statistics.

        Returns:
            Memory statistics
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("memory_stats", {})
                return result
