"""MCP client for connecting to claude-cortex-core server."""

import asyncio
import json
import os
from typing import Optional, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class CortexClient:
    """Client for interacting with claude-cortex-core MCP server.

    Can be used in two modes:

    1. Ephemeral connections (one connection per call, backwards compatible):
        cortex = CortexClient(cortex_path, db_path="~/.claude-cortex/myapp.db")
        await cortex.remember(...)
        await cortex.recall(...)

    2. Persistent connection (recommended for benchmarks - much faster):
        async with CortexClient(cortex_path, db_path="~/.claude-cortex/myapp.db") as cortex:
            await cortex.remember(...)
            await cortex.recall(...)

    The persistent mode keeps a single MCP connection open for multiple operations,
    avoiding the overhead of spawning a new Node.js process for each call.
    """

    def __init__(self, cortex_path: str, db_path: Optional[str] = None):
        """Initialize Cortex MCP client.

        Args:
            cortex_path: Path to cortex-core dist/index.js
            db_path: Optional path to SQLite database file. If provided, uses
                     an isolated database instead of the default ~/.claude-cortex/memories.db
        """
        args = [cortex_path]
        if db_path:
            args.extend(["--db", db_path])

        # Pass through environment variables (especially OPENAI_API_KEY for embeddings)
        self.server_params = StdioServerParameters(
            command="node",
            args=args,
            env=dict(os.environ)  # Pass all environment variables to subprocess
        )
        self._session: Optional[ClientSession] = None
        self._read_stream = None
        self._write_stream = None
        self._client_context = None
        self._persistent = False

    async def __aenter__(self) -> "CortexClient":
        """Enter async context manager for persistent connection.

        Returns:
            Self with active persistent session.
        """
        self._client_context = stdio_client(self.server_params)
        self._read_stream, self._write_stream = await self._client_context.__aenter__()
        self._session = ClientSession(self._read_stream, self._write_stream)
        await self._session.__aenter__()
        await self._session.initialize()
        self._persistent = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager and close connection."""
        self._persistent = False
        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None
        if self._client_context:
            await self._client_context.__aexit__(exc_type, exc_val, exc_tb)
            self._client_context = None
        self._read_stream = None
        self._write_stream = None

    async def _call_tool(self, tool_name: str, params: dict) -> Any:
        """Call an MCP tool, using persistent session if available.

        Args:
            tool_name: Name of the MCP tool to call
            params: Tool parameters

        Returns:
            Tool result
        """
        if self._persistent and self._session:
            # Use persistent session
            return await self._session.call_tool(tool_name, params)
        else:
            # Fall back to ephemeral connection
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await session.call_tool(tool_name, params)

    async def remember(
        self,
        title: str,
        content: str,
        category: str = "custom",
        tags: Optional[list[str]] = None,
        importance: str = "normal",
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
        params = {
            "title": title,
            "content": content,
            "category": category,
            "importance": importance
        }

        if tags:
            params["tags"] = tags

        if metadata:
            params["metadata"] = metadata

        return await self._call_tool("remember", params)

    async def recall(
        self,
        query: str,
        tags: Optional[list[str]] = None,
        category: Optional[str] = None,
        limit: int = 10,
        mode: str = "search",
        searchMode: str = "hybrid",
        vectorWeight: float = 0.7,
        keywordWeight: float = 0.3
    ) -> list[dict]:
        """Query memories via MCP recall tool.

        Args:
            query: Search query
            tags: Filter by tags
            category: Filter by category
            limit: Maximum results
            mode: Recall mode (search/recent/important)
            searchMode: Search algorithm (hybrid/semantic/keyword)
            vectorWeight: Weight for vector similarity in hybrid mode (0.0-1.0)
            keywordWeight: Weight for keyword score in hybrid mode (0.0-1.0)

        Returns:
            List of matching memories as dictionaries
        """
        params = {
            "query": query,
            "limit": limit,
            "mode": mode,
            "searchMode": searchMode,
            "vectorWeight": vectorWeight,
            "keywordWeight": keywordWeight
        }

        if tags:
            params["tags"] = tags  # Pass as array, not comma-separated string

        if category:
            params["category"] = category

        result = await self._call_tool("recall", params)

        # Parse the result - MCP returns TextContent objects
        memories = []
        if hasattr(result, 'content') and len(result.content) > 0:
            # Each content item is a TextContent object with a 'text' attribute
            for content_item in result.content:
                if hasattr(content_item, 'text'):
                    # Parse the text to extract memory data
                    # The recall tool returns formatted text, so we return it as-is
                    # for the orchestrator to parse
                    memories.append({
                        'text': content_item.text,
                        'type': getattr(content_item, 'type', 'text')
                    })

        return memories

    async def start_session(self, context: Optional[str] = None) -> dict:
        """Start a new session.

        Args:
            context: Optional session context

        Returns:
            Session start result
        """
        params = {}
        if context:
            params["context"] = context

        return await self._call_tool("start_session", params)

    async def end_session(self) -> dict:
        """End current session and trigger consolidation.

        Returns:
            Session end result
        """
        return await self._call_tool("end_session", {})

    async def consolidate(self, dry_run: bool = False) -> dict:
        """Manually trigger memory consolidation.

        Args:
            dry_run: If True, show what would happen without making changes

        Returns:
            Consolidation result
        """
        return await self._call_tool("consolidate", {"dryRun": dry_run})

    async def get_stats(self) -> dict:
        """Get memory statistics.

        Returns:
            Memory statistics
        """
        return await self._call_tool("memory_stats", {})

    async def export_memories(
        self,
        tags: Optional[list[str]] = None,
        category: Optional[str] = None
    ) -> list[dict]:
        """Export memories with full structured data.

        Args:
            tags: Filter by tags
            category: Filter by category

        Returns:
            List of memory dictionaries with full structure
        """
        params = {}
        if tags:
            params["tags"] = tags  # Pass as array, not comma-separated string
        if category:
            params["category"] = category

        result = await self._call_tool("export_memories", params)

        # Parse JSON export
        if hasattr(result, 'content') and len(result.content) > 0:
            for content_item in result.content:
                if hasattr(content_item, 'text'):
                    try:
                        text = content_item.text
                        # Extract JSON array from text like "Exported N memories:\n\n[...]"
                        if '[' in text and ']' in text:
                            json_start = text.index('[')
                            json_end = text.rindex(']') + 1
                            json_str = text[json_start:json_end]
                            memories = json.loads(json_str)

                            # Parse JSON string fields (tags, metadata)
                            if isinstance(memories, list):
                                for memory in memories:
                                    if 'tags' in memory and isinstance(memory['tags'], str):
                                        try:
                                            memory['tags'] = json.loads(memory['tags'])
                                        except:
                                            memory['tags'] = []
                                    if 'metadata' in memory and isinstance(memory['metadata'], str):
                                        try:
                                            memory['metadata'] = json.loads(memory['metadata'])
                                        except:
                                            memory['metadata'] = {}

                            return memories if isinstance(memories, list) else []
                    except (json.JSONDecodeError, ValueError):
                        return []
        return []
