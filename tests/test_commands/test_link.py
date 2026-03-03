"""Tests for link command."""

import subprocess
import sys

import pytest

from psi_cli.frontmatter import read_frontmatter, write_frontmatter


def _setup_calc(tmp_path, cid, **extra):
    d = tmp_path / "calc_db" / cid
    d.mkdir(parents=True)
    meta = {"id": cid, "title": "test", "children": [], "reports": [], **extra}
    write_frontmatter(d / "README.md", meta, f"\n# {cid}\n")


class TestAddChild:
    def test_add(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_calc(tmp_path, "c001")
        _setup_calc(tmp_path, "c002")

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "link", "add-child", "c001", "c002"],
            capture_output=True, text=True, cwd=tmp_path,
        )
        assert result.returncode == 0

        meta, _ = read_frontmatter(tmp_path / "calc_db" / "c001" / "README.md")
        assert "c002" in meta["children"]

    def test_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_calc(tmp_path, "c001", children=["c002"])
        _setup_calc(tmp_path, "c002")

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "link", "add-child", "c001", "c002"],
            capture_output=True, text=True, cwd=tmp_path,
        )
        assert result.returncode == 0
        assert "already" in result.stdout

        meta, _ = read_frontmatter(tmp_path / "calc_db" / "c001" / "README.md")
        assert meta["children"].count("c002") == 1


class TestRemoveChild:
    def test_remove(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_calc(tmp_path, "c001", children=["c002"])

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "link", "remove-child", "c001", "c002"],
            capture_output=True, text=True, cwd=tmp_path,
        )
        assert result.returncode == 0

        meta, _ = read_frontmatter(tmp_path / "calc_db" / "c001" / "README.md")
        assert "c002" not in meta["children"]


class TestAddReport:
    def test_add(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_calc(tmp_path, "c001")

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "link", "add-report", "c001", "r001"],
            capture_output=True, text=True, cwd=tmp_path,
        )
        assert result.returncode == 0

        meta, _ = read_frontmatter(tmp_path / "calc_db" / "c001" / "README.md")
        assert "r001" in meta["reports"]


class TestRemoveReport:
    def test_remove(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_calc(tmp_path, "c001", reports=["r001"])

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "link", "remove-report", "c001", "r001"],
            capture_output=True, text=True, cwd=tmp_path,
        )
        assert result.returncode == 0

        meta, _ = read_frontmatter(tmp_path / "calc_db" / "c001" / "README.md")
        assert "r001" not in meta["reports"]
