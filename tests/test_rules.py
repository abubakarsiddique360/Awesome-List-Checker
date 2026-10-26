from __future__ import annotations

from pathlib import Path

from awesome_list_checker.parser import parse_list
from awesome_list_checker.report import ListReport
from awesome_list_checker.rules import RULES, run_rules

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def rule_ids(markdown: str) -> set[str]:
    return {finding.rule for finding in run_rules(parse_list(markdown))}


def test_good_example_has_no_errors() -> None:
    document = parse_list((EXAMPLES / "good-list.md").read_text(encoding="utf-8"))
    findings = run_rules(document)
    assert [finding for finding in findings if finding.severity == "error"] == []


def test_bad_example_triggers_expected_rules() -> None:
    document = parse_list((EXAMPLES / "bad-list.md").read_text(encoding="utf-8"))
    ids = {finding.rule for finding in run_rules(document)}
    assert {"insecure-link", "duplicate-url", "missing-description", "empty-section"} <= ids
    assert {"bare-url", "long-link-text", "repeated-section", "unsorted-section"} <= ids


def test_missing_title_is_an_error() -> None:
    assert "no-title" in rule_ids("## Section\n- [A](https://a.test) — a.\n")


def test_duplicate_url_detects_trailing_slash_variants() -> None:
    text = "- [A](https://a.test) — a.\n- [A again](https://a.test/) — b.\n"
    assert "duplicate-url" in rule_ids(text)


def test_http_link_is_an_error() -> None:
    assert "insecure-link" in rule_ids("# T\n- [A](http://a.test) — a.\n")


def test_descriptions_avoid_false_positives() -> None:
    assert "missing-description" not in rule_ids("# T\n- [A](https://a.test) — has a description.\n")


def test_sorted_section_is_not_flagged() -> None:
    text = "# T\n## S\n- [Alpha](https://a.test) — a.\n- [Beta](https://b.test) — b.\n"
    assert "unsorted-section" not in rule_ids(text)


def test_rules_are_documented() -> None:
    assert len(RULES) >= 8
    assert all(rule.id and rule.summary and rule.severity for rule in RULES)


def test_report_scores_and_exit_codes() -> None:
    bad = parse_list((EXAMPLES / "bad-list.md").read_text(encoding="utf-8"))
    report = ListReport(document=bad, findings=run_rules(bad), path="bad")
    assert report.status == "fail"
    assert report.exit_code == 1
    assert report.score < 100
    assert "ERROR" in report.render()

    good = parse_list((EXAMPLES / "good-list.md").read_text(encoding="utf-8"))
    clean = ListReport(document=good, findings=[], path="good")
    assert clean.status == "pass"
    assert clean.exit_code == 0


def test_report_json_shape() -> None:
    document = parse_list((EXAMPLES / "good-list.md").read_text(encoding="utf-8"))
    payload = ListReport(document=document, findings=run_rules(document)).as_dict()
    assert payload["entries"] == 9
    assert payload["sections"] == 3
    assert payload["domains"]
