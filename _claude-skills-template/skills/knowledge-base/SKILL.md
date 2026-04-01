---
name: knowledge-base
description: "Persistent memory system that stores lessons, patterns, preferences, and task history. Use this skill when: any other skill needs to read or write accumulated knowledge, the user asks 'what did we learn about X', 'what are my preferences', 'show me past patterns', or when meta-orchestrator needs context for planning. Also trigger when the user asks to 'remember', 'forget', or 'update' something about how tasks should be done. This is the system's long-term memory."
---

# Knowledge Base

The persistent memory of the skill system. Stores lessons learned, detected patterns, user preferences, and a registry of available skills.

## Data Structure

All data lives in `assets/` as JSON files:

| File | Purpose | Written by | Read by |
|---|---|---|---|
| `lessons.json` | Accumulated lessons and corrections | quality-loop | meta-orchestrator, planner, skill-factory |
| `patterns.json` | Detected recurring task patterns | quality-loop | meta-orchestrator, skill-factory |
| `preferences.json` | User's persistent preferences | quality-loop | all skills and agents |
| `skills-registry.json` | Inventory of available skills | skill-factory | meta-orchestrator, planner |

## Reading Data

When any skill needs context:
1. Read the relevant JSON file from `assets/`
2. Filter by relevance (category, applies_to, trigger conditions)
3. Sort by confidence (high first) then by date (newest first)
4. Use only the top 5-10 most relevant entries to avoid context overload

## Writing Data

Only quality-loop and skill-factory write to the knowledge-base. Rules:
1. **Validate before writing**: Check for duplicates and contradictions
2. **Increment, don't duplicate**: If a similar lesson exists, update `occurrences` and `last_confirmed`
3. **Resolve contradictions**: Newer explicit feedback overrides older inferred lessons
4. **Maintain integrity**: Always update `last_updated`

## Pruning

Periodically clean the knowledge-base:
- Remove lessons with `confidence: low` that are >90 days old and `occurrences: 1`
- Archive patterns with `status: acted_on` that haven't recurred in 60 days
- Merge similar lessons into a single consolidated lesson

## Anti-patterns

- Don't load the entire knowledge-base into context — filter first
- Don't store raw conversation history — extract lessons only
- Don't let any single JSON file exceed 500 entries — archive old ones
- Don't override user preferences with inferred preferences
- Don't store sensitive data (passwords, tokens, personal info)
