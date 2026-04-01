-- Run this in Supabase SQL Editor after creating a new project
-- Safe to re-run: uses IF NOT EXISTS / DROP IF EXISTS

create table if not exists reports (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users(id) on delete cascade,
  url         text not null,
  region      text not null default 'RU',
  json_data   jsonb not null,
  created_at  timestamptz not null default now()
);

alter table reports enable row level security;

drop policy if exists "Users can view own reports" on reports;
create policy "Users can view own reports"
  on reports for select
  using (auth.uid() = user_id);

drop policy if exists "Users can insert own reports" on reports;
create policy "Users can insert own reports"
  on reports for insert
  with check (auth.uid() = user_id);

drop policy if exists "Users can delete own reports" on reports;
create policy "Users can delete own reports"
  on reports for delete
  using (auth.uid() = user_id);

create index if not exists reports_user_id_idx on reports (user_id);
create index if not exists reports_created_at_idx on reports (created_at desc);
