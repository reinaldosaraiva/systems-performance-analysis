"""Threshold value object for performance metrics."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Threshold:
    """Threshold configuration for a performance metric."""

    warning: Optional[float] = None
    critical: Optional[float] = None
    unit: str = "%"

    def get_severity(self, value: float) -> str:
        """Determine severity based on value."""
        if self.critical and value >= self.critical:
            return "CRITICAL"
        if self.warning and value >= self.warning:
            return "WARNING"
        return "OK"
