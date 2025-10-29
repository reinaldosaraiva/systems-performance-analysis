"""LLM client port interface."""

from abc import ABC, abstractmethod
from typing import List

from ...domain.performance.entities.system_metrics import SystemMetrics
from ...domain.performance.entities.performance_insight import PerformanceInsight


class LLMClientPort(ABC):
    """Port interface for LLM client interactions."""

    @abstractmethod
    async def generate_insights(
        self, metrics: SystemMetrics
    ) -> List[PerformanceInsight]:
        """Generate performance insights using LLM."""
        pass

    @abstractmethod
    async def analyze_bottleneck(self, insight: PerformanceInsight) -> str:
        """Analyze a specific bottleneck using LLM."""
        pass
