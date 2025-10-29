"""AnalysisSession aggregate for performance analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from ..entities.performance_insight import PerformanceInsight
from ..entities.system_metrics import SystemMetrics
from ..value_objects.severity import Severity


@dataclass
class AnalysisSession:
    """Aggregate root for performance analysis session."""

    session_id: str
    hostname: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    # Aggregated entities
    metrics_history: List[SystemMetrics] = field(default_factory=list)
    insights: List[PerformanceInsight] = field(default_factory=list)

    def add_metrics(self, metrics: SystemMetrics) -> None:
        """Add metrics to the session."""
        self.metrics_history.append(metrics)

    def add_insight(self, insight: PerformanceInsight) -> None:
        """Add insight to the session."""
        self.insights.append(insight)

    def get_critical_insights(self) -> List[PerformanceInsight]:
        """Get all critical insights."""
        return [insight for insight in self.insights if insight.is_critical()]

    def get_insights_by_component(self, component: str) -> List[PerformanceInsight]:
        """Get insights by component."""
        return [insight for insight in self.insights if insight.component == component]

    def complete_session(self) -> None:
        """Mark session as completed."""
        self.end_time = datetime.now()

    def duration(self) -> Optional[float]:
        """Get session duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def has_critical_issues(self) -> bool:
        """Check if session has critical issues."""
        return any(insight.is_critical() for insight in self.insights)
