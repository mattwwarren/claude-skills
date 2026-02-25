# Queue Debt Skill

Queue tech debt items for later processing via the `cw` task queue.

## What It Does

During feature work, you often discover tech debt that shouldn't be addressed immediately. This skill queues those items so a dedicated debt session can handle them later, keeping your current session focused.

## Prerequisites

- The `cw` CLI must be installed and configured
- `$CW_CLIENT` environment variable should be set (or you'll be prompted)

## Usage

```bash
# Normal priority
/queue-debt "Fix ruff violations in session.py"

# Elevated priority
/queue-debt "Update type annotations in models.py" --priority 3

# Urgent
/queue-debt "Fix broken import in cli.py" --priority 10
```

## Priority Levels

| Priority | Meaning |
|----------|---------|
| 0 | Normal FIFO ordering (default) |
| 1-5 | Elevated (important but not urgent) |
| 10+ | Urgent (picked up next) |

## Integration

- **Used by**: `/pull-and-execute` during review loops (LOW findings become debt items)
- **Consumed by**: Debt sessions running `/pull-and-execute --purpose debt`

## Installation

```bash
./install.sh queue-debt >> ./CLAUDE.md
```
