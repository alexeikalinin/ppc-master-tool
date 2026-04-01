"""
Keyword research service.

Priority chain:
  1. Yandex Wordstat API  (if YANDEX_WORDSTAT_TOKEN is set)
  2. Google Keyword Planner (if all GOOGLE_ADS_* vars are set)
  3. Synthetic stub — always available, no keys needed

After fetching keywords, pytrends enriches each with a seasonality multiplier.
"""

import asyncio
import hashlib
import math
import random

from backend.models import Keyword

# ---------- Niche seed data (used in stub mode) ----------

_NICHE_SEEDS: dict[str, list[str]] = {
    "digital-agency": [
        "настройка контекстной рекламы",
        "яндекс директ настройка",
        "google ads настройка",
        "таргетированная реклама вк",
        "реклама в интернете цена",
        "smm агентство",
        "ведение рекламных кампаний",
        "настройка рекламы под ключ",
        "контекстная реклама для бизнеса",
        "продвижение в социальных сетях",
        "реклама для малого бизнеса",
        "интернет-маркетинг агентство",
        "настройка яндекс директ цена",
        "реклама в google стоимость",
        "аудит рекламных кампаний",
    ],
    "e-commerce": [
        "купить",
        "цена",
        "интернет-магазин",
        "доставка",
        "скидка",
        "отзывы",
        "каталог",
        "заказать онлайн",
        "бесплатная доставка",
        "акция",
    ],
    "services": [
        "заказать услугу",
        "стоимость",
        "специалист",
        "вызов мастера",
        "работа под ключ",
        "недорого",
        "с гарантией",
        "отзывы",
        "прайс",
        "запись онлайн",
    ],
    "saas": [
        "crm система",
        "автоматизация",
        "бесплатный тариф",
        "облачный сервис",
        "интеграция",
        "api",
        "демо",
        "пробный период",
        "тарифы",
        "подключить",
    ],
    "real-estate": [
        "купить квартиру",
        "аренда",
        "ипотека",
        "новостройка",
        "вторичное жилье",
        "риелтор",
        "без посредников",
        "срочная продажа",
        "оценка недвижимости",
        "жск",
    ],
    "medical": [
        "записаться к врачу",
        "консультация",
        "лечение",
        "диагностика",
        "клиника рядом",
        "платная клиника",
        "узи",
        "анализы",
        "вызов врача на дом",
        "страховка",
    ],
    "education": [
        "онлайн курс",
        "обучение",
        "сертификат",
        "дистанционно",
        "курсы программирования",
        "записаться на курс",
        "стоимость обучения",
        "отзывы студентов",
        "трудоустройство",
        "скидка",
    ],
    "finance": [
        "кредит онлайн",
        "заявка на кредит",
        "процентная ставка",
        "рефинансирование",
        "одобрение быстро",
        "без справок",
        "займ",
        "кредитная карта",
        "ипотека",
        "накопительный счет",
    ],
}

_DEFAULT_SEEDS = [
    "купить",
    "заказать",
    "цена",
    "услуга",
    "онлайн",
    "отзывы",
    "рядом",
    "недорого",
]

_CPC_RANGES: dict[str, tuple[float, float]] = {
    # Диапазоны для Яндекс.Директ Поиск (Москва/РФ) — на основе PPC-анализа 2025
    # Источник: отраслевые бенчмарки, данные аукциона Директ
    "digital-agency": (80.0, 350.0),   # B2B: высокая конкуренция, 80-350 руб.
    "e-commerce": (50.0, 200.0),        # зависит от товара; стройматериалы 50-200
    "services": (60.0, 300.0),          # широкий диапазон по типу услуги
    "saas": (100.0, 500.0),             # B2B SaaS: дорогой трафик
    "real-estate": (200.0, 1500.0),     # самая конкурентная ниша в РФ
    "medical": (150.0, 800.0),          # клиники/стоматология — очень дорого
    "education": (60.0, 300.0),         # курсы/обучение
    "finance": (300.0, 2000.0),         # кредиты/ипотека — топ-3 по CPC в РФ
}

# Мультипликатор CPC для регионов (применяется при stub-генерации)
_REGION_CPC_MULTIPLIER: dict[str, float] = {
    "MSK": 1.7,   # Москва дороже регионального CPC в 1.5-2x
    "SPB": 1.4,   # Санкт-Петербург
    "RU": 1.0,    # базовый (среднероссийский)
    "BY": 0.6,    # Беларусь дешевле РФ
}


# ---------- Public API ----------


async def get_keywords(
    niche: str,
    region: str,
    hints: list[str] | None = None,
    tokens: dict | None = None,
) -> list[Keyword]:
    """
    Return keywords for the pipeline.

    tokens dict (all optional):
      yandex_wordstat: str  — Yandex Direct OAuth token
      google_ads: bool      — True to use GOOGLE_ADS_* env vars
    """
    from backend.config import settings

    keywords: list[Keyword] = []
    seeds = _get_seeds(niche, hints)

    # 1. Yandex Wordstat (реальная статистика)
    token = _get_yandex_token(settings)
    if token:
        try:
            from backend.integrations.wordstat import fetch_keyword_bids

            # Для Wordstat используем конкретные запросы: hints + нишевые сиды скомбинированные
            # с первым hint-словом для контекста. Дженерик-сиды без контекста дают мусор.
            wordstat_seeds = _get_wordstat_seeds(niche, hints)
            yandex_kws = await fetch_keyword_bids(wordstat_seeds, token, region)
            keywords.extend(yandex_kws)
        except Exception as exc:
            print(f"[wordstat] error: {exc}")

    # 2. Google Keyword Planner
    if _google_ads_configured(settings) and not keywords:
        try:
            from backend.integrations.google_ads import fetch_keyword_ideas

            google_kws = await fetch_keyword_ideas(seeds[:10], region)
            keywords.extend(google_kws)
        except Exception as exc:
            print(f"[google_ads] error: {exc}")

    # 3. Stub fallback
    if not keywords:
        keywords = _stub_keywords(niche, region, seeds)

    # Enrich with seasonality via pytrends (best-effort, never blocks pipeline)
    keywords = await _enrich_seasonality(keywords, region)

    return keywords


# ---------- Helpers ----------


def _get_seeds(niche: str, hints: list[str] | None) -> list[str]:
    seeds = list(_NICHE_SEEDS.get(niche, _DEFAULT_SEEDS))
    if hints:
        seeds += [h for h in hints[:10] if h not in seeds]
    return seeds


def _get_wordstat_seeds(niche: str, hints: list[str] | None) -> list[str]:
    """
    Формирует сиды для Wordstat API.
    Если есть hints — они идут первыми как конкретные бизнес-запросы.
    Нишевые сиды комбинируются с первым hint для контекста (избегаем мусора от дженерик-слов).
    """
    if hints:
        # Фильтруем: только hints с кириллицей, минимум 4 символа в первом слове,
        # и не прилагательные (одиночные слова с окончаниями -ый/-ая/-ые/-ой/-ого/-ий/-ие/-ого)
        import re as _re
        _ADJ_ENDINGS = ("ый", "ий", "ая", "яя", "ые", "ие", "ого", "его", "ому", "ному", "ного")

        def _is_good_hint(h: str) -> bool:
            words = h.lower().split()
            if not words:
                return False
            # Первое слово должно начинаться с кириллицы
            if not _re.match(r'[а-яё]', words[0]):
                return False
            if len(words[0]) < 4:
                return False
            # Цифры в хинте — это артикул/размер товара, не ключевое слово
            if _re.search(r'\d', h):
                return False
            # Для однословных хинтов — отсеиваем прилагательные
            # Для биграмм (прил+сущ) оставляем — это валидные продуктовые запросы
            if len(words) == 1 and any(words[0].endswith(e) for e in _ADJ_ENDINGS):
                return False
            return True

        # Берём только 3 самых специфичных хинта — остальные часто дают нерелевантные расширения
        clean_hints = [h for h in hints if _is_good_hint(h)][:3]

        if not clean_hints:
            return list(_NICHE_SEEDS.get(niche, _DEFAULT_SEEDS))

        primary = clean_hints
        # Комбинируем первый hint с коммерческими суффиксами
        anchor = clean_hints[0]
        niche_suffixes = ["цена", "купить", "заказать", "москва", "недорого", "отзывы"]
        combined = [f"{anchor} {suf}" for suf in niche_suffixes]
        return primary + [c for c in combined if c not in primary]

    # Без hints — используем нишевые сиды как есть (они достаточно конкретны для некоторых ниш)
    return list(_NICHE_SEEDS.get(niche, _DEFAULT_SEEDS))


def _get_yandex_token(settings) -> str:
    """Токен для Wordstat: YANDEX_WORDSTAT_TOKEN или по YANDEX_CLIENT_ID/SECRET/REFRESH_TOKEN."""
    if settings.yandex_wordstat_token:
        return settings.yandex_wordstat_token
    from backend.integrations.wordstat import get_wordstat_token
    return get_wordstat_token()


def _google_ads_configured(settings) -> bool:
    return all(
        [
            settings.google_ads_client_id,
            settings.google_ads_client_secret,
            settings.google_ads_developer_token,
            settings.google_ads_refresh_token,
            settings.google_ads_customer_id,
        ]
    )


def _stub_keywords(niche: str, region: str, seeds: list[str]) -> list[Keyword]:
    cpc_min, cpc_max = _CPC_RANGES.get(niche, (50.0, 250.0))
    # Применяем региональный мультипликатор
    region_mult = _REGION_CPC_MULTIPLIER.get(region.upper(), 1.0)
    cpc_min = round(cpc_min * region_mult, 1)
    cpc_max = round(cpc_max * region_mult, 1)

    keywords: list[Keyword] = []
    for seed in seeds:
        h = int(hashlib.md5(f"{seed}{region}".encode()).hexdigest(), 16)
        rng = random.Random(h)
        freq = rng.randint(300, 50000)
        cpc = round(rng.uniform(cpc_min, cpc_max), 2)
        seasonality = round(1.0 + 0.3 * math.sin(h % 12 / 12 * 2 * math.pi), 2)
        keywords.append(
            Keyword(
                text=seed,
                frequency=freq,
                cpc=cpc,
                platform="yandex",
                seasonality=seasonality,
            )
        )
        keywords.append(
            Keyword(
                text=seed,
                frequency=int(freq * rng.uniform(0.4, 0.9)),
                cpc=round(cpc * rng.uniform(0.8, 1.3), 2),
                platform="google",
                seasonality=seasonality,
            )
        )
    return keywords


async def _enrich_seasonality(keywords: list[Keyword], region: str) -> list[Keyword]:
    """Enrich keywords with seasonality from Wordstat dynamics (or Google Trends as fallback)."""
    unique_texts = list({kw.text for kw in keywords})[:5]
    seasonality_map: dict[str, float] = {}

    # 1. Wordstat /v1/dynamics (если токен есть)
    try:
        from backend.config import settings
        from backend.integrations.wordstat import get_wordstat_seasonality, get_wordstat_token

        token = get_wordstat_token()
        if token:
            seasonality_map = await get_wordstat_seasonality(unique_texts, token, region)
    except Exception:
        pass

    # 2. Fallback: Google Trends
    if not seasonality_map:
        try:
            from backend.integrations.trends import get_seasonality
            seasonality_map = await get_seasonality(unique_texts, region)
        except Exception:
            pass

    for kw in keywords:
        if kw.text in seasonality_map:
            kw.seasonality = seasonality_map[kw.text]

    return keywords
