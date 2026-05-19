# Auto-Dev Skill

Automated Linear → plan → implement → review → ship pipeline. The main session orchestrates; all work is delegated to subagents. Friction surfaces at clearly defined checkpoints.

## What It Does

`/auto-dev` takes a Linear ticket (or a query for one) and drives it end-to-end:

1. **Triage** — pull ticket, classify scope (small/medium/large/blocked)
2. **Plan** — generate a phased implementation plan
3. **Approve** — checkpoint: user approves the plan (or auto-approves for small scope)
4. **Implement** — spawn parallel agents for independent tasks per phase
5. **Self-review** — run `/review` on the diff
6. **Fix loop** — address findings (bounded, max 2 iterations)
7. **Ship** — commit, push, open PR with auto-merge

Each phase has explicit pass/fail gates. The pipeline stops at the first failed gate and surfaces the blocker.

## Invocation

```
/auto-dev GEN-1234                                  # specific Linear issue
/auto-dev --cycle current --project backend         # query
/auto-dev --label tech-debt --priority 2            # multi-filter query
/auto-dev --headless                                 # skip interactive checkpoints
```

## Scope-Based Automation

`/auto-dev` classifies work into scope buckets and adjusts automation accordingly:

| Scope | Files | Lines | Behavior |
|-------|-------|-------|----------|
| Small | ≤3 | ≤200 | Auto-approve plan, auto-merge PR |
| Medium | ≤10 | ≤500 | Plan checkpoint, manual merge |
| Large | >10 | >500 | Plan checkpoint, design review, manual merge |
| Blocked | — | — | Stop; clarification needed |

`--scope-limit small` caps `/auto-dev` to small work only. For tech debt, see `/auto-debt` in the full pipeline (a `/auto-dev` variant with strict scope limits and a tighter agent set).

## Forbidden Areas

```
/auto-dev GEN-1234 --forbidden "migrations,auth,billing"
```

Anything that would touch a forbidden area triggers a STOP with the offending paths and a recommendation to escalate to a human.

## Installation

```bash
./install.sh auto-dev >> ./CLAUDE.md
```

Or copy `skills/auto-dev/SKILL.md` into your CLAUDE.md manually.

## Prerequisites

This skill assumes:

- **Linear** for ticket source (via `linear` CLI or MCP)
- **GitHub CLI (`gh`)** for branch/PR operations
- **`/review`** skill installed (for the review phase) — see [review](../review/)

If Linear isn't your tracker, the plan and implementation stages still work; just feed a plan markdown file as input instead of a ticket ID.

## Full Pipeline

The marketplace skill is the instructional core. The complete pipeline adds reviewer agent definitions, GitHub posting scripts, and prep-pr quality gates. See [global-claude/exports/review-pipeline](https://github.com/mattwwarren/global-claude/tree/main/exports/review-pipeline) for:

- 14 specialized reviewer agents
- `post_review.py` (GitHub inline review comments)
- `prep_pr_state.py` + `prep_pr_finalize.py` (quality gates, PR creation, auto-merge)
- Companion `/auto-debt` command for constrained tech-debt runs

## Related Skills

- **[review](../review/)** — invoked inside the implement→review→ship loop
- **[review-monitor](../review-monitor/)** — picks up after the PR opens; watches reviewer threads through merge
- **[plan-executor](../plan-executor/)** — alternative for executing a pre-approved plan without the Linear/PR plumbing
- **[handoff](../handoff/)** — `/auto-dev` produces structured handoffs when it stops at a checkpoint
