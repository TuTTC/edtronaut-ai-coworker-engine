"""
GenAI Tool: Rollout Planner.
Generates rollout checklists and RACI matrices.
"""

from __future__ import annotations


class RolloutPlanner:
    """AI-assisted rollout plan generator for Module 3."""

    @classmethod
    def generate_checklist(cls, wave: int = 1) -> str:
        """Generate a rollout checklist for a specific wave."""
        wave_data = {
            1: {
                "countries": "Italy, France, UK",
                "timeline": "Months 1-3",
                "items": [
                    ("Pre-launch", [
                        "☐ Obtain works council approval (France)",
                        "☐ Complete GDPR data processing impact assessment",
                        "☐ Translate materials to Italian and French",
                        "☐ Certify 8 trainers (minimum) across 3 countries",
                        "☐ Customize brand-specific examples for Gucci, Balenciaga, Saint Laurent",
                        "☐ Set up feedback platform with GDPR-compliant data handling",
                    ]),
                    ("Launch", [
                        "☐ Executive sponsor email from Group CEO",
                        "☐ Local HR kickoff webinar (per country)",
                        "☐ First workshops delivered (2 per country in Month 1)",
                        "☐ Self-assessment tool live for pilot group",
                    ]),
                    ("Post-launch", [
                        "☐ Collect participant NPS after each workshop",
                        "☐ Weekly check-in with trainers",
                        "☐ Month 2: Expand to remaining teams",
                        "☐ Month 3: First progress report to leadership",
                    ]),
                ],
            },
            2: {
                "countries": "Germany, Switzerland, Spain & Portugal",
                "timeline": "Months 4-6",
                "items": [
                    ("Pre-launch", [
                        "☐ Obtain works council approval (Germany)",
                        "☐ Translate materials to German, Spanish, Portuguese",
                        "☐ Address brand manager pushback in Germany (change management)",
                        "☐ Certify 6 additional trainers",
                        "☐ Adapt workshop for multi-lingual Swiss context",
                    ]),
                    ("Launch", [
                        "☐ Local HR kickoff with change management emphasis",
                        "☐ First workshops with enhanced 'why' messaging",
                        "☐ Self-assessment tool extended to Wave 2 countries",
                    ]),
                    ("Post-launch", [
                        "☐ Monitor pushback sentiment",
                        "☐ Share Wave 1 success stories as social proof",
                        "☐ Month 6: Consolidated progress report",
                    ]),
                ],
            },
            3: {
                "countries": "Nordics, Eastern Europe",
                "timeline": "Months 7-9",
                "items": [
                    ("Pre-launch", [
                        "☐ Extended trainer certification (2-day + 1 day shadow)",
                        "☐ Translate materials to local languages",
                        "☐ Simplified initial rollout materials",
                        "☐ Video-based pre-training for remote locations",
                    ]),
                    ("Launch", [
                        "☐ Blended approach: virtual + in-person workshops",
                        "☐ Partner with external coaches for initial delivery",
                    ]),
                    ("Post-launch", [
                        "☐ Intensive support for first 2 months",
                        "☐ Month 9: Full European progress report",
                        "☐ Lessons learned compilation for next region",
                    ]),
                ],
            },
        }

        data = wave_data.get(wave, wave_data[1])
        lines = [
            f"**Rollout Checklist — Wave {wave}: {data['countries']}**",
            f"Timeline: {data['timeline']}",
            "",
        ]
        for phase, items in data["items"]:
            lines.append(f"### {phase}")
            for item in items:
                lines.append(f"  {item}")
            lines.append("")

        lines.append("*This is a draft checklist. Please customize based on local needs.*")
        return "\n".join(lines)

    @classmethod
    def generate_raci(cls) -> str:
        """Generate a RACI matrix for the rollout."""
        lines = [
            "**RACI Matrix — European Rollout**",
            "",
            "| Activity | Group OD Dir | CHRO | Regional Mgr | Local HR | Trainers | Brand Mgrs |",
            "|:---|:---|:---|:---|:---|:---|:---|",
            "| Framework design | **R/A** | C | I | I | I | C |",
            "| Material translation | C | I | **R** | **A** | C | I |",
            "| Trainer certification | C | A | **R** | C | **R** | I |",
            "| Works council approval | C | A | **R** | **R** | I | I |",
            "| Workshop delivery | I | I | C | A | **R** | I |",
            "| Progress reporting | **R** | **A** | C | C | I | I |",
            "| Change management | **R** | C | **A** | C | I | C |",
            "| KPI measurement | **R** | A | C | **R** | I | I |",
            "",
            "R = Responsible, A = Accountable, C = Consulted, I = Informed",
            "",
            "*This is a draft RACI. Please validate with stakeholders.*",
        ]
        return "\n".join(lines)
