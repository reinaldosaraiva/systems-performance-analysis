"""
Report Generation Module

Geração de relatórios HTML/Markdown com gráficos matplotlib e recomendações.
Seguindo padrões de context engineering e persona do Reinaldo Saraiva.
"""

import logging
import base64
from io import BytesIO
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from jinja2 import Template

from analyzers import USEScore, Status

logger = logging.getLogger(__name__)

# Optional imports for plotting
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    import pandas as pd

    HAS_PLOTTING = True
except ImportError as e:
    HAS_PLOTTING = False
    logger.warning(f"Plotting libraries not available: {e}")


class ReportGenerator:
    """Gerador de relatórios de performance com gráficos e recomendações."""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Inicializa o gerador de relatórios.

        Args:
            template_dir: Diretório com templates customizados
        """
        self.template_dir = (
            template_dir or Path(__file__).parent.parent / "reports" / "templates"
        )

        # Configurar matplotlib para estilo profissional
        if HAS_PLOTTING:
            plt.style.use("seaborn-v0_8")
            plt.rcParams["figure.figsize"] = (12, 8)
            plt.rcParams["font.size"] = 10
            plt.rcParams["axes.titlesize"] = 14
            plt.rcParams["axes.labelsize"] = 12

    def generate_html_report(
        self,
        use_scores: Dict[str, USEScore],
        latency_analysis: Optional[Dict[str, Any]] = None,
        system_metrics: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Gera relatório HTML completo com gráficos.

        Args:
            use_scores: Scores USE Method por componente
            latency_analysis: Análise de latência (opcional)
            system_metrics: Métricas brutas do sistema (opcional)

        Returns:
            HTML do relatório
        """
        logger.info("Generating HTML report")

        try:
            # Gerar gráficos
            charts = self._generate_charts(use_scores, latency_analysis, system_metrics)

            # Compilar dados do relatório
            report_data = {
                "title": "Systems Performance Analysis Report",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "author": "Reinaldo Saraiva - Arquiteto Sênior de Infra em Nuvem",
                "summary": self._generate_summary(use_scores, latency_analysis),
                "use_scores": self._format_use_scores(use_scores),
                "latency_analysis": latency_analysis,
                "system_metrics": self._format_system_metrics(system_metrics),
                "charts": charts,
                "recommendations": self._compile_recommendations(
                    use_scores, latency_analysis
                ),
                "performance_trends": self._generate_performance_trends(use_scores),
            }

            # Renderizar HTML
            html_content = self._render_html_template(report_data)

            logger.info("HTML report generated successfully")
            return html_content

        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            return (
                f"<html><body><h1>Error generating report</h1><p>{e}</p></body></html>"
            )

    def generate_markdown_report(
        self,
        use_scores: Dict[str, USEScore],
        latency_analysis: Optional[Dict[str, Any]] = None,
        system_metrics: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Gera relatório em Markdown.

        Args:
            use_scores: Scores USE Method por componente
            latency_analysis: Análise de latência (opcional)
            system_metrics: Métricas brutas do sistema (opcional)

        Returns:
            Markdown do relatório
        """
        logger.info("Generating Markdown report")

        try:
            md_content = []

            # Header
            md_content.append("# Systems Performance Analysis Report")
            md_content.append(
                f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            md_content.append(
                f"**Author**: Reinaldo Saraiva - Arquiteto Sênior de Infra em Nuvem"
            )
            md_content.append("")

            # Executive Summary
            md_content.append("## 📊 Executive Summary")
            summary = self._generate_summary(use_scores, latency_analysis)
            md_content.append(summary)
            md_content.append("")

            # USE Method Analysis
            md_content.append("## 🔍 USE Method Analysis")
            md_content.append("")

            for component, score in use_scores.items():
                md_content.append(f"### {component.upper()}")
                md_content.append(f"- **Status**: {score.status.value}")
                md_content.append(f"- **Overall Score**: {score.overall_score:.1f}%")
                md_content.append(f"- **Utilization**: {score.utilization:.1f}%")
                md_content.append(f"- **Saturation**: {score.saturation:.1f}%")
                md_content.append(f"- **Errors**: {score.errors:.1f}%")
                md_content.append("")

                if score.recommendations:
                    md_content.append("**Recommendations**:")
                    for rec in score.recommendations:
                        md_content.append(f"- {rec}")
                    md_content.append("")

            # Latency Analysis
            if latency_analysis and "error" not in latency_analysis:
                md_content.append("## ⏱️ Latency Analysis")
                md_content.append("")

                stats = latency_analysis.get("statistics", {})
                percentiles = latency_analysis.get("percentiles", {})

                md_content.append("### Statistics")
                md_content.append(f"- **Mean**: {stats.get('mean', 0):.2f} ms")
                md_content.append(f"- **Median**: {stats.get('median', 0):.2f} ms")
                md_content.append(f"- **Std Dev**: {stats.get('std', 0):.2f} ms")
                md_content.append(
                    f"- **Range**: {stats.get('min', 0):.2f} - {stats.get('max', 0):.2f} ms"
                )
                md_content.append("")

                md_content.append("### Percentiles")
                for p, value in percentiles.items():
                    md_content.append(f"- **{p.upper()}**: {value:.2f} ms")
                md_content.append("")

                perf_class = latency_analysis.get("performance_class", "UNKNOWN")
                md_content.append(f"**Performance Class**: {perf_class}")
                md_content.append("")

                if latency_analysis.get("recommendations"):
                    md_content.append("**Recommendations**:")
                    for rec in latency_analysis["recommendations"]:
                        md_content.append(f"- {rec}")
                    md_content.append("")

            # System Metrics
            if system_metrics:
                md_content.append("## 📈 System Metrics")
                md_content.append("")
                formatted_metrics = self._format_system_metrics(system_metrics)
                for component, metrics in formatted_metrics.items():
                    md_content.append(f"### {component.upper()}")
                    for key, value in metrics.items():
                        md_content.append(f"- **{key}**: {value}")
                    md_content.append("")

            # Overall Recommendations
            md_content.append("## 🎯 Overall Recommendations")
            all_recommendations = self._compile_recommendations(
                use_scores, latency_analysis
            )
            for rec in all_recommendations:
                md_content.append(f"- {rec}")
            md_content.append("")

            # Footer
            md_content.append("---")
            md_content.append("*Generated by Systems Performance Analysis Tool*")
            md_content.append("*Based on Brendan Gregg's USE Methodology*")
            md_content.append("")
            md_content.append("#Performance #SystemsEngineering #DevOps")

            return "\n".join(md_content)

        except Exception as e:
            logger.error(f"Failed to generate Markdown report: {e}")
            return f"# Error\n\nFailed to generate report: {e}"

    def _generate_charts(
        self,
        use_scores: Dict[str, USEScore],
        latency_analysis: Optional[Dict[str, Any]] = None,
        system_metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Gera gráficos em base64 para embed no HTML."""
        charts = {}

        try:
            # USE Method Scores Chart
            charts["use_scores"] = self._create_use_scores_chart(use_scores)

            # Latency Distribution Chart
            if latency_analysis and "error" not in latency_analysis:
                charts["latency_histogram"] = self._create_latency_histogram(
                    latency_analysis
                )
                charts["latency_percentiles"] = self._create_latency_percentiles_chart(
                    latency_analysis
                )

            # System Metrics Charts
            if system_metrics:
                charts["system_overview"] = self._create_system_overview_chart(
                    system_metrics
                )

        except Exception as e:
            logger.error(f"Failed to generate charts: {e}")

        return charts

    def _create_use_scores_chart(self, use_scores: Dict[str, USEScore]) -> str:
        """Cria gráfico de barras para USE scores."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        components = list(use_scores.keys())
        utilization = [score.utilization for score in use_scores.values()]
        saturation = [score.saturation for score in use_scores.values()]
        errors = [score.errors for score in use_scores.values()]

        # Gráfico de barras agrupadas
        x = np.arange(len(components))
        width = 0.25

        ax1.bar(x - width, utilization, width, label="Utilization", color="#2E86AB")
        ax1.bar(x, saturation, width, label="Saturation", color="#A23B72")
        ax1.bar(x + width, errors, width, label="Errors", color="#F18F01")

        ax1.set_xlabel("Components")
        ax1.set_ylabel("Score (%)")
        ax1.set_title("USE Method Scores by Component")
        ax1.set_xticks(x)
        ax1.set_xticklabels(components, rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Gráfico de pizza para status
        status_counts = {status.value: 0 for status in Status}
        for score in use_scores.values():
            status_counts[score.status.value] += 1

        colors = {"OK": "#4CAF50", "WARNING": "#FF9800", "CRITICAL": "#F44336"}
        labels = [k for k, v in status_counts.items() if v > 0]
        sizes = [v for k, v in status_counts.items() if v > 0]
        chart_colors = [colors.get(label, "#9E9E9E") for label in labels]

        if sizes:
            ax2.pie(
                sizes,
                labels=labels,
                colors=chart_colors,
                autopct="%1.1f%%",
                startangle=90,
            )
            ax2.set_title("Component Status Distribution")
        else:
            ax2.text(
                0.5, 0.5, "No Data", ha="center", va="center", transform=ax2.transAxes
            )
            ax2.set_title("Component Status Distribution")

        plt.tight_layout()

        # Converter para base64
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"

    def _create_latency_histogram(self, latency_analysis: Dict[str, Any]) -> str:
        """Cria histograma de latência."""
        fig, ax = plt.subplots(figsize=(12, 6))

        heatmap_data = latency_analysis.get("heatmap", {})
        if "histogram" in heatmap_data and "bin_edges" in heatmap_data:
            hist = np.array(heatmap_data["histogram"])
            bin_edges = np.array(heatmap_data["bin_edges"])

            # Criar barras do histograma
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            bars = ax.bar(
                bin_centers,
                hist,
                width=np.diff(bin_edges),
                alpha=0.7,
                color="#2E86AB",
                edgecolor="black",
            )

            # Adicionar linhas de percentis
            percentiles = latency_analysis.get("percentiles", {})
            colors = {"p50": "green", "p90": "orange", "p95": "red", "p99": "purple"}

            for p_name, color in colors.items():
                if p_name in percentiles:
                    ax.axvline(
                        percentiles[p_name],
                        color=color,
                        linestyle="--",
                        linewidth=2,
                        label=f"{p_name.upper()}: {percentiles[p_name]:.2f}ms",
                    )

            ax.set_xlabel("Latency (ms)")
            ax.set_ylabel("Frequency")
            ax.set_title("Latency Distribution with Percentiles")
            ax.legend()
            ax.grid(True, alpha=0.3)
        else:
            ax.text(
                0.5,
                0.5,
                "No latency data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title("Latency Distribution")

        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"

    def _create_latency_percentiles_chart(
        self, latency_analysis: Dict[str, Any]
    ) -> str:
        """Cria gráfico de percentis de latência."""
        fig, ax = plt.subplots(figsize=(10, 6))

        percentiles = latency_analysis.get("percentiles", {})
        if percentiles:
            p_names = list(percentiles.keys())
            p_values = list(percentiles.values())

            colors = [
                "#4CAF50" if v < 50 else "#FF9800" if v < 200 else "#F44336"
                for v in p_values
            ]

            bars = ax.bar(p_names, p_values, color=colors, alpha=0.7, edgecolor="black")

            # Adicionar valores nas barras
            for bar, value in zip(bars, p_values):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + height * 0.01,
                    f"{value:.2f}ms",
                    ha="center",
                    va="bottom",
                )

            ax.set_xlabel("Percentile")
            ax.set_ylabel("Latency (ms)")
            ax.set_title("Latency Percentiles")
            ax.grid(True, alpha=0.3, axis="y")

            # Adicionar linha de referência
            ax.axhline(
                y=100, color="red", linestyle="--", alpha=0.5, label="100ms threshold"
            )
            ax.legend()
        else:
            ax.text(
                0.5,
                0.5,
                "No percentile data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title("Latency Percentiles")

        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"

    def _create_system_overview_chart(self, system_metrics: Dict[str, Any]) -> str:
        """Cria gráfico de overview das métricas do sistema."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        # CPU
        if "cpu" in system_metrics:
            cpu_util = system_metrics["cpu"].get("utilization", 0)
            cpu_sat = system_metrics["cpu"].get("saturation", 0)

            ax1.bar(
                ["Utilization", "Saturation"],
                [cpu_util, cpu_sat],
                color=["#2E86AB", "#A23B72"],
                alpha=0.7,
            )
            ax1.set_ylabel("Percentage (%)")
            ax1.set_title("CPU Metrics")
            ax1.set_ylim(0, 100)
            ax1.grid(True, alpha=0.3, axis="y")

        # Memory
        if "memory" in system_metrics:
            mem_util = system_metrics["memory"].get("utilization", 0)
            mem_swap = system_metrics["memory"].get("swap_utilization", 0)

            ax2.bar(
                ["Memory Util", "Swap Util"],
                [mem_util, mem_swap],
                color=["#2E86AB", "#F18F01"],
                alpha=0.7,
            )
            ax2.set_ylabel("Percentage (%)")
            ax2.set_title("Memory Metrics")
            ax2.set_ylim(0, 100)
            ax2.grid(True, alpha=0.3, axis="y")

        # Disk
        if "disk" in system_metrics:
            disk_util = system_metrics["disk"].get("total_utilization", 0)
            disk_sat = system_metrics["disk"].get("saturation", 0)

            ax3.bar(
                ["Disk Util", "I/O Sat"],
                [disk_util, disk_sat],
                color=["#2E86AB", "#A23B72"],
                alpha=0.7,
            )
            ax3.set_ylabel("Percentage (%)")
            ax3.set_title("Disk Metrics")
            ax3.set_ylim(0, 100)
            ax3.grid(True, alpha=0.3, axis="y")

        # Network
        if "network" in system_metrics:
            net_err = system_metrics["network"].get("errors", 0)
            net_sat = system_metrics["network"].get("saturation", 0)

            ax4.bar(
                ["Error Rate", "Saturation"],
                [net_err, net_sat],
                color=["#F44336", "#A23B72"],
                alpha=0.7,
            )
            ax4.set_ylabel("Percentage (%)")
            ax4.set_title("Network Metrics")
            ax4.set_ylim(0, 100)
            ax4.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"

    def _generate_summary(
        self,
        use_scores: Dict[str, USEScore],
        latency_analysis: Optional[Dict[str, Any]],
    ) -> str:
        """Gera resumo executivo."""
        total_components = len(use_scores)
        critical_count = sum(
            1 for s in use_scores.values() if s.status == Status.CRITICAL
        )
        warning_count = sum(
            1 for s in use_scores.values() if s.status == Status.WARNING
        )
        ok_count = sum(1 for s in use_scores.values() if s.status == Status.OK)

        avg_score = (
            sum(s.overall_score for s in use_scores.values()) / total_components
            if total_components > 0
            else 0
        )

        summary = []
        summary.append(f"Análise de {total_components} componentes do sistema:")
        summary.append(
            f"- **Status Geral**: {critical_count} CRÍTICO, {warning_count} AVISO, {ok_count} OK"
        )
        summary.append(f"- **Score Médio**: {avg_score:.1f}%")

        if latency_analysis and "error" not in latency_analysis:
            perf_class = latency_analysis.get("performance_class", "UNKNOWN")
            p95 = latency_analysis.get("percentiles", {}).get("p95", 0)
            summary.append(
                f"- **Performance de Latência**: {perf_class} (P95: {p95:.2f}ms)"
            )

        if critical_count > 0:
            summary.append(
                "⚠️ **AÇÃO IMEDIATA REQUERIDA**: Componentes críticos detectados!"
            )
        elif warning_count > 0:
            summary.append(
                "🔍 **MONITORAMENTO RECOMENDADO**: Componentes em aviso detectados."
            )
        else:
            summary.append(
                "✅ **SISTEMA SAUDÁVEL**: Todos os componentes operando normalmente."
            )

        return " ".join(summary)

    def _format_use_scores(
        self, use_scores: Dict[str, USEScore]
    ) -> Dict[str, Dict[str, Any]]:
        """Formata USE scores para exibição."""
        formatted = {}
        for component, score in use_scores.items():
            formatted[component] = {
                "status": score.status.value,
                "overall_score": f"{score.overall_score:.1f}%",
                "utilization": f"{score.utilization:.1f}%",
                "saturation": f"{score.saturation:.1f}%",
                "errors": f"{score.errors:.1f}%",
                "recommendations": score.recommendations,
            }
        return formatted

    def _format_system_metrics(
        self, system_metrics: Optional[Dict[str, Any]]
    ) -> Dict[str, Dict[str, str]]:
        """Formata métricas do sistema para exibição."""
        if not system_metrics:
            return {}

        formatted = {}
        for component, metrics in system_metrics.items():
            if "error" in metrics:
                formatted[component] = {"error": metrics["error"]}
                continue

            comp_formatted = {}
            for key, value in metrics.items():
                if key == "unit":
                    continue

                unit = metrics.get("unit", {}).get(key, "")
                if isinstance(value, float):
                    if unit == "%":
                        comp_formatted[key.replace("_", " ").title()] = f"{value:.1f}%"
                    elif unit == "bytes":
                        comp_formatted[key.replace("_", " ").title()] = (
                            self._format_bytes(int(value))
                        )
                    elif unit == "seconds":
                        comp_formatted[key.replace("_", " ").title()] = f"{value:.2f}s"
                    else:
                        comp_formatted[key.replace("_", " ").title()] = f"{value:.2f}"
                else:
                    comp_formatted[key.replace("_", " ").title()] = str(value)

            formatted[component] = comp_formatted

        return formatted

    def _format_bytes(self, bytes_value: int) -> str:
        """Formata bytes para unidade legível."""
        value = float(bytes_value)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024.0:
                return f"{value:.1f} {unit}"
            value /= 1024.0
        return f"{value:.1f} PB"

    def _compile_recommendations(
        self,
        use_scores: Dict[str, USEScore],
        latency_analysis: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Compila todas as recomendações."""
        all_recommendations = []

        # Recomendações USE Method
        for component, score in use_scores.items():
            if score.recommendations:
                all_recommendations.extend(score.recommendations)

        # Recomendações de latência
        if latency_analysis and latency_analysis.get("recommendations"):
            all_recommendations.extend(latency_analysis["recommendations"])

        # Remover duplicatas mantendo ordem
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        return unique_recommendations

    def _generate_performance_trends(
        self, use_scores: Dict[str, USEScore]
    ) -> Dict[str, str]:
        """Gera análise de tendências (placeholder para implementação futura)."""
        trends = {}
        for component, score in use_scores.items():
            if score.status == Status.CRITICAL:
                trends[component] = "📉 Piora detectada - ação imediata necessária"
            elif score.status == Status.WARNING:
                trends[component] = "📊 Monitorar tendência - possível degradação"
            else:
                trends[component] = "📈 Estável - performance adequada"
        return trends

    def _render_html_template(self, report_data: Dict[str, Any]) -> str:
        """Renderiza template HTML com os dados do relatório."""
        # Template HTML inline (poderia ser arquivo separado)
        html_template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; border-bottom: 2px solid #2E86AB; padding-bottom: 20px; margin-bottom: 30px; }
        .summary { background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .section { margin-bottom: 30px; }
        .chart { text-align: center; margin: 20px 0; }
        .chart img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #2E86AB; }
        .status-ok { border-left-color: #4CAF50; }
        .status-warning { border-left-color: #FF9800; }
        .status-critical { border-left-color: #F44336; }
        .recommendations { background: #fff3e0; padding: 15px; border-radius: 5px; }
        .recommendations ul { margin: 0; padding-left: 20px; }
        .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #2E86AB; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <p><strong>Generated:</strong> {{ timestamp }}</p>
            <p><strong>Author:</strong> {{ author }}</p>
        </div>
        
        <div class="section">
            <h2>📊 Executive Summary</h2>
            <div class="summary">
                <p>{{ summary }}</p>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Performance Charts</h2>
            {% if charts.use_scores %}
            <div class="chart">
                <h3>USE Method Analysis</h3>
                <img src="{{ charts.use_scores }}" alt="USE Scores Chart">
            </div>
            {% endif %}
            
            {% if charts.latency_histogram %}
            <div class="chart">
                <h3>Latency Distribution</h3>
                <img src="{{ charts.latency_histogram }}" alt="Latency Histogram">
            </div>
            {% endif %}
            
            {% if charts.system_overview %}
            <div class="chart">
                <h3>System Metrics Overview</h3>
                <img src="{{ charts.system_overview }}" alt="System Overview">
            </div>
            {% endif %}
        </div>
        
        <div class="section">
            <h2>🔍 Component Analysis</h2>
            <div class="metric-grid">
                {% for component, data in use_scores.items() %}
                <div class="metric-card status-{{ data.status.lower() }}">
                    <h3>{{ component.upper() }}</h3>
                    <p><strong>Status:</strong> {{ data.status }}</p>
                    <p><strong>Overall Score:</strong> {{ data.overall_score }}</p>
                    <p><strong>Utilization:</strong> {{ data.utilization }}</p>
                    <p><strong>Saturation:</strong> {{ data.saturation }}</p>
                    <p><strong>Errors:</strong> {{ data.errors }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
        
        {% if latency_analysis and latency_analysis.statistics %}
        <div class="section">
            <h2>⏱️ Latency Analysis</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr><td>Mean</td><td>{{ "%.2f"|format(latency_analysis.statistics.mean) }} ms</td></tr>
                <tr><td>Median</td><td>{{ "%.2f"|format(latency_analysis.statistics.median) }} ms</td></tr>
                <tr><td>Std Dev</td><td>{{ "%.2f"|format(latency_analysis.statistics.std) }} ms</td></tr>
                <tr><td>Performance Class</td><td>{{ latency_analysis.performance_class }}</td></tr>
            </table>
            
            {% if latency_analysis.percentiles %}
            <h3>Percentiles</h3>
            <table>
                <tr>
                    <th>Percentile</th>
                    <th>Value (ms)</th>
                </tr>
                {% for p, value in latency_analysis.percentiles.items() %}
                <tr><td>{{ p.upper() }}</td><td>{{ "%.2f"|format(value) }}</td></tr>
                {% endfor %}
            </table>
            {% endif %}
        </div>
        {% endif %}
        
        <div class="section">
            <h2>🎯 Recommendations</h2>
            <div class="recommendations">
                <ul>
                    {% for rec in recommendations %}
                    <li>{{ rec }}</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Systems Performance Analysis Tool</p>
            <p>Based on Brendan Gregg's USE Methodology</p>
            <p>#Performance #SystemsEngineering #DevOps</p>
        </div>
    </div>
</body>
</html>
        """

        template = Template(html_template)
        return template.render(**report_data)
