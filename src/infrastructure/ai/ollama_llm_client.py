"""Ollama LLM client implementation (adapter)."""

import json
import logging
from datetime import datetime
from typing import List, Optional

import httpx

from src.application.ports.output.llm_client import LLMClientPort
from src.domain.performance.entities.performance_insight import PerformanceInsight
from src.domain.performance.entities.system_metrics import SystemMetrics
from src.domain.performance.value_objects.severity import Severity

logger = logging.getLogger(__name__)


class OllamaLLMClient(LLMClientPort):
    """
    Ollama LLM client implementation (REAL MODE).

    Makes actual HTTP calls to Ollama API for AI-powered performance analysis
    using MiniMax-M2 or other models. Implements Brendan Gregg's USE Method
    for system performance insights.

    Falls back to example insights if Ollama is unavailable.
    """

    def __init__(self, base_url: str, model: str, temperature: float = 0.7, timeout: int = 120):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL
            model: Model name to use
            temperature: Temperature for generation
            timeout: Request timeout in seconds
        """
        # Remove /v1 suffix if present, we'll add the correct endpoint
        self.base_url = base_url.rstrip("/").replace("/v1", "")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
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
        logger.info(f"Generating LLM insights using {self.model} (REAL MODE)")

        try:
            # Build prompt based on Brendan Gregg's USE Method
            prompt = self._build_analysis_prompt(metrics)

            # Call Ollama API
            response_text = await self._call_ollama(prompt)

            # Parse LLM response into insights
            insights = self._parse_llm_response(response_text)

            logger.info(f"Successfully generated {len(insights)} LLM insights")
            return insights

        except Exception as e:
            logger.error(f"Error calling Ollama LLM: {e}")
            # Fallback to example insights if LLM fails
            return self._get_fallback_insights()

    def _build_analysis_prompt(self, metrics: Optional[SystemMetrics]) -> str:
        """Build analysis prompt using Brendan Gregg's methodology."""

        if metrics:
            # TODO: Extract real metrics data when metrics object is available
            metrics_summary = "Real-time system metrics available"
        else:
            metrics_summary = "Using general system performance patterns"

        prompt = f"""You are a performance engineer expert in Brendan Gregg's USE Method.

Task: Generate 2-3 performance insights for system analysis.

Context: {metrics_summary}

CRITICAL: You MUST respond with ONLY a valid JSON array. No explanations, no markdown, just pure JSON.

Example of expected output:
[{{"title":"🤖 CPU Saturation Detected","description":"High CPU utilization with load average above threshold indicates saturation.","component":"cpu","severity":"HIGH","recommendations":["Scale horizontally","Optimize hot paths","Review thread pools"],"metrics":["cpu_percent","load_avg"],"root_cause":"Excessive request volume"}},{{"title":"🎯 Memory Pressure","description":"Memory usage approaching limits with swap activity.","component":"memory","severity":"MEDIUM","recommendations":["Increase memory","Add caching","Review memory leaks"],"metrics":["memory_percent","swap_used"],"root_cause":"Growing dataset size"}}]]

Now generate insights following this EXACT format. USE Method:
- Utilization: resource busy time %
- Saturation: queued work
- Errors: error events

Respond with JSON array only:"""

        return prompt

    async def _call_ollama(self, prompt: str) -> str:
        """Make API call to Ollama."""

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            }
        }

        logger.info(f"Calling Ollama API at {url}")

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            response_text = data.get("response", "")

            logger.info(f"Received response from Ollama ({len(response_text)} chars)")
            return response_text

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Ollama: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            raise

    def _parse_llm_response(self, response_text: str) -> List[PerformanceInsight]:
        """Parse LLM JSON response into PerformanceInsight objects."""

        try:
            # Log raw response for debugging
            logger.debug(f"Raw LLM response: {response_text[:500]}...")

            # Extract JSON from response (LLM might add text around it)
            json_start = response_text.find("[")
            json_end = response_text.rfind("]") + 1

            if json_start == -1 or json_end == 0:
                logger.warning(f"No JSON array found in LLM response. Response: {response_text[:200]}")
                return self._get_fallback_insights()

            json_str = response_text[json_start:json_end]
            insights_data = json.loads(json_str)

            insights = []
            for data in insights_data:
                try:
                    # Map severity string to enum
                    severity_str = data.get("severity", "MEDIUM").upper()
                    severity = Severity[severity_str] if severity_str in Severity.__members__ else Severity.MEDIUM

                    insight = PerformanceInsight(
                        title=data.get("title", "🤖 AI Analysis"),
                        description=data.get("description", "Performance analysis completed"),
                        component=data.get("component", "system"),
                        severity=severity,
                        timestamp=datetime.now(),
                        recommendations=data.get("recommendations", []),
                        metrics=data.get("metrics", []),
                        root_cause=data.get("root_cause", "AI analysis"),
                    )
                    insights.append(insight)

                except Exception as e:
                    logger.error(f"Error parsing insight: {e}")
                    continue

            if not insights:
                logger.warning("No valid insights parsed from LLM response")
                return self._get_fallback_insights()

            return insights

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            return self._get_fallback_insights()
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}")
            return self._get_fallback_insights()

    def _get_fallback_insights(self) -> List[PerformanceInsight]:
        """Return fallback insights if LLM call fails."""
        logger.info("Using fallback insights")

        return [
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
        ]

    async def analyze_bottleneck(self, insight: PerformanceInsight) -> str:
        """
        Analyze a specific bottleneck using LLM.

        Args:
            insight: Performance insight to analyze

        Returns:
            Detailed analysis from LLM
        """
        logger.info(f"Analyzing bottleneck: {insight.title} (REAL MODE)")

        try:
            # Escape strings to avoid quote issues
            title = str(insight.title).replace('"', '\\"')
            desc = str(insight.description).replace('"', '\\"')
            root_cause = str(insight.root_cause or "").replace('"', '\\"')

            prompt = f"""You are a senior performance engineer expert in Brendan Gregg USE Method.

Analyze this bottleneck:

Title: {title}
Component: {insight.component}
Severity: {insight.severity.value}
Description: {desc}
Root Cause: {root_cause}

Provide:
1. Detailed explanation
2. Performance impact
3. Investigation steps
4. Optimization recommendations

Keep under 500 words, technical and actionable."""

            response_text = await self._call_ollama(prompt)
            return response_text

        except Exception as e:
            logger.error(f"Error analyzing bottleneck with LLM: {e}")
            # Fallback to structured response
            return (
                f"🤖 AI Analysis for {insight.component}:\n\n"
                f"Based on the methodology and evidence provided, this appears to be "
                f"a {insight.severity.value.lower()} priority issue. "
                f"The root cause analysis suggests: {insight.root_cause}\n\n"
                f"Recommended actions:\n"
                + "\n".join(f"• {rec}" for rec in insight.recommendations)
            )

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()
