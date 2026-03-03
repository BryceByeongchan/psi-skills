"""Computer registry operations."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from psi_cli.main import die

REGISTRY_PATH = Path.home() / ".claude" / "agent-memory" / "psi" / "computers.yaml"


def _read_registry() -> dict[str, Any]:
    """Read the computer registry."""
    if not REGISTRY_PATH.exists():
        return {"computers": {}}
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    if "computers" not in data:
        data["computers"] = {}
    return data


def _write_registry(data: dict[str, Any]) -> None:
    """Write the computer registry."""
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def _ssh_check(hostname: str) -> bool:
    """Check SSH ControlMaster connectivity. Returns True if connected."""
    try:
        result = subprocess.run(
            ["ssh", "-O", "check", hostname],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_computer(args) -> None:
    if args.computer_command == "list":
        _list_computers(args.as_json)
    elif args.computer_command == "add":
        _add_computer(args.name, args.json_data)
    elif args.computer_command == "remove":
        _remove_computer(args.name)
    elif args.computer_command == "ssh-check":
        _ssh_check_cmd(args.name)
    else:
        die("Usage: psi-cli computer {list|add|remove|ssh-check}")


def _list_computers(as_json: bool) -> None:
    """List registered computers."""
    data = _read_registry()
    computers = data.get("computers", {})

    if as_json:
        json.dump(computers, sys.stdout, ensure_ascii=False, default=str)
        print()
        return

    if not computers:
        print("No computers registered.")
        return

    # Table format
    headers = ["name", "type", "hostname", "scheduler", "work_dir"]
    rows = []
    for name, config in computers.items():
        rows.append([
            name,
            config.get("type", "-"),
            config.get("hostname", "-"),
            config.get("scheduler", "-"),
            config.get("work_dir", "-"),
        ])

    from psi_cli.markdown_table import render_table
    print(render_table(headers, rows), end="")

    # SSH status for HPC computers
    for name, config in computers.items():
        if config.get("type") == "hpc":
            hostname = config.get("hostname", "")
            if hostname:
                connected = _ssh_check(hostname)
                status = "connected" if connected else "disconnected"
                print(f"  {name}: SSH {status}")


def _add_computer(name: str, json_data: str | None) -> None:
    """Add a computer to the registry."""
    data = _read_registry()

    if json_data:
        try:
            config = json.loads(json_data)
        except json.JSONDecodeError as e:
            die(f"Invalid JSON: {e}")
    else:
        # Read from stdin
        raw = sys.stdin.read().strip()
        if not raw:
            die("No JSON input provided (pass as argument or via stdin)")
        try:
            config = json.loads(raw)
        except json.JSONDecodeError as e:
            die(f"Invalid JSON from stdin: {e}")

    data["computers"][name] = config
    _write_registry(data)
    print(f"Added computer: {name}")


def _remove_computer(name: str) -> None:
    """Remove a computer from the registry."""
    data = _read_registry()
    if name not in data["computers"]:
        die(f"Computer not found: {name}")

    del data["computers"][name]
    _write_registry(data)
    print(f"Removed computer: {name}")


def _ssh_check_cmd(name: str) -> None:
    """Check SSH connectivity for a computer."""
    data = _read_registry()
    if name not in data["computers"]:
        die(f"Computer not found: {name}")

    config = data["computers"][name]
    if config.get("type") != "hpc":
        die(f"{name} is not an HPC computer")

    hostname = config.get("hostname", "")
    if not hostname:
        die(f"No hostname set for {name}")

    if _ssh_check(hostname):
        print(f"SSH connected: {name} ({hostname})")
        sys.exit(0)
    else:
        print(f"SSH disconnected: {name} ({hostname})", file=sys.stderr)
        sys.exit(2)
