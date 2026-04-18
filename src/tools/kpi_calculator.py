"""
KPI Calculator tool for Module 3 deliverables.
Provides mock calculations for HR/business KPIs.
"""

from __future__ import annotations

from typing import Any


class KPICalculator:
    """Calculate HR and business KPIs for the simulation."""

    # Mock baseline data
    BASELINES = {
        "cross_brand_mobility_rate": 2.3,
        "voluntary_turnover_rate": 12.8,
        "internal_promotion_rate": 45.0,
        "employee_engagement_score": 72.0,
        "training_hours_per_employee": 32.0,
        "time_to_fill_leadership_days": 67.0,
        "360_response_rate": 0.0,  # Not yet implemented
        "workshop_participation_rate": 0.0,
    }

    TARGETS = {
        "cross_brand_mobility_rate": 8.0,
        "voluntary_turnover_rate": 9.0,
        "internal_promotion_rate": 60.0,
        "employee_engagement_score": 80.0,
        "training_hours_per_employee": 48.0,
        "time_to_fill_leadership_days": 45.0,
        "360_response_rate": 85.0,
        "workshop_participation_rate": 90.0,
    }

    @classmethod
    def calculate(cls, kpi_name: str, **kwargs: Any) -> dict[str, Any]:
        """Calculate a specific KPI with optional parameters."""
        if kpi_name not in cls.BASELINES:
            return {
                "error": f"Unknown KPI: {kpi_name}",
                "available_kpis": list(cls.BASELINES.keys()),
            }

        baseline = cls.BASELINES[kpi_name]
        target = cls.TARGETS[kpi_name]
        gap = target - baseline

        return {
            "kpi": kpi_name,
            "baseline": baseline,
            "target": target,
            "gap": round(abs(gap), 1),
            "direction": "increase" if gap > 0 else "decrease",
            "gap_pct": round((abs(gap) / baseline) * 100, 1) if baseline != 0 else None,
            "timeline_months": kwargs.get("timeline_months", 36),
            "monthly_improvement_needed": round(abs(gap) / kwargs.get("timeline_months", 36), 2),
        }

    @classmethod
    def get_dashboard(cls) -> list[dict[str, Any]]:
        """Return all KPIs as a dashboard summary."""
        return [cls.calculate(kpi) for kpi in cls.BASELINES]

    @classmethod
    def roi_estimate(
        cls,
        program_cost_eur: float = 4_200_000,
        turnover_reduction_pct: float = 3.0,
        avg_replacement_cost_eur: float = 85_000,
        headcount: int = 34_500,
    ) -> dict[str, Any]:
        """Estimate ROI of the leadership program."""
        employees_saved = headcount * (turnover_reduction_pct / 100.0)
        savings = employees_saved * avg_replacement_cost_eur
        roi = ((savings - program_cost_eur) / program_cost_eur) * 100

        return {
            "program_cost_eur": program_cost_eur,
            "turnover_reduction_pct": turnover_reduction_pct,
            "employees_retained": round(employees_saved),
            "savings_eur": round(savings),
            "net_benefit_eur": round(savings - program_cost_eur),
            "roi_pct": round(roi, 1),
            "payback_months": round(12 * program_cost_eur / savings, 0) if savings > 0 else None,
        }
