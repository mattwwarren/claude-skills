# wiki-lesson

Capture mid-session lessons silently to a configurable inbox — without interrupting the task.

> Wiki system design inspired by Scott Cipriano (@scottpcipriano).

## What It Does

When something unexpected happens — a tool behaves unexpectedly, a workaround is needed, an assumption turns out wrong — invoke `/wiki-lesson` to capture it. The skill writes the lesson directly to an inbox file without asking for confirmation. The inbox is processed later by `/wiki-lint` (separate plugin).

## When to Use

Write a lesson when ANY of these apply:

1. Something failed and the approach changed
2. A non-obvious workaround was needed
3. A tool behaves differently than its documentation says
4. A convention or constraint that would trip up future work

## Configuration

| Variable | Default | Notes |
|----------|---------|-------|
| `WIKI_INBOX_PATH` | `wiki/local/inbox/` | Relative to project root. Gitignored by default. |
| `WIKI_TRACKED_INBOX_PATH` | `wiki/inbox/` | For generic/public-safe lessons only. |

Set in your environment or CLAUDE.md. Defaults work without any configuration.

## Usage

```text
/wiki-lesson
```

Invoked silently — Claude identifies the lesson, writes it, and resumes the task.

## Installation

```text
/plugin install knowledge-base@claude-skills
```
