# Debug Triage

Structured debugging with issue tracking, agent escalation, and postmortem generation. Transforms chaotic debugging into a methodical process.

## Session Lifecycle

1. **Start** - Create `.debug/session-YYYY-MM-DD-HHMM.md` in the project root
2. **Triage** - For each issue: track with status (investigating/fixed/deferred/escalated)
3. **End** - Generate postmortem in `.debug/` with summary and counts

Always write debug files to `.debug/` in the project root (local workspace). Never write to `~/.claude/`.

## Starting a Session

When `/debug-start` is invoked:

1. Create `.debug/` directory in project root if it does not exist
2. Create `.debug/session-YYYY-MM-DD-HHMM.md` using the session log template
3. Set frontmatter `started` to current UTC time, `status: active`
4. Display the session file path to the user
5. Begin tracking issues as they arise

Use the template from `templates/debug-triage/session-log.md` in the claude-skills directory.

## Issue Tracking

Track each issue in the session file using this format:

```markdown
### Issue N: [Brief title]
- **Status**: investigating | fixed | deferred | escalated
- **Time spent**: ~N min
- **Root cause**: [if known]
- **Fix**: [what was done, or why deferred]
- **Agent ID**: [if escalated]
```

Update issue status in the session file as work progresses. Keep descriptions concise.

### Status Definitions

| Status | Meaning |
|--------|---------|
| `investigating` | Actively working on this issue |
| `fixed` | Root cause identified and fix applied |
| `deferred` | Captured for later, moving on |
| `escalated` | Handed to a background agent |

## Soft Escalation Guidance

After 2-3 failed fix attempts on the same issue, suggest options to the user:

> "This is taking a while. Options:
> 1. **Escalate** - Spawn background agent to investigate while we move on
> 2. **Defer** - Capture what we know and move on
> 3. **Keep trying** - I have another idea..."

Rules for this suggestion:

- Suggest after 2-3 failed attempts on the same issue
- Suggest if visibly spinning without progress
- **NEVER force** the user to move on -- only offer options
- Let the user choose which path to take
- If user says "keep trying," respect that and continue

## Agent Escalation

When the user chooses to escalate an issue:

1. Spawn a background agent with the `Task` tool (`run_in_background: true`)
2. Include this information in the agent prompt:
   - Issue description and symptoms
   - What was already tried and results
   - Hypotheses already eliminated
   - Goal: find root cause or gather diagnostic info
3. Record the agent ID in the session file under "Running Agents"
4. Update the issue status to `escalated` with the agent ID
5. Periodically mention when escalated agents complete
6. Integrate agent findings back into the session log

### Escalation Prompt Format

```
Investigate: [issue description]

Context:
- Tried: [list of attempts and their results]
- Observed: [symptoms, error messages, logs]
- Eliminated: [hypotheses ruled out and why]

Goal: Find root cause or gather diagnostic info.
Report findings when complete.
```

### Running Agents Tracking

Maintain a "Running Agents" section in the session file:

```markdown
## Running Agents
- Agent abc123: Investigating Issue 2
- Agent def456: Root cause analysis for Issue 5
```

When an agent completes:
- Update its entry with results
- Update the corresponding issue with findings
- Remove from active list or mark as completed

## Ending a Session

When the user ends the debug session or invokes `/debug-end`:

1. Update session file frontmatter: `status: completed`, add `ended` timestamp
2. Generate postmortem at `.debug/postmortem-YYYY-MM-DD-HHMM.md`
3. Use the template from `templates/debug-triage/postmortem.md`
4. Fill in all counts and summaries from the session
5. Display the postmortem path and a brief summary to the user

### Postmortem Contents

The postmortem includes:

- **Summary** with duration and counts (fixed/deferred/escalated)
- **Fixed issues** list with title and one-line fix description
- **Deferred issues** list with title and reason for deferral
- **Escalated issues** list with title and agent findings (or "still investigating")
- **Next steps** checklist for follow-up work
- **Session reference** linking back to the full session file

## Integration with Handoff

If a debug session is active when `/handoff --reason debug-fork` is invoked:

- Include the session file path in the handoff
- Reference deferred and escalated issues as context
- The debug track handoff should reference relevant issue numbers from the session

## File Naming

| File | Pattern |
|------|---------|
| Session log | `.debug/session-YYYY-MM-DD-HHMM.md` |
| Postmortem | `.debug/postmortem-YYYY-MM-DD-HHMM.md` |

Use current UTC time for all timestamps.
