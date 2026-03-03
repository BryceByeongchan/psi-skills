"""YAML front matter parse/write operations."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


# Key ordering for calc and report schemas
CALC_KEY_ORDER = [
    "id", "title", "date", "status", "code", "computer", "tags",
    "parents", "children", "reports", "hpc_path", "key_results", "notes",
]
REPORT_KEY_ORDER = [
    "id", "title", "date", "status", "calcs", "tags", "notes",
]

_FM_PATTERN = re.compile(r"\A---\n(.*?)---\n?(.*)", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split text into (metadata_dict, body_string).

    Raises ValueError if no valid front matter delimiters found.
    """
    m = _FM_PATTERN.match(text)
    if not m:
        raise ValueError("No valid YAML front matter found")
    raw_yaml, body = m.group(1), m.group(2)
    metadata = yaml.safe_load(raw_yaml) or {}
    return metadata, body


def _detect_key_order(metadata: dict[str, Any]) -> list[str]:
    """Pick the right key ordering based on the id prefix."""
    id_val = str(metadata.get("id", ""))
    if id_val.startswith("r"):
        return REPORT_KEY_ORDER
    return CALC_KEY_ORDER


class _PsiDumper(yaml.SafeDumper):
    """Custom YAML dumper: flow style for short lists/leaf dicts, block for top-level."""
    pass


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_PsiDumper.add_representer(str, _str_representer)


def _is_short_list(lst: list) -> bool:
    """True if the list is short enough for flow style."""
    return all(isinstance(v, (str, int, float)) for v in lst) and len(lst) <= 10


def _is_leaf_dict(d: dict) -> bool:
    """True if all values are scalars (good for flow style)."""
    return all(isinstance(v, (str, int, float, bool, type(None))) for v in d.values()) and len(d) <= 8


def _ordered_metadata(metadata: dict[str, Any]) -> list[tuple[str, Any]]:
    """Return metadata items in schema order, unknown keys at end."""
    key_order = _detect_key_order(metadata)
    ordered = []
    for k in key_order:
        if k in metadata:
            ordered.append((k, metadata[k]))
    for k in metadata:
        if k not in key_order:
            ordered.append((k, metadata[k]))
    return ordered


def render_frontmatter(metadata: dict[str, Any], body: str) -> str:
    """Render metadata dict + body string back to file content."""
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


def _yaml_scalar(value: Any) -> str:
    """Format a scalar value for inline YAML."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        if any(c in value for c in ",:{}[]#&*!|>'\"%@`"):
            return f'"{value}"'
        return value
    if value is None:
        return "null"
    return str(value)


def read_frontmatter(path: str | Path) -> tuple[dict[str, Any], str]:
    """Read a file and parse its front matter."""
    text = Path(path).read_text(encoding="utf-8")
    return parse_frontmatter(text)


def write_frontmatter(path: str | Path, metadata: dict[str, Any], body: str) -> None:
    """Write metadata + body to a file, creating parent dirs if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_frontmatter(metadata, body), encoding="utf-8")


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base. Lists and scalars are replaced, dicts are merged recursively."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
