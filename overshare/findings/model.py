from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}

SEVERITY_PENALTY = {
    Severity.CRITICAL: 40,
    Severity.HIGH: 20,
    Severity.MEDIUM: 8,
    Severity.LOW: 3,
    Severity.INFO: 0,
}


class Confidence(str, Enum):
    CERTAIN = "certain"
    PROBABLE = "probable"


def redact(secret: str, keep_prefix: int = 8, keep_suffix: int = 4) -> str:
    """Never let a full credential reach a report, a log, or the database."""
    if len(secret) <= keep_prefix + keep_suffix:
        return "*" * len(secret)
    hidden = len(secret) - keep_prefix - keep_suffix
    return f"{secret[:keep_prefix]}{'*' * min(hidden, 12)}{secret[-keep_suffix:]}"


@dataclass
class Finding:
    check_id: str
    severity: Severity
    confidence: Confidence
    title: str
    detail: str
    evidence: str = ""
    location: str | None = None
    remediation: str | None = None

    def key(self) -> tuple[str, str | None, str]:
        return (self.check_id, self.location, self.evidence)

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "title": self.title,
            "detail": self.detail,
            "evidence": self.evidence,
            "location": self.location,
            "remediation": self.remediation,
        }


@dataclass
class ScanResult:
    url: str
    findings: list[Finding] = field(default_factory=list)
    platform: dict = field(default_factory=dict)
    assets: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in Severity}
        for f in self.findings:
            out[f.severity.value] += 1
        return out

    def score(self) -> int:
        # Score once per check, not once per occurrence: one leaked key found in
        # three bundles is one problem to fix, not three.
        worst: dict[str, Severity] = {}
        for f in self.findings:
            current = worst.get(f.check_id)
            if current is None or SEVERITY_ORDER[f.severity] < SEVERITY_ORDER[current]:
                worst[f.check_id] = f.severity
        penalty = sum(SEVERITY_PENALTY[s] for s in worst.values())
        return max(0, 100 - penalty)

    def grade(self) -> str:
        s = self.score()
        if s >= 90:
            return "A"
        if s >= 75:
            return "B"
        if s >= 60:
            return "C"
        if s >= 40:
            return "D"
        return "F"

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "score": self.score(),
            "grade": self.grade(),
            "counts": self.counts(),
            "platform": self.platform,
            "findings": [f.to_dict() for f in sorted_findings(self.findings)],
            "assets_scanned": self.assets,
            "errors": self.errors,
            "duration_seconds": round(self.duration_seconds, 2),
        }


def sorted_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.check_id))


def dedupe(findings: list[Finding]) -> list[Finding]:
    seen: set = set()
    out: list[Finding] = []
    for f in findings:
        if f.key() in seen:
            continue
        seen.add(f.key())
        out.append(f)
    return out
