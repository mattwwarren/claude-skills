---
name: wiki-install
description: Set up macOS launchd agents for wiki-ingest (every 4h) and wiki-lint (daily 6AM). Run once on the work machine after installing the knowledge-base plugin.
model: haiku
---

# /wiki-install

> Wiki system design inspired by Scott Cipriano (@scottpcipriano).

Installs macOS `launchd` agents that run `/wiki-ingest` and `/wiki-lint` on a schedule. Use this skill once after installing the `knowledge-base` plugin on a Mac to keep the wiki inbox processed and curated unattended.

**Platform support.** Mac-only. Per [ADR 0003](https://github.com/mattwwarren/claude-skills/blob/main/docs/adr/0003-scheduling-mechanism-for-filesystem-bound-workflows.md), systemd timers and portable cron are deferred until there is a non-Mac user with the need. The wiki workflow is filesystem-bound, so cloud-only routine surfaces (`/schedule` / `RemoteTrigger`) are not appropriate; `CronCreate` is session-scoped and not usable for unattended cadence on Linux CLI.

**Scope.** This skill schedules the two skills shipped by the `knowledge-base` plugin: `wiki-ingest` and `wiki-lint`. Other periodic skills (e.g. `pr-capability-ingest`, `doc-update-digest`, `claude-code-news`) live in other plugins and are not managed here.

## Configuration

| Variable | Default | Notes |
|----------|---------|-------|
| `KB_REPO_DIR` | current working directory at install time | Repo the scheduled `claude -p` invocations `cd` into. Must contain the `wiki/` tree the skills operate on. |
| `KB_LABEL_PREFIX` | `com.knowledge-base` | Prefix for `launchd` Label keys. Override if you have multiple wikis on one machine. |
| `KB_LOG_DIR` | `$HOME/Library/Logs` | Where the per-agent log files land. |
| `KB_INGEST_INTERVAL_SECONDS` | `14400` (4 hours) | `StartInterval` for `wiki-ingest`. |
| `KB_LINT_HOUR` | `6` | Hour of day (0-23, local time) for `wiki-lint`. |
| `KB_LINT_MINUTE` | `0` | Minute for `wiki-lint`. |
| `KB_INGEST_MODEL` | `sonnet` | Model passed to `claude -p` for ingest fires. |
| `KB_LINT_MODEL` | `sonnet` | Model passed to `claude -p` for lint fires. |
| `KB_INGEST_BUDGET_USD` | `5` | `--max-budget-usd` for ingest fires. |
| `KB_LINT_BUDGET_USD` | `5` | `--max-budget-usd` for lint fires. |

All variables are read once at install time. Re-run the skill to apply changes.

## Prerequisites

1. macOS (this skill exits early on any other platform).
2. The `knowledge-base` plugin is installed and `/wiki-ingest` + `/wiki-lint` are invocable.
3. `claude` is on `PATH` — verify with `which claude`.
4. `${KB_REPO_DIR}/wiki/` exists (the target the skills will read and write).

## Steps

### 1. Verify prerequisites

```bash
[ "$(uname -s)" = "Darwin" ] || { echo "wiki-install is macOS-only — see ADR 0003"; exit 1; }
which claude >/dev/null || { echo "claude not on PATH"; exit 1; }
KB_REPO_DIR="${KB_REPO_DIR:-$PWD}"
[ -d "${KB_REPO_DIR}/wiki" ] || { echo "no wiki/ under ${KB_REPO_DIR}"; exit 1; }
```

If any check fails, stop and resolve before continuing.

### 2. Resolve install paths

```bash
KB_LABEL_PREFIX="${KB_LABEL_PREFIX:-com.knowledge-base}"
KB_LOG_DIR="${KB_LOG_DIR:-$HOME/Library/Logs}"
KB_INGEST_INTERVAL_SECONDS="${KB_INGEST_INTERVAL_SECONDS:-14400}"
KB_LINT_HOUR="${KB_LINT_HOUR:-6}"
KB_LINT_MINUTE="${KB_LINT_MINUTE:-0}"
KB_INGEST_MODEL="${KB_INGEST_MODEL:-sonnet}"
KB_LINT_MODEL="${KB_LINT_MODEL:-sonnet}"
KB_INGEST_BUDGET_USD="${KB_INGEST_BUDGET_USD:-5}"
KB_LINT_BUDGET_USD="${KB_LINT_BUDGET_USD:-5}"

LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS" "$KB_LOG_DIR"
```

### 3. Write the `wiki-ingest` plist

Write to `${LAUNCH_AGENTS}/${KB_LABEL_PREFIX}.wiki-ingest.plist` using the values from Step 2. The `&amp;` entities are required — `launchd` parses XML, not shell.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${KB_LABEL_PREFIX}.wiki-ingest</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd ${KB_REPO_DIR} &amp;&amp; claude --dangerously-skip-permissions -p "Run /wiki-ingest. Process all unprocessed transcripts. Leave changes uncommitted." --allowedTools Bash,Read,Write,Edit,Glob,Grep --model ${KB_INGEST_MODEL} --max-budget-usd ${KB_INGEST_BUDGET_USD} &gt;&gt; ${KB_LOG_DIR}/wiki-ingest.log 2&gt;&amp;1</string>
    </array>

    <key>StartInterval</key>
    <integer>${KB_INGEST_INTERVAL_SECONDS}</integer>

    <key>RunAtLoad</key>
    <false/>

    <key>StandardOutPath</key>
    <string>${KB_LOG_DIR}/wiki-ingest.log</string>
    <key>StandardErrorPath</key>
    <string>${KB_LOG_DIR}/wiki-ingest.log</string>

    <key>SoftResourceLimits</key>
    <dict>
        <key>NumberOfFiles</key>
        <integer>10240</integer>
    </dict>

    <key>EnvironmentVariables</key>
    <dict>
        <key>HOME</key>
        <string>${HOME}</string>
        <key>PATH</key>
        <string>${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
```

### 4. Write the `wiki-lint` plist

Write to `${LAUNCH_AGENTS}/${KB_LABEL_PREFIX}.wiki-lint.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${KB_LABEL_PREFIX}.wiki-lint</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd ${KB_REPO_DIR} &amp;&amp; claude --dangerously-skip-permissions -p "Run /wiki-lint --full. Leave changes uncommitted." --allowedTools Bash,Read,Write,Edit,Glob,Grep --model ${KB_LINT_MODEL} --max-budget-usd ${KB_LINT_BUDGET_USD} &gt;&gt; ${KB_LOG_DIR}/wiki-lint.log 2&gt;&amp;1</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>${KB_LINT_HOUR}</integer>
        <key>Minute</key>
        <integer>${KB_LINT_MINUTE}</integer>
    </dict>

    <key>RunAtLoad</key>
    <false/>

    <key>StandardOutPath</key>
    <string>${KB_LOG_DIR}/wiki-lint.log</string>
    <key>StandardErrorPath</key>
    <string>${KB_LOG_DIR}/wiki-lint.log</string>

    <key>SoftResourceLimits</key>
    <dict>
        <key>NumberOfFiles</key>
        <integer>10240</integer>
    </dict>

    <key>EnvironmentVariables</key>
    <dict>
        <key>HOME</key>
        <string>${HOME}</string>
        <key>PATH</key>
        <string>${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
```

### 5. Load the agents

```bash
launchctl load "${LAUNCH_AGENTS}/${KB_LABEL_PREFIX}.wiki-ingest.plist"
launchctl load "${LAUNCH_AGENTS}/${KB_LABEL_PREFIX}.wiki-lint.plist"
```

### 6. Verify

```bash
launchctl list | grep "${KB_LABEL_PREFIX}"
```

Should show two entries: `${KB_LABEL_PREFIX}.wiki-ingest` and `${KB_LABEL_PREFIX}.wiki-lint`.

### 7. Test a manual run

```bash
launchctl start "${KB_LABEL_PREFIX}.wiki-ingest"
sleep 30
tail -50 "${KB_LOG_DIR}/wiki-ingest.log"
```

Should show the `wiki-ingest` skill executing. Check `${KB_REPO_DIR}/wiki/local/log.md` for a heartbeat entry.

## Uninstall

```bash
KB_LABEL_PREFIX="${KB_LABEL_PREFIX:-com.knowledge-base}"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

launchctl unload "${LAUNCH_AGENTS}/${KB_LABEL_PREFIX}.wiki-ingest.plist" 2>/dev/null
launchctl unload "${LAUNCH_AGENTS}/${KB_LABEL_PREFIX}.wiki-lint.plist" 2>/dev/null
rm -f "${LAUNCH_AGENTS}/${KB_LABEL_PREFIX}.wiki-ingest.plist"
rm -f "${LAUNCH_AGENTS}/${KB_LABEL_PREFIX}.wiki-lint.plist"
```

Log files at `${KB_LOG_DIR}/wiki-ingest.log` and `${KB_LOG_DIR}/wiki-lint.log` are left in place — delete them manually if desired.

## Troubleshooting

**"unknown error, possibly due to low max file descriptors"** — the `SoftResourceLimits.NumberOfFiles: 10240` key in each plist fixes this. If the error appears, confirm the key is present in the installed plist.

**Agent loads but never runs** — verify the right scheduling key: `wiki-ingest` uses `StartInterval` (seconds), `wiki-lint` uses `StartCalendarInterval` (time-of-day dict). Mixing them silently fails to fire.

**Missed runs while the Mac is asleep** — `launchd` runs once on wake for each missed interval. Expected behavior; no fix needed.

**Log file is empty** — confirm `${KB_LOG_DIR}` exists and is writable, and that the `StandardOutPath` / `StandardErrorPath` in the installed plist resolve to real paths (no unresolved `${...}`).

**Multiple wikis on one machine** — set `KB_LABEL_PREFIX` to a per-repo value (e.g. `com.knowledge-base.work`, `com.knowledge-base.personal`) before running the skill in each repo. Otherwise the second install overwrites the first.

## Non-Mac platforms

Linux and Windows are intentionally not supported by this skill. See [ADR 0003](https://github.com/mattwwarren/claude-skills/blob/main/docs/adr/0003-scheduling-mechanism-for-filesystem-bound-workflows.md) for the rationale. When a user with that need surfaces, a follow-up skill (systemd timer or cron equivalent) will be added in this same plugin.
