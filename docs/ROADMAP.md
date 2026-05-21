# Roadmap

Source of truth for ticket sequencing and dependencies. Companion to GitHub Issues — issues are the unit of work, this doc shows the shape of the whole.

**Status legend:** ⬜ open · 🔵 in-progress · ✅ done · ⏸ blocked

---

## Ship order (recommended)

Sequenced so each tier unlocks the next. Within a tier, items are independent and parallelizable.

### Tier 0 — Foundations

| # | Title | Status | Why first |
|---|---|---|---|
| [#1](https://github.com/mattwwarren/claude-skills/issues/1) | `spec-author` skill | 🔵 | in-progress (PR pending) — Every other ticket benefits from a real spec schema. Bootstraps itself — the first spec it produces could be for spec-author. |
| [#9](https://github.com/mattwwarren/claude-skills/issues/9) | docs: model-cognizance | ✅ | merged via PR #19 (2026-05-21, auto-dev) |

### Tier 1 — Quality gates

| # | Title | Status | Depends on |
|---|---|---|---|
| [#2](https://github.com/mattwwarren/claude-skills/issues/2) | `spec-reviewer` + risk-tier | 🔵 | in-progress (PR pending) — consumes #1 spec schema; ADR 0004 ships with implementation |
| [#3](https://github.com/mattwwarren/claude-skills/issues/3) | `follow-up-sweeper` cron | ⬜ | none (standalone) |

### Tier 2 — Knowledge base port

Per-skill so each one dogfoods the auto-dev pipeline independently.

| # | Title | Status | Depends on |
|---|---|---|---|
| [#4](https://github.com/mattwwarren/claude-skills/issues/4) | port `wiki-lesson` (attrib @scottpcipriano) | ✅ | merged via PR #14 (2026-05-19, auto-dev) |
| [#5](https://github.com/mattwwarren/claude-skills/issues/5) | port `wiki-ingest` | ✅ | merged via PR #16 (2026-05-20, auto-dev, 2 review cycles) |
| [#6](https://github.com/mattwwarren/claude-skills/issues/6) | port `wiki-lint` | ✅ | merged via PR #17 (2026-05-20, auto-dev, 3 review cycles) |
| [#7](https://github.com/mattwwarren/claude-skills/issues/7) | port `wiki-install` | ✅ | merged via PR #18 (2026-05-21, auto-dev) |

### Tier 3 — Fleet infrastructure

Cross-repo work (cw + claude-skills). Spec lives at [`docs/specs/cw-coord-and-fleet-stream.md`](specs/cw-coord-and-fleet-stream.md).

| # | Title | Status | Depends on |
|---|---|---|---|
| [#10](https://github.com/mattwwarren/claude-skills/issues/10) | fleet-stream JSON observability | ⬜ | none, but coupled to #8 by spec |
| [#8](https://github.com/mattwwarren/claude-skills/issues/8) | `cw-coord` cross-workspace report | ⬜ | #10 (uses event bus for deltas) |
| [#11](https://github.com/mattwwarren/claude-skills/issues/11) | escalation-channel | ⬜ | #10 (hard), #8 (soft) |

### Tier 4 — Operational ergonomics

| # | Title | Status | Depends on |
|---|---|---|---|
| [#12](https://github.com/mattwwarren/claude-skills/issues/12) | session-review permissions-pass | ⬜ | none, but most useful once #11 exists (proposes-then-escalates) |

---

## Dependency graph

```
#1 spec-author ──► #2 spec-reviewer+risk
                   #3 follow-up-sweeper

#4 wiki-lesson ──► #5 wiki-ingest ──► #6 wiki-lint ──► #7 wiki-install

#10 fleet-stream ─┬──► #8 cw-coord
                  ├──► #11 escalation
                  └─ shared spec: docs/specs/cw-coord-and-fleet-stream.md

#9 docs-model-cognizance      (standalone)
#12 permissions-pass           (standalone, integrates with #11 when ready)
```

## Parallelization opportunities

If multiple agents are dispatched (auto-dev, cw daemon, manual):
- Tier 0 can run in full parallel (2 items, no shared files)
- Tier 1 #2 and #3 can run in parallel after #1 lands
- Tier 2 must serialize (each port depends on the previous establishing convention)
- Tier 3 #10 must land first; then #8 and #11 can parallelize
- Tier 4 can run anytime

## Risk distribution

Per the risk-tier scheme proposed in #2:

| Risk | Tickets |
|---|---|
| safe | #3, #4, #5, #6, #7, #9, #12 |
| sensitive | #1, #2, #8, #10, #11 |
| dangerous | (none — by design, no auth/billing/migration work in this batch) |

`sensitive` tickets require human plan-approval gate per #2.

## Cross-repo dependencies

Tickets touching `mattwwarren/claude-workspace`:
- #8 — `cw coord` command + module
- #10 — `cw event tail` flags + new event types + schema doc
- #11 — cw daemon routing + adapter framework

These need corresponding cw-side tickets filed once the spec passes review.

## Research notes

- [`docs/research/claude-code-agent-architecture.md`](research/claude-code-agent-architecture.md) — grounds #8/#10/#11 in the actual `claude --bg` / `claude agents` / `claude auto-mode` surfaces in 2.1.145. Key takeaways:
  - **`claude --bg` IS the programmatic bg-dispatch primitive** (hidden from `--help`). Lifecycle: `--bg` → `agents` (list) → `attach` / `logs` / `stop`. Requires a TTY; non-TTY callers (cw daemon, cron) need a pty wrapper.
  - `claude agents --json` is a **fleet-wide live-session registry** with `kind: "interactive" | "background"` — confirmed via bg dispatch.
  - `--brief` enables `SendUserMessage` — the **native upward channel for #11**; Slack becomes a routing layer, not the primitive.
  - **#2 risk-tier vocabulary should alias the existing `auto-mode` classifier buckets** (`allow`/`soft_deny`/`hard_deny`) instead of inventing parallel taxonomy.
  - `CronCreate` is **session-scoped** (not a daemon) — only fires while a host session is alive. For unattended cadence on Linux CLI, OS cron remains the only viable mechanism. See "Scheduling primitives" in the research doc.
- TTY validations run 2026-05-20: `claude agents` is a session manager (not agent-catalog picker); `claude logs` emits raw ANSI terminal bytes — **#10 should tail `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl`** (typed JSONL, real-time) instead. Soft_deny permission flow still untested — the last critical gap for #11.
- **#7 (wiki-install) stays as launchd port** — wiki workflow is filesystem-bound, cloud-only routines can't reach local `wiki/inbox/`. Scott's "local routines" comment to be clarified for learning (not gating the port).

## Open coordination questions

1. Should Tier 3 land before Tier 2 so the wiki ports can use fleet-stream for visibility while they run? Tradeoff: Tier 3 is sensitive (larger scope), Tier 2 is dogfood-shaped (small, isolated). Probably no — keep current order, Tier 2 generates the wiki content that Tier 3's observability will eventually surface.
2. Does the spec doc in `docs/specs/` need a separate review process, or do GitHub PRs against the doc suffice?
3. Tracker maintenance: this doc updates as tickets close. Worth a tiny script to sync open/closed state from `gh issue list`, or keep manual?
