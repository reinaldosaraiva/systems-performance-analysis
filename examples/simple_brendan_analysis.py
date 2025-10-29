#!/usr/bin/env python3
"""
Simple Brendan Gregg Persona Usage Example

This is a minimal example showing how to use the Brendan Gregg persona
for quick system performance analysis.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from brendan_gregg_persona import BrendanGreggPersona


async def main():
    """Simple analysis example."""

    print("🎯 Brendan Gregg Persona - Quick Analysis")
    print("=" * 60)

    # Initialize persona (uses localhost by default)
    persona = BrendanGreggPersona()

    print("\n📊 Running USE Method Analysis...")
    print("   Checking: CPU, Memory, Disk, Network")
    print("   Methodology: Utilization, Saturation, Errors\n")

    # Run USE Method
    insights = await persona.analyze_use_method()

    # Display results
    if insights:
        print(f"⚠️  Found {len(insights)} performance issue(s):\n")

        for i, insight in enumerate(insights, 1):
            severity_emoji = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "⚡",
                "low": "💡",
            }.get(insight.severity, "ℹ️")

            print(f"{severity_emoji} [{i}] {insight.title}")
            print(f"    Component: {insight.component}")
            print(f"    Severity: {insight.severity.upper()}")
            print(f"    {insight.observation}")
            print(f"\n    💡 Immediate Action:")
            print(f"    {insight.immediate_action}\n")

        # Generate full report
        print("\n📄 Generating detailed report...\n")
        report = persona.generate_brendan_style_report(insights)

        # Save report
        report_file = f"brendan_analysis_simple.txt"
        Path("reports").mkdir(exist_ok=True)
        with open(f"reports/{report_file}", "w") as f:
            f.write(report)

        print(f"✅ Report saved to: reports/{report_file}")

    else:
        print("✅ No performance issues detected!")
        print("   System is operating within normal parameters.")

    print("\n" + "=" * 60)
    print("Analysis complete. Review the report for details.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
