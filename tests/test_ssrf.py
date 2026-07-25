"""SSRF policy tests.

This is the highest-consequence code in the scanner: it accepts a URL from an
untrusted submitter and decides whether to connect to it. Every case below is a
real technique used to reach internal services through a URL-fetching feature.
"""

from __future__ import annotations

import pytest

from leakscan.fetch import ssrf
from leakscan.fetch.ssrf import BlockedTarget, check_ip, validate_url

BLOCKED_IPS = [
    ("127.0.0.1", "loopback"),
    ("127.1.1.1", "loopback, non-obvious form"),
    ("0.0.0.0", "unspecified, routes to localhost on Linux"),
    ("10.0.0.1", "RFC1918 private"),
    ("172.16.0.1", "RFC1918 private"),
    ("172.31.255.254", "RFC1918 upper bound"),
    ("192.168.1.1", "RFC1918 private"),
    ("169.254.169.254", "AWS/GCP/Azure instance metadata"),
    ("169.254.170.2", "ECS task metadata"),
    ("169.254.1.1", "link-local"),
    ("100.64.0.1", "carrier-grade NAT / Tailscale range"),
    ("192.0.2.1", "TEST-NET-1"),
    ("224.0.0.1", "multicast"),
    ("255.255.255.255", "broadcast"),
    ("::1", "IPv6 loopback"),
    ("fc00::1", "IPv6 unique local"),
    ("fe80::1", "IPv6 link-local"),
    ("::ffff:127.0.0.1", "IPv4-mapped IPv6 loopback"),
    ("::ffff:169.254.169.254", "IPv4-mapped IPv6 metadata"),
    ("::", "IPv6 unspecified"),
]

ALLOWED_IPS = ["8.8.8.8", "1.1.1.1", "93.184.216.34", "2606:4700:4700::1111"]


@pytest.mark.parametrize("ip,reason", BLOCKED_IPS, ids=[r for _, r in BLOCKED_IPS])
def test_internal_addresses_are_blocked(ip, reason):
    with pytest.raises(BlockedTarget):
        check_ip(ip)


@pytest.mark.parametrize("ip", ALLOWED_IPS)
def test_public_addresses_are_allowed(ip):
    check_ip(ip)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://localhost/",
        "https://localhost/admin",
        "http://[::1]/",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://10.0.0.5:8080/",
        "http://192.168.0.1/",
        "http://db.internal/",
        "http://printer.local/",
        "http://app.corp/",
    ],
)
def test_internal_urls_rejected(url):
    with pytest.raises(BlockedTarget):
        validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "gopher://127.0.0.1:6379/_SET%20key%20value",
        "dict://127.0.0.1:11211/stat",
        "ftp://internal.example.com/",
        "jar:http://example.com!/",
        "data:text/html,<script>alert(1)</script>",
        "//example.com/",
        "/etc/passwd",
    ],
)
def test_non_http_schemes_rejected(url):
    with pytest.raises(BlockedTarget):
        validate_url(url)


def test_userinfo_does_not_confuse_host_parsing():
    """http://google.com@127.0.0.1/ has host 127.0.0.1, not google.com."""
    with pytest.raises(BlockedTarget):
        validate_url("http://google.com@127.0.0.1/")


def test_decimal_encoded_loopback_rejected(monkeypatch):
    """2130706433 is 127.0.0.1 in decimal; the resolver expands it."""
    monkeypatch.setattr(ssrf, "resolve", lambda host: ["127.0.0.1"])
    with pytest.raises(BlockedTarget):
        validate_url("http://2130706433/")


def test_unusual_port_rejected(monkeypatch):
    monkeypatch.setattr(ssrf, "resolve", lambda host: ["93.184.216.34"])
    with pytest.raises(BlockedTarget, match="port not allowed"):
        validate_url("http://example.com:6379/")


def test_dns_returning_any_private_address_blocks_whole_host(monkeypatch):
    """A host with one public and one private record is an attack, not a quirk."""
    monkeypatch.setattr(ssrf, "resolve", lambda host: ["93.184.216.34", "10.0.0.1"])
    with pytest.raises(BlockedTarget):
        validate_url("https://split-horizon.example.com/")


def test_public_url_is_pinned_to_resolved_ip(monkeypatch):
    monkeypatch.setattr(ssrf, "resolve", lambda host: ["93.184.216.34"])
    target = validate_url("https://example.com/app?x=1")
    assert target.host == "example.com"
    assert target.ip == "93.184.216.34"
    assert target.pinned_url == "https://93.184.216.34:443/app?x=1"


def test_ipv6_pinned_url_is_bracketed(monkeypatch):
    monkeypatch.setattr(ssrf, "resolve", lambda host: ["2606:4700:4700::1111"])
    target = validate_url("https://example.com/")
    assert target.pinned_url == "https://[2606:4700:4700::1111]:443/"


def test_allow_private_escape_hatch_permits_localhost():
    target = validate_url("http://127.0.0.1:8000/", allow_private=True)
    assert target.ip == "127.0.0.1"
    assert target.port == 8000
