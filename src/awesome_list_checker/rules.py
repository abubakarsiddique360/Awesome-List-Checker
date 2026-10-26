"""The hygiene rules for a curated list."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from awesome_list_checker.parser import Document, Section

ERROR = "error"
WARNING = "warning"
INFO = "info"
SEVERITY_ORDER = {ERROR: 0, WARNING: 1, INFO: 2}


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    message: str
    line: int = 0

    def as_dict(self) -> dict:
        return {"rule": self.rule, "severity": self.severity, "message": self.message, "line": self.line}


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    summary: str
    check: Callable[[Document], list[Finding]]


def _no_title(document: Document) -> list[Finding]:
    if document.title.strip():
        return []
    return [Finding("no-title", ERROR, "the list has no H1 title", 1)]


def _duplicate_urls(document: Document) -> list[Finding]:
    counts = Counter(item.url.rstrip("/").lower() for item in document.items)
    findings = []
    for item in document.items:
        key = item.url.rstrip("/").lower()
        if counts[key] > 1:
            findings.append(
                Finding("duplicate-url", ERROR, f"link listed {counts[key]} times: {item.url}", item.line)
            )
    return findings


def _duplicate_titles(document: Document) -> list[Finding]:
    counts = Counter(item.text.strip().casefold() for item in document.items)
    return [
        Finding(
            "duplicate-title",
            WARNING,
            f"name listed {counts[item.text.strip().casefold()]} times: {item.text}",
            item.line,
        )
        for item in document.items
        if counts[item.text.strip().casefold()] > 1
    ]


def _insecure_links(document: Document) -> list[Finding]:
    return [
        Finding("insecure-link", ERROR, f"plain http link: {item.url}", item.line)
        for item in document.items
        if item.url.lower().startswith("http://")
    ]


def _missing_description(document: Document) -> list[Finding]:
    return [
        Finding("missing-description", WARNING, f"no description for: {item.text}", item.line)
        for item in document.items
        if not item.description
    ]


def _long_link_text(document: Document) -> list[Finding]:
    return [
        Finding("long-link-text", INFO, f"link text is {len(item.text)} characters: {item.text[:60]}", item.line)
        for item in document.items
        if len(item.text) > 60
    ]


def _bare_url(document: Document) -> list[Finding]:
    return [
        Finding("bare-url", INFO, "item uses a raw URL as its title", item.line)
        for item in document.items
        if item.text == item.url
    ]


def _empty_sections(document: Document) -> list[Finding]:
    return [
        Finding("empty-section", WARNING, f"section has no entries: {section.title}", section.line)
        for section in document.sections
        if not section.items
    ]


def _unsorted_sections(document: Document) -> list[Finding]:
    findings = []
    for section in document.sections:
        names = [item.text.casefold() for item in section.items]
        if len(names) > 1 and names != sorted(names):
            findings.append(
                Finding("unsorted-section", INFO, f"entries are not alphabetical: {section.title}", section.line)
            )
    return findings


def _repeated_section(document: Document) -> list[Finding]:
    counts = Counter(section.slug for section in document.sections)
    return [
        Finding(
            "repeated-section",
            WARNING,
            f"section appears {counts[section.slug]} times: {section.title}",
            section.line,
        )
        for section in document.sections
        if section.slug and counts[section.slug] > 1
    ]


RULES: tuple[Rule, ...] = (
    Rule("no-title", ERROR, "missing H1 title", _no_title),
    Rule("duplicate-url", ERROR, "the same link appears twice", _duplicate_urls),
    Rule("insecure-link", ERROR, "link uses http://", _insecure_links),
    Rule("duplicate-title", WARNING, "the same name appears twice", _duplicate_titles),
    Rule("missing-description", WARNING, "entry has no description", _missing_description),
    Rule("empty-section", WARNING, "section has no entries", _empty_sections),
    Rule("repeated-section", WARNING, "section title repeated", _repeated_section),
    Rule("long-link-text", INFO, "entry name is very long", _long_link_text),
    Rule("bare-url", INFO, "raw URL used as the name", _bare_url),
    Rule("unsorted-section", INFO, "entries are not alphabetical", _unsorted_sections),
)


def run_rules(document: Document) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule.check(document))
    findings.sort(key=lambda finding: (SEVERITY_ORDER[finding.severity], finding.line, finding.rule))
    return findings


def item_count(document: Document) -> int:
    return len(document.items)


def section_of(document: Document, url: str) -> Section | None:
    for section in document.sections:
        if any(item.url == url for item in section.items):
            return section
    return None
