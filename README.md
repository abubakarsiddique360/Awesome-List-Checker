# Awesome-List-Checker

[![CI](https://github.com/abubakarsiddique360/Awesome-List-Checker/actions/workflows/ci.yml/badge.svg)](https://github.com/abubakarsiddique360/Awesome-List-Checker/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.10%20%7C%203.12-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![dependencies](https://img.shields.io/badge/dependencies-none-success)

A dependency-free command line checker for curated markdown link lists ("awesome lists").
It parses the document, applies ten opinionated quality rules, prints a readable report and
returns an exit code you can drop straight into CI.

Curated lists rot quietly: the same project gets added twice, a link flips to plain HTTP,
an entry loses its one-line description, a section ends up empty, and new entries stop being
alphabetical. Reviewers only notice months later. This tool catches those problems on every
pull request in a fraction of a second.

## Why it exists

Most link checkers only verify that URLs respond. That is a network problem. The problems that
make a curated list painful to read are **document** problems: structure, duplication, ordering
and writing quality. `awesome-list-checker` is offline, deterministic and CI friendly, so it can
run on every commit without flaky network calls.

## Install

```bash
pip install -e .
```

Python 3.10+ is required and there are no runtime dependencies.

## Usage

```bash
# check a list, print the report and set the exit code
awesome-list-checker check README.md

# machine readable output for CI jobs and dashboards
awesome-list-checker check README.md --json

# only fail the build on errors, ignore warnings and notes
awesome-list-checker check README.md --min-severity error

# show document statistics: sections, entries, domains
awesome-list-checker stats README.md

# list every rule with its severity and rationale
awesome-list-checker rules
```

`check` returns `0` when the list passes, `1` when findings at or above
`--min-severity` are present, and `2` when the file cannot be read.

Example output:

```text
ERROR (2)
  line 7     duplicate-url        link listed 2 times: https://cs229.stanford.edu
  line 9     insecure-link        plain http link: http://course.fast.ai

WARNING (3)
  line 10    missing-description  no description for: https://example.com/no-title
  line 13    repeated-section     section appears 2 times: Books
  line 21    empty-section        section has no entries: Empty section

4 section(s) - 7 entries - 2 error(s), 3 warning(s), 0 note(s) - score 51/100 - FAIL
```

## Rules

| Rule | Severity | What it catches |
| --- | --- | --- |
| `no-title` | error | The document has no `#` title, so it has no identity when linked. |
| `duplicate-url` | error | The same link appears more than once (trailing slashes are ignored). |
| `insecure-link` | error | A link uses plain `http://` instead of `https://`. |
| `duplicate-title` | warning | Two entries share the same display name. |
| `missing-description` | warning | An entry has no short description after the link. |
| `empty-section` | warning | A `##` heading contains no entries. |
| `repeated-section` | warning | The same heading text appears twice. |
| `long-link-text` | warning | Link text longer than 70 characters, which reads badly. |
| `bare-url` | info | The entry uses a raw URL instead of `[name](url)`. |
| `unsorted-section` | info | Entries inside a section are not alphabetical. |

The score starts at 100 and subtracts 20 per error, 4 per warning and 1 per note. It is a rough
signal for reviewers, not a grade: a list can be genuinely good and still score 92.

## Report and JSON shape

`--json` emits a stable object so the checker can power a badge or a dashboard:

```json
{
  "path": "README.md",
  "title": "Machine learning reading list",
  "sections": 3,
  "entries": 9,
  "domains": { "scikit-learn.org": 1, "wandb.ai": 1 },
  "score": 51,
  "status": "fail",
  "findings": [
    { "rule": "insecure-link", "severity": "error", "line": 8, "message": "plain http link: http://..." }
  ]
}
```

## Design notes

- **Parsing is line oriented.** Headings, list items, links and fenced code blocks are handled
  with four compiled regular expressions. Anything indented deeper than three spaces is still
  recognised as an item so nested lists are counted, not silently dropped.
- **Code fences are skipped**, so example markdown inside a triple backtick block never produces
  findings.
- **Rules are data.** Each rule is a small function registered in `RULES`, and every rule
  records the line number so an editor can jump straight to the problem.
- **Severity is ordered**, which is what makes `--min-severity` and the exit code trivial.
- **No network access, no third-party packages.** Results are reproducible on any machine.

## Project layout

```text
src/awesome_list_checker/
  parser.py   headings, sections, items, link and description splitting
  rules.py    the rule catalogue and run_rules()
  report.py   scoring, status, exit code, text and JSON rendering
  cli.py      check / stats / rules subcommands
examples/
  good-list.md  a list that passes with no errors
  bad-list.md   a list that deliberately breaks most rules
tests/          parser, rule and CLI tests
```

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

The CI workflow runs the suite on Python 3.10 and 3.12, checks formatting, and then runs the
product itself against both example lists.

## Limitations

- Only ATX headings (`#`, `##`, ...) are recognised; underline style headings are ignored.
- Link parsing is intentionally shallow: reference style links (`[text][ref]`) are not resolved.
- The alphabetical check is case-insensitive and purely lexical, so "The Zen of Python" sorts
  under `T`.
- The tool never fetches a URL, so dead links are out of scope by design.

## License

MIT, copyright (c) 2026 ABU BAKAR SIDDIQUE.
