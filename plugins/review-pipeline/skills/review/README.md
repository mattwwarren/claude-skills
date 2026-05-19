# Review Skill

Parallel code review using specialized reviewer agents. Each agent focuses on a different concern (code quality, architecture, tests, performance, security, etc.) and only those with actionable findings get surfaced.

## What It Does

`/review` analyzes a diff and spawns reviewer subagents in parallel based on what changed:

- **Code Quality** — SOLID, DRY, naming, complexity
- **Architecture** — coupling, cohesion, dependency direction, design patterns
- **Test** — coverage, AAA pattern, test independence, mocking
- **Performance** — N+1 queries, algorithms, memory, caching
- **API Contract** — backend/frontend contract sync, schema changes
- **Deployment** — K8s, Docker, CI/CD, infrastructure security
- **SysAdmin** — speed-vs-quality, DRY violations, scope creep
- **Data Safety** — destructive defaults, blast radius, audit trails
- **Product Manager** — verifies the change satisfies the ticket requirements

Reviewers run concurrently. Findings are deduplicated and ranked. Reviewers with no findings stay silent.

## Invocation

```
/review                  # diff vs main (default)
/review #123             # GitHub PR
/review HEAD~3..HEAD     # last 3 commits
/review feature/branch   # specific branch
```

## Installation

```bash
./install.sh review >> ./CLAUDE.md
```

Or copy `skills/review/SKILL.md` into your CLAUDE.md manually.

## Reviewer Agents

The SKILL.md instructs Claude to spawn reviewer subagents. For the reviewer agent definitions themselves (markdown files describing each agent's focus and tone), see the **Full Pipeline** section below.

If reviewer agents aren't installed in your `~/.claude/agents/` directory, `/review` still works but uses generic prompts rather than the specialized agent personas.

## Posting to GitHub

`/review` produces findings locally. To post them to a GitHub PR as inline comments, pair with the **post-review** script from the full pipeline (see below).

## Full Pipeline

The marketplace skill is the instructional core. The complete review pipeline — including the 14 reviewer agent definitions and supporting scripts for posting reviews to GitHub — lives in [global-claude/exports/review-pipeline](https://github.com/mattwwarren/global-claude/tree/main/exports/review-pipeline). Install the tarball there to get:

- 14 specialized reviewer agent definitions (`~/.claude/agents/*.md`)
- `post_review.py` — post structured reviews to GitHub with inline comments
- `review_sweep.py` — find unreviewed PRs across a repo
- `prep_pr.py` + finalize — quality gates and PR creation

The marketplace skill works standalone. The full pipeline adds GitHub integration and the curated reviewer personas.

## Related Skills

- **[auto-dev](../auto-dev/)** — uses `/review` internally during the implement→review→ship loop
- **[review-monitor](../review-monitor/)** — follows reviewed PRs through merge with delta reviews
