"""Use case: Analyze system performance."""

from typing import Dict, Any, Optional

from ...domain.performance.aggregates.analysis_session import AnalysisSession
from ...domain.performance.entities.system_metrics import SystemMetrics
from ...domain.performance.services.use_method_analyzer import USEMethodAnalyzer
from ...domain.performance.services.bottleneck_detector import BottleneckDetector
from ...application.ports.output.metrics_collector import MetricsCollectorPort
from ...application.ports.output.llm_client import LLMClientPort


class AnalyzeSystem:
    """Use Case: Analyze system performance using USE Method."""

    def __init__(
        self,
        metrics_collector: MetricsCollectorPort,
        use_analyzer: USEMethodAnalyzer,
        bottleneck_detector: BottleneckDetector,
        llm_client: Optional[LLMClientPort] = None,
    ):
        """
        Initialize the analyze system use case.

        Args:
            metrics_collector: Port for collecting system metrics
            use_analyzer: Domain service for USE Method analysis
            bottleneck_detector: Domain service for bottleneck detection
            llm_client: Optional port for LLM insights
        """
        self.metrics_collector = metrics_collector
        self.use_analyzer = use_analyzer
        self.bottleneck_detector = bottleneck_detector
        self.llm_client = llm_client

    async def execute(
        self, session_id: str, hostname: Optional[str] = None
    ) -> AnalysisSession:
        """
        Execute system analysis.

        Args:
            session_id: Unique identifier for analysis session
            hostname: Optional hostname to analyze (default: current system)

        Returns:
            AnalysisSession with results
        """
        # Create analysis session
        session = AnalysisSession(
            session_id=session_id, hostname=hostname or "localhost"
        )

        try:
            # Collect current metrics
            metrics = await self.metrics_collector.collect()
            session.add_metrics(metrics)

            # Perform USE Method analysis
            use_insights = self.use_analyzer.analyze(metrics)
            for insight in use_insights:
                session.add_insight(insight)

            # Detect bottlenecks
            bottlenecks = self.bottleneck_detector.detect_bottlenecks(metrics)
            for bottleneck in bottlenecks:
                session.add_insight(bottleneck)

            # Generate LLM insights if available
            if self.llm_client:
                try:
                    llm_insights = await self.llm_client.generate_insights(metrics)
                    for insight in llm_insights:
                        session.add_insight(insight)
                except Exception as e:
                    # Log error but don't fail the analysis
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to generate LLM insights: {e}")

            # Complete session
            session.complete_session()

            return session

        except Exception as e:
            session.complete_session()
            raise e

    async def execute_continuous(
        self, session_id: str, duration_minutes: int = 5, interval_seconds: int = 30
    ) -> AnalysisSession:
        """
        Execute continuous analysis over time.

        Args:
            session_id: Unique identifier for analysis session
            duration_minutes: How long to run the analysis
            interval_seconds: Interval between metric collections

        Returns:
            AnalysisSession with time-series results
        """
        import asyncio
        import time
        from datetime import datetime, timedelta

        session = AnalysisSession(session_id=session_id, hostname="localhost")

        end_time = datetime.now() + timedelta(minutes=duration_minutes)

        try:
            while datetime.now() < end_time:
                # Collect metrics
                metrics = await self.metrics_collector.collect()
                session.add_metrics(metrics)

                # Analyze current state
                use_insights = self.use_analyzer.analyze(metrics)
                bottlenecks = self.bottleneck_detector.detect_bottlenecks(metrics)

                # Add only new critical insights to avoid duplication
                all_insights = use_insights + bottlenecks
                for insight in all_insights:
                    if insight.is_critical() or insight.severity.value == "HIGH":
                        session.add_insight(insight)

                # Wait for next interval
                await asyncio.sleep(interval_seconds)

            session.complete_session()
            return session

        except Exception as e:
            session.complete_session()
            raise e
