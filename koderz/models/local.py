"""Ollama local model client."""

import requests
import logging
from typing import Optional

from ..utils.retry import retry_with_backoff, MaxRetriesExceeded

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with local models via Ollama API."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        timeout: int = 300,
        max_retries: int = 3,
        num_ctx: int = 5120,
        seed: Optional[int] = None,
        temperature: float = 0.1
    ):
        """Initialize Ollama client.

        Args:
            host: Ollama host URL (e.g., http://localhost:11434)
            timeout: Request timeout in seconds (default: 300)
            max_retries: Maximum number of retry attempts (default: 3)
            num_ctx: Context window size in tokens (default: 5120)
                    Based on real data analysis:
                    - Regular iterations: ~3,800 tokens
                    - Checkpoint iterations: ~4,700 tokens (max observed)
                    5K provides safe headroom without wasting memory
            seed: Random seed for reproducible output (default: None, Ollama default)
            temperature: Sampling temperature (default: 0.1)
        """
        self.host = host
        self.timeout = timeout
        self.max_retries = max_retries
        self.num_ctx = num_ctx
        self.seed = seed
        self.temperature = temperature

    def generate(self, prompt: str, model: str = "codellama:70b", system: Optional[str] = None) -> str:
        """Generate code using local model with automatic retry on timeout/overload.

        Args:
            prompt: The prompt to send to the model
            model: Model name to use
            system: System prompt to set context and behavior

        Returns:
            Generated text response

        Raises:
            MaxRetriesExceeded: When all retry attempts are exhausted
            requests.exceptions.HTTPError: For non-retryable HTTP errors
        """
        @retry_with_backoff(
            max_retries=self.max_retries,
            initial_delay=2.0,
            backoff_factor=2.0,
            max_delay=60.0
        )
        def _generate_with_retry():
            # Use chat endpoint for better system prompt support
            messages = []

            if system:
                messages.append({
                    "role": "system",
                    "content": system
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            try:
                response = requests.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "top_p": 0.9,
                            "num_predict": 4096,
                            "num_ctx": self.num_ctx,
                            **({"seed": self.seed} if self.seed is not None else {})
                        }
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()["message"]["content"]

            except requests.exceptions.HTTPError as e:
                # Log the error with model context
                if e.response is not None:
                    logger.error(
                        f"HTTP {e.response.status_code} error for model {model}: {e}"
                    )
                raise

            except requests.exceptions.ReadTimeout as e:
                logger.error(
                    f"Timeout ({self.timeout}s) waiting for model {model}: {e}"
                )
                raise

        return _generate_with_retry()

    def load_model(self, name: str) -> None:
        """Ensure model is loaded.

        Args:
            name: Model name to load
        """
        # Pulling the model ensures it's available
        response = requests.post(
            f"{self.host}/api/pull",
            json={"name": name, "stream": False},
            timeout=600  # 10 minute timeout for model downloads (not using self.timeout as downloads take longer)
        )
        response.raise_for_status()

    def list_models(self) -> list[dict]:
        """List available local models.

        Returns:
            List of model information dictionaries
        """
        response = requests.get(f"{self.host}/api/tags", timeout=30)
        response.raise_for_status()
        return response.json().get("models", [])

    def generate_spec(self, problem: str, model: str) -> dict:
        """Generate specification using local model.

        Args:
            problem: The problem description
            model: Model name to use

        Returns:
            Dictionary with 'spec' (str) and 'cost' (float, always 0.0 for local)
        """
        prompt = f"""Generate a MINIMAL implementation specification for the following coding problem:

{problem}

Your spec should include ONLY:
1. Problem analysis - What is the core challenge? What are the constraints?
2. Implementation specification - What should the function do? What should it return?

CRITICAL - Do NOT include:
- Implementation approach or algorithm suggestions
- Edge cases or common pitfalls
- Test criteria or examples
- Reference implementation, pseudocode, or code skeleton
- Specific data structures or algorithms to use

Keep the spec minimal. The goal is to clarify WHAT needs to be done, not HOW to do it.
This spec will guide a coding model that should solve the problem independently."""

        spec = self.generate(prompt, model=model)
        return {
            "spec": spec,
            "cost": 0.0
        }
