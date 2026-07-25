from __future__ import annotations

from leakscan.findings.model import (
    Confidence,
    Finding,
    ScanResult,
    Severity,
    dedupe,
    redact,
    sorted_findings,
)


def make(check_id="c", severity=Severity.HIGH, location="l", evidence="e") -> Finding:
    return Finding(
        check_id=check_id,
        severity=severity,
        confidence=Confidence.CERTAIN,
        title="t",
        detail="d",
        evidence=evidence,
        location=location,
    )


def test_redact_masks_the_middle():
    out = redact("sk_live_abcdefghijklmnopqrstuvwxyz")
    assert out.startswith("sk_live_")
    assert out.endswith("wxyz")
    assert "abcdefghijkl" not in out


def test_redact_fully_masks_short_values():
    assert redact("short") == "*****"


def test_score_starts_at_100_with_no_findings():
    result = ScanResult(url="https://app.test/")
    assert result.score() == 100
    assert result.grade() == "A"


def test_info_findings_do_not_reduce_score():
    result = ScanResult(url="u")
    result.add(make(severity=Severity.INFO))
    assert result.score() == 100


def test_critical_finding_drops_grade_to_f():
    result = ScanResult(url="u")
    result.add(make(severity=Severity.CRITICAL))
    result.add(make(check_id="c2", severity=Severity.CRITICAL))
    assert result.score() == 20
    assert result.grade() == "F"


def test_same_check_at_multiple_locations_penalized_once():
    """One leaked key found in three bundles is one problem, not three."""
    result = ScanResult(url="u")
    for path in ("/a.js", "/b.js", "/c.js"):
        result.add(make(check_id="secret.stripe.live_secret", severity=Severity.CRITICAL, location=path))
    assert result.score() == 60


def test_score_uses_worst_severity_per_check():
    result = ScanResult(url="u")
    result.add(make(check_id="x", severity=Severity.LOW, location="/a"))
    result.add(make(check_id="x", severity=Severity.CRITICAL, location="/b"))
    assert result.score() == 60


def test_score_floors_at_zero():
    result = ScanResult(url="u")
    for i in range(10):
        result.add(make(check_id=f"c{i}", severity=Severity.CRITICAL))
    assert result.score() == 0


def test_counts_by_severity():
    result = ScanResult(url="u")
    result.add(make(check_id="a", severity=Severity.CRITICAL))
    result.add(make(check_id="b", severity=Severity.LOW))
    result.add(make(check_id="c", severity=Severity.LOW))
    counts = result.counts()
    assert counts["critical"] == 1
    assert counts["low"] == 2
    assert counts["high"] == 0


def test_findings_sorted_most_severe_first():
    findings = [
        make(check_id="a", severity=Severity.LOW),
        make(check_id="b", severity=Severity.CRITICAL),
        make(check_id="c", severity=Severity.MEDIUM),
    ]
    assert [f.check_id for f in sorted_findings(findings)] == ["b", "c", "a"]


def test_dedupe_collapses_identical_findings():
    findings = [make(), make(), make(evidence="different")]
    assert len(dedupe(findings)) == 2


def test_dedupe_keeps_same_check_at_different_locations():
    findings = [make(location="/a.js"), make(location="/b.js")]
    assert len(dedupe(findings)) == 2


def test_serialization_round_trips_to_json_safe_dict():
    result = ScanResult(url="https://app.test/")
    result.add(make(severity=Severity.CRITICAL))
    payload = result.to_dict()
    assert payload["url"] == "https://app.test/"
    assert payload["score"] == 60
    assert payload["grade"] == "C"
    assert payload["findings"][0]["severity"] == "critical"
    assert isinstance(payload["counts"], dict)
