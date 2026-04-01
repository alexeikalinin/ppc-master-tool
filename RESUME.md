# Точка продолжения работы

**Обновляйте этот файл в конце каждой сессии.**

---

## Последнее обновление
2026-03-31 — В knowledge-base добавлена сводка по Google Ads (`google-ads-platform-notes.json` + урок-указатель в `lessons.json`).

## Где остановились
- **Tracker модуль завершён:** SQL схема, снятие статистики, bidding robot, A/B эксперименты
- **bid_robot.py** — логика правил: night_reduction, peak_boost, cpa_limit, position_guard; поддержка dry_run
- **Новые API эндпойнты:**
  - `GET/POST /tracker/bot-rules`, `PATCH/DELETE /tracker/bot-rules/{id}`
  - `POST /tracker/bot/run`
  - `GET/POST /tracker/experiments`, `PATCH /tracker/experiments/{id}`
  - `GET /tracker/experiments/{id}/summary`
- **Direct API ошибка 58** — была 06.03; перед боевым запуском проверить снова
- Supabase: **нужно выполнить** `supabase_setup.sql` + `supabase_tracker_setup.sql` в SQL Editor

## Как запустить
```bash
# Бэкенд
cd "PPC Master Tool"
source .venv/bin/activate
uvicorn backend.app:app --reload

# Фронтенд (в отдельном терминале)
cd "PPC Master Tool/frontend"
npm run dev

# Тест робота (dry run)
TRACKER_ACCOUNT_ID=<uuid> DRY_RUN=1 python -m backend.services.bid_robot
```

## Ветка и репозиторий
- Ветка: не инициализирован git (проект без репозитория)

## Приоритеты
- [ ] Выполнить `supabase_setup.sql` + `supabase_tracker_setup.sql` в Supabase SQL Editor
- [ ] Проверить Direct API ошибку 58 (если она ещё есть)
- [ ] Тест робота через API: `POST /tracker/bot/run` с dry_run=true
- [ ] Frontend страница `/tracker` — дашборд кампаний, правила, A/B эксперименты
- [ ] Deploy: Vercel (frontend) + Railway (backend)
