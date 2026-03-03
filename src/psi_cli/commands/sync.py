"""File sync operations: push/pull calc files to/from remote."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from psi_cli.commands.computer import _read_registry, _ssh_check
from psi_cli.frontmatter import read_frontmatter, write_frontmatter
from psi_cli.main import die

LARGE_FILE_THRESHOLD = 50 * 1024 * 1024  # 50 MB


def run_sync(args) -> None:
    if args.sync_command == "push":
        _push(args.calc_id, args.sync_all)
    elif args.sync_command == "pull":
        _pull(args.calc_id, args.sync_all)
    else:
        die("Usage: psi-cli sync {push|pull}")


def _get_sync_info(calc_id: str) -> tuple[dict, str, dict, Path]:
    """Get sync info: (metadata, hpc_path, computer_config, local_calc_dir).

    Also updates hpc_path in front matter if not set.
    """
    local_dir = Path("calc_db") / calc_id
    readme = local_dir / "README.md"
    if not readme.exists():
        die(f"Calc not found: {readme}")

    metadata, body = read_frontmatter(readme)
    computer_name = metadata.get("computer", "")
    if not computer_name or computer_name == "local":
        die(f"Calc {calc_id} has no remote computer set (computer: '{computer_name}')")

    registry = _read_registry()
    computers = registry.get("computers", {})
    if computer_name not in computers:
        die(f"Computer '{computer_name}' not in registry")

    config = computers[computer_name]
    if config.get("type") != "hpc":
        die(f"Computer '{computer_name}' is not HPC type")

    hostname = config.get("hostname", "")
    if not hostname:
        die(f"No hostname for computer '{computer_name}'")

    # Check SSH
    if not _ssh_check(hostname):
        die(f"SSH not connected to {computer_name} ({hostname}). Run: ssh -MNf {hostname}", code=2)

    # Resolve hpc_path
    hpc_path = metadata.get("hpc_path", "")
    if not hpc_path:
        work_dir = config.get("work_dir", "")
        if not work_dir:
            die(f"No work_dir set for computer '{computer_name}' and no hpc_path in calc")
        project_name = Path.cwd().name
        hpc_path = f"{work_dir}/{project_name}/{calc_id}/"
        metadata["hpc_path"] = hpc_path
        write_frontmatter(readme, metadata, body)

    if not hpc_path.endswith("/"):
        hpc_path += "/"

    return metadata, hpc_path, config, local_dir


def _rsync(src: str, dst: str, hostname: str, exclude: list[str] | None = None,
           max_size: str | None = None, dry_run: bool = False) -> subprocess.CompletedProcess:
    """Run rsync with standard options."""
    cmd = ["rsync", "-avz", "-e", "ssh"]
    if max_size:
        cmd.extend(["--max-size", max_size])
    if dry_run:
        cmd.append("--dry-run")
    if exclude:
        for ex in exclude:
            cmd.extend(["--exclude", ex])
    cmd.extend([src, dst])

    print(f"  {' '.join(cmd)}", file=sys.stderr)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300)


def _push(calc_id: str, sync_all: bool) -> None:
    """Push calc files to remote."""
    metadata, hpc_path, config, local_dir = _get_sync_info(calc_id)
    hostname = config["hostname"]
    remote_base = f"{hostname}:{hpc_path}"

    # Create remote directory
    subprocess.run(
        ["ssh", hostname, "mkdir", "-p", hpc_path],
        capture_output=True, text=True, timeout=30,
    )

    if sync_all:
        result = _rsync(f"{local_dir}/", remote_base, hostname)
    else:
        # Push input/, code/, and README.md
        for subdir in ["input", "code"]:
            src = local_dir / subdir
            if src.exists():
                subprocess.run(
                    ["ssh", hostname, "mkdir", "-p", f"{hpc_path}{subdir}"],
                    capture_output=True, text=True, timeout=30,
                )
                _rsync(f"{src}/", f"{remote_base}{subdir}/", hostname)
        # Push README.md
        readme = local_dir / "README.md"
        if readme.exists():
            _rsync(str(readme), remote_base, hostname)

    print(f"Pushed {calc_id} to {hostname}:{hpc_path}")


def _pull(calc_id: str, sync_all: bool) -> None:
    """Pull calc files from remote."""
    metadata, hpc_path, config, local_dir = _get_sync_info(calc_id)
    hostname = config["hostname"]
    remote_base = f"{hostname}:{hpc_path}"

    if sync_all:
        result = _rsync(remote_base, f"{local_dir}/", hostname)
    else:
        # Pull output/ with size limit
        local_dir.mkdir(parents=True, exist_ok=True)
        output_dir = local_dir / "output"
        output_dir.mkdir(exist_ok=True)
        _rsync(
            f"{remote_base}output/",
            f"{output_dir}/",
            hostname,
            max_size="50M",
        )
        # List large files that were skipped
        result = subprocess.run(
            ["ssh", hostname, "find", f"{hpc_path}output/", "-size", "+50M", "-exec", "ls", "-lh", "{}", ";"],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip():
            print("Large files skipped (>50MB):", file=sys.stderr)
            print(result.stdout, file=sys.stderr)

    print(f"Pulled {calc_id} from {hostname}:{hpc_path}")
