# Debug Triage Skill

Structured debugging with issue tracking, agent escalation, and postmortem generation.

## Why Structured Debugging

Debugging often devolves into a chaotic loop: try something, fail, try something else, lose track of what was attempted. Debug Triage brings structure to this process by:

- **Tracking every issue** with status, time spent, and root cause
- **Recognizing when you're stuck** and offering escalation paths
- **Generating postmortems** so knowledge isn't lost when the session ends
- **Delegating to background agents** so you can keep working while hard problems are investigated

## Workflow

### 1. Start a Session

```
/debug-start
```

Creates `.debug/session-YYYY-MM-DD-HHMM.md` in your project root. All issues discovered during the session are tracked here.

### 2. Triage Issues

As bugs are found, each gets a numbered entry with status tracking:

- **investigating** - actively working on it
- **fixed** - root cause found and fix applied
- **deferred** - captured for later
- **escalated** - handed to a background agent

### 3. Escalate When Stuck

After 2-3 failed attempts on the same issue, Claude suggests options:

- **Escalate** - spawn a background agent to investigate in parallel
- **Defer** - capture what's known and move on
- **Keep trying** - continue with a new approach

This is always a suggestion, never forced. You choose.

### 4. Generate Postmortem

```
/debug-end
```

Produces `.debug/postmortem-YYYY-MM-DD-HHMM.md` with:

- Counts: how many issues were fixed, deferred, or escalated
- One-line summaries of each fix
- Deferred items with context for follow-up
- Agent findings from escalated issues
- Next steps checklist

## Installation

```bash
./install.sh debug-triage >> ./CLAUDE.md
```

This appends the debug-triage instructions to your project's CLAUDE.md so Claude Code follows the structured debugging process.

## Example Session

You're debugging a service that fails on startup. Three issues surface:

**Issue 1: Missing environment variable** (fixed)
- Symptoms: crash on startup with `KeyError: 'DATABASE_URL'`
- Root cause: `.env` file missing the variable
- Fix: added `DATABASE_URL` to `.env.example` and local `.env`

**Issue 2: Connection timeout to Redis** (escalated)
- Tried: checked Redis container status (running), verified port (correct), tested with redis-cli (hangs)
- After 3 failed attempts, Claude suggests escalation
- You choose to escalate; background agent investigates network config
- Agent finds: Docker network DNS resolution broken after compose restart
- Fix applied from agent findings

**Issue 3: Deprecation warning flooding logs** (deferred)
- Non-critical, just noisy
- Captured the warning text and library version for follow-up
- Deferred to a separate cleanup task

Session postmortem captures all three with their resolutions.

## Integration with Handoff

Debug Triage integrates with the handoff skill's `debug-fork` type. When you use `/handoff --reason debug-fork` during an active debug session:

- The session file is referenced in the handoff
- Deferred and escalated issues provide context for the debug track
- The next session starts with full knowledge of what was tried

## Files Created

All debug files live in `.debug/` in your project root:

```
.debug/
  session-2026-02-15-1430.md    # Session log with all issues
  postmortem-2026-02-15-1530.md  # Summary after session ends
```

Add `.debug/` to `.gitignore` if you don't want session logs in version control, or commit them if you want a debugging history.

## Advanced: GitHub Publishing

For teams that want to track recurring issues, postmortems can be published as GitHub Issues. This is optional and not automated -- simply copy the postmortem content into a GitHub Issue when a debugging session reveals systemic problems worth tracking across the team.
