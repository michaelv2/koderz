"""Model registry for all supported models."""

from typing import TypedDict


class ModelInfo(TypedDict):
    """Model metadata."""
    provider: str
    tier: str
    cost_per_1m_input: float
    cost_per_1m_output: float


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
    },
    "claude-haiku-4-5": {
        "provider": "anthropic",
        "tier": "small_frontier",
        "cost_per_1m_input": 0.80,
        "cost_per_1m_output": 4.00,
    },

    # Full frontier models
    "claude-opus-4-5": {
        "provider": "anthropic",
        "tier": "frontier",
        "cost_per_1m_input": 15.0,
        "cost_per_1m_output": 75.0,
    },
    "claude-sonnet-4-5": {
        "provider": "anthropic",
        "tier": "frontier",
        "cost_per_1m_input": 3.0,
        "cost_per_1m_output": 15.0,
    },
    "claude-opus-4": {
        "provider": "anthropic",
        "tier": "frontier",
        "cost_per_1m_input": 15.0,
        "cost_per_1m_output": 75.0,
    },
    "claude-sonnet-4": {
        "provider": "anthropic",
        "tier": "frontier",
        "cost_per_1m_input": 3.0,
        "cost_per_1m_output": 15.0,
    },
    "gpt-4o": {
        "provider": "openai",
        "tier": "frontier",
        "cost_per_1m_input": 2.50,
        "cost_per_1m_output": 10.00,
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
