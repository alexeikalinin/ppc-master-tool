"""
Yandex Direct Forecast API (ForecastsService v5).

Позволяет получить реальные CPC из аукциона Яндекс.Директ для заданных ключевых слов
и региона — без необходимости создавать кампанию.

Endpoint: POST https://api.direct.yandex.com/json/v5/forecasts
Методы: create → get (polling до Status == "Done")

Требуется OAuth-токен с scope direct:api.
Если YANDEX_DIRECT_TOKEN не задан — пробуем YANDEX_WORDSTAT_TOKEN.

Документация: https://yandex.ru/dev/direct/doc/ref-v5/forecasts/create.html
"""

import asyncio
import httpx

_DIRECT_API = "https://api.direct.yandex.com/json/v5/forecasts"
_SANDBOX_API = "https://api-sandbox.direct.yandex.com/json/v5/forecasts"

# Таргет: 100% охват трафика (наиболее репрезентативный CPC)
_TARGET_TRAFFIC_VOLUME = 100


def _get_direct_token() -> str:
    """Возвращает токен для Direct API: YANDEX_DIRECT_TOKEN → YANDEX_WORDSTAT_TOKEN."""
    from backend.config import settings
    return settings.yandex_direct_token or settings.yandex_wordstat_token or ""


async def fetch_cpc_estimates(
    keywords: list[str],
    region: str = "MSK",
    use_sandbox: bool = False,
) -> dict[str, float]:
    """
    Возвращает словарь {keyword: cpc_rub} с реальными ставками из аукциона Директа.

    Используется для обогащения CPC вместо формульного расчёта.
    Возвращает пустой dict если токен не задан или API недоступен.
    """
    token = _get_direct_token()
    if not token:
        return {}

    from backend.integrations.wordstat import _REGION_IDS
    geo_ids = _REGION_IDS.get(region, [213])  # По умолчанию Москва
    if not geo_ids:
        geo_ids = [225]  # 225 = Россия

    base_url = _SANDBOX_API if use_sandbox else _DIRECT_API
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
    }

    # Ограничение API: не более 200 ключей за раз
    kw_batch = keywords[:200]

    try:
        forecast_id = await _create_forecast(base_url, headers, kw_batch, geo_ids)
        if not forecast_id:
            return {}

        result = await _poll_forecast(base_url, headers, forecast_id)
        return result

    except Exception as exc:
        print(f"[direct_forecast] error: {exc}")
        return {}


async def _create_forecast(
    base_url: str,
    headers: dict,
    keywords: list[str],
    geo_ids: list[int],
) -> int | None:
    """Создаёт отчёт прогноза, возвращает ForecastID."""
    payload = {
        "method": "create",
        "params": {
            "Keywords": keywords,
            "GeoID": geo_ids,
            "Currency": "RUB",
        },
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(base_url, json=payload, headers=headers)

    if resp.status_code == 401:
        print("[direct_forecast] Unauthorized — нужен токен с scope direct:api")
        return None
    if resp.status_code == 403:
        print("[direct_forecast] Forbidden — токен не имеет доступа к Forecast API")
        return None
    if resp.status_code != 200:
        print(f"[direct_forecast] create: HTTP {resp.status_code} — {resp.text[:200]}")
        return None

    data = resp.json()
    errors = data.get("error")
    if errors:
        print(f"[direct_forecast] create error: {errors}")
        return None

    ids = data.get("result", {}).get("ForecastIDs", [])
    return ids[0] if ids else None


async def _poll_forecast(
    base_url: str,
    headers: dict,
    forecast_id: int,
    max_attempts: int = 10,
    poll_interval: float = 2.0,
) -> dict[str, float]:
    """
    Опрашивает API пока статус не станет Done.
    Возвращает {keyword: cpc_rub}.
    """
    payload = {
        "method": "get",
        "params": {
            "ForecastIDs": [forecast_id],
        },
    }

    async with httpx.AsyncClient(timeout=20) as client:
        for attempt in range(max_attempts):
            resp = await client.post(base_url, json=payload, headers=headers)

            if resp.status_code != 200:
                print(f"[direct_forecast] poll: HTTP {resp.status_code}")
                return {}

            data = resp.json()
            forecasts = data.get("result", {}).get("Forecasts", [])

            if not forecasts:
                await asyncio.sleep(poll_interval)
                continue

            forecast = forecasts[0]
            status = forecast.get("Status", "")

            if status == "Done":
                return _parse_forecast_result(forecast)

            if status == "Error":
                print(f"[direct_forecast] forecast error: {forecast}")
                return {}

            # Статус Pending/Processing — ждём
            await asyncio.sleep(poll_interval)

    print(f"[direct_forecast] timeout after {max_attempts} polls")
    return {}


def _parse_forecast_result(forecast: dict) -> dict[str, float]:
    """
    Парсит результат прогноза, извлекает CPC для каждого ключевого слова.
    Выбирает значение при TrafficVolume = 100 (максимальный охват).
    """
    result: dict[str, float] = {}

    for kw_data in forecast.get("Keywords", []):
        keyword_name = kw_data.get("KeywordName") or kw_data.get("Keyword", "")
        if not keyword_name:
            continue

        traffic_volumes = kw_data.get("TrafficVolumeForecast", [])
        if not traffic_volumes:
            continue

        # Берём максимальный traffic volume (наиболее реалистичный CPC аукциона)
        best = max(traffic_volumes, key=lambda x: x.get("TrafficVolume", 0))

        # CPC может быть в разных полях в зависимости от версии API
        cpc = (
            best.get("AvgClickCost")
            or best.get("CpcInCents", 0) / 100  # kopecks → rubles
            or _calc_cpc(best)
        )

        if cpc and cpc > 0:
            result[keyword_name.lower()] = round(float(cpc), 2)

    return result


def _calc_cpc(tv: dict) -> float:
    """Рассчитывает CPC из Cost и Clicks если нет прямого поля."""
    clicks = tv.get("Clicks", 0)
    cost = tv.get("Cost", 0)
    if clicks and cost:
        return round(cost / clicks, 2)
    return 0.0
