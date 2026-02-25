# claude-skills

Reusable skills for the [Claude Code](https://docs.anthropic.com/en/docs/claude-code) AI assistant. Each skill is a system prompt snippet you paste into your project's `CLAUDE.md` to teach Claude structured workflows.

No dependencies. No scripts. Just instructional markdown.

## Available Skills

### Session Management

| Skill | What It Does |
|-------|-------------|
| [session-done](skills/session-done/) | Wrap up work sessions with handoff generation and `cw done` signal |
| [handoff](skills/handoff/) | Structured session handoffs for context exhaustion, debug forks, and scope creep |
| [debug-triage](skills/debug-triage/) | Structured debugging with issue tracking, escalation, and postmortems |

### Plan Execution

| Skill | What It Does |
|-------|-------------|
| [plan-executor](skills/plan-executor/) | Phase-by-phase plan execution with parallel sub-agents |

### Multi-Session Orchestration (cw CLI)

| Skill | What It Does |
|-------|-------------|
| [queue-plan](skills/queue-plan/) | Queue approved plans for implementation via the `cw` task queue |
| [queue-debt](skills/queue-debt/) | Queue tech debt items with optional priority |
| [pull-and-execute](skills/pull-and-execute/) | Claim queue items, spawn agent teams, review, and complete |

## Quick Start

```bash
# 1. Clone (or add as submodule)
git clone https://github.com/mattwwarren/claude-skills.git

# 2. Install a skill
./claude-skills/install.sh handoff >> ./CLAUDE.md

# 3. Use it
# Claude now knows how to generate structured handoffs
```

## Installation

### Option A: Git Submodule (recommended for repos)

```bash
git submodule add https://github.com/mattwwarren/claude-skills.git
./claude-skills/install.sh handoff >> ./CLAUDE.md
```

### Option B: Standalone Clone

```bash
git clone https://github.com/mattwwarren/claude-skills.git
./claude-skills/install.sh --all >> ./CLAUDE.md
```

### Option C: Copy-Paste

Open any `skills/<name>/SKILL.md` and paste its contents into your `CLAUDE.md`.

## install.sh

```bash
./install.sh handoff              # Print one skill to stdout
./install.sh queue-plan           # Print another
./install.sh --list               # Show available skills
./install.sh --all                # Print all skills
./install.sh handoff >> CLAUDE.md # Append to your config
```

## Skill Format

Each skill follows this structure:

```
skills/<name>/
├── README.md    # User documentation, examples, installation guide
└── SKILL.md     # System prompt snippet (this is what gets installed)

templates/<name>/
├── README.md    # Template usage guide
└── *.md         # Fill-in-the-blank templates for skill outputs
```

- **SKILL.md** is the system prompt snippet - instructional text that teaches Claude the behavior
- **README.md** is for humans - explains what the skill does and how to use it
- **templates/** are reference templates for the documents each skill generates

## How Skills Work Together

These skills are designed as a system:

1. **plan-executor** breaks large tasks into phases and executes them with sub-agents
2. Between phases (or when context runs low), **handoff** generates structured handoff documents
3. **session-done** wraps up normal sessions and signals `cw done`
4. When debugging gets stuck, **debug-triage** tracks issues and can escalate to background agents
5. Debug triage's "debug fork" pattern produces handoffs via the **handoff** skill
6. **queue-plan** and **queue-debt** feed work into the `cw` task queue
7. **pull-and-execute** claims and executes queued items across sessions

Each skill works independently, but they're most effective together.

## Philosophy

See [CONCEPTS.md](CONCEPTS.md) for the ideas behind these skills:

- Fresh-context principle (handoffs must be self-contained)
- Debug forking (split stuck work into main + investigation tracks)
- Session boundaries (work with finite context, not against it)
- Agent orchestration (parallelize independent work)

## Contributing

To add a new skill:

1. Create `skills/<name>/SKILL.md` with the system prompt snippet
2. Create `skills/<name>/README.md` with documentation
3. Optionally add `templates/<name>/` for output templates
4. The skill automatically appears in `./install.sh --list`

## License

[Unlicense](LICENSE) - public domain.
