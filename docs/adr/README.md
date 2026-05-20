# Architecture Decision Records

This directory holds [Architecture Decision Records](https://github.com/joelparkerhenderson/architecture-decision-record) (ADRs) for the marketplace. Each ADR captures the context, decision, and consequences of a significant structural choice — the kind of choice future-you would want to revisit before reversing.

ADRs are numbered in order of acceptance. Once accepted, an ADR is rarely edited; instead, a new ADR supersedes it.

## Index

| # | Title | Status | Date |
|---|---|---|---|
| [0001](0001-plugin-marketplace-structure.md) | Plugin marketplace structure | Accepted | 2026-05-19 |
| [0002](0002-fleet-stream-observability-surface.md) | Fleet-stream observability via transcript JSONL | Accepted | 2026-05-20 |
| [0003](0003-scheduling-mechanism-for-filesystem-bound-workflows.md) | Scheduling mechanism for filesystem-bound workflows | Accepted | 2026-05-20 |
| 0004 | Risk-tier vocabulary (planned) | Deferred | — |

## Planned ADRs

- **0004 — Risk-tier vocabulary for spec-reviewer.** To be authored alongside the implementation of [#2 (spec-reviewer + risk-tier)](https://github.com/mattwwarren/claude-skills/issues/2). The proposed direction (alias the `claude auto-mode` classifier's `allow`/`soft_deny`/`hard_deny` buckets rather than invent a parallel taxonomy) is captured in [`docs/research/claude-code-agent-architecture.md`](../research/claude-code-agent-architecture.md) §"`claude auto-mode` — classifier surface". Held off from being an ADR now because implementation may surface constraints that change the decision; better to write it with evidence in hand.

## Format

ADRs in this repo follow the [Michael Nygard format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions): Title / Status / Context / Decision / Consequences. Keep them short — a long ADR is usually two ADRs.
