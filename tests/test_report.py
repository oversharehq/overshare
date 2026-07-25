"""Terminal report tests.

The limitations footer is the part that matters here. Detection is
precision-first, so the errors this tool makes are misses — a report that lists
findings and stops implies the rest is fine, which is the reading a clean result
most invites and least deserves.
"""

from __future__ import annotations

import io

from overshare.findings.model import Confidence, Finding, ScanResult, Severity
from overshare.report.terminal import LIMITATIONS, render


def _render(result: ScanResult, **kw) -> str:
    stream = io.StringIO()
    render(result, stream=stream, **kw)
    return stream.getvalue()


def test_clean_scan_still_states_what_was_not_checked():
    output = _render(ScanResult(url="https://app.example.com", assets=["x"]))

    assert "No actionable findings" in output
    assert "This scan did not check:" in output
    assert "does not mean the app is secure" in output


def test_report_with_findings_also_states_limitations():
    result = ScanResult(
        url="https://app.example.com",
        assets=["x"],
        findings=[
            Finding(
                check_id="secret.stripe.live_secret",
                severity=Severity.CRITICAL,
                confidence=Confidence.CERTAIN,
                title="Live Stripe key",
                detail="A live key ships to every visitor.",
            )
        ],
    )

    assert "This scan did not check:" in _render(result)


def test_every_limitation_is_rendered():
    output = _render(ScanResult(url="https://app.example.com", assets=["x"]))

    for limitation in LIMITATIONS:
        # Wrapped across lines, so match on the opening clause rather than the
        # whole sentence.
        assert limitation.split(" — ")[0].split(",")[0][:40] in output


def test_authenticated_surface_and_rls_are_named_explicitly():
    # The two blind spots most likely to be read as "checked and clean".
    output = _render(ScanResult(url="https://app.example.com", assets=["x"]))

    assert "behind a login" in output
    assert "Row Level Security" in output
