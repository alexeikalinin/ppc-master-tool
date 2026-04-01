"""
Bidding Robot — применяет правила bot_rules к ставкам ключевых слов.

Правила:
  night_reduction  {"from_hour": 2, "to_hour": 8, "reduction_pct": 40}
  peak_boost       {"hours": [19,20,21,22], "boost_pct": 20}
  cpa_limit        {"max_cpa_rub": 500, "min_clicks": 30, "action": "reduce_50pct"}
  position_guard   {"target_position": 2, "max_bid_rub": 150}   (требует AvgPosition в отчёте)

Порядок:
  1. Загрузить активные правила аккаунта/кампании
  2. Загрузить статистику ключей за последние N дней
  3. Загрузить текущие ставки
  4. Применить правила → посчитать новые ставки
  5. Применить через Яндекс Direct API
  6. Записать изменения в bid_changes

Запуск вручную: python -m backend.services.bid_robot
"""

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from backend.config import settings
from backend.db import get_client

logger = logging.getLogger(__name__)

_BIDS_URL = "https://api.direct.yandex.com/json/v5/bids"
_MIN_BID_RUB = 0.30   # минимальная ставка Яндекс
_MAX_BID_RUB = 2500.0


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
# Загрузка данных из Supabase
# ─────────────────────────────────────────────

def _load_bot_rules(db, account_id: str, campaign_id: int | None = None) -> list[dict]:
    """Загружает активные правила для аккаунта (и опционально кампании)."""
    q = db.table("bot_rules").select("*").eq("account_id", account_id).eq("is_active", True)
    rules = q.execute().data or []

    if campaign_id is not None:
        # Берём правила для конкретной кампании + правила для всего аккаунта (campaign_id IS NULL)
        rules = [r for r in rules if r["campaign_id"] is None or r["campaign_id"] == campaign_id]

    return rules


def _load_keyword_stats(db, account_id: str, days: int = 7) -> list[dict]:
    """Статистика ключей за последние N дней."""
    date_from = (date.today() - timedelta(days=days)).isoformat()
    return (
        db.table("keyword_daily_stats")
        .select("keyword_id,campaign_id,keyword_text,clicks,cost,conversions,avg_cpc,current_bid,stat_date")
        .eq("account_id", account_id)
        .gte("stat_date", date_from)
        .order("stat_date", desc=True)
        .limit(10000)
        .execute()
        .data or []
    )


# ─────────────────────────────────────────────
# Агрегация статистики по ключу
# ─────────────────────────────────────────────

def _aggregate_keyword_stats(rows: list[dict]) -> dict[int, dict]:
    """
    Агрегирует строки по keyword_id.
    Возвращает {keyword_id: {clicks, cost, conversions, cpa, avg_cpc, current_bid, campaign_id, keyword_text}}.
    """
    agg: dict[int, dict] = {}
    for r in rows:
        kid = int(r["keyword_id"])
        if kid not in agg:
            agg[kid] = {
                "keyword_id": kid,
                "campaign_id": r["campaign_id"],
                "keyword_text": r["keyword_text"],
                "clicks": 0,
                "cost": 0.0,
                "conversions": 0,
                "current_bid": r.get("current_bid"),  # берём самую свежую
            }
        else:
            # current_bid уже взяли из первой (самой свежей) записи
            pass
        agg[kid]["clicks"] += int(r.get("clicks") or 0)
        agg[kid]["cost"] += float(r.get("cost") or 0)
        agg[kid]["conversions"] += int(r.get("conversions") or 0)

    for kid, v in agg.items():
        clicks = v["clicks"]
        cost = v["cost"]
        conv = v["conversions"]
        v["avg_cpc"] = round(cost / clicks, 2) if clicks > 0 else 0.0
        v["cpa"] = round(cost / conv, 2) if conv > 0 else None

    return agg


# ─────────────────────────────────────────────
# Применение правил
# ─────────────────────────────────────────────

def _current_hour_msk() -> int:
    """Текущий час по МСК (UTC+3)."""
    return (datetime.now(timezone.utc) + timedelta(hours=3)).hour


def _clamp_bid(bid: float) -> float:
    return round(max(_MIN_BID_RUB, min(_MAX_BID_RUB, bid)), 2)


def apply_rules(
    kw: dict,
    rules: list[dict],
    hour: int | None = None,
) -> tuple[float | None, str | None, str | None]:
    """
    Применяет все правила к ключевому слову.
    Возвращает (new_bid, reason_text, rule_name) или (None, None, None) если изменений нет.
    """
    current_bid = kw.get("current_bid")
    if current_bid is None:
        return None, None, None

    current_bid = float(current_bid)
    if hour is None:
        hour = _current_hour_msk()

    # Собираем множители от всех применимых правил
    multiplier = 1.0
    reasons: list[str] = []
    rule_names: list[str] = []

    for rule in rules:
        name = rule["rule_name"]
        params: dict[str, Any] = rule.get("params") or {}

        if name == "night_reduction":
            from_h = int(params.get("from_hour", 2))
            to_h = int(params.get("to_hour", 8))
            pct = float(params.get("reduction_pct", 40))
            # Обрабатываем переход через полночь: from_h=23, to_h=6
            in_range = (
                (from_h <= to_h and from_h <= hour < to_h)
                or (from_h > to_h and (hour >= from_h or hour < to_h))
            )
            if in_range:
                multiplier *= (1 - pct / 100)
                reasons.append(f"ночное снижение -{pct}% (час {hour})")
                rule_names.append(name)

        elif name == "peak_boost":
            hours = [int(h) for h in params.get("hours", [])]
            pct = float(params.get("boost_pct", 20))
            if hour in hours:
                multiplier *= (1 + pct / 100)
                reasons.append(f"пиковый boost +{pct}% (час {hour})")
                rule_names.append(name)

        elif name == "cpa_limit":
            max_cpa = float(params.get("max_cpa_rub", 500))
            min_clicks = int(params.get("min_clicks", 30))
            action = params.get("action", "reduce_50pct")
            cpa = kw.get("cpa")
            clicks = kw.get("clicks", 0)
            if cpa is not None and cpa > max_cpa and clicks >= min_clicks:
                if action == "reduce_50pct":
                    multiplier *= 0.5
                    reasons.append(f"CPA {cpa}₽ > лимита {max_cpa}₽ → -50%")
                elif action == "reduce_30pct":
                    multiplier *= 0.7
                    reasons.append(f"CPA {cpa}₽ > лимита {max_cpa}₽ → -30%")
                rule_names.append(name)

        elif name == "position_guard":
            max_bid = float(params.get("max_bid_rub", 150))
            # Без позиции из API — просто не даём ставке превысить max_bid
            if current_bid * multiplier > max_bid:
                multiplier = max_bid / current_bid if current_bid > 0 else 1.0
                reasons.append(f"position_guard: ставка ≤ {max_bid}₽")
                rule_names.append(name)

    if multiplier == 1.0:
        return None, None, None

    new_bid = _clamp_bid(current_bid * multiplier)
    if new_bid == current_bid:
        return None, None, None

    reason = "; ".join(reasons)
    rule_name = ",".join(dict.fromkeys(rule_names))  # уникальные, порядок сохранён
    return new_bid, reason, rule_name


# ─────────────────────────────────────────────
# Применение ставок через Direct API
# ─────────────────────────────────────────────

async def _set_bids(
    bid_updates: list[dict],  # [{KeywordId, Bid}]
    login: str | None = None,
) -> dict:
    """Устанавливает ставки пачками по 10 000 (лимит API)."""
    if not bid_updates:
        return {"updated": 0, "errors": 0}

    updated = 0
    errors = 0
    chunk_size = 10_000

    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(0, len(bid_updates), chunk_size):
            chunk = bid_updates[i : i + chunk_size]
            payload = {
                "method": "set",
                "params": {"Bids": chunk},
            }
            resp = await client.post(_BIDS_URL, json=payload, headers=_headers(login))
            data = resp.json()
            if "error" in data:
                logger.error(f"[bot] set bids error: {data['error']}")
                errors += len(chunk)
            else:
                results = data.get("result", {}).get("SetResults", [])
                for r in results:
                    if "Errors" in r:
                        errors += 1
                    else:
                        updated += 1

    return {"updated": updated, "errors": errors}


# ─────────────────────────────────────────────
# Запись изменений в лог
# ─────────────────────────────────────────────

def _log_bid_changes(
    db,
    account_id: str,
    changes: list[dict],
    experiment_id: str | None = None,
) -> None:
    if not changes:
        return
    for c in changes:
        c["account_id"] = account_id
        c["source"] = "bot"
        if experiment_id:
            c["experiment_id"] = experiment_id
    try:
        db.table("bid_changes").insert(changes).execute()
    except Exception as e:
        logger.error(f"[bot] log_bid_changes error: {e}")


# ─────────────────────────────────────────────
# Главная функция робота
# ─────────────────────────────────────────────

async def run_bot(
    account_id: str,
    login: str,
    campaign_id: int | None = None,
    dry_run: bool = False,
    experiment_id: str | None = None,
    stats_days: int = 7,
) -> dict:
    """
    Запускает биддинг-робота для аккаунта.

    dry_run=True — считает новые ставки, но НЕ применяет их (для тестирования).
    Возвращает сводку: сколько ставок изменено, общий ∆ бюджета.
    """
    db = get_client()

    rules = _load_bot_rules(db, account_id, campaign_id)
    if not rules:
        return {"status": "no_rules", "changes": 0}

    rows = _load_keyword_stats(db, account_id, stats_days)
    if not rows:
        return {"status": "no_stats", "changes": 0}

    kw_stats = _aggregate_keyword_stats(rows)
    hour = _current_hour_msk()

    bid_updates: list[dict] = []
    change_log: list[dict] = []

    for kid, kw in kw_stats.items():
        # Применяем только правила для нужной кампании
        kw_rules = [
            r for r in rules
            if r["campaign_id"] is None or r["campaign_id"] == kw["campaign_id"]
        ]
        new_bid, reason, rule_name = apply_rules(kw, kw_rules, hour)
        if new_bid is None:
            continue

        bid_updates.append({
            "KeywordId": kid,
            "Bid": new_bid,
        })
        change_log.append({
            "campaign_id": kw["campaign_id"],
            "campaign_name": None,
            "keyword_id": kid,
            "keyword_text": kw["keyword_text"],
            "bid_before": kw["current_bid"],
            "bid_after": new_bid,
            "reason": reason,
            "rule_triggered": rule_name,
            "experiment_id": experiment_id,
        })

    if not bid_updates:
        return {"status": "no_changes", "changes": 0, "dry_run": dry_run}

    if not dry_run:
        apply_result = await _set_bids(bid_updates, login)
        _log_bid_changes(db, account_id, change_log, experiment_id)
    else:
        apply_result = {"updated": len(bid_updates), "errors": 0, "dry_run": True}

    total_before = sum(c["bid_before"] for c in change_log if c["bid_before"])
    total_after = sum(c["bid_after"] for c in change_log)

    return {
        "status": "ok",
        "dry_run": dry_run,
        "changes": len(change_log),
        "api_result": apply_result,
        "avg_bid_before": round(total_before / len(change_log), 2) if change_log else 0,
        "avg_bid_after": round(total_after / len(change_log), 2) if change_log else 0,
        "preview": change_log[:20],  # первые 20 изменений для превью
    }


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

async def _main():
    import json
    import os
    from dotenv import load_dotenv
    load_dotenv()

    account_id = os.getenv("TRACKER_ACCOUNT_ID", "")
    login = os.getenv("YANDEX_LOGIN", "alexeikalinin1")
    dry = os.getenv("DRY_RUN", "1") != "0"

    if not account_id:
        print("Задайте TRACKER_ACCOUNT_ID в .env")
        return

    result = await run_bot(account_id, login, dry_run=dry)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main())
