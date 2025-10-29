"""
Brendan Gregg Agent with LLM Integration (AutoGen + Ollama MiniMax-M2)

Uses AutoGen (autogen-agentchat 0.7.5) with local MiniMax-M2 model via Ollama
to generate intelligent, contextual performance insights based on Brendan Gregg's
methodologies and the USE Method.

Architecture:
- AssistantAgent with Brendan Gregg persona system message
- OpenAIChatCompletionClient configured for Ollama's OpenAI-compatible API
- Async/await pattern for non-blocking LLM interactions
- Structured parsing of LLM responses into BrendanGreggInsight objects
- Fallback to rule-based analysis if LLM fails

Best Practices:
- Type hints for all functions
- Dataclasses for configuration
- Comprehensive error handling with specific exceptions
- Logging at appropriate levels
- Separation of concerns (collection, analysis, parsing)
- Async context managers for resource cleanup
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# AutoGen new API (0.7.5+)
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Import existing components
from brendan_gregg_persona import BrendanGreggInsight, PrometheusClient

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """
    Configuration for LLM via Ollama's OpenAI-compatible API.

    Attributes:
        base_url: Ollama API endpoint (OpenAI-compatible)
        model: Model name in Ollama (must match exactly with tag)
        temperature: Sampling temperature (0.0-1.0)
        timeout: Request timeout in seconds
        max_tokens: Maximum tokens to generate
    """
    base_url: str = "http://localhost:11434/v1"
    model: str = "minimax-m2:cloud"
    temperature: float = 0.7
    timeout: int = 300
    max_tokens: int = 4096


class BrendanLLMAgent:
    """
    Brendan Gregg Performance Analysis Agent powered by LLM.

    Uses MiniMax-M2 via Ollama and AutoGen (autogen-agentchat) to generate
    intelligent insights following Brendan Gregg's USE Method and performance
    analysis principles.

    The agent:
    1. Collects metrics from Prometheus
    2. Formats metrics for LLM consumption
    3. Sends analysis prompt to LLM with Brendan Gregg persona
    4. Parses LLM response into structured BrendanGreggInsight objects
    5. Falls back to rule-based analysis if LLM fails

    Example:
        >>> agent = BrendanLLMAgent(
        ...     prometheus_url="http://localhost:9090",
        ...     llm_config=LLMConfig(model="minimax-m2:cloud")
        ... )
        >>> insights = await agent.analyze_system()
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        llm_config: Optional[LLMConfig] = None
    ):
        """
        Initialize the LLM-powered Brendan Gregg agent.

        Args:
            prometheus_url: URL of Prometheus server
            llm_config: LLM configuration (defaults to Ollama MiniMax-M2)
        """
        self.prometheus = PrometheusClient(prometheus_url)
        self.llm_config = llm_config or LLMConfig()

        # Initialize AutoGen model client for Ollama
        self.model_client = OpenAIChatCompletionClient(
            model=self.llm_config.model,
            base_url=self.llm_config.base_url,
            api_key="ollama",  # Dummy key for Ollama (required by API but not used)
            model_info={
                "family": "minimax",  # Required in autogen-ext 0.7.5+
                "vision": False,
                "function_calling": False,  # MiniMax-M2 may not support this
                "json_output": False,
            },
            temperature=self.llm_config.temperature,
            timeout=self.llm_config.timeout,
            max_tokens=self.llm_config.max_tokens,
        )

        logger.info(
            f"Initialized BrendanLLMAgent with model={self.llm_config.model} "
            f"at {self.llm_config.base_url}"
        )

    def _create_brendan_agent(self) -> AssistantAgent:
        """
        Create AssistantAgent with Brendan Gregg persona.

        Returns:
            AssistantAgent configured with performance analysis persona
        """
        system_message = """You are Brendan Gregg, the world-renowned performance engineer and author of "Systems Performance" and "BPF Performance Tools".

Your expertise includes:
- The USE Method (Utilization, Saturation, Errors)
- Performance analysis and troubleshooting
- Linux systems internals
- BPF/eBPF tracing
- Flame graphs and visualization

When analyzing performance metrics, you:
1. Apply the USE Method systematically
2. Identify bottlenecks and saturation points
3. Provide actionable recommendations with specific commands
4. Explain root causes with technical depth
5. Reference specific tools (perf, bpftrace, sar, vmstat, etc.)
6. Use your signature analytical style

Output format for each insight:
- Severity: CRITICAL/HIGH/MEDIUM/LOW
- Component: cpu/memory/disk/network
- Title: Brief, clear problem statement
- Observation: What the data shows
- Evidence: Key metrics with values
- Root Cause: Technical explanation
- Immediate Action: Specific commands to run
- Investigation Steps: How to dig deeper
- Long-term Fix: Sustainable solution

Be direct, technical, and actionable. No fluff."""

        agent = AssistantAgent(
            name="BrendanGregg",
            model_client=self.model_client,
            system_message=system_message,
        )

        return agent

    async def analyze_metrics(
        self,
        metrics: Dict[str, float]
    ) -> List[BrendanGreggInsight]:
        """
        Analyze metrics using LLM to generate insights.

        Args:
            metrics: Dictionary of metric names to values

        Returns:
            List of BrendanGreggInsight objects generated by LLM

        Raises:
            Exception: If LLM analysis fails, returns fallback rule-based analysis
        """
        logger.info(f"Analyzing {len(metrics)} metrics with LLM")

        # Format metrics for LLM
        metrics_text = self._format_metrics_for_llm(metrics)

        # Create analysis prompt
        prompt = self._create_analysis_prompt(metrics_text)

        try:
            # Create agent and run analysis
            agent = self._create_brendan_agent()

            logger.info("Sending analysis request to LLM...")
            response = await agent.run(task=prompt)

            # Extract text from response
            llm_response = self._extract_response_text(response)

            logger.info(f"LLM response received ({len(llm_response)} chars)")
            logger.debug(f"LLM response: {llm_response[:500]}...")

            # Parse LLM response into insights
            insights = self._parse_llm_response(llm_response, metrics)

            logger.info(f"Generated {len(insights)} insights from LLM")
            return insights

        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}", exc_info=True)
            logger.warning("Falling back to rule-based analysis")
            # Fallback to rule-based analysis
            return self._fallback_analysis(metrics)

    def _format_metrics_for_llm(self, metrics: Dict[str, float]) -> str:
        """
        Format metrics in human-readable format for LLM.

        Args:
            metrics: Dictionary of metric names to values

        Returns:
            Formatted string with metrics
        """
        lines = ["PERFORMANCE METRICS:\n"]

        # Group metrics by component
        cpu_metrics = {}
        memory_metrics = {}
        disk_metrics = {}
        network_metrics = {}
        other_metrics = {}

        for key, value in metrics.items():
            key_lower = key.lower()
            if "cpu" in key_lower or "load" in key_lower:
                cpu_metrics[key] = value
            elif "memory" in key_lower or "mem" in key_lower or "swap" in key_lower:
                memory_metrics[key] = value
            elif "disk" in key_lower or "io" in key_lower:
                disk_metrics[key] = value
            elif "network" in key_lower or "net" in key_lower or "tx" in key_lower or "rx" in key_lower:
                network_metrics[key] = value
            else:
                other_metrics[key] = value

        # Format by category
        if cpu_metrics:
            lines.append("\n🔥 CPU Metrics:")
            for key, value in cpu_metrics.items():
                lines.append(f"  • {key}: {value:.2f}")

        if memory_metrics:
            lines.append("\n💾 Memory Metrics:")
            for key, value in memory_metrics.items():
                lines.append(f"  • {key}: {value:.2f}")

        if disk_metrics:
            lines.append("\n💿 Disk Metrics:")
            for key, value in disk_metrics.items():
                lines.append(f"  • {key}: {value:.2f}")

        if network_metrics:
            lines.append("\n🌐 Network Metrics:")
            for key, value in network_metrics.items():
                lines.append(f"  • {key}: {value:.2f}")

        if other_metrics:
            lines.append("\n📊 Other Metrics:")
            for key, value in other_metrics.items():
                lines.append(f"  • {key}: {value:.2f}")

        return "\n".join(lines)

    def _create_analysis_prompt(self, metrics_text: str) -> str:
        """
        Create analysis prompt for LLM.

        Args:
            metrics_text: Formatted metrics string

        Returns:
            Complete prompt for LLM analysis
        """
        return f"""Analyze these system performance metrics using the USE Method:

{metrics_text}

Generate insights for any issues detected. For each issue, provide:

1. **Severity level**:
   - CRITICAL if CPU >95%, Memory >90%, or any critical threshold exceeded
   - HIGH if CPU >80%, Memory >85%, or significant issues
   - MEDIUM if CPU >60%, Memory >75%, or moderate issues
   - LOW for minor observations

2. **Component**: cpu, memory, disk, or network

3. **Clear title**: Brief problem statement (e.g., "CPU Utilization at Critical Level")

4. **Observation**: What you observe in the data (2-3 sentences)

5. **Evidence**: Key metric values that support your observation

6. **Root cause**: Technical explanation of why this is happening

7. **Immediate action**: Specific commands to run RIGHT NOW (e.g., "Use `top` to identify CPU consumers")

8. **Investigation steps**: 3-5 specific steps to investigate deeper (e.g., "Run mpstat -P ALL 1")

9. **Long-term fix**: Sustainable solution (e.g., "Optimize hot code paths or scale horizontally")

Focus on the most impactful issues first. Be specific and actionable.
Use your signature Brendan Gregg analytical style.

Output format for each insight:

---
SEVERITY: [CRITICAL/HIGH/MEDIUM/LOW]
COMPONENT: [cpu/memory/disk/network]
TITLE: [Brief title]

OBSERVATION:
[What the data shows]

EVIDENCE:
[Key metrics with values]

ROOT CAUSE:
[Technical explanation]

IMMEDIATE ACTION:
[Specific commands]

INVESTIGATION STEPS:
1. [Step 1]
2. [Step 2]
3. [Step 3]

LONG-TERM FIX:
[Sustainable solution]
---

Analyze now and provide actionable insights."""

    def _extract_response_text(self, response: Any) -> str:
        """
        Extract text from AutoGen response.

        Args:
            response: Response object from agent.run()

        Returns:
            Extracted text string
        """
        # The response from agent.run() is typically a TaskResult object
        # that has messages attribute
        if hasattr(response, 'messages') and response.messages:
            # Get the last message content
            last_message = response.messages[-1]
            if hasattr(last_message, 'content'):
                return str(last_message.content)
            return str(last_message)

        # Fallback: convert to string
        return str(response)

    def _parse_llm_response(
        self,
        response: str,
        metrics: Dict[str, float]
    ) -> List[BrendanGreggInsight]:
        """
        Parse LLM response into structured insights.

        Uses regex patterns to extract structured information from the
        LLM's formatted response.

        Args:
            response: LLM text response
            metrics: Original metrics for evidence

        Returns:
            List of structured BrendanGreggInsight objects
        """
        insights = []

        # Split by insight separator (---)
        sections = re.split(r'\n---+\n', response)

        for idx, section in enumerate(sections):
            if not section.strip() or len(section.strip()) < 50:
                continue

            try:
                insight = self._parse_single_insight(section, metrics, idx)
                if insight:
                    insights.append(insight)
            except Exception as e:
                logger.warning(f"Failed to parse insight section {idx}: {e}")
                continue

        # If no structured insights found, create single insight from full response
        if not insights and response.strip():
            logger.warning("No structured insights found, creating single insight")
            insight = self._create_fallback_insight(response, metrics)
            insights.append(insight)

        return insights

    def _parse_single_insight(
        self,
        section: str,
        metrics: Dict[str, float],
        idx: int
    ) -> Optional[BrendanGreggInsight]:
        """
        Parse a single insight section.

        Args:
            section: Text section for one insight
            metrics: Original metrics
            idx: Index for unique ID

        Returns:
            BrendanGreggInsight object or None if parsing fails
        """
        # Extract fields using regex
        severity = self._extract_field(section, r'SEVERITY:\s*(\w+)')
        component = self._extract_field(section, r'COMPONENT:\s*(\w+)')
        title = self._extract_field(section, r'TITLE:\s*(.+?)(?:\n|$)')
        observation = self._extract_multiline_field(section, 'OBSERVATION')
        evidence_text = self._extract_multiline_field(section, 'EVIDENCE')
        root_cause = self._extract_multiline_field(section, 'ROOT CAUSE')
        immediate_action = self._extract_multiline_field(section, 'IMMEDIATE ACTION')
        investigation_text = self._extract_multiline_field(section, 'INVESTIGATION STEPS')
        long_term_fix = self._extract_multiline_field(section, 'LONG-TERM FIX')

        # Parse investigation steps as list
        investigation_steps = self._parse_list_items(investigation_text)

        # Extract evidence metrics mentioned in text
        evidence = self._extract_evidence_metrics(evidence_text, metrics)

        # Validate required fields
        if not severity:
            severity = self._detect_severity_from_text(section, metrics)
        if not component:
            component = self._detect_component(section)
        if not title:
            title = f"Performance Issue #{idx + 1}"

        # Create insight
        insight = BrendanGreggInsight(
            id=f"llm_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx}",
            timestamp=datetime.now(),
            methodology="use_method",
            component=component.lower(),
            issue_type="performance",
            severity=severity.upper(),
            title=title.strip(),
            observation=observation or section[:200],
            evidence=evidence,
            root_cause=root_cause or "See full analysis for details",
            immediate_action=immediate_action or "Review metrics and system state",
            investigation_steps=investigation_steps,
            long_term_fix=long_term_fix or "Implement optimization based on analysis",
            related_metrics=list(evidence.keys()) if evidence else list(metrics.keys())[:5],
            confidence=90.0,
            book_reference="Systems Performance, 2nd Edition"
        )

        return insight

    def _extract_field(self, text: str, pattern: str) -> str:
        """Extract single field using regex pattern."""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_multiline_field(self, text: str, field_name: str) -> str:
        """Extract multiline field content."""
        # Match field name followed by content until next field or end
        pattern = rf'{field_name}:\s*(.*?)(?=\n[A-Z\s]+:|---|\Z)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    def _parse_list_items(self, text: str) -> List[str]:
        """Parse numbered or bulleted list items."""
        if not text:
            return ["Review metrics", "Check logs", "Monitor trends"]

        # Match numbered items (1. 2. etc.) or bulleted items (- • etc.)
        items = re.findall(r'(?:^\s*[\d\-•]\s*\.?\s*(.+?)$)', text, re.MULTILINE)

        if items:
            return [item.strip() for item in items if item.strip()][:5]

        # Fallback: split by newlines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return lines[:5] if lines else ["Review metrics", "Check logs", "Monitor trends"]

    def _extract_evidence_metrics(
        self,
        evidence_text: str,
        metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """Extract metrics mentioned in evidence text."""
        evidence = {}

        if not evidence_text:
            return dict(list(metrics.items())[:5])  # Return first 5 metrics

        # Look for metrics mentioned in evidence
        for key, value in metrics.items():
            key_variants = [
                key,
                key.replace('_', ' '),
                key.replace('_', '-'),
            ]

            for variant in key_variants:
                if variant.lower() in evidence_text.lower():
                    evidence[key] = value
                    break

        # If no evidence found, return top metrics
        return evidence if evidence else dict(list(metrics.items())[:5])

    def _create_fallback_insight(
        self,
        response: str,
        metrics: Dict[str, float]
    ) -> BrendanGreggInsight:
        """Create single insight from unstructured response."""
        return BrendanGreggInsight(
            id=f"llm_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            methodology="use_method",
            component=self._detect_component(response),
            issue_type="performance",
            severity=self._detect_severity_from_text(response, metrics),
            title="Performance Analysis",
            observation=response[:300],
            evidence=dict(list(metrics.items())[:5]),
            root_cause=self._extract_section(response, "root cause"),
            immediate_action=self._extract_section(response, "immediate"),
            investigation_steps=self._extract_list(response, "investigation"),
            long_term_fix=self._extract_section(response, "long-term"),
            related_metrics=list(metrics.keys())[:5],
            confidence=80.0,
            book_reference="Systems Performance, 2nd Edition"
        )

    def _detect_component(self, text: str) -> str:
        """Detect component from text."""
        text_lower = text.lower()
        if "cpu" in text_lower or "processor" in text_lower:
            return "cpu"
        elif "memory" in text_lower or "ram" in text_lower:
            return "memory"
        elif "disk" in text_lower or "storage" in text_lower or "i/o" in text_lower:
            return "disk"
        elif "network" in text_lower or "net" in text_lower:
            return "network"
        return "system"

    def _detect_severity_from_text(
        self,
        text: str,
        metrics: Dict[str, float]
    ) -> str:
        """Detect severity from text or metrics."""
        text_upper = text.upper()

        # Check if severity mentioned in text
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if severity in text_upper:
                return severity

        # Fallback to metrics-based detection
        cpu_util = metrics.get("cpu_utilization", 0)
        memory_util = metrics.get("memory_utilization_percent", 0)

        if cpu_util > 95 or memory_util > 90:
            return "CRITICAL"
        elif cpu_util > 80 or memory_util > 85:
            return "HIGH"
        elif cpu_util > 60 or memory_util > 75:
            return "MEDIUM"
        return "LOW"

    def _extract_section(self, text: str, keyword: str) -> str:
        """Extract section from text by keyword."""
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        if keyword_lower in text_lower:
            idx = text_lower.index(keyword_lower)
            section = text[idx:idx+300]
            lines = section.split('\n')
            return lines[0].strip() if lines else ""

        return "See full analysis for details"

    def _extract_list(self, text: str, keyword: str) -> List[str]:
        """Extract list items from text by keyword."""
        lines = text.split('\n')
        in_section = False
        items = []

        for line in lines:
            if keyword.lower() in line.lower():
                in_section = True
                continue

            if in_section:
                if line.strip().startswith(('-', '•', '1.', '2.', '3.')):
                    items.append(line.strip())
                elif not line.strip() and items:
                    break

        return items[:5] if items else [
            "Review metrics",
            "Check system logs",
            "Monitor trends"
        ]

    def _fallback_analysis(
        self,
        metrics: Dict[str, float]
    ) -> List[BrendanGreggInsight]:
        """
        Fallback to rule-based analysis if LLM fails.

        Args:
            metrics: Dictionary of metric names to values

        Returns:
            List of insights from rule-based analysis
        """
        insights = []

        # CPU analysis
        cpu_util = metrics.get("cpu_utilization", 0)
        if cpu_util > 95:
            insights.append(BrendanGreggInsight(
                id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                methodology="use_method",
                component="cpu",
                issue_type="utilization",
                severity="CRITICAL",
                title="CPU Utilization Critical",
                observation=f"CPU utilization at {cpu_util:.1f}%",
                evidence={"cpu_utilization": cpu_util},
                root_cause="System is compute-bound",
                immediate_action="Use `top` to identify CPU consumers",
                investigation_steps=[
                    "Run mpstat -P ALL 1",
                    "Check with perf top",
                    "Review application logs"
                ],
                long_term_fix="Optimize hot code paths or scale horizontally",
                related_metrics=["cpu_utilization"],
                confidence=95.0,
            ))

        # Memory analysis
        memory_util = metrics.get("memory_utilization_percent", 0)
        if memory_util > 90:
            insights.append(BrendanGreggInsight(
                id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}_mem",
                timestamp=datetime.now(),
                methodology="use_method",
                component="memory",
                issue_type="utilization",
                severity="CRITICAL",
                title="Memory Utilization Critical",
                observation=f"Memory utilization at {memory_util:.1f}%",
                evidence={"memory_utilization_percent": memory_util},
                root_cause="System is memory-constrained",
                immediate_action="Use `free -h` and `vmstat` to check memory",
                investigation_steps=[
                    "Run vmstat 1",
                    "Check with top -o %MEM",
                    "Review memory-intensive processes"
                ],
                long_term_fix="Increase memory or optimize memory usage",
                related_metrics=["memory_utilization_percent"],
                confidence=95.0,
            ))

        return insights

    async def analyze_system(self) -> List[BrendanGreggInsight]:
        """
        Perform complete system analysis using USE Method + LLM.

        Collects metrics from Prometheus and analyzes them with LLM to generate
        intelligent, contextual insights.

        Returns:
            List of insights generated by LLM

        Example:
            >>> agent = BrendanLLMAgent()
            >>> insights = await agent.analyze_system()
            >>> for insight in insights:
            ...     print(f"{insight.severity}: {insight.title}")
        """
        logger.info("Starting LLM-powered USE Method analysis")

        # Collect metrics from Prometheus
        metrics = await self._collect_prometheus_metrics()

        if not metrics:
            logger.warning("No metrics collected from Prometheus")
            return []

        logger.info(f"Collected {len(metrics)} metrics")

        # Analyze with LLM
        insights = await self.analyze_metrics(metrics)

        return insights

    async def _collect_prometheus_metrics(self) -> Dict[str, float]:
        """
        Collect metrics from Prometheus.

        Uses get_metric_value() for simpler, more robust metric collection.

        Returns:
            Dictionary of metric names to values
        """
        metrics = {}

        # CPU metrics
        cpu_util = self.prometheus.get_metric_value(
            '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        )
        if cpu_util is not None:
            metrics["cpu_utilization"] = cpu_util

        load1 = self.prometheus.get_metric_value("node_load1")
        if load1 is not None:
            metrics["load_average_1m"] = load1

        cpu_count = self.prometheus.get_metric_value(
            'count(node_cpu_seconds_total{mode="idle"})'
        )
        if cpu_count is not None:
            metrics["cpu_count"] = cpu_count
            if "load_average_1m" in metrics:
                metrics["load_per_cpu"] = metrics["load_average_1m"] / cpu_count

        # Memory metrics
        mem_total = self.prometheus.get_metric_value("node_memory_MemTotal_bytes")
        if mem_total is not None:
            metrics["memory_total_bytes"] = mem_total

        mem_available = self.prometheus.get_metric_value("node_memory_MemAvailable_bytes")
        if mem_available is not None:
            metrics["memory_available_bytes"] = mem_available
            if "memory_total_bytes" in metrics:
                metrics["memory_utilization_percent"] = (
                    (metrics["memory_total_bytes"] - mem_available)
                    / metrics["memory_total_bytes"] * 100
                )

        # Disk metrics
        disk_util = self.prometheus.get_metric_value(
            "rate(node_disk_io_time_seconds_total[5m]) * 100"
        )
        if disk_util is not None:
            metrics["disk_utilization_percent"] = disk_util

        # Network errors
        net_rx_errs = self.prometheus.get_metric_value(
            "rate(node_network_receive_errs_total[5m])"
        )
        if net_rx_errs is not None:
            metrics["network_rx_errors_per_sec"] = net_rx_errs

        net_tx_errs = self.prometheus.get_metric_value(
            "rate(node_network_transmit_errs_total[5m])"
        )
        if net_tx_errs is not None:
            metrics["network_tx_errors_per_sec"] = net_tx_errs

        logger.info(f"Collected {len(metrics)} metrics from Prometheus")
        return metrics
