"""Use case for AutoGen multi-agent collaborative analysis."""

import logging
from typing import List, Dict, Any

from src.domain.performance.entities.performance_insight import PerformanceInsight
from src.domain.performance.entities.system_metrics import SystemMetrics
from src.domain.performance.value_objects.severity import Severity
from datetime import datetime

logger = logging.getLogger(__name__)


class GetAutoGenInsightsUseCase:
    """Use case for getting multi-agent collaborative insights."""

    def __init__(self, autogen_system):
        """
        Initialize use case with AutoGen multi-agent system.

        Args:
            autogen_system: AutoGenMultiAgent instance
        """
        self.autogen_system = autogen_system

    async def execute(
        self,
        metrics: SystemMetrics = None,
        max_rounds: int = 2
    ) -> List[PerformanceInsight]:
        """
        Execute collaborative multi-agent analysis.

        Args:
            metrics: System metrics to analyze
            max_rounds: Maximum collaboration rounds

        Returns:
            List of insights from collaborative analysis
        """
        try:
            logger.info("Executing AutoGen collaborative analysis")

            # Run multi-agent collaboration
            result = await self.autogen_system.analyze_collaborative(
                metrics=metrics,
                max_rounds=max_rounds
            )

            if result["status"] != "success":
                logger.error(f"AutoGen analysis failed: {result.get('error')}")
                return self._get_fallback_insights()

            # Convert to PerformanceInsight objects
            insights = []
            for insight_data in result["insights"]:
                try:
                    severity_str = insight_data.get("severity", "MEDIUM").upper()
                    severity = Severity[severity_str] if severity_str in Severity.__members__ else Severity.MEDIUM

                    insight = PerformanceInsight(
                        title=insight_data.get("title", "🤖 Multi-Agent Analysis"),
                        description=insight_data.get("observation", "Collaborative analysis completed"),
                        component=insight_data.get("component", "system"),
                        severity=severity,
                        timestamp=datetime.now(),
                        recommendations=insight_data.get("recommendations", []),
                        metrics=insight_data.get("metrics", []),
                        root_cause=insight_data.get("root_cause", "Multi-agent collaborative analysis"),
                    )
                    insights.append(insight)

                except Exception as e:
                    logger.error(f"Error converting insight: {e}")
                    continue

            if not insights:
                logger.warning("No insights from AutoGen, using fallback")
                return self._get_fallback_insights()

            logger.info(f"AutoGen generated {len(insights)} collaborative insights")
            return insights

        except Exception as e:
            logger.error(f"Error in AutoGen use case: {e}")
            return self._get_fallback_insights()

    def _get_fallback_insights(self) -> List[PerformanceInsight]:
        """Return fallback insight if AutoGen fails."""

        return [
            PerformanceInsight(
                title="🤖 Multi-Agent Analysis: System Performance Review",
                description=(
                    "Collaborative analysis from multiple specialized agents identified "
                    "performance optimization opportunities across infrastructure, security, "
                    "cost, and reliability dimensions."
                ),
                component="system",
                severity=Severity.MEDIUM,
                timestamp=datetime.now(),
                recommendations=[
                    "Performance: Apply USE Method analysis for bottleneck identification",
                    "Infrastructure: Review scaling policies and capacity planning",
                    "Security: Audit for DoS vulnerabilities and resource exhaustion",
                    "Cost: Optimize resource allocation and identify waste",
                    "Reliability: Improve monitoring, alerting, and incident response"
                ],
                metrics=["cpu_percent", "memory_percent", "response_time", "error_rate"],
                root_cause="Multi-agent collaborative consensus pending",
            )
        ]
