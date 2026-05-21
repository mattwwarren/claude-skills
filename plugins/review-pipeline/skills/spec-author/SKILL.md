---
name: spec-author
description: Author ticket-shaped implementation specs that round-trip cleanly through /auto-dev. Use when starting from a Linear ticket, GitHub issue, or freeform description and you need a spec doc with summary, scope-tier, risk-tag, acceptance criteria, target files, test plan, and definition-of-done. Triggers on "spec-author", "write a spec for", "/spec-author".
model: sonnet
---

# /spec-author

Produce a spec doc in the shape `/auto-dev` expects. The output is a single markdown file with a fixed schema — no divergent prose, no missing fields, no implicit assumptions that would trip auto-dev's Step 1c ambiguity scan.

**Arguments:** "$ARGUMENTS"

## When to use

- You have a ticket (Linear, GitHub Issue) or a freeform description and want it implemented by `/auto-dev`
- The ticket body is too thin to act as its own plan (no file paths, no scope estimate, no risk read)
- You want the spec captured on the ticket or in a file BEFORE work starts, so `/spec-author` is also the first thing the spec-reviewer (#2) and risk-tier gate consume

## When NOT to use

- The ticket already has a complete plan in its description (auto-dev's Step 1a will auto-skip plan approval). Run `/auto-dev` directly.
- Pure throwaway prototyping where the spec discipline is overkill.
- Bug reproductions that need debugging before they can be specced — use the debug skill first, then spec the fix.

## Soft dependency: superpowers:brainstorming

For the divergent / exploratory phase, this skill calls `superpowers:brainstorming` when:
- The input is freeform (no ticket structure), AND
- The shape of the work is unclear (multiple plausible interpretations of "done")

The brainstorming skill is **soft** — if it's not installed, skip the divergent phase and proceed directly with a single-interpretation spec. Note the degraded mode in the spec body under `## Open questions`.

The plugin manifest schema does not currently support a formal `dependencies` field, so this dependency lives in prose. Install `superpowers` separately if you want the divergent phase.

## Input intake

Parse `$ARGUMENTS`:

| Input | Example | Source |
|---|---|---|
| Linear ID | `GEN-1234` | `get_issue` + `list_comments` via Linear MCP |
| GitHub issue | `#1`, `owner/repo#1` | `gh issue view <n> --json title,body,comments,labels` |
| Freeform | any text without ID pattern | use as-is, mark `plan_source: "freeform"` |
| Empty | _(nothing)_ | ASK the user for a description; do not invent one |

If both a Linear ID and an existing partial plan exist on the ticket, extract the partial and extend it — do not overwrite. The author of the ticket already made decisions you should honor.

## Schema (required output shape)

The output is a markdown file at the path the caller specifies (default: `specs/<slug>-<date>.md`) with YAML frontmatter plus body sections. Every field below is required unless marked optional.

### Frontmatter

```yaml
---
spec_version: 1
ticket_id: <GEN-1234 | gh:owner/repo#1 | freeform>
title: <one-line summary, <80 chars>
scope_tier: small | large
risk_tag: safe | sensitive | dangerous
plan_source: linear | github | freeform | partial-extension
author: <human or skill name>
date: YYYY-MM-DD
---
```

**`scope_tier` rules** (mirror `/auto-dev` Stage 1d):
- `small`: ≤10 files AND ≤500 lines AND no forbidden-area touches
- `large`: anything else
- If uncertain, default `large`. Auto-dev will not complain about over-classification; under-classification causes auto-merge of work that should have gated.

**`risk_tag` rules** (mirror `/auto-dev` issue #2 — risk-tier):
- `safe`: docs, tests, isolated features, non-shared utility code
- `sensitive`: auth, billing, migrations, secrets handling, multi-tenant data paths, shared bases with 3+ consumers, CI/CD config
- `dangerous`: anything `sensitive` PLUS destructive defaults, irreversible schema changes, cross-org data joins, production-write side effects

When in doubt, escalate one level. The spec-reviewer (#2) validates this; auto-dev's risk gate will force a human checkpoint on sensitive/dangerous regardless of scope.

### Body sections (in this order, exactly these headings)

```markdown
## Summary

One paragraph. What is changing and why. No file paths here — that's `## Target files`.

## Acceptance criteria

- [ ] Testable criterion 1
- [ ] Testable criterion 2
- [ ] ...

Each criterion MUST be observable from outside the change (a test, a CLI output, a UI state). "Code is clean" is not an acceptance criterion. "`uv run ruff check` exits 0" is.

## Target files

| Path | Change type | Est. lines |
|---|---|---|
| `path/to/file.py` | new \| edit \| delete | ~50 |
| ... | ... | ... |

Total: N files, ~M lines. Must match `scope_tier` classification.

## Test plan

Phase 1 (before implementation):
- Test file: `tests/test_foo.py`
- New tests to add: list them with one-line descriptions of what they assert
- Must FAIL before Phase 2 starts (red phase)

Phase 2 (implementation):
- Re-run Phase 1 tests — must PASS
- Quality gates: `<project-specific lint+typecheck+test commands>`

## Definition of done

- [ ] All acceptance criteria checked
- [ ] All Phase 1 tests passing
- [ ] Quality gates clean
- [ ] No debug artifacts (`print`, `breakpoint`, `pdb`)
- [ ] Spec posted to ticket (if Linear/GitHub) as a comment
- [ ] (project-specific) ...

## Out of scope

Explicit non-goals. Anything a reasonable reader might assume is included but isn't. This section pre-empts auto-dev's ambiguity scan.

## Decisions and assumptions

For every interpretive choice made while authoring this spec:
- **Decision**: <what>
- **Reason**: <why this and not the alternative>
- **Reversible**: yes | no — can we change this mid-implementation without rework?

## Open questions

Things that genuinely need a human answer before implementation. If non-empty, this spec is NOT ready for `/auto-dev` — resolve first.

If empty, write `NONE`.
```

## Generation steps

### Step 1: Intake and parse

Fetch the source per the intake table above. If freeform input lacks shape, optionally invoke `superpowers:brainstorming` for the divergent phase (see soft-dep section). Capture the brainstorming output as raw context — do NOT include it verbatim in the spec.

### Step 2: Pattern scan (required before proposing target files)

Before listing target files, grep the repo for sibling patterns. For each new abstraction the spec proposes (new endpoint, new model, new module, new UI component), the spec MUST record one `Patterns Found` decision in `## Decisions and assumptions`:

```
- Decision: <new thing being added>
  Reason: searched for <queries>, found <results>, chose USE_EXISTING / EXTEND_EXISTING / NEW_PATTERN because <justification>
  Reversible: <yes | no>
```

If the spec adds no new abstraction (pure bug fix, copy edit, parameter tweak), skip this requirement and note `N/A — no new abstraction proposed` in `## Decisions and assumptions`.

This step exists because `/auto-dev`'s Plan agent will fail loudly if a plan proposes a new pattern without grep-evidence that no sibling exists. Catching it here saves a fix-loop cycle.

### Step 3: Scope and risk classification

Count target files and estimated lines. Classify `scope_tier` per the rules above. Inspect target paths against the risk patterns (auth, billing, migrations, secrets, multi-tenant, shared bases, CI/CD) and assign `risk_tag`. When uncertain, escalate one level.

### Step 4: Write acceptance criteria from observable behavior

For each acceptance criterion: ask "what command, test, or visible state would prove this is done?" If you can't answer, the criterion is too vague — rewrite it.

### Step 5: Author the spec file

Write to `specs/<slug>-<date>.md` (or the caller-specified path). Use the schema above verbatim — section headings, frontmatter fields, table columns. Auto-dev's Step 1a key-section detection ("Plan", "Implementation Plan", "Approach", or file-paths-with-changes) will recognize this shape.

### Step 6: Round-trip validation

Before declaring done, mentally walk the spec through auto-dev's Stage 1:

1. Step 1a — does it look like a plan? (Has file paths? Has phases? Has scope estimate?) → YES
2. Step 1c — would the ambiguity scan find anything? (Are all interpretive choices captured under `## Decisions and assumptions`? Is `## Out of scope` populated?) → should return `NO_AMBIGUITIES`
3. Step 1d — is `scope_tier` honest given target files? → YES
4. If `## Open questions` is non-empty → the spec is NOT ready; flag this in the closing report

If all four pass, the spec round-trips. If any fail, fix before handing off.

### Step 7: Post the spec (optional)

If the source was a Linear or GitHub ticket, offer to post the spec as a comment on the ticket. This makes the spec the canonical plan auto-dev will find in Step 1a, skipping the plan-generation step entirely.

```bash
# Linear (via MCP)
create_comment <issue-id> <spec-markdown>

# GitHub
gh issue comment <number> --body-file <spec-path>
```

## Sample output

A complete sample spec for a small, safe ticket:

```markdown
---
spec_version: 1
ticket_id: gh:mattwwarren/claude-skills#42
title: Add --dry-run flag to /wiki-ingest
scope_tier: small
risk_tag: safe
plan_source: github
author: spec-author
date: 2026-05-21
---

## Summary

`/wiki-ingest` currently writes inbox files unconditionally. Add a `--dry-run`
flag that prints what would be written without touching the filesystem.
Lets users preview an ingest before committing.

## Acceptance criteria

- [ ] `/wiki-ingest --dry-run <transcript>` exits 0 without writing any files
- [ ] Dry-run output lists destination paths and fact counts
- [ ] Existing (non-dry-run) behavior unchanged — confirmed by existing tests
- [ ] `processed_tracker` is NOT updated during dry-run

## Target files

| Path | Change type | Est. lines |
|---|---|---|
| `plugins/knowledge-base/skills/wiki-ingest/SKILL.md` | edit | ~20 |
| `plugins/knowledge-base/scripts/transcript_reader.py` | edit | ~15 |
| `tests/wiki/test_wiki_ingest_dry_run.py` | new | ~40 |

Total: 3 files, ~75 lines.

## Test plan

Phase 1 (before implementation):
- New test file `tests/wiki/test_wiki_ingest_dry_run.py` asserting:
  - dry-run on a sample transcript writes no files to inbox path
  - dry-run output contains expected destination path and fact count
  - tracker file is not modified after dry-run
- All three must FAIL before Phase 2.

Phase 2:
- Implement `--dry-run` propagation through wiki-ingest steps.
- Re-run Phase 1 tests: all PASS.
- Quality gates: `uv run ruff check`, `uv run pytest tests/wiki/`.

## Definition of done

- [ ] All acceptance criteria checked
- [ ] Phase 1 tests passing
- [ ] `uv run ruff check` clean
- [ ] `uv run pytest tests/wiki/` 100% pass
- [ ] No debug artifacts
- [ ] Spec posted to GH issue #42 as a comment

## Out of scope

- Dry-run for `/wiki-lint` (separate ticket if wanted)
- Verbose / dry-run-with-diff output (could be a follow-up)
- Refactoring the inbox write path (current shape is fine for this change)

## Decisions and assumptions

- **Decision**: Implement `--dry-run` as a CLI flag, not a config variable
  **Reason**: matches existing `--strict`, `--batch`, `--resume` flag pattern in wiki-ingest
  **Reversible**: yes

- **Decision**: Dry-run skips `processed_tracker.update_size()`
  **Reason**: tracker mutation is a write side-effect; dry-run is read-only by promise
  **Reversible**: yes

- N/A — no new abstraction proposed (extending existing CLI surface)

## Open questions

NONE
```

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Auto-dev's Step 1c keeps surfacing ambiguities on this spec | `## Out of scope` is thin or `## Decisions and assumptions` is missing the interpretive choices | Re-author with explicit non-goals and decisions |
| Auto-dev classifies the spec as Large when you wrote Small | Your line/file estimate was off, OR you missed a forbidden-area touch | Re-count, re-classify, escalate `risk_tag` if a forbidden area is actually touched |
| Spec-reviewer (#2) MUST_FIXes the risk tag | You under-classified | Bump risk one level; do NOT argue with the reviewer |
| `## Acceptance criteria` items can't be turned into tests in Phase 1 | Criteria are vague or test the wrong layer | Rewrite as observable behavior — a test, a CLI output, a UI state |

## Related skills

- **[auto-dev](../auto-dev/)** — primary consumer of this spec
- **superpowers:brainstorming** — soft dependency for divergent phase on freeform input
- **spec-reviewer** (#2, not yet shipped) — validates this spec's scope/risk honesty before any code work
