"""Ollama local model client."""

import requests
from typing import Optional


class OllamaClient:
    """Client for interacting with local models via Ollama API."""

    def __init__(self, host: str = "http://localhost:11434"):
        """Initialize Ollama client.

        Args:
            host: Ollama host URL (e.g., http://localhost:11434)
        """
        self.host = host

    def generate(self, prompt: str, model: str = "codellama:70b") -> str:
        """Generate code using local model.

        Args:
            prompt: The prompt to send to the model
            model: Model name to use

        Returns:
            Generated text response
        """
        response = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()["response"]

    def load_model(self, name: str) -> None:
        """Ensure model is loaded.

        Args:
            name: Model name to load
        """
        # Pulling the model ensures it's available
        response = requests.post(
            f"{self.host}/api/pull",
            json={"name": name, "stream": False}
        )
        response.raise_for_status()

    def list_models(self) -> list[dict]:
        """List available local models.

        Returns:
            List of model information dictionaries
        """
        response = requests.get(f"{self.host}/api/tags")
        response.raise_for_status()
        return response.json().get("models", [])
