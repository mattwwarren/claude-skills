# ADR 0002: Fleet-stream observability via transcript JSONL

- **Status:** Accepted
- **Date:** 2026-05-20
- **Deciders:** Matthew Warren
- **Related:** Issue [#10](https://github.com/mattwwarren/claude-skills/issues/10), research doc [`claude-code-agent-architecture.md`](../research/claude-code-agent-architecture.md)

## Context

The fleet-buildout effort (#8/#10/#11) needs a per-session observability surface so a coordinator can see what each background Claude Code agent is doing in real time: tool calls, model turns, permission prompts, and final output. Three candidate surfaces exist in Claude Code 2.1.145.

| Candidate | What it is | Verified behavior |
|---|---|---|
| `claude logs <id>` | Prints recent terminal output of a bg session | Emits raw terminal bytes including ANSI/cursor-control sequences from the bg session's TUI. Not parseable as text without fragile ANSI-stripping. Verified 2026-05-20 — user had to kill it after the terminal began streaming odd characters. |
| `claude attach <id>` under a pty wrapper | Open the bg session locally, capture stdout | Untested. `attach` on an unseeded session exits immediately; on a seeded session it presumably opens the same TUI that `logs` dumps, so likely subject to the same ANSI problem. Adds pty management complexity (`script`, `unbuffer`, or a custom ptyhost). |
| Transcript JSONL at `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl` | Per-session event log written by the runtime | Typed JSONL events (`last-prompt`, `permission-mode`, `attachment`, presumably `user`/`assistant`/`tool_use`/`tool_result` for conversation turns). Appended in real time as the session runs. Filename is exactly the sessionId from `claude agents --json`, so correlation with the registry is trivial. Verified 2026-05-20 for bg session 4117e87b. |

## Decision

Adopt the **transcript JSONL** as the canonical observability surface for fleet-stream (#10) and any tooling that needs to observe a session's behavior in real time.

Tooling pattern:

1. Discover live sessions via `claude agents [--cwd <path>] --json` (fleet registry, lists `kind: "interactive" | "background"`).
2. For each sessionId of interest, tail `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl` via filesystem watch (inotify on Linux, `kqueue` / `FSEvents` on Mac) or polling.
3. Parse each line as a JSON object; discriminate on the `type` field.
4. Correlate sessions to PRs (where applicable) via the `--from-pr` linkage exposed in `claude --help`.

`claude logs` and `claude attach` are explicitly **not** part of the observability stack. They remain useful for human operators (`attach` for interactive driving, `logs` for a quick sanity dump) but are not the programmatic surface.

## Consequences

### Positive

- **No ANSI parsing.** Events are structured JSON; the parser is small and stable.
- **Real-time.** The runtime appends as turns happen — no polling lag beyond the watcher.
- **Cross-session correlation is free.** Filenames are sessionIds, which already appear in the `claude agents --json` registry.
- **No pty management.** Filesystem watches are well-understood primitives on every OS we care about.
- **Decoupled from the bg-lifecycle CLI.** Tools that observe sessions don't need to wrap `claude --bg` / `attach` / `stop` — they just read files. Useful for `cw daemon` and any future MCP-driven observers.

### Negative

- **Filesystem coupling.** The observer needs read access to `~/.claude/projects/`. For a single-user laptop fleet this is fine; for a multi-user host it constrains permission model.
- **Schema is undocumented.** The JSONL event schema (which `type` values exist, what fields each carries) is empirical — discovered by reading files, not from a published spec. Future runtime versions could change it without notice. Mitigation: pin the observed schema in the spec doc, run a smoke test on Claude Code version bumps.
- **No native back-pressure or filtering.** The observer reads everything; high-volume sessions (lots of tool calls, large file diffs) produce large files. For now we tolerate this; if it becomes a problem, the observer can sample or filter post-read.

### Neutral

- The transcript JSONL also backs `/resume` and `--continue`, so any session is observable retroactively, not just live. Useful for post-mortem; complicates "where does the stream start" semantics for a fleet-stream consumer (must record an offset, not just tail from end).

## Alternatives considered

### `claude logs <id>` as canonical surface

Rejected. Verified 2026-05-20 that `claude logs` emits raw terminal bytes — ANSI escapes, cursor positioning, redraw commands. The user terminated the test mid-stream when the output became visually disruptive. Filtering ANSI in a fleet observer is fragile (the TUI uses cursor positioning, not just SGR), and the bytes carry no semantic structure beyond what was rendered. Even if cleaned up, you'd still have to parse the cleaned text to recover tool calls and permission prompts — strictly worse than reading the structured JSONL the runtime already produces.

### `claude attach <id>` under a pty wrapper

Rejected. Conceptually attractive (same TTY contract the user gets) but introduces pty management complexity for no gain — the underlying byte stream is the same TUI output as `claude logs`. Also fails on unseeded sessions (verified: `claude attach` on an idle "send a prompt to start" session exits immediately). Pty wrapping is the kind of infrastructure we'd prefer not to maintain.

### Stream-json on freshly-spawned `claude -p`

Rejected for the fleet-observation case. `claude -p --output-format stream-json --include-partial-messages --include-hook-events` works beautifully for *new* processes you control — but the fleet includes pre-existing background sessions launched by `claude --bg` or via the TUI. There's no retrofit path to enable stream-json on a session that's already running. Keep this surface in mind for the dispatcher path (`cw bg` spawning new `claude -p` workers can use it), but don't make it the only observability mechanism.

## References

- Live findings: [`docs/research/claude-code-agent-architecture.md`](../research/claude-code-agent-architecture.md) §"`claude logs <id>` shape" and §"`claude agents --json` schema"
- Claude Code 2.1.145 — `claude --help`, `claude agents --help`, observed runtime behavior on Linux
