# Debug Triage Templates

Templates used by the debug-triage skill to generate session logs and postmortems.

## Files

| Template | Purpose |
|----------|---------|
| `session-log.md` | Tracks issues during an active debug session |
| `postmortem.md` | Summary generated when a debug session ends |

## Usage

These templates are referenced by the skill instructions in `skills/debug-triage/SKILL.md`. Claude Code uses them as the basis for creating `.debug/` files in your project root. Placeholders (e.g., `YYYY-MM-DD`) are replaced with actual values at creation time.
