#!/usr/bin/env python3
"""Wait until the CriticMarkup in selected notes changes.

Watches the notes' parent directories with Linux inotify, through libc via
ctypes, so there is nothing to install. Where inotify is unavailable, on
macOS and Windows, it polls the notes instead. Either way ordinary edits are
ignored: the process prints one JSON line and exits when a comment, reply,
highlight, or suggested edit is added or removed in any watched note. Run it
again to keep watching.

Events, one JSON object per line on stdout:

  {"event": "ready",   "backend": "inotify" | "poll", "files": [...], "marks": {"<path>": <count>}}
  {"event": "changed", "path": "...", "added": [...], "removed": [...]}
  {"event": "deleted", "path": "..."}
  {"event": "timeout", "files": [...]}

Each entry in "added" and "removed" is {"kind", "line", "text"}, where kind is
one of comment, highlight, addition, deletion, substitution.

Exit codes: 0 after a change, 2 after --timeout, 1 on a usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SETTLE_SECONDS = 0.15


class Inotify:
    """Directory watches with bounded blocking waits, on libc through ctypes.

    create() returns None wherever inotify is unavailable, so callers can
    fall back to polling.
    """

    CLOSE_WRITE, CREATE, DELETE = 0x8, 0x100, 0x200
    MOVED_FROM, MOVED_TO = 0x40, 0x80
    MASK = CLOSE_WRITE | CREATE | DELETE | MOVED_FROM | MOVED_TO

    @classmethod
    def create(cls, roots) -> Optional["Inotify"]:
        try:
            import ctypes
            self = cls.__new__(cls)
            self._libc = ctypes.CDLL("libc.so.6", use_errno=True)
            self._fd = self._libc.inotify_init1(0x800)  # IN_NONBLOCK
            if self._fd < 0:
                return None
            self._watched = set()
            for root in roots:
                self._add(Path(root))
            return self if self._watched else None
        except Exception:
            return None

    def _add(self, path: Path) -> None:
        candidate = str(path)
        if candidate in self._watched or not path.is_dir():
            return
        if self._libc.inotify_add_watch(self._fd, candidate.encode(), self.MASK) >= 0:
            self._watched.add(candidate)

    def wait(self, timeout: float) -> bool:
        """Block until something changes under a watched directory or the
        timeout passes. Returns whether anything fired; the caller looks at
        the files to learn what."""
        import select
        readable, _, _ = select.select([self._fd], [], [], timeout)
        if not readable:
            return False
        fired = False
        while True:
            try:
                buffer = os.read(self._fd, 65536)
            except (BlockingIOError, OSError):
                break
            fired = True
            if len(buffer) < 65536:
                break
        return fired


MARK = re.compile(
    r"(?P<comment>\{\{[^{}]*?>>.*?<<\}\}|\{>>.*?<<\})"
    r"|(?P<highlight>\{==.*?==\})"
    r"|(?P<addition>\{\+\+.*?\+\+\})"
    r"|(?P<deletion>\{--.*?--\})"
    r"|(?P<substitution>\{~~.*?~~\})",
    re.DOTALL,
)


def extract_marks(text: str) -> List[Tuple[str, int, str]]:
    """Every CriticMarkup mark as (kind, line, text) in document order."""
    marks = []
    for match in MARK.finditer(text):
        kind = match.lastgroup or "comment"
        line = text.count("\n", 0, match.start()) + 1
        marks.append((kind, line, match.group(0)))
    return marks


def mark_keys(marks: List[Tuple[str, int, str]]) -> Dict[str, Tuple[str, int, str]]:
    """A mark's identity is its kind plus its exact text, not its position,
    so edits elsewhere in the note do not count as mark changes."""
    keys: Dict[str, Tuple[str, int, str]] = {}
    for kind, line, text in marks:
        key = kind + "\x00" + " ".join(text.split())
        n = 0
        while f"{key}\x00{n}" in keys:
            n += 1
        keys[f"{key}\x00{n}"] = (kind, line, text)
    return keys


def read(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (FileNotFoundError, OSError):
        return None


def describe(entries, max_chars: int) -> List[dict]:
    out = []
    for kind, line, text in entries:
        body = text if len(text) <= max_chars else text[:max_chars] + "…"
        out.append({"kind": kind, "line": line, "text": body})
    return out


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def watch(paths: List[Path], interval: float, timeout: Optional[float], any_change: bool, max_chars: int, force_poll: bool) -> int:
    contents: Dict[Path, Optional[str]] = {p: read(p) for p in paths}
    marks = {p: mark_keys(extract_marks(c or "")) for p, c in contents.items()}
    ino = None if force_poll else Inotify.create({p.parent for p in paths})
    emit({
        "event": "ready",
        "backend": "inotify" if ino else "poll",
        "files": [str(p) for p in paths],
        "marks": {str(p): len(m) for p, m in marks.items()},
    })
    deadline = time.monotonic() + timeout if timeout else None
    while True:
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining <= 0:
            emit({"event": "timeout", "files": [str(p) for p in paths]})
            return 2
        if ino:
            if not ino.wait(remaining if remaining is not None else 3600):
                continue
        else:
            time.sleep(interval if remaining is None else min(interval, remaining))
        # Let a burst of writes settle before comparing.
        time.sleep(SETTLE_SECONDS)
        for path in paths:
            current = read(path)
            if current is None:
                if contents[path] is not None and not path.exists():
                    emit({"event": "deleted", "path": str(path)})
                    return 0
                continue
            if current == contents[path]:
                continue
            before = marks[path]
            after = mark_keys(extract_marks(current))
            contents[path] = current
            marks[path] = after
            added = [after[k] for k in after if k not in before]
            removed = [before[k] for k in before if k not in after]
            if added or removed or any_change:
                emit({
                    "event": "changed",
                    "path": str(path),
                    "added": describe(added, max_chars),
                    "removed": describe(removed, max_chars),
                })
                return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Exit when the CriticMarkup in a note changes.")
    parser.add_argument("paths", nargs="+", help="Markdown files to watch")
    parser.add_argument("--timeout", type=float, default=None, help="give up after this many seconds")
    parser.add_argument("--any-change", action="store_true", help="also exit on edits that touch no CriticMarkup")
    parser.add_argument("--max-chars", type=int, default=400, help="truncate reported mark text (default 400)")
    parser.add_argument("--interval", type=float, default=0.5, help="poll interval in seconds when inotify is unavailable (default 0.5)")
    parser.add_argument("--poll", action="store_true", help="poll even where inotify is available")
    args = parser.parse_args()
    paths = [Path(p).expanduser().resolve() for p in args.paths]
    for p in paths:
        if p.is_dir():
            print(json.dumps({"event": "error", "message": f"{p} is a directory"}), file=sys.stderr)
            return 1
    try:
        return watch(paths, args.interval, args.timeout, args.any_change, args.max_chars, args.poll)
    except KeyboardInterrupt:
        emit({"event": "cancelled"})
        return 130


if __name__ == "__main__":
    sys.exit(main())
