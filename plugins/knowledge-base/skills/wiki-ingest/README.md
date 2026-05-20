# wiki-ingest

Process session transcripts (or any source file) into the wiki inbox — in bulk, with secret filtering and processed-state tracking.

> Wiki system design inspired by Scott Cipriano (@scottpcipriano).

## What It Does

`/wiki-ingest` bulk-processes Claude Code session transcripts into inbox files ready for `/wiki-lint` to promote to wiki pages. It extracts the essential signal from `.jsonl` transcripts, strips secrets via regex filtering, and tracks which files have already been processed so reruns are safe and efficient. It is the batch complement to `/wiki-lesson` — where wiki-lesson captures a single lesson mid-session, wiki-ingest sweeps up everything after the fact.

## When to Use

- After a block of sessions, to sweep accumulated transcripts into the wiki inbox
- One-off ingestion of a specific transcript or source file
- Batch processing a large backlog (`--batch` mode)
- Resuming an interrupted batch run (`--batch --resume`)
- A scheduled cron job (scheduling is handled by a separate plugin — see ADR 0003)

## Configuration

| Variable | Default | Notes |
|----------|---------|-------|
| `WIKI_INBOX_PATH` | `wiki/local/inbox/` | Relative to project root. Gitignored by default. |
| `WIKI_TRACKED_INBOX_PATH` | `wiki/inbox/` | For generic/public-safe content only. |
| `WIKI_TRANSCRIPT_PATH` | `~/.claude/projects/*/` | Source location for session transcripts. Override to point at a different transcript directory. |

## Usage

```text
/wiki-ingest                     — process all unprocessed transcripts
/wiki-ingest <path>              — process a specific transcript or file
/wiki-ingest --batch             — batch mode: process multiple with progress logging
/wiki-ingest --batch --resume    — resume a previous batch run
/wiki-ingest --strict            — always append, never skip (ignore Tier 1 dedup)
```

## Example

Running the transcript reader + secret filter against a recent session transcript
(`python3 scripts/transcript_reader.py <transcript> | python3 scripts/secret_filter.py`):

```
[transcript_reader] Output: 104,000 chars from <session-id>.jsonl
[transcript_reader] WARNING: output exceeds 80,000 chars — wiki-ingest should use chunked processing

[USER] <redacted-command-caveat>...</redacted-command-caveat>

[USER] Port wiki-ingest skill following the same pattern as #4 (wiki-lesson, PR #14).
Source skill is from <author>'s global-claude repo; ensure attribution appears in
SKILL.md, README, and plugin.json. DO NOT bake any scheduling mechanism into the
SKILL.md — wiki-ingest is the content-processing skill; scheduling stays decoupled.

[ASSISTANT] I'll execute this plan systematically. Let me start with the branch setup
and reading all source files in parallel.
[TOOL:Bash] git fetch origin main && git merge origin/main && ...
[TOOL:Read] <redacted-path>/skills/wiki-ingest/SKILL.md
```

The output shape: one `[USER]`/`[ASSISTANT]`/`[TOOL:*]` block per message, noise
(progress, file-history-snapshots, system messages) stripped, secrets redacted.

## Requirements

Python 3 must be available in PATH. Scripts are bundled under `${CLAUDE_PLUGIN_ROOT}/scripts/`.

## Installation

```text
/plugin install knowledge-base@claude-skills
```

> **Note:** `/wiki-lint` (a separate plugin, not yet published) is required to promote inbox items to wiki pages. Without it, ingested facts accumulate in the inbox but are never organized into wiki pages.
