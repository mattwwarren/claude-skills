# Review-Monitor Skill

Follow GitHub PRs from their first review through merge. Poll thread activity, run delta reviews on new pushes, approve when every thread is resolved, and nudge stalled authors.

## What It Does

Code review usually breaks down after the *first* round — the reviewer leaves comments, the author pushes a fix, and then no one notices. `/review-monitor` is a state machine that closes that loop:

- **Polls** the threads on each monitored PR for activity
- **Delta-reviews** the new diff when the author pushes changes
- **Approves** automatically when every open thread is resolved
- **Nudges** authors who go quiet past a configurable threshold (24h default)
- **Drops** PRs when they merge or close

It supports two roles per PR: **author** (waiting for reviewer action) and **reviewer** (waiting for author fixes). Behavior diverges accordingly.

## Invocation

```
/review-monitor                       # default: run a full poll cycle
/review-monitor status                # list currently monitored PRs
/review-monitor drop 123              # stop monitoring a specific PR
/review-monitor where are my PRs?     # natural language query
/review-monitor what's blocking 123?  # natural language query
```

The poll cycle:

1. Consume pending registrations (`/tmp/review-monitor/pending/`)
2. Auto-discover this week's author PRs
3. For each monitored PR: load thread state, classify activity, take action
4. Persist updated state
5. Drop merged/closed PRs

## State

State lives in `~/.claude/review-monitor/` (per-PR JSON files). The location is overridable via `GLOBAL_CLAUDE_REVIEW_MONITOR_DIR`.

## Installation

```bash
./install.sh review-monitor >> ./CLAUDE.md
```

Or copy `skills/review-monitor/SKILL.md` into your CLAUDE.md manually.

## Prerequisites

This skill is heavier than most — it depends on a Python state machine to manage thread tracking and persistence. The marketplace SKILL.md tells Claude *how* to drive the state machine, but the state machine itself (`scripts/review_monitor.py`) is part of the full pipeline.

**To use `/review-monitor` end-to-end, install the supporting script and utils:**

```bash
# Install from the global-claude exports bundle
curl -L https://github.com/mattwwarren/global-claude/raw/main/exports/review-pipeline.tar.gz | tar xz
cd review-pipeline && ./install.sh
```

That installs `scripts/review_monitor.py`, `scripts/review_monitor_cron.sh` (template), and the `utils/runtime_paths.py` shim.

Other dependencies:

- **GitHub CLI (`gh`)** authenticated against the repos you want to monitor
- **`jq`** for argument parsing in the cron wrapper
- Optional: **Slack** webhook for nudge/escalation messages

## Scheduling

`scripts/review_monitor_cron.sh` is a template cron wrapper:

- Mon-Fri 8a-6p gate (machine TZ)
- Cheap GitHub precheck before spending tokens (skips fire if nothing changed)
- Budget cap (`--max-budget-usd 15` per fire)
- Optional escalation via `notify_escalation.sh`

Edit `REPO`, `WORKDIR`, `LOG`, and `ESCALATE_CMD` at the top of the file before scheduling. Originally written for macOS BSD utilities; Linux users need to swap `stat -f %m` for `stat -c %Y` and `date -v-1d` for `date -d '1 day ago'`.

Schedule example (every 30 min, weekdays):

```cron
*/30 8-18 * * 1-5  ~/.claude/scripts/review_monitor_cron.sh
```

## Full Pipeline

The marketplace skill is the instructional core. For everything else — the Python state machine, the cron wrapper template, the utils shim — install [global-claude/exports/review-pipeline](https://github.com/mattwwarren/global-claude/tree/main/exports/review-pipeline).

## Related Skills

- **[auto-dev](../auto-dev/)** — opens the PRs that `/review-monitor` then follows through merge
- **[review](../review/)** — used by `/review-monitor` to produce delta-review comments on new pushes
- **[handoff](../handoff/)** — `/review-monitor` produces handoff-style summaries when reviewer escalation is needed
