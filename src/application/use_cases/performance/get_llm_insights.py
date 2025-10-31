"""Use case for getting LLM-powered insights."""

import logging
from typing import List

try:
    from src.application.ports.output.llm_client import LLMClientPort
    from src.domain.performance.entities.performance_insight import PerformanceInsight
    from src.domain.performance.entities.system_metrics import SystemMetrics
except ImportError:
    from application.ports.output.llm_client import LLMClientPort
    from domain.performance.entities.performance_insight import PerformanceInsight
    from domain.performance.entities.system_metrics import SystemMetrics

logger = logging.getLogger(__name__)


class GetLLMInsightsUseCase:
    """Use case for getting AI-powered performance insights."""

    def __init__(self, llm_client: LLMClientPort):
        """
        Initialize use case with LLM client.

        Args:
            llm_client: LLM client for generating insights
        """
        self.llm_client = llm_client

    async def execute(self) -> List[PerformanceInsight]:
        """
        Get LLM-powered performance insights.

        Returns:
            List of AI-generated performance insights

        Raises:
            Exception: If LLM service is unavailable
        """
        try:
            # TODO: Get actual system metrics from repository
            # For now, pass None - the LLM client stub will generate example insights
            insights = await self.llm_client.generate_insights(None)

            logger.info(f"Generated {len(insights)} LLM insights")
            return insights

        except Exception as e:
            logger.error(f"Error generating LLM insights: {e}")
            raise


class AnalyzeBottleneckUseCase:
    """Use case for analyzing a specific bottleneck with AI."""

    def __init__(self, llm_client: LLMClientPort):
        """
        Initialize use case with LLM client.

        Args:
            llm_client: LLM client for analysis
        """
        self.llm_client = llm_client

    async def execute(self, insight: PerformanceInsight) -> str:
        """
        Analyze a specific bottleneck using AI.

        Args:
            insight: Performance insight to analyze

        Returns:
            Detailed AI analysis

        Raises:
            Exception: If LLM service is unavailable
        """
        try:
            analysis = await self.llm_client.analyze_bottleneck(insight)

            logger.info(f"Generated bottleneck analysis for: {insight.title}")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing bottleneck: {e}")
            raise
