#!/usr/bin/env python3
"""
Demo: Comparação entre Análise Rule-Based vs LLM-Powered

Demonstra a diferença de qualidade entre a análise tradicional baseada em regras
e a análise inteligente usando LLM MiniMax-M2.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from brendan_gregg_persona import BrendanGreggPersona
from brendan_llm_agent import BrendanLLMAgent, LLMConfig
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel

console = Console()


async def main():
    """Compare rule-based vs LLM-powered analysis."""

    console.print(Panel.fit(
        "[bold cyan]🔬 Brendan Gregg Analysis Comparison[/bold cyan]\n"
        "[dim]Rule-Based vs LLM-Powered (MiniMax-M2)[/dim]",
        border_style="cyan"
    ))

    prometheus_url = "http://177.93.132.48:9090"

    # ============================================================
    # 1. RULE-BASED ANALYSIS
    # ============================================================
    console.print("\n[bold yellow]📊 Running Rule-Based Analysis...[/bold yellow]")

    rule_based = BrendanGreggPersona(prometheus_url=prometheus_url)
    rule_insights = await rule_based.analyze_use_method()

    console.print(f"[green]✅ Found {len(rule_insights)} insights (rule-based)[/green]\n")

    # ============================================================
    # 2. LLM-POWERED ANALYSIS
    # ============================================================
    console.print("[bold cyan]🤖 Running LLM-Powered Analysis...[/bold cyan]")
    console.print("[dim]This may take 30-60 seconds...[/dim]\n")

    llm_agent = BrendanLLMAgent(
        prometheus_url=prometheus_url,
        llm_config=LLMConfig(
            model="minimax-m2:cloud",
            temperature=0.7
        )
    )
    llm_insights = await llm_agent.analyze_system()

    console.print(f"[green]✅ Found {len(llm_insights)} insights (LLM-powered)[/green]\n")

    # ============================================================
    # 3. SIDE-BY-SIDE COMPARISON
    # ============================================================
    console.print("\n[bold magenta]🔍 Comparison of Most Critical Issues:[/bold magenta]\n")

    # Get top insight from each
    rule_top = rule_insights[0] if rule_insights else None
    llm_top = [i for i in llm_insights if i.severity in ["CRITICAL", "HIGH"]][0] if llm_insights else None

    if rule_top and llm_top:
        # Rule-based panel
        rule_panel = Panel(
            f"[bold]{rule_top.title}[/bold]\n\n"
            f"[dim]Severity:[/dim] {rule_top.severity}\n"
            f"[dim]Component:[/dim] {rule_top.component}\n\n"
            f"📊 [bold]Observation:[/bold]\n{rule_top.observation[:200]}...\n\n"
            f"⚡ [bold]Action:[/bold]\n{rule_top.immediate_action[:150]}...",
            title="[yellow]Rule-Based[/yellow]",
            border_style="yellow",
            width=60
        )

        # LLM panel
        llm_panel = Panel(
            f"[bold]{llm_top.title}[/bold]\n\n"
            f"[dim]Severity:[/dim] {llm_top.severity}\n"
            f"[dim]Component:[/dim] {llm_top.component}\n\n"
            f"📊 [bold]Observation:[/bold]\n{llm_top.observation[:200]}...\n\n"
            f"⚡ [bold]Action:[/bold]\n{llm_top.immediate_action[:150]}...",
            title="[cyan]LLM-Powered[/cyan]",
            border_style="cyan",
            width=60
        )

        console.print(Columns([rule_panel, llm_panel]))

    # ============================================================
    # 4. KEY DIFFERENCES
    # ============================================================
    console.print("\n[bold green]📈 Key Advantages of LLM-Powered Analysis:[/bold green]\n")

    advantages = [
        "✅ [cyan]Contextual Understanding[/cyan]: Explains relationships between metrics",
        "✅ [cyan]Natural Language[/cyan]: More readable and actionable insights",
        "✅ [cyan]Deep Reasoning[/cyan]: Explains WHY metrics matter (e.g. context switching)",
        "✅ [cyan]Comprehensive[/cyan]: Better root cause analysis with technical depth",
        "✅ [cyan]Adaptive[/cyan]: Handles nuanced scenarios beyond fixed thresholds",
    ]

    for adv in advantages:
        console.print(f"  {adv}")

    # ============================================================
    # 5. RECOMMENDATIONS
    # ============================================================
    console.print("\n[bold blue]💡 Recommended Usage:[/bold blue]\n")
    console.print("  • [yellow]Quick checks:[/yellow] Use rule-based (faster, <1 sec)")
    console.print("  • [cyan]Deep analysis:[/cyan] Use LLM (slower, 30-60 sec, better insights)")
    console.print("  • [green]Best of both:[/green] Run rule-based first, then LLM for critical issues\n")


if __name__ == "__main__":
    asyncio.run(main())
