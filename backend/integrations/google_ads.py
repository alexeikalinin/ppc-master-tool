"""
Google Keyword Planner integration via google-ads-python library.

Required .env vars:
  GOOGLE_ADS_CLIENT_ID
  GOOGLE_ADS_CLIENT_SECRET
  GOOGLE_ADS_DEVELOPER_TOKEN
  GOOGLE_ADS_REFRESH_TOKEN
  GOOGLE_ADS_CUSTOMER_ID

Install: pip install google-ads (commented out in requirements.txt by default)
Docs: https://developers.google.com/google-ads/api/docs/keyword-planning/overview
"""

from backend.models import Keyword

# Locale → language_id mapping (ISO 639-1 to Google language resource)
_LANGUAGE_IDS: dict[str, str] = {
    "RU": "1031",  # Russian
    "UA": "1031",  # Russian (Ukraine)
    "US": "1000",  # English
    "EU": "1001",  # French as fallback
}

# Region → geo target constant ID
_GEO_IDS: dict[str, str] = {
    "RU": "2643",  # Russia
    "UA": "2804",  # Ukraine
    "BY": "2112",  # Belarus
    "KZ": "2398",  # Kazakhstan
    "US": "2840",  # USA
}


def _build_client(settings) -> "googleads.GoogleAdsClient":  # type: ignore[name-defined]
    """Build Google Ads client from pydantic settings."""
    # google-ads uses a YAML config or dict
    credentials = {
        "developer_token": settings.google_ads_developer_token,
        "client_id": settings.google_ads_client_id,
        "client_secret": settings.google_ads_client_secret,
        "refresh_token": settings.google_ads_refresh_token,
        "use_proto_plus": True,
    }
    from google.ads.googleads.client import GoogleAdsClient

    return GoogleAdsClient.load_from_dict(credentials)


async def fetch_keyword_ideas(
    seed_keywords: list[str],
    region: str = "RU",
) -> list[Keyword]:
    """
    Fetch keyword ideas + search volume + CPC from Google Keyword Planner.
    Runs in a thread pool (google-ads SDK is synchronous).
    """
    import asyncio

    return await asyncio.get_event_loop().run_in_executor(
        None, _fetch_sync, seed_keywords, region
    )


def _fetch_sync(seed_keywords: list[str], region: str) -> list[Keyword]:
    from backend.config import settings

    client = _build_client(settings)
    customer_id = settings.google_ads_customer_id.replace("-", "")

    kp_service = client.get_service("KeywordPlanIdeaService")
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.language = f"languageConstants/{_LANGUAGE_IDS.get(region, '1031')}"
    request.geo_target_constants.append(
        f"geoTargetConstants/{_GEO_IDS.get(region, '2643')}"
    )
    request.include_adult_keywords = False
    request.keyword_seed.keywords.extend(seed_keywords[:20])

    results: list[Keyword] = []
    for idea in kp_service.generate_keyword_ideas(request=request):
        metrics = idea.keyword_idea_metrics
        freq = metrics.avg_monthly_searches
        # CPC in micros → RUB
        cpc = (
            round(metrics.average_cpc_micros / 1_000_000, 2)
            if metrics.average_cpc_micros
            else 0.0
        )
        results.append(
            Keyword(
                text=idea.text,
                frequency=freq,
                cpc=cpc,
                platform="google",
            )
        )
    return sorted(results, key=lambda k: k.frequency, reverse=True)[:100]
