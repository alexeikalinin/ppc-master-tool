from fastapi import APIRouter
from backend.services.token_counter import counter
from backend.config import settings
from backend.services.ai_summary import _get_provider

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("")
async def get_usage():
    """Token usage stats for current server session + which API keys are configured."""
    data = counter.snapshot()
    data["keys"] = {
        "anthropic": bool(settings.anthropic_api_key),
        "openai": bool(settings.openai_api_key),
        "xai": bool(settings.xai_api_key),
        "active_provider": _get_provider() or None,
    }
    return data


@router.post("/reset")
async def reset_usage():
    """Reset all counters (e.g. after a billing cycle)."""
    counter.reset()
    return {"status": "reset"}
