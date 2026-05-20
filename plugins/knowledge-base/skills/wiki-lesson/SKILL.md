---
name: wiki-lesson
description: Capture a mid-session lesson to wiki/inbox/ without interrupting the task. Silent mode — writes directly without confirmation.
model: haiku
---

# /wiki-lesson

> Wiki system design inspired by Scott Cipriano (@scottpcipriano).

Capture a lesson learned during this session to `wiki/inbox/` for later processing by `/wiki-lint`.

**Silent mode**: writes directly to inbox without asking for confirmation. The inbox model makes this safe — wiki-lint deduplicates and validates before anything reaches a wiki page.

## Configuration

Set `WIKI_INBOX_PATH` in your environment or CLAUDE.md to control where lessons land:

| Variable | Default | Notes |
|----------|---------|-------|
| `WIKI_INBOX_PATH` | `wiki/local/inbox/` | Relative to project root. Gitignored by default. |
| `WIKI_TRACKED_INBOX_PATH` | `wiki/inbox/` | For generic/public-safe lessons only. |

If neither variable is set, the skill uses the defaults shown above. The default `wiki/local/` tree is gitignored — safe for project-private and employer-specific context.

**Path discipline**: Always write through real filesystem paths relative to `cwd`. Never write to `~/.claude/...` — Claude Code's sensitive-file detector silently blocks writes to that subtree regardless of permission settings.

## Trigger criteria (from CLAUDE.md)

Write a lesson when ANY of these apply:
1. Something failed and the approach changed
2. A non-obvious workaround was needed
3. A tool behaves differently than its documentation says
4. A convention or constraint that would trip up future work

## What NOT to capture
- Routine errors (typos, syntax mistakes)
- Documented behavior
- Point-in-time metrics

## Steps

1. **Identify the lesson** — What is the core fact? One sentence if possible.

2. **Determine the topic** — 3-6 word kebab-case description for the filename.

3. **Write to inbox** — Routing:
   - Client/employer/internal-repo/PHI context → `${WIKI_INBOX_PATH}/lesson-<description>-<YYYY-MM-DD>.md` (gitignored; default: `wiki/local/inbox/`)
   - Generic tooling/CLI/Claude-Code-infra only → `${WIKI_TRACKED_INBOX_PATH}/lesson-<description>-<YYYY-MM-DD>.md` (tracked; default: `wiki/inbox/`)
   - When in doubt, file local.

```markdown
---
source: session:<first-8-chars-of-session-id>
date: <YYYY-MM-DD>
topic: <topic-hint>
---

<Lesson text. Each discrete fact gets its own bullet.>
- Fact one [session:<id>, <date>]
- Fact two [session:<id>, <date>]
```

4. **Update index** —
   - Local lesson (default): no tracked index update. Entry will be added to `wiki/local/` pages by `/wiki-lint`.
   - Generic lesson: add under `## Generic lessons` in `wiki/index.md (relative to project root)`.

5. **Append to log** — `wiki/local/log.md` (relative to project root):
```
## [<YYYY-MM-DD>] lesson | <brief description>
Added: ${WIKI_INBOX_PATH}/lesson-<description>-<date>.md
```

## Getting the session ID

The session ID appears in the active session's transcript. In Claude Code, check the value of `CLAUDE_SESSION_ID` if available, or look for the session's `.jsonl` transcript file in your project's Claude directory. Use the first 8 characters of the session ID (the hex prefix before the first `-`).

## Secret redaction

Before writing, scan the lesson content for secrets. Never write:
- API keys (`sk-ant-`, `sk-`, `ghp_`, etc.)
- Tokens, passwords, credentials
- Long bare alphanumeric strings (30+ chars)

Replace with `[REDACTED]` if found.

## After writing

Resume the task. Do not interrupt flow to announce the lesson was written — just continue.
