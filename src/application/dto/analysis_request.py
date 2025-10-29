"""Analysis request DTO."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class AnalysisRequest:
    """Data Transfer Object for analysis requests."""

    session_id: str
    hostname: Optional[str] = None
    analysis_type: str = "single"  # "single" or "continuous"
    duration_minutes: int = 5
    interval_seconds: int = 30
    include_llm_insights: bool = False
    custom_thresholds: Optional[Dict[str, Dict[str, float]]] = None

    def is_continuous(self) -> bool:
        """Check if this is a continuous analysis request."""
        return self.analysis_type == "continuous"

    def validate(self) -> None:
        """Validate request parameters."""
        if not self.session_id:
            raise ValueError("Session ID is required")

        if self.duration_minutes <= 0:
            raise ValueError("Duration must be positive")

        if self.interval_seconds <= 0:
            raise ValueError("Interval must be positive")

        if self.analysis_type not in ["single", "continuous"]:
            raise ValueError("Analysis type must be 'single' or 'continuous'")
