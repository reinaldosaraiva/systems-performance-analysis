"""Application settings using Pydantic BaseSettings."""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.

    All settings can be overridden via environment variables.
    Example: API_HOST=0.0.0.0 API_PORT=8080 python main.py
    """

    # ============================================================
    # API Configuration
    # ============================================================
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_title: str = "Brendan Gregg Agent API"
    api_version: str = "1.0.0"
    api_debug: bool = False

    # ============================================================
    # CORS Configuration
    # ============================================================
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # ============================================================
    # Prometheus Configuration
    # ============================================================
    prometheus_url: str = "http://localhost:9090"
    prometheus_timeout: int = 30  # seconds

    # ============================================================
    # Ollama LLM Configuration
    # ============================================================
    ollama_url: str = "http://localhost:11434/v1"
    ollama_model: str = "minimax-m2:cloud"
    ollama_temperature: float = 0.7
    ollama_max_tokens: int = 4096
    ollama_timeout: int = 120  # seconds

    # ============================================================
    # Reports and Storage
    # ============================================================
    reports_dir: Path = Path("reports")
    cache_dir: Path = Path(".cache")

    # ============================================================
    # Logging Configuration
    # ============================================================
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ============================================================
    # Analysis Configuration
    # ============================================================
    analysis_interval: int = 60  # seconds
    insights_retention_days: int = 30
    max_insights_per_request: int = 100

    # ============================================================
    # Dashboard Configuration
    # ============================================================
    dashboard_refresh_interval: int = 30  # seconds
    llm_dashboard_refresh_interval: int = 300  # seconds (5 min)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        """Initialize settings and create necessary directories."""
        super().__init__(**kwargs)

        # Create directories if they don't exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def prometheus_base_url(self) -> str:
        """Get Prometheus base URL without trailing slash."""
        return self.prometheus_url.rstrip("/")

    @property
    def ollama_base_url(self) -> str:
        """Get Ollama base URL without trailing slash."""
        return self.ollama_url.rstrip("/")

    def get_llm_config(self) -> dict:
        """Get LLM configuration as dictionary."""
        return {
            "base_url": self.ollama_base_url,
            "model": self.ollama_model,
            "temperature": self.ollama_temperature,
            "max_tokens": self.ollama_max_tokens,
            "timeout": self.ollama_timeout,
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings (singleton pattern).

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
