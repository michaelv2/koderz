"""Model factory for creating appropriate clients."""

import os
from typing import Optional, Union
from .local import OllamaClient
from .frontier import FrontierClient
from .openai_client import OpenAIClient
from .registry import get_provider


def _think_setting() -> Optional[bool]:
    """Reasoning control for Ollama models, from KODERZ_LOCAL_THINK.

    "off"/"on" map to think=False/True; unset leaves the model default. Mirrors
    memoize's MEMOIZE_LOCAL_THINK. Reasoning models left on their default spend
    the num_predict budget thinking and return empty content, which scores as a
    failed iteration rather than as a truncation.
    """
    raw = os.environ.get("KODERZ_LOCAL_THINK")
    if raw is None:
        return None
    return raw.strip().lower() in ("on", "true", "1")


class ModelFactory:
    """Factory for creating model clients based on model name."""

    def __init__(self,
                 ollama_host: str = "http://llm-server:11434",
                 anthropic_api_key: Optional[str] = None,
                 openai_api_key: Optional[str] = None,
                 timeout: int = 300,
                 max_retries: int = 3,
                 num_ctx: int = 5120,
                 seed: Optional[int] = None,
                 temperature: float = 0.1,
                 think: Optional[bool] = None,
                 num_predict: Optional[int] = None):
        self.ollama_host = ollama_host
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_key = openai_api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.num_ctx = num_ctx
        self.seed = seed
        self.temperature = temperature
        self.think = think
        self.num_predict = num_predict

        # Client cache to reuse instances
        self._ollama_client: Optional[OllamaClient] = None
        self._anthropic_client: Optional[FrontierClient] = None
        self._openai_client: Optional[OpenAIClient] = None
        self._fireworks_client: Optional[OpenAIClient] = None
        self._together_client: Optional[OpenAIClient] = None
        self._llamacpp_client: Optional[OpenAIClient] = None

    def get_client(self, model_name: str) -> Union[OllamaClient, FrontierClient, OpenAIClient]:
        """Get appropriate client for the given model.

        Args:
            model_name: Name of the model to use

        Returns:
            Client instance for the model's provider

        Raises:
            ValueError: If provider is unknown or API key is missing
        """
        provider = get_provider(model_name)

        if provider == "ollama":
            if not self._ollama_client:
                think = self.think if self.think is not None else _think_setting()
                num_predict = self.num_predict if self.num_predict is not None else int(os.environ.get("KODERZ_NUM_PREDICT", "4096"))
                self._ollama_client = OllamaClient(
                    host=self.ollama_host,
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                    num_ctx=self.num_ctx,
                    seed=self.seed,
                    temperature=self.temperature,
                    num_predict=num_predict,
                    think=think,
                )
            return self._ollama_client

        elif provider == "anthropic":
            if not self._anthropic_client:
                if not self.anthropic_api_key:
                    raise ValueError("ANTHROPIC_API_KEY required for Anthropic models")
                self._anthropic_client = FrontierClient(self.anthropic_api_key)
            return self._anthropic_client

        elif provider == "openai":
            if not self._openai_client:
                if not self.openai_api_key:
                    raise ValueError("OPENAI_API_KEY required for OpenAI models")
                self._openai_client = OpenAIClient(self.openai_api_key)
            return self._openai_client

        elif provider == "fireworks":
            if not self._fireworks_client:
                api_key = os.environ.get("FIREWORKS_API_KEY")
                if not api_key:
                    raise ValueError("FIREWORKS_API_KEY required for Fireworks models")
                self._fireworks_client = OpenAIClient(
                    api_key=api_key,
                    base_url="https://api.fireworks.ai/inference/v1",
                )
            return self._fireworks_client

        elif provider == "together":
            if not self._together_client:
                api_key = os.environ.get("TOGETHER_API_KEY")
                if not api_key:
                    raise ValueError("TOGETHER_API_KEY required for Together models")
                self._together_client = OpenAIClient(
                    api_key=api_key,
                    base_url="https://api.together.xyz/v1",
                )
            return self._together_client

        elif provider == "llamacpp":
            if not self._llamacpp_client:
                llamacpp_url = os.environ.get("LLAMACPP_BASE_URL", "http://llm-server:8080/v1")
                self._llamacpp_client = OpenAIClient(
                    api_key="no-key-needed",
                    base_url=llamacpp_url,
                    max_completion_tokens=4096,
                )
            return self._llamacpp_client

        else:
            raise ValueError(f"Unknown provider '{provider}' for model: {model_name}")
