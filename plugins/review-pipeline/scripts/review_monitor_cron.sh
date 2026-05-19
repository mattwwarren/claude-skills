#!/usr/bin/env bash
# Cron entrypoint for /review-monitor.
#
# TEMPLATE — copy and customize the marked variables below before scheduling.
# Originally written for macOS (uses BSD `stat -f` / `date -v`). Linux users:
# swap `stat -f %m` for `stat -c %Y` and `date -v-1d` for `date -d '1 day ago'`.
#
# - Gates on Mon-Fri 8a-6p local (machine TZ).
# - Cheap precheck before spending tokens: pending registrations + gh search
#   for any PR updated since the last successful fire. Skips the claude
#   invocation when there's no signal.
# - On non-zero claude exit, escalates via $ESCALATE_CMD (rate-limited to one
#   notification per $ERROR_DM_COOLDOWN seconds).

set -uo pipefail

# ---- CUSTOMIZE THESE ----
REPO=owner/repo                                            # GitHub repo to watch
WORKDIR=~/workspace/owner/repo                             # Local checkout to cd into
LOG=~/Library/Logs/review-monitor.log                      # Log file (Linux: ~/.cache/review-monitor.log)
ESCALATE_CMD="~/.claude/scripts/notify_escalation.sh"      # Optional: script taking a message arg
# ----                  ----

ERR_MARKER=/tmp/review-monitor-last-error-dm
LAST_FIRE=~/.claude/.review-monitor-last-fire
ERROR_DM_COOLDOWN=3600

log() { echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') cron: $*" >> "$LOG"; }

H=$(date +%H)
D=$(date +%u)
if [[ $D -gt 5 || 10#$H -lt 8 || 10#$H -gt 18 ]]; then
  exit 0
fi

cd "$WORKDIR" || { log "cd $WORKDIR failed"; exit 0; }

# --- Precheck: skip the LLM session when nothing's likely actionable ---

PENDING_COUNT=$(find /tmp/review-monitor/pending/ -name '*.json' 2>/dev/null | wc -l | tr -d ' ')

if [[ -f "$LAST_FIRE" ]]; then
  LAST_TS=$(date -u -r "$(stat -f %m "$LAST_FIRE")" '+%Y-%m-%dT%H:%M:%SZ')
else
  # First run after install — look back 24h to catch anything missed.
  LAST_TS=$(date -u -v-1d '+%Y-%m-%dT%H:%M:%SZ')
fi

GH_OUT=$(gh pr list --repo "$REPO" --search "updated:>=$LAST_TS" --state all --json number --limit 100 2>&1)
GH_EC=$?
if (( GH_EC != 0 )); then
  log "gh precheck failed (exit $GH_EC); firing to be safe"
  UPDATED_COUNT=999
else
  UPDATED_COUNT=$(echo "$GH_OUT" | jq 'length' 2>/dev/null || echo 999)
fi

if (( PENDING_COUNT == 0 && UPDATED_COUNT == 0 )); then
  log "precheck: no work (pending=0, updated=0 since $LAST_TS); skipping claude"
  exit 0
fi

log "precheck: firing (pending=$PENDING_COUNT, updated=$UPDATED_COUNT since $LAST_TS)"

# --- Invoke claude ---

claude --dangerously-skip-permissions \
  -p "Run /review-monitor. Execute the full poll cycle. Leave any code changes uncommitted (auto-fix agents push their own branches)." \
  --allowedTools Bash,Read,Write,Edit,Glob,Grep,Task,ToolSearch \
  --model sonnet \
  --max-budget-usd 15 \
  >> "$LOG" 2>&1
EC=$?

if [[ $EC -eq 0 ]]; then
  touch "$LAST_FIRE"
  exit 0
fi

# --- Hermes DM on failure (rate-limited) ---

NOW=$(date +%s)
LAST_ERR=$(stat -f %m "$ERR_MARKER" 2>/dev/null || echo 0)
if (( NOW - LAST_ERR < ERROR_DM_COOLDOWN )); then
  exit "$EC"
fi

TAIL=$(tail -n 40 "$LOG" 2>/dev/null | tail -c 1800)
if [[ -x "${ESCALATE_CMD/#~/$HOME}" ]]; then
  "${ESCALATE_CMD/#~/$HOME}" "review-monitor cron failed (exit ${EC}). Tail of ${LOG}:
\`\`\`
${TAIL}
\`\`\`" && touch "$ERR_MARKER" || true
else
  log "escalation skipped: $ESCALATE_CMD not executable"
fi

exit "$EC"
