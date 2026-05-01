# Точка продолжения работы

**Обновляйте этот файл в конце каждой сессии.**

---

## Последнее обновление
2026-05-02 — Счётчик токенов AI API (GET /usage + UsageWidget в Workspace); поддержка прямого токена warface-astrum-lab в трекере.

## Где остановились
- **Workspace готов:** `/workspace` — 3 панели, per-agent чат, UsageWidget с авто-обновлением 30с
- **Счётчик токенов:** работает в памяти (сбрасывается при рестарте бэкенда); нужен `.env`: `YANDEX_DIRECT_TOKEN_WARFACE=` для Warface прямого аккаунта
- **Следующий шаг:** добавить ссылку на `/workspace` в навигацию dashboard; подключить Трекер-агента к `/tracker/accounts/{id}/campaigns`
- **Direct API ошибка 58** — перед боевым запуском Warface трекера проверить снова
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
