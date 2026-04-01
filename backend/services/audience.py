"""
Target audience inference from niche + keywords.
Returns per-platform targeting recommendations.
"""

from backend.models import AudienceProfile, PlatformTargeting

# Rule-based mapping: niche → targeting parameters
_NICHE_PROFILES: dict[str, dict] = {
    "digital-agency": {
        "summary": "B2B: владельцы малого и среднего бизнеса, маркетологи и предприниматели, которые хотят запустить или улучшить рекламу в интернете",
        "age_range": "28-50",
        "gender": "male",
        "interests": [
            "бизнес и предпринимательство",
            "интернет-маркетинг",
            "контекстная реклама",
            "продвижение бизнеса",
            "увеличение продаж",
            "digital-инструменты",
        ],
    },
    "e-commerce": {
        "summary": "Активные онлайн-покупатели, ищущие выгодные предложения",
        "age_range": "25-45",
        "gender": "all",
        "interests": ["онлайн-шопинг", "скидки и акции", "бренды", "отзывы товаров"],
    },
    "services": {
        "summary": "Люди, которым нужна конкретная услуга здесь и сейчас",
        "age_range": "28-55",
        "gender": "all",
        "interests": ["домашний ремонт", "бытовые услуги", "местные сервисы"],
    },
    "saas": {
        "summary": "B2B: предприниматели и IT-специалисты, автоматизирующие бизнес-процессы",
        "age_range": "25-45",
        "gender": "male",
        "interests": ["бизнес", "стартапы", "автоматизация", "crm", "технологии"],
    },
    "real-estate": {
        "summary": "Покупатели и арендаторы жилой/коммерческой недвижимости",
        "age_range": "28-50",
        "gender": "all",
        "interests": ["недвижимость", "ипотека", "переезд", "инвестиции"],
    },
    "medical": {
        "summary": "Люди, ищущие медицинскую помощь или плановую диагностику",
        "age_range": "30-60",
        "gender": "female",
        "interests": ["здоровье", "медицина", "клиники", "диета и фитнес"],
    },
    "education": {
        "summary": "Студенты и специалисты, развивающие новые навыки",
        "age_range": "18-40",
        "gender": "all",
        "interests": ["образование", "карьера", "it", "самообразование", "курсы"],
    },
    "finance": {
        "summary": "Физлица и ИП, ищущие кредитные или инвестиционные продукты",
        "age_range": "25-55",
        "gender": "all",
        "interests": ["финансы", "кредиты", "инвестиции", "экономия", "банки"],
    },
}

_DEFAULT_PROFILE = {
    "summary": "Широкая аудитория, заинтересованная в продукте или услуге",
    "age_range": "25-50",
    "gender": "all",
    "interests": ["интернет", "покупки онлайн", "услуги"],
}

# Platforms to include in recommendations (Google фильтруется для РФ в рантайме)
_PLATFORMS = ["yandex", "google", "vk"]


def infer_audience(niche: str, keywords: list, region_code: str = "") -> AudienceProfile:
    from backend.services.region_platforms import get_region_type

    profile = _NICHE_PROFILES.get(niche, _DEFAULT_PROFILE)

    # Google Ads заблокирован в РФ с 2022 года — не включаем в таргетинг
    available_platforms = list(_PLATFORMS)
    if region_code and get_region_type(region_code) == "RU":
        available_platforms = [p for p in available_platforms if p != "google"]

    targeting: list[PlatformTargeting] = []
    for platform in available_platforms:
        # VK gets slightly younger demographic and more social interests
        age = profile["age_range"]
        interests = list(profile["interests"])
        if platform == "vk":
            parts = age.split("-")
            age = f"{parts[0]}-{min(int(parts[1]), 45)}"
            interests = interests + ["социальные сети", "сообщества"]

        targeting.append(
            PlatformTargeting(
                platform=platform,
                age_range=age,
                interests=interests,
                gender=profile["gender"],
            )
        )

    return AudienceProfile(summary=profile["summary"], targeting=targeting)
