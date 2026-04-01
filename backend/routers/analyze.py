from fastapi import APIRouter, HTTPException
from urllib.parse import urlparse

from backend.models import AnalyzeRequest, AnalyzeResponse, SUPPORTED_CURRENCIES
from backend.services.parser import parse_site
from backend.services.competitors import find_competitors
from backend.services.keywords import get_keywords
from backend.services.clustering import cluster_keywords
from backend.services.audience import infer_audience
from backend.services.campaigns import generate_campaigns
from backend.services.media_plan import build_media_plan
from backend.services.ai_summary import generate_summary
from backend.services.niche_analysis_ai import analyze_niche
from backend.services.region_platforms import get_region_label

router = APIRouter()


@router.post("", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """
    Run the full PPC analysis pipeline.
    Auth dependency will be added in Phase 3.
    """
    # Validate URL
    parsed = urlparse(req.url)
    if not parsed.scheme or not parsed.netloc:
        raise HTTPException(
            status_code=422, detail="Invalid URL. Must include scheme (https://)"
        )

    # Validate currency
    currency = req.currency.upper() if req.currency else "RUB"
    if currency not in SUPPORTED_CURRENCIES:
        currency = "RUB"

    site = await parse_site(req.url)

    # Allow manual niche override
    if req.niche:
        site.niche = req.niche

    site_domain = parsed.netloc.removeprefix("www.")

    # Keywords сначала — нужны для AI-поиска конкурентов
    keywords = await get_keywords(
        niche=site.niche,
        region=req.region,
        hints=site.keywords_hint,
    )

    # Конкуренты: AI использует ключевые слова для точного поиска в нише
    competitors = await find_competitors(
        niche=site.niche,
        region=req.region,
        site_domain=site_domain,
        keywords=keywords,
    )

    groups = cluster_keywords(keywords)
    audience = infer_audience(site.niche, keywords, region_code=req.region)

    # AI niche analysis + budget recommendation (runs in parallel with other work)
    niche_insight, budget_recommendation = await analyze_niche(
        site=site,
        keywords=keywords,
        region=req.region,
        city=req.city,
        currency=currency,
    )

    # Use city name in ad copy if provided, otherwise region label
    region_label = get_region_label(req.region, req.city)

    # If no budget provided, use AI recommended optimal budget (in RUB for campaign calc)
    from backend.services.niche_analysis_ai import to_rub
    if req.budget:
        # User budget is in the selected currency → convert to RUB for internal calculations
        budget_rub = to_rub(req.budget, currency)
    else:
        # Use AI-recommended optimal budget (already in target currency → convert to RUB)
        budget_rub = to_rub(budget_recommendation.recommended_optimal, currency)

    campaigns = generate_campaigns(
        groups=groups,
        audience=audience,
        budget=budget_rub,
        region=region_label,
        site_url=site_domain,
        niche=site.niche,
        region_code=req.region,
    )

    media_plan = build_media_plan(campaigns, budget_rub, currency=currency)

    ai_summary = await generate_summary(
        site=site,
        competitors=competitors,
        campaigns=campaigns,
        audience=audience,
        media_plan=media_plan,
        region=req.region,
        city=req.city,
        budget=budget_rub,
    )

    response = AnalyzeResponse(
        currency=currency,
        site=site,
        competitors=competitors,
        keywords=keywords,
        groups=groups,
        audience=audience,
        campaigns=campaigns,
        media_plan=media_plan,
        ai_summary=ai_summary,
        niche_insight=niche_insight,
        budget_recommendation=budget_recommendation,
    )

    # Сохраняем в Supabase (best-effort — не блокирует ответ при ошибке DB)
    try:
        from backend import db
        report_id = await db.save_report(
            user_id=None,
            url=req.url,
            region=req.region,
            json_data=response.model_dump(),
        )
        response.report_id = report_id
    except Exception as exc:
        print(f"[db] save_report failed: {exc}")

    return response
