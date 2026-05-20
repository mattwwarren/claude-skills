---
name: wiki-ingest
description: Process session transcripts or other sources into wiki/inbox/ for organization by wiki-lint.
model: sonnet
---

# /wiki-ingest

> Wiki system design inspired by Scott Cipriano (@scottpcipriano).

Process unprocessed session transcripts (or a specific source file) into the wiki inbox. Uses Python helpers for transcript reading, secret filtering, and processed-state tracking. Companion to `/wiki-lesson` — where wiki-lesson captures single lessons mid-session, wiki-ingest processes transcripts in bulk after the fact.

## Usage

```
/wiki-ingest                    — process all unprocessed transcripts
/wiki-ingest <path>             — process a specific transcript or file
/wiki-ingest --batch            — batch mode: process multiple with progress logging
/wiki-ingest --batch --resume   — resume a previous batch run
/wiki-ingest --strict           — always append, never skip (ignore Tier 1 dedup)
```

## Configuration

| Variable | Default | Notes |
|----------|---------|-------|
| `WIKI_INBOX_PATH` | `wiki/local/inbox/` | Relative to project root. Gitignored by default. |
| `WIKI_TRACKED_INBOX_PATH` | `wiki/inbox/` | For generic/public-safe content only. |
| `WIKI_TRANSCRIPT_PATH` | `~/.claude/projects/*/` | Source location for session transcripts. Override to point at a different transcript directory. |

## Path discipline (REQUIRED)

Wiki file WRITES must use real filesystem paths relative to `cwd` (e.g., `wiki/...`). Never write through `~/.claude/...` paths — Claude Code's sensitive-file detector silently blocks Edit/Write on that subtree regardless of permission settings.

Reads from transcript files (`.jsonl`) are fine regardless of location — reads are not blocked.

## Steps

### 1. Find transcripts to process

Scripts are bundled at `${CLAUDE_PLUGIN_ROOT}/scripts/` when installed via the plugin marketplace. When running from a repo checkout, use repo-relative paths: `plugins/knowledge-base/scripts/`.

No CLI exists for `processed_tracker.py` — import it from Python (see Step 7). Its bundled location is `${CLAUDE_PLUGIN_ROOT}/scripts/processed_tracker.py` when installed, or `plugins/knowledge-base/scripts/processed_tracker.py` when running from a repo checkout.

Scan: `${WIKI_TRANSCRIPT_PATH}` (default: `~/.claude/projects/*/`) for `*.jsonl` files.

For each transcript:
- Check if processed: `ProcessedTracker.is_processed(path)`
- Check if grown: `ProcessedTracker.has_grown(path)` (reprocess if grown >10KB)

### 2. Extract essential content

```bash
# Installed path
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/transcript_reader.py <path> > /tmp/extracted.md

# Repo-checkout fallback
python3 plugins/knowledge-base/scripts/transcript_reader.py <path> > /tmp/extracted.md
```

Check stderr for reported output size. If >80K chars, use chunked processing (see below).

### 3. Filter secrets

```bash
# Installed path
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/secret_filter.py < /tmp/extracted.md > /tmp/clean.md

# Repo-checkout fallback
python3 plugins/knowledge-base/scripts/secret_filter.py < /tmp/extracted.md > /tmp/clean.md
```

### 4. Read current wiki state

Before extracting facts, read:
- `wiki/index.md` — understand existing pages
- Relevant existing wiki pages (for Tier 1 dedup)

### 5. Extract facts

Read `/tmp/clean.md`. For each discrete fact worth persisting:
- Is it already in a wiki page? (Tier 1 exact match — skip silently)
- Does it overlap semantically with existing content? (Tier 2 — skip silently)
- Is it a non-obvious workaround, gotcha, or decision? — capture it
- Is it a routine error, documented behavior, or point-in-time metric? — skip it

**Quality rules:**
- Every fact gets an inline source tag: `[session:<id>, YYYY-MM-DD]`
- Never persist secrets (filter already ran, but check again)
- Claims about files: verify with Read tool before tagging as Tier 1
- Unverifiable claims: tag as `[unverified]`
- Code behavior, file paths that existed at session time: verify still exist with `os.path.exists()`

### 6. Write to inbox

**Routing rule** (REQUIRED):
- If the fact names a client/employer/internal-repo/PHI context → write to `${WIKI_INBOX_PATH}` (default: `wiki/local/inbox/`, gitignored).
- Only generic tooling/CLI/Claude-Code-infra facts go to `${WIKI_TRACKED_INBOX_PATH}` (default: `wiki/inbox/`, tracked).
- When in doubt, file local. The tracked inbox is for content safe to publish.

Write one file per logical group of related facts:
`<destination>/ingest-<3-6-word-description>-<YYYY-MM-DD>.md`

```markdown
---
source: session:<8-char-id>
date: YYYY-MM-DD
topic: <topic-hint>
repo: <repo-name-if-applicable>
---

Facts here with inline source tags.
- Fact [session:<id>, YYYY-MM-DD]
```

**Zero-cost for empty sessions**: if no new facts found, write nothing.

### 7. Update processed tracker

```python
import sys
sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}/scripts")  # or "plugins/knowledge-base/scripts"
from processed_tracker import ProcessedTracker
tracker = ProcessedTracker(Path(".claude/.processed_wiki_transcripts"))
tracker.mark_as_processed(path)  # first time
tracker.update_size(path)        # after reprocessing a grown transcript
```

Always call `update_size` after reprocessing — omitting this causes an infinite reprocess loop.

### 8. Update index

- Files in `${WIKI_INBOX_PATH}` (local) → append to `wiki/local/log.md` only (no tracked index updates).
- Files in `${WIKI_TRACKED_INBOX_PATH}` (tracked) → add under `## Generic lessons` in `wiki/index.md`.

### 9. Append to log

Local/employer content: append to `wiki/local/log.md`.
Generic content: append to `wiki/local/log.md` AND (optionally) a brief line in the tracked generic notes — but default to local-only logging to minimize surface.

```markdown
## [YYYY-MM-DD] ingest | <brief description>
New inbox files: ${WIKI_TRACKED_INBOX_PATH}ingest-<name>.md  # or ${WIKI_INBOX_PATH} per routing rule above
```

Write `heartbeat` entry even if nothing processed:
```
## [YYYY-MM-DD] heartbeat | Ingest run — nothing to process
```

## Chunked processing (>80K chars)

When `transcript_reader.py` reports output >80K chars:

**Pass 1**: Split at line boundaries with 10K char overlap. Process each chunk independently into candidate facts. Overlap region provides context — extract facts only from the new region of each chunk.

**Pass 2**: Read ALL candidate facts from all chunks together. Deduplicate facts that appeared in overlap regions. Resolve contradictions (keep the later/corrected version). Write only final reconciled facts to inbox.

## Multi-repo scanning

Scan all project directories under `${WIKI_TRANSCRIPT_PATH}` (default: `~/.claude/projects/*/`).

Apply the **same routing rule as Step 6** regardless of which repo the learning came from: client/employer/internal-repo/PHI context → `${WIKI_INBOX_PATH}` (local, gitignored); generic tooling/CLI/Claude-Code-infra content → `${WIKI_TRACKED_INBOX_PATH}` (tracked). Tag the frontmatter with `repo: X` to retain provenance, but the inbox destination is determined by content classification, not source repo.

## Batch mode

In batch mode:
- Process up to 20 transcripts per session
- Log progress: `[N/total] processing <transcript>...`
- On interruption, the processed tracker preserves state — `--resume` picks up where it left off
- Process chronologically (oldest first)
