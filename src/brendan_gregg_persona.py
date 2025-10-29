#!/usr/bin/env python3
"""
Brendan Gregg Persona for AutoGen Integration

This module implements an AI persona based on Brendan Gregg's methodologies,
analysis style, and expertise in systems performance. The persona analyzes
metrics from Prometheus and Grafana dashboards using the USE Method and other
performance analysis techniques.

Author: System Performance Analysis Team
Based on: Brendan Gregg's methodologies (Systems Performance book, USE Method)
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


class AnalysisMethodology(str, Enum):
    """Performance analysis methodologies from Brendan Gregg."""

    USE_METHOD = "use_method"  # Utilization, Saturation, Errors
    TSA_METHOD = "tsa_method"  # Thread State Analysis
    WORKLOAD_CHARACTERIZATION = "workload_characterization"
    DRILL_DOWN_ANALYSIS = "drill_down_analysis"
    LATENCY_ANALYSIS = "latency_analysis"
    OFF_CPU_ANALYSIS = "off_cpu_analysis"
    RESOURCE_ANALYSIS = "resource_analysis"


class PerformanceIssueType(str, Enum):
    """Types of performance issues identified by the persona."""

    BOTTLENECK = "bottleneck"
    SATURATION = "saturation"
    ERROR = "error"
    LATENCY_SPIKE = "latency_spike"
    RESOURCE_LEAK = "resource_leak"
    CONTENTION = "contention"
    MISCONFIGURATION = "misconfiguration"


@dataclass
class BrendanGreggInsight:
    """
    An insight from Brendan Gregg persona analysis.

    This represents a finding with Brendan's characteristic depth,
    including methodology used, evidence, and actionable recommendations.
    """

    id: str
    timestamp: datetime
    methodology: AnalysisMethodology
    component: str
    issue_type: PerformanceIssueType
    severity: str  # critical, high, medium, low, info
    title: str

    # Brendan's style: data-driven analysis
    observation: str  # What the data shows
    evidence: Dict[str, float]  # Specific metrics as evidence
    root_cause: str  # Technical explanation

    # Brendan's style: practical recommendations
    immediate_action: str  # What to do right now
    investigation_steps: List[str]  # How to dig deeper
    long_term_fix: str  # Sustainable solution

    # Additional context
    related_metrics: List[str]
    confidence: float  # 0-100
    book_reference: Optional[str] = None  # Reference to Systems Performance book

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class PrometheusClient:
    """
    Client for querying Prometheus metrics.

    Supports PromQL queries and data aggregation for performance analysis.
    """

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        """
        Initialize Prometheus client.

        Args:
            prometheus_url: URL of Prometheus server
        """
        self.prometheus_url = prometheus_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        logger.info(f"Initialized Prometheus client: {self.prometheus_url}")

    def query_instant(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Execute instant PromQL query.

        Args:
            query: PromQL query string

        Returns:
            Query result or None on error
        """
        try:
            url = f"{self.prometheus_url}/api/v1/query"
            params = {"query": query}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("status") != "success":
                logger.warning(f"Prometheus query failed: {data.get('error')}")
                return None

            return data.get("data", {})

        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return None

    def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "15s"
    ) -> Optional[Dict[str, Any]]:
        """
        Execute range PromQL query.

        Args:
            query: PromQL query string
            start: Start time
            end: End time
            step: Query resolution

        Returns:
            Query result or None on error
        """
        try:
            url = f"{self.prometheus_url}/api/v1/query_range"
            params = {
                "query": query,
                "start": start.timestamp(),
                "end": end.timestamp(),
                "step": step,
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data.get("status") != "success":
                logger.warning(f"Prometheus range query failed: {data.get('error')}")
                return None

            return data.get("data", {})

        except Exception as e:
            logger.error(f"Error querying Prometheus range: {e}")
            return None

    def get_metric_value(self, query: str) -> Optional[float]:
        """
        Get single metric value from instant query.

        Args:
            query: PromQL query

        Returns:
            Metric value or None
        """
        result = self.query_instant(query)
        if not result or not result.get("result"):
            return None

        try:
            return float(result["result"][0]["value"][1])
        except (IndexError, KeyError, ValueError) as e:
            logger.debug(f"Could not extract value from query result: {e}")
            return None


class GrafanaDashboardAnalyzer:
    """
    Analyzer for Grafana dashboards.

    Fetches dashboard definitions and panel data for analysis.
    """

    def __init__(
        self,
        grafana_url: str = "http://localhost:3000",
        api_key: Optional[str] = None,
        username: str = "admin",
        password: str = "admin123"
    ):
        """
        Initialize Grafana dashboard analyzer.

        Args:
            grafana_url: URL of Grafana server
            api_key: API key for authentication (preferred)
            username: Username for basic auth (fallback)
            password: Password for basic auth (fallback)
        """
        self.grafana_url = grafana_url.rstrip("/")
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        else:
            self.session.auth = (username, password)

        self.session.headers.update({"Content-Type": "application/json"})
        logger.info(f"Initialized Grafana analyzer: {self.grafana_url}")

    def list_dashboards(self) -> List[Dict[str, Any]]:
        """
        List all available dashboards.

        Returns:
            List of dashboard metadata
        """
        try:
            url = f"{self.grafana_url}/api/search?type=dash-db"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Error listing Grafana dashboards: {e}")
            return []

    def get_dashboard(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get dashboard definition by UID.

        Args:
            uid: Dashboard UID

        Returns:
            Dashboard definition or None
        """
        try:
            url = f"{self.grafana_url}/api/dashboards/uid/{uid}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Error fetching Grafana dashboard {uid}: {e}")
            return None

    def extract_panel_queries(self, dashboard: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract PromQL queries from dashboard panels.

        Args:
            dashboard: Dashboard definition

        Returns:
            List of panel queries with metadata
        """
        panels = []

        try:
            dashboard_data = dashboard.get("dashboard", {})

            for panel in dashboard_data.get("panels", []):
                panel_info = {
                    "id": panel.get("id"),
                    "title": panel.get("title", "Untitled"),
                    "type": panel.get("type"),
                    "queries": [],
                }

                # Extract targets (queries)
                for target in panel.get("targets", []):
                    if "expr" in target:  # Prometheus query
                        panel_info["queries"].append({
                            "expr": target["expr"],
                            "legend": target.get("legendFormat", ""),
                            "refId": target.get("refId", ""),
                        })

                if panel_info["queries"]:
                    panels.append(panel_info)

        except Exception as e:
            logger.error(f"Error extracting panel queries: {e}")

        return panels


class BrendanGreggPersona:
    """
    AI Persona based on Brendan Gregg's methodologies and analysis style.

    This persona analyzes system performance metrics from Prometheus/Grafana
    using Brendan's proven methodologies including the USE Method, workload
    characterization, drill-down analysis, and more.

    Characteristics:
    - Data-driven: Always backs findings with specific metrics
    - Methodical: Uses structured analysis approaches (USE, TSA, etc.)
    - Practical: Provides actionable recommendations
    - Deep: Digs into root causes, not just symptoms
    - Educational: References book chapters and concepts
    """

    # Brendan's recommended thresholds from Systems Performance book
    THRESHOLDS = {
        "cpu": {
            "utilization_warning": 80.0,  # %
            "utilization_critical": 95.0,  # %
            "saturation_warning": 1.0,  # load per CPU
            "saturation_critical": 2.0,  # load per CPU
        },
        "memory": {
            "utilization_warning": 85.0,  # %
            "utilization_critical": 95.0,  # %
            "saturation_warning": 10.0,  # % swap usage
            "saturation_critical": 50.0,  # % swap usage
        },
        "disk": {
            "utilization_warning": 70.0,  # %
            "utilization_critical": 90.0,  # %
            "saturation_warning": 5.0,  # avg queue depth
            "saturation_critical": 10.0,  # avg queue depth
            "latency_warning": 10.0,  # ms
            "latency_critical": 50.0,  # ms
        },
        "network": {
            "utilization_warning": 70.0,  # % of bandwidth
            "utilization_critical": 90.0,  # % of bandwidth
            "error_rate_warning": 0.1,  # % packet errors
            "error_rate_critical": 1.0,  # % packet errors
        },
    }

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        grafana_url: str = "http://localhost:3000",
        grafana_username: str = "admin",
        grafana_password: str = "admin123",
    ):
        """
        Initialize Brendan Gregg persona.

        Args:
            prometheus_url: Prometheus server URL
            grafana_url: Grafana server URL
            grafana_username: Grafana username
            grafana_password: Grafana password
        """
        self.prometheus = PrometheusClient(prometheus_url)
        self.grafana = GrafanaDashboardAnalyzer(
            grafana_url,
            username=grafana_username,
            password=grafana_password,
        )

        console.print("[green]✅[/green] Brendan Gregg Persona initialized")
        console.print(f"[blue]→[/blue] Prometheus: {prometheus_url}")
        console.print(f"[blue]→[/blue] Grafana: {grafana_url}")

    async def analyze_use_method(self) -> List[BrendanGreggInsight]:
        """
        Apply the USE Method (Utilization, Saturation, Errors).

        This is Brendan's signature methodology for comprehensive
        performance analysis. For every resource, check:
        - Utilization: How busy is the resource?
        - Saturation: Is there queued work?
        - Errors: Are there any errors?

        Returns:
            List of insights from USE Method analysis
        """
        console.print("\n[bold blue]🔍 Applying USE Method[/bold blue]")
        console.print("Brendan Gregg's methodology for resource analysis\n")

        insights = []

        # CPU Analysis
        cpu_insights = await self._analyze_cpu_use()
        insights.extend(cpu_insights)

        # Memory Analysis
        memory_insights = await self._analyze_memory_use()
        insights.extend(memory_insights)

        # Disk Analysis
        disk_insights = await self._analyze_disk_use()
        insights.extend(disk_insights)

        # Network Analysis
        network_insights = await self._analyze_network_use()
        insights.extend(network_insights)

        return insights

    async def _analyze_cpu_use(self) -> List[BrendanGreggInsight]:
        """Analyze CPU using USE Method."""
        insights = []

        # Utilization
        cpu_util_query = '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        cpu_util = self.prometheus.get_metric_value(cpu_util_query)

        # Saturation (load average per CPU)
        load_query = "node_load1"
        load_1m = self.prometheus.get_metric_value(load_query)

        cpu_count_query = 'count(node_cpu_seconds_total{mode="idle"})'
        cpu_count = self.prometheus.get_metric_value(cpu_count_query)

        if cpu_util is not None and load_1m is not None and cpu_count is not None:
            load_per_cpu = load_1m / max(cpu_count, 1)

            # Analyze utilization
            if cpu_util > self.THRESHOLDS["cpu"]["utilization_critical"]:
                insights.append(BrendanGreggInsight(
                    id=f"cpu_util_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    methodology=AnalysisMethodology.USE_METHOD,
                    component="cpu",
                    issue_type=PerformanceIssueType.BOTTLENECK,
                    severity="critical",
                    title="CPU Utilization at Critical Level",
                    observation=f"CPU utilization is at {cpu_util:.1f}%, exceeding the {self.THRESHOLDS['cpu']['utilization_critical']}% critical threshold.",
                    evidence={
                        "cpu_utilization": cpu_util,
                        "cpu_count": cpu_count,
                        "threshold_critical": self.THRESHOLDS["cpu"]["utilization_critical"],
                    },
                    root_cause="High CPU utilization indicates the system is compute-bound. This could be due to inefficient algorithms, lack of caching, excessive context switching, or simply insufficient CPU resources for the workload.",
                    immediate_action="Use `top` or `htop` to identify the top CPU consumers. Consider: 1) Killing non-essential processes, 2) Moving workloads to other systems, 3) Reducing traffic/load if possible.",
                    investigation_steps=[
                        "Run `mpstat -P ALL 1` to see per-CPU utilization",
                        "Use `perf top` to identify hot functions (requires Linux perf)",
                        "Check `sar -u 1` for historical CPU utilization patterns",
                        "Profile application with flame graphs to find CPU bottlenecks",
                        "Review application logs for unusual activity spikes",
                    ],
                    long_term_fix="1) Optimize hot code paths identified in profiling, 2) Implement caching to reduce computation, 3) Scale horizontally by adding more CPU cores/instances, 4) Consider moving CPU-intensive tasks to background queues.",
                    related_metrics=["node_load1", "node_load5", "process_cpu_seconds_total"],
                    confidence=95.0,
                    book_reference="Systems Performance 2nd Ed., Chapter 6: CPUs"
                ))

            # Analyze saturation
            if load_per_cpu > self.THRESHOLDS["cpu"]["saturation_critical"]:
                insights.append(BrendanGreggInsight(
                    id=f"cpu_sat_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    methodology=AnalysisMethodology.USE_METHOD,
                    component="cpu",
                    issue_type=PerformanceIssueType.SATURATION,
                    severity="high",
                    title="CPU Saturation Detected - High Run Queue",
                    observation=f"Load average per CPU is {load_per_cpu:.2f}, meaning there are {load_per_cpu:.2f}x more runnable threads than CPUs. This indicates significant CPU saturation.",
                    evidence={
                        "load_average_1m": load_1m,
                        "cpu_count": cpu_count,
                        "load_per_cpu": load_per_cpu,
                        "threshold_critical": self.THRESHOLDS["cpu"]["saturation_critical"],
                    },
                    root_cause="CPU saturation occurs when there are more runnable threads than available CPUs, causing threads to wait in the run queue. This increases scheduling latency and overall application response time.",
                    immediate_action="Check the run queue with `vmstat 1` (look at 'r' column). Identify processes causing load with `ps -eo pid,comm,pri,%cpu --sort=-%cpu | head -20`.",
                    investigation_steps=[
                        "Use `pidstat -u 1` to see per-process CPU usage over time",
                        "Check for CPU affinity issues with `taskset -c -p <PID>`",
                        "Look for 'involuntary context switches' with `pidstat -w 1`",
                        "Profile scheduler behavior with `perf sched record/report`",
                        "Examine thread states with Thread State Analysis (TSA)",
                    ],
                    long_term_fix="1) Reduce number of CPU-bound threads (optimize thread pool sizes), 2) Add more CPU resources, 3) Implement CPU quotas/limits for less critical workloads, 4) Consider migrating workloads to separate systems.",
                    related_metrics=["node_load5", "node_load15", "node_schedstat_running"],
                    confidence=90.0,
                    book_reference="Systems Performance 2nd Ed., Chapter 6: CPUs - Section 6.3.2 Saturation"
                ))

        return insights

    async def _analyze_memory_use(self) -> List[BrendanGreggInsight]:
        """Analyze memory using USE Method."""
        insights = []

        # Utilization
        mem_total_query = "node_memory_MemTotal_bytes"
        mem_available_query = "node_memory_MemAvailable_bytes"

        mem_total = self.prometheus.get_metric_value(mem_total_query)
        mem_available = self.prometheus.get_metric_value(mem_available_query)

        if mem_total and mem_available:
            mem_used = mem_total - mem_available
            mem_util = (mem_used / mem_total) * 100

            if mem_util > self.THRESHOLDS["memory"]["utilization_critical"]:
                insights.append(BrendanGreggInsight(
                    id=f"mem_util_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    methodology=AnalysisMethodology.USE_METHOD,
                    component="memory",
                    issue_type=PerformanceIssueType.BOTTLENECK,
                    severity="critical",
                    title="Memory Utilization Critical",
                    observation=f"Memory utilization is {mem_util:.1f}%, with only {mem_available / (1024**3):.1f} GB available out of {mem_total / (1024**3):.1f} GB total.",
                    evidence={
                        "memory_utilization": mem_util,
                        "memory_available_gb": mem_available / (1024**3),
                        "memory_total_gb": mem_total / (1024**3),
                    },
                    root_cause="High memory utilization can lead to paging/swapping, which causes severe performance degradation. Common causes: memory leaks, oversized caches, too many processes, or insufficient memory for workload.",
                    immediate_action="Identify memory hogs with `ps -eo pid,comm,rss --sort=-rss | head -20`. Consider: 1) Restarting leaking processes, 2) Clearing caches (`sync; echo 3 > /proc/sys/vm/drop_caches` as root), 3) Killing non-essential processes.",
                    investigation_steps=[
                        "Check for memory leaks with `valgrind --leak-check=full <process>`",
                        "Use `pmap -x <PID>` to see detailed memory map of a process",
                        "Monitor slab cache with `slabtop` (kernel memory)",
                        "Check for large page cache: `free -h` and compare 'available' vs 'free'",
                        "Profile memory allocations with `perf record -e kmem:* -a sleep 10`",
                    ],
                    long_term_fix="1) Fix memory leaks in applications, 2) Add more RAM, 3) Implement memory limits (cgroups), 4) Optimize data structures to use less memory, 5) Scale horizontally to distribute memory load.",
                    related_metrics=["node_memory_MemFree_bytes", "node_memory_Cached_bytes", "node_memory_Buffers_bytes"],
                    confidence=95.0,
                    book_reference="Systems Performance 2nd Ed., Chapter 7: Memory"
                ))

        # Saturation (swap usage)
        swap_total_query = "node_memory_SwapTotal_bytes"
        swap_free_query = "node_memory_SwapFree_bytes"

        swap_total = self.prometheus.get_metric_value(swap_total_query)
        swap_free = self.prometheus.get_metric_value(swap_free_query)

        if swap_total and swap_free and swap_total > 0:
            swap_used = swap_total - swap_free
            swap_util = (swap_used / swap_total) * 100

            if swap_util > self.THRESHOLDS["memory"]["saturation_critical"]:
                insights.append(BrendanGreggInsight(
                    id=f"mem_sat_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    methodology=AnalysisMethodology.USE_METHOD,
                    component="memory",
                    issue_type=PerformanceIssueType.SATURATION,
                    severity="critical",
                    title="Memory Saturation - Heavy Swapping",
                    observation=f"Swap usage is {swap_util:.1f}% ({swap_used / (1024**3):.1f} GB used). System is paging memory to disk, causing severe performance degradation.",
                    evidence={
                        "swap_utilization": swap_util,
                        "swap_used_gb": swap_used / (1024**3),
                        "swap_total_gb": swap_total / (1024**3),
                    },
                    root_cause="Swapping occurs when physical memory is exhausted. The kernel moves inactive pages to disk to free RAM. Swap I/O is orders of magnitude slower than RAM access (~0.1ms vs ~100μs), causing application slowdowns.",
                    immediate_action="URGENT: Check swap activity with `vmstat 1` (si/so columns). If actively swapping, free memory immediately or applications will become unresponsive. Consider restarting high-memory processes.",
                    investigation_steps=[
                        "Monitor swap I/O: `sar -S 1` or `sar -B 1` for paging stats",
                        "Find processes using swap: `for f in /proc/*/status; do awk '/VmSwap|Name/{printf $2\" \"$3}END{print \"\"}' $f; done | sort -k 2 -n -r | head`",
                        "Check for OOM (Out of Memory) kills in `dmesg | grep -i oom`",
                        "Analyze memory pressure: `cat /proc/pressure/memory`",
                    ],
                    long_term_fix="1) Add more physical RAM (primary solution), 2) Reduce memory usage, 3) Tune kernel swappiness (`sysctl vm.swappiness=10`), 4) Consider disabling swap for performance-critical systems (after adding sufficient RAM).",
                    related_metrics=["node_vmstat_pswpin", "node_vmstat_pswpout"],
                    confidence=98.0,
                    book_reference="Systems Performance 2nd Ed., Chapter 7: Memory - Section 7.3.2 Saturation"
                ))

        return insights

    async def _analyze_disk_use(self) -> List[BrendanGreggInsight]:
        """Analyze disk using USE Method."""
        insights = []

        # Utilization (I/O time percentage)
        disk_util_query = 'rate(node_disk_io_time_seconds_total[5m]) * 100'
        disk_util = self.prometheus.get_metric_value(disk_util_query)

        if disk_util and disk_util > self.THRESHOLDS["disk"]["utilization_warning"]:
            severity = "critical" if disk_util > self.THRESHOLDS["disk"]["utilization_critical"] else "high"

            insights.append(BrendanGreggInsight(
                id=f"disk_util_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                methodology=AnalysisMethodology.USE_METHOD,
                component="disk",
                issue_type=PerformanceIssueType.BOTTLENECK,
                severity=severity,
                title="Disk I/O Utilization High",
                observation=f"Disk utilization is {disk_util:.1f}%, indicating the disk subsystem is busy. This can cause application I/O latency.",
                evidence={
                    "disk_utilization": disk_util,
                    "threshold_warning": self.THRESHOLDS["disk"]["utilization_warning"],
                },
                root_cause="High disk utilization means the disk is busy servicing I/O requests. For rotational disks, this often means the disk head is moving constantly. For SSDs, it could indicate the controller is saturated or write amplification is occurring.",
                immediate_action="Check which processes are performing I/O: `iotop` or `pidstat -d 1`. Identify hot files: `lsof | grep <mountpoint>`. Consider: 1) Stopping I/O-heavy non-essential processes, 2) Moving I/O to another disk/filesystem.",
                investigation_steps=[
                    "Use `iostat -xz 1` to see detailed per-disk statistics",
                    "Check for specific I/O patterns with `blktrace` and `blkparse`",
                    "Identify slow I/O with `biosnoop` (from BCC tools)",
                    "Profile file system operations with `filetop` (BCC)",
                    "Look for read vs write patterns: `sar -d 1`",
                ],
                long_term_fix="1) Add faster storage (SSD/NVMe), 2) Implement caching to reduce disk I/O, 3) Optimize database queries to minimize disk reads, 4) Distribute I/O across multiple disks (RAID, sharding), 5) Archive old data to free I/O capacity.",
                related_metrics=["node_disk_read_bytes_total", "node_disk_written_bytes_total", "node_disk_io_time_weighted_seconds_total"],
                confidence=85.0,
                book_reference="Systems Performance 2nd Ed., Chapter 9: Disks"
            ))

        return insights

    async def _analyze_network_use(self) -> List[BrendanGreggInsight]:
        """Analyze network using USE Method."""
        insights = []

        # Errors
        rx_errors_query = 'rate(node_network_receive_errs_total[5m])'
        tx_errors_query = 'rate(node_network_transmit_errs_total[5m])'

        rx_errors = self.prometheus.get_metric_value(rx_errors_query) or 0
        tx_errors = self.prometheus.get_metric_value(tx_errors_query) or 0

        if rx_errors > 0 or tx_errors > 0:
            insights.append(BrendanGreggInsight(
                id=f"net_errors_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                methodology=AnalysisMethodology.USE_METHOD,
                component="network",
                issue_type=PerformanceIssueType.ERROR,
                severity="high",
                title="Network Errors Detected",
                observation=f"Network errors detected: {rx_errors:.2f} receive errors/sec, {tx_errors:.2f} transmit errors/sec. Errors can indicate hardware issues, driver problems, or network congestion.",
                evidence={
                    "rx_errors_per_sec": rx_errors,
                    "tx_errors_per_sec": tx_errors,
                },
                root_cause="Network errors can be caused by: 1) Faulty NICs or cables, 2) Driver/firmware bugs, 3) Network congestion causing packet loss, 4) Duplex mismatches, 5) MTU issues causing fragmentation.",
                immediate_action="Check interface errors: `ip -s link` or `ifconfig`. Look for 'errors', 'dropped', 'overruns'. Check NIC driver: `ethtool -S <interface>` for detailed stats.",
                investigation_steps=[
                    "Inspect physical connections (cables, NICs)",
                    "Check for duplex mismatches: `ethtool <interface>` and verify link partner",
                    "Look for dropped packets: `netstat -i` or `ss -s`",
                    "Monitor network with `sar -n DEV 1`",
                    "Use `tcpdump` to analyze problematic traffic patterns",
                    "Check for MTU issues: `ping -M do -s 1472 <host>` (adjust size)",
                ],
                long_term_fix="1) Replace faulty hardware (NIC, cables, switches), 2) Update NIC drivers/firmware, 3) Configure proper duplex/speed settings, 4) Implement QoS to handle congestion, 5) Consider upgrading network capacity.",
                related_metrics=["node_network_receive_drop_total", "node_network_transmit_drop_total", "node_network_receive_packets_total"],
                confidence=88.0,
                book_reference="Systems Performance 2nd Ed., Chapter 10: Network"
            ))

        return insights

    async def analyze_grafana_dashboard(self, dashboard_uid: str) -> List[BrendanGreggInsight]:
        """
        Analyze a specific Grafana dashboard.

        Brendan's approach: Look at the dashboard panels, understand what they're
        measuring, and interpret the data in context of performance methodologies.

        Args:
            dashboard_uid: Grafana dashboard UID

        Returns:
            List of insights from dashboard analysis
        """
        console.print(f"\n[bold blue]📊 Analyzing Grafana Dashboard: {dashboard_uid}[/bold blue]\n")

        dashboard = self.grafana.get_dashboard(dashboard_uid)
        if not dashboard:
            console.print("[red]❌[/red] Could not fetch dashboard")
            return []

        dashboard_title = dashboard.get("dashboard", {}).get("title", "Unknown")
        console.print(f"[green]→[/green] Dashboard: {dashboard_title}")

        panels = self.grafana.extract_panel_queries(dashboard)
        console.print(f"[green]→[/green] Found {len(panels)} panels with queries\n")

        insights = []

        for panel in panels:
            console.print(f"[yellow]Analyzing panel:[/yellow] {panel['title']}")

            for query_info in panel["queries"]:
                expr = query_info["expr"]

                # Execute query and analyze result
                result = self.prometheus.query_instant(expr)
                if result and result.get("result"):
                    # Extract metric value
                    try:
                        value = float(result["result"][0]["value"][1])
                        console.print(f"  [cyan]→[/cyan] Metric value: {value:.2f}")

                        # Contextual analysis based on panel title
                        panel_insights = self._analyze_panel_value(
                            panel["title"],
                            expr,
                            value,
                            dashboard_title
                        )
                        insights.extend(panel_insights)

                    except (IndexError, KeyError, ValueError):
                        pass

        return insights

    def _analyze_panel_value(
        self,
        panel_title: str,
        query: str,
        value: float,
        dashboard_name: str
    ) -> List[BrendanGreggInsight]:
        """
        Analyze a panel metric value in context.

        Brendan's style: Interpret the metric based on what we know about
        the system and established performance baselines.
        """
        insights = []

        # Pattern matching on panel title to understand what we're measuring
        panel_lower = panel_title.lower()

        # CPU-related panels
        if "cpu" in panel_lower and "usage" in panel_lower:
            if value > 80:
                insights.append(BrendanGreggInsight(
                    id=f"panel_{panel_title}_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    methodology=AnalysisMethodology.DRILL_DOWN_ANALYSIS,
                    component="cpu",
                    issue_type=PerformanceIssueType.BOTTLENECK,
                    severity="high" if value > 90 else "medium",
                    title=f"High CPU observed in dashboard panel: {panel_title}",
                    observation=f"Panel '{panel_title}' in dashboard '{dashboard_name}' shows CPU at {value:.1f}%.",
                    evidence={"panel_value": value, "query": query},
                    root_cause="As observed in the dashboard, CPU utilization is elevated. This aligns with the USE Method's utilization metric for CPU resources.",
                    immediate_action="Drill down into this metric by checking which processes are consuming CPU. Cross-reference with other panels in the dashboard.",
                    investigation_steps=[
                        f"Review other panels in '{dashboard_name}' for correlated metrics",
                        "Check if this is a consistent pattern or a spike",
                        "Identify the time range and correlate with application logs",
                    ],
                    long_term_fix="Based on dashboard trends, implement capacity planning for CPU resources.",
                    related_metrics=[],
                    confidence=75.0,
                    book_reference="Systems Performance 2nd Ed., Chapter 2: Methodologies - Drill-Down Analysis"
                ))

        return insights

    def generate_brendan_style_report(self, insights: List[BrendanGreggInsight]) -> str:
        """
        Generate a performance report in Brendan Gregg's style.

        Characteristics:
        - Structured with clear sections
        - Data-driven with specific metrics
        - Practical recommendations
        - Educational references
        """
        report = []
        report.append("=" * 80)
        report.append("SYSTEMS PERFORMANCE ANALYSIS REPORT")
        report.append("Based on Brendan Gregg's Methodologies")
        report.append("=" * 80)
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if not insights:
            report.append("✅ No performance issues detected. System is operating within normal parameters.\n")
            return "\n".join(report)

        # Group by severity
        critical = [i for i in insights if i.severity == "critical"]
        high = [i for i in insights if i.severity == "high"]
        medium = [i for i in insights if i.severity == "medium"]

        report.append(f"SUMMARY:")
        report.append(f"  Critical Issues: {len(critical)}")
        report.append(f"  High Priority:   {len(high)}")
        report.append(f"  Medium Priority: {len(medium)}")
        report.append(f"  Total Findings:  {len(insights)}\n")

        # Critical issues first (Brendan's priority: fix critical issues before optimizing)
        if critical:
            report.append("🚨 CRITICAL ISSUES - IMMEDIATE ACTION REQUIRED")
            report.append("-" * 80)
            for i, insight in enumerate(critical, 1):
                report.append(f"\n[{i}] {insight.title}")
                report.append(f"    Component: {insight.component}")
                report.append(f"    Methodology: {insight.methodology.value}")
                report.append(f"\n    OBSERVATION:")
                report.append(f"    {insight.observation}")
                report.append(f"\n    EVIDENCE:")
                for key, val in insight.evidence.items():
                    report.append(f"      • {key}: {val}")
                report.append(f"\n    ROOT CAUSE:")
                report.append(f"    {insight.root_cause}")
                report.append(f"\n    ⚡ IMMEDIATE ACTION:")
                report.append(f"    {insight.immediate_action}")
                report.append(f"\n    🔍 INVESTIGATION STEPS:")
                for step in insight.investigation_steps:
                    report.append(f"      1. {step}")
                report.append(f"\n    🔧 LONG-TERM FIX:")
                report.append(f"    {insight.long_term_fix}")
                if insight.book_reference:
                    report.append(f"\n    📚 Reference: {insight.book_reference}")
                report.append("\n" + "-" * 80)

        # High priority
        if high:
            report.append("\n⚠️  HIGH PRIORITY ISSUES")
            report.append("-" * 80)
            for insight in high:
                report.append(f"\n• {insight.title}")
                report.append(f"  {insight.observation}")
                report.append(f"  → {insight.immediate_action}")

        # Recommendations summary
        report.append("\n" + "=" * 80)
        report.append("RECOMMENDATIONS SUMMARY")
        report.append("=" * 80)
        report.append("\nBrendan Gregg's methodology emphasizes fixing issues in order of impact:")
        report.append("1. Eliminate errors first (errors always indicate problems)")
        report.append("2. Address saturation (queuing adds latency)")
        report.append("3. Optimize utilization (high utilization limits headroom)\n")

        return "\n".join(report)


# Example usage and CLI integration
async def main():
    """Main function demonstrating Brendan Gregg persona usage."""
    console.print(Panel.fit(
        "[bold cyan]🎯 Brendan Gregg Persona[/bold cyan]\n"
        "Performance Analysis using proven methodologies\n"
        "USE Method | Workload Characterization | Drill-Down Analysis",
        border_style="cyan"
    ))

    # Initialize persona
    persona = BrendanGreggPersona(
        prometheus_url=os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
        grafana_url=os.getenv("GRAFANA_URL", "http://localhost:3000"),
    )

    # Run USE Method analysis
    console.print("\n[bold]Running USE Method Analysis...[/bold]")
    insights = await persona.analyze_use_method()

    # Analyze Grafana dashboards
    console.print("\n[bold]Analyzing Grafana Dashboards...[/bold]")
    dashboards = persona.grafana.list_dashboards()

    if dashboards:
        # Analyze first dashboard (or specific one)
        dashboard_uid = dashboards[0].get("uid")
        if dashboard_uid:
            dashboard_insights = await persona.analyze_grafana_dashboard(dashboard_uid)
            insights.extend(dashboard_insights)

    # Generate report
    report = persona.generate_brendan_style_report(insights)
    console.print("\n" + report)

    # Save insights to JSON
    output_file = f"brendan_gregg_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump([insight.to_dict() for insight in insights], f, indent=2, default=str)

    console.print(f"\n[green]✅[/green] Analysis complete. Insights saved to: {output_file}")
    console.print(f"[blue]→[/blue] Total insights: {len(insights)}")


if __name__ == "__main__":
    asyncio.run(main())
