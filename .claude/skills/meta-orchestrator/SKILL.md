---
name: meta-orchestrator
description: "Central coordinator that routes tasks to appropriate skills and agents. Use this skill whenever the user gives a complex or ambiguous task that may require multiple steps, delegation, or when it's unclear which skill to use. Also trigger when the user asks to 'do something', 'help me with', 'figure out', or gives multi-part requests. This skill decides WHAT to do and WHO does it. If no other skill clearly matches — meta-orchestrator handles routing. Even for simple tasks, consider whether quality-loop feedback or knowledge-base context could improve the result."
---

# Meta-Orchestrator

The brain of the self-improving skill system. It analyzes user requests, plans execution, delegates to specialized skills/agents, and feeds results back through the quality loop.

## Core Philosophy

Every task follows a cycle: **Understand → Plan → Execute → Review → Learn**. The orchestrator manages this cycle, ensuring each step feeds into the next. Over time, the system gets better because lessons from Review flow into the knowledge-base, which improves future Planning.

## Quick Reference

| User Intent | Route To | Agent |
|---|---|---|
| Complex/multi-step task | Break down → delegate to skills | planner → executor |
| "Create a skill/template for X" | skill-factory | planner |
| Repeated task pattern detected | skill-factory (suggest new skill) | planner |
| Task completed, needs review | quality-loop | reviewer |
| "What did we learn about X?" | knowledge-base | planner |
| Simple, clear task | Execute directly with relevant skill | executor |
| **PPC/marketing analysis, competitor research, keyword research, media plan, audience profiling** | **ppc-market-analyst agent** | **executor** |

## Workflow

### Step 1: Analyze the Request

Before doing anything, ask yourself:

1. What is the user actually trying to achieve? (not just what they said)
2. Is there relevant context in `knowledge-base/assets/lessons.json`? Read it.
3. Has a similar task been done before? Check `knowledge-base/assets/patterns.json`.
4. Which skills and agents are needed?

### Step 2: Plan

For simple tasks (single skill, clear output): skip planning, go straight to execution.

For complex tasks, create a plan:

```
Task: [user's request in one line]
Steps:
1. [action] → [skill/agent] → [expected output]
2. [action] → [skill/agent] → [expected output]
Dependencies: [which steps depend on others]
Risk: [what could go wrong]
```

Share the plan with the user before executing if the task has more than 3 steps or involves irreversible actions.

### Step 3: Execute

Delegate to agents. Read `agents/planner.md`, `agents/executor.md`, `agents/reviewer.md` for their specific procedures.

Key rules:
- Always check knowledge-base for relevant lessons before executing
- If a step fails, try an alternative approach before asking the user
- Document what you did and why (the reviewer needs this)

### Step 4: Review

After execution, route through quality-loop:
1. Did the output match user expectations?
2. Were there any surprises, errors, or workarounds?
3. What should be remembered for next time?

If the user provides explicit feedback ("great", "not what I wanted", corrections), this is high-value signal — always record it via quality-loop.

### Step 5: Learn

If the review reveals:
- A **repeated pattern** → suggest creating a new skill via skill-factory
- A **lesson** → store in knowledge-base via quality-loop
- A **skill improvement** → note it for future skill-factory iteration

## Agent Coordination

```
User Request
    ↓
[Planner] → creates execution plan (consults knowledge-base)
    ↓
[Executor] → follows plan, produces output
    │         ↳ if PPC/marketing task → delegates to ppc-market-analyst agent
    │              ↳ agent reads knowledge-base/lessons.json before analysis
    │              ↳ agent writes new lessons after analysis
    ↓
[Reviewer] → evaluates output quality
    ↓
[Knowledge-Base] ← stores lessons learned (via quality-loop)
    ↓
User receives output + optional improvement suggestions
```

## Self-Improvement Triggers

The orchestrator should proactively suggest improvements when:

1. **Same task type appears 3+ times** → "I notice you often ask me to X. Want me to create a dedicated skill for this?"
2. **Quality-loop finds recurring errors** → "I keep making the same mistake with Y. Let me update the knowledge-base with a fix."
3. **User corrects the same thing repeatedly** → "You've corrected Z several times. I'll remember this preference."

## Anti-patterns

- Don't over-plan simple tasks. If the user says "translate this text", just do it.
- Don't ask the user to choose between skills — that's your job.
- Don't skip the review step for important outputs. Even a quick self-check matters.
- Don't create new skills for one-off tasks. Wait for patterns.

## Edge Cases

- **No matching skill**: Execute directly using your general capabilities. Log the gap — if it recurs, it's a signal to create a new skill.
- **Conflicting lessons in knowledge-base**: Use the most recent lesson. Flag the conflict for user review.
- **User wants to override the plan**: Always respect user preferences. Update knowledge-base with their preference.
