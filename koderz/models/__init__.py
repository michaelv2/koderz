"""Model client interfaces."""

from .local import OllamaClient
from .frontier import FrontierClient

__all__ = ["OllamaClient", "FrontierClient"]
