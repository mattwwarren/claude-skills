# Changelog

All notable changes to this marketplace and its plugins are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this marketplace adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Each plugin tracks its own version inside its `.claude-plugin/plugin.json`; this top-level CHANGELOG aggregates marketplace-wide changes.

## [Unreleased]

## [1.0.0] - 2026-05-19

### Added

Initial plugin marketplace release with four plugins:

- **session-management** (1.0.0) — `handoff`, `session-done`, `debug-triage` skills plus handoff and debug-triage templates
- **plan-execution** (1.0.0) — `plan-executor` skill plus phase-handoff template
- **queue-orchestration** (1.0.0) — `queue-plan`, `queue-debt`, `pull-and-execute` skills (cw CLI)
- **review-pipeline** (1.0.0) — `review`, `auto-dev`, `review-monitor` skills, 14 reviewer agents, 8 slash commands, 6 Python scripts (`post_review.py`, `review_monitor.py`, `review_sweep.py`, `prep_pr_state.py`, `prep_pr_finalize.py`, `review_monitor_cron.sh`) and the `utils/runtime_paths.py` shim

### Marketplace structure

- `.claude-plugin/marketplace.json` manifest listing all plugins
- Per-plugin `.claude-plugin/plugin.json` manifests
- Every `SKILL.md` carries YAML frontmatter (`name`, `description`) for `Skill` tool discovery
- Command and skill references to `~/.claude/scripts/` rewritten to `${CLAUDE_PLUGIN_ROOT}/scripts/` so script paths resolve from the plugin install location
- Legacy `install.sh` snippet mode preserved; auto-discovers skills under `plugins/*/skills/*/SKILL.md`

### Decisions

See `docs/adr/0001-plugin-marketplace-structure.md` for the rationale behind the marketplace structure and the dual-tree sync model with the internal `global-claude` repo.

### Sanitized for public release

Employer-specific identifiers, internal Slack channel/team names, personal filesystem paths, and a hard-coded Python shebang were replaced with generic placeholders (`your-org/your-repo`, `<your-channel-id>`, `/path/to/...`, `#!/usr/bin/env python3`).
