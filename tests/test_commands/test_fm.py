"""Tests for fm command."""

import json
import subprocess
import sys

import pytest

from psi_cli.frontmatter import read_frontmatter, render_frontmatter, write_frontmatter
from psi_cli.templates import make_calc


class TestFmRead:
    def test_read(self, tmp_path):
        meta = {"id": "c001", "title": "test", "tags": ["a"]}
        write_frontmatter(tmp_path / "README.md", meta, "\n# test\n")

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "fm", "read", str(tmp_path / "README.md")],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["id"] == "c001"
        assert data["tags"] == ["a"]

    def test_read_nonexistent(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "fm", "read", str(tmp_path / "nope.md")],
            capture_output=True, text=True,
        )
        assert result.returncode != 0


class TestFmWrite:
    def test_write_new_from_template(self, tmp_path):
        path = tmp_path / "calc_db" / "c001" / "README.md"
        data = json.dumps({"id": "c001", "title": "Si relax", "date": "2024-01-01", "code": "VASP"})

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "fm", "write", str(path), "--template", "calc"],
            input=data, capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert path.exists()

        meta, body = read_frontmatter(path)
        assert meta["id"] == "c001"
        assert meta["code"] == "VASP"
        assert meta["status"] == "planned"  # from template default
        assert "# c001" in body

    def test_write_merge_existing(self, tmp_path):
        path = tmp_path / "README.md"
        write_frontmatter(path, {"id": "c001", "status": "planned", "tags": ["a"]}, "\n# test\n")

        data = json.dumps({"status": "completed"})
        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "fm", "write", str(path)],
            input=data, capture_output=True, text=True,
        )
        assert result.returncode == 0

        meta, body = read_frontmatter(path)
        assert meta["status"] == "completed"
        assert meta["tags"] == ["a"]  # preserved

    def test_deep_merge_key_results(self, tmp_path):
        path = tmp_path / "README.md"
        write_frontmatter(
            path,
            {"id": "c001", "key_results": {"energy": -5.0, "bandgap": 1.0}},
            "\n# test\n",
        )

        data = json.dumps({"key_results": {"energy": -5.43}})
        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "fm", "write", str(path)],
            input=data, capture_output=True, text=True,
        )
        assert result.returncode == 0

        meta, _ = read_frontmatter(path)
        assert meta["key_results"]["energy"] == -5.43
        assert meta["key_results"]["bandgap"] == 1.0  # preserved via deep merge
