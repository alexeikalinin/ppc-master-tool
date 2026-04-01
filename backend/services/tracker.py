"""
Campaign Performance Tracker.

Снимает ежедневную статистику из Яндекс Директ API и сохраняет в Supabase:
- campaign_daily_stats  — по кампаниям
- keyword_daily_stats   — по ключевым словам (с текущей ставкой)

Запуск вручную:  python -m backend.services.tracker
Запуск по cron:  каждый день в 06:00 МСК (после того как Яндекс обновил данные за вчера)
"""

import asyncio
import csv
import io
import json
import logging
from datetime import date, timedelta

import httpx

from backend.config import settings
from backend.db import get_client

logger = logging.getLogger(__name__)

_DIRECT_BASE = "https://api.direct.yandex.com/json/v5"
_REPORTS_URL = f"{_DIRECT_BASE}/reports"
_CAMPAIGNS_URL = f"{_DIRECT_BASE}/campaigns"
_BIDS_URL = f"{_DIRECT_BASE}/bids"


def _get_token() -> str:
    return settings.yandex_direct_token or settings.yandex_wordstat_token or ""


def _headers(login: str | None = None) -> dict:
    h = {
        "Authorization": f"Bearer {_get_token()}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
    }
    if login:
        h["Client-Login"] = login
    return h


# ─────────────────────────────────────────────
# Получение списка кампаний
# ─────────────────────────────────────────────

async def fetch_campaigns(login: str | None = None) -> list[dict]:
    """Возвращает список активных кампаний аккаунта."""
    payload = {
        "method": "get",
        "params": {
            "SelectionCriteria": {"Statuses": ["ON", "OFF", "SUSPENDED"]},
            "FieldNames": ["Id", "Name", "Status", "Type"],
            "Page": {"Limit": 1000},
        },
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(_CAMPAIGNS_URL, json=payload, headers=_headers(login))

    data = resp.json()
    if "error" in data:
        logger.error(f"[tracker] campaigns error: {data['error']}")
        return []
    return data.get("result", {}).get("Campaigns", [])


# ─────────────────────────────────────────────
# Снятие статистики через Reports API
# ─────────────────────────────────────────────

async def _fetch_report_tsv(
    report_name: str,
    report_type: str,
    fields: list[str],
    date_from: str,
    date_to: str,
    login: str | None = None,
    extra: dict | None = None,
) -> list[dict]:
    """Запрашивает TSV-отчёт, ждёт готовности, возвращает список строк."""
    payload: dict = {
        "params": {
            "SelectionCriteria": {"DateFrom": date_from, "DateTo": date_to},
            "FieldNames": fields,
            "ReportName": report_name,
            "ReportType": report_type,
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "NO",
            "IncludeDiscount": "NO",
        }
    }
    if extra:
        payload["params"].update(extra)

    headers = {
        **_headers(login),
        "processingMode": "auto",
        "returnMoneyInMicros": "false",
        "skipReportHeader": "true",
        "skipReportSummary": "false",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        for attempt in range(15):
            resp = await client.post(_REPORTS_URL, json=payload, headers=headers)
            if resp.status_code == 200:
                lines = resp.text.strip().splitlines()
                if len(lines) < 2:
                    return []
                reader = csv.DictReader(
                    io.StringIO("\n".join(lines[:-1])), delimiter="\t"
                )
                return list(reader)
            if resp.status_code in (201, 202):
                retry = int(resp.headers.get("retryIn", 3))
                await asyncio.sleep(max(retry, 3))
                continue
            logger.error(f"[tracker] report {report_name}: HTTP {resp.status_code} — {resp.text[:200]}")
            return []

    logger.error(f"[tracker] report {report_name}: timeout")
    return []


async def fetch_campaign_stats(
    date_from: str, date_to: str, login: str | None = None
) -> list[dict]:
    return await _fetch_report_tsv(
        report_name="CampaignStats",
        report_type="CAMPAIGN_PERFORMANCE_REPORT",
        fields=["CampaignId", "CampaignName", "CampaignType",
                "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost", "Conversions"],
        date_from=date_from,
        date_to=date_to,
        login=login,
    )


async def fetch_keyword_stats(
    date_from: str, date_to: str, login: str | None = None
) -> list[dict]:
    # CRITERIA_PERFORMANCE_REPORT — статистика по ключевым словам
    # Поле CriterionId = keyword_id, Criterion = текст ключа
    return await _fetch_report_tsv(
        report_name="KeywordStats",
        report_type="CRITERIA_PERFORMANCE_REPORT",
        fields=["CampaignId", "CampaignName", "CriterionId", "Criterion",
                "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost", "Conversions"],
        date_from=date_from,
        date_to=date_to,
        login=login,
    )


# ─────────────────────────────────────────────
# Получение текущих ставок по ключам
# ─────────────────────────────────────────────

async def fetch_current_bids(
    campaign_ids: list[int], login: str | None = None
) -> dict[str, float]:
    """Возвращает {keyword_id: bid_rub}."""
    if not campaign_ids:
        return {}

    payload = {
        "method": "get",
        "params": {
            "SelectionCriteria": {"CampaignIds": campaign_ids[:10]},  # max 10 за раз
            "FieldNames": ["KeywordId", "Bid"],
        },
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(_BIDS_URL, json=payload, headers=_headers(login))

    data = resp.json()
    if "error" in data:
        logger.warning(f"[tracker] bids error: {data['error']}")
        return {}

    result = {}
    for item in data.get("result", {}).get("Bids", []):
        kid = str(item.get("KeywordId", ""))
        bid = item.get("Bid")
        if kid and bid is not None:
            result[kid] = round(float(bid), 2)
    return result


# ─────────────────────────────────────────────
# Сохранение в Supabase
# ─────────────────────────────────────────────

def _safe_float(val, default=0.0) -> float:
    try:
        return float(val) if val not in (None, "", "--") else default
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0) -> int:
    try:
        return int(float(val)) if val not in (None, "", "--") else default
    except (ValueError, TypeError):
        return default


async def save_campaign_stats(
    account_id: str, stat_date: str, rows: list[dict]
) -> int:
    """Сохраняет статистику кампаний. Возвращает количество записей."""
    if not rows:
        return 0

    db = get_client()
    records = []
    for r in rows:
        clicks = _safe_int(r.get("Clicks"))
        cost = _safe_float(r.get("Cost"))
        ctr = _safe_float(r.get("Ctr"))
        avg_cpc = _safe_float(r.get("AvgCpc"))
        conversions = _safe_int(r.get("Conversions"))
        cpa = round(cost / conversions, 2) if conversions > 0 else None

        records.append({
            "account_id": account_id,
            "stat_date": stat_date,
            "campaign_id": _safe_int(r.get("CampaignId")),
            "campaign_name": r.get("CampaignName", ""),
            "campaign_type": r.get("CampaignType", ""),
            "impressions": _safe_int(r.get("Impressions")),
            "clicks": clicks,
            "cost": cost,
            "conversions": conversions,
            "ctr": ctr,
            "avg_cpc": avg_cpc,
            "cpa": cpa,
        })

    try:
        db.table("campaign_daily_stats").upsert(
            records, on_conflict="account_id,stat_date,campaign_id"
        ).execute()
        return len(records)
    except Exception as e:
        logger.error(f"[tracker] save_campaign_stats error: {e}")
        return 0


async def save_keyword_stats(
    account_id: str,
    stat_date: str,
    rows: list[dict],
    bids: dict[str, float],
) -> int:
    """Сохраняет статистику ключей с текущей ставкой."""
    if not rows:
        return 0

    db = get_client()
    records = []
    for r in rows:
        kid = str(r.get("CriterionId", ""))
        records.append({
            "account_id": account_id,
            "stat_date": stat_date,
            "campaign_id": _safe_int(r.get("CampaignId")),
            "keyword_id": _safe_int(r.get("CriterionId", 0)),
            "keyword_text": r.get("Criterion") or r.get("Keyword") or r.get("Query", ""),
            "impressions": _safe_int(r.get("Impressions")),
            "clicks": _safe_int(r.get("Clicks")),
            "cost": _safe_float(r.get("Cost")),
            "conversions": _safe_int(r.get("Conversions")),
            "avg_cpc": _safe_float(r.get("AvgCpc")),
            "current_bid": bids.get(kid),
        })

    try:
        db.table("keyword_daily_stats").upsert(
            records, on_conflict="account_id,stat_date,keyword_id"
        ).execute()
        return len(records)
    except Exception as e:
        logger.error(f"[tracker] save_keyword_stats error: {e}")
        return 0


# ─────────────────────────────────────────────
# Основная функция снятия статистики
# ─────────────────────────────────────────────

async def run_daily_snapshot(
    account_id: str,
    login: str,
    target_date: date | None = None,
) -> dict:
    """
    Снимает статистику за target_date (по умолчанию — вчера).
    Возвращает сводку: сколько кампаний и ключей сохранено.
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    date_str = target_date.isoformat()
    logger.info(f"[tracker] Снимаем статистику за {date_str} для аккаунта {login}")

    # 1. Статистика кампаний
    campaign_rows = await fetch_campaign_stats(date_str, date_str, login)
    campaigns_saved = await save_campaign_stats(account_id, date_str, campaign_rows)

    # 2. Статистика ключей
    keyword_rows = await fetch_keyword_stats(date_str, date_str, login)

    # 3. Текущие ставки (берём campaign_id из статистики кампаний)
    campaign_ids = list({_safe_int(r.get("CampaignId")) for r in campaign_rows if r.get("CampaignId")})
    bids = await fetch_current_bids(campaign_ids, login)

    keywords_saved = await save_keyword_stats(account_id, date_str, keyword_rows, bids)

    result = {
        "date": date_str,
        "login": login,
        "campaigns_saved": campaigns_saved,
        "keywords_saved": keywords_saved,
        "bids_fetched": len(bids),
    }
    logger.info(f"[tracker] Готово: {result}")
    return result


# ─────────────────────────────────────────────
# CLI запуск
# ─────────────────────────────────────────────

async def _main():
    import os
    from dotenv import load_dotenv
    load_dotenv()

    login = os.getenv("YANDEX_LOGIN", "alexeikalinin1")

    # Для CLI нужен account_id из БД — берём первый или создаём
    db = get_client()
    existing = db.table("direct_accounts").select("id").eq("login", login).execute()

    if existing.data:
        account_id = existing.data[0]["id"]
        print(f"Аккаунт найден: {account_id}")
    else:
        result = db.table("direct_accounts").insert({
            "login": login,
            "label": f"Аккаунт {login}",
            "token_hint": (settings.yandex_direct_token or "")[:12],
        }).execute()
        account_id = result.data[0]["id"]
        print(f"Аккаунт создан: {account_id}")

    snapshot = await run_daily_snapshot(account_id, login)
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main())
