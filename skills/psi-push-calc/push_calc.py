#!/usr/bin/env python3
"""Push calculation files to remote HPC via rsync."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


# --- Inline: frontmatter ---

_FM_PATTERN = re.compile(r"\A---\n(.*?)---\n?(.*)", re.DOTALL)

CALC_KEY_ORDER = [
    "id", "title", "date", "status", "code", "computer", "tags",
    "parents", "children", "reports", "hpc_path", "key_results", "notes",
]


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


class _PsiDumper(yaml.SafeDumper):
    pass


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_PsiDumper.add_representer(str, _str_representer)


def _is_short_list(lst: list) -> bool:
    return all(isinstance(v, (str, int, float)) for v in lst) and len(lst) <= 10


def _is_leaf_dict(d: dict) -> bool:
    return all(isinstance(v, (str, int, float, bool, type(None))) for v in d.values()) and len(d) <= 8


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        if any(c in value for c in ",:{}[]#&*!|>'\"%@`"):
            return f'"{value}"'
        return value
    if value is None:
        return "null"
    return str(value)


def _detect_key_order(metadata: dict) -> list[str]:
    id_val = str(metadata.get("id", ""))
    if id_val.startswith("r"):
        return ["id", "title", "date", "status", "calcs", "tags", "notes"]
    return CALC_KEY_ORDER


def _ordered_metadata(metadata: dict) -> list[tuple[str, Any]]:
    key_order = _detect_key_order(metadata)
    ordered = []
    for k in key_order:
        if k in metadata:
            ordered.append((k, metadata[k]))
    for k in metadata:
        if k not in key_order:
            ordered.append((k, metadata[k]))
    return ordered


def render_frontmatter(metadata: dict, body: str) -> str:
    lines = ["---"]
    ordered = _ordered_metadata(metadata)
    for key, value in ordered:
        if value is None:
            lines.append(f"{key}:")
        elif isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            elif _is_short_list(value):
                items = ", ".join(_yaml_scalar(v) for v in value)
                lines.append(f"{key}: [{items}]")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {_yaml_scalar(item)}")
        elif isinstance(value, dict):
            if not value:
                lines.append(f"{key}: {{}}")
            elif _is_leaf_dict(value):
                items = ", ".join(f"{k}: {_yaml_scalar(v)}" for k, v in value.items())
                lines.append(f"{key}: {{{items}}}")
            else:
                dumped = yaml.dump(value, Dumper=_PsiDumper, default_flow_style=False, sort_keys=False).rstrip()
                lines.append(f"{key}:")
                for line in dumped.split("\n"):
                    lines.append(f"  {line}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, str):
            if "\n" in value or ":" in value or "#" in value or value.startswith(("{", "[", "'", '"')):
                quoted = yaml.dump(value, Dumper=_PsiDumper, default_flow_style=True).strip()
                lines.append(f"{key}: {quoted}")
            else:
                lines.append(f"{key}: {value}" if value else f'{key}: ""')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    result = "\n".join(lines) + "\n"
    if body:
        result += body
    return result


def write_frontmatter(path: Path, metadata: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_frontmatter(metadata, body), encoding="utf-8")


# --- Inline: computer registry ---

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


# --- Sync logic ---

def _get_sync_info(calc_id: str) -> tuple[dict, str, dict, Path]:
    local_dir = Path("calc_db") / calc_id
    readme = local_dir / "README.md"
    if not readme.exists():
        print(f"Error: Calc not found: {readme}", file=sys.stderr)
        sys.exit(1)

    metadata, body = read_frontmatter(readme)
    computer_name = metadata.get("computer", "")
    if not computer_name or computer_name == "local":
        print(f"Error: Calc {calc_id} has no remote computer set (computer: '{computer_name}')", file=sys.stderr)
        sys.exit(1)

    registry = _read_registry()
    computers = registry.get("computers", {})
    if computer_name not in computers:
        print(f"Error: Computer '{computer_name}' not in registry", file=sys.stderr)
        sys.exit(1)

    config = computers[computer_name]
    if config.get("type") != "hpc":
        print(f"Error: Computer '{computer_name}' is not HPC type", file=sys.stderr)
        sys.exit(1)

    hostname = config.get("hostname", "")
    if not hostname:
        print(f"Error: No hostname for computer '{computer_name}'", file=sys.stderr)
        sys.exit(1)

    if not _ssh_check(hostname):
        print(f"Error: SSH not connected to {computer_name} ({hostname}). Run: ssh -MNf {hostname}", file=sys.stderr)
        sys.exit(2)

    hpc_path = metadata.get("hpc_path", "")
    if not hpc_path:
        work_dir = config.get("work_dir", "")
        if not work_dir:
            print(f"Error: No work_dir set for '{computer_name}' and no hpc_path in calc", file=sys.stderr)
            sys.exit(1)
        project_name = Path.cwd().name
        hpc_path = f"{work_dir}/{project_name}/{calc_id}/"
        metadata["hpc_path"] = hpc_path
        write_frontmatter(readme, metadata, body)

    if not hpc_path.endswith("/"):
        hpc_path += "/"

    return metadata, hpc_path, config, local_dir


def _rsync(src: str, dst: str, hostname: str, exclude: list[str] | None = None,
           max_size: str | None = None) -> subprocess.CompletedProcess:
    cmd = ["rsync", "-avz", "-e", "ssh"]
    if max_size:
        cmd.extend(["--max-size", max_size])
    if exclude:
        for ex in exclude:
            cmd.extend(["--exclude", ex])
    cmd.extend([src, dst])
    print(f"  {' '.join(cmd)}", file=sys.stderr)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300)


# --- Main ---

def main() -> None:
    parser = argparse.ArgumentParser(description="Push calc files to remote")
    parser.add_argument("calc_id", help="Calculation ID (e.g., c001)")
    parser.add_argument("--all", action="store_true", dest="sync_all", help="Sync entire directory")
    args = parser.parse_args()

    metadata, hpc_path, config, local_dir = _get_sync_info(args.calc_id)
    hostname = config["hostname"]
    remote_base = f"{hostname}:{hpc_path}"

    subprocess.run(
        ["ssh", hostname, "mkdir", "-p", hpc_path],
        capture_output=True, text=True, timeout=30,
    )

    if args.sync_all:
        _rsync(f"{local_dir}/", remote_base, hostname)
    else:
        for subdir in ["input", "code"]:
            src = local_dir / subdir
            if src.exists():
                subprocess.run(
                    ["ssh", hostname, "mkdir", "-p", f"{hpc_path}{subdir}"],
                    capture_output=True, text=True, timeout=30,
                )
                _rsync(f"{src}/", f"{remote_base}{subdir}/", hostname)
        readme = local_dir / "README.md"
        if readme.exists():
            _rsync(str(readme), remote_base, hostname)

    print(f"Pushed {args.calc_id} to {hostname}:{hpc_path}")


if __name__ == "__main__":
    main()
