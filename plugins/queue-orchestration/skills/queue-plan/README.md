# Queue Plan Skill

Queue approved plans for implementation via the `cw` task queue, enabling multi-session orchestration.

## What It Does

When you have a plan ready for implementation, this skill queues it to the `cw` task queue so a dedicated implementation session can pick it up with `/pull-and-execute`. This enables a separation between planning sessions and implementation sessions.

## Prerequisites

- The `cw` CLI must be installed and configured
- `$CW_CLIENT` environment variable should be set (or you'll be prompted)

## Usage

```bash
# Auto-detect plan from todo marker or recent modifications
/queue-plan

# Specify plan explicitly
/queue-plan --plan ~/.claude/plans/auth-system/main.md
```

## How It Works

1. Identifies the active plan (from argument, todo marker, or recent files)
2. Extracts the plan title and first incomplete phase
3. Queues the plan to the `cw` task queue with `--purpose impl`
4. Reports the queued item ID and next steps

## Integration

- **Upstream**: Plans are created via `/decompose-plan` or manual authoring
- **Downstream**: Implementation sessions use `/pull-and-execute` to claim and execute queued plans

## Installation

```bash
./install.sh queue-plan >> ./CLAUDE.md
```
