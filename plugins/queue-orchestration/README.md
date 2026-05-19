# queue-orchestration

Skills for the `cw` CLI multi-session work queue.

## Skills

- **queue-plan** — Queue an approved plan for implementation. Picked up later by `/pull-and-execute`.
- **queue-debt** — Queue a tech-debt work item with optional priority for a dedicated debt session.
- **pull-and-execute** — Claim the next queue item, decompose it, spawn agent teams, review, complete.

## Install

```text
/plugin install queue-orchestration@claude-skills
```
