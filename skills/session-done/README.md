# Session Done Skill

Wrap up a work session by generating a handoff document and signaling completion to the `cw` orchestrator.

## What It Does

When you're done working, this skill captures what was accomplished and what's remaining in a self-contained handoff document. It then signals `cw done` so the orchestrator knows the session is available for new work.

## Prerequisites

- The `cw` CLI must be installed and configured

## Usage

```bash
# Standard session wrap-up
/session-done

# With explicit plan reference
/session-done --plan ~/.claude/plans/auth-system/main.md
```

## What Gets Generated

- **Handoff document** at `.handoffs/session-YYYY-MM-DD-HHMM.md`
  - Session summary
  - Git diff summary
  - Critical context and decisions
  - Self-contained resumption prompt
- **`cw done`** signal to the orchestrator

## Integration

- **Upstream**: Works after any feature work, debugging, or queued item execution
- **Downstream**: Handoff documents feed into next session via resumption prompts; `cw done` frees the session for new queue items
- **Complements**: `/handoff` for abnormal endings (context exhaustion, debug forks)

## Installation

```bash
./install.sh session-done >> ./CLAUDE.md
```
