from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin

import httpx

from .ssrf import BlockedTarget, validate_url

USER_AGENT = "LeakScan/0.1 (+https://leakscan.dev/about-our-scanner) passive-security-scan"
MAX_REDIRECTS = 5
MAX_BODY_BYTES = 8 * 1024 * 1024


@dataclass
class Response:
    url: str
    final_url: str
    status: int
    headers: dict[str, str]
    text: str
    truncated: bool = False
    redirect_chain: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


class SafeClient:
    """HTTP client that re-applies the SSRF policy to every hop.

    Redirects are followed manually because httpx's automatic following would
    resolve the next hop itself, bypassing validation.
    """

    def __init__(
        self,
        *,
        timeout: float = 10.0,
        allow_private: bool = False,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.allow_private = allow_private
        self._mocked = transport is not None
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
            headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
            verify=True,
        )

    def __enter__(self) -> SafeClient:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def get(self, url: str, *, extra_headers: dict[str, str] | None = None) -> Response:
        chain: list[str] = []
        current = url

        for _ in range(MAX_REDIRECTS + 1):
            target = validate_url(current, allow_private=self.allow_private)

            headers = dict(extra_headers or {})
            request_url = current
            extensions: dict = {}

            # Connect to the validated IP so DNS cannot be re-resolved to an
            # internal address between our check and the socket connect.
            if not self._mocked and target.host != target.ip:
                request_url = target.pinned_url
                headers["Host"] = target.host
                extensions["sni_hostname"] = target.host

            resp = self._client.get(request_url, headers=headers, extensions=extensions)

            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("location")
                if not location:
                    break
                chain.append(current)
                current = urljoin(current, location)
                continue

            body = resp.content[:MAX_BODY_BYTES]
            return Response(
                url=url,
                final_url=current,
                status=resp.status_code,
                headers={k.lower(): v for k, v in resp.headers.items()},
                text=body.decode("utf-8", errors="replace"),
                truncated=len(resp.content) > MAX_BODY_BYTES,
                redirect_chain=chain,
            )

        raise BlockedTarget(f"too many redirects starting at {url}")

    def try_get(self, url: str, **kwargs) -> Response | None:
        """Best-effort fetch. Returns None instead of raising on any failure."""
        try:
            return self.get(url, **kwargs)
        except (httpx.HTTPError, BlockedTarget, UnicodeError, OSError):
            return None
