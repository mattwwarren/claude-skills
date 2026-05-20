# Claude Code Agent Architecture (research for #15)

**Source:** `claude --help` / `claude agents --help` / `claude agents --json` / `claude auto-mode defaults` on **Claude Code 2.1.145** (Linux, 2026-05-20).

**Status:** Programmatic surface fully grounded. Three TTY-only validations remain (noted at bottom).

---

## 1. The bg-dispatch primitive is `claude --bg` (CLI, hidden from `--help`)

**Correction from first draft:** `claude --bg` **does exist** in 2.1.145. It is hidden from `claude --help` output but works as a real flag. Initial research missed it by trusting `--help` as exhaustive — lesson: probe by invocation, not by help text alone.

The bg lifecycle uses four CLI verbs, all hidden from `claude --help`:

```
claude --bg [prompt]        # spawn a new background session; prints session id, exits immediately
claude agents               # interactive TUI listing all sessions (bg + interactive), dispatch surface
claude agents --json        # scripting-friendly list of all live sessions
claude attach <id>          # open a bg session in this terminal; Ctrl+Z to detach (session keeps running)
claude logs <id>            # print bg session's recent terminal output (one-shot, not tail)
claude stop <id>            # stop a bg session; conversation kept and resumable via `attach`
```

Example output of `claude --bg` (from user's shell):

```
backgrounded · 4117e87b (idle — send a prompt to start)
  claude agents             list sessions
  claude attach 4117e87b    open in this terminal
  claude logs 4117e87b      show recent output
  claude stop 4117e87b      stop this session
```

**TTY constraint:** `claude --bg` requires a controlling terminal to persist the session. Invoked under a pipe / closed stdin / background-shell, it prints the "backgrounded" message but the session evaporates without sticking in the registry. Verified by running `claude --bg < /dev/null` — no entry appeared. **Implication for `cw`:** programmatic bg dispatch from a non-TTY context (`cw daemon`, a cron job, an MCP tool) needs a pty wrapper (`script`, `unbuffer`, or cw's own ptyhost), or must shell out to `claude -p` instead of `claude --bg`.

The `claude agents` TUI is the **rich management view** on top of the same registry — it can also dispatch new sessions interactively. It's a sibling of `claude --bg`, not a wrapper target.

Flags that set **defaults for dispatched sessions** when opening the view:

| Flag | Effect on dispatched sessions |
|------|-------------------------------|
| `--effort <level>` | Default effort (low/medium/high/xhigh/max) |
| `--model <model>` | Default model |
| `--permission-mode <mode>` | Default permission mode |
| `--add-dir <directory>` | Additional dirs tool access is granted to |
| `--plugin-dir <path>` | Plugins to load |
| `--mcp-config <config>` | MCP servers to apply |
| `--settings <file-or-json>` | Settings overlay |
| `--setting-sources <sources>` | Which sources to load (user/project/local) |
| `--strict-mcp-config` | Ignore non-`--mcp-config` MCP sources |
| `--allow-dangerously-skip-permissions` | Make bypass mode *available* (not default) |
| `--dangerously-skip-permissions` | Alias for `--permission-mode bypassPermissions` |
| `--cwd <path>` | (for `--json`) Filter listing to sessions started under `<path>` |

**Implication for #8/#10/#11:** `cw` cannot use a CLI dispatch flag — there isn't one. To programmatically launch bg work, `cw` must continue to spawn `claude -p` itself (as it does today). `claude agents` is the **user-facing TUI**; treat it as a sibling, not a wrapper target.

## 2. `claude agents --json` schema (registry shape)

Observed schema on live data (9 entries currently, including this session):

```jsonc
{
  "pid": 1597662,                                    // OS pid of the claude process
  "cwd": "/home/matthew/workspace/...",              // absolute startup cwd
  "kind": "interactive",                             // see note below
  "startedAt": 1774753579042,                        // epoch ms
  "sessionId": "f7d6a550-f573-4c2f-ab35-558f81ef350f", // uuid; resumable via -r
  "name": "obs-streaming-docker-debug",              // optional, set by -n / --name
  "status": "busy"                                   // optional: "busy" | "idle" | (absent)
}
```

Key facts:

- **`claude agents --json` lists ALL live `claude` processes, not just background ones.** This session appears in the output (verified: pid 3158138 in cwd `/home/matthew/workspace/personal/claude-skills`). So the JSON output is a **fleet registry**, not a bg-only registry.
- **`kind` values confirmed: `"interactive"` and `"background"`.** Verified after a `claude --bg` dispatch (session 4117e87b appeared with `"kind": "background"`, `"name": "4117e87b"` — the short id is the default name).
- **`status` is optional.** Newer / actively-managed sessions emit `"busy"`/`"idle"`; older sessions (some cw worktree sessions started days ago) omit it entirely. Don't assume presence.
- **`name` is optional** for interactive sessions (set by `-n/--name`); for bg sessions launched via `claude --bg` it defaults to the short 8-char form of the sessionId.
- **`--cwd` filters by startup directory prefix**, confirmed.

**Implication for #10 (fleet-stream observability):** This is the cross-session correlation primitive. Pair `claude agents --json` (registry) with `claude logs <id>` (one-shot output) or `claude -p --output-format stream-json --include-partial-messages --include-hook-events` (real-time on a freshly-spawned process). `claude logs` is *not* a tail — it prints "recent terminal output" and exits. For real-time streaming of an existing bg session, need to investigate whether `claude attach <id>` works under a pty wrapper, or whether the session's transcript file (in `~/.claude/projects/<encoded-cwd>/`) is appended in real time.

## 3. Adjacent surfaces relevant to the fleet design

### `--brief` mode + `SendUserMessage` tool — escalation primitive

```
--brief    Enable SendUserMessage tool for agent-to-user communication
```

This is the **native agent→user upward push channel** built into the runtime. Directly relevant to **#11 (escalation-channel)** — for in-CLI escalation, this replaces "build a custom adapter." A Slack/Hermes adapter is only needed for routing when the user is away from the terminal.

### `--from-pr` — PR-linked sessions

```
--from-pr [value]    Resume a session linked to a PR by PR number/URL, or open
                     interactive picker with optional search term
```

Implies sessions can be tagged with a PR, and there's an existing lookup index. Useful for **#10 (fleet-stream)** — events can be correlated to PRs natively. Should investigate whether the linkage is automatic (gh remote inference) or explicit (a flag we haven't seen).

### `--remote-control [name]` — separate feature, not bg dispatch

```
--remote-control [name]    Start an interactive session with Remote Control enabled
```

This is *not* the bg surface. It enables remote control *of* an interactive session (likely for IDE/host driving). Mentioning so we don't confuse it with `agents`.

### `claude auto-mode` — classifier surface

```
claude auto-mode config      # effective config (your settings + defaults)
claude auto-mode defaults    # built-in allow/soft_deny/hard_deny rules
claude auto-mode critique    # AI feedback on custom rules
```

Reading the defaults exposes a **3-bucket risk taxonomy already in production**: `allow` / `soft_deny` / `hard_deny`. This is more granular than our proposed `safe`/`sensitive`/`dangerous` and uses concrete rule names (e.g., "Git Push to Default Branch", "Production Deploy", "Self-Modification", "Create Unsafe Agents").

**Direct hit for #2 (spec-reviewer + risk-tier):** instead of inventing our own vocabulary, the risk tag in our spec should **alias or extend** these:

| Our tier | Classifier bucket | Examples from defaults |
|----------|-------------------|------------------------|
| safe | allow | Local Operations, Read-Only, Memory Directory |
| sensitive | soft_deny | Production Deploy, Git Push to Default Branch, Self-Modification |
| dangerous | hard_deny | Data Exfiltration, Safety-Check Bypass |

This alignment means our spec-reviewer can lean on the classifier's existing categorization rather than building parallel taxonomies. **Action: revise #2's risk-tier spec to reference classifier rule names directly.** A formal ADR (planned 0004) is held off until #2 implementation surfaces any constraints that would change the choice — see [`docs/adr/README.md`](../adr/README.md) "Planned ADRs" section.

### Scheduling primitives — three distinct surfaces

Probed in detail 2026-05-20 after Scott's "local routines have been really nice" comment. Three surfaces exist; they are not interchangeable.

| Surface | Scope | Firing mechanism | Cross-platform unattended? | Cost per fire |
|---------|-------|------------------|----------------------------|---------------|
| `CronCreate` + `.claude/scheduled_tasks.json` | **Session-scoped** (verified: `CronList` description says "in this session") | Fires inside the host Claude session while alive | Only if a host session stays alive (desktop app probably does this; Linux CLI does not) | ≈ work cost (session already loaded) |
| `RemoteTrigger` / `/schedule` skill | Registered at `claude.ai/code/routines` | Anthropic-managed; firing model not fully verified — likely either cloud-executes (no local FS) or manages a local launcher | Yes (registration); execution model unclear | Depends on execution model |
| OS cron / launchd + `claude -p` | OS-scoped | OS scheduler spawns fresh `claude -p` | Yes (launchd Mac-only; Linux needs systemd timer or cron) | ≈ 30-50k input tokens cold-cache + work |

**Why `scheduled_tasks.json` doesn't appear on this Linux CLI host:** The file is only created if a session in that project calls `CronCreate`. The mechanism is session-scoped, not daemon-backed. There's no `claude routines` CLI subcommand — confirmed by trying it. The Mac desktop app may have a long-running host session that fires schedules transparently; the Linux CLI has no equivalent.

**Implication for filesystem-bound workflows (wiki ports #5/#6/#7):**

The wiki workflow is filesystem-bound — `wiki-ingest` and `wiki-lint` read/write `~/workspace/personal/claude-skills/wiki/*` on this machine. Cloud-only execution (if `RemoteTrigger` works that way) can't reach those files. A "mesh" architecture (local cron for ingest, cloud routine for refining) adds reconciliation complexity (commit conflicts, half-applied state) for a workload that runs 7 fires/day on one machine — not worth it.

**Decision: #7 stays as launchd port** (known cost ~$3-5/mo on Haiku, known mechanism, single host, filesystem-local). Scott's "local routines" comment to be clarified for learning, but doesn't gate the port. If his answer reveals `/schedule` is actually a local-launcher wrapper (interpretation B above), swapping launchd → `/schedule` post-port is a UX polish, not a re-architecture.

**Implications for other tickets:**
- **#3 (follow-up-sweeper):** earlier I recommended `CronCreate` over OS cron based on auto-mode allowlist. **Revised:** for unattended cadence on a Linux CLI host, OS cron is the only mechanism that doesn't require a host session. If follow-up-sweeper is meant to fire while the user is *not* actively working, it needs OS cron. If it's meant to fire mid-session (e.g., "remind me to sweep follow-ups in an hour"), `CronCreate` is the right tool. Decide based on the intended cadence when writing the spec.
- **#10/#11:** `RemoteTrigger` is still potentially relevant for cloud-managed agent registration, but execution model needs verification before committing to it for fleet dispatch.

## 4. Permission boundary

The auto-mode classifier applies to **all sessions including dispatched bg ones** (no exemption surfaced). Two consequences for the fleet:

1. **`Create Unsafe Agents` is in soft_deny.** Specifically blocks "creating new autonomous agent loops that can execute arbitrary actions (e.g. shell commands, code execution) without human approval or established safety frameworks (e.g. `--dangerously-skip-permissions`, `--no-sandbox`, disabling approval gates)". This explicitly constrains what `cw bg` may do — we cannot ship a dispatch primitive that bypasses approval gates by default.
2. **`Self-Modification` is in soft_deny.** Touches `.claude/settings*.json`, `.claude/skills/`, `.claude/commands/`, `.claude/agents/`, etc. **#12 (permissions-pass) intersects this directly** — automated permission updates will need explicit user approval per pass.

**Previously open question (handoff §4):** "Does agent-view dispatch hit the same auto-mode classifier as raw CLI?" — based on the defaults and the `--allow-dangerously-skip-permissions` flag's framing ("make bypass-permissions mode *available* to dispatched sessions"), **yes**, the classifier applies; the agent-view flags just configure dispatched session defaults, they don't disable the classifier.

## 5. State directory layout

`~/.claude/projects/<encoded-cwd>/` — one directory per project, named by encoded cwd (e.g. `-home-matthew-workspace-personal-claude-skills`). Worktree sessions get their own directories (`-home-matthew--cw-wt-633a8385-auto-dev-2/`). This is where transcripts live; `claude project purge <path>` clears them.

This is the per-session persistence backing `/resume` and `--continue`. Fleet-stream (#10) tail of stream-json output is a different surface — it observes a *live* session, not the transcript on disk.

---

## TTY validations — results from 2026-05-20 session

### #1 — `claude agents` TUI shape (RESOLVED, model corrected)

**Wrong model:** "TUI is an agent-catalog picker."
**Actual:** `claude agents` is a **session manager**. Layout:

```
┌─ Needs input  ──── sessions awaiting first prompt
├─ Working      ──── sessions currently executing
├─ Completed    ──── sessions that finished or are idle
└─ ❯ start a task in the background   ← input field; ENTER dispatches a new bg session
```

The bottom input field dispatches a new bg session with the default settings configured on the `claude agents` CLI invocation (`--effort`, `--model`, `--permission-mode`, etc.). There is **no agent-definition selection step** in the dispatch flow.

**"Agent" is overloaded across the CLI:**
- `claude agents` subcommand → "background session manager" (sessions ARE the agents)
- `--agent <name>` / `--agents <json>` root flags → named definitions from `~/.claude/agents/*.md` catalog

Do not conflate the two in design docs. The agent-catalog markdown files are used at session-spawn time via `--agent`, *not* picked through `claude agents`.

### #2 — `/resume` from inside agents-view (PARTIALLY RESOLVED)

Typing `/resume` in the `claude agents` input field was **treated as a new session command** — it spawned a session running `/resume` (visible in the Working column). The agents-view input is always session-spawn, never meta.

**Still unresolved:** scope of the `/resume` picker when invoked from a regular `claude` session — does it list bg sessions alongside interactive? Run from a fresh `claude` shell, not from agents-view.

### #3 — `claude logs <id>` shape (RESOLVED, design impact)

**`claude logs` dumps raw terminal bytes including ANSI/cursor-control sequences** from the bg session's TUI. Not parseable as text in any practical sense. Filtering ANSI is fragile and brittle.

**Cleaner observability surface for #10:** `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl`. This is the per-session transcript, typed JSONL, appended in real time. Verified for bg session 4117e87b — file matched sessionId, contained typed events: `last-prompt`, `permission-mode`, `attachment`, plus presumably `user`/`assistant`/`tool_use`/`tool_result` for actual turns.

**Implication for #10:** target the on-disk JSONL transcript via filesystem tail (inotify or polling), not `claude logs`. Schema:

- Filename: `<sessionId>.jsonl`
- Location: `~/.claude/projects/<encoded-cwd>/`
- Per-line: JSON object with `type` field discriminator

### #4 — `claude attach` behavior (PARTIAL RESOLUTION + new finding)

`claude attach <unseeded-id>` **returned immediately without opening a session** — sessions in "send a prompt to start" state cannot be attached. Status stayed `idle` in the registry.

**New finding from cleanup:** `claude agents --json` appears to list **only seeded sessions**, not the unseeded "send a prompt to start" placeholders visible in the TUI. Verified: after the TUI showed 3 entries (2 needs-input + 1 idle bg), `--json` returned only 1. Implication: `cw` discovery via `--json` will miss in-flight session creations that haven't been seeded yet.

**Still unresolved:** `claude attach` behavior on a seeded, actively-working session, and whether it streams under a pty wrapper. Probably want to defer pty-wrapper exploration until/unless real-time monitoring outside the transcript-jsonl approach is needed.

### Permission flow on soft_deny — NOT VALIDATED

Did not run the soft_deny test (`git push origin main` in a bg session) this round. Remains open as a critical gap for **#11 escalation design**. Best probe path: spawn a seeded bg session with a soft_deny first prompt, then poll the transcript JSONL for what `permission-mode` events or new event types appear when blocked.

---

## Open after this round

1. **Soft_deny permission flow on bg sessions.** Critical for #11. Probe via transcript JSONL on a deliberately-tripping bg session.
2. **`/resume` picker scope from a regular session.** Does it list bg sessions? Trivial 30-second probe.
3. **Per-agent permission defaults from the catalog.** Read 2-3 of the `~/.claude/agents/*.md` files to see if frontmatter has permission/risk-tier-relevant fields. Inform #2's risk-tier spec.

---

## Decision impact on ROADMAP

| Ticket | Decision unlocked by this research |
|--------|-----------------------------------|
| #2 (spec-reviewer + risk-tier) | Risk-tier vocabulary → alias auto-mode classifier rule names rather than invent parallel taxonomy |
| #3 (follow-up-sweeper) | Use `CronCreate` (auto-mode allowlisted) instead of OS cron |
| #8 (cw-coord) | Use `claude agents --json` as cross-session registry; no need for cw's own discovery scan. `cw` can also dispatch via `claude --bg` (pty-wrapped for non-TTY callers) instead of maintaining its own daemon-spawned `claude -p` |
| #10 (fleet-stream) | Registry: `claude agents --json` (seeded sessions only). Output: tail `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl` (typed JSONL, real-time). **Do not use `claude logs`** — emits raw terminal bytes with ANSI. `claude --bg` simplifies dispatch — sessions are first-class with id/lifecycle commands |
| #11 (escalation) | In-CLI: use `--brief` / `SendUserMessage` natively. Slack adapter is a *routing layer*, not the upward primitive |
| #12 (permissions-pass) | Affected by `Self-Modification` soft_deny — design must always require user-approval per pass |

**Tier dependencies do not change** — the architecture research grounds the *implementation details* of each tier but doesn't reshuffle the order.
