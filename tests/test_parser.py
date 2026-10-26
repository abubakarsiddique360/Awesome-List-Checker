from __future__ import annotations

from pathlib import Path

from awesome_list_checker.parser import domains, parse_list

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

DOC = """# List

Intro text that is not an entry.

## Tools

- [Alpha](https://alpha.test) - first tool.
- [Beta](https://beta.test) - second tool.
- no link here
- https://bare.test

## Empty

## Tools

- [Gamma](https://gamma.test)
"""


def test_parse_title_sections_and_items() -> None:
    document = parse_list(DOC)
    assert document.title == "List"
    assert [section.title for section in document.sections] == ["Tools", "Empty", "Tools"]
    assert len(document.items) == 4


def test_link_text_and_description_are_split() -> None:
    item = parse_list(DOC).items[0]
    assert item.text == "Alpha"
    assert item.url == "https://alpha.test"
    assert item.description == "first tool."


def test_em_dash_separator_is_removed() -> None:
    item = parse_list("# T\n- [Alpha](https://alpha.test) \u2014 dash separated.\n").items[0]
    assert item.description == "dash separated."


def test_bare_url_items_are_kept() -> None:
    item = parse_list(DOC).items[2]
    assert item.text == "https://bare.test"
    assert item.description == ""


def test_entries_without_links_are_ignored() -> None:
    assert all(item.url.startswith("https://") for item in parse_list(DOC).items)


def test_code_blocks_are_ignored() -> None:
    markdown = "## Code\n\n```\n- [Hidden](https://hidden.test)\n```\n"
    assert parse_list(markdown).items == []


def test_items_before_a_section_are_uncategorised() -> None:
    document = parse_list("- [Early](https://early.test)\n## Later\n- [Late](https://late.test)\n")
    assert document.sections[0].title == "Uncategorised"


def test_good_example_parses() -> None:
    document = parse_list((EXAMPLES / "good-list.md").read_text(encoding="utf-8"))
    assert document.title == "Machine learning reading list"
    assert len(document.sections) == 3
    assert len(document.items) == 9


def test_domains_are_ranked() -> None:
    document = parse_list((EXAMPLES / "good-list.md").read_text(encoding="utf-8"))
    ranked = domains(document)
    assert sum(ranked.values()) == len(document.items)
    assert list(ranked.values()) == sorted(ranked.values(), reverse=True)
