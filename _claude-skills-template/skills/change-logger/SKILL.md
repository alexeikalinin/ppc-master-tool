---
name: change-logger
description: "Log code changes, session progress, and completed work. Use this skill when: the user says 'log this', 'update the log', 'session is done', 'we're done', 'save progress', 'запиши в лог', 'обнови лог', 'сессия завершена', 'залогируй'. Also trigger automatically at the end of any session involving code changes. Looks for DEVELOPMENT_LOG.md and RESUME.md in project root; creates or updates them. Do NOT use for logging errors or debug output — only for session/change history."
---

# Change Logger

Records completed work in structured project logs. Maintains DEVELOPMENT_LOG.md (full history) and RESUME.md (current state + next steps).

## Overview

After code changes, the context of "what was done and why" is as important as the code itself. This skill writes structured log entries so future sessions (and other editors/assistants) can resume from a known state without asking what happened.

## Quick Reference

| Trigger | Action |
|---|---|
| Session ending with code changes | Write DEVELOPMENT_LOG entry + update RESUME.md |
| User says "log this" / "залогируй" | Write DEVELOPMENT_LOG entry for current changes |
| User says "update RESUME.md" | Update only RESUME.md current state |
| User says "what changed?" | Read DEVELOPMENT_LOG.md, summarize last 2-3 entries |
| New project, no log files | Create DEVELOPMENT_LOG.md and RESUME.md from scratch |

## Detection

Before writing, check what files exist in the project root:

```
[ ] DEVELOPMENT_LOG.md  → append new entry at the TOP
[ ] RESUME.md           → update "Последнее обновление" and "Где остановились"
[ ] Neither exists      → create both from templates below
```

If the project uses different log files (CHANGELOG.md, HISTORY.md), adapt accordingly.

## DEVELOPMENT_LOG Entry Format

Always **prepend** (add to TOP of file, not append):

```markdown
## YYYY-MM-DD — [Short title of what was done]

**Задача:** [One sentence: what was the goal]

**Что сделано:**
- [Change 1: file + what changed + why]
- [Change 2: file + what changed + why]

**Файлы изменены:** `file1.ts`, `file2.tsx`, `new-file.ts` (новый)

**Статус:** ✅ Завершено | ⚠️ Частично | 🔄 В процессе

---
```

Rules:
- Date: today's date in YYYY-MM-DD format
- Title: imperative verb + noun ("Добавлен парсер погоды", "Исправлена авторизация")
- File list: include `(новый)` for created files, `(удалён)` for deleted files
- Status: always include one of the three options

## RESUME.md Update Format

Update only these two fields (don't touch the rest):

```markdown
## Последнее обновление
YYYY-MM-DD — [What was done in 1 sentence]

## Где остановились
- [Current state of the feature/fix]
- [What's next / what's pending]
- [Any known issues or blockers]
```

## RESUME.md Template (for new projects)

```markdown
# Точка продолжения работы

**Обновляйте этот файл в конце каждой сессии.**

---

## Последнее обновление
[DATE] — [What was done]

## Где остановились
- [Current state]
- [Next steps]

## Как запустить
[Commands to start the project]

## Ветка и репозиторий
- Ветка: `main`
- Remote: [remote URL]

## Приоритеты
- [ ] [Priority 1]
- [ ] [Priority 2]
```

## DEVELOPMENT_LOG.md Template (for new projects)

```markdown
# Лог разработки

**Все изменения в проекте документируются здесь.**

---

## YYYY-MM-DD — Инициализация проекта

**Задача:** Создать базовую структуру проекта

**Что сделано:**
- Инициализирован проект
- Добавлена система скиллов Claude

**Файлы изменены:** `CLAUDE.md`, `RESUME.md`, `.claude/skills/`

**Статус:** ✅ Завершено

---

## План дальнейшей разработки

- [ ] [Task 1]
- [ ] [Task 2]
```

## Step-by-Step Workflow

### Step 1: Collect Change Information

Gather from context (git status, file edits in session, user description):
- What files were changed?
- What was the goal / what problem was solved?
- Current state: done / partial / blocked?
- What should happen next?

Run `git diff --name-only` or `git status` to confirm changed files if git is available.

### Step 2: Check Existing Logs

Read the first 20 lines of DEVELOPMENT_LOG.md (if exists) to:
- Understand the existing format
- Avoid duplicating the latest entry (check if today's entry already exists)

### Step 3: Write the Log Entry

Compose the entry following the format above.
- Be specific: "Исправлен парсинг og:image для belta.by" not "исправлен парсер"
- Include the "why" for non-obvious changes
- Link to previous work if continuing: "Продолжение: исправление от YYYY-MM-DD"

### Step 4: Update RESUME.md

Update "Последнее обновление" with today's date + one-liner.
Update "Где остановились" to reflect the current state.
If a priority item was completed, mark it: `- [x] ...`

### Step 5: Confirm with User

Briefly show what was written:
> "Записал в DEVELOPMENT_LOG.md: [title]. RESUME.md обновлён — состояние: [current state]."

Don't show the full entry unless asked.

## Examples

**Example — Feature added:**
```
## 2026-03-04 — Добавлен скилл логирования изменений

**Задача:** Создать скилл для автоматического ведения DEVELOPMENT_LOG.md

**Что сделано:**
- `.claude/skills/change-logger/SKILL.md` — новый скилл с форматом и процедурой логирования
- `knowledge-base/assets/skills-registry.json` — добавлена запись нового скилла

**Файлы изменены:** `.claude/skills/change-logger/SKILL.md` (новый), `skills-registry.json`

**Статус:** ✅ Завершено

---
```

## Anti-patterns

- Don't write vague entries ("обновлены файлы", "исправлен баг") — always name the specific change
- Don't skip the "Файлы изменены" line — it's the most useful for quick scanning
- Don't overwrite previous entries — always prepend to the top
- Don't duplicate an entry if one was already written for the same changes today — update the existing one instead
- Don't update RESUME.md "Где остановились" with completed tasks — only put the *current* state there

## Edge Cases

- **No log files exist**: Create DEVELOPMENT_LOG.md and RESUME.md from templates above
- **Multiple sessions same day**: Extend the existing today's entry instead of creating a duplicate
- **Partial work / blocked**: Use status "🔄 В процессе" and describe the blocker in "Где остановились"
- **English project**: Use English headers — same structure, different language
- **No git**: Ask the user to list changed files, or use context from the conversation
