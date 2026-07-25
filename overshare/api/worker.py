from __future__ import annotations

import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import get_context

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


def run_scan(
    url: str,
    *,
    timeout: float,
    allow_private: bool,
    include_footprint: bool,
    include_ct: bool,
) -> dict:
    """The scan itself, executed in a worker *process*.

    Module level and returning a plain dict on purpose: it has to be importable
    by a spawned interpreter, and only data may cross the process boundary. It
    takes no store handle, so every database write stays in the parent and a
    compromised scan has nothing to write to.
    """
    return scan(
        url,
        timeout=timeout,
        allow_private=allow_private,
        include_footprint=include_footprint,
        include_ct=include_ct,
    ).to_dict()


class ScanWorker:
    """Runs scans off the request path, in separate processes.

    Two pools, and the split is the point. Dispatch threads do the bookkeeping —
    mark running, wait, write the result — because that is trusted code holding
    the database handle. The scan itself goes to a process pool, because it
    parses arbitrary JavaScript from a target we do not control and fetches
    arbitrary URLs. In-process that code had the API's memory, its file
    descriptors and its lifetime, so a single segfault or runaway allocation in
    a parser took the whole service down with it. A process boundary bounds that
    to one scan and lets the OS reclaim whatever it leaked.

    `spawn`, not the platform default: the API process is threaded (uvicorn's
    loop, FastAPI's threadpool), and forking a threaded process copies its locks
    in whatever state they happened to be in, which deadlocks the child.

    This is blast-radius containment, not a sandbox. Restricting what a scan can
    reach is the deployment's job — see fly.toml.
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
        self._dispatch = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="overshare-dispatch"
        )
        self._scans = ProcessPoolExecutor(
            max_workers=max_workers, mp_context=get_context("spawn")
        )

    def submit(self, scan_id: str, url: str) -> None:
        self._dispatch.submit(self._run, scan_id, url)

    def shutdown(self) -> None:
        self._dispatch.shutdown(wait=False, cancel_futures=True)
        self._scans.shutdown(wait=False, cancel_futures=True)

    def _run(self, scan_id: str, url: str) -> None:
        try:
            # Marked here rather than at submit time: while the pool is
            # saturated the scan really is still queued, and saying otherwise
            # would be a lie the poll endpoint repeats to the user.
            self._store.mark_running(scan_id)
            payload = self._scans.submit(
                run_scan,
                url,
                timeout=self._timeout,
                allow_private=self._allow_private,
                include_footprint=self._include_footprint,
                include_ct=self._include_ct,
            ).result()
        except Exception:
            # Covers a crashed worker process as well as an exception inside the
            # scan. Full detail to the log, nothing internal to the caller.
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
        if not payload["assets_scanned"]:
            code, message = _user_message(payload["errors"])
            self._store.mark_failed(scan_id, code, message)
            return

        self._store.mark_complete(scan_id, payload)
