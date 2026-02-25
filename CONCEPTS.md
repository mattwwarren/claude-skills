# Concepts

The ideas behind these skills. Read this to understand *why* they work the way they do.

## Fresh-Context Principle

Every new Claude Code session starts with zero conversation history. The AI has no memory of what you discussed five minutes ago in a different session.

This means handoff documents must be **completely self-contained**. No "as discussed earlier." No "the approach we agreed on." Every handoff must include all context needed to resume work - file paths, decisions made, approaches rejected, and the exact next step.

If a handoff requires the reader to "just know" something, it's broken.

## Session Boundaries

Context windows are finite. Long sessions degrade in quality as the window fills. Rather than fighting this constraint, these skills work *with* it:

- **Recognize when context is running low** (80%+ usage) and proactively hand off
- **Break large work into phases** that fit within a single session
- **Generate structured handoffs** so nothing is lost between sessions
- **Start each session with a clear resumption prompt** that loads essential context efficiently

The goal isn't infinite sessions - it's reliable work across many bounded sessions.

## Debug Forking

When you're stuck debugging, the instinct is to keep digging. But after 2-3 failed attempts, continuing down the same path usually wastes the rest of the session.

**Debug forking** splits the work into two tracks:

1. **Main track** - Continue the feature work, skip the problematic area
2. **Debug track** - Fresh investigation of the specific issue with full context of what was tried

This prevents the next session from falling into the same rabbit hole. The debug track gets a clean start with all the failed attempts documented, so it can try genuinely different approaches.

## Structured Debugging

Bugs are easier to fix when you track what you've tried. The debug triage skill enforces a simple discipline:

- **Log each issue** with a title and status
- **Record each fix attempt** and its result
- **Track hypotheses** - what you've eliminated and what remains
- **Generate a postmortem** with counts (fixed/deferred/escalated) and next steps

This isn't bureaucracy. It's the difference between "I spent 2 hours debugging" and "I fixed 5 bugs, deferred 2 that need upstream changes, and escalated 1 to a background agent that found the root cause."

## Plan Decomposition

Large tasks fail when attempted as a single unit. Plan decomposition breaks work into **phases** where:

- Each phase has a clear scope and deliverables
- Tasks within a phase can be identified as independent or dependent
- Independent tasks can be parallelized across agents
- Phase boundaries are natural checkpoints for handoffs

The format is simple: H2 headers (`## Phase N: Title`) with checkbox tasks underneath. No special tooling required - just structured markdown.

## Agent Orchestration

Claude Code can spawn sub-agents that work independently in the background. The plan executor skill uses this for parallelization:

1. Read the plan and identify the current phase
2. Extract independent tasks from the phase
3. Spawn background agents (one per independent task)
4. Monitor completion and integrate results
5. Run integration checks (tests, linting, type checking)
6. Generate a phase handoff and advance to the next phase

Key constraints that make this reliable:
- **Never run mypy in parallel** - type caches conflict
- **Max 4-6 concurrent agents** depending on task weight
- **Sequential phases** - don't start Phase 2 until Phase 1 passes integration checks
- **Each agent gets full context** - task description, relevant files, conventions to follow

## Multi-Session Orchestration

A single Claude Code session has limited context. But many tasks require more work than one session can hold. Multi-session orchestration solves this with a **task queue** pattern:

1. **Planning sessions** analyze requirements, create plans, and queue work items
2. **Implementation sessions** claim items from the queue and execute them
3. **Debt sessions** pick up low-priority items queued during implementation

The `cw` CLI provides the queue infrastructure. Skills like `queue-plan`, `queue-debt`, and `pull-and-execute` provide the Claude-side integration.

### Session Specialization

Different sessions can specialize by purpose:

| Purpose | What It Does | Fed By |
|---------|-------------|--------|
| `impl` | Feature implementation | `/queue-plan` |
| `debt` | Tech debt cleanup | `/queue-debt`, review LOW findings |
| `explore` | Research and investigation | Manual queuing |
| `idea` | Prototyping and experiments | Manual queuing |

### Queue-Driven Execution

The `pull-and-execute` skill implements a complete execution loop:
- **Claim** an item from the queue
- **Plan** by reading context and assessing scope
- **Implement** with parallel agents for medium/large work
- **Review** the implementation for quality
- **Fix** any findings (max 2 iterations)
- **Complete** with quality gates, commit, and queue update

This enables continuous, hands-off execution across session boundaries.

## Skill Synergies

These skills are designed to work together as a system:

- **plan-executor** executes phases with parallel sub-agents and generates **handoffs** between them
- **session-done** wraps up sessions and signals `cw done` to free the session for new work
- **Debug triage** produces **debug fork handoffs** when stuck, which the handoff skill formats
- **queue-plan** and **queue-debt** feed work to **pull-and-execute** across sessions
- **pull-and-execute** claims queued items, implements them, and loops back for more
- All skills use the same **fresh-context principle** for their output documents

You can use each skill independently, but they're most powerful as a system.
