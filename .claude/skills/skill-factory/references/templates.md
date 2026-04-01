# Skill Templates

Starter templates for common skill types. Copy the appropriate template and customize.

---

## 1. Document Generator

```yaml
---
name: [doc-type]-generator
description: "Generate [document type]. Trigger when user mentions '[keywords]', asks to 'write a [doc type]'. Do NOT use for [boundaries]."
---
```

```markdown
# [Document Type] Generator

## Overview
Creates [document type] following [standard/template].

## Output Template
ALWAYS use this structure:
# [Title]
## [Section 1]
[content]

## Step-by-step
1. Gather input from user or files
2. Apply template structure
3. Fill sections with content
4. Review for completeness

## Anti-patterns
- Don't [common mistake]
```

---

## 2. Code Task

```yaml
---
name: [language]-[task]
description: "Handle [code task] in [language/framework]. Trigger when user asks to '[action verbs]', mentions '[keywords]'. Do NOT use for [boundaries]."
---
```

```markdown
# [Language] [Task]

## Overview
[What this does and why this approach].

## Standards
- [Coding standard 1 with reasoning]
- [Coding standard 2 with reasoning]

## Step-by-step
1. Analyze the codebase/file structure
2. [Task-specific step]
3. Validate with [linter/tests]
4. Document changes

## Anti-patterns
- Don't [common mistake with explanation]
```

---

## 3. Data Processor

```yaml
---
name: [data-type]-processor
description: "Process and transform [data type]. Trigger when user uploads [file types], asks to 'analyze', 'clean', 'transform', 'convert'. Do NOT use for [boundaries]."
---
```

```markdown
# [Data Type] Processor

## Overview
Transforms [input format] into [output format].

## Input Validation
Before processing, verify:
- [ ] File format is correct
- [ ] Required fields present

## Processing Pipeline
1. Load and validate input
2. Clean data
3. Transform
4. Validate output

## Anti-patterns
- Don't process without validating input first
- Don't silently drop malformed rows — log them
```

---

## 4. Content Creator

```yaml
---
name: [content-type]-creator
description: "Create [content type]. Trigger when user asks to 'write', 'draft', 'create' [content]. Do NOT use for [boundaries]."
---
```

```markdown
# [Content Type] Creator

## Tone and Style
- Voice: [formal/casual/technical/friendly]
- Length: [target range]
- Language: Match user's language for output

## Output Template
[Exact template with placeholders]

## Step-by-step
1. Identify audience and purpose
2. Research topic if needed
3. Draft following template
4. Self-review against tone guide

## Anti-patterns
- Don't use generic filler phrases
- Don't ignore the target audience
```

---

## 5. Workflow Automator

```yaml
---
name: [workflow]-automator
description: "Automate [workflow]. Trigger when user asks to '[action verbs]', mentions '[keywords]', or starts a [process type]. Do NOT use for [boundaries]."
---
```

```markdown
# [Workflow] Automator

## Overview
Automates [workflow] by [approach].

## Prerequisites
- [Tool/access 1]
- [Tool/access 2]

## Workflow Steps

### Step 1: [Name]
**Action**: [What to do]
**Tool**: [Which tool to use]
**Input**: [What's needed]
**Output**: [What's produced]
**On failure**: [Fallback approach]

## Decision Points

| Condition | Action |
|---|---|
| [condition 1] | [take path A] |
| [condition 2] | [take path B] |

## Anti-patterns
- Don't skip validation steps even if they seem redundant
- Don't automate steps that need human judgment without flagging them
```
