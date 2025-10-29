"""LLM client port interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

try:
    from src.domain.performance.entities.system_metrics import SystemMetrics
    from src.domain.performance.entities.performance_insight import PerformanceInsight
except ImportError:
    from domain.performance.entities.system_metrics import SystemMetrics
    from domain.performance.entities.performance_insight import PerformanceInsight


class LLMClientPort(ABC):
    """Port interface for LLM client interactions."""

    @abstractmethod
    async def generate_insights(
        self, metrics: Optional[SystemMetrics]
    ) -> List[PerformanceInsight]:
        """Generate performance insights using LLM."""
        pass

    @abstractmethod
    async def analyze_bottleneck(self, insight: PerformanceInsight) -> str:
        """Analyze a specific bottleneck using LLM."""
        pass
