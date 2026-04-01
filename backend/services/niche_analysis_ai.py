"""
AI-powered niche analysis service.

Calls LLM (Claude → OpenAI → stub fallback) to produce:
  - Deep niche understanding (what the business does)
  - Primary audience + pain points
  - Campaign type recommendations with reasoning
  - Suggested campaign structure (2-4 campaigns)
  - Best strategies for the niche
  - Budget recommendation based on search volume + CPC

Provider priority: Anthropic Claude → OpenAI → stub
"""

import json
from backend.models import (
    BudgetRecommendation,
    CampaignStructureItem,
    NicheInsight,
    Keyword,
    SiteData,
)

# Currency conversion rates (approximate, relative to RUB)
_CURRENCY_RATES: dict[str, float] = {
    "RUB": 1.0,
    "BYN": 0.034,    # ~1 BYN = 29 RUB
    "USD": 0.011,    # ~1 USD = 90 RUB
    "EUR": 0.010,    # ~1 EUR = 100 RUB
    "KZT": 5.0,      # ~1 KZT = 0.20 RUB
}

_CURRENCY_SYMBOLS: dict[str, str] = {
    "RUB": "₽",
    "BYN": "Br",
    "USD": "$",
    "EUR": "€",
    "KZT": "₸",
}


def convert_amount(amount_rub: float, currency: str) -> float:
    """Convert RUB amount to target currency."""
    rate = _CURRENCY_RATES.get(currency, 1.0)
    return round(amount_rub * rate, 2)


def to_rub(amount: float, currency: str) -> float:
    """Convert amount in given currency back to RUB."""
    rate = _CURRENCY_RATES.get(currency, 1.0)
    return round(amount / rate, 2) if rate > 0 else amount


def get_currency_symbol(currency: str) -> str:
    return _CURRENCY_SYMBOLS.get(currency, currency)


# ── Prompt builder ─────────────────────────────────────────────────────────────

def _build_niche_prompt(
    site: SiteData,
    keywords: list[Keyword],
    region: str,
    city: str | None,
    currency: str,
) -> str:
    from backend.services.region_platforms import get_region_type
    region_type = get_region_type(region)

    geo = city or region
    top_kws = sorted(keywords, key=lambda k: -k.frequency)[:15]
    kw_lines = "\n".join(
        f"  - {kw.text}: {kw.frequency:,} запросов/мес, CPC={kw.cpc:.0f} ₽"
        for kw in top_kws
    )
    avg_cpc = round(sum(k.cpc for k in top_kws) / max(len(top_kws), 1), 0) if top_kws else 50
    total_vol = sum(k.frequency for k in top_kws)
    curr_symbol = _CURRENCY_SYMBOLS.get(currency, currency)
    rate = _CURRENCY_RATES.get(currency, 1.0)

    if region_type == "RU":
        platform_note = """
ВАЖНО (рынок РФ): Google Ads заблокирован в России с марта 2022 и недоступен рекламодателям.
Доступные платформы: Яндекс.Директ (поиск + РСЯ), VK Реклама, myTarget.
В recommended_campaign_types используй только: "search" (Яндекс Директ), "display" (РСЯ), "retargeting", "vk", "smart".
НЕ рекомендуй "google" ни в каком виде."""
    else:
        platform_note = """
Доступные платформы: Google Ads, Яндекс.Директ, VK Реклама."""

    return f"""Ты — старший PPC-стратег с опытом 10+ лет в русскоязычном рынке. Проанализируй нишу и верни ТОЛЬКО JSON без комментариев.
{platform_note}

Данные о сайте:
- Сайт: {site.title}
- Описание: {site.description}
- Определённая ниша: {site.niche}
- Регион: {geo}

Топ ключевых слов (из Wordstat):
{kw_lines}

Суммарный объём поиска по топ-ключам: {total_vol:,} запросов/мес
Средний CPC: {avg_cpc:.0f} ₽
Целевая валюта отчёта: {currency} ({curr_symbol})

Верни JSON строго следующей структуры (без markdown, без пояснений, только JSON):
{{
  "business_description": "1-2 предложения: что делает бизнес, его главная ценность",
  "primary_audience": "кто основная ЦА: описание в 1-2 предложениях",
  "audience_pain_points": [
    "боль/потребность 1",
    "боль/потребность 2",
    "боль/потребность 3",
    "боль/потребность 4",
    "боль/потребность 5"
  ],
  "recommended_campaign_types": ["search", "retargeting"],
  "campaign_type_reasoning": "Объяснение почему именно эти типы кампаний подходят для этой ниши (2-3 предложения)",
  "suggested_campaign_structure": [
    {{
      "name": "Название кампании 1",
      "keywords_focus": "тематика ключевых слов для этой кампании",
      "goal": "цель и KPI кампании"
    }},
    {{
      "name": "Название кампании 2",
      "keywords_focus": "тематика ключевых слов",
      "goal": "цель и KPI"
    }},
    {{
      "name": "Название кампании 3",
      "keywords_focus": "тематика ключевых слов",
      "goal": "цель и KPI"
    }}
  ],
  "best_strategies": [
    "Стратегия 1 с конкретным советом",
    "Стратегия 2 с конкретным советом",
    "Стратегия 3 с конкретным советом"
  ],
  "competition_notes": "Комментарий о конкуренции в нише: насколько высокая, на что обратить внимание",
  "budget_min_rub": <минимальный тестовый бюджет в рублях (число)>,
  "budget_optimal_rub": <оптимальный бюджет в рублях (число)>,
  "budget_aggressive_rub": <агрессивный бюджет в рублях (число)>,
  "budget_reasoning": "Обоснование рекомендации бюджета на основе CPC и объёма поиска",
  "monthly_clicks_estimate": <прогноз кликов в месяц при оптимальном бюджете (число)>,
  "monthly_leads_estimate": <прогноз лидов в месяц при оптимальном бюджете (число)>
}}

Важно:
- Бюджет считай исходя из: avg_cpc={avg_cpc:.0f} ₽, суммарный объём={total_vol:,}/мес, CTR поиска ~5-8%, конверсия сайта ~2-4%
- "search" — поисковые кампании в Яндекс.Директ и/или Google Ads
- "display" — РСЯ / КМС (контекстно-медийная сеть)
- "retargeting" — ретаргетинг на аудиторию сайта
- "smart" — смарт-кампании / Performance Max
- "vk" — таргетированная реклама ВКонтакте
- Предложи 2-4 кампании в структуре, логично разбитых по продуктам/услугам или аудиториям"""


# ── LLM callers ────────────────────────────────────────────────────────────────

async def _call_claude(prompt: str) -> dict:
    import anthropic
    from backend.config import settings

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    msg = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


async def _call_openai(prompt: str) -> dict:
    from openai import AsyncOpenAI
    from backend.config import settings

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    r = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1500,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(r.choices[0].message.content or "{}")


# ── Stub fallback ──────────────────────────────────────────────────────────────

_NICHE_STUB: dict[str, dict] = {
    "digital-agency": {
        "business_description": "Digital-агентство, предоставляющее услуги настройки контекстной рекламы, SEO и SMM для малого и среднего бизнеса.",
        "primary_audience": "Владельцы МСБ и маркетологи компаний, которые хотят привлечь клиентов через интернет.",
        "audience_pain_points": [
            "Не знают, как настроить рекламу самостоятельно",
            "Сливают бюджет без результата",
            "Не понимают отчёты рекламных кабинетов",
            "Нужны лиды быстро и по фиксированной цене",
            "Боятся обмана со стороны подрядчиков",
        ],
        "recommended_campaign_types": ["search", "retargeting"],
        "campaign_type_reasoning": "Поисковые кампании закрывают горячий спрос — клиент уже ищет исполнителя. Ретаргетинг возвращает тех, кто изучал сайт но не оставил заявку.",
        "suggested_campaign_structure": [
            {"name": "Поиск — Настройка рекламы", "keywords_focus": "настройка яндекс директ, контекстная реклама цена", "goal": "Лидогенерация, CPA < 2000 ₽"},
            {"name": "Поиск — Комплексный маркетинг", "keywords_focus": "интернет-маркетинг, продвижение сайта", "goal": "Лидогенерация широкой аудитории"},
            {"name": "Ретаргетинг — Возврат посетителей", "keywords_focus": "аудитория сайта", "goal": "Возврат и дожим, CPA < 800 ₽"},
        ],
        "best_strategies": [
            "Акцент на уникальное торговое предложение: гарантия заявок или возврат денег",
            "Таргетинг по конкурентам: ключи с названиями известных агентств",
            "Лид-магнит: бесплатный аудит текущей рекламы для входа в воронку",
        ],
        "competition_notes": "Высокая конкуренция. Крупные игроки занимают топ, CPC выше среднего. Дифференцируйтесь специализацией или гарантиями.",
        "budget_min_rub": 30000,
        "budget_optimal_rub": 60000,
        "budget_aggressive_rub": 120000,
        "budget_reasoning": "При средн. CPC 80 ₽ и CR 3% оптимальный бюджет даёт ~750 кликов и ~22 лида/мес.",
        "monthly_clicks_estimate": 750,
        "monthly_leads_estimate": 22,
    },
}

_DEFAULT_STUB = {
    "business_description": "Бизнес в сфере услуг или товаров, ориентированный на привлечение клиентов через интернет.",
    "primary_audience": "Целевая аудитория, заинтересованная в продукте или услуге компании.",
    "audience_pain_points": [
        "Ищут решение конкретной проблемы",
        "Сравнивают предложения конкурентов",
        "Важна цена и скорость",
        "Нужны гарантии качества",
        "Хотят удобный способ заказа",
    ],
    "recommended_campaign_types": ["search", "retargeting"],
    "campaign_type_reasoning": "Поисковые кампании работают с уже сформированным спросом. Ретаргетинг дожимает аудиторию, которая уже знакома с брендом.",
    "suggested_campaign_structure": [
        {"name": "Поиск — Горячий спрос", "keywords_focus": "целевые коммерческие запросы", "goal": "Лидогенерация"},
        {"name": "Поиск — Информационный", "keywords_focus": "информационные и сравнительные запросы", "goal": "Охват и узнаваемость"},
        {"name": "Ретаргетинг", "keywords_focus": "аудитория сайта", "goal": "Возврат посетителей"},
    ],
    "best_strategies": [
        "Поисковые кампании с точным соответствием для горячего спроса",
        "A/B тестирование объявлений для снижения CPA",
        "Минус-слова для очистки нерелевантного трафика",
    ],
    "competition_notes": "Конкуренция в нише средняя. Рекомендуется начать с тестового бюджета для определения реального CPC.",
    "budget_min_rub": 20000,
    "budget_optimal_rub": 50000,
    "budget_aggressive_rub": 100000,
    "budget_reasoning": "Тестовый бюджет для получения статистики и оптимизации кампаний.",
    "monthly_clicks_estimate": 500,
    "monthly_leads_estimate": 15,
}


def _stub_insight(niche: str) -> dict:
    return _NICHE_STUB.get(niche, _DEFAULT_STUB)


# ── Parse LLM response ─────────────────────────────────────────────────────────

def _parse_insight(data: dict, currency: str) -> tuple[NicheInsight, BudgetRecommendation]:
    structure = [
        CampaignStructureItem(
            name=item.get("name", ""),
            keywords_focus=item.get("keywords_focus", ""),
            goal=item.get("goal", ""),
        )
        for item in data.get("suggested_campaign_structure", [])
    ]

    insight = NicheInsight(
        business_description=data.get("business_description", ""),
        primary_audience=data.get("primary_audience", ""),
        audience_pain_points=data.get("audience_pain_points", []),
        recommended_campaign_types=data.get("recommended_campaign_types", ["search"]),
        campaign_type_reasoning=data.get("campaign_type_reasoning", ""),
        suggested_campaign_structure=structure,
        best_strategies=data.get("best_strategies", []),
        competition_notes=data.get("competition_notes", ""),
    )

    min_rub = float(data.get("budget_min_rub", 20000))
    opt_rub = float(data.get("budget_optimal_rub", 50000))
    agg_rub = float(data.get("budget_aggressive_rub", 100000))

    budget_rec = BudgetRecommendation(
        currency=currency,
        recommended_min=convert_amount(min_rub, currency),
        recommended_optimal=convert_amount(opt_rub, currency),
        recommended_aggressive=convert_amount(agg_rub, currency),
        reasoning=data.get("budget_reasoning", ""),
        monthly_clicks_estimate=int(data.get("monthly_clicks_estimate", 0)),
        monthly_leads_estimate=int(data.get("monthly_leads_estimate", 0)),
    )

    return insight, budget_rec


# ── Public API ─────────────────────────────────────────────────────────────────

async def analyze_niche(
    site: SiteData,
    keywords: list[Keyword],
    region: str,
    city: str | None,
    currency: str = "RUB",
) -> tuple[NicheInsight, BudgetRecommendation]:
    """
    Run AI niche analysis. Returns (NicheInsight, BudgetRecommendation).
    Falls back gracefully to stub if no AI key is available.
    """
    from backend.config import settings

    prompt = _build_niche_prompt(site, keywords, region, city, currency)
    data: dict | None = None

    provider = (settings.ai_provider or "").lower()

    # Respect explicit AI_PROVIDER setting; otherwise try Anthropic → OpenAI
    try_anthropic = settings.anthropic_api_key and provider in ("", "anthropic")
    try_openai    = settings.openai_api_key    and provider in ("", "openai")

    if try_anthropic:
        try:
            data = await _call_claude(prompt)
        except Exception as exc:
            print(f"[niche_analysis] Claude error: {exc}")

    if data is None and try_openai:
        try:
            data = await _call_openai(prompt)
        except Exception as exc:
            print(f"[niche_analysis] OpenAI error: {exc}")

    # Stub fallback
    if data is None:
        print("[niche_analysis] No AI key available, using stub")
        data = _stub_insight(site.niche)

    return _parse_insight(data, currency)
