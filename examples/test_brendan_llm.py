"""
Test Brendan Gregg Agent with MiniMax-M2 LLM

Demonstrates how LLM-powered insights are more intelligent and contextual
compared to rule-based analysis.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from brendan_llm_agent import BrendanLLMAgent, LLMConfig
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def main():
    """Test LLM-powered Brendan Gregg agent."""

    console.print(Panel.fit(
        "[bold cyan]🤖 Brendan Gregg Agent with MiniMax-M2[/bold cyan]\n"
        "Using Ollama for intelligent performance analysis",
        border_style="cyan"
    ))

    # Initialize LLM agent
    console.print("\n📡 Connecting to Prometheus and Ollama...")
    agent = BrendanLLMAgent(
        prometheus_url="http://177.93.132.48:9090",
        llm_config=LLMConfig(
            model="minimax-m2:cloud",
            temperature=0.7
        )
    )

    console.print("✅ Connected!\n")

    # Run analysis
    console.print("🔍 Running LLM-powered USE Method analysis...")
    console.print("[dim]This may take 30-60 seconds as the LLM analyzes metrics...[/dim]\n")

    insights = await agent.analyze_system()

    # Display results
    console.print(f"\n[bold green]✅ Analysis Complete![/bold green]")
    console.print(f"Generated {len(insights)} insights\n")

    # Show each insight
    for i, insight in enumerate(insights, 1):
        severity_colors = {
            "CRITICAL": "red",
            "HIGH": "orange1",
            "MEDIUM": "yellow",
            "LOW": "green"
        }
        color = severity_colors.get(insight.severity, "white")

        panel = Panel(
            f"[bold]{insight.title}[/bold]\n\n"
            f"[dim]Component:[/dim] {insight.component}\n"
            f"[dim]Severity:[/dim] [{color}]{insight.severity}[/{color}]\n\n"
            f"📊 [bold]Observation:[/bold]\n{insight.observation}\n\n"
            f"🔍 [bold]Evidence:[/bold]\n" +
            "\n".join(f"  • {k}: {v}" for k, v in list(insight.evidence.items())[:5]) +
            f"\n\n🎯 [bold]Root Cause:[/bold]\n{insight.root_cause}\n\n"
            f"⚡ [bold]Immediate Action:[/bold]\n{insight.immediate_action}",
            title=f"Insight #{i}",
            border_style=color
        )
        console.print(panel)
        console.print()

    # Summary table
    table = Table(title="Analysis Summary")
    table.add_column("Severity", style="bold")
    table.add_column("Count", justify="right")

    severity_counts = {}
    for insight in insights:
        severity_counts[insight.severity] = severity_counts.get(insight.severity, 0) + 1

    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = severity_counts.get(severity, 0)
        if count > 0:
            color = severity_colors.get(severity, "white")
            table.add_row(f"[{color}]{severity}[/{color}]", str(count))

    console.print(table)

    console.print("\n[bold cyan]🎉 LLM-powered analysis complete![/bold cyan]")
    console.print("[dim]Insights are more contextual and actionable thanks to MiniMax-M2[/dim]\n")


if __name__ == "__main__":
    asyncio.run(main())
