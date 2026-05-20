"""Track which transcripts have been processed by wiki-ingest.

State file format (one entry per line):
    parent_dir/filename.jsonl:<file_size_bytes>

Keys include parent directory name to avoid collisions across projects.
Legacy filename-only entries are matched and migrated on next write.

All writes use fcntl.flock + atomic os.replace for concurrency safety.

Usage:
    from scripts.processed_tracker import ProcessedTracker
    tracker = ProcessedTracker(Path(".claude/.processed_wiki_transcripts"))
    if not tracker.is_processed(path):
        # ... process it ...
        tracker.mark_as_processed(path)
    elif tracker.has_grown(path, growth_threshold_kb=10):
        # ... reprocess it ...
        tracker.update_size(path)
"""

from __future__ import annotations

import fcntl
import os
import tempfile
from pathlib import Path

# Growth threshold: reprocess if file has grown by more than this many bytes
_DEFAULT_GROWTH_THRESHOLD = 10 * 1024  # 10 KB


class ProcessedTracker:
    def __init__(self, state_file: Path) -> None:
        self._state_file = state_file

    def _key(self, path: Path) -> str:
        """Canonical key: parent_dir/filename."""
        return f"{path.parent.name}/{path.name}"

    def _read_entries(self) -> dict[str, int]:
        """Read all entries from the state file. Returns {key: size}."""
        if not self._state_file.exists():
            return {}
        entries: dict[str, int] = {}
        with self._state_file.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if ":" in line:
                    key, _, size_str = line.rpartition(":")
                    try:
                        entries[key] = int(size_str)
                    except ValueError:
                        pass
                else:
                    # Legacy filename-only entry — size unknown, record as -1
                    entries[line] = -1
        return entries

    def _write_entries(self, entries: dict[str, int]) -> None:
        """Atomically write all entries to the state file."""
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self._state_file.parent, prefix=".tracker-")
        try:
            with os.fdopen(fd, "w") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                for key, size in sorted(entries.items()):
                    f.write(f"{key}:{size}\n")
        except Exception:
            os.unlink(tmp_path)
            raise
        os.replace(tmp_path, self._state_file)

    def _find_entry(self, path: Path, entries: dict[str, int]) -> str | None:
        """Return the matching entry key for path, handling legacy keys."""
        canonical = self._key(path)
        if canonical in entries:
            return canonical
        # Legacy: filename-only key
        if path.name in entries:
            return path.name
        return None

    def is_processed(self, path: Path) -> bool:
        """Return True if path has been processed (and hasn't grown significantly)."""
        entries = self._read_entries()
        return self._find_entry(path, entries) is not None

    def has_grown(self, path: Path, growth_threshold: int = _DEFAULT_GROWTH_THRESHOLD) -> bool:
        """Return True if path exists and has grown beyond the recorded size + threshold."""
        entries = self._read_entries()
        key = self._find_entry(path, entries)
        if key is None:
            return False  # Not processed — use is_processed() first
        recorded_size = entries[key]
        if recorded_size < 0:
            return True  # Legacy entry with no size — trigger reprocess
        try:
            current_size = path.stat().st_size
        except FileNotFoundError:
            return False
        return (current_size - recorded_size) > growth_threshold

    def mark_as_processed(self, path: Path) -> None:
        """Record path as processed with its current file size."""
        entries = self._read_entries()
        # Migrate legacy key if present
        if path.name in entries:
            del entries[path.name]
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            size = 0
        entries[self._key(path)] = size
        self._write_entries(entries)

    def update_size(self, path: Path) -> None:
        """Update the recorded file size after reprocessing (prevents infinite reprocess loop)."""
        entries = self._read_entries()
        # Migrate legacy key if present
        if path.name in entries:
            del entries[path.name]
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            size = 0
        entries[self._key(path)] = size
        self._write_entries(entries)

    def all_processed(self) -> dict[str, int]:
        """Return all tracked entries as {key: size}."""
        return self._read_entries()
