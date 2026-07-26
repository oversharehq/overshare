"""API layer tests. Contract lives in API_CONTRACT.md at the repo root.

No test here performs a real scan: the worker is replaced with a recorder, so
nothing touches the network.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

fastapi = pytest.importorskip("fastapi", reason="install with: pip install -e .[api]")
from fastapi.testclient import TestClient  # noqa: E402

from overshare.api.app import Settings, create_app  # noqa: E402
from overshare.api.serialize import fix_available, scan_to_dict  # noqa: E402
from overshare.api.store import ScanStore  # noqa: E402


class RecordingWorker:
    """Stands in for ScanWorker so no scan actually runs."""

    def __init__(self) -> None:
        self.submitted: list[tuple[str, str]] = []

    def submit(self, scan_id: str, url: str) -> None:
        self.submitted.append((scan_id, url))

    def shutdown(self) -> None:
        pass


@pytest.fixture
def store() -> ScanStore:
    return ScanStore(":memory:")


@pytest.fixture
def worker() -> RecordingWorker:
    return RecordingWorker()


@pytest.fixture
def client(store, worker) -> TestClient:
    settings = Settings(
        db_path=":memory:",
        rate_limit_per_hour=5,
        max_concurrent_per_ip=2,
        cache_seconds=0,
    )
    app = create_app(settings, store=store, worker=worker)
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_version(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"]


def test_create_scan_returns_202_and_queues_work(client, worker):
    response = client.post("/v1/scans", json={"url": "https://example.com"})

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["tier"] == "passive"
    assert body["result"] is None
    assert body["error"] is None
    assert body["id"].startswith("scn_")
    assert worker.submitted == [(body["id"], "https://example.com")]


def test_bare_hostname_gets_https_scheme(client):
    response = client.post("/v1/scans", json={"url": "example.com"})
    assert response.json()["url"] == "https://example.com"


@pytest.mark.parametrize(
    "url",
    ["", "   ", "not a url", "file:///etc/passwd", "ftp://example.com"],
)
def test_unusable_urls_are_400(client, url):
    response = client.post("/v1/scans", json={"url": url})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_url"


def test_missing_body_field_is_400_in_contract_shape(client):
    response = client.post("/v1/scans", json={})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_url"


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8000/",
        "http://localhost/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/",
        "http://admin.internal/",
    ],
)
def test_ssrf_targets_rejected_as_422_before_queueing(client, worker, url):
    response = client.post("/v1/scans", json={"url": url})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "blocked_target"
    # Nothing must reach a worker: rejection happens on the request path.
    assert worker.submitted == []


def test_blocked_target_message_does_not_leak_the_reason(client):
    response = client.post("/v1/scans", json={"url": "http://169.254.169.254/"})
    message = response.json()["error"]["message"]
    assert "169.254" not in message
    assert "metadata" not in message.lower()


def test_unknown_scan_is_404(client):
    response = client.get("/v1/scans/scn_nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "scan_not_found"


def test_concurrency_limit_returns_429_with_retry_after(client):
    for _ in range(2):
        assert client.post("/v1/scans", json={"url": "https://example.com"}).status_code == 202

    response = client.post("/v1/scans", json={"url": "https://example.com"})
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"
    assert response.headers["Retry-After"]


def test_hourly_limit_counts_completed_scans(store, worker):
    settings = Settings(
        db_path=":memory:", rate_limit_per_hour=2, max_concurrent_per_ip=99, cache_seconds=0
    )
    app = create_app(settings, store=store, worker=worker)
    with TestClient(app) as client:
        for _ in range(2):
            created = client.post("/v1/scans", json={"url": "https://example.com"})
            store.mark_complete(created.json()["id"], {"findings": []})

        response = client.post("/v1/scans", json={"url": "https://example.com"})
        assert response.status_code == 429


def test_fresh_result_is_reused_instead_of_rescanning(store, worker):
    settings = Settings(
        db_path=":memory:", rate_limit_per_hour=99, max_concurrent_per_ip=99, cache_seconds=300
    )
    app = create_app(settings, store=store, worker=worker)
    with TestClient(app) as client:
        first = client.post("/v1/scans", json={"url": "https://example.com"})
        store.mark_complete(first.json()["id"], {"findings": [], "score": 100})

        second = client.post("/v1/scans", json={"url": "https://example.com"})

        assert second.status_code == 200
        assert second.json()["id"] == first.json()["id"]
        # One submission only — the second request must not start a new scan.
        assert len(worker.submitted) == 1


def test_completed_scan_serialises_findings_with_paid_fields(client, store):
    created = client.post("/v1/scans", json={"url": "https://example.com"})
    store.mark_complete(
        created.json()["id"],
        {
            "score": 60,
            "findings": [
                {"check_id": "secret.stripe.live_secret", "severity": "critical"},
                {"check_id": "transport.header.nosniff_missing", "severity": "low"},
            ],
        },
    )

    body = client.get(f"/v1/scans/{created.json()['id']}").json()

    assert body["status"] == "complete"
    findings = body["result"]["findings"]
    # fix is the paid artifact and does not exist until M5.
    assert all(f["fix"] is None for f in findings)
    assert findings[0]["fix_available"] is True
    assert findings[1]["fix_available"] is False


def test_failed_scan_exposes_error_not_result(client, store):
    created = client.post("/v1/scans", json={"url": "https://example.com"})
    store.mark_failed(created.json()["id"], "internal_error", "The app could not be reached.")

    body = client.get(f"/v1/scans/{created.json()['id']}").json()

    assert body["status"] == "failed"
    assert body["result"] is None
    assert body["error"] == {
        "code": "internal_error",
        "message": "The app could not be reached.",
    }


def test_interrupted_scans_are_failed_not_left_polling(store):
    record = store.create("https://example.com")
    store.mark_running(record.id)

    assert store.reap_orphans() == 1

    reaped = store.get(record.id)
    assert reaped.status == "failed"
    assert reaped.error_code == "internal_error"


def test_poll_interval_stops_once_terminal(store):
    record = store.create("https://example.com")
    assert scan_to_dict(record)["poll_after_ms"] > 0

    store.mark_complete(record.id, {"findings": []})
    assert scan_to_dict(store.get(record.id))["poll_after_ms"] == 0


def _backdate(store: ScanStore, scan_id: str, days: int) -> None:
    stamp = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    store._conn.execute("UPDATE scans SET created_at = ? WHERE id = ?", (stamp, scan_id))
    store._conn.commit()


def test_scans_past_retention_are_deleted(store):
    old = store.create("https://old.example.com")
    recent = store.create("https://recent.example.com")
    store.mark_complete(old.id, {"findings": []})
    store.mark_complete(recent.id, {"findings": []})
    _backdate(store, old.id, 31)

    assert store.purge_expired(30 * 86400) == 1

    assert store.get(old.id) is None
    assert store.get(recent.id) is not None


def test_purge_expires_scans_that_never_finished(store):
    # Keyed on created_at, so a row with no completed_at still expires rather
    # than accumulating forever.
    stuck = store.create("https://stuck.example.com")
    _backdate(store, stuck.id, 31)

    assert store.purge_expired(30 * 86400) == 1
    assert store.get(stuck.id) is None


def test_expired_scan_reads_as_not_found(client, store):
    created = client.post("/v1/scans", json={"url": "https://example.com"})
    scan_id = created.json()["id"]
    _backdate(store, scan_id, 31)
    store.purge_expired(30 * 86400)

    response = client.get(f"/v1/scans/{scan_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "scan_not_found"


@pytest.mark.parametrize(
    "retention_days,expected_sweeper", [(30, True), (0, False), (-1, False)]
)
def test_sweeper_runs_only_when_retention_is_positive(
    store, worker, retention_days, expected_sweeper
):
    # Zero must mean "keep everything", not "expire everything" — someone
    # setting it to mean "no limit" should not wipe the table.
    settings = Settings(db_path=":memory:", retention_days=retention_days)
    app = create_app(settings, store=store, worker=worker)
    with TestClient(app):
        assert (app.state.sweeper is not None) is expected_sweeper


@pytest.mark.parametrize(
    "check_id,expected",
    [
        ("secret.supabase.service_role", True),
        ("secret.aws.access_key_id", True),
        ("platform.supabase.rls_untested", True),
        ("transport.header.csp_missing", True),
        ("transport.cors.origin_reflected", True),
        # Generic one-liners: `remediation` already says everything a paid fix
        # could, so offering one would be selling nothing.
        ("transport.header.nosniff_missing", False),
        ("footprint.mail.dmarc_missing", False),
        ("platform.fingerprint", False),
    ],
)
def test_fix_is_only_offered_where_it_adds_something(check_id, expected):
    assert fix_available(check_id) is expected


# --- waitlist ---------------------------------------------------------------


def test_waitlist_accepts_and_stores_an_address(client, store):
    response = client.post("/v1/waitlist", json={"email": "someone@example.com"})

    assert response.status_code == 202
    assert response.json() == {"status": "ok"}
    assert store.count_waitlist_since("testclient", 3600) == 1


def test_waitlist_normalises_case_and_whitespace(client, store):
    client.post("/v1/waitlist", json={"email": "  Someone@Example.COM  "})

    row = store._conn.execute("SELECT email FROM waitlist").fetchone()
    assert row["email"] == "someone@example.com"


def test_waitlist_signup_is_idempotent(client, store):
    first = client.post("/v1/waitlist", json={"email": "dupe@example.com"})
    second = client.post("/v1/waitlist", json={"email": "DUPE@example.com"})

    # Identical responses: whether an address is already stored must not be
    # observable from an unauthenticated endpoint.
    assert (first.status_code, first.json()) == (second.status_code, second.json())
    count = store._conn.execute("SELECT COUNT(*) AS n FROM waitlist").fetchone()["n"]
    assert count == 1


@pytest.mark.parametrize(
    "email",
    [
        "",
        "   ",
        "not-an-email",
        "no@domain",
        "@example.com",
        "spaces in@example.com",
        "two@@example.com",
        None,
        12345,
        "a" * 250 + "@example.com",
    ],
)
def test_waitlist_rejects_malformed_addresses(client, store, email):
    response = client.post("/v1/waitlist", json={"email": email})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_email"
    count = store._conn.execute("SELECT COUNT(*) AS n FROM waitlist").fetchone()["n"]
    assert count == 0


def test_waitlist_rate_limits_per_ip(store, worker):
    settings = Settings(db_path=":memory:", waitlist_limit_per_hour=2)
    app = create_app(settings, store=store, worker=worker)
    with TestClient(app) as client:
        assert client.post("/v1/waitlist", json={"email": "a@example.com"}).status_code == 202
        assert client.post("/v1/waitlist", json={"email": "b@example.com"}).status_code == 202

        blocked = client.post("/v1/waitlist", json={"email": "c@example.com"})
        assert blocked.status_code == 429
        assert blocked.json()["error"]["code"] == "rate_limited"
        assert blocked.headers["Retry-After"] == "3600"


def test_waitlist_survives_the_retention_sweep(store):
    """A scan expires after 30 days. Consent to be contacted does not."""
    store.add_waitlist("keep@example.com", client_ip="1.2.3.4")
    store.create("https://example.com")

    store.purge_expired(0)

    count = store._conn.execute("SELECT COUNT(*) AS n FROM waitlist").fetchone()["n"]
    assert count == 1


def test_waitlist_notification_failure_does_not_fail_the_signup(client, store, monkeypatch):
    """The address is committed before the email is attempted.

    A provider outage must not turn a stored signup into an error the visitor
    sees, or they will submit again and assume it is broken.
    """
    monkeypatch.setenv("OVERSHARE_MAILGUN_API_KEY", "test-key")
    monkeypatch.setenv("OVERSHARE_MAILGUN_DOMAIN", "sandbox.mailgun.org")
    monkeypatch.setenv("OVERSHARE_NOTIFY_EMAIL", "owner@example.com")

    def explode(*_args, **_kwargs):
        raise RuntimeError("provider is down")

    monkeypatch.setattr("overshare.api.notify.httpx.post", explode)

    response = client.post("/v1/waitlist", json={"email": "resilient@example.com"})

    assert response.status_code == 202
    count = store._conn.execute("SELECT COUNT(*) AS n FROM waitlist").fetchone()["n"]
    assert count == 1


def test_waitlist_notification_is_skipped_when_unconfigured(client, monkeypatch):
    monkeypatch.delenv("OVERSHARE_MAILGUN_API_KEY", raising=False)
    monkeypatch.delenv("OVERSHARE_MAILGUN_DOMAIN", raising=False)
    monkeypatch.delenv("OVERSHARE_NOTIFY_EMAIL", raising=False)

    calls: list = []
    monkeypatch.setattr(
        "overshare.api.notify.httpx.post", lambda *a, **k: calls.append(a)
    )

    assert client.post("/v1/waitlist", json={"email": "quiet@example.com"}).status_code == 202
    assert calls == []


def test_waitlist_notification_sends_when_configured(client, monkeypatch):
    monkeypatch.setenv("OVERSHARE_MAILGUN_API_KEY", "test-key")
    monkeypatch.setenv("OVERSHARE_MAILGUN_DOMAIN", "sandbox.mailgun.org")
    monkeypatch.setenv("OVERSHARE_NOTIFY_EMAIL", "owner@example.com")

    sent: list[dict] = []

    class Response:
        def raise_for_status(self) -> None:
            pass

    def capture(url, **kwargs):
        sent.append({"url": url, **kwargs})
        return Response()

    monkeypatch.setattr("overshare.api.notify.httpx.post", capture)

    client.post("/v1/waitlist", json={"email": "signup@example.com"})

    assert len(sent) == 1
    assert sent[0]["url"] == "https://api.mailgun.net/v3/sandbox.mailgun.org/messages"
    # Mailgun authenticates with HTTP Basic, username literally "api".
    assert sent[0]["auth"] == ("api", "test-key")
    assert sent[0]["data"]["to"] == "owner@example.com"
    # Not @oversharehq.com: that domain's SPF ends in -all and does not list
    # Mailgun, so mail sent from it would be dropped silently.
    assert "oversharehq.com" not in sent[0]["data"]["from"]
    assert "signup@example.com" in sent[0]["data"]["text"]


@pytest.mark.parametrize(
    "present",
    [
        ("OVERSHARE_MAILGUN_API_KEY",),
        ("OVERSHARE_MAILGUN_DOMAIN",),
        ("OVERSHARE_NOTIFY_EMAIL",),
        ("OVERSHARE_MAILGUN_API_KEY", "OVERSHARE_MAILGUN_DOMAIN"),
    ],
)
def test_partial_notification_config_sends_nothing(client, monkeypatch, present):
    """Three variables means partial configuration is a realistic mistake.

    Half-configured must behave like unconfigured rather than firing a request
    that cannot succeed — Mailgun answers a bad domain with a 404 that looks
    nothing like a credentials problem.
    """
    for name in (
        "OVERSHARE_MAILGUN_API_KEY",
        "OVERSHARE_MAILGUN_DOMAIN",
        "OVERSHARE_NOTIFY_EMAIL",
    ):
        monkeypatch.delenv(name, raising=False)
    for name in present:
        monkeypatch.setenv(name, "value")

    calls: list = []
    monkeypatch.setattr("overshare.api.notify.httpx.post", lambda *a, **k: calls.append(a))

    assert client.post("/v1/waitlist", json={"email": "x@example.com"}).status_code == 202
    assert calls == []
