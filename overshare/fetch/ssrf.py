from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {80, 443, 8080, 8443}

# Hostnames that should never be resolved, regardless of what they resolve to.
BLOCKED_HOST_SUFFIXES = (
    ".local",
    ".localhost",
    ".internal",
    ".lan",
    ".home",
    ".corp",
    ".intranet",
)
BLOCKED_HOSTS = {
    "localhost",
    "metadata",
    "metadata.google.internal",
    "instance-data",
    "instance-data.ec2.internal",
}

# Cloud instance metadata endpoints. These are globally-routable-looking in some
# clouds, so flag them by address rather than relying on is_global alone.
METADATA_ADDRESSES = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("169.254.170.2"),
    ipaddress.ip_address("fd00:ec2::254"),
}


class BlockedTarget(Exception):
    """Raised when a URL or resolved address fails the SSRF policy."""


@dataclass(frozen=True)
class Target:
    url: str
    scheme: str
    host: str
    port: int
    path: str
    ip: str

    @property
    def pinned_url(self) -> str:
        """URL with the literal validated IP, so the connection cannot be re-resolved."""
        addr = ipaddress.ip_address(self.ip)
        literal = f"[{self.ip}]" if addr.version == 6 else self.ip
        return f"{self.scheme}://{literal}:{self.port}{self.path}"


def _normalize(ip: ipaddress._BaseAddress) -> ipaddress._BaseAddress:
    """Unwrap IPv4-mapped and 6to4 IPv6 addresses so ::ffff:127.0.0.1 is caught."""
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped:
            return ip.ipv4_mapped
        if ip.sixtofour:
            return ip.sixtofour
        if ip.teredo:
            return ip.teredo[1]
    return ip


def check_ip(raw: str) -> None:
    """Raise BlockedTarget unless `raw` is a publicly routable address."""
    try:
        ip = ipaddress.ip_address(raw)
    except ValueError as exc:
        raise BlockedTarget(f"not an IP address: {raw}") from exc

    ip = _normalize(ip)

    if ip in METADATA_ADDRESSES:
        raise BlockedTarget(f"cloud metadata endpoint: {ip}")
    if ip.is_loopback:
        raise BlockedTarget(f"loopback address: {ip}")
    if ip.is_link_local:
        raise BlockedTarget(f"link-local address: {ip}")
    if ip.is_private:
        raise BlockedTarget(f"private address: {ip}")
    if ip.is_reserved:
        raise BlockedTarget(f"reserved address: {ip}")
    if ip.is_multicast:
        raise BlockedTarget(f"multicast address: {ip}")
    if ip.is_unspecified:
        raise BlockedTarget(f"unspecified address: {ip}")
    if not ip.is_global:
        raise BlockedTarget(f"non-routable address: {ip}")


def check_host(host: str) -> None:
    h = host.lower().strip(".")
    if not h:
        raise BlockedTarget("empty hostname")
    if h in BLOCKED_HOSTS:
        raise BlockedTarget(f"blocked hostname: {host}")
    if h.endswith(BLOCKED_HOST_SUFFIXES):
        raise BlockedTarget(f"internal TLD: {host}")


def resolve(host: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise BlockedTarget(f"DNS resolution failed for {host}: {exc}") from exc
    seen: list[str] = []
    for info in infos:
        addr = info[4][0]
        if addr not in seen:
            seen.append(addr)
    if not seen:
        raise BlockedTarget(f"no addresses for {host}")
    return seen


def validate_url(url: str, *, allow_private: bool = False) -> Target:
    """Parse, policy-check, resolve, and pin a URL to a single validated IP.

    Every resolved address must pass, not just the one we connect to: a host
    with one public and one private A record is an attack, not a config quirk.
    """
    parts = urlsplit(url)

    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise BlockedTarget(f"scheme not allowed: {parts.scheme or '(none)'}")

    host = parts.hostname
    if not host:
        raise BlockedTarget(f"no hostname in URL: {url}")

    try:
        port = parts.port or (443 if parts.scheme == "https" else 80)
    except ValueError as exc:
        raise BlockedTarget(f"invalid port in URL: {url}") from exc

    if port not in ALLOWED_PORTS and not allow_private:
        raise BlockedTarget(f"port not allowed: {port}")

    if not allow_private:
        check_host(host)

    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        try:
            addresses = resolve(host)
        except BlockedTarget:
            if not allow_private:
                raise
            addresses = [host]
    else:
        addresses = [str(literal)]

    if not allow_private:
        for addr in addresses:
            check_ip(addr)

    path = parts.path or "/"
    if parts.query:
        path = f"{path}?{parts.query}"

    return Target(
        url=url,
        scheme=parts.scheme.lower(),
        host=host,
        port=port,
        path=path,
        ip=addresses[0],
    )
