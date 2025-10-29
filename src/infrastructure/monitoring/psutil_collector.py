"""Psutil-based system metrics collector."""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

import psutil

from domain.performance.entities.system_metrics import SystemMetrics
from domain.performance.value_objects.metric_value import MetricValue
from application.ports.output.metrics_collector import MetricsCollectorPort

logger = logging.getLogger(__name__)


class PsutilCollector(MetricsCollectorPort):
    """Infrastructure adapter for collecting system metrics using psutil."""

    def __init__(self, cache_duration: float = 1.0):
        """
        Initialize the metrics collector.

        Args:
            cache_duration: Cache duration in seconds to avoid excessive calls
        """
        self.cache_duration = cache_duration
        self._cache: Dict[str, Any] = {}
        self._last_update: float = 0

    async def collect(self) -> SystemMetrics:
        """
        Collect all system metrics.

        Returns:
            SystemMetrics entity with current system state
        """
        current_time = time.time()

        # Use cache if still valid
        if current_time - self._last_update < self.cache_duration and self._cache:
            logger.debug("Using cached metrics")
            return self._build_metrics_from_cache()

        logger.info("Collecting system metrics")

        try:
            # Collect all metrics
            cpu_metrics = self._collect_cpu_metrics()
            memory_metrics = self._collect_memory_metrics()
            disk_metrics = self._collect_disk_metrics()
            network_metrics = self._collect_network_metrics()

            # Build SystemMetrics entity
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                hostname="localhost",
                cpu_utilization=MetricValue(cpu_metrics["utilization"], "%"),
                memory_utilization=MetricValue(memory_metrics["utilization"], "%"),
                cpu_load_average=cpu_metrics.get("load_average"),
                memory_available=MetricValue(memory_metrics["available"], "GB")
                if memory_metrics.get("available")
                else None,
                disk_utilization=disk_metrics["utilization"],
                network_utilization=network_metrics["utilization"],
            )

            # Update cache
            self._cache = {
                "cpu": cpu_metrics,
                "memory": memory_metrics,
                "disk": disk_metrics,
                "network": network_metrics,
                "hostname": metrics.hostname,
            }
            self._last_update = current_time

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            raise

    def _build_metrics_from_cache(self) -> SystemMetrics:
        """Build SystemMetrics from cached data."""
        cache = self._cache
        return SystemMetrics(
            timestamp=datetime.now(),
            hostname=cache["hostname"],
            cpu_utilization=MetricValue(cache["cpu"]["utilization"], "%"),
            memory_utilization=MetricValue(cache["memory"]["utilization"], "%"),
            cpu_load_average=cache["cpu"].get("load_average"),
            memory_available=MetricValue(cache["memory"]["available"], "GB")
            if cache["memory"].get("available")
            else None,
            disk_utilization=cache["disk"]["utilization"],
            network_utilization=cache["network"]["utilization"],
        )

    def _collect_cpu_metrics(self) -> Dict[str, Any]:
        """Collect CPU-related metrics."""
        try:
            # CPU utilization
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Load average (Linux/Unix only)
            load_avg = None
            try:
                load_avg = {
                    "1min": psutil.getloadavg()[0],
                    "5min": psutil.getloadavg()[1],
                    "15min": psutil.getloadavg()[2],
                }
            except (AttributeError, OSError):
                # Windows doesn't have load average
                pass

            # CPU context switches
            context_switches = None
            try:
                context_switches = psutil.cpu_stats().ctx_switches
            except (AttributeError, OSError):
                pass

            return {
                "utilization": round(cpu_percent, 1),
                "load_average": load_avg,
                "context_switches": context_switches,
                "cores": psutil.cpu_count(),
                "cores_logical": psutil.cpu_count(logical=True),
            }

        except Exception as e:
            logger.error(f"Failed to collect CPU metrics: {e}")
            return {"utilization": 0, "error": str(e)}

    def _collect_memory_metrics(self) -> Dict[str, Any]:
        """Collect memory-related metrics."""
        try:
            virtual = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                "utilization": round(virtual.percent, 1),
                "available": round(virtual.available / (1024**3), 2),  # GB
                "total": round(virtual.total / (1024**3), 2),  # GB
                "used": round(virtual.used / (1024**3), 2),  # GB
                "swap_utilization": round(swap.percent, 1),
                "swap_total": round(swap.total / (1024**3), 2),  # GB
            }

        except Exception as e:
            logger.error(f"Failed to collect memory metrics: {e}")
            return {"utilization": 0, "error": str(e)}

    def _collect_disk_metrics(self) -> Dict[str, Any]:
        """Collect disk-related metrics."""
        try:
            disk_utilization = {}
            disk_io = None

            # Disk utilization per partition
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_utilization[partition.device] = MetricValue(
                        round((usage.used / usage.total) * 100, 1), "%"
                    )
                except (PermissionError, OSError):
                    # Skip inaccessible partitions
                    continue

            # Disk I/O stats
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    disk_io = {
                        "read_bytes": disk_io.read_bytes,
                        "write_bytes": disk_io.write_bytes,
                        "read_count": disk_io.read_count,
                        "write_count": disk_io.write_count,
                    }
            except (AttributeError, OSError):
                pass

            return {
                "utilization": disk_utilization,
                "io_stats": disk_io,
            }

        except Exception as e:
            logger.error(f"Failed to collect disk metrics: {e}")
            return {"utilization": {}, "error": str(e)}

    def _collect_network_metrics(self) -> Dict[str, Any]:
        """Collect network-related metrics."""
        try:
            network_utilization = {}
            network_io = None

            # Network I/O stats
            try:
                net_io = psutil.net_io_counters(pernic=True)
                network_errors = 0
                network_drops = 0

                for interface, stats in net_io.items():
                    # Calculate utilization (simplified - would need baseline for real utilization)
                    network_utilization[interface] = MetricValue(0, "%")  # Placeholder

                    network_errors += stats.errin + stats.errout
                    network_drops += stats.dropin + stats.dropout

                network_io = {
                    "errors": network_errors,
                    "drops": network_drops,
                }

            except (AttributeError, OSError):
                pass

            return {
                "utilization": network_utilization,
                "io_stats": network_io,
            }

        except Exception as e:
            logger.error(f"Failed to collect network metrics: {e}")
            return {"utilization": {}, "error": str(e)}
