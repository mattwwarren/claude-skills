---
type: scope-handoff
created: 2026-05-19T15:50:00Z
reason: scope-creep
---

# Marketplace Conversion Handoff

**Date**: 2026-05-19 15:50 UTC  
**Status**: scope-deferred  
**Repository**: ~/workspace/personal/claude-skills

---

## Summary

Just added three new skills (`review`, `auto-dev`, `review-monitor`) to the markdown-snippet marketplace. During integration, discovered that this repo is not a proper Claude Code plugin marketplace — it's a custom install.sh model that prints SKILL.md to stdout for pasting into CLAUDE.md. This works for pure prompt snippets but can't distribute scripts/agents/commands natively.

The three new skills have dependencies on external scripts and agent definitions that live in `global-claude/exports/review-pipeline`. The current solution: each skill's README links to the external tarball. But this creates friction.

## What Changed This Session

**Committed to global-claude (336b42b):**
- Refreshed exports/review-pipeline/ with all stale commands/agents/scripts
- Added review-monitor command + scripts + cron wrapper + utils shim
- Added new agents (data-safety-reviewer, product-manager-reviewer)
- Updated installer and README

**Committed to claude-skills (95b79a7):**
- Added `skills/review/SKILL.md` + README.md
- Added `skills/auto-dev/SKILL.md` + README.md
- Added `skills/review-monitor/SKILL.md` + README.md
- Updated top-level README.md with "Code Review & Development" section
- Updated install.sh usage() text (but auto-discovery already works)

**Current state:** Skills are discoverable via `./install.sh --list`, but they're markdown-only. Full functionality (scripts, agents, commands) requires the user to separately install the `global-claude/exports/review-pipeline` tarball.

## Critical Discovery

This marketplace isn't a proper Claude Code plugin marketplace. Proper format would be:

```
.claude-plugin/
└── marketplace.json          # lists plugins

plugins/
├── session-management/
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── commands/
│   ├── skills/
│   └── ...
├── cw-orchestration/
│   └── ...
└── review-pipeline/          # would include scripts & agents
    ├── .claude-plugin/
    │   └── plugin.json
    ├── commands/
    ├── agents/
    ├── scripts/
    └── ...
```

Reference: `global-claude/codex-marketplace/.agents/plugins/marketplace.json` (Codex variant of this format).

## Open Decisions

### 1. Keep Current or Migrate?

**Option A: Keep as-is (markdown-snippet distributor)**
- Pro: simpler, lower friction to read/audit SKILL.md
- Con: review-pipeline stays split across two repos; users install skills + scripts separately
- Best for: users who want to read before installing

**Option B: Convert to proper plugin marketplace**
- Pro: scripts/agents/commands install in one shot; review-pipeline becomes a single plugin
- Con: lose the "paste into CLAUDE.md" simplicity; requires `.claude-plugin/` setup
- Best for: professional distribution; cloud publishing

**Option C: Hybrid**
- Marketplace stays markdown-only (install.sh unchanged)
- Add `./install.sh <skill> --bundle` mode that also copies scripts/agents if present
- Each skill can optionally have a `bundle/` subdir
- Pro: backwards-compatible; review-pipeline plugin gets bundled scripts naturally
- Con: two modes to maintain

**Recommendation**: Option C (hybrid). Lowest migration cost, unblocks review-pipeline bundling, keeps existing SKILL.md consumer happy.

### 2. Plugin Organization

If migrating, group existing skills into logical plugins:

- `session-management` — handoff, session-done, debug-triage
- `plan-execution` — plan-executor, pull-and-execute
- `queue-orchestration` — queue-plan, queue-debt
- `review-pipeline` — review, auto-dev, review-monitor (+ agents/scripts from global-claude)

Or: one monolithic `claude-workflow` plugin with everything. Simpler but less composable.

## Next Actions for Fresh Session

**If pursuing Option C (recommended):**

1. [ ] Extend `install.sh` with `./install.sh <name> --bundle` mode
   - Read skill's optional `bundle/` subdir
   - Copy commands/, agents/, scripts/ into appropriate `~/.claude/` subdirs
   - Backwards-compatible: existing `./install.sh <name>` still works

2. [ ] Create `skills/review-pipeline/` as a unified plugin (or just extend existing three skills with a `bundle/` subdir each)
   - Move scripts and agents from `global-claude/exports/review-pipeline/scripts/` and `agents/` into `skills/{review,auto-dev,review-monitor}/bundle/`
   - Symlink or copy — either works

3. [ ] Update each skill's README to drop the "Full Pipeline" section (no longer needed)

4. [ ] Test: `./install.sh review --bundle` should install SKILL.md + reviewer agents + post_review.py

5. [ ] Update top-level README to document `--bundle` mode

6. [ ] Consider: fold review-pipeline commands (review.md, auto-dev.md, review-monitor.md) into their skill definitions, or keep them separate. Currently they're in global-claude/commands/; they could live here instead.

**If pursuing Option B (full conversion to plugin marketplace):**

Much larger effort — restructure everything into `.claude-plugin/` + `plugins/*/` layout. Doable but not this session.

## Files to Know

- `~/workspace/global-claude/exports/review-pipeline/` — scripts, agents, install.sh
- `~/workspace/global-claude/commands/{review,auto-dev,review-monitor}.md` — source commands (SKILL.md came from these)
- `~/workspace/global-claude/agents/{data-safety-reviewer,product-manager-reviewer}.md` + others
- `~/workspace/global-claude/codex-marketplace/.agents/plugins/marketplace.json` — reference for plugin format
- `~/.claude/skills/handoff/` — the handoff skill definition (what generated this doc)

## Resumption Prompt

```
Continuing marketplace conversion work per HANDOFF-marketplace-conversion.md.

Session context:
- Task: decide between Option A/B/C for marketplace structure
- Completed: added 3 new skills to current markdown marketplace
- Decision pending: extend install.sh with --bundle mode (Option C, recommended) vs full plugin migration (Option B)
- If pursuing Option C: extend install.sh, reorganize skills with bundle/ subdirs, test

Previous handoff: ~/workspace/personal/claude-skills/HANDOFF-marketplace-conversion.md

Start by deciding: Option A (keep as-is), Option B (full migration), or Option C (hybrid --bundle mode). If Option C, begin extending install.sh to detect and install bundle/ subdirectories.
```
