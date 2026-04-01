"""
Yandex Wordstat API integration.

Base URL: https://api.wordstat.yandex.net
Methods:
  - /v1/topRequests  — популярные запросы для фразы + реальная частотность (count)
  - /v1/dynamics     — динамика частотности (для seasonality)

Токен: YANDEX_WORDSTAT_TOKEN в .env (OAuth Bearer, scope "API Вордстата")
Docs: https://yandex.com/support2/wordstat/en/content/api-structure
"""

import datetime
import httpx
from backend.models import Keyword

_BASE_URL = "https://api.wordstat.yandex.net"

# Yandex region IDs (пустой список = вся Россия)
_REGION_IDS: dict[str, list[int]] = {
    "RU": [],       # все регионы России
    "MSK": [213],   # Москва
    "SPB": [2],     # Санкт-Петербург
    "UA": [187],    # Украина
    "BY": [149],    # Беларусь
    "KZ": [159],    # Казахстан
    "US": [84],     # США
}

# Кэш access_token при использовании refresh
_cached_access_token: str | None = None


def get_wordstat_token() -> str:
    """Возвращает токен: либо из настроек, либо по refresh_token."""
    from backend.config import settings

    if settings.yandex_wordstat_token:
        return settings.yandex_wordstat_token
    if settings.yandex_client_id and settings.yandex_client_secret and settings.yandex_refresh_token:
        global _cached_access_token
        if not _cached_access_token:
            _cached_access_token = _sync_refresh_token()
        return _cached_access_token or ""
    return ""


def _sync_refresh_token() -> str:
    import base64
    from backend.config import settings

    auth = base64.b64encode(
        f"{settings.yandex_client_id}:{settings.yandex_client_secret}".encode()
    ).decode()
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            "https://oauth.yandex.com/token",
            data={"grant_type": "refresh_token", "refresh_token": settings.yandex_refresh_token},
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
    return resp.json().get("access_token", "")


async def fetch_keyword_bids(
    keywords: list[str],
    token: str,
    region: str = "RU",
) -> list[Keyword]:
    """
    Получает реальную частотность из Wordstat API (/v1/topRequests).

    После получения частотности — обогащает CPC из Yandex Direct Forecast API
    (реальные ставки аукциона). При недоступности Forecast API — fallback-формула
    с учётом региона (Москва ×1.7 от базового диапазона).

    Возвращает до 50 уникальных ключевых фраз по убыванию частотности.
    """
    geo_ids = _REGION_IDS.get(region, [])
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    seen: dict[str, int] = {}  # phrase -> max count

    async with httpx.AsyncClient(timeout=30) as client:
        for seed in keywords[:15]:  # ограничиваем квоту
            try:
                payload: dict = {"phrase": seed}
                if geo_ids:
                    payload["regions"] = geo_ids

                resp = await client.post(
                    f"{_BASE_URL}/v1/topRequests", json=payload, headers=headers
                )
                if resp.status_code == 429:
                    print("[wordstat] quota exceeded")
                    break
                if resp.status_code != 200:
                    print(f"[wordstat] {seed}: HTTP {resp.status_code}")
                    continue

                data = resp.json()

                # Основная фраза
                total = data.get("totalCount", 0)
                if total > 0:
                    seen[seed] = max(seen.get(seed, 0), total)

                # Связанные запросы
                for item in data.get("topRequests", []):
                    phrase = item.get("phrase", "").strip()
                    count = item.get("count", 0)
                    if phrase and count > 0:
                        seen[phrase] = max(seen.get(phrase, 0), count)

            except Exception as exc:
                print(f"[wordstat] {seed}: {exc}")

    if not seen:
        return []

    sorted_phrases = sorted(seen.items(), key=lambda x: -x[1])[:50]

    # Пробуем получить реальный CPC из Yandex Direct Forecast API
    phrase_list = [p for p, _ in sorted_phrases]
    real_cpc: dict[str, float] = {}
    try:
        from backend.integrations.direct_forecast import fetch_cpc_estimates
        real_cpc = await fetch_cpc_estimates(phrase_list, region=region)
        if real_cpc:
            print(f"[direct_forecast] получены реальные CPC для {len(real_cpc)} ключей")
    except Exception as exc:
        print(f"[direct_forecast] недоступен, используем формулу: {exc}")

    # Fallback-формула с региональным коэффициентом
    # Данные агента: Москва — поиск 50-300 руб., регионы — 25-150 руб.
    is_moscow = region in ("MSK", "SPB")
    cpc_min = 50.0 if is_moscow else 25.0
    cpc_range = 250.0 if is_moscow else 125.0

    max_freq = max(seen.values())
    results: list[Keyword] = []
    for phrase, count in sorted_phrases:
        if phrase.lower() in real_cpc:
            cpc = real_cpc[phrase.lower()]
        else:
            # Формула: частота пропорционально влияет на CPC в диапазоне [cpc_min, cpc_min+cpc_range]
            ratio = (count / max_freq) ** 0.5  # корень сглаживает эффект outliers
            cpc = round(cpc_min + ratio * cpc_range, 2)

        results.append(Keyword(text=phrase, frequency=count, cpc=cpc, platform="yandex"))

    return results


async def get_wordstat_seasonality(
    phrases: list[str],
    token: str,
    region: str = "RU",
) -> dict[str, float]:
    """
    Возвращает seasonality multiplier для каждой фразы через /v1/dynamics.
    Multiplier = текущий месяц / среднемесячное значение за год.
    """
    geo_ids = _REGION_IDS.get(region, [])
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    from_date = (
        datetime.date.today().replace(day=1) - datetime.timedelta(days=365)
    ).strftime("%Y-%m-%d")

    result: dict[str, float] = {}

    async with httpx.AsyncClient(timeout=20) as client:
        for phrase in phrases[:5]:  # dynamics стоит 1 квоту за запрос
            try:
                payload: dict = {"phrase": phrase, "period": "monthly", "fromDate": from_date}
                if geo_ids:
                    payload["regions"] = geo_ids

                resp = await client.post(
                    f"{_BASE_URL}/v1/dynamics", json=payload, headers=headers
                )
                if resp.status_code != 200:
                    continue

                dynamics = resp.json().get("dynamics", [])
                counts = [d.get("count", 0) for d in dynamics if d.get("count", 0) > 0]
                if len(counts) < 2:
                    continue

                avg = sum(counts) / len(counts)
                current = counts[-1]
                result[phrase] = round(current / avg, 2) if avg > 0 else 1.0

            except Exception:
                pass

    return result
