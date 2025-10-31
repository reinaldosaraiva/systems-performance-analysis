"""Insights repository interface (port)."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..entities.performance_insight import PerformanceInsight
from ..value_objects.severity import Severity


class InsightsRepository(ABC):
    """Repository interface for performance insights."""

    @abstractmethod
    async def get_all(self, limit: Optional[int] = None) -> List[PerformanceInsight]:
        """
        Get all insights, optionally limited.

        Args:
            limit: Maximum number of insights to return

        Returns:
            List of performance insights ordered by timestamp (newest first)
        """
        pass

    @abstractmethod
    async def get_by_severity(
        self, severity: Severity, limit: Optional[int] = None
    ) -> List[PerformanceInsight]:
        """
        Get insights filtered by severity.

        Args:
            severity: Severity level to filter by
            limit: Maximum number of insights to return

        Returns:
            List of insights with specified severity
        """
        pass

    @abstractmethod
    async def get_by_component(
        self, component: str, limit: Optional[int] = None
    ) -> List[PerformanceInsight]:
        """
        Get insights for a specific component.

        Args:
            component: Component name (CPU, Memory, Disk, Network)
            limit: Maximum number of insights to return

        Returns:
            List of insights for the specified component
        """
        pass

    @abstractmethod
    async def get_critical_insights(self) -> List[PerformanceInsight]:
        """
        Get only critical insights.

        Returns:
            List of critical severity insights
        """
        pass

    @abstractmethod
    async def get_by_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> List[PerformanceInsight]:
        """
        Get insights within a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of insights within the specified time range
        """
        pass

    @abstractmethod
    async def count_by_severity(self) -> dict[Severity, int]:
        """
        Count insights grouped by severity.

        Returns:
            Dictionary mapping severity levels to counts
        """
        pass

    @abstractmethod
    async def save(self, insight: PerformanceInsight) -> None:
        """
        Save a performance insight.

        Args:
            insight: Performance insight to save
        """
        pass

    @abstractmethod
    async def save_many(self, insights: List[PerformanceInsight]) -> None:
        """
        Save multiple performance insights.

        Args:
            insights: List of insights to save
        """
        pass
