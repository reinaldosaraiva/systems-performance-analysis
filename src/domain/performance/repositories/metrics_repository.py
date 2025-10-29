"""Metrics repository interface (port)."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.system_metrics import SystemMetrics


class MetricsRepository(ABC):
    """Repository interface for system metrics."""

    @abstractmethod
    async def save(self, metrics: SystemMetrics) -> None:
        """Save system metrics."""
        pass

    @abstractmethod
    async def find_by_hostname(
        self, hostname: str, limit: int = 100
    ) -> List[SystemMetrics]:
        """Find metrics by hostname."""
        pass

    @abstractmethod
    async def find_latest(self, hostname: str) -> Optional[SystemMetrics]:
        """Find latest metrics for hostname."""
        pass

    @abstractmethod
    async def find_by_time_range(
        self, hostname: str, start_time, end_time
    ) -> List[SystemMetrics]:
        """Find metrics within time range."""
        pass
