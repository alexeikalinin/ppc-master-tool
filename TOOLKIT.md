# PPC Master Tool — Toolkit Reference

> Полный список инструментов: скиллы, агенты, MCP, разрешения.
> Используй этот файл для быстрого воспроизведения среды в новых проектах.

---

## Скиллы (`.claude/skills/`)

| Скилл | Назначение | Команда |
|-------|-----------|---------|
| **meta-orchestrator** | Центральный координатор — маршрутизирует задачи между скиллами и агентами | авто (при сложных задачах) |
| **skill-factory** | Создаёт новые скиллы из повторяющихся паттернов | "создай скилл для X" |
| **quality-loop** | Обрабатывает фидбек, извлекает уроки, обновляет knowledge-base | авто (при feedback) |
| **knowledge-base** | Постоянная память: уроки, паттерны, предпочтения, история задач | "что мы знаем про X" |
| **change-logger** | Логирует изменения в DEVELOPMENT_LOG.md и RESUME.md | "залогируй" / авто после кода |

### Встроенные скиллы Claude Code (системные)

| Скилл | Назначение |
|-------|-----------|
| **update-config** | Настройка settings.json, hooks, permissions |
| **keybindings-help** | Кастомизация клавиатурных сокращений |
| **simplify** | Ревью изменённого кода: качество, переиспользование |
| **loop** | Запуск промпта/команды по интервалу |
| **schedule** | Создание scheduled remote agents (cron) |
| **claude-api** | Помощь с Anthropic SDK / Claude API |

---

## Агенты (`.claude/agents/`)

| Агент | Модель | Инструменты | Назначение |
|-------|--------|------------|-----------|
| **ppc-market-analyst** | claude-sonnet-4-6 | WebSearch, WebFetch, Read, Write | Конкурентный анализ, keyword research, аудитория, медиапланирование, ниша |

**Триггеры ppc-market-analyst:**
`проанализируй`, `анализ ниши`, `конкуренты`, `ключевые слова`, `медиаплан`, `аудитория`, `PPC`, `реклама`, `кампания`, `бюджет рекламы`, `wordstat`, `keyword planner`

---

## MCP-серверы

> На данный момент MCP-серверы не установлены.

### Рекомендуемые для будущего

| MCP | Назначение |
|-----|-----------|
| **filesystem** | Расширенный доступ к файловой системе |
| **github** | GitHub API — PR, issues, commits |
| **postgres / supabase** | Прямые SQL-запросы в базу |
| **puppeteer** | Браузерная автоматизация / скрейпинг |
| **ide** | Диагностика из IDE (уже подключён через Claude Code) |

---

## Разрешения (`~/.claude/settings.json`)

```json
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Read(*)",
      "Write(*)",
      "Edit(*)",
      "Glob(*)",
      "Grep(*)",
      "WebFetch(*)",
      "WebSearch(*)"
    ]
  }
}
```

---

## Структура `.claude/`

```
.claude/
├── agents/
│   └── ppc-market-analyst.md       # PPC-аналитик
├── skills/
│   ├── meta-orchestrator/
│   │   ├── SKILL.md
│   │   └── agents/
│   │       ├── planner.md
│   │       ├── executor.md
│   │       └── reviewer.md
│   ├── skill-factory/
│   │   ├── SKILL.md
│   │   └── references/templates.md
│   ├── quality-loop/
│   │   └── SKILL.md
│   ├── knowledge-base/
│   │   ├── SKILL.md
│   │   └── assets/
│   │       ├── preferences.json
│   │       ├── lessons.json
│   │       ├── patterns.json
│   │       └── skills-registry.json
│   └── change-logger/
│       └── SKILL.md
```

---

## Скиллы для подключения (из скриншота)

Анализ полезности для PPC Master Tool:

| # | Скилл | Что делает | Приоритет для проекта | Причина |
|---|-------|-----------|----------------------|---------|
| 1 | **Context Memory Sync** | Фиксирует архитектурные решения между сессиями | ✅ **Высокий** | Уже частично реализован через RESUME.md + knowledge-base; можно усилить |
| 2 | **CI/CD Quick Setup** | Docker, GitHub Actions, Railway, VPS пайплайн | 🟡 Средний | Деплой на Vercel+Railway нужен, но пока не приоритет |
| 3 | **Rapid Spec Builder** | Сырая идея → структурированное ТЗ + API-контракты | ✅ **Высокий** | При добавлении новых фич (Tracker, Bidding Robot) — формализует требования |
| 4 | **Error Handling Standardizer** | Единая система обработки ошибок и логирования | 🟡 Средний | Backend уже имеет try/except, но единого стандарта нет |
| 5 | **Performance Scanner** | Узкие места, медленные запросы, оптимизации | 🟡 Средний | Полезен когда появится реальная нагрузка |
| 6 | **API Contract Guardian** | Валидация данных, OpenAPI/Zod схемы | ✅ **Высокий** | FastAPI + Pydantic уже есть; скилл укрепит контракты и фронтовые типы |
| 7 | **Dependency Optimizer** | Аудит зависимостей, удаление лишнего | 🟢 Низкий | Проект молодой, зависимостей немного |
| 8 | **Smart Test Generator** | Unit и integration тесты с граничными сценариями | ✅ **Высокий** | Только 24 теста, покрытие слабое; критично для pipeline |
| 9 | **Auto Refactor Pro** | Безопасный рефакторинг, читаемость | 🟡 Средний | Полезен перед Phase 3 (Supabase Auth, масштабирование) |
| 10 | **Clean Architecture Enforcer** | Clean Architecture структура проекта | 🟢 Низкий | Текущая структура достаточно чистая |

### ТОП-4 для установки прямо сейчас

1. **Smart Test Generator** — покрытие тестами критично, pipeline сложный
2. **API Contract Guardian** — защита стыка FastAPI ↔ Next.js
3. **Rapid Spec Builder** — для планирования Tracker и Bidding Robot модулей
4. **Context Memory Sync** — усилит уже работающую систему RESUME.md

---

## Быстрая установка в новом проекте

### 1. Скопировать `.claude/` директорию целиком
```bash
cp -r /path/to/ppc-master-tool/.claude /path/to/new-project/
```

### 2. Настроить глобальные разрешения
```bash
# ~/.claude/settings.json — уже настроен глобально
```

### 3. Обновить агента под новый проект
```bash
# Отредактировать .claude/agents/*.md — название, описание, триггеры
```

### 4. Инициализировать knowledge-base
```bash
# Очистить .claude/skills/knowledge-base/assets/lessons.json
# Обновить preferences.json под новый проект
```

### 5. Создать RESUME.md и DEVELOPMENT_LOG.md
```bash
touch RESUME.md DEVELOPMENT_LOG.md
```
