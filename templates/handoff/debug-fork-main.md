---
type: debug-fork-main
created: YYYY-MM-DD HH:MM UTC
reason: debug-fork
---

# Session Handoff (Main Track): [Title]

**Date**: YYYY-MM-DD HH:MM UTC
**Status**: in_progress
**Plan**: [/absolute/path/to/plan/main.md]
**Related debug track**: [/absolute/path/to/.handoffs/handoff-debug-YYYY-MM-DD-HHMM.md]

## Summary

[1-3 sentences describing what was accomplished before the debug fork.]

## Progress

- **Overall**: [X]% complete
- **Todos completed this session**: [N]
- **Total completed**: [N]/[M]
- **Current phase**: Phase [N]: [Name]

## Issue Being Deferred

**What**: [Brief description of the stuck issue]
**Why deferred**: [N] debugging attempts failed; continuing would consume remaining context
**Impact**: [What functionality is affected by skipping this issue]
**Tracked in**: [GitHub issue number, or "debug track handoff"]

## Critical Context

### Decisions Made
- [Decision and rationale]

### Work Completed Before Fork
- [Completed item 1]
- [Completed item 2]

## Remaining Tasks (Skip Deferred Issue)

- [ ] [Task 1 -- proceed without the stuck feature]
- [ ] [Task 2]
- [ ] [Task 3]
- [ ] [Task 4]
- [ ] [Task 5]

## Resumption Prompt

```
Continuing work on [task name] per plan at [/absolute/path/to/plan/main.md].

IMPORTANT: Skip [brief description of stuck issue]. That issue is being investigated
separately in a debug track handoff at [/absolute/path/to/debug-handoff].

Session context:
- Phase: Phase [N]: [Name]
- Progress: [X]% complete
- [Essential context item 1]
- [Essential context item 2]

Previous handoff: [/absolute/path/to/.handoffs/handoff-main-YYYY-MM-DD-HHMM.md]

Start by [specific first action, skipping the deferred issue].
```
