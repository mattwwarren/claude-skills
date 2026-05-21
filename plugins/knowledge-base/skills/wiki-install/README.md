# wiki-install

Set up macOS `launchd` agents that run `/wiki-ingest` (every 4 hours) and `/wiki-lint` (daily at 6:00 AM) on the local machine.

> Wiki system design inspired by Scott Cipriano (@scottpcipriano).

## What It Does

`/wiki-install` writes two `launchd` plists into `~/Library/LaunchAgents/` and loads them via `launchctl`. The agents invoke `claude -p` with the `/wiki-ingest` and `/wiki-lint` skills to keep the wiki inbox processed and curated unattended.

## When to Use

- Once, after installing the `knowledge-base` plugin on a Mac, to enable scheduled wiki maintenance.
- After tuning schedule, model, or budget — re-run the skill to rewrite the plists.
- After moving the wiki repo to a new path — re-run with the new `KB_REPO_DIR`.

## Platform support

macOS only. Per [ADR 0003](../../../../docs/adr/0003-scheduling-mechanism-for-filesystem-bound-workflows.md), systemd timers and portable cron are deferred until there is a non-Mac user with the need.

## Scope

Schedules the two skills shipped by this plugin: `wiki-ingest` and `wiki-lint`. Other periodic skills live in other plugins and are not managed here.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `KB_REPO_DIR` | `$PWD` at install time | Repo the scheduled `claude -p` invocations operate in. |
| `KB_LABEL_PREFIX` | `com.knowledge-base` | `launchd` Label prefix (override for multiple wikis on one machine). |
| `KB_LOG_DIR` | `$HOME/Library/Logs` | Per-agent log location. |
| `KB_INGEST_INTERVAL_SECONDS` | `14400` | `wiki-ingest` `StartInterval`. |
| `KB_LINT_HOUR` / `KB_LINT_MINUTE` | `6` / `0` | `wiki-lint` `StartCalendarInterval`. |
| `KB_INGEST_MODEL` / `KB_LINT_MODEL` | `sonnet` | Model passed to `claude -p`. |
| `KB_INGEST_BUDGET_USD` / `KB_LINT_BUDGET_USD` | `5` | `--max-budget-usd` per fire. |

## Usage

```text
/wiki-install
```

The skill is idempotent — re-running it overwrites the plists with current configuration. To remove the agents, follow the **Uninstall** section in `SKILL.md`.

## Requirements

- macOS with `launchctl` (built-in).
- `claude` on `PATH` (Claude Code CLI installed).
- The `knowledge-base` plugin installed and `/wiki-ingest` + `/wiki-lint` invocable.
- A `wiki/` tree under `${KB_REPO_DIR}` for the scheduled skills to read and write.

## Installation

```text
/plugin install knowledge-base@claude-skills
```

`wiki-install` ships with the `knowledge-base` plugin.
