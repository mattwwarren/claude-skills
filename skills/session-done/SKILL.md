# Wrap Up Work Session

End your work session by generating a handoff document and signaling completion to the `cw` orchestrator.

## Invocation

```
/session-done [--plan <path>]
```

## What This Command Does

1. **Gathers session context** from git, todos, and conversation
2. **Generates handoff document** in `.handoffs/session-YYYY-MM-DD-HHMM.md`
3. **Signals session complete** to `cw` via `cw done`

## Execution Steps

When `/session-done` is invoked:

### Step 1: Gather Context

- Check `git status` and `git diff --stat` for changes this session
- Read current todos and their states
- Summarize key decisions and work completed
- If `--plan <path>` provided, read the plan for phase context

### Step 2: Generate Handoff Document

Write a handoff document to `.handoffs/session-YYYY-MM-DD-HHMM.md` containing:

1. **Frontmatter** - type: session-handoff, created (UTC)
2. **Summary** - 1-3 sentences of what was accomplished
3. **Changes** - Git diff stats, files modified
4. **Critical Context** - Decisions made, approaches rejected
5. **Next Actions** - Up to 5 unchecked remaining tasks
6. **Resumption Prompt** - Self-contained copy-paste prompt in a code block

### Step 3: Signal Completion

Run:

```bash
cw done
```

This tells the `cw` orchestrator that the session is finished and available for new work.

### Step 4: Display Summary

Report to the user:
- Handoff file path
- Print the resumption prompt
- Suggest next steps

## Fresh-Context Principle

The handoff MUST be completely self-contained. The next session has zero memory.

**Always include:**
- Plan file absolute path (if applicable)
- Current phase name
- Brief session summary
- Path to handoff document itself

**Never include:**
- "As discussed earlier..."
- Implicit references to prior conversation
- Assumptions about shared context

## Resumption Prompt Format

Every resumption prompt must follow this structure:

```
Continuing work on [task name].

Session context:
- [2-3 essential context items]
- [Key files modified or in progress]

Previous handoff: [absolute path to this handoff file]

Start by [specific first action].
```

## Relationship to /handoff

| Situation | Use |
|-----------|-----|
| Work complete or at a good stopping point | `/session-done` |
| Context window exhausted (80%+) | `/handoff --reason context` |
| Stuck debugging after 2+ attempts | `/handoff --reason debug-fork` |
| Scope expanded beyond original task | `/handoff --reason scope` |

`/session-done` is for normal endings. `/handoff` is for constrained or abnormal endings.
