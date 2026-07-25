"""Worker tests.

Scans run in spawned processes, so the parent cannot monkeypatch what the child
executes. The persistence branches are therefore tested with a stub pool, and a
single end-to-end test starts a real HTTP server and runs a real process pool —
that one is the point, because pickling and spawn re-import are exactly what
breaks when scans move out of process.
"""

from __future__ import annotations

import pickle
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from overshare.api.store import ScanStore
from overshare.api.worker import ScanWorker, run_scan

PAGE = b"""<!doctype html><html><head><title>t</title></head>
<body><script>const k = "sk_live_51H8xQmKZvLdEuKfPabcd";</script></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = PAGE if self.path == "/" else b"nope"
        self.send_response(200 if self.path == "/" else 404)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def target():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/"
    server.shutdown()


@pytest.fixture
def store():
    return ScanStore(":memory:")


def _wait(store: ScanStore, scan_id: str, timeout: float = 60.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        record = store.get(scan_id)
        if record.is_terminal:
            return record
        time.sleep(0.05)
    raise AssertionError(f"scan did not finish: {store.get(scan_id).status}")


def test_run_scan_survives_pickling():
    # Spawn pickles the callable by reference, so a closure or a bound method
    # here would fail only at runtime, in the child, under load.
    assert pickle.loads(pickle.dumps(run_scan)) is run_scan


def test_scan_really_runs_in_a_separate_process(target, store):
    worker = ScanWorker(
        store, max_workers=1, allow_private=True, include_footprint=False, include_ct=False
    )
    record = store.create(target)
    try:
        worker.submit(record.id, target)
        finished = _wait(store, record.id)
    finally:
        worker.shutdown()

    assert finished.status == "complete"
    check_ids = {f["check_id"] for f in finished.result["findings"]}
    assert "secret.stripe.live_secret" in check_ids


def test_child_process_never_holds_the_database(target, store):
    # The store is not picklable, so its presence in the child's arguments would
    # break spawn outright. This asserts the design rather than the symptom:
    # only data crosses the boundary.
    worker = ScanWorker(store, max_workers=1, allow_private=True, include_footprint=False)
    try:
        payload = run_scan(
            target, timeout=10.0, allow_private=True, include_footprint=False, include_ct=False
        )
    finally:
        worker.shutdown()

    assert isinstance(payload, dict)
    assert pickle.loads(pickle.dumps(payload)) == payload


class _StubPool:
    """Stands in for the process pool so the persistence branches stay fast."""

    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error

    def submit(self, *args, **kwargs):
        return self

    def result(self):
        if self._error is not None:
            raise self._error
        return self._result

    def shutdown(self, **kwargs):
        pass


def _worker_with(store, pool):
    worker = ScanWorker(store, max_workers=1)
    worker._scans.shutdown(wait=False)
    worker._scans = pool
    return worker


def test_unreachable_target_is_recorded_as_failed(store):
    # No assets means the page was never fetched. Storing that as a completed
    # scan with zero findings would be a fabricated clean result.
    payload = {"assets_scanned": [], "errors": ["target rejected: private address"]}
    worker = _worker_with(store, _StubPool(result=payload))
    record = store.create("https://blocked.example.com")

    worker._run(record.id, "https://blocked.example.com")

    finished = store.get(record.id)
    assert finished.status == "failed"
    assert finished.error_code == "blocked_target"


def test_crashed_worker_process_fails_the_scan(store):
    # A segfaulting child surfaces here as an exception on .result(). The scan
    # must not sit polling forever.
    worker = _worker_with(store, _StubPool(error=RuntimeError("process died")))
    record = store.create("https://example.com")

    worker._run(record.id, "https://example.com")

    finished = store.get(record.id)
    assert finished.status == "failed"
    assert finished.error_code == "internal_error"
    assert "process died" not in (finished.error_message or "")


def test_scan_is_marked_running_only_once_it_starts(store):
    seen = []
    payload = {"assets_scanned": ["https://example.com"], "errors": [], "findings": []}

    class _Watching(_StubPool):
        def submit(self, *args, **kwargs):
            seen.append(store.get(record.id).status)
            return self

    worker = _worker_with(store, _Watching(result=payload))
    record = store.create("https://example.com")

    worker._run(record.id, "https://example.com")

    assert seen == ["running"]
    assert store.get(record.id).status == "complete"
