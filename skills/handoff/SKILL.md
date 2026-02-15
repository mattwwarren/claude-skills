# Session Handoff

Generate structured handoff documents for abnormal session endings so work resumes cleanly.

## Triggers

Generate a handoff when any of these occur:

1. **Context exhaustion** - Session at 80%+ context usage
2. **Debug depth 2+** - Two or more failed debugging attempts on the same issue
3. **Scope creep** - Task scope expanded beyond original intent

Use `/session-done` for normal endings. Use `/handoff` only for constrained situations.

## Invocation

```
/handoff --reason context|debug-fork|scope
```

## Handoff Types

### Context Exhaustion (`--reason context`)

Single handoff document containing:
- Completed work summary
- In-progress items with current state
- Blocked items with reasons
- Compact resumption prompt

### Debug Fork (`--reason debug-fork`)

Produces **TWO** documents:

1. **Main track** (`handoff-main-YYYY-MM-DD-HHMM.md`) - Continue feature work, explicitly skip the stuck issue. Lists remaining tasks and a resumption prompt focused on forward progress.
2. **Debug track** (`handoff-debug-YYYY-MM-DD-HHMM.md`) - Fresh investigation of the specific issue. Documents symptoms, error messages, numbered attempts with results, and untested hypotheses. Resumption prompt targets a clean investigation.

This prevents the next session from falling into the same rabbit hole.

### Scope Exhaustion (`--reason scope`)

Single handoff document containing:
- Original scope vs discovered additions
- Prioritized breakdown: must-do, should-do, nice-to-do
- Handoff focused on must-do items only
- Deferred items documented as separate tasks

## Required Sections

Every handoff document MUST include:

1. **Frontmatter** - type, created (UTC), reason
2. **Header** - Date (UTC), Status, Plan reference (absolute path)
3. **Summary** - 1-3 sentences of what was accomplished
4. **Progress** - Overall %, todos completed, current phase
5. **Critical Context** - Decisions made, approaches rejected
6. **Next Actions** - Up to 5 unchecked tasks
7. **Resumption Prompt** - Self-contained copy-paste prompt in a code block

Optional sections (include when relevant):
- Changes This Session (git diff summary)
- Test Results
- Blockers
- Agent Results

## Fresh-Context Principle

Handoffs MUST be completely self-contained. The next session has zero memory.

**Always include:**
- Plan file absolute path
- Current phase name
- Progress percentage
- Brief session summary
- Path to handoff document itself

**Never include:**
- "As discussed earlier..."
- "You know how we..."
- Implicit references to prior conversation
- Assumptions about shared context

## File Location and Naming

Write all handoffs to `.handoffs/` in the project root. Create the directory if it does not exist.

| Type | Filename |
|------|----------|
| Standard | `handoff-YYYY-MM-DD-HHMM.md` |
| Debug fork main | `handoff-main-YYYY-MM-DD-HHMM.md` |
| Debug fork debug | `handoff-debug-YYYY-MM-DD-HHMM.md` |

Use current UTC time for the timestamp.

## Templates

Use the templates in `templates/handoff/` from the claude-skills directory:

| Template | Use For |
|----------|---------|
| `session-handoff.md` | Context exhaustion, scope creep |
| `debug-fork-main.md` | Main track of a debug fork |
| `debug-fork-debug.md` | Debug track of a debug fork |

## Execution Steps

When `/handoff` is invoked:

1. **Gather context**
   - Read current todos and their states
   - Check `git status` and `git diff --stat` for changes this session
   - Identify the active plan file (if any)
   - Note key decisions and rejected approaches from the session

2. **Select handoff type** based on `--reason`

3. **Generate document(s)** using the appropriate template
   - Fill all required sections
   - Write a self-contained resumption prompt
   - For debug forks, generate both documents

4. **Write to `.handoffs/`** in the project root

5. **Display summary** to the user
   - Show file path(s)
   - Print the resumption prompt
   - Suggest next steps (e.g., "Start a new session and paste the resumption prompt")

## Resumption Prompt Format

Every resumption prompt must follow this structure:

```
Continuing work on [task name] per plan at [absolute plan path].

Session context:
- Phase: [current phase name]
- Progress: [X]% complete
- [2-3 essential context items]

Previous handoff: [absolute path to this handoff file]

Start by [specific first action].
```
