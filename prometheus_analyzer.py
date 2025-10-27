#!/usr/bin/env python3
"""
Prometheus Remote Performance Analysis

Coleta remota de métricas usando Prometheus + Node Exporter
e análise local com USE Method de Brendan Gregg.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import requests
import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

import requests
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()


class PrometheusCollector:
    """Coletor de métricas do Prometheus."""

    def __init__(self, prometheus_url: str, scrape_interval: int = 300):
        """
        Inicializa coletor Prometheus.

        Args:
            prometheus_url: URL do servidor Prometheus (ex: http://localhost:9090)
            scrape_interval: Intervalo de coleta em segundos (padrão: 5 minutos)
        """
        self.prometheus_url = prometheus_url.rstrip("/")
        self.scrape_interval = scrape_interval
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def query_metric(self, query: str, time_range: str = "5m") -> Dict[str, Any]:
        """
        Executa query no Prometheus.

        Args:
            query: Query PromQL
            time_range: Range temporal (ex: 5m, 15m, 1h)

        Returns:
            Resultado da query
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=int(time_range[:-1]))

            params = {
                "query": query,
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "step": f"{self.scrape_interval}s",
            }

            response = self.session.get(
                f"{self.prometheus_url}/api/v1/query_range", params=params, timeout=30
            )
            response.raise_for_status()

            data = response.json()
            if data["status"] != "success":
                raise ValueError(f"Prometheus query failed: {data}")

            return data["data"]

        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return {}

    def get_cpu_metrics(self) -> Dict[str, Any]:
        """Coleta métricas de CPU."""
        queries = {
            "cpu_utilization": '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
            "load_1m": "node_load1",
            "load_5m": "node_load5",
            "load_15m": "node_load15",
            "cpu_count": 'count by (instance) (node_cpu_seconds_total{mode="idle"})',
        }

        metrics = {}
        for name, query in queries.items():
            result = self.query_metric(query)
            if result.get("result"):
                # Pega o valor mais recente
                latest_value = result["result"][0]["values"][-1][1]
                metrics[name] = float(latest_value)

        return metrics

    def get_memory_metrics(self) -> Dict[str, Any]:
        """Coleta métricas de memória."""
        queries = {
            "memory_total": "node_memory_MemTotal_bytes",
            "memory_available": "node_memory_MemAvailable_bytes",
            "memory_used": "node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes",
            "swap_total": "node_memory_SwapTotal_bytes",
            "swap_used": "node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes",
        }

        metrics = {}
        for name, query in queries.items():
            result = self.query_metric(query)
            if result.get("result"):
                latest_value = result["result"][0]["values"][-1][1]
                metrics[name] = float(latest_value)

        # Calcula percentuais
        if "memory_total" in metrics and "memory_used" in metrics:
            metrics["memory_utilization"] = (
                metrics["memory_used"] / metrics["memory_total"]
            ) * 100

        if (
            "swap_total" in metrics
            and "swap_used" in metrics
            and metrics["swap_total"] > 0
        ):
            metrics["swap_utilization"] = (
                metrics["swap_used"] / metrics["swap_total"]
            ) * 100

        return metrics

    def get_disk_metrics(self) -> Dict[str, Any]:
        """Coleta métricas de disco."""
        queries = {
            "disk_read_bytes": "irate(node_disk_read_bytes_total[5m])",
            "disk_write_bytes": "irate(node_disk_write_bytes_total[5m])",
            "disk_read_ops": "irate(node_disk_reads_completed_total[5m])",
            "disk_write_ops": "irate(node_disk_writes_completed_total[5m])",
            "disk_utilization": "100 - (avg by (instance) (irate(node_disk_io_time_seconds_total[5m])) * 100)",
        }

        metrics = {}
        for name, query in queries.items():
            result = self.query_metric(query)
            if result.get("result"):
                # Soma valores de todos os discos
                total_value = sum(
                    float(values[-1][1])
                    for values in [r["values"] for r in result["result"]]
                )
                metrics[name] = total_value

        return metrics

    def get_network_metrics(self) -> Dict[str, Any]:
        """Coleta métricas de rede."""
        queries = {
            "network_receive_bytes": "irate(node_network_receive_bytes_total[5m])",
            "network_transmit_bytes": "irate(node_network_transmit_bytes_total[5m])",
            "network_receive_packets": "irate(node_network_receive_packets_total[5m])",
            "network_transmit_packets": "irate(node_network_transmit_packets_total[5m])",
        }

        metrics = {}
        for name, query in queries.items():
            result = self.query_metric(query)
            if result.get("result"):
                # Soma valores de todas as interfaces
                total_value = sum(
                    float(values[-1][1])
                    for values in [r["values"] for r in result["result"]]
                )
                metrics[name] = total_value

        return metrics

    def collect_all_metrics(self) -> Dict[str, Any]:
        """Coleta todas as métricas do sistema."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            console.print(
                Panel.fit(
                    "🔍 Coletando Métricas Remotas via Prometheus", style="bold blue"
                )
            )

            task = progress.add_task("Coletando métricas...", total=4)

            metrics = {}

            # CPU
            progress.update(task, description="Coletando métricas de CPU...")
            metrics["cpu"] = self.get_cpu_metrics()
            progress.advance(task)

            # Memory
            progress.update(task, description="Coletando métricas de Memória...")
            metrics["memory"] = self.get_memory_metrics()
            progress.advance(task)

            # Disk
            progress.update(task, description="Coletando métricas de Disco...")
            metrics["disk"] = self.get_disk_metrics()
            progress.advance(task)

            # Network
            progress.update(task, description="Coletando métricas de Rede...")
            metrics["network"] = self.get_network_metrics()
            progress.advance(task)

        return metrics


class USEAnalyzer:
    """Analisador baseado no USE Method adaptado para Prometheus."""

    THRESHOLDS = {
        "cpu": {"utilization": 80, "load": 2.0},
        "memory": {"utilization": 85, "swap": 50},
        "disk": {"utilization": 70, "io": 80},
        "network": {"utilization": 80},
    }

    def analyze_cpu(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa métricas de CPU."""
        cpu_util = metrics.get("cpu_utilization", 0)
        load_1m = metrics.get("load_1m", 0)
        cpu_count = metrics.get("cpu_count", 1)

        # Normaliza load average pelo número de CPUs
        load_normalized = load_1m / cpu_count if cpu_count > 0 else 0

        # Calcula scores
        util_score = min(100, (cpu_util / self.THRESHOLDS["cpu"]["utilization"]) * 100)
        load_score = min(100, (load_normalized / self.THRESHOLDS["cpu"]["load"]) * 100)

        overall_score = max(util_score, load_score)

        if overall_score >= 90:
            status = "CRITICAL"
            severity = "🚨"
        elif overall_score >= 70:
            status = "WARNING"
            severity = "⚠️"
        else:
            status = "OK"
            severity = "✅"

        recommendations = []
        if cpu_util > self.THRESHOLDS["cpu"]["utilization"]:
            recommendations.append(
                f"CPU utilization alta ({cpu_util:.1f}%). Verifique processos CPU-bound."
            )
        if load_normalized > self.THRESHOLDS["cpu"]["load"]:
            recommendations.append(
                f"Load average elevado ({load_1m:.1f}). Considere distribuição de carga."
            )

        return {
            "status": status,
            "severity": severity,
            "overall_score": overall_score,
            "utilization": cpu_util,
            "load_average": load_1m,
            "load_normalized": load_normalized,
            "cpu_count": cpu_count,
            "recommendations": recommendations,
        }

    def analyze_memory(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa métricas de memória."""
        mem_util = metrics.get("memory_utilization", 0)
        swap_util = metrics.get("swap_utilization", 0)

        # Calcula scores
        mem_score = min(
            100, (mem_util / self.THRESHOLDS["memory"]["utilization"]) * 100
        )
        swap_score = min(100, (swap_util / self.THRESHOLDS["memory"]["swap"]) * 100)

        overall_score = max(mem_score, swap_score)

        if overall_score >= 90:
            status = "CRITICAL"
            severity = "🚨"
        elif overall_score >= 70:
            status = "WARNING"
            severity = "⚠️"
        else:
            status = "OK"
            severity = "✅"

        recommendations = []
        if mem_util > self.THRESHOLDS["memory"]["utilization"]:
            recommendations.append(
                f"Memory utilization alta ({mem_util:.1f}%). Considere aumentar RAM ou otimizar aplicações."
            )
        if swap_util > self.THRESHOLDS["memory"]["swap"]:
            recommendations.append(
                f"Swap usage elevado ({swap_util:.1f}%). Indica memory pressure."
            )

        return {
            "status": status,
            "severity": severity,
            "overall_score": overall_score,
            "utilization": mem_util,
            "swap_utilization": swap_util,
            "recommendations": recommendations,
        }

    def analyze_disk(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa métricas de disco."""
        disk_read = metrics.get("disk_read_bytes", 0)
        disk_write = metrics.get("disk_write_bytes", 0)
        disk_util = metrics.get("disk_utilization", 0)

        # Calcula throughput total (MB/s)
        throughput_mbps = (disk_read + disk_write) / (1024 * 1024)

        # Calcula scores
        io_score = min(100, (throughput_mbps / 100) * 100)  # 100 MB/s como baseline
        util_score = min(
            100, (disk_util / self.THRESHOLDS["disk"]["utilization"]) * 100
        )

        overall_score = max(io_score, util_score)

        if overall_score >= 90:
            status = "CRITICAL"
            severity = "🚨"
        elif overall_score >= 70:
            status = "WARNING"
            severity = "⚠️"
        else:
            status = "OK"
            severity = "✅"

        recommendations = []
        if throughput_mbps > 50:
            recommendations.append(
                f"Alto throughput de I/O ({throughput_mbps:.1f} MB/s). Considere SSD upgrade."
            )
        if disk_util > self.THRESHOLDS["disk"]["utilization"]:
            recommendations.append(
                f"Disk utilization alta ({disk_util:.1f}%). Verifique I/O bounds."
            )

        return {
            "status": status,
            "severity": severity,
            "overall_score": overall_score,
            "throughput_mbps": throughput_mbps,
            "utilization": disk_util,
            "read_mbps": disk_read / (1024 * 1024),
            "write_mbps": disk_write / (1024 * 1024),
            "recommendations": recommendations,
        }

    def analyze_network(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa métricas de rede."""
        rx_bytes = metrics.get("network_receive_bytes", 0)
        tx_bytes = metrics.get("network_transmit_bytes", 0)

        # Calcula throughput total (Mbps)
        throughput_mbps = (rx_bytes + tx_bytes) * 8 / (1024 * 1024)

        # Calcula score (baseline de 1 Gbps)
        util_score = min(100, (throughput_mbps / 1000) * 100)

        if util_score >= 90:
            status = "CRITICAL"
            severity = "🚨"
        elif util_score >= 70:
            status = "WARNING"
            severity = "⚠️"
        else:
            status = "OK"
            severity = "✅"

        recommendations = []
        if throughput_mbps > 800:  # 800 Mbps
            recommendations.append(
                f"Alto throughput de rede ({throughput_mbps:.1f} Mbps). Verifique bandwidth."
            )

        return {
            "status": status,
            "severity": severity,
            "overall_score": util_score,
            "throughput_mbps": throughput_mbps,
            "receive_mbps": rx_bytes * 8 / (1024 * 1024),
            "transmit_mbps": tx_bytes * 8 / (1024 * 1024),
            "recommendations": recommendations,
        }

    def analyze_all(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa todos os componentes."""
        analysis = {}

        if "cpu" in metrics:
            analysis["cpu"] = self.analyze_cpu(metrics["cpu"])

        if "memory" in metrics:
            analysis["memory"] = self.analyze_memory(metrics["memory"])

        if "disk" in metrics:
            analysis["disk"] = self.analyze_disk(metrics["disk"])

        if "network" in metrics:
            analysis["network"] = self.analyze_network(metrics["network"])

        return analysis


class PrometheusAnalyzer:
    """Analisador principal que integra Prometheus e USE Method."""

    def __init__(self, prometheus_url: str):
        """
        Inicializa analisador.

        Args:
            prometheus_url: URL do servidor Prometheus
        """
        self.collector = PrometheusCollector(prometheus_url)
        self.analyzer = USEAnalyzer()

    def run_analysis(self) -> Dict[str, Any]:
        """Executa análise completa."""
        start_time = time.time()

        # Coleta métricas
        metrics = self.collector.collect_all_metrics()

        # Analisa com USE Method
        analysis = self.analyzer.analyze_all(metrics)

        # Gera recomendações consolidadas
        all_recommendations = []
        critical_issues = []
        warning_issues = []

        for component, result in analysis.items():
            if result["status"] == "CRITICAL":
                critical_issues.append(
                    f"{result['severity']} {component.title()}: {result['recommendations'][0] if result['recommendations'] else 'Critical issue detected'}"
                )
            elif result["status"] == "WARNING":
                warning_issues.append(
                    f"{result['severity']} {component.title()}: {result['recommendations'][0] if result['recommendations'] else 'Warning detected'}"
                )

            all_recommendations.extend(result["recommendations"])

        # Calcula score geral
        scores = [result["overall_score"] for result in analysis.values()]
        overall_score = sum(scores) / len(scores) if scores else 0

        # Determina status geral
        if overall_score >= 80:
            overall_status = "CRITICAL"
            overall_severity = "🚨"
        elif overall_score >= 60:
            overall_status = "WARNING"
            overall_severity = "⚠️"
        else:
            overall_status = "HEALTHY"
            overall_severity = "✅"

        analysis_time = time.time() - start_time

        return {
            "timestamp": datetime.now().isoformat(),
            "prometheus_url": self.collector.prometheus_url,
            "scrape_interval": self.collector.scrape_interval,
            "analysis_time_seconds": round(analysis_time, 2),
            "metrics": metrics,
            "analysis": analysis,
            "overall_score": round(overall_score, 1),
            "overall_status": overall_status,
            "overall_severity": overall_severity,
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "all_recommendations": list(set(all_recommendations)),  # Remove duplicatas
        }

    def display_results(self, results: Dict[str, Any]):
        """Exibe resultados formatados."""
        console.print("\n")

        # Header
        console.print(
            Panel.fit(
                f"📊 Análise de Performance Remota\n"
                f"Prometheus: {results['prometheus_url']}\n"
                f"Data/Hora: {results['timestamp']}\n"
                f"Tempo de Análise: {results['analysis_time_seconds']}s",
                style="bold blue",
            )
        )

        # Status Geral
        console.print("\n")
        status_table = Table(title="🎯 Status Geral do Sistema")
        status_table.add_column("Métrica", style="cyan")
        status_table.add_column("Valor", style="magenta")
        status_table.add_column("Status", style="bold")

        status_table.add_row(
            "Score Geral",
            f"{results['overall_score']}%",
            f"{results['overall_severity']} {results['overall_status']}",
        )

        console.print(status_table)

        # Análise por Componente
        console.print("\n")
        component_table = Table(title="🔍 Análise por Componente (USE Method)")
        component_table.add_column("Componente", style="cyan")
        component_table.add_column("Score", style="magenta")
        component_table.add_column("Status", style="bold")
        component_table.add_column("Métricas Principais", style="white")

        for component, analysis in results["analysis"].items():
            metrics_str = ""
            if component == "cpu":
                metrics_str = f"CPU: {analysis['utilization']:.1f}% | Load: {analysis['load_average']:.1f}"
            elif component == "memory":
                metrics_str = f"Mem: {analysis['utilization']:.1f}% | Swap: {analysis.get('swap_utilization', 0):.1f}%"
            elif component == "disk":
                metrics_str = f"I/O: {analysis['throughput_mbps']:.1f} MB/s | Util: {analysis.get('utilization', 0):.1f}%"
            elif component == "network":
                metrics_str = f"Throughput: {analysis['throughput_mbps']:.1f} Mbps"

            component_table.add_row(
                component.title(),
                f"{analysis['overall_score']:.1f}%",
                f"{analysis['severity']} {analysis['status']}",
                metrics_str,
            )

        console.print(component_table)

        # Issues Críticos
        if results["critical_issues"]:
            console.print("\n")
            console.print(
                Panel(
                    "\n".join(results["critical_issues"]),
                    title="🚨 Issues Críticos",
                    border_style="red",
                )
            )

        # Warnings
        if results["warning_issues"]:
            console.print("\n")
            console.print(
                Panel(
                    "\n".join(results["warning_issues"]),
                    title="⚠️ Warnings",
                    border_style="yellow",
                )
            )

        # Recomendações
        if results["all_recommendations"]:
            console.print("\n")
            rec_table = Table(title="📋 Recomendações de Otimização")
            rec_table.add_column("Prioridade", style="cyan")
            rec_table.add_column("Recomendação", style="white")

            for i, rec in enumerate(results["all_recommendations"][:10], 1):
                priority = "Alta" if i <= 3 else "Média" if i <= 6 else "Baixa"
                rec_table.add_row(priority, rec)

            console.print(rec_table)

    def save_results(self, results: Dict[str, Any], filename: Optional[str] = None):
        """Salva resultados em arquivo JSON."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prometheus_analysis_{timestamp}.json"

        output_path = Path(filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        console.print(f"\n✅ Resultados salvos em: {output_path.absolute()}")
        return output_path


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Análise de Performance Remota com Prometheus"
    )
    parser.add_argument(
        "--prometheus-url",
        default="http://localhost:9090",
        help="URL do servidor Prometheus",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Intervalo de coleta em segundos (padrão: 300)",
    )
    parser.add_argument("--output", help="Arquivo de saída JSON")
    parser.add_argument(
        "--continuous", action="store_true", help="Executa análise contínua"
    )
    parser.add_argument(
        "--daemon", action="store_true", help="Modo daemon (executa a cada 5 minutos)"
    )

    args = parser.parse_args()

    analyzer = PrometheusAnalyzer(args.prometheus_url)

    if args.daemon:
        console.print(Panel.fit("🔄 Modo Daemon Ativo", style="bold green"))
        console.print("⏰ Análise será executada a cada 5 minutos")
        console.print("Pressione Ctrl+C para parar\n")

        try:
            while True:
                results = analyzer.run_analysis()
                analyzer.display_results(results)

                if args.output:
                    analyzer.save_results(results, args.output)

                console.print("\n" + "=" * 60 + "\n")
                time.sleep(args.interval)

        except KeyboardInterrupt:
            console.print("\n🛑 Daemon interrompido pelo usuário")

    elif args.continuous:
        console.print(Panel.fit("🔄 Análise Contínua", style="bold green"))

        try:
            while True:
                results = analyzer.run_analysis()
                analyzer.display_results(results)
                time.sleep(30)  # Atualiza a cada 30 segundos

        except KeyboardInterrupt:
            console.print("\n🛑 Análise contínua interrompida")

    else:
        # Análise única
        results = analyzer.run_analysis()
        analyzer.display_results(results)

        if args.output:
            analyzer.save_results(results, args.output)


if __name__ == "__main__":
    main()
