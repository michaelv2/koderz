"""Model factory for creating appropriate clients."""

from typing import Optional, Union
from .local import OllamaClient
from .frontier import FrontierClient
from .openai_client import OpenAIClient
from .registry import get_provider


class ModelFactory:
    """Factory for creating model clients based on model name."""

    def __init__(self,
                 ollama_host: str = "http://localhost:11434",
                 anthropic_api_key: Optional[str] = None,
                 openai_api_key: Optional[str] = None,
                 timeout: int = 300,
                 max_retries: int = 3,
                 num_ctx: int = 5120,
                 seed: Optional[int] = None,
                 temperature: float = 0.1):
        """Initialize model factory.

        Args:
            ollama_host: Ollama server host URL
            anthropic_api_key: Anthropic API key
            openai_api_key: OpenAI API key
            timeout: Request timeout in seconds for Ollama (default: 300)
            max_retries: Maximum retry attempts for Ollama (default: 3)
            num_ctx: Context window size for Ollama models in tokens (default: 5120)
                    Tuned based on real checkpoint guidance data (max 902 tokens)
            seed: Random seed for Ollama reproducibility (default: None)
            temperature: Sampling temperature for Ollama (default: 0.1)
        """
        self.ollama_host = ollama_host
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_key = openai_api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.num_ctx = num_ctx
        self.seed = seed
        self.temperature = temperature

        # Client cache to reuse instances
        self._ollama_client: Optional[OllamaClient] = None
        self._anthropic_client: Optional[FrontierClient] = None
        self._openai_client: Optional[OpenAIClient] = None

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
                self._ollama_client = OllamaClient(
                    host=self.ollama_host,
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                    num_ctx=self.num_ctx,
                    seed=self.seed,
                    temperature=self.temperature
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

        else:
            raise ValueError(f"Unknown provider '{provider}' for model: {model_name}")
