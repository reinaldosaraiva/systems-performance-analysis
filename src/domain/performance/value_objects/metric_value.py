"""Metric value object with unit handling."""

from dataclasses import dataclass
from typing import Union


@dataclass
class MetricValue:
    """Value object representing a metric with its unit."""

    value: Union[int, float]
    unit: str

    def __str__(self) -> str:
        """String representation with unit."""
        return f"{self.value}{self.unit}"

    def to_percentage(self) -> str:
        """Convert to percentage format."""
        if self.unit == "%":
            return f"{self.value}%"
        return f"{self.value}%"
