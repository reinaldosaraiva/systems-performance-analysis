"""
Main CLI Interface for Systems Performance Analysis Tool

Interface de linha de comando com scheduler e opções de análise.
Baseado em Brendan Gregg USE Method com context engineering.
"""

import logging
import argparse
import sys
import time
import schedule
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from collectors import SystemCollector
from analyzers import USEAnalyzer, LatencyAnalyzer
from reporters import ReportGenerator

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("systems-performance.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)
console = Console()


class PerformanceAnalyzer:
    """Classe principal para análise de performance."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Inicializa o analisador de performance.

        Args:
            output_dir: Diretório para salvar relatórios
        """
        self.output_dir = output_dir or Path("reports")
        self.output_dir.mkdir(exist_ok=True)

        # Inicializar componentes
        self.collector = SystemCollector()
        self.use_analyzer = USEAnalyzer()
        self.latency_analyzer = LatencyAnalyzer()
        self.report_generator = ReportGenerator()

        console.print("[green]✅[/green] Performance Analyzer initialized")

    def run_analysis(
        self,
        components: Optional[List[str]] = None,
        include_latency: bool = False,
        format: str = "html",
    ) -> Path:
        """
        Executa análise completa de performance.

        Args:
            components: Lista de componentes para analisar
            include_latency: Incluir análise de latência
            format: Formato do relatório (html, markdown, json)

        Returns:
            Caminho do arquivo de relatório gerado
        """
        start_time = time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Coletar métricas
            task = progress.add_task("📊 Collecting system metrics...", total=None)
            try:
                metrics = self.collector.collect_all()

                # Filtrar componentes se especificado
                if components:
                    metrics = {k: v for k, v in metrics.items() if k in components}

                progress.update(task, description="✅ Metrics collected")
                console.print(
                    f"[green]✅[/green] Collected metrics for {len(metrics)} components"
                )

            except Exception as e:
                console.print(f"[red]❌[/red] Failed to collect metrics: {e}")
                raise

            # Análise USE Method
            task = progress.add_task("🔍 Running USE Method analysis...", total=None)
            try:
                use_scores = self.use_analyzer.analyze_system(metrics)
                progress.update(task, description="✅ USE analysis complete")
                console.print(
                    f"[green]✅[/green] USE analysis completed for {len(use_scores)} components"
                )

            except Exception as e:
                console.print(f"[red]❌[/red] Failed USE analysis: {e}")
                raise

            # Análise de latência (se solicitado)
            latency_analysis = None
            if include_latency:
                task = progress.add_task("⏱️ Analyzing latency...", total=None)
                try:
                    # Gerar dados de latência simulados para demonstração
                    # Em produção, estes dados viriam de medições reais
                    latency_data = self._generate_sample_latency_data()
                    latency_analysis = self.latency_analyzer.analyze_latency(
                        latency_data
                    )
                    progress.update(task, description="✅ Latency analysis complete")
                    console.print("[green]✅[/green] Latency analysis completed")

                except Exception as e:
                    console.print(f"[yellow]⚠️[/yellow] Latency analysis failed: {e}")
                    latency_analysis = None

            # Gerar relatório
            task = progress.add_task("📝 Generating report...", total=None)
            try:
                if format.lower() == "html":
                    report_content = self.report_generator.generate_html_report(
                        use_scores, latency_analysis, metrics
                    )
                    extension = "html"
                elif format.lower() == "markdown":
                    report_content = self.report_generator.generate_markdown_report(
                        use_scores, latency_analysis, metrics
                    )
                    extension = "md"
                else:
                    raise ValueError(f"Unsupported format: {format}")

                # Salvar relatório
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"performance_report_{timestamp}.{extension}"
                report_path = self.output_dir / filename

                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report_content)

                progress.update(task, description="✅ Report generated")
                console.print(f"[green]✅[/green] Report saved to: {report_path}")

            except Exception as e:
                console.print(f"[red]❌[/red] Failed to generate report: {e}")
                raise

        # Exibir resumo
        elapsed_time = time.time() - start_time
        self._display_summary(use_scores, latency_analysis, elapsed_time, report_path)

        return report_path

    def _generate_sample_latency_data(self) -> List[float]:
        """
        Gera dados de latência simulados para demonstração.
        Em produção, estes dados viriam de medições reais da aplicação.
        """
        import numpy as np

        # Simular latência com distribuição log-normal (comum em sistemas)
        mean_latency = 25  # ms
        std_latency = 15  # ms

        # Gerar 1000 amostras
        samples = np.random.lognormal(
            np.log(mean_latency), std_latency / mean_latency, 1000
        )

        # Adicionar alguns outliers
        outliers = np.random.uniform(200, 500, 20)  # 20 outliers
        samples = np.concatenate([samples, outliers])

        # Limitar a valores realistas
        samples = np.clip(samples, 0.1, 1000)

        return samples.tolist()

    def _display_summary(
        self,
        use_scores: dict,
        latency_analysis: Optional[dict],
        elapsed_time: float,
        report_path: Path,
    ):
        """Exibe resumo da análise no console."""

        # Criar tabela de resumo
        table = Table(title="📊 Performance Analysis Summary")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Score", style="green")
        table.add_column("Utilization", style="yellow")
        table.add_column("Saturation", style="blue")

        for component, score in use_scores.items():
            status_color = {"OK": "green", "WARNING": "yellow", "CRITICAL": "red"}.get(
                score.status.value, "white"
            )

            table.add_row(
                component.upper(),
                f"[{status_color}]{score.status.value}[/{status_color}]",
                f"{score.overall_score:.1f}%",
                f"{score.utilization:.1f}%",
                f"{score.saturation:.1f}%",
            )

        console.print(table)

        # Exibir informações de latência se disponível
        if latency_analysis and "error" not in latency_analysis:
            perf_class = latency_analysis.get("performance_class", "UNKNOWN")
            p95 = latency_analysis.get("percentiles", {}).get("p95", 0)

            latency_panel = Panel(
                f"Performance Class: {perf_class}\nP95 Latency: {p95:.2f}ms",
                title="⏱️ Latency Analysis",
                border_style="blue",
            )
            console.print(latency_panel)

        # Exibir estatísticas da análise
        stats_panel = Panel(
            f"Analysis Time: {elapsed_time:.2f}s\n"
            f"Report Location: {report_path}\n"
            f"Components Analyzed: {len(use_scores)}",
            title="📈 Analysis Statistics",
            border_style="green",
        )
        console.print(stats_panel)

    def run_scheduled_analysis(
        self,
        time_str: str = "08:00",
        components: Optional[List[str]] = None,
        include_latency: bool = False,
        format: str = "html",
    ):
        """
        Executa análises agendadas automaticamente.

        Args:
            time_str: Horário da análise (formato HH:MM)
            components: Componentes para analisar
            include_latency: Incluir análise de latência
            format: Formato do relatório
        """
        console.print(f"[blue]🕐[/blue] Scheduling daily analysis at {time_str}")

        def job():
            try:
                console.print("[green]🚀[/green] Starting scheduled analysis...")
                report_path = self.run_analysis(components, include_latency, format)
                console.print(
                    f"[green]✅[/green] Scheduled analysis completed: {report_path}"
                )

                # Aqui poderia adicionar notificações (email, Slack, etc.)

            except Exception as e:
                console.print(f"[red]❌[/red] Scheduled analysis failed: {e}")
                logger.error(f"Scheduled analysis failed: {e}")

        # Agendar tarefa
        schedule.every().day.at(time_str).do(job)

        console.print("[green]✅[/green] Scheduler started. Press Ctrl+C to stop.")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
        except KeyboardInterrupt:
            console.print("\n[yellow]⏹️[/yellow] Scheduler stopped by user")


def create_parser() -> argparse.ArgumentParser:
    """Cria parser de argumentos da CLI."""
    parser = argparse.ArgumentParser(
        description="Systems Performance Analysis Tool - Brendan Gregg USE Method",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Full analysis with HTML report
  %(prog)s --components cpu,memory            # Analyze specific components
  %(prog)s --latency --format markdown        # Include latency analysis
  %(prog)s --schedule --time 08:00            # Schedule daily analysis
        """,
    )

    parser.add_argument(
        "--components",
        type=str,
        help="Components to analyze (comma-separated): cpu,memory,disk,network",
    )

    parser.add_argument(
        "--latency", action="store_true", help="Include latency analysis"
    )

    parser.add_argument(
        "--format",
        choices=["html", "markdown", "json"],
        default="html",
        help="Report format (default: html)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports"),
        help="Output directory for reports (default: reports)",
    )

    parser.add_argument(
        "--schedule", action="store_true", help="Run scheduled analysis daily"
    )

    parser.add_argument(
        "--time",
        type=str,
        default="08:00",
        help="Time for scheduled analysis (HH:MM format, default: 08:00)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--version", action="version", version="Systems Performance Analysis Tool 1.0.0"
    )

    return parser


def main():
    """Função principal da CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Configurar logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Exibir banner
    console.print(
        Panel.fit(
            "[bold blue]Systems Performance Analysis Tool[/bold blue]\n"
            "Based on Brendan Gregg's USE Method\n"
            "with Context Engineering",
            border_style="blue",
        )
    )

    try:
        # Inicializar analisador
        analyzer = PerformanceAnalyzer(args.output)

        # Parse components
        components = None
        if args.components:
            components = [c.strip().lower() for c in args.components.split(",")]
            valid_components = {"cpu", "memory", "disk", "network"}
            components = [c for c in components if c in valid_components]

            if not components:
                console.print("[red]❌[/red] No valid components specified")
                sys.exit(1)

        # Executar análise ou scheduler
        if args.schedule:
            analyzer.run_scheduled_analysis(
                time_str=args.time,
                components=components,
                include_latency=args.latency,
                format=args.format,
            )
        else:
            report_path = analyzer.run_analysis(
                components=components, include_latency=args.latency, format=args.format
            )

            console.print(f"\n[green]🎉[/green] Analysis completed successfully!")
            console.print(f"[blue]📄[/blue] Report available at: {report_path}")

    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️[/yellow] Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌[/red] Analysis failed: {e}")
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
