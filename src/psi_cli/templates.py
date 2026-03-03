"""Calc and report templates."""

from __future__ import annotations

from typing import Any


CALC_FIELDS: dict[str, Any] = {
    "id": "",
    "title": "",
    "date": "",
    "status": "planned",
    "code": "",
    "computer": "",
    "tags": [],
    "parents": [],
    "children": [],
    "reports": [],
    "hpc_path": "",
    "key_results": {},
    "notes": "",
}

CALC_BODY = """\

# {id}: {title}

## Description

{{What this calculation does and why}}

## Method

{{Code, functional, parameters, convergence settings, etc.}}

## Results

{{Key outcomes, tables, figures}}

## Notes

{{Anything else: problems, observations, follow-up ideas}}
"""

REPORT_FIELDS: dict[str, Any] = {
    "id": "",
    "title": "",
    "date": "",
    "status": "draft",
    "calcs": [],
    "tags": [],
    "notes": "",
}

REPORT_BODY = """\

# {id}: {title}

## Purpose

{{What question this report answers}}

## Analysis

{{Methods, comparisons, discussion}}

## Conclusions

{{Key findings, next steps}}
"""


def make_calc(id: str, title: str, date: str, **overrides: Any) -> tuple[dict[str, Any], str]:
    """Create calc metadata and body from template."""
    metadata = dict(CALC_FIELDS)
    metadata["id"] = id
    metadata["title"] = title
    metadata["date"] = date
    metadata.update(overrides)
    body = CALC_BODY.format(id=id, title=title)
    return metadata, body


def make_report(id: str, title: str, date: str, **overrides: Any) -> tuple[dict[str, Any], str]:
    """Create report metadata and body from template."""
    metadata = dict(REPORT_FIELDS)
    metadata["id"] = id
    metadata["title"] = title
    metadata["date"] = date
    metadata.update(overrides)
    body = REPORT_BODY.format(id=id, title=title)
    return metadata, body
