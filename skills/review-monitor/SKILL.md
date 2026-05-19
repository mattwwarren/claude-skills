
# Review Monitor

Poll monitored PRs for thread activity, perform delta reviews on new pushes, approve when all threads are addressed, and nudge authors who haven't responded.

When running from the checked-out `global-claude` repo or a Codex wrapper, prefer repo-relative script paths like `scripts/review_monitor.py`. The `~/.claude/scripts/...` examples below remain valid installed-path fallbacks.

**Arguments:** "$ARGUMENTS"


## Argument Routing

Parse `$ARGUMENTS` before doing anything else:

| Input | Action |
|-------|--------|
| Empty | Run the full poll cycle (Steps 1–5 below) |
| `status` | Run `scripts/review_monitor.py status` (or the installed `~/.claude/...` path) and display output, then stop |
| `drop <N>` | Run `scripts/review_monitor.py drop <N>` (or the installed `~/.claude/...` path) and confirm removal, then stop |
| Anything else | Load state via `scripts/review_monitor.py status --json` (or the installed `~/.claude/...` path), then answer the query conversationally using that data |

**Natural language query examples:**
- "where are my PRs?" — list each PR with author role (reviewer/author), open thread count, and last activity
- "who hasn't made fixes?" — list PRs where you are the reviewer and threads remain unaddressed past 24h
- "what's blocking approval on 123?" — detail open threads on PR 123, their age, and nudge status

If the argument is unrecognized and doesn't look like a natural language question, print usage and stop.


## Poll Cycle

### Step 0: Consume Pending Registrations

Projects' `ship-it.md` can drop PR announcement metadata into `/tmp/review-monitor/pending/` as a file-drop handoff (no dependency on this repo). Consume them before loading state:

```bash
~/.claude/scripts/review_monitor.py consume-pending
```

Returns `{"consumed": [...], "skipped": [...], "purged": [...]}`. Consumed keys are now registered as author-role monitored PRs with `slack_channel` + `slack_ts` populated. Safe to run always — no-op when the inbox is empty.

### Step 0.5: Auto-Discover This Week's Author PRs

Pick up any open PRs you authored in the past 7 days that aren't already monitored. Idempotent — registers only the new ones.

```bash
~/.claude/scripts/review_monitor.py discover \
  --repo genhealth/etl \
  --repo-path /Users/matthew/workspace/genhealth/etl \
  --days 7
```

Returns `{"registered": [...], "skipped": [...], "repo": "..."}`. All etl worktrees roll up to the single `genhealth/etl` repo; the canonical clone path goes in `--repo-path`. The dispatched agent in Step 4 resolves the right worktree from there.

### Step 1: Load Monitored PRs

```bash
~/.claude/scripts/review_monitor.py status --json
```

This returns a JSON array of monitored PRs. Each entry includes:

| Field | Description |
|-------|-------------|
| `pr_number` | GitHub PR number |
| `repo` | `owner/repo` slug |
| `role` | `reviewer` or `author` |
| `open_threads` | Count of unresolved review threads |
| `has_delta_diff` | `true` if new commits have landed since last review |
| `delta_diff` | The unified diff of new changes (populated when `has_delta_diff: true`) |
| `touched_threads` | List of tracked thread IDs whose file:line a new commit changed. **Candidate** signal only — `check` does NOT mark these addressed. The Step 3 confirmation pass verifies each and calls `confirm-thread` for the ones genuinely resolved. |
| `nudge_ok` | `true` if it's appropriate to nudge (last nudge was >24h ago or never sent) |
| `all_addressed` | `true` if all threads are marked resolved |
| `head_sha` | Current HEAD SHA |
| `failing_checks` | List of failed CI checks (each `{workflow, name, conclusion, url}`) — populated by `check`, not `status` |
| `pending_checks_count` | Count of in-progress / queued CI checks — populated by `check`, not `status` |
| `ci_ok` | `true` when no failing checks (pending checks do not flip this) — populated by `check`, not `status` |
| `merge_state_status` | GitHub mergeability state: `CLEAN`, `DIRTY` (conflicts), `BEHIND` (needs rebase), `BLOCKED`, `UNSTABLE`, `HAS_HOOKS`, `UNKNOWN` — populated by `check`, not `status` |
| `merge_blocked` | `true` when `merge_state_status` is `DIRTY`, `BEHIND`, or `BLOCKED` — populated by `check`, not `status` |
| `attention_state` | Author-role only: `merge_blocked` / `ci_failing` / `changes_requested` / `ready_to_approve` / `null`. Drives notification routing. `changes_requested` fires on any of: unresolved inline threads, top-level `reviewDecision == "CHANGES_REQUESTED"`, or a comment-review fallback flagged by the Step 4b' classifier. |
| `change_request_source` | When `attention_state == "changes_requested"`: `"inline"` (unresolved thread), `"formal"` (`reviewDecision == "CHANGES_REQUESTED"`), or `"comment"` (Step 4b' classifier flagged a `COMMENTED` review as requesting changes). `null` otherwise. Routes the auto-fix prompt. |
| `pending_comment_reviews` | List of `{review_id, author, submitted_at, body}` for non-bot `COMMENTED` reviews submitted after the latest push / formal review, not yet classified. **Only populated when no higher-priority signal is active** (the fallback gate). The Step 4b' classifier consumes this list. |
| `needs_local_ping` | `true` when the attention state has changed since the last peon-ping fired |
| `needs_escalation` | `true` when a Slack-bot DM should be sent this cycle (immediate for ci/merge, 15-min grace for ready_to_approve) |
| `slack_channel` / `slack_ts` / `slack_last_seen_ts` | Optional — present when the PR was announced to Slack via a ship-it file-drop |
| `is_draft` / `base_ref_name` | Populated by `check`. Used by `auto_fix_ok` gating — drafts (especially stacked ones) are skipped automatically. |
| `auto_fix_blocked_reason` | When `auto_fix_ok == false`, a short human-readable reason: `"daily cap reached"`, `"draft"`, or `"draft stacked on '<base>'"`. |

**If the array is empty:** Print "No PRs currently monitored." and stop.

### Step 2: Check Each PR

For each PR in the list, run:

```bash
~/.claude/scripts/review_monitor.py check <pr_number>
```

This refreshes thread state, resolves any threads that GitHub has auto-resolved, and returns updated fields for that PR. Use the refreshed data for all subsequent steps.

### Step 2b: Merged-PR Follow-up Tickets

When the `check` output for a PR has `completed: true`, `pr_state: "MERGED"`, AND `deferred_threads` is non-empty, the PR landed with one or more reviewer points that we replied-to-defer (matched `is_deferral` language — "follow up", "next PR", "later", etc.) but never resolved in-code. The author already deemed them out-of-scope for the merging PR; the merge would otherwise drop them on the floor.

For each `deferred_threads` entry create one Linear ticket via the Linear MCP plugin (`mcp__plugin_linear_linear__save_issue`):

- **Title:** `Follow-up from PR #<n>: <file>:<line>` (truncate file to basename if path is long)
- **Description:**
  ```
  Deferred during review of [PR #<n>](<pr_url>).

  **File:** `<file>:<line>`
  **Reviewer:** @<reviewer>
  **Reviewer comment:**
  > <reviewer_comment quoted line-by-line>

  **Our deferral reply:**
  > <deferral_reply quoted line-by-line>

  **GitHub thread:** <url>
  ```
- **Project:** route by repo / branch-prefix using the existing mapping the rest of the skill uses for ticketing (Platform for non-client work, otherwise the client project).
- **Assignee:** the PR's author (`gh pr view <n> --json author --jq .author.login`), mapped to their Linear user.

Skip the PR if `deferred_threads` is empty — no follow-ups needed.

After ticket creation, log a summary row: `#<n> | author | MERGED — N follow-up ticket(s) filed: <LIN-1234>, <LIN-1235>`.

The `check` call already ran `complete_pr` on the script side; nothing further to do for the monitoring state.

For PRs with `completed: true` but `pr_state: "CLOSED"` (un-merged), skip — the work was abandoned and its deferrals went with it.

### Step 3: Delta Review (Reviewer Role Only)

For each PR where `role == "reviewer"` and `has_delta_diff == true`, run two passes in order:
**3a confirms** that new commits addressed open threads (moves the PR *toward* approval),
**3b scans** the delta for regressions the push introduced (kept deliberately narrow).

The delta diff is already scoped — `delta_diff` is `git diff <last_seen_sha>..<new_sha>`, the
incremental change only. Never re-review code outside it.

#### Step 3a: Confirm Thread Resolution

The `check` output lists `touched_threads` — tracked thread IDs whose file:line a new commit
changed. A touched line is a **candidate** for resolution, not a confirmation: the commit may
have changed that line for an unrelated reason. `check` does NOT mark these addressed — this
pass does, after verifying.

**If `touched_threads` is empty:** skip to Step 3b.

**Otherwise:**

1. Fetch the originating review comment for each touched thread (the body of the first comment
   in the thread) via `gh api graphql` against the PR's `reviewThreads`.
2. Spawn ONE confirmation Task agent (sonnet model) covering all touched threads. Use this
   prompt verbatim:

```
You are verifying whether new commits on a pull request addressed specific review comments.
You are NOT reviewing code quality and NOT looking for new issues — only judging, per thread,
whether the change resolves the concern the reviewer raised.

DELTA DIFF (the only changes since the last review cycle):
<insert delta_diff here>

THREADS TO VERIFY (each is a review comment whose file:line the delta touched):
<for each touched thread, insert: thread_id, file, line, and the original comment body>

OUTPUT RULES — follow these exactly:
1. For each thread, return a JSON object on its own line:
   - "thread_id": the thread ID
   - "verdict": "ADDRESSED" | "NOT_ADDRESSED" | "UNCLEAR"
   - "reason": one sentence grounded in the delta diff
2. ADDRESSED — the delta makes a change that resolves the reviewer's specific concern.
3. NOT_ADDRESSED — the delta touched these lines but the concern still stands (or the change
   is unrelated to what the reviewer raised).
4. UNCLEAR — you cannot tell from the delta alone whether the concern is resolved.
5. Be strict: when in doubt, UNCLEAR or NOT_ADDRESSED. A false ADDRESSED approves a PR early.
6. Output ONLY these JSON lines, one per thread. No other text.
```

3. Act on each verdict:
   - **ADDRESSED** → mark the thread resolved:
     ```bash
     ~/.claude/scripts/review_monitor.py confirm-thread <pr_number> --repo <repo> --thread <thread_id>
     ```
     This sets `code_changed`, re-runs the status transition, and prints a JSON summary
     (`status`, `all_addressed`, `unaddressed`). Use the refreshed `status` in Step 4 instead of
     the now-stale value from `check`.
   - **NOT_ADDRESSED** → leave the thread open. Optionally post a one-line reply on the thread
     noting it still looks unresolved and why (the agent's `reason`). Do not open a new thread.
   - **UNCLEAR** → leave the thread open, no reply. It will be re-evaluated next cycle if
     another commit touches it, or the author can resolve/reply directly.

#### Step 3b: Regression Scan

Spawn a bug-hunter Task agent (sonnet model) with the delta diff. Use this prompt verbatim:

```
You are a focused bug-hunter checking whether an incremental push to a pull request BROKE or
SKIPPED something. You are NOT auditing the codebase and NOT re-reviewing previously reviewed
code. Scope: only the delta diff below. It is not your job to find every imperfection — only
regressions the push itself introduced.

DELTA DIFF:
<insert delta_diff here>

OUTPUT RULES — follow these exactly:
1. Report ONLY MUST_FIX problems: a correctness bug, a security issue, or a breaking change
   that this push introduced. Do NOT report style, maintainability, or "should fix" items —
   those are out of scope for a delta pass.
2. If you find ZERO MUST_FIX issues, respond with exactly: NO_ISSUES
3. EVIDENCE DISCIPLINE: every finding MUST quote, verbatim, an added (`+`) line from the delta
   diff under an "evidence" field. A finding without a verbatim `+`-line quote is dropped.
4. For each finding, return a JSON object on its own line:
   - "path": file path relative to repo root
   - "line": line number in the NEW version of the file (from the diff's +N line numbers)
   - "body": 1-2 sentence description — the bug, why it matters, and the specific fix
   - "evidence": verbatim quote of the offending added line from the delta diff
5. Output ONLY these JSON lines, one per finding. No other text.
6. Be direct. No hedging. State the problem and the fix.
```

**Validate evidence before posting.** For each finding, confirm the `evidence` quote appears
verbatim in `delta_diff`. Drop any finding whose quote does not match — it's a hallucination
from a loose read.

**If the agent returns `NO_ISSUES`** (or all findings were dropped): no new threads. Continue to Step 4.

**If validated findings remain:** Post them as inline review comments, then submit:

```bash
# For each validated finding:
gh review comment <pr_number> --file <path> --line <line> --body "**[Delta Review]** <body>"

# Submit the review
gh review submit <pr_number> --comment --body "Delta review of new commits — see inline comments.

🤖 Generated with [Claude Code](https://claude.ai/code)"
```

After posting, register the new threads so nudge and approval logic tracks them:

```bash
~/.claude/scripts/review_monitor.py register <pr_number> \
  --role reviewer \
  --repo <repo> \
  --repo-path <repo_path> \
  --sha <new_sha> \
  --threads <thread_id1> <thread_id2> ... \
  --thread-details '[{"id":"<thread_id1>","file":"<path>","line":<line>}, ...]'
```

(Use the thread IDs and metadata returned by `gh review comment`; pass all newly posted thread IDs via `--threads` and their details via `--thread-details`.)

### Step 4: Evaluate and Act

For each PR, apply the logic for its role:

#### Reviewer PRs

**All threads addressed (`all_addressed == true`):**

Approve the PR:

```bash
gh review submit <pr_number> --approve --body "All threads addressed. Thanks!

🤖 Generated with [Claude Code](https://claude.ai/code)"
```

Then mark it complete:

```bash
~/.claude/scripts/review_monitor.py complete <pr_number> --reason approved
```

**Threads remain unaddressed + `nudge_ok == true`:**

Post **one** PR-level nudge comment (not per-thread). Per-thread replies generate N notifications and feel like pressure rather than encouragement; a single comment achieves the same outcome without the spam:

```bash
gh pr comment <pr_number> --repo <repo> --body "Hey — checking in on the open review threads here. Happy to clarify any suggestion that's unclear, or hear if you'd prefer to handle something differently."
```

Then record the nudge:

```bash
~/.claude/scripts/review_monitor.py record-nudge <pr_number>
```

**Threads remain unaddressed + `nudge_ok == false`:** Skip. A nudge was sent recently; no action.

#### Author PRs

Author-role PRs route by `attention_state` from the `check` result. Three side-effect channels:

- **Auto-fix dispatch:** background `Task` agent (sonnet) fixes the underlying problem and pushes a new commit. Capped at 2 attempts/PR/day (`auto_fix_ok == false` when capped).
- **Channel bump:** stale `ready_to_approve` PRs accrue business-hour minutes; once ≥ 240 (4 working hours, 8a–6p ET Mon–Fri) they get batched into a single #product-umpa post via Slack MCP.
- **Hermes DM:** for human-in-the-loop signals only — `dm_escalation_reason` is `"loop"` (cap hit) or `"week_old"` (PR ≥ 7 days old). The user can't self-DM via MCP, so Hermes bot is the route.

The local peon-ping is a separate Tier 0 — fires once on every `needs_local_ping == true` to make state changes audible.

**Step 4a: Local ping when `needs_local_ping == true`:**

```bash
~/workspace/personal/global-claude/hooks/peon-ping/scripts/notify.sh \
  "PR #<pr_number> (<title>) — <attention_state>" \
  "Review Monitor" \
  red
~/.claude/scripts/review_monitor.py mark-notified <pr_number> \
  --repo <repo> --state <attention_state>
```

**Step 4b': Classify pending comment reviews (fallback change-request signal).**

GitHub records "Comment"-radio reviews as `state: COMMENTED`, which does **not** move `reviewDecision` off `REVIEW_REQUIRED` — so without this step a PR with a reviewer asking for changes via a plain comment review sits idle waiting for a formal CR or approval that may never come.

The `check` output surfaces `pending_comment_reviews` only when no higher-priority signal is already active (the fallback gate is enforced at source — `merge_blocked` of the code-fixable kind, `ci_failing`, or inline / formal `changes_requested` will all suppress it). So if the list is non-empty, this is the last actionable signal before the PR drops to a passive channel-bump.

For each PR with non-empty `pending_comment_reviews`:

1. Spawn ONE classifier Task agent per PR (`subagent_type: "general-purpose"`, `model: "sonnet"`, foreground — the verdict gates the next step), batching all of that PR's pending reviews into a single prompt:

```
You are classifying pull-request review comments. For each review below, decide
whether the author is requesting changes to the code (REQUESTS_CHANGES) or just
making a non-actionable comment like "lgtm", "nice", "fyi", a question for their
own understanding, or an approval-equivalent (NEUTRAL).

REQUESTS_CHANGES signals: "should", "could you", "needs", "missing",
"before merging", "concerned", "nervous", "blocker", "let's", suggestions to
modify code, asks to add/remove code, requests for more tests or more coverage,
"I'd feel better if".

NEUTRAL signals: "lgtm", "nice", "fyi", "wow", praise, generic questions for
their own context, off-topic chat.

When in doubt, NEUTRAL — false positives trigger an unwanted auto-fix loop.

REVIEWS (one per object — review_id, author, body):
<insert reviews here>

OUTPUT: one JSON object per review on its own line, no other text:
  {"review_id": "...", "verdict": "REQUESTS_CHANGES" | "NEUTRAL", "reason": "one sentence"}
```

2. For each verdict, persist it (so we never re-classify the same review):

```bash
~/.claude/scripts/review_monitor.py mark-comment-review <pr_number> \
  --repo <repo> --review-id <review_id> \
  --classification {requests_changes|neutral}
```

3. If **any** review on the PR came back `REQUESTS_CHANGES`, re-fetch `check` for that PR — `attention_state` will now be `changes_requested` with `change_request_source == "comment"`, and the existing Step 4b auto-fix branch picks it up. If all came back `NEUTRAL`, the PR stays `ready_to_approve` and falls through to channel-bump as usual.

Cycle summary row format:
`#<N> | author | comment-review classified REQUESTS_CHANGES (<author>); auto-fix dispatched`
or `#<N> | author | comment-review classified NEUTRAL (<author>); no action`

**Step 4b: Auto-fix dispatch.**

When `auto_fix_ok == true` AND any of:
- `attention_state == "ci_failing"`
- `attention_state == "merge_blocked"` AND `merge_state_status in {"DIRTY", "BEHIND"}` (i.e., conflicts or branch-behind — code-fixable)
- `attention_state == "changes_requested"`

The script enforces draft-skipping at the source: `auto_fix_ok` is `false` whenever `is_draft == true` (with `auto_fix_blocked_reason` populated as `"draft"` or `"draft stacked on '<base>'"`). Drafts are WIP by definition; stacked drafts would also rebase onto the wrong base. Note the reason in the cycle summary and move on.

`merge_state_status == "BLOCKED"` is **NOT auto-fixable** — it means missing required reviews / branch protection / unmet status checks. Fall through to channel-bump (Step 5a) or DM (Step 4d) instead.

For `changes_requested`: first fetch each thread's originator to skip bot threads. The skill replies on human threads only (sourcery is excessive most of the time and gets ignored silently). Use `gh api` to inspect the first comment author of each unaddressed thread:

```bash
gh api "repos/<repo>/pulls/<pr_number>/reviews" \
  --jq '.[] | select(.state=="CHANGES_REQUESTED" or .state=="COMMENTED") | {author: .user.login, body: .body, id: .id}'
```

A login is a bot if it ends with `[bot]`, `-ai`, or `-bot`, or matches a known list (`sourcery-ai`, `coderabbitai`, `dependabot`, `renovate`, `github-actions`, `codecov-commenter`). **Exception:** `sonarqubecloud` / `sonarcloud` / `sonarqube` (with or without `[bot]`) BLOCK merge and must be treated as human-equivalent — fix their findings, do not skip.

Dispatch one background agent per PR (parallel-safe — each operates in its own worktree). Use `Task` tool with `subagent_type: "general-purpose"`, `model: "sonnet"`, `run_in_background: true`.

**Prompt template** (substitute placeholders per PR):

```
Fix PR #<N> in <repo>. Branch: <branch>. URL: <url>

State: merge_state_status=<DIRTY|BEHIND|UNKNOWN>, ci_ok=<true|false>.
Failing checks (if any):
- <workflow>/<name>: <conclusion> — <details_url>

Open review threads to address (if changes_requested):
- file=<path> line=<line> author=<login>: <body>
(Skip threads from bots [`[bot]`, `-ai`, `-bot` suffix or in known bot list];
sonarqube/sonarcloud are NOT bots for this purpose — their findings block merge.)

If `changes_requested` fired with no inline threads, the signal source is set on
the check output as `change_request_source`:

- `change_request_source == "formal"` — a top-level "Request changes" review.
  Pull the body and address it:
    gh api "repos/<repo>/pulls/<N>/reviews" \
      --jq '.[] | select(.state=="CHANGES_REQUESTED") | {author: .user.login, body: .body, submittedAt: .submittedAt}'
  Treat the latest non-bot CHANGES_REQUESTED review as the request to address.

- `change_request_source == "comment"` — a top-level `COMMENTED` review that the
  Step 4b' classifier flagged as REQUESTS_CHANGES. Pull the body:
    gh api "repos/<repo>/pulls/<N>/reviews" \
      --jq '.[] | select(.state=="COMMENTED") | {author: .user.login, body: .body, id: .id, submittedAt: .submittedAt}'
  Treat the latest such review as the request. After pushing fixes, do NOT
  try to re-request review (no formal CR was filed); instead post a reply on
  the review summarizing what you addressed:
    gh api -X POST "repos/<repo>/pulls/<N>/reviews/<review_id>/comments" -f body='<summary>'
  Or, if `gh review reply <review_id>` is available, use that.

REPO ROOT: <repo_path>

WORKTREE SETUP (always — required for parallel safety):
1. Run `git worktree list` from <repo_path>
2. If a worktree already tracks <branch>, cd into it
3. Otherwise create one:
   git worktree add <repo_path>/.claude/worktrees/autofix-<N> <branch>
   cd into it
4. Symlink CLAUDE.local.md and .claude/settings.local.json from <repo_path> if present (skip if missing). Symlink .env if present.

WORK:
- Rebase against origin/main: `git fetch origin && git rebase origin/main`
- Resolve conflicts. If domain knowledge is required, STOP and report — do NOT guess.
- **If you discover the branch's commits are already in main (squash-merged):** STOP and report — do NOT skip commits or force a no-op rebase. The user will close the PR. Signs: every conflicted file's HEAD-side already contains your branch's intended change; commits in your branch reference work the user has already shipped.
- For ci_failing: read failure log via `gh run view <run_id> --log-failed`, fix root cause. Do NOT skip tests, do NOT add # noqa or # type: ignore without reason.
- For changes_requested human threads: apply suggested fixes when correct. If a suggestion is unclear or wrong, post a substantive technical reply explaining why via `gh review reply <thread_id>` (this is NOT a nudge — it's clarifying disagreement on a real finding).
- Push: `git push --force-with-lease origin <branch>` (rebase rewrites history; --force-with-lease is required and safe — refuses to overwrite if remote moved unexpectedly)
- **For changes_requested (after pushing fixes): re-request review from every human who hit "Request changes".** GitHub does not auto-clear `CHANGES_REQUESTED` when new commits land — the PR stays stuck until the reviewer is re-pinged. Identify the requesters and re-request:
  ```bash
  REQUESTERS=$(gh api "repos/<repo>/pulls/<N>/reviews" \
    --jq '[.[] | select(.state=="CHANGES_REQUESTED") | .user.login] | unique | .[]')
  for r in $REQUESTERS; do gh pr edit <N> --repo <repo> --add-reviewer "$r"; done
  ```
  Skip bot logins (`[bot]`, `-ai`, `-bot` suffix; sonarqube/sonarcloud are not bots for this purpose but they also don't need re-pinging — they'll re-scan automatically on push).

CONSTRAINTS:
- Do NOT amend commits, do NOT --no-verify, do NOT modify CI configs or coverage thresholds
- 70/30 rule (certainty threshold): act when you're ≥70% sure of the right move; stop and report when you're below. Don't wait for 100% before acting on something you understand, and don't plow ahead on a guess. Sub-70% certainty on a conflict resolution, a missing test, or a "fix" is a STOP signal, not a "try anyway" signal.
- Verification is not optional. Pushing without running the relevant tests / confirming green / reading the diff back means you are NOT done. The push is the last step, not the only step.
- No hard time cap. If you're making real progress, keep going. If you're spinning — repeating the same approach with no new information after 3 iterations — STOP and report what's blocking. System resources will catch infinite loops; logic loops are on you to recognize.

DELIVERABLE: brief report — new HEAD SHA, what was fixed, verification output (test counts, lint clean), push confirmation. Or: stopped-because-X with the specific blocker.
```

After dispatching, record the attempt:

```bash
~/.claude/scripts/review_monitor.py record-auto-fix <pr_number> --repo <repo>
```

**Step 4c: Channel bump (deferred to batch — see Step 5b).**

When `needs_channel_bump == true`, do nothing here — the batch step at the end of the cycle posts a single #product-umpa message with all pending bumps.

**Step 4d: Hermes DM when `dm_escalation_reason` is set.**

Reason-specific message:

| Reason | Message template |
|--------|------------------|
| `loop` | `PR #<n> (<title>) — auto-fix loop detected (<N> attempts today, still <attention_state>). Needs your eyes. <pr_url>` |
| `week_old` | `PR #<n> (<title>) — open ≥ 7 days, still <attention_state>. <pr_url>` |

```bash
~/.claude/scripts/notify_escalation.sh "<message>"
~/.claude/scripts/review_monitor.py mark-escalated <pr_number> --repo <repo>
```

**Step 4e: Read Slack announcement thread when `slack_channel` is set.**

If `slack_channel` is non-null, call the Slack MCP tool `slack_read_thread` with `channel=slack_channel`, `thread_ts=slack_ts`, `oldest=slack_last_seen_ts`. For each new message authored by someone other than the current user, add a line to the cycle summary. Then advance the cursor:

```bash
~/.claude/scripts/review_monitor.py update-slack-cursor <pr_number> \
  --repo <repo> --last-seen-ts <newest returned ts>
```

**First-cycle burst prevention:** On a freshly-upgraded state file run `~/.claude/scripts/review_monitor.py catchup` before the first cycle to avoid N concurrent pings.

### Step 5a: Batch Stale-Review Channel Bumps

After all per-PR processing, query for any author PRs that have accrued ≥ 4 business hours in `ready_to_approve` without a recent bump:

```bash
~/.claude/scripts/review_monitor.py pending-channel-bumps
```

Returns a list of `{repo, pr_number, business_minutes_in_state, last_channel_bump_at}`. If non-empty, fetch each PR's title + URL and post **a single batched message** to `#product-umpa` (channel ID `C067W2M3N1H`) using the Slack MCP tool `slack_send_message`.

Message format (one PR per bullet, no preamble of who/why):

```
PRs ready for review:
• <PR #N — title> <pr_url>
• <PR #M — title> <pr_url>
```

After posting (one MCP call total), record each bump:

```bash
~/.claude/scripts/review_monitor.py record-channel-bump <pr_number> --repo <repo>
```

Cooldown: each PR is eligible for re-bumping after 24h (handled by `pending-channel-bumps`). If the user merges or someone reviews, the next `check` advances state out of `ready_to_approve` and the PR drops off this list naturally.

**Step 4e: Promote drafts whose dependency has landed.**

Author drafts in this repo are not WIP — they're either standalone (based on `main`) or stacked on another open branch. Each cycle, promote any author draft whose base is ready.

For each monitored PR where `role == "author"`:

1. Check whether the PR is still a draft and fetch its base:
   ```bash
   gh pr view <pr_number> --json isDraft,baseRefName,headRefName,title,reviewRequests \
     --jq '{isDraft, baseRefName, headRefName, title, reviewers: [.reviewRequests[] | (if .login then .login else .name end)]}'
   ```
   If `isDraft == false`, skip — already promoted.

2. **WIP check** — if `headRefName` matches `(?i)wip` or `title` matches `^\[?WIP\]?` (e.g. `WIP:`, `[WIP]`), leave as draft. The author has explicitly marked it as work-in-progress. Add a row to the Step 5 summary: `Held as draft (explicit WIP marker)`.

2a. **Author-review-required check** — if `headRefName` starts with `docs/`, leave as draft. These are auto-drafted by the `doc-debt-branches` weekend pass (`branch_prefix: "docs"`) and are proposals that need the author's eyes before reviewers see them. The author opens them deliberately when ready by running `gh pr ready` (or merging directly). Add a row to the Step 5 summary: `Held as draft (docs/ branch — author-review required)`.

3. **Dependency check** — determine if the PR is stacked:
   - If `baseRefName` is `main` or `master`: **not stacked**. Proceed to promotion.
   - Otherwise: find a PR whose head matches `baseRefName`:
     ```bash
     gh pr list --repo <repo> --state open --head <baseRefName> --json number,isDraft,state --jq '.[0]'
     ```
     - If that PR is still open: **dependency unmet**. Add a row to the Step 5 summary: `Held as draft (waiting on parent PR #<n>)`.
     - If no such PR is found (parent merged/closed and branch deleted): **dependency met**. Proceed to promotion. Note: the child's base may need to be retargeted to `main` if the parent's branch was deleted — GitHub usually does this automatically but check with `gh pr view`.

4. **Promote, request review, AND dispatch a same-cycle rebase:**
   ```bash
   gh pr ready <pr_number>
   ```
   Then, only if no reviewers are currently requested (`reviewers` array is empty from step 1):
   ```bash
   gh pr edit <pr_number> --add-reviewer genhealth/umpa
   ```
   The default reviewer is the `genhealth/umpa` team. Don't double-tag if reviewers were already set.

   Post a confirmation comment:
   ```bash
   gh pr comment <pr_number> --body "Promoting from draft to ready for review."
   ```

   **Then immediately dispatch a rebase agent for this PR** using the Step 4b auto-fix prompt template (Bash + `Task` tool, `subagent_type: "general-purpose"`, `model: "sonnet"`, `run_in_background: true`). Substitute the PR's branch and metadata. The agent's `git fetch && git rebase origin/main` is a no-op if the branch is already current, so this is safe even for never-stacked drafts. Increment the daily counter:
   ```bash
   ~/.claude/scripts/review_monitor.py record-auto-fix <pr_number> --repo <repo>
   ```

   Rationale: a promoted draft whose parent just merged is almost always DIRTY against `main`. Waiting for the next cron tick to discover DIRTY and dispatch a rebase adds an hour of lag for no benefit — we already know the rebase is needed at promotion time.

   Add a row to the Step 5 summary: `Promoted draft → ready, requested genhealth/umpa, dispatched rebase`.

This step is idempotent — running on an already-ready PR is a no-op (the `isDraft == false` check at step 1 returns early).

### Step 5: Summary

Print a summary table of all actions taken this cycle:

```
| PR    | Repo             | Role     | Action                        |
|-------|------------------|----------|-------------------------------|
| #123  | owner/repo       | reviewer | Approved (all threads resolved) |
| #456  | owner/repo       | reviewer | Nudged 2 threads              |
| #789  | owner/repo       | author   | 3 threads need your response  |
| #101  | owner/repo       | reviewer | Delta review posted (2 findings) |
```

If no actions were taken for a PR (e.g., waiting, `nudge_ok == false`), include a "No action" row so all monitored PRs are visible.


## Philosophy

**Never do co-workers' work.** The goal of monitoring is not to chase or pressure — it's to make it easy for authors to finish. If a suggestion is confusing, clarify it. If an alternative approach is better, say so. If the author disagrees, discuss it.

**Encourage, don't gatekeep.** Approval is the default outcome; review threads are questions, not roadblocks. Threads get resolved when the author either makes the change or explains why they won't.

**Nudge tone.** The default nudge message is deliberately light: "Hey — just checking in on this one. Happy to clarify if the suggestion is unclear or if you'd prefer to handle it differently." This is not a demand. It's an offer to help. Never use language that implies the author is blocked, wrong, or slow.

**Delta reviews are scoped, and bias toward closing.** When new commits land, the delta agents only ever see the incremental diff — never re-litigate already-reviewed code. The first pass (3a) *confirms* whether the push resolved open threads, which moves the PR toward approval. The second pass (3b) only catches MUST_FIX regressions the push introduced. It is not the monitor's job to find every flaw in a large PR — opening a steady drip of new threads while old ones sit unaddressed makes the bot adversarial. Confirm first, scan narrowly, and let SHOULD_FIX go.


## Scheduling

Runs automatically via launchd at `~/Library/LaunchAgents/com.matthew.review-monitor.plist`, which calls `~/.claude/scripts/review_monitor_cron.sh` on a fixed `StartInterval` of **3600 seconds (hourly)**.

Hourly polling matches the cadence of normal review feedback without generating noise. The prior 30-minute interval was reduced because (a) feedback rarely arrives at sub-hour resolution, (b) tier-1 peon-pings already fire on state changes between cycles, and (c) draft-stack promotion (Step 4e) is not time-critical.

To change the cadence, edit `StartInterval` in the plist and reload:

```bash
launchctl unload ~/Library/LaunchAgents/com.matthew.review-monitor.plist
launchctl load ~/Library/LaunchAgents/com.matthew.review-monitor.plist
launchctl list | grep review-monitor   # verify
```

Logs land in `~/Library/Logs/review-monitor.log`. The plist has no day-of-week or hour-of-day gating — it polls every hour, every day. Weekend / off-hours suppression is handled inside the cycle (peon-ping respects meeting-detect, Slack escalation respects the 15-minute grace timer for `ready_to_approve`).


## Notes

- The state file is managed by `review_monitor.py`. Do not edit it directly.
- `register` (called with `--threads` and `--thread-details` after delta review) merges newly posted comments into the tracked state so nudge and approval logic works correctly. It is idempotent: calling it again with overlapping thread IDs is safe.
- `complete --reason approved` removes the PR from monitoring. If merged without approval (e.g., author self-merged), the script will detect the closed state on the next `check` call and remove it automatically.
- `drop <N>` removes a PR from monitoring without taking any GitHub action — useful when you've handed off a review or no longer want to track a PR.
- The `gh review` CLI extension is required. Verify it's installed with `gh extension list | grep review`.
