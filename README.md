# claude-skills

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) **plugin marketplace** for session management, plan execution, queue orchestration, code-review pipelines, and knowledge-base lesson capture. Each plugin ships skills (system-prompt snippets), agents (specialist sub-agents), commands (slash commands), and supporting scripts.

## Install

```text
/plugin marketplace add mattwwarren/claude-skills
/plugin install <plugin-name>@claude-skills
```

## Plugins

### [session-management](plugins/session-management/)

| Skill | What It Does |
|-------|--------------|
| [handoff](plugins/session-management/skills/handoff/) | Structured session handoffs for context exhaustion, debug forks, scope creep |
| [session-done](plugins/session-management/skills/session-done/) | Normal session wrap-up + `cw done` signal |
| [debug-triage](plugins/session-management/skills/debug-triage/) | Structured debugging with issue tracking, escalation, postmortems |

### [plan-execution](plugins/plan-execution/)

| Skill | What It Does |
|-------|--------------|
| [plan-executor](plugins/plan-execution/skills/plan-executor/) | Phase-by-phase plan execution with parallel sub-agents |

### [queue-orchestration](plugins/queue-orchestration/)

For the `cw` CLI multi-session work queue.

| Skill | What It Does |
|-------|--------------|
| [queue-plan](plugins/queue-orchestration/skills/queue-plan/) | Queue approved plans for implementation |
| [queue-debt](plugins/queue-orchestration/skills/queue-debt/) | Queue tech-debt items with priority |
| [pull-and-execute](plugins/queue-orchestration/skills/pull-and-execute/) | Claim queue items, spawn agent teams, review, complete |

### [review-pipeline](plugins/review-pipeline/)

Parallel-agent code review, end-to-end auto-dev, PR follow-through. Bundles **14 reviewer agent definitions**, **8 commands**, and **6 Python scripts** for GitHub posting and review-monitor state.

| Skill | What It Does |
|-------|--------------|
| [spec-author](plugins/review-pipeline/skills/spec-author/) | Author ticket-shaped specs that round-trip through `/auto-dev` |
| [review](plugins/review-pipeline/skills/review/) | Parallel code review using specialized reviewer agents |
| [auto-dev](plugins/review-pipeline/skills/auto-dev/) | Linear → plan → implement → review → ship pipeline |
| [review-monitor](plugins/review-pipeline/skills/review-monitor/) | Follow PRs from first review through merge |

### [knowledge-base](plugins/knowledge-base/)

> Wiki system design inspired by Scott Cipriano (@scottpcipriano).

| Skill | What It Does |
|-------|--------------|
| [wiki-lesson](plugins/knowledge-base/skills/wiki-lesson/) | Silent mid-session lesson capture to a configurable inbox |

## Marketplace Layout

```
claude-skills/
├── .claude-plugin/
│   └── marketplace.json          # marketplace manifest (5 plugins)
├── plugins/
│   ├── session-management/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/{handoff,session-done,debug-triage}/
│   ├── plan-execution/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/plan-executor/
│   ├── queue-orchestration/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/{queue-plan,queue-debt,pull-and-execute}/
│   ├── review-pipeline/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/{review,auto-dev,review-monitor}/
│   │   ├── agents/   (14 reviewer agents)
│   │   ├── commands/ (auto-debt, auto-dev, post-review, prep-pr, review,
│   │   │             review-monitor, review-sweep, ship-it)
│   │   └── scripts/  (post_review.py, review_monitor.py, etc.)
│   └── knowledge-base/
│       ├── .claude-plugin/plugin.json
│       └── skills/wiki-lesson/
└── install.sh        # legacy snippet-mode (prints SKILL.md to stdout)
```

Each `SKILL.md` carries YAML frontmatter (`name`, `description`) so Claude Code's `Skill` tool can discover it; scripts referenced by commands use `${CLAUDE_PLUGIN_ROOT}/scripts/...` paths that resolve to the plugin's install location.

## Legacy: Paste-Into-CLAUDE.md Mode

The original markdown-snippet workflow still works for users who want to drop a skill into a project's `CLAUDE.md` without installing the plugin:

```bash
git clone https://github.com/mattwwarren/claude-skills.git
./claude-skills/install.sh handoff >> ./CLAUDE.md
./claude-skills/install.sh --list                # see what's available
./claude-skills/install.sh --all >> ./CLAUDE.md  # everything
```

The installer auto-discovers skills inside `plugins/*/skills/*/SKILL.md`.

## How the Skills Fit Together

1. **plan-executor** breaks large tasks into phases and executes them with sub-agents
2. When context runs low or debugging stalls, **handoff** generates structured handoff docs
3. **session-done** wraps up normal sessions and signals `cw done`
4. **debug-triage** tracks stuck issues and can escalate to background agents
5. **queue-plan** / **queue-debt** push work into the `cw` task queue
6. **pull-and-execute** claims and executes queued items across sessions
7. **review** runs the parallel reviewer agents; **auto-dev** strings the full Linear-to-ship pipeline together; **review-monitor** shepherds PRs through merge

## Philosophy

See [CONCEPTS.md](CONCEPTS.md):

- Fresh-context principle (handoffs must be self-contained)
- Debug forking (split stuck work into main + investigation tracks)
- Session boundaries (work with finite context, not against it)
- Agent orchestration (parallelize independent work)

For subagent model selection (which model to pin on fanned-out work, and the
Opus-credit-pressure spawn-refusal failure mode), see
[docs/MODEL-GUIDANCE.md](docs/MODEL-GUIDANCE.md). Required reading before
invoking any of the fleet-dispatching skills (`/auto-dev`, `/plan-executor`,
`/pull-and-execute`) from an Opus main thread.

## Versioning

This marketplace and each plugin follow [Semantic Versioning](https://semver.org/). Marketplace-wide changes are summarized in [CHANGELOG.md](CHANGELOG.md); per-plugin versions live in each plugin's `.claude-plugin/plugin.json`.

Significant structural decisions are recorded as [Architecture Decision Records](docs/adr/) — start with [ADR-0001](docs/adr/0001-plugin-marketplace-structure.md) to understand why the marketplace is laid out the way it is.

## Sync model

This public marketplace mirrors an internal repo (`global-claude`) that the author uses day-to-day. Examples in the public version use generic placeholders (`your-org/your-repo`, `#your-review-channel`, `<your-channel-id>`) so client and employer context never leaks. The author does not personally install from this public marketplace; keeping it in sync is structural maintenance, not dogfood.

If you find a script path, identifier, or example that still looks employer-specific, please open an issue.

## License

[Unlicense](LICENSE) — public domain.
