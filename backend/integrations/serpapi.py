"""
SerpAPI integration for competitor discovery.

Searches Google/Yandex for top sites in a given niche+region
and extracts organic result domains.

Required: SERPAPI_KEY in .env
Docs: https://serpapi.com/search-api
"""

from urllib.parse import urlparse

import httpx

_SERPAPI_URL = "https://serpapi.com/search"

# SerpAPI Google country codes
_COUNTRY_CODES: dict[str, str] = {
    "RU": "ru",
    "UA": "ua",
    "BY": "by",
    "KZ": "kz",
    "US": "us",
    "EU": "de",
}

# SerpAPI Google language codes
_LANG_CODES: dict[str, str] = {
    "RU": "ru",
    "UA": "uk",
    "BY": "ru",
    "KZ": "ru",
    "US": "en",
    "EU": "en",
}


async def search_competitors(
    niche: str,
    region: str,
    api_key: str,
    site_domain: str = "",
    n: int = 10,
) -> list[str]:
    """
    Return top competitor domains for the given niche+region via SerpAPI.
    Excludes the analysed site's own domain.
    """
    query = _build_query(niche, region)
    params = {
        "q": query,
        "api_key": api_key,
        "engine": "google",
        "gl": _COUNTRY_CODES.get(region, "ru"),
        "hl": _LANG_CODES.get(region, "ru"),
        "num": 20,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(_SERPAPI_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    domains: list[str] = []
    for result in data.get("organic_results", []):
        link = result.get("link", "")
        domain = _extract_domain(link)
        if not domain:
            continue
        if site_domain and domain == site_domain:
            continue
        if domain not in domains:
            domains.append(domain)
        if len(domains) >= n:
            break

    return domains


def _build_query(niche: str, region: str) -> str:
    niche_queries: dict[str, str] = {
        "e-commerce": "интернет магазин",
        "services": "заказать услугу",
        "saas": "crm система онлайн",
        "real-estate": "продажа квартир",
        "medical": "медицинская клиника",
        "education": "онлайн курсы обучение",
        "finance": "кредит онлайн банк",
    }
    region_names: dict[str, str] = {
        "RU": "Россия",
        "UA": "Украина",
        "BY": "Беларусь",
        "KZ": "Казахстан",
        "US": "",
    }
    base = niche_queries.get(niche, niche)
    geo = region_names.get(region, "")
    return f"{base} {geo}".strip()


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return domain.removeprefix("www.")
    except Exception:
        return ""
