"""
Тест Yandex Direct API по трём точкам:
  1. Campaigns (v5) — проверяет ошибку 58 / доступ к аккаунту
  2. Forecast (v5) — CPC прогноз по ключевым словам
  3. Reports — статистика кампаний (ReportsService)

Запуск:
  cd "PPC Master Tool"
  source .venv/bin/activate
  python scripts/test_direct_api.py
"""

import asyncio
import json
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("YANDEX_DIRECT_TOKEN") or os.getenv("YANDEX_WORDSTAT_TOKEN") or ""
BASE = "https://api.direct.yandex.com/json/v5"

LOGIN = os.getenv("YANDEX_LOGIN", "")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept-Language": "ru",
    "Content-Type": "application/json; charset=utf-8",
}
if LOGIN:
    HEADERS["Client-Login"] = LOGIN

TEST_KEYWORDS = ["ремонт квартир", "натяжные потолки", "установка окон"]
TEST_GEO = [213]  # Москва


def sep(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)


# ──────────────────────────────────────────────────
# 1. Campaigns API
# ──────────────────────────────────────────────────
async def test_campaigns():
    sep("1. Campaigns API (GET список кампаний)")
    payload = {
        "method": "get",
        "params": {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "Status", "Type"],
            "Page": {"Limit": 5},
        },
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(f"{BASE}/campaigns", json=payload, headers=HEADERS)

    print(f"HTTP {resp.status_code}")
    data = resp.json()

    if "error" in data:
        err = data["error"]
        code = err.get("error_code") or err.get("error_detail", "")
        msg = err.get("error_string", "") or err.get("error_detail", "")
        print(f"ОШИБКА {code}: {msg}")
        if err.get("error_code") == 58:
            print("→ Ошибка 58: незавершённая регистрация в Директе.")
            print("  Зайди на direct.yandex.ru и пройди регистрацию до конца.")
        return False

    campaigns = data.get("result", {}).get("Campaigns", [])
    print(f"OK — найдено кампаний: {len(campaigns)}")
    for c in campaigns:
        print(f"  [{c.get('Id')}] {c.get('Name')} | {c.get('Status')} | {c.get('Type')}")
    return True


# ──────────────────────────────────────────────────
# 2. Forecast API
# ──────────────────────────────────────────────────
async def test_forecast():
    sep("2. Forecast API (CPC прогноз)")

    create_payload = {
        "method": "create",
        "params": {
            "Keywords": TEST_KEYWORDS,
            "GeoID": TEST_GEO,
            "Currency": "RUB",
        },
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(f"{BASE}/forecasts", json=create_payload, headers=HEADERS)

    print(f"HTTP {resp.status_code}")

    if resp.status_code == 404:
        print("ОШИБКА 404 — Forecast API недоступен для данного аккаунта (возможно BYN-аккаунт)")
        return False

    try:
        data = resp.json()
    except Exception:
        print(f"Не JSON-ответ: {resp.text[:200]}")
        return False

    if "error" in data:
        err = data["error"]
        print(f"ОШИБКА {err.get('error_code')}: {err.get('error_string')} — {err.get('error_detail')}")
        return False

    ids = data.get("result", {}).get("ForecastIDs", [])
    if not ids:
        print(f"Нет ForecastID в ответе: {data}")
        return False

    forecast_id = ids[0]
    print(f"Forecast создан, ID={forecast_id}. Ожидаем результат...")

    get_payload = {"method": "get", "params": {"ForecastIDs": [forecast_id]}}
    async with httpx.AsyncClient(timeout=20) as client:
        for attempt in range(8):
            resp = await client.post(f"{BASE}/forecasts", json=get_payload, headers=HEADERS)
            data = resp.json()
            forecasts = data.get("result", {}).get("Forecasts", [])
            if forecasts:
                status = forecasts[0].get("Status", "")
                print(f"  Попытка {attempt+1}: статус={status}")
                if status == "Done":
                    for kw in forecasts[0].get("Keywords", []):
                        tv = kw.get("TrafficVolumeForecast", [])
                        if tv:
                            best = max(tv, key=lambda x: x.get("TrafficVolume", 0))
                            cpc = best.get("AvgClickCost") or best.get("CpcInCents", 0) / 100
                            print(f"    {kw.get('KeywordName')}: {cpc} руб. CPC")
                    return True
                if status == "Error":
                    print(f"  Ошибка прогноза: {forecasts[0]}")
                    return False
            await asyncio.sleep(2)

    print("Timeout — прогноз не готов за 16 сек")
    return False


# ──────────────────────────────────────────────────
# 3. Reports API (ReportsService)
# ──────────────────────────────────────────────────
async def test_reports():
    sep("3. Reports API (статистика)")

    from datetime import date, timedelta
    today = date.today()
    date_from = (today - timedelta(days=30)).isoformat()
    date_to = today.isoformat()

    payload = {
        "params": {
            "SelectionCriteria": {"DateFrom": date_from, "DateTo": date_to},
            "FieldNames": ["CampaignName", "Clicks", "Cost", "Impressions"],
            "ReportName": "TestReport",
            "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "NO",
            "IncludeDiscount": "NO",
        }
    }
    headers = {
        **HEADERS,
        "processingMode": "auto",
        "returnMoneyInMicros": "false",
        "skipReportHeader": "true",
        "skipReportSummary": "false",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.direct.yandex.com/json/v5/reports",
            json=payload,
            headers=headers,
        )

    print(f"HTTP {resp.status_code}")
    if resp.status_code in (200, 201):
        lines = resp.text.strip().splitlines()
        print(f"OK — строк в ответе: {len(lines)}")
        for line in lines[:5]:
            print(f"  {line}")
        return True
    else:
        try:
            err = resp.json()
            print(f"ОШИБКА: {json.dumps(err, ensure_ascii=False, indent=2)[:400]}")
        except Exception:
            print(f"ОШИБКА (raw): {resp.text[:400]}")
        return False


# ──────────────────────────────────────────────────
async def main():
    if not TOKEN:
        print("YANDEX_DIRECT_TOKEN / YANDEX_WORDSTAT_TOKEN не найден в .env")
        sys.exit(1)

    print(f"Токен: {TOKEN[:12]}...{TOKEN[-6:]}")

    results = {}
    results["campaigns"] = await test_campaigns()
    results["forecast"] = await test_forecast()
    results["reports"] = await test_reports()

    sep("ИТОГ")
    for name, ok in results.items():
        status = "✅ OK" if ok else "❌ FAIL"
        print(f"  {status}  {name}")


if __name__ == "__main__":
    asyncio.run(main())
