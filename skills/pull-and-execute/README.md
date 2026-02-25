# Pull and Execute Skill

The execution engine for the `cw` task queue. Claims work items, decomposes them, spawns implementation agents, reviews results, and marks items complete.

## What It Does

This is the workhorse skill for multi-session orchestration. It implements a 6-phase workflow:

1. **Claim** - Pull the next item from the queue
2. **Plan** - Read context, assess scope, decompose if needed
3. **Implement** - Spawn parallel agents for medium/large work
4. **Review** - Check quality of implementation
5. **Fix** - Address review findings (max 2 iterations)
6. **Complete** - Final quality gates, commit, mark done

## Prerequisites

- The `cw` CLI must be installed with `queue claim` and `queue complete` commands
- `$CW_CLIENT` environment variable should be set
- `$CW_PURPOSE` helps auto-detect which queue to pull from

## Usage

```bash
# Pull next impl item
/pull-and-execute --purpose impl

# Pull next debt item
/pull-and-execute --purpose debt

# Execute a specific item
/pull-and-execute --id abc12345

# Auto-detect purpose from session
/pull-and-execute
```

## Scope Classification

| Scope | Files | Strategy |
|-------|-------|----------|
| Small | 1 file, < 50 lines | Direct implementation, no agents |
| Medium | 2-5 files | 1-2 parallel agents |
| Large | 5+ files | Decompose into subtasks, max 4 agents |

## Integration

- **Fed by**: `/queue-plan` (impl items) and `/queue-debt` (debt items)
- **Uses**: Task tool for agent spawning, review skills for quality checks
- **Produces**: Committed code, queue completion records

## Installation

```bash
./install.sh pull-and-execute >> ./CLAUDE.md
```
