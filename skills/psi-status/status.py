#!/usr/bin/env python3
"""Project status summary — outputs JSON."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

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


# --- Inline: computer registry (read only) ---

REGISTRY_PATH = Path.home() / ".claude" / "agent-memory" / "psi" / "computers.yaml"


def _read_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {"computers": {}}
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    if "computers" not in data:
        data["computers"] = {}
    # Handle list format: convert [{id: name, ...}, ...] to {name: {...}, ...}
    if isinstance(data["computers"], list):
        by_name = {}
        for entry in data["computers"]:
            name = entry.get("id") or entry.get("label") or entry.get("name", "unknown")
            by_name[name] = {k: v for k, v in entry.items() if k not in ("id", "label")}
        data["computers"] = by_name
    return data


def _ssh_check(hostname: str) -> bool:
    try:
        result = subprocess.run(
            ["ssh", "-O", "check", hostname],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# --- Main ---

def main() -> None:
    result = {}

    # Computers
    registry = _read_registry()
    computers = registry.get("computers", {})
    comp_status = {}
    for name, config in computers.items():
        entry = {"type": config.get("type", "unknown")}
        if config.get("type") == "hpc" and config.get("hostname"):
            entry["ssh"] = "connected" if _ssh_check(config["hostname"]) else "disconnected"
        comp_status[name] = entry
    result["computers"] = comp_status

    # Calculations
    calc_dir = Path("calc_db")
    calcs = []
    if calc_dir.exists():
        for readme in sorted(calc_dir.glob("c*/README.md")):
            try:
                metadata, _ = read_frontmatter(readme)
                calcs.append(metadata)
            except (ValueError, Exception):
                pass

    status_counts = Counter(c.get("status", "unknown") for c in calcs)
    result["calc_counts"] = dict(status_counts)
    result["total_calcs"] = len(calcs)

    sorted_calcs = sorted(calcs, key=lambda c: c.get("date", ""), reverse=True)
    result["recent_calcs"] = [
        {"id": c.get("id"), "title": c.get("title"), "date": c.get("date"), "status": c.get("status")}
        for c in sorted_calcs[:5]
    ]

    orphans = [
        c.get("id") for c in calcs
        if c.get("status") == "completed" and not c.get("reports")
    ]
    result["orphan_calcs"] = orphans

    # Reports
    report_dir = Path("reports")
    reports = []
    if report_dir.exists():
        for readme in sorted(report_dir.glob("r*/README.md")):
            try:
                metadata, _ = read_frontmatter(readme)
                reports.append(metadata)
            except (ValueError, Exception):
                pass

    result["total_reports"] = len(reports)
    draft_reports = [r.get("id") for r in reports if r.get("status") == "draft"]
    result["draft_reports"] = draft_reports

    json.dump(result, sys.stdout, ensure_ascii=False, default=str, indent=2)
    print()


if __name__ == "__main__":
    main()
