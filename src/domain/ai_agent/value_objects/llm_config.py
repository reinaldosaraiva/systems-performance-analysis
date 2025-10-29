"""LLM configuration value object."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class LLMConfig:
    """Configuration for LLM interactions."""

    model_name: str
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    additional_params: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize additional params if not provided."""
        if self.additional_params is None:
            self.additional_params = {}

    def is_openai_compatible(self) -> bool:
        """Check if config is OpenAI compatible."""
        return self.provider.lower() in ["openai", "ollama", "localai"]

    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
