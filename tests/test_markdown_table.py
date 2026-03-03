"""Tests for markdown_table module."""

from psi_cli.markdown_table import parse_table, read_index, render_table, write_index


SAMPLE_TABLE = """\
| id   | title         | date       | status    |
| ---- | ------------- | ---------- | --------- |
| c001 | Si relax      | 2024-01-01 | completed |
| c002 | Si SCF        | 2024-01-02 | planned   |
"""


class TestParseTable:
    def test_basic(self):
        headers, rows = parse_table(SAMPLE_TABLE)
        assert headers == ["id", "title", "date", "status"]
        assert len(rows) == 2
        assert rows[0][0] == "c001"
        assert rows[1][1] == "Si SCF"

    def test_empty(self):
        headers, rows = parse_table("")
        assert headers == []
        assert rows == []

    def test_no_data_rows(self):
        text = "| id | title |\n| -- | ----- |\n"
        headers, rows = parse_table(text)
        assert headers == ["id", "title"]
        assert rows == []


class TestRenderTable:
    def test_round_trip(self):
        headers, rows = parse_table(SAMPLE_TABLE)
        rendered = render_table(headers, rows)
        headers2, rows2 = parse_table(rendered)
        assert headers2 == headers
        assert [r[0] for r in rows2] == [r[0] for r in rows]

    def test_empty_headers(self):
        assert render_table([], []) == ""

    def test_column_alignment(self):
        headers = ["id", "title"]
        rows = [["c001", "A very long title"]]
        rendered = render_table(headers, rows)
        lines = rendered.strip().split("\n")
        # All lines should have the same length
        assert len(set(len(l) for l in lines)) == 1


class TestIndexIO:
    def test_read_write(self, tmp_path):
        path = tmp_path / "index.md"
        preamble = "# Test Index\n\n"
        headers = ["id", "title", "status"]
        rows = [["c001", "test", "planned"]]
        write_index(path, preamble, headers, rows)

        preamble2, headers2, rows2 = read_index(path)
        assert "# Test Index" in preamble2
        assert headers2 == headers
        assert rows2[0][0] == "c001"

    def test_nonexistent_file(self, tmp_path):
        preamble, headers, rows = read_index(tmp_path / "nope.md")
        assert preamble == ""
        assert headers == []
        assert rows == []

    def test_file_without_table(self, tmp_path):
        path = tmp_path / "no_table.md"
        path.write_text("# Just a heading\n\nSome text.\n")
        preamble, headers, rows = read_index(path)
        assert "# Just a heading" in preamble
        assert headers == []
