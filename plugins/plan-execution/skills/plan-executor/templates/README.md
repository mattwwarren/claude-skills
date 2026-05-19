# Plan Executor Templates

## phase-handoff.md

Template for the document generated after each phase completes successfully. Records what was accomplished, integration check results, and provides a resumption prompt for the next phase.

### Usage

After all tasks in a phase pass integration checks, the plan executor fills in this template and saves it alongside the plan file (e.g., `.claude/plans/my-feature/phase-1-handoff.md`).

### Fields

| Field | Description |
|-------|-------------|
| `type` | Always `phase-handoff` |
| `phase` | Phase number and title from the plan |
| `completed` | Timestamp when the phase finished |
| Summary | Brief description of what was accomplished |
| Tasks Completed | Checked-off task list from the phase |
| Integration Results | pytest, ruff, and mypy output |
| Agent Results | Summary of sub-agent work |
| Next Phase | Title and task list for the upcoming phase |
| Resumption Prompt | Copy-paste prompt to resume execution in a new session |
