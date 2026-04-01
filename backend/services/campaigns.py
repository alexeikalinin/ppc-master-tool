"""
Campaign and ad variant generation.
Takes semantic groups + audience + budget and produces campaign structures.
"""

import hashlib
import random
import textwrap

from backend.models import AdVariant, AudienceProfile, Campaign, SemanticGroup

# Budget split by campaign type
_SEARCH_SHARE = 0.70
_DISPLAY_SHARE = 0.30

# Per-niche platform selection (ordered by priority)
_NICHE_PLATFORMS: dict[str, list[str]] = {
    "digital-agency": ["yandex", "google"],        # B2B, search intent, no VK
    "saas":           ["yandex", "google"],        # B2B, no VK
    "finance":        ["yandex", "google"],        # high CPC, search only
    "real-estate":    ["yandex", "google"],
    "medical":        ["yandex"],                  # Yandex dominant in RU/BY medical
    "services":       ["yandex", "google"],
    "education":      ["yandex", "vk"],            # social works for education
    "e-commerce":     ["yandex", "google", "vk"],  # all channels
}
_DEFAULT_PLATFORMS = ["yandex", "google"]

# Whether to add display campaign per niche (B2B niches don't need display)
_NICHE_USE_DISPLAY: dict[str, bool] = {
    "digital-agency": False,
    "saas":           False,
    "finance":        False,
    "services":       False,
    "medical":        True,
    "real-estate":    True,
    "education":      True,
    "e-commerce":     True,
}

# Budget split per platform per niche (must sum to 1.0)
_NICHE_BUDGET_SPLIT: dict[str, dict[str, float]] = {
    "digital-agency": {"yandex": 0.65, "google": 0.35},
    "saas":           {"yandex": 0.55, "google": 0.45},
    "medical":        {"yandex": 1.0},
    "education":      {"yandex": 0.60, "vk": 0.40},
    "e-commerce":     {"yandex": 0.50, "google": 0.30, "vk": 0.20},
    "real-estate":    {"yandex": 0.60, "google": 0.40},
    "services":       {"yandex": 0.65, "google": 0.35},
    "finance":        {"yandex": 0.55, "google": 0.45},
}

# Ad headline templates per niche
_HEADLINE_TEMPLATES: dict[str, list[str]] = {
    "digital-agency": [
        "{kw} в {region} — под ключ",
        "Настройка рекламы за 3 дня",
        "{kw} с гарантией заявок",
        "Реклама в Google и Яндекс",
        "Первые клиенты за 7 дней",
        "Аудит рекламы — бесплатно",
        "{kw} — опыт 200+ проектов",
        "Снизим стоимость заявки",
    ],
    "_default": [
        "{kw} — от {cpc} ₽",
        "Лучший {kw} в {region}",
        "{kw}: скидка до 30%",
        "Заказать {kw} онлайн",
        "{kw} с гарантией",
        "Быстрый {kw} — звоните!",
        "Официальный {kw}",
        "{kw} под ключ",
        "Выгодный {kw} сегодня",
        "{kw} — проверено клиентами",
    ],
}

_DESCRIPTION_TEMPLATES: dict[str, list[str]] = {
    "digital-agency": [
        "Настраиваем Яндекс.Директ, Google Ads и таргет ВК. Отчёты каждую неделю. Первый месяц — без абонентской платы.",
        "Более 200 клиентов в Беларуси и России. Гарантия: если нет заявок — возвращаем деньги.",
        "{kw} для малого и среднего бизнеса. Фиксированная стоимость, без скрытых платежей.",
        "Запустим рекламу за 3 рабочих дня. Бесплатный аудит текущих кампаний. Звоните!",
        "ROI от 200%: считаем реальную окупаемость рекламы. Работаем по договору.",
    ],
    "_default": [
        "Профессиональный {kw} с гарантией результата. Работаем по всей России. Звоните!",
        "Закажите {kw} прямо сейчас и получите скидку 10% на первый заказ.",
        "Более 500 довольных клиентов. {kw} по лучшим ценам. Быстрая доставка.",
        "Надёжный {kw} без скрытых платежей. Бесплатная консультация.",
        "{kw} — опыт 10 лет на рынке. Лицензия и сертификаты.",
    ],
}

_QUICK_LINKS_POOL: dict[str, list[str]] = {
    "digital-agency": [
        "Наши услуги", "Кейсы и результаты", "Стоимость", "Контакты",
        "Бесплатный аудит", "О команде", "Отзывы клиентов", "FAQ",
        "Яндекс.Директ", "Google Ads", "Таргет ВК", "Портфолио",
    ],
    "_default": [
        "О компании", "Каталог", "Цены", "Контакты", "Отзывы",
        "Акции", "Доставка", "Гарантия", "Портфолио", "Оплата", "FAQ", "Партнёрам",
    ],
}


def generate_campaigns(
    groups: list[SemanticGroup],
    audience: AudienceProfile,
    budget: float,
    region: str = "BY",
    site_url: str = "example.com",
    niche: str = "",
    region_code: str = "",
) -> list[Campaign]:
    """
    Generate campaigns — smart platform selection per niche.
    Max ~4-6 campaigns total: top groups × relevant platforms only.
    """
    from backend.services.region_platforms import get_region_type

    platforms = list(_NICHE_PLATFORMS.get(niche, _DEFAULT_PLATFORMS))
    use_display = _NICHE_USE_DISPLAY.get(niche, True)

    # Google Ads заблокирован в РФ с 2022 года
    if region_code and get_region_type(region_code) == "RU":
        platforms = [p for p in platforms if p != "google"]
    if not platforms:
        platforms = ["yandex"]

    # Пересчитываем бюджетный сплит под доступные платформы
    raw_split = _NICHE_BUDGET_SPLIT.get(niche, {})
    available_split = {p: raw_split.get(p, 1.0) for p in platforms}
    total = sum(available_split.values()) or 1.0
    budget_split = {p: v / total for p, v in available_split.items()}

    # Use top 2 groups max to avoid campaign explosion
    top_groups = groups[:2]
    campaigns: list[Campaign] = []

    for group in top_groups:
        avg_cpc = _avg_cpc(group)
        group_budget = budget / max(len(top_groups), 1)

        for platform in platforms:
            platform_share = budget_split.get(platform, 1 / len(platforms))
            platform_budget = group_budget * platform_share

            # Search campaign (always)
            campaigns.append(Campaign(
                name=f"[Поиск] {group.name} | {platform.capitalize()}",
                type="search",
                platform=platform,
                group_name=group.name,
                budget=round(platform_budget * (_SEARCH_SHARE if use_display else 1.0), 2),
                avg_cpc=avg_cpc,
                ad_variants=_generate_variants(
                    group.name, region, avg_cpc, site_url, niche=niche, n=5
                ),
            ))

            # Display campaign (only for B2C niches)
            if use_display:
                campaigns.append(Campaign(
                    name=f"[РСЯ/КМС] {group.name} | {platform.capitalize()}",
                    type="display",
                    platform=platform,
                    group_name=group.name,
                    budget=round(platform_budget * _DISPLAY_SHARE, 2),
                    avg_cpc=round(avg_cpc * 0.4, 2),
                    ad_variants=_generate_variants(
                        group.name, region, avg_cpc, site_url, niche=niche, n=5
                    ),
                ))

    return campaigns


def _avg_cpc(group: SemanticGroup) -> float:
    if not group.keywords:
        return 30.0
    return round(sum(kw.cpc for kw in group.keywords) / len(group.keywords), 2)


def _generate_variants(
    kw: str, region: str, cpc: float, site_url: str, niche: str = "", n: int = 7
) -> list[AdVariant]:
    rng = random.Random(int(hashlib.md5(kw.encode()).hexdigest(), 16))
    headlines = _HEADLINE_TEMPLATES.get(niche, _HEADLINE_TEMPLATES["_default"])
    descriptions = _DESCRIPTION_TEMPLATES.get(niche, _DESCRIPTION_TEMPLATES["_default"])
    quick_links_pool = _QUICK_LINKS_POOL.get(niche, _QUICK_LINKS_POOL["_default"])

    shuffled_hl = list(headlines)
    shuffled_desc = list(descriptions)
    rng.shuffle(shuffled_hl)
    rng.shuffle(shuffled_desc)

    variants: list[AdVariant] = []
    for i in range(min(n, len(shuffled_hl))):
        headline = shuffled_hl[i].format(kw=kw, region=region, cpc=int(cpc))
        description = shuffled_desc[i % len(shuffled_desc)].format(kw=kw)
        headline = headline[:30]
        description = description[:90]
        quick_links = rng.sample(quick_links_pool, min(4, len(quick_links_pool)))
        display_url = f"{site_url}/{kw.replace(' ', '-').lower()}"[:35]
        variants.append(
            AdVariant(
                headline=headline,
                description=description,
                quick_links=quick_links,
                display_url=display_url,
            )
        )
    return variants
