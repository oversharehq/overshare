from __future__ import annotations

import logging
import os
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .. import __version__
from ..fetch.ssrf import BlockedTarget, validate_url
from .serialize import scan_to_dict
from .store import ScanStore
from .worker import ScanWorker


logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass
class Settings:
    db_path: str = os.environ.get("OVERSHARE_DB_PATH", "overshare-scans.db")
    max_workers: int = _env_int("OVERSHARE_MAX_WORKERS", 2)
    scan_timeout: float = float(os.environ.get("OVERSHARE_SCAN_TIMEOUT", "10"))
    rate_limit_per_hour: int = _env_int("OVERSHARE_RATE_LIMIT_PER_HOUR", 5)
    max_concurrent_per_ip: int = _env_int("OVERSHARE_MAX_CONCURRENT_PER_IP", 1)
    cache_seconds: int = _env_int("OVERSHARE_CACHE_SECONDS", 300)
    # Only enable behind a proxy you control. X-Forwarded-For is caller-supplied,
    # so trusting it on a directly-exposed API makes rate limits bypassable by
    # anyone willing to set a header.
    trust_proxy: bool = os.environ.get("OVERSHARE_TRUST_PROXY") == "1"
    # Disables SSRF protection. Local testing against testdata/ only — mirrors
    # the CLI's --unsafe-allow-private-ips. Never set this on a public deploy.
    allow_private: bool = os.environ.get("OVERSHARE_UNSAFE_ALLOW_PRIVATE_IPS") == "1"


def _error(code: str, message: str, status: int, headers: dict | None = None) -> JSONResponse:
    return JSONResponse(
        {"error": {"code": code, "message": message}}, status_code=status, headers=headers
    )


def _client_ip(request: Request, trust_proxy: bool) -> str:
    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


_HOSTNAME_RE = re.compile(
    r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$"
)


def _is_hostname_shaped(host: str) -> bool:
    """Distinguish a typo from a target we refuse to scan.

    Without this, "not a url" reaches DNS resolution, fails, and comes back as
    blocked_target — telling someone their app is unreachable when they actually
    just mistyped. Colons mean an IPv6 literal, which check_ip judges properly.
    """
    if ":" in host:
        return True
    return bool(_HOSTNAME_RE.match(host))


def _normalise(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    candidate = raw.strip()
    if not candidate:
        return None
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    return candidate


def create_app(
    settings: Settings | None = None,
    *,
    store: ScanStore | None = None,
    worker: ScanWorker | None = None,
) -> FastAPI:
    """`store` and `worker` are injection points for tests.

    Left unset they are built from `settings`, which is what production does.
    """
    config = settings or Settings()

    if config.allow_private:
        logger.warning(
            "SSRF protection is DISABLED (OVERSHARE_UNSAFE_ALLOW_PRIVATE_IPS=1). "
            "This must never be set on a publicly reachable deployment."
        )

    store = store or ScanStore(config.db_path)
    worker = worker or ScanWorker(
        store,
        max_workers=config.max_workers,
        timeout=config.scan_timeout,
        allow_private=config.allow_private,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        # Anything still marked running belongs to a process that is gone.
        store.reap_orphans()
        yield
        worker.shutdown()
        store.close()

    app = FastAPI(
        title="Overshare API",
        version=__version__,
        lifespan=lifespan,
        docs_url="/v1/docs",
        openapi_url="/v1/openapi.json",
    )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_: Request, __: RequestValidationError):
        # FastAPI's default 422 body does not match API_CONTRACT.md §8.
        return _error("invalid_url", "Enter the URL of your app.", 400)

    @app.get("/v1/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    # Sync def: FastAPI runs these in a threadpool, and both DNS resolution in
    # validate_url and the SQLite calls are blocking.
    @app.post("/v1/scans")
    def create_scan(request: Request, payload: dict) -> JSONResponse:
        url = _normalise(payload.get("url"))
        if url is None:
            return _error("invalid_url", "Enter the URL of your app.", 400)

        parts = urlsplit(url)
        if parts.scheme not in ("http", "https"):
            return _error("invalid_url", "Only http and https URLs can be scanned.", 400)
        if not parts.hostname or not _is_hostname_shaped(parts.hostname):
            return _error(
                "invalid_url",
                "That does not look like a valid URL. Try something like https://myapp.com",
                400,
            )

        try:
            validate_url(url, allow_private=config.allow_private)
        except BlockedTarget:
            # Deliberately does not echo why. The precise reason is a probe result
            # about the caller's target, and this endpoint is unauthenticated.
            return _error(
                "blocked_target",
                "That address is not publicly reachable, so it cannot be scanned.",
                422,
            )

        ip = _client_ip(request, config.trust_proxy)

        if store.count_active(ip) >= config.max_concurrent_per_ip:
            return _error(
                "rate_limited",
                "You already have a scan running. Wait for it to finish before starting another.",
                429,
                headers={"Retry-After": "30"},
            )

        if store.count_since(ip, 3600) >= config.rate_limit_per_hour:
            return _error(
                "rate_limited",
                f"Scan limit reached ({config.rate_limit_per_hour} per hour). Try again later.",
                429,
                headers={"Retry-After": "3600"},
            )

        if config.cache_seconds > 0:
            cached = store.find_cached(url, config.cache_seconds)
            if cached is not None:
                # Contract §2: a fresh result may come back as 200 rather than 202.
                return JSONResponse(scan_to_dict(cached), status_code=200)

        record = store.create(url, client_ip=ip)
        worker.submit(record.id, url)
        return JSONResponse(scan_to_dict(record), status_code=202)

    @app.get("/v1/scans/{scan_id}")
    def get_scan(scan_id: str) -> JSONResponse:
        record = store.get(scan_id)
        if record is None:
            return _error(
                "scan_not_found", "This scan link has expired or does not exist.", 404
            )
        return JSONResponse(scan_to_dict(record))

    app.state.store = store
    app.state.worker = worker
    return app
