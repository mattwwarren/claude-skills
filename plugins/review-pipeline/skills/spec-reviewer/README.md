# Spec-Reviewer Skill

Validate a `/spec-author`-shaped spec doc for honesty — scope tier matches the target file list, risk tag matches the paths being touched, acceptance criteria are actually testable, required sections are populated.

## What It Does

A bad spec becomes a bad PR cheaply. Catching the bad spec at plan-time costs one agent invocation; catching the same problem at PR-time costs an implementation cycle, a review cycle, and a fix cycle. This reviewer is the cheap pre-flight check.

It applies 8 checks (full mode) or 2 checks (tiers-only mode) defined in [SKILL.md](SKILL.md#modes), and emits MUST_FIX / SHOULD_FIX / OK findings in the same shape as code reviewers.

## Invocation

```
/spec-reviewer specs/foo-2026-05-21.md           # local file
/spec-reviewer gh:owner/repo#42                  # spec on a GitHub issue
/spec-reviewer GEN-1234                          # spec on a Linear ticket
/spec-reviewer specs/foo.md --mode tiers         # quick tier-only check
```

## How It Fits

- **Upstream:** [spec-author](../spec-author/) produces the spec; this skill reviews it.
- **Downstream:** [auto-dev](../auto-dev/) runs this skill automatically in Stage 1b.5, before the ambiguity scan and scope/risk classification.
- **Rubric:** [ADR 0004](../../../../docs/adr/0004-risk-tier-vocabulary.md) defines the risk-tag heuristics this reviewer applies.

## Related Skills

- **[spec-author](../spec-author/)** — produces the spec
- **[auto-dev](../auto-dev/)** — primary consumer
- **[review](../review/)** — code-review counterpart for the implementation diff
