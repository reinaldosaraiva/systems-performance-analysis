"""Analysis response DTO."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from ...domain.performance.aggregates.analysis_session import AnalysisSession


@dataclass
class AnalysisResponse:
    """Data Transfer Object for analysis responses."""

    session_id: str
    hostname: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    insights_count: int
    critical_insights_count: int
    metrics_collected: int
    insights: List[dict] = field(default_factory=list)
    summary: str = ""

    @classmethod
    def from_session(cls, session: AnalysisSession) -> "AnalysisResponse":
        """Create response from analysis session."""
        insights_data = []
        for insight in session.insights:
            insights_data.append(
                {
                    "title": insight.title,
                    "description": insight.description,
                    "component": insight.component,
                    "severity": insight.severity.value,
                    "timestamp": insight.timestamp.isoformat(),
                    "recommendations": insight.recommendations,
                    "metrics": insight.metrics,
                    "root_cause": insight.root_cause,
                }
            )

        critical_count = len(session.get_critical_insights())

        summary = cls._generate_summary(session)

        return cls(
            session_id=session.session_id,
            hostname=session.hostname,
            start_time=session.start_time,
            end_time=session.end_time,
            duration_seconds=session.duration(),
            insights_count=len(session.insights),
            critical_insights_count=critical_count,
            metrics_collected=len(session.metrics_history),
            insights=insights_data,
            summary=summary,
        )

    @staticmethod
    def _generate_summary(session: AnalysisSession) -> str:
        """Generate analysis summary."""
        critical_count = len(session.get_critical_insights())
        total_insights = len(session.insights)

        if critical_count > 0:
            return f"CRITICAL: {critical_count} critical issues detected out of {total_insights} total insights. Immediate action required."
        elif total_insights > 0:
            return f"WARNING: {total_insights} performance issues detected. Monitor closely."
        else:
            return "OK: No performance issues detected. System operating normally."

    def has_critical_issues(self) -> bool:
        """Check if response contains critical issues."""
        return self.critical_insights_count > 0

    def get_severity_distribution(self) -> dict:
        """Get distribution of insights by severity."""
        distribution = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for insight in self.insights:
            severity = insight.get("severity", "LOW")
            if severity in distribution:
                distribution[severity] += 1

        return distribution
