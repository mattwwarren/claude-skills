# Plan Executor Skill

Autonomous plan execution with parallel sub-agents. Takes an approved plan file and executes it phase-by-phase, spawning background agents for independent tasks and running integration checks between phases.

## What It Does

1. Reads a plan file (markdown with H2 phase headers and checkbox tasks)
2. Identifies the current phase (first phase with unchecked tasks)
3. Classifies tasks as independent or dependent
4. Spawns parallel sub-agents for independent tasks
5. Monitors agent completion
6. Runs integration checks (pytest, ruff, mypy)
7. Updates the plan file with completed tasks
8. Generates a phase handoff document
9. Advances to the next phase or finishes

## Prerequisites

- An **approved plan** in markdown format with phases and tasks
- Plan must follow the expected format (see below)
- Project must have pytest, ruff, and mypy configured

## Plan Format Guide

Plans must use H2 headers for phases and checkbox syntax for tasks:

```markdown
---
title: My Feature Plan
status: approved
---

## Phase 1: Foundation

- [ ] Create the database models
- [ ] Add migration scripts
- [ ] Write unit tests for models

## Phase 2: API Layer

- [ ] Implement CRUD endpoints
- [ ] Add input validation
- [ ] Write API integration tests

## Phase 3: Frontend

- [ ] Build list view component
- [ ] Build detail view component
- [ ] Connect to API endpoints
```

### Task Independence

By default, tasks within a phase are treated as independent and will run in parallel. To mark a dependency, include it in the task description:

```markdown
- [ ] Create user model
- [ ] Create user service (depends on user model)
```

### Phase Ordering

Phases execute sequentially. Phase 2 does not start until all Phase 1 tasks pass integration checks. This ensures each phase builds on a stable foundation.

## Installation

```bash
cd claude-skills
./install.sh plan-executor >> /path/to/project/CLAUDE.md
```

This appends the skill instructions to your project's CLAUDE.md so Claude Code knows how to execute plans.

## Example Workflow

### 1. Create and Approve a Plan

Write a plan file at `.claude/plans/my-feature/main.md` following the format above. Review it and mark the frontmatter as `status: approved`.

### 2. Start Execution

Tell Claude:

```
Execute the plan at .claude/plans/my-feature/main.md
```

### 3. Phase Execution

Claude will:
- Read Phase 1 tasks
- Spawn 3 background agents (one per independent task)
- Wait for all agents to finish
- Run pytest, ruff check, mypy
- Check off completed tasks in the plan file
- Generate a phase handoff at `.claude/plans/my-feature/phase-1-handoff.md`
- Move to Phase 2

### 4. Between Phases

A phase handoff document is generated recording:
- What was accomplished
- Integration check results
- What comes next

### 5. Completion

When all phases are done, Claude reports plan execution complete with a summary of all phases.

### 6. Resumption (if interrupted)

If a session ends mid-plan, tell the next session:

```
Continue executing plan at .claude/plans/my-feature/main.md
```

Claude reads the plan, finds the first unchecked task, and resumes from there.

## Parallelization Constraints

| Operation | Parallel Safe | Max Agents | Notes |
|-----------|--------------|------------|-------|
| File edits (non-overlapping) | Yes | 6 | Different files only |
| File edits (overlapping) | No | 1 | Must be sequential |
| ruff check | Yes | 6 | Fast, thread-safe |
| pytest | Yes | 3-4 | Test isolation handles it |
| mypy | No | 1 | Type cache conflicts |
| Builds | Depends | 3-4 | Resource-heavy |
| Simple searches | Yes | 6 | Lightweight |

## Relationship to Handoff Skill

The plan executor generates **phase handoffs** between phases using the template at `templates/plan-executor/phase-handoff.md`. These are lighter-weight than full session handoffs.

For full session handoffs (context exhaustion, debug forks, scope changes), use the handoff skill directly. The plan executor will invoke the handoff skill when session boundaries are reached mid-plan.

## Error Behavior

| Scenario | Behavior |
|----------|----------|
| Agent fails | Retry task directly, then mark blocked |
| Tests fail | Stop phase, report failures, wait for guidance |
| Lint violations | Stop phase, report violations, wait for guidance |
| mypy errors | Stop phase, report errors, wait for guidance |
| Context running low | Complete current work, generate handoff, stop |
| All tasks blocked | Generate handoff with blocker details |
