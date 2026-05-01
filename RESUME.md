# Точка продолжения работы

**Обновляйте этот файл в конце каждой сессии.**

---

## Последнее обновление
2026-05-01 — Создан 3-панельный Workspace (`/workspace`) с чатом и 5 агентами (Анализатор, Медиапланировщик, Трекер, КП-генератор, PPC-консультант).

## Где остановились
- **Workspace готов:** `/workspace` — 3 панели, per-agent история чата, маршрутизация по API, контекст отчёта в правой панели
- **Следующий шаг:** добавить ссылку на `/workspace` в навигацию dashboard и results; подключить Трекер-агента к реальному API `/tracker/campaigns`
- **Секреты:** только в `.env` (не в репозитории)
- **Tracker модуль завершён на бэкенде:** SQL схема, снятие статистики, bidding robot, A/B эксперименты
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
- Ветка: `main`
- Remote: `https://github.com/alexeikalinin/ppc-master-tool.git`

## Приоритеты
- [ ] Выполнить `supabase_setup.sql` + `supabase_tracker_setup.sql` в Supabase SQL Editor
- [ ] Проверить Direct API ошибку 58 (если она ещё есть)
- [ ] Тест робота через API: `POST /tracker/bot/run` с dry_run=true
- [ ] Frontend страница `/tracker` — дашборд кампаний, правила, A/B эксперименты
- [ ] Deploy: Vercel (frontend) + Railway (backend)
