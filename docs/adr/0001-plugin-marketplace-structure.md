# ADR 0001: Plugin Marketplace Structure

- **Status:** Accepted
- **Date:** 2026-05-19
- **Deciders:** Matthew Warren

## Context

This repository began life as a thin distributor of Claude Code skills: `install.sh <name>` printed a `SKILL.md` to stdout for pasting into a project's `CLAUDE.md`. That worked while every skill was pure instructional prose, but three new skills (`review`, `auto-dev`, `review-monitor`) had hard dependencies on:

- 14 reviewer agent definitions
- 6 Python scripts (`post_review.py`, `review_monitor.py`, `review_sweep.py`, `prep_pr_state.py`, `prep_pr_finalize.py`, `review_monitor_cron.sh`) plus a `utils/runtime_paths.py` shim
- 8 slash command files

Those supporting files lived in a separate repository (`global-claude/exports/review-pipeline/`) and had to be installed separately. Users got a confusing two-step install where some references in the skill prose pointed at scripts the user might not have installed yet.

We needed to choose between three structural directions:

- **Option A** — keep the markdown-snippet model and accept the friction of cross-repo install for skills that need binaries
- **Option B** — convert this repo into a proper Claude Code plugin marketplace (`.claude-plugin/marketplace.json`, `plugins/<name>/` layout) so a single `/plugin install` ships everything
- **Option C** — hybrid: extend `install.sh` with a `--bundle` mode that copies optional `bundle/` subdirs

## Decision

Adopt **Option B**: convert to a Claude Code plugin marketplace.

Plugins are grouped by concern:

```
.claude-plugin/marketplace.json
plugins/
  session-management/      handoff, session-done, debug-triage
  plan-execution/          plan-executor
  queue-orchestration/     queue-plan, queue-debt, pull-and-execute
  review-pipeline/         review, auto-dev, review-monitor
                           + agents/ (14)
                           + commands/ (8)
                           + scripts/ (6 + utils/)
```

Each `SKILL.md` carries `name` + `description` YAML frontmatter so the Skill tool can discover and trigger it. Script references inside skills and commands use `${CLAUDE_PLUGIN_ROOT}/scripts/...` so paths resolve from the plugin install location.

The legacy snippet model is kept for backward compatibility: `install.sh` auto-discovers skills under `plugins/*/skills/*/SKILL.md` and prints any single skill's prose to stdout.

## Dual-tree sync model

This public marketplace and the author's internal `global-claude` repo stay structurally in sync but carry different example data:

| | Internal (`global-claude`) | Public (`claude-skills`) |
|---|---|---|
| Examples reference | Real client/employer repos, Slack channels, internal team names | Generic placeholders (`your-org/your-repo`, `#your-review-channel`, `<your-channel-id>`) |
| Distribution | Private install scripts, employer-specific automation | Claude Code plugin marketplace |
| Sanitization | None | Sed-driven scrub on each update from internal source |

The internal version is the source of truth for behavior; the public version is the scrubbed mirror. The author does not personally install from the public marketplace — keeping it in sync is structural maintenance, not dogfood.

## Consequences

### Positive

- One install command (`/plugin install review-pipeline@claude-skills`) ships everything a user needs.
- Skill files can reference scripts and agents by `${CLAUDE_PLUGIN_ROOT}/...` paths that are guaranteed to exist post-install.
- Per-plugin versioning lets the review-pipeline plugin evolve faster than the session-management plugin without forcing a marketplace-wide bump.
- The marketplace format is the documented Claude Code path forward; investing here aligns with the platform direction.

### Negative

- Scrub workflow is manual: when the internal `global-claude/exports/review-pipeline/` is updated, the changes must be hand-ported and re-scrubbed here. There is no automation enforcing that.
- The legacy `install.sh` snippet mode is still maintained even though it duplicates the marketplace install path for users who only want prose. Removal needs a deprecation cycle.
- Plugin groupings (4 plugins) reflect a single author's judgment; if the marketplace grows broader contributors, regrouping may be expensive.

### Neutral

- README documents both install paths (marketplace primary, snippet legacy) which increases the surface area for documentation rot.

## Alternatives considered

### Option A (status quo): markdown-snippet distributor

Rejected because the review-pipeline scripts and agents are real dependencies — telling users "go install this other repo first" is a worse experience than a marketplace install. The cross-repo nature also made the scripts feel like an afterthought instead of part of the product.

### Option C: hybrid `--bundle` mode

Rejected because it adds a new install path that is non-standard and not auto-discovered by Claude Code itself. The marketplace format is the platform-native solution; reinventing it inside `install.sh` would saddle this repo with infrastructure that the platform already provides.

## References

- [Claude Code plugin marketplace docs](https://docs.anthropic.com/en/docs/claude-code) (see Plugins section)
- Sample marketplace: `~/.claude/plugins/marketplaces/claude-plugins-official/.claude-plugin/marketplace.json`
- Sample multi-resource plugin: official `pr-review-toolkit` plugin under that marketplace
