"""Use cases for getting performance insights."""

from datetime import datetime
from typing import List, Optional

from src.domain.performance.entities.performance_insight import PerformanceInsight
from src.domain.performance.repositories.insights_repository import InsightsRepository
from src.domain.performance.value_objects.severity import Severity


class GetAllInsightsUseCase:
    """Use case for getting all insights with optional filtering."""

    def __init__(self, repository: InsightsRepository):
        """
        Initialize use case with repository.

        Args:
            repository: Insights repository
        """
        self.repository = repository

    async def execute(
        self,
        limit: Optional[int] = None,
        severity: Optional[str] = None,
        component: Optional[str] = None,
    ) -> List[PerformanceInsight]:
        """
        Get all insights with optional filtering.

        Args:
            limit: Maximum number of insights to return
            severity: Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
            component: Filter by component (cpu, memory, disk, network)

        Returns:
            List of performance insights

        Raises:
            ValueError: If severity is invalid
        """
        # Apply filters based on parameters
        if severity and component:
            # Apply both filters
            severity_enum = self._parse_severity(severity)
            all_insights = await self.repository.get_by_severity(severity_enum)
            insights = [
                i for i in all_insights
                if component.lower() in i.component.lower()
            ]
            if limit:
                insights = insights[:limit]
        elif severity:
            # Filter by severity only
            severity_enum = self._parse_severity(severity)
            insights = await self.repository.get_by_severity(severity_enum, limit)
        elif component:
            # Filter by component only
            insights = await self.repository.get_by_component(component, limit)
        else:
            # No filters
            insights = await self.repository.get_all(limit)

        return insights

    @staticmethod
    def _parse_severity(severity_str: str) -> Severity:
        """
        Parse severity string to enum.

        Args:
            severity_str: Severity string

        Returns:
            Severity enum

        Raises:
            ValueError: If severity is invalid
        """
        try:
            return Severity[severity_str.upper()]
        except KeyError:
            valid_values = [s.value for s in Severity]
            raise ValueError(
                f"Invalid severity '{severity_str}'. Must be one of: {', '.join(valid_values)}"
            )


class GetLatestInsightUseCase:
    """Use case for getting the most recent insight."""

    def __init__(self, repository: InsightsRepository):
        """
        Initialize use case with repository.

        Args:
            repository: Insights repository
        """
        self.repository = repository

    async def execute(self) -> Optional[PerformanceInsight]:
        """
        Get the most recent insight.

        Returns:
            Latest performance insight or None if no insights available
        """
        insights = await self.repository.get_all(limit=1)
        return insights[0] if insights else None


class GetInsightsBySeverityUseCase:
    """Use case for getting insights filtered by severity."""

    def __init__(self, repository: InsightsRepository):
        """
        Initialize use case with repository.

        Args:
            repository: Insights repository
        """
        self.repository = repository

    async def execute(self, severity: str) -> List[PerformanceInsight]:
        """
        Get insights filtered by severity.

        Args:
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)

        Returns:
            List of insights with specified severity

        Raises:
            ValueError: If severity is invalid
        """
        try:
            severity_enum = Severity[severity.upper()]
        except KeyError:
            valid_values = [s.value for s in Severity]
            raise ValueError(
                f"Invalid severity '{severity}'. Must be one of: {', '.join(valid_values)}"
            )

        return await self.repository.get_by_severity(severity_enum)


class GetInsightsByComponentUseCase:
    """Use case for getting insights filtered by component."""

    def __init__(self, repository: InsightsRepository):
        """
        Initialize use case with repository.

        Args:
            repository: Insights repository
        """
        self.repository = repository

    async def execute(self, component: str) -> List[PerformanceInsight]:
        """
        Get insights for a specific component.

        Args:
            component: Component name (cpu, memory, disk, network)

        Returns:
            List of insights for the component
        """
        return await self.repository.get_by_component(component)


class GetInsightsSummaryUseCase:
    """Use case for getting insights summary statistics."""

    def __init__(self, repository: InsightsRepository):
        """
        Initialize use case with repository.

        Args:
            repository: Insights repository
        """
        self.repository = repository

    async def execute(self) -> dict:
        """
        Get summary statistics of insights.

        Returns:
            Dictionary with:
                - total_insights: Total number of insights
                - by_severity: Counts by severity level
                - by_component: Counts by component
        """
        # Get counts by severity from repository
        severity_counts = await self.repository.count_by_severity()

        # Get all insights to count by component
        all_insights = await self.repository.get_all()
        component_counts = {}
        for insight in all_insights:
            comp = insight.component
            component_counts[comp] = component_counts.get(comp, 0) + 1

        return {
            "total_insights": len(all_insights),
            "by_severity": {sev.value: count for sev, count in severity_counts.items()},
            "by_component": component_counts,
        }


class GetCriticalInsightsUseCase:
    """Use case for getting only critical insights."""

    def __init__(self, repository: InsightsRepository):
        """
        Initialize use case with repository.

        Args:
            repository: Insights repository
        """
        self.repository = repository

    async def execute(self) -> List[PerformanceInsight]:
        """
        Get only critical severity insights.

        Returns:
            List of critical insights
        """
        return await self.repository.get_critical_insights()
