---
description: "Ship the current branch as a PR with auto-merge enabled (global-claude project ship-it)"
argument-hint: "[--base <branch>]"
allowed-tools: ["Bash", "Read"]
---

# Ship It (global-claude)

Project-level ship-it for the `global-claude` repo. Runs after `/prep-pr` finishes its self-review and quality gates. Creates a PR, enables auto-merge, registers a monitor, and runs the finalize verification.

**Arguments:** "$ARGUMENTS"

This repo has no project-specific quality gates beyond what `/prep-pr` already runs (no Python, no tests for skill markdown). The ship sequence is the standard one.

---

## Step 1: Parse base branch

Default to `main`. Override with `--base <branch>` if provided.

## Step 2: Confirm branch is pushed

```bash
BRANCH=$(git branch --show-current)
git push -u origin "$BRANCH" 2>&1
```

If push fails (e.g., diverged), BLOCK — do not force-push without explicit user approval.

## Step 3: Create the PR

Read the latest commit message and recent commits to draft a PR title + body.

```bash
TITLE=$(git log --format='%s' -1)
RANGE_BODY=$(git log --format='- %s' "origin/main..HEAD")
```

Create the PR with `gh pr create`:

```bash
gh pr create \
  --base "${BASE:-main}" \
  --head "$BRANCH" \
  --title "$TITLE" \
  --body "$(cat <<EOF
## Summary

$RANGE_BODY

## Test plan

- [ ] Verification grep checks pass (see PR-specific notes if applicable)
- [ ] Skill markdown renders correctly
- [ ] No regressions in /auto-dev or other affected commands

🤖 Shipped via /prep-pr + project /ship-it
EOF
)"
```

If the body needs richer content (e.g., for a specific PR), the upstream `/prep-pr` invocation should pass it via context — this template is the default.

## Step 4: Enable auto-merge

```bash
PR_NUMBER=$(gh pr view --json number -q .number)
gh pr merge "$PR_NUMBER" --auto --squash
```

## Step 5: Register PR monitor

If `${CLAUDE_PLUGIN_ROOT}/scripts/pr_monitor_register.py` exists, register the PR for monitoring. If not, skip silently — monitor is optional for this repo.

```bash
if [ -x ${CLAUDE_PLUGIN_ROOT}/scripts/pr_monitor_register.py ]; then
  ${CLAUDE_PLUGIN_ROOT}/scripts/pr_monitor_register.py "$PR_NUMBER" 2>&1 || echo "(monitor registration optional; skipping on error)"
fi
```

## Step 6: Run finalize verification

This is the contract that proves /ship-it actually completed its side effects. /prep-pr will re-run this and require the JSON to show `status: "ok"` and a non-null `pr_number`.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/prep_pr_finalize.py verify --require-automerge --json
```

Print the JSON output verbatim — do not summarize.

---

## Failure modes

- **Push fails (diverged):** BLOCK. User must rebase or merge main first.
- **PR creation fails:** BLOCK with the `gh` error verbatim.
- **Auto-merge enable fails:** BLOCK — the PR exists but auto-merge isn't on; don't silently leave it unset.
- **Finalize verification fails:** BLOCK with the JSON; do not paper over.

No fallbacks. No silent retries. Errors surface to the user via /prep-pr's BLOCK handling.
