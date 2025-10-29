"""Brendan Gregg persona entity."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class BrendanPersona:
    """Entity representing Brendan Gregg's analysis persona."""

    name: str = "Brendan Gregg"
    expertise: List[str] = field(
        default_factory=lambda: [
            "USE Method",
            "BPF (eBPF)",
            "Systems Performance",
            "Linux Performance",
            "Cloud Performance",
        ]
    )
    analysis_style: str = "Technical, thorough, evidence-based"
    communication_style: str = "Clear, concise, with practical examples"

    def format_insight(self, insight: str, metrics_context: str = "") -> str:
        """Format insight in Brendan Gregg's style."""
        formatted = f"🔍 **{self.name} Analysis**\n\n"
        formatted += f"**Insight:** {insight}\n"

        if metrics_context:
            formatted += f"**Context:** {metrics_context}\n"

        formatted += f"\n**Recommendation:** Based on the USE Method, "
        formatted += "we should investigate Utilization, Saturation, and Errors."

        return formatted

    def get_expertise_areas(self) -> List[str]:
        """Get expertise areas."""
        return self.expertise.copy()

    def is_expert_in(self, area: str) -> bool:
        """Check if persona is expert in given area."""
        return area.lower() in [exp.lower() for exp in self.expertise]
