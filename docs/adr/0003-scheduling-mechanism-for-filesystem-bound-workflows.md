# ADR 0003: Scheduling mechanism for filesystem-bound workflows

- **Status:** Accepted
- **Date:** 2026-05-20
- **Deciders:** Matthew Warren
- **Related:** Issue [#7](https://github.com/mattwwarren/claude-skills/issues/7) (port wiki-install), Issue [#3](https://github.com/mattwwarren/claude-skills/issues/3) (follow-up-sweeper), research doc [`claude-code-agent-architecture.md`](../research/claude-code-agent-architecture.md) §"Scheduling primitives"

## Context

The knowledge-base port chain (#4 → #5 → #6 → #7) culminates in `wiki-install`, which sets up scheduled execution of `wiki-ingest` (every 4h) and `wiki-lint` (daily). The original skill on Mac uses `launchd` plists.

A primary-source comment from Scott Cipriano (original author) on 2026-05-20 — "One thing I have gone to is running these wiki jobs as local routines. It's been really nice!" — surfaced the question of whether the port should pivot to Claude Code's routine mechanisms rather than reproducing the launchd setup.

Investigation surfaced **three distinct scheduling surfaces** in Claude Code 2.1.145:

| Surface | Scope | Firing mechanism | Cross-platform unattended? | Cost per fire |
|---------|-------|------------------|----------------------------|---------------|
| `CronCreate` + `.claude/scheduled_tasks.json` | Session-scoped (`CronList` tool description: *"List all cron jobs scheduled via CronCreate in this session"*) | Fires inside the host Claude session while alive | Only if a host session stays alive (Mac desktop app may do this transparently; Linux CLI does not) | ≈ work cost (session already loaded) |
| `RemoteTrigger` / `/schedule` skill | Registered at `claude.ai/code/routines` | Anthropic-managed; execution model not fully verified — likely either cloud-executes (no local FS) or manages a local launcher | Yes (registration); execution depends on model | Unverified |
| OS cron / launchd + `claude -p` | OS-scoped | OS scheduler spawns fresh `claude -p` | Yes (launchd Mac-only; Linux needs systemd timer or cron) | ≈ 30-50k input tokens cold-cache + work cost |

The wiki workflow is **filesystem-bound**: `wiki-ingest` reads `wiki/inbox/`, `wiki-lint` writes to `wiki/pages/` and updates `wiki/index.md`, all under the user's local checkout. A purely cloud-hosted routine cannot reach these files.

A "mesh" architecture (local cron for filesystem-touching ingest, cloud routine for compute-heavy refining) was considered and rejected — it adds reconciliation complexity (commit conflicts, half-applied lint state) for a workload that runs at most 7 fires/day on one machine.

## Decision

Use **OS cron / launchd + `claude -p`** as the unattended scheduling mechanism for filesystem-bound Claude Code workflows. #7 (port wiki-install) ships the launchd plists from the original skill; non-Mac platforms are deferred to a follow-up (systemd timer or cron equivalent) until there's a user with that need.

`CronCreate` and `RemoteTrigger` remain useful for their respective scopes:

- **`CronCreate`** for in-session follow-ups: "remind me to do X in an hour" patterns where firing inside the current conversation is the desired behavior. This is its intended scope.
- **`RemoteTrigger` / `/schedule`** for cloud-managed agent registration where the work does not require local filesystem access. Cross-machine cadence, fleet-wide notifications, or anything that benefits from a hosted UI for monitoring. Not the right tool for wiki maintenance.

#3 (follow-up-sweeper) is unaffected by this ADR but should consult it: if the sweeper is meant to fire while the user is *not* actively in a Claude session, OS cron is the right mechanism. If it fires mid-session, `CronCreate` is right.

## Consequences

### Positive

- **Known mechanism.** Launchd is a well-understood OS surface; failure modes are documented and OS-native logging applies.
- **Known cost ceiling.** On Haiku, ~$3-5/mo total for the wiki cadence (6 fires/day for ingest, 1/day for lint, ~30-50k input tokens cold-cache per fire). Acceptable for the value delivered.
- **Single host, single state.** No reconciliation between local and cloud, no risk of half-applied operations.
- **Decoupled from content skills.** #5 (wiki-ingest) and #6 (wiki-lint) are scheduling-agnostic — they're plain skills invoked by whatever scheduler the user prefers. The scheduling layer (#7) can be swapped without touching them.

### Negative

- **Cold-cache cost per fire.** Each `claude -p` invocation pays the system prompt + CLAUDE.md + tool catalog overhead. For low-frequency workflows this is fine; for high-frequency or short-task workflows the overhead-to-work ratio would tilt against this choice.
- **Mac-first.** Launchd is Mac-only. Linux/Windows users need a follow-up port to systemd or cron. Acceptable for now (the primary use case is the author's Mac); flag as a known gap.
- **Forfeits the routines UI.** If `/schedule` does provide a nice management surface (visibility into past fires, errors, escalation), this decision foregoes it. Reconsider if a primary-source clarification of "local routines" (pending text to Scott) reveals `/schedule` is actually a local-launcher wrapper with a better UX over launchd plists — that would make a future ADR 0003-amendment worthwhile.

### Neutral

- The investigation surfaced that `CronCreate` is session-scoped, not daemon-backed. This corrects an earlier assumption (recorded in `docs/research/claude-code-agent-architecture.md` v1) that `CronCreate` was a viable OS-cron replacement. The research doc now records the corrected model; tickets referencing the earlier guidance (notably #3) should be re-read against this ADR.

## Alternatives considered

### Pivot #7 to `/schedule` (RemoteTrigger) cloud routines

Rejected for the wiki workflow specifically. The cloud routine cannot read `wiki/inbox/` on the user's laptop; even if `/schedule` turns out to wrap a local launcher (interpretation unconfirmed pending Scott's clarification), the port effort is comparable to launchd for unclear UX benefit. Worth revisiting as a follow-up once the firing model is verified.

### Pivot #7 to `CronCreate` writing `.claude/scheduled_tasks.json`

Rejected. `CronList` tool description explicitly scopes this mechanism to "in this session" — it fires only while a host Claude session is alive. The Mac desktop app may have a long-running host session that fires schedules transparently, but the Linux CLI has no daemon to do this and verification surfaced no `claude routines` subcommand on either platform. Unattended cadence on a Linux CLI host is not achievable via `CronCreate`.

### Mesh architecture: local cron for ingest, cloud routine for refining

Rejected. Both `wiki-ingest` and `wiki-lint` need local filesystem access — there's no clean split where one half doesn't touch disk. Splitting them would require a handoff mechanism (commit raw ingest, cloud routine pulls from git? push trigger?), reconciliation for half-applied state, and operating two schedule systems. For a 7-fires/day single-machine workload, the architecture cost exceeds the benefit.

## References

- Live findings: [`docs/research/claude-code-agent-architecture.md`](../research/claude-code-agent-architecture.md) §"Scheduling primitives"
- Primary source: Scott Cipriano (@scottpcipriano) comment on 2026-05-20 — to be followed up on for clarification of the specific mechanism he uses
- Claude Code 2.1.145 — `claude --help`, `CronList` tool description, `auto-mode defaults` allow-list entry for "Claude Code Scheduling"
