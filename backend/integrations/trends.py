"""
Google Trends integration via pytrends.
Works without API key — uses unofficial Google Trends endpoint.

Used to enrich keywords with seasonality multipliers.
"""

import asyncio
from datetime import datetime


async def get_seasonality(keywords: list[str], region: str = "RU") -> dict[str, float]:
    """
    Return seasonality multiplier per keyword (ratio: current month / annual avg).
    Values > 1.0 = above average demand this month.
    Falls back to 1.0 for all keywords on any error.
    """
    if not keywords:
        return {}
    return await asyncio.get_event_loop().run_in_executor(
        None,
        _fetch_trends_sync,
        keywords[:5],
        region,  # pytrends limit: 5 kw per request
    )


def _fetch_trends_sync(keywords: list[str], region: str) -> dict[str, float]:
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl=_hl(region), tz=180, timeout=(10, 25))
        pytrends.build_payload(
            keywords,
            cat=0,
            timeframe="today 12-m",
            geo=region if region != "EU" else "DE",
        )
        df = pytrends.interest_over_time()

        if df.empty:
            return {kw: 1.0 for kw in keywords}

        current_month = datetime.now().month
        result: dict[str, float] = {}
        for kw in keywords:
            if kw not in df.columns:
                result[kw] = 1.0
                continue
            series = df[kw]
            annual_avg = series.mean()
            # Get last available value close to current month
            recent = series.iloc[-1]
            ratio = (
                round(float(recent) / float(annual_avg), 2) if annual_avg > 0 else 1.0
            )
            result[kw] = max(0.1, min(ratio, 5.0))  # clamp to [0.1, 5.0]
        return result

    except Exception:
        return {kw: 1.0 for kw in keywords}


def _hl(region: str) -> str:
    return {"RU": "ru", "UA": "uk", "BY": "ru", "KZ": "ru", "US": "en"}.get(
        region, "ru"
    )
