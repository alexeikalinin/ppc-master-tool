---
name: skill-factory
description: "Creates new skills and improves existing ones based on detected patterns. Use this skill when: the user explicitly asks to 'create a skill', 'make a template', 'automate this workflow', or 'turn this into a reusable process'. Also trigger when meta-orchestrator detects a repeated task pattern (3+ similar requests) and suggests skill creation. Use for refactoring or improving any existing skill. If the user says 'I keep doing X' or 'every time I need to Y' — that's a signal to create a skill."
---

# Skill Factory

Creates new skills from scratch or from observed patterns, and iteratively improves existing skills.

## Skill Creation Workflow

### Step 1: Gather Requirements

Understand what the skill should do:
1. User's explicit description
2. Patterns from `knowledge-base/assets/patterns.json`
3. Lessons from `knowledge-base/assets/lessons.json`
4. Conversation history if "turn this into a skill"

Key questions:
- What does this skill enable Claude to do?
- When should it trigger? (trigger words, contexts)
- What's the expected output format?
- What are the edge cases?

### Step 2: Write the Skill

Structure:
```
new-skill-name/
├── SKILL.md              # Required
├── references/           # If needed (>500 lines of instructions)
└── assets/               # If needed (templates, examples)
```

**Frontmatter** (critical for triggering):
```yaml
---
name: descriptive-kebab-case-name
description: "What it does + WHEN to trigger. List all synonyms, related phrases, and contexts. Include 'Do NOT use for...' boundaries."
---
```

**Body must include:**
1. Overview — what and why
2. Quick Reference — table of task → approach
3. Step-by-step instructions — imperative form, with reasoning
4. Examples — Input → Output pairs
5. Anti-patterns — what NOT to do and why

### Step 3: Register

Add the new skill to `knowledge-base/assets/skills-registry.json`:
```json
{
  "name": "new-skill-name",
  "path": "new-skill-name/SKILL.md",
  "description": "One-line description",
  "created": "YYYY-MM-DD",
  "last_modified": "YYYY-MM-DD",
  "status": "active"
}
```

Notify the user: "Created skill [name]. It will activate when you [trigger conditions]."

### Step 4: Iterate

Based on usage:
1. Identify what went wrong
2. Update SKILL.md with fixes
3. Add failure cases as anti-patterns

## Templates

See `references/templates.md` for 5 starter templates:
- Document Generator
- Code Task
- Data Processor
- Content Creator
- Workflow Automator

## Anti-patterns

- Don't create skills for tasks that happen only once
- Don't make skills too specific (hardcoded values, single-use templates)
- Don't duplicate existing skills — check the registry first
