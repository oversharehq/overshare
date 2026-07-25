"""SARIF output tests.

The shape matters more than usual here: GitHub silently drops a run it cannot
parse, so a malformed document looks exactly like a clean scan.
"""

from __future__ import annotations

import json

import pytest

from overshare.findings.model import Confidence, Finding, ScanResult, Severity
from overshare.report.sarif import to_sarif


def _finding(check_id="secret.stripe.live_secret", severity=Severity.CRITICAL, **kw) -> Finding:
    return Finding(
        check_id=check_id,
        severity=severity,
        confidence=Confidence.CERTAIN,
        title=kw.get("title", "Live Stripe secret key in bundle"),
        detail=kw.get("detail", "A live Stripe secret key is served to every visitor."),
        evidence=kw.get("evidence", "sk_live_************abcd"),
        location=kw.get("location", "https://app.example.com/main.js"),
        remediation=kw.get("remediation", "Roll the key and move it server-side."),
    )


def _result(*findings, url="https://app.example.com") -> ScanResult:
    return ScanResult(url=url, findings=list(findings), assets=[url])


def test_document_has_required_sarif_envelope():
    doc = to_sarif(_result(_finding()))

    assert doc["version"] == "2.1.0"
    assert doc["$schema"].endswith("sarif-2.1.0.json")
    assert len(doc["runs"]) == 1
    assert doc["runs"][0]["tool"]["driver"]["name"] == "Overshare"


def test_every_result_references_a_declared_rule():
    doc = to_sarif(_result(_finding(), _finding(check_id="transport.header.csp_missing")))
    run = doc["runs"][0]

    rule_ids = [r["id"] for r in run["tool"]["driver"]["rules"]]
    for result in run["results"]:
        assert result["ruleId"] in rule_ids
        # ruleIndex must point at the matching rule or GitHub mis-attributes it.
        assert run["tool"]["driver"]["rules"][result["ruleIndex"]]["id"] == result["ruleId"]


def test_repeated_check_declares_one_rule_but_many_results():
    doc = to_sarif(
        _result(
            _finding(location="https://app.example.com/a.js"),
            _finding(location="https://app.example.com/b.js"),
        )
    )
    run = doc["runs"][0]

    assert len(run["tool"]["driver"]["rules"]) == 1
    assert len(run["results"]) == 2


def test_severity_maps_to_level_and_security_severity():
    doc = to_sarif(
        _result(
            _finding(severity=Severity.CRITICAL),
            _finding(check_id="transport.header.csp_missing", severity=Severity.MEDIUM),
            _finding(check_id="footprint.mail.dmarc_missing", severity=Severity.LOW),
        )
    )
    run = doc["runs"][0]
    by_id = {r["id"]: r for r in run["tool"]["driver"]["rules"]}

    assert by_id["secret.stripe.live_secret"]["properties"]["security-severity"] == "9.5"
    assert by_id["transport.header.csp_missing"]["properties"]["security-severity"] == "5.0"

    levels = {r["ruleId"]: r["level"] for r in run["results"]}
    assert levels["secret.stripe.live_secret"] == "error"
    assert levels["transport.header.csp_missing"] == "warning"
    assert levels["footprint.mail.dmarc_missing"] == "note"


def test_info_findings_are_excluded_unless_requested():
    result = _result(_finding(check_id="platform.fingerprint", severity=Severity.INFO))

    assert to_sarif(result)["runs"][0]["results"] == []
    assert len(to_sarif(result, show_info=True)["runs"][0]["results"]) == 1


def test_clean_scan_produces_a_valid_empty_run():
    doc = to_sarif(_result())
    run = doc["runs"][0]

    assert run["results"] == []
    assert run["tool"]["driver"]["rules"] == []
    assert run["invocations"][0]["executionSuccessful"] is True


def test_unreachable_target_is_reported_as_unsuccessful_execution():
    # No assets means the target was never reached. Reporting that as a
    # successful run with zero findings would be a fabricated clean result.
    result = ScanResult(url="https://app.example.com", errors=["connect timeout"])

    invocation = to_sarif(result)["runs"][0]["invocations"][0]

    assert invocation["executionSuccessful"] is False
    assert invocation["toolExecutionNotifications"][0]["message"]["text"] == "connect timeout"


def test_findings_locate_against_their_asset_url():
    doc = to_sarif(_result(_finding(location="https://app.example.com/main.js")))
    location = doc["runs"][0]["results"][0]["locations"][0]

    assert location["physicalLocation"]["artifactLocation"]["uri"] == (
        "https://app.example.com/main.js"
    )


def test_finding_without_location_falls_back_to_scanned_url():
    doc = to_sarif(_result(_finding(check_id="transport.tls.weak", location=None)))
    location = doc["runs"][0]["results"][0]["locations"][0]

    assert location["physicalLocation"]["artifactLocation"]["uri"] == "https://app.example.com"


def test_fingerprints_are_stable_across_runs():
    first = to_sarif(_result(_finding()))["runs"][0]["results"][0]
    second = to_sarif(_result(_finding()))["runs"][0]["results"][0]

    assert first["partialFingerprints"] == second["partialFingerprints"]


def test_runs_are_scoped_per_host():
    one = to_sarif(_result(_finding(), url="https://one.example.com"))
    two = to_sarif(_result(_finding(), url="https://two.example.com"))

    assert one["runs"][0]["automationDetails"]["id"] != (
        two["runs"][0]["automationDetails"]["id"]
    )


def test_evidence_is_carried_but_stays_redacted():
    doc = to_sarif(_result(_finding(evidence="sk_live_************abcd")))
    message = doc["runs"][0]["results"][0]["message"]["text"]

    assert "sk_live_************abcd" in message


def test_sarif_file_is_written_alongside_the_human_report(tmp_path, monkeypatch, capsys):
    # CI needs both from a single scan: the readable report in the job log and
    # a SARIF file to upload. Requiring two runs would double-hit the target.
    from overshare import cli

    monkeypatch.setattr(cli, "scan", lambda url, **kw: _result(_finding(), url=url))
    sarif_path = tmp_path / "out.sarif"

    exit_code = cli.main(["https://app.example.com", "--sarif-file", str(sarif_path)])

    assert exit_code == cli.EXIT_FINDINGS
    assert "Live Stripe secret key" in capsys.readouterr().out
    assert json.loads(sarif_path.read_text())["version"] == "2.1.0"


@pytest.mark.parametrize("extra", [[], ["--json"]])
def test_sarif_file_is_independent_of_stdout_format(tmp_path, monkeypatch, extra):
    from overshare import cli

    monkeypatch.setattr(cli, "scan", lambda url, **kw: _result(_finding(), url=url))
    sarif_path = tmp_path / "out.sarif"

    cli.main(["https://app.example.com", "--sarif-file", str(sarif_path), *extra])

    assert json.loads(sarif_path.read_text())["runs"][0]["results"]
