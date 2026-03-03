"""Tests for frontmatter module."""

import pytest

from psi_cli.frontmatter import (
    deep_merge,
    parse_frontmatter,
    read_frontmatter,
    render_frontmatter,
    write_frontmatter,
)


SAMPLE = """\
---
id: c001
title: Si bulk relax
date: 2024-01-01
status: completed
code: VASP
computer: local
tags: [silicon, relax]
parents: []
children: [c002]
reports: []
hpc_path: ""
key_results: {energy: -5.43}
notes: ""
---

# c001: Si bulk relax

Some body text.
"""


class TestParseFrontmatter:
    def test_basic(self):
        meta, body = parse_frontmatter(SAMPLE)
        assert meta["id"] == "c001"
        assert meta["title"] == "Si bulk relax"
        assert meta["tags"] == ["silicon", "relax"]
        assert meta["children"] == ["c002"]
        assert meta["key_results"] == {"energy": -5.43}
        assert "# c001" in body

    def test_no_frontmatter(self):
        with pytest.raises(ValueError):
            parse_frontmatter("No front matter here")

    def test_empty_frontmatter(self):
        text = "---\n---\nBody"
        meta, body = parse_frontmatter(text)
        assert meta == {}
        assert body == "Body"


class TestRenderFrontmatter:
    def test_round_trip(self):
        meta, body = parse_frontmatter(SAMPLE)
        rendered = render_frontmatter(meta, body)
        meta2, body2 = parse_frontmatter(rendered)
        assert meta2 == meta
        assert body2.strip() == body.strip()

    def test_flow_style_short_list(self):
        meta = {"id": "c001", "tags": ["a", "b"]}
        rendered = render_frontmatter(meta, "")
        assert "[a, b]" in rendered

    def test_flow_style_leaf_dict(self):
        meta = {"id": "c001", "key_results": {"energy": -5.43, "bandgap": 1.12}}
        rendered = render_frontmatter(meta, "")
        assert "{energy: -5.43, bandgap: 1.12}" in rendered

    def test_empty_list(self):
        meta = {"id": "c001", "parents": []}
        rendered = render_frontmatter(meta, "")
        assert "parents: []" in rendered

    def test_empty_dict(self):
        meta = {"id": "c001", "key_results": {}}
        rendered = render_frontmatter(meta, "")
        assert "key_results: {}" in rendered

    def test_empty_string(self):
        meta = {"id": "c001", "notes": ""}
        rendered = render_frontmatter(meta, "")
        assert 'notes: ""' in rendered

    def test_key_ordering_calc(self):
        meta = {"tags": ["a"], "id": "c001", "title": "test", "status": "planned"}
        rendered = render_frontmatter(meta, "")
        lines = rendered.split("\n")
        # id should come before tags
        id_line = next(i for i, l in enumerate(lines) if l.startswith("id:"))
        tags_line = next(i for i, l in enumerate(lines) if l.startswith("tags:"))
        assert id_line < tags_line

    def test_key_ordering_report(self):
        meta = {"tags": ["a"], "id": "r001", "title": "test", "calcs": ["c001"]}
        rendered = render_frontmatter(meta, "")
        lines = rendered.split("\n")
        id_line = next(i for i, l in enumerate(lines) if l.startswith("id:"))
        calcs_line = next(i for i, l in enumerate(lines) if l.startswith("calcs:"))
        assert id_line < calcs_line

    def test_special_chars_in_title(self):
        meta = {"id": "c001", "title": "Si: bulk & relax #1"}
        rendered = render_frontmatter(meta, "")
        meta2, _ = parse_frontmatter(rendered)
        assert meta2["title"] == "Si: bulk & relax #1"


class TestFileIO:
    def test_read_write(self, tmp_path):
        path = tmp_path / "test.md"
        meta = {"id": "c001", "title": "test", "tags": ["a", "b"]}
        body = "\n# c001: test\n\nBody.\n"
        write_frontmatter(path, meta, body)
        meta2, body2 = read_frontmatter(path)
        assert meta2["id"] == "c001"
        assert meta2["tags"] == ["a", "b"]
        assert "Body." in body2

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "a" / "b" / "c.md"
        write_frontmatter(path, {"id": "c001"}, "")
        assert path.exists()


class TestDeepMerge:
    def test_basic(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        assert deep_merge(base, override) == {"a": 1, "b": 3, "c": 4}

    def test_nested_dict(self):
        base = {"key_results": {"energy": -5.0, "bandgap": 1.0}}
        override = {"key_results": {"energy": -5.43}}
        result = deep_merge(base, override)
        assert result == {"key_results": {"energy": -5.43, "bandgap": 1.0}}

    def test_list_replaced(self):
        base = {"tags": ["a", "b"]}
        override = {"tags": ["c"]}
        assert deep_merge(base, override) == {"tags": ["c"]}
