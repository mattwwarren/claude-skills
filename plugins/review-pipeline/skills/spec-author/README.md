# Spec-Author Skill

Produce a ticket-shaped spec doc that round-trips through `/auto-dev` without ambiguity-scan exits.

## What It Does

`/auto-dev` consumes a plan from Linear or generates one inline. Neither path produces a *spec* — a structured doc with scope tier, risk tag, acceptance criteria, target files, test plan, and definition-of-done. `/spec-author` fills that gap.

Given a Linear ticket, GitHub issue, or freeform description, the skill emits a markdown file in a fixed schema that auto-dev's Step 1a recognizes as a complete plan and Step 1c clears as ambiguity-free.

## Invocation

```
/spec-author GEN-1234              # Linear ticket
/spec-author #1                    # GitHub issue (current repo)
/spec-author owner/repo#1          # GitHub issue (other repo)
/spec-author "freeform description" # ad-hoc
```

## Output

A single markdown file at `specs/<slug>-<date>.md` (or caller-specified path). Full schema lives in [SKILL.md](SKILL.md#schema-required-output-shape).

## Soft Dependency

`superpowers:brainstorming` is invoked during the divergent phase for freeform input. If not installed, the skill degrades gracefully (single-interpretation spec, noted in `## Open questions`). The plugin manifest schema does not currently support a formal `dependencies` field; the dependency is documented in prose.

## Related Skills

- **[auto-dev](../auto-dev/)** — primary consumer
- **superpowers:brainstorming** — soft dep, divergent phase
- **[spec-reviewer](../spec-reviewer/)** — validates this spec before any code work (per [ADR 0004](../../../../docs/adr/0004-risk-tier-vocabulary.md))
