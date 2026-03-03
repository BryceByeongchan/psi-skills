#!/usr/bin/env python3
"""Initialize psi provenance tracking: create calc_db/ and reports/ with index files."""

from __future__ import annotations

import argparse
from pathlib import Path


# --- Inline: markdown_table ---

def _parse_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


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


# --- Constants ---

CALC_HEADERS = ["id", "title", "date", "status", "code", "computer", "parents", "tags"]
REPORT_HEADERS = ["id", "title", "date", "status", "calcs", "tags"]
CALC_PREAMBLE = "# Calculation Index\n\n"
REPORT_PREAMBLE = "# Report Index\n\n"


# --- Main ---

def main() -> None:
    calc_dir = Path("calc_db")
    reports_dir = Path("reports")

    calc_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    calc_index = calc_dir / "index.md"
    if not calc_index.exists():
        write_index(calc_index, CALC_PREAMBLE, CALC_HEADERS, [])
        print(f"Created {calc_index}")
    else:
        print(f"Already exists: {calc_index}")

    reports_index = reports_dir / "index.md"
    if not reports_index.exists():
        write_index(reports_index, REPORT_PREAMBLE, REPORT_HEADERS, [])
        print(f"Created {reports_index}")
    else:
        print(f"Already exists: {reports_index}")

    print("Initialization complete.")


if __name__ == "__main__":
    argparse.ArgumentParser(description="Initialize psi provenance tracking").parse_args()
    main()
