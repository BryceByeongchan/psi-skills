"""Project status summary."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from psi_cli.commands.computer import _read_registry, _ssh_check
from psi_cli.frontmatter import read_frontmatter


def run_status(args) -> None:
    """Output project status as JSON."""
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

    # Recent calcs (last 5 by date)
    sorted_calcs = sorted(calcs, key=lambda c: c.get("date", ""), reverse=True)
    result["recent_calcs"] = [
        {"id": c.get("id"), "title": c.get("title"), "date": c.get("date"), "status": c.get("status")}
        for c in sorted_calcs[:5]
    ]

    # Orphan calcs (completed but no reports)
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
