# claude-skills

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin marketplace of reusable skills for session management, plan execution, and multi-session orchestration.

Skills are auto-loaded by Claude Code when their description matches the situation - no copy-paste, no `CLAUDE.md` edits.

## Installation

Add this repo as a marketplace, then install the plugins you want:

```bash
# In any Claude Code session
/plugin marketplace add mattwwarren/claude-skills
/plugin install session-management@claude-skills
/plugin install plan-execution@claude-skills
/plugin install cw-orchestration@claude-skills
```

`/plugin` lists installed plugins and lets you toggle them on or off per project.

## Plugins

### `session-management`

Skills for session boundaries - normal endings, abnormal endings, and structured debugging.

| Skill | Triggers When |
|-------|---------------|
| [session-done](plugins/session-management/skills/session-done/) | Wrapping up a normal session at a clean stopping point. Generates a handoff and signals `cw done`. |
| [handoff](plugins/session-management/skills/handoff/) | Context window 80%+ full, debug attempts stalled (debug fork), or scope creep. Generates self-contained handoff documents. |
| [debug-triage](plugins/session-management/skills/debug-triage/) | Multi-issue or long-running debugging. Tracks issues, supports agent escalation, generates postmortems. |

### `plan-execution`

| Skill | Triggers When |
|-------|---------------|
| [plan-executor](plugins/plan-execution/skills/plan-executor/) | Given an approved plan file (H2 phases, checkbox tasks) to execute. Phase-by-phase with parallel sub-agents. |

### `cw-orchestration`

Skills for the [`cw`](https://github.com/mattwwarren/cw) task queue - lets work flow across sessions.

| Skill | Triggers When |
|-------|---------------|
| [queue-plan](plugins/cw-orchestration/skills/queue-plan/) | Approved plan ready for implementation but not in this session. |
| [queue-debt](plugins/cw-orchestration/skills/queue-debt/) | Tech debt surfaces but is out of scope for the current task. |
| [pull-and-execute](plugins/cw-orchestration/skills/pull-and-execute/) | Claim and execute the next queued item end-to-end. |

## How Skills Work Together

These skills are designed as a system:

1. **plan-executor** breaks large tasks into phases and executes them with sub-agents.
2. Between phases, or when context runs low, **handoff** generates self-contained handoff documents.
3. **session-done** wraps up normal sessions and signals `cw done`.
4. When debugging gets stuck, **debug-triage** tracks issues and can escalate to background agents.
5. The **debug fork** pattern from `handoff` produces two tracks - main work and isolated investigation.
6. **queue-plan** and **queue-debt** push work onto the `cw` task queue.
7. **pull-and-execute** claims and executes queued items in fresh sessions.

Each skill works independently, but they're most effective together.

## Repository Layout

```
.
├── .claude-plugin/
│   └── marketplace.json              # Marketplace manifest
├── plugins/
│   ├── session-management/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       ├── handoff/
│   │       │   ├── SKILL.md          # Frontmatter + system prompt
│   │       │   ├── README.md         # Human-facing documentation
│   │       │   └── templates/        # Output document templates
│   │       ├── session-done/
│   │       └── debug-triage/
│   ├── plan-execution/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/plan-executor/
│   └── cw-orchestration/
│       ├── .claude-plugin/plugin.json
│       └── skills/{queue-plan,queue-debt,pull-and-execute}/
├── CONCEPTS.md
├── LICENSE
├── README.md
└── install.sh                        # Legacy: print SKILL.md to stdout
```

Each `SKILL.md` starts with YAML frontmatter:

```yaml
---
name: skill-name
description: Use when ... (this is what Claude matches against to decide whether to invoke the skill)
---
```

## Local Development

To work against this marketplace from a local checkout:

```bash
git clone https://github.com/mattwwarren/claude-skills.git
# In Claude Code:
/plugin marketplace add ./claude-skills
/plugin install session-management@claude-skills
```

## Legacy `install.sh`

For users who still want to paste skill bodies into a `CLAUDE.md`:

```bash
./install.sh --list                           # List skills across all plugins
./install.sh handoff                          # Print one skill to stdout
./install.sh handoff >> ./CLAUDE.md           # Append to a project CLAUDE.md
./install.sh --all >> ./CLAUDE.md             # Print every skill
```

Prefer the marketplace install path - skills load only when relevant, keeping the project's `CLAUDE.md` focused on project-specific guidance.

## Philosophy

See [CONCEPTS.md](CONCEPTS.md) for the ideas behind these skills:

- Fresh-context principle (handoffs must be self-contained)
- Debug forking (split stuck work into main + investigation tracks)
- Session boundaries (work with finite context, not against it)
- Agent orchestration (parallelize independent work)

## Contributing

To add a new skill to an existing plugin:

1. Create `plugins/<plugin>/skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`) and the skill body.
2. Create `plugins/<plugin>/skills/<name>/README.md` with human-facing documentation.
3. Optionally add `plugins/<plugin>/skills/<name>/templates/` for output templates the skill references.

To add a new plugin:

1. Create `plugins/<plugin>/.claude-plugin/plugin.json` with `name`, `version`, `description`, etc.
2. Add a `skills/` directory and one or more skills following the structure above.
3. Add an entry for the plugin in `.claude-plugin/marketplace.json`.

## License

[Unlicense](LICENSE) - public domain.
