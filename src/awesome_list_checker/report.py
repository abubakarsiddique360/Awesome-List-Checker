"""Aggregate findings into a readable report."""

from __future__ import annotations

from dataclasses import dataclass, field

from awesome_list_checker.parser import Document, domains
from awesome_list_checker.rules import ERROR, INFO, WARNING, Finding

PENALTY = {ERROR: 20, WARNING: 4, INFO: 1}


@dataclass
class ListReport:
    document: Document
    findings: list[Finding] = field(default_factory=list)
    path: str = ""

    def by_severity(self) -> dict[str, list[Finding]]:
        grouped: dict[str, list[Finding]] = {ERROR: [], WARNING: [], INFO: []}
        for finding in self.findings:
            grouped.setdefault(finding.severity, []).append(finding)
        return grouped

    @property
    def score(self) -> int:
        return max(0, 100 - sum(PENALTY.get(finding.severity, 0) for finding in self.findings))

    @property
    def status(self) -> str:
        if self.by_severity()[ERROR]:
            return "fail"
        if self.by_severity()[WARNING]:
            return "warn"
        return "pass"

    @property
    def exit_code(self) -> int:
        return 1 if self.status == "fail" else 0

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "title": self.document.title,
            "sections": len(self.document.sections),
            "entries": len(self.document.items),
            "domains": domains(self.document),
            "status": self.status,
            "score": self.score,
            "counts": {severity: len(items) for severity, items in self.by_severity().items()},
            "findings": [finding.as_dict() for finding in self.findings],
        }

    def render(self) -> str:
        lines: list[str] = []
        for severity in (ERROR, WARNING, INFO):
            items = self.by_severity()[severity]
            if not items:
                continue
            lines.append(f"{severity.upper()} ({len(items)})")
            for finding in items:
                location = f"line {finding.line}" if finding.line else "document"
                lines.append(f"  {location:<10} {finding.rule:<20} {finding.message}")
            lines.append("")
        if not self.findings:
            lines.append("No findings. The list is tidy.")
            lines.append("")
        counts = self.by_severity()
        lines.append(
            f"{len(self.document.sections)} section(s) - {len(self.document.items)} entries - "
            f"{len(counts[ERROR])} error(s), {len(counts[WARNING])} warning(s), {len(counts[INFO])} note(s) - "
            f"score {self.score}/100 - {self.status.upper()}"
        )
        return "\n".join(lines)
