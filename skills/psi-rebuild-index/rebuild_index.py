#!/usr/bin/env python3
"""Rebuild index files from YAML front matter of all README.md files."""

from __future__ import annotations

import fcntl
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import yaml


# --- Inline: frontmatter (read only) ---

_FM_PATTERN = re.compile(r"\A---\n(.*?)---\n?(.*)", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = _FM_PATTERN.match(text)
    if not m:
        raise ValueError("No valid YAML front matter found")
    raw_yaml, body = m.group(1), m.group(2)
    metadata = yaml.safe_load(raw_yaml) or {}
    return metadata, body


def read_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    return parse_frontmatter(text)


# --- Inline: markdown_table ---

def render_table(headers: list[str], rows: list[list[str]]) -> str:
    if not headers:
        return ""
    ncols = len(headers)
    norm_rows = []
    for row in rows:
        if len(row) < ncols:
            row = row + [""] * (ncols - len(row))
        elif len(row) > ncols:
            row = row[:ncols]
        norm_rows.append(row)
    widths = [len(h) for h in headers]
    for row in norm_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    widths = [max(w, 4) for w in widths]

    def fmt_row(cells: list[str]) -> str:
        parts = [f" {cell:<{widths[i]}} " for i, cell in enumerate(cells)]
        return "|" + "|".join(parts) + "|"

    lines = [fmt_row(headers)]
    lines.append("|" + "|".join(f" {'-' * widths[i]} " for i in range(ncols)) + "|")
    for row in norm_rows:
        lines.append(fmt_row(row))
    return "\n".join(lines) + "\n"


def write_index(path: Path, preamble: str, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = preamble + render_table(headers, rows)
    path.write_text(content, encoding="utf-8")


# --- Inline: filelock ---

@contextmanager
def locked_write(path: str | Path, timeout: float = 30.0) -> Generator[Path, None, None]:
    p = Path(path)
    lock_path = p.with_suffix(p.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(lock_path, "w")
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except (OSError, BlockingIOError):
            if time.monotonic() >= deadline:
                lock_fd.close()
                raise TimeoutError(f"Could not acquire lock on {lock_path} within {timeout}s")
            time.sleep(0.05)
    try:
        yield p
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


# --- Constants ---

CALC_HEADERS = ["id", "title", "date", "status", "code", "computer", "parents", "tags"]
REPORT_HEADERS = ["id", "title", "date", "status", "calcs", "tags"]
CALC_PREAMBLE = "# Calculation Index\n\n"
REPORT_PREAMBLE = "# Report Index\n\n"


def _fmt_cell(value, header: str) -> str:
    if value is None or value == "" or value == []:
        return "-"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items())
    return str(value)


# --- Main ---

def _rebuild(dir_path: Path, prefix: str, headers: list[str], preamble: str, glob_pattern: str) -> None:
    readmes = sorted(dir_path.glob(glob_pattern))
    rows = []
    for readme in readmes:
        try:
            metadata, _ = read_frontmatter(readme)
            row = [_fmt_cell(metadata.get(h, "-"), h) for h in headers]
            rows.append(row)
        except (ValueError, Exception) as e:
            print(f"Warning: skipping {readme}: {e}", file=sys.stderr)

    rows.sort(key=lambda r: r[0])

    index_path = dir_path / "index.md"
    with locked_write(index_path):
        write_index(index_path, preamble, headers, rows)
    print(f"Rebuilt {index_path}: {len(rows)} entries")


def main() -> None:
    calc_dir = Path("calc_db")
    if calc_dir.exists():
        _rebuild(calc_dir, "c", CALC_HEADERS, CALC_PREAMBLE, "c*/README.md")
    else:
        print("calc_db/ not found, skipping", file=sys.stderr)

    report_dir = Path("reports")
    if report_dir.exists():
        _rebuild(report_dir, "r", REPORT_HEADERS, REPORT_PREAMBLE, "r*/README.md")
    else:
        print("reports/ not found, skipping", file=sys.stderr)


if __name__ == "__main__":
    main()
