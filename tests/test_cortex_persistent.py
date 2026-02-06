"""Tests for persistent Cortex connection."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from koderz.cortex.client import CortexClient


class TestCortexClientPersistent:
    """Tests for CortexClient persistent connection mode."""

    def test_init_not_persistent(self):
        """Test that client starts without persistent connection."""
        client = CortexClient("/fake/path/index.js")
        assert client._persistent is False
        assert client._session is None

    def test_context_manager_sets_persistent(self):
        """Test that context manager sets persistent flag."""
        client = CortexClient("/fake/path/index.js")

        async def run_test():
            # Mock the stdio_client and ClientSession
            mock_client_context = AsyncMock()
            mock_read_stream = MagicMock()
            mock_write_stream = MagicMock()
            mock_client_context.__aenter__ = AsyncMock(return_value=(mock_read_stream, mock_write_stream))
            mock_client_context.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.initialize = AsyncMock()

            with patch('koderz.cortex.client.stdio_client', return_value=mock_client_context):
                with patch('koderz.cortex.client.ClientSession', return_value=mock_session):
                    async with client as persistent_client:
                        assert persistent_client is client
                        assert client._persistent is True
                        assert client._session is mock_session

            # After exit, should be cleaned up
            assert client._persistent is False
            assert client._session is None

        asyncio.run(run_test())

    def test_call_tool_uses_persistent_session(self):
        """Test that _call_tool uses persistent session when available."""
        client = CortexClient("/fake/path/index.js")

        async def run_test():
            # Mock for context manager
            mock_client_context = AsyncMock()
            mock_read_stream = MagicMock()
            mock_write_stream = MagicMock()
            mock_client_context.__aenter__ = AsyncMock(return_value=(mock_read_stream, mock_write_stream))
            mock_client_context.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value={"result": "test"})

            with patch('koderz.cortex.client.stdio_client', return_value=mock_client_context):
                with patch('koderz.cortex.client.ClientSession', return_value=mock_session):
                    async with client:
                        # Call tool multiple times
                        await client._call_tool("remember", {"title": "test1"})
                        await client._call_tool("remember", {"title": "test2"})
                        await client._call_tool("remember", {"title": "test3"})

                        # Persistent session should be reused
                        assert mock_session.call_tool.call_count == 3

                        # stdio_client should only be called once (for context manager entry)
                        assert mock_client_context.__aenter__.call_count == 1

        asyncio.run(run_test())

    def test_call_tool_ephemeral_mode(self):
        """Test that _call_tool creates new connections when not persistent."""
        client = CortexClient("/fake/path/index.js")

        async def run_test():
            call_count = 0

            # Mock that tracks connection creation
            def mock_stdio_client(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                mock_ctx = AsyncMock()
                mock_read = MagicMock()
                mock_write = MagicMock()
                mock_ctx.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
                mock_ctx.__aexit__ = AsyncMock(return_value=None)
                return mock_ctx

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value={"result": "test"})

            with patch('koderz.cortex.client.stdio_client', side_effect=mock_stdio_client):
                with patch('koderz.cortex.client.ClientSession', return_value=mock_session):
                    # Call tool multiple times without context manager
                    await client._call_tool("remember", {"title": "test1"})
                    await client._call_tool("remember", {"title": "test2"})
                    await client._call_tool("remember", {"title": "test3"})

                    # Each call should create a new connection
                    assert call_count == 3

        asyncio.run(run_test())

    def test_remember_uses_call_tool(self):
        """Test that remember method uses _call_tool internally."""
        client = CortexClient("/fake/path/index.js")

        async def test():
            with patch.object(client, '_call_tool', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = {"result": "ok"}
                await client.remember("title", "content", tags=["tag1"])

                mock_call.assert_called_once()
                call_args = mock_call.call_args
                assert call_args[0][0] == "remember"
                assert call_args[0][1]["title"] == "title"
                assert call_args[0][1]["content"] == "content"
                assert call_args[0][1]["tags"] == ["tag1"]

        asyncio.run(test())

    def test_start_session_uses_call_tool(self):
        """Test that start_session method uses _call_tool internally."""
        client = CortexClient("/fake/path/index.js")

        async def test():
            with patch.object(client, '_call_tool', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = {"result": "ok"}
                await client.start_session(context="test context")

                mock_call.assert_called_once_with("start_session", {"context": "test context"})

        asyncio.run(test())

    def test_end_session_uses_call_tool(self):
        """Test that end_session method uses _call_tool internally."""
        client = CortexClient("/fake/path/index.js")

        async def test():
            with patch.object(client, '_call_tool', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = {"result": "ok"}
                await client.end_session()

                mock_call.assert_called_once_with("end_session", {})

        asyncio.run(test())

    def test_export_memories_uses_call_tool(self):
        """Test that export_memories method uses _call_tool internally."""
        client = CortexClient("/fake/path/index.js")

        async def test():
            # Mock result with proper structure
            mock_result = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Exported 0 memories:\n\n[]"
            mock_result.content = [mock_content]

            with patch.object(client, '_call_tool', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = mock_result
                await client.export_memories(tags=["test"])

                mock_call.assert_called_once()
                call_args = mock_call.call_args
                assert call_args[0][0] == "export_memories"
                assert call_args[0][1]["tags"] == ["test"]

        asyncio.run(test())


class TestCortexClientBackwardsCompatibility:
    """Tests to ensure backwards compatibility with ephemeral mode."""

    def test_can_use_without_context_manager(self):
        """Test that client works without context manager (backwards compatible)."""
        client = CortexClient("/fake/path/index.js")

        # Should work without entering context manager
        async def test():
            mock_ctx = AsyncMock()
            mock_read = MagicMock()
            mock_write = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
            mock_ctx.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value={"result": "ok"})

            with patch('koderz.cortex.client.stdio_client', return_value=mock_ctx):
                with patch('koderz.cortex.client.ClientSession', return_value=mock_session):
                    result = await client.remember("title", "content")

            assert result == {"result": "ok"}

        asyncio.run(test())

    def test_server_params_unchanged(self):
        """Test that server parameters are set correctly."""
        client = CortexClient("/path/to/index.js", db_path="/path/to/db.sqlite")

        assert client.server_params.command == "node"
        assert "/path/to/index.js" in client.server_params.args
        assert "--db" in client.server_params.args
        assert "/path/to/db.sqlite" in client.server_params.args
