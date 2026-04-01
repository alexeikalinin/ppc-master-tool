export interface SiteData {
  title: string;
  description: string;
  niche: string;
  keywords_hint: string[];
}

export interface Keyword {
  text: string;
  frequency: number;
  cpc: number;
  platform: string;
  seasonality: number;
}

export interface SemanticGroup {
  name: string;
  keywords: Keyword[];
  minus_words: string[];
}

export interface PlatformTargeting {
  platform: string;
  age_range: string;
  interests: string[];
  gender: string;
}

export interface AudienceProfile {
  summary: string;
  targeting: PlatformTargeting[];
}

export interface AdVariant {
  headline: string;
  description: string;
  quick_links: string[];
  display_url: string;
}

export interface Campaign {
  name: string;
  type: string;
  platform: string;
  group_name: string;
  budget: number;
  avg_cpc: number;
  ad_variants: AdVariant[];
}

export interface MediaPlanRow {
  campaign_name: string;
  platform: string;
  budget: number;
  avg_cpc: number;
  cr: number;
  cpa: number;
  conversions: number;
}

export interface MediaPlan {
  rows: MediaPlanRow[];
  total_budget: number;
  total_conversions: number;
  avg_cpa: number;
}

export interface AiSummary {
  recommendation: string;
  platforms: string[];
  platform_rationale: Record<string, string>;
  quick_wins: string[];
  confidence: string;
}

// ── New: Niche Insight ──────────────────────────────────────────────────────

export interface CampaignStructureItem {
  name: string;
  keywords_focus: string;
  goal: string;
}

export interface NicheInsight {
  business_description: string;
  primary_audience: string;
  audience_pain_points: string[];
  recommended_campaign_types: string[];
  campaign_type_reasoning: string;
  suggested_campaign_structure: CampaignStructureItem[];
  best_strategies: string[];
  competition_notes: string;
}

// ── New: Budget Recommendation ──────────────────────────────────────────────

export interface BudgetRecommendation {
  currency: string;
  recommended_min: number;
  recommended_optimal: number;
  recommended_aggressive: number;
  reasoning: string;
  monthly_clicks_estimate: number;
  monthly_leads_estimate: number;
}

// ── Full response ───────────────────────────────────────────────────────────

export interface AnalyzeResponse {
  report_id: string | null;
  currency: string;
  site: SiteData;
  competitors: string[];
  keywords: Keyword[];
  groups: SemanticGroup[];
  audience: AudienceProfile;
  campaigns: Campaign[];
  media_plan: MediaPlan;
  ai_summary: AiSummary | null;
  niche_insight: NicheInsight | null;
  budget_recommendation: BudgetRecommendation | null;
}
