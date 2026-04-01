# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PPC Master Tool** — a web application that automates PPC campaign setup. Given a website URL and region, it analyzes the site, identifies the niche and competitors, researches keywords, and generates campaign recommendations for Yandex Direct, Google Ads, and VK Ads.

## Stack

- **Frontend**: Next.js (App Router), Tailwind CSS + Shadcn/UI, Framer Motion, Chart.js
- **Backend**: FastAPI (Python 3.11+), uvicorn, `.venv` in project root
- **Database**: Supabase (PostgreSQL via supabase-py) — best-effort, pipeline completes even if DB is unavailable
- **AI summary/chat**: Anthropic, OpenAI, or xAI (Grok) — whichever key is in `.env`; falls back to stub if none

## Commands

```bash
# Backend (from project root)
source .venv/bin/activate
uvicorn backend.app:app --reload

# Run all tests
pytest backend/tests/ -v

# Run a single test
pytest backend/tests/test_analyze.py::TestKeywords::test_stub_returns_keywords -v

# Lint / format
black backend/

# Frontend (from frontend/)
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
npm run build
npm run lint
```

Open http://localhost:3000 → enter a site URL → get the report.

## Architecture

### Backend (`backend/`)

**Entry point**: `backend/app.py` — FastAPI app with CORS, mounts five routers:
- `POST /analyze` → `routers/analyze.py` — full pipeline
- `GET/POST /reports` → `routers/reports.py` — Supabase-backed report CRUD
- `POST /assistant/chat` → `routers/assistant.py` — Q&A over a report (answers only from report data)
- `POST /pdf?variant=1|3` → `routers/pdf.py` — generate PDF proposal (КП) in two design variants
- `POST /export/keywords?fmt=csv|tsv` → `routers/export.py` — keywords by semantic group for Yandex Direct / Excel import

**Analysis pipeline** (called by `/analyze`):
1. `services/parser.py` — BeautifulSoup scrape of target URL → niche, keywords_hint
2. `services/keywords.py` — keyword research (stub mode when no API keys; real mode with YANDEX_WORDSTAT_TOKEN / Google Ads)
3. `services/competitors.py` — SerpAPI competitor discovery (uses keywords for niche-accurate search)
4. `services/clustering.py` — sentence-transformers keyword clustering into groups with minus-words
5. `services/audience.py` — per-platform targeting (Yandex, Google, VK)
6. `services/niche_analysis_ai.py` — AI deep niche analysis → `NicheInsight` + `BudgetRecommendation`; provider chain: Claude → OpenAI → stub; handles currency conversion (RUB/BYN/USD/EUR/KZT)
7. `services/region_platforms.py` — maps region code + city to human-readable label for ad copy
8. `services/campaigns.py` — search + display campaigns, 5–10 ad variants (headline ≤30 chars, description ≤90 chars)
9. `services/media_plan.py` — CR 2–5%, CPA = CPC/CR, conversions = budget/CPA; converts all amounts to selected currency
10. `services/ai_summary.py` — LLM summary of the full report
11. `services/pdf_export.py` — reportlab PDF generation (two variants: Dark Premium, Split Layout; Arial Unicode for Cyrillic)

**Assistant chat**: `services/assistant_chat.py` — `chat_with_report(report_json, question)` answers questions strictly from report data; uses the same AI provider as `ai_summary.py` via `_get_provider()`.

**Integrations**: `backend/integrations/` — `google_ads.py`, `serpapi.py`, `trends.py`, `wordstat.py`, `direct_forecast.py`, `direct_stats.py`

**Models**: `backend/models.py` — all Pydantic request/response models. Key types: `AnalyzeRequest`, `AnalyzeResponse`, `Keyword`, `SemanticGroup`, `Campaign`, `MediaPlan`, `NicheInsight`, `BudgetRecommendation`, `AiSummary`.

**Database**: `backend/db.py` — Supabase client. Run `supabase_setup.sql` once in Supabase. Report save in `/analyze` is wrapped in try/except — a DB failure does not block the response.

**Config**: `backend/config.py` — `pydantic_settings` `Settings` class; reads from `.env` file automatically.

**Scripts**: `scripts/get_yandex_token.py` — OAuth flow for Yandex tokens; `scripts/run_supabase_setup.py` — runs `supabase_setup.sql` programmatically.

**Tests**: `pytest.ini` sets `asyncio_mode = auto` and `testpaths = backend/tests`. All 24 tests run in stub mode (no API keys required).

### Frontend (`frontend/`)

Next.js App Router, dark glassmorphism theme (indigo palette). API types mirrored in `frontend/types/api.ts`. API calls in `frontend/lib/api.ts`.

- `app/page.tsx` — landing/home
- `app/dashboard/page.tsx` — input form (URL, region, optional niche/budget/city/currency)
- `app/results/page.tsx` — report display: NicheInsightBlock, BudgetRecommendationBlock, keywords, campaigns, media plan, AssistantChatBlock, PDF download buttons
- `app/reports/page.tsx` — list of saved reports from Supabase

## Environment Variables

```
# Supabase (optional — pipeline runs without it)
SUPABASE_URL
SUPABASE_KEY
SUPABASE_SERVICE_ROLE_KEY

# AI summary + chat (set at least one; ai_provider auto-selects first available)
ANTHROPIC_API_KEY
OPENAI_API_KEY
XAI_API_KEY
AI_PROVIDER              # explicit override: anthropic | openai | xai

# Yandex (optional, falls back to stub mode)
YANDEX_WORDSTAT_TOKEN    # OAuth access_token for Wordstat API
YANDEX_DIRECT_TOKEN      # OAuth token with scope direct:api (falls back to WORDSTAT_TOKEN)
YANDEX_CLIENT_ID
YANDEX_CLIENT_SECRET
YANDEX_REFRESH_TOKEN

# SerpAPI — enables real competitor search
SERPAPI_KEY

# Google Ads (all must be set to enable GKP integration)
GOOGLE_ADS_CLIENT_ID
GOOGLE_ADS_CLIENT_SECRET
GOOGLE_ADS_DEVELOPER_TOKEN
GOOGLE_ADS_REFRESH_TOKEN
GOOGLE_ADS_CUSTOMER_ID
```

Frontend: `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`.

## Key Design Decisions

- Keywords service runs in **stub mode** when no API keys are present; all 24 tests rely on stub mode
- **Currency**: user selects RUB/BYN/USD/EUR/KZT; budget input and all media plan outputs are in the selected currency; internal campaign calculations use RUB (converted via `to_rub()` in `niche_analysis_ai.py`)
- `POST /assistant/chat` accepts the full report JSON and answers **only from report data** — no hallucination
- Supabase Auth is planned for Phase 3; auth dependency in `routers/analyze.py` is a placeholder comment
- `# TODO: AdCreative.ai integration` comments are intentional placeholders
- Deploy: Vercel (frontend) + Railway (backend); `vercel.json` in repo root

## Skills System (Self-Learning)

The skills system lives in `.claude/skills/`. It accumulates lessons, user preferences, and task patterns across sessions.

### Before any complex task

1. Read `.claude/skills/knowledge-base/assets/preferences.json` for user preferences
2. Read `.claude/skills/knowledge-base/assets/lessons.json` and filter by task category for past lessons
3. Apply relevant lessons to avoid repeating mistakes

### After receiving user feedback

When the user gives feedback (corrections, "not what I wanted", "perfect", preferences like "always do X"):

1. Follow `.claude/skills/quality-loop/SKILL.md`
2. Append a structured lesson to `knowledge-base/assets/lessons.json`
3. Update `preferences.json` if the user expressed a persistent preference
4. Briefly confirm: "Noted, I'll apply this going forward"

### For complex multi-step tasks

Follow `.claude/skills/meta-orchestrator/SKILL.md`:
- Use the Planner approach to structure work
- Use the Reviewer approach to self-check results

### After completing code changes

Follow `.claude/skills/change-logger/SKILL.md`:
- Write an entry to DEVELOPMENT_LOG.md (prepend at top)
- Update RESUME.md current state and last-updated fields

### Skill creation

If the same type of task repeats 3+ times, suggest creating a skill via `.claude/skills/skill-factory/SKILL.md`.

## Sync Protocol (Cursor ↔ Claude Code)

### Session Start — MANDATORY
1. Read **`RESUME.md`** — current state, last changes, priorities
2. Read last 2-3 entries in **`DEVELOPMENT_LOG.md`** — recent changes
3. Do NOT ask user to "initialize project". Confirm state in 1-2 sentences, then wait for task.

### Session End — MANDATORY
1. Update **`RESUME.md`**: today's date + what was done, current state + next steps
2. Append entry to **`DEVELOPMENT_LOG.md`** (prepend at top): date, what changed, files, status

### Shared Files

| File | Purpose | When to update |
|------|---------|----------------|
| **RESUME.md** | Where we left off, priorities | Start + end of session |
| **DEVELOPMENT_LOG.md** | Full change history | After every code change |
