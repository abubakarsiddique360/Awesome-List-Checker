"""Command-line interface for Awesome-List-Checker."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from awesome_list_checker import __version__
from awesome_list_checker.parser import domains, parse_list
from awesome_list_checker.report import ListReport
from awesome_list_checker.rules import RULES, SEVERITY_ORDER, run_rules


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _check(args: argparse.Namespace) -> int:
    document = parse_list(_read(args.file))
    findings = run_rules(document)
    if args.min_severity:
        threshold = SEVERITY_ORDER[args.min_severity]
        findings = [finding for finding in findings if SEVERITY_ORDER[finding.severity] <= threshold]
    report = ListReport(document=document, findings=findings, path=args.file)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(report.render())
    return report.exit_code


def _stats(args: argparse.Namespace) -> int:
    document = parse_list(_read(args.file))
    print(f"title    : {document.title or '(none)'}")
    print(f"sections : {len(document.sections)}")
    print(f"entries  : {len(document.items)}")
    print("domains  :")
    for host, count in domains(document).items():
        print(f"  {count:>3}  {host}")
    return 0


def _rules(args: argparse.Namespace) -> int:
    for rule in RULES:
        print(f"{rule.severity:<8} {rule.id:<20} {rule.summary}")
    print(f"\n{len(RULES)} rule(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="awesome-list-checker",
        description="Check a curated markdown list for duplicates, insecure links and missing descriptions.",
    )
    parser.add_argument("--version", action="version", version=f"awesome-list-checker {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="check a markdown file")
    check.add_argument("file")
    check.add_argument("--json", action="store_true")
    check.add_argument("--min-severity", choices=("error", "warning", "info"))
    check.set_defaults(func=_check)

    stats = sub.add_parser("stats", help="count sections, entries and domains")
    stats.add_argument("file")
    stats.set_defaults(func=_stats)

    rules = sub.add_parser("rules", help="list the rules")
    rules.set_defaults(func=_rules)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except FileNotFoundError as exc:
        print(f"error: file not found: {exc.filename}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
