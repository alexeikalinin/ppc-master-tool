"""
Integration + unit tests for the PPC Master Tool backend.
Run with: pytest backend/tests/ -v
"""

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from backend.app import app
from backend.services.keywords import get_keywords, _stub_keywords, _get_seeds
from backend.services.clustering import cluster_keywords
from backend.services.audience import infer_audience
from backend.services.campaigns import generate_campaigns
from backend.services.media_plan import build_media_plan
from backend.models import Keyword

# ---------- Fixtures ----------


@pytest.fixture
def sample_keywords() -> list[Keyword]:
    seeds = _get_seeds("e-commerce", None)
    return _stub_keywords("e-commerce", "RU", seeds)


# ---------- Unit tests ----------


class TestKeywords:
    def test_stub_returns_keywords(self, sample_keywords):
        assert len(sample_keywords) > 0

    def test_stub_has_both_platforms(self, sample_keywords):
        platforms = {kw.platform for kw in sample_keywords}
        assert "yandex" in platforms
        assert "google" in platforms

    def test_cpc_positive(self, sample_keywords):
        assert all(kw.cpc > 0 for kw in sample_keywords)

    def test_frequency_positive(self, sample_keywords):
        assert all(kw.frequency > 0 for kw in sample_keywords)

    def test_seasonality_in_range(self, sample_keywords):
        for kw in sample_keywords:
            assert 0.0 <= kw.seasonality <= 5.0

    @pytest.mark.asyncio
    async def test_get_keywords_stub_mode(self):
        kws = await get_keywords("services", "RU")
        assert len(kws) >= 10

    @pytest.mark.asyncio
    async def test_hints_added_to_seeds(self):
        kws = await get_keywords("e-commerce", "RU", hints=["уникальный товар"])
        texts = {kw.text for kw in kws}
        assert "уникальный товар" in texts


class TestClustering:
    def test_produces_groups(self, sample_keywords):
        groups = cluster_keywords(sample_keywords)
        assert len(groups) >= 3

    def test_groups_have_keywords(self, sample_keywords):
        groups = cluster_keywords(sample_keywords)
        for g in groups:
            assert len(g.keywords) > 0

    def test_groups_have_minus_words(self, sample_keywords):
        groups = cluster_keywords(sample_keywords)
        for g in groups:
            assert len(g.minus_words) > 0

    def test_empty_input(self):
        assert cluster_keywords([]) == []


class TestAudience:
    def test_returns_all_platforms(self, sample_keywords):
        audience = infer_audience("e-commerce", sample_keywords)
        platforms = {t.platform for t in audience.targeting}
        assert {"yandex", "google", "vk"} == platforms

    def test_summary_not_empty(self, sample_keywords):
        audience = infer_audience("finance", sample_keywords)
        assert len(audience.summary) > 0


class TestCampaigns:
    def test_generates_search_and_display(self, sample_keywords):
        groups = cluster_keywords(sample_keywords)
        audience = infer_audience("e-commerce", sample_keywords)
        campaigns = generate_campaigns(groups, audience, 50_000)
        types = {c.type for c in campaigns}
        assert "search" in types
        assert "display" in types

    def test_ad_variants_count(self, sample_keywords):
        groups = cluster_keywords(sample_keywords)
        audience = infer_audience("e-commerce", sample_keywords)
        campaigns = generate_campaigns(groups, audience, 50_000)
        for c in campaigns:
            assert 5 <= len(c.ad_variants) <= 10

    def test_headline_length(self, sample_keywords):
        groups = cluster_keywords(sample_keywords)
        audience = infer_audience("e-commerce", sample_keywords)
        campaigns = generate_campaigns(groups, audience, 50_000)
        for c in campaigns:
            for v in c.ad_variants:
                assert len(v.headline) <= 30, f"Headline too long: {v.headline!r}"

    def test_description_length(self, sample_keywords):
        groups = cluster_keywords(sample_keywords)
        audience = infer_audience("e-commerce", sample_keywords)
        campaigns = generate_campaigns(groups, audience, 50_000)
        for c in campaigns:
            for v in c.ad_variants:
                assert len(v.description) <= 90


class TestMediaPlan:
    def test_cpa_positive(self, sample_keywords):
        groups = cluster_keywords(sample_keywords)
        audience = infer_audience("e-commerce", sample_keywords)
        campaigns = generate_campaigns(groups, audience, 50_000)
        plan = build_media_plan(campaigns, 50_000)
        assert plan.avg_cpa > 0

    def test_conversions_positive(self, sample_keywords):
        groups = cluster_keywords(sample_keywords)
        audience = infer_audience("e-commerce", sample_keywords)
        campaigns = generate_campaigns(groups, audience, 50_000)
        plan = build_media_plan(campaigns, 50_000)
        assert plan.total_conversions > 0

    def test_budget_matches(self, sample_keywords):
        budget = 100_000.0
        groups = cluster_keywords(sample_keywords)
        audience = infer_audience("e-commerce", sample_keywords)
        campaigns = generate_campaigns(groups, audience, budget)
        plan = build_media_plan(campaigns, budget)
        assert abs(plan.total_budget - budget) < 1.0  # within 1 RUB rounding


# ---------- API endpoint tests ----------


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_analyze_valid_url():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/analyze", json={"url": "https://example.com", "region": "RU"}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "keywords" in data
    assert "campaigns" in data
    assert "media_plan" in data
    assert len(data["keywords"]) > 0
    assert len(data["campaigns"]) > 0


@pytest.mark.asyncio
async def test_analyze_invalid_url():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/analyze", json={"url": "not-a-url", "region": "RU"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_analyze_with_niche_override():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/analyze",
            json={
                "url": "https://example.com",
                "region": "RU",
                "niche": "finance",
                "budget": 30000,
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["site"]["niche"] == "finance"
