"""
AI Assistant: суммари отчёта и чат по данным отчёта (правдивые ответы из контекста).

Провайдеры (первый доступный по ключу или AI_PROVIDER):
  - anthropic — Claude
  - openai — GPT
  - xai — Grok (OpenAI-совместимый API)
Без ключа — rule-based stub.
"""

from backend.models import AiSummary, SiteData, AudienceProfile, Campaign, MediaPlan


def _get_provider() -> str:
    from backend.config import settings
    if settings.ai_provider:
        return settings.ai_provider.lower()
    if settings.anthropic_api_key:
        return "anthropic"
    if settings.openai_api_key:
        return "openai"
    if settings.xai_api_key:
        return "xai"
    return ""


async def generate_summary(
    site: SiteData,
    competitors: list[str],
    campaigns: list[Campaign],
    audience: AudienceProfile,
    media_plan: MediaPlan,
    region: str,
    city: str | None,
    budget: float,
) -> AiSummary:
    from backend.config import settings

    provider = _get_provider()
    if provider == "anthropic" and settings.anthropic_api_key:
        try:
            return await _claude_summary(
                site, competitors, campaigns, audience, media_plan, region, city, budget
            )
        except Exception as exc:
            print(f"[ai_summary] Claude API error: {exc}, falling back to stub")
    if provider == "openai" and settings.openai_api_key:
        try:
            return await _openai_summary(
                site, competitors, campaigns, audience, media_plan, region, city, budget
            )
        except Exception as exc:
            print(f"[ai_summary] OpenAI API error: {exc}, falling back to stub")
    if provider == "xai" and settings.xai_api_key:
        try:
            return await _xai_summary(
                site, competitors, campaigns, audience, media_plan, region, city, budget
            )
        except Exception as exc:
            print(f"[ai_summary] xAI (Grok) API error: {exc}, falling back to stub")
    # Fallback: try any available key if no explicit provider
    if not provider and settings.anthropic_api_key:
        try:
            return await _claude_summary(
                site, competitors, campaigns, audience, media_plan, region, city, budget
            )
        except Exception as exc:
            print(f"[ai_summary] Claude API error: {exc}, falling back to stub")
    if not provider and settings.openai_api_key:
        try:
            return await _openai_summary(
                site, competitors, campaigns, audience, media_plan, region, city, budget
            )
        except Exception as exc:
            print(f"[ai_summary] OpenAI API error: {exc}, falling back to stub")
    if not provider and settings.xai_api_key:
        try:
            return await _xai_summary(
                site, competitors, campaigns, audience, media_plan, region, city, budget
            )
        except Exception as exc:
            print(f"[ai_summary] xAI API error: {exc}, falling back to stub")

    return _stub_summary(site, competitors, campaigns, audience, media_plan, region, city, budget)


def _build_summary_prompt(
    site: SiteData,
    competitors: list[str],
    campaigns: list[Campaign],
    audience: AudienceProfile,
    media_plan: MediaPlan,
    region: str,
    city: str | None,
    budget: float,
) -> str:
    platforms = list({c.platform for c in campaigns})
    geo = city or region
    return f"""Ты — старший PPC-стратег. Проанализируй данные и дай рекомендацию для клиента.

Данные:
- Сайт: {site.title} — ниша: {site.niche}
- Регион: {geo}
- Бюджет: {budget:.0f} ₽/мес
- Платформы в плане: {", ".join(platforms)}
- Конкуренты: {", ".join(competitors[:5])}
- Аудитория: {audience.summary}
- Кампаний: {len(campaigns)}
- Прогноз конверсий: {media_plan.total_conversions:.1f}/мес, CPA: {media_plan.avg_cpa:.0f} ₽

Напиши блок рекомендаций для клиента (3-4 абзаца):
1. Стратегия и почему именно эти платформы
2. На что обратить внимание в первый месяц
3. Ключевые метрики для контроля
4. Один конкретный совет по оптимизации

Формат: обычный текст, без markdown заголовков, профессионально и конкретно."""


async def _claude_summary(
    site: SiteData,
    competitors: list[str],
    campaigns: list[Campaign],
    audience: AudienceProfile,
    media_plan: MediaPlan,
    region: str,
    city: str | None,
    budget: float,
) -> AiSummary:
    import anthropic
    from backend.config import settings
    from backend.services.token_counter import counter

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    prompt = _build_summary_prompt(site, competitors, campaigns, audience, media_plan, region, city, budget)
    model = "claude-sonnet-4-20250514"

    message = await client.messages.create(
        model=model,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    counter.record(model, message.usage.input_tokens, message.usage.output_tokens)
    recommendation_text = message.content[0].text
    platforms_used = list({c.platform for c in campaigns})
    geo = city or region
    return AiSummary(
        recommendation=recommendation_text,
        platforms=platforms_used,
        platform_rationale=_platform_rationale(site.niche, platforms_used, geo),
        quick_wins=_quick_wins(site.niche),
        confidence="high",
    )


async def _openai_summary(
    site: SiteData,
    competitors: list[str],
    campaigns: list[Campaign],
    audience: AudienceProfile,
    media_plan: MediaPlan,
    region: str,
    city: str | None,
    budget: float,
) -> AiSummary:
    from openai import AsyncOpenAI
    from backend.config import settings
    from backend.services.token_counter import counter

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    prompt = _build_summary_prompt(site, competitors, campaigns, audience, media_plan, region, city, budget)
    model = "gpt-4o-mini"
    r = await client.chat.completions.create(
        model=model,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    if r.usage:
        counter.record(model, r.usage.prompt_tokens, r.usage.completion_tokens)
    recommendation_text = (r.choices[0].message.content or "").strip()
    platforms_used = list({c.platform for c in campaigns})
    geo = city or region
    return AiSummary(
        recommendation=recommendation_text,
        platforms=platforms_used,
        platform_rationale=_platform_rationale(site.niche, platforms_used, geo),
        quick_wins=_quick_wins(site.niche),
        confidence="high",
    )


async def _xai_summary(
    site: SiteData,
    competitors: list[str],
    campaigns: list[Campaign],
    audience: AudienceProfile,
    media_plan: MediaPlan,
    region: str,
    city: str | None,
    budget: float,
) -> AiSummary:
    from openai import AsyncOpenAI
    from backend.config import settings
    from backend.services.token_counter import counter

    client = AsyncOpenAI(api_key=settings.xai_api_key, base_url="https://api.x.ai/v1")
    prompt = _build_summary_prompt(site, competitors, campaigns, audience, media_plan, region, city, budget)
    model = "grok-3-mini"
    r = await client.chat.completions.create(
        model=model,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    if r.usage:
        counter.record(model, r.usage.prompt_tokens, r.usage.completion_tokens)
    recommendation_text = (r.choices[0].message.content or "").strip()
    platforms_used = list({c.platform for c in campaigns})
    geo = city or region
    return AiSummary(
        recommendation=recommendation_text,
        platforms=platforms_used,
        platform_rationale=_platform_rationale(site.niche, platforms_used, geo),
        quick_wins=_quick_wins(site.niche),
        confidence="high",
    )


def _stub_summary(
    site: SiteData,
    competitors: list[str],
    campaigns: list[Campaign],
    audience: AudienceProfile,
    media_plan: MediaPlan,
    region: str,
    city: str | None,
    budget: float,
) -> AiSummary:
    geo = city or ("Беларуси" if region == "BY" else "России")
    platforms_used = list({c.platform for c in campaigns})
    niche = site.niche

    recommendation = _build_recommendation(niche, geo, budget, media_plan, platforms_used, competitors)

    return AiSummary(
        recommendation=recommendation,
        platforms=platforms_used,
        platform_rationale=_platform_rationale(niche, platforms_used, geo),
        quick_wins=_quick_wins(niche),
        confidence="medium",
    )


# ─── Text builders ────────────────────────────────────────────────────────────

_NICHE_STRATEGY: dict[str, str] = {
    "digital-agency": (
        "Для digital-агентства в {geo} ключевой канал — поисковая реклама: клиенты ищут исполнителей "
        "в момент, когда у них уже есть задача и бюджет. Рекомендуем сосредоточить {budget_pct}% бюджета "
        "на Яндекс.Директ (доминирует в РУ/BY-сегменте), остальное — Google Ads для охвата аудитории, "
        "которая изначально ориентирована на западные инструменты. ВКонтакте для B2B-агентских услуг "
        "показывает низкий ROI — исключаем из первого запуска."
    ),
    "services": (
        "Для сервисного бизнеса в {geo} поиск — основной канал привлечения: люди ищут исполнителя "
        "в конкретный момент потребности. Рекомендуем поисковые кампании в Яндекс.Директ как приоритет — "
        "здесь самый высокий intent. Google Ads добавляем вторым каналом для охвата оставшихся {budget_pct}% аудитории."
    ),
    "e-commerce": (
        "Для интернет-магазина в {geo} рекомендуем мультиканальный подход: поисковая реклама закрывает "
        "горячий спрос, ретаргетинг возвращает посетителей, таргет ВК работает на широкую аудиторию. "
        "Распределяем бюджет {budget_pct}% на поиск, остальное — на ретаргетинг и соцсети."
    ),
    "_default": (
        "На основе анализа ниши и региона {geo} рекомендуем сфокусироваться на поисковой рекламе "
        "как основном канале — она работает с горячим спросом. Бюджет {budget_pct}% направляем "
        "на Яндекс.Директ как доминирующую платформу в русскоязычном сегменте."
    ),
}

_NICHE_FIRST_MONTH: dict[str, str] = {
    "digital-agency": (
        "В первый месяц фокус — на тестировании объявлений и накоплении статистики. "
        "Запустите 2-3 варианта заголовков на каждую группу и отключите неэффективные через 2 недели. "
        "Ключевой вопрос: какой запрос даёт заявку по минимальной цене — именно на него направляйте бюджет."
    ),
    "_default": (
        "Первый месяц — тестовый: собираем данные по CTR, CPC и конверсиям. "
        "Не оптимизируйте слишком рано — дайте системе обучиться. "
        "Через 2 недели отключите ключевые слова без кликов и объявления с CTR ниже 2%."
    ),
}

_NICHE_METRICS: dict[str, str] = {
    "digital-agency": (
        "Контролируйте три метрики: стоимость заявки (CPA) — целевая до {target_cpa} ₽, "
        "конверсия сайта (CR) — нормальная 3-8% для B2B, качество заявок (процент целевых обращений). "
        "Подключите call-tracking если планируете звонки — без него половина конверсий будет невидима."
    ),
    "_default": (
        "Основные KPI: CPA (стоимость заявки/покупки), CTR объявлений (норма 5-15% для поиска), "
        "CR сайта (конверсия из клика в действие). Настройте цели в Яндекс.Метрике до запуска — "
        "без этого оптимизация невозможна."
    ),
}


def _build_recommendation(
    niche: str,
    geo: str,
    budget: float,
    media_plan: MediaPlan,
    platforms: list[str],
    competitors: list[str],
) -> str:
    budget_pct = 65 if "yandex" in platforms and "google" in platforms else 100
    target_cpa = round(media_plan.avg_cpa * 0.8)

    strategy = _NICHE_STRATEGY.get(niche, _NICHE_STRATEGY["_default"])
    first_month = _NICHE_FIRST_MONTH.get(niche, _NICHE_FIRST_MONTH["_default"])
    metrics = _NICHE_METRICS.get(niche, _NICHE_METRICS["_default"])

    parts = [
        strategy.format(geo=geo, budget_pct=budget_pct),
        first_month,
        metrics.format(target_cpa=target_cpa),
    ]

    if competitors:
        comp_note = (
            f"Среди конкурентов в выдаче активны: {', '.join(competitors[:3])}. "
            f"Изучите их объявления — используйте то, что работает, и выделитесь там, где они слабы."
        )
        parts.append(comp_note)

    return "\n\n".join(parts)


def _platform_rationale(niche: str, platforms: list[str], geo: str) -> dict[str, str]:
    rationales: dict[str, dict[str, str]] = {
        "yandex": {
            "digital-agency": f"Яндекс.Директ — основной канал для B2B в {geo}. Доля поискового рынка 60%+. Горячий спрос, высокий intent.",
            "_default": f"Яндекс.Директ — доминирующий поисковик в {geo} с долей 55-65% рынка.",
        },
        "google": {
            "digital-agency": "Google Ads охватывает аудиторию, ориентированную на международные инструменты. CPC ниже, чем в Директе.",
            "_default": "Google Ads — второй по охвату канал, хорошо работает в связке с Яндексом.",
        },
        "vk": {
            "_default": "ВКонтакте — таргетинг по интересам и поведению. Подходит для B2C и широкой аудитории.",
        },
    }
    result = {}
    for p in platforms:
        p_rationales = rationales.get(p, {})
        result[p] = p_rationales.get(niche, p_rationales.get("_default", f"Платформа {p}"))
    return result


def _quick_wins(niche: str) -> list[str]:
    wins: dict[str, list[str]] = {
        "digital-agency": [
            "Добавьте номер телефона в объявления — повышает CTR на 15-20%",
            "Используйте быстрые ссылки: Кейсы, Стоимость, Бесплатный аудит — они увеличивают площадь объявления",
            "Настройте ретаргетинг на посетителей страницы 'Услуги' — они уже заинтересованы",
            "Исключите нерелевантные запросы: 'бесплатно', 'самому', 'курс' — сэкономит до 20% бюджета",
        ],
        "e-commerce": [
            "Запустите товарные кампании — Яндекс.Маркет и Google Shopping дают дешёвые клики",
            "Добавьте в минус-слова: 'своими руками', 'бесплатно', 'скачать'",
            "Ретаргетинг на брошенные корзины — конверсия в 3-5 раз выше обычной",
            "Используйте акционные расширения в периоды скидок",
        ],
        "_default": [
            "Добавьте расширения объявлений: быстрые ссылки, уточнения, адрес",
            "Настройте корректировки ставок по устройствам — мобильный трафик дешевле",
            "Подключите Яндекс.Метрику и настройте цели до запуска рекламы",
            "Составьте список минус-слов из 50+ позиций перед запуском",
        ],
    }
    return wins.get(niche, wins["_default"])
