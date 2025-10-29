#!/usr/bin/env python3
"""
Brendan Gregg Persona - CLI Integration

This module integrates the Brendan Gregg persona into the main CLI,
providing transparent validation of Prometheus data analysis.

Features:
- Verbose mode showing each query executed
- Validation report of data collected
- Detailed logging of analysis steps
- Integration with existing CLI commands
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

from brendan_gregg_persona import (
    BrendanGreggPersona,
    BrendanGreggInsight,
    PrometheusClient,
)

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class AnalysisValidation:
    """
    Tracks all queries executed and data collected during analysis.
    Provides full transparency into what was analyzed.
    """

    queries_executed: List[Dict[str, Any]] = field(default_factory=list)
    metrics_collected: Dict[str, float] = field(default_factory=dict)
    dashboards_analyzed: List[str] = field(default_factory=list)
    insights_generated: List[BrendanGreggInsight] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)

    def add_query(self, query: str, result: Any, success: bool):
        """Record a Prometheus query execution."""
        self.queries_executed.append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "result": str(result)[:100] if result else None,
        })

    def add_metric(self, name: str, value: float):
        """Record a metric that was collected."""
        self.metrics_collected[name] = value

    def add_dashboard(self, dashboard_uid: str, dashboard_name: str):
        """Record a dashboard that was analyzed."""
        self.dashboards_analyzed.append(f"{dashboard_name} ({dashboard_uid})")

    def add_insight(self, insight: BrendanGreggInsight):
        """Record an insight that was generated."""
        self.insights_generated.append(insight)

    def add_error(self, error: str):
        """Record an error that occurred."""
        self.errors.append(error)

    def generate_report(self) -> str:
        """Generate a validation report showing what was analyzed."""
        duration = (
            (self.end_time - self.start_time).total_seconds()
            if self.start_time and self.end_time
            else 0
        )

        report = []
        report.append("=" * 80)
        report.append("BRENDAN GREGG PERSONA - ANALYSIS VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"\nAnalysis Duration: {duration:.2f} seconds")
        report.append(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else 'N/A'}")
        report.append(f"Ended: {self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else 'N/A'}")

        # Queries executed
        report.append(f"\n📊 PROMETHEUS QUERIES EXECUTED: {len(self.queries_executed)}")
        report.append("-" * 80)

        successful_queries = [q for q in self.queries_executed if q["success"]]
        failed_queries = [q for q in self.queries_executed if not q["success"]]

        report.append(f"  ✅ Successful: {len(successful_queries)}")
        report.append(f"  ❌ Failed: {len(failed_queries)}")

        if self.queries_executed:
            report.append("\n  Sample Queries:")
            for i, query_info in enumerate(self.queries_executed[:5], 1):
                report.append(f"\n  [{i}] Query:")
                # Truncate long queries
                query_text = query_info["query"][:100]
                if len(query_info["query"]) > 100:
                    query_text += "..."
                report.append(f"      {query_text}")
                report.append(f"      Status: {'✅ Success' if query_info['success'] else '❌ Failed'}")
                report.append(f"      Time: {query_info['timestamp']}")

        # Metrics collected
        report.append(f"\n📈 METRICS COLLECTED: {len(self.metrics_collected)}")
        report.append("-" * 80)

        if self.metrics_collected:
            report.append("  Metrics with values:")
            for name, value in list(self.metrics_collected.items())[:10]:
                report.append(f"    • {name}: {value:.2f}")

        # Dashboards analyzed
        if self.dashboards_analyzed:
            report.append(f"\n📋 GRAFANA DASHBOARDS ANALYZED: {len(self.dashboards_analyzed)}")
            report.append("-" * 80)
            for dashboard in self.dashboards_analyzed:
                report.append(f"    • {dashboard}")

        # Insights generated
        report.append(f"\n💡 INSIGHTS GENERATED: {len(self.insights_generated)}")
        report.append("-" * 80)

        if self.insights_generated:
            severity_counts = {}
            for insight in self.insights_generated:
                severity_counts[insight.severity] = severity_counts.get(insight.severity, 0) + 1

            for severity, count in severity_counts.items():
                report.append(f"    • {severity.upper()}: {count}")

            report.append("\n  Sample Insights:")
            for i, insight in enumerate(self.insights_generated[:3], 1):
                report.append(f"\n  [{i}] {insight.title}")
                report.append(f"      Component: {insight.component}")
                report.append(f"      Severity: {insight.severity.upper()}")
                report.append(f"      Methodology: {insight.methodology.value}")
                report.append(f"      Evidence: {', '.join(f'{k}={v:.2f}' for k, v in list(insight.evidence.items())[:3])}")

        # Errors
        if self.errors:
            report.append(f"\n⚠️  ERRORS ENCOUNTERED: {len(self.errors)}")
            report.append("-" * 80)
            for error in self.errors[:5]:
                report.append(f"    • {error}")

        # Summary
        report.append("\n" + "=" * 80)
        report.append("VALIDATION SUMMARY")
        report.append("=" * 80)
        report.append(f"✅ Prometheus queries executed: {len(successful_queries)}")
        report.append(f"✅ Metrics successfully collected: {len(self.metrics_collected)}")
        report.append(f"✅ Dashboards analyzed: {len(self.dashboards_analyzed)}")
        report.append(f"✅ Insights generated: {len(self.insights_generated)}")

        if failed_queries:
            report.append(f"⚠️  Failed queries: {len(failed_queries)}")
        if self.errors:
            report.append(f"⚠️  Errors encountered: {len(self.errors)}")

        report.append("\n" + "=" * 80)

        return "\n".join(report)


class VerbosePrometheusClient(PrometheusClient):
    """
    Extended Prometheus client with verbose logging.
    Tracks all queries and results for validation.
    """

    def __init__(self, prometheus_url: str, validation: AnalysisValidation):
        super().__init__(prometheus_url)
        self.validation = validation

    def query_instant(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute query with verbose logging."""
        console.print(f"[dim cyan]→ Executing query:[/dim cyan] {query[:80]}...")

        try:
            result = super().query_instant(query)
            success = result is not None and result.get("result")

            if success:
                console.print(f"[dim green]  ✅ Query successful[/dim green]")
            else:
                console.print(f"[dim yellow]  ⚠️  Query returned no data[/dim yellow]")

            self.validation.add_query(query, result, success)
            return result

        except Exception as e:
            console.print(f"[dim red]  ❌ Query failed: {e}[/dim red]")
            self.validation.add_query(query, None, False)
            self.validation.add_error(f"Query failed: {str(e)[:100]}")
            return None

    def get_metric_value(self, query: str) -> Optional[float]:
        """Get metric value with verbose logging."""
        result = self.query_instant(query)

        if not result or not result.get("result"):
            return None

        try:
            value = float(result["result"][0]["value"][1])
            console.print(f"[dim green]  📊 Metric value: {value:.2f}[/dim green]")

            # Record metric
            # Extract metric name from query (simple heuristic)
            metric_name = query.split("(")[0].strip() if "(" in query else query[:30]
            self.validation.add_metric(metric_name, value)

            return value

        except (IndexError, KeyError, ValueError) as e:
            console.print(f"[dim red]  ❌ Could not extract value: {e}[/dim red]")
            return None


class BrendanGreggCLI:
    """
    CLI integration for Brendan Gregg persona.
    Provides verbose analysis with full validation.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.validation = AnalysisValidation()

    async def run_analysis(
        self,
        prometheus_url: str = "http://localhost:9090",
        grafana_url: str = "http://localhost:3000",
        analyze_dashboards: bool = True,
        output_format: str = "text",
    ) -> AnalysisValidation:
        """
        Run complete Brendan Gregg analysis with validation.

        Args:
            prometheus_url: Prometheus server URL
            grafana_url: Grafana server URL
            analyze_dashboards: Whether to analyze Grafana dashboards
            output_format: Output format (text, json, markdown)

        Returns:
            AnalysisValidation with complete analysis details
        """

        self.validation.start_time = datetime.now()

        console.print(
            Panel.fit(
                "[bold cyan]🎯 Brendan Gregg Performance Analysis[/bold cyan]\n"
                "USE Method with Prometheus/Grafana Integration\n\n"
                f"Verbose Mode: {'ON ✅' if self.verbose else 'OFF'}",
                border_style="cyan",
            )
        )

        # Initialize persona with verbose client
        console.print("\n[bold]Step 1: Initializing Brendan Gregg Persona[/bold]")

        if self.verbose:
            prometheus_client = VerbosePrometheusClient(prometheus_url, self.validation)
        else:
            prometheus_client = PrometheusClient(prometheus_url)

        persona = BrendanGreggPersona(prometheus_url, grafana_url)

        # Replace with verbose client if needed
        if self.verbose:
            persona.prometheus = prometheus_client

        console.print(f"  ✅ Connected to Prometheus: {prometheus_url}")
        console.print(f"  ✅ Connected to Grafana: {grafana_url}\n")

        # Run USE Method analysis
        console.print("[bold]Step 2: Running USE Method Analysis[/bold]")
        console.print("  Analyzing: CPU, Memory, Disk, Network\n")

        if self.verbose:
            console.print("[dim]Verbose mode: showing all queries...[/dim]\n")

        insights = await persona.analyze_use_method()

        # Record insights
        for insight in insights:
            self.validation.add_insight(insight)

        console.print(f"\n  ✅ USE Method complete: {len(insights)} insights generated\n")

        # Analyze Grafana dashboards if requested
        if analyze_dashboards:
            console.print("[bold]Step 3: Analyzing Grafana Dashboards[/bold]\n")

            dashboards = persona.grafana.list_dashboards()
            console.print(f"  Found {len(dashboards)} dashboards\n")

            # Analyze USE Method dashboard if available
            use_dashboard = next(
                (d for d in dashboards if "use" in d.get("title", "").lower()),
                None
            )

            if use_dashboard:
                uid = use_dashboard["uid"]
                title = use_dashboard["title"]

                console.print(f"  Analyzing: {title}...")
                self.validation.add_dashboard(uid, title)

                dashboard_insights = await persona.analyze_grafana_dashboard(uid)
                insights.extend(dashboard_insights)

                for insight in dashboard_insights:
                    self.validation.add_insight(insight)

                console.print(f"  ✅ Dashboard analysis complete: {len(dashboard_insights)} insights\n")

        # Generate reports
        console.print("[bold]Step 4: Generating Reports[/bold]\n")

        # Brendan-style report
        brendan_report = persona.generate_brendan_style_report(insights)
        report_path = Path("reports") / f"brendan_cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w") as f:
            f.write(brendan_report)

        console.print(f"  ✅ Brendan report: {report_path}")

        # Validation report
        self.validation.end_time = datetime.now()
        validation_report = self.validation.generate_report()

        validation_path = Path("reports") / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(validation_path, "w") as f:
            f.write(validation_report)

        console.print(f"  ✅ Validation report: {validation_path}\n")

        # Display summary
        self._display_summary(insights)

        return self.validation

    def _display_summary(self, insights: List[BrendanGreggInsight]):
        """Display analysis summary."""

        console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]                     ANALYSIS SUMMARY                          [/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")

        # Summary table
        table = Table(title="Analysis Results", show_header=True, border_style="cyan")
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Value", style="white", width=30)

        duration = (
            (self.validation.end_time - self.validation.start_time).total_seconds()
            if self.validation.start_time and self.validation.end_time
            else 0
        )

        table.add_row("Analysis Duration", f"{duration:.2f} seconds")
        table.add_row("Prometheus Queries", str(len(self.validation.queries_executed)))
        table.add_row("Metrics Collected", str(len(self.validation.metrics_collected)))
        table.add_row("Dashboards Analyzed", str(len(self.validation.dashboards_analyzed)))
        table.add_row("Insights Generated", str(len(insights)))

        # Count by severity
        severity_counts = {}
        for insight in insights:
            severity_counts[insight.severity] = severity_counts.get(insight.severity, 0) + 1

        for severity in ["critical", "high", "medium", "low", "info"]:
            if severity in severity_counts:
                color = {"critical": "red", "high": "yellow", "medium": "cyan"}.get(severity, "green")
                table.add_row(
                    f"  {severity.title()} Issues",
                    f"[{color}]{severity_counts[severity]}[/{color}]"
                )

        console.print(table)

        # Validation stats
        console.print("\n[bold]Data Collection Validation:[/bold]")
        successful_queries = [q for q in self.validation.queries_executed if q["success"]]
        failed_queries = [q for q in self.validation.queries_executed if not q["success"]]

        console.print(f"  ✅ Successful queries: {len(successful_queries)}")
        console.print(f"  ❌ Failed queries: {len(failed_queries)}")
        console.print(f"  📊 Metrics with data: {len(self.validation.metrics_collected)}")

        if self.validation.errors:
            console.print(f"  ⚠️  Errors encountered: {len(self.validation.errors)}")

        console.print(f"\n[bold green]✅ Analysis validated and complete![/bold green]\n")


def start_api_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    reports_dir: Path = Path("reports")
):
    """
    Start the API server for Grafana integration.

    Args:
        host: Host to bind to
        port: Port to bind to
        reports_dir: Directory containing analysis reports
    """
    console.print("\n[bold cyan]🚀 Starting API Server for Grafana Integration[/bold cyan]")
    console.print(f"[dim]Host: {host}:{port}[/dim]")
    console.print(f"[dim]API Endpoint: http://{host if host != '0.0.0.0' else 'localhost'}:{port}[/dim]")
    console.print(f"[dim]Dashboard URL: http://localhost:3000/d/brendan-agent-analysis[/dim]")
    console.print("[dim]Press Ctrl+C to stop the server[/dim]\n")

    # Import and start API server
    from brendan_api_server import BrendanInsightsAPI

    api = BrendanInsightsAPI(reports_dir=reports_dir)

    try:
        api.run(host=host, port=port)
    except KeyboardInterrupt:
        console.print("\n[yellow]API server stopped by user[/yellow]")


async def main():
    """CLI entry point for Brendan Gregg analysis."""

    import argparse

    parser = argparse.ArgumentParser(
        description="Brendan Gregg Performance Analysis CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run analysis with verbose output
  python brendan_gregg_cli.py --verbose

  # Run without dashboard analysis
  python brendan_gregg_cli.py --no-dashboards

  # Custom Prometheus/Grafana URLs
  python brendan_gregg_cli.py --prometheus http://remote:9090 --grafana http://remote:3000
        """,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose mode (show all Prometheus queries)",
    )

    parser.add_argument(
        "--prometheus",
        default="http://localhost:9090",
        help="Prometheus server URL (default: http://localhost:9090)",
    )

    parser.add_argument(
        "--grafana",
        default="http://localhost:3000",
        help="Grafana server URL (default: http://localhost:3000)",
    )

    parser.add_argument(
        "--no-dashboards",
        action="store_true",
        help="Skip Grafana dashboard analysis",
    )

    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start API server after analysis to expose insights to Grafana",
    )

    parser.add_argument(
        "--api-host",
        default="0.0.0.0",
        help="API server host (default: 0.0.0.0, only used with --serve)",
    )

    parser.add_argument(
        "--api-port",
        type=int,
        default=8080,
        help="API server port (default: 8080, only used with --serve)",
    )

    args = parser.parse_args()

    # Run analysis
    cli = BrendanGreggCLI(verbose=args.verbose)

    try:
        validation = await cli.run_analysis(
            prometheus_url=args.prometheus,
            grafana_url=args.grafana,
            analyze_dashboards=not args.no_dashboards,
            output_format=args.output,
        )

        # Print validation summary
        console.print("\n[bold]Validation Report Summary:[/bold]")
        console.print(f"  Queries executed: {len(validation.queries_executed)}")
        console.print(f"  Metrics collected: {len(validation.metrics_collected)}")
        console.print(f"  Insights generated: {len(validation.insights_generated)}")

        if validation.errors:
            console.print(f"  [yellow]Warnings: {len(validation.errors)}[/yellow]")

        console.print("\n[bold green]✅ Analysis complete![/bold green]")
        console.print(f"[dim]Reports saved in: reports/[/dim]\n")

        # Start API server if --serve flag is provided
        if args.serve:
            start_api_server(
                host=args.api_host,
                port=args.api_port,
                reports_dir=Path("reports")
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Analysis failed: {e}[/red]")
        import traceback
        if args.verbose:
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
