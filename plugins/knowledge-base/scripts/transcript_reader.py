"""Extract essential content from Claude Code JSONL session transcripts.

Filters out noise (file-history-snapshot, progress, system messages) and
produces a compact, readable representation that fits in a Claude context window.

Usage:
    python3 scripts/transcript_reader.py <path-to-transcript.jsonl> > /tmp/extracted.md
    python3 scripts/transcript_reader.py <path-to-meeting.json> > /tmp/extracted.md

Output format:
    [USER] message text
    [ASSISTANT] message text
    [TOOL:tool_name] tool input summary
    [TOOL_RESULT] result summary (errors only for non-error results)
    [SPEAKER:Name] speaker text  (meeting transcripts)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Messages types to skip entirely
_NOISE_TYPES = frozenset(
    {
        "file-history-snapshot",
        "progress",
        "system",
        "debug",
    }
)

# Tool names whose results are always noise (unless they contain errors)
_QUIET_TOOLS = frozenset(
    {
        "Glob",
        "Grep",
        "LS",
        "Read",
    }
)

# Maximum characters for a single tool input/result summary
_MAX_SNIPPET = 2000

# Maximum output characters before we warn (but still emit)
_WARN_SIZE = 80_000


def _truncate(text: str, max_chars: int = _MAX_SNIPPET) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return f"{text[:half]}\n...[{len(text) - max_chars} chars omitted]...\n{text[-half:]}"


def _format_tool_input(name: str, tool_input: dict) -> str:
    """Produce a one-line summary of a tool call."""
    if name in ("Bash", "Edit", "Write"):
        cmd = tool_input.get("command") or tool_input.get("file_path") or ""
        return f"[TOOL:{name}] {_truncate(str(cmd), 200)}"
    if name == "Agent":
        desc = tool_input.get("description") or tool_input.get("prompt", "")[:80]
        return f"[TOOL:Agent] {desc}"
    # Generic: show first non-empty string value
    for v in tool_input.values():
        if isinstance(v, str) and v.strip():
            return f"[TOOL:{name}] {_truncate(v, 200)}"
    return f"[TOOL:{name}]"


def _extract_text_from_content(content: list | str | None) -> str:
    """Pull plain text from a message content field."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type", "")
        if btype == "text":
            text = block.get("text", "").strip()
            if text:
                parts.append(text)
        elif btype == "tool_use":
            name = block.get("name", "unknown")
            inp = block.get("input", {})
            parts.append(_format_tool_input(name, inp))
        elif btype == "tool_result":
            # Only include errors
            is_error = block.get("is_error", False)
            tool_content = block.get("content", "")
            if isinstance(tool_content, list):
                tool_content = " ".join(
                    b.get("text", "") for b in tool_content if isinstance(b, dict)
                )
            if is_error and tool_content:
                parts.append(f"[TOOL_ERROR] {_truncate(str(tool_content))}")
    return "\n".join(parts)


def extract_from_jsonl(path: Path) -> str:
    """Extract essential content from a Claude Code JSONL session transcript."""
    lines: list[str] = []
    with path.open(encoding="utf-8") as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                msg = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")
            if msg_type in _NOISE_TYPES:
                continue

            inner = msg.get("message") if isinstance(msg.get("message"), dict) else {}
            role = inner.get("role", "") or msg.get("role", "")
            content = inner.get("content", msg.get("content", ""))

            if role == "user":
                text = _extract_text_from_content(content)
                if text:
                    lines.append(f"[USER] {text}")
            elif role == "assistant":
                text = _extract_text_from_content(content)
                if text:
                    lines.append(f"[ASSISTANT] {text}")
            elif msg_type == "tool_result":
                is_error = msg.get("is_error", False)
                if is_error:
                    result_content = msg.get("content", "")
                    if isinstance(result_content, list):
                        result_content = " ".join(
                            b.get("text", "") for b in result_content if isinstance(b, dict)
                        )
                    lines.append(f"[TOOL_ERROR] {_truncate(str(result_content))}")

    return "\n\n".join(lines)


def extract_from_meeting_json(path: Path) -> str:
    """Extract essential content from a meeting transcript JSON file.

    Preserves speaker attribution for provenance.
    """
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    lines: list[str] = []

    # Support multiple meeting transcript formats
    if isinstance(data, list):
        segments = data
    else:
        segments = (
            data.get("segments")
            or data.get("transcript")
            or data.get("utterances")
            or []
        )

    for seg in segments:
        if not isinstance(seg, dict):
            continue
        speaker = seg.get("speaker") or seg.get("speaker_label") or seg.get("name") or "Unknown"
        text = seg.get("text") or seg.get("content") or seg.get("transcript") or ""
        text = text.strip()
        if text:
            lines.append(f"[SPEAKER:{speaker}] {text}")

    return "\n\n".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: transcript_reader.py <path> [> output.md]", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1]).expanduser()
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        output = extract_from_jsonl(path)
    elif suffix == ".json":
        output = extract_from_meeting_json(path)
    else:
        print(f"Unsupported file type: {suffix} (expected .jsonl or .json)", file=sys.stderr)
        sys.exit(1)

    char_count = len(output)
    print(f"[transcript_reader] Output: {char_count:,} chars from {path.name}", file=sys.stderr)
    if char_count > _WARN_SIZE:
        print(
            f"[transcript_reader] WARNING: output exceeds {_WARN_SIZE:,} chars — "
            "wiki-ingest should use chunked processing",
            file=sys.stderr,
        )

    print(output)


if __name__ == "__main__":
    main()
