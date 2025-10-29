"""Ollama LLM client implementation (adapter)."""

import logging
from datetime import datetime
from typing import List, Optional

from src.application.ports.output.llm_client import LLMClientPort
from src.domain.performance.entities.performance_insight import PerformanceInsight
from src.domain.performance.entities.system_metrics import SystemMetrics
from src.domain.performance.value_objects.severity import Severity

logger = logging.getLogger(__name__)


class OllamaLLMClient(LLMClientPort):
    """
    Ollama LLM client implementation.

    This is a stub implementation that returns example insights.
    TODO: Integrate with real Ollama API using settings.ollama_url
    """

    def __init__(self, base_url: str, model: str, temperature: float = 0.7):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL
            model: Model name to use
            temperature: Temperature for generation
        """
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        logger.info(f"OllamaLLMClient initialized with model={model} at {base_url}")

    async def generate_insights(
        self, metrics: Optional[SystemMetrics]
    ) -> List[PerformanceInsight]:
        """
        Generate performance insights using LLM.

        Args:
            metrics: System metrics to analyze (optional)

        Returns:
            List of AI-generated insights
        """
        # TODO: Replace with real Ollama API call
        logger.info("Generating LLM insights (stub mode)")

        # For now, return example insights based on Brendan Gregg's methodology
        insights = [
            PerformanceInsight(
                title="🤖 AI Analysis: System Performance Overview",
                description=(
                    "Based on the USE method analysis, I've identified potential "
                    "bottlenecks in your system. The CPU shows signs of saturation "
                    "with elevated load averages, which may impact response times."
                ),
                component="system",
                severity=Severity.MEDIUM,
                timestamp=datetime.now(),
                recommendations=[
                    "Consider scaling horizontally to distribute load",
                    "Review application-level CPU-intensive operations",
                    "Monitor thread pool sizes and async operations",
                ],
                metrics=["load_average", "cpu_utilization", "context_switches"],
                root_cause="AI-powered analysis using Brendan Gregg's USE Method",
            ),
            PerformanceInsight(
                title="🎯 AI Recommendation: Optimize Resource Utilization",
                description=(
                    "Machine learning analysis suggests optimizing resource "
                    "utilization patterns. Current metrics indicate room for "
                    "improvement in memory and I/O efficiency."
                ),
                component="optimization",
                severity=Severity.LOW,
                timestamp=datetime.now(),
                recommendations=[
                    "Implement caching strategies for frequently accessed data",
                    "Review database query patterns and add indexes",
                    "Consider async I/O for network operations",
                ],
                metrics=["memory_usage", "io_wait", "cache_hit_ratio"],
                root_cause="AI pattern recognition on historical metrics",
            ),
        ]

        logger.info(f"Generated {len(insights)} LLM insights")
        return insights

    async def analyze_bottleneck(self, insight: PerformanceInsight) -> str:
        """
        Analyze a specific bottleneck using LLM.

        Args:
            insight: Performance insight to analyze

        Returns:
            Detailed analysis from LLM
        """
        # TODO: Replace with real Ollama API call
        logger.info(f"Analyzing bottleneck: {insight.title} (stub mode)")

        return (
            f"🤖 AI Analysis for {insight.component}:\n\n"
            f"Based on the methodology and evidence provided, this appears to be "
            f"a {insight.severity.value.lower()} priority issue. "
            f"The root cause analysis suggests: {insight.root_cause}\n\n"
            f"Recommended actions:\n"
            + "\n".join(f"• {rec}" for rec in insight.recommendations)
        )
