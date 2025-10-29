"""Bottleneck detection domain service."""

from typing import List, Tuple

from domain.performance.entities.performance_insight import PerformanceInsight
from domain.performance.entities.system_metrics import SystemMetrics
from domain.performance.value_objects.severity import Severity


class BottleneckDetector:
    """Domain Service: Detects system performance bottlenecks."""

    def detect_bottlenecks(self, metrics: SystemMetrics) -> List[PerformanceInsight]:
        """
        Detect performance bottlenecks in system metrics.

        Args:
            metrics: Current system metrics

        Returns:
            List of bottleneck insights
        """
        bottlenecks = []

        # Check for CPU bottlenecks
        cpu_bottleneck = self._detect_cpu_bottleneck(metrics)
        if cpu_bottleneck:
            bottlenecks.append(cpu_bottleneck)

        # Check for memory bottlenecks
        memory_bottleneck = self._detect_memory_bottleneck(metrics)
        if memory_bottleneck:
            bottlenecks.append(memory_bottleneck)

        # Check for I/O bottlenecks
        io_bottleneck = self._detect_io_bottleneck(metrics)
        if io_bottleneck:
            bottlenecks.append(io_bottleneck)

        return bottlenecks

    def _detect_cpu_bottleneck(self, metrics: SystemMetrics) -> PerformanceInsight:
        """Detect CPU-related bottlenecks."""
        cpu_util = metrics.cpu_utilization.value

        if cpu_util > 95:
            return PerformanceInsight(
                title="Severe CPU Bottleneck",
                description=f"CPU utilization at {cpu_util}% indicates severe performance bottleneck",
                component="cpu",
                severity=Severity.CRITICAL,
                metrics=["cpu_utilization"],
                recommendations=[
                    "Immediate: Identify and terminate CPU-intensive processes",
                    "Short-term: Scale horizontally or vertically",
                    "Long-term: Optimize algorithms and code efficiency",
                ],
            )
        elif cpu_util > 85:
            return PerformanceInsight(
                title="CPU Bottleneck Detected",
                description=f"CPU utilization at {cpu_util}% indicates performance bottleneck",
                component="cpu",
                severity=Severity.HIGH,
                metrics=["cpu_utilization"],
                recommendations=[
                    "Monitor CPU trends closely",
                    "Investigate periodic CPU spikes",
                    "Consider capacity planning",
                ],
            )

        return None

    def _detect_memory_bottleneck(self, metrics: SystemMetrics) -> PerformanceInsight:
        """Detect memory-related bottlenecks."""
        mem_util = metrics.memory_utilization.value

        if mem_util > 95:
            return PerformanceInsight(
                title="Critical Memory Bottleneck",
                description=f"Memory utilization at {mem_util}% - system may start swapping",
                component="memory",
                severity=Severity.CRITICAL,
                metrics=["memory_utilization"],
                recommendations=[
                    "Immediate: Free up memory by clearing caches/restarting services",
                    "Short-term: Add more RAM or use memory optimization",
                    "Long-term: Optimize application memory usage",
                ],
            )
        elif mem_util > 85:
            return PerformanceInsight(
                title="Memory Pressure Detected",
                description=f"Memory utilization at {mem_util}% - approaching critical levels",
                component="memory",
                severity=Severity.HIGH,
                metrics=["memory_utilization"],
                recommendations=[
                    "Monitor memory usage patterns",
                    "Check for memory leaks",
                    "Plan memory upgrades",
                ],
            )

        return None

    def _detect_io_bottleneck(self, metrics: SystemMetrics) -> PerformanceInsight:
        """Detect I/O-related bottlenecks."""
        # Check disk utilization
        for device, utilization in metrics.disk_utilization.items():
            if utilization.value > 90:
                return PerformanceInsight(
                    title=f"Disk I/O Bottleneck on {device}",
                    description=f"Disk {device} utilization at {utilization.value}%",
                    component="disk",
                    severity=Severity.CRITICAL,
                    metrics=[f"disk_utilization_{device}"],
                    recommendations=[
                        "Clean up disk space immediately",
                        "Move data to less utilized storage",
                        "Consider SSD upgrade or storage expansion",
                    ],
                )

        # Check for network issues
        if metrics.network_errors and metrics.network_errors.value > 100:
            return PerformanceInsight(
                title="Network Error Rate High",
                description=f"Network errors: {metrics.network_errors.value}",
                component="network",
                severity=Severity.HIGH,
                metrics=["network_errors"],
                recommendations=[
                    "Check network hardware and cables",
                    "Investigate application network handling",
                    "Monitor network stability",
                ],
            )

        return None

    def get_bottleneck_priority(
        self, bottlenecks: List[PerformanceInsight]
    ) -> List[PerformanceInsight]:
        """
        Sort bottlenecks by priority (critical first, then by impact).

        Args:
            bottlenecks: List of bottleneck insights

        Returns:
            Sorted list by priority
        """
        # Sort by severity (CRITICAL first) and then by component priority
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
        }
        component_priority = {"cpu": 0, "memory": 1, "disk": 2, "network": 3}

        return sorted(
            bottlenecks,
            key=lambda b: (
                severity_order.get(b.severity, 4),
                component_priority.get(b.component, 99),
            ),
        )
