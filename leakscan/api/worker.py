from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from ..scanner import scan
from .store import ScanStore

logger = logging.getLogger(__name__)


def _user_message(errors: list[str]) -> tuple[str, str]:
    """Map internal scanner errors onto a code and a message safe to show a user.

    Scanner errors carry exception text and internal hostnames. The contract
    requires user-facing messages to be plain language and to leak nothing, so
    nothing from `errors` is passed through verbatim.
    """
    first = errors[0] if errors else ""
    if first.startswith("target rejected:"):
        return (
            "blocked_target",
            "That address could not be scanned. Only publicly reachable apps are supported.",
        )
    return (
        "internal_error",
        "The app could not be reached. Check the URL loads in a browser and try again.",
    )


class ScanWorker:
    """Runs scans off the request path.

    Threads, not isolated processes. The build brief calls for sandboxed workers
    with locked-down egress, because a scan parses arbitrary JavaScript and hits
    arbitrary endpoints — that hardening belongs in the deployment, by running
    this as its own service with its own egress rules rather than beside the API.
    """

    def __init__(
        self,
        store: ScanStore,
        *,
        max_workers: int = 2,
        timeout: float = 10.0,
        include_footprint: bool = True,
        include_ct: bool = True,
        allow_private: bool = False,
    ) -> None:
        self._store = store
        self._timeout = timeout
        self._include_footprint = include_footprint
        self._include_ct = include_ct
        self._allow_private = allow_private
        self._pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="leakscan-worker"
        )

    def submit(self, scan_id: str, url: str) -> None:
        self._pool.submit(self._run, scan_id, url)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    def _run(self, scan_id: str, url: str) -> None:
        try:
            self._store.mark_running(scan_id)
            result = scan(
                url,
                timeout=self._timeout,
                allow_private=self._allow_private,
                include_footprint=self._include_footprint,
                include_ct=self._include_ct,
            )
        except Exception:
            # Full detail to the log, nothing internal to the caller.
            logger.exception("scan %s crashed", scan_id)
            self._store.mark_failed(
                scan_id,
                "internal_error",
                "The scan stopped unexpectedly. Please try again.",
            )
            return

        # scanner._run appends the final URL to `assets` immediately after the
        # page fetch succeeds, so an empty list means the target was never
        # reached at all — which is a failed scan, not a clean one.
        if not result.assets:
            code, message = _user_message(result.errors)
            self._store.mark_failed(scan_id, code, message)
            return

        self._store.mark_complete(scan_id, result.to_dict())
