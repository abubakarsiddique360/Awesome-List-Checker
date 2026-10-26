from __future__ import annotations

import json
from pathlib import Path

from awesome_list_checker.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_check_good_list(capsys) -> None:
    assert main(["check", str(EXAMPLES / "good-list.md")]) == 0
    out = capsys.readouterr().out
    assert "section(s)" in out
    assert "PASS" in out


def test_check_bad_list(capsys) -> None:
    assert main(["check", str(EXAMPLES / "bad-list.md")]) == 1
    out = capsys.readouterr().out
    assert "duplicate-url" in out
    assert "insecure-link" in out


def test_check_json(capsys) -> None:
    assert main(["check", str(EXAMPLES / "bad-list.md"), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "fail"
    assert payload["findings"]


def test_min_severity_filters(capsys) -> None:
    assert main(["check", str(EXAMPLES / "bad-list.md"), "--min-severity", "error", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert {finding["severity"] for finding in payload["findings"]} == {"error"}


def test_stats(capsys) -> None:
    assert main(["stats", str(EXAMPLES / "good-list.md")]) == 0
    out = capsys.readouterr().out
    assert "entries  : 9" in out
    assert "domains  :" in out


def test_rules_listing(capsys) -> None:
    assert main(["rules"]) == 0
    assert "duplicate-url" in capsys.readouterr().out


def test_missing_file(tmp_path, capsys) -> None:
    assert main(["check", str(tmp_path / "nope.md")]) == 2
    assert "error" in capsys.readouterr().err
