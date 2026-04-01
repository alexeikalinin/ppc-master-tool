"""
Media plan builder: forecasts CR, CPA, and conversions for each campaign.
Supports currency conversion via niche_analysis_ai helpers.
"""

from backend.models import Campaign, MediaPlan, MediaPlanRow

DEFAULT_CR = 0.03  # 3% conversion rate


def build_media_plan(
    campaigns: list[Campaign],
    total_budget: float,
    currency: str = "RUB",
) -> MediaPlan:
    """Compute per-campaign forecast and aggregate totals."""
    from backend.services.niche_analysis_ai import convert_amount

    rows: list[MediaPlanRow] = []

    for camp in campaigns:
        cr = DEFAULT_CR
        # Convert CPC from RUB to target currency for display
        avg_cpc_converted = convert_amount(camp.avg_cpc, currency)
        budget_converted = convert_amount(camp.budget, currency)

        cpa = round(avg_cpc_converted / cr, 2) if cr > 0 else 0.0
        conversions = round(budget_converted / cpa, 2) if cpa > 0 else 0.0
        rows.append(
            MediaPlanRow(
                campaign_name=camp.name,
                platform=camp.platform,
                budget=budget_converted,
                avg_cpc=avg_cpc_converted,
                cr=cr,
                cpa=cpa,
                conversions=conversions,
            )
        )

    actual_budget = sum(r.budget for r in rows)
    total_conversions = round(sum(r.conversions for r in rows), 2)
    avg_cpa = (
        round(actual_budget / total_conversions, 2) if total_conversions > 0 else 0.0
    )

    return MediaPlan(
        rows=rows,
        total_budget=round(actual_budget, 2),
        total_conversions=total_conversions,
        avg_cpa=avg_cpa,
    )
