from pydantic import BaseModel, HttpUrl

# ---------- Request ----------

SUPPORTED_CURRENCIES = {"RUB", "BYN", "USD", "EUR", "KZT"}


class AnalyzeRequest(BaseModel):
    url: str
    region: str = "BY"
    city: str | None = None
    niche: str | None = None
    budget: float | None = None
    currency: str = "RUB"   # RUB | BYN | USD | EUR | KZT
    ga_ym_metrics: dict | None = None


# ---------- Site ----------


class SiteData(BaseModel):
    title: str
    description: str
    niche: str
    keywords_hint: list[str]


# ---------- Keywords ----------


class Keyword(BaseModel):
    text: str
    frequency: int
    cpc: float  # cost-per-click in RUB
    platform: str  # yandex | google | trends
    seasonality: float = 1.0  # multiplier (1.0 = no seasonality)


# ---------- Semantic groups ----------


class SemanticGroup(BaseModel):
    name: str
    keywords: list[Keyword]
    minus_words: list[str]


# ---------- Audience ----------


class PlatformTargeting(BaseModel):
    platform: str
    age_range: str
    interests: list[str]
    gender: str = "all"


class AudienceProfile(BaseModel):
    summary: str
    targeting: list[PlatformTargeting]


# ---------- Campaigns ----------


class AdVariant(BaseModel):
    headline: str  # max 30 chars
    description: str  # max 90 chars
    quick_links: list[str]
    display_url: str


class Campaign(BaseModel):
    name: str
    type: str  # search | display
    platform: str  # yandex | google | vk
    group_name: str
    budget: float
    avg_cpc: float
    ad_variants: list[AdVariant]


# ---------- Media plan ----------


class MediaPlanRow(BaseModel):
    campaign_name: str
    platform: str
    budget: float
    avg_cpc: float
    cr: float
    cpa: float
    conversions: float


class MediaPlan(BaseModel):
    rows: list[MediaPlanRow]
    total_budget: float
    total_conversions: float
    avg_cpa: float


# ---------- Niche Analysis ----------


class NicheAnalysis(BaseModel):
    niche: str
    business_type: str          # B2C / B2B / hybrid
    product: str                # основной продукт/услуга
    price_segment: str          # economy / mid / premium / unknown
    geo_focus: str              # город или регион
    seasonality: str            # "Пик: март–май, спад: июль–август"
    competition_level: str      # high / medium / low
    summary: str                # краткое описание ниши


# ---------- Platform Recommendation ----------


class CampaignTypeRec(BaseModel):
    type: str           # search / rsa / retargeting / smart / etc.
    name: str           # "Поисковые кампании"
    why: str            # обоснование
    priority: str       # high / medium / low
    budget_pct: float   # доля бюджета


class PlatformRec(BaseModel):
    platform: str
    why: str
    budget_pct: float
    campaign_types: list[CampaignTypeRec]


class PlatformRecommendation(BaseModel):
    region_note: str            # объяснение почему именно эти платформы
    primary_platform: str
    platforms: list[PlatformRec]


# ---------- Niche Insight (AI deep analysis) ----------


class CampaignStructureItem(BaseModel):
    name: str           # «Создание сайтов»
    keywords_focus: str # ключевые темы для этой кампании
    goal: str           # цель кампании


class NicheInsight(BaseModel):
    business_description: str       # что делает бизнес (1-2 предл.)
    primary_audience: str           # кто основная аудитория
    audience_pain_points: list[str] # боли/потребности аудитории (3-5 шт.)
    recommended_campaign_types: list[str]   # search / display / retargeting / smart
    campaign_type_reasoning: str    # почему именно эти типы
    suggested_campaign_structure: list[CampaignStructureItem]  # 2-4 кампании
    best_strategies: list[str]      # топ-3 стратегии для ниши
    competition_notes: str          # комментарий по конкуренции в нише


# ---------- Budget Recommendation ----------


class BudgetRecommendation(BaseModel):
    currency: str
    recommended_min: float      # минимальный тестовый бюджет
    recommended_optimal: float  # оптимальный бюджет
    recommended_aggressive: float  # агрессивный бюджет
    reasoning: str              # обоснование рекомендации
    monthly_clicks_estimate: int  # прогноз кликов при оптимальном бюджете
    monthly_leads_estimate: int   # прогноз лидов


# ---------- AI Summary ----------


class AiSummary(BaseModel):
    recommendation: str
    platforms: list[str]
    platform_rationale: dict[str, str]
    quick_wins: list[str]
    confidence: str = "medium"  # high | medium | low


# ---------- Full response ----------


class AnalyzeResponse(BaseModel):
    report_id: str | None = None
    currency: str = "RUB"
    site: SiteData
    competitors: list[str]
    keywords: list[Keyword]
    groups: list[SemanticGroup]
    audience: AudienceProfile
    campaigns: list[Campaign]
    media_plan: MediaPlan
    ai_summary: AiSummary | None = None
    niche_analysis: NicheAnalysis | None = None
    platform_recommendation: PlatformRecommendation | None = None
    niche_insight: NicheInsight | None = None
    budget_recommendation: BudgetRecommendation | None = None


# ---------- Report list ----------


class ReportOut(BaseModel):
    id: str
    url: str
    region: str
    created_at: str
    title: str | None = None
