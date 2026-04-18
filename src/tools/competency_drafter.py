"""
GenAI Tool: Competency Drafter.
Assists users in drafting competency model components.
In mock mode, returns pre-built templates.
"""

from __future__ import annotations


class CompetencyDrafter:
    """AI-assisted competency model drafting tool."""

    TEMPLATES = {
        "behavior_indicator": {
            "Vision": {
                "Associate": "Understands and can articulate the brand's market position and connects daily work to broader strategy.",
                "Mid": "Translates Group strategy into actionable plans and anticipates market shifts to adapt priorities.",
                "Senior": "Shapes long-term strategic direction and identifies transformative opportunities for competitive advantage.",
            },
            "Entrepreneurship": {
                "Associate": "Proposes incremental improvements and takes ownership of small projects with accountability.",
                "Mid": "Launches new initiatives generating measurable business value while balancing risk and reward.",
                "Senior": "Drives business model innovation and creates environments where calculated risk-taking is celebrated.",
            },
            "Passion": {
                "Associate": "Demonstrates genuine enthusiasm for brand products and heritage with strong attention to detail.",
                "Mid": "Inspires team with visible commitment to craft excellence and protects brand standards under pressure.",
                "Senior": "Serves as a cultural ambassador and builds an organizational culture where quality is non-negotiable.",
            },
            "Trust": {
                "Associate": "Communicates openly, follows through on commitments, and builds collaborative relationships.",
                "Mid": "Creates psychologically safe environments, delegates effectively, and navigates conflicts with integrity.",
                "Senior": "Models transparency at organizational level and creates governance balancing autonomy with accountability.",
            },
        },
        "problem_statement": (
            "DRAFT PROBLEM STATEMENT:\n\n"
            "Gucci Group's 9 luxury brands thrive on autonomous identities, but this autonomy has "
            "created fragmented leadership development and critically low cross-brand mobility (2.3% "
            "vs. 8% industry benchmark). Rising mid-level turnover (3-7 year tenure cohort) signals "
            "that high-potential leaders see limited career paths beyond their current brand.\n\n"
            "The challenge: Design a Group-level leadership system that codifies a shared 'Group DNA' "
            "without homogenizing brand identities — enabling talent to be assessed, developed, and "
            "deployed across brands while preserving the creative autonomy that makes each brand "
            "worth billions.\n\n"
            "— This is a draft recommendation based on available internal data. Please customize."
        ),
    }

    @classmethod
    def draft_indicator(cls, theme: str, level: str) -> str:
        """Draft a behavior indicator for a given theme and level."""
        indicators = cls.TEMPLATES.get("behavior_indicator", {})
        theme_data = indicators.get(theme)
        if theme_data and level in theme_data:
            return f"*Draft recommendation:* {theme_data[level]}"
        return (
            f"*Draft recommendation:* [Auto-draft for {theme}/{level} not available. "
            f"Please describe the expected behaviors for a {level}-level leader "
            f"demonstrating {theme} in a luxury brand context.]"
        )

    @classmethod
    def draft_problem_statement(cls) -> str:
        """Generate a draft problem statement."""
        return cls.TEMPLATES["problem_statement"]

    @classmethod
    def draft_competency_matrix(cls) -> str:
        """Generate a draft competency matrix in CSV-like format."""
        lines = ["Theme,Level,Behavior Indicator"]
        indicators = cls.TEMPLATES["behavior_indicator"]
        for theme, levels in indicators.items():
            for level, indicator in levels.items():
                lines.append(f'"{theme}","{level}","{indicator}"')
        return "\n".join(lines)
