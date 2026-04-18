"""
GenAI Tool: Feedback Synthesizer.
Synthesizes 360° feedback patterns from mock data.
"""

from __future__ import annotations


class FeedbackSynthesizer:
    """AI-assisted 360° feedback pattern synthesis."""

    MOCK_FEEDBACK_DATA = {
        "sample_leader_1": {
            "name": "Anonymous Leader A (Gucci, Senior)",
            "self_assessment": {"Vision": 4.2, "Entrepreneurship": 3.8, "Passion": 4.5, "Trust": 4.0},
            "manager_assessment": {"Vision": 3.8, "Entrepreneurship": 3.5, "Passion": 4.6, "Trust": 3.7},
            "peer_assessment": {"Vision": 3.5, "Entrepreneurship": 3.2, "Passion": 4.3, "Trust": 3.9},
            "direct_report_assessment": {"Vision": 4.0, "Entrepreneurship": 3.0, "Passion": 4.4, "Trust": 3.5},
        },
        "sample_leader_2": {
            "name": "Anonymous Leader B (Bottega Veneta, Mid)",
            "self_assessment": {"Vision": 3.5, "Entrepreneurship": 4.0, "Passion": 3.8, "Trust": 4.2},
            "manager_assessment": {"Vision": 3.0, "Entrepreneurship": 4.2, "Passion": 3.5, "Trust": 4.0},
            "peer_assessment": {"Vision": 2.8, "Entrepreneurship": 4.1, "Passion": 3.6, "Trust": 4.3},
            "direct_report_assessment": {"Vision": 3.2, "Entrepreneurship": 3.8, "Passion": 3.4, "Trust": 4.5},
        },
    }

    @classmethod
    def synthesize(cls, leader_id: str = "sample_leader_1") -> str:
        """Synthesize feedback patterns for a sample leader."""
        data = cls.MOCK_FEEDBACK_DATA.get(leader_id)
        if not data:
            return "No feedback data available for this leader."

        lines = [
            f"**360° Feedback Synthesis: {data['name']}**",
            "",
            "| Theme | Self | Manager | Peers | Direct Reports | Gap Analysis |",
            "|:---|:---|:---|:---|:---|:---|",
        ]

        for theme in ["Vision", "Entrepreneurship", "Passion", "Trust"]:
            self_score = data["self_assessment"][theme]
            mgr = data["manager_assessment"][theme]
            peer = data["peer_assessment"][theme]
            dr = data["direct_report_assessment"][theme]
            avg_others = round((mgr + peer + dr) / 3, 1)
            gap = round(self_score - avg_others, 1)

            gap_label = "Aligned" if abs(gap) < 0.3 else (
                "Self-overrate" if gap > 0 else "Hidden strength"
            )
            lines.append(
                f"| {theme} | {self_score} | {mgr} | {peer} | {dr} | {gap_label} ({gap:+.1f}) |"
            )

        lines.extend([
            "",
            "**Key Patterns:**",
            "- Strongest theme across all raters: Passion",
            "- Largest development gap: Entrepreneurship (self vs. direct reports)",
            "- Trust perception differs between peers (higher) and direct reports (lower)",
            "",
            "*This is a draft synthesis based on sample data.*",
        ])

        return "\n".join(lines)

    @classmethod
    def list_available(cls) -> list[str]:
        """List available sample leaders."""
        return list(cls.MOCK_FEEDBACK_DATA.keys())
