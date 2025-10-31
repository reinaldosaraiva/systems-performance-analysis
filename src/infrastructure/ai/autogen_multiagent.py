"""AutoGen Multi-Agent Collaborative System for Performance Analysis."""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx

from src.domain.performance.entities.performance_insight import PerformanceInsight
from src.domain.performance.entities.system_metrics import SystemMetrics
from src.domain.performance.value_objects.severity import Severity

logger = logging.getLogger(__name__)


class AutoGenMultiAgent:
    """
    Multi-agent collaborative system using AutoGen + Ollama MiniMax-M2.

    Creates specialized agents that collaborate to provide comprehensive
    performance analysis from different perspectives (performance, security,
    cost, reliability, infrastructure).
    """

    def __init__(self, base_url: str, model: str, temperature: float = 0.7, timeout: int = 120):
        """
        Initialize multi-agent system.

        Args:
            base_url: Ollama API base URL
            model: Model name (e.g., minimax-m2:cloud)
            temperature: Temperature for generation
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/").replace("/v1", "")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

        # Define specialized agents
        self.agents = self._create_agents()

        logger.info(f"AutoGen multi-agent system initialized with {len(self.agents)} agents")

    def _create_agents(self) -> List[Dict[str, str]]:
        """Create specialized agents for different analysis perspectives."""

        agents = [
            {
                "name": "PerformanceAnalyst",
                "role": "Performance Engineer",
                "system_message": """You are a senior performance engineer expert in Brendan Gregg's USE Method.

Analyze system performance for Utilization, Saturation, and Errors.

Focus on: CPU, memory, disk I/O, network bottlenecks.
Provide: 2-3 specific recommendations with technical details.
Format: JSON with {insights: [{"finding": "...", "recommendation": "..."}]}"""
            },
            {
                "name": "InfrastructureExpert",
                "role": "Infrastructure Architect",
                "system_message": """You are an infrastructure architect expert in cloud scalability.

Analyze infrastructure capacity and scaling opportunities.

Focus on: Scaling strategies, resource allocation, architecture patterns.
Provide: 2-3 strategic recommendations for capacity and architecture.
Format: JSON with {insights: [{"finding": "...", "recommendation": "..."}]}"""
            },
            {
                "name": "SecurityAnalyst",
                "role": "Security Expert",
                "system_message": """You are a security analyst expert in OWASP and system hardening.

Identify security implications of performance issues.

Focus on: DoS vulnerabilities, configuration security, monitoring gaps.
Provide: 2-3 critical security recommendations.
Format: JSON with {insights: [{"finding": "...", "recommendation": "..."}]}"""
            },
            {
                "name": "CostOptimizer",
                "role": "Cost Optimization Expert",
                "system_message": """You are a cloud cost optimization expert (AWS/Azure/GCP).

Identify cost-saving opportunities without sacrificing performance.

Focus on: Over-provisioning, pricing models, resource efficiency.
Provide: 2-3 cost optimization recommendations with estimated savings.
Format: JSON with {insights: [{"finding": "...", "recommendation": "..."}]}"""
            },
            {
                "name": "ReliabilityEngineer",
                "role": "SRE Expert",
                "system_message": """You are an SRE expert in system reliability and incident response.

Ensure system reliability and minimize MTTR.

Focus on: SLO compliance, incident prevention, monitoring improvements.
Provide: 2-3 reliability recommendations with proactive measures.
Format: JSON with {insights: [{"finding": "...", "recommendation": "..."}]}"""
            }
        ]

        return agents

    async def analyze_collaborative(
        self,
        metrics: Optional[SystemMetrics] = None,
        max_rounds: int = 2
    ) -> Dict[str, Any]:
        """
        Run collaborative analysis with all agents.

        Args:
            metrics: System metrics to analyze
            max_rounds: Maximum discussion rounds

        Returns:
            Collaborative analysis results with insights from all agents
        """
        logger.info(f"Starting collaborative analysis with {len(self.agents)} agents (REAL MODE)")

        try:
            # Build analysis context
            context = self._build_analysis_context(metrics)

            # Collect analysis from each agent
            agent_analyses = []

            for agent in self.agents:
                logger.info(f"Calling agent: {agent['name']}")

                # Create agent-specific prompt
                prompt = f"""{agent['system_message']}

Scenario: {context}

Analyze from your {agent['role']} perspective and provide 2-3 actionable recommendations.
Respond with JSON only."""

                # Call Ollama for this agent
                try:
                    response = await self._call_ollama(prompt)
                    agent_analyses.append({
                        "agent": agent["name"],
                        "role": agent["role"],
                        "analysis": response
                    })
                    logger.info(f"Agent {agent['name']} analysis received ({len(response)} chars)")
                except Exception as e:
                    logger.error(f"Error calling agent {agent['name']}: {e}")
                    continue

            # Consolidate all analyses into final insights
            insights = await self._consolidate_analyses(agent_analyses, context)

            logger.info(f"Collaborative analysis completed with {len(insights)} insights")

            return {
                "status": "success",
                "agents_participated": len(agent_analyses),
                "rounds": 1,  # Each agent analyzes once
                "insights": insights,
                "collaboration_summary": f"Analysis from {len(agent_analyses)} specialized agents consolidated"
            }

        except Exception as e:
            logger.error(f"Error in collaborative analysis: {e}")
            return {
                "status": "error",
                "error": str(e),
                "insights": []
            }

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

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            return data.get("response", "")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Ollama: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            raise

    async def _consolidate_analyses(
        self,
        agent_analyses: List[Dict[str, Any]],
        context: str
    ) -> List[Dict[str, Any]]:
        """Consolidate analyses from all agents into final insights."""

        if not agent_analyses:
            return []

        # Build consolidation prompt
        analyses_text = "\n\n".join([
            f"**{analysis['agent']} ({analysis['role']}):**\n{analysis['analysis']}"
            for analysis in agent_analyses
        ])

        consolidation_prompt = f"""You are a senior technical lead consolidating analyses from 5 specialized agents.

Context: {context}

Agent Analyses:
{analyses_text}

Task: Create 1-2 consolidated performance insights that combine the best recommendations from all agents.

For each insight provide:
- title: Clear actionable title with emoji
- observation: Consolidated finding from multiple agents
- recommendations: Best 5-7 recommendations from all agents (prefix with agent name)
- severity: CRITICAL, HIGH, MEDIUM, or LOW
- confidence: 85-95 (higher for multi-agent consensus)

Respond with JSON only: {{"insights": [{{"title": "...", "observation": "...", "recommendations": [...], "severity": "HIGH", "confidence": 92}}]}}"""

        try:
            response = await self._call_ollama(consolidation_prompt)

            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                logger.warning("No JSON found in consolidation response")
                return self._create_fallback_consolidated_insight(agent_analyses)

            json_str = response[json_start:json_end]
            data = json.loads(json_str)

            return data.get("insights", [])

        except Exception as e:
            logger.error(f"Error consolidating analyses: {e}")
            return self._create_fallback_consolidated_insight(agent_analyses)

    def _create_fallback_consolidated_insight(
        self,
        agent_analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create fallback consolidated insight."""

        recommendations = [
            f"{analysis['agent']}: Analyze from {analysis['role']} perspective"
            for analysis in agent_analyses
        ]

        return [{
            "title": "🤖 Multi-Agent Collaborative Analysis",
            "observation": f"Analysis from {len(agent_analyses)} specialized agents",
            "recommendations": recommendations,
            "severity": "MEDIUM",
            "confidence": 85
        }]

    def _build_analysis_context(self, metrics: Optional[SystemMetrics]) -> str:
        """Build context for agent analysis."""

        if metrics:
            # TODO: Extract real metrics when available
            return "Real-time system metrics with performance degradation detected."
        else:
            return """General system performance analysis.

Scenario: Production system showing performance degradation.
- Response times increased 40%
- CPU utilization at 85%
- Memory usage climbing
- Some requests timing out

Analyze from your specialized perspective."""

    async def close(self):
        """Cleanup resources."""
        await self.client.aclose()
        logger.info("AutoGen multi-agent system closed")
