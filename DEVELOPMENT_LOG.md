# Лог разработки

**Все изменения в проекте документируются здесь.**

---

## 2026-05-02 — Счётчик токенов AI API + Direct per-account токены

**Задача:** Добавить мониторинг расхода токенов по API-ключам (чтобы видеть что близко к лимиту); поддержать прямой токен Warface в трекере.

**Что сделано:**
- `backend/services/token_counter.py` (новый) — in-memory singleton: записывает input/output токены и считает стоимость в USD по ценам каждой модели; метод `snapshot()` для API; `reset()` для сброса
- `backend/routers/usage.py` (новый) — `GET /usage` возвращает статус ключей + per-provider/model breakdown + общую стоимость; `POST /usage/reset` сбрасывает счётчик
- `backend/services/ai_summary.py` — `counter.record()` после каждого вызова Claude/OpenAI/Grok
- `backend/services/niche_analysis_ai.py` — то же для `_call_claude` и `_call_openai`
- `backend/services/assistant_chat.py` — то же для всех трёх провайдеров
- `backend/app.py` — подключён `usage.router`; добавлен `localhost:3001` в CORS
- `frontend/lib/api.ts` — добавлены `api.getUsage()` и `api.resetUsage()`
- `frontend/components/workspace/UsageWidget.tsx` (новый) — виджет: статус ключей (✓/✗), токены + стоимость по провайдерам, раскрываемая разбивка по моделям, авто-обновление 30с, кнопка сброса
- `frontend/components/workspace/RightPanel.tsx` — добавлена секция "API / Токены" с UsageWidget
- `backend/config.py` — добавлены `yandex_direct_token_warface`, `yandex_refresh_token_warface`
- `backend/services/tracker.py` — `_get_token(login)` теперь резолвит прямой токен для warface-astrum-lab; `Client-Login` не передаётся для прямых аккаунтов
- `backend/routers/tracker.py` — новый `GET /tracker/accounts/{id}/campaigns` — живой список кампаний из Direct API без снапшота

**Файлы изменены:** 11 файлов (3 новых)

**Статус:** ✅ Завершено — запушено 2 коммита

---

## 2026-05-01 — Workspace: 3-панельный интерфейс с агентами

**Задача:** Создать главный workspace — 3-панельный интерфейс (левая панель + чат + правый контекст) для работы со всеми агентами PPC Master Tool.

**Что сделано:**
- `frontend/lib/agents.ts` (новый) — конфигурация 5 агентов (Анализатор, Медиапланировщик, Трекер, КП-генератор, PPC-консультант) и список клиентов (Astrum, Starmedia)
- `frontend/components/workspace/LeftPanel.tsx` (новый) — левая панель: лого, навигация, список агентов с активным индикатором, клиенты, настройки
- `frontend/components/workspace/ChatPanel.tsx` (новый) — центральный чат: хедер агента, история сообщений с анимацией, typing-индикатор, быстрые действия, auto-resize input (Enter=отправить, Shift+Enter=новая строка); маршрутизация по API на основе выбранного агента
- `frontend/components/workspace/RightPanel.tsx` (новый) — правая панель: контекст текущего отчёта (ниша/ключи/конкуренты/регион) с кнопкой очистки, быстрые ссылки, статистика сессии, история запросов
- `frontend/app/workspace/page.tsx` (новый) — страница `/workspace`: state-машина (activeAgent, activeClient, agentMessages per-agent, currentReport), компоновка 3 панелей в h-screen

**Логика агентов в ChatPanel:**
- Анализатор → `POST /analyze` (парсит URL + регион из сообщения, сохраняет отчёт в state)
- Медиапланировщик + PPC-консультант → `POST /assistant/chat` (требует активного отчёта)
- КП-генератор → `api.downloadKp(report, variant)` (скачивает PDF по variant 1 или 3)
- Трекер → заглушка с навигацией на `/tracker`

**Файлы изменены:** `frontend/lib/agents.ts` (новый), `frontend/components/workspace/LeftPanel.tsx` (новый), `frontend/components/workspace/ChatPanel.tsx` (новый), `frontend/components/workspace/RightPanel.tsx` (новый), `frontend/app/workspace/page.tsx` (новый)

**Статус:** ✅ Завершено — TypeScript clean, `/workspace` возвращает 200

---

## 2026-04-12 — Warface: семантическое ядро для Яндекс Директ

**Задача:** Собрать полное семантическое ядро запросов по шутерам для рекламы Warface (Astrum Entertainment); создать структуру папок с ключевыми фразами и минус-словами; обновить базу знаний.

**Что сделано:**
- `Astrum/Warface/README.md` (новый) — обзор, структура кампаний, UTM-метки, следующие шаги
- `Astrum/Warface/keywords/01_brand_main.txt` (новый) — брендовые варианты написания (9 фраз)
- `Astrum/Warface/keywords/02_brand_download.txt` (новый) — бренд + скачать/установить (14 фраз)
- `Astrum/Warface/keywords/03_brand_site_reg.txt` (новый) — бренд + сайт/регистрация/вход (13 фраз)
- `Astrum/Warface/keywords/04_brand_ingame.txt` (новый) — варбаксы, промокод, классы (27 фраз)
- `Astrum/Warface/keywords/05_category_f2p_shooter.txt` (новый) — бесплатный шутер (15 фраз)
- `Astrum/Warface/keywords/06_category_online_fps.txt` (новый) — онлайн шутер/fps (19 фраз)
- `Astrum/Warface/keywords/07_category_download_shooter.txt` (новый) — скачать шутер (8 фраз)
- `Astrum/Warface/keywords/08_category_military.txt` (новый) — военные игры (9 фраз)
- `Astrum/Warface/keywords/09_competitor_cs2.txt` (новый) — CS:GO/CS2 конкурентные (13 фраз)
- `Astrum/Warface/keywords/10_competitor_crossfire_pb.txt` (новый) — Crossfire + Point Blank (13 фраз)
- `Astrum/Warface/keywords/11_competitor_cod_battlefield.txt` (новый) — CoD + Battlefield (10 фраз)
- `Astrum/Warface/keywords/12_competitor_tarkov_survarium.txt` (новый) — Тарков/Survarium/CRSED (8 фраз)
- `Astrum/Warface/keywords/13_multiplayer_coop.txt` (новый) — мультиплеер/командные (11 фраз)
- `Astrum/Warface/keywords/14_battle_royale.txt` (новый) — Battle Royale (9 фраз)
- `Astrum/Warface/keywords/15_arena_pvp_shooters.txt` (новый) — арена/PvP (8 фраз)
- `Astrum/Warface/keywords/16_transact_donate.txt` (новый) — донат/варбаксы (12 фраз)
- `Astrum/Warface/minus_words/global_minus.txt` (новый) — ~70 минус-слов по 10 блокам
- `Astrum/Warface/minus_words/notes.md` (новый) — приоритет, пересечения кампаний
- `.claude/skills/knowledge-base/assets/warface-analysis.json` — добавлен блок `semantic_core` с метаданными всех групп, бенчмарками, следующими шагами

**Итого ключевых фраз:** ~145 (16 групп), ~70 минус-слов

**Файлы изменены:** `Astrum/Warface/` (19 новых файлов), `warface-analysis.json`

**Статус:** ✅ Завершено

---

## 2026-04-02 — Безопасность: убраны секреты из `.claude/settings.local.json`

**Задача:** Устранить утечку токенов и OAuth-данных из локального конфига Claude Code; зафиксировать, что секреты только в `.env`.

**Что сделано:**
- `.claude/settings.local.json` — перезаписан без встроенных Bash-команд с `y0__*`, refresh_token, OpenAI `sk-*`, client_secret и одноразовых OAuth `code`; оставлены только безопасные allow-правила (pytest, black, npm build, uvicorn).
- `.gitignore` — добавлено игнорирование `.claude/settings.local.json`, чтобы файл с историей разрешений не попадал в репозиторий.
- `.claude/settings.local.json.example` (новый) — шаблон без секретов с комментарием использовать `.env`.

**Файлы изменены:** `.claude/settings.local.json`, `.gitignore`, `.claude/settings.local.json.example` (новый)

**Статус:** ✅ Завершено (если старый JSON с секретами уже пушили на GitHub — нужна ротация ключей и при необходимости очистка истории git)

---

## 2026-03-31 — База знаний: сводка Google Ads (анонсы Help Center)

**Задача:** Зафиксировать в knowledge-base практичные выжимки по Google Ads (цели и конверсии, аудитории, скрипты, API) с привязкой к PPC Master Tool.

**Что сделано:**
- `.claude/skills/knowledge-base/assets/google-ads-platform-notes.json` (новый) — структурированная справка: отслеживание целей, enhanced conversions/OCI, Customer Match и first-party, скрипты, Google Ads API/OAuth, недавние продуктовые изменения (лентa анонсов), `project_alignment` с `backend/integrations/google_ads.py` и env.
- `.claude/skills/knowledge-base/assets/lessons.json` — запись `lesson-2026-03-31-google-ads-001` (тип reference) со ссылкой на JSON-актив.

**Источник индекса новостей:** [Google Ads announcements](https://support.google.com/google-ads/announcements/9048695).

**Статус:** ✅ Готово для чтения агентами при задачах по Google Ads.

---

## 2026-03-27 — Bidding Robot + Bot Rules + A/B Experiments API

**Задача:** Продолжить разработку трекера — добавить биддинг-робота, управление правилами, A/B эксперименты.

**Что сделано:**
- `backend/services/bid_robot.py` (новый) — полная логика биддинг-робота:
  - Поддержка 4 типов правил: `night_reduction`, `peak_boost`, `cpa_limit`, `position_guard`
  - Агрегация статистики ключей за N дней, применение множителей
  - Применение ставок через Яндекс Direct API (`/bids` метод `set`)
  - Запись всех изменений в таблицу `bid_changes`
  - Режим `dry_run=True` — считает без применения (для тестирования)
  - CLI: `TRACKER_ACCOUNT_ID=<uuid> DRY_RUN=1 python -m backend.services.bid_robot`
- `backend/routers/tracker.py` — добавлены эндпойнты:
  - `GET/POST /tracker/bot-rules` — список и создание правил
  - `PATCH/DELETE /tracker/bot-rules/{id}` — обновление и удаление
  - `POST /tracker/bot/run` — запуск робота (поддерживает dry_run, experiment_id)
  - `GET/POST /tracker/experiments` — список и создание A/B экспериментов
  - `PATCH /tracker/experiments/{id}` — завершение/пауза с выводом
  - `GET /tracker/experiments/{id}/summary` — сравнение кампаний A vs B

**Файлы изменены:** `backend/services/bid_robot.py` (новый), `backend/routers/tracker.py`

**Статус:** ✅ Backend tracker модуль завершён. Ожидает: выполнение SQL миграций в Supabase, проверка Direct API, frontend страница `/tracker`.

---

## 2026-03-06 — Диагностика Direct API, база знаний API-ошибок, CLAUDE.md обновлён, Playwright установлен

**Задача:** Проверить работоспособность Яндекс.Директ API после одобрения заявки; обновить документацию проекта.

**Что сделано:**
- `CLAUDE.md` — обновлён: добавлены роутеры `/pdf` и `/export`, сервисы `niche_analysis_ai` и `region_platforms`, полный список env-переменных, система валют, описание best-effort Supabase
- `.claude/skills/knowledge-base/assets/lessons.json` — добавлены 7 уроков по Yandex Direct API и Wordstat: коды ошибок 58/513/3000, OAuth scope/force_confirm, Direct Forecast 404 fallback, условия доступа к API v5, справочник всех error codes
- Playwright установлен в `.venv` (chromium), постоянный профиль создан в `~/.playwright-yandex-profile`

**Диагностика Direct API (🔄 в процессе):**
- Wordstat API ✅ — реальные данные, 50 ключей, `ремонт квартир` = 651K/мес
- Direct Forecast API ❌ — 404 (fallback на формулу CPC работает)
- Direct Campaigns/Dictionaries API ❌ — ошибка 58 «Незавершённая регистрация»
- Проверено: OAuth-приложение настроено (scope direct:api ✅), заявка одобрена 05.03 ✅, аккаунт активен ✅, токен валидный ✅
- Версия: вероятно задержка активации на стороне Яндекса (24–48ч после одобрения)

**Файлы изменены:** `CLAUDE.md`, `.claude/skills/knowledge-base/assets/lessons.json`

**Статус:** 🔄 В процессе — Direct API не заработал, возврат завтра

---

## 2026-03-05 — КП PDF в двух дизайн-вариантах (Dark Premium и Split Layout)

**Задача:** Создать профессиональное КП для отправки клиентам в 2 вариантах дизайна с возможностью скачивания в один клик.

**Что сделано:**
- `backend/services/pdf_export.py` — полная перепись: два профессиональных варианта с Arial Unicode (кириллица), 5-6 страниц, разделы: обложка, анализ ниши, стратегия, семантика, медиаплан, бюджет, CTA. Variant 1: тёмный фон (#0d0d1a), accent indigo/violet. Variant 3: белый контент + тёмный сайдбар (#1e1b4b) с навигацией
- `backend/routers/pdf.py` (новый) — `POST /pdf?variant=1|3`, принимает JSON отчёта, возвращает PDF без Supabase
- `backend/app.py` — зарегистрирован `/pdf` роутер
- `frontend/lib/api.ts` — метод `downloadKp(report, variant)` — скачивает blob → авто-сохранение файла
- `frontend/app/results/page.tsx` — заменена одна кнопка на две: "КП Вариант 1" (indigo) и "КП Вариант 3" (ghost)

**Файлы изменены:** `backend/services/pdf_export.py`, `backend/routers/pdf.py` (новый), `backend/app.py`, `frontend/lib/api.ts`, `frontend/app/results/page.tsx`

**Статус:** ✅ Завершено

---

## 2026-03-05 — Добавлен AI-анализ ниши, рекомендация бюджета, поддержка валют

**Задача:** Реализовать глубокий AI-анализ ниши (понимание бизнеса, аудитория, структура кампаний, стратегии), рекомендацию бюджета на основе поискового объёма и выбор валюты для медиаплана.

**Что сделано:**
- `backend/services/niche_analysis_ai.py` (новый) — вызывает Claude Haiku → OpenAI → stub; возвращает `NicheInsight` (бизнес, аудитория, типы кампаний, структура 2-4 кампаний, стратегии) + `BudgetRecommendation` (min/optimal/aggressive бюджет с прогнозом кликов и лидов); конвертация RUB/BYN/USD/EUR/KZT
- `backend/models.py` — добавлены модели `NicheInsight`, `CampaignStructureItem`, `BudgetRecommendation`; поле `currency` в `AnalyzeRequest`; поля `niche_insight`, `budget_recommendation`, `currency` в `AnalyzeResponse`
- `backend/services/media_plan.py` — конвертирует бюджет и CPC в выбранную валюту через `convert_amount()`
- `backend/routers/analyze.py` — интегрирован вызов `analyze_niche()`, передаётся `currency`, если бюджет не задан — используется AI-рекомендованный оптимальный
- `frontend/types/api.ts` — добавлены типы `NicheInsight`, `CampaignStructureItem`, `BudgetRecommendation`, поле `currency` в `AnalyzeResponse`
- `frontend/components/InputForm.tsx` — выбор валюты (RUB/BYN/USD/EUR/KZT), toggle «Рекомендовать AI» для бюджета (отключает поле ввода)
- `frontend/app/dashboard/page.tsx` — передаёт `currency` и пропускает `budget` при auto_budget=true
- `frontend/app/results/page.tsx` — новые блоки `NicheInsightBlock` (ниша, аудитория, типы кампаний, структура, стратегии, конкуренция) и `BudgetRecommendationBlock` (3 тира + прогноз); медиаплан отображает символ выбранной валюты

**Файлы изменены:** `backend/services/niche_analysis_ai.py` (новый), `backend/models.py`, `backend/services/media_plan.py`, `backend/routers/analyze.py`, `frontend/types/api.ts`, `frontend/components/InputForm.tsx`, `frontend/app/dashboard/page.tsx`, `frontend/app/results/page.tsx`

**Статус:** ✅ Завершено

---

## 2026-03-05 — Диагностика интеграции Yandex Wordstat API

**Задача:** Подключить реальные токены Яндекс.Директа и OpenAI, проверить работу Wordstat API.

**Что сделано:**
- `.env` — добавлены `OPENAI_API_KEY` (✅ рабочий), `YANDEX_WORDSTAT_TOKEN`, `YANDEX_REFRESH_TOKEN`, `YANDEX_CLIENT_ID`, `YANDEX_CLIENT_SECRET`
- `CLAUDE.md` — обновлён: убрана пометка «planned», добавлены реальные команды, актуальные env-переменные и структура бэкенда
- OpenAI API — протестирован, работает, 121 модель доступна включая gpt-4o

**Диагностика Yandex Direct API (🔄 в процессе):**
- Токен валиден (аккаунт: `alexeikalinin1`)
- Все эндпоинты возвращают ошибку 58 «Незавершенная регистрация»
- `adforecast` endpoint — 404 (не существует в v5 API, нужно исправить в коде)
- Sandbox выдаёт: «Ваш логин не подключен к Яндекс.Директу»
- Выяснено: токен нельзя отозвать через API (выдан без `device_id`)
- Предположение: `alexeikalinin1` не является рекламодателем Директа напрямую (кампания могла быть создана через другой аккаунт)

**Файлы изменены:** `.env`, `CLAUDE.md`

**Статус:** 🔄 В процессе — Yandex API заблокирован ошибкой 58, OpenAI подключён

---

## 2026-03-04 — Интеграция AI-ассистента: Claude / OpenAI / Grok, чат по отчёту

**Задача:** Подключить маркетингового ассистента для анализа запросов в веб-сервисе; ответы только по данным отчёта (правдивые).

**Что сделано:**
- `backend/config.py` — добавлены `openai_api_key`, `xai_api_key`, `ai_provider` (anthropic | openai | xai)
- `backend/services/ai_summary.py` — мультипровайдер: выбор Claude (Anthropic), OpenAI (GPT) или Grok (xAI); общий промпт вынесен в `_build_summary_prompt`; добавлены `_openai_summary`, `_xai_summary` (Grok через OpenAI-совместимый API)
- `backend/services/assistant_chat.py` (новый) — чат по отчёту: контекст = JSON отчёта в промпте, системный промпт «отвечать только по данным»; те же провайдеры
- `backend/routers/assistant.py` (новый) — `POST /assistant/chat` (body: report, question → answer)
- `backend/app.py` — подключён роутер `assistant`
- `frontend/lib/api.ts` — метод `api.assistantChat(report, question)`
- `frontend/app/results/page.tsx` — блок «Вопрос по отчёту» (AssistantChatBlock): поле ввода + кнопка Спросить, вывод ответа
- `requirements.txt` — добавлены `anthropic`, `openai`
- `.env.example` — комментарии по ANTHROPIC_API_KEY, OPENAI_API_KEY, XAI_API_KEY, AI_PROVIDER

**Файлы изменены:** `backend/config.py`, `backend/services/ai_summary.py`, `backend/services/assistant_chat.py` (новый), `backend/routers/assistant.py` (новый), `backend/app.py`, `frontend/lib/api.ts`, `frontend/app/results/page.tsx`, `requirements.txt`, `.env.example`

**Статус:** ✅ Завершено — один из ключей в .env включает нейросеть в суммари и в чат; без ключа — stub и сообщение в чате

---

## 2026-03-04 — Редизайн UI: тёмная тема v2 (glass + indigo, крупный текст)

**Задача:** Заменить светлую SaaS Dashboard тему на тёмный дизайн с glassmorphism, градиентным фоном, индиго-акцентами, увеличенной типографикой и Framer Motion анимациями.

**Что сделано:**
- `frontend/app/globals.css` — body 18px / line-height 1.6; `:root` → `#111827` bg, `#6366f1` primary (indigo-500); утилиты `.glass-card` (backdrop-blur, rgba bg, border), `.card-surface` (алиас), `.stat-card` с левой границей; `.badge-platform` для Яндекс/Google/VK с тёмным стилем; `body::before` — двойной radial-gradient mesh фон
- `frontend/app/layout.tsx` — `className="dark"` на `<html>`, `bg-[#111827] text-gray-50` на body
- `frontend/components/ResultsTable.tsx` — тёмные стили: `bg-white/[0.03]` заголовки, `even:bg-white/[0.02]` чередование строк, `hover:bg-indigo-500/5`, `text-gray-200` ячейки, крупный `text-base`
- `frontend/components/ForecastChart.tsx` — цвета indigo-500/emerald-500; крупные шрифты осей/легенды (14-16px); тёмный tooltip; округлые bars (`borderRadius: 6`)
- `frontend/components/InputForm.tsx` — `glass-card` обёртка; `bg-gray-800/80` инпуты; `text-lg h-12`; `bg-indigo-600` кнопка с hover + shadow; `motion.button` с whileHover/whileTap
- `frontend/app/dashboard/page.tsx` — `text-5xl` заголовок с gradient text; text-xl subtitle; step-карточки с `glass-card` + `whileHover scale`; staggered анимация шагов
- `frontend/app/results/page.tsx` — рефактор `SectionCard` компонент; `stat-card` с цветными левыми рамками; dark tab-bar; expanded accordion с `motion.div height: 0→auto`; цветные значения в MediaPlanTab (indigo/emerald/amber)

**Файлы изменены:** `frontend/app/globals.css`, `frontend/app/layout.tsx`, `frontend/components/ResultsTable.tsx`, `frontend/components/ForecastChart.tsx`, `frontend/components/InputForm.tsx`, `frontend/app/dashboard/page.tsx`, `frontend/app/results/page.tsx`

**Статус:** ✅ Завершено — `npm run build` проходит без ошибок TypeScript

---

## 2026-03-04 — Редизайн UI: тёмная тема → SaaS Dashboard (светлая)

**Задача:** Заменить glassmorphism/тёмную космическую тему на светлый SaaS Dashboard стиль (как Ahrefs/SEMrush) для лучшей читаемости данных.

**Что сделано:**
- `frontend/app/globals.css` — заменены CSS-переменные `:root` на светлую тему (#f8f9fa фон, #2563eb синий акцент, #0f172a текст); добавлены утилиты `.card-surface`, `.stat-card`, `.badge-platform`, `.badge-yandex`, `.badge-google`, `.badge-vk`; сохранён блок `.dark {}` для будущего тёмного режима; удалены `.glass` и `.neon-glow`
- `frontend/app/layout.tsx` — убран `className="dark"` с `<html>`, `body` переведён на `bg-background text-foreground`
- `frontend/components/ResultsTable.tsx` — обновлены стили таблицы: белый фон, slate-заголовки, hover на строках
- `frontend/components/ForecastChart.tsx` — обновлены цвета Chart.js (синий/зелёный вместо фиолетового/циана), `.glass` → `.card-surface`
- `frontend/components/InputForm.tsx` — инпуты на белом фоне с border-slate-200, синий focus-ring, кнопка `bg-blue-600`, спиннер `border-t-blue-600`
- `frontend/app/dashboard/page.tsx` — бейдж `bg-blue-50`, заголовок `text-blue-600`, степ-карточки `.card-surface`, ошибка `bg-red-50 text-red-700`
- `frontend/app/results/page.tsx` — стат-карточки `.stat-card` с цветной левой рамкой, таб-бар `border-slate-200` / активный `text-blue-600`, все `.glass` → `.card-surface`, платформ-бейджи с цветовым рендером, сезонность `text-green-600`/`text-red-600`

**Файлы изменены:** `frontend/app/globals.css`, `frontend/app/layout.tsx`, `frontend/components/ResultsTable.tsx`, `frontend/components/ForecastChart.tsx`, `frontend/components/InputForm.tsx`, `frontend/app/dashboard/page.tsx`, `frontend/app/results/page.tsx`

**Статус:** ✅ Завершено — `npm run build` проходит без ошибок TypeScript

---

## 2026-03-04 — Автоматизация настройки Supabase и проверка бэкенда

**Задача:** Выполнить инициализацию проекта самостоятельно: настройка Supabase (SQL) и проверка запуска бэкенда.

**Что сделано:**
- `scripts/run_supabase_setup.py` (новый) — скрипт выполняет `supabase_setup.sql` по `DATABASE_URL` из .env (строка из Supabase Dashboard → Connect)
- `requirements.txt` — добавлен `psycopg2-binary` для скрипта
- `.env.example` — добавлен комментарий с примером `DATABASE_URL`
- Проверка конфига: `SUPABASE_URL`, ключи читаются из .env; бэкенд стартует (uvicorn)
- Выполнить SQL без DATABASE_URL нельзя (нет доступа к SQL Editor из кода); в RESUME добавлены два варианта: вручную в SQL Editor или добавить DATABASE_URL и запустить скрипт

**Файлы изменены:** `scripts/run_supabase_setup.py` (новый), `requirements.txt`, `.env.example`, `RESUME.md`

**Статус:** ✅ Завершено — автоматический запуск SQL возможен только при наличии DATABASE_URL в .env

---

## 2026-03-04 — Реализованы Phase 5–6: реальные API + тесты

**Задача:** Подключить реальные API (Wordstat, GKP, SerpAPI, pytrends) и написать тесты

**Что сделано:**
- `backend/integrations/wordstat.py` (новый) — Yandex Direct API v5: `hasSearchVolume` + `adforecast`
- `backend/integrations/google_ads.py` (новый) — Google Keyword Planner через `google-ads-python` (в thread pool)
- `backend/integrations/serpapi.py` (новый) — конкуренты через SerpAPI Google Search
- `backend/integrations/trends.py` (новый) — сезонность через pytrends (без ключа)
- `backend/services/keywords.py` — priority chain: Wordstat → GKP → stub + enrichment pytrends
- `backend/services/competitors.py` — SerpAPI если ключ есть, иначе stub
- `backend/config.py` — все поля optional (MVP без .env запускается)
- `backend/tests/test_analyze.py` (новый) — 24 теста: unit + API endpoint
- `pytest.ini` (новый) — asyncio_mode=auto
- `requirements.txt` — убраны жёсткие версии, pytrends добавлен

**Файлы изменены:** `backend/integrations/` (4 новых), `backend/services/keywords.py`, `backend/services/competitors.py`, `backend/config.py`, `backend/tests/test_analyze.py` (новый), `pytest.ini` (новый), `requirements.txt`

**Статус:** ✅ Завершено — 24/24 тестов зелёные, black чистый

---

## 2026-03-04 — Реализованы Phase 1–4: полный MVP

**Задача:** Построить рабочий MVP PPC Master Tool — от scaffold до работающего фронтенда

**Что сделано:**
- `requirements.txt`, `.env.example`, `supabase_setup.sql`, `vercel.json` — project scaffold
- `backend/config.py`, `backend/db.py`, `backend/models.py`, `backend/app.py` — FastAPI core
- `backend/services/parser.py` — парсинг сайта через BeautifulSoup, определение ниши
- `backend/services/competitors.py` — заглушка конкурентов по нише (TODO: SerpAPI)
- `backend/services/keywords.py` — генерация ключей (заглушка; TODO: Wordstat, GKP)
- `backend/services/clustering.py` — семантическая кластеризация через sentence-transformers + KMeans
- `backend/services/audience.py` — rule-based таргетинг по нише и платформам
- `backend/services/campaigns.py` — генерация кампаний и вариантов объявлений
- `backend/services/media_plan.py` — расчёт CR/CPA/конверсий
- `backend/services/pdf_export.py` — PDF через reportlab
- `backend/routers/analyze.py` — `POST /analyze` полный pipeline
- `frontend/` — Next.js scaffold: dark тема, glassmorphism, Inter шрифт
- `frontend/app/dashboard/page.tsx` — форма ввода с Framer Motion
- `frontend/app/results/page.tsx` — страница результатов: 4 таба, Chart.js, accordion кампаний
- `frontend/components/InputForm.tsx`, `ResultsTable.tsx`, `ForecastChart.tsx`
- `frontend/types/api.ts`, `frontend/lib/api.ts`
- `.claude/skills/` — установлена Skills System (knowledge-base, change-logger, quality-loop, meta-orchestrator, skill-factory)

**Файлы изменены:** `backend/` (все файлы — новые), `frontend/app/` (новые), `frontend/components/` (новые), `frontend/lib/api.ts`, `frontend/types/api.ts` (новые), `.claude/skills/` (новые), `CLAUDE.md` (обновлён)

**Статус:** ✅ Завершено

---
