from __future__ import annotations

import json

import httpx
import pytest

from leakscan.checks import transport
from leakscan.fetch.client import SafeClient
from leakscan.findings.model import Severity
from leakscan.scanner import scan

from . import fixtures as fx

BASE = "https://vulnerable.test"

INDEX_HTML = f"""<!doctype html>
<html><head>
  <title>My Vibe App</title>
  <script type="module" crossorigin src="/assets/app.js"></script>
  <script src="https://cdn.gpteng.co/gptengineer.js"></script>
</head><body>
  <div id="root"></div>
  <script>
    window.__CONFIG__ = {{
      SUPABASE_URL: "https://abcdefghijklmnopqrst.supabase.co",
      SUPABASE_ANON_KEY: "{fx.SUPABASE_ANON_JWT}"
    }};
  </script>
</body></html>
"""

APP_JS = f"""
import {{ createClient }} from "@supabase/supabase-js";
const supabase = createClient("https://abcdefghijklmnopqrst.supabase.co", "{fx.SUPABASE_ANON_JWT}");
const admin = createClient("https://abcdefghijklmnopqrst.supabase.co", "{fx.SUPABASE_SERVICE_ROLE_JWT}");
const stripe = "{fx.STRIPE_LIVE}";
const openai = "{fx.OPENAI}";
export default supabase;
//# sourceMappingURL=app.js.map
"""

SOURCE_MAP = json.dumps({"version": 3, "sources": ["src/App.tsx"], "mappings": "AAAA"})

ENV_FILE = f"DATABASE_URL={fx.POSTGRES_URI}\nSTRIPE_SECRET_KEY={fx.STRIPE_LIVE}\n"

ROUTES = {
    "/": (200, INDEX_HTML, "text/html"),
    "/assets/app.js": (200, APP_JS, "application/javascript"),
    "/assets/app.js.map": (200, SOURCE_MAP, "application/json"),
    "/.env": (200, ENV_FILE, "text/plain"),
    "/.git/HEAD": (200, "ref: refs/heads/main\n", "text/plain"),
}


def handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path not in ROUTES:
        return httpx.Response(404, text="Not Found")
    status, body, content_type = ROUTES[path]
    headers = {"content-type": content_type, "server": "nginx/1.18.0"}
    origin = request.headers.get("origin")
    if origin:
        headers["access-control-allow-origin"] = origin
        headers["access-control-allow-credentials"] = "true"
    if path == "/":
        headers["set-cookie"] = "session=abc123; Path=/"
    return httpx.Response(status, text=body, headers=headers)


@pytest.fixture
def result(monkeypatch):
    monkeypatch.setattr(transport, "check_tls", lambda url, timeout=10.0: [])
    client = SafeClient(transport=httpx.MockTransport(handler), allow_private=True)
    try:
        return scan(f"{BASE}/", client=client, include_footprint=False)
    finally:
        client.close()


def ids(result) -> set[str]:
    return {f.check_id for f in result.findings}


def test_finds_service_role_key_in_bundle(result):
    assert "secret.supabase.service_role" in ids(result)


def test_finds_stripe_and_openai_keys(result):
    found = ids(result)
    assert "secret.stripe.live_secret" in found
    assert "secret.openai.api_key" in found


def test_finds_exposed_env_and_git(result):
    found = ids(result)
    assert "exposure.path_env" in found or any(i.startswith("exposure.path") for i in found)


def test_finds_exposed_source_map(result):
    assert "exposure.source_map" in ids(result)


def test_detects_supabase_and_lovable(result):
    assert result.platform["backend"] == "supabase"
    assert result.platform["project_ref"] == "abcdefghijklmnopqrst"
    assert result.platform["builder"] == "lovable"


def test_flags_reflected_cors(result):
    assert "transport.cors.origin_reflected" in ids(result)


def test_flags_missing_headers_and_insecure_cookie(result):
    found = ids(result)
    assert "transport.header.csp_missing" in found
    assert "transport.cookie.insecure_flags" in found


def test_score_is_zero_for_a_thoroughly_broken_app(result):
    assert result.score() == 0
    assert result.grade() == "F"


def test_no_raw_secret_appears_anywhere_in_serialized_output(result):
    blob = json.dumps(result.to_dict())
    for secret in (fx.SUPABASE_SERVICE_ROLE_JWT, fx.STRIPE_LIVE, fx.OPENAI, fx.POSTGRES_URI):
        assert secret not in blob, "raw credential leaked into report output"


def test_scanned_assets_recorded(result):
    assert f"{BASE}/assets/app.js" in result.assets


def test_clean_app_scores_well(monkeypatch):
    clean_html = "<!doctype html><html><head><title>Clean</title></head><body></body></html>"

    def clean_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path != "/":
            return httpx.Response(404, text="Not Found")
        return httpx.Response(
            200,
            text=clean_html,
            headers={
                "content-type": "text/html",
                "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
                "strict-transport-security": "max-age=31536000",
                "x-frame-options": "DENY",
                "x-content-type-options": "nosniff",
                "referrer-policy": "strict-origin-when-cross-origin",
            },
        )

    monkeypatch.setattr(transport, "check_tls", lambda url, timeout=10.0: [])
    client = SafeClient(transport=httpx.MockTransport(clean_handler), allow_private=True)
    try:
        clean = scan(f"{BASE}/", client=client, include_footprint=False)
    finally:
        client.close()

    assert clean.score() == 100
    assert clean.grade() == "A"


def test_scan_of_blocked_target_records_error_and_finds_nothing():
    outcome = scan("http://169.254.169.254/latest/meta-data/", include_footprint=False)
    assert outcome.findings == []
    assert outcome.errors
    assert "rejected" in outcome.errors[0]
