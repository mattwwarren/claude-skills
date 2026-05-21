# Model selection for fleet-dispatching skills

Guidance for which Claude model to pin on subagents spawned by `/auto-dev`, `/plan-executor`, `/pull-and-execute`, and any other skill that fans out parallel work. The cost of getting this wrong is not the wrong answer — it is **a failed dispatch** under credit pressure.

## TL;DR

| Model | Use for |
|---|---|
| **Haiku** | Searches, file listings, quick exploration, confidence scoring, infra/deployment checks, simple reviewers (formatting, lint triage), single-file edits |
| **Sonnet** | Implementation, planning, code review, multi-file refactors, integration work. **Default for any subagent that writes code or reviews diffs.** |
| **Opus** | Main-thread reasoning only. **Never fan out into parallel subagents.** |

When in doubt, pick Sonnet. Picking Haiku where Sonnet was warranted produces shallow work; picking Opus where Sonnet was warranted burns rate limit on work Sonnet could do indistinguishably well.

## Decision tree

```
Is this work on the main thread (the conversation the user is talking to)?
├── Yes → use whatever the main thread already is (Opus is fine here)
└── No → it's a subagent. Pick by task type:
    ├── Reads/greps/lists/file lookups → Haiku
    ├── Single-file edit or tiny script → Haiku
    ├── Code review, planning, multi-file impl, refactor → Sonnet
    ├── Multi-step reasoning with no fan-out → Sonnet (Opus only if explicit)
    └── Anything you intend to spawn 3+ of in parallel → Sonnet or Haiku, NEVER Opus
```

## The Opus→Sonnet spawn refusal (failure mode)

**Symptom.** A main-thread session running on Opus hits its usage credit ceiling. It then tries to spawn a Sonnet subagent. The spawn is **refused by the harness** — not by Sonnet, by the credit guardrail attached to the Opus session. The session appears to "lock up" mid-dispatch: the Task tool returns an error, the fleet does not start, and the work stalls.

**Root cause.** Subagent dispatch is billed against the parent session's credit pool, even when the subagent itself uses a cheaper model. An Opus session at its credit ceiling cannot spawn _anything_, regardless of the child's model.

**Mitigation (only one).** **Do not be on Opus when you intend to dispatch a fleet.** If you know in advance that this session will fan out (you are about to invoke `/auto-dev`, `/plan-executor`, `/pull-and-execute`, or any other skill that spawns 3+ parallel agents), switch the main thread to Sonnet first. The fleet still dispatches Sonnet/Haiku children with the same effective behavior; the difference is that the parent has headroom to actually issue the spawn calls.

**What does NOT work.**
- Picking Sonnet/Haiku as the child model. The block is on the parent's credit pool, not the child.
- Splitting the fleet across multiple smaller spawns. Same pool, same ceiling.
- Retrying after a short wait. The ceiling resets on its own schedule; there is no in-session unblock.

**What this doc does not try to fix.** Skill-level model enforcement, budget tracking, or anything that "negotiates around" the credit guardrail. The mitigation is behavioral, not mechanical: notice when you are about to fan out and pick the right main-thread model before you do.

## Anti-patterns

### Fanning Opus into parallel subagents

```
Task(... model: "opus" ...)      # spawn 1
Task(... model: "opus" ...)      # spawn 2  ← stop
Task(... model: "opus" ...)      # spawn 3
```

Three Opus subagents working in parallel burns the Opus rate limit ~3× faster than the main thread, almost always to do work Sonnet would do indistinguishably. Code review, planning, multi-file impl — these are Sonnet-shaped tasks.

If you find yourself writing `model: "opus"` on a subagent without a specific reason ("Opus is needed here because…"), that IS the signal — change it to Sonnet.

### `model: "inherit"` on subagents

`inherit` propagates the main-thread model into every spawn. If main is Opus, every child becomes Opus. This is the silent version of the "fan-out Opus" antipattern — it does the wrong thing without the spawn site ever mentioning Opus.

**Pin the model explicitly on every subagent spawn.** Do not rely on `inherit`.

### Picking Haiku for code-writing subagents

Haiku is fine for reads and greps but produces shallow code. A reviewer agent on Haiku will miss subtle issues a Sonnet reviewer catches. If the subagent is going to write code, edit multiple files, or reason about a diff — pick Sonnet.

## Quick reference for the three fleet-dispatch skills

| Skill | Subagent kind | Recommended model |
|---|---|---|
| `/auto-dev` | Plan agent | Sonnet |
| `/auto-dev` | Implementation agent | Sonnet |
| `/auto-dev` | Reviewers (Code Quality, SysAdmin, PM, Data Safety, etc.) | Sonnet |
| `/auto-dev` | `/prep-pr` agent | Sonnet |
| `/plan-executor` | Phase-internal independent task agents | Sonnet (most), Haiku (read-only investigations) |
| `/pull-and-execute` | Implementation agents | Sonnet |
| `/pull-and-execute` | Reviewer agents | Sonnet |
| Exploration agent (`Explore` subagent type) | (intrinsic) | Haiku |

If the main thread is Opus and you are about to invoke any of the three, switch main to Sonnet first.

## Non-goals of this doc

- Skill-level model enforcement. Skills do not refuse to dispatch based on the parent's model; the harness handles credit limits and the failure mode is informative, not catastrophic.
- Budget tracking. `--max-budget-usd` is a separate concern; this doc is about model choice, not spend control.
- Working around the credit guardrail. The guardrail is correct; the fix is to choose the right main-thread model in advance.
