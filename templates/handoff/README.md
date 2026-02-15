# Handoff Templates

Fill-in-the-blanks markdown templates for session handoff documents.

## Templates

| File | Purpose |
|------|---------|
| `session-handoff.md` | Standard handoff for context exhaustion or scope creep |
| `debug-fork-main.md` | Main work track when debug forking |
| `debug-fork-debug.md` | Debug investigation track when debug forking |

## Usage

The handoff skill fills these templates automatically when invoked via `/handoff`. You can also copy and fill them manually for ad-hoc handoffs.

### Placeholders

All templates use bracket placeholders like `[description]` for fields you fill in. Replace every placeholder -- do not leave any brackets in the final document.

### Frontmatter

Every template starts with YAML frontmatter containing:
- `type` - document type identifier
- `created` - UTC timestamp
- `reason` - what triggered the handoff

### Resumption Prompt

Every template ends with a resumption prompt in a fenced code block. This prompt must be completely self-contained -- the next session has no memory of the current one. Include absolute file paths, current phase, progress percentage, and a specific first action.

## Output Location

Write completed handoffs to `.handoffs/` in the project root. Create the directory if it does not exist.
