"""Front matter read/write commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from psi_cli.frontmatter import deep_merge, read_frontmatter, write_frontmatter
from psi_cli.main import die
from psi_cli.templates import make_calc, make_report


def run_fm(args) -> None:
    if args.fm_command == "read":
        _fm_read(args.path)
    elif args.fm_command == "write":
        _fm_write(args.path, args.template)
    else:
        die("Usage: psi-cli fm {read|write}")


def _fm_read(path: str) -> None:
    """Read front matter and output as JSON."""
    p = Path(path)
    if not p.exists():
        die(f"File not found: {path}")
    metadata, _ = read_frontmatter(p)
    json.dump(metadata, sys.stdout, ensure_ascii=False, default=str)
    print()


def _fm_write(path: str, template: str | None) -> None:
    """Read JSON from stdin, deep-merge into existing front matter (or create from template)."""
    raw = sys.stdin.read().strip()
    if not raw:
        die("No JSON input on stdin")
    try:
        override = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"Invalid JSON: {e}")

    p = Path(path)
    if p.exists():
        metadata, body = read_frontmatter(p)
        metadata = deep_merge(metadata, override)
    elif template == "calc":
        id_val = override.get("id", "")
        title = override.get("title", "")
        date = override.get("date", "")
        metadata, body = make_calc(id_val, title, date)
        # Apply remaining overrides
        for k, v in override.items():
            if k not in ("id", "title", "date"):
                if isinstance(metadata.get(k), dict) and isinstance(v, dict):
                    metadata[k] = deep_merge(metadata[k], v)
                else:
                    metadata[k] = v
    elif template == "report":
        id_val = override.get("id", "")
        title = override.get("title", "")
        date = override.get("date", "")
        metadata, body = make_report(id_val, title, date)
        for k, v in override.items():
            if k not in ("id", "title", "date"):
                if isinstance(metadata.get(k), dict) and isinstance(v, dict):
                    metadata[k] = deep_merge(metadata[k], v)
                else:
                    metadata[k] = v
    else:
        die(f"File not found and no template specified: {path}")
        return  # unreachable, for type checker

    write_frontmatter(p, metadata, body)
    print(f"Wrote {p}")
