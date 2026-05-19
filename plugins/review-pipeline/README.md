# review-pipeline

Full code-review pipeline: parallel specialized reviewer agents, the Linear-to-ship `auto-dev` flow, and PR review monitoring through merge.

## Skills

- **review** — Parallel code review using specialized reviewer agents (architecture, performance, test, deployment, security, data-safety, etc.). Only actionable findings surface.
- **auto-dev** — Linear → plan → implement → review → ship pipeline with scope-based approval automation.
- **review-monitor** — Monitor PRs from first review through merge. Polls threads, performs delta reviews on new pushes, approves when all threads addressed, nudges idle authors.

## Agents (14)

Located under `agents/`. Each reviewer is a specialist subagent:

- `code-reviewer`, `code-simplifier`
- `architecture-reviewer`, `performance-reviewer`, `test-reviewer`
- `api-contract-validator`, `deployment-reviewer`
- `data-safety-reviewer`, `product-manager-reviewer`, `sysadmin-reviewer`
- `integration-tester`, `test-generator`, `verify-app`
- `session-handoff`

## Commands

Slash commands under `commands/`:

- `/auto-dev`, `/auto-debt`
- `/review`, `/review-sweep`, `/review-monitor`
- `/post-review`, `/prep-pr`, `/ship-it`

## Scripts

Python scripts under `scripts/`, referenced from commands via `${CLAUDE_PLUGIN_ROOT}/scripts/...`:

- `post_review.py` — Post GitHub PR review with inline comments
- `review_monitor.py` — State machine for PR monitoring
- `review_sweep.py` — Find/review unreviewed PRs
- `prep_pr_state.py`, `prep_pr_finalize.py` — PR preparation gates
- `review_monitor_cron.sh` — Hourly cron wrapper
- `utils/runtime_paths.py` — Shared path resolution

## Install

```text
/plugin install review-pipeline@claude-skills
```
