#!/usr/bin/env python3
"""
Demo: Brendan Gregg Persona Integration

This script demonstrates how to use the Brendan Gregg persona for
performance analysis with AutoGen integration.

The persona analyzes Prometheus metrics and Grafana dashboards using
Brendan's proven methodologies from the Systems Performance book.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from brendan_gregg_persona import (
    BrendanGreggPersona,
    AnalysisMethodology,
    PerformanceIssueType,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

console = Console()


async def demo_use_method_analysis():
    """
    Demo 1: USE Method Analysis

    Brendan Gregg's USE Method is applied to all system resources:
    - Utilization: How busy is the resource?
    - Saturation: Is there queued work?
    - Errors: Are there any errors?
    """
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold cyan]DEMO 1: USE Method Analysis[/bold cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    console.print(
        "The USE Method provides a complete checklist for investigating performance.\n"
        "For every resource, we check Utilization, Saturation, and Errors.\n"
    )

    # Initialize persona
    persona = BrendanGreggPersona()

    # Run USE Method analysis
    console.print("[bold]Running comprehensive USE Method analysis...[/bold]\n")
    insights = await persona.analyze_use_method()

    # Display results
    if insights:
        console.print(f"[green]✅ Found {len(insights)} performance insights[/green]\n")

        # Create summary table
        table = Table(title="USE Method Findings Summary", show_header=True)
        table.add_column("Component", style="cyan")
        table.add_column("Issue Type", style="yellow")
        table.add_column("Severity", style="red")
        table.add_column("Title", style="white")

        for insight in insights:
            severity_style = {
                "critical": "bold red",
                "high": "bold yellow",
                "medium": "yellow",
                "low": "green",
            }.get(insight.severity, "white")

            table.add_row(
                insight.component,
                insight.issue_type.value,
                f"[{severity_style}]{insight.severity.upper()}[/{severity_style}]",
                insight.title,
            )

        console.print(table)

        # Show detailed analysis for first critical issue
        critical_insights = [i for i in insights if i.severity == "critical"]
        if critical_insights:
            console.print("\n[bold red]🚨 Detailed Analysis of Critical Issue:[/bold red]\n")
            insight = critical_insights[0]

            details = f"""
**{insight.title}**

**Component:** {insight.component}
**Methodology:** {insight.methodology.value}
**Confidence:** {insight.confidence:.0f}%

**📊 OBSERVATION:**
{insight.observation}

**🔍 EVIDENCE:**
{chr(10).join(f'  • {k}: {v}' for k, v in insight.evidence.items())}

**🧠 ROOT CAUSE:**
{insight.root_cause}

**⚡ IMMEDIATE ACTION:**
{insight.immediate_action}

**🔧 INVESTIGATION STEPS:**
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(insight.investigation_steps))}

**💡 LONG-TERM FIX:**
{insight.long_term_fix}

**📚 REFERENCE:**
{insight.book_reference or 'N/A'}
            """

            console.print(Panel(Markdown(details), border_style="red"))

    else:
        console.print("[green]✅ No performance issues detected![/green]")
        console.print("System is operating within normal parameters.\n")


async def demo_grafana_dashboard_analysis():
    """
    Demo 2: Grafana Dashboard Analysis

    Analyze Grafana dashboards to understand system behavior through
    visualizations and panel metrics.
    """
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold cyan]DEMO 2: Grafana Dashboard Analysis[/bold cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    console.print(
        "Brendan's approach: Look at dashboards, understand metrics in context,\n"
        "and apply performance methodologies to interpret the data.\n"
    )

    # Initialize persona
    persona = BrendanGreggPersona()

    # List available dashboards
    console.print("[bold]Discovering Grafana dashboards...[/bold]\n")
    dashboards = persona.grafana.list_dashboards()

    if not dashboards:
        console.print("[yellow]⚠️ No Grafana dashboards found.[/yellow]")
        console.print("Make sure Grafana is running: http://localhost:3000")
        console.print("Import the USE Method dashboard from grafana/dashboards/\n")
        return

    # Display available dashboards
    table = Table(title="Available Grafana Dashboards", show_header=True)
    table.add_column("#", style="cyan", width=5)
    table.add_column("Title", style="white")
    table.add_column("UID", style="yellow")
    table.add_column("Tags", style="green")

    for i, dash in enumerate(dashboards[:10], 1):  # Show max 10
        tags = ", ".join(dash.get("tags", []))
        table.add_row(
            str(i),
            dash.get("title", "Untitled"),
            dash.get("uid", "N/A"),
            tags or "No tags",
        )

    console.print(table)

    # Analyze first USE Method dashboard if available
    use_dashboard = next(
        (d for d in dashboards if "use" in d.get("title", "").lower()), None
    )

    if use_dashboard:
        uid = use_dashboard["uid"]
        title = use_dashboard["title"]

        console.print(f"\n[bold]Analyzing dashboard: {title}[/bold]\n")
        insights = await persona.analyze_grafana_dashboard(uid)

        if insights:
            console.print(f"[green]✅ Found {len(insights)} insights from dashboard[/green]\n")

            for insight in insights[:3]:  # Show top 3
                console.print(f"[yellow]• {insight.title}[/yellow]")
                console.print(f"  {insight.observation}\n")
        else:
            console.print(
                "[green]✅ Dashboard metrics are within normal ranges[/green]\n"
            )

    else:
        console.print(
            "[yellow]💡 Tip:[/yellow] Import the USE Method dashboard for best analysis"
        )
        console.print(
            "   Dashboard file: grafana/dashboards/unified-use-method-dashboard.json\n"
        )


async def demo_methodology_comparison():
    """
    Demo 3: Methodology Comparison

    Compare different analysis methodologies on the same system.
    """
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold cyan]DEMO 3: Methodology Comparison[/bold cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    console.print(
        "Brendan Gregg has developed several methodologies for performance analysis.\n"
        "Each methodology has strengths for different investigation scenarios:\n"
    )

    # Methodology descriptions
    methodologies = {
        "USE Method": "For resource-focused analysis (CPU, Memory, Disk, Network)",
        "TSA Method": "Thread State Analysis for understanding application behavior",
        "Workload Characterization": "Understanding the nature and source of load",
        "Drill-Down Analysis": "Starting from high-level metrics, digging into details",
        "Latency Analysis": "For investigating response time issues",
        "Off-CPU Analysis": "Finding why threads aren't running (waiting, blocked)",
    }

    table = Table(title="Brendan Gregg's Performance Methodologies", show_header=True)
    table.add_column("Methodology", style="cyan", width=30)
    table.add_column("Best Used For", style="white")

    for method, description in methodologies.items():
        table.add_row(method, description)

    console.print(table)

    console.print("\n[bold]💡 Recommendation:[/bold]")
    console.print("1. Start with USE Method for comprehensive resource check")
    console.print("2. Use Workload Characterization to understand application behavior")
    console.print("3. Apply Drill-Down Analysis when specific issues are identified")
    console.print("4. Use Latency Analysis for user-facing performance problems\n")


async def demo_brendan_style_report():
    """
    Demo 4: Generate Brendan Gregg Style Report

    Shows how insights are formatted in Brendan's characteristic style:
    - Data-driven with specific metrics
    - Structured investigation steps
    - Practical recommendations
    - Educational references
    """
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold cyan]DEMO 4: Brendan Gregg Style Report[/bold cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    # Initialize persona
    persona = BrendanGreggPersona()

    # Collect insights
    console.print("[bold]Performing comprehensive analysis...[/bold]\n")
    insights = await persona.analyze_use_method()

    # Generate report
    console.print("[bold]Generating Brendan Gregg style report...[/bold]\n")
    report = persona.generate_brendan_style_report(insights)

    # Display report
    console.print(Panel(report, title="Performance Analysis Report", border_style="cyan"))

    # Save to file
    from datetime import datetime

    filename = f"reports/brendan_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    Path("reports").mkdir(exist_ok=True)

    with open(filename, "w") as f:
        f.write(report)

    console.print(f"\n[green]✅ Report saved to: {filename}[/green]\n")


async def demo_integration_with_autogen():
    """
    Demo 5: Integration with Existing AutoGen System

    Shows how Brendan Gregg persona can work alongside other AutoGen agents
    to provide specialized performance analysis.
    """
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold cyan]DEMO 5: AutoGen Integration[/bold cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    console.print(
        "The Brendan Gregg persona integrates with the existing AutoGen system.\n"
        "It can work as a specialized 'Performance Expert' agent alongside:\n"
    )

    agents = [
        ("Performance Analyst", "General performance metrics analysis"),
        ("Brendan Gregg Persona", "USE Method & Systems Performance expertise"),
        ("Infrastructure Expert", "System architecture and capacity planning"),
        ("Security Analyst", "Security implications of performance"),
        ("Cost Optimizer", "Resource efficiency and cost reduction"),
    ]

    table = Table(title="Multi-Agent Performance Analysis", show_header=True)
    table.add_column("Agent Role", style="cyan")
    table.add_column("Specialty", style="white")

    for role, specialty in agents:
        table.add_row(role, specialty)

    console.print(table)

    console.print("\n[bold]🤝 Collaboration Pattern:[/bold]")
    console.print("1. Brendan Gregg persona runs USE Method analysis")
    console.print("2. Findings are shared with other AutoGen agents")
    console.print("3. Infrastructure Expert suggests scaling/architecture changes")
    console.print("4. Security Analyst evaluates security implications")
    console.print("5. Cost Optimizer proposes cost-effective solutions")
    console.print("6. Consensus recommendations are generated\n")

    console.print("[bold]📝 Example Integration Code:[/bold]")
    code_example = '''
# In autogen_integration.py

from brendan_gregg_persona import BrendanGreggPersona

# Create Brendan Gregg agent
brendan_agent = BrendanGreggPersona()

# Run USE Method analysis
use_insights = await brendan_agent.analyze_use_method()

# Convert to AutoGen AnalysisFinding format
for insight in use_insights:
    autogen_finding = AnalysisFinding(
        id=insight.id,
        agent=AgentRole.PERFORMANCE_ANALYST,
        component=insight.component,
        severity=insight.severity,
        title=insight.title,
        description=insight.observation,
        recommendation=insight.immediate_action,
        metrics=insight.evidence,
        confidence=insight.confidence,
        timestamp=insight.timestamp,
    )
    all_findings.append(autogen_finding)
'''

    console.print(Panel(code_example, border_style="green"))


async def main():
    """Run all demos."""
    console.print(
        Panel.fit(
            "[bold cyan]🎯 Brendan Gregg Persona Demonstration[/bold cyan]\n\n"
            "Performance Analysis using proven methodologies from\n"
            "'Systems Performance: Enterprise and the Cloud' (2nd Edition)\n\n"
            "Methodologies: USE Method, TSA, Workload Characterization,\n"
            "Drill-Down Analysis, Latency Analysis, and more.",
            border_style="cyan",
        )
    )

    demos = [
        ("USE Method Analysis", demo_use_method_analysis),
        ("Grafana Dashboard Analysis", demo_grafana_dashboard_analysis),
        ("Methodology Comparison", demo_methodology_comparison),
        ("Brendan Style Report", demo_brendan_style_report),
        ("AutoGen Integration", demo_integration_with_autogen),
    ]

    console.print("\n[bold]Available Demos:[/bold]")
    for i, (name, _) in enumerate(demos, 1):
        console.print(f"  {i}. {name}")

    console.print("\n[bold]Running all demos...[/bold]\n")

    for name, demo_func in demos:
        try:
            await demo_func()
            await asyncio.sleep(1)  # Pause between demos
        except KeyboardInterrupt:
            console.print("\n[yellow]Demo interrupted by user[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]❌ Demo '{name}' failed: {e}[/red]\n")
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")

    console.print("\n[bold green]🎉 Demo complete![/bold green]\n")
    console.print("[bold]Next Steps:[/bold]")
    console.print("1. Review generated reports in reports/ directory")
    console.print("2. Integrate Brendan Gregg persona into your AutoGen workflows")
    console.print("3. Customize thresholds for your specific environment")
    console.print("4. Add more Grafana dashboards for comprehensive analysis\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Demonstration interrupted[/yellow]")
