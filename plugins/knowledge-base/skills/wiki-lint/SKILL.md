---
name: wiki-lint
description: Organize wiki/inbox/ into wiki pages, check quality, compact index, rotate log. Run daily via cron.
model: sonnet
---

# /wiki-lint

> Wiki system design inspired by Scott Cipriano (@scottpcipriano).

Maintenance skill for the wiki system. Reads inbox files, routes them into wiki pages, and runs quality checks across the whole wiki. Companion to `/wiki-lesson` (mid-session capture) and `/wiki-ingest` (bulk transcript processing) — those two producers fill the inboxes; this skill curates them.

## Configuration

| Variable | Default | Notes |
|----------|---------|-------|
| `WIKI_INBOX_PATH` | `wiki/local/inbox/` | Relative to project root. Gitignored by default. |
| `WIKI_TRACKED_INBOX_PATH` | `wiki/inbox/` | For generic/public-safe content only. |
| `WIKI_ROOT` | `wiki/` | Root of the wiki tree. Index, log, and per-section pages live here. |

## Path discipline (REQUIRED)

Wiki file WRITES must use real filesystem paths relative to `cwd` (e.g., `wiki/...`). Never write through `~/.claude/...` paths — Claude Code's sensitive-file detector silently blocks Edit/Write on that subtree regardless of permission settings.

Reads from session transcript files (`.jsonl` under `~/.claude/projects/*/`) are fine — reads are not blocked.

## Usage

```text
/wiki-lint           — process inbox + run all checks
/wiki-lint --full    — same as above (explicit)
/wiki-lint --inbox   — only process inbox files, skip checks
/wiki-lint --check   — only run quality checks, skip inbox
```

## Phase 1: Process inbox files

Process both inboxes: `${WIKI_TRACKED_INBOX_PATH}` (tracked shared/runtime-safe scope) and `${WIKI_INBOX_PATH}` (gitignored project/employer/private scope). Files routed to their matching half:

- `${WIKI_INBOX_PATH}` entries → `${WIKI_ROOT}local/lessons/`, `${WIKI_ROOT}local/<page>.md`
- `${WIKI_TRACKED_INBOX_PATH}` entries → `${WIKI_ROOT}lessons/` (create if missing), `${WIKI_ROOT}<page>.md`

If a `${WIKI_TRACKED_INBOX_PATH}` item contains project/employer/private scope material, MOVE it to `${WIKI_INBOX_PATH}` before processing. This includes client names, employer names, internal repo context, PHI, stakeholder expectations, product goals, people/roles, business rules, or user-private feedback. This is the final tripwire against non-portable context leaking to tracked files.

For each file in both inboxes:

### 1a. Read inbox file and current wiki

- Read the inbox file's frontmatter (`source`, `date`, `topic`, `repo`)
- **Sanitize `repo` field**: must be kebab-case only (`^[a-z0-9-]+$`). Reject if it contains slashes, dots, or other characters — this prevents path traversal.
- Read existing relevant wiki pages to check for duplicates

### 1b. Decide destination

No routing table — use judgment based on:
- `topic` and `repo` frontmatter hints
- Content similarity to existing pages
- The concrete noun test: "X is a ___" — if you can fill the blank, it might deserve its own page

Common destinations:
- Lessons/gotchas → `${WIKI_ROOT}lessons/<topic>.md`
- Tool behavior → `${WIKI_ROOT}tools.md` or `${WIKI_ROOT}lessons/<tool>.md`
- Runtime-specific behavior that is safe to track → existing runtime pages such as `${WIKI_ROOT}claude-code.md` or another tracked runtime page
- Project/employer/product context → local pages only (`${WIKI_ROOT}local/<topic>.md`, `${WIKI_ROOT}local/lessons/<topic>.md`)
- Auto-memory files → route based on content (same judgment)

### 1c. Deduplication (before merging)

**Tier 1 (automatic)**: Exact or near-exact string match with existing content → skip silently.

**Tier 2 (Claude judgment)**: Semantic overlap with existing content → skip silently.

No `[possible-dup]` tags — make a definitive decision.

### 1d. Contradiction check

If new fact contradicts an existing fact, keep both:
```markdown
- Old claim [session:abc, 2026-03-01]
- New claim [session:def, 2026-04-15] **[CONTRADICTION]**
```

Never silently overwrite existing content.

### 1e. Merge into destination (safety order — never skip steps)

1. **Merge** content into destination page (append to appropriate section, or create new page)
2. **Verify** merge succeeded: Read the destination page and confirm the source tag is present
3. **Update** `${WIKI_ROOT}index.md`: remove Inbox entry, add/update destination page entry
4. **Delete** inbox file

Never delete the inbox file before confirming the merge. If interrupted between steps 1-3, content is duplicated (inbox + destination) but not lost — dedup handles it on next run.

### 1f. New page creation

When inbox content doesn't fit any existing page, create `${WIKI_ROOT}<path>.md`:

```markdown
---
title: Page Title
type: lesson | concept | entity | synthesis | summary
updated: YYYY-MM-DD
---

# Page Title

Content with inline source tags.
```

Add to `${WIKI_ROOT}index.md` under the appropriate section.

### 1g. Auto-memory files

Move any files in `${WIKI_ROOT}auto-memory/` (other than `MEMORY.md`) to `${WIKI_TRACKED_INBOX_PATH}` and process them the same way as inbox files.

## Phase 2: Quality checks

Run all 14 checks. Flag issues in output — do not auto-fix except where noted.

### Check 1: Contradictions
Find lines containing `**[CONTRADICTION]**`. Report count and locations.

### Check 2: Stale claims
Staleness thresholds by content type:
- Code behavior, file paths, API details: 90 days
- Tool configuration, CLI syntax: 90 days
- Business context (team, strategy): 180 days
- People (roles, responsibilities): 180 days
- Architecture, design decisions: 1 year
- Invariants/lessons: never stale

Report facts past threshold as suggestions to re-verify. Don't delete.

### Check 3: Orphan pages
Pages referenced in `index.md` that don't exist on disk. Report as errors.

### Check 4: Missing index entries
Pages that exist in `${WIKI_ROOT}` but aren't in `index.md`. Report as warnings.

### Check 5: Broken cross-links
Scan all `.md` files for `[text](path)` links. Check each `path` resolves. Report broken links.

### Check 6: Oversized pages
Pages >500 lines → suggest splitting. Auto-split if `--full` and content is clearly separable into a sub-topic (write to new page, update cross-links).

### Check 7: Missing source tags
Lines that look like facts (start with `-`, contain specific claims) but have no `[source:...]` tag. Report as warnings.

### Check 8: Duplicate check
Scan for obvious duplicate facts across pages (same file path, same error code, same proper noun + claim). Report as `[possible-dup]` candidates for human review.

### Check 9: Index size

Count lines in `${WIKI_ROOT}index.md` (or `wiki/index.md` if `WIKI_ROOT` is unset).

- 180-199 lines: warn. If running with `--full`, perform consolidation (see below) before Phase 3 rebuilds the index.
- 200 or more lines: `index_builder.py` raises `IndexTooLargeError` when invoked in Phase 3 (the threshold is `>= 200`, not `> 200`). Perform consolidation first, then re-run `/wiki-lint` from the top.

**Consolidation** (performed by the skill, not the script): replace per-page entries in a directory with a single directory entry — `- [Lessons](lessons/) — N pages (topic1, topic2, ...)`. Individual pages still exist on disk; they're just not listed individually in the index. The script regenerates the index from the resulting page-list state.

### Check 10: Log rotation
If `wiki/local/log.md` >500 lines, move entries older than 90 days to `wiki/local/.archive/log-YYYY-MM.md`. Update `wiki/local/log.md` to contain only recent entries.

### Check 11: Heartbeat staleness
Check `wiki/local/log.md` for the most recent `heartbeat` entry. If the last heartbeat is older than the expected refresh window (typically >25 hours), warn: "Ingest pipeline may not be running."

### Check 12: Repo docs flag
Scan inbox/new wiki pages for facts flagged as `[consider-pr-to: <repo>]`. Report them as a list for the user to action.

### Check 13: Inbox age
Inbox files older than 7 days → warn that lint hasn't run recently (or processed correctly).

### Check 14: Secret scan
Run the bundled secret filter against each wiki page. Report if any secrets found (should not happen — defense-in-depth catch).

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/secret_filter.py < <page>  # installed
python3 plugins/knowledge-base/scripts/secret_filter.py < <page> # repo-checkout fallback
```

## Phase 3: Rebuild index

After all inbox processing and checks, regenerate `${WIKI_ROOT}index.md` from disk:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/index_builder.py ${WIKI_ROOT}  # installed
python3 plugins/knowledge-base/scripts/index_builder.py ${WIKI_ROOT} # repo-checkout fallback
```

The helper is stdlib-only and deterministic — running it twice with no other changes produces an identical file.

## Phase 4: Log

This phase runs regardless of invocation mode (`--full`, `--inbox`, or `--check`). It has two independent steps.

### Step 4a: Lint summary (only when processing happened)

If Phase 1 actually processed at least one inbox file (N > 0), append a summary entry to `wiki/local/log.md`:

```markdown
## [YYYY-MM-DD] lint | Full lint run
Inbox processed: N files → M pages updated, K new pages
Issues: X contradictions, Y stale, Z orphans
Index: N lines
```

Skip Step 4a entirely when no inbox files were processed (the heartbeat in Step 4b is the aliveness signal in that case).

### Step 4b: Heartbeat (conditional on today's date)

Scan `wiki/local/log.md` for an existing line matching `## [<today's date>] heartbeat` (the `heartbeat` tag must match — do not match the date alone, because a same-day lint summary line also contains today's date and would cause a false skip). If no such line exists, append:

```markdown
## [YYYY-MM-DD] heartbeat | Lint run — nothing to process
```

If today's heartbeat line is already present, skip the append. This keeps same-day re-runs (with no new inbox input) as true zero-write no-ops while still giving Check 11's staleness detector one liveness signal per day.

wiki-lint writes to the same `wiki/local/log.md` as wiki-lesson and wiki-ingest, so heartbeat staleness checks see all producer activity in one place.

## Index file format

`${WIKI_ROOT}index.md` is regenerated from disk by `index_builder.py`. Its shape:

- Title line: `# Knowledge Base Index`
- One HTML comment declaring the 200-line hard limit (the index is loaded at session start)
- Root-level pages first, without a section header: `- [Title](page.md)` per line
- One `## <Title>` section per subdirectory, alphabetical order, listing each page as `- [Title](<dir>/page.md)`
- A trailing `## Inbox` section listing inbox files, or `<!-- Empty — wiki-lint is up to date. -->` if empty

The helper skips `index.md` and `log.md` at any depth (these names are reserved for system files this script manages; user pages named `index.md` or `log.md` anywhere in the wiki tree will also be skipped silently — name your pages differently). It also skips the `.archive/` and `auto-memory/` trees. If a regeneration would emit 200 or more lines, `IndexTooLargeError` is raised and the operator must consolidate (Check 9).

## Idempotency

Running `/wiki-lint` twice in a row with no new input is a safe no-op:

1. Tier 1 exact-match dedup short-circuits already-merged content.
2. Inbox files are deleted only after a successful merge (Phase 1e), so a second run finds an empty inbox.
3. `index_builder.py` regenerates `index.md` deterministically — identical input produces identical output.
4. Both log writes are guarded: the lint summary in Step 4a only fires when inbox processing produced changes, and the heartbeat in Step 4b only fires on the first invocation of each calendar day. A same-day re-run with no new inbox files produces zero writes anywhere on disk.
