from __future__ import annotations

import pytest

from overshare.checks.secrets import decode_jwt_payload, scan_content
from overshare.findings.model import Severity

from . import fixtures as fx


def ids_for(content: str) -> set[str]:
    return {f.check_id for f in scan_content(content, "https://x.test/app.js")}


POSITIVE_CASES = [
    (fx.SUPABASE_SECRET, "secret.supabase.secret_key", Severity.CRITICAL),
    (fx.STRIPE_LIVE, "secret.stripe.live_secret", Severity.CRITICAL),
    (fx.STRIPE_RESTRICTED, "secret.stripe.restricted", Severity.HIGH),
    (fx.AWS_KEY_ID, "secret.aws.access_key_id", Severity.CRITICAL),
    (fx.OPENAI, "secret.openai.api_key", Severity.CRITICAL),
    (fx.ANTHROPIC, "secret.anthropic.api_key", Severity.CRITICAL),
    (fx.GITHUB_TOKEN, "secret.github.token", Severity.CRITICAL),
    (fx.GITHUB_PAT, "secret.github.fine_grained_pat", Severity.CRITICAL),
    (fx.SLACK, "secret.slack.token", Severity.CRITICAL),
    (fx.SENDGRID, "secret.sendgrid.api_key", Severity.CRITICAL),
    (fx.PADDLE, "secret.paddle.api_key", Severity.CRITICAL),
    (fx.MAILGUN, "secret.mailgun.api_key", Severity.HIGH),
    (fx.GOOGLE_API, "secret.google.api_key", Severity.MEDIUM),
    (fx.POSTGRES_URI, "secret.db_connection_string", Severity.CRITICAL),
    (fx.PRIVATE_KEY, "secret.private_key", Severity.CRITICAL),
    (fx.JWT_SECRET_ASSIGNMENT, "secret.jwt_signing_secret", Severity.CRITICAL),
]


@pytest.mark.parametrize(
    "value,check_id,severity", POSITIVE_CASES, ids=[c[1] for c in POSITIVE_CASES]
)
def test_detects_secret(value, check_id, severity):
    content = f'const config = {{ key: "{value}" }};'
    findings = scan_content(content, "https://x.test/app.js")
    match = [f for f in findings if f.check_id == check_id]
    assert match, f"{check_id} not detected in {content[:80]}"
    assert match[0].severity is severity


def test_benign_bundle_produces_no_findings():
    """The false-positive guard. Build hashes and minified identifiers are not secrets."""
    findings = scan_content(fx.BENIGN_BUNDLE, "https://x.test/app.js")
    assert findings == [], f"false positives: {[f.check_id for f in findings]}"


def test_service_role_jwt_is_critical():
    findings = scan_content(fx.SUPABASE_SERVICE_ROLE_JWT, "https://x.test/app.js")
    match = [f for f in findings if f.check_id == "secret.supabase.service_role"]
    assert len(match) == 1
    assert match[0].severity is Severity.CRITICAL
    assert "abcdefghijklmnopqrst" in match[0].detail


def test_anon_jwt_is_informational_not_a_vulnerability():
    findings = scan_content(fx.SUPABASE_ANON_JWT, "https://x.test/app.js")
    ids = {f.check_id for f in findings}
    assert "platform.supabase.anon_key" in ids
    assert "secret.supabase.service_role" not in ids
    assert all(f.severity is Severity.INFO for f in findings)


def test_evidence_never_contains_the_full_secret():
    for value, check_id, _ in POSITIVE_CASES:
        findings = scan_content(value, "https://x.test/app.js")
        for f in findings:
            assert value not in f.evidence, f"{check_id} leaked the raw secret into evidence"


def test_service_role_jwt_is_redacted_in_output():
    findings = scan_content(fx.SUPABASE_SERVICE_ROLE_JWT, "https://x.test/app.js")
    assert fx.SUPABASE_SERVICE_ROLE_JWT not in findings[0].evidence
    assert "*" in findings[0].evidence


def test_anthropic_key_not_double_reported_as_openai():
    ids = ids_for(fx.ANTHROPIC)
    assert ids == {"secret.anthropic.api_key"}


def test_malformed_jwt_ignored():
    assert decode_jwt_payload("eyJhbGciOi.notbase64!!.sig") is None
    assert decode_jwt_payload("not.a.jwt") is None
    assert decode_jwt_payload("onlyonepart") is None


def test_duplicate_occurrences_reported_once():
    content = f"{fx.STRIPE_LIVE} and again {fx.STRIPE_LIVE}"
    findings = [f for f in scan_content(content, "u") if f.check_id == "secret.stripe.live_secret"]
    assert len(findings) == 1


def test_stripe_publishable_key_is_not_flagged():
    assert ids_for('const pk = "pk_live_51H8xKQ2mNpR7vT4wY6zA1bC3dE5fG7hJ";') == set()
