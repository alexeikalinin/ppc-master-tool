"""
Region-aware platform selection.

РФ:  Google Ads недоступен с 2022 → только Яндекс Директ + VK Ads
BY:  все три платформы; Google ~70% поискового трафика, Яндекс ~30%
"""

# Регионы РФ (ISO + яндексовские коды городов)
_RU_REGIONS = {"RU", "MSK", "SPB", "NSK", "EKB", "KZN", "NN", "CHB", "SAM", "UFА", "RND"}

# Регионы BY
_BY_REGIONS = {"BY", "MINSK", "GRODNO", "BREST", "VITEBSK", "GOMEL", "MOGILEV"}


def get_region_type(region: str) -> str:
    """Возвращает 'RU', 'BY' или 'OTHER'."""
    r = region.upper()
    if r in _RU_REGIONS:
        return "RU"
    if r in _BY_REGIONS:
        return "BY"
    # Эвристика: если не BY — считаем RU-подобным
    return "RU"


def get_platforms_for_region(region: str) -> list[str]:
    """Список платформ для региона."""
    rt = get_region_type(region)
    if rt == "BY":
        return ["google", "yandex", "vk"]
    return ["yandex", "vk"]  # RU: Google не работает


def get_budget_split(region: str, niche: str, budget: float) -> dict[str, float]:
    """
    Распределение бюджета по платформам.
    РФ:
      < 30 000 ₽  → Яндекс 100%
      30–60 000   → Яндекс 70% + VK 30%
      60 000+     → Яндекс 60% + VK 40% (больше на соцсети)
    BY:
      < $300  → Google 100%
      $300+   → Google 60% + Яндекс 25% + VK 15%
    """
    rt = get_region_type(region)

    if rt == "BY":
        if budget < 1000:  # ~$300 по приблизительному курсу
            return {"google": 1.0}
        return {"google": 0.60, "yandex": 0.25, "vk": 0.15}

    # RU
    if budget < 30_000:
        return {"yandex": 1.0}
    if budget < 60_000:
        return {"yandex": 0.70, "vk": 0.30}
    return {"yandex": 0.60, "vk": 0.40}


def get_region_label(region: str, city: str | None) -> str:
    """Читабельное название региона для UI и промптов."""
    if city:
        return city
    labels = {
        "RU": "России",
        "BY": "Беларуси",
        "MSK": "Москве",
        "SPB": "Санкт-Петербурге",
        "MINSK": "Минске",
        "KZ": "Казахстане",
        "UA": "Украине",
    }
    return labels.get(region.upper(), region)
