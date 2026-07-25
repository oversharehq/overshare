from __future__ import annotations

from overshare.checks.platform import (
    detect_backend,
    detect_builder,
    detect_framework,
    detect_host,
    fingerprint,
)


def test_supabase_backend_and_project_ref():
    content = 'createClient("https://abcdefghijklmnopqrst.supabase.co","key")'
    detected = detect_backend(content)
    assert detected["backend"] == "supabase"
    assert detected["project_ref"] == "abcdefghijklmnopqrst"


def test_firebase_backend_and_project_id():
    content = 'initializeApp({authDomain:"x.firebaseapp.com","projectId":"my-app-1234"})'
    detected = detect_backend(content)
    assert detected["backend"] == "firebase"
    assert detected["project_id"] == "my-app-1234"


def test_convex_backend():
    assert detect_backend('new ConvexClient("https://happy-otter-123.convex.cloud")')[
        "backend"
    ] == "convex"


def test_no_backend_detected_on_static_site():
    assert detect_backend("console.log('hello')") == {}


def test_lovable_builder_from_injected_script():
    assert detect_builder('<script src="https://cdn.gpteng.co/gptengineer.js">', "", {}) == "lovable"


def test_lovable_builder_from_domain():
    assert detect_builder("", "https://my-app.lovable.app/", {}) == "lovable"


def test_bolt_builder():
    assert detect_builder("webcontainer boot", "https://x.test/", {}) == "bolt"


def test_replit_builder():
    assert detect_builder("", "https://my-app.replit.dev/", {}) == "replit"


def test_unknown_builder_returns_none():
    assert detect_builder("plain js", "https://example.com/", {}) is None


def test_marketing_mention_of_a_builder_is_not_a_fingerprint():
    """vercel.com talks about v0 constantly; that does not mean it was built with v0."""
    content = "Try v0.dev today! Build with lovable.app and bolt.new. v0-preview-2"
    assert detect_builder(content, "https://vercel.com/", {}) is None


def test_builder_domain_must_match_host_not_substring():
    assert detect_builder("", "https://not-lovable.app.evil.test/", {}) is None
    assert detect_builder("", "https://my-app.lovable.app/", {}) == "lovable"


def test_framework_detection():
    assert detect_framework("", '<script id="__NEXT_DATA__">') == "nextjs"
    assert detect_framework("react-dom.production.min.js", "") == "react"
    assert detect_framework("", "<astro-island>") == "astro"
    assert detect_framework("nothing", "") is None


def test_host_detection():
    assert detect_host({"x-vercel-id": "syd1::abc"}) == "vercel"
    assert detect_host({"x-nf-request-id": "abc"}) == "netlify"
    assert detect_host({"server": "cloudflare"}) == "cloudflare"
    assert detect_host({}) is None


def test_supabase_fingerprint_emits_rls_advisory():
    content = 'createClient("https://abcdefghijklmnopqrst.supabase.co","k")'
    platform, findings = fingerprint(content, "", "https://app.test/", {})
    ids = {f.check_id for f in findings}
    assert platform["backend"] == "supabase"
    assert "platform.supabase.rls_untested" in ids
    assert "platform.fingerprint" in ids


def test_non_supabase_stack_has_no_rls_advisory():
    platform, findings = fingerprint("react-dom", "", "https://app.test/", {})
    assert "platform.supabase.rls_untested" not in {f.check_id for f in findings}


def test_empty_stack_produces_no_fingerprint_finding():
    platform, findings = fingerprint("", "", "https://app.test/", {})
    assert platform == {}
    assert findings == []
