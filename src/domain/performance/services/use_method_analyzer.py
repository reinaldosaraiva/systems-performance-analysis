"""USE Method analyzer domain service."""

from typing import Dict, List, Any

from ..entities.performance_insight import PerformanceInsight
from ..entities.system_metrics import SystemMetrics
from ..value_objects.severity import Severity
from ..value_objects.threshold import Threshold


class USEMethodAnalyzer:
    """Domain Service: Implements Brendan Gregg's USE Method."""

    # USE Method thresholds based on best practices
    THRESHOLDS = {
        "cpu": Threshold(warning=70, critical=90),
        "memory": Threshold(warning=80, critical=95),
        "disk": Threshold(warning=60, critical=85),
        "network": Threshold(warning=70, critical=90),
    }

    def analyze(self, metrics: SystemMetrics) -> List[PerformanceInsight]:
        """Analyze system metrics using USE Method."""
        insights = []

        # CPU Analysis (Utilization, Saturation, Errors)
        insights.extend(self._analyze_cpu(metrics))

        # Memory Analysis
        insights.extend(self._analyze_memory(metrics))

        # Disk Analysis
        insights.extend(self._analyze_disk(metrics))

        # Network Analysis
        insights.extend(self._analyze_network(metrics))

        return insights

    def _analyze_cpu(self, metrics: SystemMetrics) -> List[PerformanceInsight]:
        """Analyze CPU metrics."""
        insights = []

        # CPU Utilization
        cpu_util = metrics.cpu_utilization.value
        if cpu_util >= self.THRESHOLDS["cpu"].critical:
            insights.append(
                PerformanceInsight(
                    title="Critical CPU Utilization",
                    description=f"CPU utilization is at {cpu_util}%, indicating severe performance bottleneck",
                    component="cpu",
                    severity=Severity.CRITICAL,
                    metrics=["cpu_utilization"],
                    recommendations=[
                        "Identify and optimize CPU-intensive processes",
                        "Consider scaling horizontally or vertically",
                        "Check for runaway processes or infinite loops",
                    ],
                )
            )
        elif cpu_util >= self.THRESHOLDS["cpu"].warning:
            insights.append(
                PerformanceInsight(
                    title="High CPU Utilization",
                    description=f"CPU utilization is at {cpu_util}%, approaching capacity limits",
                    component="cpu",
                    severity=Severity.HIGH,
                    metrics=["cpu_utilization"],
                    recommendations=[
                        "Monitor CPU trends closely",
                        "Investigate periodic CPU spikes",
                        "Plan capacity upgrades if trend continues",
                    ],
                )
            )

        return insights

    def _analyze_memory(self, metrics: SystemMetrics) -> List[PerformanceInsight]:
        """Analyze memory metrics."""
        insights = []

        # Memory Utilization
        mem_util = metrics.memory_utilization.value
        if mem_util >= self.THRESHOLDS["memory"].critical:
            insights.append(
                PerformanceInsight(
                    title="Critical Memory Utilization",
                    description=f"Memory utilization is at {mem_util}%, system may start swapping",
                    component="memory",
                    severity=Severity.CRITICAL,
                    metrics=["memory_utilization"],
                    recommendations=[
                        "Free up memory by terminating unnecessary processes",
                        "Add more RAM to the system",
                        "Optimize application memory usage",
                    ],
                )
            )
        elif mem_util >= self.THRESHOLDS["memory"].warning:
            insights.append(
                PerformanceInsight(
                    title="High Memory Utilization",
                    description=f"Memory utilization is at {mem_util}%, approaching critical levels",
                    component="memory",
                    severity=Severity.HIGH,
                    metrics=["memory_utilization"],
                    recommendations=[
                        "Monitor memory usage trends",
                        "Identify memory leaks in applications",
                        "Consider memory optimization",
                    ],
                )
            )

        return insights

    def _analyze_disk(self, metrics: SystemMetrics) -> List[PerformanceInsight]:
        """Analyze disk metrics."""
        insights = []

        for device, utilization in metrics.disk_utilization.items():
            if utilization.value >= self.THRESHOLDS["disk"].critical:
                insights.append(
                    PerformanceInsight(
                        title=f"Critical Disk Utilization on {device}",
                        description=f"Disk {device} utilization is at {utilization.value}%",
                        component="disk",
                        severity=Severity.CRITICAL,
                        metrics=[f"disk_utilization_{device}"],
                        recommendations=[
                            f"Clean up disk space on {device}",
                            "Archive old files to external storage",
                            "Consider disk expansion",
                        ],
                    )
                )

        return insights

    def _analyze_network(self, metrics: SystemMetrics) -> List[PerformanceInsight]:
        """Analyze network metrics."""
        insights = []

        for interface, utilization in metrics.network_utilization.items():
            if utilization.value >= self.THRESHOLDS["network"].critical:
                insights.append(
                    PerformanceInsight(
                        title=f"Critical Network Utilization on {interface}",
                        description=f"Network interface {interface} utilization is at {utilization.value}%",
                        component="network",
                        severity=Severity.CRITICAL,
                        metrics=[f"network_utilization_{interface}"],
                        recommendations=[
                            "Optimize network traffic patterns",
                            "Consider network bandwidth upgrade",
                            "Implement traffic shaping or QoS",
                        ],
                    )
                )

        return insights
