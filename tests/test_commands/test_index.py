"""Tests for index command."""

import json
import subprocess
import sys

import pytest

from psi_cli.frontmatter import write_frontmatter
from psi_cli.markdown_table import read_index, write_index


class TestNextId:
    def test_from_index(self, tmp_path):
        calc_db = tmp_path / "calc_db"
        calc_db.mkdir()
        write_index(
            calc_db / "index.md",
            "# Calculation Index\n\n",
            ["id", "title"],
            [["c001", "test"], ["c003", "test2"]],
        )

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "index", "next-id", str(calc_db)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "c004"

    def test_from_dirs_fallback(self, tmp_path):
        calc_db = tmp_path / "calc_db"
        calc_db.mkdir()
        (calc_db / "index.md").write_text("# Calculation Index\n\n| id | title |\n| -- | ----- |\n")
        (calc_db / "c001").mkdir()
        (calc_db / "c002").mkdir()

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "index", "next-id", str(calc_db)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "c003"

    def test_empty_start(self, tmp_path):
        calc_db = tmp_path / "calc_db"
        calc_db.mkdir()

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "index", "next-id", str(calc_db)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "c001"

    def test_reports_prefix(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "index", "next-id", str(reports)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "r001"


class TestAppend:
    def test_append(self, tmp_path):
        calc_db = tmp_path / "calc_db"
        calc_db.mkdir()
        write_index(
            calc_db / "index.md",
            "# Calculation Index\n\n",
            ["id", "title", "status"],
            [["c001", "test", "planned"]],
        )

        data = json.dumps({"id": "c002", "title": "test2", "status": "planned"})
        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "index", "append", str(calc_db / "index.md"), data],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

        _, _, rows = read_index(calc_db / "index.md")
        assert len(rows) == 2
        assert rows[1][0] == "c002"


class TestUpdate:
    def test_update(self, tmp_path):
        calc_db = tmp_path / "calc_db"
        calc_db.mkdir()
        write_index(
            calc_db / "index.md",
            "# Calculation Index\n\n",
            ["id", "title", "status"],
            [["c001", "test", "planned"]],
        )

        data = json.dumps({"status": "completed"})
        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "index", "update", str(calc_db / "index.md"), "c001", data],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

        _, _, rows = read_index(calc_db / "index.md")
        assert rows[0][2] == "completed"


class TestRebuild:
    def test_rebuild(self, tmp_path):
        calc_db = tmp_path / "calc_db"
        calc_db.mkdir()

        for cid, title in [("c001", "first"), ("c002", "second")]:
            d = calc_db / cid
            d.mkdir()
            write_frontmatter(
                d / "README.md",
                {"id": cid, "title": title, "date": "2024-01-01", "status": "planned",
                 "code": "VASP", "computer": "local", "parents": [], "tags": ["test"]},
                f"\n# {cid}: {title}\n",
            )

        result = subprocess.run(
            [sys.executable, "-m", "psi_cli", "index", "rebuild", str(calc_db)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "2 entries" in result.stdout

        _, headers, rows = read_index(calc_db / "index.md")
        assert len(rows) == 2
        assert rows[0][0] == "c001"
        assert rows[1][0] == "c002"
