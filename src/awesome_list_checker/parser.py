"""Parse a curated markdown list into sections and items."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
ITEM_RE = re.compile(r"^\s{0,3}[-*+]\s+(.*)$")
LINK_RE = re.compile(r"\[([^\]]*)\]\(\s*([^)\s]+)\s*\)?")
BARE_URL_RE = re.compile(r"https?://[^\s)>\]]+")

# items after an H3 belong to that heading but are still reported under the H2 section
SUBSECTION_RE = re.compile(r"^#{3,6}\s+(.*)$")


@dataclass(frozen=True)
class Item:
    text: str
    url: str
    line: int
    description: str = ""

    @property
    def raw(self) -> str:
        return f"{self.text} {self.description}".strip()

    def as_dict(self) -> dict:
        return {"text": self.text, "url": self.url, "line": self.line, "description": self.description}


@dataclass
class Section:
    title: str
    line: int
    items: list[Item] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return self.title.strip().lower()


@dataclass
class Document:
    title: str = ""
    sections: list[Section] = field(default_factory=list)

    @property
    def items(self) -> list[Item]:
        return [item for section in self.sections for item in section.items]

    @property
    def urls(self) -> list[str]:
        return [item.url for item in self.items]


def parse_list(markdown: str) -> Document:
    document = Document()
    current: Section | None = None
    in_code_block = False

    for line_number, raw_line in enumerate(markdown.splitlines(), start=1):
        line = raw_line.rstrip()
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2).strip()
            if level == 1 and not document.title:
                document.title = text
                current = None
            elif level == 2:
                current = Section(title=text, line=line_number)
                document.sections.append(current)
            # deeper headings only organise items inside the current section
            continue

        item_match = ITEM_RE.match(line)
        if not item_match:
            continue

        content = item_match.group(1).strip()
        link = LINK_RE.search(content)
        if link:
            text = link.group(1).strip()
            url = link.group(2).strip()
            description = (content[: link.start()] + content[link.end() :]).strip(" —-–:·|")
        else:
            bare = BARE_URL_RE.search(content)
            if not bare:
                continue
            text = bare.group(0)
            url = text
            description = ""

        if current is None:
            current = Section(title="Uncategorised", line=line_number)
            document.sections.append(current)
        current.items.append(Item(text=text, url=url, line=line_number, description=" ".join(description.split())))

    return document


def domains(document: Document) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in document.items:
        host = re.sub(r"^https?://", "", item.url).split("/")[0].lower()
        counts[host] = counts.get(host, 0) + 1
    return dict(sorted(counts.items(), key=lambda pair: pair[1], reverse=True))
