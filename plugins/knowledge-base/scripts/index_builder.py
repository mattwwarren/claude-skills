"""Rebuild wiki/index.md from the current directory structure.

Scans wiki/ for markdown files, reads their frontmatter title if available,
and regenerates index.md with one entry per page grouped by directory.

Respects the 200-line hard limit: at 200+ lines, raises IndexTooLargeError.

Usage:
    from scripts.index_builder import rebuild_index
    rebuild_index(wiki_dir)

    # CLI:
    python3 scripts/index_builder.py [wiki_dir]
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_INDEX_FILE = "index.md"
_LOG_FILE = "log.md"
_ARCHIVE_DIR = ".archive"
_AUTO_MEMORY_DIR = "auto-memory"
_INBOX_DIR = "inbox"

_MAX_INDEX_LINES = 200


class IndexTooLargeError(Exception):
    pass


@dataclass
class PageEntry:
    path: Path
    title: str
    description: str = ""


def _read_frontmatter_title(path: Path) -> str | None:
    """Read the title field from YAML frontmatter, if present."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not content.startswith("---"):
        return None
    end = content.find("\n---", 3)
    if end == -1:
        return None
    fm_block = content[3:end]
    for line in fm_block.splitlines():
        if line.startswith("title:"):
            return line[6:].strip().strip('"\'')
    return None


def _stem_to_title(stem: str) -> str:
    """Convert kebab-case stem to Title Case."""
    return stem.replace("-", " ").title()


def _collect_pages(wiki_dir: Path) -> dict[str, list[PageEntry]]:
    """Walk wiki/ and collect all .md pages by directory group."""
    groups: dict[str, list[PageEntry]] = {}

    skip_names = {_INDEX_FILE, _LOG_FILE}
    skip_dirs = {_ARCHIVE_DIR, _AUTO_MEMORY_DIR, _INBOX_DIR}

    for md_file in sorted(wiki_dir.rglob("*.md")):
        # Skip top-level special files
        if md_file.parent == wiki_dir and md_file.name in skip_names:
            continue
        # Skip archive and auto-memory trees
        rel = md_file.relative_to(wiki_dir)
        parts = rel.parts
        if any(p in skip_dirs for p in parts):
            continue

        # Group key: parent directory relative to wiki root (or root itself)
        if md_file.parent == wiki_dir:
            group_key = ""
        else:
            group_key = str(rel.parent)

        title = _read_frontmatter_title(md_file) or _stem_to_title(md_file.stem)
        entry = PageEntry(path=md_file, title=title)
        groups.setdefault(group_key, []).append(entry)

    return groups


def _inbox_entries(wiki_dir: Path) -> list[PageEntry]:
    """Collect inbox files."""
    inbox = wiki_dir / _INBOX_DIR
    if not inbox.exists():
        return []
    return [
        PageEntry(path=f, title=_stem_to_title(f.stem))
        for f in sorted(inbox.glob("*.md"))
    ]


def _render_index(groups: dict[str, list[PageEntry]], inbox: list[PageEntry]) -> list[str]:
    """Render index.md lines."""
    lines: list[str] = [
        "# Knowledge Base Index",
        "",
        "<!-- This file is loaded at session start. Keep under 200 lines. -->",
        "<!-- wiki-lint auto-consolidates directory entries at 180 lines. -->",
        "",
    ]

    # Root-level pages first (no section header)
    root_pages = groups.get("", [])
    for e in root_pages:
        desc = f" — {e.description}" if e.description else ""
        lines.append(f"- [{e.title}]({e.path.name}){desc}")
    if root_pages:
        lines.append("")

    # Subdirectories
    for group_key in sorted(k for k in groups if k):
        entries = groups[group_key]
        section_title = _stem_to_title(group_key.split("/")[-1])
        lines.append(f"## {section_title}")
        for e in entries:
            desc = f" — {e.description}" if e.description else ""
            lines.append(f"- [{e.title}]({group_key}/{e.path.name}){desc}")
        lines.append("")

    # Inbox section
    lines.append("## Inbox")
    if inbox:
        for e in inbox:
            lines.append(f"- [{e.title}](inbox/{e.path.name})")
    else:
        lines.append("<!-- Empty — wiki-lint is up to date. -->")
    lines.append("")

    return lines


def rebuild_index(wiki_dir: Path) -> int:
    """Rebuild wiki/index.md from directory scan. Returns line count written."""
    groups = _collect_pages(wiki_dir)
    inbox = _inbox_entries(wiki_dir)

    lines = _render_index(groups, inbox)

    line_count = len(lines)
    if line_count >= _MAX_INDEX_LINES:
        raise IndexTooLargeError(
            f"Index would be {line_count} lines (limit {_MAX_INDEX_LINES}). "
            "Run /wiki-lint to consolidate."
        )

    index_path = wiki_dir / _INDEX_FILE
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return line_count


def main() -> None:
    wiki_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("wiki")
    wiki_dir = wiki_dir.expanduser()
    if not wiki_dir.is_dir():
        print(f"Not a directory: {wiki_dir}", file=sys.stderr)
        sys.exit(1)
    try:
        n = rebuild_index(wiki_dir)
        print(f"[index_builder] Wrote {n} lines to {wiki_dir / 'index.md'}", file=sys.stderr)
    except IndexTooLargeError as e:
        print(f"[index_builder] ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
