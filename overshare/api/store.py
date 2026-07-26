from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

QUEUED = "queued"
RUNNING = "running"
COMPLETE = "complete"
FAILED = "failed"

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id            TEXT PRIMARY KEY,
    url           TEXT NOT NULL,
    tier          TEXT NOT NULL,
    status        TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    started_at    TEXT,
    completed_at  TEXT,
    result_json   TEXT,
    error_code    TEXT,
    error_message TEXT,
    client_ip     TEXT
);
CREATE INDEX IF NOT EXISTS scans_client_created ON scans (client_ip, created_at);
CREATE INDEX IF NOT EXISTS scans_url_status ON scans (url, status, completed_at);
CREATE INDEX IF NOT EXISTS scans_created ON scans (created_at);

-- Deliberately outside the retention sweep, which only touches `scans`. A scan
-- is a vulnerability report with a shelf life; a waitlist signup is consent to
-- be contacted, and silently deleting it after 30 days would lose the consent
-- while keeping none of the benefit.
CREATE TABLE IF NOT EXISTS waitlist (
    email      TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    client_ip  TEXT
);
CREATE INDEX IF NOT EXISTS waitlist_client_created ON waitlist (client_ip, created_at);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _since(seconds: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


@dataclass
class ScanRecord:
    id: str
    url: str
    tier: str
    status: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    result: dict | None = None
    error_code: str | None = None
    error_message: str | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status in (COMPLETE, FAILED)


def _row_to_record(row: sqlite3.Row) -> ScanRecord:
    return ScanRecord(
        id=row["id"],
        url=row["url"],
        tier=row["tier"],
        status=row["status"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        result=json.loads(row["result_json"]) if row["result_json"] else None,
        error_code=row["error_code"],
        error_message=row["error_message"],
    )


class ScanStore:
    """SQLite-backed job store.

    A job table rather than a managed queue, per the build brief's portability
    rules — this moves to Postgres by swapping the connection, with no change to
    callers or to the deployment platform.
    """

    def __init__(self, path: str = ":memory:") -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            if path != ":memory:":
                self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def create(self, url: str, *, tier: str = "passive", client_ip: str | None = None) -> ScanRecord:
        record = ScanRecord(
            id=f"scn_{uuid.uuid4().hex[:16]}",
            url=url,
            tier=tier,
            status=QUEUED,
            created_at=utcnow(),
        )
        with self._lock:
            self._conn.execute(
                "INSERT INTO scans (id, url, tier, status, created_at, client_ip)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (record.id, url, tier, QUEUED, record.created_at, client_ip),
            )
            self._conn.commit()
        return record

    def get(self, scan_id: str) -> ScanRecord | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM scans WHERE id = ?", (scan_id,)
            ).fetchone()
        return _row_to_record(row) if row else None

    def mark_running(self, scan_id: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE scans SET status = ?, started_at = ? WHERE id = ?",
                (RUNNING, utcnow(), scan_id),
            )
            self._conn.commit()

    def mark_complete(self, scan_id: str, result: dict) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE scans SET status = ?, completed_at = ?, result_json = ? WHERE id = ?",
                (COMPLETE, utcnow(), json.dumps(result), scan_id),
            )
            self._conn.commit()

    def mark_failed(self, scan_id: str, code: str, message: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE scans SET status = ?, completed_at = ?, error_code = ?,"
                " error_message = ? WHERE id = ?",
                (FAILED, utcnow(), code, message, scan_id),
            )
            self._conn.commit()

    def count_since(self, client_ip: str, seconds: int) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM scans WHERE client_ip = ? AND created_at >= ?",
                (client_ip, _since(seconds)),
            ).fetchone()
        return int(row["n"])

    def count_active(self, client_ip: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM scans WHERE client_ip = ? AND status IN (?, ?)",
                (client_ip, QUEUED, RUNNING),
            ).fetchone()
        return int(row["n"])

    def find_cached(self, url: str, seconds: int) -> ScanRecord | None:
        """Most recent completed scan of this URL, if it is fresh enough to reuse."""
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM scans WHERE url = ? AND status = ? AND completed_at >= ?"
                " ORDER BY completed_at DESC LIMIT 1",
                (url, COMPLETE, _since(seconds)),
            ).fetchone()
        return _row_to_record(row) if row else None

    def purge_expired(self, seconds: int) -> int:
        """Delete scans past the retention window.

        A stored scan is a vulnerability report about a live app, frequently one
        the submitter does not own. Kept indefinitely the job table becomes a
        target list, so retention is a deliberate bound rather than whatever the
        disk happens to hold. Keyed on created_at so a row that never reached a
        terminal status expires too.
        """
        with self._lock:
            cursor = self._conn.execute(
                "DELETE FROM scans WHERE created_at < ?", (_since(seconds),)
            )
            self._conn.commit()
            return cursor.rowcount

    def reap_orphans(self) -> int:
        """Fail scans left running by a process that died.

        Without this a crashed worker leaves a scan polling forever. Reporting it
        as failed is honest; leaving it queued is not.
        """
        with self._lock:
            cursor = self._conn.execute(
                "UPDATE scans SET status = ?, completed_at = ?, error_code = ?,"
                " error_message = ? WHERE status IN (?, ?)",
                (
                    FAILED,
                    utcnow(),
                    "internal_error",
                    "The scan was interrupted before it finished. Please run it again.",
                    QUEUED,
                    RUNNING,
                ),
            )
            self._conn.commit()
            return cursor.rowcount

    def add_waitlist(self, email: str, *, client_ip: str | None = None) -> None:
        """Record interest in the hosted tier. Idempotent.

        INSERT OR IGNORE rather than a duplicate check, so a second signup from
        the same address is a no-op and keeps the original timestamp. Callers
        get no signal either way — whether an address is already on the list is
        not something an unauthenticated endpoint should confirm.
        """
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO waitlist (email, created_at, client_ip)"
                " VALUES (?, ?, ?)",
                (email, utcnow(), client_ip),
            )
            self._conn.commit()

    def count_waitlist_since(self, client_ip: str, seconds: int) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM waitlist WHERE client_ip = ? AND created_at >= ?",
                (client_ip, _since(seconds)),
            ).fetchone()
            return row["n"]
