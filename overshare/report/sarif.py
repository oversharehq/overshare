"""SARIF 2.1.0 output, so CI can ingest findings instead of parsing text.

GitHub code scanning is the delivery target: uploading this puts every finding in
the repository's Security tab with severity, description and remediation, and
tracks whether an alert is new, fixed or still open across runs.

One honest limitation. Overshare scans a *deployed URL*, not a working tree, so a
finding cannot be traced back to a source file and line. Results therefore locate
against the scanned URL, which means code scanning shows them as repository-level
alerts rather than inline annotations on a diff.
"""

from __future__ import annotations

import json
import sys
from urllib.parse import urlsplit

from .. import __version__
from ..findings.model import Finding, ScanResult, Severity, sorted_findings

SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
INFORMATION_URI = "https://oversharehq.com"

# SARIF has four levels; we have five severities. Critical and high both collapse
# onto "error" — the distinction survives in security-severity below.
SARIF_LEVEL = {
    Severity.CRITICAL: "error",
    Severity.HIGH: "error",
    Severity.MEDIUM: "warning",
    Severity.LOW: "note",
    Severity.INFO: "none",
}

# GitHub reads this numeric property, not `level`, to bucket an alert as
# Critical/High/Medium/Low. Without it every error lands in one undifferentiated
# pile and a leaked live Stripe key looks the same as a missing CSP.
SECURITY_SEVERITY = {
    Severity.CRITICAL: "9.5",
    Severity.HIGH: "7.5",
    Severity.MEDIUM: "5.0",
    Severity.LOW: "3.0",
    Severity.INFO: "0.0",
}


def _rule(finding: Finding) -> dict:
    help_text = finding.remediation or finding.detail
    return {
        "id": finding.check_id,
        "name": finding.check_id,
        "shortDescription": {"text": finding.title},
        "fullDescription": {"text": finding.detail},
        "help": {"text": help_text, "markdown": help_text},
        "defaultConfiguration": {"level": SARIF_LEVEL[finding.severity]},
        "properties": {
            "security-severity": SECURITY_SEVERITY[finding.severity],
            "tags": ["security", finding.check_id.split(".")[0]],
        },
    }


def _result(finding: Finding, rule_index: int, scanned_url: str) -> dict:
    message = finding.detail
    if finding.evidence:
        # Evidence is already redacted at construction time by findings.model.
        message = f"{message}\n\nEvidence: {finding.evidence}"

    return {
        "ruleId": finding.check_id,
        "ruleIndex": rule_index,
        "level": SARIF_LEVEL[finding.severity],
        "message": {"text": message},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": finding.location or scanned_url}
                }
            }
        ],
        # Keyed on the stable check_id so code scanning can tell "still open"
        # from "new" across runs instead of reopening every alert each scan.
        "partialFingerprints": {
            "oversharePrimary": f"{finding.check_id}:{finding.location or scanned_url}"
        },
    }


def to_sarif(result: ScanResult, show_info: bool = False) -> dict:
    findings = [
        f for f in sorted_findings(result.findings)
        if show_info or f.severity is not Severity.INFO
    ]

    rules: list[dict] = []
    rule_index: dict[str, int] = {}
    for finding in findings:
        if finding.check_id not in rule_index:
            rule_index[finding.check_id] = len(rules)
            rules.append(_rule(finding))

    host = urlsplit(result.url).hostname or "target"

    return {
        "$schema": SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Overshare",
                        "version": __version__,
                        "informationUri": INFORMATION_URI,
                        "rules": rules,
                    }
                },
                # Scoped per host so scanning several apps from one repo produces
                # independent alert sets rather than each run closing the last's.
                "automationDetails": {"id": f"overshare/{host}/"},
                "results": [
                    _result(f, rule_index[f.check_id], result.url) for f in findings
                ],
                "invocations": [
                    {
                        "executionSuccessful": bool(result.assets),
                        "toolExecutionNotifications": [
                            {"level": "warning", "message": {"text": error}}
                            for error in result.errors
                        ],
                    }
                ],
            }
        ],
    }


def render(result: ScanResult, stream=None, show_info: bool = False) -> None:
    stream = stream or sys.stdout
    json.dump(to_sarif(result, show_info=show_info), stream, indent=2)
    stream.write("\n")
