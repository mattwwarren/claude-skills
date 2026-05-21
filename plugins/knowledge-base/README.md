# knowledge-base

Mid-session lesson capture and knowledge-base inbox management for Claude Code.

> Wiki system design inspired by Scott Cipriano (@scottpcipriano).

## Skills

| Skill | What It Does |
|-------|--------------|
| [wiki-lesson](skills/wiki-lesson/) | Capture a mid-session lesson to a configurable inbox without interrupting the task |
| [wiki-ingest](skills/wiki-ingest/) | Process session transcripts into the wiki inbox in bulk, with secret filtering and dedup tracking |
| [wiki-lint](skills/wiki-lint/) | Promote inbox items to wiki pages, run quality checks, rebuild index, rotate log |
| [wiki-install](skills/wiki-install/) | Install macOS `launchd` agents that run `wiki-ingest` (every 4h) and `wiki-lint` (daily 6AM) on the local machine. Mac-only; see ADR 0003. |

## Install

```text
/plugin install knowledge-base@claude-skills
```
