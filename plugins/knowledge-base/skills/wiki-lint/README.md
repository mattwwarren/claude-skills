# wiki-lint

Promote inbox items into wiki pages, run quality checks, rebuild the index, and rotate the log.

> Wiki system design inspired by Scott Cipriano (@scottpcipriano).

## What It Does

`/wiki-lint` is the curator side of the wiki workflow. Where `/wiki-lesson` and `/wiki-ingest` deposit raw inbox files, wiki-lint promotes those entries into the right wiki pages, dedupes against existing content, flags contradictions, and runs 14 quality checks across the wiki tree. It then regenerates `index.md` from disk and appends a run summary (plus a heartbeat) to `log.md`.

## When to Use

- After a batch of `/wiki-lesson` or `/wiki-ingest` runs, to turn raw inbox entries into curated pages
- Periodic maintenance pass over an established wiki (orphan pages, stale claims, oversized pages, broken cross-links)
- Before a knowledge handoff, to ensure `index.md` and `log.md` reflect current state
- As a scheduled cron job. Expected cadence: once per day, typically early morning. Scheduling itself is handled by a separate plugin — see ADR 0003.

## Configuration

| Variable | Default | Notes |
|----------|---------|-------|
| `WIKI_INBOX_PATH` | `wiki/local/inbox/` | Relative to project root. Gitignored by default. |
| `WIKI_TRACKED_INBOX_PATH` | `wiki/inbox/` | For generic/public-safe content only. |
| `WIKI_ROOT` | `wiki/` | Root of the wiki tree. Index, log, and per-section pages live here. |

## Usage

```text
/wiki-lint           — process inbox + run all checks
/wiki-lint --full    — same as above (explicit)
/wiki-lint --inbox   — only process inbox files, skip checks
/wiki-lint --check   — only run quality checks, skip inbox
```

## Requirements

Python 3 must be available in PATH. Helpers are bundled under `${CLAUDE_PLUGIN_ROOT}/scripts/` (`index_builder.py`, `secret_filter.py`).

## Installation

```text
/plugin install knowledge-base@claude-skills
```

## Companion Skills

- `/wiki-lesson` — mid-session lesson capture (single entry, silent)
- `/wiki-ingest` — bulk transcript processing into the inbox

wiki-lint is the third leg: it organizes whatever those two producers deposit. Without it, inbox entries accumulate but never become wiki pages.
