# Handoff Skill

Generate structured handoff documents when a Claude Code session ends abnormally, ensuring zero context loss across session boundaries.

## Why Handoffs Matter

Claude Code sessions have finite context windows. When a session ends -- whether from context exhaustion, a debugging rabbit hole, or scope creep -- work-in-progress can be lost if not captured properly. The handoff skill generates self-contained documents that let the next session resume exactly where the previous one left off.

## Three Scenarios

### 1. Context Exhaustion

You are 80%+ through your context window with work still remaining.

```
/handoff --reason context
```

Generates a single handoff with completed work, in-progress state, and a resumption prompt. The next session picks up immediately without re-reading the entire codebase.

### 2. Debug Fork

You have tried two or more approaches to fix a bug and none have worked. Continuing to debug will consume the rest of the session.

```
/handoff --reason debug-fork
```

Generates **two** documents:
- **Main track**: Continue the feature work, skip the stuck issue
- **Debug track**: Fresh investigation with all failed attempts documented

This prevents the next session from repeating the same failed approaches.

### 3. Scope Creep

A "quick fix" turned into a larger refactoring effort that exceeds the original task.

```
/handoff --reason scope
```

Generates a handoff focused on the original must-do items, with expanded scope items deferred as separate tasks.

## Installation

Append the skill's system prompt to your project's CLAUDE.md:

```bash
./install.sh handoff >> ./CLAUDE.md
```

Or copy the contents of `skills/handoff/SKILL.md` into your CLAUDE.md manually.

## Integration with Plans

The handoff skill works with plan-based workflows:

- Handoffs reference the active plan file by absolute path
- Progress is reported as overall percentage and current phase
- The resumption prompt includes the plan path so the next session loads it immediately
- Phase-level handoffs from the plan executor use the same templates

## Templates

Templates live in `templates/handoff/`. Each is a fill-in-the-blanks markdown file:

| Template | When Used |
|----------|-----------|
| `session-handoff.md` | Context exhaustion or scope creep |
| `debug-fork-main.md` | Main track of a debug fork |
| `debug-fork-debug.md` | Debug investigation track |

The skill fills these templates automatically. You can also use them manually for ad-hoc handoffs.

## Example Output (Context Exhaustion)

```markdown
---
type: session-handoff
created: 2026-02-15 14:30 UTC
reason: context
---

# Session Handoff: User Service Authentication

**Date**: 2026-02-15 14:30 UTC
**Status**: in_progress
**Plan**: /home/dev/project/.claude/plans/user-auth/main.md

## Summary

Implemented JWT token generation and validation. Completed login endpoint
and middleware integration. Refresh token rotation is partially implemented.

## Progress

- **Overall**: 65% complete
- **Todos completed this session**: 4
- **Total completed**: 8/12
- **Current phase**: Phase 2: Token Management

## Critical Context

### Decisions Made
- Used RS256 for JWT signing (security requirement from spec)
- Token expiry set to 15 minutes with 7-day refresh window

### Approaches Rejected
- HS256 signing - rejected due to shared secret risk in microservices

## Next Actions

- [ ] Complete refresh token rotation logic in auth_service.py
- [ ] Add token revocation endpoint
- [ ] Write integration tests for token refresh flow

## Resumption Prompt

\```
Continuing work on user authentication per plan at
/home/dev/project/.claude/plans/user-auth/main.md.

Session context:
- Phase: Phase 2: Token Management
- Progress: 65% complete
- JWT generation and login endpoint are complete
- Refresh token rotation is partially implemented in auth_service.py

Previous handoff: /home/dev/project/.handoffs/handoff-2026-02-15-1430.md

Start by completing the refresh token rotation logic in
/home/dev/project/services/user-service/app/auth_service.py.
\```
```

## Relationship to /session-done

| Situation | Use |
|-----------|-----|
| Work complete or at a good stopping point | `/session-done` |
| Context window exhausted (80%+) | `/handoff --reason context` |
| Stuck debugging after 2+ attempts | `/handoff --reason debug-fork` |
| Scope expanded beyond original task | `/handoff --reason scope` |

Both commands generate handoff documents, but `/handoff` is optimized for constrained or abnormal endings where preserving state is critical.
