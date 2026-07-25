from __future__ import annotations

from overshare.checks.transport import (
    PROBE_ORIGIN,
    check_cookies,
    check_cors,
    check_exposed_paths,
    check_headers,
)

URL = "https://app.test/"

SECURE_HEADERS = {
    "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "x-frame-options": "DENY",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
}


def ids(findings) -> set[str]:
    return {f.check_id for f in findings}


def test_fully_hardened_headers_produce_no_findings():
    assert check_headers(SECURE_HEADERS, URL) == []


def test_bare_headers_flag_every_missing_control():
    found = ids(check_headers({}, URL))
    assert "transport.header.csp_missing" in found
    assert "transport.header.hsts_missing" in found
    assert "transport.header.clickjacking" in found
    assert "transport.header.nosniff_missing" in found
    assert "transport.header.referrer_policy_missing" in found


def test_csp_frame_ancestors_satisfies_clickjacking_check():
    headers = {"content-security-policy": "frame-ancestors 'none'"}
    assert "transport.header.clickjacking" not in ids(check_headers(headers, URL))


def test_unsafe_inline_csp_flagged_as_weak_not_missing():
    headers = {**SECURE_HEADERS, "content-security-policy": "default-src 'self' 'unsafe-inline'"}
    found = ids(check_headers(headers, URL))
    assert "transport.header.csp_weak" in found
    assert "transport.header.csp_missing" not in found


def test_hsts_not_required_on_plaintext_site():
    assert "transport.header.hsts_missing" not in ids(check_headers({}, "http://app.test/"))


def test_server_banner_disclosure_flagged():
    headers = {**SECURE_HEADERS, "x-powered-by": "Express"}
    assert "transport.header.version_disclosure" in ids(check_headers(headers, URL))


def test_cdn_banner_not_treated_as_disclosure():
    headers = {**SECURE_HEADERS, "server": "cloudflare"}
    assert "transport.header.version_disclosure" not in ids(check_headers(headers, URL))


def test_reflected_origin_with_credentials_is_high():
    findings = check_cors(
        {
            "access-control-allow-origin": PROBE_ORIGIN,
            "access-control-allow-credentials": "true",
        },
        URL,
    )
    assert len(findings) == 1
    assert findings[0].check_id == "transport.cors.origin_reflected"
    assert findings[0].severity.value == "high"


def test_reflected_origin_without_credentials_is_medium():
    findings = check_cors({"access-control-allow-origin": PROBE_ORIGIN}, URL)
    assert findings[0].severity.value == "medium"


def test_wildcard_cors_alone_is_not_a_finding():
    assert check_cors({"access-control-allow-origin": "*"}, URL) == []


def test_wildcard_cors_with_credentials_flagged():
    findings = check_cors(
        {"access-control-allow-origin": "*", "access-control-allow-credentials": "true"}, URL
    )
    assert findings[0].check_id == "transport.cors.wildcard_with_credentials"


def test_no_cors_headers_no_findings():
    assert check_cors({}, URL) == []


def test_cookie_missing_flags_reported():
    findings = check_cookies([("set-cookie", "session=abc123; Path=/")], URL)
    assert len(findings) == 1
    assert "Secure" in findings[0].evidence
    assert "HttpOnly" in findings[0].evidence
    assert "SameSite" in findings[0].evidence


def test_fully_flagged_cookie_passes():
    header = [("set-cookie", "session=abc; Secure; HttpOnly; SameSite=Lax")]
    assert check_cookies(header, URL) == []


def test_env_file_exposure_detected():
    body = "SUPABASE_URL=https://x.supabase.co\nSTRIPE_KEY=sk_live_x\n"
    findings = check_exposed_paths("/.env", 200, body, "https://app.test")
    assert len(findings) == 1
    assert findings[0].severity.value == "critical"


def test_spa_catchall_html_does_not_produce_env_false_positive():
    """Most SPAs return index.html for unknown paths; that must not read as exposure."""
    body = "<!doctype html><html><head><title>App</title></head><body>=</body></html>"
    assert check_exposed_paths("/.env", 200, body, "https://app.test") == []


def test_git_head_exposure_detected():
    findings = check_exposed_paths("/.git/HEAD", 200, "ref: refs/heads/main\n", "https://app.test")
    assert len(findings) == 1


def test_non_200_is_never_an_exposure():
    assert check_exposed_paths("/.env", 404, "Not Found", "https://app.test") == []


def test_env_probe_returning_wrong_content_ignored():
    assert check_exposed_paths("/.env", 200, "nothing useful here", "https://app.test") == []
