# Spec: cw-coord + fleet-stream

**Repo targets:** `mattwwarren/claude-workspace` (cw) primary, `mattwwarren/claude-skills` secondary (consumer skill)
**Tracking issues:** [claude-skills#8](https://github.com/mattwwarren/claude-skills/issues/8) (cw-coord), [claude-skills#10](https://github.com/mattwwarren/claude-skills/issues/10) (fleet-stream)
**Status:** draft — pending spec-review
**Author:** drafted by Claude under @mattwwarren direction
**Format:** follows the schema proposed in [claude-skills#1](https://github.com/mattwwarren/claude-skills/issues/1) (spec-author). This doc dogfoods that schema before the skill exists.

---

## Summary

Two co-evolving capabilities that share cw's existing event-bus + queue infrastructure:

1. **cw-coord** — read-only cross-workspace coordination report. Surfaces overlapping file claims, shared interface touches, probable duplicate tickets, and dependency cycles across all client queues. New `cw coord` subcommand + thin skill wrapper.
2. **fleet-stream** — formalize `cw events tail` as the canonical stable JSON event stream for any host renderer (zellij plugin, cmux, tmux, VS Code extension). Adds schema versioning, documents consumer integration, fills in missing event types for end-to-end fleet observability.

Both build on cw's existing `events.py` + `dev_queue.py` + per-client `queue.py`. Neither requires inventing new state stores.

## Scope tier

**Large** for the cw side (multiple new modules, public CLI surface, schema versioning commitment).
**Small** for the claude-skills side (one skill per feature, ~1 file each).

Split into two cw issues + two claude-skills issues to keep blast radius bounded.

## Risk tag

**Sensitive** — touches shared CLI surface in a tool the user runs across multiple workspaces. Schema versioning commitment is a one-way door once consumers exist. Requires human gate at plan-approval per [claude-skills#2](https://github.com/mattwwarren/claude-skills/issues/2).

Not `dangerous` — no auth, billing, migration, or multi-tenant data concerns.

## Target files

### cw repo (`mattwwarren/claude-workspace`)

**fleet-stream (do first, cw-coord depends on it):**
- `src/cw/events.py` — add `schema_version` field to `OrchestratorEvent`; freeze v1 schema
- `src/cw/cli.py` — extend `event_tail` with `--json`, `--watch`, `--since` flags; document stable contract
- `docs/events.md` — add "Stable Schema" section, version compatibility matrix, deprecation policy
- `docs/fleet-stream-schema.md` — new file, full JSON schema for v1
- New event types in `events.py`: `session.phase_changed`, `session.friction_reported`, `session.health_reported`, `session.idle`, `pr.opened`, `pr.merged`, `pr.ci_failed`
- Producer hooks in `wrapper.py` / `auto_dev_result.py` to emit the new event types
- `tests/test_events_stream.py` — schema-contract tests

**cw-coord:**
- `src/cw/coord.py` — new module: reads queues across all clients, computes coordination report
- `src/cw/cli.py` — new `cw coord` command group: `cw coord report`, `cw coord watch`
- `src/cw/models.py` — `CoordinationFinding` model: severity (FYI/WARN/CONFLICT), kind (file_overlap/interface_touch/duplicate_ticket/dependency_cycle), affected items
- Optionally: workspace registration mechanism if auto-discovery from `cw config` isn't sufficient
- `tests/test_coord.py` — given fixture queues, assert findings

### claude-skills repo (`mattwwarren/claude-skills`)

- `plugins/queue-orchestration/skills/cw-coord/SKILL.md` — thin skill that invokes `cw coord report`, summarizes findings for the chat session, suggests resolution actions
- `plugins/queue-orchestration/skills/fleet-stream/SKILL.md` — skill that documents the stream contract for consumer authors; not really a runtime skill, more a "how do I plug my host into this" reference
- (Optional) sample consumer: `examples/zellij-fleet-panel/` — minimal zellij plugin reading the stream

## Acceptance criteria

### fleet-stream

- [ ] `OrchestratorEvent` has `schema_version: int` field (default `1`)
- [ ] `docs/fleet-stream-schema.md` exists with full v1 schema, including all event types listed above
- [ ] `cw event tail --json` emits one JSON line per event, schema_version included on each
- [ ] `cw event tail --watch` streams indefinitely until SIGTERM
- [ ] `cw event tail --since <iso8601|cursor>` resumes from a known point
- [ ] Deprecation policy documented: additive changes within v1, breaking changes require v2
- [ ] Schema-contract test confirms every emitted event validates against the published JSON schema
- [ ] At least one sample renderer in `examples/` (shell jq one-liner + one TUI of choice)
- [ ] README and `docs/events.md` updated with link to schema

### cw-coord

- [ ] `cw coord report` runs in <2s against a fleet with 10 clients × 20 queue items
- [ ] Output formats: human-readable markdown (default), `--json` for consumers
- [ ] Findings sorted by severity (CONFLICT first, then WARN, then FYI)
- [ ] At minimum these checks fire:
  - File path appears in 2+ queue items across clients → WARN
  - Shared interface file touched by 2+ in-flight items → CONFLICT
  - Ticket title similarity > threshold across queues → FYI (with similarity score)
  - A blocks B, both in-flight (B running before A complete) → CONFLICT
- [ ] Pure read — never mutates queues, sessions, or events
- [ ] `cw coord watch` re-runs on a configurable interval, emitting deltas via the event bus as `coord.finding_added` / `coord.finding_resolved` event types (which become part of fleet-stream)
- [ ] Skill in claude-skills reads `cw coord report --json`, presents findings, offers resolution suggestions without executing them

## Test plan

**fleet-stream:**
- Unit: schema validation round-trip for every event type
- Integration: spawn a fake session, emit each event type, consume via `cw event tail --json`, assert ordering + schema
- Contract: pin a sample stream fixture; CI fails if schema changes incompatibly within v1
- Manual dogfood: pipe `cw event tail --watch --json` into `jq`, run an auto-dev session, confirm every transition visible

**cw-coord:**
- Unit: fixture queues representing each finding kind → expected findings list
- Integration: real `cw status` against a fleet with intentional overlap → verify findings
- Manual dogfood: run `cw coord report` against the user's actual workspace state, capture output as a sample in docs

## Definition of done

- All acceptance criteria checked off
- `cw coord` + `cw event tail --json --watch` documented in cw's `--help` and README
- `docs/fleet-stream-schema.md` linked from cw README and from claude-skills #10 issue
- Two skills published in claude-skills marketplace, install-tested
- Sample renderer works end-to-end (host-agnostic proof)
- Spec-reviewer pass (per #2) cleared
- Human plan-approval gate cleared (risk tier: sensitive)

## Out of scope

- Cross-host fleet aggregation (multiple machines) — single-machine v1 only
- TUI built into cw itself — host-agnostic by design
- Mutating coord actions (auto-resolve overlaps) — read-only v1
- Cross-repo PR coordination beyond what's already in queue items
- Auth/permissions on the event stream (assumes single-user machine)

## Dependencies + sequencing

```
fleet-stream (cw)  ─┬─►  cw-coord (cw)
                    │
                    └─►  fleet-stream skill (claude-skills)

cw-coord (cw)  ──────►  cw-coord skill (claude-skills)
```

fleet-stream lands first because cw-coord uses the event bus to emit deltas. Skills follow once cw side is stable.

## Open questions for review

1. Should `coord.finding_added` events also include suggested resolution metadata, or keep that in the skill layer?
2. Workspace registration: is auto-discovery from `cw config` sufficient, or do we need an explicit `cw coord register <workspace>` to opt in?
3. Schema versioning: do we commit to forever-backwards-compatible additive changes within v1, or allow breaking changes with a deprecation window?
4. Skill repo placement: extend existing `queue-orchestration` plugin, or split into a new `fleet-observability` plugin?

## Notes

- cw already has the bones (`events.py`, `dev_queue.py`, per-client queues). Most of the work is formalizing contracts, not new infrastructure.
- The headless contract for auto-dev ([cw docs/headless-contract.md](https://github.com/mattwwarren/claude-workspace/blob/main/docs/headless-contract.md)) is the model for how fleet-stream should be documented: producer-side source of truth in code, consumer-side reference doc in `docs/`.
- This spec itself dogfoods the schema proposed in claude-skills#1 — gaps in this doc are signal for refining the spec-author skill.
