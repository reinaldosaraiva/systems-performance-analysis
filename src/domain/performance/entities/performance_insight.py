"""PerformanceInsight entity for analysis results."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from ..value_objects.severity import Severity


@dataclass
class PerformanceInsight:
    """Entity representing a performance analysis insight."""

    title: str
    description: str
    component: str
    severity: Severity
    timestamp: datetime = field(default_factory=datetime.now)
    recommendations: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    root_cause: Optional[str] = None

    def is_critical(self) -> bool:
        """Check if insight is critical."""
        return self.severity == Severity.CRITICAL

    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation."""
        self.recommendations.append(recommendation)

    def __str__(self) -> str:
        """String representation."""
        return f"[{self.severity.value}] {self.component}: {self.title}"
