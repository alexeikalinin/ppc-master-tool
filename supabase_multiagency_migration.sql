-- Миграция: поддержка нескольких агентств и клиентов
-- Запустить в Supabase SQL Editor ПОСЛЕ supabase_tracker_setup.sql
-- Safe to re-run

-- ─────────────────────────────────────────────
-- 1. Агентства (верхний уровень)
-- ─────────────────────────────────────────────
create table if not exists agencies (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid references auth.users(id) on delete cascade,
  login         text not null unique,   -- starmedia-agency
  label         text not null,          -- "StarMedia Agency" / "Личный аккаунт"
  token_env_key text not null,          -- имя ключа в .env: YANDEX_DIRECT_TOKEN_STARMEDIA
  is_active     boolean not null default true,
  created_at    timestamptz not null default now()
);

-- ─────────────────────────────────────────────
-- 2. Обновить direct_accounts: добавить поля
-- ─────────────────────────────────────────────

-- Привязка к агентству
alter table direct_accounts
  add column if not exists agency_id uuid references agencies(id) on delete set null;

-- Валюта клиента (RUB / BYN / USD / EUR / KZT)
alter table direct_accounts
  add column if not exists currency text not null default 'RUB';

-- Сайт клиента
alter table direct_accounts
  add column if not exists website text;

-- Гео (для быстрого контекста)
alter table direct_accounts
  add column if not exists geo text;    -- "Минск", "Москва", "Казахстан"

-- Ниша
alter table direct_accounts
  add column if not exists niche text;  -- "Медицина", "Стройматериалы"

-- Метрика счётчик
alter table direct_accounts
  add column if not exists metrika_counter bigint;

-- ─────────────────────────────────────────────
-- 3. Обновить campaign_daily_stats: валюта
-- ─────────────────────────────────────────────
-- cost_rub → cost (фактическая валюта хранится в direct_accounts.currency)
alter table campaign_daily_stats
  rename column cost_rub to cost;

alter table keyword_daily_stats
  rename column cost_rub to cost;

alter table campaign_weekly_stats
  rename column cost_rub to cost;

-- ─────────────────────────────────────────────
-- 4. Лог изменений Claude (AI-действия)
-- ─────────────────────────────────────────────
create table if not exists ai_actions (
  id            uuid primary key default gen_random_uuid(),
  account_id    uuid references direct_accounts(id) on delete cascade,
  performed_at  timestamptz not null default now(),
  action_type   text not null,  -- 'campaign_created', 'keyword_added', 'bid_changed', 'campaign_paused'
  entity_type   text,           -- 'campaign', 'adgroup', 'keyword', 'ad'
  entity_id     bigint,
  entity_name   text,
  payload       jsonb,          -- детали действия
  note          text,           -- объяснение почему
  reverted      boolean not null default false
);

create index if not exists ai_actions_account_idx on ai_actions (account_id, performed_at desc);

-- ─────────────────────────────────────────────
-- 5. Вставить текущих клиентов
-- ─────────────────────────────────────────────

-- Агентство StarMedia (вставляем без user_id пока нет Auth)
insert into agencies (login, label, token_env_key, is_active)
values ('starmedia-agency', 'StarMedia Agency', 'YANDEX_DIRECT_TOKEN', true)
on conflict (login) do nothing;

-- ─────────────────────────────────────────────
-- 6. Полезные вьюхи для быстрых запросов
-- ─────────────────────────────────────────────

-- Актуальная статистика за последние 30 дней по аккаунтам
create or replace view v_account_summary_30d as
select
  da.login,
  da.label,
  da.currency,
  da.geo,
  da.niche,
  sum(cds.clicks)       as clicks_30d,
  sum(cds.cost)         as cost_30d,
  sum(cds.conversions)  as conversions_30d,
  round(sum(cds.cost) / nullif(sum(cds.conversions), 0), 2) as avg_cpa,
  round(avg(cds.ctr), 2) as avg_ctr,
  count(distinct cds.campaign_id) as active_campaigns
from direct_accounts da
left join campaign_daily_stats cds
  on cds.account_id = da.id
  and cds.stat_date >= current_date - 30
where da.is_active = true
group by da.id, da.login, da.label, da.currency, da.geo, da.niche;

-- Топ кампаний по CPA за 30 дней
create or replace view v_campaign_cpa_30d as
select
  da.login    as account_login,
  da.label    as account_label,
  da.currency,
  cds.campaign_id,
  cds.campaign_name,
  sum(cds.clicks)       as clicks,
  sum(cds.cost)         as cost,
  sum(cds.conversions)  as conversions,
  round(sum(cds.cost) / nullif(sum(cds.conversions), 0), 2) as cpa,
  round(avg(cds.ctr), 2) as avg_ctr
from campaign_daily_stats cds
join direct_accounts da on da.id = cds.account_id
where cds.stat_date >= current_date - 30
group by da.id, da.login, da.label, da.currency, cds.campaign_id, cds.campaign_name
order by cpa asc nulls last;

-- ─────────────────────────────────────────────
-- 7. RLS для новых таблиц
-- ─────────────────────────────────────────────
alter table agencies enable row level security;
alter table ai_actions enable row level security;

drop policy if exists "Own agencies" on agencies;
create policy "Own agencies" on agencies
  for all using (auth.uid() = user_id);

drop policy if exists "Own ai actions" on ai_actions;
create policy "Own ai actions" on ai_actions
  for all using (
    account_id in (select id from direct_accounts where user_id = auth.uid())
  );
