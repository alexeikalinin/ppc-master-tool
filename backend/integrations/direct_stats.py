"""
Yandex Direct ReportsService integration.

Fetches campaign statistics across multiple dimensions (campaigns, keywords,
search queries, demographics, geo, ads) for performance audit.

API docs: https://yandex.ru/dev/direct/doc/reports/
"""

import asyncio
import csv
import io
from datetime import date, timedelta

import httpx

_BASE_URL = "https://api.direct.yandex.com/json/v5/reports"
_POLL_INTERVAL = 3  # seconds between polling attempts
_MAX_POLLS = 20


def _default_period() -> tuple[str, str]:
    today = date.today()
    return (today - timedelta(days=30)).isoformat(), today.isoformat()


def _parse_tsv(text: str) -> list[dict]:
    """Parse TSV report body (first row = headers, last row = Total — skip it)."""
    lines = text.strip().splitlines()
    if len(lines) < 2:
        return []
    reader = csv.DictReader(io.StringIO("\n".join(lines[:-1])), delimiter="\t")
    return list(reader)


async def _fetch_report(
    client: httpx.AsyncClient,
    token: str,
    report_name: str,
    report_type: str,
    fields: list[str],
    date_from: str,
    date_to: str,
    extra_params: dict | None = None,
) -> list[dict]:
    """
    Request a single report. Handles both inline (200) and queued (201) modes.
    Returns parsed rows as list[dict].
    """
    body: dict = {
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
    if extra_params:
        body["params"].update(extra_params)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "ru",
        "processingMode": "auto",
        "returnMoneyInMicros": "false",
        "skipReportHeader": "true",
        "skipReportSummary": "false",
    }

    for attempt in range(_MAX_POLLS):
        resp = await client.post(_BASE_URL, json=body, headers=headers, timeout=60)

        if resp.status_code == 200:
            return _parse_tsv(resp.text)

        if resp.status_code == 201:
            # Report queued — retry with RetryIn header
            retry_in = int(resp.headers.get("retryIn", _POLL_INTERVAL))
            await asyncio.sleep(max(retry_in, _POLL_INTERVAL))
            continue

        if resp.status_code == 202:
            # Still processing
            await asyncio.sleep(_POLL_INTERVAL)
            continue

        # Error
        print(f"[direct_stats] {report_name}: HTTP {resp.status_code} — {resp.text[:200]}")
        return []

    print(f"[direct_stats] {report_name}: max polls reached")
    return []


async def fetch_campaign_stats(
    token: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    Fetch all statistics slices needed for performance audit.

    Returns:
        {
            "campaigns": [...],
            "keywords": [...],
            "search_queries": [...],
            "demographics": [...],
            "geo": [...],
            "ads": [...],
        }
    """
    if not date_from or not date_to:
        date_from, date_to = _default_period()

    async with httpx.AsyncClient(timeout=120) as client:
        results = await asyncio.gather(
            _fetch_report(
                client, token, "CampaignStats", "CAMPAIGN_PERFORMANCE_REPORT",
                ["CampaignId", "CampaignName", "CampaignType",
                 "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost",
                 "Conversions", "CostPerConversion"],
                date_from, date_to,
            ),
            _fetch_report(
                client, token, "KeywordStats", "SEARCH_QUERY_PERFORMANCE_REPORT",
                ["CampaignName", "Keyword", "Impressions", "Clicks",
                 "Ctr", "AvgCpc", "Cost", "Conversions"],
                date_from, date_to,
                {"Filter": [{"Field": "Clicks", "Operator": "GREATER_THAN", "Values": ["0"]}]},
            ),
            _fetch_report(
                client, token, "SearchQueryStats", "SEARCH_QUERY_PERFORMANCE_REPORT",
                ["CampaignName", "Query", "Impressions", "Clicks",
                 "Ctr", "AvgCpc", "Cost"],
                date_from, date_to,
                {"Filter": [{"Field": "Clicks", "Operator": "GREATER_THAN", "Values": ["0"]}]},
            ),
            _fetch_report(
                client, token, "DemographicsStats", "GENDER_AGE_PERFORMANCE_REPORT",
                ["Gender", "Age", "Impressions", "Clicks", "Ctr",
                 "Cost", "Conversions", "ConversionRate"],
                date_from, date_to,
            ),
            _fetch_report(
                client, token, "GeoStats", "GEO_PERFORMANCE_REPORT",
                ["LocationOfPresenceName", "Clicks", "Cost",
                 "Conversions", "CostPerConversion", "Ctr"],
                date_from, date_to,
            ),
            _fetch_report(
                client, token, "AdStats", "AD_PERFORMANCE_REPORT",
                ["AdId", "AdTitle", "AdText", "CampaignName",
                 "Impressions", "Clicks", "Ctr", "Cost"],
                date_from, date_to,
                {"Filter": [{"Field": "Impressions", "Operator": "GREATER_THAN", "Values": ["100"]}]},
            ),
            return_exceptions=True,
        )

    labels = ["campaigns", "keywords", "search_queries", "demographics", "geo", "ads"]
    output: dict = {}
    for label, result in zip(labels, results):
        if isinstance(result, Exception):
            print(f"[direct_stats] {label} error: {result}")
            output[label] = []
        else:
            output[label] = result

    return output


def generate_demo_stats() -> dict:
    """Demo data when Direct API is unavailable (error_code 58 or no token)."""
    return {
        "campaigns": [
            {"CampaignId": "1001", "CampaignName": "Поиск — Металлочерепица", "CampaignType": "TEXT_CAMPAIGN",
             "Impressions": "12500", "Clicks": "420", "Ctr": "3.36", "AvgCpc": "95.20",
             "Cost": "39984", "Conversions": "18", "CostPerConversion": "2221"},
            {"CampaignId": "1002", "CampaignName": "РСЯ — Металлочерепица", "CampaignType": "TEXT_CAMPAIGN",
             "Impressions": "85000", "Clicks": "310", "Ctr": "0.36", "AvgCpc": "22.50",
             "Cost": "6975", "Conversions": "4", "CostPerConversion": "1743"},
            {"CampaignId": "1003", "CampaignName": "Поиск — Гибкая черепица", "CampaignType": "TEXT_CAMPAIGN",
             "Impressions": "4200", "Clicks": "85", "Ctr": "2.02", "AvgCpc": "140.00",
             "Cost": "11900", "Conversions": "2", "CostPerConversion": "5950"},
        ],
        "keywords": [
            {"CampaignName": "Поиск — Металлочерепица", "Keyword": "металлочерепица купить",
             "Impressions": "3200", "Clicks": "150", "Ctr": "4.69", "AvgCpc": "88.00", "Cost": "13200", "Conversions": "8"},
            {"CampaignName": "Поиск — Металлочерепица", "Keyword": "металлочерепица цена",
             "Impressions": "2800", "Clicks": "95", "Ctr": "3.39", "AvgCpc": "102.00", "Cost": "9690", "Conversions": "5"},
            {"CampaignName": "Поиск — Металлочерепица", "Keyword": "кровля металлическая",
             "Impressions": "4100", "Clicks": "28", "Ctr": "0.68", "AvgCpc": "120.00", "Cost": "3360", "Conversions": "0"},
            {"CampaignName": "Поиск — Металлочерепица", "Keyword": "+купить +кровлю",
             "Impressions": "1800", "Clicks": "12", "Ctr": "0.67", "AvgCpc": "135.00", "Cost": "1620", "Conversions": "0"},
        ],
        "search_queries": [
            {"CampaignName": "Поиск — Металлочерепица", "Query": "металлочерепица купить москва",
             "Impressions": "800", "Clicks": "42", "Ctr": "5.25", "AvgCpc": "85.00", "Cost": "3570"},
            {"CampaignName": "Поиск — Металлочерепица", "Query": "металлочерепица своими руками",
             "Impressions": "650", "Clicks": "31", "Ctr": "4.77", "AvgCpc": "72.00", "Cost": "2232"},
            {"CampaignName": "Поиск — Металлочерепица", "Query": "металлочерепица фото",
             "Impressions": "920", "Clicks": "25", "Ctr": "2.72", "AvgCpc": "45.00", "Cost": "1125"},
            {"CampaignName": "Поиск — Металлочерепица", "Query": "металлочерепица чертёж скачать",
             "Impressions": "380", "Clicks": "18", "Ctr": "4.74", "AvgCpc": "38.00", "Cost": "684"},
        ],
        "demographics": [
            {"Gender": "MALE", "Age": "AGE_25_34", "Impressions": "5200", "Clicks": "210", "Ctr": "4.04",
             "Cost": "19320", "Conversions": "11", "ConversionRate": "5.24"},
            {"Gender": "MALE", "Age": "AGE_35_44", "Impressions": "4100", "Clicks": "155", "Ctr": "3.78",
             "Cost": "14260", "Conversions": "6", "ConversionRate": "3.87"},
            {"Gender": "FEMALE", "Age": "AGE_25_34", "Impressions": "2100", "Clicks": "42", "Ctr": "2.00",
             "Cost": "3864", "Conversions": "1", "ConversionRate": "2.38"},
            {"Gender": "FEMALE", "Age": "AGE_45_54", "Impressions": "1800", "Clicks": "28", "Ctr": "1.56",
             "Cost": "2576", "Conversions": "0", "ConversionRate": "0"},
        ],
        "geo": [
            {"LocationOfPresenceName": "Москва", "Clicks": "180", "Cost": "18000",
             "Conversions": "10", "CostPerConversion": "1800", "Ctr": "3.80"},
            {"LocationOfPresenceName": "Московская область", "Clicks": "140", "Cost": "12600",
             "Conversions": "6", "CostPerConversion": "2100", "Ctr": "3.20"},
            {"LocationOfPresenceName": "Санкт-Петербург", "Clicks": "55", "Cost": "6050",
             "Conversions": "1", "CostPerConversion": "6050", "Ctr": "2.10"},
            {"LocationOfPresenceName": "Краснодар", "Clicks": "45", "Cost": "3600",
             "Conversions": "1", "CostPerConversion": "3600", "Ctr": "2.50"},
        ],
        "ads": [
            {"AdId": "2001", "AdTitle": "Металлочерепица — от 450 руб/м²",
             "AdText": "Доставка по Москве. Скидки оптовикам. Гарантия 50 лет!",
             "CampaignName": "Поиск — Металлочерепица",
             "Impressions": "5600", "Clicks": "280", "Ctr": "5.00", "Cost": "24640"},
            {"AdId": "2002", "AdTitle": "Кровля и металлочерепица",
             "AdText": "Широкий выбор. Монтаж под ключ. Звоните!",
             "CampaignName": "Поиск — Металлочерепица",
             "Impressions": "6900", "Clicks": "140", "Ctr": "2.03", "Cost": "15344"},
            {"AdId": "2003", "AdTitle": "Гибкая черепица в Москве",
             "AdText": "Популярные бренды. Доставка 1 день.",
             "CampaignName": "Поиск — Гибкая черепица",
             "Impressions": "4200", "Clicks": "85", "Ctr": "2.02", "Cost": "11900"},
        ],
    }
