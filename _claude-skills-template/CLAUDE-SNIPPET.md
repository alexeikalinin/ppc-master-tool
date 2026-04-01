# Сниппет для вставки в CLAUDE.md нового проекта

Скопируй секцию ниже (между ---) в CLAUDE.md своего проекта.
Замени пути если структура папок отличается.

---

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

---
