#!/usr/bin/env python3
"""
Simple Prometheus Remote Test
Testa conexão e coleta básica de métricas do Prometheus remoto.
"""

import requests
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class PrometheusRemoteTest:
    def __init__(self, prometheus_url="http://177.93.132.48:9090"):
        self.prometheus_url = prometheus_url.rstrip("/")
        self.session = requests.Session()
        self.session.timeout = 10

    def query(self, promql):
        """Executa query PromQL."""
        try:
            response = self.session.get(
                f"{self.prometheus_url}/api/v1/query", params={"query": promql}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            console.print(f"[red]❌ Query failed: {promql} - {e}[/red]")
            return None

    def get_basic_metrics(self):
        """Coleta métricas básicas do sistema."""
        console.print("[blue]📊[/blue] Coletando métricas básicas...")

        queries = {
            "load1": "node_load1",
            "load5": "node_load5",
            "load15": "node_load15",
            "cpu_util": "100 - avg by(instance)(irate(node_cpu_seconds_total{mode='idle'}[5m]) * 100)",
            "memory_total": "node_memory_MemTotal_bytes",
            "memory_available": "node_memory_MemAvailable_bytes",
            "memory_used": "node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes",
            "swap_total": "node_memory_SwapTotal_bytes",
            "swap_free": "node_memory_SwapFree_bytes",
            "disk_root_total": "node_filesystem_size_bytes{mountpoint='/'}",
            "disk_root_free": "node_filesystem_free_bytes{mountpoint='/'}",
            "network_receive": "irate(node_network_receive_bytes_total{device!='lo'}[5m])",
            "network_transmit": "irate(node_network_transmit_bytes_total{device!='lo'}[5m])",
            "boot_time": "node_boot_time_seconds",
            "uptime": "time() - node_boot_time_seconds",
        }

        metrics = {}

        for name, query in queries.items():
            result = self.query(query)
            if result and result.get("status") == "success":
                data = result.get("data", {}).get("result", [])
                if data:
                    value = float(data[0]["value"][1])
                    metrics[name] = value
                    console.print(f"  ✅ {name}: {value}")
                else:
                    metrics[name] = 0
                    console.print(f"  ⚠️ {name}: no data")
            else:
                metrics[name] = None
                console.print(f"  ❌ {name}: failed")

        return metrics

    def analyze_use_method(self, metrics):
        """Análise simples usando USE Method."""
        console.print("\n[blue]🔍[/blue] Análise USE Method...")

        analysis = {}

        # CPU Analysis
        cpu_util = metrics.get("cpu_util", 0)
        load1 = metrics.get("load1", 0)

        cpu_status = "OK"
        if cpu_util > 90 or load1 > 4:
            cpu_status = "CRITICAL"
        elif cpu_util > 80 or load1 > 2:
            cpu_status = "WARNING"

        analysis["cpu"] = {
            "utilization": cpu_util,
            "load1": load1,
            "status": cpu_status,
        }

        # Memory Analysis
        mem_total = metrics.get("memory_total", 1)
        mem_used = metrics.get("memory_used", 0)
        mem_util = (mem_used / mem_total) * 100 if mem_total > 0 else 0

        swap_total = metrics.get("swap_total", 1)
        swap_used = swap_total - metrics.get("swap_free", 0)
        swap_util = (swap_used / swap_total) * 100 if swap_total > 0 else 0

        memory_status = "OK"
        if mem_util > 95 or swap_util > 80:
            memory_status = "CRITICAL"
        elif mem_util > 85 or swap_util > 50:
            memory_status = "WARNING"

        analysis["memory"] = {
            "utilization": mem_util,
            "swap_utilization": swap_util,
            "status": memory_status,
        }

        # Disk Analysis
        disk_total = metrics.get("disk_root_total", 1)
        disk_free = metrics.get("disk_root_free", 0)
        disk_util = (
            ((disk_total - disk_free) / disk_total) * 100 if disk_total > 0 else 0
        )

        disk_status = "OK"
        if disk_util > 95:
            disk_status = "CRITICAL"
        elif disk_util > 85:
            disk_status = "WARNING"

        analysis["disk"] = {"utilization": disk_util, "status": disk_status}

        # Network Analysis (simplified)
        net_rx = metrics.get("network_receive", 0)
        net_tx = metrics.get("network_transmit", 0)

        analysis["network"] = {
            "receive_mbps": net_rx * 8 / 1_000_000,  # Convert to Mbps
            "transmit_mbps": net_tx * 8 / 1_000_000,
            "status": "OK",  # Simplified
        }

        return analysis

    def display_results(self, metrics, analysis):
        """Exibe resultados formatados."""

        # System Info Panel
        uptime_hours = metrics.get("uptime", 0) / 3600
        info_panel = Panel(
            f"Uptime: {uptime_hours:.1f} hours\n"
            f"Load Average: {metrics.get('load1', 0):.2f}, {metrics.get('load5', 0):.2f}, {metrics.get('load15', 0):.2f}\n"
            f"Boot Time: {datetime.fromtimestamp(metrics.get('boot_time', 0)).strftime('%Y-%m-%d %H:%M:%S')}",
            title="🖥️ System Information",
            border_style="blue",
        )
        console.print(info_panel)

        # USE Analysis Table
        table = Table(title="📊 USE Method Analysis")
        table.add_column("Component", style="cyan")
        table.add_column("Utilization", style="green")
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="yellow")

        # CPU Row
        cpu = analysis["cpu"]
        cpu_status_color = {
            "OK": "[green]OK[/green]",
            "WARNING": "[yellow]WARNING[/yellow]",
            "CRITICAL": "[red]CRITICAL[/red]",
        }.get(cpu["status"], cpu["status"])

        table.add_row(
            "CPU",
            f"{cpu['utilization']:.1f}%",
            cpu_status_color,
            f"Load: {cpu['load1']:.2f}",
        )

        # Memory Row
        memory = analysis["memory"]
        memory_status_color = {
            "OK": "[green]OK[/green]",
            "WARNING": "[yellow]WARNING[/yellow]",
            "CRITICAL": "[red]CRITICAL[/red]",
        }.get(memory["status"], memory["status"])

        table.add_row(
            "Memory",
            f"{memory['utilization']:.1f}%",
            memory_status_color,
            f"Swap: {memory['swap_utilization']:.1f}%",
        )

        # Disk Row
        disk = analysis["disk"]
        disk_status_color = {
            "OK": "[green]OK[/green]",
            "WARNING": "[yellow]WARNING[/yellow]",
            "CRITICAL": "[red]CRITICAL[/red]",
        }.get(disk["status"], disk["status"])

        table.add_row(
            "Disk", f"{disk['utilization']:.1f}%", disk_status_color, "Root filesystem"
        )

        # Network Row
        network = analysis["network"]
        table.add_row(
            "Network",
            "N/A",
            "[green]OK[/green]",
            f"RX: {network['receive_mbps']:.2f} Mbps, TX: {network['transmit_mbps']:.2f} Mbps",
        )

        console.print(table)

        # Overall Status
        critical_count = sum(
            1 for comp in analysis.values() if comp.get("status") == "CRITICAL"
        )
        warning_count = sum(
            1 for comp in analysis.values() if comp.get("status") == "WARNING"
        )

        if critical_count > 0:
            overall_status = "[red]CRITICAL[/red]"
        elif warning_count > 0:
            overall_status = "[yellow]WARNING[/yellow]"
        else:
            overall_status = "[green]HEALTHY[/green]"

        status_panel = Panel(
            f"Overall Status: {overall_status}\n"
            f"Components: {critical_count} critical, {warning_count} warning",
            title="🎯 System Health",
            border_style="green" if critical_count == 0 else "red",
        )
        console.print(status_panel)

    def run_test(self):
        """Executa teste completo."""
        console.print(
            Panel.fit(
                "[bold blue]Prometheus Remote Performance Test[/bold blue]\n"
                f"Server: {self.prometheus_url}",
                border_style="blue",
            )
        )

        # Test connection
        console.print("[blue]🔍[/blue] Testing connection...")
        health = self.query("up")
        if not health or health.get("status") != "success":
            console.print("[red]❌[/red] Failed to connect to Prometheus")
            return False

        console.print("[green]✅[/green] Connected to Prometheus")

        # Collect metrics
        metrics = self.get_basic_metrics()

        # Analyze
        analysis = self.analyze_use_method(metrics)

        # Display results
        self.display_results(metrics, analysis)

        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "prometheus_url": self.prometheus_url,
            "metrics": metrics,
            "analysis": analysis,
        }

        with open("prometheus_remote_test.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        console.print(
            f"\n[green]✅[/green] Results saved to prometheus_remote_test.json"
        )
        return True


def main():
    """Função principal."""
    tester = PrometheusRemoteTest()
    success = tester.run_test()

    if not success:
        exit(1)


if __name__ == "__main__":
    main()
