# session-management

Handoff generation, session wrap-up, and structured debug triage for Claude Code work sessions.

## Skills

- **handoff** — Generate self-contained handoff docs for abnormal session endings (context exhaustion, debug fork, scope creep). Ships templates under `skills/handoff/templates/`.
- **session-done** — Normal session wrap-up. Builds a handoff doc and signals `cw done`.
- **debug-triage** — Structured debugging with issue tracking, hypothesis confirmation, and pipeline handoff. Templates under `skills/debug-triage/templates/`.

## Install

```text
/plugin install session-management@claude-skills
```
