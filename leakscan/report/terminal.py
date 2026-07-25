from __future__ import annotations

import os
import shutil
import sys
import textwrap

from ..findings.model import ScanResult, Severity, sorted_findings

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

SEVERITY_COLOR = {
    Severity.CRITICAL: "\033[97;41m",
    Severity.HIGH: "\033[31m",
    Severity.MEDIUM: "\033[33m",
    Severity.LOW: "\033[36m",
    Severity.INFO: "\033[90m",
}

GRADE_COLOR = {"A": "\033[32m", "B": "\033[32m", "C": "\033[33m", "D": "\033[31m", "F": "\033[31m"}


def _color_enabled(stream) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(stream, "isatty") and stream.isatty()


def render(result: ScanResult, stream=None, show_info: bool = False) -> None:
    stream = stream or sys.stdout
    use_color = _color_enabled(stream)
    width = min(shutil.get_terminal_size((100, 24)).columns, 100)

    def c(text: str, code: str) -> str:
        return f"{code}{text}{RESET}" if use_color else text

    def line(char: str = "-") -> None:
        print(char * width, file=stream)

    counts = result.counts()
    score = result.score()
    grade = result.grade()

    line("=")
    print(c(f" LeakScan report: {result.url}", BOLD), file=stream)
    line("=")

    print(
        f" Score: {c(str(score) + '/100', BOLD)}   "
        f"Grade: {c(grade, GRADE_COLOR.get(grade, ''))}   "
        f"Scanned {len(result.assets)} asset(s) in {result.duration_seconds:.1f}s",
        file=stream,
    )

    summary = "  ".join(
        c(f"{counts[s.value]} {s.value}", SEVERITY_COLOR[s])
        for s in Severity
        if counts[s.value]
    )
    print(f" Findings: {summary or 'none'}", file=stream)

    if result.platform:
        detected = ", ".join(f"{k}={v}" for k, v in result.platform.items())
        print(f" Platform: {c(detected, DIM)}", file=stream)
    print(file=stream)

    visible = [
        f
        for f in sorted_findings(result.findings)
        if show_info or f.severity is not Severity.INFO
    ]

    if not visible:
        print(" No actionable findings. Run with --show-info for context checks.\n", file=stream)
    else:
        for finding in visible:
            badge = c(f" {finding.severity.value.upper()} ", SEVERITY_COLOR[finding.severity])
            print(f"{badge} {c(finding.title, BOLD)}", file=stream)
            if finding.location:
                print(f"   {c('where:', DIM)} {finding.location}", file=stream)
            if finding.evidence:
                print(f"   {c('evidence:', DIM)} {finding.evidence}", file=stream)
            for para in finding.detail.split("\n"):
                for wrapped in textwrap.wrap(para, width - 6) or [""]:
                    print(f"   {wrapped}", file=stream)
            if finding.remediation:
                print(f"   {c('fix:', DIM)}", file=stream)
                for wrapped in textwrap.wrap(finding.remediation, width - 8):
                    print(f"     {wrapped}", file=stream)
            print(file=stream)

    if result.errors:
        line()
        print(c(" Errors during scan:", BOLD), file=stream)
        for err in result.errors:
            print(f"   - {err}", file=stream)
        print(file=stream)

    hidden = len(result.findings) - len(visible)
    if hidden and not show_info:
        print(c(f" {hidden} informational finding(s) hidden. Use --show-info.", DIM), file=stream)

    line("=")
