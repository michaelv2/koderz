"""No-op Cortex stub for running without claude-cortex-core MCP server.

Provides the same interface as CortexClient but silently discards all
remember/recall operations. Benchmark results are still saved to JSON
by the CLI, so no data is lost.
"""


class StubCortexClient:
    """Drop-in replacement for CortexClient that does nothing."""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def remember(self, **kwargs):
        return {}

    async def recall(self, **kwargs):
        return []

    async def export_memories(self, **kwargs):
        return []

    async def start_session(self, **kwargs):
        return {}

    async def end_session(self, **kwargs):
        return {}

    async def consolidate(self, **kwargs):
        return {}

    async def get_stats(self, **kwargs):
        return {}
