---
type: debug-fork-debug
created: YYYY-MM-DD HH:MM UTC
reason: debug-fork
---

# Debug Investigation: [Issue Title]

**Date**: YYYY-MM-DD HH:MM UTC
**Status**: investigating
**Plan**: [/absolute/path/to/plan/main.md]
**Related main track**: [/absolute/path/to/.handoffs/handoff-main-YYYY-MM-DD-HHMM.md]

## Issue Description

[Clear description of the issue. What should happen vs what actually happens.]

## Symptoms

- [Observable symptom 1]
- [Observable symptom 2]
- [Error messages, stack traces, or unexpected behavior]

## Error Messages

```
[Exact error output, stack traces, or log messages. Include file paths and line numbers.]
```

## Relevant Files

- [/absolute/path/to/file1.py] - [why this file is relevant]
- [/absolute/path/to/file2.py] - [why this file is relevant]

## Attempts Made

### Attempt 1: [Approach name]
**What was tried**: [Description of the approach]
**Result**: [What happened -- error, partial fix, new symptom]
**Why it failed**: [Root cause analysis if known]

### Attempt 2: [Approach name]
**What was tried**: [Description of the approach]
**Result**: [What happened]
**Why it failed**: [Root cause analysis if known]

### Attempt 3: [Approach name]
[Optional. Include if a third attempt was made.]
**What was tried**: [Description]
**Result**: [What happened]
**Why it failed**: [Root cause analysis if known]

## Hypotheses Not Yet Tested

1. [Hypothesis 1 -- what it is and how to test it]
2. [Hypothesis 2 -- what it is and how to test it]
3. [Hypothesis 3 -- what it is and how to test it]

## Environment Context

[Optional. Relevant environment details -- versions, config, dependencies.]

## Resumption Prompt

```
Investigating a debug issue from [task name].
Plan: [/absolute/path/to/plan/main.md]

Issue: [One-sentence description of the problem]

What has been tried (all failed):
1. [Attempt 1 summary] - [result]
2. [Attempt 2 summary] - [result]

Untested hypotheses:
1. [Hypothesis 1]
2. [Hypothesis 2]

Key files:
- [/absolute/path/to/file1.py]
- [/absolute/path/to/file2.py]

Previous handoff: [/absolute/path/to/.handoffs/handoff-debug-YYYY-MM-DD-HHMM.md]

Start by testing hypothesis 1: [specific first action].
```
