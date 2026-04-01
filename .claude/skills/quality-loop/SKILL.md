---
name: quality-loop
description: "Evaluates output quality, collects feedback, and extracts lessons for continuous improvement. Use this skill after ANY task completion when the user provides feedback (positive, negative, corrections). Also trigger when the user says 'remember this', 'next time do X', 'I prefer Y', or expresses satisfaction/dissatisfaction. Trigger proactively after complex tasks to self-review even without explicit feedback. This is the learning engine — every piece of feedback makes future tasks better."
---

# Quality Loop

The feedback and learning engine. Captures what went well, what didn't, and why — then stores actionable lessons in the knowledge-base.

## Quick Reference

| Signal | Action |
|---|---|
| User says "great" / "perfect" | Record positive pattern (light touch) |
| User says "wrong" / "fix this" / corrections | Record lesson with HIGH priority |
| User edits output themselves | Extract the delta as a lesson |
| Complex task completed, no feedback | Run quick self-review |
| User says "remember this" / "always do X" | Record as persistent preference |
| Same error 2+ times | Escalate — update skill or create anti-pattern |

## Feedback Processing Workflow

### Step 1: Classify Feedback

| Type | Examples | Action |
|---|---|---|
| **Preference** | "I prefer tables over lists" | Store in preferences.json |
| **Correction** | "The date format should be DD.MM.YYYY" | Store as lesson with before/after |
| **Approval** | "Perfect", "exactly right" | Store as positive pattern (lightweight) |
| **Rejection** | "Not what I asked for" | Analyze the gap, store as high-priority lesson |
| **Improvement** | "Good but add X" | Store as refinement with context |

### Step 2: Extract Actionable Lesson

```json
{
  "id": "lesson-YYYY-MM-DD-NNN",
  "date": "2026-02-13",
  "type": "preference | correction | pattern | anti-pattern",
  "category": "formatting | content | code | workflow | communication",
  "summary": "One-line actionable takeaway",
  "detail": "Full context: what was expected, what was delivered, what the fix is",
  "trigger": "When this lesson applies (task type, keywords, context)",
  "source": "user_feedback | self_review | error_analysis",
  "confidence": "high | medium | low",
  "applies_to": ["skill-name-1", "general"]
}
```

Quality rules:
- **Specific > vague**: "Use DD.MM.YYYY date format" not "improve date formatting"
- **Actionable**: Every lesson must answer "what should I do differently next time?"
- **Scoped**: Indicate when the lesson applies
- **Timestamped**: Newer lessons take priority over older contradictory ones

### Step 3: Check for Patterns

Before storing, scan existing lessons for:
1. **Duplicates**: Update confidence/occurrences instead of duplicating
2. **Contradictions**: Replace old with new, note the change
3. **Escalation**: 2nd+ occurrence → mark as high priority
4. **Skill gap**: Recurring error → flag for skill-factory

### Step 4: Store in Knowledge Base

Append to `.claude/skills/knowledge-base/assets/lessons.json`.

If pattern detected (3+ similar lessons), also update `patterns.json`.

### Step 5: Report (if significant)

Only report when there's a meaningful improvement:
- "I've noted your preference for [X]. I'll apply this going forward."
- "This is the 3rd time you've asked for [task type]. Want me to create a dedicated skill?"

Don't report on every minor lesson.

## Self-Review Mode

For complex tasks without explicit feedback:
1. Re-read the original request
2. Compare output — does it answer what was asked?
3. Check completeness, accuracy, format, tone
4. If issues found, note as "low confidence" lessons
5. If no issues — no action needed

## Anti-patterns

- Don't store lessons for obvious one-off situations ("user had a typo")
- Don't create lessons that are too generic to be actionable
- Don't overwhelm the user with "I learned X" messages — be selective
- Don't second-guess explicit user preferences
- Don't let knowledge-base grow without bounds — prune stale lessons (>90 days, low confidence, occurrences: 1)
