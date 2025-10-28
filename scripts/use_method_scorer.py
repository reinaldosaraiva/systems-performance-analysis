#!/usr/bin/env python3
"""
USE Method Scorer
Calculates USE (Utilization, Saturation, Errors) scores following Brendan Gregg's methodology.
Integrates with Prometheus metrics for real-time system performance analysis.
"""

import logging
import time
import json
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class Status(Enum):
    """Status codes for USE analysis."""

    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class USEScore:
    """USE Method score for a component."""

    component: str
    utilization: float  # 0-100%
    saturation: float  # 0-100%
    errors: float  # 0-100%
    overall_score: float  # 0-100%
    status: Status
    recommendations: List[str]
    timestamp: str


class USEMethodScorer:
    """
    USE Method Scorer following Brendan Gregg's methodology.

    Thresholds based on best practices:
    - CPU: U>80%, S>20%, E>0
    - Memory: U>85%, S>10%, E>0
    - Disk: U>70%, S>30%, E>0
    - Network: U>80%, S>15%, E>0
    """

    THRESHOLDS = {
        "cpu": {"utilization": 80, "saturation": 20, "errors": 0},
        "memory": {"utilization": 85, "saturation": 10, "errors": 0},
        "disk": {"utilization": 70, "saturation": 30, "errors": 0},
        "network": {"utilization": 80, "saturation": 15, "errors": 0},
    }

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        """
        Initialize USE Method scorer.

        Args:
            prometheus_url: Prometheus server URL
        """
        self.prometheus_url = prometheus_url
        self.session = requests.Session()
        # Session timeout handled in individual requests

    def calculate_system_scores(self, instance_filter: str = "") -> Dict[str, USEScore]:
        """
        Calculate USE scores for all system components.

        Args:
            instance_filter: Filter for specific instances

        Returns:
            Dictionary of USE scores by component
        """
        logger.info("Calculating USE Method scores for system")
        scores = {}

        # Calculate scores for each component
        for component in ["cpu", "memory", "disk", "network"]:
            try:
                score = self._calculate_component_score(component, instance_filter)
                scores[component] = score
                logger.info(
                    f"{component.upper()} USE score: {score.overall_score:.1f}% ({score.status.value})"
                )
            except Exception as e:
                logger.error(f"Failed to calculate {component} score: {e}")
                scores[component] = USEScore(
                    component=component,
                    utilization=0,
                    saturation=0,
                    errors=100,
                    overall_score=100,
                    status=Status.CRITICAL,
                    recommendations=[f"Analysis failed: {e}"],
                    timestamp=datetime.now().isoformat(),
                )

        return scores

    def _calculate_component_score(
        self, component: str, instance_filter: str
    ) -> USEScore:
        """Calculate USE score for a specific component."""
        thresholds = self.THRESHOLDS[component]

        # Calculate metrics based on component type
        if component == "cpu":
            utilization = self._query_cpu_utilization(instance_filter)
            saturation = self._query_cpu_saturation(instance_filter)
            errors = self._query_cpu_errors(instance_filter)
        elif component == "memory":
            utilization = self._query_memory_utilization(instance_filter)
            saturation = self._query_memory_saturation(instance_filter)
            errors = self._query_memory_errors(instance_filter)
        elif component == "disk":
            utilization = self._query_disk_utilization(instance_filter)
            saturation = self._query_disk_saturation(instance_filter)
            errors = self._query_disk_errors(instance_filter)
        elif component == "network":
            utilization = self._query_network_utilization(instance_filter)
            saturation = self._query_network_saturation(instance_filter)
            errors = self._query_network_errors(instance_filter)
        else:
            raise ValueError(f"Unknown component: {component}")

        # Limit values to 0-100%
        utilization = min(max(utilization, 0), 100)
        saturation = min(max(saturation, 0), 100)
        errors = min(max(errors, 0), 100)

        # Calculate overall score (maximum of the three)
        overall_score = max(utilization, saturation, errors)

        # Determine status
        status = self._determine_status(utilization, saturation, errors, thresholds)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            component, utilization, saturation, errors, status
        )

        return USEScore(
            component=component,
            utilization=utilization,
            saturation=saturation,
            errors=errors,
            overall_score=overall_score,
            status=status,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
        )

    def _query_prometheus(self, query: str) -> float:
        """Execute Prometheus query and return float value."""
        try:
            response = self.session.get(
                f"{self.prometheus_url}/api/v1/query", params={"query": query}
            )
            response.raise_for_status()
            data = response.json()

            if data["status"] == "success" and data["data"]["result"]:
                value = float(data["data"]["result"][0]["value"][1])
                return value
            else:
                logger.warning(f"No data for query: {query}")
                return 0.0

        except Exception as e:
            logger.error(f"Failed to query Prometheus: {e}")
            return 0.0

    def _query_cpu_utilization(self, instance_filter: str) -> float:
        """Query CPU utilization."""
        query = f'100 - avg by(instance)(irate(node_cpu_seconds_total{{mode="idle"{instance_filter}}}[5m]) * 100)'
        return self._query_prometheus(query)

    def _query_cpu_saturation(self, instance_filter: str) -> float:
        """Query CPU saturation (load average per CPU)."""
        query = f'node_load1{instance_filter} / count by(instance)(node_cpu_seconds_total{{mode="idle"{instance_filter}}}) * 100'
        return self._query_prometheus(query)

    def _query_cpu_errors(self, instance_filter: str) -> float:
        """Query CPU errors (steal time as proxy)."""
        query = f'avg by(instance)(irate(node_cpu_seconds_total{{mode="steal"{instance_filter}}}[5m]) * 100)'
        return self._query_prometheus(query)

    def _query_memory_utilization(self, instance_filter: str) -> float:
        """Query memory utilization."""
        query = f"(1 - (node_memory_MemAvailable_bytes{instance_filter} / node_memory_MemTotal_bytes{instance_filter})) * 100"
        return self._query_prometheus(query)

    def _query_memory_saturation(self, instance_filter: str) -> float:
        """Query memory saturation (swap usage)."""
        query = f"(1 - (node_memory_SwapFree_bytes{instance_filter} / node_memory_SwapTotal_bytes{instance_filter})) * 100"
        return self._query_prometheus(query)

    def _query_memory_errors(self, instance_filter: str) -> float:
        """Query memory errors (OOM kills)."""
        query = f"rate(node_vmstat_oom_kill{instance_filter}[5m]) * 100"
        return self._query_prometheus(query)

    def _query_disk_utilization(self, instance_filter: str) -> float:
        """Query disk utilization."""
        query = f'(1 - (node_filesystem_free_bytes{{fstype!="tmpfs"{instance_filter}}} / node_filesystem_size_bytes{{fstype!="tmpfs"{instance_filter}}})) * 100'
        return self._query_prometheus(query)

    def _query_disk_saturation(self, instance_filter: str) -> float:
        """Query disk saturation (I/O time)."""
        query = f"avg by(instance)(irate(node_disk_io_time_seconds_total{instance_filter}[5m]) * 100)"
        return self._query_prometheus(query)

    def _query_disk_errors(self, instance_filter: str) -> float:
        """Query disk errors."""
        query = f"rate(node_disk_read_errors_total{instance_filter}[5m]) + rate(node_disk_write_errors_total{instance_filter}[5m])"
        return self._query_prometheus(query) * 100  # Convert to percentage

    def _query_network_utilization(self, instance_filter: str) -> float:
        """Query network utilization (as percentage of 1Gbps)."""
        query = f'(rate(node_network_receive_bytes_total{{device!="lo"{instance_filter}}}[5m]) + rate(node_network_transmit_bytes_total{{device!="lo"{instance_filter}}}[5m])) * 8 / 10000000 * 100'
        return self._query_prometheus(query)

    def _query_network_saturation(self, instance_filter: str) -> float:
        """Query network saturation (packet drops)."""
        query = f'(rate(node_network_receive_drop_total{{device!="lo"{instance_filter}}}[5m]) + rate(node_network_transmit_drop_total{{device!="lo"{instance_filter}}}[5m]))'
        drops_per_sec = self._query_prometheus(query)
        return min(drops_per_sec / 10, 100)  # Scale to percentage, max at 10 drops/sec

    def _query_network_errors(self, instance_filter: str) -> float:
        """Query network errors."""
        query = f'(rate(node_network_receive_errs_total{{device!="lo"{instance_filter}}}[5m]) + rate(node_network_transmit_errs_total{{device!="lo"{instance_filter}}}[5m]))'
        errors_per_sec = self._query_prometheus(query)
        return min(errors_per_sec * 10, 100)  # Scale to percentage

    def _determine_status(
        self,
        utilization: float,
        saturation: float,
        errors: float,
        thresholds: Dict[str, Any],
    ) -> Status:
        """Determine status based on USE metrics and thresholds."""
        if errors > thresholds["errors"]:
            return Status.CRITICAL
        elif (
            utilization > thresholds["utilization"]
            or saturation > thresholds["saturation"]
        ):
            return Status.WARNING
        else:
            return Status.OK

    def _generate_recommendations(
        self,
        component: str,
        utilization: float,
        saturation: float,
        errors: float,
        status: Status,
    ) -> List[str]:
        """Generate recommendations based on USE analysis."""
        recommendations = []

        if component == "cpu":
            if utilization > 80:
                recommendations.append(
                    "🔥 CPU utilization >80%: Consider scaling up or optimizing CPU-intensive processes"
                )
            if saturation > 20:
                recommendations.append(
                    "⚡ CPU saturation detected: High load average indicates system overload"
                )
            if errors > 0:
                recommendations.append(
                    "❌ CPU steal time detected: Virtualization contention, consider larger instance"
                )

        elif component == "memory":
            if utilization > 85:
                recommendations.append(
                    "💾 Memory utilization >85%: Risk of OOM, consider adding RAM or optimizing memory usage"
                )
            if saturation > 10:
                recommendations.append(
                    "🔄 Swap usage >10%: Performance degradation, increase RAM or optimize applications"
                )
            if errors > 0:
                recommendations.append(
                    "🚨 OOM kills detected: Critical memory shortage, immediate action required"
                )

        elif component == "disk":
            if utilization > 70:
                recommendations.append(
                    "💿 Disk usage >70%: Risk of full disk, implement cleanup and monitoring"
                )
            if saturation > 30:
                recommendations.append(
                    "⏱️ Disk I/O saturation: Storage bottleneck, consider SSD upgrade or I/O optimization"
                )
            if errors > 0:
                recommendations.append(
                    "❌ Disk I/O errors: Hardware issues detected, check disk health"
                )

        elif component == "network":
            if utilization > 80:
                recommendations.append(
                    "🌐 Network utilization >80%: Bandwidth saturation, consider link upgrade"
                )
            if saturation > 15:
                recommendations.append(
                    "📦 Packet drops detected: Network congestion, check network configuration"
                )
            if errors > 0:
                recommendations.append(
                    "❌ Network errors: Hardware or configuration issues, check interfaces"
                )

        # General recommendations based on status
        if status == Status.CRITICAL:
            recommendations.append(
                "🚨 CRITICAL: Immediate action required to prevent system failure"
            )
        elif status == Status.WARNING:
            recommendations.append(
                "⚠️ WARNING: Monitor closely and plan corrective actions"
            )
        else:
            recommendations.append(
                "✅ OK: Component operating within normal parameters"
            )

        return recommendations

    def export_scores_json(
        self, scores: Dict[str, USEScore], filename: Optional[str] = None
    ) -> str:
        """Export USE scores to JSON file."""
        if filename is None:
            filename = f"use_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Convert to serializable format
        data = {
            "timestamp": datetime.now().isoformat(),
            "methodology": "USE Method by Brendan Gregg",
            "thresholds": self.THRESHOLDS,
            "scores": {comp: asdict(score) for comp, score in scores.items()},
        }

        # Convert Status enum to string
        for comp, score in data["scores"].items():
            score["status"] = (
                score["status"].value
                if hasattr(score["status"], "value")
                else str(score["status"])
            )

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"USE scores exported to {filename}")
        return filename

    def get_overall_system_health(self, scores: Dict[str, USEScore]) -> Dict[str, Any]:
        """Calculate overall system health from component scores."""
        if not scores:
            return {"health": "UNKNOWN", "score": 0, "critical_components": []}

        # Find worst status
        status_priority = {Status.CRITICAL: 3, Status.WARNING: 2, Status.OK: 1}
        worst_status = max(
            scores.values(), key=lambda s: status_priority[s.status]
        ).status

        # Calculate average score
        avg_score = sum(score.overall_score for score in scores.values()) / len(scores)

        # Find critical components
        critical_components = [
            comp for comp, score in scores.items() if score.status == Status.CRITICAL
        ]

        return {
            "health": worst_status.value,
            "score": round(avg_score, 1),
            "critical_components": critical_components,
            "total_components": len(scores),
            "healthy_components": len(
                [s for s in scores.values() if s.status == Status.OK]
            ),
        }


def main():
    """Main function for testing USE Method scorer."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    scorer = USEMethodScorer()

    try:
        # Calculate scores for local node exporter
        instance_filter = '{job="node_exporter"}'
        scores = scorer.calculate_system_scores(instance_filter)

        # Print results
        print("\n" + "=" * 60)
        print("USE METHOD ANALYSIS - Brendan Gregg")
        print("=" * 60)

        for component, score in scores.items():
            print(f"\n{component.upper()}:")
            print(f"  Utilization: {score.utilization:.1f}%")
            print(f"  Saturation:  {score.saturation:.1f}%")
            print(f"  Errors:      {score.errors:.1f}%")
            print(f"  Overall:     {score.overall_score:.1f}% ({score.status.value})")

            if score.recommendations:
                print("  Recommendations:")
                for rec in score.recommendations:
                    print(f"    {rec}")

        # Overall system health
        health = scorer.get_overall_system_health(scores)
        print(f"\n{'=' * 60}")
        print(f"OVERALL SYSTEM HEALTH: {health['health']}")
        print(f"Average Score: {health['score']}%")
        print(
            f"Components: {health['healthy_components']}/{health['total_components']} healthy"
        )

        if health["critical_components"]:
            print(f"Critical: {', '.join(health['critical_components'])}")

        # Export to JSON
        filename = scorer.export_scores_json(scores)
        print(f"\nDetailed results exported to: {filename}")

    except Exception as e:
        logger.error(f"Failed to run USE analysis: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
