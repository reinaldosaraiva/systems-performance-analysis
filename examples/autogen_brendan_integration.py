#!/usr/bin/env python3
"""
AutoGen + Brendan Gregg Persona Integration

This example shows how to integrate the Brendan Gregg persona with the
existing AutoGen multi-agent system for collaborative performance analysis.

The Brendan persona acts as a specialized "Performance Expert" agent that
provides USE Method analysis and systems performance insights, working
alongside other AutoGen agents for comprehensive analysis.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from brendan_gregg_persona import (
    BrendanGreggPersona,
    BrendanGreggInsight,
    AnalysisMethodology,
)
from autogen_integration import (
    AutoGenIntegration,
    AgentRole,
    AnalysisFinding,
    AnalysisSeverity,
    CollaborativeAnalysis,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def convert_brendan_to_autogen(insight: BrendanGreggInsight) -> AnalysisFinding:
    """
    Convert Brendan Gregg insight to AutoGen finding format.

    This allows Brendan's USE Method analysis to be integrated with
    other AutoGen agents for collaborative decision-making.
    """
    # Map severity
    severity_map = {
        "critical": AnalysisSeverity.CRITICAL,
        "high": AnalysisSeverity.HIGH,
        "medium": AnalysisSeverity.MEDIUM,
        "low": AnalysisSeverity.LOW,
        "info": AnalysisSeverity.INFO,
    }

    return AnalysisFinding(
        id=insight.id,
        agent=AgentRole.PERFORMANCE_ANALYST,  # Brendan acts as performance analyst
        component=insight.component,
        severity=severity_map.get(insight.severity, AnalysisSeverity.MEDIUM),
        title=f"[Brendan Gregg] {insight.title}",
        description=f"{insight.observation}\n\nROOT CAUSE: {insight.root_cause}",
        recommendation=f"{insight.immediate_action}\n\nLONG-TERM: {insight.long_term_fix}",
        metrics=insight.evidence,
        confidence=insight.confidence / 100,  # Convert to 0-1 range
        timestamp=insight.timestamp,
    )


async def integrated_analysis():
    """
    Run integrated analysis with both Brendan persona and AutoGen agents.

    Flow:
    1. Brendan runs USE Method analysis on Prometheus/Grafana data
    2. Insights are converted to AutoGen findings
    3. Other AutoGen agents analyze the same system
    4. All findings are combined for collaborative recommendations
    """
    console.print(
        Panel.fit(
            "[bold cyan]🤝 Integrated Performance Analysis[/bold cyan]\n"
            "Brendan Gregg Persona + AutoGen Multi-Agent System\n\n"
            "Combining USE Method expertise with collaborative AI analysis",
            border_style="cyan",
        )
    )

    # Step 1: Initialize both systems
    console.print("\n[bold]Step 1: Initializing Systems[/bold]")

    brendan = BrendanGreggPersona()
    autogen = AutoGenIntegration()

    console.print("  ✅ Brendan Gregg Persona ready")
    console.print("  ✅ AutoGen Multi-Agent System ready\n")

    # Step 2: Brendan runs USE Method analysis
    console.print("[bold]Step 2: Brendan's USE Method Analysis[/bold]")
    console.print("  Running comprehensive resource analysis...\n")

    use_insights = await brendan.analyze_use_method()

    if use_insights:
        console.print(f"  [yellow]→[/yellow] Brendan found {len(use_insights)} insights")

        # Display Brendan's findings
        table = Table(title="Brendan Gregg's USE Method Findings", show_header=True)
        table.add_column("Component", style="cyan")
        table.add_column("Severity", style="red")
        table.add_column("Issue", style="white")

        for insight in use_insights:
            table.add_row(
                insight.component,
                insight.severity.upper(),
                insight.title[:50] + "..." if len(insight.title) > 50 else insight.title,
            )

        console.print(table)
    else:
        console.print("  [green]✅[/green] No issues found by Brendan\n")

    # Step 3: Convert Brendan's insights to AutoGen format
    console.print("\n[bold]Step 3: Converting to AutoGen Format[/bold]")

    autogen_findings = [convert_brendan_to_autogen(i) for i in use_insights]
    console.print(
        f"  ✅ Converted {len(autogen_findings)} Brendan insights to AutoGen findings\n"
    )

    # Step 4: Run AutoGen collaborative analysis
    console.print("[bold]Step 4: AutoGen Collaborative Analysis[/bold]")
    console.print("  Engaging other specialized agents...\n")

    # Collect system metrics for AutoGen
    metrics = await autogen.collect_system_metrics()

    # Run collaborative analysis (this will include other agents)
    collaborative_analysis = await autogen.run_collaborative_analysis(metrics=metrics)

    # Step 5: Merge Brendan's findings with AutoGen findings
    console.print("\n[bold]Step 5: Merging Findings[/bold]")

    # Add Brendan's findings to collaborative analysis
    collaborative_analysis.findings.extend(autogen_findings)

    total_findings = len(collaborative_analysis.findings)
    brendan_findings = len(autogen_findings)
    other_findings = total_findings - brendan_findings

    console.print(f"  Total findings: {total_findings}")
    console.print(f"    • Brendan Gregg insights: {brendan_findings}")
    console.print(f"    • Other AutoGen agents: {other_findings}\n")

    # Step 6: Generate consensus recommendations
    console.print("[bold]Step 6: Consensus Recommendations[/bold]\n")

    # Priority findings (critical + high)
    priority_findings = [
        f
        for f in collaborative_analysis.findings
        if f.severity in [AnalysisSeverity.CRITICAL, AnalysisSeverity.HIGH]
    ]

    if priority_findings:
        console.print(f"  [red]⚠️[/red] {len(priority_findings)} priority issues identified\n")

        # Show top 3 priority recommendations
        console.print("  [bold]Top Priority Recommendations:[/bold]\n")

        for i, finding in enumerate(priority_findings[:3], 1):
            agent_name = finding.agent.value.replace("_", " ").title()
            severity_color = "red" if finding.severity == AnalysisSeverity.CRITICAL else "yellow"

            console.print(f"  [{severity_color}]{i}.[/{severity_color}] [{agent_name}] {finding.title}")
            console.print(f"     {finding.recommendation[:100]}...\n")

    # Step 7: Generate comprehensive reports
    console.print("[bold]Step 7: Generating Reports[/bold]\n")

    # Brendan-style report
    brendan_report = brendan.generate_brendan_style_report(use_insights)
    brendan_report_path = Path("reports") / f"brendan_integrated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    brendan_report_path.parent.mkdir(exist_ok=True)

    with open(brendan_report_path, "w") as f:
        f.write(brendan_report)

    console.print(f"  ✅ Brendan's report: {brendan_report_path}")

    # AutoGen report
    autogen_report_path = autogen.generate_comprehensive_report(
        collaborative_analysis, "html"
    )
    console.print(f"  ✅ AutoGen report: {autogen_report_path}")

    # Step 8: Display summary
    console.print("\n[bold]Step 8: Analysis Summary[/bold]\n")

    summary_table = Table(title="Integrated Analysis Summary", show_header=True)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")

    summary_table.add_row("Total Findings", str(total_findings))
    summary_table.add_row("Brendan Gregg Insights", str(brendan_findings))
    summary_table.add_row("Other Agent Findings", str(other_findings))
    summary_table.add_row("Consensus Score", f"{collaborative_analysis.consensus_score:.1f}%")
    summary_table.add_row("Critical Issues", str(len([f for f in collaborative_analysis.findings if f.severity == AnalysisSeverity.CRITICAL])))
    summary_table.add_row("High Priority", str(len([f for f in collaborative_analysis.findings if f.severity == AnalysisSeverity.HIGH])))

    console.print(summary_table)

    # Step 9: Next steps
    console.print("\n[bold]Step 9: Next Steps[/bold]\n")

    if priority_findings:
        console.print("  [red]⚠️  IMMEDIATE ACTIONS REQUIRED:[/red]\n")
        console.print("  1. Review critical and high-priority findings")
        console.print("  2. Execute immediate actions from Brendan's recommendations")
        console.print("  3. Investigate root causes using provided commands")
        console.print("  4. Implement long-term fixes")
        console.print("  5. Monitor metrics to verify improvements\n")
    else:
        console.print("  [green]✅ SYSTEM HEALTHY:[/green]\n")
        console.print("  1. Continue monitoring with regular USE Method checks")
        console.print("  2. Review trends in Grafana dashboards")
        console.print("  3. Plan capacity based on usage patterns")
        console.print("  4. Document baselines for future comparison\n")

    console.print("[green]🎉 Integrated analysis complete![/green]\n")

    return collaborative_analysis


async def main():
    """Run integrated analysis demo."""

    try:
        analysis = await integrated_analysis()

        console.print("\n" + "=" * 80)
        console.print("INTEGRATION BENEFITS")
        console.print("=" * 80 + "\n")

        benefits = [
            ("USE Method Expertise", "Brendan's proven methodology for resource analysis"),
            ("Multi-Agent Perspectives", "Infrastructure, Security, Cost perspectives"),
            ("Collaborative Recommendations", "Consensus-based actionable suggestions"),
            ("Comprehensive Reports", "Both technical (Brendan) and business (AutoGen)"),
            ("Historical Context", "Prometheus time-series + AutoGen analysis history"),
        ]

        for benefit, description in benefits:
            console.print(f"[cyan]•[/cyan] [bold]{benefit}:[/bold] {description}")

        console.print("\n" + "=" * 80 + "\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
