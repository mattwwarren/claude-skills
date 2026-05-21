---
name: spec-reviewer
description: Review a /spec-author-shaped spec doc for scope honesty, risk-tag accuracy, acceptance-criteria testability, and missing tiers — before any code is written. Triggers on "spec-reviewer", "review this spec", "/spec-reviewer".
model: sonnet
---

# /spec-reviewer

Validate a spec doc against the schema and heuristics defined by [`/spec-author`](../spec-author/SKILL.md) and [ADR 0004](../../../../docs/adr/0004-risk-tier-vocabulary.md). Output is MUST_FIX / SHOULD_FIX / OK on the spec, mirroring the code-review output shape.

**Arguments:** "$ARGUMENTS"

## When to use

- A spec author (or `/spec-author`) just produced a draft and you want to validate it before queuing the ticket for `/auto-dev`.
- `/auto-dev` is about to consume a spec extracted from a ticket and you want a pre-flight honesty check (this is the path `/auto-dev` Stage 1b.5 takes automatically — calling `/spec-reviewer` manually is for the iterative-authoring case).
- You inherited a spec from someone else and want a quick read on whether the tiers are honest before starting work.

## When NOT to use

- The spec is still a rough idea or bullet list — run `/spec-author` first to produce a structured doc, then review.
- You want to review *code*, not a spec — use `/review` for the implementation diff.
- You want to evaluate whether a ticket should exist at all (prioritization, deduplication) — this skill assumes the work is going to happen and is checking that the spec is honest about what the work is.

## Invocation

```
/spec-reviewer specs/foo-2026-05-21.md           # local file path
/spec-reviewer gh:owner/repo#42                  # spec is a comment on GH issue 42
/spec-reviewer GEN-1234                          # spec is a comment on Linear issue
/spec-reviewer specs/foo.md --mode tiers         # quick tier-only check (Mode 2)
```

## Input intake

Parse `$ARGUMENTS`:

| Input | Example | Source |
|---|---|---|
| File path | `specs/foo.md` | Read the file directly |
| GitHub issue | `gh:owner/repo#1`, `#1` (current repo) | `gh issue view <n> --json title,body,comments` — search description and comments for a spec block; the most recent spec-shaped comment wins |
| Linear ID | `GEN-1234` | `get_issue` + `list_comments` — same search rule |
| Empty | _(nothing)_ | ASK the user for a spec path or ticket ID; do not invent one |

If multiple specs exist on a ticket (e.g., re-authored after a fix loop), review the most recent one. Older specs are kept as history; only the latest is the active plan.

If the spec doc fails to parse (no frontmatter, no body sections, not markdown at all), return:

```
SPEC_MALFORMED — <one-line description of what's wrong>. Fix the shape before re-running review.
```

…and stop. Do not run the agent on a malformed input.

## Modes

The skill dispatches to the `spec-reviewer` agent in one of two modes:

### Mode 1: Full validation (default)

Runs all 8 checks defined in [`agents/spec-reviewer.md`](../../agents/spec-reviewer.md):

1. Schema completeness
2. Open questions block status
3. Scope tier honesty
4. Risk tag honesty (per ADR 0004 heuristics)
5. Acceptance criteria testability
6. Decisions and assumptions completeness
7. Out of scope vs Summary parity
8. Cross-ticket faithfulness (when a ticket is supplied)

### Mode 2: Tiers only (`--mode tiers`)

Runs only checks 3 and 4 (scope tier + risk tag). Fast path for when the caller wants a quick "are the tiers honest?" answer without paying for the full review.

## Output shape

Identical to the agent's output shape (see [`agents/spec-reviewer.md`](../../agents/spec-reviewer.md) §"Output format"). The skill surfaces the agent's output unchanged, with one wrapper:

- If `SPEC_OK` or `TIERS_OK`: print the clean signal, then a one-line summary of which checks ran.
- If any MUST_FIX: print the full findings, then a closing line `Spec has N MUST_FIX item(s). NOT ready for /auto-dev.`
- If only SHOULD_FIX: print the findings, then `Spec has N SHOULD_FIX item(s). Ready for /auto-dev with caveats.`

## Integration with `/auto-dev`

When `/auto-dev` runs Stage 1b.5, it spawns this skill's underlying agent automatically. The output is consumed as follows:

- `SPEC_OK` → proceed to Step 1c (ambiguity scan).
- `MUST_FIX` items → behavior depends on mode:
  - Interactive: present the findings via AskUserQuestion; ask whether to fix-and-re-review, override and proceed anyway, or abort.
  - Headless: EXIT `spec_blocked` with the findings in the structured output payload.
- `SHOULD_FIX` only → log the findings and proceed (small/large-scope independent — these are advisory).
- `SPEC_MALFORMED` → EXIT `blocked` with `blocker.reason: "spec_malformed"`; cannot proceed without a parseable spec.

See [`commands/auto-dev.md`](../../commands/auto-dev.md) §"Step 1b.5: Spec Review" for the orchestrator-side details.

## Dogfood example: tiny-scope auth change forces the gate

Acceptance criterion from issue #2: "a tiny-scope auth change forces the gate". Concrete walkthrough.

A spec author writes:

```yaml
---
spec_version: 1
ticket_id: gh:example/repo#99
title: Add MFA check to /login endpoint
scope_tier: small
risk_tag: safe
plan_source: github
author: human
date: 2026-05-21
---

## Summary
Add a one-line MFA check inside /login. ~15 lines, one file.

## Target files
| Path | Change type | Est. lines |
|---|---|---|
| `auth/login.py` | edit | ~15 |

Total: 1 file, ~15 lines.

(... other sections omitted for brevity ...)
```

The scope_tier (`small`) is honest — 1 file, 15 lines, no other forbidden-area touches. So Check 3 passes.

Check 4 fires. The target path `auth/login.py` matches the `auth/` heuristic from ADR 0004 §"Path-pattern heuristics", which maps to the `Permission Grant` / `Security Weaken` family in the `soft_deny` bucket. Derived risk tier is `sensitive`. Declared is `safe`. Mismatch → MUST_FIX:

```
MUST_FIX — Risk tag under-classifies
  what: Declared risk_tag is `safe` but target file `auth/login.py` matches the `Permission Grant`/`Security Weaken` family (soft_deny bucket per `claude auto-mode defaults`).
  why: Under-classification causes /auto-dev to auto-merge work that should have gated. A 15-line MFA change is small-scope, but its risk profile is sensitive — the risk-tier gate is the only mechanism preventing it from shipping without review.
  fix: Bump risk_tag to `sensitive`.
  spec_evidence: "risk_tag: safe" / "auth/login.py | edit | ~15"
  rule_evidence: "auth/login.py" — matches "Permission Grant"/"Security Weaken" rule per ADR 0004 §"Path-pattern heuristics".
```

After the author bumps `risk_tag: sensitive` and re-runs, the spec passes review. `/auto-dev` then sees `risk_tag: sensitive` and forces a human plan-approval gate at Checkpoint 1 regardless of the `scope_tier: small` classification.

The dangerous-but-tiny class is now gated.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Reviewer keeps flagging the same risk-tag MUST_FIX after author bumped it | Author bumped to `sensitive` but a different path matches a `dangerous` heuristic — reviewer wants `dangerous` | Re-read the rule_evidence; check if ANY path matches a hard_deny signal, not just the original one |
| Reviewer flags scope_tier mismatch but the math adds up | Author may be using inflated `~N` estimates as padding; reviewer is comparing the sum against the declared tier. Either reduce padding or bump the tier. | Re-count honestly; if the realistic estimate is large, declare `large`. |
| Reviewer returns `SPEC_MALFORMED` on a spec that looks fine | Frontmatter YAML probably has a tab character or unquoted special char | Run `python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]).read().split('---')[1])" specs/foo.md` to find the parse error |
| Reviewer flags "out of scope is thin" but you genuinely thought of everything | Some adjacent-behavior questions don't have an obvious answer — list them in `## Open questions` instead | Move the unresolvable items to `## Open questions`; this changes the spec from "ready" to "needs human" but is more honest |

## Related skills

- **[spec-author](../spec-author/)** — produces the spec doc this skill reviews
- **[auto-dev](../auto-dev/)** — primary consumer; runs this skill automatically in Stage 1b.5
- **[review](../review/)** — code-review counterpart; reviews implementation diffs, not specs
- **superpowers:brainstorming** — useful upstream when the input is freeform and the spec author needs to explore before authoring

## See also

- [ADR 0004 — Risk-tier vocabulary](../../../../docs/adr/0004-risk-tier-vocabulary.md) — the rubric this reviewer applies
- [`agents/spec-reviewer.md`](../../agents/spec-reviewer.md) — the agent definition this skill dispatches to
- [`commands/auto-dev.md`](../../commands/auto-dev.md) §"Step 1b.5: Spec Review" — how `/auto-dev` integrates this reviewer
