from __future__ import annotations

import json

import pytest

from overshare.checks import footprint
from overshare.checks.footprint import (
    check_certificate_transparency,
    check_mail_auth,
    registrable_domain,
)


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://example.com/", "example.com"),
        ("https://app.example.com/x", "example.com"),
        ("https://a.b.c.example.com/", "example.com"),
        ("https://my-app.lovable.app/", "lovable.app"),
        ("https://foo.example.co.uk/", "example.co.uk"),
        ("https://example.com.au/", "example.com.au"),
    ],
)
def test_registrable_domain(url, expected):
    assert registrable_domain(url) == expected


class FakeResponse:
    def __init__(self, text: str, ok: bool = True) -> None:
        self.text = text
        self.ok = ok


class FakeClient:
    def __init__(self, payload) -> None:
        self.payload = payload

    def try_get(self, url, **kwargs):
        if self.payload is None:
            return None
        return FakeResponse(json.dumps(self.payload))


def test_ct_ignores_lookalike_registrations(monkeypatch):
    """testexample.com ends with 'example.com' but is a different domain."""
    monkeypatch.setattr(footprint, "_query", lambda name, rdtype, timeout=5.0: ["1.2.3.4"])
    client = FakeClient(
        [
            {"name_value": "test.example.com"},
            {"name_value": "m.testexample.com"},
            {"name_value": "staging.example.com"},
        ]
    )
    findings = check_certificate_transparency("example.com", client)
    detail = next(f.detail for f in findings if f.check_id == "footprint.ct.subdomains")
    assert "test.example.com" in detail
    assert "staging.example.com" in detail
    assert "testexample.com" not in detail


def test_ct_flags_live_nonprod_subdomains(monkeypatch):
    monkeypatch.setattr(footprint, "_query", lambda name, rdtype, timeout=5.0: ["1.2.3.4"])
    client = FakeClient([{"name_value": "staging.example.com"}, {"name_value": "www.example.com"}])
    findings = check_certificate_transparency("example.com", client)
    risky = [f for f in findings if f.check_id == "footprint.ct.nonprod_subdomain_live"]
    assert len(risky) == 1
    assert "staging.example.com" in risky[0].detail
    assert "www.example.com" not in risky[0].evidence


def test_ct_ignores_nonprod_names_that_do_not_resolve(monkeypatch):
    monkeypatch.setattr(footprint, "_query", lambda name, rdtype, timeout=5.0: [])
    client = FakeClient([{"name_value": "staging.example.com"}])
    findings = check_certificate_transparency("example.com", client)
    assert not [f for f in findings if f.check_id == "footprint.ct.nonprod_subdomain_live"]


def test_ct_unavailable_degrades_gracefully():
    findings = check_certificate_transparency("example.com", FakeClient(None))
    assert [f.check_id for f in findings] == ["footprint.ct.unavailable"]


def test_missing_spf_and_dmarc_flagged(monkeypatch):
    monkeypatch.setattr(footprint, "_query", lambda name, rdtype, timeout=5.0: [])
    ids = {f.check_id for f in check_mail_auth("example.com")}
    assert "footprint.mail.spf_missing" in ids
    assert "footprint.mail.dmarc_missing" in ids


def test_permissive_spf_is_high_severity(monkeypatch):
    def fake_query(name, rdtype, timeout=5.0):
        if name == "example.com" and rdtype == "TXT":
            return ["v=spf1 include:_spf.google.com +all"]
        return []

    monkeypatch.setattr(footprint, "_query", fake_query)
    findings = check_mail_auth("example.com")
    permissive = [f for f in findings if f.check_id == "footprint.mail.spf_permissive"]
    assert permissive and permissive[0].severity.value == "high"


def test_hardened_mail_config_produces_no_findings(monkeypatch):
    def fake_query(name, rdtype, timeout=5.0):
        if name == "example.com" and rdtype == "TXT":
            return ["v=spf1 include:_spf.google.com -all"]
        if name == "_dmarc.example.com":
            return ["v=DMARC1; p=reject; rua=mailto:x@example.com"]
        return []

    monkeypatch.setattr(footprint, "_query", fake_query)
    assert check_mail_auth("example.com") == []


def test_dmarc_monitor_only_flagged(monkeypatch):
    def fake_query(name, rdtype, timeout=5.0):
        if name == "example.com" and rdtype == "TXT":
            return ["v=spf1 -all"]
        if name == "_dmarc.example.com":
            return ["v=DMARC1; p=none"]
        return []

    monkeypatch.setattr(footprint, "_query", fake_query)
    ids = {f.check_id for f in check_mail_auth("example.com")}
    assert "footprint.mail.dmarc_monitor_only" in ids
