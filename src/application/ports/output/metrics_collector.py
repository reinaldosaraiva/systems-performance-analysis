"""Metrics collector port interface."""

from abc import ABC, abstractmethod

from domain.performance.entities.system_metrics import SystemMetrics


class MetricsCollectorPort(ABC):
    """Port interface for collecting system metrics."""

    @abstractmethod
    async def collect(self) -> SystemMetrics:
        """Collect current system metrics."""
        pass
