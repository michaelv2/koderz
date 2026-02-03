"""Model registry for all supported models."""

from typing import TypedDict


class ModelInfo(TypedDict, total=False):
    """Model metadata."""
    provider: str
    tier: str
    cost_per_1m_input: float
    cost_per_1m_output: float
    cost_per_1m_cache_read: float
    cost_per_1m_cache_creation: float


MODEL_REGISTRY: dict[str, ModelInfo] = {
    # Local models (Ollama)
    "codellama:70b": {
        "provider": "ollama",
        "tier": "local",
        "cost_per_1m_input": 0.0,
        "cost_per_1m_output": 0.0,
    },
    "llama3.3:70b": {
        "provider": "ollama",
        "tier": "local",
        "cost_per_1m_input": 0.0,
        "cost_per_1m_output": 0.0,
    },

    # Small frontier models
    "gpt-4o-mini": {
        "provider": "openai",
        "tier": "small_frontier",
        "cost_per_1m_input": 0.15,
        "cost_per_1m_output": 0.60,
        "cost_per_1m_cache_read": 0.075,  # 50% of input
    },
    "gpt-5-mini": {
        "provider": "openai",
        "tier": "small_frontier",
        "cost_per_1m_input": 0.25,
        "cost_per_1m_output": 2.00,
        "cost_per_1m_cache_read": 0.125,  # 50% of input
    },
    "gpt-5-nano": {
        "provider": "openai",
        "tier": "small_frontier",
        "cost_per_1m_input": 0.05,
        "cost_per_1m_output": 0.40,
        "cost_per_1m_cache_read": 0.025,  # 50% of input
    },
    "claude-haiku-4-5": {
        "provider": "anthropic",
        "tier": "small_frontier",
        "cost_per_1m_input": 0.80,
        "cost_per_1m_output": 4.00,
        "cost_per_1m_cache_read": 0.08,       # 10% of input
        "cost_per_1m_cache_creation": 1.00,    # 125% of input
    },

    # Full frontier models
    "claude-opus-4-5": {
        "provider": "anthropic",
        "tier": "frontier",
        "cost_per_1m_input": 15.0,
        "cost_per_1m_output": 75.0,
        "cost_per_1m_cache_read": 1.50,        # 10% of input
        "cost_per_1m_cache_creation": 18.75,    # 125% of input
    },
    "claude-sonnet-4-5": {
        "provider": "anthropic",
        "tier": "frontier",
        "cost_per_1m_input": 3.0,
        "cost_per_1m_output": 15.0,
        "cost_per_1m_cache_read": 0.30,        # 10% of input
        "cost_per_1m_cache_creation": 3.75,     # 125% of input
    },
    "claude-opus-4": {
        "provider": "anthropic",
        "tier": "frontier",
        "cost_per_1m_input": 15.0,
        "cost_per_1m_output": 75.0,
        "cost_per_1m_cache_read": 1.50,        # 10% of input
        "cost_per_1m_cache_creation": 18.75,    # 125% of input
    },
    "claude-sonnet-4": {
        "provider": "anthropic",
        "tier": "frontier",
        "cost_per_1m_input": 3.0,
        "cost_per_1m_output": 15.0,
        "cost_per_1m_cache_read": 0.30,        # 10% of input
        "cost_per_1m_cache_creation": 3.75,     # 125% of input
    },
    "gpt-4o": {
        "provider": "openai",
        "tier": "frontier",
        "cost_per_1m_input": 2.50,
        "cost_per_1m_output": 10.00,
        "cost_per_1m_cache_read": 1.25,  # 50% of input
    },
}


def get_model_info(model_name: str) -> ModelInfo:
    """Get model metadata from registry.

    Args:
        model_name: Name of the model

    Returns:
        Model metadata dictionary
    """
    # First check if model is explicitly in registry
    if model_name in MODEL_REGISTRY:
        return MODEL_REGISTRY[model_name]

    # Auto-detect Ollama models by colon in name (e.g., "qwen2.5-coder:32b")
    if ":" in model_name:
        return {
            "provider": "ollama",
            "tier": "local",
            "cost_per_1m_input": 0.0,
            "cost_per_1m_output": 0.0,
        }

    # Unknown model
    return {
        "provider": "unknown",
        "tier": "unknown",
        "cost_per_1m_input": 0.0,
        "cost_per_1m_output": 0.0,
    }


def calculate_cost(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
) -> float:
    """Calculate API cost from token usage using registry pricing.

    Args:
        model_name: Name of the model
        input_tokens: Number of input tokens (excludes cache tokens)
        output_tokens: Number of output tokens
        cache_read_tokens: Number of tokens read from cache
        cache_creation_tokens: Number of tokens written to cache

    Returns:
        Cost in USD
    """
    info = get_model_info(model_name)
    cost = (
        (input_tokens / 1_000_000) * info["cost_per_1m_input"]
        + (output_tokens / 1_000_000) * info["cost_per_1m_output"]
    )
    if cache_read_tokens:
        rate = info.get("cost_per_1m_cache_read", info["cost_per_1m_input"])
        cost += (cache_read_tokens / 1_000_000) * rate
    if cache_creation_tokens:
        rate = info.get("cost_per_1m_cache_creation", info["cost_per_1m_input"])
        cost += (cache_creation_tokens / 1_000_000) * rate
    return cost


def get_provider(model_name: str) -> str:
    """Get provider name (ollama, anthropic, openai).

    Args:
        model_name: Name of the model

    Returns:
        Provider name
    """
    return get_model_info(model_name)["provider"]


def get_tier(model_name: str) -> str:
    """Get tier (local, small_frontier, frontier).

    Args:
        model_name: Name of the model

    Returns:
        Tier name
    """
    return get_model_info(model_name)["tier"]
