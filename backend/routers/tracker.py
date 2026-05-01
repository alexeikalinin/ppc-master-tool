"""
Tracker API — управление снятием статистики и просмотр данных.

POST /tracker/snapshot          — снять статистику за вчера (или указанную дату)
GET  /tracker/campaigns         — статистика кампаний за период
GET  /tracker/keywords          — статистика ключей за период
GET  /tracker/accounts          — список подключённых аккаунтов
POST /tracker/accounts          — добавить аккаунт
GET  /tracker/bid-changes       — лог изменений ставок
GET  /tracker/bot-rules         — правила биддинг-робота
POST /tracker/bot-rules         — добавить правило
PATCH /tracker/bot-rules/{id}   — обновить правило
DELETE /tracker/bot-rules/{id}  — удалить правило
POST /tracker/bot/run           — запустить робота
GET  /tracker/experiments       — список A/B экспериментов
POST /tracker/experiments       — создать эксперимент
PATCH /tracker/experiments/{id} — обновить эксперимент
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.db import get_client
from backend.services.tracker import run_daily_snapshot, fetch_campaigns
from backend.services.bid_robot import run_bot

router = APIRouter(prefix="/tracker", tags=["tracker"])


class AccountIn(BaseModel):
    login: str
    label: Optional[str] = None


class SnapshotIn(BaseModel):
    account_id: str
    target_date: Optional[str] = None  # YYYY-MM-DD, по умолчанию вчера


class BotRuleIn(BaseModel):
    account_id: str
    campaign_id: Optional[int] = None
    rule_name: str   # night_reduction | peak_boost | cpa_limit | position_guard
    params: dict[str, Any] = {}
    is_active: bool = True


class BotRuleUpdate(BaseModel):
    params: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class BotRunIn(BaseModel):
    account_id: str
    campaign_id: Optional[int] = None
    dry_run: bool = True
    experiment_id: Optional[str] = None
    stats_days: int = 7


class ExperimentIn(BaseModel):
    account_id: str
    name: str
    description: Optional[str] = None
    campaign_a_id: int
    campaign_b_id: int
    campaign_a_label: str = "Ручное"
    campaign_b_label: str = "Робот"
    started_at: str  # YYYY-MM-DD


class ExperimentUpdate(BaseModel):
    ended_at: Optional[str] = None
    status: Optional[str] = None   # active | paused | completed
    conclusion: Optional[str] = None


# ─────────────────────────────────────────────
# Аккаунты
# ─────────────────────────────────────────────

@router.get("/accounts")
async def list_accounts():
    db = get_client()
    result = db.table("direct_accounts").select("id,login,label,is_active,created_at").execute()
    return result.data


@router.post("/accounts")
async def add_account(body: AccountIn):
    from backend.config import settings
    db = get_client()
    result = db.table("direct_accounts").insert({
        "login": body.login,
        "label": body.label or body.login,
        "token_hint": (settings.yandex_direct_token or "")[:12],
    }).execute()
    return result.data[0]


# ─────────────────────────────────────────────
# Снятие статистики
# ─────────────────────────────────────────────

@router.post("/snapshot")
async def run_snapshot(body: SnapshotIn):
    db = get_client()
    acc = db.table("direct_accounts").select("id,login").eq("id", body.account_id).execute()
    if not acc.data:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    login = acc.data[0]["login"]
    target = date.fromisoformat(body.target_date) if body.target_date else None

    result = await run_daily_snapshot(body.account_id, login, target)
    return result


# ─────────────────────────────────────────────
# Список кампаний из Директа (без снапшота)
# ─────────────────────────────────────────────

@router.get("/accounts/{account_id}/campaigns")
async def list_campaigns_live(account_id: str, debug: bool = False):
    """Список кампаний напрямую из Яндекс Директ API (не из БД)."""
    import httpx as _httpx
    from backend.services.tracker import _headers, _CAMPAIGNS_URL
    db = get_client()
    acc = db.table("direct_accounts").select("id,login").eq("id", account_id).execute()
    if not acc.data:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    login = acc.data[0]["login"]
    payload = {
        "method": "get",
        "params": {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "Status", "State", "Type"],
            "Page": {"Limit": 1000},
        },
    }
    async with _httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(_CAMPAIGNS_URL, json=payload, headers=_headers(login))
    data = resp.json()
    if debug:
        return {"status_code": resp.status_code, "raw": data}
    if "error" in data:
        raise HTTPException(status_code=502, detail=data["error"])
    return data.get("result", {}).get("Campaigns", [])


# ─────────────────────────────────────────────
# Статистика кампаний
# ─────────────────────────────────────────────

@router.get("/campaigns")
async def get_campaign_stats(
    account_id: str = Query(...),
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
):
    if not date_from:
        date_from = (date.today() - timedelta(days=30)).isoformat()
    if not date_to:
        date_to = date.today().isoformat()

    db = get_client()
    result = (
        db.table("campaign_daily_stats")
        .select("*")
        .eq("account_id", account_id)
        .gte("stat_date", date_from)
        .lte("stat_date", date_to)
        .order("stat_date", desc=True)
        .execute()
    )
    return result.data


# ─────────────────────────────────────────────
# Статистика ключей
# ─────────────────────────────────────────────

@router.get("/keywords")
async def get_keyword_stats(
    account_id: str = Query(...),
    campaign_id: Optional[int] = Query(default=None),
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
    limit: int = Query(default=100, le=1000),
):
    if not date_from:
        date_from = (date.today() - timedelta(days=7)).isoformat()
    if not date_to:
        date_to = date.today().isoformat()

    db = get_client()
    q = (
        db.table("keyword_daily_stats")
        .select("*")
        .eq("account_id", account_id)
        .gte("stat_date", date_from)
        .lte("stat_date", date_to)
        .order("stat_date", desc=True)
        .limit(limit)
    )
    if campaign_id:
        q = q.eq("campaign_id", campaign_id)

    result = q.execute()
    return result.data


# ─────────────────────────────────────────────
# Лог изменений ставок
# ─────────────────────────────────────────────

@router.get("/bid-changes")
async def get_bid_changes(
    account_id: str = Query(...),
    date_from: str = Query(default=None),
    source: Optional[str] = Query(default=None),  # bot | manual | import
    limit: int = Query(default=100, le=500),
):
    if not date_from:
        date_from = (date.today() - timedelta(days=30)).isoformat()

    db = get_client()
    q = (
        db.table("bid_changes")
        .select("*")
        .eq("account_id", account_id)
        .gte("changed_at", date_from)
        .order("changed_at", desc=True)
        .limit(limit)
    )
    if source:
        q = q.eq("source", source)

    result = q.execute()
    return result.data


# ─────────────────────────────────────────────
# Правила биддинг-робота
# ─────────────────────────────────────────────

@router.get("/bot-rules")
async def list_bot_rules(
    account_id: str = Query(...),
    campaign_id: Optional[int] = Query(default=None),
):
    db = get_client()
    q = db.table("bot_rules").select("*").eq("account_id", account_id)
    if campaign_id is not None:
        q = q.eq("campaign_id", campaign_id)
    return q.order("created_at").execute().data


@router.post("/bot-rules", status_code=201)
async def create_bot_rule(body: BotRuleIn):
    db = get_client()
    row = {
        "account_id": body.account_id,
        "campaign_id": body.campaign_id,
        "rule_name": body.rule_name,
        "params": body.params,
        "is_active": body.is_active,
    }
    result = db.table("bot_rules").insert(row).execute()
    return result.data[0]


@router.patch("/bot-rules/{rule_id}")
async def update_bot_rule(rule_id: str, body: BotRuleUpdate):
    db = get_client()
    updates = {}
    if body.params is not None:
        updates["params"] = body.params
    if body.is_active is not None:
        updates["is_active"] = body.is_active
    if not updates:
        raise HTTPException(status_code=400, detail="Нет полей для обновления")
    result = db.table("bot_rules").update(updates).eq("id", rule_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    return result.data[0]


@router.delete("/bot-rules/{rule_id}", status_code=204)
async def delete_bot_rule(rule_id: str):
    db = get_client()
    db.table("bot_rules").delete().eq("id", rule_id).execute()


# ─────────────────────────────────────────────
# Запуск робота
# ─────────────────────────────────────────────

@router.post("/bot/run")
async def run_bidding_bot(body: BotRunIn):
    db = get_client()
    acc = db.table("direct_accounts").select("id,login").eq("id", body.account_id).execute()
    if not acc.data:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    login = acc.data[0]["login"]

    result = await run_bot(
        account_id=body.account_id,
        login=login,
        campaign_id=body.campaign_id,
        dry_run=body.dry_run,
        experiment_id=body.experiment_id,
        stats_days=body.stats_days,
    )
    return result


# ─────────────────────────────────────────────
# A/B Эксперименты
# ─────────────────────────────────────────────

@router.get("/experiments")
async def list_experiments(
    account_id: str = Query(...),
    status: Optional[str] = Query(default=None),  # active | paused | completed
):
    db = get_client()
    q = db.table("experiments").select("*").eq("account_id", account_id)
    if status:
        q = q.eq("status", status)
    return q.order("started_at", desc=True).execute().data


@router.post("/experiments", status_code=201)
async def create_experiment(body: ExperimentIn):
    db = get_client()
    row = {
        "account_id": body.account_id,
        "name": body.name,
        "description": body.description,
        "campaign_a_id": body.campaign_a_id,
        "campaign_b_id": body.campaign_b_id,
        "campaign_a_label": body.campaign_a_label,
        "campaign_b_label": body.campaign_b_label,
        "started_at": body.started_at,
        "status": "active",
    }
    result = db.table("experiments").insert(row).execute()
    return result.data[0]


@router.patch("/experiments/{experiment_id}")
async def update_experiment(experiment_id: str, body: ExperimentUpdate):
    db = get_client()
    updates = {}
    if body.ended_at is not None:
        updates["ended_at"] = body.ended_at
    if body.status is not None:
        if body.status not in ("active", "paused", "completed"):
            raise HTTPException(status_code=400, detail="Неверный статус")
        updates["status"] = body.status
    if body.conclusion is not None:
        updates["conclusion"] = body.conclusion
    if not updates:
        raise HTTPException(status_code=400, detail="Нет полей для обновления")
    result = db.table("experiments").update(updates).eq("id", experiment_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Эксперимент не найден")
    return result.data[0]


@router.get("/experiments/{experiment_id}/summary")
async def experiment_summary(experiment_id: str):
    """Сравнительный итог кампаний A и B за период эксперимента."""
    db = get_client()
    exp = db.table("experiments").select("*").eq("id", experiment_id).execute()
    if not exp.data:
        raise HTTPException(status_code=404, detail="Эксперимент не найден")
    e = exp.data[0]

    date_from = e["started_at"]
    date_to = e["ended_at"] or date.today().isoformat()

    def _stats_for(campaign_id: int) -> dict:
        rows = (
            db.table("campaign_daily_stats")
            .select("impressions,clicks,cost,conversions")
            .eq("account_id", e["account_id"])
            .eq("campaign_id", campaign_id)
            .gte("stat_date", date_from)
            .lte("stat_date", date_to)
            .execute()
            .data or []
        )
        impressions = sum(r["impressions"] for r in rows)
        clicks = sum(r["clicks"] for r in rows)
        cost = sum(float(r["cost"]) for r in rows)
        conversions = sum(r["conversions"] for r in rows)
        return {
            "impressions": impressions,
            "clicks": clicks,
            "cost": round(cost, 2),
            "conversions": conversions,
            "ctr": round(clicks / impressions * 100, 2) if impressions else None,
            "avg_cpc": round(cost / clicks, 2) if clicks else None,
            "cpa": round(cost / conversions, 2) if conversions else None,
        }

    return {
        "experiment": e,
        "campaign_a": {
            "label": e["campaign_a_label"],
            "campaign_id": e["campaign_a_id"],
            **_stats_for(e["campaign_a_id"]),
        },
        "campaign_b": {
            "label": e["campaign_b_label"],
            "campaign_id": e["campaign_b_id"],
            **_stats_for(e["campaign_b_id"]),
        },
    }
