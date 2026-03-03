"""DAG rendering with Unicode box-drawing characters."""

from __future__ import annotations

from pathlib import Path

from psi_cli.frontmatter import read_frontmatter
from psi_cli.main import die


def run_graph(args) -> None:
    target_id = args.id if hasattr(args, "id") else None
    _render_graph(target_id)


def _load_all_calcs() -> dict[str, dict]:
    """Load all calc metadata keyed by id."""
    calc_dir = Path("calc_db")
    calcs = {}
    if not calc_dir.exists():
        return calcs
    for readme in sorted(calc_dir.glob("c*/README.md")):
        try:
            metadata, _ = read_frontmatter(readme)
            cid = metadata.get("id", "")
            if cid:
                calcs[cid] = metadata
        except (ValueError, Exception):
            pass
    return calcs


def _format_node(cid: str, calcs: dict[str, dict], highlight: str | None = None) -> str:
    """Format a single node for display."""
    meta = calcs.get(cid, {})
    title = meta.get("title", "")
    status = meta.get("status", "?")
    label = f"{cid}"
    if title:
        label += f" ({title})"
    label += f" [{status}]"
    if highlight and cid == highlight:
        label = f">>> {label} <<<"
    return label


def _render_tree(cid: str, calcs: dict[str, dict], prefix: str, is_last: bool,
                 highlight: str | None, visited: set[str], lines: list[str]) -> None:
    """Recursively render a tree node and its children."""
    if cid in visited:
        connector = "└─ " if is_last else "├─ "
        lines.append(f"{prefix}{connector}{cid} (cycle)")
        return
    visited.add(cid)

    connector = "└─ " if is_last else "├─ "
    lines.append(f"{prefix}{connector}{_format_node(cid, calcs, highlight)}")

    children = calcs.get(cid, {}).get("children", [])
    if not isinstance(children, list):
        children = []

    child_prefix = prefix + ("   " if is_last else "│  ")
    for i, child in enumerate(children):
        is_child_last = (i == len(children) - 1)
        _render_tree(child, calcs, child_prefix, is_child_last, highlight, visited, lines)


def _find_ancestors(cid: str, calcs: dict[str, dict]) -> set[str]:
    """Find all ancestor IDs."""
    ancestors = set()
    queue = [cid]
    while queue:
        current = queue.pop(0)
        parents = calcs.get(current, {}).get("parents", [])
        if not isinstance(parents, list):
            parents = []
        for p in parents:
            if p not in ancestors and p in calcs:
                ancestors.add(p)
                queue.append(p)
    return ancestors


def _find_descendants(cid: str, calcs: dict[str, dict]) -> set[str]:
    """Find all descendant IDs."""
    descendants = set()
    queue = [cid]
    while queue:
        current = queue.pop(0)
        children = calcs.get(current, {}).get("children", [])
        if not isinstance(children, list):
            children = []
        for c in children:
            if c not in descendants and c in calcs:
                descendants.add(c)
                queue.append(c)
    return descendants


def _render_graph(target_id: str | None) -> None:
    calcs = _load_all_calcs()
    if not calcs:
        print("No calculations found.")
        return

    if target_id:
        if target_id not in calcs:
            die(f"Calc not found: {target_id}")

        # Show ancestors + target + descendants
        ancestors = _find_ancestors(target_id, calcs)
        descendants = _find_descendants(target_id, calcs)
        relevant = ancestors | descendants | {target_id}

        # Find roots among relevant nodes
        roots = []
        for cid in relevant:
            parents = calcs.get(cid, {}).get("parents", [])
            if not isinstance(parents, list):
                parents = []
            if not any(p in relevant for p in parents):
                roots.append(cid)
        roots.sort()

        # Filter children to only show relevant nodes
        filtered_calcs = {}
        for cid in relevant:
            meta = dict(calcs[cid])
            children = meta.get("children", [])
            if isinstance(children, list):
                meta["children"] = [c for c in children if c in relevant]
            filtered_calcs[cid] = meta
    else:
        # Show full graph — find root nodes
        filtered_calcs = calcs
        roots = []
        for cid, meta in calcs.items():
            parents = meta.get("parents", [])
            if not isinstance(parents, list):
                parents = []
            if not parents:
                roots.append(cid)
        roots.sort()

    if not roots:
        # All nodes have parents — pick lowest ID
        roots = [sorted(filtered_calcs.keys())[0]]

    lines: list[str] = []
    visited: set[str] = set()
    for i, root in enumerate(roots):
        is_last = (i == len(roots) - 1)
        label = _format_node(root, filtered_calcs, target_id)
        lines.append(label)
        visited.add(root)

        children = filtered_calcs.get(root, {}).get("children", [])
        if not isinstance(children, list):
            children = []
        for j, child in enumerate(children):
            is_child_last = (j == len(children) - 1)
            _render_tree(child, filtered_calcs, "", is_child_last, target_id, visited, lines)

    print("\n".join(lines))
