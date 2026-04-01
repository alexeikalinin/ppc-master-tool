"""
Competitor discovery.

Priority:
  1. SerpAPI (if SERPAPI_KEY is set) — real search results
  2. AI-powered discovery via OpenAI/Claude (uses site keywords for specificity)
  3. Static stub by niche — always available, no keys needed
"""

import asyncio
import json

_NICHE_COMPETITORS: dict[str, list[str]] = {
    "digital-agency": [
        "pixelplus.ru", "convert.ru", "adlabs.ru", "netpeak.ru",
        "molinos.ru", "kokoc.com", "ingate.ru", "adventum.ru",
    ],
    "e-commerce": [
        "wildberries.ru", "ozon.ru", "market.yandex.ru",
        "megamarket.ru", "sbermegamarket.ru",
    ],
    "services": ["profi.ru", "youdo.com", "remontnik.ru", "zoon.ru", "flamp.ru"],
    "saas": ["bitrix24.ru", "amocrm.ru", "retailcrm.ru", "megaplan.ru", "planfix.ru"],
    "real-estate": ["cian.ru", "domclick.ru", "realty.yandex.ru", "sob.ru", "realty.mail.ru"],
    "medical": [
        "napopravku.ru", "prodoctorov.ru", "docdoc.ru", "sberzdorovye.ru", "medsi.ru",
    ],
    "education": [
        "skillbox.ru", "netology.ru", "geekbrains.ru", "stepik.org", "gb.ru",
    ],
    "finance": ["banki.ru", "sravni.ru", "tinkoff.ru", "raiffeisen.ru", "alfabank.ru"],
}

_DEFAULT_COMPETITORS = ["profi.ru", "avito.ru", "zoon.ru", "flamp.ru", "irecommend.ru"]


async def find_competitors(
    niche: str,
    region: str,
    site_domain: str = "",
    keywords: list | None = None,
) -> list[str]:
    from backend.config import settings

    # 1. SerpAPI — реальные результаты поиска
    if settings.serpapi_key:
        try:
            from backend.integrations.serpapi import search_competitors

            results = await search_competitors(
                niche=niche,
                region=region,
                api_key=settings.serpapi_key,
                site_domain=site_domain,
            )
            if results:
                return results
        except Exception as exc:
            print(f"[serpapi] error: {exc}")

    # 2. AI-поиск конкурентов по ключевым словам сайта
    if keywords and (settings.openai_api_key or settings.anthropic_api_key):
        try:
            results = await _find_competitors_ai(niche, region, site_domain, keywords)
            if results:
                return results
        except Exception as exc:
            print(f"[competitors_ai] error: {exc}")

    await asyncio.sleep(0)
    return _NICHE_COMPETITORS.get(niche, _DEFAULT_COMPETITORS)


async def _find_competitors_ai(
    niche: str,
    region: str,
    site_domain: str,
    keywords: list,
) -> list[str]:
    """Находит реальных конкурентов через AI на основе ключевых слов бизнеса."""
    from backend.config import settings

    # Берём топ-5 ключей по частоте (только Яндекс, без дублей)
    seen_texts: set[str] = set()
    top_kws: list[str] = []
    for kw in sorted(keywords, key=lambda k: -k.frequency):
        if kw.platform == "yandex" and kw.text not in seen_texts and len(top_kws) < 5:
            top_kws.append(kw.text)
            seen_texts.add(kw.text)

    kw_str = ", ".join(top_kws) if top_kws else niche

    from backend.services.region_platforms import get_region_type
    region_label = "России" if get_region_type(region) == "RU" else "Беларуси"

    prompt = f"""Ты PPC-специалист. Назови 5-7 реальных сайтов-конкурентов для интернет-бизнеса в {region_label}.

Ниша: {niche}
Главные ключевые слова: {kw_str}
Сайт клиента (исключи его): {site_domain}

Верни ТОЛЬКО JSON без пояснений:
{{"competitors": ["site1.ru", "site2.ru", "site3.ru", "site4.ru", "site5.ru"]}}

Правила:
- Только реально существующие российские/белорусские сайты
- Прямые конкуренты с теми же товарами или услугами что в ключевых словах
- НЕ включай: поисковики, соцсети, wikipedia, если только они сами не продают те же товары
- НЕ включай сайт клиента: {site_domain}"""

    if settings.openai_api_key:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        r = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = json.loads(r.choices[0].message.content or "{}")
    else:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)

    competitors = data.get("competitors", [])
    # Фильтруем: убираем сайт клиента и явный мусор
    filtered = [c for c in competitors if c and c != site_domain and "." in c]
    return filtered[:7]
