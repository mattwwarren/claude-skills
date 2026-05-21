# ADR 0004: Risk-tier vocabulary for spec-reviewer

- **Status:** Accepted
- **Date:** 2026-05-21
- **Deciders:** Matthew Warren
- **Related:** Issue [#2](https://github.com/mattwwarren/claude-skills/issues/2) (spec-reviewer + risk-tier), Issue [#1](https://github.com/mattwwarren/claude-skills/issues/1) (spec-author schema), research doc [`claude-code-agent-architecture.md`](../research/claude-code-agent-architecture.md) §"`claude auto-mode` — classifier surface"

## Context

Issue #2 introduces a `risk_tag` field on the spec schema (`safe | sensitive | dangerous`) and uses it to gate `/auto-dev`'s plan and review checkpoints. Two vocabularies were considered:

1. **Invent a parallel taxonomy** — `safe | sensitive | dangerous`. Easy to author, easy to read. But disconnected from any other surface in Claude Code; the user learning the spec schema picks up one more bespoke set of words.
2. **Alias Claude Code's existing `auto-mode` classifier buckets** — `allow | soft_deny | hard_deny`. The classifier already runs on every tool call, ships ~30 named rules per bucket, and has concrete examples the spec author can pattern-match against (e.g., "Git Push to Default Branch", "Production Deploy", "Self-Modification", "Data Exfiltration", "Create Unsafe Agents").

The classifier vocabulary is grounded in shipped, observed behavior of Claude Code 2.1.145 — surfaced via `claude auto-mode defaults`. The spec-reviewer's job is to validate that a spec author has classified their work honestly; pointing them at concrete rule names ("does this work include behavior that matches the 'Self-Modification' rule?") is more actionable than asking them to introspect on whether the work "feels sensitive".

A spec frontmatter rewrite (`risk_tag: allow` instead of `risk_tag: safe`) was considered. Rejected — `safe | sensitive | dangerous` reads naturally in YAML and in human conversation about a spec; the words `allow | soft_deny | hard_deny` are denial-system jargon that doesn't match how a human classifies work. The mapping is 1:1, so authors can use the friendly tags while the rubric references the classifier rule names underneath.

## Decision

**The `risk_tag` field on the spec schema uses the friendly tags `safe | sensitive | dangerous` as the canonical values.** Each tag aliases exactly one classifier bucket:

| `risk_tag` (spec) | `auto-mode` bucket | Meaning |
|---|---|---|
| `safe` | `allow` | The work matches only rules in the classifier's `allow` bucket — Local Operations, Read-Only, Memory Directory, Declared Dependencies, etc. No human gate needed beyond scope-based defaults. |
| `sensitive` | `soft_deny` | The work matches one or more rules in `soft_deny` — Git Push to Default Branch, Production Deploy, Self-Modification, Modify Shared Resources, Permission Grant, etc. Force a human gate at plan approval regardless of scope. |
| `dangerous` | `hard_deny` | The work matches one or more rules in `hard_deny` — Data Exfiltration, Auto-Mode Bypass. Force a human gate at plan AND review regardless of scope. |

The friendly tag is what spec authors write and what `/auto-dev` parses. The classifier rule names are the **rubric** that `spec-reviewer` uses to validate the tag and the **path-pattern heuristics** used to auto-derive a default tag from target files.

### Path-pattern heuristics (auto-derive)

When a spec is in hand, the spec-reviewer infers a baseline `risk_tag` from the target file paths and flags under-classification as MUST_FIX. Heuristics (matched against any target file path):

**`sensitive` (soft_deny) signals:**
- `.claude/commands/`, `.claude/agents/`, `.claude/skills/`, `.claude/hooks/`, `.claude/settings*.json`, `CLAUDE.md` — Self-Modification rule
- `auth/`, `authn/`, `authz/`, `oauth/`, `session/` — Permission Grant / Security Weaken adjacent
- `migrations/`, `alembic/`, `schema/`, `**/migrate*.sql` — Production Deploy (schema migration)
- `billing/`, `payment/`, `stripe/`, `invoice/` — Real-World Transactions adjacent
- `.github/workflows/`, `.gitlab-ci/`, `ci/`, `Jenkinsfile`, `.buildkite/` — Production Deploy (CI)
- shared base classes / interfaces with 3+ known consumers (judgment call)

**`dangerous` (hard_deny) signals:**
- All of the above PLUS one of:
  - Removes existing destructive-default guard (e.g., changes `--force` from opt-in to default)
  - Cross-org / cross-tenant data joins
  - Adds an external network egress not previously present (Data Exfiltration adjacent)
  - Disables, weakens, or bypasses the classifier itself (Auto-Mode Bypass)

If no signals fire, default is `safe`. When a path matches multiple signals, take the highest tier.

When in doubt, escalate one tier. Under-classification causes auto-merge of work that should have gated; over-classification just adds one human gate.

## Consequences

### Positive

- **Grounded in shipped behavior.** Spec authors and reviewers reference the same classifier their tool calls already pass through. No parallel mental model to learn.
- **Actionable rubric.** "Does this match the 'Self-Modification' rule?" is more concrete than "is this sensitive?" Reviewers can cite the rule name in MUST_FIX findings, giving the author a specific thing to verify.
- **Friendly surface preserved.** Spec authors write `sensitive`, not `soft_deny` — the YAML stays readable, the cognitive load stays low.
- **Future-proof against classifier evolution.** When Anthropic adds new rules to a bucket (or moves a rule between buckets), the heuristics in spec-reviewer get re-checked against `claude auto-mode defaults` and updated; the spec schema doesn't change.

### Negative

- **Bucket mapping can drift.** If Anthropic re-buckets a rule (e.g., moves something from `soft_deny` to `allow`), the heuristics drift and spec-reviewer's auto-derive misclassifies. Mitigation: spec-reviewer's path-pattern table cites the rule names it's keying off; a quarterly refresh against `claude auto-mode defaults` keeps drift small. Track as a follow-up if drift becomes a real problem.
- **Two vocabularies coexist.** A reader skimming spec-reviewer output sees both `risk_tag: sensitive` and "matches 'Self-Modification' (soft_deny) rule". The mapping is mechanical, but it's two words for one concept. Accepted — the friendly tag is for the spec, the rule name is for the rubric, and readers don't need to use both interchangeably.
- **Classifier is observed, not documented as stable API.** `claude auto-mode defaults` is reachable today on 2.1.145 but isn't advertised as a stable contract. If Anthropic restructures the command, the rubric needs a new source. Mitigation: the classifier defaults are also documented in the research doc, which can serve as a snapshot reference if the live command goes away.

### Neutral

- **No change to existing spec-author schema.** Spec-author (#1, already shipped) uses `safe | sensitive | dangerous` in its frontmatter rules and example. This ADR ratifies the choice rather than changing it. The spec-author rules section gets a small update to cite the classifier mapping for clarity, but the field values don't move.

- **Bootstrap exemption for tooling development.** The first PR that ships this gating system (issue #2 itself) is not gated by the system it introduces — by definition it cannot be. Subsequent PRs that modify the gating logic itself (auto-dev.md, the spec-reviewer agent, this ADR's heuristics) fall under the `Self-Modification` rule and would be classified `sensitive` by the heuristic. That is the correct behavior — the system gating itself is desirable, not circular. For the bootstrap-only case (a PR shipping a fix to spec-reviewer before spec-reviewer is widely adopted), maintainers can route around the gate by hand-running spec-review out-of-band; this is not a separate code path, just an operational note that the first invocation of any self-gating system is exempt from its own gate by necessity.

## Alternatives considered

### Rewrite the spec schema to use `allow | soft_deny | hard_deny`

Rejected. The denial-system words don't match how a human author classifies work. "Is this dangerous?" is a question a human can answer in the moment they're writing a spec; "does this hit hard_deny?" requires them to map their mental model onto the classifier's. The friendly tags are a one-time learning cost; the classifier vocabulary in the rubric is a tool the reviewer reaches for, not something the author has to internalize.

### Invent more granular tiers (e.g., 5 levels, or per-domain tiers)

Rejected for now. Three tiers map cleanly onto two existing gating axes (`auto-accept` vs `gate at plan` vs `gate at plan and review`). More tiers would require more bespoke gate behaviors and would over-engineer a system whose primary failure mode today is under-classification, not insufficient nuance. Revisit only if real specs surface a class of work that doesn't fit any of the three tiers.

### Drop the risk tag entirely and rely on scope tier alone

Rejected — this is the failure mode the issue body specifically calls out. A 30-line auth migration is small-scope and high-risk; a 600-line UI refactor is large-scope and low-risk. Scope and risk are independent axes and need independent gates. The risk tag exists precisely because scope tier under-protects the dangerous-but-tiny class.

## References

- Issue [#2](https://github.com/mattwwarren/claude-skills/issues/2) — spec-reviewer + risk-tier (this ticket; owner comment foreshadowed this ADR)
- Issue [#1](https://github.com/mattwwarren/claude-skills/issues/1) — spec-author (defines the spec schema this ADR's `risk_tag` lives in)
- [`docs/research/claude-code-agent-architecture.md`](../research/claude-code-agent-architecture.md) §"`claude auto-mode` — classifier surface" — primary source for the bucket vocabulary and rule-name examples
- `claude auto-mode defaults` — live source for the classifier rules on the host machine
- [`plugins/review-pipeline/skills/spec-reviewer/SKILL.md`](../../plugins/review-pipeline/skills/spec-reviewer/SKILL.md) — consumer of this ADR (validates the risk_tag against the classifier rules)
- [`plugins/review-pipeline/commands/auto-dev.md`](../../plugins/review-pipeline/commands/auto-dev.md) — consumer of this ADR (gates on the risk_tag)
