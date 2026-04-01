from supabase import create_client, Client
from backend.config import settings

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        key = settings.supabase_service_role_key or settings.supabase_key
        _client = create_client(settings.supabase_url, key)
    return _client


async def save_report(user_id: str | None, url: str, region: str, json_data: dict) -> str:
    """Insert a report and return its id."""
    client = get_client()
    row: dict = {"url": url, "region": region, "json_data": json_data}
    if user_id is not None:
        row["user_id"] = user_id
    result = client.table("reports").insert(row).execute()
    return result.data[0]["id"]


async def list_reports(user_id: str | None = None) -> list[dict]:
    client = get_client()
    q = (
        client.table("reports")
        .select("id, url, region, created_at, json_data")
        .order("created_at", desc=True)
        .limit(50)
    )
    if user_id is not None:
        q = q.eq("user_id", user_id)
    result = q.execute()
    rows = []
    for r in result.data:
        site = (r.get("json_data") or {}).get("site") or {}
        rows.append({
            "id": r["id"],
            "url": r["url"],
            "region": r["region"],
            "created_at": r["created_at"],
            "title": site.get("title"),
        })
    return rows


async def get_report(report_id: str, user_id: str | None = None) -> dict | None:
    client = get_client()
    q = client.table("reports").select("*").eq("id", report_id)
    if user_id is not None:
        q = q.eq("user_id", user_id)
    result = q.single().execute()
    return result.data
