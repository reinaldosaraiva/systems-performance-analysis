"""
Analisador de Performance Local com USE Method
Versão simplificada para demonstração da metodologia
"""

import json
import time
import psutil
import socket
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class LocalSystemCollector:
    """Coletor de métricas do sistema local."""

    def get_cpu_metrics(self) -> Dict[str, Any]:
        """Coleta métricas de CPU."""
        cpu_percent = psutil.cpu_percent(interval=1)

        # Load averages
        try:
            load_avg = psutil.getloadavg()
            load_1m, load_5m, load_15m = load_avg
        except AttributeError:
            load_1m = load_5m = load_15m = 0

        cpu_count = psutil.cpu_count(logical=True)

        return {
            "utilization": cpu_percent,
            "load_1m": load_1m,
            "load_5m": load_5m,
            "load_15m": load_15m,
            "cpu_count": cpu_count,
        }

    def get_memory_metrics(self) -> Dict[str, Any]:
        """Coleta métricas de memória."""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "utilization": memory.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_utilization": swap.percent,
        }

    def get_disk_metrics(self) -> Dict[str, Any]:
        """Coleta métricas de disco."""
        disk_io = psutil.disk_io_counters()
        disk_usage = psutil.disk_usage("/")

        # Calcula throughput (bytes/segundo)
        read_throughput = disk_io.read_bytes if hasattr(disk_io, "read_bytes") else 0
        write_throughput = disk_io.write_bytes if hasattr(disk_io, "write_bytes") else 0

        return {
            "total": disk_usage.total,
            "used": disk_usage.used,
            "free": disk_usage.free,
            "utilization": (disk_usage.used / disk_usage.total) * 100,
            "read_bytes": read_throughput,
            "write_bytes": write_throughput,
            "read_throughput_mbps": (read_throughput / (1024 * 1024)),
            "write_throughput_mbps": (write_throughput / (1024 * 1024)),
        }

    def get_network_metrics(self) -> Dict[str, Any]:
        """Coleta métricas de rede."""
        net_io = psutil.net_io_counters()

        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "throughput_mbps": ((net_io.bytes_sent + net_io.bytes_recv) * 8)
            / (1024 * 1024),
        }

    def collect_all(self) -> Dict[str, Any]:
        """Coleta todas as métricas."""
        return {
            "cpu": self.get_cpu_metrics(),
            "memory": self.get_memory_metrics(),
            "disk": self.get_disk_metrics(),
            "network": self.get_network_metrics(),
            "hostname": socket.gethostname(),
            "timestamp": datetime.now().isoformat(),
        }


class USEAnalyzer:
    """Analisador baseado no USE Method de Brendan Gregg."""

    THRESHOLDS = {
        "cpu": {"utilization": 80, "load": 2.0},
        "memory": {"utilization": 85, "swap": 50},
        "disk": {"utilization": 70, "io": 80},
        "network": {"utilization": 80},
    }

    def analyze_cpu(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa métricas de CPU."""
        cpu_util = metrics.get("utilization", 0)
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
        mem_util = metrics.get("utilization", 0)
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
        disk_util = metrics.get("utilization", 0)
        read_mbps = metrics.get("read_throughput_mbps", 0)
        write_mbps = metrics.get("write_throughput_mbps", 0)

        # Calcula throughput total
        throughput_mbps = read_mbps + write_mbps

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
            "read_mbps": read_mbps,
            "write_mbps": write_mbps,
            "recommendations": recommendations,
        }

    def analyze_network(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa métricas de rede."""
        throughput_mbps = metrics.get("throughput_mbps", 0)

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


class SystemAnalyzer:
    """Analisador principal de sistemas."""

    def __init__(self):
        """Inicializa analisador."""
        self.collector = LocalSystemCollector()
        self.analyzer = USEAnalyzer()

    def run_analysis(self) -> Dict[str, Any]:
        """Executa análise completa."""
        start_time = time.time()

        # Coleta métricas
        metrics = self.collector.collect_all()

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
            "timestamp": metrics["timestamp"],
            "hostname": metrics["hostname"],
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
                f"📊 Análise de Performance Local (USE Method)\n"
                f"Host: {results['hostname']}\n"
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
            filename = f"system_analysis_{timestamp}.json"

        output_path = Path(filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        console.print(f"\n✅ Resultados salvos em: {output_path.absolute()}")
        return output_path


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Análise de Performance Local com USE Method"
    )
    parser.add_argument("--output", help="Arquivo de saída JSON")
    parser.add_argument(
        "--continuous", action="store_true", help="Executa análise contínua"
    )
    parser.add_argument(
        "--daemon", action="store_true", help="Modo daemon (executa a cada 5 minutos)"
    )

    args = parser.parse_args()

    analyzer = SystemAnalyzer()

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
                time.sleep(300)  # 5 minutos

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
