-- PPC Tracker: Campaign Performance + Bidding Robot + A/B Experiments
-- Run in Supabase SQL Editor AFTER supabase_setup.sql
-- Safe to re-run

-- ─────────────────────────────────────────────
-- 1. Аккаунты Яндекс Директ
-- ─────────────────────────────────────────────
create table if not exists direct_accounts (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users(id) on delete cascade,
  login       text not null,              -- alexeikalinin1
  label       text,                       -- "Мой аккаунт" / "Клиент X"
  token_hint  text,                       -- первые 12 символов токена (не хранить полный!)
  is_active   boolean not null default true,
  created_at  timestamptz not null default now()
);

-- ─────────────────────────────────────────────
-- 2. Ежедневная статистика по кампаниям
-- ─────────────────────────────────────────────
create table if not exists campaign_daily_stats (
  id              uuid primary key default gen_random_uuid(),
  account_id      uuid references direct_accounts(id) on delete cascade,
  stat_date       date not null,
  campaign_id     bigint not null,
  campaign_name   text not null,
  campaign_type   text,                   -- TEXT_CAMPAIGN, SMART_CAMPAIGN и т.д.
  impressions     integer not null default 0,
  clicks          integer not null default 0,
  cost_rub        numeric(12,2) not null default 0,
  conversions     integer not null default 0,
  ctr             numeric(6,4),           -- %
  avg_cpc         numeric(10,2),          -- руб
  cpa             numeric(10,2),          -- руб
  created_at      timestamptz not null default now(),
  unique (account_id, stat_date, campaign_id)
);

create index if not exists cds_account_date_idx on campaign_daily_stats (account_id, stat_date desc);
create index if not exists cds_campaign_idx on campaign_daily_stats (campaign_id, stat_date desc);

-- ─────────────────────────────────────────────
-- 3. Ежедневная статистика по ключевым словам
-- ─────────────────────────────────────────────
create table if not exists keyword_daily_stats (
  id              uuid primary key default gen_random_uuid(),
  account_id      uuid references direct_accounts(id) on delete cascade,
  stat_date       date not null,
  campaign_id     bigint not null,
  keyword_id      bigint not null,
  keyword_text    text not null,
  impressions     integer not null default 0,
  clicks          integer not null default 0,
  cost_rub        numeric(12,2) not null default 0,
  conversions     integer not null default 0,
  avg_cpc         numeric(10,2),
  current_bid     numeric(10,2),          -- ставка на момент снятия статистики
  created_at      timestamptz not null default now(),
  unique (account_id, stat_date, keyword_id)
);

create index if not exists kds_account_date_idx on keyword_daily_stats (account_id, stat_date desc);
create index if not exists kds_keyword_idx on keyword_daily_stats (keyword_id, stat_date desc);

-- ─────────────────────────────────────────────
-- 4. Лог всех изменений ставок (бот + ручные)
-- ─────────────────────────────────────────────
create table if not exists bid_changes (
  id              uuid primary key default gen_random_uuid(),
  account_id      uuid references direct_accounts(id) on delete cascade,
  changed_at      timestamptz not null default now(),
  source          text not null check (source in ('bot', 'manual', 'import')),
  campaign_id     bigint not null,
  campaign_name   text,
  keyword_id      bigint,
  keyword_text    text,
  bid_before      numeric(10,2),
  bid_after       numeric(10,2),
  reason          text,                   -- "позиция упала с 2 на 5", "CPA > 500₽", "ночной режим"
  rule_triggered  text,                   -- "position_guard", "cpa_limit", "night_reduction"
  experiment_id   uuid,                   -- ссылка на эксперимент если есть
  note            text                    -- ручной комментарий
);

create index if not exists bc_account_idx on bid_changes (account_id, changed_at desc);
create index if not exists bc_keyword_idx on bid_changes (keyword_id, changed_at desc);
create index if not exists bc_experiment_idx on bid_changes (experiment_id);

-- ─────────────────────────────────────────────
-- 5. A/B Эксперименты
-- ─────────────────────────────────────────────
create table if not exists experiments (
  id              uuid primary key default gen_random_uuid(),
  account_id      uuid references direct_accounts(id) on delete cascade,
  name            text not null,          -- "Робот vs Ручное управление Q2 2026"
  description     text,
  campaign_a_id   bigint not null,        -- кампания A (ручное управление)
  campaign_b_id   bigint not null,        -- кампания B (робот)
  campaign_a_label text default 'Ручное',
  campaign_b_label text default 'Робот',
  started_at      date not null,
  ended_at        date,                   -- null = активен
  status          text not null default 'active' check (status in ('active', 'paused', 'completed')),
  conclusion      text,                   -- вывод по итогу эксперимента
  created_at      timestamptz not null default now()
);

-- ─────────────────────────────────────────────
-- 6. Настройки биддинг-робота
-- ─────────────────────────────────────────────
create table if not exists bot_rules (
  id              uuid primary key default gen_random_uuid(),
  account_id      uuid references direct_accounts(id) on delete cascade,
  campaign_id     bigint,                 -- null = правило для всего аккаунта
  rule_name       text not null,          -- "night_reduction", "cpa_limit", "position_guard"
  is_active       boolean not null default true,
  params          jsonb not null default '{}',
  -- Примеры params:
  -- night_reduction:   {"from_hour": 2, "to_hour": 8, "reduction_pct": 40}
  -- cpa_limit:         {"max_cpa_rub": 500, "min_clicks": 30, "action": "reduce_50pct"}
  -- position_guard:    {"target_position": 2, "max_bid_rub": 150}
  -- peak_boost:        {"hours": [19,20,21,22,23], "boost_pct": 20}
  created_at      timestamptz not null default now()
);

-- ─────────────────────────────────────────────
-- 7. Агрегированные данные (для архивации)
-- Заполняется скриптом авто-агрегации раз в неделю
-- ─────────────────────────────────────────────
create table if not exists campaign_weekly_stats (
  id              uuid primary key default gen_random_uuid(),
  account_id      uuid references direct_accounts(id) on delete cascade,
  week_start      date not null,          -- понедельник недели
  campaign_id     bigint not null,
  impressions     integer,
  clicks          integer,
  cost_rub        numeric(12,2),
  conversions     integer,
  avg_ctr         numeric(6,4),
  avg_cpc         numeric(10,2),
  avg_cpa         numeric(10,2),
  bid_changes_count integer default 0,   -- сколько раз менялись ставки за неделю
  unique (account_id, week_start, campaign_id)
);

-- ─────────────────────────────────────────────
-- RLS — доступ только к своим данным
-- ─────────────────────────────────────────────
alter table direct_accounts enable row level security;
alter table campaign_daily_stats enable row level security;
alter table keyword_daily_stats enable row level security;
alter table bid_changes enable row level security;
alter table experiments enable row level security;
alter table bot_rules enable row level security;
alter table campaign_weekly_stats enable row level security;

-- direct_accounts
drop policy if exists "Own accounts" on direct_accounts;
create policy "Own accounts" on direct_accounts
  for all using (auth.uid() = user_id);

-- campaign_daily_stats (через account_id → user_id)
drop policy if exists "Own campaign stats" on campaign_daily_stats;
create policy "Own campaign stats" on campaign_daily_stats
  for all using (
    account_id in (select id from direct_accounts where user_id = auth.uid())
  );

-- keyword_daily_stats
drop policy if exists "Own keyword stats" on keyword_daily_stats;
create policy "Own keyword stats" on keyword_daily_stats
  for all using (
    account_id in (select id from direct_accounts where user_id = auth.uid())
  );

-- bid_changes
drop policy if exists "Own bid changes" on bid_changes;
create policy "Own bid changes" on bid_changes
  for all using (
    account_id in (select id from direct_accounts where user_id = auth.uid())
  );

-- experiments
drop policy if exists "Own experiments" on experiments;
create policy "Own experiments" on experiments
  for all using (
    account_id in (select id from direct_accounts where user_id = auth.uid())
  );

-- bot_rules
drop policy if exists "Own bot rules" on bot_rules;
create policy "Own bot rules" on bot_rules
  for all using (
    account_id in (select id from direct_accounts where user_id = auth.uid())
  );

-- campaign_weekly_stats
drop policy if exists "Own weekly stats" on campaign_weekly_stats;
create policy "Own weekly stats" on campaign_weekly_stats
  for all using (
    account_id in (select id from direct_accounts where user_id = auth.uid())
  );
