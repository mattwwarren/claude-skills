---
type: phase-handoff
phase: "Phase N: [Title]"
completed: YYYY-MM-DD HH:MM UTC
---

# Phase Complete: [Title]

## Summary

[What was accomplished in this phase]

## Tasks Completed

- [x] Task 1
- [x] Task 2

## Integration Results

```
pytest: X passed, 0 failed
ruff: 0 violations
mypy: 0 errors
```

## Agent Results

[Summary of work done by sub-agents, including which tasks each agent handled and any notable decisions made]

## Next Phase

Phase N+1: [Title]
- [ ] First task
- [ ] Second task

## Resumption Prompt

```
Continue executing plan at [path]

Last completed: Phase N: [Title]
Next: Phase N+1: [Title]
Integration checks: all passing

Start by reading the plan and executing Phase N+1.
```
