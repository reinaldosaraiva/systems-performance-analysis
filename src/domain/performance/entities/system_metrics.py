"""SystemMetrics entity for performance analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

from ..value_objects.metric_value import MetricValue


@dataclass
class SystemMetrics:
    """Entity representing system performance metrics."""

    timestamp: datetime
    hostname: str
    cpu_utilization: MetricValue
    memory_utilization: MetricValue

    # Optional metrics with defaults
    cpu_load_average: Optional[Dict[str, float]] = None
    cpu_context_switches: Optional[MetricValue] = None
    memory_available: Optional[MetricValue] = None
    memory_swap_utilization: Optional[MetricValue] = None
    disk_utilization: Dict[str, MetricValue] = field(default_factory=dict)
    disk_io_utilization: Optional[MetricValue] = None
    disk_wait_time: Optional[MetricValue] = None
    network_utilization: Dict[str, MetricValue] = field(default_factory=dict)
    network_errors: Optional[MetricValue] = None
    network_drops: Optional[MetricValue] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    def get_metric_by_name(self, name: str) -> Optional[MetricValue]:
        """Get metric by name."""
        metric_map = {
            "cpu_utilization": self.cpu_utilization,
            "memory_utilization": self.memory_utilization,
        }
        return metric_map.get(name)

    def is_critical(self) -> bool:
        """Check if any metric is in critical state."""
        critical_thresholds = {
            "cpu_utilization": 90,
            "memory_utilization": 95,
        }

        for metric_name, threshold in critical_thresholds.items():
            metric = self.get_metric_by_name(metric_name)
            if metric and metric.value >= threshold:
                return True
        return False
